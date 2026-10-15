"""Independent contact-processing readback guard; no SDK/producer imports."""
from independent_math import Rejected

PATH = "/physics/disableContactProcessing"


def require(test, reason):
    if not test:
        raise Rejected(reason)


def validate_readback(value, expected, clock):
    require(type(value) is dict and value.get("schema") == "WorkerLocalContactProcessingReadback/1",
            "actual processing-setting readback schema")
    require(value.get("status") == "OBSERVED" and type(value.get("value")) is bool and value["value"] is expected,
            "processing-setting actual boolean equals prospective case request")
    require(value.get("setting_path") == PATH and value.get("getter") == "carb.settings.get_settings().get(path)" and
            value.get("worker_local_scope") is True and value.get("readback_not_force_physics_qualification") is True,
            "worker-local readonly setting source/scope")
    require(value.get("native_clock_before") == value.get("native_clock_after") == clock,
            "processing-setting readback same actual native clock")
    require(value.get("no_native_step_during_readback") is (True if clock is not None else None),
            "processing-setting no-step scope")


def validate_install(install, expected):
    require(install.get("schema") == "WorkerLocalContactProcessingInstallation/1" and
            install.get("phase") == "AFTER_CONTEXT_CONSTRUCTION_BEFORE_RESET" and
            type(install.get("requested_disabled")) is bool and install["requested_disabled"] is expected and
            install.get("actual_matches_requested") is True and
            install.get("setter") == "carb.settings.get_settings().set_bool(path,requested_disabled)" and
            install.get("scope") == "CURRENT_OWNED_WORKER_PROCESS_NOT_GLOBAL_GPU_DRIVER", "before-reset case-bound installation")
    before = install["actual_before"]
    require(before.get("setting_path") == PATH and before.get("native_clock_before") is None and before.get("native_clock_after") is None and
            before.get("no_native_step_during_readback") is None, "pre-install no native clock fabricated")
    require((before.get("status") == "OBSERVED" and type(before.get("value")) is bool) or
            (before.get("status") == "UNKNOWN" and before.get("value") is None), "actual pre-install state not assumed True")
    validate_readback(install["actual_after"], expected, None)


def validate_processing(header, begin, rows, end, install):
    case = header["case"]; expected = case["contact_processing_disabled_requested"]
    require(type(expected) is bool, "case-bound processing request bool")
    expected_role = "NEGATIVE_PROCESSING_DISABLED_CONTROL" if expected else "POSITIVE_PROCESSING_ENABLED_FIXTURE"
    require(case["measurement_role"] == expected_role, "predeclared control/positive role")
    require(case["id"] == "cal_force_c1_stack_processing_off_v03" if expected else case["id"] in
            {"cal_force_c0_freefall_v03","cal_force_c1_stack_v03","cal_force_c2_rotated_v03","cal_force_c3_actor_order_v03","cal_force_c4_mass_v03"},
            "bounded six-case identity and processing role")
    validate_install(install, expected)
    require(header["contact_processing_install"] == install, "header/actual before-reset install binding")
    validate_readback(header["contact_processing_setting"], expected, header["origin_clock"])
    validate_readback(begin["contact_processing_setting"], expected, begin["clock"])
    for row in rows:
        validate_readback(row["contact_processing_setting"], expected, row["native_clock_after_step"])
    validate_readback(end["contact_processing_setting"], expected, end["clock"])
    return {"status":"PASS_ACTUAL_CASE_BOUND_SETTING_AT_ALL_CAPTURE_BOUNDARIES",
            "setting_path":PATH,"actual_disabled_value":expected,"role":expected_role,
            "controlled_readback_count":len(rows),"installation_before_value_not_assumed":True,
            "setting_readback_itself_is_physics_qualification":False}


def classify_measurement_role(report, case):
    negative = case["measurement_role"] == "NEGATIVE_PROCESSING_DISABLED_CONTROL"
    report["measurement_role"] = case["measurement_role"]
    report["raw_physical_threshold_status"] = report["status"]
    report["positive_fixture_qualified"] = not negative and report["status"] == "PASS_CONDITIONAL_FIXTURE_CALIBRATION"
    report["method_failure_inference"] = "NOT_EVALUATED_NEGATIVE_MEASUREMENT_CONTROL" if negative else "NOT_A_LEARNING_COMPARISON"
    if negative:
        failed = {c["tick"] for c in report["failed_checks"] if c["name"] == "A/mg_support"}
        report["negative_control_outcome"] = "EXPECTED_ALL49_MG_FAILURE_RETAINED" if len(failed) == 49 else "UNEXPECTED_OR_MIXED_MG_THRESHOLD_OUTCOME_RETAINED"
        if report["status"] == "PASS_CONDITIONAL_FIXTURE_CALIBRATION":
            report["status"] = "NEGATIVE_CONTROL_NOT_POSITIVE_QUALIFICATION"
    return report
