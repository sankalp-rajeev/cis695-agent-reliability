#!/usr/bin/env python3
"""Three serial base-only cost probes, chosen solely by frozen selection size."""

import argparse
import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import phase3_execution_smoke as smoke
from phase3_fix3_smoke import FROZEN
from reliability.env import clean_env
from reliability.verifier.container import _docker_bin


def selection_sizes():
    rows = []
    for task in json.loads((FROZEN / 'tasks.json').read_text()):
        path = FROZEN / task['selections']['v2']
        ids = json.loads(path.read_text())['tests']
        rows.append({'task': task['instance_id'],
                     'runner': 'sympy' if task['repo'] == 'sympy/sympy' else task['runner']['name'],
                     'selected_ids': len(ids), 'modules': len({t.split('::')[0] for t in ids}),
                     'selection_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(rows) == 83
    return rows


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def run_probe(output, runner, budget):
    rows = selection_sizes()
    largest = min((r for r in rows if r['runner'] == runner),
                  key=lambda r: (-r['selected_ids'], r['task']))
    observed = {}
    original = smoke.TaskContainer

    class AuditedContainer(original):
        def __enter__(self):
            super().__enter__()
            try:
                proc = subprocess.run([_docker_bin(), 'inspect', '-f', '{{json .HostConfig}}', self.name],
                                      env=clean_env(), capture_output=True, text=True, check=True)
                config = json.loads(proc.stdout)
                observed.update(cpu_shares=config['CpuShares'], nano_cpus=config['NanoCpus'],
                                network=config['NetworkMode'], container_name=self.name)
                assert observed['cpu_shares'] == 2048 and observed['nano_cpus'] == 0
                assert observed['network'] == 'none'
                return self
            except BaseException:
                self.stop()
                raise

    smoke.TaskContainer = AuditedContainer
    start = time.monotonic()
    try:
        smoke.main(SimpleNamespace(task=largest['task'], output=output, timeout_s=budget))
    finally:
        smoke.TaskContainer = original
    run = json.loads((output / 'base_run.json').read_text())
    summary_path = output / 'summary.json'
    summary = json.loads(summary_path.read_text())
    summary.update(selection_rule='largest frozen selected-ID count per actual runner; task ID breaks ties',
                   pass_wall_s=run['duration_s'], budget_s=run['budget_s'],
                   probe_total_wall_s=time.monotonic()-start, observed_container=observed,
                   NOT_REACHED=sum(r['status'] == 'not_reached' for r in run['results']))
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    write_csv(output / 'all_83_selection_sizes.csv', rows)
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for path in (Path(__file__), Path('src/reliability/verifier/sympy_adapter.py'),
                 Path('src/reliability/agent/isolation.py')):
        manifest['source_sha256'][str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['executor_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


def estimate(root):
    rows = selection_sizes()
    probes = {r: json.loads((root / r / 'summary.json').read_text()) for r in ('django', 'pytest', 'sympy')}
    estimates = []
    for row in rows:
        probe = probes[row['runner']]
        # One observation per runner cannot identify a size-dependent setup
        # model. Treat measured setup as fixed and pass time as proportional
        # to frozen selection size, explicitly marking any capped observation.
        setup = max(0, probe['probe_total_wall_s'] - probe['pass_wall_s'])
        scaled = probe['pass_wall_s'] * row['selected_ids'] / probe['selected_original_slots']
        estimate = setup + min(probe['budget_s'], scaled)
        estimates.append({**row, 'setup_s': setup, 'estimated_pass_s': min(probe['budget_s'], scaled),
                          'estimated_one_tree_wall_s': estimate,
                          'estimated_two_tree_wall_s': 2 * estimate,
                          'runner_probe_censored': probe['timed_out']})
    write_csv(root / 'task_time_estimates.csv', estimates)
    # Deterministic longest-first scheduling gives finite-task estimates at
    # 2/4 containers; the serial sum and ideal division are also reported.
    jobs = [r['estimated_two_tree_wall_s'] for r in estimates]
    serial = sum(jobs)
    schedules = {}
    for concurrency in (1, 2, 4):
        lanes = [0.0] * concurrency
        for job in sorted(jobs, reverse=True):
            lane = min(range(concurrency), key=lambda i: lanes[i])
            lanes[lane] += job
        schedules[str(concurrency)] = {'estimated_wall_s': max(lanes),
                                        'ideal_division_s': serial / concurrency}
    result = {'tasks': 83, 'trees': 2, 'selected_ids_per_tree': sum(r['selected_ids'] for r in rows),
              'budget_s': 1800, 'containers': schedules,
              'runner_probes': {r: {k: p[k] for k in ('instance_id', 'selected_original_slots',
                                                       'pass_wall_s', 'probe_total_wall_s', 'timed_out')}
                                for r, p in probes.items()},
              'censored': any(p['timed_out'] for p in probes.values()),
              'assumptions': ['Base time stands in for patched time; no outcomes compared to labels.',
                              'Measured setup plus selected-ID-proportional pass time, capped at 1800 s.',
                              'Two trees share a task scheduling job; setup charged twice conservatively.',
                              '2/4-container estimates assume no contention, no concurrency is chosen.',
                              'Confirmation cost is additional and unknown: six isolated passes per candidate.',
                              'Largest-task cap hits are censored cost observations, not completed-run rates.'],
              'confirmation_additional_serial_upper_s_per_candidate': 6 * 1800,
              'all_166_pass_caps_serial_s': 83 * 2 * 1800,
              'correctness_labels_read': False, 'concurrency_chosen': None}
    (root / 'estimates.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runner', choices=('django', 'pytest', 'sympy'))
    parser.add_argument('--budget-s', type=float, default=1800)
    args = parser.parse_args()
    if args.runner:
        run_probe(args.output, args.runner, args.budget_s)
    else:
        estimate(args.output)


if __name__ == '__main__':
    main()
