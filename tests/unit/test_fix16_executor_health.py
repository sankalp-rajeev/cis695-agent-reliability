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


def sealed_fixture(tmp_path,monkeypatch,collections=None,exclusions=None):
    """A real Git commit binds a manifest and the receipt bytes used by the loader."""
    import gzip,hashlib,json,subprocess
    from pathlib import Path
    from reliability.verifier.g1_reference import PUBLISHED_HYGIENE_PATH,published_spurious_ids
    from tests.unit.test_phase4_launcher import launch
    root=Path(__file__).resolve().parents[2]
    published=root/PUBLISHED_HYGIENE_PATH
    local=tmp_path/PUBLISHED_HYGIENE_PATH;local.parent.mkdir(parents=True);local.write_bytes(published.read_bytes())
    sources=[PUBLISHED_HYGIENE_PATH,launch.DRIFT_REFERENCE_RELATIVE+'/manifest.json',launch.DRIFT_REFERENCE_RELATIVE+'/drift_ids.json.gz']
    for name in sources[1:]:
        destination=tmp_path/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((root/name).read_bytes())
    g1=tmp_path/'g1';g1.mkdir()
    summary=dict(launch_allowed=True,task_tree_count=166,exhaustive=True,gate_evaluated_after_all_pairs=True,projected_halts=[])
    (g1/'summary.json').write_text(json.dumps(summary))
    expected=[dict(instance_id='pylint-dev__pylint-4970',tree=tree,selected_id=t)
        for tree in ('base','patched') for t in sorted(published_spurious_ids())]
    (g1/'reference_hygiene.json').write_text(json.dumps({'exclusions':expected if exclusions is None else exclusions}))
    for name,data in (collections or {}).items():
        path=g1/name;path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(data).encode();path.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
    manifest={'source_sha256':{name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in sources},
        'receipt_sha256':{str(p.relative_to(g1)):hashlib.sha256(p.read_bytes()).hexdigest() for p in g1.rglob('*') if p.is_file()}}
    (g1/'manifest.json').write_text(json.dumps(manifest))
    digest=hashlib.sha256((g1/'manifest.json').read_bytes()).hexdigest()
    plan=tmp_path/'reports/next_phases/phase4_plan.md';plan.parent.mkdir(parents=True,exist_ok=True)
    plan.write_text('Fix 16 G1 manifest SHA-256: '+digest+'\n')
    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True)
    subprocess.run(['git','-c','user.name=Unit Test','-c','user.email=unit@example.invalid','commit','-qm','seal'],cwd=tmp_path,check=True)
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    return g1,plan,digest


def test_unpinned_plain_collection_cannot_shadow_verified_gzip(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from tests.unit.test_phase4_launcher import launch
    from reliability.verifier.g1_reference import read_collection
    root=Path(__file__).resolve().parents[2];task='pylint-dev__pylint-4970'
    original=launch.load_reference()[task]
    collections={f'tasks/{task}/{tree}/collection.json.gz':read_collection(
        root/'reports/next_phases/phase4_rerun/fix15_g1/tasks'/task/tree/'collection.json') for tree in ('base','patched')}
    ids=tuple(r['selected_id'] for r in collections[f'tasks/{task}/base/collection.json.gz']['records'])
    g1,_,_=sealed_fixture(tmp_path,monkeypatch,collections)
    for tree in ('base','patched'):
        (g1/'tasks'/task/tree/'collection.json').write_text('UNPINNED MALFORMED SHADOW')
    refs=launch.with_g1_references({task:original},[SimpleNamespace(instance_id=task,tests=ids)],g1)
    assert all(len(refs[task][tree]['excluded_spurious_ids'])==16 for tree in ('base','patched'))
    assert read_collection(g1/'tasks'/task/'base/collection.json')['records']
    (g1/'tasks'/task/'base/collection.json.gz').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        read_collection(g1/'tasks'/task/'base/collection.json')


def test_wrong_published_removal_set_blocks_real_launcher_before_inputs(tmp_path,monkeypatch):
    from tests.unit.test_phase4_launcher import launch
    g1,_,_=sealed_fixture(tmp_path,monkeypatch,exclusions=[])
    monkeypatch.setattr(launch,'require_frozen_head',lambda *a:'unit-freeze')
    monkeypatch.setattr(launch,'validate_inputs',lambda *a:pytest.fail('input work after hygiene mismatch'))
    monkeypatch.setattr(launch,'execute',lambda *a,**k:pytest.fail('launch after hygiene mismatch'))
    with pytest.raises(ValueError,match='Reference hygiene removal mismatch'):
        launch.main(['--execute','--freeze-tag','unit-freeze','--health-preflight',str(g1),'--output',str(tmp_path/'out')])


def test_native_proof_removing_fifteen_instead_of_sixteen_blocks_reference_loader(tmp_path,monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    from tests.unit.test_phase4_launcher import launch
    from reliability.verifier.g1_reference import read_collection
    root=Path(__file__).resolve().parents[2];task='pylint-dev__pylint-4970'
    original=launch.load_reference()[task]
    collection=read_collection(root/'reports/next_phases/phase4_rerun/fix15_g1/tasks'/task/'base/collection.json')
    ids=tuple(r['selected_id'] for r in collection['records'])
    first=next(r for r in collection['records'] if r.get('reason')=='not_a_test_module')
    first['native_proven_absent']=False
    g1,_,_=sealed_fixture(tmp_path,monkeypatch,{f'tasks/{task}/base/collection.json.gz':collection})
    with pytest.raises(ValueError,match='Reference hygiene removal mismatch'):
        launch.with_g1_references({task:original},[SimpleNamespace(instance_id=task,tests=ids)],g1)


def test_unmapped_case_progress_remains_identity_loss_even_with_CRASH_outcome():
    ids=identities(20)
    raw=b'test_unknown.py::test_foreign FAILED\n'
    run=run_from_capture(TestRunner('pytest','fixture'),ids,runner_log=raw,
        events=({'event':'start','batch':1,'ids':ids,'offset':0},
                {'event':'end','batch':1,'returncode':1,'missing_ids':ids,'per_test_output':True,'offset':len(raw)},
                {'event':'complete'}))
    assert run.results[0].status is TestStatus.CRASH
    record=health_for_run('task','base',run,{'admitted_ids':ids,'g1_collected_ids':ids})
    assert record['G2']['lost_count']==20 and record['halt']


def test_exact_drift_projection_excludes_XFAIL_XPASS_and_never_decodes_labels(tmp_path,monkeypatch):
    import json,hashlib
    from reliability.verifier.admission_reference import JSONProjection
    from reliability.verifier.drift_reference import drift_reference_ids
    source=tmp_path/'original.json'
    source.write_text(json.dumps({'signal':'FORBIDDEN_VERDICT','labels':['FORBIDDEN_LABEL'],
        'calls':[{'patched':False,'run':{'results':[{'test_id':status,'status':status}
          for status in ('passed','failed','error','xfail','xpass','skipped')]}}]}))
    original=JSONProjection.scalar
    def guarded(self):
        value=original(self)
        assert not (isinstance(value,str) and value.startswith('FORBIDDEN'))
        return value
    monkeypatch.setattr(JSONProjection,'scalar',guarded)
    assert drift_reference_ids(source,hashlib.sha256(source.read_bytes()).hexdigest())['base']==['error','failed','passed']
