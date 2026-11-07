#!/usr/bin/env python3
"""POST-HOC, OFFLINE ONLY: attribute stored V2 evidence gaps and accepted skips.

No benchmark/harness imports, subprocesses, Docker, installs or execution of
archived source. Source inspection uses ast and tarfile readers only.
"""
import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import tarfile

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
PYTEST = re.compile(r'^(?P<id>\S.*?::\S.*?)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b(?P<tail>.*)', re.I)
DJANGO = re.compile(r'^(?P<name>\w+) \((?P<label>[^)]+)\)(?P<tail>.*)$')
DJ_STATUS = re.compile(r'\.\.\.\s*(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)', re.I)
STATUSES = {'PASSED': 'passed', 'FAILED': 'failed', 'ERROR': 'error', 'SKIPPED': 'skipped',
            'XFAIL': 'skipped', 'XPASS': 'passed', 'ok': 'passed', 'fail': 'failed', 'error': 'error', 'skipped': 'skipped',
            'expected failure': 'skipped', 'unexpected success': 'passed'}
SEVERITY = {'skipped': 0, 'passed': 1, 'failed': 2, 'error': 3}
GROUPS = ['cores_CPU', 'missing_dependency', 'platform', 'Python_version', 'other']


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def django_label(test):
    parts = test.split('::')
    module = parts[0][:-3].replace('/', '.')
    if module.startswith('tests.'):
        module = module[6:]
    return '.'.join([module] + parts[1:])


def literal(node):
    try:
        value = ast.literal_eval(node)
        return value if isinstance(value, str) else None
    except (ValueError, TypeError, SyntaxError):
        return None


def group_reason(reason):
    text = (reason or '').lower()
    if re.search(r'\bcores?\b|\bcpus?\b|need 2|two.core|multiprocess', text):
        return 'cores_CPU'
    if re.search(r'python\s*[<>=!0-9]|python version|pypy|cpython|sys\.version_info|python.?2|python.?3', text):
        return 'Python_version'
    if re.search(r'windows|win32|linux|darwin|macos|mac os|unix|posix|platform|only.*nix', text):
        return 'platform'
    if re.search(r'not installed|could not import|importorskip|no module named|missing depend|requires? (?:scipy|numpy|pandas|cupy|dask|pint|sparse|bottleneck|numba|pyarrow|matplotlib|docutils|sphinx|pytest|pillow|qt|wx|jinja)|(?:dependency|module|package).*(?:missing|unavailable)|(?:needs?|missing).*(?:scipy|numpy|cupy|dask|pint|sparse|pyarrow|matplotlib)', text):
        return 'missing_dependency'
    return 'other'


def parse_capture(text, runner):
    """Parse observed terminal outcomes; reject Django summary-derived fake IDs."""
    result, pending = {}, None
    for number, physical in enumerate(text.split('\n'), 1):
        for line in ANSI.sub('', physical).split('\r'):
            line = line.strip()
            if runner == 'django':
                header = DJANGO.match(line)
                if header:
                    name, label, tail = header.group('name', 'label', 'tail')
                    if name in ('OK', 'FAILED', 'FAIL', 'ERROR', 'Ran'):
                        pending = None
                        continue
                    if re.fullmatch(r'(?:[A-Za-z_]\w*|<locals>)(?:\.(?:[A-Za-z_]\w*|<locals>))*', label):
                        pending = (label if label.endswith('.' + name) else label + '.' + name, number)
                    else:
                        # A docstring such as "Ensure ('fieldpath', ClassName)"
                        # is not a new unittest header; retain the real pending ID.
                        tail = line
                else:
                    tail = line
                match = DJ_STATUS.search(tail)
                if match is None and pending is not None:
                    # Verbose unittest output can put a docstring/warning between
                    # the test header and a bare terminal status on a later line.
                    match = re.match(r'^(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)$', tail)
                if pending is None or match is None:
                    continue
                rid, header_line = pending
                word = match.group(1).lower()
                status = STATUSES[word]
                reason = match.group(2).strip().strip('"\'') if status == 'skipped' else ''
                if word == 'expected failure':
                    reason = 'expected failure'
                pending = None
                kind = 'loader_placeholder' if 'unittest.loader._FailedTest.' in rid else 'fixture' if rid.endswith(('.setUpClass', '.tearDownClass', '.setUpModule', '.tearDownModule')) else 'case'
            else:
                match = PYTEST.match(line)
                if match is None:
                    continue
                rid, word, tail = match.group('id', 'status', 'tail')
                word = word.upper()
                status = STATUSES[word]
                skip = re.search(r'^\s*\((.*?)\)', tail)
                reason = skip.group(1) if skip and status == 'skipped' else ''
                kind, header_line = 'case', number
            observation = {'status': status, 'line': number, 'header_line': header_line,
                           'reason': reason, 'flavor': word, 'kind': kind}
            if rid not in result or SEVERITY[status] >= SEVERITY[result[rid]['status']]:
                result[rid] = observation
    return result


def mapping_for(selected, runner):
    wanted = set(selected)
    labels = defaultdict(list)
    if runner == 'django':
        for test in selected:
            labels[django_label(test)].append(test)

    def map_id(rid):
        if runner != 'django':
            candidates = [rid, rid.split('[', 1)[0]] if '[' in rid else [rid]
            return list(dict.fromkeys(t for t in candidates if t in wanted))
        if rid in labels:
            return labels[rid]
        # Only a unique shortened framework label is admitted; ambiguity stays visible.
        candidates = [test for label, ids in labels.items() if label.endswith('.' + rid) for test in ids]
        return candidates if len(candidates) == 1 else []
    return map_id


class Inputs:
    def __init__(self):
        self.hashes = {}

    def bytes(self, path, expected=None):
        path = Path(path)
        data = path.read_bytes()
        digest = digest_bytes(data)
        if expected:
            assert digest == expected, str(path)
        previous = self.hashes.setdefault(str(path), digest)
        assert previous == digest, 'Input changed during analysis: ' + str(path)
        return data

    def json(self, path, expected=None):
        return json.loads(self.bytes(path, expected))


class Sources:
    def __init__(self, tasks, inputs):
        self.tasks, self.inputs = tasks, inputs
        self.archives, self.cache, self.objects, self.source_refs = {}, {}, {}, {}

    def module(self, task, name):
        key = (task, name)
        if key in self.cache:
            return self.cache[key]
        if task not in self.archives:
            archive = Path('/home/sankalp/cg_repos/task_archives') / (task + '.tar')
            if not archive.exists():
                return None
            digest = file_sha(archive)
            assert digest == self.tasks[task]['base_archive_sha256'], str(archive)
            self.inputs.hashes[str(archive)] = digest
            self.archives[task] = tarfile.open(archive)
        archive = self.archives[task]
        try:
            member = archive.getmember('testbed/' + name)
        except KeyError:
            self.cache[key] = None
            return None
        data = archive.extractfile(member).read()
        expected = self.tasks[task]['base_source_sha256'].get(name)
        if expected:
            assert digest_bytes(data) == expected, (task, name)
        text = data.decode('utf-8', 'replace')
        reference = archive.name + '!testbed/' + name
        self.source_refs[reference] = digest_bytes(data)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        value = {'text': text, 'tree': tree, 'reference': reference, 'lines': text.splitlines()}
        self.cache[key] = value
        return value

    def object(self, task, test):
        key = (task, test)
        if key in self.objects:
            return self.objects[key]
        parts = test.split('[', 1)[0].split('::')
        module = self.module(task, parts[0])
        result = {'kind': 'unknown', 'non_test': 'unknown', 'source': '', 'line': 0,
                  'node': None, 'module': module, 'class_node': None}
        if not module or not module['tree']:
            self.objects[key] = result
            return result
        node, nested, cls = module['tree'], False, None
        for name in parts[1:]:
            found = None
            for child in reversed(getattr(node, 'body', [])):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and child.name == name:
                    found = child
                    break
                if isinstance(child, (ast.Assign, ast.AnnAssign)):
                    targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                    if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                        found = child
                        break
            if found is None:
                result.update(kind='not_defined_at_selected_path', non_test='unknown')
                self.objects[key] = result
                return result
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested = True
            if isinstance(found, ast.ClassDef):
                cls = found
            node = found
        decorators = getattr(node, 'decorator_list', [])
        property_decorator = next((d for d in decorators if
            (isinstance(d, ast.Name) and d.id in ('property', 'cached_property')) or
            (isinstance(d, ast.Attribute) and d.attr in ('property', 'cached_property'))), None)
        if property_decorator:
            kind, non_test = 'property', True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            kind = 'class_attribute' if cls else 'module_attribute'
            non_test = isinstance(node.value, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set))
        elif nested:
            kind, non_test = 'nested_helper', True
        elif isinstance(node, ast.ClassDef):
            kind, non_test = 'class', 'unknown'
        else:
            kind, non_test = 'function', 'unknown'
        result.update(kind=kind, non_test=non_test, source=module['reference'], line=node.lineno,
                      node=node, class_node=cls)
        self.objects[key] = result
        return result

    def skip_reason(self, task, test, captured):
        obj = self.object(task, test)
        node, module = obj['node'], obj['module']
        candidates = []
        if node and module:
            decorators = getattr(node, 'decorator_list', []) + getattr(obj['class_node'], 'decorator_list', [])
            if any(isinstance(d, ast.Attribute) and d.attr == 'needs_two_cores' for d in decorators):
                hook = self.module(task, 'tests/conftest.py')
                if hook:
                    for i, line in enumerate(hook['lines'], 1):
                        m = re.search(r'reason=["\'](Need 2 or more cores[^"\']*)', line)
                        if m:
                            return m.group(1), 'cores_CPU', 'source_marker_hook', hook['reference'], i
            nodes = list(decorators)
            # Literal reasons in test body and module collection guards are candidates,
            # never evaluation of condition expressions or imported functions.
            nodes += list(ast.walk(node))
            for top in module['tree'].body:
                if not isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    nodes += list(ast.walk(top))
            for item in nodes:
                if not isinstance(item, ast.Call):
                    continue
                func = item.func.attr if isinstance(item.func, ast.Attribute) else item.func.id if isinstance(item.func, ast.Name) else ''
                values = [literal(k.value) for k in item.keywords if k.arg == 'reason']
                if func in ('skip', 'skipIf', 'skipUnless', 'skipif') and item.args:
                    values.append(literal(item.args[-1]))
                if func == 'importorskip' and item.args:
                    package = literal(item.args[0])
                    if package:
                        values.append('importorskip(' + package + ')')
                for value in values:
                    if value:
                        candidates.append((value, item.lineno))
        candidates = list(dict.fromkeys(candidates))
        prefix = re.sub(r'\.{3}|…', '', captured or '').strip().strip('"\'')
        matched = [(value, line) for value, line in candidates if prefix and value.startswith(prefix)]
        if len(matched) == 1 and ('...' in captured or '…' in captured):
            value, line = matched[0]
            return value, group_reason(value), 'source_matches_truncated_capture', module['reference'], line
        if captured:
            return captured, group_reason(captured), 'captured_truncated' if '...' in captured or '…' in captured else 'captured', '', 0
        if len(candidates) == 1:
            value, line = candidates[0]
            return value, group_reason(value), 'source_candidate_not_runtime_confirmed', module['reference'], line
        return 'reason not preserved; mechanism not uniquely identified', 'other', 'unknown', '', 0

    def class_setup_skip(self, task, test, batch):
        """Match an unnamed captured setup skip to a literal class guard; no outcome invented."""
        if not batch:
            return None
        bare = []
        for i, line in enumerate(batch['text'].splitlines()):
            match = re.fullmatch(r'''skipped\s+(["'])(.*?)\1''', line.strip())
            if match:
                bare.append((match.group(2), batch['line'] + i))
        if not bare:
            return None
        obj = self.object(task, test)
        cls = obj['class_node']
        if cls is None:
            return None
        for setup in getattr(cls, 'body', []):
            if not isinstance(setup, ast.FunctionDef) or setup.name != 'setUpClass':
                continue
            for node in ast.walk(setup):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                reason = literal(node.args[0])
                if name == 'SkipTest' and reason:
                    for captured, line in bare:
                        if captured == reason:
                            return {'reason': captured, 'line': line, 'source': obj['source'],
                                    'source_line': node.lineno, 'class': cls.name,
                                    'confidence': 'bare captured SkipTest reason matches selected class setUpClass source; no individual test body observed'}
        return None

    def close(self):
        for archive in self.archives.values():
            archive.close()


def requested_batch_index(call, selected, runner, raw_bytes):
    events = call['run'].get('events', [])
    by_label = {django_label(t) if runner == 'django' else t: t for t in selected}
    result = {}
    for i, start in enumerate(events):
        if start.get('event') != 'start':
            continue
        end = next((e for e in events[i + 1:] if e.get('event') == 'end' and e.get('batch') == start['batch']), None)
        if end is None or end.get('split'):
            continue
        offset, finish = start.get('offset', 0), end.get('offset', len(raw_bytes))
        text = ANSI.sub('', raw_bytes[offset:finish].decode('utf-8', 'replace'))
        collection_skip = runner != 'django' and bool(re.search(r'collected\s+0\s+items[^\n]*skipped|collected[^\n]*/\s*\d+\s+skipped', text))
        entry = {'batch': start['batch'], 'returncode': end['returncode'], 'collection_skip': collection_skip,
                 'line': raw_bytes[:offset].count(b'\n') + 1, 'text': text}
        for label in start.get('ids', []):
            result[by_label.get(label, label)] = entry
    return result


def batch_details(task, call_index, call, selected, runner, raw_bytes, parsed, sources, phase):
    run = call['run']
    events = run.get('events', [])
    mapper = mapping_for(selected, runner)
    natives = {r['test_id']: r['status'] for r in run.get('results', [])}
    by_label = {django_label(t) if runner == 'django' else t: t for t in selected}
    aborted, per_test = [], defaultdict(list)
    for start_index, start in enumerate(events):
        if start.get('event') != 'start':
            continue
        end = next((e for e in events[start_index + 1:] if e.get('event') == 'end' and e.get('batch') == start['batch']), None)
        if not end or end.get('split') or end.get('returncode') == 0:
            continue
        begin, finish = start.get('offset', 0), end.get('offset', len(raw_bytes))
        segment = raw_bytes[begin:finish].decode('utf-8', 'replace')
        cleaned = ANSI.sub('', segment)
        segment_cases = parse_capture(segment, runner)
        real_outcomes = [r for r in segment_cases.values() if r['kind'] == 'case' and r['status'] in ('passed', 'failed', 'skipped')]
        startup = bool(re.search(r'No module named (?:pytest|_pytest)|can.t open file.*(?:pytest|runtests)', cleaned))
        environment_guard = 'Aborting: A GIS database backend is required to run gis_tests.' in cleaned
        loader = bool(re.search(r'TypeError:|ERROR: not found:|found no collectors|ERROR collecting|ERROR: file or directory not found:|ImportError while loading conftest|ModuleNotFoundError:|ImportError:|unittest\.loader\._FailedTest|Failed to import test module|AttributeError:.*(?:has no attribute|no such)', cleaned)) or environment_guard
        if real_outcomes or not (loader or startup or end.get('returncode') in (2, 4)):
            continue
        requested = [by_label.get(s, s) for s in start.get('ids', [])]
        suspects, confidence = [], 'not_named_in_capture'
        for test in requested:
            native_label = django_label(test) if runner == 'django' else test
            if ('not found: ' + native_label) in cleaned or ('not found: /testbed/' + native_label) in cleaned:
                suspects.append(test)
        if suspects:
            confidence = 'explicit_not_found_label'
        if not suspects and 'property object' in cleaned:
            suspects = [t for t in requested if sources.object(task, t)['kind'] == 'property']
            confidence = 'unique_base_property_consistent_with_traceback' if len(suspects) == 1 else 'multiple_base_property_candidates'
        callable_name = re.search(r'TypeError:\s*(?:[\w.]+\.)?(\w+)\(\)\s+(?:missing|takes|got)', cleaned)
        if not suspects and callable_name and 'unittest/loader.py' in cleaned:
            suspects = [t for t in requested if t.split('::')[-1] == callable_name.group(1)]
            if suspects:
                confidence = 'method_named_in_loader_signature_error' if len(suspects) == 1 else 'method_name_multiple_label_candidates'
        if environment_guard:
            suspects = [t for t in requested if t.startswith('tests/gis_tests/')]
            confidence = 'explicit_GIS_module_environment_guard'
        collecting_modules = re.findall(r'ERROR collecting\s+([^\s_][^\s]*\.py)', cleaned)
        if not suspects and collecting_modules:
            suspects = [t for t in requested if any(t.split('::')[0].endswith(module.replace('/testbed/', '')) for module in collecting_modules)]
            if suspects:
                confidence = 'explicit_collection_module_not_an_individual_test'
        if not suspects and 'Failed to import test module' in cleaned:
            names = re.findall(r'Failed to import test module:\s*([^\n]+)', cleaned)
            suspects = [t for t in requested if any(n.strip() in (django_label(t), django_label(t).split('.')[-1]) for n in names)]
            if suspects:
                confidence = 'failed_import_label'
        if not suspects and not startup:
            bad = [t for t in requested if sources.object(task, t)['non_test'] is True]
            if bad:
                suspects, confidence = bad, 'static_non_test_candidates_not_proven_unique_cause'
        offender_kinds = [sources.object(task, t)['kind'] for t in suspects]
        if confidence.startswith('method_named') or confidence.startswith('method_name_multiple'):
            offender_kinds = ['helper_callable_for_unittest_loader' for t in suspects]
        if environment_guard:
            offender_kinds = ['GIS_environment_guard']
        if confidence == 'explicit_collection_module_not_an_individual_test':
            offender_kinds = ['module_collection_error']
        not_run = [t for t in requested if natives.get(t) == 'not_run' and not any(t in mapper(rid) for rid in segment_cases)]
        collateral = [t for t in not_run if t not in suspects]
        diagnostics = [line.strip() for line in cleaned.splitlines() if re.search(r'(?:TypeError:|ImportError:|ModuleNotFoundError:|AttributeError:|ERROR: not found:|ERROR collecting|No module named pytest|Failed to import test module|Aborting:)', line)]
        record = {'instance_id': task, 'tree': phase, 'call_index': call_index,
            'scope': 'initial' if call_index < 2 else 'confirmation', 'batch': start['batch'],
            'abort_kind': 'runner_start_failure' if startup else 'environment_guard_abort' if environment_guard else 'load_or_collection_abort',
            'returncode': end['returncode'], 'offending_label': '; '.join(django_label(t) if runner == 'django' else t for t in suspects) or 'NOT_IDENTIFIED_FROM_CAPTURE',
            'offending_selected_ids': json.dumps(suspects), 'label_identification': confidence,
            'base_object_kinds': '; '.join(offender_kinds) or 'unknown',
            'non_test_object_at_base': True if confidence.startswith('method_named') or confidence.startswith('method_name_multiple') else False if environment_guard or confidence == 'explicit_collection_module_not_an_individual_test' else all(sources.object(task, t)['non_test'] is True for t in suspects) if suspects and all(sources.object(task, t)['non_test'] != 'unknown' for t in suspects) else 'unknown',
            'requested_count': len(requested), 'not_run_count': len(not_run),
            'collateral_not_run_count': len(collateral) if suspects else '',
            'unattributed_not_run_count': len(not_run) if not suspects else 0,
            'collateral_selected_ids': json.dumps(collateral if suspects else []),
            'requested_selected_ids': json.dumps(requested),
            'diagnostic': ' | '.join(diagnostics)[:1400],
            'evidence_path': run['evidence_files']['runner.raw'],
            'line_start': raw_bytes[:begin].count(b'\n') + 1, 'line_end': raw_bytes[:finish].count(b'\n'),
            'events_path': run['evidence_files'].get('events.jsonl', ''),
            'base_source_references': '; '.join(sources.object(task, t)['source'] + ':' + str(sources.object(task, t)['line']) for t in suspects)}
        aborted.append(record)
        for test in requested:
            per_test[test].append(record)
    return aborted, per_test


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, sort_keys=True)
        stream.write('\n')


def normalized_path(path, repo):
    path = Path(path)
    if path.exists():
        return path
    marker = '/cis695-agent-reliability/'
    if marker in str(path):
        return repo / str(path).split(marker, 1)[1]
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--frozen', type=Path, required=True)
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists(), 'Use a fresh output directory; never overwrite frozen inputs'
    inputs = Inputs()
    evidence_manifest = Path('/home/sankalp/projects/cis695-artifacts/local_evidence_manifest_20261106.sha256')
    manifest_bytes = inputs.bytes(evidence_manifest, '11ad4bb7ea40b987d20bcbbb6afdd030314ad1379c2956dada570e7c1ff87642')
    expected = dict((line.split('  ', 1)[1], line.split('  ', 1)[0]) for line in manifest_bytes.decode().splitlines())
    tasks = {r['instance_id']: r for r in inputs.json(args.frozen / 'tasks.json', expected[str(args.frozen / 'tasks.json')])}
    assert len(tasks) == 83
    sources = Sources(tasks, inputs)
    call_summaries, batch_rows, skip_rows, gap_rows, ledger, task_rows, replay_rows, pass_error_rows = [], [], [], [], [], [], [], []
    collection_skip_rows, class_skip_rows = [], []
    history_inventory, history_skips = [], []
    current_data = {}
    all_capture_paths = set()
    for ordinal, (task, meta) in enumerate(tasks.items(), 1):
        native_path = args.results / 'tasks' / task / 'v2/result.json'
        row = inputs.json(native_path, expected[str(native_path)])
        current_data[task] = row
        selected = row.get('selected_tests') or []
        frozen_selection = inputs.json(args.frozen / meta['selections']['v2'], expected[str(args.frozen / meta['selections']['v2'])])
        assert selected == frozen_selection['tests']
        runner = meta['runner']['name']
        task_causes, native_gap_causes, gaps_by_key = Counter(), Counter(), {}
        initial = {}
        for call_index, call in enumerate(row.get('calls', [])):
            run, phase = call['run'], 'patched' if call['patched'] else 'base'
            call_selected = list(call.get('requested', run.get('requested_tests', selected)))
            assert set(call_selected) <= set(selected), (task, call_index)
            for name, path in run['evidence_files'].items():
                inputs.bytes(Path(path), run['evidence_sha256'][name])
                all_capture_paths.add(path)
            capture_path = Path(run['evidence_files']['runner.raw'])
            raw_bytes = inputs.bytes(capture_path, run['evidence_sha256']['runner.raw'])
            text = raw_bytes.decode('utf-8', 'replace')
            parsed = parse_capture(text, runner)
            mapper = mapping_for(call_selected, runner)
            batch_index = requested_batch_index(call, call_selected, runner, raw_bytes)
            failed_loader_methods = {rid.rsplit('.', 1)[-1] for rid, value in parsed.items() if value['kind'] == 'loader_placeholder' and value['status'] == 'error'}
            fixture_prefixes = {rid.rsplit('.', 1)[0] + '.' for rid, value in parsed.items() if value['kind'] == 'fixture' and value['status'] == 'error'}
            mapped = defaultdict(list)
            unmapped = []
            for rid, observed in parsed.items():
                ids = mapper(rid)
                if len(ids) == 1 and observed['kind'] == 'case':
                    mapped[ids[0]].append((rid, observed))
                else:
                    unmapped.append((rid, observed))
            aborted, abort_map = batch_details(task, call_index, call, call_selected, runner, raw_bytes, parsed, sources, phase)
            batch_rows.extend(aborted)
            native_results = {r['test_id']: r for r in run.get('results', [])}
            original_raw = {r['test_id'] for r in run.get('raw_results', [])}
            removed_fake = {rid for rid in original_raw - set(parsed) if runner == 'django' and re.match(r'^(?:skipped=|expected failures=|failures=|errors=|unexpected successes=)', rid)}
            reasons = []
            events = run.get('events', [])
            starts = [e for e in events if e.get('event') == 'start']
            ends = [e for e in events if e.get('event') == 'end']
            complete_physical = bool(events and events[-1].get('event') == 'complete') and {e['batch'] for e in starts} == {e['batch'] for e in ends}
            if run.get('timed_out'):
                reasons.append('timeout')
            if not complete_physical:
                reasons.append('unfinished_capture_or_batch')
            for end in ends:
                if end.get('split') or end['returncode'] == 0:
                    continue
                start = next(e for e in starts if e['batch'] == end['batch'])
                segment = raw_bytes[start.get('offset', 0):end.get('offset', len(raw_bytes))].decode('utf-8', 'replace')
                outcomes = parse_capture(segment, runner)
                if end['returncode'] not in (0, 1) or not any(v['status'] in ('failed', 'error') for v in outcomes.values()):
                    reasons.append('collection_or_runner_error')
            if any(v['status'] == 'error' for v in parsed.values()):
                reasons.append('collection_or_test_error')
            if unmapped:
                reasons.append('unmapped_or_ambiguous_raw_id')
            if call_index < 2:
                initial[phase] = {'mapped': mapped, 'parsed': parsed, 'reasons': reasons,
                                  'native': native_results, 'call': call, 'removed_fake': removed_fake}
            for test in call_selected:
                native = native_results.get(test, {'status': 'missing'})['status']
                cases = mapped.get(test, [])
                if native not in ('not_run', 'timeout', 'error', 'missing'):
                    continue
                if native == 'error':
                    cause, line, detail = 'collection_or_test_error', (cases[0][1]['line'] if cases else 1), 'Admitted selected ERROR; this is not a missing parser admission'
                elif cases:
                    if '[' in cases[0][0] and cases[0][0].split('[', 1)[0] == test:
                        cause = 'parameter_family_admission'
                    else:
                        cause = 'output_parsing'
                    line = cases[0][1]['line']
                    detail = 'Concrete outcomes exist in stored capture; selected-ID admission was missing'
                elif abort_map.get(test):
                    abort = abort_map[test][0]
                    cause = 'sympy_runner_mismatch' if task.startswith('sympy__') and abort['abort_kind'] == 'runner_start_failure' else 'environment_guard_abort' if abort['abort_kind'] == 'environment_guard_abort' else 'collection_or_runner_error'
                    line, detail = abort['line_start'], abort['diagnostic']
                elif native == 'timeout' or run.get('timed_out'):
                    cause, line, detail = 'timeout_or_not_launched', 1, 'Recorded timeout / unreached request'
                elif native == 'error':
                    cause, line, detail = 'collection_or_test_error', 1, 'Recorded selected ERROR; no successful body observation'
                elif runner == 'django' and (test.split('::')[-1] in failed_loader_methods or any(django_label(test).startswith(prefix) for prefix in fixture_prefixes)):
                    cause, line, detail = 'collection_or_test_error', 1, 'Captured class/module fixture or failed-loader placeholder ERROR prevents a concrete selected outcome'
                elif runner == 'django' and any(part in failed_loader_methods for part in test.split('::')[1:]):
                    cause, line, detail = 'collection_or_test_error', 1, 'Captured failed-loader placeholder names a missing selected class or method; other co-batched tests may still run'
                elif runner == 'django' and sources.class_setup_skip(task, test, batch_index.get(test)):
                    matched_skip = sources.class_setup_skip(task, test, batch_index.get(test))
                    cause, line, detail = 'class_setup_skip', matched_skip['line'], matched_skip['reason']
                    class_skip_rows.append({'instance_id': task, 'tree': phase, 'call_index': call_index,
                        'scope': 'initial' if call_index < 2 else 'confirmation', 'selected_test_id': test,
                        'native_status': native, 'reason_group': group_reason(matched_skip['reason']),
                        'reason': matched_skip['reason'], 'reason_quality': matched_skip['confidence'],
                        'evidence_path': str(capture_path), 'line': line,
                        'source_reference': matched_skip['source'], 'source_line': matched_skip['source_line'],
                        'unit': 'selected request blocked by class setup SKIP, not a concrete test-body outcome'})
                elif batch_index.get(test, {}).get('collection_skip'):
                    cause, line, detail = 'collection_skip_or_deselection', batch_index[test]['line'], 'This request’s own batch reports collection skipping; no per-test terminal outcome'
                    reason, group, quality, ref, source_line = sources.skip_reason(task, test, '')
                else:
                    cause, line, detail = 'unreported_selected_identity', 1, 'Selected request has no concrete observed outcome; exact mechanism unresolved'
                evidence = {'instance_id': task, 'tree': phase, 'call_index': call_index,
                    'scope': 'initial' if call_index < 2 else 'confirmation', 'test_id': test,
                    'native_status': native, 'cause': cause, 'detail': detail,
                    'concrete_cases': len(cases), 'evidence_path': str(capture_path), 'line': line}
                gap_rows.append(evidence)
                if not cases and batch_index.get(test, {}).get('collection_skip'):
                    reason, group, quality, ref, source_line = sources.skip_reason(task, test, '')
                    collection_skip_rows.append({'instance_id': task, 'tree': phase, 'call_index': call_index,
                        'scope': 'initial' if call_index < 2 else 'confirmation', 'selected_test_id': test,
                        'batch': batch_index[test]['batch'], 'native_status': native,
                        'reason_group': group, 'reason': reason, 'reason_quality': quality,
                        'unit': 'selected request in a collection-skipping batch; static source explains candidates, not a test-body SKIPPED observation',
                        'evidence_path': str(capture_path), 'line': batch_index[test]['line'],
                        'source_reference': ref, 'source_line': source_line})
                if call_index < 2:
                    task_causes[cause] += 1
                    gaps_by_key[phase, test] = evidence
            for rid, observed in parsed.items():
                if observed['status'] != 'skipped':
                    continue
                ids = mapper(rid)
                for test in ids or ['UNMAPPED:' + rid]:
                    if observed['flavor'] in ('XFAIL', 'expected failure'):
                        reason, group, quality, source_ref, source_line = 'expected failure (XFAIL)', 'other', 'captured_expected_failure_status', '', 0
                    else:
                        reason, group, quality, source_ref, source_line = sources.skip_reason(task, test, observed['reason']) if len(ids) == 1 else (observed['reason'] or 'reason not preserved', group_reason(observed['reason']), 'unmapped_or_ambiguous', '', 0)
                    native = native_results.get(test, {}).get('status', 'missing')
                    current_pass = row.get('signal') == 'PASS'
                    original_pass = row.get('original_signal') == 'PASS'
                    frozen_recovered_case = any(r['test_id'] == rid and r['status'] == 'skipped' and run.get('raw_id_map', {}).get(rid) == [test] for r in run.get('raw_results', []))
                    skip_rows.append({'scope': 'current_full83', 'instance_id': task, 'tree': phase,
                        'call_index': call_index, 'call_scope': 'initial' if call_index < 2 else 'confirmation',
                        'selected_test_id': test, 'raw_test_id': rid, 'native_selected_status': native,
                        'reason_group': group, 'captured_reason': observed['reason'], 'reason': reason,
                        'reason_quality': quality, 'skip_flavor': observed['flavor'],
                        'environment_conditioned_group': group != 'other', 'current_task_verdict': row.get('signal'),
                        'original_task_verdict': row.get('original_signal'), 'task_completeness': row.get('completeness'),
                        'accepted_for_current_PASS_completeness': current_pass and len(ids) == 1 and (native == 'skipped' or (native == 'not_run' and frozen_recovered_case)),
                        'accepted_in_original_PASS_scoring': original_pass and native == 'skipped',
                        'evidence_path': str(capture_path), 'line': observed['line'],
                        'source_reference': source_ref, 'source_line': source_line})
            call_summaries.append({'instance_id': task, 'tree': phase, 'call_index': call_index,
                'scope': 'initial' if call_index < 2 else 'confirmation', 'selected': len(call_selected),
                'parsed_cases': len(parsed), 'mapped_families': len(mapped), 'unmapped_cases': len(unmapped),
                'removed_summary_pseudo_ids': len(removed_fake), 'batch_aborts': len(aborted),
                'timed_out': run.get('timed_out'), 'physical_capture_finished': complete_physical,
                'replay_runner_gap_reasons': ';'.join(sorted(set(reasons))), 'evidence_path': str(capture_path)})
        for index, message in enumerate(row.get('incompleteness', [])):
            match = re.match(r'^(base|patched): (.*): (not_run|timeout|error|missing)$', message)
            if match and (match[1], match[2]) in gaps_by_key:
                detail = gaps_by_key[match[1], match[2]]
                cause, evidence_path, line = detail['cause'], detail['evidence_path'], detail['line']
            elif 'concrete raw test IDs differ' in message:
                cause, evidence_path, line = 'base_patched_id_set_difference', str(native_path), 1
            elif 'unmatched raw ID:' in message or 'unaccounted raw ID:' in message:
                rid = re.split(r'(?:unmatched|unaccounted) raw ID: ', message, maxsplit=1)[-1]
                cause = 'output_parsing' if rid.startswith(('skipped=', 'expected failures=', 'failures=', 'errors=', 'unexpected successes=')) else 'collection_or_runner_error' if 'unittest.loader._FailedTest.' in rid else 'raw_id_mapping'
                evidence_path, line = str(native_path), 1
            elif 'ambiguous raw ID:' in message:
                cause, evidence_path, line = 'raw_id_mapping', str(native_path), 1
            elif 'raw ERROR:' in message:
                cause, evidence_path, line = 'collection_or_test_error', str(native_path), 1
            elif 'pass timed out' in message:
                cause, evidence_path, line = 'timeout_or_not_launched', str(native_path), 1
            elif 'infrastructure:' in message or 'capture unavailable' in message:
                cause, evidence_path, line = 'sympy_runner_mismatch' if task.startswith('sympy__') else 'collection_or_runner_error', str(native_path), 1
            else:
                cause, evidence_path, line = 'unclassified_original_gap', str(native_path), 1
            ledger.append({'instance_id': task, 'original_gap_index': index, 'original_gap': message,
                           'cause': cause, 'evidence_path': evidence_path, 'line': line,
                           'native_record': str(native_path), 'json_pointer': '/incompleteness/' + str(index)})
            native_gap_causes[cause] += 1
        for phase in ['base', 'patched']:
            if phase in initial:
                for rid, value in initial[phase]['parsed'].items():
                    if value['status'] == 'error':
                        task_causes['collection_or_test_error_observed'] += 1
        if 'base' in initial and 'patched' in initial:
            b, p = initial['base'], initial['patched']
            complete, strict = True, True
            paired_cases, transitions = 0, 0
            for test in selected:
                bc, pc = dict(b['mapped'].get(test, [])), dict(p['mapped'].get(test, []))
                if not bc or set(bc) != set(pc):
                    complete = strict = False
                for rid in bc.keys() & pc.keys():
                    paired_cases += 1
                    if 'error' in (bc[rid]['status'], pc[rid]['status']):
                        complete = strict = False
                    if 'skipped' in (bc[rid]['status'], pc[rid]['status']):
                        strict = False
                    if bc[rid]['status'] == 'passed' and pc[rid]['status'] == 'error':
                        pass_error_rows.append({'instance_id': task, 'selected_test_id': test, 'raw_test_id': rid,
                            'base_status': 'passed', 'patched_status': 'error',
                            'evidence_path': p['call']['run']['evidence_files']['runner.raw'], 'line': pc[rid]['line']})
                        task_causes['pass_to_exception_scored_error'] += 1
                    if bc[rid]['status'] == 'passed' and pc[rid]['status'] == 'failed':
                        transitions += 1
            if b['reasons'] or p['reasons']:
                complete = strict = False
            b_ids, p_ids = set(b['parsed']), set(p['parsed'])
            if b_ids != p_ids:
                complete = strict = False
                task_causes['base_patched_id_set_difference'] += len(b_ids ^ p_ids)
            if row.get('signal') == 'FAIL':
                assert transitions > 0, 'Fixed parser lost an original V2 FAIL: ' + task
            replay_rows.append({'instance_id': task, 'native_signal': row.get('signal'),
                'native_completeness': row.get('completeness'), 'parser_only_complete_skip_compatible': complete,
                'parser_only_complete_skip_strict': strict, 'paired_concrete_cases': paired_cases,
                'base_pass_patched_fail_observations': transitions,
                'postparse_id_set_difference': len(b_ids ^ p_ids),
                'parser_only_recovered_INCOMPLETE': row.get('signal') == 'INCOMPLETE' and complete,
                'parser_only_binary_evidence_from_NOT_AVAILABLE': row.get('signal') == 'NOT_AVAILABLE' and complete,
                'scope': 'offline diagnostic; no new native verdict or confirmation inferred'})
        else:
            replay_rows.append({'instance_id': task, 'native_signal': row.get('signal'),
                'native_completeness': row.get('completeness'), 'parser_only_complete_skip_compatible': False,
                'parser_only_complete_skip_strict': False, 'paired_concrete_cases': 0,
                'base_pass_patched_fail_observations': 0, 'postparse_id_set_difference': 0,
                'parser_only_recovered_INCOMPLETE': False, 'parser_only_binary_evidence_from_NOT_AVAILABLE': False,
                'scope': 'no selected executions; cannot infer PASS'})
            if not selected:
                task_causes['empty_selection'] = 1
        task_rows.append({'instance_id': task, 'signal': row.get('signal'), 'original_signal': row.get('original_signal'),
                          'completeness': row.get('completeness'), 'selected': len(selected),
                          'native_gap_count': len(row.get('incompleteness', [])), 'cause_counts': dict(task_causes),
                          'native_gap_cause_counts': dict(native_gap_causes)})
        print('CURRENT', ordinal, '/83', task, row.get('signal'), 'abort rows', len(batch_rows), 'skip rows', len(skip_rows), flush=True)
    # All 780 captured files are verified, including SCG's 26 calls; attribution
    # tables are explicitly V2-only rather than pooling different selections.
    for task in tasks:
        scg_path = args.results / 'tasks' / task / 'scg/result.json'
        scg = inputs.json(scg_path, expected[str(scg_path)])
        for call in scg.get('calls', []):
            for name, path in call['run']['evidence_files'].items():
                inputs.bytes(Path(path), call['run']['evidence_sha256'][name])
                all_capture_paths.add(path)
    assert len(all_capture_paths) == 780
    complete = inputs.json(args.results / 'collection_complete.json')
    assert file_sha(args.results / 'results.json') == complete['results_sha256']
    inputs.hashes[str(args.results / 'results.json')] = complete['results_sha256']
    analyze_histories(args, tasks, inputs, sources, history_inventory, history_skips)
    write_outputs(args, inputs, sources, current_data, task_rows, call_summaries, batch_rows, skip_rows,
                  gap_rows, ledger, replay_rows, pass_error_rows, history_inventory, history_skips, all_capture_paths,
                  collection_skip_rows, class_skip_rows)
    sources.close()


def analyze_histories(args, tasks, inputs, sources, inventory, skips):
    """Canonical old native records, not oracle projections or derived duplicates."""
    def history_skip(task, selected, rid, native, reason, phase, record, path, line,
                     quality, complete, verdict='PASS', patch_binding='unknown', call_index=0):
        full_reason, group, reason_quality, source_ref, source_line = sources.skip_reason(task, selected, reason)
        skips.append({'scope': quality, 'instance_id': task, 'tree': phase, 'call_index': call_index,
            'selected_test_id': selected, 'raw_test_id': rid, 'native_selected_status': native,
            'reason_group': group, 'captured_reason': reason, 'reason': full_reason,
            'reason_quality': reason_quality, 'current_task_verdict': verdict,
            'task_completeness': complete, 'accepted_for_PASS_completeness': complete == 'COMPLETE',
            'acceptance_limit': 'paired/capture accounting available' if complete == 'COMPLETE' else 'Historical PASS includes this baseline skip; patched status/completeness not preserved',
            'patch_binding': patch_binding, 'source_record': str(record),
            'evidence_path': str(path), 'line': line,
            'source_reference': source_ref, 'source_line': source_line})

    for path in sorted((args.repo / 'runs').glob('*/tasks/*/verification_record.full.json')):
        task = path.parent.name
        if task not in tasks:
            continue
        record = inputs.json(path)
        native = record.get('regression') or {}
        verdict = (native.get('findings') or {}).get('signal', native.get('outcome'))
        if verdict != 'PASS':
            continue
        patch = record.get('patch_sha256', '').replace('sha256:', '')
        bound = patch == tasks[task]['patch_sha256']
        cache = path.parents[2] / '_baseline_cache' / (task + '.baseline.json')
        selected = set(record.get('selected_tests', []))
        baseline_skips = []
        if cache.exists():
            baseline = inputs.json(cache)
            baseline_skips = [r for r in baseline.get('results', []) if r['test_id'] in selected and r['status'] == 'skipped']
            lines = cache.read_text().splitlines()
            for result in baseline_skips:
                if not bound:
                    continue
                line = next((i for i, text in enumerate(lines, 1) if result['test_id'] in text), 1)
                history_skip(task, result['test_id'], result['test_id'], 'skipped', result.get('message', ''),
                    'base_only', path, cache, line, 'historical_baseline_cache', 'NOT_RECORDED',
                    patch_binding='exact_frozen_candidate_hash')
        inventory.append({'instance_id': task, 'source_record': str(path), 'kind': 'historical_native_verification',
            'native_verdict': verdict, 'completeness': 'NOT_RECORDED', 'patch_binding': 'exact_frozen_candidate_hash' if bound else 'different_candidate_excluded_from_counts',
            'selected_count': len(selected), 'baseline_cache_available': cache.exists(),
            'known_baseline_skip_count': len(baseline_skips) if cache.exists() else '',
            'paired_skip_evidence_available': False, 'excluded_run_name': path.parents[2].name.startswith('_excluded'),
            'limitation': 'Baseline cache linked by run/task path, not a recorded cache digest; no patched per-test statuses in this envelope'})

    # Older native pairs retain structured per-case evidence even when a former
    # absolute capture path must be relocated to this repository.
    native_pairs = list((args.repo / 'reports/v2_discovery_cleanup/comparison_final/docker').glob('*/*/result.json'))
    native_pairs += list((args.results.parent.parent / 'pilot_20261105T183041_929325Z/results/tasks').glob('*/v2/result.json'))
    for path in sorted(native_pairs):
        record = inputs.json(path)
        task = record.get('instance_id')
        if task not in tasks or record.get('signal') != 'PASS':
            continue
        source_kind = 'historical_pilot' if '/pilot_' in str(path) else 'historical_discovery_pair'
        binding = record.get('patch_sha256')
        binding = 'exact_frozen_candidate_hash' if binding == tasks[task]['patch_sha256'] else 'not_stored_in_native_pair'
        skip_count, missing_captures = 0, 0
        for call_index, call in enumerate(record.get('calls', [])[:record.get('initial_calls', 2)]):
            run = call['run']
            selected = run.get('requested_tests', call.get('requested', []))
            mapper = mapping_for(selected, tasks[task]['runner']['name'])
            originals = {r['test_id']: r['status'] for r in run.get('results', [])}
            capture = normalized_path(run['evidence_files']['runner.raw'], args.repo)
            if capture.exists():
                raw_bytes = inputs.bytes(capture, run.get('evidence_sha256', {}).get('runner.raw'))
                parsed = parse_capture(raw_bytes.decode('utf-8', 'replace'), tasks[task]['runner']['name'])
            else:
                missing_captures += 1
                parsed = {r['test_id']: {'status': r['status'], 'reason': r.get('message', ''), 'line': 1}
                          for r in run.get('raw_results', [])}
            for rid, outcome in parsed.items():
                ids = mapper(rid)
                if outcome['status'] == 'skipped' and len(ids) == 1:
                    skip_count += 1
                    history_skip(task, ids[0], rid, originals.get(ids[0], 'missing'), outcome['reason'],
                        'patched' if call['patched'] else 'base', path, capture if capture.exists() else path,
                        outcome['line'], source_kind, record.get('completeness', 'NOT_RECORDED'),
                        patch_binding=binding, call_index=call_index)
        inventory.append({'instance_id': task, 'source_record': str(path), 'kind': source_kind,
            'native_verdict': 'PASS', 'completeness': record.get('completeness', 'NOT_RECORDED'),
            'patch_binding': binding, 'selected_count': record.get('selected', ''),
            'baseline_cache_available': False, 'known_baseline_skip_count': skip_count,
            'paired_skip_evidence_available': True, 'excluded_run_name': False,
            'limitation': str(missing_captures) + ' missing raw captures; preserved structured cases used where needed; selections/images are historical and not pooled with full83'})

    for path in sorted((args.repo / 'reports/v2_stabilization/classifier_v2/live/tasks').glob('*/result.json')):
        record = inputs.json(path)
        task = record.get('instance_id')
        if task not in tasks or record.get('new') != 'PASS':
            continue
        table = path.parent / 'paired_outcomes.csv'
        count = 0
        if table.exists():
            inputs.bytes(table)
            with table.open(newline='') as stream:
                for line, row in enumerate(csv.DictReader(stream), 2):
                    ids = json.loads(row['selected_ids'])
                    if len(ids) != 1:
                        continue
                    for phase in ['base', 'patched']:
                        if row.get(phase) == 'skipped':
                            count += 1
                            history_skip(task, ids[0], row['raw_id'], 'skipped', '', phase,
                                path, table, line, 'historical_stabilization_table', record.get('completeness', 'NOT_RECORDED'))
        inventory.append({'instance_id': task, 'source_record': str(path), 'kind': 'historical_stabilization_table',
            'native_verdict': 'PASS', 'completeness': record.get('completeness', 'NOT_RECORDED'),
            'patch_binding': 'not_stored_in_result', 'selected_count': record.get('selected', ''),
            'baseline_cache_available': False, 'known_baseline_skip_count': count if table.exists() else '',
            'paired_skip_evidence_available': table.exists(), 'excluded_run_name': False,
            'limitation': 'Per-case CSV preserved, but raw logs may be absent and source/image equivalence is not established'})
    print('HISTORICAL PASS inventories', len(inventory), 'skip observations', len(skips), flush=True)


# These counters are observations, never selected tree-ID slots.
OBSERVATION_UNITS = {
    'collection_or_test_error_observed': 'raw_ERROR_case_tree_observations',
    'base_patched_id_set_difference': 'raw_ID_symmetric_difference',
    'pass_to_exception_scored_error': 'base_PASS_patched_ERROR_case_transitions',
    'empty_selection': 'tasks_with_empty_selection',
}


def write_outputs(args, inputs, sources, current, task_rows, calls, batches, skips,
                  gaps, ledger, replays, pass_errors, history_inventory, history_skips, captures,
                  collection_skips, class_skips):
    out = args.output
    out.mkdir(parents=True)
    canonical = {
        'parameter_family_admission': 'parameterized_family_mismatch',
        'output_parsing': 'output_or_ID_parsing', 'raw_id_mapping': 'output_or_ID_parsing',
        'collection_or_runner_error': 'collection_runner_error',
        'collection_or_test_error': 'collection_runner_error',
        'collection_or_test_error_observed': 'collection_runner_error',
        'timeout_or_not_launched': 'timeout_not_reached',
        'collection_skip_or_deselection': 'collection_skip_or_deselection',
        'class_setup_skip': 'collection_skip_or_deselection',
        'environment_guard_abort': 'environment_guard_abort',
        'unreported_selected_identity': 'unresolved_unreported_selected_ID',
        'sympy_runner_mismatch': 'sympy_runner_mismatch',
        'pass_to_exception_scored_error': 'pass_to_exception_scored_error',
        'base_patched_id_set_difference': 'base_patched_id_set_difference',
        'empty_selection': 'empty_selection', 'unclassified_original_gap': 'unclassified_gap',
    }
    causes = sorted(set(canonical.values()))
    flat_tasks = []
    for row in task_rows:
        flat = {k: v for k, v in row.items() if k not in ('cause_counts', 'native_gap_cause_counts')}
        selected_counts, native_counts = Counter(), Counter()
        observed_counts = Counter()
        for name, count in row['cause_counts'].items():
            destination = observed_counts if name in OBSERVATION_UNITS else selected_counts
            destination[canonical[name]] += count
        for name, count in row['native_gap_cause_counts'].items():
            native_counts[canonical[name]] += count
        for cause in causes:
            flat[cause + '_selected_slots'] = selected_counts[cause]
            flat[cause + '_native_gap_records'] = native_counts[cause]
            flat[cause + '_observed_events'] = observed_counts[cause]
            flat[cause + '_observed_event_unit'] = next((unit for name, unit in OBSERVATION_UNITS.items() if canonical[name] == cause), '')
        flat_tasks.append(flat)
    write_csv(out / 'phase2_incomplete_causes.csv', flat_tasks)
    write_csv(out / 'selected_gap_attribution.csv', gaps)
    write_csv(out / 'native_gap_ledger.csv', ledger)
    write_csv(out / 'batch_aborts.csv', batches)
    tree_summary = []
    for task in current:
        for tree in ['base', 'patched']:
            rows = [r for r in batches if r['instance_id'] == task and r['tree'] == tree]
            initial = [r for r in rows if r['scope'] == 'initial']
            tree_summary.append({'instance_id': task, 'tree': tree,
                'initial_load_abort_batches': sum(r['abort_kind'] != 'runner_start_failure' for r in initial),
                'initial_environment_guard_aborts': sum(r['abort_kind'] == 'environment_guard_abort' for r in initial),
                'initial_runner_start_failures': sum(r['abort_kind'] == 'runner_start_failure' for r in initial),
                'all_calls_load_abort_batches': sum(r['abort_kind'] != 'runner_start_failure' for r in rows),
                'all_calls_not_run_requests': sum(r['not_run_count'] for r in rows),
                'all_calls_collateral_not_run_with_identified_suspect': sum(r['collateral_not_run_count'] for r in rows if r['collateral_not_run_count'] != ''),
                'all_calls_unattributed_not_run_requests': sum(r['unattributed_not_run_count'] for r in rows),
                'selected': len(current[task].get('selected_tests') or []), 'task_verdict': current[task].get('signal')})
    assert len(tree_summary) == 166
    write_csv(out / 'task_tree_batch_aborts.csv', tree_summary)
    write_csv(out / 'all_task_skips.csv', skips)
    write_csv(out / 'module_collection_skips.csv', collection_skips,
        fields=['instance_id', 'tree', 'call_index', 'scope', 'selected_test_id', 'batch', 'native_status',
                'reason_group', 'reason', 'reason_quality', 'unit', 'evidence_path', 'line', 'source_reference', 'source_line'])
    write_csv(out / 'class_setup_skips.csv', class_skips,
        fields=['instance_id', 'tree', 'call_index', 'scope', 'selected_test_id', 'native_status',
                'reason_group', 'reason', 'reason_quality', 'evidence_path', 'line', 'source_reference', 'source_line', 'unit'])
    accepted = [r for r in skips if r['accepted_for_current_PASS_completeness'] or r['accepted_in_original_PASS_scoring']]
    write_csv(out / 'accepted_skips.csv', accepted)
    write_csv(out / 'historical_PASS_inventory.csv', history_inventory)
    write_csv(out / 'historical_skip_observations.csv', history_skips)
    write_csv(out / 'parser_replay.csv', replays)
    write_csv(out / 'call_replay_summary.csv', calls)
    write_csv(out / 'pass_to_error_observations.csv', pass_errors,
              fields=['instance_id', 'selected_test_id', 'raw_test_id', 'base_status', 'patched_status', 'evidence_path', 'line'])
    charts = out / 'charts'
    charts.mkdir()
    cause_chart = []
    for cause in causes:
        affected = [r for r in flat_tasks if r[cause + '_selected_slots'] or r[cause + '_native_gap_records'] or r[cause + '_observed_events']]
        cause_chart.append({'cause': cause, 'all_tasks': len(affected),
            'INCOMPLETE_tasks': sum(r['signal'] == 'INCOMPLETE' for r in affected),
            'NOT_AVAILABLE_tasks': sum(r['signal'] == 'NOT_AVAILABLE' for r in affected),
            'selected_tree_slots': sum(r[cause + '_selected_slots'] for r in flat_tasks),
            'native_gap_records': sum(r[cause + '_native_gap_records'] for r in flat_tasks),
            'observed_events': sum(r[cause + '_observed_events'] for r in flat_tasks),
            'observed_event_unit': next((unit for name, unit in OBSERVATION_UNITS.items() if canonical[name] == cause), '')})
    write_csv(charts / 'cause_counts.csv', cause_chart)
    kinds = sorted({r['base_object_kinds'] if ';' not in r['base_object_kinds'] else 'multiple_candidates' for r in batches})
    abort_chart = []
    for kind in kinds:
        rows = [r for r in batches if (r['base_object_kinds'] if ';' not in r['base_object_kinds'] else 'multiple_candidates') == kind]
        abort_chart.append({'base_object_kind': kind, 'batch_occurrences': len(rows),
            'unique_tasks': len({r['instance_id'] for r in rows}),
            'not_run_requests': sum(r['not_run_count'] for r in rows),
            'collateral_with_identified_suspect': sum(r['collateral_not_run_count'] for r in rows if r['collateral_not_run_count'] != '')})
    write_csv(charts / 'batch_abort_object_types.csv', abort_chart)
    accepted_chart, skip_chart = [], []
    for group in GROUPS:
        current_group = [r for r in skips if r['reason_group'] == group and r['call_scope'] == 'initial']
        complete_pass = [r for r in current_group if r['accepted_for_current_PASS_completeness']]
        original_pass = [r for r in current_group if r['accepted_in_original_PASS_scoring']]
        old = [r for r in history_skips if r['reason_group'] == group]
        accepted_chart.append({'reason_group': group, 'current_PASS_raw_case_tree_slots': len(complete_pass),
            'current_PASS_tasks': len({r['instance_id'] for r in complete_pass}),
            'original_PASS_exact_selected_skip_slots': len(original_pass),
            'historical_complete_PASS_skip_slots': sum(r['accepted_for_PASS_completeness'] for r in old),
            'historical_baseline_only_skip_slots': sum(r['scope'] == 'historical_baseline_cache' for r in old)})
        skip_chart.append({'reason_group': group, 'initial_raw_skip_case_tree_slots': len(current_group),
            'tasks': len({r['instance_id'] for r in current_group}),
            'captured_reason_slots': sum(r['reason_quality'].startswith('captured') for r in current_group),
            'source_reason_slots': sum(r['reason_quality'].startswith('source') for r in current_group),
            'unconfirmed_source_candidate_slots': sum(r['reason_quality'] == 'source_candidate_not_runtime_confirmed' for r in current_group),
            'unknown_reason_slots': sum(r['reason_quality'] == 'unknown' for r in current_group),
            'xfail_slots': sum(r['skip_flavor'] in ('XFAIL', 'expected failure') for r in current_group),
            'module_collection_skip_request_slots': sum(r['reason_group'] == group and r['scope'] == 'initial' for r in collection_skips),
            'class_setup_skip_request_slots': sum(r['reason_group'] == group and r['scope'] == 'initial' for r in class_skips),
            'GIS_guard_abort_request_slots': sum(r['requested_count'] for r in batches if group == 'other' and r['abort_kind'] == 'environment_guard_abort' and r['scope'] == 'initial')})
    write_csv(charts / 'accepted_skip_reasons.csv', accepted_chart)
    write_csv(charts / 'all_task_skip_reasons.csv', skip_chart)
    recovered = [r for r in replays if r['parser_only_recovered_INCOMPLETE']]
    recovered_na = [r for r in replays if r['parser_only_binary_evidence_from_NOT_AVAILABLE']]
    recovery_chart = [
        {'metric': 'native_INCOMPLETE_tasks', 'tasks': 39},
        {'metric': 'native_NOT_AVAILABLE_tasks', 'tasks': 13},
        {'metric': 'parser_only_COMPLETE_from_INCOMPLETE_skip_compatible', 'tasks': len(recovered)},
        {'metric': 'parser_only_binary_evidence_from_NOT_AVAILABLE', 'tasks': len(recovered_na)},
        {'metric': 'parser_only_complete_all_skip_strict', 'tasks': sum(r['parser_only_complete_skip_strict'] for r in replays)},
        {'metric': 'native_FAIL_tasks_retained', 'tasks': sum(r.get('signal') == 'FAIL' for r in current.values())},
    ]
    write_csv(charts / 'parser_recovery.csv', recovery_chart)
    assert all(len(list(csv.reader(p.open()))) <= 15 for p in charts.glob('*.csv'))
    known = {r['instance_id']: r for r in flat_tasks}
    assert sum(r['signal'] == 'INCOMPLETE' for r in flat_tasks) == 39
    assert sum(r['signal'] == 'NOT_AVAILABLE' for r in flat_tasks) == 13
    unclassified = [r for r in ledger if r['cause'] == 'unclassified_original_gap']
    unresolved = [r for r in ledger if r['cause'] == 'unreported_selected_identity']
    unidentified = [r for r in batches if r['abort_kind'] == 'load_or_collection_abort' and r['offending_label'] == 'NOT_IDENTIFIED_FROM_CAPTURE']
    summaries = {'tasks': 83, 'native_INCOMPLETE': 39, 'native_NOT_AVAILABLE': 13,
        'V2_calls': len(calls), 'verified_full83_capture_files_in_both_arms': len(captures),
        'load_abort_batch_occurrences': sum(r['abort_kind'] != 'runner_start_failure' for r in batches),
        'GIS_environment_guard_abort_batches': sum(r['abort_kind'] == 'environment_guard_abort' for r in batches),
        'runner_start_failures': sum(r['abort_kind'] == 'runner_start_failure' for r in batches),
        'load_abort_tasks': len({r['instance_id'] for r in batches if r['abort_kind'] != 'runner_start_failure'}),
        'unidentified_load_abort_batches': len(unidentified),
        'collateral_not_run_slots_with_identified_suspects': sum(r['collateral_not_run_count'] for r in batches if r['collateral_not_run_count'] != ''),
        'current_PASS_tasks_with_accepted_skips': len({r['instance_id'] for r in skips if r['accepted_for_current_PASS_completeness']}),
        'current_initial_skip_slots': sum(r['call_scope'] == 'initial' for r in skips),
        'module_collection_skip_request_slots': len(collection_skips),
        'class_setup_skip_request_slots': len(class_skips),
        'historical_PASS_records': len(history_inventory), 'historical_skip_observations': len(history_skips),
        'parser_only_recovered_INCOMPLETE_tasks': [r['instance_id'] for r in recovered],
        'parser_only_binary_evidence_from_NOT_AVAILABLE_tasks': [r['instance_id'] for r in recovered_na],
        'unclassified_original_gap_records': len(unclassified), 'unresolved_original_selected_gap_records': len(unresolved),
        'base_PASS_patched_ERROR_concrete_observations': len(pass_errors),
        'status': 'in progress' if unclassified or unresolved or unidentified else 'done',
        'native_verdicts_changed': False, 'benchmark_runs': 0, 'phase2_Docker_calls': 0}
    write_json(out / 'analysis_summary.json', summaries)
    write_json(out / 'input_manifest.json', {'analysis_scope': 'POST-HOC ANALYSIS ONLY',
        'input_sha256': inputs.hashes, 'archive_member_sha256': sources.source_refs,
        'source_execution': 'none; ast parsing only', 'code_sha256': file_sha(Path(__file__)),
        'historical_scope': 'All available runs/*/tasks/COHORT_TASK/verification_record.full.json with native PASS, plus canonical discovery pairs, pilot V2 pairs and stabilization tables; oracle files and derived duplicates excluded',
        'reason_group_policy': GROUPS, 'unknown_reason_policy': 'other with explicit unknown quality, never invented',
        'native_verdicts_changed': False, 'phase2_Docker_calls': 0})
    md = ['# Phase 2: stored V2 evidence-gap audit', '', '**POST-HOC ANALYSIS ONLY. Native results remain unchanged.**', '',
        'Status: **' + summaries['status'] + '**. All 83 V2 tasks and both initial trees are inventoried, with confirmation calls marked separately; all 780 capture hashes in both arms verify. The three earlier CPU probes are documented separately in Phase 1 and are not benchmark runs or Phase 2 inputs to scoring.', '',
        '## Cause counts and parser-only replay', '',
        '`phase2_incomplete_causes.csv` reports all 83 tasks, including 39 INCOMPLETE and 13 NOT_AVAILABLE. Selected tree-ID slot counts, native gap-record counts and typed observation counts have separate columns; they must not be summed as one unit. Cause groups overlap.', '',
        'Parser-only replay makes ' + str(len(recovered)) + '/39 INCOMPLETE tasks complete with the frozen skip-compatible policy; ' + str(len(recovered_na)) + '/13 NOT_AVAILABLE tasks gain paired binary evidence. These are offline evidence reconstructions, not new native verdicts or confirmed new FAILs. All six original native FAIL tasks retain observed base-pass/patched-fail evidence.', '',
        'Replay changes only result reading: ANSI removal, Django two-line status handling and summary rejection, unique ID mapping, and concrete parameter accounting. It admits no new selected family, executes no tests, and reports the skip-strict alternative separately. Missing tests, ERROR observations, actual runner failures and ID-set changes continue to block completeness.', '',
        '## Batch aborts', '',
        str(summaries['load_abort_batch_occurrences']) + ' load/collection-abort batch occurrences across ' + str(summaries['load_abort_tasks']) + ' tasks, including ' + str(summaries['GIS_environment_guard_abort_batches']) + ' GIS environment-guard aborts; ' + str(summaries['runner_start_failures']) + ' additional runner-start failures are separate (including SymPy missing pytest). `task_tree_batch_aborts.csv` has all 166 task/tree rows, including zeros.', '',
        '`batch_aborts.csv` names the offending label when the capture names it, or lists static base-source candidates with an explicit identification confidence. It classifies properties, attributes and nested helpers using AST only. An inferred unique property is not an experimental isolated rerun. Unknown labels are retained: ' + str(len(unidentified)) + ' load-abort occurrences. Collateral counts exclude named suspects and only count selected NOT_RUN identities with no observed concrete outcome; they do not guarantee those tests would pass after repair.', '',
        '## Accepted and environment-conditioned skips', '',
        str(summaries['current_PASS_tasks_with_accepted_skips']) + ' current PASS tasks accept selected SKIPPED evidence for completeness. `accepted_skips.csv` distinguishes exact selected skips, mapped parameter skips and original pre-integrity PASS scoring. `all_task_skips.csv` covers the same five reason groups across every task, with unknown/truncated/source-only quality visible and XFAIL preserved separately.', '',
        'Reason groups: cores/CPU, missing dependency, platform, Python version, other. Source-derived explanations are labelled as static candidates or matches to captured prefixes; ambiguous and missing reasons stay explicit. Other includes unknown reasons and non-environment expected failures, so it is not an asserted environmental-cause count. `module_collection_skips.csv` reports selected requests whose own batch skipped collection; `class_setup_skips.csv` matches unnamed captured setup skips to literal setUpClass guards, without manufacturing test-body outcomes. Both are separate from concrete SKIPPED outcomes; chart columns also separate GIS-guard NOT_RUN requests.', '',
        '`historical_PASS_inventory.csv` lists ' + str(len(history_inventory)) + ' historical PASS records; `historical_skip_observations.csv` lists ' + str(len(history_skips)) + ' available skip observations. Full historical verification envelopes usually preserve only a baseline cache and aggregate patched verdict: their patched statuses/completeness are unknown, not silently reconstructed. Different candidates are excluded from skip counts; unbound later pairs remain separately labelled, and heterogeneous selections/images are not pooled with the 83-task run.', '',
        '## Remaining evidence limits', '',
        str(len(unclassified)) + ' native gap records remain unclassified; ' + str(len(unresolved)) + ' original selected-ID gap records have no resolved mechanism beyond an unreported outcome; ' + str(len(unidentified)) + ' load-abort batches have no identified offending label. These unresolved details prevent claiming complete causal attribution when nonzero. All records have an input path/hash; capture examples have 1-based lines, and native gap records also have JSON pointers.', '',
        'The audit does not install missing runners, change selection, repair the executor, alter CPU resources, or start Phase 3. The new skip-strict PASS rule is reported as a diagnostic policy contrast, not silently substituted for parser-only recovery.', '',
        '## Files for review', '',
        '- `native_gap_ledger.csv`: every recorded native gap and its assigned group.',
        '- `selected_gap_attribution.csv`: every selected NOT_RUN/TIMEOUT/ERROR slot and observed admission or execution mechanism.',
        '- `batch_aborts.csv`, `task_tree_batch_aborts.csv`: aborts, candidates, object kinds and collateral accounting.',
        '- `accepted_skips.csv`, `all_task_skips.csv`, historical inventories: case-level skip evidence.',
        '- `parser_replay.csv`, `call_replay_summary.csv`, `pass_to_error_observations.csv`: offline replay and classification diagnostics.',
        '- `charts/*.csv`: each at most 15 rows including its header; plotting units are explicit.',
        '- `input_manifest.json`: source/capture/archive hashes and historical coverage scope.', '',
        'Outputs are uncommitted for user review.', '']
    with (out / 'SUMMARY.md').open('x') as stream:
        stream.write('\n'.join(md))
    print('SUMMARY', json.dumps(summaries), flush=True)


if __name__ == '__main__':
    main()
