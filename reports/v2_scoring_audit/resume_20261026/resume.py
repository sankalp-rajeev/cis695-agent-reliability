"""Execute the existing frozen protocol; never mutate production or prior outputs.

No oracle data is read here. All runner logs are persisted before any parser runs.
"""
from __future__ import annotations

import ast
import concurrent.futures
import hashlib
import json
import os
import re
import shlex
import subprocess
import tarfile
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
AUDIT = OUT.parent
ROOT = AUDIT.parents[1]
PROTOCOL = json.loads((AUDIT / 'protocol.json').read_text())
INPUTS = json.loads((AUDIT / 'frozen_inputs/selections.json').read_text())
LOCK = threading.Lock()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n')


def command(argv, folder, key, timeout=20, data=None):
    folder.mkdir(parents=True, exist_ok=True)
    meta = dict(argv=argv, timeout_s=timeout,
                utc=datetime.now(timezone.utc).isoformat(),
                stdin_sha256=sha(data) if data is not None else None)
    with LOCK:
        with (OUT / 'commands.jsonl').open('a') as f:
            f.write(json.dumps(meta) + '\n')
            f.flush()
            os.fsync(f.fileno())
        print('EXACT COMMAND BEFORE EXECUTION:', shlex.join(argv), flush=True)
    env = dict(os.environ)
    for var in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONNOUSERSITE'):
        env.pop(var, None)
    start = time.monotonic()
    try:
        p = subprocess.run(argv, input=data, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=timeout, env=env)
        stdout, stderr, rc, state = p.stdout, p.stderr, p.returncode, 'completed'
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, rc, state = exc.stdout or b'', exc.stderr or b'', None, 'timeout'
    except OSError as exc:
        stdout, stderr, rc, state = b'', str(exc).encode(), None, 'launch_error'
    # Raw bytes are written and fsynced before the command result is returned.
    for suffix, raw in (('stdout', stdout), ('stderr', stderr)):
        with (folder / (key + '.' + suffix)).open('xb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
    meta.update(returncode=rc, state=state, duration_s=time.monotonic()-start,
                stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
    save(folder / (key + '.json'), meta)
    return meta, stdout, stderr


# Same runner argv, order, 25-ID batching and exit-4 split budget as production.
# Instrumentation saves raw bytes and batch events; it never parses test results.
# Streaming additionally preserves partial output when the outer pass times out.
DRIVER = r'''
import json, os, pathlib, subprocess, sys, time
try:
    os.setsid()
except OSError:
    pass
pathlib.Path('/tmp/audit_pgid').write_text(str(os.getpgrp()))
kind = sys.argv[1]
ids = [s.strip() for s in pathlib.Path('/tmp/verifier_ids').read_text(encoding='utf-8', errors='replace').splitlines() if s.strip()]
log = open('/tmp/verifier_out.txt', 'wb', buffering=0)
events = open('/tmp/audit_events.jsonl', 'w', buffering=1)
budget = [200]
sequence = [0]
def run(part):
    cmd = (['python', 'tests/runtests.py', '--verbosity=2'] + part if kind == 'django'
           else ['python', '-m', 'pytest'] + part + ['-p', 'no:cacheprovider', '-v'])
    sequence[0] += 1
    index = sequence[0]
    raw_path = '/tmp/audit_batch_%04d.raw' % index
    start = time.monotonic()
    events.write(json.dumps(dict(event='start', batch=index, argv=cmd, ids=part, raw_path=raw_path, time=start)) + '\n')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open(raw_path, 'wb', buffering=0) as raw:
        while True:
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            raw.write(chunk)
            log.write(chunk)
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
    code = proc.wait()
    events.write(json.dumps(dict(event='end', batch=index, returncode=code, duration_s=time.monotonic()-start)) + '\n')
    return code
def execute(part):
    code = run(part)
    if kind == 'pytest' and code == 4 and len(part)>1 and budget[0]>0:
        budget[0] -= 1
        mid = len(part)//2
        execute(part[:mid])
        execute(part[mid:])
for start in range(0, len(ids), 25):
    execute(ids[start:start+25])
'''


def dexec(name, script, folder, key, timeout=20, data=None):
    argv = ['docker', 'exec']
    if data is not None:
        argv.append('-i')
    argv += ['-w', '/testbed', name, 'bash', '-lc', script]
    return command(argv, folder, key, timeout, data)


def verify_frozen():
    manifest = json.loads((AUDIT/'frozen_inputs/manifest.json').read_text())
    assert sha((AUDIT/'protocol.json').read_bytes()) == manifest['protocol_sha256']
    for path, digest in manifest['files_sha256'].items():
        assert sha((AUDIT/path).read_bytes()) == digest, path
    for path, digest in PROTOCOL['source_hashes'].items():
        assert sha((ROOT/path).read_bytes()) == digest, path
    for path, digest in json.loads((OUT/'preserved_inputs.sha256.json').read_text()).items():
        assert sha((ROOT/path).read_bytes()) == digest, path


def full_pass(name, iid, tree, tests, folder, runner, key='initial'):
    run_folder = folder / tree / key
    native = tests
    if runner == 'django':
        native = [django_label(t) for t in tests]
    m, _, _ = dexec(name, 'cat > /tmp/verifier_ids', run_folder, 'ids',
                    data=('\n'.join(native)+'\n').encode())
    assert m['returncode'] == 0, m
    # Avoid old raw files being mistaken for results from a new attempt.
    m, _, _ = dexec(name, 'rm -f /tmp/audit_events.jsonl /tmp/audit_batch_*.raw /tmp/verifier_out.txt /tmp/audit_pgid',
                    run_folder, 'clear_previous_raw')
    assert m['returncode'] == 0, m
    meta, stdout, stderr = dexec(name, 'python /tmp/verifier_driver.py '+runner,
                               run_folder, 'driver',
                               PROTOCOL['full_pass_timeout_s'] if key=='initial'
                               else PROTOCOL['individual_rerun_timeout_s'])
    if meta['state']=='timeout':
        # docker-exec client termination alone does not stop container children.
        kill = "python - <<'PY'\nimport os,signal\np=int(open('/tmp/audit_pgid').read())\nos.killpg(p,signal.SIGKILL)\nPY"
        dexec(name, kill, run_folder, 'kill_timed_out_group')
    # Raw driver log and raw batch events are fetched before any parser is called.
    for remote, local in (('/tmp/verifier_out.txt','runner.raw'),
                          ('/tmp/audit_events.jsonl','batch_events.jsonl')):
        m, raw, _ = dexec(name, 'cat '+remote, run_folder, 'capture_'+local.replace('.','_'))
        if m['returncode']==0:
            (run_folder/local).write_bytes(raw)
    raw_path = run_folder/'runner.raw'
    if not raw_path.exists():
        raw_path.write_bytes(stdout)
    # Preserve each batch separately: duplicate summary lines must not be new tests.
    events_path = run_folder/'batch_events.jsonl'
    events = [json.loads(s) for s in events_path.read_text().splitlines()] if events_path.exists() else []
    for event in events:
        if event['event']=='start':
            m, raw, _ = dexec(name, 'cat '+event['raw_path'], run_folder,
                             'capture_batch_%04d'%event['batch'])
            if m['returncode']==0:
                (run_folder/('batch_%04d.raw'%event['batch'])).write_bytes(raw)
    save(run_folder/'attempt.json',dict(instance_id=iid,tree=tree,requested_tests=tests,
         runner=runner,timeout_s=meta['timeout_s'],driver_state=meta['state'],
         driver_returncode=meta['returncode'],duration_s=meta['duration_s'],
         raw_sha256=sha(raw_path.read_bytes()),raw_captured_before_parsing=True))
    return run_folder


def phase2(iid):
    r = INPUTS[iid]
    folder = OUT/'phase2'/iid
    image_meta = json.loads((OUT/'preflight'/f'{iid}.image.json').read_text())
    if image_meta['returncode']!=0:
        save(folder/'blocked.json',dict(instance_id=iid,reason='frozen local image missing; no pull/build/substitution',phase2_executed=False))
        return None
    image = json.loads((OUT/'preflight'/f'{iid}.image.stdout').read_text())
    name = 'v2audit_20261026_'+iid.replace('__','_').replace('-','_')
    launch = ['docker','run','-d','--pull=never','--name',name,
              '--label','experiment_id=v2_scoring_audit_resume_20261026',
              '-w','/testbed','--network','none',image['Id'],'sleep','infinity']
    meta, _, _ = command(launch,folder,'launch')
    if meta['returncode']!=0:
        save(folder/'blocked.json',dict(instance_id=iid,reason='container launch failed',phase2_executed=False))
        return None
    try:
        # Versions and current commit are observed, never inferred from a tag.
        script = "git rev-parse HEAD; git status --porcelain; python --version; python -m pytest --version"
        dexec(name,script,folder,'environment')
        patch = (AUDIT/'frozen_inputs'/f'{iid}.patch').read_bytes()
        assert sha(patch)==r['patch_sha256']
        m,_,_=dexec(name,'git apply --check -',folder,'patch_check',data=patch)
        if m['returncode']!=0:
            save(folder/'blocked.json',dict(instance_id=iid,reason='frozen candidate does not apply',phase2_executed=False))
            return None
        m,_,_=dexec(name,'cat > /tmp/verifier_driver.py',folder,'install_capture_driver',data=DRIVER.encode())
        assert m['returncode']==0,m
        full_pass(name,iid,'base',r['selected_tests'],folder,r['runner'])
        m,_,_=dexec(name,'git apply -',folder,'apply_frozen_candidate',data=patch)
        assert m['returncode']==0,m
        dexec(name,'git diff --binary; git rev-parse HEAD',folder,'patched_tree_identity')
        full_pass(name,iid,'patched',r['selected_tests'],folder,r['runner'])
        return iid
    finally:
        command(['docker','rm','-f',name],folder,'cleanup')


def parser_namespace(fixed=False):
    """Compile only parser definitions, enums and classifier, no app imports."""
    source = (ROOT/'src/reliability/verifier/container.py').read_text()
    if fixed:
        old = '''        if match is None or match.group("id") not in wanted:
            continue
        test, status = match.group("id"), _PYTEST_OUTCOME[match.group("outcome")]
'''
        new = '''        if match is None:
            continue
        test = match.group("id")
        if test not in wanted and "[" in test:
            family = test.split("[", 1)[0]
            if family in wanted:
                test = family
        if test not in wanted:
            continue
        status = _PYTEST_OUTCOME[match.group("outcome")]
'''
        assert source.count(old)==1
        # Exact carried-forward proposal: no outcome-directed parser changes.
        proposed = (AUDIT/'parser_fix.diff').read_text()
        assert '+            family = test.split("[", 1)[0]' in proposed
        source = source.replace(old,new)
    body = [ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),
            ast.ImportFrom(module='enum',names=[ast.alias(name='Enum')],level=0)]
    reg = ast.parse((ROOT/'src/reliability/verifier/regression.py').read_text())
    body += [n for n in reg.body if isinstance(n,ast.ClassDef) and n.name in {'TestStatus','Outcome','Signal'}
             or isinstance(n,ast.FunctionDef) and n.name=='classify']
    sel = ast.parse((ROOT/'src/reliability/verifier/selection.py').read_text())
    body += [n for n in sel.body if isinstance(n,ast.FunctionDef) and n.name=='django_label']
    for n in ast.parse(source).body:
        if isinstance(n,ast.FunctionDef) and n.name in {'_parse_output','_parse_pytest','_parse_django'}:
            body.append(n)
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            names = n.targets if isinstance(n,ast.Assign) else [n.target]
            if any(isinstance(t,ast.Name) and t.id.startswith(('_PYTEST_','_DJANGO_')) for t in names):body.append(n)
    ns={'re':re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),
                 '<frozen-parser-fixed>' if fixed else '<production-parser>', 'exec'),ns)
    return ns


OLD = parser_namespace()
django_label = OLD['django_label']


def raw_cases(folder):
    """Use concrete emitted IDs for confirmation selection, independent of oracle."""
    by_id = {}
    severity = OLD['_PYTEST_SEVERITY']
    for line in (folder/'runner.raw').read_text(errors='replace').splitlines():
        match = OLD['_PYTEST_LINE'].match(line.strip())
        if match:
            tid = match.group('id')
            status = OLD['_PYTEST_OUTCOME'][match.group('outcome')]
            if tid not in by_id or severity[status]>=severity[by_id[tid]]:by_id[tid]=status
    return by_id


def phase3(iid):
    r=INPUTS[iid]
    initial=OUT/'phase2'/iid
    base=raw_cases(initial/'base/initial')
    patch=raw_cases(initial/'patched/initial')
    wanted=set(r['selected_tests'])
    def selected(t):return t in wanted or t.split('[',1)[0] in wanted
    candidates=sorted(t for t in base.keys()|patch.keys() if selected(t) and
        ((t in base and base[t].value=='failed') or (t in base and t in patch and base[t]!=patch[t])))
    # A missing counterpart is recorded as missing, not a fabricated difference.
    missing=sorted(t for t in base.keys()^patch.keys() if selected(t))
    folder=OUT/'phase3'/iid
    save(folder/'candidates.json',dict(instance_id=iid,candidates=candidates,
        missing_counterpart_ids=missing,rule=PROTOCOL['phase3_candidates']))
    if not candidates:
        return dict(instance_id=iid,candidates=0)
    image=json.loads((OUT/'preflight'/f'{iid}.image.stdout').read_text())
    name='v2audit_repeat_20261026_'+iid.replace('__','_').replace('-','_')
    m,_,_=command(['docker','run','-d','--pull=never','--name',name,
                   '--label','experiment_id=v2_scoring_audit_resume_20261026',
                   '-w','/testbed','--network','none',image['Id'],'sleep','infinity'],folder,'launch')
    assert m['returncode']==0,m
    try:
        m,_,_=dexec(name,'cat > /tmp/verifier_driver.py',folder,'install_capture_driver',data=DRIVER.encode())
        assert m['returncode']==0,m
        patch_bytes=(AUDIT/'frozen_inputs'/f'{iid}.patch').read_bytes()
        # Three separate isolated invocations for EACH concrete candidate per side.
        for tree in ('base','patched'):
            if tree=='patched':
                m,_,_=dexec(name,'git apply -',folder,'apply_frozen_candidate',data=patch_bytes)
                assert m['returncode']==0,m
            for index,tid in enumerate(candidates):
                for repeat in range(1,PROTOCOL['phase3_reruns_per_tree']+1):
                    full_pass(name,iid,tree,[tid],folder,r['runner'],
                              key='candidate_%04d_repeat_%d'%(index,repeat))
        return dict(instance_id=iid,candidates=len(candidates),planned_attempts=len(candidates)*6)
    finally:
        command(['docker','rm','-f',name],folder,'cleanup')


def main():
    verify_frozen()
    save(OUT/'execution_rules.json',dict(protocol_sha256=sha((AUDIT/'protocol.json').read_bytes()),
        proposed_fix_sha256=sha((AUDIT/'parser_fix.diff').read_bytes()),
        usable_definition=PROTOCOL['usable_v2_exact_user_definition'],
        usable_treatment='Only observed terminal PASS/FAIL/ERROR/SKIP are recorded per-test outcomes. Missing IDs, inferred NOT_RUN and process-level timeout do not supply raw outcomes. At least one concrete PASS/FAIL/SKIP is required on each tree. A family is covered only if its responsible batch completed with rc 0/1 and emitted a concrete result.',
        instrumentation='Original runner commands, selection order, batch size 25, split-on-exit4 budget 200; streaming byte capture and batch events added. No plugins installed or dependencies changed.',
        historical_image_digest='UNKNOWN: not stored in frozen metadata',
        oracle_gate='CLOSED until all authorized possible raw collection and repeats finish'))
    (OUT/'capture_driver.py').write_text(DRIVER)
    # Independent repositories can execute concurrently; no agent/model invocation.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        completed=list(pool.map(phase2,INPUTS))
    completed=[iid for iid in completed if iid]
    save(OUT/'phase2_complete.json',dict(completed_ids=completed,
        blocked_ids=sorted(set(INPUTS)-set(completed)),raw_collected_before_parsing=True))
    for iid in completed:
        print('PHASE 3:',phase3(iid),flush=True)
    save(OUT/'collection_complete.json',dict(completed_ids=completed,
         oracle_inputs_read=False,utc=datetime.now(timezone.utc).isoformat()))
    verify_frozen()
    print('COLLECTION COMPLETE; offline parser comparison and metrics remain.',flush=True)


if __name__=='__main__':
    main()
