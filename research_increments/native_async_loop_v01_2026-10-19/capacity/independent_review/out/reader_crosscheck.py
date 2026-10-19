#!/usr/bin/env python3
"""Generate journals with the module under review and cross-check the independent reader.

Writes journals + headers to out/journals/<scenario>/, runs the reader CLI in a separate
isolated interpreter (proving it does not import the module), replays each journal with the
module, compares min headroom and per-kind bounds, and writes out/reader_crosscheck_results.json.
"""
import copy
import json
import os
import random
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _u
_spec = _u.spec_from_file_location("_harness", os.path.join(HERE, "_harness.py"))
H = _u.module_from_spec(_spec); _spec.loader.exec_module(H)
M2, MAX_INT = H.M2, H.MAX_INT
OUTJ = os.path.join(HERE, "journals")
READER_PATH = os.path.join(HERE, "independent_reservation_reader.py")


class Tracked(H.Driver):
    """Driver that records the module's capacity_report headroom after every persisted event."""

    def __init__(self, m, header, path):
        super().__init__(m, header, path)
        self.headrooms = [self.b.capacity_report()["headroom"]]
        orig = self.b._persist

        def persist(*a):
            orig(*a)
            if not self.b._s["closed"]:
                self.headrooms.append(self.b.capacity_report()["headroom"])
        self.b._persist = persist


def scenario_dir(name):
    d = os.path.join(OUTJ, name)
    os.makedirs(d, exist_ok=True)
    for f in ("journal.jsonl", "header.json"):
        p = os.path.join(d, f)
        if os.path.exists(p):
            os.remove(p)
    return d


def new(name, header):
    d = scenario_dir(name)
    with open(os.path.join(d, "header.json"), "w") as f:
        json.dump(header, f, sort_keys=True)
    return Tracked(M2, header, os.path.join(d, "journal.jsonl"))


# ---------------------------------------------------------------- scenarios

def sc_normal():
    h = H.make_header()
    d = new("normal", h)
    d.observe(0, wall=10)
    d.packet("p0", b"hello", wall=11)
    d.start("t1", list(range(2, 10)), 8, wall=12)
    d.start("t2", list(range(3, 11)), 100, wall=12)
    d.ret("t1", rows=[[0.1 * i] * 9 for i in range(8)], wall=13)
    d.ret("t2", status="ERROR", wall=13)
    for i in range(8):
        d.slot("t1", i)
        d.slot("t2", i)
    d.refuse("PUBLIC_PACKET", "TOO_BIG")
    tick = 0
    while d.s["queue"]:
        cmd = d.s["commands"][d.s["queue"][0]]
        if tick < cmd["desired_tick"]:
            tick = cmd["desired_tick"]
            d.observe(tick, wall=20 + tick)
        d.chan_head()
    d.close("done")
    return d


def sc_worst(L=64, name="worst_L64"):
    aids = (H.pad("S", 0, L), H.pad("T", 1, L))
    h = H.make_header(L=L, events=1000, kinds={"ACTOR_TRANSITION": 99}, latency=10**6, actor_ids=aids)
    d = new(name, h)
    base = MAX_INT - 3 * 10**6
    k = 0
    def obs(tick):
        nonlocal k
        k += 1
        d.observe(tick, sid=H.pad("s:", k, L), wall=MAX_INT, time_ns=MAX_INT, deadline=MAX_INT)
    obs(base)
    for j in range(12):  # actor_generation reaches two digits
        d.actor(aids[(j + 1) % 2], reason=H.pad("why", j, L))
    for j in range(100 if L > 1 else 80):  # seq reaches three digits
        obs(base + j)
    d.failure(True, True)
    d.packet(H.pad("pkt:", 0, L), b"\x00" * 50)
    tick = d.tick()
    first = tick + 10**6
    tids = []
    for j, purpose in enumerate(["SAFE_LOCAL_RECOVERY"] * 4 + ["SAFETY_ABORT", "ORIGINAL_GOAL"]):
        tid = H.pad("t:%d:" % j, j, L)
        tids.append(tid)
        d.start(tid, [first + 8 * j + i for i in range(8)], MAX_INT, purpose=purpose)
    for j, tid in enumerate(tids[:5]):
        d.ret(tid, status="ERROR" if j == 3 else "OK")
    for tid in tids[:3]:
        for i in range(8):
            d.slot(tid, i)
    d.slot(tids[3], 0)   # ERROR_NO_OUTPUT
    for i in range(4):
        d.slot(tids[4], i)
    for _ in range(10):
        d.chan_head("REJECTED")
    for _ in range(8):
        d.refuse()
    d.close()
    return d


def sc_multi(seed=1):
    rnd = random.Random(seed)
    h = H.make_header(L=16, inflight=16, tickets=40)
    d = new("multi_ticket", h)
    tick = 0
    d.observe(tick, wall=1)
    d.packet("p", b"x" * 7)
    n = 0
    for step in range(220):
        r = rnd.random()
        s = d.s
        try:
            if r < 0.12 and sum(t["return"] is None for t in s["tickets"].values()) < 16 and len(s["tickets"]) < 40:
                n += 1
                off = rnd.randint(0, 6)
                d.start("tk:%d" % n, [tick + off + 2 * i for i in range(8)], tick + rnd.randint(4, 20),
                        purpose=rnd.choice(["ORIGINAL_GOAL", "SAFETY_ABORT"]))
            elif r < 0.30:
                un = [t for t, v in s["tickets"].items() if v["return"] is None]
                if un:
                    d.ret(rnd.choice(un), status="ERROR" if rnd.random() < 0.2 else "OK",
                          rows=[[rnd.choice(H.EDGE_VALUES) for _ in range(9)] for _ in range(8)])
            elif r < 0.60:
                cand = [(t, i) for t, v in s["tickets"].items() if v["return"] is not None for i in range(8) if str(i) not in v["slots"]]
                if cand:
                    d.slot(*rnd.choice(cand))
            elif r < 0.75 and s["queue"]:
                d.chan_head()
            elif r < 0.90:
                tick += rnd.randint(1, 3)
                d.observe(tick)
            elif r < 0.95:
                d.actor(rnd.choice(["student", "teacher"]))
            elif s["refusals"] < h["caps"]["refusal_reserve"]:
                d.refuse("K", "R")
        except M2.BridgeError:
            raise
    d.close("multi")
    return d


def _prefix_ops(L):
    def ops(d):
        d.observe(0, sid=H.pad("s", 0, L), wall=1)
        d.packet(H.pad("p", 0, L), b"abc")
        d.start(H.pad("a:", 0, L), list(range(1, 9)), 100)
        d.start(H.pad("b:", 1, L), list(range(9, 17)), 100, purpose="SAFETY_ABORT")
    return ops


def _prefix_ok(L):
    ops = _prefix_ops(L)
    def pred(h):
        dd = H.fresh_dir("tight_")
        try:
            d = H.Driver(M2, h, os.path.join(dd, "j"))
            ops(d)
            return True
        except M2.BridgeError as e:
            if e.code in H.BYTE_COUNT_CODES:
                return False
            raise
        finally:
            H.shutil.rmtree(dd, ignore_errors=True)
    return pred


def sc_tight(L, name):
    h = H.make_header(L=L, refusal_reserve=3, actor_ids=(H.pad("S", 0, L), H.pad("T", 1, L)))
    cap = H.min_cap(h, predicate=_prefix_ok(L), lo=1, hi=10**7)
    h["caps"]["journal_bytes"] = cap
    d = new(name, h)
    _prefix_ops(L)(d)
    extra = {}
    try:
        d.observe(1, sid=H.pad("s", 1, L))
        extra["next_ordinary"] = "ACCEPTED"
    except M2.BridgeError as e:
        extra["next_ordinary"] = e.code
    extra["module_headroom_after_prefix"] = d.b.capacity_report()["headroom"]
    extra["cap"] = cap
    res = d.drain(random.Random(3), refusals_first=False)
    extra["drain"] = res
    return d, extra


def sc_stateless():
    h = H.make_header(refusal_reserve=2)
    d = new("stateless_close", h)
    d.refuse("NO_STATE", "BOOT")
    d.close("early")
    return d


def sc_open():
    h = H.make_header(L=20)
    d = new("open_unclosed", h)
    d.observe(0, wall=1)
    d.packet("p", b"q")
    d.start("open:1", list(range(1, 9)), 4)
    d.ret("open:1")
    d.slot("open:1", 0)
    return d


# ---------------------------------------------------------------- checks

def run_reader_cli(journal, header_path):
    out = subprocess.run([sys.executable, "-B", "-I", READER_PATH, journal, header_path, "--json"],
                         capture_output=True, text=True, timeout=120)
    return out.returncode, json.loads(out.stdout) if out.stdout.strip() else {"stderr": out.stderr}


def max_lines(journal):
    mx = {}
    with open(journal, "rb") as f:
        for raw in f:
            k = json.loads(raw)["kind"]
            mx[k] = max(mx.get(k, 0), len(raw))
    return mx


def check(name, d, extra=None):
    hp = os.path.join(OUTJ, name, "header.json")
    jp = os.path.join(OUTJ, name, "journal.jsonl")
    ok, rep = H.module_replay(M2, jp, d.h)
    rc, rr = run_reader_cli(jp, hp)
    mb = M2.line_bounds(d.h)
    ib = rr.get("bounds", {})
    mx = max_lines(jp)
    row = {"scenario": name, "events": d.s["events"], "bytes": d.s["journal_bytes"], "cap": d.h["caps"]["journal_bytes"],
           "closed": d.s["closed"], "module_replay": "ACCEPT" if ok else rep, "reader_verdict": rr.get("verdict"),
           "reader_exit": rc, "reader_first_violation": rr.get("first_violation"),
           "module_min_headroom": min(d.headrooms), "reader_min_headroom": rr.get("min_headroom_while_open"),
           "agree": ok == (rr.get("verdict") == "PASS"),
           "reader_headroom_ge_module": (rr.get("min_headroom_while_open") is None or rr["min_headroom_while_open"] >= min(d.headrooms)),
           "max_line_by_kind": {k: mx.get(k) for k in ("INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "CAPACITY_REFUSAL", "CASE_END")},
           "module_bounds": mb, "reader_bounds": ib,
           "replay_state_equals_live": ok and rep._s == d.s}
    if extra:
        row["extra"] = extra
    return row


def bounds_table():
    rows = []
    variants = [dict(L=1), dict(L=8), dict(L=64), dict(L=200), dict(L=64, events=30), dict(L=64, events=MAX_INT),
                dict(L=64, latency=10**6), dict(L=64, actor_ids=(H.pad("A", 0, 64), H.pad("B", 1, 64))),
                dict(L=64, kinds={"ACTOR_TRANSITION": MAX_INT}, events=MAX_INT, actor_ids=(H.pad("A", 0, 64), "b"))]
    for v in variants:
        h = H.make_header(**v)
        mb = M2.line_bounds(h)
        ib = H.READER.Bounds(h).bounds
        rows.append({"variant": {k: (str(x) if k == "actor_ids" else x) for k, x in v.items()},
                     "module": mb, "reader": ib,
                     "module_minus_reader": {k: mb[k] - ib[k] for k in ("INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "CAPACITY_REFUSAL", "CASE_END_BASE")} | {"CASE_END_PER_TICKET": mb["CASE_END_PER_TICKET"] - ib["CASE_END_PER_TICKET_MARGINAL"]}})
    return rows


def main():
    os.makedirs(OUTJ, exist_ok=True)
    results = []
    results.append(check("normal", sc_normal()))
    results.append(check("worst_L64", sc_worst(64, "worst_L64")))
    results.append(check("worst_L1", sc_worst(1, "worst_L1")))
    results.append(check("multi_ticket", sc_multi()))
    for L, nm in ((32, "tight_L32"), (1, "tight_L1"), (80, "tight_L80")):
        d, extra = sc_tight(L, nm)
        results.append(check(nm, d, extra))
    results.append(check("stateless_close", sc_stateless()))
    results.append(check("open_unclosed", sc_open()))
    table = bounds_table()
    out = {"scenarios": results, "bounds_table": table}
    with open(os.path.join(HERE, "reader_crosscheck_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
    print("%-16s %6s %8s %7s %-8s %-6s %6s %12s %12s %s" % ("scenario", "events", "bytes", "closed", "replay", "reader", "agree", "mod_minhead", "rdr_minhead", "drain"))
    for r in results:
        dr = r.get("extra", {}).get("drain")
        drs = "" if not dr else "defects=%d blocked=%d unexpected=%d next_ordinary=%s" % (len(dr["defects"]), len(dr["blocked"]), len(dr["unexpected"]), r["extra"]["next_ordinary"])
        print("%-16s %6d %8d %7s %-8s %-6s %6s %12s %12s %s" % (r["scenario"], r["events"], r["bytes"], r["closed"], r["module_replay"] if isinstance(r["module_replay"], str) else "?", r["reader_verdict"], r["agree"], r["module_min_headroom"], r["reader_min_headroom"], drs))
        if r["reader_first_violation"]:
            print("   first violation:", r["reader_first_violation"])
        if not r["replay_state_equals_live"]:
            print("   replay state != live state")
    print("\nper-kind: max observed line / reader bound / module bound")
    for r in results:
        mb, ib, mx = r["module_bounds"], r["reader_bounds"], r["max_line_by_kind"]
        print("  %-16s" % r["scenario"], "  ".join("%s=%s/%s/%s" % (k[:6], mx[k], ib.get(k, "-"), mb.get(k, "-")) for k in ("INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "CAPACITY_REFUSAL") if mx[k]))
    print("\nbounds table (module - reader, bytes):")
    for t in table:
        print("  ", t["variant"], t["module_minus_reader"])
    bad = [r for r in results if not r["agree"] or r["reader_verdict"] != "PASS" or not r["reader_headroom_ge_module"] or not r["replay_state_equals_live"]
           or (r.get("extra") and r["extra"]["drain"]["defects"])]
    print("\nCROSSCHECK:", "ALL_AGREE_PASS" if not bad else "DISAGREEMENT in %s" % [r["scenario"] for r in bad])
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
