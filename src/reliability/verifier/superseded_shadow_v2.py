"""Version-2 shadow runner; reuses the immutable v1 kernel-isolation boundary."""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from reliability.verifier.superseded_shadow import BOOTSTRAP

DEFAULT_MANIFEST=Path(__file__).resolve().parents[3]/'reports/v2_stabilization/classifier_v2/frozen_rule.json'


def run_shadow(packets, *, manifest=DEFAULT_MANIFEST, probes=()):
    """Never returns a decision or modifies V2. Failure of isolation abstains."""
    unavailable=lambda reason: {'predictions':[{'prediction':'UNCERTAIN','shadow_mode':True,
        'suggest_suppress_v2_negative':False,'reason':reason,'evidence':[]} for _ in packets],
        'isolation':{'verified':False,'reason':reason}}
    allowed={'issue','candidate_patch','test_source','base_output','patched_output'}
    if any(set(packet)!=allowed for packet in packets):
        return unavailable('Packet rejected before process launch: non-allowlisted input')
    try:
        frozen=json.loads(Path(manifest).read_text())
        canonical=json.dumps({'config':frozen['config'],
            'implementation_sha256':frozen['implementation_sha256']},
            sort_keys=True,separators=(',',':')).encode()
        if hashlib.sha256(canonical).hexdigest()!=frozen['frozen_rule_sha256']:
            return unavailable('Frozen configuration hash mismatch')
        source=Path(__file__).with_name('superseded_rule_v2.py').read_text()
        for name,digest in frozen['implementation_sha256'].items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:
                return unavailable('Frozen implementation hash mismatch')
        envelope={'source':source,'config':frozen['config'],'packets':packets,'probes':list(probes)}
        env={k:v for k,v in os.environ.items() if k not in
             ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONNOUSERSITE')}
        proc=subprocess.run([sys.executable,'-I','-S','-B','-c',BOOTSTRAP],
            input=json.dumps(envelope).encode(),capture_output=True,timeout=15,env=env,
            close_fds=True,cwd='/',check=False)
        if proc.returncode:
            return unavailable('Isolation/classifier unavailable: '+proc.stderr.decode(errors='replace')[-300:])
        result=json.loads(proc.stdout)
        result['frozen_rule_sha256']=frozen['frozen_rule_sha256']
        return result
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return unavailable('Shadow unavailable: '+str(exc))


def observation(run, tid):
    """Keep full context; add candidate scope only with a completed batch receipt."""
    raw=base64.b64decode(run.runner_log_b64)
    ends=[e for e in run.events if e.get('event')=='end' and not e.get('split')]
    result={'stdout':raw.decode('utf-8','replace'),
            'stderr':base64.b64decode(run.raw_stderr_b64).decode('utf-8','replace'),
            'returncode':None if run.infrastructure_errors else
                1 if any(e.get('returncode')==1 for e in ends) else 0,
            'timed_out':run.timed_out}
    starts={e['batch']:e for e in run.events if e.get('event')=='start'}
    matches=[]
    for end in ends:
        start=starts.get(end.get('batch'),{})
        requested=start.get('ids',[])
        if tid not in requested and tid.split('[',1)[0] not in requested:continue
        lo,hi=start.get('offset'),end.get('offset')
        if not isinstance(lo,int) or not isinstance(hi,int) or not 0<=lo<=hi<=len(raw):continue
        matches.append({'stdout':raw[lo:hi].decode('utf-8','replace'),'stderr':'',
                        'returncode':end.get('returncode'),'timed_out':False,
                        'requested_ids':requested})
    if len(matches)==1:result['target_output']=matches[0]
    return result


def shadow_from_report(report, issue, candidate_patch, tree, executor=None,
                       *, manifest=DEFAULT_MANIFEST, timeout_s=300):
    """Two observations per side for FAIL candidates only, never a policy change.

    The legacy patched confirmation is reused. One isolated base confirmation
    is added; if no patched confirmation exists, add exactly one. No retry loop
    repairs disagreements or missing evidence. Retain all observations.
    """
    costs={'additional_base_runs':0,'additional_patched_runs':0,
           'reused_patched_runs':0,'additional_wall_s':0.0,'additional_runner_s':0.0}
    abstain=lambda reason:{'prediction':'UNCERTAIN','shadow_mode':True,
        'suggest_suppress_v2_negative':False,'reason':reason,'costs':costs}
    if report.signal.value!='FAIL':return abstain('No V2 FAIL; no stability executions')
    if executor is None:return abstain('No executor for second base observation')
    try:
        frozen=json.loads(Path(manifest).read_text())
        canonical=json.dumps({'config':frozen['config'],
            'implementation_sha256':frozen['implementation_sha256']},sort_keys=True,separators=(',',':')).encode()
        if hashlib.sha256(canonical).hexdigest()!=frozen['frozen_rule_sha256']:
            return abstain('Frozen configuration hash mismatch')
        for name,digest in frozen['implementation_sha256'].items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:
                return abstain('Frozen implementation hash mismatch')
    except (OSError,ValueError) as exc:return abstain('Frozen v2 unavailable: '+str(exc))
    paths=sorted({tid.split('::',1)[0] for tid in report.regressions})
    if any('+++ b/'+path in candidate_patch for path in paths):
        return abstain('Candidate changes failing test source')
    source='\n'.join(tree.read_text(path) for path in paths)
    packets=[];ids=[];extra=[]
    started=time.monotonic()
    def repeat(tid,patched):
        result=executor.run((tid,),patched=patched,timeout_s=timeout_s)
        costs['additional_patched_runs' if patched else 'additional_base_runs']+=1
        costs['additional_runner_s']+=sum(e.get('duration_s',0.0) for e in result.events if e.get('event')=='end')
        from reliability.verifier.regression import run_to_dict
        extra.append({'tree':'patched' if patched else 'base',
                      'test_id':tid,'run':run_to_dict(result,inline_raw=False)})
        return result
    error=None
    try:
        for tid in report.regressions:
            base=[observation(report.baseline,tid)] if report.baseline else []
            patched=[observation(report.patched,tid)] if report.patched else []
            base.append(observation(repeat(tid,False),tid))
            confirmations=[r for r in report.confirmations
                           if tid in r.by_id() or tid in r.requested_tests]
            if confirmations:
                costs['reused_patched_runs']+=len(confirmations)
                patched.extend(observation(r,tid) for r in confirmations)
            else:patched.append(observation(repeat(tid,True),tid))
            packets.append({'issue':issue or '', 'candidate_patch':candidate_patch,
                'test_source':source,'base_output':base,'patched_output':patched})
            ids.append(tid)
    except Exception as exc:  # noqa: BLE001 - shadow cannot alter V2's decision
        error=f'{type(exc).__name__}: {exc}'
    finally:
        # The verifier continues with the patched tree, just as before shadow work.
        if hasattr(executor,'container'):
            try:executor.container.set_patched(True)
            except Exception as exc:  # noqa: BLE001
                error=f'Could not restore patched tree: {exc}'
        costs['additional_wall_s']=time.monotonic()-started
    if error:
        result=abstain('Stability evidence unavailable: '+error)
    else:
        result=run_shadow(packets,manifest=manifest)
        for tid,prediction in zip(ids,result['predictions'],strict=True):prediction['test_id']=tid
        result['costs']=costs
    result['additional_evidence']=extra
    return result

