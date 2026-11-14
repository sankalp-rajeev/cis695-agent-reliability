#!/usr/bin/env python3
"""Mechanical report from frozen harness captures; never runs benchmark tests."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import phase6b_run as harness


def csv_file(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/next_phases/phase6b_results')
    args = parser.parse_args()
    run, output = args.run.resolve(), args.output
    invocation = json.loads((run / 'invocation.json').read_text())
    assert invocation['mode'] == 'run' and not invocation['smoke_only']
    assert not (run / 'HALT.json').exists()
    rows = [harness.completed_task(run / iid) for iid in invocation['task_order']]
    assert len(rows) == 13 and [r['task'] for r in rows] == invocation['task_order']
    result = harness.aggregate(rows)
    assert result == json.loads((run / 'results.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    harness.write(output / 'results.json', result)
    per_task, comparison = [], []
    for row in rows:
        m, info = row['modes']['file'], row['trace_accounting']
        per_task.append({'task': row['task'], 'reference_kept': m['reference_kept_count'],
            'reference_total': m['reference_total'], 'v2_size': row['v2_size'],
            'selected_count': m['selected_count'], 'selected_executed': m['selected_executed'],
            'reduction': m['r'], 'stable_disagreements': len(row['stable_disagreements']),
            'trace_incomplete': info['incomplete_count'], 'executed_base': info['executed_count'],
            'trace_incomplete_fraction': info['incomplete_fraction'],
            'without_usable_trace': len(row['selection']['without_usable_trace']),
            'base_untraced_s': row['base_untraced_s'], 'base_traced_s': row['base_traced_s'],
            'tracing_overhead_T_exploratory': row['T'], 'selected_patched_s': m['patched_s'],
            'sealed_full_patched_s': row['sealed_full_patched_s'], 'total_cost_s': m['total_cost_s'],
            'baseline_cost_s': m['baseline_cost_s'], 'break_even_lhs_s': m['break_even_lhs_s'],
            'break_even_rhs_s': m['break_even_rhs_s'], 'break_even_met': m['break_even_met'],
            'phase4_flaky_exclusions': len(row['phase4_flaky_excluded']),
            'selected_patched_outcome_differences': len(m['sealed_outcome_disagreements'])})
        for selector in ('file', 'function', 'test_window_file', 'test_window_function'):
            secondary = selector.startswith('test_window_')
            mode = selector.removeprefix('test_window_')
            selection = row['selection']['secondary_test_window_exploratory'] if secondary else row['selection']
            refs = set(m['reference_kept']) | set(m['reference_missed'])
            comparison.append({'task': row['task'], 'selector': selector,
                'reading': 'preregistered' if selector == 'file' else 'exploratory',
                'selected_count': len(selection[mode]), 'v2_size': row['v2_size'],
                'selected_share': len(selection[mode]) / row['v2_size'],
                'reference_kept': len(refs & set(selection[mode])),
                'selected_executed': '' if secondary else row['modes'][mode]['selected_executed'],
                'reduction_by_executed_count': '' if secondary else row['modes'][mode]['r'],
                'patched_s': '' if secondary else row['modes'][mode]['patched_s']})
    csv_file(output / 'per_task.csv', per_task)
    csv_file(output / 'selector_comparison.csv', comparison)
    p = result['pooled']['file']
    lines = [f"{result['verdict']}: file-level selection kept {p['reference_kept_count']}/12 reference regressions, "
             f"with a median per-task reduction of {p['median_task_reduction']:.2%} and "
             f"{p['stable_disagreement_count']} traced/untraced disagreements on Phase-4-stable tests.",
             f"{'ADOPT' if result['adopt'] else 'DO NOT ADOPT'}: total execution cost was "
             f"{p['total_cost_s']:.3f}s versus {p['baseline_cost_s']:.3f}s baseline; median-task costs were "
             f"{p['median_task_total_cost_s']:.3f}s versus {p['median_task_baseline_cost_s']:.3f}s.", '',
             'All 13 pre-registered tasks completed in eval_set.json order. No task or test was excluded to pass a gate.', '',
             '| Task | Reference kept | Selected / V2 | Executed | Reduction | Incomplete / executed base | Stable differences | Cost / baseline (s) |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in per_task:
        lines.append(f"| {r['task']} | {r['reference_kept']}/{r['reference_total']} | "
            f"{r['selected_count']}/{r['v2_size']} | {r['selected_executed']} | {r['reduction']:.2%} | "
            f"{r['trace_incomplete']}/{r['executed_base']} | {r['stable_disagreements']} | "
            f"{r['total_cost_s']:.3f} / {r['baseline_cost_s']:.3f} |")
    lines += ['', f"Pooled selected/executed: {p['selected_count']}/{p['selected_executed']} of {p['v2_size']} V2 IDs. "
              f"Pooled reduction: {p['pooled_reduction']:.2%}.",
              f"Reusable-history cost: {p['reusable_history_cost_s']:.3f}s versus "
              f"{p['reusable_history_baseline_s']:.3f}s for the sealed full patched passes.",
              f"TRACE_INCOMPLETE: {p['trace_incomplete_count']}; without usable traces: {p['without_usable_trace_count']}; "
              f"patch-only absent definitions/files: {p['patch_only_absent_count']}.", '',
              'Break-even uses the frozen inequality `(T - 1) * B < r * P`. Both sides and the strict comparison appear per task in per_task.csv. '
              'Costs sum all module-process end events, including retries and fallback events; collection and setup costs are excluded.', '',
              'Limits: these results cover this frozen set and these Phase 4 images. Shared initialization can touch a changed file and retain every test in scope; '
              'this is the primary definition. Missing, skipped, errored and unreached traces are retained. Reduction uses actual executed selected IDs over the frozen V2 list size, '
              'so retained skipped IDs contribute no execution. The patched baseline is sealed Phase 4 data, not a simultaneous full patched rerun.', '',
              'Function-level selection, test-window-only selection and all time ratios are exploratory. '
              'They do not alter the primary verdict or adoption rule. No patched pass was run for the test-window-only selection; its table reports selection counts only.', '',
              f"Exploratory pooled tracing time ratio T: {p['tracing_overhead_T']:.3f}. "
              f"Selected patched/Phase 4 outcome differences: {p['selected_patched_disagreement_count']}; these are reported separately from the preregistered traced/untraced criterion.", '',
              'Phase 4 FLAKY exclusions from the stable-outcome criterion:']
    flaky = [(r['task'], tid) for r in rows for tid in r['phase4_flaky_excluded']]
    lines += [f'- {task}: `{tid}`' for task, tid in flaky] or ['None.']
    lines += ['', 'Unspecified cases: none; no incomplete evaluation task was omitted.', '',
              f"Run: `{run}`. Frozen harness: `{invocation['freeze_tag']}` at `{invocation['HEAD']}`. "
              'Independent verification is documented in verification.md; this report must not be sealed before that check passes.', '']
    (output / 'results.md').write_text('\n'.join(lines))
    (output / 'verification.md').write_text('Independent verification pending. Do not seal.\n')
    print(json.dumps({'verdict': result['verdict'], 'adopt': result['adopt'], 'output': str(output)}))


if __name__ == '__main__':
    main()
