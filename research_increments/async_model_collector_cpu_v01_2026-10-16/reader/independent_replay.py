"""Bounded, independent semantic audit of AsyncCollectorEvent/0.1.

No import of the author's module. This is a separately written property checker,
not a second dispatcher or physical evidence validator. Original bytes retained.
"""
from __future__ import annotations
import argparse,base64,collections,copy,hashlib,json,pathlib

def C(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def H(x):return hashlib.sha256(x).hexdigest()
def D(x):return H(C(x))
def A(ok,msg):
    if not ok:raise ValueError(msg)
def I(x):return type(x) is int and x>=0
def nine(x):
    import math
    return type(x) is list and len(x)==9 and all(type(v) in (int,float) and math.isfinite(v) for v in x)
FIELDS={'CASE_BEGIN':{'header','header_sha256'},'OBSERVED_STATE':{'state'},'PUBLIC_PACKET':{'packet_id','public_bytes_b64','sha256','state_id'},'INFERENCE_START':{'ticket_id','snapshot','snapshot_sha256'},'INFERENCE_RETURN':{'ticket_id','snapshot_sha256','output_8x9','output_sha256','current_state_id','status'},'SLOT_DISPOSITION':{'prepared'},'CHANNEL_RESULT':{'command_id','status','current_state_id','actual_target_9d','claimed_owner'},'ACTOR_TRANSITION':{'actor_id','reason','current_state_id'},'FULL_TASK_FAILURE':{'known_original_failure','original_full_failure','evidence_sha256','current_state_id'},'CAPACITY_REFUSAL':{'request_kind','reason'},'CASE_END':{'reason','censored'}}
class Audit:
    def __init__(self,expected):
        self.h=copy.deepcopy(expected);self.state=None;self.states={};self.packets=[];self.tickets={};self.commands={};self.queue=[];self.actor=expected['initial_actor_id'];self.gen=0;self.full=False;self.known=False;self.clock=[-1]*4;self.chain='0'*64;self.seq=0;self.counts=collections.Counter();self.closed=False;self.applied=set();self.asset_bytes=0;self.refusals=0;self.ret_events={}
    def owner(self):return dict(next(a for a in self.h['actors'] if a['actor_id']==self.actor),actor_generation=self.gen)
    def current(self,sid):A(self.state is not None and sid==self.state['state_id'],'LATEST_STATE_LINK')
    def prefix(self):
        p=self.packets[-self.h['caps']['history_window']:]
        return {'attempt_id':self.h['attempt_id'],'native_epoch':self.h['native_epoch'],'start':len(self.packets)-len(p),'end':len(self.packets),'length':len(p),'packet_ids':[x['packet_id'] for x in p],'digest':D(p),'as_of_time_ns':self.state['time_ns']}
    def accept(self,e):
        A(not self.closed,'AFTER_CLOSED');A(set(e)=={'schema','seq','prev_sha256','kind','body','clock','wall_ns','sha256'},'EVENT_FIELDS')
        A(e['schema']=='AsyncCollectorEvent/0.1' and e['seq']==self.seq and e['prev_sha256']==self.chain,'EVENT_ORDER')
        A(e['sha256']==D({k:v for k,v in e.items() if k!='sha256'}),'EVENT_SHA')
        k=e['kind'];b=e['body'];A(k in FIELDS and set(b)==FIELDS[k],'BODY_FIELDS');A(I(e['wall_ns']),'WALL_TYPE')
        if k=='CASE_BEGIN':
            A(self.seq==0 and C(b['header'])==C(self.h) and b['header_sha256']==D(self.h) and e['clock'] is None,'EXTERNAL_HEADER_BEGIN')
            high=[-1,-1,-1,e['wall_ns']]
        else:
            if k=='OBSERVED_STATE':
                s=b['state'];A(s['state_id'] not in self.states,'DUPLICATE_STATE')
                for key in ('attempt_id','native_epoch','deadline_clock_id','collector_source_sha256'):A(s[key]==self.h[key],'FOREIGN_STATE_HEADER')
                A(all(I(s[key]) for key in ('tick','time_ns','deadline_time_ns')) and type(s['lawful_state']) is bool,'STATE_TYPES')
                self.state=copy.deepcopy(s);self.states[s['state_id']]=copy.deepcopy(s)
            A(self.state is not None,'STATE_BEFORE_EVENT');clk=[self.state[x] for x in ('tick','time_ns','deadline_time_ns')]
            A(e['clock']==clk,'CURRENT_EVENT_CLOCK');high=clk+[e['wall_ns']]
        A(all(x>=y for x,y in zip(high,self.clock)),'MONOTONE_ARRIVAL_CLOCK')
        if k=='PUBLIC_PACKET':
            self.current(b['state_id']);A(b['packet_id'] not in [p['packet_id'] for p in self.packets],'PACKET_REUSE')
            raw=base64.b64decode(b['public_bytes_b64'],validate=True);A(H(raw)==b['sha256'],'PACKET_DIGEST');self.asset_bytes+=len(raw);self.packets.append(copy.deepcopy(b))
        elif k=='INFERENCE_START':
            tid=b['ticket_id'];s=b['snapshot'];A(tid not in self.tickets,'TICKET_REUSE');A(D(s)==b['snapshot_sha256'],'SNAPSHOT_HASH')
            A(s['actor']==self.owner() and s['start_state']==self.state and s['input_prefix']==self.prefix(),'START_SOURCE_STATE_PREFIX')
            A(s['wall_start_ns']==e['wall_ns'] and s['original_contract_sha256']==D(self.h),'START_CONTRACT_WALL')
            A(self.packets and s['input_packet_id']==self.packets[-1]['packet_id'] and s['input_bytes_b64']==self.packets[-1]['public_bytes_b64'] and s['input_sha256']==self.packets[-1]['sha256'],'ACTUAL_INPUT_NOT_LATEST_PACKET')
            raw=base64.b64decode(s['input_bytes_b64'],validate=True);A(H(raw)==s['input_sha256'] and s['assets']==[],'INPUT_BYTES_ASSETS')
            A(s['purpose'] in ('ORIGINAL_GOAL','SAFE_LOCAL_RECOVERY','SAFETY_ABORT'),'FROZEN_PURPOSE')
            t=s['desired_ticks'];A(type(t) is list and len(t)==8 and all(I(v) for v in t) and all(x<y for x,y in zip(t,t[1:])) and t[0]>=self.state['tick'],'SLOT_ORIGINAL_TIMES')
            self.asset_bytes+=len(raw);self.tickets[tid]={'snapshot':copy.deepcopy(s),'sha':b['snapshot_sha256'],'return':None,'slots':{}}
        elif k=='INFERENCE_RETURN':
            self.current(b['current_state_id']);tid=b['ticket_id'];A(tid in self.tickets,'RETURN_UNKNOWN');t=self.tickets[tid]
            A(t['return'] is None and b['snapshot_sha256']==t['sha'],'RETURN_ORIGINAL_BINDING')
            o=b['output_8x9'];A(b['output_sha256']==D(o),'OUTPUT_SHA')
            A((b['status']=='ERROR' and o is None) or (b['status']=='OK' and type(o) is list and len(o)==8 and all(nine(r) for r in o)),'OUTPUT_H8_9D_STATUS')
            t['return']=copy.deepcopy(b);self.ret_events[tid]=e['sha256']
        elif k=='SLOT_DISPOSITION':
            p=b['prepared'];tid=p['ticket_id'];A(tid in self.tickets,'SLOT_UNKNOWN_TICKET');t=self.tickets[tid];s=t['snapshot'];r=t['return'];i=p['slot_index']
            A(type(i) is int and 0<=i<8 and i not in t['slots'] and r is not None,'SLOT_MEMBERSHIP')
            self.current(p['current_state_id']);queue=[self.commands[c] for c in self.queue]
            A(p['current_state_sha256']==D(self.state) and p['queue_sha256']==D(queue),'CURRENT_GUARD_STATE_QUEUE')
            A(p['prepared_sha256']==D({k:v for k,v in p.items() if k!='prepared_sha256'}),'PREPARED_HASH')
            A(p['owner']==s['actor'] and p['actor_generation']==self.gen and p['input_snapshot_sha256']==t['sha'] and p['return_event_sha256']==self.ret_events[tid],'ORIGINAL_INPUT_OWNER_REF')
            A(p['known_original_failure']==self.known and p['original_full_failure']==self.full and p['purpose']==s['purpose'],'GUARD_FAILURE_PURPOSE')
            A(p['guard_source_sha256']==self.h['guard_source_sha256'] and p['channel_source_sha256']==self.h['channel']['source_sha256'],'GUARD_CHANNEL_SOURCE')
            desired=s['desired_ticks'][i];target=None if r['output_8x9'] is None else r['output_8x9'][i]
            A(p['desired_tick']==desired and p['target_9d']==target and p['target_sha256']==(None if target is None else D(target)),'ORIGINAL_SLOT_TARGET')
            earliest=max([self.state['tick']+self.h['channel']['latency_ticks']]+([queue[-1]['desired_tick']+1] if queue else []));A(p['earliest_apply_tick']==earliest,'FIFO_EARLIEST')
            if r['status']!='OK':reason='ERROR_NO_OUTPUT'
            elif desired>=s['declared_end_tick']:reason='PADDING'
            elif s['actor']!=self.owner():reason='ACTOR_REVOKED'
            elif desired<earliest:reason='STALE'
            else:
                reason='GUARD_REJECTED' if s['purpose']=='ORIGINAL_GOAL' and not self.state['lawful_state'] else 'SUBMIT'
                if s['purpose']=='ORIGINAL_GOAL':
                    A(p['authorization'] is None,'GOAL_NULL_AUTH')
                    if self.state['deadline_time_ns']>self.h['original_deadline_ns'] or self.full:reason='GUARD_REJECTED'
                else:
                    if s['purpose']=='SAFE_LOCAL_RECOVERY':A(self.known and (self.state['deadline_time_ns']<=self.h['original_deadline_ns'] or self.full),'RECOVERY_KNOWN_FULL_FALSE')
                    A(p['authorization']=={'state_id':self.state['state_id'],'purpose':s['purpose'],'target_sha256':D(target),'source_sha256':self.h['authorization_source_sha256']},'PER_TARGET_CURRENT_AUTH')
                if reason=='SUBMIT' and len(self.commands)>=self.h['caps']['commands']:reason='CAPACITY_REFUSED'
            A(p['disposition']==reason,'SLOT_DISPOSITION_ORACLE');t['slots'][i]=copy.deepcopy(p)
            cid=tid+':'+str(i) if reason=='SUBMIT' else None;A(p['command_id']==cid,'COMMAND_NAMESPACE')
            if cid is not None:
                A(cid not in self.commands,'COMMAND_REUSE');self.commands[cid]={'command_id':cid,'ticket_id':tid,'slot_index':i,'desired_tick':desired,'ready_tick':earliest,'owner':copy.deepcopy(s['actor']),'target_9d':copy.deepcopy(target),'target_sha256':D(target),'purpose':s['purpose'],'submit_state_id':self.state['state_id'],'status':'SUBMITTED'};self.queue.append(cid)
        elif k=='CHANNEL_RESULT':
            self.current(b['current_state_id']);cid=b['command_id'];A(cid in self.commands and self.queue and self.queue[0]==cid,'CHANNEL_PENDING_FIFO')
            cmd=self.commands[cid];A(b['claimed_owner']==cmd['owner'] and b['actual_target_9d']==cmd['target_9d'],'CHANNEL_ORIGINAL_OWNER_TARGET');A(b['status'] in ('APPLIED','REJECTED','DROPPED'),'CHANNEL_STATUS')
            if b['status']=='APPLIED':
                tick=self.state['tick'];A(tick==cmd['desired_tick'] and tick>=cmd['ready_tick'] and tick not in self.applied,'NORMAL_APPLIED_SCHEDULE');self.applied.add(tick)
            cmd['status']=b['status'];cmd['result_state_id']=self.state['state_id'];self.queue.pop(0)
        elif k=='ACTOR_TRANSITION':
            self.current(b['current_state_id']);A(b['actor_id'] in [a['actor_id'] for a in self.h['actors']],'ACTOR_ID');self.actor=b['actor_id'];self.gen+=1
        elif k=='FULL_TASK_FAILURE':
            self.current(b['current_state_id']);A(type(b['known_original_failure']) is bool and type(b['original_full_failure']) is bool,'FAILURE_TYPE');A(not self.known or b['known_original_failure'],'KNOWN_FAILURE_ABSORBING');A(not self.full or b['original_full_failure'],'FULL_FAILURE_ABSORBING');A(not b['original_full_failure'] or b['known_original_failure'],'FULL_REQUIRES_KNOWN');self.full=b['original_full_failure'];self.known=b['known_original_failure']
        elif k=='CAPACITY_REFUSAL':self.refusals+=1;A(self.refusals<=self.h['caps']['refusal_reserve'],'REFUSAL_RESERVE')
        elif k=='CASE_END':
            A(b['censored']=={'unreturned_tickets':[k for k,t in self.tickets.items() if t['return'] is None],'unresolved_slots':{k:[i for i in range(8) if i not in t['slots']] for k,t in self.tickets.items() if len(t['slots'])<8},'pending_commands':self.queue,'unresolved_outcomes':'UNKNOWN_NO_AUTOMATIC_RESEND'},'CLOSURE_CENSORING');self.closed=True
        self.seq+=1;self.chain=e['sha256'];self.clock=high;self.counts[k]+=1
        caps=self.h['caps'];A(self.seq<=caps['events'] and self.counts[k]<=caps['kinds'][k],'EVENT_KIND_CAP');A(len(self.tickets)<=caps['tickets'] and sum(t['return'] is None for t in self.tickets.values())<=caps['inflight'],'TICKET_CAP');A(len(self.commands)<=caps['commands'] and len(self.packets)<=caps['packet_archive'] and self.asset_bytes<=caps['asset_bytes'],'ARCHIVE_ASSET_COMMAND_CAP')
    def summary(self):return {'events':self.seq,'chain':self.chain,'packets':len(self.packets),'tickets':len(self.tickets),'slots':sum(len(t['slots']) for t in self.tickets.values()),'commands':self.commands,'queue':self.queue,'actor_id':self.actor,'actor_generation':self.gen,'known_original_failure':self.known,'original_full_failure':self.full,'closed':self.closed,'kind_counts':dict(self.counts)}
def audit(path,expected):
    path=pathlib.Path(path);A(path.stat().st_size<=expected['caps']['journal_bytes'],'FILE_BYTES_CAP');r=Audit(expected)
    with path.open('rb') as f:
        while True:
            raw=f.readline(expected['caps']['max_line_bytes']+1)
            if not raw:break
            A(len(raw)<=expected['caps']['max_line_bytes'] and raw.endswith(b'\n'),'LINE_BYTES_OR_TRUNCATION');A(r.seq<expected['caps']['events'],'EVENT_COUNT_CAP_BEFORE_PARSE');event=json.loads(raw);A(C(event)+b'\n'==raw,'CANONICAL_EVENT');r.accept(event)
    A(r.seq>0,'EMPTY');return r.summary()
def main():
    p=argparse.ArgumentParser();p.add_argument('--journal',required=True);p.add_argument('--expected-header',required=True);p.add_argument('--out',required=True);a=p.parse_args();expected=json.loads(pathlib.Path(a.expected_header).read_text());s=audit(a.journal,expected);pathlib.Path(a.out).write_text(json.dumps({'schema':'PaperBIndependentAsyncJournalAudit/1','status':'PASS_SCOPED_CPU_JOURNAL','journal_sha256':H(pathlib.Path(a.journal).read_bytes()),'expected_header_sha256':D(expected),'reader_sha256':H(pathlib.Path(__file__).read_bytes()),'summary':s,'scope':'No author reducer import; no physical authenticity/native/model/SFR proof'},indent=2)+'\n');print(json.dumps({k:s[k] for k in ['events','packets','tickets','slots','queue','closed']}))
if __name__=='__main__':main()
