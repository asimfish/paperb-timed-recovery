"""One new native fixture epoch. No control policy, scoring, reset or retry."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time
import traceback
import faulthandler
import sys

from execution_gate import child_source_gate, sha
from capture_raw import canonical, plain, observed, query_contact, sha_value
from physical_capture import capture_snapshot
from contact_processing_setting import install_processing_setting, read_processing_setting
from lifecycle_observer import LifecycleObserver, readonly_replicator_observations

gate, admission = child_source_gate()
parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument('--root', required=True)
parser.add_argument('--case', required=True)
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
root = Path(args.root).resolve()
protocol = json.loads((root / 'protocol.json').read_text())
case = next(c for c in protocol['cases'] if c['id'] == args.case)
out = root / 'cases' / args.case
out.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
app = None
raw_file = None
rows = 0
end_fsynced = False
result_fsynced = False
lifecycle = LifecycleObserver(out / "LIFECYCLE.jsonl", case_id=args.case, process_start_monotonic=started)


def record(name, value):
    with (out / name).open('x') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
        f.flush(); os.fsync(f.fileno())


try:
    record('SOURCE_GATE.json', gate)
    lifecycle.mark('BEFORE_APP_START', clock_read=None)
    app = AppLauncher(dict(vars(args))).app
    lifecycle.mark('AFTER_APP_START', clock_read=None)
    import omni.usd
    import carb
    import omni.kit.app
    from pxr import UsdGeom, UsdPhysics, PhysxSchema
    import isaaclab.sim as sim_utils
    from isaaclab.assets import RigidObject, RigidObjectCfg
    from isaacsim.core.version import get_version
    version = get_version()
    manager = omni.kit.app.get_app().get_extension_manager()
    physx_id = manager.get_enabled_extension_id('omni.physx')
    if version[0] != '5.1.0' or not physx_id:
        raise RuntimeError('UNEXPECTED_RUNTIME_VERSION')
    dt = protocol['dt_s']
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=dt, gravity=tuple(case['gravity_world_m_s2']),
        device='cpu', use_fabric=True, physx=sim_utils.PhysxCfg(solver_type=1,
        max_position_iteration_count=32, max_velocity_iteration_count=4, enable_ccd=True)))
    processing_settings = carb.settings.get_settings()
    processing_install = install_processing_setting(processing_settings, case['contact_processing_disabled_requested'])
    record('CONTACT_PROCESSING_INSTALL_BEFORE_RESET.json', processing_install)
    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    UsdGeom.Xform.Define(stage, '/Cal')
    theta = case.get('fixture_rotation_about_world_Y_rad', 0.0)
    quat = (math.cos(theta / 2), 0.0, math.sin(theta / 2), 0.0)
    def rotated(position):
        x, y, z = position
        return (math.cos(theta) * x + math.sin(theta) * z, y,
                -math.sin(theta) * x + math.cos(theta) * z)
    friction = sim_utils.RigidBodyMaterialCfg(static_friction=0.0, dynamic_friction=0.0,
        restitution=0.0, friction_combine_mode='average', restitution_combine_mode='average')
    collision = sim_utils.CollisionPropertiesCfg(collision_enabled=True, contact_offset=0.001, rest_offset=0.0,
        torsional_patch_radius=0.0, min_torsional_patch_radius=0.0)
    freefall = case['fixture_reference_case_id'] == 'cal_force_c0_freefall_v01'
    creation_order = ['A_top'] if freefall else case['creation_order']
    bodies = {}
    if not freefall:
        ground_cfg = sim_utils.CuboidCfg(size=(2.0, 2.0, 0.1), collision_props=collision,
            physics_material=friction, rigid_props=None)
        ground_cfg.func('/Cal/ground', ground_cfg, translation=rotated((0.0, 0.0, -0.05)), orientation=quat)
    for name in creation_order:
        side = 0.05 if name == 'A_top' else 0.1
        mass = case['mass_A_kg'] if name == 'A_top' else case['mass_B_kg']
        position = (0.0, 0.0, 2.0) if freefall else rotated((0.0, 0.0, 0.125 if name == 'A_top' else 0.05))
        cfg = RigidObjectCfg(prim_path='/Cal/' + name,
            spawn=sim_utils.CuboidCfg(size=(side, side, side), collision_props=collision,
                mass_props=sim_utils.MassPropertiesCfg(mass=mass), physics_material=friction,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(rigid_body_enabled=True, kinematic_enabled=False,
                    disable_gravity=False, linear_damping=0.0, angular_damping=0.0, sleep_threshold=0.0,
                    stabilization_threshold=0.0, solver_position_iteration_count=32,
                    solver_velocity_iteration_count=4, retain_accelerations=True)),
            init_state=RigidObjectCfg.InitialStateCfg(pos=position, rot=quat))
        bodies['/Cal/' + name] = RigidObject(cfg)
        PhysxSchema.PhysxContactReportAPI.Apply(stage.GetPrimAtPath('/Cal/' + name)).CreateThresholdAttr(0.0)
    callback = {'count': 0, 'last_dt': None}
    def on_physics(value):
        callback['count'] += 1; callback['last_dt'] = float(value)
    sim.reset()
    for body in bodies.values():
        body.reset()
    sim.add_physics_callback('paperb_fixture_calibration_count', on_physics)
    simulation_view = next(iter(bodies.values()))._physics_sim_view
    epoch = 'paperb_signed_force_fixture_calibration_v3:' + args.case + ':' + sha(root / 'protocol.json')
    def clock():
        return {'native_epoch': epoch, 'time_s': float(sim.current_time), 'callback_count': callback['count']}
    origin = clock()
    def usd_inventory():
        inventory = {'scope': 'COMPOSED_USD_ONLY_NOT_COMPLETE_ACTIVE_BACKEND_CONSTRAINTS',
            'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage),
            'kilograms_per_unit': UsdPhysics.GetStageKilogramsPerUnit(stage),
            'colliders': [], 'rigid_bodies': [], 'joints': [], 'materials': [],
            'backend_constraint_inventory_status': 'UNKNOWN_NO_COMPLETE_INSTALLED_GETTER'}
        for prim in stage.Traverse():
            path = str(prim.GetPath())
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                inventory['colliders'].append({'path': path, 'type': prim.GetTypeName(),
                    'collision_enabled': UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get(),
                    'all_authored_attributes': {a.GetName(): str(a.Get()) for a in prim.GetAttributes() if a.HasAuthoredValueOpinion()}})
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                body_api = UsdPhysics.RigidBodyAPI(prim); px = PhysxSchema.PhysxRigidBodyAPI(prim)
                report = PhysxSchema.PhysxContactReportAPI(prim)
                inventory['rigid_bodies'].append({'path': path,
                    'rigid_body_enabled': body_api.GetRigidBodyEnabledAttr().Get(),
                    'kinematic_enabled': body_api.GetKinematicEnabledAttr().Get(),
                    'disable_gravity': px.GetDisableGravityAttr().Get(),
                    'linear_damping': px.GetLinearDampingAttr().Get(),
                    'angular_damping': px.GetAngularDampingAttr().Get(),
                    'sleep_threshold': px.GetSleepThresholdAttr().Get(),
                    'contact_report_threshold': report.GetThresholdAttr().Get(),
                    'authored_mass_kg': UsdPhysics.MassAPI(prim).GetMassAttr().Get()})
            if prim.IsA(UsdPhysics.Joint):
                joint = UsdPhysics.Joint(prim)
                inventory['joints'].append({'path': path, 'body0': [str(x) for x in joint.GetBody0Rel().GetTargets()],
                                           'body1': [str(x) for x in joint.GetBody1Rel().GetTargets()]})
            if prim.HasAPI(UsdPhysics.MaterialAPI):
                mat = UsdPhysics.MaterialAPI(prim)
                inventory['materials'].append({'path': path, 'static_friction': mat.GetStaticFrictionAttr().Get(),
                    'dynamic_friction': mat.GetDynamicFrictionAttr().Get(), 'restitution': mat.GetRestitutionAttr().Get()})
        return inventory
    inventory = usd_inventory()
    initial_inventory = inventory
    def capture_bodies(tick, phase):
        return {path: capture_snapshot(body_view=body.root_physx_view, simulation_view=simulation_view,
            rigid_object=body, clock_read=clock, tick=tick, phase=phase, body_path=path,
            usd_inventory=inventory) for path, body in bodies.items()}
    contact_views = {}
    for path in bodies:
        filters = [] if freefall else (['/Cal/B_bottom'] if path == '/Cal/A_top' else ['/Cal/A_top', '/Cal/ground/geometry/mesh'])
        view = simulation_view.create_rigid_contact_view(path, filter_patterns=filters, max_contact_data_count=128)
        metadata = {'sensor_paths': plain(view.sensor_paths), 'filter_paths': plain(view.filter_paths),
            'sensor_count': int(view.sensor_count), 'filter_count': int(view.filter_count),
            'max_contact_data_count': int(view.max_contact_data_count), 'check': bool(view.check()),
            'requested_sensor_path': path, 'requested_filter_paths': filters}
        metadata['filter_roles'] = [] if freefall else (['B_bottom'] if path == '/Cal/A_top' else ['A_top', 'ground'])
        contact_views[path] = (view, metadata)
    global_body_view = simulation_view.create_rigid_body_view('/Cal/*')
    actual_backend_order = {'rigid_body_prim_paths': plain(global_body_view.prim_paths),
        'count': int(global_body_view.count), 'max_shapes': int(global_body_view.max_shapes),
        'complete_backend_shape_order': 'UNKNOWN_NO_INSTALLED_PUBLIC_GETTER'}
    setup_readback = {path: {
        'material_properties_static_dynamic_restitution': observed(clock, body.root_physx_view.get_material_properties),
        'contact_offsets': observed(clock, body.root_physx_view.get_contact_offsets),
        'rest_offsets': observed(clock, body.root_physx_view.get_rest_offsets),
        'prim_paths': plain(body.root_physx_view.prim_paths), 'max_shapes': int(body.root_physx_view.max_shapes)
        } for path, body in bodies.items()}
    header = {'schema': 'SignedForceFixtureHeader/1', 'case': case,
        'protocol_sha256': sha(root / 'protocol.json'), 'source_release_sha256': sha(root / 'EXECUTION_RELEASE.json'),
        'installed_api_pin_sha256': sha(root / 'INSTALLED_API_PIN.json'),
        'root_admission_sha256': gate['root_admission_sha256'], 'source_review_sha256': gate['source_review_sha256'],
        'reader_freeze_sha256': gate['reader_freeze_sha256'], 'expected_header': admission['expected_header'],
        'epoch': epoch, 'origin_clock': origin, 'stage_inventory': inventory,
        'fixture_creation_order': creation_order, 'actual_backend_order': actual_backend_order,
        'contact_views': {path: meta for path, (_, meta) in contact_views.items()},
        'fixture_setup_readback': setup_readback,
        'runtime_versions': {'isaac_version': version, 'physx_extension': physx_id,
            'isaaclab_distribution': importlib.metadata.version('isaaclab'), 'selected_experience': args.experience},
        'contact_processing_setting': read_processing_setting(processing_settings, clock_read=clock),
        'contact_processing_install': processing_install, 'physical_device': 'cpu', 'no_policy_or_force_or_torque_commands': True,
        'pose_velocity_writes_after_first_controlled_step': 0,
        'model_calls': 0, 'training_gpu_hours': 0}
    record('HEADER.json', header)
    begin = {'schema': 'SignedForceFixtureBoundary/1', 'phase': 'BEGIN', 'tick': -1,
             'clock': clock(), 'bodies': capture_bodies(-1, 'TASK_BEGIN'),
             'contact_processing_setting': read_processing_setting(processing_settings, clock_read=clock)}
    record('BEGIN.json', begin)
    if clock() != origin:
        raise RuntimeError('SETUP_GETTERS_CHANGED_NATIVE_CLOCK')
    raw_file = (out / 'RAW_POST.jsonl').open('x')
    previous = sha(out / 'HEADER.json')
    for tick in range(case['controlled_steps']):
        before = clock(); sim.step(render=False)
        for body in bodies.values():
            body.update(dt)
        after = clock()
        if after['callback_count'] - before['callback_count'] != 1 or abs(after['time_s'] - before['time_s'] - dt) > 1e-7 or abs(callback['last_dt'] - dt) > 1e-9:
            raise RuntimeError('CONTROLLED_INTEGRATION_CLOCK_MISMATCH')
        if tick == 0:
            record('NATIVE_CLOCK_STARTED.json', {'native_clock': after, 'native_before_s': before['time_s'],
                'controlled_tick': 0, 'origin_clock': origin})
        inventory = usd_inventory()
        row = {'schema': 'SignedForceFixturePOST/1', 'tick': tick, 'phase': 'POST_STEP',
            'native_clock_before_step': before, 'native_clock_after_step': after,
            'bodies': capture_bodies(tick, 'POST_STEP'),
            'contacts': {path: {'metadata': meta, 'queries': [query_contact(view, qdt, clock, not freefall)
                for qdt in (1.0, dt, 2.0 * dt)]} for path, (view, meta) in contact_views.items()},
            'contact_processing_setting': read_processing_setting(processing_settings, clock_read=clock),
            'stage_inventory': inventory, 'stage_inventory_sha256': sha_value(inventory),
            'previous_record_sha256': previous}
        row['record_sha256'] = sha_value(row); previous = row['record_sha256']
        raw_file.write(canonical(row) + '\n'); raw_file.flush(); rows += 1
    raw_file.close(); raw_file = None
    end_inventory = usd_inventory()
    record('END.json', {'schema': 'SignedForceFixtureBoundary/1', 'phase': 'END',
        'tick': case['controlled_steps'], 'clock': clock(),
        'bodies': capture_bodies(case['controlled_steps'], 'TASK_END'),
        'contact_processing_setting': read_processing_setting(processing_settings, clock_read=clock),
        'stage_inventory': end_inventory, 'stage_inventory_unchanged': initial_inventory == end_inventory})
    end_fsynced = True
    lifecycle.mark('BEFORE_RESULT_WRITE', clock_read=clock)
    record('RESULT.json', {'schema': 'SignedForceFixtureWorkerResult/1', 'status': 'WORKER_COMPLETE_NOT_PHYSICS_PASS',
        'case_id': args.case, 'rows': rows, 'controlled_steps': case['controlled_steps'],
        'origin_clock': origin, 'end_clock': clock(), 'last_record_sha256': previous,
        'RAW_POST_sha256': sha(out / 'RAW_POST.jsonl'), 'HEADER_sha256': sha(out / 'HEADER.json'),
        'BEGIN_sha256': sha(out / 'BEGIN.json'), 'END_sha256': sha(out / 'END.json'),
        'wall_s_before_app_close': time.monotonic() - started,
        'scientific_qualification': 'UNKNOWN_INDEPENDENT_PROSPECTIVE_READER_REQUIRED',
        'S_F_R_admitted': 0, 'robot_load_truth': 'UNKNOWN', 'chemical_success': 'UNKNOWN'})
    lifecycle.mark('AFTER_RESULT_FSYNC', clock_read=clock, fields={'result_file_bytes': (out / 'RESULT.json').stat().st_size})
    result_fsynced = True
except BaseException as exc:
    record('FAILURE_RETAINED.json', {'status': 'FAILED_RETAINED', 'case_id': args.case,
        'rows_retained': rows, 'exception_type': type(exc).__name__, 'message': str(exc),
        'traceback': traceback.format_exc(), 'native_started': (out / 'NATIVE_CLOCK_STARTED.json').exists(),
        'no_retry_authorized': True})
    raise
finally:
    if raw_file is not None:
        raw_file.close()
    if app is not None:
        live_clock = globals().get('clock')
        callback_state = globals().get('callback')
        before_clear_marker = None
        context_cleared = False
        faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)
        try:
            if end_fsynced and result_fsynced and rows == case['controlled_steps']:
                owned_context_is_sim = sim_utils.SimulationContext.instance() is sim
                before_clear_marker = lifecycle.mark('BEFORE_CLEAR_INSTANCE', clock_read=live_clock, fields={
                    'complete_END_RESULT_fsynced': True, 'owned_context_is_sim': owned_context_is_sim,
                    'owned_stop_handle_present': getattr(sim, '_app_control_on_stop_handle', None) is not None,
                    'actual_python_callback_count_beforeclear': callback_state.get('count') if callback_state is not None else None})
                if not owned_context_is_sim:
                    raise RuntimeError('REFUSE_CLEAR_FOREIGN_OR_MISSING_SIMULATION_CONTEXT')
                sim_utils.SimulationContext.clear_instance()
                context_cleared = True
                live_clock = None
                lifecycle.mark('AFTER_CLEAR_INSTANCE', clock_read=None, fields={
                    'cached_pre_clear_clock': before_clear_marker['native_clock_after_read'],
                    'live_clock_unavailable_after_clear_instance': True,
                    'public_instance_is_None': sim_utils.SimulationContext.instance() is None,
                    'owned_stop_handle_is_None': getattr(sim, '_app_control_on_stop_handle', None) is None,
                    'actual_python_callback_count_afterclear': callback_state.get('count') if callback_state is not None else None})
            else:
                lifecycle.mark('CLEAR_INSTANCE_NOT_ELIGIBLE', clock_read=live_clock,
                    fields={'end_fsynced':end_fsynced,'result_fsynced':result_fsynced,'rows':rows})
            before_close_marker = lifecycle.mark('BEFORE_APP_CLOSE', clock_read=live_clock, fields={
                'context_cleared': context_cleared,
                'cached_pre_clear_clock': before_clear_marker['native_clock_after_read'] if before_clear_marker is not None else None,
                'live_clock_unavailable_after_clear_instance': context_cleared})
            lifecycle.mark('BEFORE_READONLY_REP_STATUS', clock_read=live_clock)
            status = readonly_replicator_observations(sys.modules)
            lifecycle.mark('AFTER_READONLY_REP_STATUS', clock_read=live_clock, fields={'readonly_replicator':status})
            app.close()
            lifecycle.mark('AFTER_APP_CLOSE', clock_read=None, fields={
                'native_time_afterclose': 'UNKNOWN_NOT_READ_AFTER_FRAMEWORK_RELEASE',
                'cached_pre_clear_clock': before_clear_marker['native_clock_after_read'] if before_clear_marker is not None else None,
                'cached_pre_close_clock': before_close_marker['native_clock_after_read'],
                'live_clock_unavailable_after_close': True,
                'actual_python_callback_count_afterclose': callback_state.get('count') if callback_state is not None else None,
                'default_close_returned': True,'context_cleared':context_cleared})
        finally:
            faulthandler.cancel_dump_traceback_later()
    lifecycle.close()
