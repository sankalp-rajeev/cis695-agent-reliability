"""Scan staged blobs without opening excluded labels or printing secret values."""
import re
import subprocess

patterns = [r'sk-ant-[A-Za-z0-9_-]{16,}', r'sk-proj-[A-Za-z0-9_-]{16,}',
            r'sk-[A-Za-z0-9]{32,}', r'ghp_[A-Za-z0-9]{20,}',
            r'hf_[A-Za-z0-9]{20,}', r'AKIA[0-9A-Z]{16}']
paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z']).decode().split('\0')
for path in filter(None, paths):
    assert path != '.env' and 'oracle_record.json' not in path
    assert not any(x in path for x in ('phase4_posthoc/', 'grader_gap/', 'docs/results_100.'))
    blob = subprocess.check_output(['git', 'show', ':' + path])
    if re.search('|'.join(patterns).encode(), blob, re.I):
        raise SystemExit('FAIL: credential-shaped value in staged file ' + path)
print('PASS: staged secret scan')
