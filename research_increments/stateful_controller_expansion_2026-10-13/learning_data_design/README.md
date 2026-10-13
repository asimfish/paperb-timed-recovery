# VerifiedReplay CPU metadata prototype

This release catalogues 20 previously audited robot episodes and eight already seen CPU development witnesses. It does not train a policy, materialize student inputs, copy images, migrate a dataset, execute physics or relabel old tests as heldout. Its design was made after those old outcomes were available.

The schema and `verified_replay.py` define objective-qualified admission, episode-group splits, explicit public input rejection and observation-to-future-submission causality. `metadata_adapter.py` binds existing independent audits/private RAW dispatch to `INPUT_PIN.json` and produces JSONL metadata only. Full outcome truth remains distinct from RAW integrity and from the original certification boolean.

`metadata_v1/EPISODE_RECORDS.jsonl` has 28 records with original 4cal/16test/8development roles. `metadata_v1/CAUSAL_CANDIDATES.jsonl` has 852 private-frame references: 832 remain UNKNOWN because policy image delivery was never logged, and 20 have no future submission and are rejected. The initial capture precedes first submission; subsequent captures follow a physics step and can label only the next legal submission or a later chunk. Actual FIFO application and physical effect remain separate.

Robot primary test TRUE/FALSE/UNKNOWN remains 8/2/6; strict hold is 0/16. Complete timed+hold successful robot episodes are 0/20. All DP, RL and student-state OPD admissions remain zero. Partial mechanical/failure metadata is objective-qualified, and the eight CPU successes do not become robot demonstrations. A later explicitly authorized legacy training release is possible, with old roles retained and no untouched-holdout claim.

The terminal receipt is `CPU_ACCEPTANCE.json`: 34 focused tests, all 28 episode and 852 candidate schema/cross-field checks, and an exact read-only metadata transformation replay. The replay used no native reintegration. `UNSAFE_ALTERNATIVES_RED.json` preserves illustrative rejected shortcuts; it is not a defect allegation against the frozen physical auditor.

Run the public metadata contract tests from this directory:

```sh
/usr/bin/python3 -B -m unittest test_verified_replay -v
```

Python 3.10.12 and jsonschema 3.2.0 were used for this stdlib/JSON gate. No NumPy calculation or SDK score was repeated here. The original scores remain bound to their NumPy 1.26 independent auditor receipts. The real adapter requires private hash-matching inputs at the pinned paths; a public metadata release cannot reproduce private native scene execution or supply original RAW downloads. Write-once output can be reproduced in a fresh directory under this owned component:

```sh
/usr/bin/python3 -B metadata_adapter.py --output metadata_reproduction
```

`run_cpu_acceptance.py` produces write-once terminal receipts; do not overwrite the existing receipt. Source/doc/output SHA identities are in `ARTIFACT_MANIFEST.json`. See the ADR and Chinese learning plan for future DP/RL/OPD objective/input/budget gates and the new support-handoff contract requirement. The old frozen 604-file increment is untouched.
