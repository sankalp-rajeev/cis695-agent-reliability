#!/usr/bin/env python3
"""Build the patch-independent registry from the hash-verified Phase 4 freeze."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import phase4_launch as frozen
from reliability.env import assert_clean_interpreter
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.pre_install import load_specs
from reliability.verifier.task_specs import DEFAULT_WHEEL, load_registries, require_hash, sha, write

ROOT = Path(__file__).resolve().parents[1]


def project(path, schema):
    return JSONProjection(path.read_text()).project(schema)


def build(output):
    cohort = frozen.DEFAULT_FROZEN
    require_hash(cohort / 'tasks.json', frozen.FROZEN_TASKS_SHA256)
    require_hash(cohort / 'protocol.json', frozen.FROZEN_PROTOCOL_SHA256)
    tasks = project(cohort / 'tasks.json', {'*': {k: True for k in
        ('instance_id', 'repo', 'base_commit', 'base_archive_sha256', 'patch_path', 'patch_sha256',
         'runner', 'selections', 'image_binding')}})
    protocol = project(cohort / 'protocol.json', {'task_artifact_sha256': True})
    if len(tasks) != 83 or len({t['instance_id'] for t in tasks}) != 83:
        raise ValueError('Wrong frozen cohort')
    provenance = frozen.PROVENANCE
    metadata = project(provenance / 'provenance.json', {'wheel_sha256': True, 'dataset_projection_sha256': True})
    projection = provenance / 'dataset_projection.json'
    require_hash(projection, metadata['dataset_projection_sha256'])
    require_hash(DEFAULT_WHEEL, metadata['wheel_sha256'])
    specs = load_specs(DEFAULT_WHEEL, projection)
    if set(specs) != {t['instance_id'] for t in tasks}:
        raise ValueError('Pre_install/frozen cohort mismatch')
    manifest = json.loads((frozen.PREFLIGHT / 'manifest.json').read_bytes())
    summary = project(frozen.PREFLIGHT / 'summary.json', {'statuses': True, 'tasks_with_unresolved_mismatches': True})
    if summary != {'statuses': {'VERIFIED': 83}, 'tasks_with_unresolved_mismatches': []}:
        raise ValueError('Pristine preflight did not verify every image')
    if manifest['frozen_tasks_sha256'] != frozen.FROZEN_TASKS_SHA256 or manifest['pre_install_provenance'] != metadata:
        raise ValueError('Preflight/provenance mismatch')
    for path, expected in manifest['source_sha256'].items():
        if path in ('src/reliability/verifier/source_integrity.py', 'src/reliability/verifier/pre_install.py',
                    'scripts/phase4_integrity_preflight.py'):
            require_hash(frozen.confined(ROOT, path), expected)
    for path, expected in manifest['receipt_sha256'].items():
        require_hash(frozen.confined(frozen.PREFLIGHT, path), expected)
    # The approved exception is restricted to the exact manifest and its 31 sources.
    require_hash(frozen.REFERENCE / 'manifest.json',
                 '5464690f7a64d1bdeeea88f257f8bdedc70a98d7d758a4a298f34e7a6933b792')
    result, commands = [], []
    for task in tasks:
        iid = task['instance_id']
        proof = specs[iid]
        if proof.repo != task['repo'] or proof.base_commit != task['base_commit']:
            raise ValueError('Dataset/frozen source identity mismatch')
        for relative in (task['selections']['v2'], task['patch_path']):
            require_hash(frozen.confined(cohort, relative), protocol['task_artifact_sha256'][relative])
        require_hash(frozen.confined(cohort, task['patch_path']), task['patch_sha256'])
        identity = project(frozen.PREFLIGHT / 'tasks' / iid / 'identity.json',
                           {k: True for k in ('image_id', 'image_tag_metadata', 'base_commit', 'archive_sha256')})
        if (identity['image_id'] != task['image_binding']['host_image_id'] or
            identity['base_commit'] != task['base_commit'] or identity['archive_sha256'] != task['base_archive_sha256']):
            raise ValueError('Pristine preflight identity mismatch')
        runner = dict(task['runner'], django_parallel_one=None)
        if runner['name'] == 'django':
            choice = frozen.frozen_django_command_choice(iid)
            runner['django_parallel_one'] = choice['parallel_one']
            commands.append(dict(instance_id=iid, **choice))
        relative = 'tasks/' + iid + '/source_receipt.json'
        if relative not in manifest['receipt_sha256']:
            relative += '.gz'
        receipt = frozen.confined(frozen.PREFLIGHT, relative)
        result.append({'instance_id': iid, 'repo': proof.repo, 'version': proof.version,
            'base_commit': proof.base_commit, 'image': {'tag': identity['image_tag_metadata'], 'id': identity['image_id']},
            'archive': {'path': str(Path('/home/sankalp/cg_repos/task_archives') / (iid + '.tar')),
                        'sha256': task['base_archive_sha256'], 'pax_comment': proof.base_commit},
            'pre_install': {**metadata, 'spec': proof.resolve(), 'wheel_path': str(DEFAULT_WHEEL),
                            'dataset_projection_path': str(projection)},
            'integrity_preflight': {'status': 'VERIFIED', 'receipt_path': str(receipt),
                                    'receipt_sha256': manifest['receipt_sha256'][relative]},
            'runner': runner, 'origin': 'phase4_freeze'})
    registry = {'schema': 'task_spec_registry/1', 'cohort': 'swebench_verified_phase4_83',
                'built_by_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'tasks': result}
    # Validate everything before publishing the registry at its requested path.
    temporary = ROOT / 'runs/e2e_v1_4_1_checks/task_specs_83.candidate.json'
    write(temporary, registry)
    validated, _ = load_registries([temporary])
    write(output, registry)
    report = {'tasks': len(validated), 'registry_sha256': sha(output),
              'django_commands': commands, 'outcome_fields_decoded': False}
    write(ROOT / 'reports/next_phases/e2e_v1_4_1/registry_build.json', report)
    print(json.dumps({'tasks': len(validated), 'registry_sha256': sha(output), 'django_sources': len(commands)}))


if __name__ == '__main__':
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'configs/e2e/task_specs_83.json')
    build(parser.parse_args().output)
