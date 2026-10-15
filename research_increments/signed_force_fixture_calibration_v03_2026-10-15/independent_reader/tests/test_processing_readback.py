"""CPU synthetic setting controls; no SDK or native force evidence."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code"))
from independent_math import Rejected
from processing_readback import PATH, validate_processing, validate_install, classify_measurement_role
from audit_fixture import audit_data
from synthetic_fixture import fixture, rehash


def readback(disabled, clock):
    return {"schema":"WorkerLocalContactProcessingReadback/1", "status":"OBSERVED", "value":disabled,
        "reason":None,"setting_path":PATH,"getter":"carb.settings.get_settings().get(path)",
        "worker_local_scope":True,"native_clock_before":clock,"native_clock_after":clock,
        "no_native_step_during_readback":True if clock is not None else None,
        "readback_not_force_physics_qualification":True}


def install(disabled):
    return {"schema":"WorkerLocalContactProcessingInstallation/1", "phase":"AFTER_CONTEXT_CONSTRUCTION_BEFORE_RESET",
        "requested_disabled":disabled,"actual_before":readback(False,None),"actual_after":readback(disabled,None),
        "actual_matches_requested":True,"setter":"carb.settings.get_settings().set_bool(path,requested_disabled)",
        "scope":"CURRENT_OWNED_WORKER_PROCESS_NOT_GLOBAL_GPU_DRIVER"}


def small(disabled=False):
    clock={"native_epoch":"CPU_SYNTHETIC_ONLY","time_s":1.0,"callback_count":240}
    case={"id":"cal_force_c1_stack_processing_off_v03" if disabled else "cal_force_c1_stack_v03",
        "contact_processing_disabled_requested":disabled,
        "measurement_role":"NEGATIVE_PROCESSING_DISABLED_CONTROL" if disabled else "POSITIVE_PROCESSING_ENABLED_FIXTURE"}
    setting=install(disabled)
    header={"case":case,"origin_clock":clock,"contact_processing_setting":readback(disabled,clock),"contact_processing_install":setting}
    begin={"clock":clock,"contact_processing_setting":readback(disabled,clock)}
    rows=[{"native_clock_after_step":clock,"contact_processing_setting":readback(disabled,clock)} for _ in range(3)]
    end={"clock":clock,"contact_processing_setting":readback(disabled,clock)}
    return header,begin,rows,end,setting


class ProcessingReadbackTests(unittest.TestCase):
    def test_actual_on_and_off_are_distinct_and_observed(self):
        for disabled in (False,True):
            summary=validate_processing(*small(disabled))
            self.assertIs(summary["actual_disabled_value"],disabled)
            self.assertFalse(summary["setting_readback_itself_is_physics_qualification"])

    def test_preinstall_false_or_unknown_allowed_not_assumed_true(self):
        for before in (readback(False,None),dict(readback(False,None),status="UNKNOWN",value=None,reason="SDK_RETURNED_NONE")):
            setting=install(False);setting["actual_before"]=before
            validate_install(setting,False)

    def test_each_boundary_missing_unknown_nonboolean_wrongvalue_is_red(self):
        for location in ("HEADER","BEGIN","RAW","END"):
            for bad in ({"status":"UNKNOWN","value":None},{"value":0},{"value":True}):
                data=small();target={"HEADER":data[0],"BEGIN":data[1],"RAW":data[2][1],"END":data[3]}[location]
                target["contact_processing_setting"].update(bad)
                with self.subTest(location=location,bad=bad), self.assertRaises(Rejected):
                    validate_processing(*data)
            data=small();target={"HEADER":data[0],"BEGIN":data[1],"RAW":data[2][1],"END":data[3]}[location]
            target.pop("contact_processing_setting")
            with self.assertRaises(KeyError):validate_processing(*data)

    def test_native_clock_advance_and_boolean_request_wrongrole_are_red(self):
        data=small();data[2][1]["contact_processing_setting"]["native_clock_after"]={"native_epoch":"CPU_SYNTHETIC_ONLY","time_s":1.01,"callback_count":241}
        with self.assertRaises(Rejected):validate_processing(*data)
        for mutate in (lambda d:d[0]["case"].update(contact_processing_disabled_requested=0),
                       lambda d:d[0]["case"].update(measurement_role="NEGATIVE_PROCESSING_DISABLED_CONTROL"),
                       lambda d:d[4]["actual_after"].update(native_clock_before={"fabricated":True})):
            data=small();mutate(data)
            with self.assertRaises(Rejected):validate_processing(*data)

    def test_negative_raw_pass_never_positive_and_mixed_failure_retained(self):
        case=small(True)[0]["case"]
        report={"status":"PASS_CONDITIONAL_FIXTURE_CALIBRATION","failed_checks":[]}
        classify_measurement_role(report,case)
        self.assertEqual(report["status"],"NEGATIVE_CONTROL_NOT_POSITIVE_QUALIFICATION")
        self.assertEqual(report["raw_physical_threshold_status"],"PASS_CONDITIONAL_FIXTURE_CALIBRATION")
        self.assertFalse(report["positive_fixture_qualified"])
        report={"status":"FAIL_CONDITIONAL_FIXTURE_MEASUREMENT","failed_checks":[{"tick":1000,"name":"A/mg_support"}]}
        classify_measurement_role(report,case)
        self.assertEqual(report["status"],"FAIL_CONDITIONAL_FIXTURE_MEASUREMENT")
        self.assertEqual(report["negative_control_outcome"],"UNEXPECTED_OR_MIXED_MG_THRESHOLD_OUTCOME_RETAINED")

    def test_full_zero_contact_control_stays_original_all49_mg_red(self):
        data=fixture(1)
        case=data[0]["case"]
        oldcase=case["id"];case.update(id="cal_force_c1_stack_processing_off_v03",contact_processing_disabled_requested=True,measurement_role="NEGATIVE_PROCESSING_DISABLED_CONTROL")
        newepoch=data[0]["epoch"].replace(oldcase,case["id"])
        def replace_epochs(value):
            if isinstance(value,dict):
                if "native_epoch" in value:value["native_epoch"]=newepoch
                for v in value.values():replace_epochs(v)
            elif isinstance(value,(list,tuple)):
                for v in value:replace_epochs(v)
        replace_epochs(data);data[0]["epoch"]=newepoch;data[4]["case_id"]=case["id"]
        setting=install(True);data[0]["contact_processing_install"]=setting
        for obj,clock in [(data[0],data[0]["origin_clock"]),(data[1],data[1]["clock"]),(data[3],data[3]["clock"])]:
            obj["contact_processing_setting"]=readback(True,clock)
        for row in data[2]:
            row["contact_processing_setting"]=readback(True,row["native_clock_after_step"])
            for contact in row["contacts"].values():
                for query in contact["queries"]:
                    query["net_normal"]["value"]=[[0,0,0]]
                    query["matrix_normal"]["value"]=[[[0,0,0] for _ in query["matrix_normal"]["value"][0]]]
                    for name in ("normal_detail","friction_detail"):
                        detail=query[name]["value"];n=len(detail["counts"][0])
                        detail["counts"]=[[0]*n];detail["starts"]=[[0]*n];detail["selected_slot_indices"]=[]
                        for array in ("forces","points","normals","separations"):
                            if array in detail:detail[array]=[None]*128
        for boundary in (data[1],data[3]):
            for body in boundary["bodies"].values():
                body.pop("record_sha256",None)
                from audit_fixture import digest
                body["record_sha256"]=digest(body)
        rehash(data)
        validate_processing(data[0],data[1],data[2],data[3],setting)
        report,series=audit_data(*data);classify_measurement_role(report,case)
        self.assertEqual(report["status"],"FAIL_CONDITIONAL_FIXTURE_MEASUREMENT")
        self.assertEqual(report["negative_control_outcome"],"EXPECTED_ALL49_MG_FAILURE_RETAINED")
        self.assertFalse(report["positive_fixture_qualified"])
        self.assertEqual(len(series["rows"]),49)
        self.assertEqual({x["tick"] for x in report["failed_checks"] if x["name"]=="A/mg_support"},set(range(1000,1049)))
        self.assertTrue(all(x["signed_scalar_min"] is None for x in series["rows"]))

if __name__=="__main__":unittest.main()
