"""Review/reader/header binding is exercised without importing any native SDK."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import execution_gate as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        protocol = {'cases': [{'id': 'case', 'controlled_steps': 120}], 'setup': {'gravity': [-9.81]}, 'dt_s': 1 / 240, 'cleanup_candidate':{'publicclear':True}, 'family_budget':{'total':6}, 'parent_execution_release_sha256':'p'*64, 'measurement_instrumentation_candidate':{'settingpath':'test'}}
        selection = self.root / 'ROOT_SELECTION.json'; selection.write_text('{}')
        protocol['prospective_budget_confirmation'] = {'status':'ROOT_CONFIRMED_BEFORE_V03_OUTCOMES','path':str(selection),'sha256':gate.sha(selection)}
        for name, value in [('protocol.json', protocol), ('INSTALLED_API_PIN.json', {'files': {}}),
                            ('SCHEMA_CONTRACT.json', {'schema': 'x'})]:
            (self.root / name).write_text(json.dumps(value))
        release = {'schema': 'SignedForceFixtureV03ExecutionRelease/1', 'maximum_distinct_native_epochs': 6,
            'files': {name: gate.sha(self.root / name) for name in ('protocol.json', 'INSTALLED_API_PIN.json', 'SCHEMA_CONTRACT.json')}}
        (self.root / 'EXECUTION_RELEASE.json').write_text(json.dumps(release))
        self.release = gate.sha(self.root / 'EXECUTION_RELEASE.json'); self.reader = 'r' * 64; self.review_sha = 'v' * 64
        self.review = {'status': 'PASS_PROSPECTIVE_SIGNED_FORCE_CALIBRATION_V03_SOURCE_REVIEW',
                      'source_release_sha256': self.release, 'reader_freeze_sha256': self.reader}
        self.admission = {'status': 'ADMITTED_ONE_SIGNED_FORCE_FIXTURE_CALIBRATION_V03_CASE',
            'source_release_sha256': self.release, 'source_review_sha256': self.review_sha,
            'reader_freeze_sha256': self.reader, 'case_id': 'case', 'GPU_uuid': 'GPU-test',
            'maximum_new_distinct_native_epochs': 6, 'closed_old_family_cap': 3,
            'per_child_wait_s': 300, 'termination_wait_s': 30,
            'closed_force_v01_actual_epochs':1, 'closed_force_v02_actual_epochs':2, 'closed_calibration_actual_epochs_before_v03':3, 'calibration_family_cumulative_upper_bound':9, 'separate_shutdown_diagnostic_actual_epochs':1,
            'expected_header': gate.expected_header(self.root, 'case', self.reader)}
    def tearDown(self):
        self.temp.cleanup()
    def validate(self):
        gate.validate_review_root(self.review, self.admission, self.release, self.review_sha,
            'case', 'GPU-test', self.reader, root=self.root)
    def test_original_binding_passes(self):
        self.validate(); gate.verify_sources(self.root)
    def test_changed_source_refused(self):
        (self.root / 'protocol.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'SOURCE_PIN'):
            gate.verify_sources(self.root)
    def test_reader_pin_cannot_be_omitted(self):
        del self.review['reader_freeze_sha256']
        with self.assertRaisesRegex(ValueError, 'READER'):
            self.validate()
    def test_independent_header_case_cannot_be_rewritten(self):
        self.admission['expected_header']['case']['controlled_steps'] = 1
        with self.assertRaisesRegex(ValueError, 'HEADER'):
            self.validate()
    def test_unapproved_sixth_case_refused(self):
        with self.assertRaisesRegex(ValueError, 'FROZEN_CASE'):
            gate.expected_header(self.root, 'case6', self.reader)
    def test_resource_insufficient_refused(self):
        receipt = {'gpu_uuid': 'GPU-test', 'free_mib': 24575, 'minimum_free_mib': 24576,
                   'foreign_processes_signaled': False, 'global_driver_changes': False}
        with self.assertRaisesRegex(ValueError, 'RESOURCE'):
            gate.validate_live_gpu(receipt, 'GPU-test')
    def test_no_false_formal_start_without_clock(self):
        self.assertFalse(gate.formal_native_started(self.root, 'case'))
    def test_source_review_status_cannot_be_unknown(self):
        self.review['status'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'REVIEW'):
            self.validate()
    def test_wrong_gpu_or_limit_refused(self):
        for key, wrong in [('GPU_uuid', 'other'), ('maximum_new_distinct_native_epochs', 7), ('per_child_wait_s', 500)]:
            original = self.admission[key]; self.admission[key] = wrong
            with self.assertRaises(ValueError): self.validate()
            self.admission[key] = original


if __name__ == '__main__':
    unittest.main()
