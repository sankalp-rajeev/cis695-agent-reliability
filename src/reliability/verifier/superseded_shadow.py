"""Fail-closed, filesystem-denied subprocess boundary for the frozen prototype."""
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_MANIFEST=Path(__file__).resolve().parents[3]/'reports/v2_stabilization/frozen_rule.json'

# All imports/implementation load BEFORE Landlock. No path is allowed afterward.
# close_fds isolates parent handles; only JSON stdin/stdout/stderr cross the boundary.
BOOTSTRAP=r'''
import ast, ctypes, hashlib, json, os, platform, re, sys
envelope=json.load(sys.stdin)
namespace={'__name__':'frozen_rule'}
exec(compile(envelope['source'],'<frozen-rule>','exec'),namespace)
libc=ctypes.CDLL(None,use_errno=True)
abi=libc.syscall(444,None,0,1) if platform.machine()=='x86_64' else -1
class Ruleset(ctypes.Structure):
    _fields_=[('handled_access_fs',ctypes.c_uint64),('handled_access_net',ctypes.c_uint64)]
if abi<4:
    raise RuntimeError('Landlock ABI >=4 on x86_64 required; classifier not executed')
attributes=Ruleset((1<<15)-1,3)
fd=libc.syscall(444,ctypes.byref(attributes),ctypes.sizeof(attributes),0)
if fd<0 or libc.prctl(38,1,0,0,0)!=0 or libc.syscall(446,fd,0)!=0:
    raise RuntimeError('Filesystem isolation failed; classifier not executed')
os.close(fd)
probes={}
for path in envelope.get('probes',[]):
    try:
        with open(path,'rb') as f:f.read(1)
        probes[path]='ACCESSIBLE'
    except PermissionError:probes[path]='DENIED'
    except OSError as exc:probes[path]='ERROR:'+str(exc.errno)
if any(value!='DENIED' for value in probes.values()):
    raise RuntimeError('Restriction verification failed; classifier not executed')
predictions=[namespace['classify'](packet,envelope['config']) for packet in envelope['packets']]
print(json.dumps({'predictions':predictions,'isolation':{'landlock_abi':abi,
    'all_filesystem_reads_denied':True,'tcp_bind_connect_denied':True,
    'probe_results':probes,'input_keys':[sorted(p) for p in envelope['packets']]}}))
'''


def run_shadow(packets, *, manifest=DEFAULT_MANIFEST, probes=()):
    """Never returns a decision or modifies V2. Failure of isolation abstains."""
    unavailable=lambda reason: {'predictions':[{'prediction':'UNCERTAIN','shadow_mode':True,
        'suggest_suppress_v2_negative':False,'reason':reason,'evidence':[]} for _ in packets],
        'isolation':{'verified':False,'reason':reason}}
    try:
        frozen=json.loads(Path(manifest).read_text())
        canonical=json.dumps({'config':frozen['config'],
            'implementation_sha256':frozen['implementation_sha256']},
            sort_keys=True,separators=(',',':')).encode()
        if hashlib.sha256(canonical).hexdigest()!=frozen['frozen_rule_sha256']:
            return unavailable('Frozen configuration hash mismatch')
        source=Path(__file__).with_name('superseded_rule.py').read_text()
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


def shadow_from_report(report, issue, candidate_patch, tree):
    """Log a suggestion only. Never mutates the report, outcomes or policy input.

    Existing V2 has only one base pass: without additional stable observations
    the frozen rule will abstain. This hook does not add executions or budgets.
    """
    if report.signal.value!='FAIL':
        return {'prediction':'UNCERTAIN','shadow_mode':True,
                'suggest_suppress_v2_negative':False,'reason':'No V2 FAIL to classify'}
    paths=sorted({tid.split('::',1)[0] for tid in report.regressions})
    if any('+++ b/'+path in candidate_patch for path in paths):
        return {'prediction':'UNCERTAIN','shadow_mode':True,
                'suggest_suppress_v2_negative':False,'reason':'Candidate changes failing test source'}
    def output(run):
        if run is None:return []
        ends=[e for e in run.events if e.get('event')=='end' and not e.get('split')]
        rc=1 if any(e.get('returncode')==1 for e in ends) else 0
        if run.infrastructure_errors or not run.evidence_complete:rc=None
        return [{'stdout':base64.b64decode(run.runner_log_b64).decode('utf-8','replace'),
                 'stderr':base64.b64decode(run.raw_stderr_b64).decode('utf-8','replace'),
                 'returncode':rc,'timed_out':run.timed_out}]
    packet={'issue':issue or '', 'candidate_patch':candidate_patch,
            'test_source':'\n'.join(tree.read_text(path) for path in paths),
            'base_output':output(report.baseline),'patched_output':output(report.patched)}
    for confirmation in report.confirmations:
        packet['patched_output'].extend(output(confirmation))
    return run_shadow([packet])
