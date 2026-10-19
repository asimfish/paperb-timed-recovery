# Independent adversarial review of AsyncBridge v0.2 — reviewer's final report (verbatim)

Reviewer: separate agent with read-only copies of v0.1/v0.2 sources; it never saw the author tests' expectations beyond the module and the task description; scripts in `out/`.

**Verdict: CONFIRMED_DEFECTS — but none in the byte/count reservation itself.** With plain JSON-typed caller values, the CASE_END guarantee and the byte reservation held across everything I ran (NO_DEFECT_FOUND_WITHIN_SEARCH). The defects are in what the contract text promises beyond that, in type validation, and in replay strictness.

### Confirmed defects
**T3 – MEDIUM (contract overclaim; not a v0.1 regression).** "All reserved events writable without any further ordinary event" is false for SLOT_DISPOSITIONs. Reproducer: fixture header with `caps.events=30`; observe, packet, `start_inference(purpose="SAFE_LOCAL_RECOVERY")`, `accept_return` OK → `prepare_slot` = `RECOVERY_REQUIRES_KNOWN_FAILURE`; `record_failure`/`observe_state`/`transition_actor` = `EVENT_CAPACITY_REFUSED`. `close()` still succeeds with all 8 slots censored. Variant: known-not-full failure + passed deadline → `POST_DEADLINE_RECOVERY_REQUIRES_FULL_FALSE`. Expected: reserved dispositions writable without ordinary events; actual: only CASE_END is guaranteed. v0.1 behaves identically.

**T1 – MEDIUM. `commit_slot` accepts an `==`-equal but differently typed/serialized prepared body** (`require(p == expected)`). Reproducer: take `prepare_slot(...)`, set `target_9d[0]=int(1.7976931348623157e308)` (309 digits), `desired_tick` to float, `known_original_failure=0`, `actor_generation=False` → accepted, module replay accepts; `prepared_sha256`/`target_sha256` no longer hash the recorded fields; the journal holds a target int with |int|>2^53 (breaks the stated premise). Knock-on T1b: the module's own next prepared gets `earliest_apply_tick = 1.2345678901234568e+18` (22 chars > the 20-char assumption). Byte cap still holds because the whole-line bound check blocks any overrun. v0.1 also accepts.

**T2 – LOW-MEDIUM (needs a hostile/buggy in-process caller). Subclass objects make live writer and replay diverge.** A dict subclass with always-True `__eq__` as `claimed_owner` is accepted live; replay then refuses the journal (`CHANNEL_OWNER_TARGET_MISMATCH`). An int subclass as `desired_tick`: the module's next computed SLOT_DISPOSITION is refused with `RESERVED_LINE_BOUND_VIOLATED` until the queue drains; an APPLIED result is accepted at tick 1 for desired tick 5; replay refuses that journal.

**T5 – LOW. Replay accepts envelope values the live writer never emits:** after re-chaining hashes, `seq` = 2.0 or True and a float `clock` are accepted (float `wall_ns` is refused).

**T6 – LOW. Some malformed inputs raise non-`BridgeError`:** `OverflowError` (int 10**400 in output), `ValueError` (NaN/inf in `accept_return`), `TypeError` (list as status/actor id/authorization purpose), `JSONDecodeError` (blank line in replay). None changed state or file.

### Notes (not defects)
T7 – `line_bounds()` builds strings of length `max_token_chars`: 10^6 → 14 MB peak; 10^9 extrapolates to ~14 GB (NOT_RUN). T10 – v0.1→v0.2 scope changes: NATIVE_SIM headers accepted; refusals/CASE_END before any state; long/unicode/newline reasons now refused; differential fuzz showed only intended tightenings. T13 – injected write/flush/fsync errors make the owner BROKEN and CASE_END unwritable (by design); the on-disk prefix stays replayable.

### Checks that held
T4: v0.1 defect reproduces in v0.1; in v0.2 a 60 KB cap sweep always refused-or-drained-and-closed. T8: `:` in ticket ids — 56 unique command ids, no collision. T9: -0.0, 5e-324, 1e-320, ±2^53, 1e308, 24-char floats within bounds; 2^53+1 and bool refused; replay == live. T11: minimal caps across 10^4/10^5 digit boundaries correct (9999 → 10001). T12: exact fit at headroom 0 accepted, +1 byte refused, nothing changed.

Fuzz: 2,560 runs / 227k operations incl. 545 zero-headroom states; 5,835 fork-and-drains with worst-case content (31.5k reserved events): no reserved event refused for bytes/counts, no refusal mutated state/file, replay == live in every run, gate invariant held at every step.

### Independent reader vs module
On all 9 cross-check journals and all 6,699 fuzz journals: reader PASS, module replay ACCEPT, reader headroom ≥ module headroom. Disagreement only on T1/T5 journals, where the reader flags the type violations. Both bound sets are sound (no line exceeded either); the reader's are tighter and hit exactly by worst-case lines (RETURN 2517, CHANNEL 1169, REFUSAL 497; SLOT within 2 bytes).

| Kind | Module | Reader |
|---|---|---|
| INFERENCE_RETURN | 2541 | 2519 |
| SLOT_DISPOSITION | 2540 | 2403 |
| CHANNEL_RESULT | 1208 | 1117 |
| CAPACITY_REFUSAL | 518 | 499 |
| CASE_END base | 561 | 542 |
| CASE_END per open ticket | 704 | 704 |

Module looseness (20-digit seq/clock/wall/slot/generation; actor ids at the token limit; ERROR status counted with output rows; unreachable CAPACITY_REFUSED disposition counted with a command id) costs headroom, not safety.

### Not covered (NOT_RUN)
Formal proof; concurrent writers; real-disk fsync/failures (used /dev/shm) beyond injected hook exceptions; token limits ≥ 10^7; journals beyond a few hundred events; hash verification in the reader (it checks `prev_sha256` link strings only); Python other than 3.12.3; non-empty asset bindings; APPLIED results (30 in fuzz plus the normal scenario). The differential fuzz stops at the first divergence per run; fuzz counts depend on the time budget.

### Rerun
```
O=out
python3 -B -I $O/independent_reservation_reader.py --selftest
python3 -B -I $O/reader_crosscheck.py                          # ~6 s, "CROSSCHECK: ALL_AGREE_PASS"
python3 -B -I $O/adversarial.py --budget 520 --seed 20261019   # ~9 min
```
