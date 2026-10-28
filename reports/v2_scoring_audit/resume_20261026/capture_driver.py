
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
