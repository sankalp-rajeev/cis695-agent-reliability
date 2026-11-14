#!/usr/bin/env python3
"""Independent Phase 6b recomputation. Standard library only; no analysis imports."""
import argparse
import gzip
import hashlib
import json
import math
import statistics
import subprocess
from pathlib import Path

EXECUTED = {'passed', 'failed', 'error', 'crash', 'xfail', 'xpass', 'timeout'}
PATCHED_EXECUTED = EXECUTED - {'timeout'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def time_s(run):
    return math.fsum(e['duration_s'] for e in run['events'] if e['event'] == 'end')


def outcomes(run):
    return {r['test_id']: r['status'] for r in run['results']}


def independently_trace(folder, run, windows=False):
    records = {}
    assert not list(folder.glob('*.error')), 'Tracer error marker'
    for path in sorted(folder.glob('*.jsonl.gz')):
        d = {'codes': [], 'tests': {}, 'flags': {}, 'common': set(), 'common_flags': set(),
             'scopes': [], 'children': []}
        with gzip.open(path, 'rt') as stream:
            for line in stream:
                item = json.loads(line)
                assert item['version'] == 3 and item['codes_start'] == len(d['codes'])
                d['pid'], d['parent_pid'], d['segment'] = item['pid'], item['parent_pid'], item['segment']
                d['codes'] += [tuple(c) for c in item['codes']]
                for tid, codes in item['tests'].items():
                    d['tests'][tid] = set(codes)
                d['flags'].update({tid: set(f) for tid, f in item['flags'].items()})
                d['common'].update(item['common'])
                d['common_flags'].update(item['common_flags'])
                d['scopes'] += item['scopes']
                d['children'] += item['children']
        stem = str(d['pid']) + ('_' + str(d['segment']) if d['segment'] else '')
        assert path.name == stem + '.jsonl.gz'
        d['complete'] = all((folder / (stem + '.' + ext)).is_file() for ext in ('ready', 'done'))
        if d['complete']:
            ready, done = read(folder / (stem + '.ready')), read(folder / (stem + '.done'))
            assert ready['pid'] == done['pid'] == d['pid']
            d['complete'] = done.get('state') == 'final'
        records[d['pid'], d['segment']] = d
    for e in run['events']:
        if e['event'] == 'start':
            assert records[e['pid'], 0]['complete']
    aliases = dict(run['raw_execution_map'])
    aliases.update({tid: tid for tid in run['execution_id_map']})
    calls_by_native, flags_by_native = {}, {}

    def attribute(raw, codes=(), flags=()):
        if raw in aliases:
            native = aliases[raw]
            calls_by_native.setdefault(native, set()).update(codes)
            flags_by_native.setdefault(native, set()).update(flags)

    for d in records.values():
        for child in d['children']:
            if child.get('python') is False:
                continue
            target = records.get((child['pid'], child.get('segment', 0)))
            if target is None or not target['complete']:
                if child['tests']:
                    for tid in child['tests']:
                        d['flags'].setdefault(tid, set()).add('unfollowed_child_process')
                else:
                    d['common_flags'].add('unfollowed_child_process')
    for key, d in records.items():
        inherited_codes, inherited_flags, seen = set(), set(), set()
        ancestor = key
        while ancestor in records:
            assert ancestor not in seen
            seen.add(ancestor)
            a = records[ancestor]
            if not windows:
                inherited_codes.update(a['codes'][i] for i in a['common'])
            inherited_flags.update(a['common_flags'])
            ancestor = a['parent_pid'], 0
        for tid, indices in d['tests'].items():
            if windows:
                own = {d['codes'][i] for scope in d['scopes'] if scope['scope'] == 'test'
                       and tid in scope['tests'] for i in scope['codes']}
            else:
                own = {d['codes'][i] for i in indices}
            attribute(tid, inherited_codes | own, inherited_flags | d['flags'].get(tid, set()))
        for child in d['children']:
            if child.get('python') is False or not child['tests']:
                continue
            c = records.get((child['pid'], child.get('segment', 0)))
            if c is None:
                continue
            coverage = {c['codes'][i] for scope in c['scopes'] if scope['scope'] == 'test'
                        for i in scope['codes']} if windows else set(c['codes'])
            for tid in child['tests']:
                attribute(tid, coverage, c['common_flags'])
    executed = {r['test_id'] for r in run['execution_results'] if r['status'] in EXECUTED}
    missing = {tid for tid in executed if not calls_by_native.get(tid)}
    for tid in missing:
        flags_by_native.setdefault(tid, set()).add('executed_without_trace_record')
    calls, flags = {}, {}
    for native, tests in run['execution_id_map'].items():
        for tid in tests:
            calls.setdefault(tid, set()).update(calls_by_native.get(native, ()))
            if native in executed:
                flags.setdefault(tid, set()).update(flags_by_native.get(native, ()))
    incomplete = {tid for tid in executed if flags_by_native.get(tid)}
    worker_pids = sorted({pid for (pid, segment), d in records.items() if (d['parent_pid'], 0) in records})
    info = {'process_count': len({pid for pid, segment in records}), 'worker_pids': worker_pids,
            'workers_seen': len(worker_pids),
            'workers_with_tests': sum(bool(d['tests']) for (pid, segment), d in records.items() if pid in worker_pids),
            'executed_count': len(executed), 'incomplete_count': len(incomplete),
            'incomplete_fraction': len(incomplete) / len(executed) if executed else 0.,
            'incomplete_ids': sorted(incomplete), 'missing_record_ids': sorted(missing),
            'trace_nonempty': any(calls_by_native.values()),
            'scopes_seen': sorted({s['scope'] for d in records.values() for s in d['scopes']}),
            'child_observations': [c for d in records.values() for c in d['children']]}
    return calls, flags, info


def independently_select(tests, status, calls, flags, targets):
    out = {'file': [], 'function': [], 'retained_reasons': {}, 'trace_incomplete': [],
           'without_usable_trace': [], 'absent_from_base': targets['absent_from_base'],
           'mapping_errors': targets['mapping_errors']}
    for tid in tests:
        events = calls.get(tid, set())
        incomplete = set(flags.get(tid, ())) if status.get(tid) in EXECUTED else set()
        unusable = not events or status.get(tid) not in ('passed', 'failed')
        if not events and status.get(tid) in EXECUTED:
            incomplete.add('executed_without_trace_record')
        if unusable:
            out['without_usable_trace'].append(tid)
        if incomplete:
            out['trace_incomplete'].append(tid)
        why = (['NO_USABLE_TRACE'] if unusable else []) + (['TRACE_INCOMPLETE'] if incomplete else [])
        if targets['absent_from_base'] or targets['mapping_errors']:
            why.append('BASE_MAP_INCOMPLETE')
        if why:
            out['file'].append(tid)
            out['function'].append(tid)
            out['retained_reasons'][tid] = why
            continue
        events = {(p[len('/testbed/'):] if p.startswith('/testbed/') else p, name, line)
                  for p, name, line in events}
        hit_file = any(p in targets['files'] for p, name, line in events)
        hit_function = any(p == f['path'] and name == f['name'] and line in (f['start'], f['decorator_start'])
                           for p, name, line in events for f in targets['functions'])
        if not targets['functions'] or targets.get('module_level_change'):
            hit_function = hit_file
        if hit_file:
            out['file'].append(tid)
        if hit_function:
            out['function'].append(tid)
    for field in ('trace_incomplete', 'without_usable_trace'):
        out[field].sort()
    assert set(out['function']) <= set(out['file'])
    return out


def independently_task(folder):
    inputs = read(folder / 'task_inputs.json')
    baseline, traced = read(folder / 'base_untraced.json'), read(folder / 'base_traced.json')
    phase4 = read(folder / 'phase4_comparison.json')
    tests, targets = inputs['tests'], inputs['targets']
    codes, flags, info = independently_trace(folder / 'traces/base_traced', traced)
    selected = independently_select(tests, outcomes(traced), codes, flags, targets)
    codes, flags, _ = independently_trace(folder / 'traces/base_traced', traced, windows=True)
    selected['secondary_test_window_exploratory'] = independently_select(tests, outcomes(traced), codes, flags, targets)
    B, TB, P = time_s(baseline), time_s(traced), time_s(phase4['patched'])
    assert math.isclose(P, phase4['sealed_patched_execution_s'], rel_tol=1e-12)
    # The pinned Phase 5 cost is the authoritative baseline scalar, independently
    # checked above against all sealed Phase 4 module-process end events.
    P = phase4['sealed_patched_execution_s']
    stable = phase4['stable_outcomes']
    differences = [t for t in tests if outcomes(baseline).get(t) != outcomes(traced).get(t)]
    row = {'task': inputs['task'], 'v2_size': len(tests), 'base_untraced_s': B, 'base_traced_s': TB,
           'sealed_full_patched_s': P, 'T': TB / B if B else None, 'selection': selected,
           'trace_accounting': info, 'disagreements': differences,
           'stable_disagreements': [t for t in differences if stable.get(t) != 'FLAKY'],
           'phase4_flaky_excluded': sorted(t for t in tests if stable.get(t) == 'FLAKY'),
           'blind_spot_counts': {'TRACE_INCOMPLETE': len(selected['trace_incomplete']),
                                'without_usable_trace': len(selected['without_usable_trace']),
                                'patch_only_absent': len(targets['absent_from_base'])},
           'targets': targets, 'modes': {}}
    refs = set(phase4['reference_ids'])
    for mode in ('file', 'function'):
        patched = read(folder / ('patched_' + mode + '.json'))
        observed = outcomes(patched)
        executed = sum(v in PATCHED_EXECUTED for v in observed.values())
        seconds, reduction = time_s(patched), 1 - executed / len(tests)
        kept, missed = sorted(refs & set(selected[mode])), sorted(refs - set(selected[mode]))
        row['modes'][mode] = {'selected_count': len(selected[mode]), 'selected_executed': executed,
            'selected_share': len(selected[mode]) / len(tests), 'r': reduction,
            'reference_kept': kept, 'reference_missed': missed, 'reference_kept_count': len(kept),
            'reference_total': len(refs), 'recall': len(kept) / len(refs) if refs else None,
            'patched_s': seconds, 'total_cost_s': TB + seconds, 'baseline_cost_s': B + P,
            'reusable_history_cost_s': seconds, 'reusable_history_baseline_s': P,
            'sealed_outcome_disagreements': [t for t in selected[mode] if observed.get(t) != outcomes(phase4['patched']).get(t)],
            'break_even_lhs_s': TB - B, 'break_even_rhs_s': reduction * P,
            'break_even_met': TB - B < reduction * P}
    return row


def independently_pool(rows):
    out = {'tasks': rows, 'pooled': {}}
    disagreements = sum(len(r['stable_disagreements']) for r in rows)
    for mode in ('file', 'function'):
        entries = [r['modes'][mode] for r in rows]
        kept = sum(len(e['reference_kept']) for e in entries)
        median_reduction = statistics.median(e['r'] for e in entries)
        total, baseline = (math.fsum(e[key] for e in entries) for key in ('total_cost_s', 'baseline_cost_s'))
        median_total, median_base = (statistics.median(e[key] for e in entries) for key in ('total_cost_s', 'baseline_cost_s'))
        n, chosen, executed = sum(r['v2_size'] for r in rows), sum(e['selected_count'] for e in entries), sum(e['selected_executed'] for e in entries)
        success = kept == 12 and median_reduction >= .5 and disagreements == 0
        out['pooled'][mode] = {'reading': 'preregistered' if mode == 'file' else 'exploratory',
            'reference_kept_count': kept, 'reference_total': 12, 'recall': kept / 12,
            'median_task_reduction': median_reduction, 'selected_count': chosen, 'selected_share': chosen / n,
            'selected_executed': executed, 'v2_size': n, 'pooled_reduction': 1 - executed / n,
            'tracing_overhead_T': math.fsum(r['base_traced_s'] for r in rows) / math.fsum(r['base_untraced_s'] for r in rows),
            'total_cost_s': total, 'baseline_cost_s': baseline, 'median_task_total_cost_s': median_total,
            'median_task_baseline_cost_s': median_base, 'pooled_total_cost_below_baseline': total < baseline,
            'median_task_cost_below_baseline': median_total < median_base,
            'reusable_history_cost_s': math.fsum(e['patched_s'] for e in entries),
            'reusable_history_baseline_s': math.fsum(r['sealed_full_patched_s'] for r in rows),
            'stable_disagreement_count': disagreements,
            'selected_patched_disagreement_count': sum(len(e['sealed_outcome_disagreements']) for e in entries),
            'trace_incomplete_count': sum(len(r['selection']['trace_incomplete']) for r in rows),
            'without_usable_trace_count': sum(len(r['selection']['without_usable_trace']) for r in rows),
            'patch_only_absent_count': sum(len(r['targets']['absent_from_base']) for r in rows),
            'success': success, 'failure': kept < 12 or disagreements > 0,
            'adopt': success and total < baseline and median_total < median_base}
    p = out['pooled']['file']
    out.update(verdict='FAILURE' if p['failure'] else ('SUCCESS' if p['success'] else 'INCONCLUSIVE'),
               adopt=p['adopt'], unspecified_cases=[],
               secondary_selection_reading='exploratory: test-window records only; no secondary patched pass')
    return out


def compare(expected, actual, path='results'):
    count = 0
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and expected.keys() == actual.keys(), path + ': keys differ'
        for key, value in expected.items():
            count += compare(value, actual[key], path + '.' + key)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(expected) == len(actual), path + ': lengths differ'
        for i, value in enumerate(expected):
            count += compare(value, actual[i], path + '[' + str(i) + ']')
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert isinstance(actual, (int, float)) and math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-9), path + ': numeric mismatch'
        count += 1
    else:
        assert expected == actual, path + ': value mismatch'
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    run, results = args.run.resolve(), args.results.resolve()
    invocation = read(run / 'invocation.json')
    assert invocation['mode'] == 'run' and not invocation['smoke_only']
    assert len(invocation['task_order']) == 13
    assert not (run / 'HALT.json').exists()
    verified_files = 0
    for iid in invocation['task_order']:
        folder = run / iid
        manifest = read(folder / 'capture_manifest.json')
        files = {str(p.relative_to(folder)): p for p in folder.rglob('*') if p.is_file() and p.name != 'capture_manifest.json'}
        assert files.keys() == manifest.keys()
        for name, file in files.items():
            assert sha(file) == manifest[name], 'Raw capture changed: ' + name
            verified_files += 1
    rows = [independently_task(run / iid) for iid in invocation['task_order']]
    expected = independently_pool(rows)
    count = compare(expected, read(results / 'results.json'))
    compare(expected, read(run / 'results.json'))
    root = Path(__file__).resolve().parents[1]
    tag = invocation['freeze_tag']
    assert subprocess.check_output(['git', 'diff', tag, '--', 'scripts', 'src'], cwd=root) == b''
    assert subprocess.check_output(['git', 'diff', tag, '--', 'tools/phase6b_trace'], cwd=root) == b''
    proof = {'passed': True, 'verified_numeric_values': count, 'verified_raw_files': verified_files,
             'tasks': 13, 'raw_run': str(run), 'harness_tag': tag, 'harness_HEAD': invocation['HEAD'],
             'results_sha256': sha(results / 'results.json'), 'verifier_sha256': sha(Path(__file__)),
             'method': 'Independent standard-library trace, selector, per-task and pooled recomputation; no analysis imports'}
    (results / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n')
    (results / 'verification.md').write_text(
        'PASS: independent verification recomputed every numeric value and compared every result field.\n\n'
        f"{count} numeric values, {verified_files} hashed raw capture files, and all 13 tasks checked. "
        'The verifier imports only the Python standard library and reconstructs primary and exploratory '
        'selections from the raw per-PID scope journals. It recomputes outcomes, reference recall, reduction, '
        'incompleteness fractions, time/cost sums, break-even comparisons, verdict and adoption.\n\n'
        f"Code diff against `{tag}` is empty for scripts/, src/, and tools/phase6b_trace/. "
        'Raw task manifests match their complete file sets and hashes. The original task order is retained.\n\n'
        'Label-access command audit is recorded separately in reports/next_phases/phase6b_run/command_audit.md. '
        'No audit file or correctness label is an input to this script.\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
