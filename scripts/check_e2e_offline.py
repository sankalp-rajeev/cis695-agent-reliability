#!/usr/bin/env python3
"""A1/A2 against the package path; never run benchmark code or a model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.archive_tree import ArchiveTree
from reliability.verifier.g1_reference import read_collection
from reliability.verifier.guarded_v2 import run_policies
from reliability.verifier.native_reference import collection_reference, empty_reference, load_drift, project_collection
from reliability.verifier.patch import parse_patch
from reliability.verifier.regression import RunResult, run_from_dict
from reliability.verifier.selection import Selection, SelectionConfig, select_tests
from reliability.verifier.task_specs import ROOT, load_registries, require_hash, sha, write
from reliability.verifier.generic_health import paired_exception_scope, exception_metadata, rules_stamp, check_generic_pair
from reliability.verifier.run_health import exception_match, exception_rules

FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
SEAL = ROOT / 'reports/next_phases/phase4_rerun/attempt4_seal'
G1 = ROOT / 'reports/next_phases/phase4_rerun/fix18b_g1'
POLICIES = ('C_invalid_excluded', 'C_invalid_missing', 'S_invalid_excluded', 'S_invalid_missing')


def projected(path, schema):
    return JSONProjection(path.read_text()).project(schema)


def frozen_tasks():
    require_hash(FROZEN / 'tasks.json', '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625')
    return projected(FROZEN / 'tasks.json', {'*': {k: True for k in
        ('instance_id', 'patch_path', 'patch_sha256', 'selections')}})


def a1(specs, output):
    rows = []
    for row in frozen_tasks():
        iid = row['instance_id']
        spec = specs[iid]
        patch_path = FROZEN / row['patch_path']
        require_hash(patch_path, row['patch_sha256'])
        with ArchiveTree(spec.source.archive_path) as tree:
            selected = select_tests(parse_patch(patch_path.read_text()), tree, SelectionConfig())
        expected_path = FROZEN / row['selections']['v2']
        expected = projected(expected_path, {'tests': True})['tests']
        actual = list(selected.tests)
        write(output / 'selections' / iid / 'v2.json', {'instance_id': iid, 'tests': actual})
        rows.append({'instance_id': iid, 'same_ids_and_order': actual == expected,
                     'selected_count': len(actual), 'expected_sha256': sha(expected_path),
                     'selection_sha256': sha(output / 'selections' / iid / 'v2.json')})
        if actual != expected:
            write(output / 'A1.json', {'status': 'FAIL', 'tasks': rows})
            raise ValueError('A1 selection mismatch: ' + iid)
    result = {'status': 'PASS', 'matched': len(rows), 'tasks': rows}
    write(output / 'A1.json', result)
    print(json.dumps({'A1': 'PASS', 'matched': len(rows)}), flush=True)
    return {r['instance_id']: r for r in frozen_tasks()}


class SealedExecutor:
    def __init__(self, base, patched, confirmations):
        self.calls = [(False, base), (True, patched)] + [
            (r.confirmation['tree'] == 'patched', r) for r in confirmations]
        self.index = 0

    def run(self, tests, *, patched, timeout_s):
        if self.index >= len(self.calls):
            raise ValueError('Sealed captures exhausted')
        expected_tree, run = self.calls[self.index]
        if expected_tree != patched or tuple(run.requested_tests) != tuple(tests) or timeout_s != 1800:
            raise ValueError('Sealed execution request mismatch at call ' + str(self.index))
        self.index += 1
        return run


def a2(specs, metadata, captures, output):
    authority = projected(SEAL / 'results.json', {'run_manifest': {
        'sha256': True, 'file_count': True, 'total_bytes': True}})['run_manifest']
    require_hash(SEAL / 'run_manifest.sha256', authority['sha256'])
    entries = {}
    for line in (SEAL / 'run_manifest.sha256').read_text().splitlines():
        if line and not line.startswith('#'):
            digest, name = line.split('  ', 1)
            if Path(name).is_absolute() or '..' in Path(name).parts or name in entries:
                raise ValueError('Unsafe/duplicate seal path')
            entries[name] = digest
    if len(entries) != authority['file_count'] or len(entries) != 1799:
        raise ValueError('Sealed run manifest file count mismatch')
    verified, total_bytes = [], 0
    try:
        for name, digest in entries.items():
            if any(word in name.casefold() for word in ('oracle', 'grade', 'grader', 'label', 'gold', 'posthoc')):
                raise ValueError('Required sealed input has a forbidden path: ' + name)
            path = captures / name
            require_hash(path, digest)
            verified.append(name)
            total_bytes += path.stat().st_size
        if total_bytes != authority['total_bytes']:
            raise ValueError('Sealed run byte count mismatch')
    except Exception as exc:
        write(output / 'seal_check.json', {'status': 'HARD_STOP', 'files_verified': len(verified), 'error': str(exc)})
        raise
    write(output / 'seal_check.json', {'status': 'VERIFIED', 'files': len(verified), 'bytes': total_bytes,
          'capture_root': str(captures), 'manifest_sha256': authority['sha256']})
    print(json.dumps({'seal': 'VERIFIED', 'files': len(verified), 'bytes': total_bytes}), flush=True)
    def read(name, schema):
        path = captures / name
        require_hash(path, entries[name])
        return projected(path, schema)
    drift = load_drift()
    rows = []
    run_schema = {k: True for k in RunResult.__dataclass_fields__}
    for iid, spec in specs.items():
        tests = tuple(projected(FROZEN / metadata[iid]['selections']['v2'], {'tests': True})['tests'])
        references, generic_stages = {}, {}
        for tree in ('base', 'patched'):
            collection = read_collection(G1 / 'tasks' / iid / tree / 'collection.json')
            # Re-evaluate eligibility against the frozen raw collection messages;
            # published per-task entries retain priority, including nonmatches.
            generic_stages[tree] = []
            with paired_exception_scope(iid, spec.source.pre_install.repo):
                for stage in collection.get('stage_health', ()):
                    matches = [exception_match(exception_rules(), iid, stage.get('module', ''),
                        stage['stage'], message, tree=tree) for message in stage.get('messages', ())]
                    if matches and all(matches) and exception_metadata(matches):
                        generic_stages[tree].append({**stage, **exception_metadata(matches),
                            'allowed_exception': sorted({m['cause'] for m in matches})})
            references[tree] = collection_reference(iid, tree, tests, collection, drift)
            projection = project_collection(iid, tree, collection, empty_reference(iid, tree, tests, drift))
            if projection['halt']:
                write(output / 'A2_halt.json', {'task': iid, 'tree': tree, 'projection': projection})
                raise ValueError('A2 G1 projected halt: ' + iid + '/' + tree)
        prefix = 'tasks/' + iid + '/'
        expected = read(prefix + 'result.json', {'policies': {p: {'signal': True, 'outcomes': True,
                        'confirmations': {'*': run_schema}} for p in POLICIES}})['policies']
        base, patched = (run_from_dict(read(prefix + name + '.json', run_schema)) for name in ('base', 'patched'))
        confirmations = [run_from_dict(r) for r in expected['C_invalid_excluded'].get('confirmations', [])]
        executor = SealedExecutor(base, patched, confirmations)
        pair_reasons = check_generic_pair(generic_stages)
        if pair_reasons:
            raise ValueError('A2 generic both-tree mismatch: ' + iid)
        with paired_exception_scope(iid, spec.source.pre_install.repo):
            reports = run_policies(iid, Selection(tests=tests, runner=spec.runner), executor,
                                   references, output / 'tasks' / iid)
        differences = {p: {'expected_signal': expected[p]['signal'], 'actual_signal': reports[p].signal,
                           'outcomes_equal': reports[p].outcomes == expected[p]['outcomes']}
                       for p in POLICIES if reports[p].signal != expected[p]['signal'] or
                       reports[p].outcomes != expected[p]['outcomes']}
        row = {'instance_id': iid, 'equal': not differences, 'differences': differences,
               'signal': reports['S_invalid_excluded'].signal,
               'generic_rule_modules': sorted({s['module'] for stages in generic_stages.values() for s in stages})}
        rows.append(row)
        if differences:
            write(output / 'A2.json', {'status': 'FAIL', 'tasks': rows})
            raise ValueError('A2 replay difference: ' + iid)
        print(json.dumps({'A2_task': iid, 'equal': True}), flush=True)
    write(output / 'A2.json', {'status': 'PASS', 'matched': len(rows), 'health_halts': 0, 'tasks': rows,
        'generic_exception_rules': rules_stamp(),
        'generic_rule_tasks': sum(bool(r['generic_rule_modules']) for r in rows)})


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-specs', type=Path, default=ROOT / 'configs/e2e/task_specs_83.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--captures', type=Path)
    parser.add_argument('--a1-only', action='store_true')
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / 'runs'):
        raise ValueError('Offline outputs must be under runs/')
    specs, _ = load_registries([args.task_specs])
    metadata = a1(specs, args.output)
    if not args.a1_only:
        if args.captures is None or not args.captures.is_dir():
            print('A2 NOT_RUN: sealed capture directory is required; no replay was attempted.')
            return 2
        a2(specs, metadata, args.captures, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
