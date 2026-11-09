"""Fix 17 uses paired execution evidence and preserves frozen Django commands."""

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from reliability.verifier.container import ContainerTestExecutor, TaskContainer, _BATCH_DRIVER
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.run_health import RunHealthError, health_for_run
from reliability.verifier.selection import TestRunner
from tests.unit.test_fix14_health import LocalContainer
from tests.unit.test_phase4_launcher import launch, task_spec


@pytest.mark.parametrize('base_silent', [False, True])
def test_paired_silent_module_is_ERROR_only_after_base_progress(tmp_path, base_silent):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    ids = tuple('test_real.py::test_case_%d' % i for i in range(12))
    body = '\n'.join('def test_case_%d(): pass' % i for i in range(12))
    silent = 'import sys\nif "--collect-only" not in sys.argv: raise RuntimeError("module failed")\n'

    class Container(LocalContainer):
        def set_patched(self, patched):
            (self.root/'test_real.py').write_text((silent if patched or base_silent else '') + body)

    executor = ContainerTestExecutor(Container(tmp_path), TestRunner('pytest', 'fixture'), tmp_path/'evidence')
    base = executor.run(ids, patched=False, timeout_s=30)
    patch = executor.run(ids, patched=True, timeout_s=30)
    assert all(r.status is (TestStatus.NOT_RUN if base_silent else TestStatus.PASSED) for r in base.results)
    assert all(r.status is (TestStatus.NOT_RUN if base_silent else TestStatus.ERROR) for r in patch.results)
    assert len([e for e in patch.events if e['event'] == 'end']) == 13
    stages = [s for s in patch.stage_health if s['stage'] == 'module_execution']
    assert stages and all(s['identity_failure'] is base_silent for s in stages)
    health = health_for_run('fixture', 'patched', patch, {'admitted_ids': ids, 'g1_collected_ids': ids})
    assert health['G2']['lost_count'] == (12 if base_silent else 0)
    assert health['halt'] is base_silent
    if not base_silent:
        assert patch.evidence_complete and not patch.infrastructure_errors
        from reliability.verifier.regression import concrete_comparison
        base_cases, patch_cases = concrete_comparison(ids, base, patch)
        assert set(base_cases) == set(patch_cases) == set(ids)
        assert all(r.status is TestStatus.ERROR for r in patch_cases.values())


@pytest.mark.parametrize('failure', ['startup', 'driver', 'unfinished', 'malformed'])
def test_explicit_failure_halts_three_ID_tree_before_next_tree(tmp_path, monkeypatch, failure):
    ids = tuple('test_real.py::test_case_%d' % i for i in range(3))
    run = RunResult(results=tuple(TestResult(t, TestStatus.PASSED) for t in ids), requested_tests=ids)
    if failure == 'startup':
        run = replace(run, stage_health=({'stage': 'runner_startup', 'status': 'RUNNER_UNAVAILABLE',
                                        'input_count': 1, 'output_count': 0},))
    else:
        error = {'driver': 'capture driver exit 137', 'unfinished': 'unfinished runner batch',
                 'malformed': 'malformed capture events'}[failure]
        run = replace(run, infrastructure_errors=(error,))
    assert health_for_run('task', 'base', run, ids)['halt']
    calls = []

    class Executor:
        def __init__(self, *a, **k): pass
        def run(self, tests, *, patched, timeout_s):
            calls.append(patched)
            return run

    from tests.unit.test_fix14_health import ContainerShell
    monkeypatch.setattr(launch, 'FrozenContainer', ContainerShell)
    monkeypatch.setattr(launch, 'ContainerTestExecutor', Executor)
    monkeypatch.setattr(launch, 'run_regression', lambda *a, **k: pytest.fail('scored executor failure'))
    spec = replace(task_spec(tmp_path), tests=ids)
    with pytest.raises(RunHealthError):
        launch.run_task(spec, tmp_path/'task', 'fixture', {'base': ids, 'patched': ids}, tmp_path/'health.jsonl')
    assert calls == [False]
    record = json.loads((tmp_path/'health.jsonl').read_text())
    assert record['halt'] and record['capture']['requested_tests'] == list(ids)


def test_actual_startup_failure_with_three_selected_IDs(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    ids = tuple('test_real.py::test_case_%d' % i for i in range(3))
    (tmp_path/'test_real.py').write_text('\n'.join('def test_case_%d(): pass' % i for i in range(3)))

    class Container(LocalContainer, TaskContainer):
        source_spec = object()
        source_integrity = {'status': 'VERIFIED'}
        def set_patched(self, patched): pass
        def generated_snapshot(self, *a, **k): return {'files': {}}
        def exec(self, command, **kwargs):
            if command == 'python -m pytest --help':
                return 1, 'runner start-up failed'
            return super().exec(command, **kwargs)

    run = ContainerTestExecutor(Container(tmp_path), TestRunner('pytest', 'fixture')).run(
        ids, patched=False, timeout_s=30)
    assert all(r.status is TestStatus.RUNNER_UNAVAILABLE for r in run.results)
    assert not run.events
    record = health_for_run('fixture', 'base', run, ids)
    assert record['G2']['lost_count'] == 3 and not record['G2']['halt']
    assert record['halt'] and record['executor_failures']


@pytest.mark.parametrize('parallel_one', [False, True])
def test_Django_driver_matches_hash_verified_frozen_command(tmp_path, monkeypatch, parallel_one):
    ids = ('tests/a/tests.py::Case::test_a',)
    argv = ['python', 'tests/runtests.py', '--verbosity=2']
    if parallel_one:
        argv += ['--parallel', '1']
    argv += ['a.tests.Case.test_a']
    original = tmp_path/'original'/'task'/'v2'/'result.json'
    original.parent.mkdir(parents=True)
    launch.write(original, {'verdict': 'DO NOT DECODE', 'calls': [
        {'run': {'results': 'DO NOT DECODE', 'events': [{'argv': argv}]}}] * 2})
    reference = tmp_path/'reference'
    launch.write(reference/'manifest.json', {'input_sha256': {str(original): launch.sha(original)}})
    monkeypatch.setattr(launch, 'REFERENCE', reference)
    choice = launch.frozen_django_command_choice('task')
    assert choice['parallel_one'] is parallel_one
    runner = TestRunner('django', 'frozen argv', choice['parallel_one'])
    import shlex
    assert shlex.split(runner.command(ids, 'unused')) == argv

    # Execute the actual batch driver against a synthetic Django runner.
    tests = tmp_path/'tests'; tests.mkdir()
    (tests/'runtests.py').write_text('print("test_a (a.tests.Case) ... ok")\n')
    (tmp_path/'verifier_ids').write_text('a.tests.Case.test_a\n')
    (tmp_path/'verifier_module_ids.json').write_text(json.dumps({'a.tests.Case.test_a': 'tests/a/tests.py'}))
    driver = tmp_path/'driver.py'
    driver.write_text(_BATCH_DRIVER.replace('/tmp/verifier_', str(tmp_path/'verifier_')))
    from reliability.env import clean_env
    env = clean_env(); env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    args = [sys.executable, str(driver), 'django', '30', '0']
    if parallel_one:
        args.append('parallel_one')
    subprocess.run(args, cwd=tmp_path, env=env, check=True, capture_output=True, timeout=30)
    events = [json.loads(line) for line in (tmp_path/'verifier_events.jsonl').read_text().splitlines()]
    assert [e['argv'] for e in events if e['event'] == 'start'] == [argv]
    original.write_text('{}')
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        launch.frozen_django_command_choice('task')
