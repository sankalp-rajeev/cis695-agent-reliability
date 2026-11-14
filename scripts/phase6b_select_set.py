#!/usr/bin/env python3
"""Freeze Phase 6b's evaluation set from label-free, hash-pinned inputs only.

No Docker, tracer, benchmark imports/execution, model calls, patches, correctness
labels, or oracle inputs. An existing output directory is never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE5 = ROOT / 'reports/next_phases/phase5_replay'
FROZEN_TASKS = Path(
    '/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/'
    'ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen/tasks.json'
)
OUTPUT = ROOT / 'reports/next_phases/phase6b_plan'
COSTS_SHA256 = '86c97ee2e0c64aebd10629e58c8bce3d739a803350768f8573245c8bd9f7ca97'
RESULTS_SHA256 = '8dd782e2e005e9e767baccb438b8391e02d6daca34f601254f162a301cd1ff8a'
TASKS_SHA256 = '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625'
SEED = 20261114
FIXED = (
    'django__django-10973',
    'django__django-12209',
    'django__django-14140',
    'django__django-14631',
    'matplotlib__matplotlib-25479',
    'pytest-dev__pytest-5809',
    'sphinx-doc__sphinx-10435',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_pinned(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    require(sha256(raw) == expected, 'Input hash mismatch; stop: ' + str(path))
    return raw


def select_set() -> dict:
    costs_raw = read_pinned(PHASE5 / 'per_task_costs.csv', COSTS_SHA256)
    results_raw = read_pinned(PHASE5 / 'results.json', RESULTS_SHA256)
    metadata_raw = read_pinned(FROZEN_TASKS, TASKS_SHA256)
    costs_list = list(csv.DictReader(io.StringIO(costs_raw.decode())))
    metadata_list = json.loads(metadata_raw)
    phase5 = json.loads(results_raw)
    costs = {row['task']: row for row in costs_list}
    metadata = {row['instance_id']: row for row in metadata_list}
    references = {row['task']: sorted(row['reference_regressions'])
                  for row in phase5['per_task_details']}
    require(len(costs_list) == len(costs) == 83, 'Wrong Phase 5 cost cohort')
    require(len(metadata_list) == len(metadata) == 83, 'Wrong frozen task cohort')
    require(len(phase5['per_task_details']) == len(references) == 83,
            'Wrong Phase 5 reference cohort')
    require(set(costs) == set(metadata) == set(references), 'Input cohorts differ')
    require(set(phase5['regression_cases']) == set(FIXED), 'Fixed case set changed')
    require(sum(len(references[iid]) for iid in FIXED) == 12, 'Expected 12 reference IDs')
    require(all(bool(references[iid]) == (iid in FIXED) for iid in references),
            'Unexpected regression task outside the fixed set')

    pool: dict[str, list[str]] = {}
    for iid in sorted(costs):
        row, meta = costs[iid], metadata[iid]
        require(row['ordering_eligible'] in ('True', 'False'), 'Invalid ordering eligibility')
        duration = float(row['patched_execution_s'])
        require(math.isfinite(duration) and duration >= 0, 'Invalid recorded execution cost')
        if (meta['runner']['name'] == 'pytest'
                and meta['repo'] != 'sympy/sympy'
                and row['ordering_eligible'] == 'True'
                and duration <= 180
                and iid not in FIXED):
            pool.setdefault(meta['repo'], []).append(iid)
    repositories = sorted(pool)
    rng = random.Random(SEED)
    chosen_repositories = sorted(rng.sample(repositories, 6)) if len(repositories) >= 6 else repositories
    seeded = [rng.choice(sorted(pool[repo])) for repo in chosen_repositories]
    task_ids = list(FIXED) + seeded
    require(len(task_ids) == len(set(task_ids)) == len(FIXED) + min(6, len(repositories)),
            'Evaluation tasks are duplicated or missing')
    require(all(not references[iid] for iid in seeded), 'Seeded task has a reference regression')
    require(all(metadata[iid]['runner']['name'] in ('pytest', 'django') for iid in task_ids),
            'Evaluation runner outside pytest/Django scope')
    tasks = []
    for iid in task_ids:
        meta, cost = metadata[iid], costs[iid]
        tasks.append({
            'instance_id': iid,
            'cohort': 'fixed' if iid in FIXED else 'seeded',
            'repository': meta['repo'],
            'runner': meta['runner']['name'],
            'v2_list_size': int(cost['v2_count']),
            'sealed_patched_execution_s': float(cost['patched_execution_s']),
            'reference_ids': references[iid],
            'reference_count': len(references[iid]),
            'repository_pool_size': len(pool.get(meta['repo'], [])),
        })
    return {
        'seed': SEED,
        'python_version': '.'.join(str(v) for v in sys.version_info[:3]),
        'selection_method': 'One random.Random(20261114): sample sorted repositories, '
                            'then choose one sorted task per chosen repository in repository order',
        'pool_criteria': {
            'runner': 'pytest',
            'excluded_repository': 'sympy/sympy',
            'ordering_eligible': True,
            'patched_execution_s_max_inclusive': 180,
            'exclude_fixed_set': True,
        },
        'pool_repository_sizes': {repo: len(pool[repo]) for repo in repositories},
        'pool_task_ids': {repo: sorted(pool[repo]) for repo in repositories},
        'chosen_repositories': chosen_repositories,
        'fixed_task_ids': list(FIXED),
        'seeded_task_ids': seeded,
        'task_count': len(tasks),
        'reference_id_count': 12,
        'tasks': tasks,
        'seeded_interpretation': 'No reference regressions: recall is vacuous; '
                                 'count for reduction, overhead and outcome agreement',
        'inputs': {
            'phase5_costs': {'path': 'reports/next_phases/phase5_replay/per_task_costs.csv',
                             'sha256': COSTS_SHA256},
            'phase5_reference_ids': {'path': 'reports/next_phases/phase5_replay/results.json',
                                     'sha256': RESULTS_SHA256},
            'frozen_task_metadata': {'path': str(FROZEN_TASKS), 'sha256': TASKS_SHA256},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    require(not args.output_dir.exists(), 'Output directory already exists; choose a new directory')
    result = select_set()
    raw = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    digest = sha256(raw)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'eval_set.json').write_bytes(raw)
    (args.output_dir / 'eval_set.sha256').write_text(digest + '  eval_set.json\n')
    print(json.dumps({'task_count': result['task_count'], 'sha256': digest,
                      'seeded_tasks': [task for task in result['tasks'] if task['cohort'] == 'seeded']},
                     sort_keys=True))


if __name__ == '__main__':
    main()
