"""Durable observation-only lifecycle markers; SDK imports and mutations absent."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import time


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def observed(getter):
    try:
        value = getter()
        if value is None:
            return {'status':'UNKNOWN','value':None,'reason':'GETTER_RETURNED_NONE'}
        # Verify builtin JSON representation before returning any live SDK value.
        canonical(value)
        return {'status': 'OBSERVED', 'value': value, 'reason': None}
    except Exception as exc:
        return {'status': 'UNKNOWN', 'value': None,
                'reason': {'exception_type': type(exc).__name__, 'message': str(exc)}}


def readonly_replicator_observations(modules):
    """Never initialize an unimported replicator to inspect its shutdown state."""
    module = modules.get('omni.replicator.core.scripts.orchestrator')
    if module is None:
        rep = modules.get('omni.replicator.core')
        module = getattr(rep, 'orchestrator', None) if rep is not None else None
    out = {'observation_scope': 'ALREADY_LOADED_MODULE_READS_ONLY_NO_CAPTURE_STOP_OR_WAIT',
           'replicator_already_loaded': module is not None,
           'actual_active_capture_complete_status': 'UNKNOWN_NO_PUBLIC_COMPLETE_CAPTURE_INVENTORY_GETTER'}
    if module is None:
        out['orchestrator_status'] = {'status': 'UNKNOWN', 'value': None, 'reason': 'MODULE_NOT_ALREADY_LOADED_NOT_INITIALIZED_FOR_OBSERVATION'}
    else:
        def status():
            value = module.get_status()
            return {'enum_name': value.name, 'enum_value': value.value}
        out['orchestrator_status'] = observed(status)
        for name in ('get_is_started', 'get_is_paused', 'get_is_stopped'):
            out[name] = observed(lambda name=name: getattr(module, name)())
        def active_triggers():
            instance = getattr(module, '_orchestrator')
            flags = {str(key): value['active'] for key, value in instance._trigger_instances.items()}
            if any(type(flag) is not bool for flag in flags.values()):
                raise ValueError('ACTUAL_TRIGGER_ACTIVE_FLAG_NOT_BOOLEAN')
            return flags
        out['observed_trigger_active_flags'] = observed(active_triggers)
        def pending_times():
            instance = getattr(module, '_orchestrator')
            return len(instance._sim_times_to_write)
        out['observed_sim_times_to_write_count'] = observed(pending_times)
    carb = modules.get('carb')
    if carb is None:
        out['capture_on_play_setting'] = {'status':'UNKNOWN','value':None,'reason':'CARB_NOT_ALREADY_LOADED'}
    else:
        out['capture_on_play_setting'] = observed(lambda: carb.settings.get_settings().get('/omni/replicator/captureOnPlay'))
    out['capture_on_play_not_proof_capture_job_active'] = True
    return out


class LifecycleObserver:
    def __init__(self, path, *, case_id, process_start_monotonic):
        self.path = Path(path)
        self.file = self.path.open('x', encoding='utf-8')
        self.case_id = case_id
        self.start = process_start_monotonic
        self.seq = 0
        self.previous = None

    def mark(self, event, *, clock_read, fields=None):
        before = observed(clock_read) if clock_read is not None else {'status':'UNKNOWN','value':None,'reason':'NO_LIVE_CLOCK_READER_AT_THIS_STAGE'}
        after = observed(clock_read) if clock_read is not None else {'status':'UNKNOWN','value':None,'reason':'NO_LIVE_CLOCK_READER_AT_THIS_STAGE'}
        row = {'schema':'NativeShutdownLifecycleMarker/1','seq':self.seq,'case_id':self.case_id,
            'event':event,'wall_unix_s':time.time(),
            'wall_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'monotonic_ns':time.monotonic_ns(),'process_elapsed_s':time.monotonic()-self.start,
            'pid':os.getpid(),'native_clock_before_read':before,'native_clock_after_read':after,
            'no_native_step_during_clock_reads':before['value']==after['value'] if before['status']==after['status']=='OBSERVED' else None,
            'fields':fields or {},'marker_write_policy':'EXCLUSIVE_JSONL_FLUSH_FSYNC_NO_NATIVE_APP_UPDATE',
            'previous_record_sha256':self.previous}
        row['record_sha256'] = digest(row)
        self.file.write(canonical(row)+'\n'); self.file.flush(); os.fsync(self.file.fileno())
        self.previous = row['record_sha256']; self.seq += 1
        return row

    def close(self):
        self.file.close()
