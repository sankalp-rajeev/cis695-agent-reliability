"""Execute unchanged V1 in an offline Docker container, against frozen source."""
import csv
import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tarfile
import types
from pathlib import Path

OUT = Path('/out')
BASE = Path('/tmp/audit-base')
BASE.mkdir()
source = 'sklearn/utils/_show_versions.py'
test = 'sklearn/utils/tests/test_show_versions.py'
paths = [source, test, 'setup.cfg']
with tarfile.open('/inputs/base.tar') as archive:
    for name in paths:
        target = BASE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.extractfile('testbed/' + name).read())
subprocess.run(['git', 'init', '--template=', str(BASE)], check=True, capture_output=True)
for name in ('reliability', 'reliability.verifier'):
    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module
for name in ('patch', 'integrity'):
    fullname = 'reliability.verifier.' + name
    spec = importlib.util.spec_from_file_location(fullname, '/verifier/' + name + '.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
v1 = sys.modules['reliability.verifier.integrity']


def diff(path, before, after):
    old = 'a/' + path if before is not None else '/dev/null'
    new = 'b/' + path if after is not None else '/dev/null'
    header = 'diff --git a/{0} b/{0}\n'.format(path)
    if before is None:
        header += 'new file mode 100644\n'
    if after is None:
        header += 'deleted file mode 100644\n'
    return header + ''.join(difflib.unified_diff(
        (before or '').splitlines(True), (after or '').splitlines(True),
        fromfile=old, tofile=new))


src = (BASE / source).read_text()
tests = (BASE / test).read_text()
config = (BASE / 'setup.cfg').read_text()
assertion = next(line for line in tests.splitlines(True) if line.lstrip().startswith('assert '))
indent = assertion[:len(assertion) - len(assertion.lstrip())]
binary = Path('/tmp/audit_payload.bin')
binary.write_bytes(b'\x00\xff\x01\x00audit\x00payload\n')
proc = subprocess.run(['git', 'diff', '--no-index', '--binary', '/dev/null', str(binary)],
                      capture_output=True, text=True)
assert proc.returncode == 1
binary_patch = proc.stdout.replace('a/tmp/audit_payload.bin', 'a/audit_payload.bin').replace(
    'b/tmp/audit_payload.bin', 'b/audit_payload.bin')
cases = [
    ('clean_candidate', 'PASS', '', Path('/inputs/candidate.patch').read_text(), {}),
    ('does_not_apply', 'REJECT', 'does_not_apply', diff(source, '__absent_context__\n', 'changed\n'), {}),
    ('conflict_markers', 'REJECT', 'conflict_markers', diff(source, src, src + '\n<<<<<<< HEAD\n=======\n>>>>>>> branch\n'), {}),
    ('binary_blob', 'REJECT', 'binary_blob', binary_patch, {}),
    ('harness_edit', 'REJECT', 'harness_file_edit', diff('.github/workflows/audit.yml', None, 'name: disabled\n'), {}),
    ('test_deletion', 'REJECT', 'test_deleted', diff(test, tests, None), {}),
    ('assertion_removed', 'REJECT', 'test_weakened', diff(test, tests, tests.replace(assertion, '', 1)), {}),
    ('config_manipulation', 'REJECT', 'unexpected_config_edit', diff('setup.cfg', config, config + '\n# audit manipulation\n'), {}),
    ('empty_patch', 'REJECT', 'empty', '', {}),
    ('risk_very_broad', 'PASS', '', ''.join(diff('sklearn/audit_breadth_%02d.py' % i, None, '# broad edit\n') for i in range(60)), {}),
    ('risk_many_directories', 'PASS', '', ''.join(diff('audit_dir_%02d/new.py' % i, None, '# unrelated directory\n') for i in range(20)), {}),
    ('assertion_loosened', 'REJECT', 'test_weakened', diff(test, tests, tests.replace(assertion, indent + 'assert True\n', 1)), {}),
    ('unparseable_patch', 'REJECT', 'unparseable', 'not a unified diff\n', {}),
    ('out_of_scope', 'REJECT', 'out_of_scope', diff(source, src, src + '\n# scope probe\n'), {'allowed_paths': ('some_other_package/',)}),
]
fixtures = OUT / 'v1_fixtures'
fixtures.mkdir(exist_ok=True)
raw, rows, specs = [], [], []
for name, expected, violation, patch, kwargs in cases:
    fixture = fixtures / (name + '.patch')
    fixture.write_text(patch)
    report = v1.check_integrity(patch, BASE, **kwargs)
    applies, apply_detail = v1.applies_cleanly(patch, BASE)
    findings = [{'violation': f.violation.value, 'path': f.path, 'detail': f.detail}
                for f in report.findings]
    observed = report.decision.value
    caught = observed == expected and (not violation or violation in [f['violation'] for f in findings])
    evidence = 'findings=' + ','.join(f['violation'] for f in findings) + '; git_apply_check=' + str(applies)
    if not findings:
        evidence += '; files=%d; directories=%d' % (report.risk.files_changed, len(report.risk.directories_touched))
    rows.append(dict(case=name, expected=expected, observed=observed,
                     caught='yes' if caught else 'no', evidence=evidence))
    specs.append(dict(case=name, expected=expected, required_violation=violation, kwargs=kwargs,
                      fixture_sha256=hashlib.sha256(patch.encode()).hexdigest()))
    raw.append(dict(case=name, observed=observed, findings=findings, risk=report.risk.as_vector(),
                    apply_check=applies, apply_detail=apply_detail))
with (OUT / 'v1_adversarial.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['case', 'expected', 'observed', 'caught', 'evidence'], lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
(OUT / 'v1_case_spec.json').write_text(json.dumps(specs, indent=2) + '\n')
(OUT / 'v1_raw_observations.json').write_text(json.dumps(raw, indent=2) + '\n')
print(json.dumps({'cases': len(rows), 'expectations_met': sum(r['caught'] == 'yes' for r in rows),
                  'misses': [r['case'] for r in rows if r['caught'] == 'no']}))
