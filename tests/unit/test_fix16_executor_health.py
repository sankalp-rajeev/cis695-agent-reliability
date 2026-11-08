"""Fix 16 health and scoring use actual capture, driver and launcher paths."""
import pytest

from reliability.verifier.container import run_from_capture
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.run_health import health_for_run
from reliability.verifier.selection import TestRunner


def identities(count):
    return tuple('test_real.py::test_case_%04d' % i for i in range(count))


def receipt_run(ids, status, changed=None):
    return RunResult(results=tuple(TestResult(t,status if changed is None or i<changed else TestStatus.PASSED,
        message='infrastructure: missing runner result' if status is TestStatus.NOT_RUN else '') for i,t in enumerate(ids)),
        requested_tests=ids,stage_health=(
            dict(stage='native_collection',input_count=len(ids),output_count=len(ids),status='COMPLETE'),
            dict(stage='module_execution',input_count=len(ids),output_count=0,status='ERROR'),
            dict(stage='execution',input_count=len(ids),output_count=0,status='ERROR'),
            dict(stage='admission',input_count=len(ids),output_count=0,status='ZERO_OUTPUT')))


@pytest.mark.parametrize('status',[TestStatus.ERROR,TestStatus.TIMEOUT,TestStatus.FAILED,
    TestStatus.NOT_REACHED,TestStatus.XFAIL,TestStatus.XPASS,TestStatus.SKIPPED])
def test_one_outcome_in_20_reference_ids_never_halts(status):
    ids=identities(20)
    record=health_for_run('task','patched',receipt_run(ids,status,1),
        {'admitted_ids':ids,'module_skip_blocked_ids':ids,'g1_collected_ids':ids})
    assert not record['halt'] and record['G2']['lost_count']==0
    assert record['outcome_counts'][status.value]==1
    assert not record['G3']['halt']


def test_whole_tree_ERROR_capture_is_outcome_not_identity_loss():
    ids=identities(500)
    raw=''.join(t+' ERROR\n' for t in ids).encode()
    capture=run_from_capture(TestRunner('pytest','fixture'),ids,runner_log=raw,
        events=({'event':'start','batch':1,'ids':ids,'offset':0},
                {'event':'end','batch':1,'returncode':1,'offset':len(raw)}, {'event':'complete'}))
    from dataclasses import replace
    capture=replace(capture,stage_health=receipt_run(ids,TestStatus.ERROR).stage_health)
    assert all(r.status is TestStatus.ERROR for r in capture.results)
    record=health_for_run('task','patched',capture,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert not record['halt'] and record['G2']['lost_count']==0
    assert record['outcome_counts']['error']==500 and record['admitted_ids']==0


@pytest.mark.parametrize('size,lost,halt',[(500,10,True),(500,9,False),(2000,10,False),(2000,20,True)])
@pytest.mark.parametrize('status',[TestStatus.NOT_RUN,TestStatus.COLLECTION_ERROR,TestStatus.INVALID_ID,TestStatus.RUNNER_UNAVAILABLE])
def test_identity_loss_requires_ten_AND_one_percent(size,lost,halt,status):
    ids=identities(size)
    # Collection still produces the unaffected identities; no collection zero-output.
    run=receipt_run(ids,status,lost)
    record=health_for_run('task','base',run,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert record['G2']['lost_count']==lost
    assert record['G2']['halt'] is halt and record['G1_collected_guard']['halt'] is halt
    assert record['halt'] is halt


@pytest.mark.parametrize('size,skips,halt',[(20,1,False),(500,9,False),(500,10,True),(2000,10,False)])
def test_reference_skip_is_separate_thresholded_environment_drift(size,skips,halt):
    ids=identities(size)
    record=health_for_run('task','patched',receipt_run(ids,TestStatus.SKIPPED,skips),
        {'admitted_ids':ids,'module_skip_blocked_ids':ids,'g1_collected_ids':ids})
    assert record['G2']['lost_count']==0 and not record['G1_collected_guard']['halt']
    assert record['environment_drift']['skipped_reference_ids']==list(ids[:skips])
    assert record['environment_drift']['halt'] is halt and record['halt'] is halt


def actual_execution(tmp_path,source,tests):
    import subprocess
    from tests.unit.test_fix14_health import LocalContainer
    from reliability.verifier.container import ContainerTestExecutor
    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    (tmp_path/'test_real.py').write_text(source)
    class Container(LocalContainer):
        def set_patched(self,value):self._patch_applied=value
        def generated_snapshot(self,*a,**k):return {'files':{}}
        def exec(self,command,**kwargs):
            return super().exec('ulimit -c 0\n'+command,**kwargs)
    return ContainerTestExecutor(Container(tmp_path),runner=TestRunner('pytest','fixture'),
        evidence_dir=tmp_path/'evidence').run(tests,patched=False,timeout_s=30)


@pytest.mark.parametrize('death',['os._exit(0)','os._exit(17)','os.kill(os.getpid(), signal.SIGSEGV)'])
def test_actual_process_death_after_test_start_is_CRASH_and_no_health_halt(tmp_path,death):
    ids=('test_real.py::test_a','test_real.py::test_b','test_real.py::test_c')
    run=actual_execution(tmp_path,'import os, signal\ndef test_a(): pass\ndef test_b(): '+death+'\ndef test_c(): pass\n',ids)
    assert run.by_id()[ids[0]].status is TestStatus.PASSED
    assert run.by_id()[ids[1]].status is TestStatus.CRASH
    assert run.by_id()[ids[2]].status is TestStatus.NOT_REACHED
    ends=[e for e in run.events if e['event']=='end']
    assert len(ends)==1 and ends[0]['test_started'] and not ends[0]['load_failure']
    assert run.evidence_complete and not run.infrastructure_errors
    health=health_for_run('fixture','base',run,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert health['G2']['lost_count']==0 and not health['halt']
    assert not any(s['stage']=='module_execution' for s in run.stage_health)
    from reliability.verifier.regression import run_from_dict,run_to_dict
    assert run_from_dict(run_to_dict(run))==run


@pytest.mark.parametrize('termination',['raise RuntimeError("silent module execution")','os._exit(0)'])
def test_module_execution_identity_failure_requires_actual_first_attempt_AND_retry(tmp_path,termination):
    ids=('test_real.py::test_a',)
    source='import os, sys\nif "--collect-only" not in sys.argv: '+termination+'\ndef test_a(): pass\n'
    run=actual_execution(tmp_path,source,ids)
    ends=[e for e in run.events if e['event']=='end']
    assert len(ends)==2 and ends[1]['retry'] and ends[1]['parent']==ends[0]['batch']
    assert all(not e['test_started'] and not e['per_test_output'] for e in ends)
    assert run.results[0].status is TestStatus.NOT_RUN
    stages=[s for s in run.stage_health if s['stage']=='module_execution']
    assert len(stages)==1 and stages[0]['identity_failure']
    health=health_for_run('fixture','base',run,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert health['G2']['lost_count']==1 and not health['halt']


def test_one_failed_module_attempt_is_not_identity_failure():
    ids=identities(20)
    run=run_from_capture(TestRunner('pytest','fixture'),ids,runner_log=b'import failed\n',
        events=({'event':'start','batch':1,'ids':ids,'offset':0},
                {'event':'end','batch':1,'returncode':2,'offset':14,'missing_ids':ids,'load_failure':True},
                {'event':'complete'}))
    assert all(r.status is TestStatus.NOT_REACHED for r in run.results)
    record=health_for_run('task','base',run,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert not record['halt'] and record['G2']['lost_count']==0


@pytest.mark.parametrize('patched_status',[TestStatus.ERROR,TestStatus.CRASH])
def test_real_crash_capture_and_ERROR_confirmations_restore_REGRESSION_ERROR(tmp_path,patched_status):
    from reliability.verifier.regression import run_regression,Outcome,Signal
    from reliability.verifier.selection import Selection
    ids=('test_real.py::test_b',)
    crashed=actual_execution(tmp_path,'import os\ndef test_b(): os._exit(17)\n',ids)
    assert crashed.results[0].status is TestStatus.CRASH
    error=run_from_capture(TestRunner('pytest','fixture'),ids,runner_log=(ids[0]+' ERROR\n').encode())
    patched=crashed if patched_status is TestStatus.CRASH else error
    from dataclasses import replace
    # A terminal ERROR fixture uses the same complete-capture status as the real driver.
    patched=replace(patched,evidence_complete=True)
    base=run_from_capture(TestRunner('pytest','fixture'),ids,runner_log=(ids[0]+' PASSED\n').encode())
    base=replace(base,evidence_complete=True)
    class Executor:
        calls=[]
        def run(self,tests,*,patched:bool,timeout_s):
            self.calls.append((tests,patched))
            return patch if patched else base
    patch=patched;executor=Executor()
    report=run_regression('fixture',Selection(tests=ids),executor)
    assert report.outcomes[ids[0]] is Outcome.REGRESSION_ERROR and report.signal is Signal.REGRESSION_ERROR
    assert report.confirmation_summary[0]['stable'] and report.confirmation_summary[0]['base_PASS']==3
    assert report.confirmation_summary[0]['patched_non_PASS']==3 and len(executor.calls)==8
    assert all(not health_for_run('fixture','patched',run,ids)['halt'] for run in report.confirmations)


@pytest.mark.parametrize('patch_statuses',[
    (TestStatus.ERROR,TestStatus.PASSED,TestStatus.ERROR),
    (TestStatus.CRASH,TestStatus.ERROR,TestStatus.PASSED),
    (TestStatus.ERROR,TestStatus.TIMEOUT,TestStatus.ERROR)])
def test_mixed_or_timed_out_confirmations_are_FLAKY(patch_statuses):
    from tests.unit.test_fix8_confirmation import Executor
    from reliability.verifier.regression import run_regression,Outcome
    from reliability.verifier.selection import Selection
    executor=Executor(initial=TestStatus.ERROR,patches=list(patch_statuses))
    report=run_regression('fixture',Selection(tests=('t.py::test_a','t.py::test_b')),executor)
    assert report.outcomes['t.py::test_a'] is Outcome.FLAKY
    assert len(report.confirmations)==6
