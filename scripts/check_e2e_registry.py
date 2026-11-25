#!/usr/bin/env python3
"""A4b: manually prepare one existing task using the shared registry interface."""

import copy
import json
import subprocess

from reliability.env import assert_clean_interpreter
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.pre_install import load_specs
from reliability.verifier.task_specs import (
    DEFAULT_PROJECTION, DEFAULT_WHEEL, ROOT, load_registries, sha, write,
)


def check():
    iid = 'astropy__astropy-13977'
    preflight = ROOT / 'reports/next_phases/phase4_rerun/fix10_integrity_preflight'
    def project(path, schema):
        return JSONProjection(path.read_text()).project(schema)
    identity = project(preflight / 'tasks' / iid / 'identity.json', {
        k: True for k in ('image_id', 'image_tag_metadata', 'base_commit', 'archive_sha256')})
    proof = load_specs(DEFAULT_WHEEL, DEFAULT_PROJECTION)[iid]
    receipt = preflight / 'tasks' / iid / 'source_receipt.json.gz'
    task = {'instance_id': iid, 'repo': proof.repo, 'version': proof.version,
        'base_commit': identity['base_commit'],
        'image': {'tag': identity['image_tag_metadata'], 'id': identity['image_id']},
        'archive': {'path': '/home/sankalp/cg_repos/task_archives/' + iid + '.tar',
                    'sha256': identity['archive_sha256'], 'pax_comment': identity['base_commit']},
        'pre_install': {'wheel_sha256': sha(DEFAULT_WHEEL), 'dataset_projection_sha256': sha(DEFAULT_PROJECTION),
                        'spec': proof.resolve(), 'wheel_path': str(DEFAULT_WHEEL),
                        'dataset_projection_path': str(DEFAULT_PROJECTION)},
        'integrity_preflight': {'status': 'VERIFIED', 'receipt_path': str(receipt), 'receipt_sha256': sha(receipt)},
        'runner': {'name': 'pytest', 'evidence': 'pytest in setup.cfg', 'django_parallel_one': None},
        'origin': 'prepared'}
    # Evidence text is patch-independent layout metadata, copied from the frozen task.
    frozen = ROOT / 'configs/e2e/task_specs_83.json'
    frozen_row = next(t for t in json.loads(frozen.read_text())['tasks'] if t['instance_id'] == iid)
    task['runner'] = frozen_row['runner']
    registry = {'schema': 'task_spec_registry/1', 'cohort': 'prepared_interface_probe',
                'built_by_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                'tasks': [task]}
    output = ROOT / 'runs/e2e_v1_4_1_checks/registry_interface'
    path = output / 'prepared.json'
    write(path, registry)
    prepared, _ = load_registries([path])
    frozen_specs, _ = load_registries([frozen])
    if prepared[iid] != frozen_specs[iid] or prepared[iid].source != frozen_specs[iid].source:
        raise ValueError('Prepared TaskSpec/BaseSourceSpec differs')
    refused = []
    for mode in ('wrong_hash', 'duplicate_id', 'missing_field'):
        bad = copy.deepcopy(registry)
        if mode == 'wrong_hash':
            bad['tasks'][0]['archive']['sha256'] = '0' * 64
        elif mode == 'duplicate_id':
            bad['tasks'].append(copy.deepcopy(task))
        else:
            del bad['tasks'][0]['base_commit']
        bad_path = output / (mode + '.json')
        write(bad_path, bad)
        try:
            load_registries([bad_path])
        except ValueError:
            refused.append(mode)
        else:
            raise ValueError('Invalid registry accepted: ' + mode)
    report = {'A4b': 'PASS', 'instance_id': iid, 'cohort': registry['cohort'],
              'origin': 'prepared', 'same_TaskSpec': True, 'same_BaseSourceSpec': True,
              'refused': refused, 'registry_sha256': sha(path)}
    write(ROOT / 'reports/next_phases/e2e_v1_4_1/A4b.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    assert_clean_interpreter()
    check()
