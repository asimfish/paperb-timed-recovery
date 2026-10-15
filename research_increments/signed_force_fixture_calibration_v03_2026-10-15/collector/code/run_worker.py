"""One owned worker on one explicitly admitted GPU. No foreign process signals."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import execution_gate as force_gate
import signal
import subprocess
import time

ROOT=Path(__file__).parent
CAPSULE=Path('/tmp/chemrm-papera-v15/pilot/paperA/driver_library_isolation_v54_20261011/capsule_r2')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def prior_native_output_exists(root,case_id):
    root=Path(root)
    return (root/'cases'/case_id).exists() or (root/'logs'/(case_id+'.json')).exists()

def resource_refusal_path(root,case_id,attempt_id):
    return Path(root)/'resource_gate_attempts'/case_id/(attempt_id+'.json')

def verify_sources():
    return force_gate.verify_sources(ROOT)


def live_group(pgid):
    values=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if os.getpgid(int(p.name))==pgid and (p/'stat').read_text().split(') ',1)[1].split()[0]!='Z':values.append(int(p.name))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    return values

def cleanup_owned_group(pgid,timeout_s=30.):
    """Only the worker-created session; observe emptiness after any SIGKILL."""
    if type(pgid) is not int or pgid<=0 or pgid==os.getpgrp():
        raise ValueError('EXACT_OWNED_CHILD_PROCESS_GROUP_REQUIRED')
    start=time.monotonic();left=live_group(pgid)
    if left:
        try:os.killpg(pgid,signal.SIGKILL)
        except ProcessLookupError:pass
    while left and time.monotonic()-start<timeout_s:
        time.sleep(.05);left=live_group(pgid)
    return left,time.monotonic()-start

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--case',required=True);p.add_argument('--gpu-uuid',required=True)
    p.add_argument('--verify-only',action='store_true')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--admission')
    p.add_argument('--source-review')
    p.add_argument('--reader-freeze')
    a=p.parse_args()
    release=verify_sources();protocol=json.loads((ROOT/'protocol.json').read_text())
    cases=[c for c in protocol['cases'] if c['id']==a.case]
    if len(cases)!=1:raise ValueError('unknown frozen case')
    case=cases[0]
    if a.verify_only:
        print(json.dumps(dict(status='SOURCE_VERIFIED_NO_GPU_ALLOCATION',case=a.case,files=len(release['files']))));return
    if not a.execute or not a.admission or not a.source_review or not a.reader_freeze:
        raise ValueError('Explicit execute, independent source review and root admission required; no native started')
    independent=json.loads(Path(a.source_review).read_text())
    admitted=json.loads(Path(a.admission).read_text())
    release_sha=sha(ROOT/'EXECUTION_RELEASE.json')
    force_gate.validate_review_root(independent,admitted,release_sha,sha(a.source_review),a.case,a.gpu_uuid,sha(a.reader_freeze))
    if prior_native_output_exists(ROOT,a.case):
        raise ValueError('prior output preserved; no overwrite/restart allowed')
    lock=open('/tmp/paperb-native-'+a.gpu_uuid+'.lock','a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    attempt_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+str(os.getpid())
    env=dict(os.environ);env['LD_LIBRARY_PATH']=str(CAPSULE)
    # Read-only subprocess avoids importing incompatible NVML into this worker.
    try:
        admission=json.loads(subprocess.check_output(['python3',str(ROOT/'gpu_mapping.py'),'--uuid',a.gpu_uuid],env=env,text=True))
    except subprocess.CalledProcessError as e:
        write(resource_refusal_path(ROOT,a.case,attempt_id),dict(status='RESOURCE_GATE_REFUSED',exit_code=e.returncode,gpu_uuid=a.gpu_uuid,
              case_id=a.case,attempt_id=attempt_id,foreign_processes_signaled=False,gpu_work_started=False,
              formal_episode_started=False,retry_after_resource_change_allowed=True,
              allocated_gpu_hours_upper_bound=0,model_calls=0,training_gpu_hours=0));raise
    force_gate.validate_live_gpu(admission,a.gpu_uuid)
    write(ROOT/'admission'/a.case/(attempt_id+'.json'),admission)
    gate_path=ROOT/'gate_attempts'/a.case/(attempt_id+'.json')
    write(gate_path,dict(case_id=a.case,source_release_sha256=release_sha,source_review_path=str(Path(a.source_review).resolve()),root_admission_path=str(Path(a.admission).resolve()),root_admission_sha256=sha(a.admission),source_review_sha256=sha(a.source_review),reader_freeze_path=str(Path(a.reader_freeze).resolve()),reader_freeze_sha256=sha(a.reader_freeze),gpu_uuid=a.gpu_uuid,live_gpu=admission,issued_at_unix_s=time.time()))
    env['PAPERB_FORCE_GATE_RECEIPT']=str(gate_path)
    child=None;start=time.monotonic();timed_out=False;code=None;remaining=[];cleanup_wall_s=0.
    try:
        log_path=ROOT/'launch_attempts'/a.case/(attempt_id+'.log')
        log_path.parent.mkdir(parents=True,exist_ok=True)
        with log_path.open('x') as log:
            child=subprocess.Popen(['bash',str(ROOT/'launch_worker.sh'),a.case,a.gpu_uuid],stdout=log,stderr=subprocess.STDOUT,
                                   env=env,start_new_session=True)
            write(ROOT/'running'/a.case/(attempt_id+'.json'),dict(case_id=a.case,attempt_id=attempt_id,pid=child.pid,pgid=child.pid,gpu_uuid=a.gpu_uuid,
                started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),max_seconds=protocol['max_worker_seconds']))
            try:code=child.wait(timeout=protocol['max_worker_seconds'])
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(child.pid,signal.SIGTERM)
                try:code=child.wait(timeout=15)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait(timeout=15)
        remaining,cleanup_wall_s=cleanup_owned_group(child.pid)
        verify_sources()
    finally:
        if child is not None:
            left,extra_cleanup_s=cleanup_owned_group(child.pid)
            remaining=left;cleanup_wall_s+=extra_cleanup_s
        wall=time.monotonic()-start
        native_output_exists=(ROOT/'cases'/a.case).exists()
        resource_refused=code==42 and not native_output_exists
        terminal_path=resource_refusal_path(ROOT,a.case,attempt_id) if resource_refused else ROOT/'logs'/(a.case+'.json')
        write(terminal_path,dict(status='RESOURCE_GATE_REFUSED' if resource_refused else 'COMPLETE' if code==0 and not remaining else 'FAILED_RETAINED',
            case_id=a.case,gpu_uuid=a.gpu_uuid,exit_code=code,timed_out=timed_out,wall_s=wall,
            attempt_id=attempt_id,launch_log=str(log_path.relative_to(ROOT)),native_output_exists=native_output_exists,
            formal_episode_started=force_gate.formal_native_started(ROOT,a.case),retry_after_resource_change_allowed=resource_refused,
            allocated_gpu_hours_upper_bound=0 if resource_refused else wall/3600,owned_process_group_empty=not remaining,
            owned_cleanup_wall_s=cleanup_wall_s,remaining_owned_process_ids=remaining,
            cost_scope='OWNED_CHILD_ATTEMPT_WALL_UPPER_BOUND_INCLUDING_STARTUP_AND_FAILED_LAUNCHES; RESOURCE_REFUSAL_WITHOUT_NATIVE_ONLY_ZERO',
            model_calls=0,training_gpu_hours=0,foreign_processes_signaled=False,gpu_global_configuration_changes=False))
    print(json.dumps(dict(case_id=a.case,exit_code=code,timed_out=timed_out,wall_s=wall)))
    if code or remaining:raise SystemExit(code or 1)

if __name__=='__main__':main()
