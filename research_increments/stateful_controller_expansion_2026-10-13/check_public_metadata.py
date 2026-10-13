"""Offline metadata/schema/admission replay. Does not require private RAW/images."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
DATA = HERE/'learning_data_design'
sys.path.insert(0, str(DATA))
from jsonschema import Draft7Validator
from verified_replay import validate_record, causal_admission, summarize_robot


def main():
    manifest = json.loads((DATA/'ARTIFACT_MANIFEST.json').read_text())
    for name, entry in manifest['files'].items():
        raw = (DATA/name).read_bytes()
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256'], name
    episodes = [json.loads(l) for l in (DATA/'metadata_v1/EPISODE_RECORDS.jsonl').read_text().splitlines()]
    candidates = [json.loads(l) for l in (DATA/'metadata_v1/CAUSAL_CANDIDATES.jsonl').read_text().splitlines()]
    episode_schema = Draft7Validator(json.loads((DATA/'VerifiedReplay.schema.json').read_text()))
    candidate_schema = Draft7Validator(json.loads((DATA/'VerifiedReplayCausalCandidate.schema.json').read_text()))
    for record in episodes:
        episode_schema.validate(record)
        validate_record(record)
    statuses = Counter()
    for candidate in candidates:
        candidate_schema.validate(candidate)
        if candidate['action_label'] is None:
            assert candidate['admission']['status'] == 'REJECTED'
            assert candidate['admission']['reasons'] == ['NO_FUTURE_SUBMISSION_RECORDED']
        else:
            assert causal_admission(candidate) == candidate['admission']
        statuses[candidate['admission']['status']] += 1
        assert candidate['admission']['training_admitted'] is False
    assert len(episodes) == 28 and len(candidates) == 852 and statuses == {'UNKNOWN':832,'REJECTED':20}
    summary = summarize_robot(episodes)
    assert summary['robot_episodes'] == 20 and summary['original_test_denominator'] == 16
    assert summary['primary_test_T_F_U'] == {'TRUE':8,'FALSE':2,'UNKNOWN':6}
    assert summary['full_timed_and_hold_success_demo_episodes'] == 0
    print(json.dumps({'status':'PASS_PUBLIC_METADATA_ONLY', 'episodes':len(episodes), 'causal_candidates':len(candidates),
        'admission_statuses':dict(statuses), 'training_admitted':0, 'new_native_epochs':0,
        'original_private_dispatch_transform_or_physical_labels_recomputed':False}, sort_keys=True))


if __name__ == '__main__':
    main()
