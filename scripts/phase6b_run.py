#!/usr/bin/env python3
"""Phase 6b repaired-executor harness. Smoke never launches evaluation tasks.

`run` requires clean HEAD at the annotated harness freeze. Infrastructure halts
publish an incident only, never partial experiment metrics. Raw captures and
interned gzip traces live exclusively in a new ignored runs/ directory.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
import statistics
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import phase4_launch as p4
import phase5_replay as replay
from reliability.verifier.container import ContainerTestExecutor
from reliability.verifier.patch import parse_patch
from reliability.verifier.pre_install import load_specs
from reliability.verifier.regression import run_to_dict
from reliability.verifier.run_health import explicit_executor_failures
from reliability.verifier.selection import TestRunner
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive

ROOT = Path(__file__).resolve().parents[1]
TRACE_CODE = ROOT / 'tools/phase6b_trace'
sys.path.insert(0, str(TRACE_CODE))
from phase6b_selection import build_selection, changed_targets, load_traces

EVAL = ROOT / 'reports/next_phases/phase6b_plan/eval_set.json'
EVAL_SHA = '368c8650739746b53638c35682a876134c14e76d80def8511bcb76b3054f4920'
FROZEN_TAG = 'phase6b-harness-frozen'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    p4.write(path, value)


def statuses(run):
    return {r.test_id: r.status.value for r in run.results}


def execution_s(run):
    return math.fsum(e['duration_s'] for e in run.events if e['event'] == 'end')


def command_prefix(argv, runner):
    if runner == 'pytest':
        prefix = argv[:7]
        require(prefix == ['python', '-m', 'pytest', '-p', 'no:cacheprovider', '-v', '--'],
                'STOP: frozen pytest command cannot be traced unchanged: ' + repr(argv))
        return prefix
    require(runner == 'django' and argv[:3] == ['python', 'tests/runtests.py', '--verbosity=2'],
            'STOP: unsupported frozen runner command')
    if '--parallel' in argv:
        position = argv.index('--parallel')
        require(position == 3 and argv[position + 1].isdigit(),
                'Unsupported frozen parallel command')
        return argv[:5]
    require(not any(a.startswith('--parallel') for a in argv), 'STOP: unsupported parallel command')
    return argv[:3]


class TraceContainer(p4.FrozenContainer):
    trace_output = None
    trace_token = None
    trace_runner = None

    def run_args(self):
        args = super().run_args()
        position = args.index(self.image)
        args[position:position] = [
            '--mount', 'type=bind,src=' + str(TRACE_CODE.resolve()) + ',dst=/phase6b_tracer,readonly',
            '--mount', 'type=bind,src=' + str(self.trace_output.resolve()) + ',dst=/phase6b_output',
        ]
        return args

    def exec_raw(self, command, timeout_s):
        if self.trace_token and command.startswith('python /tmp/verifier_driver.py '):
            # Only the execution driver and its children receive instrumentation.
            # Its source, child argv, ID list, shell activation and parser remain
            # the repaired Phase 4 path. Collection/startup/probes stay untraced.
            env = ('env PYTHONPATH=/phase6b_tracer${PYTHONPATH:+:$PYTHONPATH} '
                   'PHASE6B_TRACE=1 PHASE6B_ROOT=/testbed '
                   'PHASE6B_TRACE_OUT=/phase6b_output/' + shlex.quote(self.trace_token)
                   + ' PHASE6B_RUNNER=' + shlex.quote(self.trace_runner) + ' ')
            if self.trace_runner == 'pytest':
                env += 'PYTEST_PLUGINS=phase6b_pytest${PYTEST_PLUGINS:+,$PYTEST_PLUGINS} '
            command = env + command
        return super().exec_raw(command, timeout_s)


class Inputs:
    def __init__(self):
        entries, self.manifest = replay.verify_manifest()
        self.inputs = replay.Inputs(entries)
        self.protocol = self.inputs.pinned(p4.DEFAULT_FROZEN / 'protocol.json',
            p4.FROZEN_PROTOCOL_SHA256, {'task_artifact_sha256': True})
        metadata = self.inputs.pinned(p4.DEFAULT_FROZEN / 'tasks.json',
            p4.FROZEN_TASKS_SHA256, {'*': {k: True for k in (
                'instance_id', 'repo', 'runner', 'image_binding', 'patch_path', 'selections')}})
        self.metadata = {r['instance_id']: r for r in metadata}
        plan = self.inputs.run('plan.json', {'task_specs': True})
        self.specs = {r['instance_id']: r for r in plan['task_specs']}
        self.evaluation = self.inputs.pinned(EVAL, EVAL_SHA, {'tasks': True})['tasks']
        self.eval_ids = {r['instance_id'] for r in self.evaluation}
        costs_path = ROOT / 'reports/next_phases/phase5_replay/per_task_costs.csv'
        p4.require_hash(costs_path, '86c97ee2e0c64aebd10629e58c8bce3d739a803350768f8573245c8bd9f7ca97')
        self.costs = {r['task']: r for r in csv.DictReader(costs_path.open())}
        self.preinstall = None

    def sealed(self, iid, tree):
        return self.inputs.run('tasks/' + iid + '/' + tree + '.json', replay.RUN_SCHEMA)

    def prefixes(self, iid):
        raw = self.inputs.run('tasks/' + iid + '/patched.json', {
            'events': {'*': {'event': True, 'argv': True}}})
        runner = self.metadata[iid]['runner']['name']
        prefixes = {tuple(command_prefix(e['argv'], runner)) for e in raw['events']
                    if e['event'] == 'start'}
        require(len(prefixes) == 1, 'STOP: absent/inconsistent Phase 4 commands: ' + iid)
        return next(iter(prefixes))

    def smoke_ids(self):
        chosen, rejected = [], []
        for runner in ('pytest', 'django'):
            pool = sorted((iid for iid, meta in self.metadata.items()
                if iid not in self.eval_ids and meta['runner']['name'] == runner
                and int(self.costs[iid]['v2_count']) > 0),
                key=lambda iid: (int(self.costs[iid]['v2_count']), iid))
            for iid in pool:
                bad = {r['status'] for tree in ('base', 'patched')
                       for r in self.sealed(iid, tree)['results']} & {
                           'invalid_id', 'collection_error', 'not_run', 'not_reached', 'timeout', 'runner_unavailable'}
                if bad:
                    rejected.append({'task': iid, 'reason': sorted(bad)})
                    continue
                chosen.append(iid)
                break
            else:
                raise ValueError('No executable non-evaluation smoke task: ' + runner)
        # The third smoke must prove the actual parallel runner shape, using
        # captured database-clone evidence rather than the "up to N" banner.
        pool = sorted((iid for iid, meta in self.metadata.items()
            if iid not in self.eval_ids and meta['runner']['name'] == 'django'
            and int(self.costs[iid]['v2_count']) > 0),
            key=lambda iid: (int(self.costs[iid]['v2_count']), iid))
        for iid in pool:
            evidence = self.inputs.run('tasks/' + iid + '/base.json', {'evidence_files': True})
            capture = Path(evidence['evidence_files']['runner.raw'])
            relative = capture.relative_to(replay.RUN)
            p4.require_hash(capture, self.inputs.entries[relative.as_posix()])
            text = capture.read_text(errors='replace')
            if 'Cloning test database' in text:
                chosen.append(iid)
                break
        else:
            raise ValueError('No non-evaluation parallel Django smoke task')
        require(not set(chosen) & self.eval_ids, 'Smoke/evaluation overlap')
        return chosen, rejected

    def task(self, iid):
        meta, original = self.metadata[iid], self.specs[iid]
        selection = self.inputs.selection(meta, 'v2', self.protocol)
        tests = tuple(selection['tests'])
        require(original['selected_ids'] == len(tests), 'Frozen V2 list size changed')
        selection_path = p4.confined(p4.DEFAULT_FROZEN, meta['selections']['v2'])
        p4.require_hash(selection_path, original['selection_sha256'])
        patch = p4.confined(p4.DEFAULT_FROZEN, meta['patch_path'])
        p4.require_hash(patch, original['patch_sha256'])
        p4.require_hash(patch, self.protocol['task_artifact_sha256'][meta['patch_path']])
        if self.preinstall is None:
            self.preinstall = load_specs(ROOT / 'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl',
                                         p4.PROVENANCE / 'dataset_projection.json')
        source = BaseSourceSpec(original['base_commit'], Path(original['archive_path']),
                               original['archive_sha256'], self.preinstall[iid])
        require(source.pre_install.resolve() == original['pre_install'], 'Phase 4 pre_install provenance changed')
        require(original['image_id'] == meta['image_binding']['host_image_id'], 'Phase 4 image identity changed')
        runner = TestRunner(**meta['runner'])
        if runner.name == 'django':
            runner = replace(runner, django_parallel_one=original['django_parallel_one'])
        prefix = self.prefixes(iid)
        expected = ('python', 'tests/runtests.py', '--verbosity=2', '--parallel', '1') if (
            runner.name == 'django' and runner.django_parallel_one) else (
            ('python', 'tests/runtests.py', '--verbosity=2') if runner.name == 'django' else
            ('python', '-m', 'pytest', '-p', 'no:cacheprovider', '-v', '--'))
        require(prefix == expected, 'STOP: Phase 4 executor command differs from the sealed command')
        return p4.TaskSpec(iid, original['image_id'], patch, selection_path, tests, runner, source)


def capture(executor, spec, folder, name, tests, *, patched=False, traced=False):
    executor.container.trace_token = name if traced else None
    trace_dir = executor.container.trace_output / name
    if traced:
        trace_dir.mkdir(exist_ok=False)
    result = executor.run(tuple(tests), patched=patched, timeout_s=p4.PASS_BUDGET_S)
    failures = explicit_executor_failures(result)
    require(not failures, 'Infrastructure halt: ' + repr(failures))
    require(not result.timed_out, 'Infrastructure halt: pass budget exhausted')
    expected = (['python', 'tests/runtests.py', '--verbosity=2'] +
                (['--parallel', '1'] if spec.runner.django_parallel_one else [])) if spec.runner.name == 'django' else [
                    'python', '-m', 'pytest', '-p', 'no:cacheprovider', '-v', '--']
    if tests:
        # No tracing CLI flags or runner substitutions are allowed, even for
        # selected patched passes. Native IDs may be a subset of the V2 list.
        for event in result.events:
            if event['event'] == 'start':
                require(command_prefix(event['argv'], spec.runner.name) == expected, 'Runner argv changed within pass')
    write(folder / (name + '.json'), run_to_dict(result, inline_raw=False))
    return result, trace_dir


def selection_for(spec, run, directory, targets):
    codes, flags, info = load_traces(directory, run, spec.runner.name)
    require(info['process_count'] > 0 and info['trace_nonempty'], 'Infrastructure halt: missing/empty attributed trace')
    return build_selection(spec.tests, statuses(run), codes, flags, targets), info


def check_parallel_smoke(info, parallel_smoke):
    if parallel_smoke:
        require(info['workers_with_tests'] > 1, 'Parallel smoke did not observe multiple test workers')
    require(info['incomplete_fraction'] <= .05,
            'Smoke gate: more than 5% of executed tests TRACE_INCOMPLETE')


def one_task(inputs, iid, folder, *, smoke=False, parallel_smoke=False):
    spec = inputs.task(iid)
    archive = SourceArchive(spec.source)
    patch_text = spec.patch_path.read_text()
    paths = {change.old_path or change.path for change in parse_patch(patch_text)}
    targets = changed_targets(patch_text, archive.read_many(paths))
    folder.mkdir(parents=True, exist_ok=False)
    trace_root = folder / 'traces'
    trace_root.mkdir()
    container = TraceContainer(iid, patch_text, image=spec.image_id, experiment_id='phase6b_smoke' if smoke else 'phase6b',
                               source_spec=spec.source, source_receipt_path=folder / 'source_receipt.json')
    container.trace_output = trace_root
    container.trace_runner = spec.runner.name
    with container:
        require(container.source_integrity.get('status') == 'VERIFIED', 'Pristine source not verified')
        executor = ContainerTestExecutor(container, runner=spec.runner, evidence_dir=folder / 'raw')
        untraced, _ = capture(executor, spec, folder, 'base_untraced', spec.tests)
        traced, trace_path = capture(executor, spec, folder, 'base_traced', spec.tests, traced=True)
        selected, trace_info = selection_for(spec, traced, trace_path, targets)
        stable = inputs.inputs.run('tasks/' + iid + '/result.json', {
            'policies': {'C_invalid_excluded': {'outcomes': True}}})['policies']['C_invalid_excluded']['outcomes']
        disagreement = [t for t in spec.tests if statuses(untraced).get(t) != statuses(traced).get(t)]
        stable_disagreement = [t for t in disagreement if stable.get(t) != 'FLAKY']
        if smoke:
            require(not disagreement, 'Smoke gate: traced/untraced outcomes differ')
            repeated, repeated_path = capture(executor, spec, folder, 'base_traced_repeat', spec.tests, traced=True)
            second, repeated_info = selection_for(spec, repeated, repeated_path, targets)
            require(statuses(repeated) == statuses(traced), 'Smoke gate: repeated outcomes differ')
            require(second == selected, 'Smoke gate: repeated selection differs')
            check_parallel_smoke(trace_info, parallel_smoke)
            check_parallel_smoke(repeated_info, parallel_smoke)
        patched_runs = {}
        for mode in ('file', 'function'):
            patched_runs[mode], _ = capture(executor, spec, folder, 'patched_' + mode,
                                            selected[mode], patched=True)
    if smoke:
        return {'task': iid, 'v2_count': len(spec.tests), 'outcomes_match': True,
                'trace_nonempty': True, 'selection_repeat_identical': True,
                'trace_accounting': trace_info,
                'time_ratio_information_only': execution_s(traced) / execution_s(untraced),
                'smoke_only': True, 'used_in_experiment_numbers': False}
    B, traced_B = execution_s(untraced), execution_s(traced)
    P = float(inputs.costs[iid]['patched_execution_s'])
    sealed = {r['test_id']: r['status'] for r in inputs.sealed(iid, 'patched')['results']}
    refs = next(t['reference_ids'] for t in inputs.evaluation if t['instance_id'] == iid)
    metrics = {'task': iid, 'v2_size': len(spec.tests), 'base_untraced_s': B,
               'base_traced_s': traced_B, 'sealed_full_patched_s': P,
               'T': traced_B / B if B else None, 'selection': selected,
               'trace_accounting': trace_info,
               'disagreements': disagreement, 'stable_disagreements': stable_disagreement,
               'phase4_flaky_excluded': sorted(t for t in spec.tests if stable.get(t) == 'FLAKY'),
               'blind_spot_counts': {'TRACE_INCOMPLETE': len(selected['trace_incomplete']),
                                    'without_usable_trace': len(selected['without_usable_trace']),
                                    'patch_only_absent': len(targets['absent_from_base'])},
               'targets': targets, 'modes': {}}
    for mode, result in patched_runs.items():
        observed = statuses(result)
        executed = sum(status in ('passed', 'failed', 'error', 'crash', 'xfail', 'xpass')
                       for status in observed.values())
        cost = execution_s(result)
        metrics['modes'][mode] = {
            'selected_count': len(selected[mode]), 'selected_executed': executed,
            'selected_share': len(selected[mode]) / len(spec.tests),
            'r': 1 - executed / len(spec.tests), 'reference_kept': sorted(set(refs) & set(selected[mode])),
            'reference_missed': sorted(set(refs) - set(selected[mode])),
            'reference_kept_count': len(set(refs) & set(selected[mode])), 'reference_total': len(refs),
            'recall': len(set(refs) & set(selected[mode])) / len(refs) if refs else None,
            'patched_s': cost, 'total_cost_s': traced_B + cost, 'baseline_cost_s': B + P,
            'reusable_history_cost_s': cost, 'reusable_history_baseline_s': P,
            'sealed_outcome_disagreements': [t for t in selected[mode] if observed.get(t) != sealed.get(t)],
            'break_even_lhs_s': traced_B - B, 'break_even_rhs_s': (1 - executed / len(spec.tests)) * P,
            'break_even_met': traced_B - B < (1 - executed / len(spec.tests)) * P,
        }
    return metrics


def aggregate(rows):
    result = {'tasks': rows, 'pooled': {}}
    disagreements = sum(len(row['stable_disagreements']) for row in rows)
    for mode in ('file', 'function'):
        data = [row['modes'][mode] for row in rows]
        kept = sum(len(r['reference_kept']) for r in data)
        median_r = statistics.median(r['r'] for r in data)
        total = math.fsum(r['total_cost_s'] for r in data)
        baseline = math.fsum(r['baseline_cost_s'] for r in data)
        success = kept == 12 and median_r >= .5 and disagreements == 0
        median_cost_below = statistics.median(r['total_cost_s'] for r in data) < statistics.median(r['baseline_cost_s'] for r in data)
        result['pooled'][mode] = {
            'reference_kept_count': kept, 'reference_total': 12, 'recall': kept / 12,
            'median_task_reduction': median_r,
            'selected_count': sum(r['selected_count'] for r in data),
            'selected_share': sum(r['selected_count'] for r in data) / sum(r['v2_size'] for r in rows),
            'selected_executed': sum(r['selected_executed'] for r in data),
            'v2_size': sum(r['v2_size'] for r in rows),
            'pooled_reduction': 1 - sum(r['selected_executed'] for r in data) / sum(r['v2_size'] for r in rows),
            'tracing_overhead_T': math.fsum(r['base_traced_s'] for r in rows) / math.fsum(r['base_untraced_s'] for r in rows),
            'total_cost_s': total, 'baseline_cost_s': baseline,
            'median_task_total_cost_s': statistics.median(r['total_cost_s'] for r in data),
            'median_task_baseline_cost_s': statistics.median(r['baseline_cost_s'] for r in data),
            'pooled_total_cost_below_baseline': total < baseline,
            'median_task_cost_below_baseline': median_cost_below,
            'reusable_history_cost_s': math.fsum(r['patched_s'] for r in data),
            'reusable_history_baseline_s': math.fsum(r['sealed_full_patched_s'] for r in rows),
            'stable_disagreement_count': disagreements,
            'selected_patched_disagreement_count': sum(len(r.get('sealed_outcome_disagreements', [])) for r in data),
            'trace_incomplete_count': sum(len(r['selection']['trace_incomplete']) for r in rows),
            'without_usable_trace_count': sum(len(r['selection']['without_usable_trace']) for r in rows),
            'patch_only_absent_count': sum(len(r['targets']['absent_from_base']) for r in rows),
            'success': success, 'failure': kept < 12 or disagreements > 0,
            'adopt': success and total < baseline and median_cost_below,
        }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'run'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze-tag')
    args = parser.parse_args(argv)
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / 'runs').resolve()), 'Outputs/traces must stay in ignored runs/')
    require(not output.exists(), 'Never overwrite or resume an existing output directory')
    if args.command == 'run':
        require(args.freeze_tag == FROZEN_TAG, 'Run requires the annotated harness freeze tag')
        head = p4.require_frozen_head(args.freeze_tag)
        tag_hash = subprocess.check_output(['git', 'rev-parse', 'refs/tags/' + args.freeze_tag], text=True).strip()
    else:
        require('smoke' in output.name.lower(), 'Smoke output directory must be explicitly marked smoke')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        tag_hash = None
    inputs = Inputs()
    # Inspect every evaluation command without starting any evaluation task.
    for iid in sorted(inputs.eval_ids):
        inputs.prefixes(iid)
    ids, rejected = inputs.smoke_ids() if args.command == 'smoke' else (sorted(inputs.eval_ids), [])
    require(args.command != 'smoke' or not set(ids) & inputs.eval_ids, 'Refuse evaluation task in smoke')
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'invocation.json', {'mode': args.command, 'HEAD': head, 'freeze_tag': args.freeze_tag,
        'tag_hash': tag_hash, 'task_order': ids, 'smoke_only': args.command == 'smoke', 'rejected_smoke': rejected,
        'manifest': inputs.manifest, 'cpu_shares': 2048, 'network': 'none'})
    rows = []
    try:
        for iid in ids:
            folder = output / iid
            rows.append(one_task(inputs, iid, folder, smoke=args.command == 'smoke',
                                 parallel_smoke=args.command == 'smoke' and iid == ids[2]))
        write(output / ('smoke_gates.json' if args.command == 'smoke' else 'results.json'),
              {'smoke_only': True, 'gates': rows} if args.command == 'smoke' else aggregate(rows))
        print(json.dumps({'mode': args.command, 'tasks': ids, 'gates_passed': True, 'output': str(output)}))
    except BaseException as exc:
        write(output / 'HALT.json', {'task': ids[len(rows)] if len(rows) < len(ids) else None,
                                    'reason': str(exc), 'metrics_published': False,
                                    'instruction': 'Fix infrastructure, amend plan, restart evaluation from task 1; never resume'})
        raise


if __name__ == '__main__':
    main()
