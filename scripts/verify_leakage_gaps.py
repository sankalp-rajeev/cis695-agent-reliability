"""Independent stdlib-only recount and rule-3 verification; no reliability imports.

Never opens a dataset, gold patch, correctness label or grader result. Symbol
hashes are checked against tokens read directly from the verified base tar.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import tarfile
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def fail(message):
    raise ValueError(message)


def symbol_hashes(pin):
    path = Path(pin['path'])
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != pin['sha256']:
        fail('archive digest mismatch')
    symbols = set()
    with tarfile.open(path) as tar:
        for member in tar:
            if member.isfile() and member.name.startswith('testbed/'):
                if '..' in Path(member.name).parts:
                    fail('unsafe archive path')
                raw = tar.extractfile(member).read()
                symbols.update(hashlib.sha256(s).hexdigest() for s in
                               re.findall(rb'\btest[A-Za-z0-9_]+\b', raw))
    return symbols


def finding_key(f):
    return f['path'], f['kind'], f['line_no'], f['severity']


def verify(root):
    tasks = [read(p) for p in sorted((root/'tasks').glob('*/*/*.json'))]
    if not tasks:
        fail('empty trajectory results')
    findings = [f for task in tasks for f in task['findings']]
    summary = read(root/'trajectory_summary.json')
    expected = dict(task_directories=len(tasks), unique_tasks=len({r['instance_id'] for r in tasks}),
        repair_directories=sum(r['role']=='repair' for r in tasks),
        generator_directories=sum(r['role']=='generator' for r in tasks),
        scanned_files=sum(r['scanned_files'] for r in tasks), findings=len(findings),
        severity=dict(collections.Counter(f['severity'] for f in findings)),
        rules=dict(collections.Counter(f['rule'] for f in findings)),
        legacy_findings=sum(len(r['legacy_findings']) for r in tasks),
        downgrades=sum(len(r['golden']['downgrades']) for r in tasks),
        golden_violations=sum(len(r['golden']['violations']) for r in tasks),
        awareness_tasks=len({r['instance_id'] for r in tasks if any(f['severity']=='benchmark-awareness' for f in r['findings'])}),
        confirmed_tasks=sorted({r['instance_id'] for r in tasks if any(f['severity']=='confirmed' for f in r['findings'])}))
    if expected != summary:
        fail('trajectory totals mismatch')
    pins, checked = {}, 0
    for task in tasks:
        before = collections.Counter(finding_key(f) for f in task['legacy_findings'])
        after = collections.Counter(finding_key(f) for f in task['findings'])
        for downgrade in task['golden']['downgrades']:
            old, new = downgrade['before'], downgrade['after']
            if old['severity'] != 'confirmed' or new['severity'] != 'review':
                fail('invalid downgrade severity')
            if (old['path'],old['kind'],old['line_no']) != (new['path'],new['kind'],new['line_no']):
                fail('downgrade identity changed')
            rule = new['rule']
            pin = task['archive']
            if pin['sha256'] not in pins:
                pins[pin['sha256']] = symbol_hashes(pin)
            symbol_hash = new['evidence']['symbol_sha256']
            present = symbol_hash in pins[pin['sha256']]
            if rule == 'test-name-present-at-base':
                if not present or not new['evidence']['base_present']:
                    fail('base-present downgrade disproved')
            elif rule == 'test-name-agent-defined-before-output':
                if present or new['evidence']['base_present']:
                    fail('agent-definition downgrade unexpectedly at base')
                # Find a definition of this hashed symbol in a file-write call
                # before the first output containing the symbol. No gold names.
                trajectory = Path(new['path'])
                definitions, appearances = [], []
                for n, raw in enumerate(trajectory.read_text().splitlines(), 1):
                    for token in re.findall(r'\btest[A-Za-z0-9_]+\b', raw):
                        if hashlib.sha256(token.encode()).hexdigest() == symbol_hash:
                            appearances.append(n)
                            if '"role": "assistant"' in raw and re.search(r'(?:>|write_text|apply_patch)', raw) and 'def ' + token in raw:
                                definitions.append(n)
                if not definitions or min(definitions) > min(appearances):
                    fail('ordered-definition downgrade disproved')
            else:
                fail('unsupported downgrade rule')
            before[finding_key(old)] -= 1
            checked += 1
        if any(count > after[key] for key, count in before.items()):
            fail('legacy golden finding lost')
    if read(root/'downgrades.json') != [d for t in tasks for d in t['golden']['downgrades']]:
        fail('downgrade inventory mismatch')
    images = [read(p) for p in sorted((root/'images').glob('*.json'))]
    image_summary = read(root/'image_summary.json')
    if len(images) != image_summary['cohort']:
        fail('image cohort total mismatch')
    missing = sorted(r['instance_id'] for r in images if r.get('status') == 'missing')
    if missing != sorted(image_summary['missing']):
        fail('missing image inventory mismatch')
    report = (root/'REPORT.md').read_text()
    marker = re.search(r'<!-- totals-json: (.+?) -->', report)
    if not marker or json.loads(marker.group(1)) != dict(trajectory=expected, images=image_summary):
        fail('report totals mismatch')
    result = dict(status='pass', task_directories=len(tasks), findings=len(findings),
                  image_tasks=len(images), downgrades_rechecked=checked,
                  golden_violations=expected['golden_violations'])
    if expected['golden_violations'] or image_summary['incomplete']:
        fail('audit incomplete or golden violated')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, default=Path('reports/next_phases/leakage_gaps'))
    args = parser.parse_args()
    print(json.dumps(verify(args.report_dir), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
