"""Host-side, label-free file/function selection; never executes source code."""
from __future__ import annotations

import ast
import gzip
import json
from pathlib import Path

from unidiff import PatchSet


def definitions(source, path):
    tree = ast.parse(source)
    result = []

    def visit(node, prefix=''):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            qualified = prefix + node.name
            if not isinstance(node, ast.ClassDef):
                result.append({'path': path, 'qualname': qualified, 'name': node.name,
                               'start': node.lineno, 'end': node.end_lineno,
                               'decorator_start': min([node.lineno] + [d.lineno for d in node.decorator_list])})
            prefix = qualified + '.'
        for child in ast.iter_child_nodes(node):
            visit(child, prefix)
    visit(tree)
    return result


def changed_targets(patch_text, base_sources):
    files, functions, absent, errors = set(), [], [], []
    module_level_change = False
    for change in PatchSet(patch_text):
        path = change.source_file.removeprefix('a/')
        target_path = change.target_file.removeprefix('b/')
        if path == '/dev/null':
            path = target_path
        files.add(path)
        source = base_sources.get(path)
        if source is None:
            absent.append(path)
            continue
        if not path.endswith('.py'):
            errors.append(path + ': non-Python file has no code-object map')
            continue
        try:
            defs = definitions(source, path)
        except (SyntaxError, UnicodeError) as exc:
            errors.append(path + ': ' + str(exc))
            continue
        # AST-qualify the candidate via an in-memory application of its hunks.
        lines = source.decode().splitlines(keepends=True) if isinstance(source, bytes) else source.splitlines(keepends=True)
        offset = 0
        for hunk in change:
            position = max(0, hunk.source_start - 1) + offset
            replacement = [line.value for line in hunk if not line.is_removed]
            lines[position:position + hunk.source_length] = replacement
            offset += hunk.target_length - hunk.source_length
        try:
            new_defs = definitions(''.join(lines), target_path)
            old_names = {d['qualname'] for d in defs}
            absent.extend(target_path + '::' + d['qualname'] for d in new_defs if d['qualname'] not in old_names)
            touched = set()
            for hunk in change:
                for line in hunk:
                    if not (line.is_added or line.is_removed):
                        continue
                    number = line.target_line_no if line.is_added else line.source_line_no
                    candidates = [d for d in (new_defs if line.is_added else defs)
                                  if d['decorator_start'] <= number <= d['end']]
                    if candidates:
                        touched.add(min(candidates, key=lambda d: d['end'] - d['decorator_start'])['qualname'])
                    else:
                        module_level_change = True
            functions.extend(d for d in defs if d['qualname'] in touched)
        except (SyntaxError, UnicodeError) as exc:
            errors.append(target_path + ': candidate AST unavailable: ' + str(exc))
    return {'files': sorted(files), 'functions': functions,
            'absent_from_base': sorted(set(absent)), 'mapping_errors': errors,
            'module_level_change': module_level_change}


def read_trace(path):
    data = {'codes': [], 'tests': {}, 'flags': {}, 'common': set(),
            'common_flags': set(), 'children': [], 'scopes': [], 'segment': 0}
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            item = json.loads(line)
            if item['version'] not in (2, 3) or item['codes_start'] != len(data['codes']):
                raise ValueError('Invalid/incomplete per-PID trace journal')
            data.update(pid=item['pid'], parent_pid=item['parent_pid'], segment=item.get('segment', 0))
            data['codes'].extend(item['codes'])
            data['tests'].update(item['tests'])
            data['flags'].update(item['flags'])
            data['common'].update(item['common'])
            data['common_flags'].update(item['common_flags'])
            data['children'].extend(item['children'])
            for record in item.get('scopes', []):
                if record['scope'] not in ('session', 'module', 'class', 'test'):
                    raise ValueError('Invalid trace scope')
                data['scopes'].append(record)
    return data


def load_traces(directory, run, runner, *, test_window_only=False):
    directory = Path(directory)
    if list(directory.glob('*.error')):
        raise ValueError('Tracer error marker present')
    records = {}
    for path in sorted(directory.glob('*.jsonl.gz')):
        data = read_trace(path)
        pid, segment = data['pid'], data['segment']
        stem = str(pid) + ('_' + str(segment) if segment else '')
        key = (pid, segment)
        if path.name != stem + '.jsonl.gz' or key in records:
            raise ValueError('Trace PID collision/identity mismatch')
        data['complete'] = all((directory / (stem + '.' + suffix)).is_file() for suffix in ('ready', 'done'))
        if data['complete']:
            for suffix in ('ready', 'done'):
                marker = json.loads((directory / (stem + '.' + suffix)).read_text())
                if marker.get('pid') != pid:
                    raise ValueError('Trace marker PID mismatch')
        records[key] = data
    expected = {event['pid'] for event in run.events if event['event'] == 'start'}
    for pid in expected:
        if (pid, 0) not in records or not records[(pid, 0)]['complete']:
            raise ValueError('Missing trace/readiness/completion marker for PID ' + str(pid))
    aliases = dict(run.raw_execution_map)
    aliases.update({tid: tid for tid in run.execution_id_map})
    native_codes, native_flags = {}, {}

    def calls(data, indices):
        return {tuple(data['codes'][i]) for i in indices}

    def add(raw_id, coverage, reasons):
        native = aliases.get(raw_id)
        if native is not None:
            native_codes.setdefault(native, set()).update(coverage)
            native_flags.setdefault(native, set()).update(reasons)

    def ancestor_chain(key):
        chain, seen = [], set()
        while key in records:
            if key in seen:
                raise ValueError('Cyclic trace process ancestry')
            seen.add(key)
            chain.append(records[key])
            key = (records[key]['parent_pid'], 0)
        return chain

    def window_calls(data, raw_id=None):
        return {tuple(data['codes'][i]) for record in data['scopes'] if record['scope'] == 'test'
                and (raw_id is None or raw_id in record['tests']) for i in record['codes']}

    # Flag absent/unfollowable Python children only in their spawn scope.
    # Non-Python observations never create incomplete coverage flags.
    for data in records.values():
        for child in data['children']:
            if child.get('python') is False:
                continue
            key = (child['pid'], child.get('segment', 0))
            descendant = records.get(key)
            if descendant is None or not descendant['complete']:
                targets = child['tests']
                if not targets:
                    data['common_flags'].add('unfollowed_child_process')
                for tid in targets:
                    data['flags'].setdefault(tid, []).append('unfollowed_child_process')

    for key, data in records.items():
        chain = ancestor_chain(key)
        common = set() if test_window_only else {c for item in chain for c in calls(item, item['common'])}
        common_flags = {reason for item in chain for reason in item['common_flags']}
        for raw_id, indices in data['tests'].items():
            coverage = window_calls(data, raw_id) if test_window_only else calls(data, indices)
            add(raw_id, common | coverage, common_flags | set(data['flags'].get(raw_id, ())))
        for child in data['children']:
            if child.get('python') is False or not child['tests']:
                continue
            descendant = records.get((child['pid'], child.get('segment', 0)))
            if descendant is None:
                continue
            coverage = window_calls(descendant) if test_window_only else set(map(tuple, descendant['codes']))
            for raw_id in child['tests']:
                add(raw_id, coverage, descendant['common_flags'])
    executed_statuses = {'passed', 'failed', 'error', 'crash', 'xfail', 'xpass', 'timeout'}
    executed = {r.test_id for r in run.execution_results if r.status.value in executed_statuses}
    missing = {tid for tid in executed if not native_codes.get(tid)}
    for tid in missing:
        native_flags.setdefault(tid, set()).add('executed_without_trace_record')
    codes, flags = {}, {}
    for native, owners in run.execution_id_map.items():
        for tid in owners:
            codes.setdefault(tid, set()).update(native_codes.get(native, ()))
            if native in executed:
                flags.setdefault(tid, set()).update(native_flags.get(native, ()))
    incomplete = {t for t in executed if native_flags.get(t)}
    worker_pids = sorted({pid for (pid, segment), data in records.items()
                          if (data['parent_pid'], 0) in records})
    return codes, flags, {
        'process_count': len({key[0] for key in records}), 'worker_pids': worker_pids,
        'workers_seen': len(worker_pids),
        'workers_with_tests': sum(bool(data['tests']) for (pid, segment), data in records.items() if pid in worker_pids),
        'executed_count': len(executed), 'incomplete_count': len(incomplete),
        'incomplete_fraction': len(incomplete) / len(executed) if executed else 0.,
        'incomplete_ids': sorted(incomplete), 'missing_record_ids': sorted(missing),
        'trace_nonempty': any(native_codes.values()),
        'scopes_seen': sorted({r['scope'] for d in records.values() for r in d['scopes']}),
        'child_observations': [c for d in records.values() for c in d['children']],
    }


def build_selection(tests, statuses, codes, flags, targets):
    file_kept, function_kept, reasons = [], [], {}
    executed_statuses = {'passed', 'failed', 'error', 'crash', 'xfail', 'xpass', 'timeout'}
    effective_flags = {t: set(flags.get(t, ())) if statuses.get(t) in executed_statuses else set() for t in tests}
    for tid in tests:
        calls = codes.get(tid, set())
        reason = []
        if not calls or statuses.get(tid) not in ('passed', 'failed'):
            reason.append('NO_USABLE_TRACE')
        if not calls and statuses.get(tid) in executed_statuses:
            effective_flags[tid].add('executed_without_trace_record')
        if effective_flags[tid]:
            reason.append('TRACE_INCOMPLETE')
        if targets['absent_from_base'] or targets['mapping_errors']:
            reason.append('BASE_MAP_INCOMPLETE')
        if reason:
            file_kept.append(tid)
            function_kept.append(tid)
            reasons[tid] = reason
            continue
        normalized = {(filename.removeprefix('/testbed/'), name, line) for filename, name, line in calls}
        file_hit = any(path in targets['files'] for path, _, _ in normalized)
        function_hit = any(path == d['path'] and name == d['name']
                           and line in (d['start'], d['decorator_start'])
                           for path, name, line in normalized for d in targets['functions'])
        # Module-level edits have no enclosing function: fall back to file hits.
        if not targets['functions'] or targets.get('module_level_change'):
            function_hit = file_hit
        if file_hit:
            file_kept.append(tid)
        if function_hit:
            function_kept.append(tid)
    if not set(function_kept) <= set(file_kept):
        raise ValueError('Function-level selection is not a subset of file-level selection')
    return {'file': file_kept, 'function': function_kept, 'retained_reasons': reasons,
            'trace_incomplete': sorted(t for t in tests if effective_flags[t]),
            'without_usable_trace': sorted(t for t in tests if not codes.get(t) or statuses.get(t) not in ('passed', 'failed')),
            'absent_from_base': targets['absent_from_base'], 'mapping_errors': targets['mapping_errors']}
