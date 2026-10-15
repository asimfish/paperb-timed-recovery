"""Prospective SDK-free reader. One ROOT terminal request, one retained audit/case."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from independent_math import (Rejected, acceleration, add, detail_matrix_agreement,
    dt_consistency, freefall, integer, low_motion, near, norm, number, reciprocal,
    scale, signed_pair_sum, static_top, vector)
from cleanup_lifecycle import verify_cleanup
from processing_readback import validate_processing, classify_measurement_role

HERE = Path(__file__).resolve().parents[1]
DT = 1/240
SCHEMA = "SignedForceFixtureIndependentAudit/1"
LIMITS = [
    "CONDITIONAL_FIXTURE_CONTACT_REPRESENTATION_DT_WORLD_FRAME_ONLY",
    "COMPLETE_ACTIVE_BACKEND_CONSTRAINT_INVENTORY_UNKNOWN",
    "NOT_REAL_HARDWARE_SI_CERTIFICATION",
    "NO_ROBOT_LOAD_UNLOAD_TORQUE_CHEMICAL_SUCCESS_OR_TRAINING_ADMISSION",
    "DOES_NOT_REWRITE_LEGACY_M0_M1_M2_RESULTS",
]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while chunk := f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def unique_pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise Rejected("duplicate JSON key: " + k)
        out[k] = v
    return out


def parse(text):
    return json.loads(text, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(Rejected("nonfinite JSON " + x)))


def read_json(path, maximum=16*1024*1024):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > maximum:
        raise Rejected("symlink/oversized JSON: " + str(path))
    return parse(path.read_text())


def require(condition, message):
    if not condition:
        raise Rejected(message)


def flatten(value):
    if type(value) is list:
        return [item for sub in value for item in flatten(sub)]
    return [value]


def same_clock(actual, expected, label):
    require(type(actual) is dict and set(actual) == {"native_epoch", "time_s", "callback_count"}, label+" clock shape")
    require(type(actual["native_epoch"]) is str and bool(actual["native_epoch"]), label+" epoch")
    integer(actual["callback_count"], label+" callback")
    number(actual["time_s"], label+" time")
    require(actual == expected, label+" moved/mismatched native clock")


def getter(item, clock, label):
    require(type(item) is dict and item.get("status") == "OBSERVED", label+" missing/unobserved")
    same_clock(item["clock_before"], clock, label+" before")
    same_clock(item["clock_after"], clock, label+" after")
    require(item.get("no_step_during_getter") is True, label+" no-step flag")
    return item["value"]


def simple_observed(item, label):
    require(type(item) is dict and item.get("status") == "OBSERVED", label+" missing/unobserved")
    require(item.get("value") is not None, label+" null observed")
    return item["value"]


def observed_body(snapshot, path, clock, tick, phase):
    require(snapshot.get("schema") == "paperb-handoff-physical-snapshot-v1", "body schema")
    require(snapshot["body_path"] == path and snapshot["tick"] == tick and snapshot["phase"] == phase,
            "body identity/phase/tick")
    same_clock(snapshot["native_clock_before"], clock, "body before")
    same_clock(snapshot["native_clock_after"], clock, "body after")
    require(snapshot["no_native_step_during_getters"] is True, "body no-step")
    unsigned = dict(snapshot); claimed = unsigned.pop("record_sha256")
    require(digest(unsigned) == claimed, "body record digest")
    fields = snapshot["rigid_body"]
    values = {key: simple_observed(value, "body "+key) for key, value in fields.items()}
    for flag in ("gravity_disabled_flag", "simulation_disabled_flag"):
        require(all(type(x) in (bool, int) and x == 0 for x in flatten(values[flag])), "body disabled "+flag)
    mass_flat = flatten(values["mass_kg"])
    require(len(mass_flat) == 1 and number(mass_flat[0]) > 0, "single positive actual mass")
    inverse = flatten(values["inverse_mass_per_kg"])
    require(len(inverse) == 1 and abs(number(inverse[0])*number(mass_flat[0])-1) <= 1e-5, "actual inverse mass")
    for key in ("transform_xyz_xyzw", "velocity_world_com_linear_angular", "acceleration_world_com_linear_angular",
                "com_local_xyz_xyzw", "inertia_com_body_frame_column_major_kg_m2"):
        for x in flatten(values[key]):
            number(x, key)
    velocity = flatten(values["velocity_world_com_linear_angular"])
    accel = flatten(values["acceleration_world_com_linear_angular"])
    require(len(velocity) == len(accel) == 6, "world COM six-component velocity/accel")
    gravity = vector(simple_observed(snapshot["scene_gravity_world_m_s2"], "scene gravity"))
    for name in ("instantaneous", "permanent"):
        wrench = simple_observed(snapshot["external_wrench_buffers"][name], "external composer "+name)
        require(all(type(x) is bool and x is False for x in flatten(wrench["active"])), "active external composer")
        require(all(number(x) == 0 for x in flatten(wrench["force_body_frame_N"])), "external force")
        require(all(number(x) == 0 for x in flatten(wrench["torque_body_frame_N_m"])), "external torque")
    return {"mass": number(mass_flat[0]), "gravity": gravity,
            "v": vector(velocity[:3]), "omega": vector(velocity[3:]),
            "a": vector(accel[:3]), "alpha": vector(accel[3:])}


def detail(value, filters, kind):
    require(type(value) is dict and value.get("capacity") == 128, "detail capacity")
    unsigned = dict(value); claimed = unsigned.pop("copied_payload_sha256")
    require(digest(unsigned) == claimed, "detail copied payload digest")
    require(value.get("capacity_saturated") is False, "detail capacity saturation")
    require(value.get("unused_slot_policy") == "NULL_MARKER_NOT_READ_NOT_ZERO_IMPUTED", "unused slot scope")
    counts, starts = value["counts"], value["starts"]
    require(type(counts) is list and len(counts) == 1 and len(counts[0]) == filters, "count dimensions")
    require(type(starts) is list and len(starts) == 1 and len(starts[0]) == filters, "start dimensions")
    shapes = value["buffer_shapes"]
    expected = {"forces": [128, 1] if kind == "normal" else [128, 3], "points": [128, 3],
                "counts": [1, filters], "starts": [1, filters]}
    if kind == "normal":
        expected.update({"normals": [128, 3], "separations": [128, 1]})
    require(shapes == expected, "exact detail backend shapes")
    ranges, used = [], set()
    for count, start in zip(counts[0], starts[0]):
        count, start = integer(count, "detail count"), integer(start, "detail start")
        require(start+count <= 128, "detail range exceeds capacity")
        selected = list(range(start, start+count))
        require(not used.intersection(selected), "overlap selected ranges")
        used.update(selected); ranges.append(selected)
    require(len(used) < 128 and value["selected_slot_indices"] == sorted(used), "selected coverage or saturation")
    for name in expected:
        if name in ("counts", "starts"):
            continue
        array = value[name]
        require(type(array) is list and len(array) == 128, name+" capacity slots")
        for i, cell in enumerate(array):
            if i not in used:
                require(cell is None, "unused cell was read/imputed")
            else:
                n = expected[name][1]
                require(type(cell) is list and len(cell) == n, name+" selected cell dimensions")
                for x in cell:
                    number(x, name+" selected cell")
    pairs = []
    for selected in ranges:
        if kind == "normal":
            contacts = [{"scalar": value["forces"][i][0], "normal": value["normals"][i]} for i in selected]
            pairs.append({"vector": signed_pair_sum(contacts), "selected": contacts})
        else:
            summed = [math.fsum(value["forces"][i][axis] for i in selected) for axis in range(3)]
            pairs.append({"vector": summed, "selected": [value["forces"][i] for i in selected]})
    return pairs


def copied_query(contact, clock, path, expected_metadata, freefall_case):
    require(contact["metadata"] == expected_metadata, "contact metadata changed")
    filters = expected_metadata["filter_count"]
    queries = contact["queries"]
    require(type(queries) is list and len(queries) == 3, "three copied getter-dt queries")
    collected = []
    for query, qdt in zip(queries, (1.0, DT, 2*DT)):
        require(type(query["query_dt_s"]) in (int, float) and query["query_dt_s"] == qdt, "query dt order")
        same_clock(query["clock_before"], clock, "query before")
        same_clock(query["clock_after"], clock, "query after")
        require(query["no_step_during_query"] is True, "query no-step")
        net = getter(query["net_normal"], clock, "net normal")
        require(type(net) is list and len(net) == 1, "net sensor dimensions")
        item = {"net": vector(net[0]), "qdt": qdt}
        if freefall_case:
            require(query.get("channel_scope") == "INTENTIONALLY_NOT_CONFIGURED_FREEFALL", "freefall channel scope")
            require(query.get("unconfigured_channels") == ["matrix_normal", "normal_detail", "friction_detail"], "freefall unconfigured list")
            require(not any(key in query for key in ("matrix_normal", "normal_detail", "friction_detail")), "freefall unconfigured imputation")
        else:
            matrix = getter(query["matrix_normal"], clock, "matrix normal")
            require(type(matrix) is list and len(matrix) == 1 and len(matrix[0]) == filters, "matrix dimensions")
            item["matrix"] = [vector(v) for v in matrix[0]]
            item["normal_raw"] = getter(query["normal_detail"], clock, "normal detail")
            item["friction_raw"] = getter(query["friction_detail"], clock, "friction detail")
            item["normal"] = detail(item["normal_raw"], filters, "normal")
            item["friction"] = detail(item["friction_raw"], filters, "friction")
        collected.append(item)
    if not freefall_case:
        for kind in ("normal_raw", "friction_raw"):
            structural = [key for key in collected[0][kind] if key not in ("forces", "copied_payload_sha256")]
            for query in collected[1:]:
                require(all(query[kind][key] == collected[0][kind][key] for key in structural),
                        "copied dt counts/start/points/normals/separations changed")
    return collected


def inventory_check(header, paths, freefall_case, case):
    inventory = header["stage_inventory"]
    require(inventory["meters_per_unit"] == inventory["kilograms_per_unit"] == 1, "stage SI units")
    require(inventory["joints"] == [], "authored joints in fixture")
    allowed = paths if freefall_case else paths+["/Cal/ground"]
    colliders = inventory["colliders"]
    require(type(colliders) is list and len(colliders) == len(allowed), "complete authored collider count")
    require(all(any(c["path"] == p or c["path"].startswith(p+"/") for p in allowed) and
                c["collision_enabled"] is True for c in colliders), "unexpected/disabled collider")
    require(len({c["path"] for c in colliders}) == len(colliders), "duplicate collider")
    require(all(any(c["path"] == p or c["path"].startswith(p+"/") for c in colliders) for p in allowed), "missing fixture collider")
    rigid = inventory["rigid_bodies"]
    require({item["path"] for item in rigid} == set(paths), "exact dynamic actor inventory")
    for item in rigid:
        require(item["rigid_body_enabled"] is True and item["kinematic_enabled"] is False and item["disable_gravity"] is False,
                "authored actor activation")
        for k in ("linear_damping", "angular_damping", "sleep_threshold", "contact_report_threshold"):
            require(number(item[k]) == 0, "authored nonzero "+k)
        expected_mass = case["mass_A_kg"] if item["path"] == "/Cal/A_top" else case["mass_B_kg"]
        require(abs(number(item["authored_mass_kg"])-expected_mass) <= 1e-7, "authored mass")
    # SimulationContext authors a global default material even when fixture
    # constructors override it. Preserve its observation, but do not pretend
    # an unused global default is a participating fixture contact material.
    fixture_materials = [m for m in inventory["materials"]
                         if any(m["path"].startswith(p+"/") for p in allowed)]
    require(all(any(m["path"].startswith(p+"/") for m in fixture_materials) for p in allowed),
            "missing fixture-owned authored material inventory")
    for material in fixture_materials:
        for k in ("static_friction", "dynamic_friction", "restitution"):
            require(number(material[k]) == 0, "fixture-owned authored material "+k)
    for path in paths:
        readback = header["fixture_setup_readback"][path]
        require(flatten(readback["prim_paths"]) == [path] and readback["max_shapes"] == 1, "actual body path/shape readback")
        mat = getter(readback["material_properties_static_dynamic_restitution"], header["origin_clock"], "actual material")
        require(len(flatten(mat)) == 3 and all(number(x) == 0 for x in flatten(mat)), "actual material friction/restitution")
        for key, expected in (("contact_offsets", .001), ("rest_offsets", 0)):
            observed = flatten(getter(readback[key], header["origin_clock"], "actual "+key))
            require(len(observed) == 1 and abs(number(observed[0])-expected) <= 1e-7, "actual "+key)


def metadata_check(header, paths, freefall_case):
    require(set(header["contact_views"]) == set(paths), "contact sensor coverage")
    ground_colliders = [c["path"] for c in header["stage_inventory"]["colliders"]
                        if c["path"] == "/Cal/ground" or c["path"].startswith("/Cal/ground/")]
    if not freefall_case:
        require(len(ground_colliders) == 1, "unique actual static ground collider")
    for path, meta in header["contact_views"].items():
        expected_filters = [] if freefall_case else (["/Cal/B_bottom"] if path == "/Cal/A_top" else ["/Cal/A_top", ground_colliders[0]])
        require(meta["requested_sensor_path"] == path and meta["requested_filter_paths"] == expected_filters, "requested contact filters")
        require(flatten(meta["sensor_paths"]) == [path] and flatten(meta["filter_paths"]) == expected_filters, "actual sensor/filter path order")
        require(meta["sensor_count"] == 1 and meta["filter_count"] == len(expected_filters) and
                meta["max_contact_data_count"] == 128 and meta["check"] is True, "actual contact view capacity/check")


def measurement(row, previous, header, case):
    clock = row["native_clock_after_step"]
    paths = list(header["contact_views"])
    c0 = case["id"] == "cal_force_c0_freefall_v03"
    bodies = {p: observed_body(row["bodies"][p], p, clock, row["tick"], "POST_STEP") for p in paths}
    prev_clock = previous["native_clock_after_step"]
    prev = {p: observed_body(previous["bodies"][p], p, prev_clock, previous["tick"], "POST_STEP") for p in paths}
    require(set(row["bodies"]) == set(row["contacts"]) == set(paths), "RAW body/contact coverage")
    for p, b in bodies.items():
        expected_mass = case["mass_A_kg"] if p == "/Cal/A_top" else case["mass_B_kg"]
        require(abs(b["mass"]-expected_mass) <= 1e-7, "actual mass disagrees frozen case")
        near(b["gravity"], case["gravity_world_m_s2"], 1e-5, label="actual frozen gravity")
    contacts = {p: copied_query(row["contacts"][p], clock, p, header["contact_views"][p], c0) for p in paths}
    a = bodies["/Cal/A_top"]
    fd = acceleration(a["v"], prev["/Cal/A_top"]["v"], DT)
    series = {"case_id": case["id"], "tick": row["tick"], "native_time_s": clock["time_s"],
              "mass_A_kg": a["mass"], "gravity_world": a["gravity"],
              "acceleration_A_world": a["a"], "velocity_difference_acceleration_A_world": fd,
              "velocity_A_world": a["v"], "net_normal_A_world": contacts["/Cal/A_top"][1]["net"],
              "pair_normal_AB_world": None, "pair_normal_BA_world": None, "friction_AB_world": None,
              "matrix_vs_signed_err_N": None, "dt_err_N": None, "dt_impulse_err_Ns": None,
              "signed_scalar_min": None, "selected_negative_count": None,
              "channel_scope": "NET_ONLY_INTENTIONALLY_UNCONFIGURED_DETAILS" if c0 else "NORMAL_PAIR_AND_FRICTION_SELECTED_FILTERS"}
    checks = []
    def check(name, function):
        try:
            result = function()
            checks.append({"name": name, "status": "PASS", "value": result})
            return result
        except Rejected as e:
            checks.append({"name": name, "status": "FAIL", "reason": str(e)})
            return None
    dt_errors, impulse_errors = [], []
    def dt_check(name, values):
        tested = check(name, lambda: dt_consistency(values, DT))
        if tested is not None:
            dt_errors.append(tested["force_halving_error_N"])
            impulse_errors.append(tested["impulse_error_Ns"])
    dt_check("A/net_dt", [q["net"] for q in contacts["/Cal/A_top"]])
    if c0:
        check("freefall/getter_acceleration", lambda: freefall(a["a"], a["gravity"], series["net_normal_A_world"]))
        check("freefall/velocity_difference_acceleration", lambda: freefall(fd, a["gravity"], series["net_normal_A_world"]))
    else:
        matrix_errors, scalars = [], []
        for path, queries in contacts.items():
            b = bodies[path]
            derivative = acceleration(b["v"], prev[path]["v"], DT)
            angular_derivative = acceleration(b["omega"], prev[path]["omega"], DT)
            check(path+"/getter_low_motion", lambda b=b: low_motion(b["v"], b["omega"], b["a"], b["alpha"]))
            check(path+"/velocity_difference_low_motion", lambda b=b, d=derivative, ad=angular_derivative: low_motion(b["v"], b["omega"], d, ad))
            dt_check(path+"/net_dt", [x["net"] for x in queries])
            for pair in range(len(queries[1]["matrix"])):
                for i, query in enumerate(queries):
                    err = check(path+f"/pair{pair}/query{i}/signed_matrix", lambda q=query, p=pair: detail_matrix_agreement(q["normal"][p]["selected"], q["matrix"][p]))
                    if err is not None and i == 1:
                        matrix_errors.append(err)
                for kind in ("matrix", "normal", "friction"):
                    values = [q[kind][pair] if kind == "matrix" else q[kind][pair]["vector"] for q in queries]
                    dt_check(path+f"/pair{pair}/{kind}_dt", values)
                # Per-slot conversion detects cancelling errors hidden by aggregate forces.
                for slot in queries[1]["normal_raw"]["selected_slot_indices"]:
                    dt_check(path+f"/selected_normal_slot{slot}_dt",
                             [[q["normal_raw"]["forces"][slot][0], 0, 0] for q in queries])
                for slot in queries[1]["friction_raw"]["selected_slot_indices"]:
                    dt_check(path+f"/selected_friction_slot{slot}_dt",
                             [q["friction_raw"]["forces"][slot] for q in queries])
                check(path+f"/pair{pair}/zero_friction", lambda p=pair, q=queries: near(q[1]["friction"][p]["vector"], [0, 0, 0], .0001, label="friction zero"))
            scalars.extend(x["scalar"] for pair in queries[1]["normal"] for x in pair["selected"])
        ab = contacts["/Cal/A_top"][1]; ba = contacts["/Cal/B_bottom"][1]
        series.update({"pair_normal_AB_world": ab["matrix"][0], "pair_normal_BA_world": ba["matrix"][0],
                       "friction_AB_world": ab["friction"][0]["vector"],
                       "matrix_vs_signed_err_N": max(matrix_errors) if matrix_errors else None,
                       "signed_scalar_min": min(scalars) if scalars else None,
                       "selected_negative_count": sum(x < 0 for x in scalars)})
        check("A/mg_support", lambda: static_top(a["mass"], a["a"], a["gravity"], ab["net"], ab["matrix"][0], ab["friction"][0]["vector"]))
        check("A/velocity_difference_Newton_support", lambda: static_top(a["mass"], fd, a["gravity"], ab["net"], ab["matrix"][0], ab["friction"][0]["vector"]))
        check("AB/reciprocal", lambda: reciprocal(ab["matrix"][0], ba["matrix"][0], ab["friction"][0]["vector"], ba["friction"][0]["vector"]))
        # B-ground stays a separate pair. Its normal net is independently checked.
        check("B/net_pair_sum", lambda: near(ba["net"], add(ba["matrix"][0], ba["matrix"][1]),
              max(.01, .02*bodies["/Cal/B_bottom"]["mass"]*norm(a["gravity"])), label="B net separate pairs"))
    series["dt_err_N"] = max(dt_errors) if dt_errors else None
    series["dt_impulse_err_Ns"] = max(impulse_errors) if impulse_errors else None
    return series, checks


def audit_data(header, begin, rows, end, result, expected_header, header_sha):
    require(header.get("schema") == "SignedForceFixtureHeader/1", "header schema")
    case = expected_header["case"]
    require(header["expected_header"] == expected_header and header["case"] == case, "external expected header/case mismatch")
    for key in ("protocol_sha256", "source_release_sha256", "installed_api_pin_sha256", "reader_freeze_sha256"):
        require(header[key] == expected_header[key], "external pin "+key)
    require(expected_header["dt_s"] == DT, "externally frozen dt")
    require(header["model_calls"] == header["training_gpu_hours"] == header["pose_velocity_writes_after_first_controlled_step"] == 0,
            "forbidden training/control writes")
    require(header["physical_device"] == "cpu" and header["no_policy_or_force_or_torque_commands"] is True, "fixture control/device scope")
    require(header["runtime_versions"]["isaac_version"][0] == "5.1.0", "native version")
    c0 = case["id"] == "cal_force_c0_freefall_v03"
    paths = ["/Cal/A_top"] if c0 else ["/Cal/A_top", "/Cal/B_bottom"]
    require(header["fixture_creation_order"] == (["A_top"] if c0 else case["creation_order"]), "fixture creation order")
    require(set(flatten(header["actual_backend_order"]["rigid_body_prim_paths"])) == set(paths), "backend actor membership")
    require(header["actual_backend_order"]["count"] == len(paths) and header["actual_backend_order"]["max_shapes"] == 1,
            "backend actor/shape capacity")
    metadata_check(header, paths, c0)
    inventory_check(header, paths, c0, case)
    origin = header["origin_clock"]
    same_clock(origin, origin, "origin")
    require(origin["native_epoch"] == header["epoch"] ==
            "paperb_signed_force_fixture_calibration_v3:"+case["id"]+":"+expected_header["protocol_sha256"], "epoch/case/protocol")
    require(begin["schema"] == end["schema"] == "SignedForceFixtureBoundary/1", "boundary schema")
    require(begin["phase"] == "BEGIN" and begin["tick"] == -1, "begin boundary")
    same_clock(begin["clock"], origin, "begin")
    require(set(begin["bodies"]) == set(paths), "begin body inventory")
    for p in paths:
        require(begin["bodies"][p].get("usd_inventory") == header["stage_inventory"], "begin body USD inventory")
        observed_body(begin["bodies"][p], p, origin, -1, "TASK_BEGIN")
    require(len(rows) == case["controlled_steps"], "complete fixed controlled steps required")
    previous_sha, previous_clock = header_sha, origin
    inventory_sha = digest(header["stage_inventory"])
    for tick, row in enumerate(rows):
        require(row["schema"] == "SignedForceFixturePOST/1" and row["phase"] == "POST_STEP" and row["tick"] == tick,
                "RAW sequential schema/tick/phase")
        require(row["stage_inventory_sha256"] == inventory_sha, "RAW stage inventory pin")
        require(row.get("stage_inventory") == header["stage_inventory"], "fresh RAW authored inventory drift")
        require(row["previous_record_sha256"] == previous_sha, "RAW hashchain previous")
        unsigned = dict(row); claimed = unsigned.pop("record_sha256")
        require(digest(unsigned) == claimed, "RAW hashchain content")
        same_clock(row["native_clock_before_step"], previous_clock, "step before")
        after = row["native_clock_after_step"]
        same_clock(after, after, "step after")
        require(after["native_epoch"] == origin["native_epoch"] and after["callback_count"] == previous_clock["callback_count"]+1,
                "one real controlled callback")
        require(abs(number(after["time_s"])-number(previous_clock["time_s"])-DT) <= 1e-7, "physical dt clock")
        require(set(row["bodies"]) == set(row["contacts"]) == set(paths), "all-step body/contact inventory")
        for p in paths:
            require(row["bodies"][p].get("usd_inventory") == header["stage_inventory"], "all-step body USD inventory")
            observed_body(row["bodies"][p], p, after, tick, "POST_STEP")
            copied_query(row["contacts"][p], after, p, header["contact_views"][p], c0)
        previous_sha, previous_clock = claimed, after
    require(end["phase"] == "END" and end["tick"] == len(rows), "end boundary")
    same_clock(end["clock"], previous_clock, "end")
    require(end["stage_inventory_unchanged"] is True and end["stage_inventory"] == header["stage_inventory"], "end stage drift")
    require(set(end["bodies"]) == set(paths), "end body inventory")
    for p in paths:
        require(end["bodies"][p].get("usd_inventory") == header["stage_inventory"], "end body USD inventory")
        observed_body(end["bodies"][p], p, previous_clock, len(rows), "TASK_END")
    require(result["schema"] == "SignedForceFixtureWorkerResult/1" and result["status"] == "WORKER_COMPLETE_NOT_PHYSICS_PASS", "worker completion required")
    require(result["case_id"] == case["id"] and result["rows"] == result["controlled_steps"] == len(rows), "result counts")
    require(result["last_record_sha256"] == previous_sha, "result final chain")
    same_clock(result["origin_clock"], origin, "result origin")
    same_clock(result["end_clock"], previous_clock, "result end")
    require(result["S_F_R_admitted"] == 0 and result["robot_load_truth"] == result["chemical_success"] == "UNKNOWN", "worker scientific scope")
    first, last = case["fixed_POST_window_inclusive"]
    require(last-first+1 == 49 and first >= 1 and last == len(rows)-1, "frozen 49-point final window")
    series, checks = [], []
    for tick in range(first, last+1):
        item, tested = measurement(rows[tick], rows[tick-1], header, case)
        series.append(item)
        checks.extend({"tick": tick, **check} for check in tested)
    failed = [item for item in checks if item["status"] == "FAIL"]
    report = {"schema": SCHEMA, "case_id": case["id"],
              "status": "PASS_CONDITIONAL_FIXTURE_CALIBRATION" if not failed else "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT",
              "structure_source_clock": "PASS", "all49_required": True,
              "fixed_window_inclusive": [first, last], "samples": len(series),
              "controlled_steps": len(rows), "checks": checks, "failed_checks": failed,
              "qualification_limits": LIMITS, "S_F_R_admitted": 0,
              "robot_load_truth": "UNKNOWN", "chemical_success": "UNKNOWN",
              "creation_order_mechanism": "NOT_THIS_CASE" if not case["id"].startswith("cal_force_c3") else
                  "INCONCLUSIVE_COMPLETE_BACKEND_SHAPE_ORDER_UNOBSERVED"}
    return report, {"schema": "SignedForceFixtureAuditedSeries/1", "case_id": case["id"],
                    "measurement_scope": LIMITS[0], "rows": series}


def compare_reference(report, series, header, reference_report, reference_series, reference_header):
    case = report["case_id"]
    if not (case.startswith("cal_force_c3") or case.startswith("cal_force_c4")):
        return
    require(reference_report["case_id"] == reference_series["case_id"] == reference_header["case"]["id"] == "cal_force_c1_stack_v03",
            "cross-case baseline must be C1")
    if reference_report["status"] != "PASS_CONDITIONAL_FIXTURE_CALIBRATION":
        report["cross_case_status"] = "UNKNOWN_BASELINE_NOT_QUALIFIED"
        return
    require(len(reference_series["rows"]) == len(series["rows"]) == 49, "cross-case fixed window")
    cross = []
    for now, base in zip(series["rows"], reference_series["rows"]):
        require(now["tick"] == base["tick"] and now["gravity_world"] == base["gravity_world"], "cross-case matched tick/gravity")
        ratio = now["mass_A_kg"]/base["mass_A_kg"]
        require(abs(ratio-(2 if case.startswith("cal_force_c4") else 1)) <= 1e-6, "cross-case actual mass ratio")
        try:
            error = near(now["pair_normal_AB_world"], scale(base["pair_normal_AB_world"], ratio),
                         max(.01, .02*now["mass_A_kg"]*norm(now["gravity_world"])), label="cross-case support invariance/scaling")
            cross.append({"tick": now["tick"], "status": "PASS", "force_error_N": error})
        except Rejected as e:
            cross.append({"tick": now["tick"], "status": "FAIL", "reason": str(e)})
    report["cross_case_checks"] = cross
    report["cross_case_status"] = "PASS" if all(x["status"] == "PASS" for x in cross) else "FAIL"
    if report["cross_case_status"] == "FAIL":
        report["status"] = "FAIL_CONDITIONAL_FIXTURE_MEASUREMENT"
    if case.startswith("cal_force_c3"):
        report["actual_actor_order_proxy_changed"] = header["actual_backend_order"]["rigid_body_prim_paths"] != reference_header["actual_backend_order"]["rigid_body_prim_paths"]
        # The installed public API does not expose complete backend shape order.
        report["creation_order_mechanism"] = "INCONCLUSIVE_COMPLETE_BACKEND_SHAPE_ORDER_UNOBSERVED"


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--request", required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--reader-freeze-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    require(sha(args.request) == args.request_sha256, "external root request digest")
    freeze_path = HERE / "PROSPECTIVE_READER_FREEZE.json"
    require(sha(freeze_path) == args.reader_freeze_sha256, "external reader freeze digest")
    freeze = read_json(freeze_path)
    for name, pin in freeze["files"].items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and sha(HERE/name) == pin["sha256"], "reader source drift")
    request = read_json(args.request)
    require(request.get("schema") == "SignedForceFixtureROOTTerminalAuditRequest/3" and
            request.get("authorization") == "ROOT_TERMINAL_NOTIFICATION_ONE_ACTUAL_READ_PER_CASE" and
            request.get("reader_freeze_sha256") == args.reader_freeze_sha256, "ROOT terminal notification required")
    out = Path(args.output); out.mkdir(parents=True, exist_ok=False)
    def write(name, value):
        with (out/name).open("x") as f:
            f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")
    write("AUDIT_STARTED.json", {"request_sha256": args.request_sha256, "reader_freeze_sha256": args.reader_freeze_sha256,
                                "case_id": request["case_id"], "one_actual_read": True})
    report = {"schema": SCHEMA, "case_id": request["case_id"], "status": "UNKNOWN_REJECTED_SOURCE_OR_RAW",
              "qualification_limits": LIMITS, "S_F_R_admitted": 0, "robot_load_truth": "UNKNOWN", "chemical_success": "UNKNOWN"}
    try:
        inputs = request["files"]
        expected = request["expected_header"]
        require(set(inputs) == {"HEADER.json", "BEGIN.json", "RAW_POST.jsonl", "END.json", "RESULT.json",
                "LIFECYCLE.jsonl", "WORKER_TERMINAL.json", "SOURCE_RELEASE.json", "INSTALLED_API_PIN.json",
                "ROOT_ADMISSION.json", "SOURCE_REVIEW.json", "CONTACT_PROCESSING_INSTALL_BEFORE_RESET.json"},
                "exact twelve externally pinned terminal inputs")
        require(expected["maximum_new_distinct_epochs"] == 6 and expected["closed_old_family_cap"] == 3 and
                expected["family_budget"] == {"calibration_family_cumulative_upper_bound": 9,
                    "closed_calibration_actual_epochs_before_v03": 3, "closed_old_M0_M1_M2_family_cap": 3,
                    "closed_v01_actual_epochs": 1, "closed_v02_actual_epochs": 2,
                    "max_controlled_steps_v03": 5365, "negative_controls": 1,
                    "no_seventh_implicit_epoch": True, "positive_fixtures": 5,
                    "separate_shutdown_diagnostic_actual_epochs": 1, "v01_remaining_NOT_EXECUTED": 4,
                    "v02_remaining_NOT_EXECUTED": 3, "v03_maximum_distinct_epochs": 6},
                "prospective separate family caps/closed cases retained")
        budget = expected["prospective_budget_confirmation"]
        require(budget["status"] == "ROOT_CONFIRMED_BEFORE_V03_OUTCOMES" and
                budget["sha256"] == "8a9a74a00493454db0cbf54d2c0e4132ed3f3ddc528767ecd6daf646c0d004b9" and
                sha(budget["path"]) == budget["sha256"], "prospective six-case ordered root selection")
        candidate = expected["cleanup_candidate"]
        require(candidate["condition"] == "ONLY_AFTER_COMPLETE_END_AND_RESULT_FSYNC_OWNED_CONTEXT_MATCH" and
                candidate["default_app_close_args"] == [] and candidate["default_app_close_kwargs"] == {} and
                candidate["no_physics_getters_after_clear_instance"] is True and
                candidate["no_task_callbacks_cleared"] is True and candidate["timeout_termination_unchanged"] == [300, 30],
                "owned public release only after completed measurement/default close preserved")
        for name, pin in inputs.items():
            require(sha(pin["path"]) == pin["sha256"], "ROOT terminal input hash "+name)
        for filename, expected_key in (("SOURCE_RELEASE.json", "source_release_sha256"),
                                       ("INSTALLED_API_PIN.json", "installed_api_pin_sha256")):
            require(inputs[filename]["sha256"] == request["expected_header"][expected_key], "source/API release external binding")
        release = read_json(inputs["SOURCE_RELEASE.json"]["path"])
        require(release.get("schema") == "SignedForceFixtureV03ExecutionRelease/1" and
                release.get("maximum_distinct_native_epochs") == 6 and
                release.get("maximum_native_controlled_steps_total") == 5365 and
                release.get("default_close_and_terminal_clear_unchanged_v02") is True,
                "bounded V03 source release/default close contract")
        source_root = Path(inputs["SOURCE_RELEASE.json"]["path"]).parent
        for name, pin in release["files"].items():
            require(not Path(name).is_absolute() and ".." not in Path(name).parts and
                    sha(source_root/name) == pin, "collector source unchanged before read")
        api_pin = read_json(inputs["INSTALLED_API_PIN.json"]["path"])
        for pin in api_pin["files"].values():
            require(sha(pin["path"]) == pin["sha256"], "installed API source unchanged before read")
        header = read_json(inputs["HEADER.json"]["path"])
        begin = read_json(inputs["BEGIN.json"]["path"])
        end = read_json(inputs["END.json"]["path"])
        result = read_json(inputs["RESULT.json"]["path"])
        terminal = read_json(inputs["WORKER_TERMINAL.json"]["path"])
        require(terminal.get("status") == "COMPLETE" and terminal.get("exit_code") == 0 and
                terminal.get("timed_out") is False and terminal.get("formal_episode_started") is True and
                terminal.get("owned_process_group_empty") is True and terminal.get("remaining_owned_process_ids") == [] and
                terminal.get("foreign_processes_signaled") is False and terminal.get("gpu_global_configuration_changes") is False and
                terminal.get("model_calls") == terminal.get("training_gpu_hours") == 0 and
                terminal.get("case_id") == request["case_id"], "owned native lifecycle/cleanup terminal")
        lifecycle_path = Path(inputs["LIFECYCLE.jsonl"]["path"])
        require(not lifecycle_path.is_symlink() and lifecycle_path.stat().st_size <= 4*1024*1024, "cleanup lifecycle input bounds")
        cleanup = verify_cleanup([parse(line) for line in lifecycle_path.read_text().splitlines() if line],
                                 result, Path(inputs["RESULT.json"]["path"]).stat().st_size)
        cleanup["default_close_exit_scope"] = "EXIT0_AFTER_PRE_CLOSE_MARKERS" if cleanup["default_close_python_return"] == "UNKNOWN_NO_AFTER_APP_CLOSE_MARKER" else "EXIT0_WITH_OBSERVED_PYTHON_RETURN"
        raw_path = Path(inputs["RAW_POST.jsonl"]["path"])
        require(not raw_path.is_symlink() and raw_path.stat().st_size <= 512*1024*1024, "RAW bound")
        rows = []
        with raw_path.open() as f:
            for line in f:
                require(len(line) <= 16*1024*1024, "RAW line bound")
                rows.append(parse(line))
                require(len(rows) <= 1049, "RAW controlled row bound")
        for name in ("HEADER", "BEGIN", "END", "RAW_POST"):
            filename = name+(".jsonl" if name == "RAW_POST" else ".json")
            require(result[name+"_sha256"] == inputs[filename]["sha256"], "RESULT readback hash "+name)
        require(header["root_admission_sha256"] == request["root_admission_sha256"] and
                header["source_review_sha256"] == request["source_review_sha256"], "external root/review header binding")
        require(inputs["ROOT_ADMISSION.json"]["sha256"] == request["root_admission_sha256"] and
                inputs["SOURCE_REVIEW.json"]["sha256"] == request["source_review_sha256"], "root/review actual artifacts")
        admission = read_json(inputs["ROOT_ADMISSION.json"]["path"])
        review = read_json(inputs["SOURCE_REVIEW.json"]["path"])
        require(admission.get("expected_header") == request["expected_header"] and
                admission.get("case_id") == request["case_id"] and
                admission.get("status") == "ADMITTED_ONE_SIGNED_FORCE_FIXTURE_CALIBRATION_V03_CASE", "actual root admission")
        require(review.get("status") == "PASS_PROSPECTIVE_SIGNED_FORCE_CALIBRATION_V03_SOURCE_REVIEW" and
                review.get("source_release_sha256") == request["expected_header"]["source_release_sha256"] and
                review.get("reader_freeze_sha256") == args.reader_freeze_sha256, "actual source review")
        install = read_json(inputs["CONTACT_PROCESSING_INSTALL_BEFORE_RESET.json"]["path"])
        processing = validate_processing(header, begin, rows, end, install)
        report, series = audit_data(header, begin, rows, end, result, request["expected_header"], inputs["HEADER.json"]["sha256"])
        report["contact_processing_readback"] = processing
        report["cleanup_lifecycle"] = cleanup
        report["family_accounting"] = {"v03_batch_max_new_epochs": 6, "force_fixture_cumulative_max_including_closed_v01_v02": 9,
                                       "closed_v01_actual_epochs": 1, "closed_v02_actual_epochs": 2,
                                       "prior_v01_remaining_not_executed": 4, "prior_v02_remaining_not_executed": 3,
                                       "separate_shutdown_diagnostic_epochs": 1, "separate_closed_M0_M1_M2_family_epochs": 3,
                                       "negative_control_cases": 1, "positive_fixture_cases": 5}
        require(report["case_id"] == request["case_id"], "request actual case")
        if report["case_id"].startswith(("cal_force_c3", "cal_force_c4")):
            reference = request.get("reference")
            if reference is None:
                report["cross_case_status"] = "UNKNOWN_BASELINE_NOT_PROVIDED"
            else:
                for pin in reference.values():
                    require(sha(pin["path"]) == pin["sha256"], "cross-case external hash")
                baseline_report = read_json(reference["REPORT.json"]["path"])
                require(baseline_report.get("series_sha256") == reference["AUDITED_SERIES.json"]["sha256"] and
                        baseline_report.get("reader_freeze_sha256") == args.reader_freeze_sha256,
                        "baseline prospective audit/series binding")
                compare_reference(report, series, header, baseline_report,
                                  read_json(reference["AUDITED_SERIES.json"]["path"]), read_json(reference["HEADER.json"]["path"]))
        classify_measurement_role(report, header["case"])
        series["measurement_role"] = header["case"]["measurement_role"]
        write("AUDITED_SERIES.json", series)
        report["series_sha256"] = sha(out/"AUDITED_SERIES.json")
        report["diagnostic_series_is_qualification"] = False
        report["input_files"] = inputs
    except (Rejected, ValueError, KeyError, TypeError, IndexError, OSError) as exc:
        report.update({"status": "UNKNOWN_REJECTED_SOURCE_OR_RAW", "rejection_type": type(exc).__name__, "reason": str(exc),
                       "series_emitted": False})
    report["request_sha256"] = args.request_sha256
    report["reader_freeze_sha256"] = args.reader_freeze_sha256
    write("REPORT.json", report)
    print(json.dumps({"status": report["status"], "case_id": request["case_id"],
                      "report_sha256": sha(out/"REPORT.json"), "series_sha256": report.get("series_sha256")}, sort_keys=True))
    return 0 if report["status"] == "PASS_CONDITIONAL_FIXTURE_CALIBRATION" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Rejected, ValueError, KeyError, TypeError, OSError) as exc:
        print("PROSPECTIVE_READER_REFUSED: "+str(exc), file=sys.stderr)
        sys.exit(3)
