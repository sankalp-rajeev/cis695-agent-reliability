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


def definition_evidence(path, symbol_hash):
    """Independently decode commands and require a successful ordered write."""
    first, definitions, pending = None, [], {}
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        try:
            message = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        if any(hashlib.sha256(token.encode()).hexdigest() == symbol_hash
               for token in re.findall(r'\btest[A-Za-z0-9_]+\b', raw)):
            first = number if first is None else first
        if message.get('role') == 'assistant':
            for index, call in enumerate(message.get('tool_calls') or []):
                function = call.get('function') or {}
                if function.get('name') != 'bash':
                    continue
                args = function.get('arguments') or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        continue
                command = args.get('command', '') if isinstance(args, dict) else ''
                if not re.search(r'(?:>|\b(?:write_text|write_bytes|write|writelines|apply_patch|sed|perl|tee)\b)', command):
                    continue
                symbols = re.findall(r'\b(?:async\s+)?def\s+(test[A-Za-z0-9_]+)\s*\(', command)
                if any(hashlib.sha256(s.encode()).hexdigest() == symbol_hash for s in symbols):
                    pending[str(call.get('id') or f'call-{index}')] = number
        elif message.get('role') == 'tool':
            definition = pending.pop(str(message.get('tool_call_id') or ''), None)
            if definition is not None and re.search(r'<returncode>\s*0\s*</returncode>', str(message.get('content') or '')):
                definitions.append(definition)
    return first, min(definitions) if definitions else None


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
                first, definition = definition_evidence(Path(new['path']), symbol_hash)
                if first is None or definition is None or definition > first:
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
    git_results = [r.get('checks', {}).get('git', {}).get('result', {}) for r in images]
    copies = [(r['instance_id'], c) for r in images for c in
              r.get('checks', {}).get('packages', {}).get('result', {}).get('copies', [])]
    image_recount = dict(cohort=len(images), present=sum(r.get('status') != 'missing' for r in images),
        missing=missing,
        incomplete=sorted(r['instance_id'] for r in images if r.get('status') == 'incomplete' or
            any(c['status'] != 'complete' for c in r.get('checks', {}).values())),
        future_history_images=sum(g.get('future_object_count', 0) > 0 for g in git_results),
        future_reachable_images=sum(g.get('future_reachable_count', 0) > 0 for g in git_results),
        gold_blob_images=sum(any(b['present'] for b in g.get('gold_post_image_blobs', [])) for g in git_results),
        gold_blobs_probed=sum(len(g.get('gold_post_image_blobs', [])) for g in git_results),
        different_version_copies=sum(c.get('different_from_base') is True for _, c in copies),
        different_version_tasks=sorted({iid for iid,c in copies if c.get('different_from_base')}),
        unresolved_copy_versions=sum(c.get('different_from_base') is None for _, c in copies))
    if image_recount != image_summary:
        fail('image totals mismatch')
    subtraction = root/'legacy_subtraction_comparison.json'
    if subtraction.is_file():
        proof = read(subtraction)
        by_id = {row['instance_id']:row for row in proof['tasks']}
        if proof['checked'] != len(images) or proof['mismatches'] or len(by_id) != len(images):
            fail('legacy subtraction coverage mismatch')
        for image in images:
            row = by_id[image['instance_id']]
            hashes = sorted(set(image['checks']['base_probes']['result']))
            observed = hashlib.sha256(json.dumps(hashes).encode()).hexdigest()
            if not row['equal'] or row['baseline_sha256'] != observed or row['extended_sha256'] != observed:
                fail('legacy subtraction proof mismatch')
    report = (root/'REPORT.md').read_text()
    marker = re.search(r'<!-- totals-json: (.+?) -->', report)
    if not marker or json.loads(marker.group(1)) != dict(trajectory=expected, images=image_summary):
        fail('report totals mismatch')
    human_totals = {
        r'Confirmed findings: (\d+)': expected['severity'].get('confirmed', 0),
        r'Benchmark-awareness findings: (\d+)': expected['severity'].get('benchmark-awareness', 0),
        r'(\d+) images contain commits after base': image_summary['future_history_images'],
        r'(\d+) images contain at least one exact gold': image_summary['gold_blob_images'],
        r'(\d+) unmasked package copies have': image_summary['different_version_copies'],
        r'(\d+) copy versions remain unresolved': image_summary['unresolved_copy_versions'],
    }
    for pattern, expected_value in human_totals.items():
        found = re.search(pattern, report)
        if not found or int(found.group(1)) != expected_value:
            fail('human-readable report total mismatch')
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
