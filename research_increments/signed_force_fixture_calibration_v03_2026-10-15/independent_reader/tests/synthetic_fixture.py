"""Clearly synthetic ideal Newton fixtures; never native calibration evidence."""
import copy
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code"))
from audit_fixture import DT, digest

AP = "/Cal/A_top"
BP = "/Cal/B_bottom"
GP = "/Cal/ground/geometry/mesh"


def observed(value):
    return {"status": "OBSERVED", "value": value}


def getter(value, clock):
    return {"status": "OBSERVED", "value": value, "clock_before": clock,
            "clock_after": clock, "no_step_during_getter": True, "reason": None}


def body(path, tick, phase, clock, mass, gravity, moving=False):
    t = clock["time_s"]
    velocity = [x*t for x in gravity] if moving else [0, 0, 0]
    accel = gravity if moving else [0, 0, 0]
    values = {
        "mass_kg": [[mass]], "inverse_mass_per_kg": [[1/mass]],
        "gravity_disabled_flag": [0], "simulation_disabled_flag": [0],
        "transform_xyz_xyzw": [[0, 0, 2, 0, 0, 0, 1]],
        "velocity_world_com_linear_angular": [velocity+[0, 0, 0]],
        "acceleration_world_com_linear_angular": [list(accel)+[0, 0, 0]],
        "com_local_xyz_xyzw": [[0, 0, 0, 0, 0, 0, 1]],
        "inertia_com_body_frame_column_major_kg_m2": [[1, 0, 0, 0, 1, 0, 0, 0, 1]],
    }
    wrench = observed({"active": False, "force_body_frame_N": [[[0, 0, 0]]],
                       "torque_body_frame_N_m": [[[0, 0, 0]]]})
    out = {"schema": "paperb-handoff-physical-snapshot-v1", "body_path": path,
        "tick": tick, "phase": phase, "native_clock_before": clock, "native_clock_after": clock,
        "no_native_step_during_getters": True, "rigid_body": {k: observed(v) for k, v in values.items()},
        "scene_gravity_world_m_s2": observed(gravity),
        "external_wrench_buffers": {"instantaneous": wrench, "permanent": copy.deepcopy(wrench)}}
    out["record_sha256"] = digest(out)
    return out


def selected_detail(vectors, dt, kind, negative_first=False):
    n = len(vectors)
    names = ["forces", "points", "normals", "separations"] if kind == "normal" else ["forces", "points"]
    detail = {"capacity": 128, "counts": [[1]*n], "starts": [list(range(n))],
        "selected_slot_indices": list(range(n)), "capacity_saturated": False,
        "unused_slot_policy": "NULL_MARKER_NOT_READ_NOT_ZERO_IMPUTED",
        "buffer_shapes": {"forces": [128, 1] if kind == "normal" else [128, 3],
                          "points": [128, 3], "counts": [1, n], "starts": [1, n]}}
    if kind == "normal":
        detail["buffer_shapes"].update({"normals": [128, 3], "separations": [128, 1]})
    for name in names:
        detail[name] = [None]*128
    for i, vec in enumerate(vectors):
        detail["points"][i] = [0, 0, .1]
        if kind == "normal":
            mag = math.sqrt(sum(x*x for x in vec))
            sign = -1 if negative_first and i == 0 else 1
            detail["forces"][i] = [sign*mag*DT/dt]
            detail["normals"][i] = [sign*x/mag for x in vec]
            detail["separations"][i] = [0]
        else:
            detail["forces"][i] = [x*DT/dt for x in vec]
    detail["copied_payload_sha256"] = digest(detail)
    return detail


def fixture(index=1):
    c0 = index == 0
    mass = .2 if index == 4 else .1
    gravity = [-9.81, 0, 0] if index == 2 else [0, 0, -9.81]
    case_id = f"cal_force_c{index}_"+({0:"freefall", 1:"stack", 2:"rotated", 3:"actor_order", 4:"mass"}[index])+"_v03"
    count, window = (120, [71, 119]) if c0 else (1049, [1000, 1048])
    order = ["A_top"] if c0 else (["A_top", "B_bottom"] if index == 3 else ["B_bottom", "A_top"])
    case = {"id": case_id, "controlled_steps": count, "fixed_POST_window_inclusive": window,
            "mass_A_kg": mass, "gravity_world_m_s2": gravity}
    if not c0:
        case.update({"mass_B_kg": .2, "creation_order": order})
    epoch = "paperb_signed_force_fixture_calibration_v3:"+case_id+":"+"1"*64
    clock = lambda tick: {"native_epoch": epoch, "time_s": (tick+1)*DT, "callback_count": tick+1}
    origin = clock(-1)
    paths = [AP] if c0 else [AP, BP]
    expected = {"case": case, "protocol_sha256": "1"*64, "source_release_sha256": "2"*64,
                "installed_api_pin_sha256": "3"*64, "reader_freeze_sha256": "4"*64, "dt_s": DT}
    inventory = {"meters_per_unit": 1, "kilograms_per_unit": 1, "joints": [],
        "colliders": [{"path": p+"/geometry/mesh" if p != GP else p, "collision_enabled": True} for p in paths+([] if c0 else [GP])],
        "materials": [{"path": p+"/geometry/material", "static_friction": 0, "dynamic_friction": 0, "restitution": 0}
                      for p in paths+([] if c0 else ["/Cal/ground"])],
        "rigid_bodies": [{"path": p, "rigid_body_enabled": True, "kinematic_enabled": False, "disable_gravity": False,
            "linear_damping": 0, "angular_damping": 0, "sleep_threshold": 0, "contact_report_threshold": 0,
            "authored_mass_kg": mass if p == AP else .2} for p in paths]}
    metadata = {}
    for p in paths:
        filters = [] if c0 else ([BP] if p == AP else [AP, GP])
        metadata[p] = {"sensor_paths": [p], "filter_paths": [filters], "sensor_count": 1,
            "filter_count": len(filters), "max_contact_data_count": 128, "check": True,
            "requested_sensor_path": p, "requested_filter_paths": filters}
    setup = {p: {"prim_paths": [p], "max_shapes": 1,
        "material_properties_static_dynamic_restitution": getter([[[0, 0, 0]]], origin),
        "contact_offsets": getter([[.001]], origin), "rest_offsets": getter([[0]], origin)} for p in paths}
    header = {"schema": "SignedForceFixtureHeader/1", "case": case, **{k:v for k,v in expected.items() if k != "dt_s"},
        "expected_header": expected, "epoch": epoch, "origin_clock": origin, "stage_inventory": inventory,
        "fixture_creation_order": order, "actual_backend_order": {"rigid_body_prim_paths": ["/Cal/"+x for x in order],
            "count": len(paths), "max_shapes": 1, "complete_backend_shape_order": "UNKNOWN_NO_INSTALLED_PUBLIC_GETTER"},
        "contact_views": metadata, "fixture_setup_readback": setup,
        "runtime_versions": {"isaac_version": ["5.1.0"]}, "model_calls": 0, "training_gpu_hours": 0,
        "pose_velocity_writes_after_first_controlled_step": 0, "physical_device": "cpu", "no_policy_or_force_or_torque_commands": True}
    get_bodies = lambda tick, phase: {p: body(p, tick, phase, clock(tick), mass if p == AP else .2, gravity, c0) for p in paths}
    begin = {"schema": "SignedForceFixtureBoundary/1", "phase": "BEGIN", "tick": -1, "clock": origin, "bodies": get_bodies(-1, "TASK_BEGIN")}
    for b in begin["bodies"].values():
        b["usd_inventory"] = inventory
        b.pop("record_sha256"); b["record_sha256"] = digest(b)
    rows = []
    header_sha = "5"*64
    previous = header_sha
    for tick in range(count):
        after = clock(tick)
        contacts = {}
        for p in paths:
            queries = []
            for qdt in (1.0, DT, 2*DT):
                if c0:
                    net = [0, 0, 0]
                    q = {"unconfigured_channels": ["matrix_normal", "normal_detail", "friction_detail"],
                         "channel_scope": "INTENTIONALLY_NOT_CONFIGURED_FREEFALL"}
                else:
                    up = [-x/9.81 for x in gravity]
                    vectors = [[x*mass*9.81 for x in up]] if p == AP else [[-x*mass*9.81 for x in up], [x*(mass+.2)*9.81 for x in up]]
                    net = [sum(v[a] for v in vectors)*DT/qdt for a in range(3)]
                    q = {"matrix_normal": getter([[[x*DT/qdt for x in v] for v in vectors]], after),
                         "normal_detail": getter(selected_detail(vectors, qdt, "normal", negative_first=True), after),
                         "friction_detail": getter(selected_detail([[0, 0, 0] for _ in vectors], qdt, "friction"), after)}
                q.update({"query_dt_s": qdt, "net_normal": getter([net], after),
                          "clock_before": after, "clock_after": after, "no_step_during_query": True})
                queries.append(q)
            contacts[p] = {"metadata": metadata[p], "queries": queries}
        row = {"schema": "SignedForceFixturePOST/1", "phase": "POST_STEP", "tick": tick,
            "native_clock_before_step": clock(tick-1), "native_clock_after_step": after,
            "bodies": get_bodies(tick, "POST_STEP"), "contacts": contacts,
            "stage_inventory": inventory, "stage_inventory_sha256": digest(inventory), "previous_record_sha256": previous}
        for b in row["bodies"].values():
            b["usd_inventory"] = inventory
            b.pop("record_sha256"); b["record_sha256"] = digest(b)
        row["record_sha256"] = digest(row); previous = row["record_sha256"]
        rows.append(row)
    end = {"schema": "SignedForceFixtureBoundary/1", "phase": "END", "tick": count,
        "clock": clock(count-1), "bodies": {p: body(p, count, "TASK_END", clock(count-1), mass if p == AP else .2, gravity, c0) for p in paths},
        "stage_inventory": inventory, "stage_inventory_unchanged": True}
    for b in end["bodies"].values():
        b["usd_inventory"] = inventory
        b.pop("record_sha256"); b["record_sha256"] = digest(b)
    result = {"schema": "SignedForceFixtureWorkerResult/1", "status": "WORKER_COMPLETE_NOT_PHYSICS_PASS", "case_id": case_id,
        "rows": count, "controlled_steps": count, "last_record_sha256": previous, "origin_clock": origin,
        "end_clock": clock(count-1), "S_F_R_admitted": 0, "robot_load_truth": "UNKNOWN", "chemical_success": "UNKNOWN"}
    return header, begin, rows, end, result, expected, header_sha


def rehash(data):
    header, begin, rows, end, result, expected, header_sha = data
    previous = header_sha
    for row in rows:
        row["previous_record_sha256"] = previous
        for snapshot in row["bodies"].values():
            snapshot.pop("record_sha256", None); snapshot["record_sha256"] = digest(snapshot)
        for contact in row["contacts"].values():
            for query in contact["queries"]:
                for key in ("normal_detail", "friction_detail"):
                    if key in query and query[key]["value"] is not None:
                        payload = query[key]["value"]
                        payload.pop("copied_payload_sha256", None)
                        payload["copied_payload_sha256"] = digest(payload)
        row.pop("record_sha256", None); row["record_sha256"] = digest(row); previous = row["record_sha256"]
    result["last_record_sha256"] = previous
    return data
