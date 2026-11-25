"""Paired GIS environment exceptions through real collectors and V2 execution."""

import base64
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from reliability.verifier import guarded_v2, run_v1_4_1 as runtime
from reliability.verifier.generic_health import (
    check_generic_pair, paired_exception_scope, rules_manifest, rules_stamp,
)
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.run_health import allowed_failure, exception_match, module_execution_stages, RunHealthError
from reliability.verifier.selection import Selection, TestRunner
from tests.unit.test_fix14_health import LocalContainer


GIS = 'tests/gis_tests/newapp/tests.py::Example::test_body'
HEALTHY = 'tests/basic/tests.py::Example::test_body'
MESSAGE = 'A GIS database backend is required to run gis_tests'


def local_runtime(tmp_path, monkeypatch, messages, repo='django/django'):
    created = []

    class Container(LocalContainer):
        def __init__(self, instance_id, patch, **kwargs):
            root = tmp_path / ('container' + str(len(created)))
            root.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            super().__init__(root)
            self.instance_id = instance_id
            self.source_integrity = {'status': 'VERIFIED'}
            receipt = kwargs['source_receipt_path']
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps(self.source_integrity))
            for module in ('gis_tests/newapp', 'basic'):
                folder = root / 'tests' / module
                folder.mkdir(parents=True)
                for package in (folder, folder.parent):
                    (package / '__init__.py').touch()
                (folder / 'tests.py').write_text(
                    'import unittest\nclass Example(unittest.TestCase):\n'
                    '    def test_body(self):\n        self.assertTrue(True)\n')
            created.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def generated_snapshot(self, *args, **kwargs):
            return {'files': {}}

        def set_patched(self, patched):
            self._patch_applied = patched
            message = messages[int(patched)]
            (self.root / 'tests/runtests.py').write_text(
                'import os, sys, unittest\n'
                'sys.path.insert(0, os.path.dirname(__file__))\n'
                'def setup(verbosity, test_labels, parallel):\n'
                f'    if {message!r} and any(x.startswith("gis_tests.") for x in test_labels):\n'
                f'        print("Aborting: " + {message!r} + ".")\n'
                '        sys.exit(1)\n'
                'if __name__ == "__main__":\n'
                '    if "--help" in sys.argv: print("help"); sys.exit(0)\n'
                '    labels = [x for x in sys.argv[1:] if not x.startswith("--")]\n'
                '    unittest.main(module=None, argv=[sys.argv[0]] + labels, verbosity=2)\n')

        def exec_raw(self, command, timeout_s):
            proc = subprocess.run(self.command(command), shell=True, cwd=self.root,
                                  env=self.environment(), capture_output=True, timeout=timeout_s)
            return proc.returncode, proc.stdout, proc.stderr, False

    monkeypatch.setattr(guarded_v2, 'FrozenContainer', Container)
    monkeypatch.setattr(runtime, 'FrozenContainer', Container)
    patch = tmp_path / 'patch.diff'
    patch.write_text('synthetic patch')
    task = SimpleNamespace(instance_id='fixture', image_id='local',
        source=SimpleNamespace(pre_install=SimpleNamespace(repo=repo)),
        runner=TestRunner('django', 'local fixture', django_parallel_one=False))
    return task, patch, created


# The last two abort the GIS module with SystemExit on both trees. Amendment A7
# (part F) excludes such a paired collection error and runs the rest; before A7
# they blocked, because only the GIS guard rule could unblock a module.
@pytest.mark.parametrize('messages,repo,proceeds', [
    ((MESSAGE, MESSAGE), 'django/django', True),
    ((MESSAGE, ''), 'django/django', False),
    ((MESSAGE, 'different failure'), 'django/django', False),
    (('different failure', 'different failure'), 'django/django', 'excluded'),
    ((MESSAGE, MESSAGE), 'example/project', 'excluded'),
])
def test_g1_paired_rule_controls_real_v2(tmp_path, monkeypatch, messages, repo, proceeds):
    task, patch, created = local_runtime(tmp_path, monkeypatch, messages, repo)
    folder = tmp_path / 'verification'
    call = lambda: runtime.run_v2(task, patch, Selection(tests=(GIS, HEALTHY), runner=task.runner),
        folder, experiment='unit', drift={}, stamps={'g1_receipt_sha256': {}})
    if proceeds == 'excluded':
        signal = call()
        assert signal.findings['n_executed'] == 1 and signal.findings['signal'] == 'PASS'
        assert signal.findings['paired_collection_exclusions'] == [{
            'module': GIS.split('::')[0], 'exception_type': 'SystemExit',
            'excluded_tests': [GIS], 'trees': ['base', 'patched']}]
        assert len(created) == 5
        health = [json.loads(line) for line in (folder / 'health.jsonl').read_text().splitlines()]
        assert [r['status'] for r in health if r.get('scope') == 'G1'] == ['BLOCKED', 'BLOCKED']
        assert [r['status'] for r in health if r.get('scope') == 'G1_after_paired_exclusion'] == [
            'READY', 'READY']
        return
    if proceeds:
        signal = call()
        assert signal.findings['n_executed'] == 1
        # Environment-unavailable stays missing evidence, just as for per-task entries.
        assert signal.findings['signal'] == 'INCOMPLETE'
        assert len(created) == 3
        policies = json.loads((folder / 'v2_policies.json').read_text())['policies']
        assert set(policies) == {
            f'{policy}_invalid_{handling}'
            for policy in 'SCP' for handling in ('excluded', 'missing')
        }
        for policy in policies.values():
            for tree in ('baseline', 'patched'):
                assert not any('gis_tests' in e.get('module', '') for e in policy[tree]['events'])
    else:
        with pytest.raises(RunHealthError):
            call()
        assert len(created) == 2
        assert not (folder / 'v2_policies.json').exists()
    health = [json.loads(line) for line in (folder / 'health.jsonl').read_text().splitlines()]
    g1 = [r for r in health if r.get('scope') == 'G1']
    assert all(r['status'] == 'READY' for r in g1) == proceeds
    for row in health:
        assert row['generic_exception_rules'] == rules_stamp()
    applications = [s for r in g1 for s in r['stages'] if s.get('exception_source') == 'generic_rule']
    assert len(applications) == (2 if proceeds else 0)
    for stage in applications:
        assert stage['both_trees_confirmed']
        assert stage['rules_file_sha256'] == rules_stamp()['sha256']
        assert stage['rule_id'] == 'django_sqlite_gis_guard'
    if proceeds:
        for tree in ('base', 'patched'):
            collection = json.loads((folder / 'g1/tasks/fixture' / tree / 'collection.json').read_text())
            record = next(r for r in collection['records'] if r['selected_id'] == GIS)
            assert record['unavailable'] and not record['collector_fallback'] and not record['valid']


@pytest.mark.parametrize('matches', [True, False])
def test_per_task_presence_always_prevents_generic_fallback(matches):
    row = dict(instance_id='fixture', module=GIS.split('::')[0], stages=['native_collection'],
               trees=['base', 'patched'], required_message=MESSAGE if matches else 'other guard', cause='PER_TASK')
    with paired_exception_scope('fixture', 'django/django'):
        result = exception_match([row], 'fixture', row['module'], 'native_collection', MESSAGE, tree='base')
        assert result == (row if matches else None)
        assert allowed_failure([row], 'fixture', row['module'], 'module_execution', MESSAGE, tree='base') is None


def test_per_task_entry_uses_existing_accounting_through_g1_and_v2(tmp_path, monkeypatch):
    from reliability.verifier import collection, run_health
    task, patch, _ = local_runtime(tmp_path, monkeypatch, (MESSAGE, MESSAGE))
    row = dict(instance_id='fixture', module=GIS.split('::')[0],
               stages=['native_collection', 'module_execution'], trees=['base', 'patched'],
               required_message=MESSAGE, cause='GIS_GUARD')
    monkeypatch.setattr(collection, 'exception_rules', lambda: [row])
    monkeypatch.setattr(run_health, 'exception_rules', lambda: [row])
    folder = tmp_path / 'verification'
    signal = runtime.run_v2(task, patch, Selection(tests=(GIS, HEALTHY), runner=task.runner),
        folder, experiment='unit', drift={}, stamps={'g1_receipt_sha256': {}})
    assert signal.findings['n_executed'] == 1 and signal.findings['signal'] == 'INCOMPLETE'
    health = [json.loads(line) for line in (folder / 'health.jsonl').read_text().splitlines()]
    for record in (r for r in health if r.get('scope') == 'G1'):
        assert record['status'] == 'READY'
        stage = next(s for s in record['stages'] if s.get('module') == row['module'])
        assert stage['allowed_exception'] == ['GIS_GUARD']
        assert 'exception_source' not in stage and 'rule_id' not in stage


def test_v2_rechecks_both_trees_instead_of_trusting_g1(tmp_path):
    from reliability.verifier.collection import collection_stages
    module = GIS.split('::')[0]
    runs = []
    with paired_exception_scope('fixture', 'django/django'):
        for tree, fails in [('base', True), ('patched', False)]:
            native = dict(ids=[] if fails else [GIS], completed=not fails,
                collection_status='COLLECTION_ERROR' if fails else 'COMPLETE',
                message=MESSAGE if fails else '', returncode=0)
            stages = collection_stages('fixture', (GIS,), {'ids': {GIS: native}}, [], tree=tree)
            runs.append(RunResult(results=(TestResult(GIS, TestStatus.COLLECTION_ERROR if fails else TestStatus.PASSED),),
                requested_tests=(GIS,), stage_health=stages))
        class Executor:
            def run(self, *args, **kwargs):
                return runs.pop(0)
        with pytest.raises(RunHealthError, match='both-tree failure'):
            guarded_v2.run_policies('fixture', Selection(tests=(GIS,), runner=TestRunner('django', 'fixture')),
                Executor(), {tree: [] for tree in ('base', 'patched')}, tmp_path)
    assert not (tmp_path / 'v2_policies.json').exists()
    health = json.loads((tmp_path / 'health.jsonl').read_text().splitlines()[-1])
    assert health['halt'] and health['trees'][0]['G3']['halt']


@pytest.mark.parametrize('message', [MESSAGE + ' changed', MESSAGE + '\nRuntimeError: another failure',
    MESSAGE + '\nSystemExit: 2', 'a different GIS failure'])
def test_guard_text_does_not_hide_other_failures(message):
    with paired_exception_scope('fixture', 'django/django'):
        assert allowed_failure([], 'fixture', GIS.split('::')[0], 'native_collection', message, tree='base') is None


@pytest.mark.parametrize('module,stage', [('tests/gis_tests_other/a.py', 'native_collection'),
    ('tests/gis_tests/../a.py', 'native_collection'), ('tests/other.py', 'native_collection'),
    ('tests/gis_tests/a.py', 'runner_startup')])
def test_rule_path_and_stage_are_narrow(module, stage):
    with paired_exception_scope('fixture', 'django/django'):
        assert allowed_failure([], 'fixture', module, stage, MESSAGE, tree='base') is None
    assert allowed_failure([], 'fixture', GIS.split('::')[0], 'native_collection', MESSAGE, tree='base') is None


def test_execution_failure_requires_both_trees_and_records_provenance():
    module = GIS.split('::')[0]
    data = ('Aborting: ' + MESSAGE + '.\n').encode()
    run = RunResult(results=(TestResult(GIS, TestStatus.NOT_RUN),), runner_log_b64=base64.b64encode(data).decode(),
        events=({'event': 'start', 'batch': 1, 'module': module, 'ids': [GIS], 'offset': 0},
                {'event': 'end', 'batch': 1, 'module': module, 'missing_ids': [GIS],
                 'load_failure': True, 'offset': len(data), 'returncode': 1},
                {'event': 'start', 'batch': 2, 'module': module, 'ids': [GIS], 'offset': 0},
                {'event': 'end', 'batch': 2, 'module': module, 'missing_ids': [GIS],
                 'load_failure': True, 'retry': True, 'parent': 1, 'offset': len(data), 'returncode': 1}))
    with paired_exception_scope('fixture', 'django/django'):
        stages = {tree: module_execution_stages('fixture', tree, 'pytest', run, []) for tree in ('base', 'patched')}
    assert stages['base'] and stages['patched']
    assert not check_generic_pair(stages)
    assert all(s['both_trees_confirmed'] for group in stages.values() for s in group)
    stages['patched'] = []
    assert check_generic_pair(stages)
    assert not stages['base'][0]['allowed_exception']


def test_one_committed_rule():
    manifest = rules_manifest()
    assert len(manifest['rules']) == 1
    rule = manifest['rules'][0]
    assert rule['cause'] == 'GIS_GUARD' and rule['repo'] == 'django/django'
    assert rule['required_message'] == MESSAGE and rule['require_both_trees']


@pytest.fixture
def source_amendments(tmp_path, monkeypatch):
    scripts = Path(__file__).resolve().parents[2] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('release_checker', scripts / 'verify_e2e_v1_4_1.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    sources, frozen = [], []
    for path in ('src/reliability/verifier/collection.py', 'src/reliability/verifier/run_health.py'):
        file = tmp_path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'new source')
        old, new = (hashlib.sha256(value).hexdigest() for value in (b'old source', b'new source'))
        sources.append(dict(path=path, historical_sha256=old, release_sha256=new))
        frozen.append(dict(manifest='reports/umgpt_probe/frozen_files.json', path=path,
            expected_sha256=old, actual_sha256=new, status='MISMATCH'))
    manifest = tmp_path / 'configs/e2e/v1_4_3_source_amendments.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(dict(release='e2e-v1.4.3',
        base_commit='8a0aea302cce60c4aee6791c668422346fb9382f', sources=sources)))
    monkeypatch.setattr(checker, 'SOURCE_AMENDMENTS_SHA256', hashlib.sha256(manifest.read_bytes()).hexdigest())
    return checker, frozen, manifest


def test_source_amendments_allow_only_exact_historical_to_release_transition(tmp_path, source_amendments):
    checker, frozen, _ = source_amendments
    rows = checker.audit_release_sources(frozen, tmp_path)
    assert all(row['status'] == 'APPROVED_RELEASE_SOURCE' for row in rows)
    other = dict(path='other.py', status='MISMATCH')
    assert checker.audit_release_sources([*frozen, other], tmp_path)[-1] == other


@pytest.mark.parametrize('part', ['historical', 'current', 'manifest', 'missing'])
def test_source_amendments_reject_unregistered_changes(tmp_path, source_amendments, part):
    checker, frozen, manifest = source_amendments
    if part == 'historical':
        frozen[0]['expected_sha256'] = '0' * 64
    elif part == 'current':
        (tmp_path / frozen[0]['path']).write_bytes(b'unregistered source')
    elif part == 'manifest':
        manifest.write_bytes(manifest.read_bytes() + b' ')
    else:
        frozen.pop()
    with pytest.raises(ValueError, match='[Rr]elease source amendment'):
        checker.audit_release_sources(frozen, tmp_path)
