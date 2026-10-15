import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code"))
from audit_fixture import Rejected, audit_data, compare_reference, digest
from synthetic_fixture import AP, BP, fixture, rehash


class SchemaReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {i: fixture(i) for i in range(5)}

    def test_all_five_synthetic_positive_and_fixed49(self):
        for i, data in self.fixtures.items():
            report, series = audit_data(*data)
            self.assertEqual(report["status"], "PASS_CONDITIONAL_FIXTURE_CALIBRATION", (i, report["failed_checks"][:1]))
            self.assertEqual(len(series["rows"]), 49)
            self.assertEqual(report["S_F_R_admitted"], 0)
            if i == 0:
                self.assertIsNone(series["rows"][0]["pair_normal_AB_world"])
            else:
                self.assertGreater(series["rows"][0]["selected_negative_count"], 0)

    def test_abs_scalar_is_physical_red_not_abs_pass(self):
        data = copy.deepcopy(self.fixtures[1])
        data[2][1000]["contacts"][AP]["queries"][1]["normal_detail"]["value"]["forces"][0][0] *= -1
        rehash(data)
        report, series = audit_data(*data)
        self.assertEqual(report["status"], "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT")
        self.assertEqual(len(series["rows"]), 49)
        self.assertTrue(any("signed_matrix" in x["name"] for x in report["failed_checks"]))

    def test_cancelling_scalar_dt_errors_cannot_hide_in_aggregate(self):
        data = copy.deepcopy(self.fixtures[1])
        queries = data[2][1000]["contacts"][AP]["queries"]
        for query in queries:
            raw = query["normal_detail"]["value"]
            raw["counts"] = [[2]]; raw["selected_slot_indices"] = [0, 1]
            raw["forces"][0][0] /= 2
            raw["forces"][1] = list(raw["forces"][0])
            for name in ("points", "normals", "separations"):
                raw[name][1] = list(raw[name][0])
        queries[0]["normal_detail"]["value"]["forces"][0][0] += .01
        queries[0]["normal_detail"]["value"]["forces"][1][0] -= .01
        rehash(data)
        report, _ = audit_data(*data)
        self.assertEqual(report["status"], "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT")
        self.assertTrue(any("selected_normal_slot" in x["name"] for x in report["failed_checks"]))

    def test_window_one_bad_point_cannot_average_or_drop(self):
        data = copy.deepcopy(self.fixtures[0])
        data[2][119]["contacts"][AP]["queries"][1]["net_normal"]["value"][0][0] = .002
        rehash(data)
        report, series = audit_data(*data)
        self.assertEqual(report["status"], "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT")
        self.assertEqual(len(series["rows"]), 49)
        self.assertTrue(any(x["tick"] == 119 for x in report["failed_checks"]))

    def test_missing_row_and_bad_external_header_are_rejected(self):
        data = copy.deepcopy(self.fixtures[0]); data[2].pop(70)
        with self.assertRaisesRegex(Rejected, "complete fixed controlled"):
            audit_data(*data)
        data = copy.deepcopy(self.fixtures[0]); data[0]["case"]["mass_A_kg"] = .2
        # deepcopy preserves shared aliases; independent external expected object is replaced.
        data = list(data); data[5] = copy.deepcopy(self.fixtures[0][5])
        with self.assertRaisesRegex(Rejected, "external expected header"):
            audit_data(*data)

    def test_same_callback_query_is_mandatory(self):
        data = copy.deepcopy(self.fixtures[0])
        # Replace dict to avoid shared synthetic clock aliases.
        query = data[2][71]["contacts"][AP]["queries"][1]
        query["clock_after"] = dict(query["clock_after"], callback_count=74)
        rehash(data)
        with self.assertRaisesRegex(Rejected, "native clock"):
            audit_data(*data)

    def test_missing_readback_saturation_and_bad_range_reject(self):
        mutations = [
            lambda d: d[2][1000]["bodies"][AP]["rigid_body"]["mass_kg"].update(status="UNKNOWN", value=None),
            lambda d: d[2][1000]["contacts"][AP]["queries"][1]["normal_detail"]["value"].update(capacity_saturated=True),
            lambda d: d[2][1000]["contacts"][AP]["queries"][1]["normal_detail"]["value"].update(starts=[[128]]),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.fixtures[1]); mutate(data); rehash(data)
            with self.assertRaises(Rejected):
                audit_data(*data)

    def test_actor_order_unobserved_remains_inconclusive(self):
        base_report, base_series = audit_data(*self.fixtures[1])
        report, series = audit_data(*self.fixtures[3])
        compare_reference(report, series, self.fixtures[3][0], base_report, base_series, self.fixtures[1][0])
        self.assertEqual(report["cross_case_status"], "PASS")
        self.assertTrue(report["actual_actor_order_proxy_changed"])
        self.assertIn("INCONCLUSIVE", report["creation_order_mechanism"])

    def test_unused_global_default_material_preserved_and_allowed(self):
        data = copy.deepcopy(self.fixtures[0])
        inventory = data[0]["stage_inventory"]
        inventory["materials"].append({"path": "/physicsScene/defaultMaterial", "static_friction": .5,
                                       "dynamic_friction": .5, "restitution": 0})
        for row in data[2]:
            row["stage_inventory_sha256"] = digest(inventory)
        for boundary in (data[1], data[3]):
            for b in boundary["bodies"].values():
                b.pop("record_sha256"); b["record_sha256"] = digest(b)
        rehash(data)
        report, _ = audit_data(*data)
        self.assertEqual(report["status"], "PASS_CONDITIONAL_FIXTURE_CALIBRATION")

    def test_fixture_owned_nonzero_material_is_rejected(self):
        data = copy.deepcopy(self.fixtures[0])
        data[0]["stage_inventory"]["materials"][0]["static_friction"] = .5
        with self.assertRaisesRegex(Rejected, "fixture-owned authored material"):
            audit_data(*data)

    def test_mass_doubling_crosscase_and_unqualified_baseline(self):
        base_report, base_series = audit_data(*self.fixtures[1])
        report, series = audit_data(*self.fixtures[4])
        compare_reference(report, series, self.fixtures[4][0], base_report, base_series, self.fixtures[1][0])
        self.assertEqual(report["cross_case_status"], "PASS")
        base_report["status"] = "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT"
        compare_reference(report, series, self.fixtures[4][0], base_report, base_series, self.fixtures[1][0])
        self.assertEqual(report["cross_case_status"], "UNKNOWN_BASELINE_NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()
