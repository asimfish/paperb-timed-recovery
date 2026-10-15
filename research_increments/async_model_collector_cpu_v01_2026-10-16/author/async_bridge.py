"""CPU-only versioned single-owner asynchronous collector journal.

No SDK, model, actuator, private-data isolation, S/F/R qualification or reset.
All live changes stage a deep copy, persist+fsync one event, then swap indices.
Replay is read-only; persistence uncertainty makes the live owner BROKEN.
"""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path

SCHEMA = "AsyncCollectorHeader/0.1"
PURPOSES = {"ORIGINAL_GOAL", "SAFE_LOCAL_RECOVERY", "SAFETY_ABORT"}
KINDS = {"CASE_BEGIN", "OBSERVED_STATE", "PUBLIC_PACKET", "INFERENCE_START", "INFERENCE_RETURN", "SLOT_DISPOSITION", "CHANNEL_RESULT", "ACTOR_TRANSITION", "FULL_TASK_FAILURE", "CAPACITY_REFUSAL", "CASE_END"}

class BridgeError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def require(ok, code):
    if not ok:
        raise BridgeError(code)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True).encode("ascii")

def sha256(value):
    return hashlib.sha256(value).hexdigest()

def digest(value):
    return sha256(canonical(value))

def integer(value):
    return type(value) is int and value >= 0

def hexsha(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

def bytes64(value):
    require(type(value) is bytes, "IMMUTABLE_BYTES_REQUIRED")
    return base64.b64encode(value).decode("ascii")

def row9(value):
    require(type(value) is list and len(value) == 9, "TARGET_9D_REQUIRED")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in value), "FINITE_NONBOOL_TARGET_REQUIRED")
    return copy.deepcopy(value)

def target_sha(target_9d):
    return digest(row9(target_9d))

def fixture_header():
    """Synthetic fixture convenience; caller must freeze independent expected bytes."""
    h = lambda text: sha256(text.encode())
    actors = []
    for role in ("STUDENT", "TEACHER"):
        actors.append({"actor_id": role.lower(), "role": role, "actor_source_sha256": h(role+"source"), "weights_sha256": h(role+"weights"), "input_adapter_sha256": h(role+"adapter")})
    return {"schema": SCHEMA, "mode": "CPU_FIXTURE", "attempt_id": "cpu-attempt", "failure_root_id": "cpu-root", "native_epoch": "synthetic-epoch", "original_deadline_ns": 1000000000, "deadline_clock_id": "synthetic-clock", "clock_mapping_sha256": h("clock-map"), "collector_source_sha256": h("collector-fixture"), "source_pins": {"fixture": h("fixture-only-not-native")}, "graph_id": "cpu-graph", "split": "TRAIN", "actors": actors, "initial_actor_id": "student", "horizon": 8, "action_dimension": 9, "guard_source_sha256": h("guard-fixture"), "authorization_source_sha256": h("trusted-authority-fixture"), "channel": {"source_sha256": h("fifo-channel-fixture"), "latency_ticks": 1, "semantics": "FIFO_NONCANCELLABLE"}, "caps": {"events": 100000, "tickets": 2000, "inflight": 64, "packet_archive": 3000, "asset_bytes": 20000000, "commands": 16000, "history_window": 512, "end_reserve": 1, "refusal_reserve": 8, "max_line_bytes": 4000000, "journal_bytes": 512000000, "kinds": {k: 100000 for k in KINDS}}}

def fixture_state(header, tick):
    return {"attempt_id": header["attempt_id"], "native_epoch": header["native_epoch"], "state_id": "state-"+str(tick), "physical_state_sha256": digest({"synthetic_tick": tick}), "tick": tick, "time_ns": tick*1000000, "deadline_clock_id": header["deadline_clock_id"], "deadline_time_ns": tick*1000000, "collector_source_sha256": header["collector_source_sha256"], "lawful_state": True}

def _validate_header(header, expected):
    require(type(header) is dict and canonical(header) == canonical(expected), "EXTERNAL_FULL_HEADER_MISMATCH")
    require(set(header) == set(fixture_header()), "HEADER_FIELDS_REQUIRED")
    require(header["schema"] == SCHEMA and header["mode"] == "CPU_FIXTURE", "CPU_FIXTURE_ONLY")
    require(header["horizon"] == 8 and header["action_dimension"] == 9, "FIXED_H8_9D")
    for key in ("attempt_id", "failure_root_id", "native_epoch", "deadline_clock_id", "graph_id"):
        require(type(header[key]) is str and bool(header[key]), "HEADER_ID_REQUIRED")
    require(header["split"] in ("TRAIN", "VALIDATION", "EVAL"), "HEADER_SPLIT_REQUIRED")
    require(integer(header["original_deadline_ns"]), "ORIGINAL_DEADLINE_REQUIRED")
    for key in ("clock_mapping_sha256", "collector_source_sha256", "guard_source_sha256", "authorization_source_sha256"):
        require(hexsha(header[key]), "HEADER_SHA_REQUIRED")
    require(type(header["source_pins"]) is dict and bool(header["source_pins"]) and all(type(k) is str and hexsha(v) for k,v in header["source_pins"].items()), "SOURCE_PINS_REQUIRED")
    actors = header["actors"]
    require(type(actors) is list and len(actors) >= 1, "ACTORS_REQUIRED")
    ids = set()
    for actor in actors:
        require(set(actor) == {"actor_id", "role", "actor_source_sha256", "weights_sha256", "input_adapter_sha256"}, "ACTOR_FIELDS_REQUIRED")
        require(type(actor["actor_id"]) is str and actor["actor_id"] not in ids and actor["role"] in ("STUDENT", "TEACHER"), "ACTOR_ID_OR_ROLE_INVALID")
        require(all(hexsha(actor[k]) for k in ("actor_source_sha256", "weights_sha256", "input_adapter_sha256")), "ACTOR_SOURCE_BINDING_REQUIRED")
        ids.add(actor["actor_id"])
    require(header["initial_actor_id"] in ids, "INITIAL_ACTOR_UNKNOWN")
    ch = header["channel"]
    require(set(ch) == {"source_sha256", "latency_ticks", "semantics"} and hexsha(ch["source_sha256"]) and integer(ch["latency_ticks"]) and ch["latency_ticks"] >= 1 and ch["semantics"] == "FIFO_NONCANCELLABLE", "CHANNEL_CONTRACT_INVALID")
    caps = header["caps"]
    require(set(caps) == {"events", "tickets", "inflight", "packet_archive", "asset_bytes", "commands", "history_window", "end_reserve", "refusal_reserve", "max_line_bytes", "journal_bytes", "kinds"}, "CAP_FIELDS_REQUIRED")
    require(all(integer(v) and v > 0 for k,v in caps.items() if k != "kinds"), "POSITIVE_CAPS_REQUIRED")
    require(caps["end_reserve"] == 1 and caps["inflight"] <= caps["tickets"] and caps["history_window"] <= caps["packet_archive"], "CAP_RELATION_INVALID")
    require(type(caps["kinds"]) is dict and set(caps["kinds"]) == KINDS and all(integer(v) and v > 0 for v in caps["kinds"].values()), "KIND_CAPS_REQUIRED")

def _initial(header):
    return {"header": copy.deepcopy(header), "header_sha256": digest(header), "events": 0, "journal_bytes": 0, "chain": "0"*64, "kind_counts": {}, "highwater": [-1,-1,-1,-1], "state": None, "states": {}, "packets": [], "packet_ids": [], "asset_bytes": 0, "tickets": {}, "commands": {}, "queue": [], "actor_id": header["initial_actor_id"], "actor_generation": 0, "original_full_failure": False, "known_original_failure": False, "last_applied_tick": None, "reserved_events": 0, "reserved_commands": 0, "reserved_kinds": {"INFERENCE_RETURN":0,"SLOT_DISPOSITION":0,"CHANNEL_RESULT":0}, "closed": False, "refusals": 0}

def _actor(s):
    actor = next(a for a in s["header"]["actors"] if a["actor_id"] == s["actor_id"])
    return dict(actor, actor_generation=s["actor_generation"])

def _state_check(s, state):
    h = s["header"]
    require(type(state) is dict and set(state) == set(fixture_state(h, 0)), "STATE_FIELDS_REQUIRED")
    for key in ("attempt_id", "native_epoch", "deadline_clock_id", "collector_source_sha256"):
        require(state[key] == h[key], "STATE_HEADER_BINDING_MISMATCH")
    require(type(state["state_id"]) is str and bool(state["state_id"]) and hexsha(state["physical_state_sha256"]), "STATE_ID_SHA_REQUIRED")
    require(all(integer(state[k]) for k in ("tick", "time_ns", "deadline_time_ns")) and type(state["lawful_state"]) is bool, "STATE_TYPES_INVALID")

def _current(s, state_id):
    require(s["state"] is not None and state_id == s["state"]["state_id"], "LATEST_CURRENT_STATE_REQUIRED")

def _prefix(s):
    require(s["state"] is not None, "STATE_REQUIRED")
    cap = s["header"]["caps"]["history_window"]
    rows = s["packets"][-cap:]
    return {"attempt_id": s["header"]["attempt_id"], "native_epoch": s["header"]["native_epoch"], "start": len(s["packets"])-len(rows), "end": len(s["packets"]), "length": len(rows), "packet_ids": [r["packet_id"] for r in rows], "digest": digest(rows), "as_of_time_ns": s["state"]["time_ns"]}

def _queue(s):
    commands = [s["commands"][cid] for cid in s["queue"]]
    return {"commands": copy.deepcopy(commands), "sha256": digest(commands)}

def _prepare(s, ticket_id, slot_index, state_id, queue_sha, purpose, authorization):
    _current(s, state_id)
    require(queue_sha == _queue(s)["sha256"], "CURRENT_QUEUE_MISMATCH")
    require(ticket_id in s["tickets"], "UNKNOWN_TICKET")
    t = s["tickets"][ticket_id]
    require(type(slot_index) is int and 0 <= slot_index < 8, "SLOT_INDEX_INVALID")
    require(str(slot_index) not in t["slots"], "DUPLICATE_SLOT")
    require(t["return"] is not None, "RETURN_REQUIRED")
    require(purpose == t["snapshot"]["purpose"], "FROZEN_PURPOSE_MISMATCH")
    state = s["state"]
    desired = t["snapshot"]["desired_ticks"][slot_index]
    owner = t["snapshot"]["actor"]
    earliest = state["tick"] + s["header"]["channel"]["latency_ticks"]
    if s["queue"]:
        earliest = max(earliest, s["commands"][s["queue"][-1]]["desired_tick"]+1)
    output = t["return"]["output_8x9"]
    target = None if output is None else output[slot_index]
    target_hash = None if target is None else target_sha(target)
    reason = "SUBMIT"
    if t["return"]["status"] != "OK":
        reason = "ERROR_NO_OUTPUT"
    elif desired >= t["snapshot"]["declared_end_tick"]:
        reason = "PADDING"
    elif owner != _actor(s):
        reason = "ACTOR_REVOKED"
    elif desired < earliest:
        reason = "STALE"
    else:
        if not state["lawful_state"] and purpose == "ORIGINAL_GOAL":
            reason = "GUARD_REJECTED"
        if purpose == "ORIGINAL_GOAL":
            require(authorization is None, "ORIGINAL_GOAL_AUTHORIZATION_MUST_BE_NULL")
            if state["deadline_time_ns"] > s["header"]["original_deadline_ns"] or s["original_full_failure"]:
                reason = "GUARD_REJECTED"
        else:
            if purpose == "SAFE_LOCAL_RECOVERY":
                require(s["known_original_failure"], "RECOVERY_REQUIRES_KNOWN_FAILURE")
                require(state["deadline_time_ns"] <= s["header"]["original_deadline_ns"] or s["original_full_failure"], "POST_DEADLINE_RECOVERY_REQUIRES_FULL_FALSE")
            expected = {"state_id": state_id, "purpose": purpose, "target_sha256": target_hash, "source_sha256": s["header"]["authorization_source_sha256"]}
            require(authorization == expected, "CURRENT_TARGET_AUTHORIZATION_REQUIRED")
        if reason == "SUBMIT" and len(s["commands"]) >= s["header"]["caps"]["commands"]:
            reason = "CAPACITY_REFUSED"
    prepared = {"ticket_id": ticket_id, "slot_index": slot_index, "desired_tick": desired, "target_9d": copy.deepcopy(target), "target_sha256": target_hash, "disposition": reason, "input_snapshot_sha256": t["snapshot_sha256"], "return_event_sha256": t["return_event_sha256"], "owner": copy.deepcopy(owner), "current_state_id": state_id, "current_state_sha256": digest(state), "queue_sha256": queue_sha, "actor_generation": s["actor_generation"], "known_original_failure": s["known_original_failure"], "original_full_failure": s["original_full_failure"], "earliest_apply_tick": earliest, "purpose": purpose, "authorization": copy.deepcopy(authorization), "guard_source_sha256": s["header"]["guard_source_sha256"], "channel_source_sha256": s["header"]["channel"]["source_sha256"], "command_id": (ticket_id+":"+str(slot_index)) if reason == "SUBMIT" else None}
    prepared["prepared_sha256"] = digest(prepared)
    return prepared

def _reduce(old, kind, body, clock, wall):
    """Pure semantic stage. Does not modify old or perform file/channel effects."""
    s = copy.deepcopy(old)
    body_fields={"CASE_BEGIN":{"header","header_sha256"},"OBSERVED_STATE":{"state"},"PUBLIC_PACKET":{"packet_id","public_bytes_b64","sha256","state_id"},"INFERENCE_START":{"ticket_id","snapshot","snapshot_sha256"},"INFERENCE_RETURN":{"ticket_id","snapshot_sha256","output_8x9","output_sha256","current_state_id","status"},"SLOT_DISPOSITION":{"prepared"},"CHANNEL_RESULT":{"command_id","status","current_state_id","actual_target_9d","claimed_owner"},"ACTOR_TRANSITION":{"actor_id","reason","current_state_id"},"FULL_TASK_FAILURE":{"known_original_failure","original_full_failure","evidence_sha256","current_state_id"},"CAPACITY_REFUSAL":{"request_kind","reason"},"CASE_END":{"reason","censored"}}
    require(kind in body_fields and type(body) is dict and set(body)==body_fields[kind],"EVENT_BODY_FIELDS_REQUIRED")
    require(kind in KINDS and not s["closed"], "CASE_CLOSED_OR_UNKNOWN_EVENT")
    require(integer(wall), "WALL_MONOTONIC_INTEGER_REQUIRED")
    if kind == "CASE_BEGIN":
        require(s["events"] == 0 and body == {"header": s["header"], "header_sha256": s["header_sha256"]} and clock is None, "CASE_BEGIN_INVALID")
        high = [-1,-1,-1,wall]
    else:
        require(s["events"] > 0, "CASE_BEGIN_REQUIRED")
        if kind == "OBSERVED_STATE":
            state = body["state"]
            _state_check(s, state)
            require(state["state_id"] not in s["states"], "DUPLICATE_STATE_ID")
            s["state"] = copy.deepcopy(state)
            s["states"][state["state_id"]] = copy.deepcopy(state)
        require(s["state"] is not None, "STATE_REQUIRED")
        expected_clock = [s["state"][k] for k in ("tick", "time_ns", "deadline_time_ns")]
        require(clock == expected_clock, "EVENT_CURRENT_CLOCK_MISMATCH")
        high = clock + [wall]
    require(all(a >= b for a,b in zip(high, s["highwater"])), "ACCEPTED_CLOCK_ROLLBACK")
    caps = s["header"]["caps"]
    require(s["kind_counts"].get(kind,0) < caps["kinds"][kind], "KIND_CAPACITY_REFUSED")
    if kind == "PUBLIC_PACKET":
        require(set(body) == {"packet_id", "public_bytes_b64", "sha256", "state_id"}, "PACKET_FIELDS_REQUIRED")
        _current(s, body["state_id"])
        require(type(body["packet_id"]) is str and bool(body["packet_id"]) and body["packet_id"] not in s["packet_ids"], "PACKET_ID_INVALID")
        data = base64.b64decode(body["public_bytes_b64"], validate=True)
        require(sha256(data) == body["sha256"] and len(s["packets"]) < caps["packet_archive"], "PACKET_SHA_OR_ARCHIVE_CAPACITY")
        s["asset_bytes"] += len(data)
        s["packets"].append(copy.deepcopy(body)); s["packet_ids"].append(body["packet_id"])
    elif kind == "INFERENCE_START":
        t_id = body["ticket_id"]
        require(type(t_id) is str and bool(t_id) and t_id not in s["tickets"], "TICKET_ID_INVALID_OR_DUPLICATE")
        require(len(s["tickets"]) < caps["tickets"] and sum(t["return"] is None for t in s["tickets"].values()) < caps["inflight"], "TICKET_OR_INFLIGHT_CAPACITY_REFUSED")
        snap = body["snapshot"]
        require(body["snapshot_sha256"] == digest(snap), "SNAPSHOT_SHA_MISMATCH")
        require(set(snap) == {"actor", "start_state", "input_prefix", "input_bytes_b64", "input_sha256", "input_packet_id", "assets", "desired_ticks", "declared_end_tick", "purpose", "original_contract_sha256", "wall_start_ns"}, "SNAPSHOT_FIELDS_REQUIRED")
        require(snap["actor"] == _actor(s) and snap["start_state"] == s["state"] and snap["input_prefix"] == _prefix(s), "START_ACTOR_STATE_PREFIX_MISMATCH")
        require(snap["wall_start_ns"] == wall and snap["original_contract_sha256"] == s["header_sha256"] and snap["purpose"] in PURPOSES, "FROZEN_CONTRACT_PURPOSE_MISMATCH")
        ticks = snap["desired_ticks"]
        require(type(ticks) is list and len(ticks)==8 and all(integer(v) for v in ticks) and all(a<b for a,b in zip(ticks,ticks[1:])) and ticks[0] >= s["state"]["tick"] and integer(snap["declared_end_tick"]), "ORIGINAL_SLOT_TIMES_INVALID")
        data = base64.b64decode(snap["input_bytes_b64"], validate=True)
        require(sha256(data) == snap["input_sha256"], "ACTUAL_INPUT_SHA_MISMATCH")
        require(s["packets"] and snap["input_packet_id"] == s["packets"][-1]["packet_id"] and snap["input_bytes_b64"] == s["packets"][-1]["public_bytes_b64"] and snap["input_sha256"] == s["packets"][-1]["sha256"], "ACTUAL_INPUT_MUST_EQUAL_LATEST_DELIVERED_PACKET")
        require(snap["assets"] == [], "ASSET_BINDINGS_UNSUPPORTED_NONEMPTY_REFUSED")
        added = len(data)
        for asset in snap["assets"]:
            require(set(asset) == {"bytes_b64", "sha256"}, "PUBLIC_ASSET_FIELDS_REQUIRED")
            raw = base64.b64decode(asset["bytes_b64"], validate=True)
            require(sha256(raw) == asset["sha256"], "PUBLIC_ASSET_SHA_MISMATCH")
            added += len(raw)
        s["asset_bytes"] += added
        s["tickets"][t_id] = {"snapshot": copy.deepcopy(snap), "snapshot_sha256": body["snapshot_sha256"], "return": None, "return_event_sha256": None, "slots": {}}
        require(len(s["commands"])+s["reserved_commands"]+8 <= caps["commands"], "WHOLE_TICKET_COMMAND_CAPACITY_REFUSED")
        s["reserved_events"] += 17
        s["reserved_commands"] += 8
        s["reserved_kinds"]["INFERENCE_RETURN"] += 1
        s["reserved_kinds"]["SLOT_DISPOSITION"] += 8
        s["reserved_kinds"]["CHANNEL_RESULT"] += 8
    elif kind == "INFERENCE_RETURN":
        _current(s, body["current_state_id"])
        require(body["ticket_id"] in s["tickets"], "UNKNOWN_TICKET")
        t=s["tickets"][body["ticket_id"]]
        require(t["return"] is None, "DUPLICATE_RETURN")
        require(body["snapshot_sha256"] == t["snapshot_sha256"], "RETURN_START_SNAPSHOT_MISMATCH")
        require(body["status"] in ("OK", "ERROR"), "RETURN_STATUS_INVALID")
        if body["status"] == "OK":
            require(type(body["output_8x9"]) is list and len(body["output_8x9"]) == 8, "OUTPUT_H8_REQUIRED")
            for row in body["output_8x9"]: row9(row)
        else:
            require(body["output_8x9"] is None, "ERROR_OUTPUT_MUST_BE_NULL")
        require(body["output_sha256"] == digest(body["output_8x9"]), "OUTPUT_SHA_MISMATCH")
        t["return"] = copy.deepcopy(body)
        s["reserved_events"] -= 1
        s["reserved_kinds"]["INFERENCE_RETURN"] -= 1
    elif kind == "SLOT_DISPOSITION":
        p=body["prepared"]
        expected=_prepare(s,p["ticket_id"],p["slot_index"],p["current_state_id"],p["queue_sha256"],p["purpose"],p["authorization"])
        require(p == expected, "PREPARED_STALE_OR_TAMPERED")
        t=s["tickets"][p["ticket_id"]]
        t["slots"][str(p["slot_index"])]=copy.deepcopy(p)
        s["reserved_events"] -= 1
        s["reserved_commands"] -= 1
        s["reserved_kinds"]["SLOT_DISPOSITION"] -= 1
        if p["disposition"] != "SUBMIT":
            s["reserved_events"] -= 1
            s["reserved_kinds"]["CHANNEL_RESULT"] -= 1
        if p["disposition"] == "SUBMIT":
            cid=p["command_id"]
            require(cid not in s["commands"], "DUPLICATE_COMMAND")
            cmd={"command_id": cid, "ticket_id": p["ticket_id"], "slot_index":p["slot_index"], "desired_tick":p["desired_tick"], "ready_tick":p["earliest_apply_tick"], "owner":p["owner"], "target_9d":p["target_9d"], "target_sha256":p["target_sha256"], "purpose":p["purpose"], "submit_state_id":p["current_state_id"], "status":"SUBMITTED"}
            s["commands"][cid]=copy.deepcopy(cmd);s["queue"].append(cid)
    elif kind == "CHANNEL_RESULT":
        _current(s,body["current_state_id"])
        cid=body["command_id"]
        require(cid in s["commands"] and cid in s["queue"], "SUBMITTED_PENDING_COMMAND_REQUIRED")
        cmd=s["commands"][cid]
        require(body["claimed_owner"] == cmd["owner"] and target_sha(body["actual_target_9d"]) == cmd["target_sha256"], "CHANNEL_OWNER_TARGET_MISMATCH")
        require(body["status"] in ("APPLIED", "REJECTED", "DROPPED"), "CHANNEL_STATUS_INVALID")
        require(s["queue"][0] == cid, "FIFO_HEAD_REQUIRED")
        if body["status"] == "APPLIED":
            tick=s["state"]["tick"]
            require(tick >= cmd["ready_tick"] and tick == cmd["desired_tick"], "APPLIED_ORIGINAL_TICK_OR_READY_MISMATCH")
            require(s["last_applied_tick"] != tick, "ONE_APPLIED_PER_TICK")
            s["last_applied_tick"]=tick
        cmd["status"]=body["status"];cmd["result_state_id"]=body["current_state_id"]
        s["queue"].pop(0)
        s["reserved_events"] -= 1
        s["reserved_kinds"]["CHANNEL_RESULT"] -= 1
    elif kind == "ACTOR_TRANSITION":
        _current(s,body["current_state_id"])
        require(body["actor_id"] in {a["actor_id"] for a in s["header"]["actors"]} and type(body["reason"]) is str and bool(body["reason"]), "ACTOR_TRANSITION_INVALID")
        s["actor_id"]=body["actor_id"];s["actor_generation"]+=1
    elif kind == "FULL_TASK_FAILURE":
        _current(s,body["current_state_id"])
        require(type(body["known_original_failure"]) is bool and type(body["original_full_failure"]) is bool and hexsha(body["evidence_sha256"]), "FAILURE_EVIDENCE_INVALID")
        require(not body["original_full_failure"] or body["known_original_failure"], "FULL_FALSE_REQUIRES_KNOWN_FAILURE")
        require((not s["known_original_failure"] or body["known_original_failure"]) and (not s["original_full_failure"] or body["original_full_failure"]), "HARD_FAILURE_ABSORBING")
        s["known_original_failure"]=body["known_original_failure"];s["original_full_failure"]=body["original_full_failure"]
    elif kind == "CAPACITY_REFUSAL":
        require(type(body["request_kind"]) is str and type(body["reason"]) is str and bool(body["reason"]), "REFUSAL_REASON_REQUIRED")
        require(s["refusals"] < caps["refusal_reserve"], "REFUSAL_RESERVE_EXHAUSTED")
        s["refusals"]+=1
    elif kind == "CASE_END":
        require(type(body["reason"]) is str and bool(body["reason"]), "END_REASON_REQUIRED")
        expected={"unreturned_tickets":[k for k,t in s["tickets"].items() if t["return"] is None], "unresolved_slots":{k:[i for i in range(8) if str(i) not in t["slots"]] for k,t in s["tickets"].items() if len(t["slots"])<8}, "pending_commands":copy.deepcopy(s["queue"]), "unresolved_outcomes":"UNKNOWN_NO_AUTOMATIC_RESEND"}
        require(body["censored"] == expected, "CLOSURE_CENSORING_MISMATCH")
        s["reserved_events"]=0;s["reserved_commands"]=0;s["reserved_kinds"]={k:0 for k in s["reserved_kinds"]};s["closed"]=True
    require(s["asset_bytes"] <= caps["asset_bytes"], "ASSET_CAPACITY_REFUSED")
    reserve = 0 if kind=="CASE_END" else caps["end_reserve"] + max(0,caps["refusal_reserve"]-s["refusals"])
    require(s["events"]+1+s["reserved_events"]+reserve <= caps["events"], "EVENT_CAPACITY_REFUSED")
    s["events"]+=1;s["kind_counts"][kind]=s["kind_counts"].get(kind,0)+1;s["highwater"]=high
    for event_kind, count in s["reserved_kinds"].items():
        require(s["kind_counts"].get(event_kind,0)+count <= caps["kinds"][event_kind], "WHOLE_TICKET_KIND_CAPACITY_REFUSED")
    if not s["closed"]:
        require(s["kind_counts"].get("CASE_END",0)+1 <= caps["kinds"]["CASE_END"], "END_KIND_RESERVE_REQUIRED")
        require(s["kind_counts"].get("CAPACITY_REFUSAL",0)+caps["refusal_reserve"]-s["refusals"] <= caps["kinds"]["CAPACITY_REFUSAL"], "REFUSAL_KIND_RESERVE_REQUIRED")
    return s

class AsyncBridge:
    def __init__(self,journal_path,header,*,expected_header,persist_hook=None):
        _validate_header(header,expected_header)
        self.path=Path(journal_path);self.broken=False;self.read_only=False;self._hook=persist_hook
        self._s=_initial(header)
        self._f=open(self.path,"xb",buffering=0)
        self._commit("CASE_BEGIN",{"header":copy.deepcopy(header),"header_sha256":digest(header)},wall_ns=0,clock=None)

    def snapshot(self):
        return copy.deepcopy(self._s)

    def _commit(self,kind,body,*,wall_ns,clock="CURRENT"):
        require(not self.broken,"JOURNAL_BROKEN")
        require(not self.read_only,"READ_ONLY_REPLAY")
        body=copy.deepcopy(body)
        if clock=="CURRENT":
            state=body["state"] if kind=="OBSERVED_STATE" else self._s["state"]
            require(state is not None,"STATE_REQUIRED")
            clock=[state[k] for k in ("tick","time_ns","deadline_time_ns")]
        stage=_reduce(self._s,kind,body,clock,wall_ns)
        event={"schema":"AsyncCollectorEvent/0.1","seq":self._s["events"],"prev_sha256":self._s["chain"],"kind":kind,"body":body,"clock":clock,"wall_ns":wall_ns}
        event["sha256"]=digest(event)
        encoded=canonical(event)+b"\n"
        require(len(encoded) <= self._s["header"]["caps"]["max_line_bytes"],"JOURNAL_LINE_BYTE_CAPACITY_REFUSED")
        require(self._s["journal_bytes"]+len(encoded) <= self._s["header"]["caps"]["journal_bytes"],"JOURNAL_TOTAL_BYTE_CAPACITY_REFUSED")
        stage["journal_bytes"]=self._s["journal_bytes"]+len(encoded)
        try:
            if self._hook:self._hook("before_write",copy.deepcopy(event),self._f)
            count=self._f.write(encoded)
            if count != len(encoded):raise OSError("short journal write")
            if self._hook:self._hook("after_write",copy.deepcopy(event),self._f)
            self._f.flush()
            if self._hook:self._hook("after_flush",copy.deepcopy(event),self._f)
            os.fsync(self._f.fileno())
            if self._hook:self._hook("after_fsync",copy.deepcopy(event),self._f)
        except Exception:
            self.broken=True
            raise
        stage["chain"]=event["sha256"]
        if kind=="INFERENCE_RETURN":stage["tickets"][body["ticket_id"]]["return_event_sha256"]=event["sha256"]
        self._s=stage
        return copy.deepcopy(event)

    def observe_state(self,state,*,wall_ns):
        return self._commit("OBSERVED_STATE",{"state":copy.deepcopy(state)},wall_ns=wall_ns)

    def publish_packet(self,packet_id,public_bytes,*,wall_ns):
        return self._commit("PUBLIC_PACKET",{"packet_id":packet_id,"public_bytes_b64":bytes64(public_bytes),"sha256":sha256(public_bytes),"state_id":self._s["state"]["state_id"]},wall_ns=wall_ns)

    def prefix(self):return copy.deepcopy(_prefix(self._s))
    def queue_snapshot(self):return _queue(self._s)

    def start_inference(self,ticket_id,*,actor_id,actual_input_bytes,actual_asset_bytes=(),desired_ticks,declared_end_tick,purpose="ORIGINAL_GOAL",wall_ns):
        require(actor_id==self._s["actor_id"],"CURRENT_ACTOR_REQUIRED")
        require(not actual_asset_bytes,"ASSET_BINDINGS_UNSUPPORTED_NONEMPTY_REFUSED")
        require(self._s["packets"],"DELIVERED_PUBLIC_INPUT_PACKET_REQUIRED")
        snap={"actor":_actor(self._s),"start_state":copy.deepcopy(self._s["state"]),"input_prefix":_prefix(self._s),"input_bytes_b64":bytes64(actual_input_bytes),"input_sha256":sha256(actual_input_bytes),"input_packet_id":self._s["packets"][-1]["packet_id"],"assets":[{"bytes_b64":bytes64(a),"sha256":sha256(a)} for a in actual_asset_bytes],"desired_ticks":copy.deepcopy(desired_ticks),"declared_end_tick":declared_end_tick,"purpose":purpose,"original_contract_sha256":self._s["header_sha256"],"wall_start_ns":wall_ns}
        return self._commit("INFERENCE_START",{"ticket_id":ticket_id,"snapshot":snap,"snapshot_sha256":digest(snap)},wall_ns=wall_ns)

    def accept_return(self,ticket_id,*,snapshot_sha256,output_8x9,current_state_id,wall_ns,status="OK"):
        body={"ticket_id":ticket_id,"snapshot_sha256":snapshot_sha256,"output_8x9":copy.deepcopy(output_8x9),"output_sha256":digest(output_8x9),"current_state_id":current_state_id,"status":status}
        return self._commit("INFERENCE_RETURN",body,wall_ns=wall_ns)

    def prepare_slot(self,ticket_id,slot_index,*,current_state_id,queue_sha256,purpose,authorization=None):
        require(not self.broken,"JOURNAL_BROKEN")
        require(not self._s["closed"],"CASE_CLOSED_OR_UNKNOWN_EVENT")
        return copy.deepcopy(_prepare(self._s,ticket_id,slot_index,current_state_id,queue_sha256,purpose,authorization))

    def commit_slot(self,prepared,*,current_state_id,queue_sha256,wall_ns):
        require(prepared["current_state_id"]==current_state_id and prepared["queue_sha256"]==queue_sha256,"PREPARED_EXPECTATION_MISMATCH")
        return self._commit("SLOT_DISPOSITION",{"prepared":copy.deepcopy(prepared)},wall_ns=wall_ns)

    def record_channel_result(self,command_id,*,status,current_state_id,actual_target_9d,claimed_owner,wall_ns):
        return self._commit("CHANNEL_RESULT",{"command_id":command_id,"status":status,"current_state_id":current_state_id,"actual_target_9d":copy.deepcopy(actual_target_9d),"claimed_owner":copy.deepcopy(claimed_owner)},wall_ns=wall_ns)

    def transition_actor(self,actor_id,*,reason,current_state_id,wall_ns):
        return self._commit("ACTOR_TRANSITION",{"actor_id":actor_id,"reason":reason,"current_state_id":current_state_id},wall_ns=wall_ns)

    def record_failure(self,*,known_original_failure,original_full_failure,evidence_sha256,current_state_id,wall_ns):
        return self._commit("FULL_TASK_FAILURE",{"known_original_failure":known_original_failure,"original_full_failure":original_full_failure,"evidence_sha256":evidence_sha256,"current_state_id":current_state_id},wall_ns=wall_ns)

    def record_capacity_refusal(self,request_kind,reason,*,wall_ns):
        return self._commit("CAPACITY_REFUSAL",{"request_kind":request_kind,"reason":reason},wall_ns=wall_ns)

    def close(self,*,reason,wall_ns):
        s=self._s
        censored={"unreturned_tickets":[k for k,t in s["tickets"].items() if t["return"] is None],"unresolved_slots":{k:[i for i in range(8) if str(i) not in t["slots"]] for k,t in s["tickets"].items() if len(t["slots"])<8},"pending_commands":copy.deepcopy(s["queue"]),"unresolved_outcomes":"UNKNOWN_NO_AUTOMATIC_RESEND"}
        event=self._commit("CASE_END",{"reason":reason,"censored":censored},wall_ns=wall_ns)
        self._f.close()
        return event

    @classmethod
    def replay(cls,journal_path,*,expected_header):
        path=Path(journal_path)
        obj=cls.__new__(cls);obj.path=path;obj.broken=False;obj.read_only=True;obj._hook=None;obj._f=None
        _validate_header(expected_header,expected_header)
        limits=expected_header["caps"]
        require(path.stat().st_size <= limits["journal_bytes"],"READER_FILE_BYTE_CAPACITY_REFUSED")
        def bounded_lines():
            with open(path,"rb") as file:
                count=0
                while True:
                    raw=file.readline(limits["max_line_bytes"]+1)
                    if not raw:break
                    require(len(raw) <= limits["max_line_bytes"],"READER_LINE_BYTE_CAPACITY_REFUSED")
                    require(raw.endswith(b"\n"),"TRUNCATED_JOURNAL_UNKNOWN")
                    count+=1
                    require(count <= limits["events"],"READER_EVENT_CAPACITY_REFUSED")
                    yield raw[:-1]
        lines=bounded_lines()
        try:first_line=next(lines)
        except StopIteration:raise BridgeError("EMPTY_JOURNAL")
        first=json.loads(first_line);header=first["body"]["header"]
        _validate_header(header,expected_header)
        s=_initial(header)
        import itertools
        for line in itertools.chain([first_line],lines):
            event=json.loads(line)
            require(set(event)=={"schema","seq","prev_sha256","kind","body","clock","wall_ns","sha256"},"EVENT_FIELDS_REQUIRED")
            require(event["schema"]=="AsyncCollectorEvent/0.1" and event["seq"]==s["events"] and event["prev_sha256"]==s["chain"],"EVENT_CHAIN_ORDER_MISMATCH")
            unsigned={k:v for k,v in event.items() if k!="sha256"}
            require(event["sha256"]==digest(unsigned) and canonical(event)==line,"EVENT_HASH_OR_CANONICAL_MISMATCH")
            stage=_reduce(s,event["kind"],event["body"],event["clock"],event["wall_ns"])
            stage["chain"]=event["sha256"]
            stage["journal_bytes"]=s["journal_bytes"]+len(line)+1
            if event["kind"]=="INFERENCE_RETURN":stage["tickets"][event["body"]["ticket_id"]]["return_event_sha256"]=event["sha256"]
            s=stage
        obj._s=s
        return obj
