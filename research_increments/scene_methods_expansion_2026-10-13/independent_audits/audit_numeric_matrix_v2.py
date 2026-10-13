"""Third-party recomputation of the frozen synthetic scheduling matrix.

Uses the independently written common-denominator integer oracle, not either
producer implementation. This produces zero physics/robot samples.
"""
from collections import Counter
import datetime
import hashlib
import itertools
import json
from pathlib import Path

from integer_grid_oracle_full import classify, oracle

ROOT = Path(__file__).parent
SOURCE = Path('/data/liyufeng/paperb_joint_scheduler_validation_20261013_v1')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    release = read(SOURCE/'EXECUTION_RELEASE.json')
    for name, digest in release['files'].items():
        require(sha(SOURCE/name) == digest, 'source freeze changed: '+name)
    report, protocol = read(SOURCE/'SUMMARY.json'), read(SOURCE/'protocol.json')
    for name, digest in report['artifacts'].items():
        require(sha(SOURCE/name) == digest, 'numeric data binding changed: '+name)
    require(report['execution_release_sha256'] == sha(SOURCE/'EXECUTION_RELEASE.json') and
            report['protocol_sha256'] == sha(SOURCE/'protocol.json'), 'numeric report freeze identity mismatch')
    require(report['native_episode_count'] == report['physics_sample_count'] == 0, 'numeric validator credited physics samples')
    methods = protocol['methods']
    counts = {m: Counter() for m in methods}
    families = Counter()
    false_refusals, false_feasible, candidate_mismatches, hashes = [], [], [], {}
    feasible_total = conditions = total_pairs = 0
    ids = set()
    output_rows = ROOT/'NUMERIC_MATRIX_AUDIT_ROWS_V2.jsonl'
    with (SOURCE/'ROSTER.jsonl').open() as roster, (SOURCE/'results.jsonl').open() as results, \
         (SOURCE/'oracle_pairs.jsonl').open() as producer_oracle, output_rows.open('x') as output:
        for index, triplet in enumerate(itertools.zip_longest(roster, results, producer_oracle)):
            require(all(line is not None for line in triplet), 'numeric output streams have different lengths')
            case, result, saved_oracle = [json.loads(line) for line in triplet]
            cid = case['id']
            require(cid not in ids and cid == result['case_id'] == saved_oracle['case_id'], 'duplicate/out-of-order numeric condition')
            ids.add(cid)
            families[case['family']] += 1
            independent = oracle(case)
            total_pairs += independent['pairs_checked']
            for name in ('feasible_pair_count', 'feasible_pairs', 'selected_ticks', 'objective_ratio', 'absolute_a_ticks', 'absolute_b_ticks', 'pairs_checked'):
                require(independent[name] == saved_oracle[name], 'producer oracle mismatch '+cid+': '+name)
            exists = independent['feasible_pair_count'] > 0
            require(result['oracle_feasible'] is exists and result['oracle_feasible_pair_count'] == independent['feasible_pair_count'] and
                    result['oracle_selected_ticks'] == independent['selected_ticks'], 'result oracle summary differs from integer oracle '+cid)
            candidate = result['candidate']
            match = candidate['selected_ticks'] == independent['selected_ticks'] and candidate['objective_ratio'] == independent['objective_ratio']
            require(candidate['status'] == ('FEASIBLE' if exists else 'REFUSED'), 'candidate feasibility status mismatch '+cid)
            require(result['candidate_matches_oracle'] is match, 'candidate-match flag wrong '+cid)
            if not match:
                candidate_mismatches.append(cid)
            rows = result['methods']
            require([r['method'] for r in rows] == methods, 'methods missing or order changed '+cid)
            checked = []
            for row in rows:
                m = row['method']
                pair = row['selected_ticks'] if row['selected_ticks'] is not None else row['diagnostic_fallback_ticks']
                checks = classify(case, pair) if pair is not None else None
                require(checks == row['robust_checks'], 'frozen method effect classification mismatch '+cid+': '+m)
                accepted = row['selected_ticks'] is not None
                success = accepted and checks['joint']
                require(row['robust_joint_pass'] is success, 'frozen method pass flag mismatch '+cid+': '+m)
                if row['exception'] is not None:
                    require(not accepted and row['status'] == 'EXCEPTION_RETAINED_AS_REJECTION', 'exception omitted from rejection '+cid)
                counts[m]['denominator'] += 1
                counts[m][row['status']] += 1
                counts[m]['robust_joint_pass'] += int(success)
                counts[m]['contact_and_release_pass_gap_fail'] += int(checks is not None and checks['contact'] and checks['release'] and not checks['duration_gap'])
                checked.append(dict(method=m, selected=accepted, robust_joint_pass=success, exception=row['exception']))
            old = rows[methods.index('joint_interval_scheduler')]
            old_selected = old['selected_ticks'] is not None
            false_refusal = exists and not old_selected
            false_accept = old_selected and not classify(case, old['selected_ticks'])['joint']
            require(result['old_joint_false_refusal'] is false_refusal and result['old_joint_false_feasible'] is false_accept, 'old joint error flag mismatch '+cid)
            if false_refusal:
                false_refusals.append(cid)
            if false_accept:
                false_feasible.append(cid)
            feasible_total += int(exists)
            conditions += 1
            output.write(json.dumps(dict(case_id=cid, integer_scale=independent['integer_common_denominator'],
                feasible_pair_count=independent['feasible_pair_count'], exact_best_ticks=independent['selected_ticks'],
                exact_objective_ratio=independent['objective_ratio'], candidate_matches=match,
                old_joint_false_refusal=false_refusal, old_joint_false_feasible=false_accept, methods=checked), sort_keys=True)+'\n')
            if conditions % 1000 == 0:
                print(json.dumps({'independently_audited_numeric_conditions': conditions}), flush=True)
    expected_grid = 1
    for values in protocol['full_grid'].values():
        expected_grid *= len(values)
    require(families['grid'] == expected_grid and families['synthetic_draw'] == protocol['random_draws'] and families['targeted'] == 4, 'declared numeric family denominator differs')
    require(total_pairs == report['independently_enumerated_pair_checks'], 'enumerated candidate pair count mismatch')
    require(conditions == report['total_conditions'] and conditions*len(methods) == report['method_comparisons'], 'numeric comparison denominator mismatch')
    require(false_refusals == report['old_joint_false_refusal_ids'] and false_feasible == report['old_joint_false_feasible_ids'], 'numeric failure records filtered or changed')
    require(candidate_mismatches == report['candidate_mismatch_ids'], 'numeric candidate discrepancy list mismatch')
    for m, count in counts.items():
        require(dict(count) == report['method_summary'][m], 'numeric method summary differs from raw rows: '+m)
    for name, digest in release['files'].items():
        require(sha(SOURCE/name) == digest, 'source changed during integer audit: '+name)
    result = dict(schema='paperb-third-party-integer-scheduling-audit-v2', status='PASS_COMPONENT_EXACT_INTEGER_RECOMPUTATION',
        created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_root=str(SOURCE),
        conditions=conditions, independently_enumerated_pair_checks=total_pairs, families=dict(families), feasible_conditions=feasible_total,
        refused_conditions=conditions-feasible_total, frozen_method_comparisons=conditions*len(methods),
        candidate_denominator=conditions, candidate_exact_matches=conditions-len(candidate_mismatches),
        old_joint_false_refusals=len(false_refusals), old_joint_false_feasible=len(false_feasible),
        method_summary={m: dict(c) for m, c in counts.items()}, native_episode_count=0, physics_sample_count=0,
        new_policy_weights=0, chemistry_evidence=False, statistical_coverage_guarantee=False,
        oracle='Independent exact common-denominator integer enumeration of all effect corners and minimum skill differences; minimum exact squared objective with lexicographic tie break',
        producer_implementation_or_oracle_imported=False,
        source_execution_release_sha256=sha(SOURCE/'EXECUTION_RELEASE.json'),
        source_artifact_sha256={name: sha(SOURCE/name) for name in ('ROSTER.jsonl', 'results.jsonl', 'oracle_pairs.jsonl', 'SUMMARY.json', 'protocol.json')},
        independent_rows_sha256=sha(output_rows),
        auditor_source_sha256={name: sha(ROOT/name) for name in ('audit_numeric_matrix_v2.py', 'integer_grid_oracle_full.py', 'test_integer_grid_oracle.py')})
    with (ROOT/'NUMERIC_MATRIX_AUDIT_V2.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'conditions', 'candidate_exact_matches', 'old_joint_false_refusals', 'old_joint_false_feasible')}))


if __name__ == '__main__':
    main()
