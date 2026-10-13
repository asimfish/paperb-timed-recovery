"""Independent raw and MuJoCo replay audit for the contact-free graph component.

Never imports the producer's controller, plant, referee or replay auditor. All
fourteen controlled traces and the original full-power reference are retained.
Replay integrations verify existing evidence and add zero experiment episodes.
"""
from collections import Counter
import csv
import datetime
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

ROOT = Path(__file__).parent
SOURCE = Path('/data/liyufeng/paperb_task_graph_expansion_20261013_v1')
CODE = SOURCE/'code'
NATIVE = SOURCE/'native'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def states(path, protocol):
    with path.open() as f:
        entries = list(csv.DictReader(f))
    require(len(entries) == protocol['horizon_ns']//protocol['dt_ns']+1, 'native sample count mismatch')
    parsed = []
    for i, entry in enumerate(entries):
        values = {k: float(entry[k]) for k in ('A_position', 'A_velocity', 'B_position', 'B_velocity', 'A_drive_next_interval', 'B_drive_next_interval', 'native_time_s')}
        require(all(np.isfinite(value) for value in values.values()), 'nonfinite native state')
        now = int(entry['sim_ns'])
        require(now == i*protocol['dt_ns'] and int(entry['epoch_id']) == 0 and round(values['native_time_s']*1e9) == now, 'native grid or epoch changed')
        parsed.append(dict(ns=now, native_time_s=values['native_time_s'],
                           position=[values['A_position'], values['B_position']],
                           velocity=[values['A_velocity'], values['B_velocity']],
                           drive=[values['A_drive_next_interval'], values['B_drive_next_interval']]))
    return parsed


def independent_model(protocol):
    tree = ET.fromstring((CODE/'shared_bus.xml').read_text())
    for name in ('A', 'B'):
        setting = protocol['private_'+name+'_setting']
        body = tree.find('./worldbody/body[@name="'+name+'"]')
        inertia = setting['inertia']
        body.find('inertial').set('diaginertia', str(inertia/2)+' '+str(inertia/2)+' '+str(inertia))
        body.find('joint').set('damping', str(setting['damping']))
    model = mujoco.MjModel.from_xml_string(ET.tostring(tree, encoding='unicode'))
    require(model.nq == model.nv == model.nu == 2 and model.opt.timestep == protocol['dt_ns']/1e9, 'compiled physics schema mismatch')
    return model


def physics_replay(rows, protocol, full_power=False):
    model = independent_model(protocol)
    data = mujoco.MjData(model)
    data.qpos[:] = protocol['initial_state']['qpos']
    data.qvel[:] = protocol['initial_state']['qvel']
    data.ctrl[:] = protocol['drive_torque']
    mujoco.mj_forward(model, data)
    maximum = 0.
    for i, row in enumerate(rows):
        require(float(data.time) == row['native_time_s'], 'native replay time changed')
        difference = max(float(np.max(np.abs(data.qpos-row['position']))), float(np.max(np.abs(data.qvel-row['velocity']))))
        maximum = max(maximum, difference)
        require(difference == 0., 'native trajectory differs from exact independent MuJoCo replay')
        require(data.ncon == 0, 'contact-free component unexpectedly has contacts')
        if full_power:
            require(row['drive'] == [protocol['drive_torque']]*2, 'original reference was altered by stop control')
            data.ctrl[:] = protocol['drive_torque']
        else:
            data.ctrl[:] = row['drive']
        if i < len(rows)-1:
            mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
    return {'replay_max_absolute_state_error': maximum, 'replay_rows': len(rows), 'native_clock_exact': True,
            'contacts': 0, 'verification_integrations_are_not_new_experiment_rollouts': True}


def reference_intervals(rows, protocol):
    answers = []
    threshold = protocol['reference_angle_rad']
    for axis in range(2):
        hit = next((i for i in range(1, len(rows)) if rows[i-1]['position'][axis] < threshold <= rows[i]['position'][axis]), None)
        answers.append([rows[hit-1]['ns'], rows[hit]['ns']] if hit is not None else None)
    return answers


def observed_stops(rows, protocol):
    answers = []
    for axis in range(2):
        moving = any_low = False
        start = None
        event = None
        for i, row in enumerate(rows):
            positive = abs(row['velocity'][axis]) <= protocol['speed_threshold']
            if not positive:
                moving = True
                start = None
                continue
            if not moving:
                continue
            if start is None:
                start = i
            if row['ns']-rows[start]['ns'] >= protocol['hold_ns']:
                require(start > 0, 'left-censored initial stillness became a stop')
                event = {'occurrence_interval_ns': [rows[start-1]['ns'], rows[start]['ns']],
                         'confirmation_ns': row['ns'], 'low_sample_count': i-start+1,
                         'had_prior_moving_sample': True}
                require(event['low_sample_count'] >= 21, '200ms confirmation used fewer than 21 endpoints')
                break
        answers.append(event)
    return answers


def both(values):
    return 'FALSE' if any(v == 'FALSE' for v in values) else 'TRUE' if all(v == 'TRUE' for v in values) else 'UNKNOWN'


def time_verdict(anchor, stop, window, horizon, hold):
    if anchor is None:
        return 'UNKNOWN'
    if stop is None:
        return 'FALSE' if horizon > anchor[1]+window[1]+hold else 'UNKNOWN'
    lo = stop['occurrence_interval_ns'][0]-anchor[1]
    hi = stop['occurrence_interval_ns'][1]-anchor[0]
    if lo >= window[0] and hi <= window[1]:
        return 'TRUE'
    return 'FALSE' if hi < window[0] or lo > window[1] else 'UNKNOWN'


def graph_verdict(rows, reference, graph, protocol):
    anchors = reference_intervals(reference, protocol)
    actual = reference_intervals(rows, protocol)
    stops = observed_stops(rows, protocol)
    predicates = {}
    for axis, name in enumerate(('A', 'B')):
        predicates[name+'_time'] = time_verdict(anchors[axis], stops[axis], graph['windows_ns'][axis], rows[-1]['ns'], protocol['hold_ns'])
        predicates[name+'_original_reference'] = 'TRUE' if anchors[axis] is not None and actual[axis] == anchors[axis] else 'FALSE'
    dependencies = []
    for first, second in graph['edges']:
        if stops[first] is None or stops[second] is None:
            dependencies.append('FALSE')
        else:
            a, b = stops[first]['occurrence_interval_ns'], stops[second]['occurrence_interval_ns']
            minimum = graph['minimum_edge_gap_ns']
            dependencies.append('TRUE' if b[0]-a[1] >= minimum else 'FALSE' if b[1]-a[0] < minimum else 'UNKNOWN')
    predicates['graph_dependencies'] = both(dependencies)
    maintenance, witness = 'TRUE', None
    hold = graph['B_power_hold_lower_ns']
    if hold is not None:
        if anchors[1] is None:
            maintenance = 'UNKNOWN'
        else:
            lower, upper = [x+hold for x in anchors[1]]
            ambiguous = False
            for row in rows:
                if anchors[1][1] <= row['ns'] < upper:
                    bad = abs(row['velocity'][1]) <= protocol['speed_threshold'] or row['drive'][1] != protocol['drive_torque']
                    if bad and row['ns'] < lower:
                        maintenance, witness = 'FALSE', row['ns']
                        break
                    ambiguous = ambiguous or bad
            if maintenance != 'FALSE':
                maintenance = 'UNKNOWN' if ambiguous or rows[-1]['ns'] < upper else 'TRUE'
    predicates['B_sampled_power_and_motion_maintenance'] = maintenance
    return dict(original_references=anchors, actual_references=actual, stop_events=stops, **predicates,
                joint_original_contract=both(list(predicates.values())), maintenance_failure_witness_ns=witness,
                sampled_not_continuous=True, chemical_certified=0, robot_task_certified=0)


def delivery_and_dispatch(directory, rows, protocol):
    commands = read(directory/'commands.json')
    effects = read(directory/'private_plant_effects.json')
    services = {('A', 'initial_A'): protocol['first_A_delay_ns'], ('B', 'selective_B'): protocol['selective_B_delay_ns'], ('global', 'relay'): protocol['relay_delay_ns']}
    bus_free = 0
    for seq, command in enumerate(commands):
        require(command['seq'] == seq and (command['target'], command['tag']) in services, 'unknown or duplicate reservation')
        start = command['request_ns'] if command['target'] == 'global' else max(command['request_ns'], bus_free)
        require(command['service_start_ns'] == start and command['ack_ns'] == start+services[command['target'], command['tag']], 'queue/service reservation mismatch')
        if command['target'] != 'global':
            bus_free = command['ack_ns']
    expected_effects = []
    current = [protocol['drive_torque']]*2
    global_latched = False
    applied = set()
    for tick, row in enumerate(rows):
        for command in commands:
            if command['ack_ns'] <= row['ns'] and command['seq'] not in applied:
                applied.add(command['seq'])
                if command['target'] == 'global':
                    global_latched = True
                if global_latched:
                    current = [0., 0.]
                else:
                    current[0 if command['target'] == 'A' else 1] = 0.
                expected_effects.append(dict(seq=command['seq'], scheduled_ack_ns=command['ack_ns'],
                    actual_apply_ns=row['ns'], applied_to_plant=True, bus_latched=global_latched))
        require(row['drive'] == current, 'queued target counted before actual application or relay effect mismatch')
    require(len(applied) == len(commands) and expected_effects == effects, 'missing/forged private application records')
    deliveries = read(directory/'public_deliveries.json')
    delay = protocol['public_delivery_delay_ns']
    expected = []
    for i, row in enumerate(rows):
        if row['ns']+delay > rows[-1]['ns']:
            break
        # Capture occurs before same-tick application; positions and velocity
        # are unchanged by a drive update, while powered uses previous ctrl.
        before_drive = rows[i-1]['drive'] if i else [protocol['drive_torque']]*2
        expected.append(dict(capture_ns=row['ns'], arrival_ns=row['ns']+delay, positions=row['position'],
                             velocities=row['velocity'], powered=[bool(x) for x in before_drive]))
    require(deliveries == expected, 'delayed public packet differs from native pre-application capture')
    inputs = read(directory/'public_actor_inputs.json')
    require(len(inputs) == len(rows), 'actor input ledger has missing ticks')
    for row, item in zip(rows, inputs):
        capture = row['ns']-delay if row['ns'] >= delay else None
        require(item == dict(consumer_now_ns=row['ns'], latest_capture_ns=capture, latest_arrival_ns=row['ns'] if capture is not None else None), 'actor consumed premature/future packet')
    decisions = read(directory/'public_decisions.json')
    require(len(decisions) == 1 and decisions[0]['now_ns'] == delay and decisions[0]['consumed_packet'] == expected[0] and
            decisions[0]['private_fault_or_model_read'] is False, 'actor plan not bound to first delivered public packet')
    plan = decisions[0]['selected_plan']
    expected_requests = [] if plan is None else [dict(request_ns=x[0], target=x[1], tag=x[2]) for x in plan['commands']]
    require([{k: c[k] for k in ('request_ns', 'target', 'tag')} for c in commands] == expected_requests, 'applied reservations differ from public selected plan')
    return {'commands': len(commands), 'public_packets': len(deliveries), 'actual_application_verified': True,
            'same_tick_capture_precedes_application': True, 'no_future_private_packet_consumed': True,
            'selected_plan': plan}


def main():
    require(mujoco.__version__ == '3.3.7' and np.__version__ == '2.2.6', 'exact graph replay requires its source runtime')
    release = read(CODE/'EXECUTION_RELEASE.json')
    for name, expected in release['files'].items():
        require(sha(CODE/name) == expected and sha(NATIVE/'source_snapshot'/name) == expected, 'frozen source or snapshot changed: '+name)
    require(read(NATIVE/'execution_release_snapshot.json') == release, 'execution source release identity mismatch')
    protocol, raw_results = read(CODE/'PROTOCOL.json'), read(NATIVE/'results.json')
    require(protocol['private_fault'] == 'none', 'unexpected hidden fault domain')
    reference = states(NATIVE/'original_fullpower_reference.csv', protocol)
    replay_reference = physics_replay(reference, protocol, True)
    roster = [(case, arm) for case in protocol['main_cases'] for arm in protocol['arms']]+[(case, case['arm']) for case in protocol['sentinel_cases']]
    require(len(raw_results['slots']) == len(roster) == 14, 'declared controlled episode denominator mismatch')
    outputs, counts, hashes = [], {arm: Counter() for arm in protocol['arms']}, {}
    for (case, arm), saved_summary in zip(roster, raw_results['slots']):
        episode = case['id']+'--'+arm
        directory = NATIVE/episode
        rows = states(directory/'independent_samples.csv', protocol)
        replay = physics_replay(rows, protocol)
        contract = read(directory/'contract.json')
        graph = protocol['graphs'][case['graph_id']]
        require(contract['case'] == case and contract['graph'] == graph and contract['arm'] == arm, 'case/graph declaration differs from freeze')
        runtime = read(directory/'model_runtime.json')
        require(runtime['mujoco'] == mujoco.__version__ and runtime['numpy'] == np.__version__ and
                runtime['mjcf_sha256'] == sha(CODE/'shared_bus.xml') and runtime['initial_state'] == protocol['initial_state'], 'native model/runtime binding mismatch')
        transport = delivery_and_dispatch(directory, rows, protocol)
        verdict = graph_verdict(rows, reference, graph, protocol)
        require(verdict == read(directory/'independent_verdict.json'), 'independent raw graph event verdict differs from producer: '+episode)
        summary = read(directory/'summary.json')
        require(summary == saved_summary and summary['samples'] == len(rows) and summary['commands'] == transport['commands'] and
                summary['episode_id'] == episode and summary['joint_original_contract'] == verdict['joint_original_contract'], 'summary differs from raw evidence: '+episode)
        outputs.append(dict(episode_id=episode, role=case['role'], arm=arm, graph_id=case['graph_id'],
                            samples=len(rows), verdict=verdict, replay=replay, transport=transport))
        if case['role'] == 'main_component':
            counts[arm][verdict['joint_original_contract']] += 1
        for name in ('independent_samples.csv', 'contract.json', 'commands.json', 'private_plant_effects.json',
                     'public_actor_inputs.json', 'public_deliveries.json', 'public_decisions.json', 'model_runtime.json', 'independent_verdict.json', 'summary.json'):
            hashes[str((directory/name).relative_to(SOURCE))] = sha(directory/name)
        print(json.dumps({'episode_id': episode, 'raw_joint': verdict['joint_original_contract'], 'replay_error': replay['replay_max_absolute_state_error']}), flush=True)
    for name, expected in release['files'].items():
        require(sha(CODE/name) == expected and sha(NATIVE/'source_snapshot'/name) == expected, 'source changed during graph audit: '+name)
    for name in ('native/original_fullpower_reference.csv', 'native/results.json', 'code/PROTOCOL.json', 'code/EXECUTION_RELEASE.json'):
        hashes[name] = sha(SOURCE/name)
    result = dict(schema='paperb-third-party-native-graph-audit-v1', status='PASS_COMPONENT_RAW_REPLAY_AND_CONTRACTS',
        created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), main_episode_count=12, sentinel_episode_count=2,
        main_task_graph_instances=4, controlled_native_samples=sum(e['samples'] for e in outputs),
        original_reference_integrations=1, original_reference_samples=len(reference), total_existing_native_samples_including_reference=sum(e['samples'] for e in outputs)+len(reference),
        new_experiment_rollouts_created_by_auditor=0, verification_reintegrations=15,
        component_scope='Contact-free two-rotor known noiseless physics, fixed graph programs and rule controllers; no learning/robot/chemistry generalization claim',
        arm_main_counts={arm: {key: counts[arm].get(key, 0) for key in ('TRUE', 'FALSE', 'UNKNOWN')} for arm in counts},
        episodes=outputs, original_reference_replay=replay_reference,原始fullpoweranchors_ns=reference_intervals(reference, protocol),
        source_artifact_sha256=hashes, source_execution_release_sha256=sha(CODE/'EXECUTION_RELEASE.json'),
        audit_source_sha256=sha(ROOT/'audit_task_graph.py'), producer_referee_or_controller_imported=False,
        real_robot_runs=0, chemistry_claims=0, new_policy_weights=0, continuous_force_or_motion_between_samples_proven=False)
    with (ROOT/'TASK_GRAPH_AUDIT.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    public = {k: result[k] for k in ('schema', 'status', 'main_episode_count', 'sentinel_episode_count', 'main_task_graph_instances',
                'controlled_native_samples', 'original_reference_integrations', 'original_reference_samples', 'total_existing_native_samples_including_reference',
                'arm_main_counts', 'component_scope', 'real_robot_runs', 'chemistry_claims', 'new_policy_weights')}
    public.update(full_audit_file='TASK_GRAPH_AUDIT.json', full_audit_sha256=sha(ROOT/'TASK_GRAPH_AUDIT.json'),
                  source_execution_release_sha256=sha(CODE/'EXECUTION_RELEASE.json'), raw_replay_max_absolute_error=0.,
                  new_experiment_rollouts_created_by_auditor=0)
    with (ROOT/'PUBLIC_TASK_GRAPH_AUDIT.json').open('x') as f:
        json.dump(public, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(public))


if __name__ == '__main__':
    main()
