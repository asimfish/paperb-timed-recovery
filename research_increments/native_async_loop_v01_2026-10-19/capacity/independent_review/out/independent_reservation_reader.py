#!/usr/bin/env python3
"""Independent byte/count reservation reader for AsyncCollector v0.2 journals.

Deliberately does NOT import the module under review. Line bounds are derived
arithmetically from the header with a small JSON-length calculus (object/list/
string/integer lengths), not by serializing worst-case bodies.

Usage:
  python3 -B -I independent_reservation_reader.py JOURNAL EXPECTED_HEADER_JSON [--json]
  python3 -B -I independent_reservation_reader.py --bounds-only EXPECTED_HEADER_JSON

Exit status: 0 PASS, 1 FAIL (first violation reported), 2 usage/IO error.

Derivation rules (from the v0.2 contract):
  * every id that can appear in a reserved body is a printable-ASCII token without
    quote/backslash, 1..max_token_chars chars, so it serializes to len+2 bytes;
  * command_id = ticket_id + ":" + slot digit (len <= L+2) iff disposition == SUBMIT;
  * state ticks/time_ns/deadline_time_ns, wall_ns, desired ticks <= 2**63-1 (19 digits);
  * earliest_apply_tick <= max(MAX_INT + latency_ticks, MAX_INT + 1);
  * seq < caps.events; actor_generation <= number of ACTOR_TRANSITION events
    <= min(caps.kinds.ACTOR_TRANSITION, caps.events - 1);
  * target values are finite floats (repr <= 24 chars: sign, 17 significant digits,
    '.', 'e-308') or ints with |v| <= 2**53 (<= 17 chars), never bool;
  * owner = one of the header actors + actor_generation;
  * target_9d is null iff the return status is ERROR iff disposition ERROR_NO_OUTPUT;
  * CASE_END lists: unreturned ids, {ticket: missing slot list}, pending command ids.
The reservation for an open case is
  unreturned*B_RET + unresolved_slots*(B_SLOT+B_CHAN) + pending*B_CHAN
  + refusals_left*B_REF + END(state)
where END(state) over-approximates every CASE_END reachable from the current state by
reserved events only (each open ticket keeps its unreturned entry, its unresolved
entry with its current missing count, and pending + missing command ids).
"""
import json
import math
import sys

MAX_INT = 2**63 - 1
MAX_TARGET_INT = 2**53
FLOAT_CHARS = 24          # '-d.dddddddddddddddde-308'
INT_TARGET_CHARS = len(str(-MAX_TARGET_INT))  # 17
EVENT_SCHEMA = "AsyncCollectorEvent/0.2"
KINDS = ("CASE_BEGIN", "OBSERVED_STATE", "PUBLIC_PACKET", "INFERENCE_START", "INFERENCE_RETURN",
         "SLOT_DISPOSITION", "CHANNEL_RESULT", "ACTOR_TRANSITION", "FULL_TASK_FAILURE",
         "CAPACITY_REFUSAL", "CASE_END")
RESERVED_FIXED = ("INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "CAPACITY_REFUSAL")
PURPOSES = ("ORIGINAL_GOAL", "SAFE_LOCAL_RECOVERY", "SAFETY_ABORT")
DISPOSITIONS = ("SUBMIT", "ERROR_NO_OUTPUT", "PADDING", "ACTOR_REVOKED", "STALE", "GUARD_REJECTED", "CAPACITY_REFUSED")
CHANNEL_STATUSES = ("APPLIED", "REJECTED", "DROPPED")
RETURN_STATUSES = ("OK", "ERROR")
UNRESOLVED = "UNKNOWN_NO_AUTOMATIC_RESEND"
PREPARED_KEYS = {"ticket_id", "slot_index", "desired_tick", "target_9d", "target_sha256", "disposition",
                 "input_snapshot_sha256", "return_event_sha256", "owner", "current_state_id",
                 "current_state_sha256", "queue_sha256", "actor_generation", "known_original_failure",
                 "original_full_failure", "earliest_apply_tick", "purpose", "authorization",
                 "guard_source_sha256", "channel_source_sha256", "command_id", "prepared_sha256"}
OWNER_KEYS = {"actor_id", "role", "actor_source_sha256", "weights_sha256", "input_adapter_sha256", "actor_generation"}
ENVELOPE_KEYS = {"schema", "seq", "prev_sha256", "kind", "body", "clock", "wall_ns", "sha256"}
SHA = 66  # quoted 64-hex


# ------------------------------------------------------------ JSON length calculus

def digits(n):
    return len(str(n))


def jstr(n):
    """Serialized length of a token string of n chars (no escaping needed)."""
    return n + 2


def jobj(pairs):
    """pairs: iterable of (key_len, value_len) -> length of {"k":v,...}."""
    pairs = list(pairs)
    return 2 + sum(k + 3 + v for k, v in pairs) + max(0, len(pairs) - 1)


def jlist(lens):
    lens = list(lens)
    return 2 + sum(lens) + max(0, len(lens) - 1)


def K(name):
    return len(name)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True)


# ------------------------------------------------------------ bound derivation

class Bounds:
    def __init__(self, header):
        caps = header["caps"]
        self.L = L = caps["max_token_chars"]
        self.cap = caps["journal_bytes"]
        self.max_line = caps["max_line_bytes"]
        self.refusal_reserve = caps["refusal_reserve"]
        self.events_cap = caps["events"]
        self.kind_caps = caps["kinds"]
        self.SEQ = digits(max(0, caps["events"] - 1))
        self.CLOCK = max(4, jlist([digits(MAX_INT)] * 3))
        self.WALL = digits(MAX_INT)
        self.TICK = digits(MAX_INT)
        self.EARLIEST = digits(max(MAX_INT + header["channel"]["latency_ticks"], MAX_INT + 1))
        gen_max = min(caps["kinds"]["ACTOR_TRANSITION"], max(0, caps["events"] - 1))
        self.GEN = digits(gen_max)
        self.OWNER = max(jobj([(K("actor_id"), jstr(len(a["actor_id"]))), (K("role"), jstr(len(a["role"]))),
                               (K("actor_source_sha256"), SHA), (K("weights_sha256"), SHA),
                               (K("input_adapter_sha256"), SHA), (K("actor_generation"), self.GEN)])
                         for a in header["actors"])
        self.NUM = max(FLOAT_CHARS, INT_TARGET_CHARS)
        self.ROW = jlist([self.NUM] * 9)
        self.PURPOSE = max(jstr(len(p)) for p in PURPOSES)
        self.AUTH = max(4, jobj([(K("purpose"), self.PURPOSE), (K("source_sha256"), SHA),
                                 (K("state_id"), jstr(L)), (K("target_sha256"), max(4, SHA))]))
        self.CID = jstr(L + 2)
        self.bounds = {
            "INFERENCE_RETURN": self.line("INFERENCE_RETURN", self._return_body()),
            "SLOT_DISPOSITION": self.line("SLOT_DISPOSITION", self._slot_body()),
            "CHANNEL_RESULT": self.line("CHANNEL_RESULT", self._channel_body()),
            "CAPACITY_REFUSAL": self.line("CAPACITY_REFUSAL", jobj([(K("request_kind"), jstr(L)), (K("reason"), jstr(L))])),
        }
        self.bounds["CASE_END_BASE"] = self.end_bound([])
        one = [(L, 1, 8, 0)]
        self.bounds["CASE_END_ONE_TICKET"] = self.end_bound(one)
        self.bounds["CASE_END_PER_TICKET_MARGINAL"] = self.end_bound(one * 2) - self.end_bound(one)

    def line(self, kind, body_len, clock_len=None):
        clock_len = self.CLOCK if clock_len is None else clock_len
        return jobj([(K("body"), body_len), (K("clock"), clock_len), (K("kind"), jstr(len(kind))),
                     (K("prev_sha256"), SHA), (K("schema"), jstr(len(EVENT_SCHEMA))), (K("seq"), self.SEQ),
                     (K("sha256"), SHA), (K("wall_ns"), self.WALL)]) + 1

    def _return_body(self):
        L = self.L
        best = 0
        for status in RETURN_STATUSES:
            out = jlist([self.ROW] * 8) if status == "OK" else 4
            best = max(best, jobj([(K("ticket_id"), jstr(L)), (K("snapshot_sha256"), SHA), (K("output_8x9"), out),
                                   (K("output_sha256"), SHA), (K("current_state_id"), jstr(L)), (K("status"), jstr(len(status)))]))
        return best

    def _slot_body(self):
        L = self.L
        best = 0
        for d in DISPOSITIONS:
            target = 4 if d == "ERROR_NO_OUTPUT" else self.ROW
            tsha = 4 if d == "ERROR_NO_OUTPUT" else SHA
            cid = self.CID if d == "SUBMIT" else 4
            prepared = jobj([(K("ticket_id"), jstr(L)), (K("slot_index"), 1), (K("desired_tick"), self.TICK),
                             (K("target_9d"), target), (K("target_sha256"), tsha), (K("disposition"), jstr(len(d))),
                             (K("input_snapshot_sha256"), SHA), (K("return_event_sha256"), SHA), (K("owner"), self.OWNER),
                             (K("current_state_id"), jstr(L)), (K("current_state_sha256"), SHA), (K("queue_sha256"), SHA),
                             (K("actor_generation"), self.GEN), (K("known_original_failure"), 5),
                             (K("original_full_failure"), 5), (K("earliest_apply_tick"), self.EARLIEST),
                             (K("purpose"), self.PURPOSE), (K("authorization"), self.AUTH),
                             (K("guard_source_sha256"), SHA), (K("channel_source_sha256"), SHA),
                             (K("command_id"), cid), (K("prepared_sha256"), SHA)])
            best = max(best, jobj([(K("prepared"), prepared)]))
        return best

    def _channel_body(self):
        L = self.L
        return jobj([(K("command_id"), self.CID), (K("status"), max(jstr(len(s)) for s in CHANNEL_STATUSES)),
                     (K("current_state_id"), jstr(L)), (K("actual_target_9d"), self.ROW), (K("claimed_owner"), self.OWNER)])

    def end_bound(self, tickets):
        """tickets: list of (id_len, unreturned(0/1), missing_count, pending_count) for open tickets."""
        L = self.L
        unret = [jstr(n) for n, u, k, p in tickets if u]
        # {"<ticket id of n chars>":[d,d,...]} -- bare key length n, value is a list of k single digits
        unres_len = jobj([(n, jlist([1] * k)) for n, u, k, p in tickets if k > 0])
        cids = []
        for n, u, k, p in tickets:
            cids += [jstr(n + 2)] * (p + k)
        censored = jobj([(K("unreturned_tickets"), jlist(unret)), (K("unresolved_slots"), unres_len),
                         (K("pending_commands"), jlist(cids)), (K("unresolved_outcomes"), jstr(len(UNRESOLVED)))])
        return self.line("CASE_END", jobj([(K("reason"), jstr(L)), (K("censored"), censored)]))


# ------------------------------------------------------------ field predicates

def is_int(v):
    return type(v) is int


def token(v, L):
    return type(v) is str and 1 <= len(v) <= L and all(32 <= ord(c) <= 126 and c not in '"\\' for c in v)


def hexsha(v):
    return type(v) is str and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def target_row(v):
    return (type(v) is list and len(v) == 9 and all(
        (type(x) is float and math.isfinite(x)) or (type(x) is int and abs(x) <= MAX_TARGET_INT) for x in v))


# ------------------------------------------------------------ reader

class Reader:
    def __init__(self, header):
        self.h = header
        self.B = Bounds(header)
        self.L = self.B.L
        self.actor_ids = {a["actor_id"]: a for a in header["actors"]}
        self.violations = []
        self.bytes = 0
        self.events = 0
        self.kind_counts = {}
        self.prev = "0" * 64
        self.closed = False
        self.state_id = None
        self.tickets = {}   # id -> {"returned": bool, "slots": set(), "status": str}
        self.queue = []     # pending command ids, FIFO
        self.cmd_ticket = {}
        self.refusals = 0
        self.min_headroom = None
        self.min_headroom_seq = None
        self.max_line = {}
        self.min_slack = {}

    # -- helpers
    def viol(self, seq, cat, msg):
        if len(self.violations) < 200:
            self.violations.append({"seq": seq, "category": cat, "detail": msg})

    def counts(self):
        unret = unres = 0
        open_t = []
        pending_by = {}
        for cid in self.queue:
            t = self.cmd_ticket[cid]
            pending_by[t] = pending_by.get(t, 0) + 1
        for tid, t in self.tickets.items():
            missing = 8 - len(t["slots"])
            unret += not t["returned"]
            unres += missing
            p = pending_by.get(tid, 0)
            if missing or p:
                open_t.append((len(tid), int(not t["returned"]), missing, p))
        return unret, unres, len(self.queue), open_t

    def reserve(self):
        B = self.B.bounds
        unret, unres, pend, open_t = self.counts()
        left = max(0, self.B.refusal_reserve - self.refusals)
        return (unret * B["INFERENCE_RETURN"] + unres * (B["SLOT_DISPOSITION"] + B["CHANNEL_RESULT"])
                + pend * B["CHANNEL_RESULT"] + left * B["CAPACITY_REFUSAL"] + self.B.end_bound(open_t))

    def censored(self):
        return {"unreturned_tickets": [k for k, t in self.tickets.items() if not t["returned"]],
                "unresolved_slots": {k: [i for i in range(8) if i not in t["slots"]] for k, t in self.tickets.items() if len(t["slots"]) < 8},
                "pending_commands": list(self.queue), "unresolved_outcomes": UNRESOLVED}

    def owner_ok(self, o):
        return (type(o) is dict and set(o) == OWNER_KEYS and o.get("actor_id") in self.actor_ids
                and o["role"] == self.actor_ids[o["actor_id"]]["role"] and is_int(o["actor_generation"])
                and 0 <= o["actor_generation"] and all(hexsha(o[k]) for k in ("actor_source_sha256", "weights_sha256", "input_adapter_sha256")))

    # -- per line
    def feed(self, raw, idx):
        seq = idx
        if not raw.endswith(b"\n"):
            self.viol(seq, "FORMAT", "line not newline-terminated (truncated)")
            return False
        line = raw[:-1]
        n = len(raw)
        try:
            ev = json.loads(line)
        except Exception as e:
            self.viol(seq, "FORMAT", "json parse error: %s" % type(e).__name__)
            return False
        try:
            canon = canonical(ev).encode("ascii")
        except (ValueError, TypeError) as e:
            self.viol(seq, "CANONICAL", "not canonically serializable: %s" % e)
            return False
        if canon != line:
            self.viol(seq, "CANONICAL", "line is not canonical JSON")
        if self.closed:
            self.viol(seq, "STATE", "event after CASE_END")
        if type(ev) is not dict or set(ev) != ENVELOPE_KEYS:
            self.viol(seq, "ENVELOPE", "envelope keys")
            return False
        kind, body = ev["kind"], ev["body"]
        if not (is_int(ev["seq"]) and ev["seq"] == self.events):
            self.viol(seq, "ENVELOPE", "seq %r not int == %d" % (ev["seq"], self.events))
        if ev["schema"] != EVENT_SCHEMA or ev["prev_sha256"] != self.prev or not hexsha(ev["sha256"]):
            self.viol(seq, "ENVELOPE", "schema/prev link/sha field")
        if not (is_int(ev["wall_ns"]) and 0 <= ev["wall_ns"] <= MAX_INT):
            self.viol(seq, "FIELD_RANGE", "wall_ns %r" % (ev["wall_ns"],))
        c = ev["clock"]
        if not (c is None or (type(c) is list and len(c) == 3 and all(is_int(x) and 0 <= x <= MAX_INT for x in c))):
            self.viol(seq, "FIELD_RANGE", "clock %r" % (c,))
        if kind not in KINDS or type(body) is not dict:
            self.viol(seq, "ENVELOPE", "unknown kind/body")
            return False
        self.prev = ev["sha256"]
        # line caps
        if n > self.B.max_line:
            self.viol(seq, "CAP", "line %d > max_line_bytes %d" % (n, self.B.max_line))
        # reserved-kind line bound (a)
        if kind in RESERVED_FIXED:
            bound = self.B.bounds[kind]
        elif kind == "CASE_END":
            bound = self.B.end_bound(self.counts()[3])
        else:
            bound = None
        if bound is not None:
            self.max_line[kind] = max(self.max_line.get(kind, 0), n)
            self.min_slack[kind] = min(self.min_slack.get(kind, bound), bound - n)
            if n > bound:
                self.viol(seq, "LINE_BOUND", "%s line %d > independent bound %d" % (kind, n, bound))
        try:
            self.apply(seq, kind, body)
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            self.viol(seq, "STATE", "malformed %s body: %s %s" % (kind, type(e).__name__, e))
        self.events += 1
        self.kind_counts[kind] = self.kind_counts.get(kind, 0) + 1
        self.bytes += n
        if self.bytes > self.B.cap:
            self.viol(seq, "CAP", "journal bytes %d > cap %d" % (self.bytes, self.B.cap))
        if not self.closed:
            res = self.reserve()
            head = self.B.cap - self.bytes - res
            if self.min_headroom is None or head < self.min_headroom:
                self.min_headroom, self.min_headroom_seq = head, seq
            if head < 0:
                self.viol(seq, "RESERVATION", "bytes %d + reserve %d > cap %d" % (self.bytes, res, self.B.cap))
            self.count_checks(seq)
        return True

    def count_checks(self, seq):
        unret, unres, pend, _ = self.counts()
        left = max(0, self.B.refusal_reserve - self.refusals)
        reserved_events = unret + 2 * unres + pend
        if self.events + reserved_events + 1 + left > self.B.events_cap:
            self.viol(seq, "COUNT_RESERVATION", "events %d + reserved %d + end 1 + refusals %d > %d" % (self.events, reserved_events, left, self.B.events_cap))
        need = {"INFERENCE_RETURN": unret, "SLOT_DISPOSITION": unres, "CHANNEL_RESULT": unres + pend,
                "CASE_END": 1, "CAPACITY_REFUSAL": left}
        for k, r in need.items():
            if self.kind_counts.get(k, 0) + r > self.B.kind_caps[k]:
                self.viol(seq, "COUNT_RESERVATION", "kind %s count %d + reserved %d > %d" % (k, self.kind_counts.get(k, 0), r, self.B.kind_caps[k]))

    def apply(self, seq, kind, b):
        L = self.L
        if kind == "CASE_BEGIN":
            if self.events != 0 or canonical(b.get("header")) != canonical(self.h):
                self.viol(seq, "HEADER", "CASE_BEGIN header differs from expected header or not first")
            return
        if self.events == 0:
            self.viol(seq, "STATE", "first event is not CASE_BEGIN")
        if kind == "OBSERVED_STATE":
            sid = b["state"]["state_id"]
            if not token(sid, L):
                self.viol(seq, "FIELD_RANGE", "state_id not a token")
            self.state_id = sid
        elif kind == "INFERENCE_START":
            tid = b["ticket_id"]
            if not token(tid, L) or tid in self.tickets:
                self.viol(seq, "FIELD_RANGE", "ticket id invalid/duplicate")
            self.tickets[tid] = {"returned": False, "slots": set()}
        elif kind == "INFERENCE_RETURN":
            tid = b["ticket_id"]
            t = self.tickets.get(tid)
            if t is None or t["returned"]:
                self.viol(seq, "STATE", "return for unknown/returned ticket")
                return
            if b["current_state_id"] != self.state_id:
                self.viol(seq, "STATE", "return not at current state")
            st, out = b["status"], b["output_8x9"]
            ok = (st == "OK" and type(out) is list and len(out) == 8 and all(target_row(r) for r in out)) or (st == "ERROR" and out is None)
            if not ok or not hexsha(b["snapshot_sha256"]) or not hexsha(b["output_sha256"]):
                self.viol(seq, "FIELD_RANGE", "return status/output/sha fields outside rules")
            t["returned"] = True
        elif kind == "SLOT_DISPOSITION":
            p = b["prepared"]
            if type(p) is not dict or set(p) != PREPARED_KEYS:
                self.viol(seq, "FIELD_RANGE", "prepared keys")
                return
            tid, si, d = p["ticket_id"], p["slot_index"], p["disposition"]
            t = self.tickets.get(tid)
            if t is None or not t["returned"] or not is_int(si) or not 0 <= si < 8 or si in t["slots"]:
                self.viol(seq, "STATE", "slot for unknown/unreturned ticket or bad/duplicate slot")
                return
            problems = []
            if d not in DISPOSITIONS: problems.append("disposition")
            if p["current_state_id"] != self.state_id: problems.append("current_state_id")
            want_cid = tid + ":" + str(si) if d == "SUBMIT" else None
            if p["command_id"] != want_cid or (want_cid is not None and type(p["command_id"]) is not str): problems.append("command_id")
            if d == "ERROR_NO_OUTPUT":
                if p["target_9d"] is not None or p["target_sha256"] is not None: problems.append("target for ERROR")
            elif not target_row(p["target_9d"]) or not hexsha(p["target_sha256"]): problems.append("target_9d/target_sha256")
            for k in ("desired_tick", "actor_generation"):
                if not (is_int(p[k]) and 0 <= p[k] <= MAX_INT): problems.append(k)
            if not (is_int(p["earliest_apply_tick"]) and 0 <= p["earliest_apply_tick"] <= MAX_INT + 10**6): problems.append("earliest_apply_tick")
            for k in ("known_original_failure", "original_full_failure"):
                if type(p[k]) is not bool: problems.append(k)
            if p["purpose"] not in PURPOSES: problems.append("purpose")
            a = p["authorization"]
            if not (a is None or (type(a) is dict and set(a) == {"state_id", "purpose", "target_sha256", "source_sha256"}
                                  and token(a["state_id"], L) and a["purpose"] in PURPOSES
                                  and (a["target_sha256"] is None or hexsha(a["target_sha256"])) and hexsha(a["source_sha256"]))):
                problems.append("authorization")
            if not self.owner_ok(p["owner"]): problems.append("owner")
            for k in ("input_snapshot_sha256", "return_event_sha256", "current_state_sha256", "queue_sha256",
                      "guard_source_sha256", "channel_source_sha256", "prepared_sha256"):
                if not hexsha(p[k]): problems.append(k)
            if problems:
                self.viol(seq, "FIELD_RANGE", "SLOT_DISPOSITION fields outside rules: %s" % ",".join(problems))
            t["slots"].add(si)
            if d == "SUBMIT" and type(p["command_id"]) is str:
                self.queue.append(p["command_id"])
                self.cmd_ticket[p["command_id"]] = tid
        elif kind == "CHANNEL_RESULT":
            cid = b["command_id"]
            if not self.queue or self.queue[0] != cid:
                self.viol(seq, "STATE", "channel result is not for FIFO head")
                if cid in self.queue:
                    self.queue.remove(cid)
                return
            problems = []
            if b["status"] not in CHANNEL_STATUSES: problems.append("status")
            if b["current_state_id"] != self.state_id: problems.append("current_state_id")
            if not target_row(b["actual_target_9d"]): problems.append("actual_target_9d")
            if not self.owner_ok(b["claimed_owner"]): problems.append("claimed_owner")
            if problems:
                self.viol(seq, "FIELD_RANGE", "CHANNEL_RESULT fields outside rules: %s" % ",".join(problems))
            self.queue.pop(0)
        elif kind == "CAPACITY_REFUSAL":
            if not (token(b["request_kind"], L) and token(b["reason"], L)):
                self.viol(seq, "FIELD_RANGE", "refusal tokens")
            self.refusals += 1
            if self.refusals > self.B.refusal_reserve:
                self.viol(seq, "STATE", "more refusals than refusal_reserve")
        elif kind == "CASE_END":
            if not token(b["reason"], L):
                self.viol(seq, "FIELD_RANGE", "end reason token")
            if canonical(b["censored"]) != canonical(self.censored()):
                self.viol(seq, "STATE", "CASE_END censored differs from independently tracked state")
            self.closed = True

    def report(self):
        verdict = "PASS" if not self.violations else "FAIL"
        by_cat = {}
        for v in self.violations:
            by_cat[v["category"]] = by_cat.get(v["category"], 0) + 1
        return {"verdict": verdict, "first_violation": self.violations[0] if self.violations else None,
                "violation_counts": by_cat, "events": self.events, "journal_bytes": self.bytes,
                "journal_cap": self.B.cap, "closed": self.closed,
                "min_headroom_while_open": self.min_headroom, "min_headroom_seq": self.min_headroom_seq,
                "final_reserve": 0 if self.closed else self.reserve(),
                "bounds": self.B.bounds, "max_reserved_line": self.max_line, "min_reserved_slack": self.min_slack}


def read_journal(journal_path, header):
    r = Reader(header)
    with open(journal_path, "rb") as f:
        data = f.read()
    if not data:
        r.viol(0, "FORMAT", "empty journal")
        return r.report()
    lines = data.split(b"\n")
    tail = lines.pop()  # b"" when the file ends with a newline
    for i, ln in enumerate(lines):
        r.feed(ln + b"\n", i)
    if tail:
        r.feed(tail, len(lines))
    rep = r.report()
    return rep


def selftest(n=2000):
    """Check the length calculus against json.dumps on random token structures."""
    import random
    rnd = random.Random(7)
    alphabet = [chr(c) for c in range(32, 127) if chr(c) not in '"\\']
    def tok():
        return "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 30)))
    for _ in range(n):
        keys = sorted({tok() for _ in range(rnd.randint(0, 6))})
        vals = [rnd.choice([tok(), rnd.randint(0, MAX_INT), [rnd.randint(0, 9) for _ in range(rnd.randint(0, 8))], None, False])
                for _ in keys]
        obj = dict(zip(keys, vals))
        est = jobj([(len(k), len(canonical(v))) for k, v in obj.items()])
        assert est == len(canonical(obj)), (obj, est)
        lst = [tok() for _ in range(rnd.randint(0, 6))]
        assert jlist([jstr(len(s)) for s in lst]) == len(canonical(lst))
    for v in (-2.2250738585072014e-308, -1.7976931348623157e308, -1.2345678901234567e-300, -MAX_TARGET_INT):
        assert len(canonical(v)) <= FLOAT_CHARS
    return True


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        print("selftest:", "PASS" if selftest() else "FAIL")
        return 0
    if len(argv) == 3 and argv[1] == "--bounds-only":
        with open(argv[2]) as f:
            header = json.load(f)
        print(json.dumps(Bounds(header).bounds, sort_keys=True))
        return 0
    if len(argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        return 2
    with open(argv[2]) as f:
        header = json.load(f)
    rep = read_journal(argv[1], header)
    if "--json" in argv:
        print(json.dumps(rep, sort_keys=True))
    else:
        print("verdict:", rep["verdict"])
        if rep["first_violation"]:
            print("first violation:", rep["first_violation"])
            print("violation counts:", rep["violation_counts"])
        print("events: %d  bytes: %d / cap %d  closed: %s" % (rep["events"], rep["journal_bytes"], rep["journal_cap"], rep["closed"]))
        print("min headroom while open: %s (after seq %s)" % (rep["min_headroom_while_open"], rep["min_headroom_seq"]))
        print("independent bounds:", rep["bounds"])
        print("min slack per reserved kind:", rep["min_reserved_slack"])
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
