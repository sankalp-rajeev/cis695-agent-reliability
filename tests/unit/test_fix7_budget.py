"""The pass cap covers collection and execution; unreached work stays missing."""

import ast
import json
import subprocess
import sys

import pytest

from reliability.env import clean_env
from reliability.verifier.collection import _NATIVE_DRIVER, ValidationPass
from reliability.verifier.container import _BATCH_DRIVER, ContainerTestExecutor, run_from_capture
from reliability.verifier.id_validation import IDValidation, merge_native
from reliability.verifier.regression import (
    Outcome,
    RegressionConfig,
    RunResult,
    TestResult,
    TestStatus,
    classify,
    completeness_of,
    run_from_dict,
    run_to_dict,
)
from reliability.verifier.selection import TestRunner
from reliability.verifier.validated_run import apply_validation


def local_program(tmp_path, code):
    for name in ('verifier_ids', 'verifier_out.txt', 'verifier_events.jsonl', 'verifier_pgid',
                 'verifier_module_ids.json', 'verifier_collect_request.json',
                 'verifier_collect_pgid', 'verifier_collect_partial.json', 'verifier_django_collect.py'):
        code = code.replace('/tmp/' + name, str(tmp_path / name))
    program = tmp_path / 'driver.py'
    program.write_text(code.replace('"python"', repr(sys.executable)))
    return program


def test_execution_deadline_retains_completed_cases_and_stops_later_modules(tmp_path):
    tests = tmp_path / 'tests'
    tests.mkdir()
    (tests / 'runtests.py').write_text("""import sys,time
print('test_done (a.Case.test_done) ... ok',flush=True)
time.sleep(10)
""")
    ids = ('a.Case.test_done', 'a.Case.test_pending', 'b.Case.test_later')
    (tmp_path / 'verifier_ids').write_text('\n'.join(ids))
    (tmp_path / 'verifier_module_ids.json').write_text(json.dumps({t: t[0] for t in ids}))
    program = local_program(tmp_path, _BATCH_DRIVER)
    subprocess.run([sys.executable, str(program), 'django', '0.3', '2.0'], cwd=tmp_path,
                   env=clean_env(), capture_output=True, check=True, timeout=5)
    events = tuple(json.loads(line) for line in (tmp_path / 'verifier_events.jsonl').read_text().splitlines())
    starts = [e for e in events if e['event'] == 'start']
    assert len(starts) == 1 and starts[0]['module'] == 'a'
    result = run_from_capture(TestRunner('django', ''), ids,
                             runner_log=(tmp_path / 'verifier_out.txt').read_bytes(), events=events,
                             budget_s=2.3)
    assert result.by_id()[ids[0]].status is TestStatus.PASSED
    for tid in ids[1:]:
        assert result.by_id()[tid].status is TestStatus.NOT_REACHED
        assert result.by_id()[tid].elapsed_s >= 2.3
    assert result.timed_out and result.budget_s == 2.3
    assert not any(e.get('retry') for e in starts)


def test_collection_deadline_retains_partial_receipts_without_invalid_ids(tmp_path):
    ids = ['tests/a.py::Case::test_a', 'tests/b.py::Case::test_b', 'tests/c.py::Case::test_c']
    (tmp_path / 'verifier_collect_request.json').write_text(json.dumps(
        {'runner': 'django', 'ids': ids, 'module_timeout_s': 10, 'budget_s': 0.3}))
    (tmp_path / 'verifier_django_collect.py').write_text("""import sys,json,time
r=json.load(sys.stdin)
if r['module']=='b':time.sleep(10)
print(json.dumps({t:dict(ids=[t],completed=True,returncode=0) for t in r['labels']}))
""")
    program = local_program(tmp_path, _NATIVE_DRIVER)
    proc = subprocess.run([sys.executable, str(program)], cwd=tmp_path, env=clean_env(),
                          capture_output=True, text=True, check=True, timeout=5)
    receipt = json.loads(proc.stdout)
    assert receipt == json.loads((tmp_path / 'verifier_collect_partial.json').read_text())
    assert receipt['ids'][ids[0]]['completed'] is True
    assert receipt['ids'][ids[1]]['collection_status'] == 'COLLECTION_ERROR'
    assert receipt['ids'][ids[2]]['collection_status'] == 'NOT_REACHED'
    static = tuple(IDValidation(t, 'runnable_test', (t,)) for t in ids)
    result = merge_native(static, receipt['ids'])
    assert result[0].valid
    assert result[2].unavailable and result[2].failure_status == 'NOT_REACHED'
    assert result[2].elapsed_s >= 0.3


def test_collection_time_is_subtracted_before_execution(monkeypatch):
    import reliability.verifier.container as module
    now = [0.0]
    monkeypatch.setattr(module.time, 'monotonic', lambda: now[0])
    tid = 't.py::test_a'
    def validate(*args, **kwargs):
        assert kwargs['timeout_s'] == 1.0
        now[0] = 1.1
        return ValidationPass((IDValidation(tid, 'runnable_test', (tid,)),))
    monkeypatch.setattr(module, 'validate_in_container', validate)
    class Container:
        def set_patched(self, value): pass
        def exec_input(self, *args, **kwargs): return 0, ''
        def exec_raw(self, command, timeout_s):
            assert not command.startswith('python /tmp/verifier_driver.py')
            return 0, b'', b'', False
    result = ContainerTestExecutor(Container()).run((tid,), patched=False, timeout_s=1)
    assert result.by_id()[tid].status is TestStatus.NOT_REACHED
    assert result.by_id()[tid].elapsed_s == 1.1
    assert result.duration_s == 1.1 and result.budget_s == 1


@pytest.mark.parametrize('compatible', [False, True])
def test_not_reached_is_missing_under_each_policy_and_round_trips(compatible):
    tid = 't.py::test_a'
    record = IDValidation(tid, 'runnable_test', (tid,))
    run = apply_validation(RunResult(results=(TestResult(tid, TestStatus.NOT_REACHED, elapsed_s=1800),),
                                   evidence_complete=True, budget_s=1800), ValidationPass((record,)))
    assert run_from_dict(run_to_dict(run)) == run
    assert not run.validation[0]['admitted']
    assert run.results[0].elapsed_s == 1800
    assert classify(tid, run.results[0], run.results[0]) is Outcome.NOT_REACHED
    assert not Outcome.NOT_REACHED.executed
    assert completeness_of((tid,), run, run, skip_compatible=compatible)[0] == 'INCOMPLETE_CONFIRMED'


def test_default_budget_and_standalone_python36_syntax():
    assert RegressionConfig().per_pass_timeout_s == 1800
    ast.parse(_BATCH_DRIVER, feature_version=(3, 6))
    ast.parse(_NATIVE_DRIVER, feature_version=(3, 6))
