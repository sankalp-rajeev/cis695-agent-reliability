#!/usr/bin/env python3
"""Pre-registered Phase 4 attempt-4 seal. Stored data only; no execution/labels.

Inputs are the manifested attempt, the frozen original V2 run/selections, and
Fix 5's committed projection and hash-listed provenance. The two provenance
CSVs reconstruct its fixed B1/static overlay. Its exact historical parser is
embedded below, so later parser repairs cannot redefine H1b's residual.
Unknown JSON fields are skipped structurally without decoding their values.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RUN = ROOT / 'runs/phase4_v4_attempt4_20261109T185713Z'
FIX5 = ROOT / 'reports/next_phases/phase3_fix5/stored_accounting'
FIX5_MANIFEST_SHA = '3ad922201c5599642bcfc59c73585161252722ba768aa7dd0b6f1977fbbb4139'
FIX5_H1_SHA = '42611fb455bf17f90cb6c55c7a041d97824628777d3b86a52a68ad56a40b91ba'
RUN_MANIFEST_SHA = '69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25'
FIX5_PARSER_SHA = 'c86991d74a1f522f75879af761d137e1881e594607b90fde49d90b13023ff241'
ADMITTED = frozenset(('passed', 'failed', 'skipped', 'xfail', 'xpass'))
POLICIES = ('C_invalid_excluded', 'C_invalid_missing', 'S_invalid_excluded', 'S_invalid_missing')
CATEGORIES = ('INVALID_ID', 'FLAKY', 'REGRESSION_ERROR', 'NOT_REACHED', 'TIMEOUT',
              'COLLECTION_ERROR', 'COLLECTOR_FALLBACK', 'GENERATED_INPUT_CHANGED')
INPUT_HASHES = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class ManifestMismatch(RuntimeError):
    pass


def verify_run():
    raw = (OUT / 'run_manifest.sha256').read_bytes()
    if sha(raw) != RUN_MANIFEST_SHA:
        raise ManifestMismatch('The committed run manifest changed')
    header, entries = {}, {}
    for line in raw.decode().splitlines():
        if line.startswith('# '):
            key, value = line[2:].split(': ', 1)
            header[key] = value
        elif line:
            digest, name = line.split('  ', 1)
            if name in entries or Path(name).is_absolute() or '..' in Path(name).parts:
                raise ManifestMismatch('Unsafe/duplicate manifest path')
            entries[name] = digest
    files = {p.relative_to(RUN).as_posix(): p for p in RUN.rglob('*') if p.is_file()}
    if any(p.is_symlink() for p in RUN.rglob('*')) or files.keys() != entries.keys():
        raise ManifestMismatch('Run file set changed')
    total = 0
    for name, path in sorted(files.items()):
        if hash_file(path) != entries[name]:
            raise ManifestMismatch('Run hash changed: ' + name)
        total += path.stat().st_size
    if len(files) != int(header['file_count']) or total != int(header['total_bytes']):
        raise ManifestMismatch('Run size/count changed')
    assert header['run_directory'] == RUN.relative_to(ROOT).as_posix()
    return entries, {'sha256': sha(raw), 'file_count': len(files), 'total_bytes': total}


class Projection:
    """Decode whitelisted fields only; skip other JSON values without decoding."""
    string = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"')
    structure = re.compile(r'["{}\[\]]')
    scalar_end = re.compile(r'[,}\]]')

    def __init__(self, text):
        self.text, self.pos = text, 0
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
                if match is None:
                    raise ValueError('Unfinished JSON container')
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
        self.pos += 1
        if char == '{':
            result = {}
            self.whitespace()
            while self.text[self.pos] != '}':
                key = self.scalar()
                self.whitespace()
                assert self.text[self.pos] == ':'
                self.pos += 1
                if key in schema:
                    result[key] = self.project(schema[key])
                else:
                    self.skip()
                self.whitespace()
                if self.text[self.pos] == ',':
                    self.pos += 1
                self.whitespace()
            self.pos += 1
            return result
        if char == '[':
            result, index = [], 0
            self.whitespace()
            while self.text[self.pos] != ']':
                if index < schema.get('@limit', float('inf')):
                    result.append(self.project(schema['*']))
                else:
                    self.skip()
                index += 1
                self.whitespace()
                if self.text[self.pos] == ',':
                    self.pos += 1
                self.whitespace()
            self.pos += 1
            return result
        raise ValueError('Unexpected JSON container')


def project(raw, schema):
    return Projection(raw.decode()).project(schema)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def django_label(node_id):
    path, _, rest = node_id.partition('::')
    path = path.removeprefix('tests/')
    module = path[:-3].replace('/', '.') if path.endswith('.py') else path.replace('/', '.')
    return module + '.' + rest.replace('::', '.') if rest else module


# Exact Fix 5 result_parser.py; source SHA is asserted before use.
FIX5_PARSER_SOURCE = r'''"""Terminal result parsing shared by live execution and stored-capture scoring.

XFAIL/XPASS retain distinct statuses as well as their original runner flavor.
"""

import re
from collections import defaultdict

from reliability.verifier.selection import django_label

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PYTEST = re.compile(
    r"^(?P<id>\S.*?::\S.*?)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b(?P<tail>.*)",
    re.IGNORECASE,
)
DJANGO = re.compile(r"^(?P<name>\w+) \((?P<label>[^)]+)\)(?P<tail>.*)$")
DJ_STATUS = re.compile(
    r"\.\.\.\s*(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)", re.IGNORECASE
)
STATUSES = {
    "PASSED": "passed",
    "FAILED": "failed",
    "ERROR": "error",
    "SKIPPED": "skipped",
    "XFAIL": "xfail",
    "XPASS": "xpass",
    "ok": "passed",
    "fail": "failed",
    "error": "error",
    "skipped": "skipped",
    "expected failure": "xfail",
    "unexpected success": "xpass",
}
SEVERITY = {"skipped": 0, "xfail": 1, "passed": 2, "xpass": 3, "failed": 4, "error": 5}


def parse_capture(text, runner):
    """Parse observed terminal outcomes; reject Django summary-derived fake IDs."""
    if runner == "sympy":
        return parse_sympy_capture(text)
    result, pending = {}, None
    for number, physical in enumerate(text.split("\n"), 1):
        for line in ANSI.sub("", physical).split("\r"):
            line = line.strip()
            if runner == "django":
                header = DJANGO.match(line)
                if header:
                    name, label, tail = header.group("name", "label", "tail")
                    if name in ("OK", "FAILED", "FAIL", "ERROR", "Ran"):
                        pending = None
                        continue
                    if re.fullmatch(
                        r"(?:[A-Za-z_]\w*|<locals>)(?:\.(?:[A-Za-z_]\w*|<locals>))*", label
                    ):
                        pending = (
                            label if label.endswith("." + name) else label + "." + name,
                            number,
                        )
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
                    match = re.match(
                        r"^(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b(.*)$", tail
                    )
                if pending is None or match is None:
                    continue
                rid, header_line = pending
                word = match.group(1).lower()
                status = STATUSES[word]
                reason = match.group(2).strip().strip("\"'") if status == "skipped" else ""
                if word == "expected failure":
                    reason = "expected failure"
                pending = None
                kind = (
                    "loader_placeholder"
                    if "unittest.loader._FailedTest." in rid
                    else "fixture"
                    if rid.endswith(
                        (".setUpClass", ".tearDownClass", ".setUpModule", ".tearDownModule")
                    )
                    else "case"
                )
            else:
                match = PYTEST.match(line)
                if match is None:
                    continue
                rid, word, tail = match.group("id", "status", "tail")
                word = word.upper()
                status = STATUSES[word]
                skip = re.search(r"^\s*\((.*?)\)", tail)
                reason = skip.group(1) if skip and status == "skipped" else ""
                kind, header_line = "case", number
            observation = {
                "status": status,
                "line": number,
                "header_line": header_line,
                "reason": reason,
                "flavor": word,
                "kind": kind,
            }
            if rid not in result or SEVERITY[status] >= SEVERITY[result[rid]["status"]]:
                result[rid] = observation
    return result


# SymPy's native verbose reporter identifies the file once, then emits a test
# name and a token (sometimes on a later line after warnings/debug output).
_SYMPY_FILE = re.compile(r"^(?P<path>[^\s\[]+\.py)\[(?:\d+|\?)\]")
_SYMPY_TEST = re.compile(r"^(?P<name>test_\w+|<lambda>)(?:\s+(?P<tail>.*))?$")
_SYMPY_TOKEN = re.compile(r"(?:^|\s)(ok|[fXFEsKwT])\s*(?:\[(?:OK|FAIL)\])?\s*$")
_SYMPY_STATUS = {
    "ok": "passed",
    "f": "xfail",
    "X": "xpass",
    "F": "failed",
    "E": "error",
    "s": "skipped",
    "K": "skipped",
    "w": "skipped",
    "T": "timeout",
}


def parse_sympy_capture(text):
    result, module, pending = {}, None, None
    severity = dict(SEVERITY, timeout=6)
    for number, physical in enumerate(text.split("\n"), 1):
        for line in ANSI.sub("", physical).split("\r"):
            line = line.strip()
            header = _SYMPY_FILE.match(line)
            if header:
                module = header.group("path")
                module = re.sub(r"^/testbed/", "", module)
                pending = None
                continue
            if line.startswith(("===", "___", "DO *NOT* COMMIT")):
                module, pending = None, None
                continue
            test = _SYMPY_TEST.match(line)
            if test and module:
                pending = (module + "::" + test.group("name"), number)
                tail = test.group("tail") or ""
            else:
                tail = line
            token = _SYMPY_TOKEN.search(tail)
            if not pending or not token:
                continue
            word = token.group(1)
            status = _SYMPY_STATUS[word]
            rid, header_line = pending
            flavor = "XFAIL" if word == "f" else "XPASS" if word == "X" else status.upper()
            observed = {
                "status": status,
                "line": number,
                "header_line": header_line,
                "reason": tail[: token.start()].strip() if status in ("skipped", "timeout") else "",
                "flavor": flavor,
                "kind": "case",
            }
            if rid not in result or severity[status] >= severity[result[rid]["status"]]:
                result[rid] = observed
    return result


def mapping_for(selected, runner):
    wanted = set(selected)
    labels = defaultdict(list)
    if runner == "django":
        for test in selected:
            labels[django_label(test)].append(test)

    def map_id(rid):
        if runner != "django":
            candidates = [rid, rid.split("[", 1)[0]] if "[" in rid else [rid]
            return list(dict.fromkeys(t for t in candidates if t in wanted))
        if rid in labels:
            return labels[rid]
        # Only a unique shortened framework label is admitted; ambiguity stays visible.
        candidates = [
            test for label, ids in labels.items() if label.endswith("." + rid) for test in ids
        ]
        return candidates if len(candidates) == 1 else []

    return map_id
'''

ROW = {k: True for k in ('test_id', 'status', 'message', 'elapsed_s')}
VALIDATION = {k: True for k in ('selected_id', 'runnable_ids', 'admitted', 'valid',
    'collector_fallback', 'reason', 'static_reason', 'failure_status', 'stage',
    'module_skip_reason', 'module_skip_instances', 'native_disagrees', 'unavailable')}
EVENT = {k: True for k in ('event', 'batch', 'module', 'ids', 'observed_ids', 'missing_ids',
    'offset', 'split', 'load_failure', 'timed_out', 'returncode', 'retry', 'parent')}
RUN_SCHEMA = {'results': {'*': ROW}, 'raw_results': {'*': ROW}, 'raw_id_map': True,
    'execution_results': {'*': ROW}, 'execution_id_map': True,
    'validation': {'*': VALIDATION}, 'timed_out': True, 'budget_s': True,
    'evidence_flags': True, 'confirmation': True,
    'stage_health': {'*': {k: True for k in ('stage', 'module', 'status', 'import_signature')}},
    'requested_tests': True}
CONFIRM_SCHEMA = {k: v for k, v in RUN_SCHEMA.items() if k not in
                  ('raw_results', 'raw_id_map', 'execution_results', 'execution_id_map', 'stage_health')}
REPORT_SCHEMA = {'signal': True, 'outcomes': True, 'incompleteness': True,
    'confirmation_summary': True, 'evidence_flags': True,
    'confirmations': {'*': CONFIRM_SCHEMA}}
ORIGINAL_SCHEMA = {'instance_id': True, 'signal': True, 'outcomes': True, 'selected_tests': True,
    'calls': {'@limit': 2, '*': {'patched': True, 'requested': True, 'run': {
        'results': {'*': ROW}, 'requested_tests': True, 'evidence_files': True,
        'evidence_sha256': True, 'events': {'*': EVENT}, 'timed_out': True}}}}


def fix5_statuses(parser, raw, stderr, events, requested, runner):
    """Admission-relevant projection of the exact Fix 5 capture interpreter.

    Match its split-parent suppression, unique mapping, severity dominance and
    load-failure override. Infrastructure diagnostics never create admission.
    """
    observed = parser['parse_capture']((raw + stderr).decode('utf-8', 'replace'), runner)
    for event in events:
        if event.get('event') != 'end' or not event.get('split'):
            continue
        start = next((e for e in events if e.get('event') == 'start' and e.get('batch') == event.get('batch')), {})
        begin, end = start.get('offset'), event.get('offset')
        if not isinstance(begin, int) or not isinstance(end, int):
            continue
        first, last = raw[:begin].count(b'\n') + 1, raw[:end].count(b'\n')
        admitted = set(event.get('observed_ids', ()))
        observed = {rid: value for rid, value in observed.items() if not
            (first <= value['line'] <= last and (value['kind'] != 'case' or rid not in admitted))}
    mapper = parser['mapping_for'](requested, runner)
    statuses = {}
    for rid, value in observed.items():
        selected = mapper(rid)
        if len(selected) == 1 and value['kind'] == 'case':
            tid, status = selected[0], value['status']
            if tid not in statuses or parser['SEVERITY'][status] >= parser['SEVERITY'][statuses[tid]]:
                statuses[tid] = status
    for event in events:
        if event.get('event') == 'end' and not event.get('split') and event.get('load_failure'):
            for missing in event.get('missing_ids', ()):
                for tid in mapper(missing):
                    statuses[tid] = 'collection_error'  # Both historical loader classes are non-admitted.
    return statuses, observed


def judge(numerator, denominator, prediction, falsification, *, percent=False):
    value = numerator * 100 if percent else numerator
    scale = denominator if percent else 1
    met, falsified = value >= prediction * scale, value < falsification * scale
    return {'numerator': numerator, 'denominator': denominator,
            'fraction': numerator / denominator if denominator else None,
            'prediction_threshold': prediction, 'falsification_below': falsification,
            'threshold_unit': 'percent' if percent else 'slots_or_tasks',
            'prediction_met': met, 'falsified': falsified,
            'verdict': 'prediction_met' if met else 'falsified' if falsified else 'between_thresholds'}


def compute(entries, manifest_info):
    def run_read(relative, schema):
        assert relative in entries, 'Unmanifested input: ' + relative
        raw = (RUN / relative).read_bytes()
        if sha(raw) != entries[relative]:
            raise ManifestMismatch('Run input changed: ' + relative)
        return project(raw, schema)

    def pinned(path, expected):
        path = Path(path)
        raw = path.read_bytes()
        assert sha(raw) == expected, 'Frozen input hash mismatch: ' + str(path)
        INPUT_HASHES[str(path)] = expected
        return raw

    provenance = json.loads(pinned(FIX5 / 'manifest.json', FIX5_MANIFEST_SHA))
    frozen_hashes = provenance['input_sha256']

    def frozen_read(path):
        return pinned(path, frozen_hashes[str(path)])

    baseline = json.loads(pinned(FIX5 / 'H1_projection.json', FIX5_H1_SHA))
    assert baseline['primary_B1'] == 37614 and baseline['admitted_original_slots'] == 23761
    tasks_path = Path(next(p for p in frozen_hashes if p.endswith('/paired_frozen/tasks.json')))
    frozen = tasks_path.parent
    tasks = project(frozen_read(tasks_path), {'*': {'instance_id': True, 'runner': {'name': True}, 'selections': {'v2': True}}})
    order = run_read('plan.json', {'task_order': True})['task_order']
    assert len(tasks) == len(order) == 83 and {t['instance_id'] for t in tasks} == set(order)
    by_task = {t['instance_id']: t for t in tasks}
    gaps_path = Path(next(p for p in frozen_hashes if p.endswith('/selected_gap_attribution.csv')))
    gaps = list(csv.DictReader(io.StringIO(frozen_read(gaps_path).decode())))
    b1 = {(r['instance_id'], r['tree'], r['test_id']) for r in gaps
          if r['scope'] == 'initial' and r['cause'] != 'environment_guard_abort'}
    assert len(b1) == 37614
    static_path = Path(next(p for p in frozen_hashes if p.endswith('/static_ids.csv.gz')))
    static = {}
    for row in csv.DictReader(io.StringIO(gzip.decompress(frozen_read(static_path)).decode())):
        static[row['instance_id'], row['tree'], row['selected_id']] = row
    assert sha(FIX5_PARSER_SOURCE.encode()) == FIX5_PARSER_SHA
    parser = {'django_label': django_label}
    exec(compile(FIX5_PARSER_SOURCE.replace('from reliability.verifier.selection import django_label\n', ''),
                 '<embedded-hash-verified-Fix5-parser>', 'exec'), parser)
    # CPU membership comes from frozen metadata, never from live outcomes.
    cpu_ids = {(iid, tid) for (iid, tree, tid), record in static.items()
               if any(re.search(r'\bneeds_two_cores\b', decorator)
                      for decorator in json.loads(record['decorators']))}
    cpu_original_native_instances = set()
    projection_admitted, originals, selections = set(), {}, {}
    for iid in order:
        meta = by_task[iid]
        tests = project(frozen_read(frozen / meta['selections']['v2']), {'tests': True})['tests']
        assert len(tests) == len(set(tests))
        selections[iid] = tests
        original_path = Path(next(p for p in frozen_hashes if p.endswith('/tasks/' + iid + '/v2/result.json')))
        original = project(frozen_read(original_path), ORIGINAL_SCHEMA)
        assert (original.get('selected_tests') or []) == tests
        originals[iid] = original
        runner = meta['runner']['name']
        for call in original.get('calls', []):
            tree = 'patched' if call['patched'] else 'base'
            captured = call['run']
            requested = call.get('requested', captured.get('requested_tests', tests))
            records = [static.get((iid, tree, tid), {'selected_id': tid, 'runnable_ids': json.dumps([tid]), 'reason': ''}) for tid in requested]
            native = list(dict.fromkeys(tid for r in records if not r['reason'] for tid in json.loads(r['runnable_ids'])))
            paths = captured['evidence_files']
            raw = frozen_read(Path(paths['runner.raw']))
            assert sha(raw) == captured['evidence_sha256']['runner.raw']
            stderr = frozen_read(Path(paths['stderr.raw'])) if paths.get('stderr.raw') else b''
            if paths.get('stderr.raw'):
                assert sha(stderr) == captured['evidence_sha256']['stderr.raw']
            statuses, observed = fix5_statuses(parser, raw, stderr, captured.get('events', []), native, runner)
            for record in records:
                instances = json.loads(record['runnable_ids'])
                if not record['reason'] and instances and all(statuses.get(t) in ADMITTED for t in instances):
                    projection_admitted.add((iid, tree, record['selected_id']))
            mapper = parser['mapping_for'](tests, runner)
            for native_id, observation in observed.items():
                if observation['kind'] == 'case' and any((iid, tid) in cpu_ids for tid in mapper(native_id)):
                    cpu_original_native_instances.add((iid, tree, native_id))
                if observation['status'] == 'skipped' and re.search(r'\b(cpu|cpus|core|cores|processor|processors)\b', observation.get('reason', ''), re.I):
                    for selected_id in mapper(native_id):
                        cpu_ids.add((iid, selected_id))
    projected = b1 & projection_admitted
    assert len(projected) == 23761, ('Fix5 identity reconstruction differs', len(projected))
    residual = b1 - projected
    assert len(residual) == 13853
    residual_sha = sha(json_bytes(sorted(residual)))
    print('Fix5 projection reproduced: 23761 admitted B1 slots; 13853 fixed residual slots.', flush=True)

    admitted, invalid, per_task, caps = set(), set(), [], []
    all_policies = {policy: collections.Counter() for policy in POLICIES}
    sensitivity = {'C': [], 'S': []}
    category_totals = collections.Counter()
    skip_groups, skip_reasons = collections.Counter(), collections.Counter()
    strict_abstention_groups = collections.defaultdict(list)
    cpu_statuses = collections.Counter()
    cpu_native_statuses = collections.Counter()
    confirmations_total = 0
    integrity_rows, unexplained = [], []
    original_fail_tasks = []

    def skip_reason(run, identity, receipt):
        reasons = []
        for result in run.get('raw_results', []):
            if result['status'] == 'skipped' and identity in run.get('raw_id_map', {}).get(result['test_id'], []):
                if result.get('message'):
                    reasons.append(result['message'])
        reasons.extend(reason for _, reason in receipt.get('module_skip_instances', []) if reason)
        if receipt.get('module_skip_reason'):
            reasons.append('module_skip: ' + receipt['module_skip_reason'])
        return sorted(set(reasons))

    def group_skip(iid, identity, reasons):
        text = ' | '.join(reasons).lower()
        if (iid, identity) in cpu_ids:
            return 'CPU_CONDITIONED'
        if not text:
            return 'REASON_NOT_CAPTURED'
        if 'disabled' in text:
            return 'MODULE_DISABLED'
        if any(word in text for word in ('windows', 'platform', 'python 2', 'python 3', 'not supported on', 'posix')):
            return 'PLATFORM_OR_INTERPRETER'
        if any(word in text for word in ('requires', 'not installed', 'dependency', 'no module', 'not available', 'unavailable')):
            return 'OPTIONAL_DEPENDENCY_OR_FEATURE'
        return 'OTHER_RECORDED_SKIP'

    def cap_record(iid, tree, run, scope, index=None):
        if run.get('timed_out'):
            row = {'task': iid, 'tree': tree, 'scope': scope,
                   'NOT_REACHED': sum(r['status'] == 'not_reached' for r in run.get('results', [])),
                   'TIMEOUT': sum(r['status'] == 'timeout' for r in run.get('results', [])),
                   'budget_s': run.get('budget_s'), 'retried_by_seal': False}
            if index is not None:
                row['confirmation_index'] = index
            caps.append(row)

    for iid in order:
        tests = selections[iid]
        runs = {tree: run_read('tasks/' + iid + '/' + tree + '.json', RUN_SCHEMA) for tree in ('base', 'patched')}
        item = run_read('tasks/' + iid + '/result.json', {'native_passes': True,
            'policies': {p: REPORT_SCHEMA for p in POLICIES}})
        reports = item['policies']
        primary = reports['C_invalid_excluded']
        assert set(reports) == set(POLICIES)
        counts = collections.Counter({c: 0 for c in CATEGORIES})
        tree_counts, skipped_selected = {}, []
        for tree, run in runs.items():
            results = {r['test_id']: r for r in run['results']}
            receipts = {r['selected_id']: r for r in run['validation']}
            assert len(run['results']) == len(results) and set(results) == set(tests)
            assert set(receipts) == set(tests)
            admitted_count = 0
            for tid, result in results.items():
                receipt = receipts[tid]
                key = iid, tree, tid
                if result['status'] in ADMITTED and receipt.get('admitted') and not receipt.get('collector_fallback'):
                    admitted.add(key)
                    admitted_count += 1
                if result['status'] == 'invalid_id':
                    invalid.add(key)
                for category in ('INVALID_ID', 'NOT_REACHED', 'TIMEOUT', 'COLLECTION_ERROR'):
                    counts[category] += result['status'] == category.lower()
                counts['COLLECTOR_FALLBACK'] += bool(receipt.get('collector_fallback'))
                if result['status'] == 'skipped':
                    reasons = skip_reason(run, tid, receipt)
                    group = group_skip(iid, tid, reasons)
                    skip_groups[group] += 1
                    skip_reasons[' | '.join(reasons) or '(not captured)'] += 1
                    skipped_selected.append(tid)
                if (iid, tid) in cpu_ids:
                    cpu_statuses[result['status']] += 1
            cpu_seen = set()
            for native_result in run.get('raw_results', []):
                raw_id = native_result['test_id']
                if raw_id not in cpu_seen and any((iid, tid) in cpu_ids
                        for tid in run.get('raw_id_map', {}).get(raw_id, [])):
                    cpu_native_statuses[native_result['status']] += 1
                    cpu_seen.add(raw_id)
            tree_counts[tree] = {'admitted': admitted_count, 'selected': len(tests),
                                'status_counts': dict(sorted(collections.Counter(r['status'] for r in results.values()).items()))}
            cap_record(iid, tree, run, 'initial')
        outcomes = primary['outcomes']
        counts['FLAKY'] = sum(value == 'FLAKY' for value in outcomes.values())
        counts['REGRESSION_ERROR'] = sum(value == 'REGRESSION_ERROR' for value in outcomes.values())
        confirmations = primary.get('confirmations', [])
        confirmation_count = item['native_passes'] - 2
        assert confirmation_count == len(confirmations) and confirmation_count >= 0
        confirmations_total += confirmation_count
        actual_passes = list(runs.values()) + confirmations
        generated_passes = sum('GENERATED_INPUT_CHANGED' in r.get('evidence_flags', []) for r in actual_passes)
        counts['GENERATED_INPUT_CHANGED'] = int(generated_passes > 0 or 'GENERATED_INPUT_CHANGED' in primary.get('evidence_flags', []))
        for index, run in enumerate(confirmations):
            tree = run.get('confirmation', {}).get('tree', 'patched' if index % 2 else 'base')
            cap_record(iid, tree, run, 'confirmation', index + 1)
        verdicts = {policy: reports[policy]['signal'] for policy in POLICIES}
        for policy in POLICIES:
            all_policies[policy][verdicts[policy]] += 1
        for policy in ('C', 'S'):
            if verdicts[policy + '_invalid_excluded'] != verdicts[policy + '_invalid_missing']:
                sensitivity[policy].append({'task': iid, 'excluded': verdicts[policy + '_invalid_excluded'],
                                            'missing': verdicts[policy + '_invalid_missing']})
        if verdicts['S_invalid_excluded'] not in ('PASS', 'FAIL'):
            reasons = {value for value in reports['S_invalid_excluded']['outcomes'].values()
                       if value in ('SKIPPED', 'NOT_REACHED', 'TIMEOUT', 'COLLECTION_ERROR', 'NOT_RUN',
                                    'RUNNER_UNAVAILABLE', 'FLAKY', 'REGRESSION_ERROR', 'ERROR', 'INVALID_ID')}
            if not reasons:
                reasons = {verdicts['S_invalid_excluded']}
            for reason in sorted(reasons):
                strict_abstention_groups[reason].append(iid)
        category_totals.update(counts)
        row = {'task': iid, 'policies': verdicts, 'trees': tree_counts,
               'counts': dict(counts), 'confirmation_runs': confirmation_count,
               'confirmation_candidates': len(primary.get('confirmation_summary', [])),
               'GENERATED_INPUT_CHANGED_actual_passes': generated_passes}
        per_task.append(row)
        original = originals[iid]
        if original['signal'] == 'FAIL':
            original_fail_tasks.append(iid)
            candidates = [tid for tid, value in original.get('outcomes', {}).items() if value == 'REGRESSION']
            details = []
            for tid in candidates:
                current = outcomes.get(tid)
                evidence = []
                if current == 'REGRESSION':
                    cause = 'native FAIL present as confirmed REGRESSION'
                elif current in ('FLAKY', 'REGRESSION_ERROR'):
                    evidence = [c for c in primary.get('confirmation_summary', []) if c.get('candidate_id') == tid]
                    cause = 'recorded isolated confirmations: ' + current if evidence else None
                else:
                    cause = None
                    for tree, run in runs.items():
                        result = next((r for r in run['results'] if r['test_id'] == tid), None)
                        receipt = next((r for r in run['validation'] if r['selected_id'] == tid), {})
                        if result is None:
                            continue
                        status = result['status']
                        if status in ('not_reached', 'timeout') and run.get('timed_out'):
                            cause = 'recorded per-pass cap; no seal retry'
                        elif status in ('collection_error', 'invalid_id') and receipt.get('reason'):
                            cause = 'recorded collection/identity receipt: ' + receipt['reason']
                        elif status == 'skipped':
                            reasons = skip_reason(run, tid, receipt)
                            if reasons:
                                cause = 'recorded skip: ' + ' | '.join(reasons)
                        if cause:
                            evidence.append({'tree': tree, 'status': status,
                                             'message': result.get('message', ''), 'receipt_reason': receipt.get('reason', '')})
                            break
                detail = {'test_id': tid, 'current_outcome': current, 'cause': cause, 'evidence': evidence}
                details.append(detail)
                if cause is None:
                    unexplained.append({'task': iid, **detail})
            present = all(verdicts[p] == 'FAIL' for p in POLICIES)
            explained = bool(details) and all(d['cause'] for d in details)
            if not present and not explained:
                unexplained.append({'task': iid, 'cause': 'original native FAIL verdict vanished without a recorded cause', 'current_policies': verdicts})
            integrity_rows.append({'task': iid, 'original_verdict': 'FAIL', 'current_policies': verdicts,
                                   'present_under_all_four_policies': present, 'candidates': details})
    assert len(original_fail_tasks) == 6
    h1 = judge(len(b1 & admitted), 37614, 60, 30, percent=True)
    h1['INVALID_ID_in_B1'] = len(b1 & invalid)
    h1['secondary_informational'] = {'label': 'SECONDARY INFORMATIONAL; INVALID_ID removed from B1',
        'numerator': h1['numerator'], 'denominator': 37614 - len(b1 & invalid),
        'fraction': h1['numerator'] / (37614 - len(b1 & invalid))}
    h1b = judge(len(residual & admitted), 13853, 6927, 3463)
    h1b.update({'Fix5_admitted_B1_slots': len(projected), 'fixed_residual_identity_sha256': residual_sha})
    policy_counts = {policy: {'verdict_counts': dict(sorted(counter.items())),
        'yes_no_primary_PASS_or_FAIL': counter['PASS'] + counter['FAIL'],
        'secondary_including_REGRESSION_ERROR': counter['PASS'] + counter['FAIL'] + counter['REGRESSION_ERROR'],
        'tasks': 83} for policy, counter in all_policies.items()}
    h2 = judge(policy_counts['C_invalid_excluded']['yes_no_primary_PASS_or_FAIL'], 83, 50, 42)
    h2['secondary_including_REGRESSION_ERROR'] = policy_counts['C_invalid_excluded']['secondary_including_REGRESSION_ERROR']
    h3 = {'Policy_S_yes_no': policy_counts['S_invalid_excluded']['yes_no_primary_PASS_or_FAIL'],
          'B2': 21, 'delta_vs_B2': policy_counts['S_invalid_excluded']['yes_no_primary_PASS_or_FAIL'] - 21,
          'verdict': 'DESCRIPTIVE; no prediction/falsification thresholds registered',
          'remaining_selected_tree_SKIPPED_by_reason_group': dict(sorted(skip_groups.items())),
          'remaining_selected_tree_SKIPPED_by_recorded_reason': dict(sorted(skip_reasons.items())),
          'strict_nonbinary_tasks_by_reason_group_overlapping': dict(sorted(strict_abstention_groups.items())),
          'CPU_conditioned': {'source': 'Fix5 frozen needs_two_cores decorators and any explicit frozen-original CPU skip reasons',
              'fixed_original_unique_task_test_ids': len(cpu_ids),
              'fixed_original_native_tree_instances': len(cpu_original_native_instances),
              'current_native_tree_status_counts': dict(sorted(cpu_native_statuses.items())),
              'current_initial_tree_status_counts': dict(sorted(cpu_statuses.items())),
              'remaining_SKIPPED_tree_slots': cpu_statuses['skipped'],
              'fixed_ids': [{'task': iid, 'test_id': tid} for iid, tid in sorted(cpu_ids)]}}
    return {'scope': 'Pre-registered label-free Phase 4 seal only; no post-hoc analysis',
        'run_directory': RUN.relative_to(ROOT).as_posix(), 'run_manifest': manifest_info,
        'H1': h1, 'H1b': h1b, 'H2': h2, 'H3': h3, 'four_policy_reports': policy_counts,
        'INVALID_ID_accounting_verdict_differences': sensitivity,
        'integrity': {'ok': not unexplained, 'original_native_FAIL_tasks': len(original_fail_tasks),
            'original_native_FAIL_audit': integrity_rows, 'unexplained_disappearing_native_FAILs': unexplained,
            'manifest_verified_before_and_after_computation': True},
        'cap_hits': caps, 'seal_retries': 0,
        'category_count_units': {'INVALID_ID_NOT_REACHED_TIMEOUT_COLLECTION_ERROR_COLLECTOR_FALLBACK': 'initial selected tree slots; confirmations and policy copies excluded',
            'FLAKY_REGRESSION_ERROR': 'selected families in primary Policy C final outcomes; counted once per task/test',
            'GENERATED_INPUT_CHANGED': 'tasks with this recorded flag in any actual pass or primary policy report'},
        'category_counts_total': dict(category_totals), 'confirmation_run_count': confirmations_total,
        'per_task': per_task, 'input_sha256': dict(sorted(INPUT_HASHES.items())),
        'script_sha256': hash_file(Path(__file__)), 'correctness_labels_read': False,
        'oracle_data_read': False, 'label_joins': False, 'Docker_calls': 0, 'benchmark_test_executions': 0}


def markdown(result):
    lines = ['# Phase 4 attempt 4: pre-registered label-free seal', '',
             'Manifest: `%s`; %s files, %s bytes.' % (result['run_manifest']['sha256'], result['run_manifest']['file_count'], result['run_manifest']['total_bytes']), '',
             '| Quantity | Value | Prediction | Falsification |', '|---|---:|---|---|']
    for key in ('H1', 'H1b', 'H2'):
        h = result[key]
        lines.append('| %s | %s/%s (%.4f%%) | %s | %s |' % (key, h['numerator'], h['denominator'], 100*h['fraction'], 'met' if h['prediction_met'] else 'not met', 'falsified' if h['falsified'] else 'not falsified'))
    h = result['H1']['secondary_informational']
    lines += ['', 'H1 **secondary informational**, INVALID_ID removed from B1: %s/%s (%.4f%%). The primary denominator and thresholds are unchanged.' % (h['numerator'], h['denominator'], 100*h['fraction']),
              '', 'H2 secondary, including REGRESSION_ERROR: %s/83.' % result['H2']['secondary_including_REGRESSION_ERROR'],
              '', 'H3: Policy S yes/no = %s/83 versus B2 = 21 (change %+d). Descriptive only; no prediction/falsification thresholds were registered.' % (result['H3']['Policy_S_yes_no'], result['H3']['delta_vs_B2']),
              '', '## Four policy reports', '', '| Policy | INVALID_ID accounting | PASS | FAIL | REGRESSION_ERROR | INCOMPLETE | NOT_AVAILABLE | BASELINE_UNRELIABLE | Yes/no primary | Secondary incl. REGRESSION_ERROR |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for policy, row in result['four_policy_reports'].items():
        c = row['verdict_counts']
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (policy[0], 'missing' if policy.endswith('missing') else 'excluded', *[c.get(k,0) for k in ('PASS','FAIL','REGRESSION_ERROR','INCOMPLETE','NOT_AVAILABLE','BASELINE_UNRELIABLE')], row['yes_no_primary_PASS_or_FAIL'], row['secondary_including_REGRESSION_ERROR']))
    lines += ['', '## INVALID_ID accounting differences', '', '| Policy | Task | Excluded | Missing |', '|---|---|---|---|']
    for policy, rows in result['INVALID_ID_accounting_verdict_differences'].items():
        if not rows:
            lines.append('| %s | None | — | — |' % policy)
        for row in rows:
            lines.append('| %s | `%s` | %s | %s |' % (policy, row['task'], row['excluded'], row['missing']))
    lines += ['', '## Remaining skips', '', 'Selected-tree SKIPPED slots; each slot has one reason group. Exact captured reasons and overlapping strict nonbinary task groups are in results.json.', '', '| Reason group | Slots |', '|---|---:|']
    for reason,count in result['H3']['remaining_selected_tree_SKIPPED_by_reason_group'].items():
        lines.append('| %s | %s |' % (reason,count))
    cpu = result['H3']['CPU_conditioned']
    lines += ['', '**CPU-conditioned tests (separate):** %s fixed selected families, covering %s frozen-original native tree instances; %s remain SKIPPED selected tree slots. Current selected-tree statuses: `%s`. Current concrete native-tree statuses: `%s`.' % (cpu['fixed_original_unique_task_test_ids'], cpu['fixed_original_native_tree_instances'], cpu['remaining_SKIPPED_tree_slots'], json.dumps(cpu['current_initial_tree_status_counts'],sort_keys=True), json.dumps(cpu['current_native_tree_status_counts'],sort_keys=True)),
              '', '## Integrity', '', '**%s**: %s original native FAIL tasks reconciled; %s unexplained disappearing native FAILs. Run bytes were reverified before and after computation.' % ('PASS' if result['integrity']['ok'] else 'FAIL — STOP; no seal tag',result['integrity']['original_native_FAIL_tasks'],len(result['integrity']['unexplained_disappearing_native_FAILs'])), '', '| Original native FAIL task | Present as FAIL under all four policies |', '|---|---|']
    for row in result['integrity']['original_native_FAIL_audit']:
        lines.append('| `%s` | %s |' % (row['task'],'Yes' if row['present_under_all_four_policies'] else 'Recorded cause; see results.json'))
    lines += ['', '## Cap hits', '', 'No benchmark or cap retries were performed by the seal computation.', '', '| Task | Tree | Scope | NOT_REACHED | TIMEOUT | Budget seconds |', '|---|---|---|---:|---:|---:|']
    if not result['cap_hits']:
        lines.append('| None | — | — | 0 | 0 | — |')
    for row in result['cap_hits']:
        lines.append('| `%s` | %s | %s | %s | %s | %s |' % (row['task'],row['tree'],row['scope'],row['NOT_REACHED'],row['TIMEOUT'],row['budget_s']))
    lines += ['', '## Category totals', '', 'Initial selected tree slots for INVALID_ID/NOT_REACHED/TIMEOUT/COLLECTION_ERROR/COLLECTOR_FALLBACK; selected final Policy C families for FLAKY/REGRESSION_ERROR; flagged tasks for GENERATED_INPUT_CHANGED. Policy copies and confirmations do not inflate initial-slot counts.', '', '| Category | Count |', '|---|---:|']
    for category in CATEGORIES:
        lines.append('| %s | %s |' % (category,result['category_counts_total'].get(category,0)))
    lines += ['', '**Confirmation-run count:** %s actual isolated tree calls, counted once from native_passes minus the two initial calls and checked against the primary stored report.' % result['confirmation_run_count'],
              '', '## Per-task label-free table', '', '| Task | Policy C | Policy S | Base admitted/selected | Patched admitted/selected |', '|---|---|---|---:|---:|']
    for row in result['per_task']:
        b,p=row['trees']['base'],row['trees']['patched']
        lines.append('| `%s` | %s | %s | %s/%s | %s/%s |' % (row['task'],row['policies']['C_invalid_excluded'],row['policies']['S_invalid_excluded'],b['admitted'],b['selected'],p['admitted'],p['selected']))
    lines += ['', '## Counts by task', '', '| Task | '+ ' | '.join(CATEGORIES) +' | Confirmation runs |', '|---|'+'---:|'*(len(CATEGORIES)+1)]
    for row in result['per_task']:
        lines.append('| `%s` | %s | %s |' % (row['task'],' | '.join(str(row['counts'].get(c,0)) for c in CATEGORIES),row['confirmation_runs']))
    lines += ['', 'Fix 5 residual identities were reconstructed from its hash-pinned original captures, static overlay and gap provenance using the exact embedded Fix 5 parser. The reconstruction must reproduce 23,761 admitted B1 slots and the 13,853 fixed residual before any live hypothesis is calculated. INVALID_ID is never admitted. Expansion admission is unanimous, and collector fallback is excluded.', '',
              'No correctness labels, oracle data, label joins, Docker, benchmark execution, quarantined attempts, or post-hoc quantities were used.', '']
    return '\n'.join(lines).encode()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        entries, info = verify_run()
        result = compute(entries, info)
        verify_run()
    except ManifestMismatch as exc:
        result = {'integrity': {'ok': False, 'manifest_mismatch': str(exc)},
                  'hypotheses': 'NOT COMPUTED / INVALIDATED', 'correctness_labels_read': False}
        (OUT / 'results.json').write_bytes(json_bytes(result))
        (OUT / 'results.md').write_text('# Integrity incident\n\nManifest mismatch; stop. No seal tag.\n')
        (OUT / 'incident.md').write_text('# Attempt 4 integrity incident\n\n' + str(exc) + '\n\nNo further computation or seal tag is permitted.\n')
        return 2
    (OUT / 'results.json').write_bytes(json_bytes(result))
    (OUT / 'results.md').write_bytes(markdown(result))
    if not result['integrity']['ok']:
        (OUT / 'incident.md').write_text('# Attempt 4 integrity incident\n\nUnexplained disappearing native FAIL evidence. See results.json. Stop; do not create the seal tag.\n')
    print(json.dumps({'integrity_ok': result['integrity']['ok'],
        'results_json_sha256': hash_file(OUT / 'results.json'),
        'results_md_sha256': hash_file(OUT / 'results.md')}, sort_keys=True))
    return 0 if result['integrity']['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
