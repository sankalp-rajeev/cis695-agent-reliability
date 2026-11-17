#!/usr/bin/env python3
"""Independent A1/A2, registry, preservation and A4 evidence check (stdlib only).

A1 compares recorded selector output with the frozen lists; it does not claim
an independent reimplementation of the multi-tier selector.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import tarfile
from pathlib import Path

from e2e_input_preflight import Projection as StructuralProjection, audit_frozen_files

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
CAPTURES = Path('/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/phase4_v4_attempt4_20261109T185713Z')
SEAL = ROOT / 'reports/next_phases/phase4_rerun/attempt4_seal'
G1 = ROOT / 'reports/next_phases/phase4_rerun/fix18b_g1'
POLICIES = ('C_invalid_excluded', 'C_invalid_missing', 'S_invalid_excluded', 'S_invalid_missing')


class Projection(StructuralProjection):
    """Skip large unrequested captures structurally, without decoding values."""
    string = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"')
    structure = re.compile(r'["{}\[\]]')
    scalar_end = re.compile(r'[,}\]]')

    def skip(self):
        self.whitespace()
        char = self.text[self.pos]
        if char == '"':
            self.pos = self.string.match(self.text, self.pos).end()
        elif char in '[{':
            depth = 1
            self.pos += 1
            while depth:
                match = self.structure.search(self.text, self.pos)
                if match is None:
                    raise ValueError('Unfinished JSON')
                char = match.group()
                if char == '"':
                    self.pos = self.string.match(self.text, match.start()).end()
                else:
                    depth += 1 if char in '[{' else -1
                    self.pos = match.end()
        else:
            match = self.scalar_end.search(self.text, self.pos)
            self.pos = match.start() if match else len(self.text)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def require_hash(path, expected):
    if sha(path) != expected:
        raise ValueError('SHA-256 mismatch: ' + str(path))


def project(path, schema):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    return Projection(raw.decode()).project(schema)


def seal_entries(captures):
    authority = project(SEAL / 'results.json', {'run_manifest': {'sha256': True, 'file_count': True, 'total_bytes': True}})['run_manifest']
    require_hash(SEAL / 'run_manifest.sha256', authority['sha256'])
    entries = {}
    for line in (SEAL / 'run_manifest.sha256').read_text().splitlines():
        if line and not line.startswith('#'):
            checksum, name = line.split('  ', 1)
            if name in entries or Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('Unsafe seal path')
            entries[name] = checksum
    if len(entries) != 1799:
        raise ValueError('Sealed file count mismatch')
    # The acceptance launch already checked every file; independently hash each
    # raw policy result before using it below, plus the pinned launch authority.
    require_hash(captures / 'attempt.json', entries['attempt.json'])
    pin = project(captures / 'attempt.json', {'G1_manifest_sha256': True})['G1_manifest_sha256']
    require_hash(G1 / 'manifest.json', pin)
    return entries, pin


def collection(root, iid, tree, manifest):
    logical = 'tasks/' + iid + '/' + tree + '/collection.json'
    name = logical if logical in manifest['receipt_sha256'] else logical + '.gz'
    path = root / name
    require_hash(path, manifest['receipt_sha256'][name])
    schema = {'records': {'*': {k: True for k in (
        'selected_id', 'stage', 'valid', 'runnable_ids', 'collector_fallback', 'module_skip_reason')}}}
    return project(path, schema)


def native_ids(receipt):
    return {r['selected_id'] for r in receipt['records'] if r.get('stage') == 'native' and r.get('valid')
            and r.get('runnable_ids') and not r.get('collector_fallback') and not r.get('module_skip_reason')}


def concrete_ids(receipt):
    selected = native_ids(receipt)
    return {identity for r in receipt['records'] if r['selected_id'] in selected for identity in r['runnable_ids']}


def registry_check(path):
    require_hash(FROZEN / 'tasks.json', '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625')
    require_hash(FROZEN / 'protocol.json', '2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153')
    metadata = project(FROZEN / 'tasks.json', {'*': {k: True for k in (
        'instance_id', 'repo', 'base_commit', 'base_archive_sha256', 'image_binding', 'runner', 'selections',
        'patch_path', 'patch_sha256')}})
    metadata = {r['instance_id']: r for r in metadata}
    registry = json.loads(path.read_text())
    if registry['schema'] != 'task_spec_registry/1' or {r['instance_id'] for r in registry['tasks']} != set(metadata):
        raise ValueError('Registry/frozen cohort mismatch')
    preflight = ROOT / 'reports/next_phases/phase4_rerun/fix10_integrity_preflight'
    preflight_manifest = json.loads((preflight / 'manifest.json').read_bytes())
    reference = ROOT / 'reports/next_phases/phase4_rerun/fix13_reference/manifest.json'
    require_hash(reference, '5464690f7a64d1bdeeea88f257f8bdedc70a98d7d758a4a298f34e7a6933b792')
    sources = project(reference, {'input_sha256': True})['input_sha256']
    choices = {}
    for iid, task in metadata.items():
        if task['runner']['name'] != 'django':
            continue
        matches = [(Path(p), h) for p, h in sources.items() if Path(p).parts[-3:] == (iid, 'v2', 'result.json')]
        if len(matches) != 1:
            raise ValueError('Missing unique frozen Django source')
        source, checksum = matches[0]
        require_hash(source, checksum)
        calls = project(source, {'calls': {'@limit': 2, '*': {'run': {'events': {'*': {'argv': True}}}}}})['calls']
        flags = set()
        for call in calls:
            for event in call['run'].get('events', []):
                if 'argv' not in event:
                    continue
                argv = event['argv']
                if argv[:3] != ['python', 'tests/runtests.py', '--verbosity=2']:
                    raise ValueError('Unexpected Django argv')
                enabled = '--parallel' in argv and argv[argv.index('--parallel')+1:argv.index('--parallel')+2] == ['1']
                tokens = [t for t in argv if t.startswith('--parallel')]
                if tokens and (tokens != ['--parallel'] or not enabled):
                    raise ValueError('Unsupported Django parallel choice')
                flags.add(enabled)
        if len(flags) != 1:
            raise ValueError('Inconsistent Django choice')
        choices[iid] = flags.pop()
    rows = registry['tasks']
    for row in rows:
        iid, expected = row['instance_id'], metadata[row['instance_id']]
        if (row['repo'] != expected['repo'] or row['base_commit'] != expected['base_commit'] or
            row['archive']['sha256'] != expected['base_archive_sha256'] or
            row['image']['id'] != expected['image_binding']['host_image_id']):
            raise ValueError('Registry frozen identity mismatch: ' + iid)
        require_hash(Path(row['archive']['path']), expected['base_archive_sha256'])
        with tarfile.open(row['archive']['path']) as archive:
            if archive.pax_headers.get('comment') != row['base_commit'] or row['archive']['pax_comment'] != row['base_commit']:
                raise ValueError('Registry archive commit mismatch')
        pre = row['pre_install']
        if pre['wheel_sha256'] != preflight_manifest['pre_install_provenance']['wheel_sha256'] or pre['dataset_projection_sha256'] != preflight_manifest['pre_install_provenance']['dataset_projection_sha256']:
            raise ValueError('Registry pre-install provenance differs from freeze')
        require_hash(Path(pre['wheel_path']), pre['wheel_sha256'])
        require_hash(Path(pre['dataset_projection_path']), pre['dataset_projection_sha256'])
        data_row = pre['spec']['dataset_row']
        if data_row != {k: row[k] for k in ('instance_id', 'repo', 'version', 'base_commit')}:
            raise ValueError('Pre_install dataset identity mismatch')
        receipt = Path(row['integrity_preflight']['receipt_path'])
        logical = receipt.relative_to(preflight).as_posix()
        require_hash(receipt, preflight_manifest['receipt_sha256'][logical])
        require_hash(receipt, row['integrity_preflight']['receipt_sha256'])
        proof = project(receipt, {'status': True, 'base_commit': True, 'archive_sha256': True})
        if proof != {'status': 'VERIFIED', 'base_commit': row['base_commit'], 'archive_sha256': row['archive']['sha256']}:
            raise ValueError('Registry preflight mismatch')
        if row['runner']['name'] != expected['runner']['name'] or row['runner']['evidence'] != expected['runner']['evidence']:
            raise ValueError('Registry runner mismatch')
        if row['runner']['name'] == 'django' and row['runner']['django_parallel_one'] != choices[iid]:
            raise ValueError('Registry Django choice mismatch')
    return metadata, sha(path), choices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-specs', type=Path, default=ROOT / 'configs/e2e/task_specs_83.json')
    parser.add_argument('--offline', type=Path, default=ROOT / 'runs/e2e_v1_4_1_checks/offline')
    parser.add_argument('--live', type=Path, default=ROOT / 'runs/e2e_v1_4_1_checks/live_final')
    parser.add_argument('--captures', type=Path, default=CAPTURES)
    args = parser.parse_args()
    metadata, registry_sha, django_choices = registry_check(args.task_specs)
    frozen = audit_frozen_files(approved_exceptions=True)
    if any(r['status'] != 'MATCH' for r in frozen):
        raise ValueError('Frozen artifact mismatch or unapproved file')
    entries, g1_pin = seal_entries(args.captures)
    policies_schema = {'policies': {p: {'signal': True, 'outcomes': True} for p in POLICIES}}
    a1, a2, expected_policies = 0, 0, {}
    protocol = project(FROZEN / 'protocol.json', {'task_artifact_sha256': True})
    for iid, row in metadata.items():
        path = FROZEN / row['selections']['v2']
        require_hash(path, protocol['task_artifact_sha256'][row['selections']['v2']])
        expected = project(path, {'tests': True})['tests']
        actual = project(args.offline / 'selections' / iid / 'v2.json', {'tests': True})['tests']
        if actual != expected:
            raise ValueError('A1 ordered list mismatch: ' + iid)
        a1 += 1
        relative = 'tasks/' + iid + '/result.json'
        raw = args.captures / relative
        require_hash(raw, entries[relative])
        expected = project(raw, policies_schema)['policies']
        actual = project(args.offline / 'tasks' / iid / 'v2_policies.json', policies_schema)['policies']
        if expected != actual:
            raise ValueError('A2 raw per-test/signal mismatch: ' + iid)
        expected_policies[iid] = expected
        for line in (args.offline / 'tasks' / iid / 'health.jsonl').read_text().splitlines():
            if Projection(line).project({'halt': True}).get('halt'):
                raise ValueError('A2 health halt: ' + iid)
        a2 += 1
    completion = json.loads((args.live / 'completion.json').read_text())
    if completion['status'] != 'COMPLETE' or len(completion['completed_tasks']) != 3:
        raise ValueError('A4 live batch incomplete')
    header = json.loads((args.live / 'header.json').read_text())
    if header['policy_version'] != 'v1.4.1-full' or not header['skip_v4']:
        raise ValueError('A4 policy/skip stamp mismatch')
    if header['registry_sha256'].get(str(args.task_specs.resolve())) != registry_sha:
        raise ValueError('A4 registry hash stamp mismatch')
    for key, path in (('config_sha256', ROOT / 'configs/verifier/full_v1_4_1.yaml'),
                      ('primary_config_sha256', ROOT / 'configs/model/primary.yaml'),
                      ('generator_config_sha256', ROOT / 'configs/model/generator.yaml')):
        require_hash(path, header[key])
    manifest = json.loads((G1 / 'manifest.json').read_bytes())
    a4 = []
    for iid in completion['completed_tasks']:
        directory = args.live / 'tasks' / iid
        record = json.loads((directory / 'verification_record.full-v1.4.1.json').read_bytes())
        expected_task = metadata[iid]
        if record['provenance'] != header or record['image_id'] != expected_task['image_binding']['host_image_id'] or record['archive_sha256'] != expected_task['base_archive_sha256']:
            raise ValueError('A4 task input stamps mismatch')
        require_hash(directory / 'patch.diff', expected_task['patch_sha256'])
        require_hash(directory / 'patch.diff', record['patch_sha256'].removeprefix('sha256:'))
        require_hash(directory / 'verification/selection.json', record['selection_sha256'])
        expected_selection = project(FROZEN / expected_task['selections']['v2'], {'tests': True})['tests']
        if record['selected_tests'] != expected_selection:
            raise ValueError('A4 selection changed')
        if not record['skip_v4'] or record['reproduction']['detail'] != 'SKIP_V4_FOR_CHECK':
            raise ValueError('A4 did not skip V4')
        receipt = directory / 'verification/pristine_source_receipt.json'
        require_hash(receipt, record['pristine_receipt_sha256'])
        if project(receipt, {'status': True})['status'] != 'VERIFIED':
            raise ValueError('A4 pristine receipt not VERIFIED')
        v3 = directory / 'verification/v3_pristine_source_receipt.json'
        if project(v3, {'status': True})['status'] != 'VERIFIED':
            raise ValueError('A4 V3 pristine receipt not VERIFIED')
        for tree in ('base', 'patched'):
            sealed = collection(G1, iid, tree, manifest)
            live = directory / 'verification/g1/tasks' / iid / tree / 'collection.json'
            require_hash(live, record['g1_receipt_sha256'][tree])
            actual = project(live, {'records': {'*': {k: True for k in (
                'selected_id', 'stage', 'valid', 'runnable_ids', 'collector_fallback', 'module_skip_reason')}}})
            if native_ids(actual) != native_ids(sealed):
                raise ValueError('A4 native collection identity mismatch: ' + iid + '/' + tree)
            if concrete_ids(actual) != concrete_ids(sealed):
                raise ValueError('A4 concrete native identity mismatch: ' + iid + '/' + tree)
            pristine = live.parent / 'pristine_source_receipt.json'
            if project(pristine, {'status': True})['status'] != 'VERIFIED':
                raise ValueError('A4 G1 pristine receipt not VERIFIED')
        actual = project(directory / 'verification/v2_policies.json', policies_schema)['policies']
        if actual != expected_policies[iid]:
            raise ValueError('A4 policy outcomes differ: ' + iid)
        runner = project(directory / 'verification/base.json', {
            'validation_summary': {'context': {'runner': True}}})['validation_summary']['context']['runner']
        expected_runner = 'sympy' if expected_task['repo'] == 'sympy/sympy' else expected_task['runner']['name']
        if runner != expected_runner:
            raise ValueError('A4 native runner differs: ' + iid)
        a4.append({'instance_id': iid, 'image_id': record['image_id'], 'archive_sha256': record['archive_sha256'],
                   'patch_sha256': record['patch_sha256'], 'selection_sha256': record['selection_sha256'],
                   'pristine_receipt_sha256': record['pristine_receipt_sha256'],
                   'g1_receipt_sha256': record['g1_receipt_sha256'], 'pristine_status': 'VERIFIED',
                   'native_selected_and_concrete_sets_equal': True, 'all_four_policies_equal': True,
                   'runner': runner, 'skip_v4': True, 'decision': record['decision']['decision']})
    if {r['runner'] for r in a4} != {'django', 'sympy', 'pytest'}:
        raise ValueError('A4 needs all three native runners')
    report_dir = ROOT / 'reports/next_phases/e2e_v1_4_1'
    (report_dir / 'A4.json').write_text(json.dumps({'A4': 'PASS', 'live_root': str(args.live.resolve()), 'tasks': a4, 'model_calls': 0,
        'django_parallel_one_in_freeze': any(django_choices.values()), 'differences': []}, indent=2) + '\n')
    (report_dir / 'A7.json').write_text(json.dumps({'A7': 'PASS', 'registry_sha256': registry_sha,
        'A1': {'matched': a1, 'method': 'RECORDED_OUTPUT_ONLY; selector not independently reimplemented'},
        'A2': {'matched': a2, 'policies': list(POLICIES), 'health_halts': 0},
        'G1_manifest_sha256': g1_pin, 'frozen_artifacts': frozen,
        'A4_tasks': [r['instance_id'] for r in a4]}, indent=2) + '\n')
    print('PASS registry: 83 frozen task identities and artifact hashes; SHA-256 ' + registry_sha)
    print('PASS frozen artifacts: ' + str(len(frozen)) + ' matching hashes; golden CSV hashed as bytes only')
    print('PASS A1: ' + str(a1) + '/83 identical ordered lists (RECORDED_OUTPUT_ONLY; selector not independently reimplemented)')
    print('PASS A2: ' + str(a2) + '/83 raw four-policy per-test/signal equality, zero recorded health halts')
    print('PASS G1 authority: sealed launch manifest SHA-256 ' + g1_pin)
    print('PASS A4: VERIFIED pristine receipts, sealed selected/concrete native identity sets and all four policy outcomes for ' + ', '.join(r['instance_id'] for r in a4))
    print('PASS independent checker; standard library only; no model calls')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
