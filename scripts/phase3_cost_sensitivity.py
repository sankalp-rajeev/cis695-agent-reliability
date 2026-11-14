#!/usr/bin/env python3
"""Stage-aware timing sensitivity and module-sized confirmation cost proxies."""

import argparse
import json
import statistics
from pathlib import Path

from phase3_cost_probes import selection_sizes, write_csv


def scheduling(rows, field):
    result = {}
    for concurrency in (1, 2, 4):
        lanes = [0.0] * concurrency
        for wall in sorted((r[field] for r in rows), reverse=True):
            index = min(range(concurrency), key=lambda i: lanes[i])
            lanes[index] += wall
        result[str(concurrency)] = max(lanes)
    return result


def quantile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def main(root):
    sizes = selection_sizes()
    models = {}
    for runner in ('django', 'pytest', 'sympy'):
        folder = root / runner
        summary = json.loads((folder / 'summary.json').read_text())
        run = json.loads((folder / 'base_run.json').read_text())
        collection = [g['duration_s'] for g in run['validation_summary']['groups']]
        execution = [e['duration_s'] for e in run['events'] if e['event'] == 'end']
        selected = next(r for r in sizes if r['task'] == summary['instance_id'])
        fixed = max(0, summary['pass_wall_s'] - sum(collection) - sum(execution))
        setup = max(0, summary['probe_total_wall_s'] - summary['pass_wall_s'])
        median_proxy = fixed + statistics.median(collection) + statistics.median(execution)
        p95_proxy = fixed + quantile(collection, .95) + quantile(execution, .95)
        models[runner] = {'task': summary['instance_id'], 'selected_ids': selected['selected_ids'],
                          'selected_modules': selected['modules'], 'fixed_pass_s': fixed,
                          'setup_s': setup, 'collection_s': sum(collection),
                          'execution_s': sum(execution), 'capped': summary['timed_out'],
                          'six_confirmation_module_median_proxy_s': 6 * min(1800, median_proxy),
                          'six_confirmation_module_p95_proxy_s': 6 * min(1800, p95_proxy)}
        assert abs(setup + fixed + sum(collection) + sum(execution)
                   - summary['probe_total_wall_s']) < 0.01
    rows = []
    for size in sizes:
        model = models[size['runner']]
        passing = (model['fixed_pass_s']
                   + model['collection_s'] * size['modules'] / model['selected_modules']
                   + model['execution_s'] * size['selected_ids'] / model['selected_ids']) if size['selected_ids'] else 0
        rows.append({**size, 'stage_aware_one_tree_wall_s': model['setup_s'] + min(1800, passing),
                     'stage_aware_two_tree_wall_s': 2 * (model['setup_s'] + min(1800, passing))})
    write_csv(root / 'stage_aware_task_estimates.csv', rows)
    assert len(rows) == 83 and sum(r['selected_ids'] for r in rows) == 57682
    result = {'label': 'Secondary stage-aware cost sensitivity; no concurrency selected',
              'models': models, 'containers_wall_s': scheduling(rows, 'stage_aware_two_tree_wall_s'),
              'method': 'Measured fixed pass overhead per task + native collection scaled by module count + execution scaled by original selected-ID count; each pass capped at 1800 s; setup charged twice.',
              'confirmation_note': 'Module-sized median/p95 proxies, not isolated-confirmation measurements or confidence bounds. Actual cost depends on future paired failures; each candidate requires six isolated passes. Six 1800-second budgets total 10800 seconds, excluding cleanup.',
              'correctness_labels_read': False, 'concurrency_chosen': None}
    (root / 'stage_aware_estimates.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
