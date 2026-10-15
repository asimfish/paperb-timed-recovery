"""Read-only adapter for an already running, externally owned Isaac scene.

This module imports no physics SDK and cannot create/reset/advance a scene. The
caller injects the existing RigidBodyView, SimulationView, and RigidObject. Its
clock reader must return native_epoch, time_s, and callback_count from the same
existing scene. SDK arrays are copied to ordinary JSON values immediately.

This is reviewed trusted-adapter code, not a hostile-Python sandbox. It reports
observations and missing getters; it NEVER assigns a load-bearing success label.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

SCHEMA = "paperb-handoff-physical-snapshot-v1"
PHASES = ("PRE_WRITE", "POST_STEP", "TASK_BEGIN", "TASK_END")
BODY_GETTERS = {
    "transform_xyz_xyzw": "get_transforms",
    "velocity_world_com_linear_angular": "get_velocities",
    "acceleration_world_com_linear_angular": "get_accelerations",
    "mass_kg": "get_masses",
    "inverse_mass_per_kg": "get_inv_masses",
    "com_local_xyz_xyzw": "get_coms",
    "inertia_com_body_frame_column_major_kg_m2": "get_inertias",
    "gravity_disabled_flag": "get_disable_gravities",
    "simulation_disabled_flag": "get_disable_simulations",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def plain(value):
    """Copy SDK values; None stays None. No synthetic zero or NaN substitution."""
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite observed numeric value")
        return value
    if type(value) in (list, tuple):
        return [plain(v) for v in value]
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise TypeError("JSON object keys must be plain strings")
        return {k: plain(v) for k, v in value.items()}
    # Actual existing torch frontend. Conversion is immediate, before another
    # getter can reuse its backend buffer. Never retain a live tensor reference.
    if hasattr(value, "detach"):
        return plain(value.detach().cpu().tolist())
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    # SimulationView.get_gravity returns a carb.Float3, not a tensor.
    if all(hasattr(value, name) for name in ("x", "y", "z")):
        return [plain(float(value.x)), plain(float(value.y)), plain(float(value.z))]
    raise TypeError("unsupported SDK value type: " + type(value).__name__)


def observed(getter):
    try:
        value = plain(getter())
        if value is None:
            return {"status": "UNKNOWN", "value": None, "reason": "GETTER_RETURNED_NONE"}
        return {"status": "OBSERVED", "value": value}
    except Exception as exc:
        return {"status": "UNKNOWN", "value": None,
                "reason": "GETTER_EXCEPTION", "exception_type": type(exc).__name__,
                "exception_message": str(exc)}


def _clock(clock_read):
    value = plain(clock_read())
    if type(value) is not dict or set(value) != {"native_epoch", "time_s", "callback_count"}:
        raise ValueError("native clock must contain exactly epoch/time/callback_count")
    if type(value["native_epoch"]) is not str or not value["native_epoch"]:
        raise ValueError("missing native epoch")
    if type(value["time_s"]) not in (float, int) or isinstance(value["time_s"], bool):
        raise ValueError("time must be a finite plain number")
    if type(value["callback_count"]) is not int or value["callback_count"] < 0:
        raise ValueError("callback count must be a nonnegative plain integer")
    return value


def _wrench(composer):
    return {
        "active": plain(composer.active),
        "force_body_frame_N": plain(composer.composed_force_as_torch),
        "torque_body_frame_N_m": plain(composer.composed_torque_as_torch),
    }


def capture_snapshot(*, body_view, simulation_view, rigid_object, clock_read,
                     tick, phase, body_path, usd_inventory=None):
    """Capture getters only, including composer values BEFORE write/clear.

    Root must call PRE_WRITE before scene.write_data_to_sim(), and POST_STEP
    after sim.step()/scene.update(). TASK_BEGIN/END are endpoint readbacks.
    Missing getters are retained as UNKNOWN; failure of the native clock itself
    raises and must be retained by the caller's terminal exception logger.
    """
    if type(tick) is not int or type(phase) is not str or phase not in PHASES:
        raise ValueError("invalid tick/phase")
    if type(body_path) is not str or not body_path.startswith("/"):
        raise ValueError("invalid body prim path")
    before = _clock(clock_read)
    fields = {name: observed(lambda method=method: getattr(body_view, method)())
              for name, method in BODY_GETTERS.items()}
    gravity = observed(lambda: simulation_view.get_gravity())
    wrenches = {
        "instantaneous": observed(lambda: _wrench(rigid_object.instantaneous_wrench_composer)),
        "permanent": observed(lambda: _wrench(rigid_object.permanent_wrench_composer)),
    }
    after = _clock(clock_read)
    row = {
        "schema": SCHEMA, "tick": tick, "phase": phase, "body_path": body_path,
        "native_clock_before": before, "native_clock_after": after,
        "no_native_step_during_getters": before == after,
        "rigid_body": fields, "scene_gravity_world_m_s2": gravity,
        "external_wrench_buffers": wrenches,
        "external_wrench_buffer_role": "PRE_WRITE_IS_INPUT_TO_NEXT_WRITE;POST_STEP_MAY_ALREADY_BE_CLEARED",
        "usd_inventory": plain(usd_inventory),
        "backend_constraint_inventory_status": "UNKNOWN_NO_COMPLETE_INSTALLED_GETTER",
        "active_kinematic_flag_status": "UNKNOWN_NO_INSTALLED_TENSOR_GETTER",
        "load_bearing_verdict": "UNKNOWN_INSTRUMENTATION_ONLY",
    }
    row["record_sha256"] = digest(row)
    return row


class WriteOnceJSONL:
    """One exclusive output, no append/resume into an existing epoch file."""
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("x", encoding="utf-8")
        self.epoch = None
        self.last_tick = None
        self.rows = 0

    def write(self, row):
        from physical_validate import validate_snapshot
        report = validate_snapshot(row)
        if not report["structure_pass"]:
            raise ValueError("invalid snapshot: " + canonical(report))
        epoch = row["native_clock_before"]["native_epoch"]
        if self.epoch is not None and epoch != self.epoch:
            raise ValueError("cross-epoch output is forbidden")
        if self.last_tick is not None and row["tick"] < self.last_tick:
            raise ValueError("tick regression")
        self.epoch, self.last_tick = epoch, row["tick"]
        self.file.write(canonical(row) + "\n")
        self.file.flush()
        self.rows += 1

    def close(self):
        self.file.close()
