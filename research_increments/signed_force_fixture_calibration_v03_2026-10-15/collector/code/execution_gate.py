"""Source, independent reader/review, root header and GPU pins before SDK import."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_sources(root=ROOT):
    root = Path(root)
    release = json.loads((root / 'EXECUTION_RELEASE.json').read_text())
    if release.get('schema') != 'SignedForceFixtureV03ExecutionRelease/1' or release.get('maximum_distinct_native_epochs') != 6:
        raise ValueError('WRONG_SOURCE_RELEASE')
    for name, pin in release['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or sha(root / path) != pin:
            raise ValueError('SOURCE_PIN_MISMATCH:' + name)
    installed = json.loads((root / 'INSTALLED_API_PIN.json').read_text())
    for pin in installed['files'].values():
        if sha(pin['path']) != pin['sha256']:
            raise ValueError('INSTALLED_SOURCE_PIN_CHANGED')
    protocol = json.loads((root / 'protocol.json').read_text())
    budget = protocol['prospective_budget_confirmation']
    if budget.get('status') != 'ROOT_CONFIRMED_BEFORE_V03_OUTCOMES' or sha(budget['path']) != budget['sha256']:
        raise ValueError('ROOT_PROSPECTIVE_V03_BUDGET_PIN_CHANGED')
    return release


def expected_header(root, case, reader_sha):
    root = Path(root)
    protocol = json.loads((root / 'protocol.json').read_text())
    cases = [c for c in protocol['cases'] if c['id'] == case]
    if len(cases) != 1:
        raise ValueError('WRONG_FROZEN_CASE')
    return {'case': cases[0], 'protocol_sha256': sha(root / 'protocol.json'),
        'source_release_sha256': sha(root / 'EXECUTION_RELEASE.json'),
        'installed_api_pin_sha256': sha(root / 'INSTALLED_API_PIN.json'),
        'schema_contract_sha256': sha(root / 'SCHEMA_CONTRACT.json'),
        'reader_freeze_sha256': reader_sha, 'setup': protocol['setup'],
        'dt_s': protocol['dt_s'], 'no_control_actions': True,
        'cleanup_candidate': protocol['cleanup_candidate'], 'family_budget': protocol['family_budget'],
        'measurement_instrumentation_candidate': protocol['measurement_instrumentation_candidate'],
        'prospective_budget_confirmation': protocol['prospective_budget_confirmation'],
        'parent_execution_release_sha256': protocol['parent_execution_release_sha256'],
        'closed_old_family_cap': 3, 'maximum_new_distinct_epochs': 6}


def validate_review_root(review, admission, release_sha, review_sha, case, gpu_uuid, reader_sha, root=ROOT):
    if review.get('status') != 'PASS_PROSPECTIVE_SIGNED_FORCE_CALIBRATION_V03_SOURCE_REVIEW' or review.get('source_release_sha256') != release_sha or review.get('reader_freeze_sha256') != reader_sha:
        raise ValueError('INDEPENDENT_SOURCE_REVIEW_AND_READER_REQUIRED')
    required = {'status': 'ADMITTED_ONE_SIGNED_FORCE_FIXTURE_CALIBRATION_V03_CASE',
        'source_release_sha256': release_sha, 'source_review_sha256': review_sha,
        'reader_freeze_sha256': reader_sha, 'case_id': case, 'GPU_uuid': gpu_uuid,
        'maximum_new_distinct_native_epochs': 6, 'closed_old_family_cap': 3,
        'per_child_wait_s': 300, 'termination_wait_s': 30,
        'closed_force_v01_actual_epochs': 1, 'closed_force_v02_actual_epochs': 2, 'closed_calibration_actual_epochs_before_v03': 3, 'calibration_family_cumulative_upper_bound': 9,
        'separate_shutdown_diagnostic_actual_epochs': 1}
    if any(admission.get(k) != v for k, v in required.items()) or admission.get('expected_header') != expected_header(root, case, reader_sha):
        raise ValueError('ROOT_CASE_REVIEW_READER_GPU_HEADER_ADMISSION_REQUIRED')


def validate_live_gpu(receipt, uuid):
    if receipt.get('gpu_uuid') != uuid or receipt.get('free_mib', 0) < 24576 or receipt.get('minimum_free_mib') != 24576 or receipt.get('foreign_processes_signaled') is not False or receipt.get('global_driver_changes') is not False:
        raise ValueError('LIVE_GPU_RESOURCE_GATE_REQUIRED')


def formal_native_started(root, case):
    path = Path(root) / 'cases' / case / 'NATIVE_CLOCK_STARTED.json'
    if not path.is_file():
        return False
    try:
        value = json.loads(path.read_text())['native_clock']
        return bool(value['native_epoch']) and type(value['callback_count']) is int and value['callback_count'] > 0 and math.isfinite(value['time_s'])
    except (ValueError, TypeError, KeyError):
        return False


def child_source_gate():
    verify_sources()
    if '--root' not in sys.argv or '--case' not in sys.argv:
        raise ValueError('EXPLICIT_ROOT_CASE_REQUIRED')
    root = Path(sys.argv[sys.argv.index('--root') + 1]).resolve()
    case = sys.argv[sys.argv.index('--case') + 1]
    if root != ROOT:
        raise ValueError('FOREIGN_CHILD_ROOT')
    gate_path = os.environ.get('PAPERB_FORCE_GATE_RECEIPT')
    if not gate_path or not Path(gate_path).resolve().is_relative_to(ROOT / 'gate_attempts'):
        raise ValueError('ROOT_GATE_RECEIPT_REQUIRED')
    gate = json.loads(Path(gate_path).read_text())
    if gate['case_id'] != case or gate['source_release_sha256'] != sha(ROOT / 'EXECUTION_RELEASE.json') or not 0 <= time.time() - gate['issued_at_unix_s'] <= 120:
        raise ValueError('STALE_OR_WRONG_CASE_GATE')
    review_path, admission_path, reader_path = map(Path, (gate['source_review_path'], gate['root_admission_path'], gate['reader_freeze_path']))
    if sha(review_path) != gate['source_review_sha256'] or sha(admission_path) != gate['root_admission_sha256'] or sha(reader_path) != gate['reader_freeze_sha256']:
        raise ValueError('INDEPENDENT_GATE_ARTIFACT_CHANGED')
    review, admission = json.loads(review_path.read_text()), json.loads(admission_path.read_text())
    validate_review_root(review, admission, gate['source_release_sha256'], gate['source_review_sha256'], case, gate['gpu_uuid'], gate['reader_freeze_sha256'])
    validate_live_gpu(gate['live_gpu'], gate['gpu_uuid'])
    return gate, admission
