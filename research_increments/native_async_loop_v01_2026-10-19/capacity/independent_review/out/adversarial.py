#!/usr/bin/env python3
"""Adversarial search against the v0.2 byte-reservation guarantee.

Sections
  T*  targeted counterexample attempts (each prints expected vs actual)
  F   randomized fuzz over caps + event sequences: refusal immutability, gate invariants,
      fork-and-drain (every reserved event + refusals + CASE_END must be writable from
      arbitrary accepted prefixes with worst-case content), replay equality, independent reader
  D   differential fuzz v0.1 vs v0.2 under generous caps (semantic regressions)

Usage: python3 -B -I adversarial.py [--budget SECONDS] [--seed N]
Writes out/adversarial_results.json. Exit 0 always (verdict is in the output).
"""
import copy
import json
import math
import os
import random
import shutil
import sys
import time
import tracemalloc

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _u
_spec = _u.spec_from_file_location("_harness", os.path.join(HERE, "_harness.py"))
H = _u.module_from_spec(_spec); _spec.loader.exec_module(H)
M2, M1, MAX_INT = H.M2, H.M1, H.MAX_INT
RESULTS = {"targeted": [], "fuzz": {}, "differential": {}}


def record(tid, title, verdict, expected, actual, severity=None, **extra):
    row = {"id": tid, "title": title, "verdict": verdict, "expected": expected, "actual": actual}
    if severity:
        row["severity"] = severity
    row.update(extra)
    RESULTS["targeted"].append(row)
    print("[%s] %s -> %s%s" % (tid, title, verdict, (" (%s)" % severity) if severity else ""))
    print("      expected: %s" % expected)
    print("      actual:   %s" % actual)


def code(fn):
    try:
        fn()
        return "ACCEPTED"
    except Exception as e:  # noqa
        return getattr(e, "code", "%s:%s" % (type(e).__name__, str(e)[:60]))


def jpath(tag):
    return os.path.join(H.fresh_dir("adv_%s_" % tag), "j")


def base_ticket(m=M2, h=None, purpose="ORIGINAL_GOAL", ticks=None, path=None, end=100):
    h = h or H.make_header(m)
    d = H.Driver(m, h, path or jpath("t"))
    d.observe(0, wall=1)
    d.packet("p", b"abc")
    d.start("t", ticks or list(range(1, 9)), end, purpose=purpose)
    return d


def file_bytes(p):
    with open(p, "rb") as f:
        return f.read()


# ============================================================ targeted

def t1_type_confusion():
    d = base_ticket()
    rows = [[1.7976931348623157e308, -0.0, 1e16] + [0.5] * 6 for _ in range(8)]
    d.ret("t", rows=rows)
    p = d.prepare("t", 0)
    p2 = copy.deepcopy(p)
    p2["target_9d"][0] = int(1.7976931348623157e308)   # 309-digit int == float max
    p2["target_9d"][1] = 0.0                            # == -0.0
    p2["target_9d"][2] = 10**16                         # int == 1e16
    p2["desired_tick"] = float(p["desired_tick"])
    p2["known_original_failure"] = 0
    p2["actor_generation"] = False
    p2["owner"]["actor_generation"] = 0.0
    ev = d.commit(p2)
    line = len(M2.canonical(ev)) + 1
    pr = ev["body"]["prepared"]
    self_sha_ok = M2.digest({k: v for k, v in pr.items() if k != "prepared_sha256"}) == pr["prepared_sha256"]
    tgt_sha_ok = M2.digest(pr["target_9d"]) == pr["target_sha256"]
    big = max(abs(v) for v in pr["target_9d"] if type(v) is int)
    nxt = d.prepare("t", 1)
    ok, rep = H.module_replay(M2, d.path, d.h)
    rr = H.reader_check(d.path, d.h)
    record("T1", "commit_slot accepts caller prepared that is ==-equal but differently typed/serialized",
           "CONFIRMED_DEFECT", "prepared recorded exactly as _prepare computed it; |target int|<=2^53; prepared_sha256/target_sha256 bind the recorded fields",
           "ACCEPTED line=%d (module bound %d); recorded target int has %d digits; prepared_sha256 matches recorded fields=%s; target_sha256 matches recorded target_9d=%s; "
           "module-computed next prepared has earliest_apply_tick type=%s; module replay=%s; independent reader=%s first=%s"
           % (line, M2.line_bounds(d.h)["SLOT_DISPOSITION"], len(str(big)), self_sha_ok, tgt_sha_ok,
              type(nxt["earliest_apply_tick"]).__name__, "ACCEPT" if ok else rep, rr["verdict"], rr["first_violation"]),
           severity="MEDIUM (journal integrity; byte gate still bounds the line)")
    # float propagation into a module-computed reserved field longer than the module's 20-digit integer worst case
    T = 1234567890123456768  # exactly representable; repr(float(T)) has 22 chars
    d = base_ticket(ticks=[T + i for i in range(8)], end=MAX_INT)
    d.ret("t", rows=[[0.5] * 9] * 8)
    p = d.prepare("t", 0)
    p2 = copy.deepcopy(p)
    p2["desired_tick"] = float(T)
    d.commit(p2)
    nxt = d.prepare("t", 1)
    e = nxt["earliest_apply_tick"]
    record("T1b", "type-confused desired_tick propagates into module-computed earliest_apply_tick",
           "CONFIRMED_DEFECT", "earliest_apply_tick is an int with <= 20 digits (WORST_INT assumption)",
           "earliest_apply_tick=%r (%s, %d chars > 20); commit=%s (fits only because of slack elsewhere in the line)"
           % (e, type(e).__name__, len(json.dumps(e)), code(lambda: d.commit(nxt))),
           severity="LOW (same root cause as T1; per-field worst case exceeded, whole-line bound still enforced)")


class AnyEq(dict):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False
    __hash__ = None


class EvilInt(int):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    def __add__(self, other):
        return 10**3000
    __hash__ = int.__hash__


def t2_subclass_objects():
    # (a) claimed_owner that compares equal to anything
    d = base_ticket()
    d.ret("t", rows=[[0.5] * 9] * 8)
    d.slot("t", 0)
    cmd = d.s["commands"]["t:0"]
    live = code(lambda: d.b.record_channel_result("t:0", status="DROPPED", current_state_id=d.sid(), actual_target_9d=cmd["target_9d"],
                                                  claimed_owner=AnyEq({"forged_owner": "x" * 400}), wall_ns=1))
    ok, rep = H.module_replay(M2, d.path, d.h)
    record("T2a", "dict subclass with permissive __eq__ as claimed_owner", "CONFIRMED_DEFECT",
           "live writer refuses an owner that differs from the command owner",
           "live=%s; module replay of the live journal=%s" % (live, "ACCEPT" if ok else rep),
           severity="LOW-MEDIUM (needs a hostile/buggy in-process caller; live journal becomes unreplayable)")
    # (b) EvilInt desired_tick: inflates the honest earliest_apply_tick of later slots
    d = base_ticket(ticks=list(range(5, 13)))
    d.ret("t", rows=[[0.5] * 9] * 8)
    p = d.prepare("t", 0)
    p2 = copy.deepcopy(p)
    p2["desired_tick"] = EvilInt(p["desired_tick"])
    c0 = code(lambda: d.commit(p2))
    nxt = d.prepare("t", 1)
    c1 = code(lambda: d.commit(nxt))
    # head result is reserved and honest; after it the queue is empty and the slot is writable again
    d.observe(1)
    c2 = code(lambda: d.chan_head("APPLIED"))
    c3 = code(lambda: d.slot("t", 1))
    ok, rep = H.module_replay(M2, d.path, d.h)
    record("T2b", "int subclass in prepared.desired_tick (== always, + returns 10**3000)", "CONFIRMED_DEFECT",
           "a reserved SLOT_DISPOSITION computed by the module itself is always writable",
           "commit evil=%s; module-computed next prepared earliest_apply_tick has %d digits; its commit=%s; "
           "CHANNEL_RESULT APPLIED at tick 1 for desired_tick %d=%s; slot after drain=%s; module replay=%s"
           % (c0, len(str(nxt["earliest_apply_tick"])), c1, p["desired_tick"], c2, c3, "ACCEPT" if ok else rep),
           severity="LOW-MEDIUM (hostile in-process caller; reserved event refused until queue drains; live/replay divergence)")


def t3_recovery_liveness():
    rows = [[0.5] * 9] * 8
    # (a) generous caps: the slot still needs an ordinary event first
    d = base_ticket(purpose="SAFE_LOCAL_RECOVERY")
    d.ret("t", rows=rows)
    a = code(lambda: d.prepare("t", 0))
    # (b) exact event cap: no ordinary event can ever be admitted afterwards
    h = H.make_header(events=30)
    d = base_ticket(h=h, purpose="SAFE_LOCAL_RECOVERY")
    d.ret("t", rows=rows)
    pb = code(lambda: d.prepare("t", 0))
    fb = code(lambda: d.failure(True, False))
    ob = code(lambda: d.observe(50))
    tb = code(lambda: d.actor("teacher"))
    cb = code(lambda: d.close())
    unres = d.s["closed"] and d.s["tickets"]["t"]["slots"] == {}
    # (c) post-deadline variant: known failure recorded but not full failure
    h = H.make_header(deadline=10)
    d = H.Driver(M2, h, jpath("t3c"))
    d.observe(0, wall=1)
    d.failure(True, False)
    d.packet("p", b"abc")
    d.start("t", list(range(1, 9)), 100, purpose="SAFE_LOCAL_RECOVERY")
    d.ret("t", rows=rows)
    d.observe(0, deadline=11)  # same tick, deadline clock now past original_deadline_ns
    pc = code(lambda: d.prepare("t", 0))
    # (d) v0.1 comparison
    h1 = H.make_header(M1, events=30)
    d1 = base_ticket(m=M1, h=h1, purpose="SAFE_LOCAL_RECOVERY")
    d1.ret("t", rows=rows)
    pd = code(lambda: d1.prepare("t", 0))
    fd = code(lambda: d1.failure(True, False))
    record("T3", "admitted SAFE_LOCAL_RECOVERY ticket: SLOT_DISPOSITION needs an ordinary event first", "CONFIRMED_DEFECT",
           "every reserved SLOT_DISPOSITION writable without any further ordinary event (contract text)",
           "generous caps: prepare=%s; caps.events=30: prepare=%s, FULL_TASK_FAILURE=%s, OBSERVED_STATE=%s, ACTOR_TRANSITION=%s, CASE_END=%s, "
           "closed with all 8 slots censored=%s; post-deadline+known-not-full: prepare=%s; v0.1 same case: prepare=%s FULL_TASK_FAILURE=%s"
           % (a, pb, fb, ob, tb, cb, unres, pc, pd, fd),
           severity="MEDIUM (liveness of reserved events; CASE_END still guaranteed; pre-existing in v0.1, not a regression)")


def t4_v01_defect_fixed():
    # v0.1: a cap that admits INFERENCE_START but not CASE_END
    h1 = H.make_header(M1)
    need = base_ticket(m=M1, h=copy.deepcopy(h1)).s["journal_bytes"]
    h1["caps"]["journal_bytes"] = need + 10
    d1 = base_ticket(m=M1, h=h1)
    v1 = ("START=ACCEPTED", code(lambda: d1.close()))
    # v0.2: sweep caps across the whole START-admission boundary; whenever the prefix stops (any refusal), close must work
    h2 = H.make_header(M2)
    need2 = base_ticket(h=copy.deepcopy(h2)).s["journal_bytes"]
    outcomes, bad = {}, []
    for cap in range(max(1, need2 - 30000), need2 + 30000, 61):
        h = copy.deepcopy(h2)
        h["caps"]["journal_bytes"] = cap
        try:
            d = H.Driver(M2, h, jpath("t4"))
        except M2.BridgeError as e:
            outcomes[("ctor", e.code)] = outcomes.get(("ctor", e.code), 0) + 1
            continue
        stage = "done"
        for name, fn in (("observe", lambda: d.observe(0, wall=1)), ("packet", lambda: d.packet("p", b"abc")),
                         ("start", lambda: d.start("t", list(range(1, 9)), 100))):
            c = code(fn)
            if c != "ACCEPTED":
                stage = "%s=%s" % (name, c)
                break
        res = d.drain(refusals_first=False)
        key = (stage, "close=" + ("ACCEPTED" if d.s["closed"] else "REFUSED"))
        outcomes[key] = outcomes.get(key, 0) + 1
        if not d.s["closed"] or res["defects"]:
            bad.append((cap, stage, res))
    record("T4", "v0.1 byte defect (admitted START, unclosable case) re-tested on v0.2 with a cap sweep",
           "HOLDS" if v1[1] == "JOURNAL_TOTAL_BYTE_CAPACITY_REFUSED" and not bad else "CONFIRMED_DEFECT",
           "v0.1: START admitted then CASE_END refused; v0.2: at every cap, either the event is refused or the case drains+closes",
           "v0.1 %s close=%s | v0.2 sweep outcomes %s; failures=%s" % (v1[0], v1[1], {"%s/%s" % k: v for k, v in outcomes.items()}, bad[:2]))


def rechain(events):
    prev = "0" * 64
    out = []
    for ev in events:
        ev = dict(ev)
        ev["prev_sha256"] = prev
        ev.pop("sha256", None)
        ev["sha256"] = M2.digest(ev)
        prev = ev["sha256"]
        out.append(ev)
    return out


def write_events(path, events):
    with open(path, "wb") as f:
        for ev in events:
            f.write(M2.canonical(ev) + b"\n")


def t5_replay_type_laxity():
    h = H.make_header()
    d = H.Driver(M2, h, jpath("t5"))
    d.observe(5, wall=1)
    d.refuse("K", "R")
    d.close("end")
    evs = [json.loads(l) for l in file_bytes(d.path).splitlines()]
    res = {}
    for name, mut in (("seq_float", lambda e: e[2].__setitem__("seq", 2.0)),
                      ("seq_bool", lambda e: e[1].__setitem__("seq", True)),
                      ("clock_float", lambda e: e[2].__setitem__("clock", [5.0, 5000.0, 5000.0])),
                      ("wall_float", lambda e: e[2].__setitem__("wall_ns", 1.0))):
        e = copy.deepcopy(evs)
        mut(e)
        p = jpath("t5f")
        write_events(p, rechain(e))
        ok, rep = H.module_replay(M2, p, h)
        rr = H.reader_check(p, h)
        res[name] = ("ACCEPT" if ok else rep, rr["verdict"], (rr["first_violation"] or {}).get("category"))
    accepted = [k for k, v in res.items() if v[0] == "ACCEPT"]
    record("T5", "replay accepts envelope values the live writer never emits (float/bool seq, float clock)",
           "CONFIRMED_DEFECT" if accepted else "HOLDS",
           "replay refuses non-integer seq/clock (live writer only writes ints)",
           "; ".join("%s: module replay=%s, reader=%s/%s" % (k, *v) for k, v in res.items()),
           severity="LOW (replay strictness; needs a re-chained forged file; bytes still gated by actual line length)")


def t6_non_bridge_errors():
    d = base_ticket()
    tid = "t"
    snap = d.s["tickets"][tid]["snapshot_sha256"]
    rows_ok = [[0.5] * 9] * 8
    cases = {
        "return int 10**400": lambda: d.b.accept_return(tid, snapshot_sha256=snap, output_8x9=[[10**400] + [0.5] * 8] + rows_ok[1:], current_state_id=d.sid(), wall_ns=1),
        "return NaN": lambda: d.b.accept_return(tid, snapshot_sha256=snap, output_8x9=[[float("nan")] * 9] * 8, current_state_id=d.sid(), wall_ns=1),
        "return status list": lambda: d.b.accept_return(tid, snapshot_sha256=snap, output_8x9=rows_ok, current_state_id=d.sid(), wall_ns=1, status=["OK"]),
        "actor id list": lambda: d.b.transition_actor(["student"], reason="r", current_state_id=d.sid(), wall_ns=1),
        "observe non-dict": lambda: d.b.observe_state(None, wall_ns=1),
        "packet bytearray": lambda: d.b.publish_packet("q", bytearray(b"x"), wall_ns=1),
    }
    out = {}
    for name, fn in cases.items():
        before, fb = d.b.snapshot(), file_bytes(d.path)
        c = code(fn)
        out[name] = (c, d.b.snapshot() == before and file_bytes(d.path) == fb and not d.b.broken)
    d.ret(tid, rows=rows_ok)
    p = d.prepare(tid, 0)
    before, fb = d.b.snapshot(), file_bytes(d.path)
    p2 = copy.deepcopy(p); p2["purpose"] = ["ORIGINAL_GOAL"]
    out["commit purpose list"] = (code(lambda: d.commit(p2)), d.b.snapshot() == before and file_bytes(d.path) == fb)
    out["prepare auth purpose list"] = (code(lambda: d.prepare(tid, 1, auth={"state_id": "s", "purpose": ["x"], "target_sha256": None, "source_sha256": "a" * 64})), d.b.snapshot() == before)
    raw = [k for k, v in out.items() if ":" in v[0]]
    mut = [k for k, v in out.items() if not v[1]]
    # replay of a journal with an empty line / NaN token
    p = jpath("t6r")
    good = file_bytes(d.path).splitlines(keepends=True)
    with open(p, "wb") as f:
        f.write(good[0] + b"\n")
    rep_empty = H.module_replay(M2, p, d.h)[1]
    record("T6", "malformed inputs raise non-BridgeError exceptions (state/file unchanged?)",
           "CONFIRMED_DEFECT" if raw else "HOLDS", "every refusal is a BridgeError code and leaves state/file unchanged",
           "%s; state/file mutated by: %s; replay with blank line -> %s" % ({k: v[0] for k, v in out.items()}, mut or "none", rep_empty),
           severity="LOW (robustness; no mutation observed)")


def t7_token_limit_scaling():
    rows = []
    for L in (10**3, 10**4, 10**5, 10**6):
        h = H.make_header(L=L, max_line=10**9)
        tracemalloc.start()
        t0 = time.time()
        M2.line_bounds(h)
        dt = time.time() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        rows.append((L, round(dt, 3), peak))
    record("T7", "header-trusted max_token_chars drives O(L) string building in line_bounds()",
           "NOTE", "bounds computable arithmetically in O(1) memory",
           "L, seconds, peak bytes: %s; extrapolated peak for L=1e9 ~ %.1f GB (NOT_RUN)" % (rows, rows[-1][2] / 1e6 * 1e9 / 1e9),
           severity="LOW (header is externally pinned/trusted; replay and constructor both pay it)")


def t8_colon_ids():
    h = H.make_header(L=8)
    d = H.Driver(M2, h, jpath("t8"))
    d.observe(0, wall=1)
    d.packet("p", b"z")
    ids = ["a", "a:", "a:0", ":0", "a:0:0", "::", ":"]
    for j, t in enumerate(ids):
        d.start(t, [1 + 8 * j + i for i in range(8)], 1000)
        d.ret(t, rows=[[0.5] * 9] * 8)
    codes = set()
    for t in ids:
        for i in range(8):
            codes.add(code(lambda: d.slot(t, i)))
    cids = d.s["queue"]
    record("T8", "ticket ids containing ':' (command_id collisions)", "HOLDS",
           "command_id = ticket+':'+digit is injective; no DUPLICATE_COMMAND",
           "slot outcomes=%s; %d command ids, %d unique; drain=%s" % (sorted(codes), len(cids), len(set(cids)), {k: v for k, v in d.drain().items() if k != "written"}))


def t9_float_edges():
    h = H.make_header(L=8)
    d = H.Driver(M2, h, jpath("t9"))
    d.observe(0, wall=1)
    d.packet("p", b"z")
    vals = H.EDGE_VALUES
    out = {}
    for j in range(0, len(vals), 9):
        row = (vals[j:j + 9] + [0.5] * 9)[:9]
        t = "f%d" % j
        d.start(t, list(range(1, 9)), 100)
        d.ret(t, rows=[row] * 8)
        d.slot(t, 0)
    for bad in (2**53 + 1, -(2**53) - 1, True, float("inf")):
        t = "b%s" % str(bad)[:5]
        d.start(t, list(range(1, 9)), 100)
        out[repr(bad)] = code(lambda: d.ret(t, rows=[[bad] + [0.5] * 8] * 8))
    while d.s["queue"]:
        d.chan_head("REJECTED")
    res = d.drain()
    ok, rep = H.module_replay(M2, d.path, d.h)
    same = ok and M2.canonical(rep._s) == M2.canonical(d.s)
    rr = H.reader_check(d.path, d.h)
    record("T9", "unusual floats/ints in targets (-0.0, 5e-324, 1e-320, +-2^53, 1e308, 24-char floats)", "HOLDS",
           "accepted values serialize within bounds; out-of-rule values refused; replay identical",
           "refusals=%s; drain defects=%s; replay canonical-identical=%s; reader=%s min_slack=%s"
           % (out, res["defects"], same, rr["verdict"], rr["min_reserved_slack"]))


def t10_scope_changes():
    h = H.make_header(mode="NATIVE_SIM")
    v2 = code(lambda: H.Driver(M2, h, jpath("t10")))
    h1 = H.to_v01(h)
    h1["mode"] = "NATIVE_SIM"
    v1 = code(lambda: H.Driver(M1, h1, jpath("t10")))
    # stateless close / refusal before any state
    d2 = H.Driver(M2, H.make_header(), jpath("t10b"))
    s2 = (code(lambda: d2.refuse("K", "R")), code(lambda: d2.close("early")))
    d1 = H.Driver(M1, H.make_header(M1), jpath("t10c"))
    s1 = (code(lambda: d1.refuse("K", "R")), code(lambda: d1.close("early")))
    # tightened validation: long/unicode/empty tokens that v0.1 accepted
    def tok_case(m, rk, reason):
        d = H.Driver(m, H.make_header(m), jpath("t10d"))
        d.observe(0, wall=1)
        return code(lambda: d.refuse(rk, reason)), code(lambda: d.close(reason))
    toks = {"empty request_kind": ("", "r"), "reason 65 chars": ("k", "x" * 65), "unicode reason": ("k", "ré"), "newline": ("k", "a\nb")}
    tv = {k: (tok_case(M1, *v), tok_case(M2, *v)) for k, v in toks.items()}
    record("T10", "v0.1 -> v0.2 semantic scope changes", "NOTE",
           "only byte-reservation tightening",
           "NATIVE_SIM header: v0.1=%s v0.2=%s; refusal/close with no state: v0.1=%s v0.2=%s; token tightening (v0.1, v0.2) [refusal, close]: %s"
           % (v1, v2, s1, s2, tv), severity="LOW/INFO (NATIVE_SIM accepted by an unchanged CPU-fixture code path; callers' long/unicode reasons now refused)")


def t11_min_cap_boundaries():
    rows = []
    bad = []
    def mc(L, r):
        return H.min_cap(H.make_header(L=L, refusal_reserve=r, actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)),
                                       kinds={"CAPACITY_REFUSAL": r}), lo=1, hi=10**7)
    plan = []
    for L in (1, 7, 64):
        c1, c2 = mc(L, 1), mc(L, 2)
        rs = set(range(1, 9))
        for T in (10**4, 10**5):
            r0 = max(1, (T - c1) // (c2 - c1) + 1)
            rs |= set(range(max(1, r0 - 3), r0 + 4))
        plan.append((L, sorted(rs)))
    for L, rlist in plan:
        for r in rlist:
            h = H.make_header(L=L, refusal_reserve=r, actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)),
                              kinds={"CAPACITY_REFUSAL": max(r, 1)})
            c = H.min_cap(h, lo=1, hi=10**7)
            hm = copy.deepcopy(h); hm["caps"]["journal_bytes"] = c - 1
            below = H.construct_ok(M2, hm)
            hh = copy.deepcopy(h); hh["caps"]["journal_bytes"] = c
            d = H.Driver(M2, hh, jpath("t11"))
            head0 = d.b.capacity_report()["headroom"]
            res = d.drain(refusals_first=True)
            rr = H.reader_check(d.path, hh)
            mono = all(H.construct_ok(M2, dict(copy.deepcopy(h), caps=dict(h["caps"], journal_bytes=c + k))) for k in (1, 2, 3, 7))
            rows.append((L, r, c, head0))
            if below or res["defects"] or res["unexpected"] or rr["verdict"] != "PASS" or d.s["journal_bytes"] > c or not mono:
                bad.append((L, r, c, below, res, rr["first_violation"]))
    # exact digit-boundary sweep: pad attempt_id one byte at a time so the minimal cap walks across 10**4 and 10**5
    near = []
    for T in (10**4, 10**5):
        L = 16
        hb = H.make_header(L=L, refusal_reserve=1, actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)), kinds={"CAPACITY_REFUSAL": 1})
        c1 = H.min_cap(hb, lo=1, hi=10**7)
        hb2 = copy.deepcopy(hb); hb2["caps"]["refusal_reserve"] = 2; hb2["caps"]["kinds"]["CAPACITY_REFUSAL"] = 2
        delta = H.min_cap(hb2, lo=1, hi=10**7) - c1
        r = max(1, (T - c1) // delta + 1)
        def hdr(k):
            h = H.make_header(L=L, refusal_reserve=r, actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)), kinds={"CAPACITY_REFUSAL": r})
            h["attempt_id"] = "cpu-attempt" + "a" * k
            return h
        k0 = max(0, T - H.min_cap(hdr(0), lo=max(1, T - 3 * delta), hi=T + 3 * delta) - 6)
        for k in range(k0, k0 + 14):
            h = hdr(k)
            c = H.min_cap(h, lo=max(1, T - 3 * delta), hi=T + 3 * delta)
            if abs(c - T) <= 3:
                hm = copy.deepcopy(h); hm["caps"]["journal_bytes"] = c - 1
                below = H.construct_ok(M2, hm)
                hh = copy.deepcopy(h); hh["caps"]["journal_bytes"] = c
                d = H.Driver(M2, hh, jpath("t11b"))
                res = d.drain(refusals_first=True)
                rr = H.reader_check(d.path, hh)
                near.append((T, k, c, below, bool(res["defects"]), d.s["closed"], rr["verdict"], d.s["journal_bytes"]))
                if below or res["defects"] or not d.s["closed"] or rr["verdict"] != "PASS":
                    bad.append(("digit", T, k, c, below, res, rr["first_violation"]))
    crossings = [(T, k, c, "closed=%s bytes=%d reader=%s" % (cl, b, rv)) for T, k, c, bel, df, cl, rv, b in near]
    record("T11", "minimal journal_bytes caps (cap digits inside CASE_BEGIN) then all refusals + CASE_END",
           "HOLDS" if not bad else "CONFIRMED_DEFECT",
           "cap-1 refused at construction; at min cap every remaining refusal and CASE_END fit; monotone above",
           "%d header variants + %d digit-boundary variants, %d failures %s; min caps within 3 of 10^4/10^5 (T, pad, min_cap, result): %s; headroom at min cap ranges %s..%s"
           % (len(rows), len(near), len(bad), bad[:3], crossings, min(x[3] for x in rows), max(x[3] for x in rows)))


def t12_exact_fit():
    """An ordinary event that leaves headroom exactly 0 is admitted; one byte more is refused unchanged."""
    def setup(cap):
        h = H.make_header(L=16)
        h["caps"]["journal_bytes"] = cap
        d = H.Driver(M2, h, jpath("t12"))
        d.observe(0, wall=1)
        return d
    def packet_line(d, pid, n):
        s = d.s
        data = bytes(n)
        body = {"packet_id": pid, "public_bytes_b64": M2.bytes64(data), "sha256": M2.sha256(data), "state_id": d.sid()}
        ev = {"schema": M2.EVENT_SCHEMA, "seq": s["events"], "prev_sha256": s["chain"], "kind": "PUBLIC_PACKET", "body": body,
              "clock": [s["state"][k] for k in ("tick", "time_ns", "deadline_time_ns")], "wall_ns": d.wall}
        ev["sha256"] = M2.digest(ev)
        return len(M2.canonical(ev)) + 1
    d = setup(200000)
    head = d.b.capacity_report()["headroom"]
    x = head - packet_line(d, "q", 0)
    pl = 1 + x % 4
    n = 3 * ((x - (pl - 1)) // 4)
    target = (pl, n) if packet_line(d, "q" * pl, n) == head else None
    if not target:
        record("T12", "exact-fit ordinary event at headroom 0", "NOT_RUN", "-", "no exact-fit packet found")
        return
    pl, n = target
    a = code(lambda: d.packet("q" * pl, bytes(n)))
    h0 = d.b.capacity_report()["headroom"]
    res = d.drain(refusals_first=False)
    d2 = setup(200000)
    before, fb = d2.b.snapshot(), file_bytes(d2.path)
    b = code(lambda: d2.packet("q" * (pl + 1), bytes(n)))
    unchanged = d2.b.snapshot() == before and file_bytes(d2.path) == fb
    record("T12", "exact-fit ordinary event at headroom 0, then worst-case drain", "HOLDS" if a == "ACCEPTED" and h0 == 0 and not res["defects"] and b == "BYTE_RESERVATION_REFUSED" and unchanged else "CONFIRMED_DEFECT",
           "fit -> ACCEPTED headroom 0, drain ok; +1 byte -> BYTE_RESERVATION_REFUSED, state/file unchanged",
           "fit=%s headroom_after=%s drain_defects=%s blocked=%s; +1 byte=%s unchanged=%s" % (a, h0, res["defects"], res["blocked"], b, unchanged))


def t13_hook_failures():
    out = {}
    for stage in ("before_write", "after_write", "after_flush", "after_fsync"):
        def hook(ev_stage, event, f, stage=stage):
            if ev_stage == stage and event["kind"] == "OBSERVED_STATE":
                raise OSError("injected")
        h = H.make_header()
        p = jpath("t13")
        d = H.Driver(M2, h, p, hook=hook)
        before = d.b.snapshot()
        c = code(lambda: d.observe(0, wall=1))
        ok, rep = H.module_replay(M2, p, h)
        rr = H.reader_check(p, h)
        out[stage] = (c, d.b.broken, d.b.snapshot() == before, "ACCEPT(%d ev)" % rep._s["events"] if ok else rep, rr["verdict"], code(lambda: d.close()))
    record("T13", "persist hook failures (persistence uncertainty)", "NOTE",
           "live owner BROKEN; on-disk prefix replayable and within reservation",
           "; ".join("%s: %s broken=%s state_unchanged=%s replay=%s reader=%s close=%s" % (k, *v) for k, v in out.items()),
           severity="INFO (by design: a BROKEN owner can no longer write CASE_END; outside the byte guarantee)")


# ============================================================ fuzz

ALPH = H.TOKEN_ALPHABET


def rtok(rnd, L, pmax=0.35, pcolon=0.3):
    n = L if rnd.random() < pmax else rnd.randint(1, L)
    s = [rnd.choice(ALPH) for _ in range(n)]
    if n >= 2 and rnd.random() < pcolon:
        s[rnd.randrange(n)] = ":"
    return "".join(s)


def bad_tok(rnd, L):
    return rnd.choice(["", "x" * (L + 1), "é", 'a"b', "a\\b", "a\nb", "\x7f", 7, None])


def gen_op(rnd, s, h, L, diff=False, clean=False):
    w = s["highwater"][3]
    wall = min(MAX_INT, max(0, w) + rnd.choice([0, 0, 1, 7, 1000]))
    if rnd.random() < 0.02:
        wall = MAX_INT
    r = rnd.random()
    P = {"wall": wall}
    bt = (lambda: rtok(rnd, L)) if clean else (lambda: bad_tok(rnd, L))
    if r < 0.14:
        P.update(op="observe", dt=rnd.choice([0, 1, 1, 1, 2, 3, 10, 1000]) if rnd.random() > 0.03 else -1,
                 dtime=rnd.choice([0, 1000, 10**6]), ddead=rnd.choice([0] * 12 + [1000, 10**9]) if rnd.random() > 0.02 else -5,
                 sid=rtok(rnd, L), lawful=rnd.random() < 0.93, maxclock=rnd.random() < 0.02, to_head=rnd.random() < 0.35)
    elif r < 0.23:
        P.update(op="packet", pid=rtok(rnd, L), n=rnd.choice([0, 1, 5, 50, 500, 3000]), seed=rnd.random(),
                 fill=(not diff) and rnd.random() < 0.25)
    elif r < 0.38:
        base = rnd.choice([1, 1, 2, 3, 5, 0]) if rnd.random() > 0.03 else -1
        offs = sorted(rnd.sample(range(0, 24), 8))
        P.update(op="start", tid=rtok(rnd, L), base=base, offs=offs, end_off=rnd.choice([0, 3, 8, 20, 100, MAX_INT]),
                 purpose=rnd.choice(["ORIGINAL_GOAL", "ORIGINAL_GOAL", "SAFETY_ABORT", "SAFE_LOCAL_RECOVERY"]),
                 wrong_actor=rnd.random() < 0.04, dup=rnd.random() < 0.05)
    elif r < 0.51:
        P.update(op="ret", pick=rnd.random(), status="ERROR" if rnd.random() < 0.2 else "OK",
                 rows=rnd.choice(["worst", "edge", "edge", "small"]), bad=None if clean else rnd.choice([None] * 12 + ["bigint", "bool", "short", "nan"]))
    elif r < 0.72:
        P.update(op="slot", pick=rnd.random(), auth="expected" if clean else rnd.choice(["expected"] * 6 + ["none", "other_shape", "garbage"]),
                 tamper=None if clean else rnd.choice([None] * 10 + ["disposition", "drop_key", "stale_queue"]))
    elif r < 0.84:
        P.update(op="chan", status=rnd.choice([None, None, "APPLIED", "REJECTED", "DROPPED"]), wrong=rnd.random() < 0.05)
    elif r < 0.85:
        P.update(op="actor", pick=rnd.randrange(len(h["actors"]) + (0 if clean else 1)), reason=rtok(rnd, L) if rnd.random() > 0.05 else bt())
    elif r < 0.88:
        k = rnd.random() < 0.6
        P.update(op="failure", known=k, full=k and rnd.random() < 0.4)
    elif r < 0.93:
        P.update(op="refusal", rk=rtok(rnd, L) if rnd.random() > 0.1 else bt(), reason=rtok(rnd, L) if rnd.random() > 0.1 else bt())
        if clean and s["state"] is None:
            P.update(op="garbage", variant=99, tok="x")
    elif r < 0.995:
        if clean:
            return gen_op(rnd, s, h, L, diff, clean)
        P.update(op="garbage", variant=rnd.randrange(14), tok=bad_tok(rnd, L))
    else:
        P.update(op="close", reason=rtok(rnd, L))
    return P


def rows_for(P):
    kind = P["rows"]
    rnd = random.Random(repr((P["pick"], kind)))
    if kind == "worst":
        rows = [H.worst_row(i) for i in range(8)]
    elif kind == "edge":
        rows = [[rnd.choice(H.EDGE_VALUES) for _ in range(9)] for _ in range(8)]
    else:
        rows = [[round(rnd.uniform(-2, 2), 3) for _ in range(9)] for _ in range(8)]
    b = P["bad"]
    if b == "bigint":
        rows[0][0] = 2**53 + 1
    elif b == "bool":
        rows[0][0] = True
    elif b == "short":
        rows = rows[:7]
    elif b == "nan":
        rows[0][0] = float("nan")
    return rows


def exec_op(m, b, h, P):
    s = b._s
    op, wall = P["op"], P["wall"]
    if op == "observe":
        cur = s["state"]
        hw = s["highwater"]
        tick = max(0, min(MAX_INT - 10**7, (cur["tick"] if cur else 0) + P["dt"]))
        if P.get("to_head") and cur and s["queue"]:
            want = s["commands"][s["queue"][0]]["desired_tick"]
            if want >= cur["tick"]:
                tick = want
        tn = max(0, hw[1]) + P["dtime"]
        dl = max(0, hw[2]) + P["ddead"]
        if P["maxclock"]:
            tn = dl = MAX_INT
        st = {"attempt_id": h["attempt_id"], "native_epoch": h["native_epoch"], "state_id": P["sid"],
              "physical_state_sha256": (P["sid"].encode().hex() * 64)[:64], "tick": tick, "time_ns": min(tn, MAX_INT),
              "deadline_clock_id": h["deadline_clock_id"], "deadline_time_ns": min(dl, MAX_INT),
              "collector_source_sha256": h["collector_source_sha256"], "lawful_state": P["lawful"]}
        return b.observe_state(st, wall_ns=wall)
    if op == "packet":
        n = P["n"]
        if P.get("fill") and hasattr(b, "capacity_report"):
            head = b.capacity_report()["headroom"]
            n = max(0, (head - 400) * 3 // 4)
            lo, hi = 0, max(0, n + 600)
            # largest n whose staged packet passes the pure byte gate
            def fits(k):
                try:
                    b._stage("PUBLIC_PACKET", {"packet_id": P["pid"], "public_bytes_b64": m.bytes64(bytes(k)), "sha256": m.sha256(bytes(k)),
                                               "state_id": s["state"]["state_id"] if s["state"] else None}, wall_ns=wall, clock=[s["state"][k2] for k2 in ("tick", "time_ns", "deadline_time_ns")] if s["state"] else None)
                    return True
                except Exception:
                    return False
            if not fits(0):
                n = 0
            else:
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if fits(mid):
                        lo = mid
                    else:
                        hi = mid - 1
                n = lo
            data = bytes(n)
        else:
            data = random.Random(P["seed"]).randbytes(n)
        return b.publish_packet(P["pid"], data, wall_ns=wall)
    if op == "start":
        tick = s["state"]["tick"] if s["state"] else 0
        tid = P["tid"]
        if P["dup"] and s["tickets"]:
            tid = next(iter(s["tickets"]))
        data = m.base64.b64decode(s["packets"][-1]["public_bytes_b64"]) if s["packets"] else b""
        ticks = [tick + P["base"] + o for o in P["offs"]]
        end = min(MAX_INT, tick + P["end_off"])
        actor = s["actor_id"] if not P["wrong_actor"] else "nobody"
        return b.start_inference(tid, actor_id=actor, actual_input_bytes=data, desired_ticks=ticks, declared_end_tick=end,
                                 purpose=P["purpose"], wall_ns=wall)
    if op == "ret":
        un = [t for t, v in s["tickets"].items() if v["return"] is None]
        tid = un[int(P["pick"] * len(un))] if un else "nope"
        t = s["tickets"].get(tid)
        snap = t["snapshot_sha256"] if t else "0" * 64
        rows = rows_for(P) if P["status"] == "OK" else None
        return b.accept_return(tid, snapshot_sha256=snap, output_8x9=rows, current_state_id=s["state"]["state_id"] if s["state"] else "x",
                               wall_ns=wall, status=P["status"])
    if op == "slot":
        cand = [(t, i) for t, v in s["tickets"].items() if v["return"] is not None for i in range(8) if str(i) not in v["slots"]]
        if not cand:
            cand = [("nope", 0)]
        tid, i = cand[int(P["pick"] * len(cand))]
        t = s["tickets"].get(tid)
        purpose = t["snapshot"]["purpose"] if t else "ORIGINAL_GOAL"
        sid = s["state"]["state_id"] if s["state"] else "x"
        q = b.queue_snapshot()["sha256"]
        a = None
        if P["auth"] == "expected" and t and purpose != "ORIGINAL_GOAL":
            out = t["return"]["output_8x9"]
            a = {"state_id": sid, "purpose": purpose, "target_sha256": None if out is None else m.target_sha(out[i]),
                 "source_sha256": h["authorization_source_sha256"]}
        elif P["auth"] == "other_shape":
            a = {"state_id": "o", "purpose": "SAFETY_ABORT", "target_sha256": None, "source_sha256": "e" * 64}
        elif P["auth"] == "garbage":
            a = {"state_id": 5}
        prepared = b.prepare_slot(tid, i, current_state_id=sid, queue_sha256=q, purpose=purpose, authorization=a)
        if P["tamper"] == "disposition":
            prepared["disposition"] = "PADDING" if prepared["disposition"] != "PADDING" else "STALE"
        elif P["tamper"] == "drop_key":
            prepared.pop("owner")
        elif P["tamper"] == "stale_queue":
            prepared["queue_sha256"] = "0" * 64
        return b.commit_slot(prepared, current_state_id=prepared.get("current_state_id"), queue_sha256=prepared.get("queue_sha256"), wall_ns=wall)
    if op == "chan":
        sid = s["state"]["state_id"] if s["state"] else "x"
        if not s["queue"]:
            return b.record_channel_result("nope:0", status="DROPPED", current_state_id=sid, actual_target_9d=[0.0] * 9, claimed_owner={}, wall_ns=wall)
        cid = s["queue"][0]
        cmd = s["commands"][cid]
        st = P["status"]
        if st is None:
            tick = s["state"]["tick"]
            st = "APPLIED" if tick >= cmd["ready_tick"] and tick == cmd["desired_tick"] and s["last_applied_tick"] != tick else "REJECTED"
        tgt = copy.deepcopy(cmd["target_9d"])
        if P["wrong"]:
            tgt[0] = 12345.0
        return b.record_channel_result(cid, status=st, current_state_id=sid, actual_target_9d=tgt, claimed_owner=copy.deepcopy(cmd["owner"]), wall_ns=wall)
    if op == "actor":
        acts = [a["actor_id"] for a in h["actors"]] + ["nobody"]
        return b.transition_actor(acts[P["pick"]], reason=P["reason"], current_state_id=s["state"]["state_id"] if s["state"] else "x", wall_ns=wall)
    if op == "failure":
        return b.record_failure(known_original_failure=P["known"], original_full_failure=P["full"], evidence_sha256="cd" * 32,
                                current_state_id=s["state"]["state_id"] if s["state"] else "x", wall_ns=wall)
    if op == "refusal":
        return b.record_capacity_refusal(P["rk"], P["reason"], wall_ns=wall)
    if op == "close":
        return b.close(reason=P["reason"], wall_ns=wall)
    if op == "garbage":
        v, tk = P["variant"], P["tok"]
        sid = s["state"]["state_id"] if s["state"] else "x"
        st = copy.deepcopy(s["state"]) if s["state"] else None
        if v == 0 and st:
            st["tick"] = True; st["state_id"] = "g"
            return b.observe_state(st, wall_ns=wall)
        if v == 1 and st:
            st["tick"] = float(st["tick"]); st["state_id"] = "g2"
            return b.observe_state(st, wall_ns=wall)
        if v == 2 and st:
            st["state_id"] = tk
            return b.observe_state(st, wall_ns=wall)
        if v == 3:
            return b.publish_packet(tk, b"x", wall_ns=wall)
        if v == 4:
            return b.publish_packet("ok", bytearray(b"x"), wall_ns=wall)
        if v == 5:
            return b.record_capacity_refusal("k", "r", wall_ns=-1)
        if v == 6:
            return b.record_capacity_refusal("k", "r", wall_ns=True)
        if v == 7:
            return b.record_capacity_refusal("k", "r", wall_ns=float(max(0, s["highwater"][3])))
        if v == 8:
            return b.record_capacity_refusal("k", "r", wall_ns=max(0, s["highwater"][3]) - 1 if s["highwater"][3] > 0 else -1)
        if v == 9:
            return b.close(reason=tk, wall_ns=wall)
        if v == 10:
            return b.commit_slot(None, current_state_id=sid, queue_sha256="0" * 64, wall_ns=wall)
        if v == 11:
            return b.transition_actor("nobody", reason="r", current_state_id=sid, wall_ns=wall)
        if v == 12:
            return b.record_failure(known_original_failure="yes", original_full_failure=False, evidence_sha256="cd" * 32, current_state_id=sid, wall_ns=wall)
        if v == 13 and s["tickets"]:
            tid = next(iter(s["tickets"]))
            return b.start_inference(tid, actor_id=s["actor_id"], actual_input_bytes=b"", desired_ticks=tuple(range(8)), declared_end_tick=1, wall_ns=wall)
        raise H.M2.BridgeError("GARBAGE_NOOP")
    raise AssertionError(op)


def random_header(rnd):
    L = rnd.choice([1, 2, 3, 8, 16, 64, 100])
    events = rnd.choice([rnd.randint(30, 90), rnd.randint(90, 400), 100000])
    tickets = rnd.randint(1, 8)
    rr = rnd.randint(1, 10)
    kinds = {}
    if rnd.random() < 0.35:
        for k in ("INFERENCE_START", "INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "OBSERVED_STATE", "ACTOR_TRANSITION", "PUBLIC_PACKET"):
            if rnd.random() < 0.4:
                kinds[k] = rnd.randint(1, 40)
        kinds["CASE_END"] = rnd.choice([1, 1, 2])
        kinds["CAPACITY_REFUSAL"] = rr + rnd.choice([0, 0, 1, 5])
    hist = rnd.randint(1, 6)
    h = H.make_header(L=L, events=events, tickets=tickets, inflight=rnd.randint(1, tickets),
                      commands=rnd.choice([8, 16, rnd.randint(8, 80), 16000]), refusal_reserve=rr,
                      kinds=kinds, latency=rnd.choice([1, 1, 1, 1, 2, 5, 10**6]), packet_archive=rnd.choice([hist, hist + 3, 3000]),
                      history_window=hist, asset_bytes=rnd.choice([3000, 20000000]),
                      actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)) if L < 7 or rnd.random() < 0.5 else ("student", "teacher"))
    b = M2.line_bounds(h)
    need = max(max(b[k] for k in M2.FIXED_LINE_KINDS), M2.end_bound(b, 1))
    h["caps"]["max_line_bytes"] = need + rnd.choice([0, 0, 5, b["CASE_END_PER_TICKET"], 4 * b["CASE_END_PER_TICKET"], 10**6])
    return h


class Stats(dict):
    def inc(self, k, n=1):
        self[k] = self.get(k, 0) + n


def checked(m, drv, P, stats, anomalies, tag):
    b = drv.b
    before = b.snapshot()
    fb = file_bytes(drv.path) if not b._s["closed"] else None
    try:
        exec_op(m, b, drv.h, P)
        return True
    except Exception as e:  # noqa
        kind = getattr(e, "code", None) or type(e).__name__
        stats.inc(("refused", P["op"], kind if hasattr(e, "code") else "RAW:" + kind))
        if b.snapshot() != before or (fb is not None and file_bytes(drv.path) != fb) or b.broken:
            anomalies.append({"type": "REFUSAL_MUTATED_STATE_OR_FILE", "tag": tag, "op": P, "error": kind})
        return False


def invariants(drv, anomalies, tag):
    s = drv.s
    cap = drv.h["caps"]["journal_bytes"]
    if os.path.getsize(drv.path) != s["journal_bytes"]:
        anomalies.append({"type": "FILE_SIZE_MISMATCH", "tag": tag})
    if not s["closed"]:
        r = M2.byte_reserve(s)
        if s["journal_bytes"] + r > cap:
            anomalies.append({"type": "GATE_INVARIANT_BROKEN", "tag": tag, "bytes": s["journal_bytes"], "reserve": r})
        left = drv.h["caps"]["refusal_reserve"] - s["refusals"]
        if s["events"] + s["reserved_events"] + 1 + max(0, left) > drv.h["caps"]["events"]:
            anomalies.append({"type": "COUNT_INVARIANT_BROKEN", "tag": tag})


def wrap(m, h, b, path):
    d = H.Driver.__new__(H.Driver)
    d.m, d.h, d.path, d.b = m, h, path, b
    d.L = h["caps"].get("max_token_chars", 64)
    d.wall, d.nstate = max(0, b._s["highwater"][3]), 0
    return d


def post_checks(drv, stats, anomalies, tag, module_min_head):
    ok, rep = H.module_replay(M2, drv.path, drv.h)
    if not ok:
        anomalies.append({"type": "LIVE_JOURNAL_REPLAY_REFUSED", "tag": tag, "error": rep})
    elif rep._s != drv.s:
        anomalies.append({"type": "REPLAY_STATE_DIFFERS", "tag": tag})
    rr = H.reader_check(drv.path, drv.h)
    stats.inc("reader_runs")
    if rr["verdict"] != "PASS":
        anomalies.append({"type": "READER_DISAGREES", "tag": tag, "first": rr["first_violation"]})
    if module_min_head is not None and rr["min_headroom_while_open"] is not None and rr["min_headroom_while_open"] < module_min_head:
        anomalies.append({"type": "READER_HEADROOM_BELOW_MODULE", "tag": tag})
    for k, v in rr["min_reserved_slack"].items():
        cur = stats.get(("min_slack_reader", k))
        stats[("min_slack_reader", k)] = v if cur is None else min(cur, v)
    mb = M2.line_bounds(drv.h)
    with open(drv.path, "rb") as f:
        for raw in f:
            ev = json.loads(raw)
            k = ev["kind"]
            if k == "SLOT_DISPOSITION":
                stats.inc(("disposition", ev["body"]["prepared"]["disposition"]))
            elif k == "CHANNEL_RESULT":
                stats.inc(("channel", ev["body"]["status"]))
            if k in mb:
                cur = stats.get(("min_slack_module", k))
                stats[("min_slack_module", k)] = mb[k] - len(raw) if cur is None else min(cur, mb[k] - len(raw))


def fuzz(budget, seed):
    rnd = random.Random(seed)
    stats, anomalies = Stats(), []
    t_end = time.time() + budget
    run = 0
    while time.time() < t_end:
        run += 1
        h = random_header(rnd)
        tag = "seed%d-run%d" % (seed, run)
        try:
            c = H.min_cap(h, lo=1, hi=10**8)
        except M2.BridgeError as e:
            stats.inc(("header_rejected", e.code))
            continue
        except AssertionError:
            stats.inc(("header_rejected", "COUNT_RESERVE_UNSATISFIABLE"))
            continue
        slack = rnd.choice([0, rnd.randint(0, 400), rnd.randint(400, 6000), rnd.randint(6000, 60000), rnd.randint(60000, 400000)])
        h["caps"]["journal_bytes"] = c + slack
        dd = H.fresh_dir("fz_")
        path = os.path.join(dd, "j")
        try:
            drv = H.Driver(M2, h, path)
        except M2.BridgeError as e:
            anomalies.append({"type": "CONSTRUCTOR_REFUSED_AT_MIN_CAP", "tag": tag, "code": e.code})
            continue
        L = h["caps"]["max_token_chars"]
        log = []
        heads = [drv.b.capacity_report()["headroom"]]
        nops = rnd.randint(15, 160)
        seeded = []
        if rnd.random() < 0.85:
            seeded = [{"wall": 1, "op": "observe", "dt": 0, "dtime": 0, "ddead": 0, "sid": rtok(rnd, L), "lawful": True, "maxclock": False},
                      {"wall": 1, "op": "packet", "pid": rtok(rnd, L), "n": rnd.choice([0, 3, 40]), "seed": rnd.random(), "fill": False}]
        for i in range(nops):
            if drv.s["closed"]:
                break
            P = seeded.pop(0) if seeded else gen_op(rnd, drv.s, h, L)
            if checked(M2, drv, P, stats, anomalies, tag):
                stats.inc(("accepted", P["op"]))
                log.append((P, drv.s["journal_bytes"]))
                invariants(drv, anomalies, tag)
                if not drv.s["closed"]:
                    heads.append(drv.b.capacity_report()["headroom"])
                    if heads[-1] < 0:
                        anomalies.append({"type": "NEGATIVE_HEADROOM", "tag": tag})
        stats.inc("runs")
        stats.inc("ops", nops)
        stats.inc("zero_headroom_states", sum(1 for x in heads if x == 0))
        stats.inc("tight_states_lt_500", sum(1 for x in heads if x < 500))
        # fork-and-drain from random accepted prefixes, plus the final state
        forks = sorted(set(rnd.sample(range(0, len(log) + 1), min(len(log) + 1, rnd.choice([1, 2, 3])))))
        if not drv.s["closed"]:
            forks = [k for k in forks if k != len(log)]
        for k in forks:
            fp = os.path.join(dd, "fork%d" % k)
            fd = H.Driver(M2, h, fp)
            okk = True
            for P, _ in log[:k]:
                try:
                    exec_op(M2, fd.b, h, P)
                except Exception as e:  # noqa
                    anomalies.append({"type": "NONDETERMINISTIC_REEXEC", "tag": tag, "op": P, "error": str(e)})
                    okk = False
                    break
            if not okk:
                continue
            prefix_len = log[k - 1][1] if k else None
            if k and file_bytes(fp) != file_bytes(path)[:prefix_len]:
                anomalies.append({"type": "FORK_PREFIX_DIFFERS", "tag": tag})
            if fd.s["closed"]:
                continue
            fd.wall = max(0, fd.s["highwater"][3])
            res = fd.drain(random.Random(rnd.random()), error_prob=rnd.choice([0, 0.2]), refusals_first=None)
            stats.inc("drains")
            stats.inc("drain_events", res["written"])
            stats.inc("drain_blocked_slots", len(res["blocked"]))
            for x in res["blocked"]:
                stats.inc(("drain_blocked", x[2]))
            if res["defects"]:
                anomalies.append({"type": "RESERVED_EVENT_REFUSED", "tag": tag, "fork": k, "defects": res["defects"]})
            if res["unexpected"]:
                anomalies.append({"type": "DRAIN_UNEXPECTED", "tag": tag, "fork": k, "unexpected": res["unexpected"][:3]})
            if not fd.s["closed"]:
                anomalies.append({"type": "CASE_NOT_CLOSABLE", "tag": tag, "fork": k})
            if fd.s["journal_bytes"] > h["caps"]["journal_bytes"]:
                anomalies.append({"type": "CAP_EXCEEDED", "tag": tag})
            post_checks(fd, stats, anomalies, tag + "-fork%d" % k, min(heads) if k == len(log) else None)
        # final drain on the original live bridge
        if not drv.s["closed"]:
            fdrv = wrap(M2, h, drv.b, path)
            res = fdrv.drain(random.Random(rnd.random()), refusals_first=None)
            stats.inc("drains")
            if res["defects"]:
                anomalies.append({"type": "RESERVED_EVENT_REFUSED", "tag": tag, "fork": "final", "defects": res["defects"]})
            if not drv.s["closed"]:
                anomalies.append({"type": "CASE_NOT_CLOSABLE", "tag": tag, "fork": "final"})
            stats.inc("drain_blocked_slots", len(res["blocked"]))
            for x in res["blocked"]:
                stats.inc(("drain_blocked", x[2]))
        post_checks(drv, stats, anomalies, tag + "-final", min(heads))
        shutil.rmtree(dd, ignore_errors=True)
    return stats, anomalies


# ============================================================ differential v0.1 vs v0.2

def project(s):
    return {"events": s["events"], "kinds": dict(sorted(s["kind_counts"].items())), "refusals": s["refusals"], "closed": s["closed"],
            "tickets": [(t, v["return"]["status"] if v["return"] else None, sorted((k, x["disposition"]) for k, x in v["slots"].items())) for t, v in s["tickets"].items()],
            "queue": list(s["queue"]), "cmd_status": sorted((c, v["status"]) for c, v in s["commands"].items()), "actor": (s["actor_id"], s["actor_generation"])}


def differential(budget, seed, clean=False):
    rnd = random.Random(seed)
    t_end = time.time() + budget
    mism, runs, ops, matched_runs = Stats(), 0, 0, 0
    examples = {}
    while time.time() < t_end:
        runs += 1
        h2 = H.make_header(L=rnd.choice([8, 64]), tickets=6, inflight=6, refusal_reserve=4)
        h1 = H.to_v01(h2)
        dd = H.fresh_dir("df_")
        d2 = H.Driver(M2, h2, os.path.join(dd, "j2"))
        d1 = H.Driver(M1, h1, os.path.join(dd, "j1"))
        L = h2["caps"]["max_token_chars"]
        diverged = False
        for i in range(rnd.randint(20, 120)):
            if d2.s["closed"] or d1.s["closed"]:
                break
            P = gen_op(rnd, d2.s, h2, L, diff=True, clean=clean)
            r2 = code(lambda: exec_op(M2, d2.b, h2, P))
            r1 = code(lambda: exec_op(M1, d1.b, h1, P))
            ops += 1
            a2, a1 = r2 == "ACCEPTED", r1 == "ACCEPTED"
            if a1 != a2:
                key = (P["op"], r1 if not a1 else "ACCEPTED", r2 if not a2 else "ACCEPTED")
                mism.inc(key)
                examples.setdefault(key, {k: (v if not isinstance(v, str) or len(v) < 40 else v[:20] + "...") for k, v in P.items()})
                diverged = True
                break
        if not diverged:
            if project(d1.s) != project(d2.s):
                mism.inc(("STATE_PROJECTION_DIFFERS", "", ""))
            else:
                matched_runs += 1
        shutil.rmtree(dd, ignore_errors=True)
    return {"runs": runs, "ops": ops, "runs_without_divergence": matched_runs,
            "divergences": {"%s | v0.1=%s | v0.2=%s" % k: v for k, v in sorted(mism.items(), key=lambda x: -x[1])},
            "examples": {"%s | v0.1=%s | v0.2=%s" % k: v for k, v in examples.items()}}


# ============================================================ main

def main():
    budget = 600
    seed = 20261019
    if "--budget" in sys.argv:
        budget = int(sys.argv[sys.argv.index("--budget") + 1])
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    t0 = time.time()
    print("== targeted")
    for t in (t1_type_confusion, t2_subclass_objects, t3_recovery_liveness, t4_v01_defect_fixed, t5_replay_type_laxity,
              t6_non_bridge_errors, t7_token_limit_scaling, t8_colon_ids, t9_float_edges, t10_scope_changes,
              t11_min_cap_boundaries, t12_exact_fit, t13_hook_failures):
        try:
            t()
        except Exception as e:  # noqa
            import traceback
            record(t.__name__, "harness error", "ERROR", "-", traceback.format_exc()[-600:])
    t_targeted = time.time() - t0
    rest = max(30, budget - t_targeted)
    print("== fuzz (%.0fs)" % (rest * 0.8))
    stats, anomalies = fuzz(rest * 0.8, seed)
    RESULTS["fuzz"] = {"stats": {str(k): v for k, v in sorted(stats.items(), key=lambda x: str(x[0]))},
                       "anomalies": anomalies[:200], "anomaly_counts": {}}
    for a in anomalies:
        RESULTS["fuzz"]["anomaly_counts"][a["type"]] = RESULTS["fuzz"]["anomaly_counts"].get(a["type"], 0) + 1
    print("runs=%s ops=%s drains=%s drain_events=%s reader_runs=%s zero_headroom_states=%s tight(<500)=%s blocked_slots=%s"
          % (stats.get("runs"), stats.get("ops"), stats.get("drains"), stats.get("drain_events"), stats.get("reader_runs"),
             stats.get("zero_headroom_states"), stats.get("tight_states_lt_500"), stats.get("drain_blocked_slots")))
    print("anomaly counts:", RESULTS["fuzz"]["anomaly_counts"] or "none")
    for a in anomalies[:8]:
        print("  ", json.dumps(a, default=str)[:400])
    acc = {k[1]: v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "accepted"}
    print("accepted by op:", acc)
    print("min slack module/reader:", {k[1]: v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "min_slack_module"},
          {k[1]: v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "min_slack_reader"})
    raw = {k: v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "refused" and str(k[2]).startswith("RAW:")}
    print("non-BridgeError refusals:", raw or "none")
    print("dispositions/channel statuses seen:", {k[1]: v for k, v in stats.items() if isinstance(k, tuple) and k[0] in ("disposition", "channel")})
    print("drain-blocked slot codes:", {k[1]: v for k, v in stats.items() if isinstance(k, tuple) and k[0] == "drain_blocked"})
    for mode in ("raw", "clean"):
        print("== differential v0.1 vs v0.2, %s inputs (%.0fs)" % (mode, rest * 0.1))
        RESULTS["differential"][mode] = dif = differential(rest * 0.1, seed + (1 if mode == "raw" else 2), clean=(mode == "clean"))
        print("runs=%d ops=%d runs_without_divergence=%d" % (dif["runs"], dif["ops"], dif["runs_without_divergence"]))
        for k, v in list(dif["divergences"].items())[:25]:
            print("  %5d  %s" % (v, k))
    RESULTS["elapsed_s"] = round(time.time() - t0, 1)
    RESULTS["seed"] = seed
    with open(os.path.join(HERE, "adversarial_results.json"), "w") as f:
        json.dump(RESULTS, f, indent=1, default=str, sort_keys=True)
    base = "/dev/shm" if os.path.isdir("/dev/shm") else os.path.join(HERE, "tmp")
    for name in os.listdir(base):
        if name.startswith(("adv_", "fz_", "df_", "mincap_", "tight_")):
            shutil.rmtree(os.path.join(base, name), ignore_errors=True)
    print("elapsed %.1fs; results -> %s" % (RESULTS["elapsed_s"], os.path.join(HERE, "adversarial_results.json")))


if __name__ == "__main__":
    main()
