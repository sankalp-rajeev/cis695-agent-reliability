"""Guarded execution primitives moved from the sealed Phase 4 launcher."""
from dataclasses import asdict
from reliability.verifier.accounting import ADMITTED_STATUSES
from reliability.verifier.container import TaskContainer
from reliability.verifier.regression import run_to_dict
from reliability.verifier.run_health import RunHealthError, append_health, health_for_run, explicit_executor_failures
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import write
from reliability.verifier.regression import RegressionConfig, run_regression
from reliability.verifier.generic_health import check_generic_pair

DEFAULT_V2_ACCOUNTING = 'S_invalid_excluded'
V2_ACCOUNTINGS = frozenset(
    f'{policy}_invalid_{handling}' for policy in 'CSP' for handling in ('excluded', 'missing')
)

class ReplayMismatch(ValueError):
    """A policy requested execution outside its captured call sequence."""

class FrozenContainer(TaskContainer):
    def run_args(self):
        args = super().run_args()
        args.insert(2, '--pull=never')
        return args

class Calls:
    """Capture both initial trees, then confirm once; policy replays do no I/O."""
    def __init__(self, executor, task=None, health_path=None, g1_reference=None):
        self.executor = executor
        self.task = task
        self.health_path = health_path
        self.g1_reference = g1_reference or {}
        self.calls = []

    def run(self, tests, *, patched, timeout_s):
        confirmation = len(self.calls) >= 2 and self.task is not None
        try:
            result = self.executor.run(tests, patched=patched, timeout_s=timeout_s)
        except SourceIntegrityError:
            raise
        except Exception as exc:
            if not confirmation:
                raise
            record = {'task': self.task, 'scope': 'confirmation', 'halt': True,
                      'halt_reasons': ['confirmation stage error: '+repr(exc)],
                      'G2': 'BLOCKED_UPSTREAM', 'G3': 'BLOCKED_UPSTREAM'}
            append_health(self.health_path, record)
            raise RunHealthError(record) from exc
        failures = explicit_executor_failures(result)
        if failures:
            record = {'task': self.task, 'scope': 'confirmation' if confirmation else 'initial',
                      'tree': 'patched' if patched else 'base', 'halt': True,
                      'halt_reasons': failures, 'capture': run_to_dict(result, inline_raw=False)}
            append_health(self.health_path, record)
            raise RunHealthError(record)
        if confirmation:
            initial = self.calls[int(patched)][3]
            tree='patched' if patched else 'base'
            evidence=self.g1_reference.get(tree,{})
            g1_ids=evidence.get('g1_collected_ids',()) if isinstance(evidence,dict) else ()
            reference = confirmation_reference(initial, tests, g1_ids)
            record = health_for_run(self.task, 'patched' if patched else 'base', result, reference, confirmation=True)
            modules = {t.split('::', 1)[0] for t in tests}
            opposite = self.calls[int(not patched)][3]
            pair_reasons = check_generic_pair({tree: record['stages'],
                'base' if patched else 'patched': [dict(s) for s in opposite.stage_health if s.get('module') in modules]})
            if pair_reasons:
                record['halt'] = True
                record['halt_reasons'].extend(pair_reasons)
            record['scope'] = 'confirmation'
            record['call'] = len(self.calls) + 1
            append_health(self.health_path, record)
            if record['halt']:
                raise RunHealthError(record)
        self.calls.append((tests, patched, timeout_s, result))
        return result

def confirmation_reference(initial, tests, g1_ids=()):
    receipts = {r['selected_id']: r for r in initial.validation}
    admitted = {r.test_id for r in initial.results if r.status in ADMITTED_STATUSES
                and (not receipts or (receipts.get(r.test_id, {}).get('admitted')
                     and not receipts.get(r.test_id, {}).get('collector_fallback')))}
    concrete = {r.test_id for r in initial.execution_results if r.status in ADMITTED_STATUSES
                and set(initial.execution_id_map.get(r.test_id, ())) & admitted}
    blocked = {r.test_id for r in (*initial.results, *initial.execution_results)
               if r.status.value in ('passed', 'failed', 'error', 'crash')}
    return {'admitted_ids': sorted((admitted | concrete) & set(tests)),
            'module_skip_blocked_ids': sorted(blocked & set(tests)),
            'drift_reference_ids': sorted(blocked & set(tests)),
            'g1_collected_ids': sorted(t for t in tests if t in g1_ids or set(initial.execution_id_map.get(t,())) & set(g1_ids)), 'reference_source': 'INITIAL_ADMITTED_SUBSET'}

class Replay:
    def __init__(self, calls, fallback=None):
        self.calls = iter(tuple(calls))
        self.fallback = fallback

    def run(self, tests, *, patched, timeout_s):
        entry = next(self.calls, None)
        if entry is None:
            if self.fallback is None:
                raise ReplayMismatch('Policy replay requested unrecorded execution')
            return self.fallback.run(tests, patched=patched, timeout_s=timeout_s)
        if entry[:3] != (tests, patched, timeout_s):
            raise ReplayMismatch('Policy replay request differs from captured execution')
        return entry[3]

def fallback_results(report):
    """Record selection origin for both selected and concrete outcome IDs."""
    selection = report.selection
    fallback = set(selection.fallback_tests) if selection is not None else set()
    owners = {test: {test} for test in selection.tests} if selection is not None else {}
    for run in (report.baseline, report.patched, *report.confirmations):
        if run is None:
            continue
        for mapping in (run.raw_id_map, run.execution_id_map):
            for test, selected in mapping.items():
                owners.setdefault(test, set()).update(selected)
        for raw, execution in run.raw_execution_map.items():
            owners.setdefault(execution, set()).update(run.raw_id_map.get(raw, ()))
    return {
        test: {'outcome': outcome.value, 'from_fallback': bool(owners.get(test))
               and owners[test] <= fallback}
        for test, outcome in report.outcomes.items()
    }


def report_json(report, *, include_fallback=False):
    data = asdict(report)
    if report.selection is not None:
        data['selection'] = report.selection.to_dict(include_fallback=include_fallback)
        if include_fallback:
            data.update(report.selection.fallback_metadata(), test_results=fallback_results(report))
    for field in ('baseline', 'patched'):
        run = getattr(report, field)
        data[field] = run_to_dict(run, inline_raw=False) if run is not None else None
    data['confirmations'] = [run_to_dict(r, inline_raw=False) for r in report.confirmations]
    return data


#: Amendment B10: every V2 policy run (live and replayed) stops after this many confirmed
#: regressions. Policies replay one captured call sequence, so all stop at the same point.
V2_STOP_AFTER_REGRESSIONS = 3


def run_policies(instance_id, selection, executor, reference, folder, *, primary_accounting=None):
    """Capture both trees, guard them, confirm live once, then replay all arms.

    C_invalid_excluded drives the live capture. The caller selects the
    decision signal from the returned reports.
    """
    folder.mkdir(parents=True, exist_ok=True)
    health_path = folder / 'health.jsonl'
    calls = Calls(executor, instance_id, health_path, reference)
    for patched in (False, True):
        run = calls.run(selection.tests, patched=patched, timeout_s=1800)
        write(folder / ('patched.json' if patched else 'base.json'), run_to_dict(run, inline_raw=False))
    pair_reasons = check_generic_pair({tree: calls.calls[i][3].stage_health
                                      for i, tree in enumerate(('base', 'patched'))})
    # Persist the paired approval/rejection and calculate G3 after revocation.
    if any(s.get('both_trees_confirmed') or s.get('generic_rule_rejected')
           for entry in calls.calls for s in entry[3].stage_health):
        for i, tree in enumerate(('base', 'patched')):
            write(folder / (tree + '.json'), run_to_dict(calls.calls[i][3], inline_raw=False))
    trees = [health_for_run(instance_id, tree, calls.calls[i][3], reference[tree])
             for i, tree in enumerate(('base', 'patched'))]
    reasons = [reason for tree in trees for reason in tree['halt_reasons']]
    reasons += pair_reasons
    health = {'task': instance_id, 'trees': trees, 'halt': bool(reasons), 'halt_reasons': reasons}
    if reasons:
        append_health(health_path, health)
        raise RunHealthError(health)
    primary = run_regression(instance_id, selection, Replay(calls.calls, fallback=calls),
                             RegressionConfig(per_pass_timeout_s=1800, rerun_flaky=True, baseline_cache_dir=None,
                                              stop_after_regressions=V2_STOP_AFTER_REGRESSIONS))
    objects = {'C_invalid_excluded': primary}
    for policy, compatible, paired, missing in [
        ('C', True, False, True),
        ('S', False, False, False), ('S', False, False, True),
        ('P', False, True, False), ('P', False, True, True),
    ]:
        report = run_regression(instance_id, selection, Replay(calls.calls),
            RegressionConfig(per_pass_timeout_s=1800, rerun_flaky=True, baseline_cache_dir=None,
                             skip_compatible=compatible, invalid_as_missing=missing, skip_paired=paired,
                             stop_after_regressions=V2_STOP_AFTER_REGRESSIONS))
        objects[policy + ('_invalid_missing' if missing else '_invalid_excluded')] = report
    reports = {name: report_json(report, include_fallback=primary_accounting is not None)
               for name, report in objects.items()}
    payload = {'instance_id': instance_id, 'policies': reports,
               'native_passes': len(calls.calls), 'both_initial_trees_captured': True}
    if primary_accounting is not None:
        payload['primary_accounting'] = primary_accounting
    write(folder / 'v2_policies.json', payload)
    health['confirmation_collector_statuses'] = [r.validation_summary.get('collector_status', 'NOT_REPORTED')
                                                for _, _, _, r in calls.calls[2:]]
    append_health(health_path, health)
    return objects
