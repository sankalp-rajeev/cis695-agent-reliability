"""Focused completeness, compatibility and raw-evidence regression checks."""
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from reliability.verifier.container import _BATCH_DRIVER, ContainerTestExecutor, account_raw_output
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    completeness_of,
    integrity_verdict,
    run_from_dict,
    run_regression,
    run_to_dict,
)
from reliability.verifier.run import signal_from_regression
from reliability.verifier.selection import Selection, TestRunner


def run(statuses, **kwargs):
    return RunResult(results=tuple(TestResult(k, TestStatus(v)) for k,v in statuses.items()),
                     **kwargs)


@pytest.mark.parametrize('old', ['PASS','FAIL','NOT_AVAILABLE','BASELINE_UNRELIABLE'])
@pytest.mark.parametrize('state', ['COMPLETE','INCOMPLETE_CONFIRMED','UNVERIFIABLE'])
def test_only_pass_can_change(old, state):
    new = integrity_verdict(old, state)
    assert new == ('INCOMPLETE' if old == 'PASS' and state != 'COMPLETE' else old)


def test_unknown_historical_capture_is_not_an_invented_timeout():
    b = run({'t':'passed'})
    state, reasons = completeness_of(('t',), b, b)
    assert state == 'UNVERIFIABLE'
    assert all('capture unavailable' in s for s in reasons)
    assert b.by_id()['t'].status is TestStatus.PASSED


@pytest.mark.parametrize('gap', ['not_run','timeout','error'])
def test_any_gap_precludes_a_complete_pass(gap):
    b = run({'a':'passed','b':'passed'}, evidence_complete=True)
    p = run({'a':'passed','b':gap}, evidence_complete=True)
    assert completeness_of(('a','b'),b,p)[0] == 'INCOMPLETE_CONFIRMED'


def test_timeout_even_after_all_result_lines_precludes_complete_pass():
    b = run({'a':'passed'}, evidence_complete=True)
    p = run({'a':'passed'}, evidence_complete=True, timed_out=True)
    assert completeness_of(('a',),b,p)[0] == 'INCOMPLETE_CONFIRMED'


def test_regression_dominates_incompleteness_and_is_serialized():
    class Executor:
        def run(self, tests, *, patched, timeout_s):
            return run({'a':'failed' if patched else 'passed', 'b':'not_run'},
                       evidence_complete=True)
    report = run_regression('x',Selection(tests=('a','b')),Executor(),
                            RegressionConfig(rerun_flaky=False))
    assert report.original_signal is report.signal is Signal.FAIL
    assert report.completeness == 'INCOMPLETE_CONFIRMED'
    stored = signal_from_regression(report)
    assert stored.findings['base']['results'][0]['status'] == 'passed'
    assert stored.findings['patched']['results'][0]['status'] == 'failed'
    assert stored.findings['incompleteness']


def test_incomplete_adapts_to_existing_unavailable_vocabulary():
    class Executor:
        def run(self, tests, *, patched, timeout_s):
            return run({'a':'passed'})
    report = run_regression('x',Selection(tests=('a',)),Executor())
    assert report.original_signal is Signal.PASS
    assert report.signal is Signal.INCOMPLETE
    stored = signal_from_regression(report)
    assert stored.outcome is SignalOutcome.NOT_AVAILABLE
    assert stored.absence.value == 'incomplete'


def test_parameter_cases_are_accounted_without_collapsing_legacy_results():
    raw, mapping, unmatched = account_raw_output(TestRunner('pytest','fixture'),
        't.py::f[one] PASSED\nt.py::f[two] FAILED\nextra.py::x PASSED\n',('t.py::f',))
    assert mapping['t.py::f[one]'] == ('t.py::f',)
    assert mapping['t.py::f[two]'] == ('t.py::f',)
    assert unmatched == ('extra.py::x',)
    assert raw[1].status is TestStatus.FAILED


def test_django_multiline_label_and_collision_are_not_silently_dropped():
    tid = 'tests/a/tests.py::Case::test_it'
    raw, mapping, missing = account_raw_output(TestRunner('django','fixture'),
        'test_it (a.tests.Case)\nSome docstring ... ok\n', (tid,))
    assert raw[0].status is TestStatus.PASSED
    assert mapping['a.tests.Case.test_it'] == (tid,)
    assert not missing


def test_changed_parameter_ids_block_completeness():
    b = run({'t':'passed'},evidence_complete=True,
            raw_results=(TestResult('t[x]',TestStatus.PASSED),),raw_id_map={'t[x]':('t',)})
    p = run({'t':'passed'},evidence_complete=True,
            raw_results=(TestResult('t[y]',TestStatus.PASSED),),raw_id_map={'t[y]':('t',)})
    assert 'differ' in completeness_of(('t',),b,p)[1][-1]


def test_fully_accounted_healthy_parameter_family_is_not_a_missing_outcome():
    evidence = run({'t':'not_run'}, evidence_complete=True,
        raw_results=(TestResult('t[x]',TestStatus.PASSED),), raw_id_map={'t[x]':('t',)})
    assert completeness_of(('t',),evidence,evidence)==('COMPLETE',())


def test_unscored_parameter_failure_cannot_become_a_complete_pass():
    b = run({'t':'not_run'}, evidence_complete=True,
        raw_results=(TestResult('t[x]',TestStatus.PASSED),), raw_id_map={'t[x]':('t',)})
    p = run({'t':'not_run'}, evidence_complete=True,
        raw_results=(TestResult('t[x]',TestStatus.FAILED),), raw_id_map={'t[x]':('t',)})
    assert completeness_of(('t',),b,p)[0]=='INCOMPLETE_CONFIRMED'


def test_raw_selected_disagreement_blocks_silent_last_write_pass():
    b = run({'t':'passed'},evidence_complete=True,
            raw_results=(TestResult('t',TestStatus.FAILED),),raw_id_map={'t':('t',)})
    assert any('conflict' in r for r in completeness_of(('t',),b,b)[1])


def test_capture_retains_undecodable_bytes_and_cache_roundtrips(tmp_path, monkeypatch):
    from reliability.verifier.collection import ValidationPass
    from reliability.verifier.id_validation import IDValidation
    monkeypatch.setattr('reliability.verifier.container.validate_in_container',
        lambda container, tests, runner, **kwargs: ValidationPass(tuple(
            IDValidation(t, 'runnable_test', (t,)) for t in tests)))
    raw = b't.py::a PASSED\n\xff'
    events = b'{"event":"start","batch":1}\n{"event":"end","batch":1,"returncode":0}\n{"event":"complete"}\n'
    class Container:
        def set_patched(self,p):pass
        def exec_input(self,*args,**kwargs):return 0,''
        def exec_raw(self,command,timeout_s):
            if command.startswith('python /tmp/verifier_driver'):return 0,raw,b'',False
            if command.startswith('cat /tmp/verifier_out'):return 0,raw,b'',False
            if command.startswith('cat /tmp/verifier_events'):return 0,events,b'',False
            return 0,b'',b'',False
    result = ContainerTestExecutor(Container(),evidence_dir=tmp_path).run(
        ('t.py::a',),patched=False,timeout_s=1)
    assert result.evidence_complete
    assert base64.b64decode(result.raw_stdout_b64) == raw
    assert Path(result.evidence_files['stdout.raw']).read_bytes() == raw
    restored = run_from_dict(json.loads(json.dumps(run_to_dict(result))))
    assert restored == result
    events = b'not-json\n'
    broken = ContainerTestExecutor(Container(), evidence_dir=tmp_path).run(
        ('t.py::a',), patched=False, timeout_s=1)
    assert not broken.evidence_complete
    assert 'malformed capture events' in broken.infrastructure_errors
    assert Path(broken.evidence_files['events.jsonl']).read_bytes() == events


def test_driver_streams_raw_bytes_before_runner_finishes(tmp_path):
    """Exercise the actual driver with a synthetic runner, never benchmark code."""
    fakebin=tmp_path/'bin';fakebin.mkdir()
    fake=fakebin/'python'
    release=tmp_path/'release_runner'
    fake.write_text('#!'+sys.executable+'\nimport sys,time\n'
                    'from pathlib import Path\n'
                    "sys.stdout.write('t.py::a PASSED\\n');sys.stdout.flush()\n"
                    'while not Path('+repr(str(release))+').exists():time.sleep(0.01)\n')
    fake.chmod(0o700)
    prefix=str(tmp_path/'verifier')
    driver=_BATCH_DRIVER.replace('/tmp/verifier',prefix)
    (tmp_path/'verifier_ids').write_text('t.py::a\n')
    env={**os.environ,'PATH':str(fakebin)+os.pathsep+os.environ.get('PATH','')}
    proc=subprocess.Popen([sys.executable,'-B','-c',driver,'pytest'],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    try:
        log=tmp_path/'verifier_out.txt'
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and (not log.exists() or not log.read_bytes()):
            time.sleep(0.01)
        assert log.read_bytes()==b't.py::a PASSED\n'
        assert proc.poll() is None
        release.touch()
        stdout,stderr=proc.communicate(timeout=3)
        assert proc.returncode==0,stderr
        assert stdout==log.read_bytes()
        events=[json.loads(s) for s in (tmp_path/'verifier_events.jsonl').read_text().splitlines()]
        assert events[-1]['event']=='complete'
        assert events[-1]['budget_s']==1800
        assert events[-1]['timed_out'] is False
        assert events[1]['returncode']==0
        assert events[1]['offset']==len(stdout)
    finally:
        release.touch(exist_ok=True)
        if proc.poll() is None:
            proc.kill();proc.wait()
