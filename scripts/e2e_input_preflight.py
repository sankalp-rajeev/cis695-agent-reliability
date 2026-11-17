#!/usr/bin/env python3
"""Audit D1 input access without opening any command-projection source.

This is an access preflight, not the A1–A7 acceptance verifier. Unknown task
metadata values are skipped structurally without JSON decoding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
TASKS_SHA256 = '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625'
PROTOCOL_SHA256 = '2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153'
FORBIDDEN_NAMES = ('oracle', 'grade', 'grader', 'label', 'gold', 'posthoc',
                   'fail_to_pass', 'pass_to_pass')


class Projection:
    """Minimal independent JSON whitelist reader, including unknown containers."""

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.decoder = json.JSONDecoder()

    def whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def scalar(self):
        self.whitespace()
        value, self.pos = self.decoder.raw_decode(self.text, self.pos)
        return value

    def skip(self):
        self.whitespace()
        depth, quoted, escaped = 0, False, False
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
                    if depth == 0:
                        self.pos += 1
                        return
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
            elif char in ']}':
                if depth == 0:
                    return
                depth -= 1
                if depth == 0:
                    self.pos += 1
                    return
            elif depth == 0 and char == ',':
                return
            self.pos += 1

    def project(self, schema):
        self.whitespace()
        if schema is True:
            return self.scalar()
        char = self.text[self.pos]
        self.pos += 1
        if char == '[':
            result = []
            self.whitespace()
            while self.text[self.pos] != ']':
                result.append(self.project(schema['*']))
                self.whitespace()
                if self.text[self.pos] == ',':
                    self.pos += 1
                self.whitespace()
            self.pos += 1
            return result
        if char != '{':
            raise ValueError('Expected a JSON object or array')
        result = {}
        self.whitespace()
        while self.text[self.pos] != '}':
            key = self.scalar()
            self.whitespace()
            if self.text[self.pos] != ':':
                raise ValueError('Malformed JSON object')
            self.pos += 1
            if key in schema:
                result[key] = self.project(schema[key])
            else:
                self.skip()
            self.whitespace()
            if self.text[self.pos] == ',':
                self.pos += 1
            self.whitespace()
        self.pos += 1
        return result


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit_frozen_files(root=ROOT):
    """Rehash permitted frozen artifacts; report forbidden names without opening."""
    manifest = root / 'reports/policy_v1_4/artifact_manifest.sha256'
    entries = []
    for line in manifest.read_text().splitlines():
        if line.strip():
            checksum, name = line.split('  ', 1)
            entries.append((manifest.relative_to(root).as_posix(), name, checksum))
    probe = root / 'reports/umgpt_probe/frozen_files.json'
    rows = Projection(probe.read_text()).project({'*': {'path': True, 'sha256': True}})
    entries.extend((probe.relative_to(root).as_posix(), r['path'], r['sha256']) for r in rows)
    result = []
    for origin, name, checksum in entries:
        row = {'manifest': origin, 'path': name, 'expected_sha256': checksum}
        path = root / name
        if any(word in name.casefold() for word in FORBIDDEN_NAMES):
            row.update(status='BLOCKED_FORBIDDEN_NAME', opened=False)
        elif Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe frozen artifact path: ' + name)
        elif path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Frozen artifact escapes worktree: ' + name)
        else:
            row['actual_sha256'] = digest(path.read_bytes())
            row.update(status='MATCH' if row['actual_sha256'] == checksum else 'MISMATCH', opened=True)
        result.append(row)
    return result


def audit(frozen=FROZEN, reference=None):
    """Resolve the exact Django sources in the existing function, without I/O there."""
    reference = reference or ROOT / 'reports/next_phases/phase4_rerun/fix13_reference'
    inputs = {}
    for name, expected in (('tasks.json', TASKS_SHA256), ('protocol.json', PROTOCOL_SHA256)):
        raw = (frozen / name).read_bytes()
        actual = digest(raw)
        if actual != expected:
            raise ValueError('Frozen input hash mismatch: ' + name)
        inputs[str(frozen / name)] = actual
        if name == 'tasks.json':
            tasks = Projection(raw.decode()).project({'*': {
                'instance_id': True, 'runner': {'name': True}}})
    raw = (reference / 'manifest.json').read_bytes()
    inputs[str(reference / 'manifest.json')] = digest(raw)
    manifest = Projection(raw.decode()).project({'input_sha256': True})
    rows = []
    for task in tasks:
        if task['runner']['name'] != 'django':
            continue
        iid = task['instance_id']
        matches = [(Path(path), checksum) for path, checksum in manifest['input_sha256'].items()
                   if Path(path).parts[-3:] == (iid, 'v2', 'result.json')]
        if len(matches) != 1:
            raise ValueError('Missing unique frozen Django command: ' + iid)
        path, checksum = matches[0]
        # Do not resolve symlinks or stat/open these paths. The declared paths
        # themselves already fall outside the user-authorized input roots.
        inside = path.is_absolute() and path.is_relative_to(frozen)
        rows.append({'instance_id': iid, 'path': str(path), 'sha256': checksum,
                     'inside_paired_frozen': inside, 'source_opened': False})
    blocked = [row for row in rows if not row['inside_paired_frozen']]
    return {'check': 'D1_INPUT_ACCESS', 'status': 'BLOCKED_INPUT_ACCESS' if blocked else 'READY',
            'frozen_tasks': len(tasks), 'django_tasks': len(rows),
            'blocked_sources': blocked, 'input_sha256': inputs,
            'command_projection_sources_opened': 0, 'model_calls': 0,
            'acceptance_checks_run': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit()
    report['frozen_artifacts'] = audit_frozen_files()
    blocked_files = [r for r in report['frozen_artifacts'] if r['status'] == 'BLOCKED_FORBIDDEN_NAME']
    mismatches = [r for r in report['frozen_artifacts'] if r['status'] == 'MISMATCH']
    if blocked_files or mismatches:
        report['status'] = 'BLOCKED_INPUT_ACCESS' if not mismatches else 'FROZEN_HASH_MISMATCH'
    output = args.output.resolve()
    allowed = ROOT / 'reports/next_phases/e2e_v1_4_1'
    if not output.is_relative_to(allowed):
        raise ValueError('Preflight report must be under reports/next_phases/e2e_v1_4_1/')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('blocked_sources', 'frozen_artifacts')}, indent=2))
    print('blocked_source_count=' + str(len(report['blocked_sources'])))
    print('frozen_artifact_matches=' + str(sum(r['status'] == 'MATCH' for r in report['frozen_artifacts'])))
    print('frozen_artifact_mismatches=' + str(len(mismatches)))
    print('blocked_frozen_artifacts=' + json.dumps([r['path'] for r in blocked_files]))
    return 2 if report['status'] != 'READY' else 0


if __name__ == '__main__':
    raise SystemExit(main())
