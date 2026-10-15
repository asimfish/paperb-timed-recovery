import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code"))
from cleanup_lifecycle import verify_cleanup, digest
from independent_math import Rejected


def fixture():
    clock = {"native_epoch": "SYNTHETIC_NOT_NATIVE", "time_s": .5, "callback_count": 120}
    observed = {"status": "OBSERVED", "value": clock, "reason": None}
    unknown = {"status": "UNKNOWN", "value": None, "reason": "NO_LIVE_CLOCK_READER"}
    fields = {
        "BEFORE_RESULT_WRITE": {},
        "AFTER_RESULT_FSYNC": {"result_file_bytes": 100},
        "BEFORE_CLEAR_INSTANCE": {"complete_END_RESULT_fsynced": True, "owned_context_is_sim": True,
            "owned_stop_handle_present": True, "actual_python_callback_count_beforeclear": 120},
        "AFTER_CLEAR_INSTANCE": {"live_clock_unavailable_after_clear_instance": True, "public_instance_is_None": True,
            "owned_stop_handle_is_None": True, "actual_python_callback_count_afterclear": 120, "cached_pre_clear_clock": observed},
        "BEFORE_APP_CLOSE": {"context_cleared": True, "live_clock_unavailable_after_clear_instance": True,
            "cached_pre_clear_clock": observed},
        "BEFORE_READONLY_REP_STATUS": {},
        "AFTER_READONLY_REP_STATUS": {},
        "AFTER_APP_CLOSE": {"native_time_afterclose": "UNKNOWN_NOT_READ_AFTER_FRAMEWORK_RELEASE", "default_close_returned": True,
            "context_cleared": True, "actual_python_callback_count_afterclose": 120},
    }
    rows, previous = [], None
    for seq, (event, f) in enumerate(fields.items()):
        live = observed if seq < 3 else unknown
        row = {"schema": "NativeShutdownLifecycleMarker/1", "case_id": "cal_force_c0_freefall_v03", "seq": seq,
            "pid": 999, "monotonic_ns": seq+1, "wall_unix_s": 17000+seq, "process_elapsed_s": seq,
            "event": event, "fields": f, "marker_write_policy": "EXCLUSIVE_JSONL_FLUSH_FSYNC_NO_NATIVE_APP_UPDATE",
            "native_clock_before_read": live, "native_clock_after_read": live,
            "no_native_step_during_clock_reads": True if seq < 3 else None, "previous_record_sha256": previous}
        row["record_sha256"] = digest(row); previous = row["record_sha256"]; rows.append(row)
    return rows, {"case_id": "cal_force_c0_freefall_v03", "end_clock": clock}, 100


def rehash(rows):
    previous = None
    for row in rows:
        row["previous_record_sha256"] = previous
        row.pop("record_sha256", None); row["record_sha256"] = digest(row); previous = row["record_sha256"]


class CleanupTests(unittest.TestCase):
    def test_release_after_retained_measurement_unknown_postclear_time(self):
        result = verify_cleanup(*fixture())
        self.assertEqual(result["status"], "PASS_MEASUREMENT_THEN_OWNED_PUBLIC_CONTEXT_RELEASE")
        self.assertEqual(result["after_clear_native_time"], "UNKNOWN_NOT_READ")
        self.assertEqual(result["stop_subscription_release"], "OBSERVED_PRESENT_THEN_NONE")
        self.assertFalse(result["native_fix_claim_from_source_only"])

    def test_release_before_fsync_is_rejected(self):
        data = list(fixture()); data[0][1]["event"], data[0][2]["event"] = data[0][2]["event"], data[0][1]["event"]
        rehash(data[0])
        with self.assertRaisesRegex(Rejected, "strictly after"):
            verify_cleanup(*data)

    def test_foreign_context_and_unreleased_subscription_rejected(self):
        for seq, field in ((2, "owned_context_is_sim"), (3, "owned_stop_handle_is_None"), (3, "public_instance_is_None")):
            data = copy.deepcopy(fixture()); data[0][seq]["fields"][field] = False; rehash(data[0])
            with self.assertRaises(Rejected):
                verify_cleanup(*data)

    def test_no_native_clock_getter_after_clear_even_if_same_value(self):
        data = copy.deepcopy(fixture())
        data[0][3]["native_clock_before_read"] = data[0][2]["native_clock_before_read"]
        rehash(data[0])
        with self.assertRaisesRegex(Rejected, "after context release prohibited"):
            verify_cleanup(*data)

    def test_cached_clock_cannot_be_backdated_or_imputed_fresh(self):
        data = copy.deepcopy(fixture())
        data[0][3]["fields"]["cached_pre_clear_clock"] = {"status": "OBSERVED", "value": {"callback_count": 0}}
        rehash(data[0])
        with self.assertRaisesRegex(Rejected, "cached endpoint"):
            verify_cleanup(*data)

    def test_callback_count_changed_or_wrong_fsync_size_rejected(self):
        for seq, field, value in ((3, "actual_python_callback_count_afterclear", 121), (1, "result_file_bytes", 99)):
            data = copy.deepcopy(fixture()); data[0][seq]["fields"][field] = value; rehash(data[0])
            with self.assertRaises(Rejected):
                verify_cleanup(*data)

    def test_fast_framework_process_exit_need_not_invent_close_return(self):
        data = list(fixture()); data[0].pop(); rehash(data[0])
        result = verify_cleanup(*data)
        self.assertNotIn("AFTER_APP_CLOSE", result["events"])
        self.assertEqual(result["default_close_python_return"], "UNKNOWN_NO_AFTER_APP_CLOSE_MARKER")

    def test_missing_beforeclear_afterclear_or_readonly_return_rejected(self):
        for event in ("BEFORE_CLEAR_INSTANCE", "AFTER_CLEAR_INSTANCE", "AFTER_READONLY_REP_STATUS"):
            data = list(fixture()); data[0] = [row for row in data[0] if row["event"] != event]
            for seq, row in enumerate(data[0]):
                row["seq"] = seq
            rehash(data[0])
            with self.assertRaises(Rejected):
                verify_cleanup(*data)


if __name__ == "__main__":
    unittest.main()
