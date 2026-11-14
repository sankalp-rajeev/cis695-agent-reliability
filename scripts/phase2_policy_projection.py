#!/usr/bin/env python3
"""Offline Phase 2 batch/skip counts and completeness-only policy projections.

The summarize stage never reads correctness labels. Run the label join as a
separate post-hoc action only after its label-blind outputs have been written.
No archived source execution, benchmark imports, subprocesses or Docker calls.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

GROUPS = ['cores_CPU', 'missing_dependency', 'platform', 'Python_version', 'other']
CLASSES = ['property', 'non_test_function', 'class_attribute',
           'module_level_helper', 'missing_module', 'other']
EXPECTED_FAILURES = {'XFAIL', 'expected failure'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def batch_class(row):
    """Mutually exclusive classes of batch occurrences, retaining uncertainty.

An existing function rejected by pytest is not thereby a proven non-test
function. Missing class/method paths are not evidence of a missing module.
The callable-signature cases are incompatible with unittest label loading;
this does not assert that they cannot run through their intended framework.
"""
    kinds = row['base_object_kinds'].split('; ')
    if kinds == ['property']:
        return 'property'
    if kinds and all(k == 'helper_callable_for_unittest_loader' for k in kinds):
        ids = json.loads(row['offending_selected_ids'])
        return 'module_level_helper' if all(len(t.split('::')) == 2 for t in ids) else 'non_test_function'
    if kinds == ['class_attribute']:
        return 'class_attribute'
    if kinds == ['nested_helper']:
        return 'non_test_function'
    if 'No module named' in row['diagnostic'] or 'Failed to import test module' in row['diagnostic']:
        return 'missing_module'
    return 'other'


def cpu_only(rows, include_expected_failures):
    relevant = rows if include_expected_failures else [r for r in rows if r['skip_flavor'] not in EXPECTED_FAILURES]
    return bool(relevant) and {r['reason_group'] for r in relevant} == {'cores_CPU'}


def projected_verdict(replay, strict):
    # Strictness constrains PASS; it does not erase a confirmed native FAIL.
    if replay['native_signal'] == 'FAIL':
        return 'RETAINED_NATIVE_FAIL'
    complete = replay['parser_only_complete_skip_strict' if strict else 'parser_only_complete_skip_compatible'] == 'True'
    return 'PROJECTED_PASS' if complete else 'NO_PROJECTED_BINARY_VERDICT'


def summarize(args):
    assert not args.output.exists(), 'Use a fresh output directory'
    hashes = {}

    def read_rows(name):
        path = args.report / name
        hashes[str(path)] = sha(path)
        with path.open(newline='') as stream:
            return list(csv.DictReader(stream))

    batches = [r for r in read_rows('batch_aborts.csv') if r['abort_kind'] != 'runner_start_failure']
    skips = [r for r in read_rows('accepted_skips.csv')
             if r['accepted_for_current_PASS_completeness'] == 'True' and r['call_scope'] == 'initial']
    replay = {r['instance_id']: r for r in read_rows('parser_replay.csv')}
    manifest_path = args.report / 'input_manifest.json'
    hashes[str(manifest_path)] = sha(manifest_path)
    expected = json.loads(manifest_path.read_text())['input_sha256']
    not_run, collateral = set(), set()
    native_signals = Counter()
    for task, replay_row in replay.items():
        path = args.results / 'tasks' / task / 'v2/result.json'
        digest = sha(path)
        assert digest == expected[str(path)], path
        hashes[str(path)] = digest
        native = json.loads(path.read_text())
        assert native['signal'] == replay_row['native_signal']
        native_signals[native['signal']] += 1
        for call in native.get('calls', [])[:2]:
            tree = 'patched' if call['patched'] else 'base'
            for result in call['run'].get('results', []):
                if result['status'] == 'not_run':
                    key = (task, tree, result['test_id'])
                    assert key not in not_run
                    not_run.add(key)
    classified, task_loss = [], Counter()
    for row in batches:
        assert row['scope'] == 'initial'
        ids = json.loads(row['collateral_selected_ids'])
        assert len(ids) == int(row['collateral_not_run_count'])
        keys = {(row['instance_id'], row['tree'], t) for t in ids}
        assert not collateral & keys
        collateral |= keys
        task_loss[row['instance_id']] += len(keys)
        classified.append({**row, 'offending_label_class': batch_class(row)})
    assert len(batches) == 942 and collateral <= not_run
    assert sum(task_loss.values()) == len(collateral) == 3138
    assert len(not_run) == 31179
    class_chart = []
    for kind in CLASSES:
        relevant = [r for r in classified if r['offending_label_class'] == kind]
        labels = [(r['instance_id'], r['tree'], t) for r in relevant for t in json.loads(r['offending_selected_ids'])]
        class_chart.append({'offending_label_class': kind, 'batch_occurrences': len(relevant),
            'tasks': len({r['instance_id'] for r in relevant}), 'candidate_label_occurrences': len(labels),
            'distinct_task_tree_candidate_labels': len(set(labels)),
            'collateral_NOT_RUN_tree_ID_slots': sum(int(r['collateral_not_run_count']) for r in relevant)})
    assert sum(r['batch_occurrences'] for r in class_chart) == 942
    top_five = [{'rank': i, 'instance_id': task, 'collateral_NOT_RUN_tree_ID_slots': count,
                 'base_slots': sum(int(r['collateral_not_run_count']) for r in classified if r['instance_id'] == task and r['tree'] == 'base'),
                 'patched_slots': sum(int(r['collateral_not_run_count']) for r in classified if r['instance_id'] == task and r['tree'] == 'patched')}
                for i, (task, count) in enumerate(task_loss.most_common(5), 1)]
    reason_chart, skip_tasks = [], []
    for group in GROUPS:
        relevant = [r for r in skips if r['reason_group'] == group]
        ordinary = [r for r in relevant if r['skip_flavor'] not in EXPECTED_FAILURES]
        reason_chart.append({'reason_group': group,
            'concrete_tests': len({(r['instance_id'], r['raw_test_id']) for r in relevant}),
            'tasks': len({r['instance_id'] for r in relevant}), 'raw_case_tree_slots': len(relevant),
            'selected_families': len({(r['instance_id'], r['selected_test_id']) for r in relevant}),
            'ordinary_skip_tests': len({(r['instance_id'], r['raw_test_id']) for r in ordinary}),
            'ordinary_skip_tasks': len({r['instance_id'] for r in ordinary}),
            'expected_failure_tests': len({(r['instance_id'], r['raw_test_id']) for r in relevant if r['skip_flavor'] in EXPECTED_FAILURES})})
    for task in sorted({r['instance_id'] for r in skips}):
        relevant = [r for r in skips if r['instance_id'] == task]
        assert replay[task]['native_signal'] == 'PASS'
        skip_tasks.append({'instance_id': task, 'native_verdict': 'PASS',
            'accepted_skip_concrete_tests': len({r['raw_test_id'] for r in relevant}),
            'accepted_skip_raw_case_tree_slots': len(relevant),
            'reason_groups': ';'.join(g for g in GROUPS if any(r['reason_group'] == g for r in relevant)),
            'cpu_only_all_normalized_SKIPPED': cpu_only(relevant, True),
            'cpu_only_ordinary_skips': cpu_only(relevant, False),
            'expected_failure_tests': len({r['raw_test_id'] for r in relevant if r['skip_flavor'] in EXPECTED_FAILURES}),
            'projected_strict_verdict': projected_verdict(replay[task], True),
            'evidence_path': str(args.report / 'accepted_skips.csv')})
    assert len(skip_tasks) == 13
    projection_tasks = []
    for task, row in replay.items():
        projection_tasks.append({'instance_id': task, 'native_verdict': row['native_signal'],
            'current_policy_parser_projection': projected_verdict(row, False),
            'strict_skip_parser_projection': projected_verdict(row, True),
            'evidence_path': str(args.report / 'parser_replay.csv')})
    projection_chart = []
    for name, column in [('current_policy_plus_parser_replay', 'current_policy_parser_projection'),
                         ('parser_replay_plus_strict_skips', 'strict_skip_parser_projection')]:
        counts = Counter(r[column] for r in projection_tasks)
        projection_chart.append({'scope': 'PROJECTION_ONLY', 'policy': name, 'cohort_tasks': len(replay),
            'native_yes_no_reference': native_signals['PASS'] + native_signals['FAIL'],
            'projected_PASS': counts['PROJECTED_PASS'], 'retained_native_FAIL': counts['RETAINED_NATIVE_FAIL'],
            'projected_yes_no': counts['PROJECTED_PASS'] + counts['RETAINED_NATIVE_FAIL'],
            'net_change_vs_native': counts['PROJECTED_PASS'] + counts['RETAINED_NATIVE_FAIL'] - 31})
    metrics = {'scope': 'LABEL_BLIND_STORED_DATA_ONLY', 'load_collection_abort_batches': len(batches),
        'load_collection_abort_tasks': len({r['instance_id'] for r in batches}),
        'collateral_NOT_RUN_tree_ID_slots': len(collateral), 'all_native_initial_NOT_RUN_tree_ID_slots': len(not_run),
        'collateral_share_of_all_native_NOT_RUN': len(collateral) / len(not_run),
        'current_PASS_tasks_accepting_skips': len(skip_tasks),
        'stay_PASS_under_strict_rule': sum(r['projected_strict_verdict'] == 'PROJECTED_PASS' for r in skip_tasks),
        'CPU_only_all_normalized_SKIPPED_tasks': sum(r['cpu_only_all_normalized_SKIPPED'] for r in skip_tasks),
        'CPU_only_ordinary_skip_tasks': sum(r['cpu_only_ordinary_skips'] for r in skip_tasks),
        'native_yes_no': 31, 'current_policy_parser_projected_yes_no': projection_chart[0]['projected_yes_no'],
        'strict_skip_parser_projected_yes_no': projection_chart[1]['projected_yes_no'],
        'native_verdicts_changed': False, 'benchmark_runs': 0, 'Docker_calls': 0}
    args.output.mkdir(parents=True)
    write_csv(args.output / 'batch_offending_label_classes.csv', classified)
    write_csv(args.output / 'accepted_PASS_skip_policy.csv', skip_tasks)
    write_csv(args.output / 'policy_projection_tasks.csv', projection_tasks)
    write_csv(args.output / 'charts/batch_offending_label_classes.csv', class_chart)
    write_csv(args.output / 'charts/batch_collateral_top5.csv', top_five)
    write_csv(args.output / 'charts/batch_collateral_share.csv', [
        {'kind': 'collateral_from_load_collection_abort', 'NOT_RUN_tree_ID_slots': len(collateral), 'share_of_all_native_NOT_RUN': len(collateral) / len(not_run)},
        {'kind': 'remaining_native_NOT_RUN', 'NOT_RUN_tree_ID_slots': len(not_run - collateral), 'share_of_all_native_NOT_RUN': len(not_run - collateral) / len(not_run)}])
    write_csv(args.output / 'charts/accepted_PASS_skip_reasons.csv', reason_chart)
    write_csv(args.output / 'charts/policy_projections.csv', projection_chart)
    write_json(args.output / 'policy_projection_summary.json', metrics)
    md = ['# Phase 2 additions: batch collateral, accepted skips and policy projections', '',
        '**Stored data only. Correctness labels were not read by this stage.**', '',
        '## Batch abort collateral', '',
        f"The 942 load/collection-abort batch occurrences across 32 tasks strand **{len(collateral):,} collateral NOT_RUN tree-ID slots**, or **{len(collateral) / len(not_run):.2%} of {len(not_run):,} native NOT_RUN slots**.", '',
        'The denominator is every native selected-ID NOT_RUN status in initial base/patched calls, including parser-admission gaps; it excludes TIMEOUT, ERROR, missing identities and confirmation calls. Each (task, tree, selected ID) is counted once. The 216 runner-start failures are outside this 942-batch scope. Collateral excludes the offending candidate set, so it is not a prediction of how many tests would pass if the loader were repaired.', '',
        '| Offending-label class | Batch occurrences | Candidate-label occurrences | Collateral tree-ID slots |',
        '|---|---:|---:|---:|']
    md += [f"| {r['offending_label_class']} | {r['batch_occurrences']} | {r['candidate_label_occurrences']} | {r['collateral_NOT_RUN_tree_ID_slots']} |" for r in class_chart]
    md += ['', 'The classes are mutually exclusive batch-occurrence counts summing to 942. Multiple method-name candidates remain explicit in the case table. Non-test function means a method/helper incompatible with standalone unittest label loading; module-level helpers are separated by their selected source path. Ordinary pytest functions that were not collected remain other. A missing selected class/method is not called a missing module. Missing module covers 130 pytest-5787 batches with explicit ModuleNotFoundError for xmlschema. Other consists of 584 remaining pytest not-found batches, 92 GIS environment guards and 26 Matplotlib collection attribute errors; missing selected class/method attributes are not promoted to missing modules.', '',
           '| Top task | Collateral tree-ID slots | Base | Patched |', '|---|---:|---:|---:|']
    md += [f"| {r['instance_id']} | {r['collateral_NOT_RUN_tree_ID_slots']} | {r['base_slots']} | {r['patched_slots']} |" for r in top_five]
    md += ['', '## Accepted skips among the 13 native PASS tasks', '',
           '| Reason group | Concrete tests | Tasks | Case/tree slots | Ordinary skip tests | Expected-failure tests |',
           '|---|---:|---:|---:|---:|---:|']
    md += [f"| {r['reason_group']} | {r['concrete_tests']} | {r['tasks']} | {r['raw_case_tree_slots']} | {r['ordinary_skip_tests']} | {r['expected_failure_tests']} |" for r in reason_chart]
    md += ['', 'A test here is a unique (task, concrete raw test ID), deduplicated across the two trees; selected-family counts also appear in the CSV. Task counts overlap across reason groups. Native SKIPPED normalization includes XFAIL; expected-failure tests are exposed separately under other. Reason quality and source/capture references remain in accepted_skips.csv.', '',
           f"**{metrics['stay_PASS_under_strict_rule']}/13 stay PASS** under the strict rule that every selected SKIPPED observation is missing evidence. **{metrics['CPU_only_all_normalized_SKIPPED_tasks']}/13 are CPU-only across all normalized SKIPPED outcomes**. **{metrics['CPU_only_ordinary_skip_tasks']}/13 have only CPU-conditioned ordinary skips** (pylint-6528 and pylint-7277), but each also has XFAIL outcomes stored as SKIPPED, so changing CPU resources alone does not satisfy this strict rule.", '',
           '## Net projections — not experimental results', '',
           '| Policy projection | Projected PASS | Retained native FAIL | Projected yes/no | Change from native 31/83 |', '|---|---:|---:|---:|---:|']
    md += [f"| {r['policy']} | {r['projected_PASS']} | {r['retained_native_FAIL']} | {r['projected_yes_no']}/83 | {r['net_change_vs_native']:+} |" for r in projection_chart]
    md += ['', 'Current policy plus parser replay retains 25 PASS and 6 FAIL and adds 9 formerly INCOMPLETE plus 2 formerly NOT_AVAILABLE tasks: 31 + 9 + 2 = 42. Strict skip handling retains 12 native PASS, the same 6 confirmed FAIL and 2 newly complete tasks: 12 + 6 + 2 = 20. Equivalently, 42 minus 13 skip-dependent native PASS minus 9 skip-dependent replay gains = 20.', '',
           'These are completeness-only projections, not rerun results or new native verdicts. Confirmed native FAIL remains decisive even with other missing evidence; strictness applies to PASS. No new regression, REGRESSION_ERROR, confirmation, runner repair or CPU-induced execution is inferred. XFAIL follows the existing native SKIPPED normalization. Actual executor implementation and validation may differ from this offline projection.', '',
           '## Evidence and ordering', '',
           'batch_offending_label_classes.csv preserves the capture path:line range, source references, labels, identification confidence and collateral identities for all 942 batches. policy_projection_tasks.csv and accepted_PASS_skip_policy.csv preserve the task-level sets behind every projection. policy_projection_manifest.json hashes the label-blind inputs and analyzer. A later post-hoc label join must record this document’s SHA-256 and must not change these sets or counts.', '']
    (args.output / 'BATCH_AND_POLICY_PROJECTIONS.md').write_text('\n'.join(md))
    write_json(args.output / 'policy_projection_manifest.json', {'analyzer_sha256': sha(Path(__file__)),
        'input_sha256': hashes, 'labels_read': False, 'native_verdicts_changed': False,
        'output_sha256': {str(p.relative_to(args.output)): sha(p) for p in args.output.rglob('*') if p.is_file()}})
    assert all(len(list(csv.reader(p.open()))) <= 15 for p in (args.output / 'charts').glob('*.csv'))
    print(json.dumps(metrics, indent=2))


def posthoc_labels(args):
    """Join labels to a previously written, fixed 13-task diagnostic cohort."""
    assert not args.output.exists(), 'Use a fresh output directory'
    prelabel = args.report / 'BATCH_AND_POLICY_PROJECTIONS.md'
    fixed = args.report / 'accepted_PASS_skip_policy.csv'
    blind_metrics = args.report / 'policy_projection_summary.json'
    blind_manifest = args.report / 'policy_projection_manifest.json'
    # These files must already exist before the correctness-label file is read.
    fixed_sha, prelabel_sha = sha(fixed), sha(prelabel)
    assert json.loads(blind_metrics.read_text())['scope'] == 'LABEL_BLIND_STORED_DATA_ONLY'
    with fixed.open(newline='') as stream:
        cohort = list(csv.DictReader(stream))
    assert len(cohort) == 13
    labels = {}
    with args.posthoc_labels.open(newline='') as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            task = row[args.label_id_column]
            if task in labels:
                assert labels[task][0] == row[args.label_value_column]
            labels[task] = (row[args.label_value_column], line)
    joined = []
    for row in cohort:
        task = row['instance_id']
        label, line = labels[task]
        joined.append({'instance_id': task, 'current_verdict': 'PASS',
            'correctness_label_POST_HOC_ONLY': label,
            'incorrect_label_POST_HOC_ONLY': label == args.incorrect_value,
            'evidence_path': str(args.posthoc_labels), 'line': line})
    count = sum(r['incorrect_label_POST_HOC_ONLY'] for r in joined)
    assert sha(fixed) == fixed_sha and sha(prelabel) == prelabel_sha
    args.output.mkdir(parents=True)
    write_csv(args.output / 'accepted_PASS_labels_POST_HOC_ONLY.csv', joined)
    write_json(args.output / 'accepted_PASS_labels_POST_HOC_ONLY.json', {
        'scope': 'POST-HOC ANALYSIS ONLY', 'cohort_tasks': 13, 'incorrect_labelled_tasks': count,
        'label_distribution': dict(Counter(r['correctness_label_POST_HOC_ONLY'] for r in joined)),
        'prelabel_document_sha256': prelabel_sha, 'prelabel_cohort_sha256': fixed_sha,
        'prelabel_manifest_sha256': sha(blind_manifest),
        'label_input': str(args.posthoc_labels), 'label_input_sha256': sha(args.posthoc_labels),
        'analyzer_sha256': sha(Path(__file__)), 'label_value_column': args.label_value_column,
        'incorrect_value': args.incorrect_value, 'selection_or_parser_changed': False})
    (args.output / 'ACCEPTED_SKIP_LABELS_POST_HOC_ONLY.md').write_text(
        '# Accepted-skip correctness labels — POST-HOC ANALYSIS ONLY\n\n'
        f'**{count}/13** current PASS tasks accepting selected skips are incorrect-labelled.\n\n'
        'The batch, skip and projection outputs were written before reading these labels. '
        'The fixed 13-task cohort and the label-blind document hashes are recorded in '
        'accepted_PASS_labels_POST_HOC_ONLY.json. Labels did not set a selection, parser '
        'decision, reason group or policy projection. This count is not a claim that '
        'executing skipped tests would detect those incorrect patches.\n')
    print(json.dumps({'scope': 'POST-HOC ANALYSIS ONLY', 'incorrect_labelled_tasks': count, 'cohort_tasks': 13}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--results', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--posthoc-labels', type=Path)
    parser.add_argument('--label-id-column', default='instance_id')
    parser.add_argument('--label-value-column', default='label')
    parser.add_argument('--incorrect-value', default='incorrect')
    args = parser.parse_args()
    if args.posthoc_labels:
        posthoc_labels(args)
    else:
        assert args.results, '--results is required for label-blind summarization'
        summarize(args)


if __name__ == '__main__':
    main()
