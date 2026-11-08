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
