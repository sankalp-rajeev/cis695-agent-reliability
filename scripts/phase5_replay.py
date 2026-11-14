#!/usr/bin/env python3
"""Offline, label-free Phase 5 replay. Never imports benchmark code or runs tests.

Only the sealed run, its manifest/results, the frozen paired selections and
their protocol/task index, and A1's offline tier projection are data inputs.
Unknown JSON fields are skipped without decoding their values. All input bytes
are hash-checked, including the entire run before and after computation.
"""

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/phase4_v4_attempt4_20261109T185713Z'
SEAL = ROOT / 'reports/next_phases/phase4_rerun/attempt4_seal'
FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/'
              'v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
OFFLINE = ROOT / 'reports/v2_discovery_cleanup/comparison_final/offline.json'
OUTPUT = ROOT / 'reports/next_phases/phase5_replay'
MANIFEST_SHA = '69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25'
PROTOCOL_SHA = '2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153'
TASKS_SHA = '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625'
OFFLINE_SHA = 'c8b62809571952a02a0057ece03bd1f6f11ab5e54a52357db33d0d1d50bc574a'
SEALED_RESULTS_SHA = '94786d24848b9707eaeb73dd353affd108d95d50ddc773d0f23ed539341d7530'
BUDGETS = (30, 60, 120, 300)
SEEDS = tuple(range(20))
VARIANTS = ('execution_only', 'execution_plus_collection')
ROW = {'test_id': True, 'status': True}
EVENT = {k: True for k in ('event', 'module', 'duration_s', 'retry', 'split', 'timed_out')}
RUN_SCHEMA = {
    'requested_tests': True, 'results': {'*': ROW}, 'events': {'*': EVENT},
    'execution_results': {'*': ROW}, 'execution_id_map': True,
    'validation': {'*': {'selected_id': True, 'runnable_ids': True}},
    'timed_out': True, 'duration_s': True,
    'validation_summary': {'duration_s': True, 'groups': {'*': {'module': True, 'duration_s': True}}},
}
CONFIRM_SUMMARY = {k: True for k in ('candidate_id', 'initial_outcome', 'stable',
    'base_PASS', 'patched_non_PASS', 'base_statuses', 'patched_statuses', 'attempts_per_tree')}
REPORT_SCHEMA = {
    'signal': True, 'outcomes': True, 'confirmation_summary': {'*': CONFIRM_SUMMARY},
    'confirmations': {'*': {
        'confirmation': {'tree': True, 'candidate_id': True, 'attempt': True, 'isolated': True},
        'results': {'*': ROW}, 'events': {'*': EVENT},
        'validation_summary': {'groups': {'*': {'module': True, 'duration_s': True}}},
    }},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class Projection:
    """Decode only whitelisted JSON fields; skip other values structurally."""

    string = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"')
    structure = re.compile(r'["{}\[\]]')
    scalar_end = re.compile(r'[,}\]]')

    def __init__(self, raw):
        self.text, self.pos = raw.decode(), 0
        self.decoder = json.JSONDecoder()

    def whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def scalar(self):
        self.whitespace()
        value, self.pos = self.decoder.raw_decode(self.text, self.pos)
        return value

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
                require(match is not None, 'Unfinished JSON container')
                char = match.group()
                if char == '"':
                    self.pos = self.string.match(self.text, match.start()).end()
                else:
                    depth += 1 if char in '[{' else -1
                    self.pos = match.end()
        else:
            match = self.scalar_end.search(self.text, self.pos)
            self.pos = match.start() if match else len(self.text)

    def project(self, schema):
        self.whitespace()
        if schema is True:
            return self.scalar()
        char = self.text[self.pos]
        if char not in '[{':
            # Optional structured values may be null, never arbitrary scalars.
            require(self.scalar() is None, 'Unexpected scalar in structured field')
            return None
        self.pos += 1
        result = {} if char == '{' else []
        closing = '}' if char == '{' else ']'
        self.whitespace()
        while self.text[self.pos] != closing:
            if char == '{':
                key = self.scalar()
                self.whitespace()
                require(self.text[self.pos] == ':', 'Missing JSON colon')
                self.pos += 1
                if key in schema:
                    result[key] = self.project(schema[key])
                else:
                    self.skip()
            else:
                result.append(self.project(schema['*']))
            self.whitespace()
            if self.text[self.pos] == ',':
                self.pos += 1
            self.whitespace()
        self.pos += 1
        return result


def project(raw, schema):
    return Projection(raw).project(schema)


def verify_manifest():
    raw = (SEAL / 'run_manifest.sha256').read_bytes()
    require(digest(raw) == MANIFEST_SHA, 'Sealed manifest changed; STOP')
    entries, header = {}, {}
    for line in raw.decode().splitlines():
        if line.startswith('# '):
            key, value = line[2:].split(': ', 1)
            header[key] = value
        elif line:
            sha, name = line.split('  ', 1)
            require(not Path(name).is_absolute() and '..' not in Path(name).parts
                    and name not in entries, 'Unsafe/duplicate manifest path')
            entries[name] = sha
    paths = list(RUN.rglob('*'))
    require(not any(p.is_symlink() for p in paths), 'Symlink in sealed run; STOP')
    files = {p.relative_to(RUN).as_posix(): p for p in paths if p.is_file()}
    require(files.keys() == entries.keys(), 'Run file set differs from manifest; STOP')
    total = 0
    for name, path in sorted(files.items()):
        require(file_digest(path) == entries[name], 'Run hash mismatch; STOP: ' + name)
        total += path.stat().st_size
    require(len(entries) == int(header['file_count']) == 1799, 'Run file count changed; STOP')
    require(total == int(header['total_bytes']), 'Run byte count changed; STOP')
    require(header['run_directory'] == RUN.relative_to(ROOT).as_posix(), 'Wrong run directory')
    return entries, {'sha256': MANIFEST_SHA, 'file_count': len(entries), 'total_bytes': total}


class Inputs:
    def __init__(self, entries):
        self.entries = entries
        self.hashes = {}

    def pinned(self, path, sha, schema):
        raw = path.read_bytes()
        require(digest(raw) == sha, 'Input hash mismatch; STOP: ' + str(path))
        self.hashes[str(path)] = sha
        return project(raw, schema)

    def run(self, relative, schema):
        require(relative in self.entries, 'Unmanifested run input: ' + relative)
        return self.pinned(RUN / relative, self.entries[relative], schema)

    def selection(self, task, arm, protocol):
        relative = task['selections'][arm]
        require(relative == 'selections/' + task['instance_id'] + '/' + arm + '.json',
                'Unexpected frozen selection path')
        result = self.pinned(FROZEN / relative, protocol['task_artifact_sha256'][relative], {
            'instance_id': True, 'arm': True, 'tests': True, 'selection_status': True,
            'mapping': {'*': {'path': True, 'base_path': True}},
        })
        require(result['instance_id'] == task['instance_id'] and result['arm'] == arm,
                'Frozen selection identity mismatch')
        tests = result['tests']
        require(tests is None or (isinstance(tests, list) and len(tests) == len(set(tests))
                and all(isinstance(t, str) for t in tests)), 'Invalid frozen test list')
        return result


def tier_gate(tests, record):
    """A1 exact ordered equality, then exact tier union. No reconstruction."""
    exact = [side for side in ('before', 'after') if tests == record.get(side)]
    reasons = []
    for side in exact:
        by_tier = record.get(side + '_by_tier', {})
        tiers = {}
        for key, ids in by_tier.items():
            tier = int(key)
            require(tier in (1, 2), 'Unexpected tier outside frozen Tier 1 + Tier 2')
            for tid in ids:
                tiers[tid] = min(tier, tiers.get(tid, tier))
        if set(tiers) == set(tests) and len(tests) == len(set(tests)):
            return {'matched': side, 'exact_matches': exact, 'tiers': tiers, 'reason': ''}
        reasons.append(side + ' tier union differs from frozen V2 list')
    return {'matched': 'none', 'exact_matches': exact, 'tiers': None,
            'reason': '; '.join(reasons) or 'Frozen V2 list equals neither before nor after in content and order'}


def module_of(tid):
    return tid.split('::', 1)[0]


def name_key(path):
    """Exact module basename, with the conventional test affix removed."""
    # The offline replay host uses Python 3.8 (no str.removeprefix).
    return re.sub(r'_test$', '', re.sub(r'^test_', '', Path(path).stem))


def rule_order(modules, tiers, changed_paths):
    source_order = {module: index for index, module in enumerate(modules)}
    names = {name_key(p) for p in changed_paths}
    return sorted(modules, key=lambda m: (tiers[m], name_key(m) not in names, source_order[m]))


def module_costs(events):
    """Count every end event, including split parents, retries and fallbacks."""
    costs = collections.defaultdict(list)
    for event in events:
        if event['event'] == 'end':
            duration = event['duration_s']
            require(isinstance(duration, (float, int)) and math.isfinite(duration)
                    and duration >= 0, 'Invalid process duration')
            costs[event['module']].append(duration)
    return {m: math.fsum(values) for m, values in costs.items()}


def collection_costs(groups):
    costs = collections.defaultdict(list)
    for group in groups:
        value = group['duration_s']
        require(isinstance(value, (float, int)) and math.isfinite(value) and value >= 0,
                'Invalid collection-group duration')
        costs[group['module']].append(value)
    return {m: math.fsum(values) for m, values in costs.items()}


def selector_metrics(tests, selected, regressions):
    if selected is None:
        return {'status': 'unavailable', 'reference_kept': None, 'reference_missed': None,
                'v2_kept': None, 'share_v2_kept': None, 'outside_reference_count': None,
                'outside_reference_ids': None}
    reference, selection, regressions = set(tests), set(selected), set(regressions)
    overlap = reference & selection
    return {'status': 'available', 'reference_kept': sorted(regressions & overlap),
            'reference_missed': sorted(regressions - overlap), 'v2_kept': len(overlap),
            'share_v2_kept': len(overlap) / len(reference) if reference else None,
            'outside_reference_count': len(selection - reference),
            'outside_reference_ids': sorted(selection - reference)}


def replay(order, costs, tests, regressions, budget, selected_modules=None, failure_modules=None):
    """A module starts strictly before the deadline; an end at the deadline counts.

    The crossing module is attempted but not completed. Its reference outcomes
    count only for the optimistic bound. No fractional per-test cost is assigned.
    """
    elapsed = 0.0
    starts, ends = {}, {}
    for module in order:
        starts[module] = elapsed
        elapsed = math.fsum((elapsed, costs[module]))
        ends[module] = elapsed
    reached = [m for m in order if starts[m] < budget]
    completed = [m for m in reached if ends[m] <= budget]
    reached_set = set(reached)
    completed_set = set(completed)
    not_reached = [m for m in order if m not in reached_set]
    active = [m for m in reached if ends[m] > budget]
    selected_modules = selected_modules or {t: [module_of(t)] for t in tests}
    failure_modules = failure_modules or {t: [module_of(t)] for t in regressions}
    regression_modules = {m for ms in failure_modules.values() for m in ms}
    first_start = min((starts[m] for m in regression_modules), default=None)
    first_end = min((ends[m] for m in regression_modules), default=None)
    kept_start = sorted(t for t in regressions if set(failure_modules[t]) & reached_set)
    kept_end = sorted(t for t in regressions if set(failure_modules[t]) & completed_set)
    not_reached_ids = [t for t in tests if not (set(selected_modules[t]) & reached_set)]
    partially_reached_ids = [t for t in tests if set(selected_modules[t]) & reached_set
                             and not set(selected_modules[t]) <= reached_set]
    return {
        'modules_run': reached, 'modules_completed': completed, 'modules_in_progress': active,
        'modules_not_reached': not_reached,
        'share_not_reached': len(not_reached_ids) / len(tests) if tests else None,
        'partially_reached_selected_count': len(partially_reached_ids),
        'first_regression_start_s': first_start if first_start is not None and first_start < budget else None,
        'first_regression_end_s': first_end if first_end is not None and first_end <= budget else None,
        'full_first_regression_start_s': first_start, 'full_first_regression_end_s': first_end,
        'reference_kept_start': kept_start, 'reference_kept_end': kept_end,
        'reference_missed_start': sorted(set(regressions) - set(kept_start)),
        'reference_missed_end': sorted(set(regressions) - set(kept_end)),
        'whole_patched_pass_s': math.fsum(costs.values()), 'binds': math.fsum(costs.values()) > budget,
        'informative': math.fsum(costs.values()) > budget,
    }


def quantile(values, probability):
    """Linear quantile; None denotes right censoring, ordered after finite times."""
    values = sorted(float('inf') if v is None else v for v in values)
    require(bool(values), 'Empty quantile input')
    index = (len(values) - 1) * probability
    lower, upper = math.floor(index), math.ceil(index)
    if not math.isfinite(values[upper]):
        return None
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def quantiles(values):
    return {key: quantile(values, p) for key, p in (('q25', .25), ('median', .5), ('q75', .75))}


def reference_regressions(report, base, patched):
    b = {x['test_id']: x['status'] for x in base['results']}
    p = {x['test_id']: x['status'] for x in patched['results']}
    summaries = {s['candidate_id']: s for s in report['confirmation_summary']}
    refs = {}
    for tid, outcome in report['outcomes'].items():
        if outcome not in ('REGRESSION', 'REGRESSION_ERROR'):
            continue
        summary = summaries.get(tid, {})
        expected = 'failed' if outcome == 'REGRESSION' else 'error'
        require(b.get(tid) == 'passed' and p.get(tid) == expected,
                'Reference initial outcome mismatch: ' + tid)
        require(summary.get('stable') is True and summary.get('attempts_per_tree') == 3
                and summary.get('base_statuses') == ['passed'] * 3
                and summary.get('patched_statuses') == [expected] * 3,
                'Reference lacks stable 3/3 confirmation: ' + tid)
        # Independently check the actual isolated calls, not just their summary.
        for tree, status in (('base', 'passed'), ('patched', expected)):
            calls = [c for c in report['confirmations'] if c['confirmation']['candidate_id'] == tid
                     and c['confirmation']['tree'] == tree]
            require(sorted(c['confirmation']['attempt'] for c in calls) == [1, 2, 3]
                    and all(c['confirmation']['isolated'] for c in calls),
                    'Missing isolated confirmations: ' + tid)
            require(all({r['test_id']: r['status'] for r in c['results']}.get(tid) == status
                        for c in calls), 'Confirmation statuses disagree: ' + tid)
        refs[tid] = outcome
    return refs


def compute(inputs, manifest_info):
    protocol = inputs.pinned(FROZEN / 'protocol.json', PROTOCOL_SHA, {'task_artifact_sha256': True})
    tasks = inputs.pinned(FROZEN / 'tasks.json', TASKS_SHA, {'*': {
        'instance_id': True, 'selections': {'v2': True, 'scg': True}}})
    offline = inputs.pinned(OFFLINE, OFFLINE_SHA, {'tasks': {'*': {
        k: True for k in ('instance_id', 'before', 'after', 'before_by_tier', 'after_by_tier')}}})
    sealed = inputs.pinned(SEAL / 'results.json', SEALED_RESULTS_SHA, {
        'integrity': {'ok': True, 'original_native_FAIL_audit': {'*': {'task': True}}},
        'run_manifest': True,
    })
    require(sealed['integrity']['ok'] and sealed['run_manifest']['sha256'] == MANIFEST_SHA,
            'Sealed result integrity mismatch')
    order = [t['instance_id'] for t in tasks]
    require(len(order) == len(set(order)) == 83, 'Wrong frozen task cohort')
    offline_tasks = {t['instance_id']: t for t in offline['tasks']}
    require(len(offline['tasks']) == 83 and set(offline_tasks) == set(order), 'A1 cohort mismatch')
    original_cases = [x['task'] for x in sealed['integrity']['original_native_FAIL_audit']]
    require(len(original_cases) == 6, 'Expected six original native FAIL tasks')
    cases = sorted(original_cases + ['django__django-10973'])
    require(len(set(cases)) == 7, 'Wrong regression case set')
    plan = inputs.run('plan.json', {'task_specs': {'*': {
        'instance_id': True, 'selection_sha256': True, 'selected_ids': True}}})
    run_tasks = {t['instance_id']: t for t in plan['task_specs']}
    require(set(run_tasks) == set(order), 'Phase 4 task cohort mismatch')
    tier_rows, selector_rows, cost_rows, ordering_rows, details = [], [], [], [], []
    for task in sorted(tasks, key=lambda t: t['instance_id']):
        iid = task['instance_id']
        v2 = inputs.selection(task, 'v2', protocol)
        scg = inputs.selection(task, 'scg', protocol)
        tests = v2['tests']
        require(tests is not None, 'Unavailable V2 reference selection: ' + iid)
        require(run_tasks[iid]['selection_sha256'] == protocol['task_artifact_sha256'][task['selections']['v2']]
                and run_tasks[iid]['selected_ids'] == len(tests), 'Selection differs from Phase 4: ' + iid)
        gate = tier_gate(tests, offline_tasks[iid])
        tiers = gate['tiers']
        tier_rows.append({'task': iid, 'matched': gate['matched'], 'exact_matches': gate['exact_matches'],
                          'tier1_count': sum(t == 1 for t in tiers.values()) if tiers is not None else None,
                          'tier2_count': sum(t == 2 for t in tiers.values()) if tiers is not None else None,
                          'reason': gate['reason']})
        base = inputs.run('tasks/' + iid + '/base.json', RUN_SCHEMA)
        patched = inputs.run('tasks/' + iid + '/patched.json', RUN_SCHEMA)
        item = inputs.run('tasks/' + iid + '/result.json', {
            'policies': {'C_invalid_excluded': REPORT_SCHEMA}})
        report = item['policies']['C_invalid_excluded']
        require(base['requested_tests'] == patched['requested_tests'] == tests,
                'Initial pass requested tests differ from frozen V2: ' + iid)
        refs = reference_regressions(report, base, patched)
        require(bool(refs) == (iid in cases), 'Reference regression case set changed: ' + iid)
        for selector, selected in (
            ('v2_tier1', [t for t in tests if tiers[t] == 1] if tiers is not None else None),
            ('v2_tier1_tier2', tests), ('corrected_scg', scg['tests']),
        ):
            metrics = selector_metrics(tests, selected, refs)
            if selector == 'v2_tier1' and tiers is None:
                metrics['status'] = 'unavailable_tier_gate'
            if selector == 'corrected_scg' and selected is None:
                metrics['status'] = scg['selection_status']
            selector_rows.append({'task': iid, 'selector': selector, **metrics})
        # A selected inherited family can expand into other modules. Use the
        # recorded native mapping, never assign those process costs to a test.
        validation = {v['selected_id']: v['runnable_ids'] for v in patched['validation']}
        selected_modules, memberships = {}, {}
        for tid in tests:
            runnable = validation.get(tid, [])
            selected_modules[tid] = list(dict.fromkeys(module_of(t) for t in runnable)) or [module_of(tid)]
            memberships[tid] = list(dict.fromkeys([module_of(tid)] + selected_modules[tid]))
        modules = list(dict.fromkeys(m for tid in tests for m in memberships[tid]))
        owners = {m: [t for t in tests if m in memberships[t]] for m in modules}
        failure_modules = {t: set() for t in refs}
        for row in patched['execution_results']:
            for tid in patched['execution_id_map'].get(row['test_id'], []):
                if tid in refs and row['status'] == ('failed' if refs[tid] == 'REGRESSION' else 'error'):
                    failure_modules[tid].add(module_of(row['test_id']))
        require(all(failure_modules.values()), 'No recorded concrete failure module: ' + iid)
        execution = module_costs(patched['events'])
        collection = collection_costs(patched['validation_summary'].get('groups', []))
        require(set(execution) <= set(modules) and set(collection) <= set(modules),
                'Cost module outside reference selection: ' + iid)
        module_tiers, mixed = {}, {}
        if tiers is not None:
            for m in modules:
                values = sorted({tiers[t] for t in owners[m]})
                module_tiers[m] = min(values)
                if len(values) > 1:
                    mixed[m] = values
        # Mapping paths are label-free changed-source metadata already frozen
        # with SCG. Do not open patches or rebuild the graph to fill gaps.
        changed = sorted({p for row in scg.get('mapping', [])
                          for p in (row.get('path'), row.get('base_path')) if p})
        reasons = []
        if tiers is None:
            reasons.append('Tier gate: ' + gate['reason'])
        if not tests:
            reasons.append('Empty V2 reference selection')
        if tests and not changed:
            reasons.append('Frozen SCG selection has no changed-module paths; name priority unavailable')
        # A crash can leave individual IDs not_reached inside a fully measured
        # module process. That is an outcome gap, not a missing process cost.
        censored = patched['timed_out'] or any(
            e['event'] == 'not_reached' or e.get('timed_out') for e in patched['events'])
        if censored:
            reasons.append('Phase 4 patched pass censored; missing/truncated module durations cannot be invented')
        by_module = collections.defaultdict(list)
        for event in patched['events']:
            if event['event'] == 'end':
                by_module[event['module']].append(event)
        # No process was launched for these modules (e.g. collection rejected or
        # skipped them). Zero denotes observed execution cost, not a test time.
        zero_execution = [m for m in modules if m not in execution]
        confirm_events = [e for c in report['confirmations'] if c['confirmation']['tree'] == 'patched'
                          for e in c['events']]
        confirm_cost = math.fsum(module_costs(confirm_events).values())
        total_exec = math.fsum(execution.values())
        total_collection = math.fsum(collection.values())
        total_plus = math.fsum((total_exec, total_collection))
        cost_rows.append({
            'task': iid, 'v2_count': len(tests), 'module_count': len(modules),
            'patched_execution_s': total_exec, 'patched_collection_groups_s': total_collection,
            'patched_execution_plus_collection_s': total_plus,
            'patched_recorded_pass_wall_s': patched['duration_s'],
            'patched_recorded_collection_wall_s': patched['validation_summary'].get('duration_s', 0),
            'patched_confirmation_execution_s': confirm_cost,
            'end_event_count': sum(len(v) for v in by_module.values()),
            'retry_end_event_count': sum(bool(e.get('retry')) for v in by_module.values() for e in v),
            'split_parent_end_event_count': sum(bool(e.get('split')) for v in by_module.values() for e in v),
            'zero_execution_modules': zero_execution,
            'ordering_eligible': not reasons, 'ordering_exclusion_reason': '; '.join(reasons),
            'execution_cost_complete': not censored,
            **{'execution_binds_' + str(b): True if total_exec > b else None if censored else False
               for b in BUDGETS},
            **{'plus_collection_binds_' + str(b): True if total_plus > b else None if censored else False
               for b in BUDGETS},
        })
        module_rows = []
        for index, m in enumerate(modules):
            module_rows.append({'module': m, 'source_order': index, 'tier': module_tiers.get(m),
                'tiers': mixed.get(m, [module_tiers[m]] if m in module_tiers else []),
                'changed_name_match': name_key(m) in {name_key(p) for p in changed},
                'selected_count': len(owners[m]),
                'execution_s': execution.get(m, 0.0), 'collection_s': collection.get(m, 0.0),
                'end_event_count': len(by_module[m]),
                'execution_not_launched': m in zero_execution,
                'cost_censored': any(e.get('timed_out') for e in by_module[m]) or any(
                    e['event'] == 'not_reached' and e['module'] == m for e in patched['events'])})
        details.append({'task': iid, 'tier_match': gate['matched'], 'tier_exact_matches': gate['exact_matches'],
                        'reference_regressions': refs, 'mixed_tier_modules': mixed,
                        'reference_failure_modules': {t: sorted(ms) for t, ms in failure_modules.items()},
                        'selected_family_module_expansions': {t: ms for t, ms in selected_modules.items()
                            if ms != [module_of(t)]},
                        'changed_module_paths': changed, 'modules': module_rows,
                        'ordering_exclusion_reasons': reasons})
        if reasons:
            # Explicit exclusion rows retain all tasks without fabricating times.
            for variant in VARIANTS:
                for budget in BUDGETS:
                    ordering_rows.append({'task': iid, 'variant': variant, 'budget': budget,
                                          'ordering': 'excluded', 'status': '; '.join(reasons)})
            continue
        orders = {'rule': rule_order(modules, module_tiers, changed)}
        for seed in SEEDS:
            shuffled = list(modules)
            random.Random(seed).shuffle(shuffled)
            orders['random_' + str(seed)] = shuffled
        for variant in VARIANTS:
            costs = {m: execution.get(m, 0.0) + (collection.get(m, 0.0)
                      if variant == 'execution_plus_collection' else 0.0) for m in modules}
            for budget in BUDGETS:
                for ordering, sequence in orders.items():
                    ordering_rows.append({'task': iid, 'variant': variant, 'budget': budget,
                        'ordering': ordering, 'status': 'available',
                        **replay(sequence, costs, tests, refs, budget, selected_modules, failure_modules)})
    counts = dict(collections.Counter(r['matched'] for r in tier_rows))
    case_summaries = []
    index = {(r['task'], r['variant'], r['budget'], r['ordering']): r for r in ordering_rows}
    for iid in cases:
        for variant in VARIANTS:
            for budget in BUDGETS:
                rule = index.get((iid, variant, budget, 'rule'))
                if rule is None:
                    case_summaries.append({'task': iid, 'variant': variant, 'budget': budget,
                                           'status': 'ordering_excluded'})
                    continue
                randoms = [index[iid, variant, budget, 'random_' + str(seed)] for seed in SEEDS]
                case_summaries.append({'task': iid, 'variant': variant, 'budget': budget,
                    'status': 'available', 'binds': rule['binds'],
                    'rule_start_s': rule['first_regression_start_s'],
                    'rule_end_s': rule['first_regression_end_s'],
                    'rule_reference_kept_start': rule['reference_kept_start'],
                    'rule_reference_kept_end': rule['reference_kept_end'],
                    'rule_reference_missed_start': rule['reference_missed_start'],
                    'rule_reference_missed_end': rule['reference_missed_end'],
                    'random_start_s': quantiles([r['first_regression_start_s'] for r in randoms]),
                    'random_end_s': quantiles([r['first_regression_end_s'] for r in randoms])})
    readings = {}
    refs_by_case = {d['task']: list(d['reference_regressions']) for d in details if d['task'] in cases}
    for variant in VARIANTS:
        bounds = {}
        available = all((iid, variant, 120, 'rule') in index for iid in cases)
        for bound, suffix in (('optimistic', 'start'), ('conservative', 'end')):
            if not available:
                bounds[bound] = {'meets_reading': False, 'reason': 'A regression case is excluded'}
                continue
            rules = [index[iid, variant, 120, 'rule'] for iid in cases]
            kept = sum(len(r['reference_kept_' + suffix]) for r in rules)
            total = sum(len(refs_by_case[iid]) for iid in cases)
            rule_median = quantile([r['first_regression_' + suffix + '_s'] for r in rules], .5)
            random_medians = [quantile([index[iid, variant, 120, 'random_' + str(seed)][
                'first_regression_' + suffix + '_s'] for iid in cases], .5) for seed in SEEDS]
            random_q25 = quantile(random_medians, .25)
            coverage_met = 10 * kept >= 9 * total
            faster = rule_median is not None and random_q25 is not None and rule_median < random_q25
            bounds[bound] = {'reference_kept_count': kept, 'reference_total_count': total,
                'required_count': math.ceil(.9 * total), 'coverage_threshold_met': coverage_met,
                'rule_median_s': rule_median, 'random_ordering_task_medians_s': random_medians,
                'random_q25_of_task_medians_s': random_q25, 'strictly_faster': faster,
                'meets_reading': coverage_met and faster,
                'nonbinding_tasks': [r['task'] for r in rules if not r['binds']]}
        disagreement = bounds['optimistic']['meets_reading'] != bounds['conservative']['meets_reading']
        all_nonbinding = available and all(not index[iid, variant, 120, 'rule']['binds'] for iid in cases)
        # Nonbinding budgets are explicitly non-informative under plan f.
        verdict = ('inconclusive' if disagreement or not available or all_nonbinding else
                   'useful' if bounds['conservative']['meets_reading'] else 'criterion_not_met')
        readings[variant] = {'budget_s': 120, 'bounds': bounds, 'bounds_disagree': disagreement,
                             'all_regression_case_budgets_nonbinding': all_nonbinding,
                             'verdict': verdict}
    return {
        'scope': 'Seven sealed regression tasks, case by case; no extrapolation or rates over this set',
        'manifest': manifest_info, 'input_sha256': dict(sorted(inputs.hashes.items())),
        'tier_match_counts': {k: counts.get(k, 0) for k in ('before', 'after', 'none')},
        'tier_match': tier_rows, 'selector_replay': selector_rows, 'ordering_replay': ordering_rows,
        'per_task_costs': cost_rows, 'per_task_details': details, 'case_summaries': case_summaries,
        'regression_cases': cases, 'pre_registered_reading': readings,
        'random_seeds': list(SEEDS), 'budgets_s': list(BUDGETS),
        'definitions': {
            'tier_tie': 'Prefer before when both before and after exactly match; record both exact matches',
            'source_order': 'First appearance through the frozen V2 list, with recorded native runnable module expansions in their recorded order',
            'changed_name': 'Exact basename after removing test_ prefix or _test suffix; frozen SCG mapping path/base_path only',
            'missing_changed_paths': 'Exclude ordering rather than reconstruct changed modules from patches',
            'module_cost': 'All end-event durations in the initial patched pass, including retry, fallback and split-parent processes',
            'confirmation_cost': 'Isolated patched confirmations reported separately; not part of the initial patched pass',
            'collection_variant': 'Add each module collection-group duration; collection wall overhead remains separately reported',
            'not_launched': 'No recorded module process means zero observed process cost; not a per-test runtime estimate',
            'censored_pass': 'Exclude ordering if original patched process costs are truncated or module processes not reached; individual IDs not_reached after a measured crash do not censor process cost',
            'budget_cutoff': 'Start < budget; complete <= budget. Crossing module attempted but conservative outcomes unavailable',
            'share_not_reached': 'Frozen V2 IDs with no recorded runnable module started / frozen V2 size; partially reached expanded families counted separately',
            'censoring': 'Null time means no regression at that bound within the budget; full unbudgeted bounds also recorded',
            'quantiles': 'Linear interpolation at (n-1)*p; censored values sort after finite values; censored upper interpolation returns null',
            'reading_median': 'Median across seven task TTFs; compare strictly against q25 of 20 per-seed task medians',
            'reading_counts': '90% threshold evaluated with integer counts; no aggregate regression rate reported',
            'nonbinding': 'Non-informative; if all seven budgets are nonbinding, overall evidence verdict is inconclusive',
        },
        'constraints': {'docker_calls': 0, 'test_executions': 0, 'model_calls': 0,
                        'correctness_labels_read': 0, 'oracle_data_read': 0},
    }


def fmt(value):
    return '>budget' if value is None else f'{value:.3f}'


def triplet(values):
    return '/'.join(fmt(values[k]) for k in ('q25', 'median', 'q75'))


def markdown(result):
    counts = result['tier_match_counts']
    lines = ['# Phase 5 offline replay — Amendment A1', '',
        'Sealed Phase 4 reference: `' + MANIFEST_SHA + '`; all 1,799 files verified before and after replay.', '',
        (f"Tier gate: before **{counts['before']}**, after **{counts['after']}**, neither **{counts['none']}**. "
        'Exact content and order plus exact tier union required. When both match, before wins; both matches are recorded.'), '',
        ('Execution-only is primary. All module end-event durations in the initial patched pass are summed, including '
        'split parents, retries and fallback processes. Isolated confirmation execution costs are reported separately. '
        'Collection-group time is separate and added in the second variant. No per-test times are estimated.'), '',
        ('Source order means first module appearance through the frozen V2 list, expanding inherited families to native '
        'modules only with their recorded validation mappings. Partially reached families are counted separately. Changed-module names use exact basenames '
        'with conventional test affixes removed, using only frozen SCG mapping paths. Modules mixing tiers take the lowest tier.'), '',
        ('A module starts before the deadline; completion at the deadline counts. A crossing module is attempted, '
        'but its reference outcomes count only under the optimistic bound. `>budget` means right-censored, not zero. '
        'Random columns are the 25th/median/75th percentiles over seeds 0..19.'), '',
        ('These are recorded module-process cost replays. They do not establish outcomes or costs of tests outside '
        'the V2 reference, or of a newly executed reduced module. Reaching a module does not turn its skipped or '
        'collection-error IDs into executed tests.'), '', '## Exclusions', '',
        '| Task | Reason |', '|---|---|']
    exclusions = [r for r in result['per_task_costs'] if not r['ordering_eligible']]
    for row in exclusions:
        lines.append(f"| `{row['task']}` | {row['ordering_exclusion_reason']} |")
    if not exclusions:
        lines.append('| None | — |')
    lines += ['', 'Tier-gate exclusions: ' + ', '.join('`' + r['task'] + '`' for r in result['tier_match']
              if r['matched'] == 'none') + ('None.' if counts['none'] == 0 else '.'), '',
              '## Seven regression cases: selectors', '',
              ('Counts are kept/missed reference IDs; exact names appear below and in selector_replay.csv. '
              'Outside-reference selections count separately and never become kept or missed reference regressions.'), '',
              '| Task | Tier 1 kept/missed | V2 kept/missed | SCG kept/missed | SCG outside reference |',
              '|---|---:|---:|---:|---:|']
    selector_index = {(r['task'], r['selector']): r for r in result['selector_replay']}
    for iid in result['regression_cases']:
        rows = [selector_index[iid, s] for s in ('v2_tier1', 'v2_tier1_tier2', 'corrected_scg')]
        cells = ['unavailable' if r['reference_kept'] is None else
                 str(len(r['reference_kept'])) + '/' + str(len(r['reference_missed'])) for r in rows]
        lines.append('| `' + iid + '` | ' + ' | '.join(cells) + ' | ' + str(rows[2]['outside_reference_count']) + ' |')
    lines += ['', '| Task | Selector | Reference regressions kept (named) | Reference regressions missed (named) |',
              '|---|---|---|---|']
    for row in result['selector_replay']:
        if row['task'] in result['regression_cases']:
            names = lambda ids: 'unavailable' if ids is None else '<br>'.join('`' + t + '`' for t in ids) or 'none'
            lines.append(f"| `{row['task']}` | {row['selector']} | {names(row['reference_kept'])} | {names(row['reference_missed'])} |")
    for variant in VARIANTS:
        lines += ['', '## Ordering: ' + variant, '',
            'Each time is seconds. Nonbinding budgets are non-informative.', '',
            '| Task | Budget | Binds | Rule start | Random start q25/median/q75 | Rule end | Random end q25/median/q75 | Rule kept start/end |',
            '|---|---:|---|---:|---|---:|---|---|']
        for row in result['case_summaries']:
            if row['variant'] != variant:
                continue
            if row['status'] != 'available':
                lines.append(f"| `{row['task']}` | {row['budget']} | excluded | — | — | — | — | — |")
                continue
            lines.append(f"| `{row['task']}` | {row['budget']} | {'yes' if row['binds'] else 'no'} | "
                         f"{fmt(row['rule_start_s'])} | {triplet(row['random_start_s'])} | "
                         f"{fmt(row['rule_end_s'])} | {triplet(row['random_end_s'])} | "
                         f"{len(row['rule_reference_kept_start'])}/{len(row['rule_reference_kept_end'])} |")
        reading = result['pre_registered_reading'][variant]
        lines += ['', '**Pre-registered evidence verdict: ' + reading['verdict'] + '.**', '']
        for bound, row in reading['bounds'].items():
            if 'reason' in row:
                lines.append(bound + ': ' + row['reason'])
            else:
                lines.append(f"{bound}: {row['reference_kept_count']} reference IDs kept; "
                    f"integer threshold {row['required_count']} of {row['reference_total_count']}. "
                    f"Rule task-median {fmt(row['rule_median_s'])} s; random q25 of per-seed task-medians "
                    f"{fmt(row['random_q25_of_task_medians_s'])} s. Strict time improvement: "
                    f"{row['strictly_faster']}; arithmetic criterion met: {row['meets_reading']}.")
        lines += ['', 'Bound disagreement: ' + str(reading['bounds_disagree']) + '. '
                  'All seven 120 s budgets nonbinding: ' + str(reading['all_regression_case_budgets_nonbinding']) + '.', '']
    lines += ['## Mixed-tier modules', '', '| Task | Module | Tiers |', '|---|---|---|']
    mixed = [(d['task'], m, tiers) for d in result['per_task_details'] for m, tiers in d['mixed_tier_modules'].items()]
    lines += [f'| `{iid}` | `{module}` | {tiers} |' for iid, module, tiers in mixed] or ['| None | — | — |']
    lines += ['', '## Budget binding and cost completeness for all tasks', '',
              ('Binding uses the replayed sum of module process durations (plus collection groups in the second variant). '
              'Recorded wall durations, which also include setup and validation overhead, are separate columns in per_task_costs.csv. '
              'A censored original pass has no known complete cost; its observed cost is a lower bound '
              'that can still establish binding when already above a budget.'), '',
              '| Task | Execution s | Collection groups s | Execution binding budgets | With collection binding budgets |',
              '|---|---:|---:|---|---|']
    for row in result['per_task_costs']:
        def binding(prefix, row=row):
            known = ', '.join(str(b) for b in BUDGETS if row[prefix + str(b)] is True) or 'none'
            unknown = ', '.join(str(b) for b in BUDGETS if row[prefix + str(b)] is None)
            return known + ('; unknown: ' + unknown if unknown else '')
        lines.append(f"| `{row['task']}` | {row['patched_execution_s']:.3f} | {row['patched_collection_groups_s']:.3f} | "
                     f"{binding('execution_binds_')} | {binding('plus_collection_binds_')} |")
    lines += ['', ('No aggregate regression rate is reported over the seven cases. The reading uses the registered '
              'integer coverage threshold and task medians only. Nonbinding budgets provide no budget-pressure evidence. '
              'No extrapolation beyond these cases. Synthetic unit checks are supplied but were not executed, '
              'as requested. No Docker, benchmark execution, model calls, correctness labels or oracle inputs. '
              'Phase 6b was not started.'), '']
    return '\n'.join(lines)


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (json.dumps(row[k], sort_keys=True, separators=(',', ':'))
                            if isinstance(row.get(k), (list, dict)) else row.get(k)) for k in fields})
    return stream.getvalue().encode()


def outputs(result):
    files = {'results.md': markdown(result).encode()}
    for key in ('tier_match', 'selector_replay', 'ordering_replay', 'per_task_costs'):
        rows = result[key]
        fields = list(dict.fromkeys(k for row in rows for k in row))
        files[key + '.csv'] = csv_bytes(rows, fields)
    # The complete named module schedules live in CSV, without duplicating
    # their large arrays in JSON. JSON retains case summaries and provenance.
    summary = {k: v for k, v in result.items() if k != 'ordering_replay'}
    summary['ordering_replay_artifact'] = {'path': 'ordering_replay.csv',
        'sha256': digest(files['ordering_replay.csv']), 'rows': len(result['ordering_replay'])}
    files['results.json'] = (json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    require(not args.output.exists(), 'Output already exists; choose a new directory')
    entries, info = verify_manifest()
    inputs = Inputs(entries)
    result = compute(inputs, info)
    entries_after, info_after = verify_manifest()
    require(entries == entries_after and info == info_after, 'Run changed during replay; STOP')
    for name, expected in inputs.hashes.items():
        require(file_digest(Path(name)) == expected, 'Input changed during replay; STOP: ' + name)
    files = outputs(result)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        (args.output / name).write_bytes(raw)
    print(json.dumps({'tier_match_counts': result['tier_match_counts'],
        'verdicts': {k: v['verdict'] for k, v in result['pre_registered_reading'].items()},
        'output_sha256': {name: digest(raw) for name, raw in sorted(files.items())}}, sort_keys=True))


if __name__ == '__main__':
    main()
