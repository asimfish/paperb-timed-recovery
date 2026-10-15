"""Source-bound lifecycle gate. No native or physical arithmetic/step/getter."""
import hashlib
import json

from independent_math import Rejected, integer, number


def require(test, reason):
    if not test:
        raise Rejected(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify_cleanup(markers, result, result_bytes):
    require(type(markers) is list and 1 <= len(markers) <= 32, "bounded cleanup markers")
    previous, pid, last_ns, events, indexed = None, None, -1, [], {}
    fresh_count = 0
    endpoint = result["end_clock"]
    after_release = False
    for seq, row in enumerate(markers):
        require(row["schema"] == "NativeShutdownLifecycleMarker/1" and row["case_id"] == result["case_id"] and
                type(row["seq"]) is int and row["seq"] == seq, "cleanup marker identity/sequence")
        unsigned = dict(row); claimed = unsigned.pop("record_sha256")
        require(digest(unsigned) == claimed and row["previous_record_sha256"] == previous, "cleanup marker hashchain")
        previous = claimed
        integer(row["pid"], "marker PID", 1)
        pid = row["pid"] if pid is None else pid
        require(row["pid"] == pid, "cleanup marker same process")
        integer(row["monotonic_ns"], "marker monotonic ns")
        require(row["monotonic_ns"] > last_ns, "cleanup marker monotonic order")
        last_ns = row["monotonic_ns"]
        number(row["wall_unix_s"], "marker wall"); number(row["process_elapsed_s"], "marker elapsed")
        require(row["marker_write_policy"] == "EXCLUSIVE_JSONL_FLUSH_FSYNC_NO_NATIVE_APP_UPDATE", "cleanup marker durability")
        event = row["event"]
        require(event not in events, "duplicate cleanup event")
        events.append(event); indexed[event] = row
        if event == "AFTER_CLEAR_INSTANCE":
            after_release = True
        before, after = row["native_clock_before_read"], row["native_clock_after_read"]
        for wrapper in (before, after):
            require(wrapper["status"] in ("OBSERVED", "UNKNOWN"), "cleanup native-clock status")
            if wrapper["status"] == "OBSERVED":
                require(not after_release, "native clock getter after context release prohibited")
                require(wrapper["value"] == endpoint, "native clock advanced after completed measurement")
                fresh_count += 1
            else:
                require(wrapper["value"] is None, "unknown clock cannot contain imputed cached value")
        if before["status"] == after["status"] == "OBSERVED":
            require(row["no_native_step_during_clock_reads"] is True, "cleanup no-step clock")
        else:
            require(row["no_native_step_during_clock_reads"] is None, "unknown cleanup no-step must stay unknown")
    required = ["BEFORE_RESULT_WRITE", "AFTER_RESULT_FSYNC", "BEFORE_CLEAR_INSTANCE", "AFTER_CLEAR_INSTANCE", "BEFORE_APP_CLOSE",
                "BEFORE_READONLY_REP_STATUS", "AFTER_READONLY_REP_STATUS"]
    require(all(name in indexed for name in required), "complete END/RESULT/public release/default close boundaries")
    require([events.index(name) for name in required] == sorted(events.index(name) for name in required), "release strictly after completed measurement/result fsync")
    require("CLEAR_INSTANCE_NOT_ELIGIBLE" not in indexed, "measurement incomplete not eligible for clear/qualification")
    fsync = indexed["AFTER_RESULT_FSYNC"]["fields"]
    require(type(fsync["result_file_bytes"]) is int and fsync["result_file_bytes"] == result_bytes, "fsynced result byte-size observation")
    pre = indexed["BEFORE_CLEAR_INSTANCE"]
    require(pre["fields"]["complete_END_RESULT_fsynced"] is True and pre["fields"]["owned_context_is_sim"] is True,
            "release only fully retained owned SimulationContext")
    require(type(pre["fields"]["owned_stop_handle_present"]) is bool, "pre-release actual stop handle presence")
    require(pre["fields"]["actual_python_callback_count_beforeclear"] == endpoint["callback_count"], "pre-clear actual callback count")
    require(pre["native_clock_before_read"]["status"] == pre["native_clock_after_read"]["status"] == "OBSERVED", "fresh pre-release endpoint clock")
    post = indexed["AFTER_CLEAR_INSTANCE"]["fields"]
    require(post["live_clock_unavailable_after_clear_instance"] is True and post["public_instance_is_None"] is True and
            post["owned_stop_handle_is_None"] is True and post["actual_python_callback_count_afterclear"] == endpoint["callback_count"],
            "actual owned context and stop subscription released after measurement")
    require(post["cached_pre_clear_clock"] == pre["native_clock_after_read"], "cached endpoint explicitly bound to pre-clear observation")
    close = indexed["BEFORE_APP_CLOSE"]["fields"]
    require(close["context_cleared"] is True and close["live_clock_unavailable_after_clear_instance"] is True and
            close["cached_pre_clear_clock"] == pre["native_clock_after_read"], "default close only after public context release")
    if "AFTER_APP_CLOSE" in indexed:
        ret = indexed["AFTER_APP_CLOSE"]["fields"]
        require(ret["native_time_afterclose"] == "UNKNOWN_NOT_READ_AFTER_FRAMEWORK_RELEASE" and
                ret["default_close_returned"] is True and ret["context_cleared"] is True and
                ret["actual_python_callback_count_afterclose"] == endpoint["callback_count"], "after-framework time unknown/callback count retained")
    return {"status": "PASS_MEASUREMENT_THEN_OWNED_PUBLIC_CONTEXT_RELEASE", "events": events,
            "marker_count": len(markers), "last_marker_sha256": previous, "fresh_preclear_clock_reads": fresh_count,
            "after_clear_native_time": "UNKNOWN_NOT_READ", "after_framework_native_time": "UNKNOWN_NOT_READ",
            "stop_subscription_release": "OBSERVED_PRESENT_THEN_NONE" if pre["fields"]["owned_stop_handle_present"] else "INCONCLUSIVE_NOT_PRESENT_BEFORE_CLEAR",
            "default_close_python_return": "OBSERVED_RETURNED_TRUE" if "AFTER_APP_CLOSE" in indexed else "UNKNOWN_NO_AFTER_APP_CLOSE_MARKER",
            "compiled_backend_root_cause": "UNKNOWN", "native_fix_claim_from_source_only": False}
