"""Shared test harness for the v0.2 review (loads modules by path; never writes under input/)."""
import copy
import importlib.util
import json
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(os.path.dirname(HERE), "input")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M2 = _load("bridge_v02_under_review", os.path.join(INPUT, "async_bridge_v02_under_review.py"))
M1 = _load("bridge_v01", os.path.join(INPUT, "async_bridge_v01.py"))
READER = _load("independent_reader", os.path.join(HERE, "independent_reservation_reader.py"))

MAX_INT = 2**63 - 1
TOKEN_ALPHABET = [chr(c) for c in range(32, 127) if chr(c) not in '"\\']
_CAND = [-2.2250738585072014e-308, -1.7976931348623157e308, -1.2345678901234567e-300, -9.876543210987654e+200,
         -1.0000000000000002e-100, -4.9406564584124654e-310]
WORST_FLOATS = [v for v in _CAND if len(json.dumps(v)) == 24]
assert len(WORST_FLOATS) >= 3
EDGE_VALUES = [-0.0, 0.0, 5e-324, -5e-324, 1e-320, -1e-320, 2**53, -2**53, 0, 1, -1, 1.5, 1e16, -1e-5,
               -0.00012345678901234567, 1.7976931348623157e308] + WORST_FLOATS
BYTE_COUNT_CODES = {"BYTE_RESERVATION_REFUSED", "JOURNAL_TOTAL_BYTE_CAPACITY_REFUSED", "RESERVED_LINE_BOUND_VIOLATED",
                    "EVENT_CAPACITY_REFUSED", "KIND_CAPACITY_REFUSED", "WHOLE_TICKET_KIND_CAPACITY_REFUSED",
                    "END_LINE_RESERVATION_EXCEEDS_LINE_CAP", "JOURNAL_LINE_BYTE_CAPACITY_REFUSED",
                    "END_KIND_RESERVE_REQUIRED", "REFUSAL_KIND_RESERVE_REQUIRED", "REFUSAL_RESERVE_EXHAUSTED",
                    "WHOLE_TICKET_COMMAND_CAPACITY_REFUSED", "ASSET_CAPACITY_REFUSED"}
SEMANTIC_BLOCK_CODES = {"RECOVERY_REQUIRES_KNOWN_FAILURE", "POST_DEADLINE_RECOVERY_REQUIRES_FULL_FALSE"}


def fresh_dir(prefix="abrev_"):
    base = "/dev/shm" if os.path.isdir("/dev/shm") else os.path.join(HERE, "tmp")
    os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(dir=base, prefix=prefix)


def worst_row(i=0):
    return [WORST_FLOATS[(i + j) % len(WORST_FLOATS)] for j in range(9)]


def pad(prefix, n, L):
    """Unique printable token of exactly L chars for index n (base-94 when prefix+n does not fit)."""
    s = prefix + str(n)
    if len(s) > L:
        digs = []
        k = n
        while True:
            digs.append(TOKEN_ALPHABET[k % len(TOKEN_ALPHABET)])
            k //= len(TOKEN_ALPHABET)
            if not k:
                break
        s = "".join(reversed(digs))
        assert len(s) <= L, "index too large for token length"
        return s.rjust(L, "~")
    return s + "x" * (L - len(s))


def make_header(m=M2, *, L=64, events=100000, tickets=2000, inflight=64, commands=16000, refusal_reserve=8,
                max_line=4000000, journal_bytes=512000000, kinds=None, latency=1, actor_ids=("student", "teacher"),
                mode="CPU_FIXTURE", deadline=10**9, packet_archive=3000, history_window=512, asset_bytes=20000000):
    h = M2.fixture_header()
    roles = ["STUDENT", "TEACHER"]
    acts = []
    for i, aid in enumerate(actor_ids):
        base = h["actors"][i % 2]
        acts.append({"actor_id": aid, "role": roles[i % 2], "actor_source_sha256": base["actor_source_sha256"],
                     "weights_sha256": base["weights_sha256"], "input_adapter_sha256": base["input_adapter_sha256"]})
    h["actors"] = acts
    h["initial_actor_id"] = actor_ids[0]
    h["mode"] = mode
    h["original_deadline_ns"] = deadline
    h["channel"]["latency_ticks"] = latency
    c = h["caps"]
    c.update({"events": events, "tickets": tickets, "inflight": inflight, "commands": commands,
              "refusal_reserve": refusal_reserve, "max_line_bytes": max_line, "journal_bytes": journal_bytes,
              "max_token_chars": L, "packet_archive": packet_archive, "history_window": history_window,
              "asset_bytes": asset_bytes})
    c["kinds"] = {k: (kinds or {}).get(k, events) for k in M2.KINDS}
    if m is M1:
        h["schema"] = M1.SCHEMA
        del c["max_token_chars"]
    return h


def to_v01(h2):
    h = copy.deepcopy(h2)
    h["schema"] = M1.SCHEMA
    h["caps"].pop("max_token_chars", None)
    return h


def construct_ok(m, header):
    d = fresh_dir("mincap_")
    try:
        try:
            b = m.AsyncBridge(os.path.join(d, "j"), header, expected_header=copy.deepcopy(header))
            if b._f:
                b._f.close()
            return True
        except m.BridgeError as e:
            if e.code in BYTE_COUNT_CODES:
                return False
            raise
    finally:
        shutil.rmtree(d, ignore_errors=True)


def min_cap(header, predicate=None, lo=1, hi=10**9):
    """Smallest caps.journal_bytes for which predicate(header_with_cap) holds (default: constructor succeeds)."""
    predicate = predicate or (lambda h: construct_ok(M2, h))
    def ok(c):
        h = copy.deepcopy(header)
        h["caps"]["journal_bytes"] = c
        return predicate(h)
    assert ok(hi), "hi cap does not satisfy predicate"
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


class Driver:
    """Thin wrapper over a live AsyncBridge (works for v0.1 and v0.2)."""

    def __init__(self, m, header, path, hook=None):
        self.m, self.h, self.path = m, header, path
        self.b = m.AsyncBridge(path, header, expected_header=copy.deepcopy(header), persist_hook=hook)
        self.L = header["caps"].get("max_token_chars", 64)
        self.wall = 0
        self.nstate = 0

    @property
    def s(self):
        return self.b._s

    def sid(self):
        return self.s["state"]["state_id"] if self.s["state"] else None

    def tick(self):
        return self.s["state"]["tick"] if self.s["state"] else None

    def mkstate(self, tick, sid, time_ns=None, deadline=None, lawful=True):
        h = self.h
        st = {"attempt_id": h["attempt_id"], "native_epoch": h["native_epoch"], "state_id": sid,
              "physical_state_sha256": self.m.digest({"synthetic_tick": tick, "sid": sid}), "tick": tick,
              "time_ns": tick * 1000 if time_ns is None else time_ns, "deadline_clock_id": h["deadline_clock_id"],
              "deadline_time_ns": tick * 1000 if deadline is None else deadline,
              "collector_source_sha256": h["collector_source_sha256"], "lawful_state": lawful}
        return st

    def w(self, wall=None):
        if wall is not None:
            self.wall = max(self.wall, wall)
        return self.wall

    # ordinary
    def observe(self, tick, sid=None, wall=None, **kw):
        self.nstate += 1
        sid = sid or ("state-%d" % self.nstate)
        return self.b.observe_state(self.mkstate(tick, sid, **kw), wall_ns=self.w(wall))

    def packet(self, pid, data, wall=None):
        return self.b.publish_packet(pid, data, wall_ns=self.w(wall))

    def start(self, tid, ticks, end, purpose="ORIGINAL_GOAL", wall=None, actor=None):
        data = self.m.base64.b64decode(self.s["packets"][-1]["public_bytes_b64"]) if self.s["packets"] else b""
        return self.b.start_inference(tid, actor_id=actor or self.s["actor_id"], actual_input_bytes=data,
                                      desired_ticks=ticks, declared_end_tick=end, purpose=purpose, wall_ns=self.w(wall))

    def actor(self, aid, reason="r", wall=None):
        return self.b.transition_actor(aid, reason=reason, current_state_id=self.sid(), wall_ns=self.w(wall))

    def failure(self, known, full, wall=None):
        return self.b.record_failure(known_original_failure=known, original_full_failure=full, evidence_sha256="ab" * 32,
                                     current_state_id=self.sid(), wall_ns=self.w(wall))

    # reserved
    def ret(self, tid, rows=None, status="OK", wall=None):
        t = self.s["tickets"][tid]
        if status == "OK" and rows is None:
            rows = [worst_row(i) for i in range(8)]
        return self.b.accept_return(tid, snapshot_sha256=t["snapshot_sha256"], output_8x9=rows if status == "OK" else None,
                                    current_state_id=self.sid(), wall_ns=self.w(wall), status=status)

    def expected_auth(self, tid, i):
        t = self.s["tickets"][tid]
        purpose = t["snapshot"]["purpose"]
        if purpose == "ORIGINAL_GOAL":
            return None
        out = t["return"]["output_8x9"]
        return {"state_id": self.sid(), "purpose": purpose,
                "target_sha256": None if out is None else self.m.target_sha(out[i]),
                "source_sha256": self.h["authorization_source_sha256"]}

    def prepare(self, tid, i, auth="expected"):
        t = self.s["tickets"][tid]
        a = self.expected_auth(tid, i) if auth == "expected" else auth
        return self.b.prepare_slot(tid, i, current_state_id=self.sid(), queue_sha256=self.b.queue_snapshot()["sha256"],
                                   purpose=t["snapshot"]["purpose"], authorization=a)

    def commit(self, prepared, wall=None):
        return self.b.commit_slot(prepared, current_state_id=prepared["current_state_id"],
                                  queue_sha256=prepared["queue_sha256"], wall_ns=self.w(wall))

    def slot(self, tid, i, auth="expected", wall=None):
        return self.commit(self.prepare(tid, i, auth), wall)

    def chan_head(self, status=None, wall=None):
        cid = self.s["queue"][0]
        cmd = self.s["commands"][cid]
        if status is None:
            tick = self.tick()
            ok = tick >= cmd["ready_tick"] and tick == cmd["desired_tick"] and self.s["last_applied_tick"] != tick
            status = "APPLIED" if ok else "REJECTED"
        return self.b.record_channel_result(cid, status=status, current_state_id=self.sid(),
                                            actual_target_9d=copy.deepcopy(cmd["target_9d"]),
                                            claimed_owner=copy.deepcopy(cmd["owner"]), wall_ns=self.w(wall))

    def refuse(self, rk=None, reason=None, wall=None):
        return self.b.record_capacity_refusal(rk or "r" * self.L, reason or "y" * self.L, wall_ns=self.w(wall))

    def close(self, reason=None, wall=None):
        return self.b.close(reason=reason or "e" * self.L, wall_ns=self.w(wall))

    def drain(self, rnd=None, error_prob=0.0, refusals_first=None, interleave=0.5):
        """Write every reserved event with worst-case content, the remaining refusals, then CASE_END.

        Returns dict(defects=[(kind, code)], blocked=[(tid, slot, code)], unexpected=[(kind, repr)])."""
        import random as _r
        rnd = rnd or _r.Random(0)
        res = {"defects": [], "blocked": [], "unexpected": [], "written": 0}

        def attempt(kind, fn):
            try:
                fn()
                res["written"] += 1
                return True
            except self.m.BridgeError as e:
                if e.code in BYTE_COUNT_CODES:
                    res["defects"].append((kind, e.code))
                else:
                    res["unexpected"].append((kind, e.code))
                return False
            except Exception as e:  # noqa
                res["unexpected"].append((kind, "%s:%s" % (type(e).__name__, e)))
                return False

        left = self.h["caps"]["refusal_reserve"] - self.s["refusals"]
        pre = rnd.randint(0, left) if refusals_first is None else (left if refusals_first else 0)
        for _ in range(pre):
            attempt("CAPACITY_REFUSAL", lambda: self.refuse())
        blocked = set()
        for tid in list(self.s["tickets"]):
            if self.s["tickets"][tid]["return"] is None:
                st = "ERROR" if rnd.random() < error_prob else "OK"
                attempt("INFERENCE_RETURN", lambda: self.ret(tid, status=st))
        for tid in list(self.s["tickets"]):
            t = self.s["tickets"][tid]
            if t["return"] is None:
                continue
            for i in range(8):
                if str(i) in self.s["tickets"][tid]["slots"]:
                    continue
                try:
                    p = self.prepare(tid, i)
                except self.m.BridgeError as e:
                    if e.code in SEMANTIC_BLOCK_CODES:
                        res["blocked"].append((tid, i, e.code))
                    else:
                        res["unexpected"].append(("prepare", e.code))
                    continue
                attempt("SLOT_DISPOSITION", lambda: self.commit(p))
                while self.s["queue"] and rnd.random() < interleave:
                    attempt("CHANNEL_RESULT", lambda: self.chan_head())
        while self.s["queue"]:
            if not attempt("CHANNEL_RESULT", lambda: self.chan_head()):
                break
        left = self.h["caps"]["refusal_reserve"] - self.s["refusals"]
        for _ in range(left):
            attempt("CAPACITY_REFUSAL", lambda: self.refuse())
        attempt("CASE_END", lambda: self.close())
        return res


def reader_check(journal, header):
    return READER.read_journal(journal, header)


def module_replay(m, journal, header):
    try:
        r = m.AsyncBridge.replay(journal, expected_header=copy.deepcopy(header))
        return True, r
    except Exception as e:  # noqa
        return False, "%s:%s" % (type(e).__name__, getattr(e, "code", e))
