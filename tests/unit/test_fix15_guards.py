"""Fix 15: real receipt paths, native collection, and launcher/scoring guards."""
import json
from pathlib import Path

import pytest

from reliability.verifier.g1_reference import clean_reference, read_collection
from reliability.verifier.run_health import health_for_run
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from tests.unit.test_phase4_launcher import launch, task_spec

ROOT = Path(__file__).resolve().parents[2]


def test_pylint_spurious_references_require_real_native_directory_proof():
    reference = launch.load_reference()['pylint-dev__pylint-4970']
    exclusions=[]
    for tree in ('base','patched'):
        collection=read_collection(ROOT/'reports/next_phases/phase4_rerun/fix14_g1/tasks/pylint-dev__pylint-4970'/tree/'collection.json')
        cleaned=clean_reference(reference[tree],collection,task='pylint-dev__pylint-4970',tree=tree)
        assert len(cleaned['excluded_spurious_ids'])==16
        assert all('consider_using_with.py::' in t for t in cleaned['excluded_spurious_ids'])
        assert set(reference[tree]['admitted_ids'])-set(cleaned['admitted_ids'])==set(cleaned['excluded_spurious_ids'])
        exclusions.append(cleaned['excluded_spurious_ids'])
    assert exclusions[0]==exclusions[1]


def test_other_invalid_reference_is_never_removed():
    identity='tests/test_real.py::helper'
    reference={'admitted_ids':[identity]}
    collection={'records':[{'selected_id':identity,'stage':'native','reason':'helper',
        'validation_status':'INVALID_ID','native_proven_absent':True}]}
    assert clean_reference(reference,collection,task='task',tree='base')['admitted_ids']==[identity]


def test_pylint_cleaned_reference_G2_projection_passes():
    from reliability.verifier.g1_reference import project_collection
    original=launch.load_reference()['pylint-dev__pylint-4970']
    for tree in ('base','patched'):
        collection=read_collection(ROOT/'reports/next_phases/phase4_rerun/fix14_g1/tasks/pylint-dev__pylint-4970'/tree/'collection.json')
        result=project_collection('pylint-dev__pylint-4970',tree,collection,original[tree])
        assert not result['halt'] and result['G2']['lost_count']==0
        assert len(result['excluded_spurious_ids'])==16


def test_G1_synthetic_projected_halt_blocks_gate(tmp_path,monkeypatch):
    from dataclasses import replace
    from types import SimpleNamespace
    from tests.unit.test_fix14_health import G1_module,ContainerShell
    from reliability.verifier.collection import ValidationPass
    from reliability.verifier.id_validation import IDValidation
    module=G1_module(monkeypatch)
    spec=replace(task_spec(tmp_path),source=SimpleNamespace(pre_install=SimpleNamespace(repo='example/repo',version='1')))
    monkeypatch.setattr(launch,'validate_inputs',lambda *args:[spec])
    monkeypatch.setattr(launch,'load_reference',lambda *args:{'task':{tree:['lost%d' % i for i in range(10)] for tree in ('base','patched')}})
    monkeypatch.setattr(launch,'plan_for',lambda *args:{})
    class Container(ContainerShell):
        def set_patched(self,value):pass
        def generated_snapshot(self,*args,**kwargs):return {'files':{}}
    monkeypatch.setattr(launch,'FrozenContainer',Container)
    monkeypatch.setattr(module,'runner_startup',lambda *a,**k:dict(stage='runner_startup',status='COMPLETE',input_count=1,output_count=1))
    monkeypatch.setattr(module,'validate_in_container',lambda *a,**k:ValidationPass(
        (IDValidation(spec.tests[0],'runnable_test',spec.tests,stage='native'),),
        stage_health=({'stage':'native_collection','status':'COMPLETE','input_count':1,'output_count':1},)))
    out=tmp_path/'g1'
    assert module.main(out)==1
    summary=json.loads((out/'summary.json').read_text())
    assert len(summary['projected_halts'])==2 and not summary['launch_allowed']


@pytest.mark.parametrize('confirmation_status',[TestStatus.ERROR,TestStatus.TIMEOUT,TestStatus.COLLECTION_ERROR])
def test_confirmation_identity_loss_vs_unstable_through_real_launcher(tmp_path,monkeypatch,confirmation_status):
    from tests.unit.test_fix14_health import ContainerShell
    from reliability.verifier.regression import Outcome
    spec=task_spec(tmp_path);count=[]
    class Executor:
        def __init__(self,*a,**k):pass
        def run(self,tests,*,patched,timeout_s):
            count.append(patched)
            status=(TestStatus.FAILED if patched else TestStatus.PASSED) if len(count)<=2 else (confirmation_status if patched or confirmation_status is TestStatus.COLLECTION_ERROR else TestStatus.PASSED)
            return RunResult(results=(TestResult(tests[0],status),),requested_tests=tests,evidence_complete=True,
                stage_health=({'stage':'execution','input_count':1,'output_count':int(status in (TestStatus.PASSED,TestStatus.FAILED))},
                              {'stage':'admission','input_count':1,'output_count':int(status in (TestStatus.PASSED,TestStatus.FAILED))}))
    monkeypatch.setattr(launch,'FrozenContainer',ContainerShell)
    monkeypatch.setattr(launch,'ContainerTestExecutor',Executor)
    out=tmp_path/'task';health=tmp_path/'health.jsonl'
    launch.run_task(spec,out,'fixture',{'base':spec.tests,'patched':spec.tests},health)
    report=json.loads((out/'result.json').read_text())['policies']['C_invalid_excluded']
    expected={TestStatus.ERROR:Outcome.REGRESSION_ERROR,TestStatus.TIMEOUT:Outcome.FLAKY,
              TestStatus.COLLECTION_ERROR:Outcome.COLLECTION_ERROR}[confirmation_status]
    assert report['outcomes'][spec.tests[0]]==expected.value
    assert len(count)==8
    rows=[json.loads(line) for line in health.read_text().splitlines()]
    assert all(not r['halt'] for r in rows)
    if confirmation_status is TestStatus.TIMEOUT:
        assert any(r.get('unstable_confirmation_ids') for r in rows)


@pytest.mark.parametrize('status,halt',[(TestStatus.NOT_RUN,True),(TestStatus.COLLECTION_ERROR,True),
    (TestStatus.INVALID_ID,True),(TestStatus.RUNNER_UNAVAILABLE,True),(TestStatus.NOT_REACHED,False),
    (TestStatus.TIMEOUT,False),(TestStatus.ERROR,False)])
def test_G1_collected_guard_identity_loss_vs_budget_on_real_G1_paths(status,halt):
    from reliability.verifier.g1_reference import native_collected_ids
    collection=read_collection(ROOT/'reports/next_phases/phase4_rerun/fix14_g1/tasks/astropy__astropy-7606/base/collection.json')
    ids=native_collected_ids(collection)
    assert len(ids)>10
    reference={'admitted_ids':[],'g1_collected_ids':ids}
    results=tuple(TestResult(t,status if i<10 else TestStatus.PASSED) for i,t in enumerate(ids))
    run=RunResult(results=results,requested_tests=tuple(ids))
    record=health_for_run('task','base',run,reference)
    assert record['G1_collected_guard']['halt']==halt
    assert record['G2']['halt']==halt
    assert record['G2']['mode']=='IDENTITY_ONLY'
    assert record['G1_collected_guard']['lost_count']==(10 if halt else 0)


def test_budget_only_zero_admission_is_reported_without_halt():
    ids=('tests/test_real.py::test_a','tests/test_real.py::test_b')
    run=RunResult(results=tuple(TestResult(t,TestStatus.NOT_REACHED) for t in ids),requested_tests=ids,
        stage_health=({'stage':'execution','input_count':2,'output_count':0},
                      {'stage':'admission','input_count':2,'output_count':0}))
    reference={'admitted_ids':[],'g1_collected_ids':ids}
    record=health_for_run('task','base',run,reference)
    assert not record['halt'] and record['admitted_share']==0
    assert record['G1_collected_guard']['budget_ids']==list(ids)
    assert all(s['non_identity_gap_count']==2 for s in record['stages'])


def test_frozen_nonempty_reference_also_uses_identity_only_loss():
    identity='tests/test_real.py::test_a'
    run=RunResult(results=(TestResult(identity,TestStatus.NOT_REACHED),),requested_tests=(identity,))
    record=health_for_run('task','base',run,{'admitted_ids':[identity],'g1_collected_ids':[identity]})
    assert not record['G2']['halt'] and not record['G1_collected_guard']['halt']


def committed_plan_fixture(tmp_path,monkeypatch):
    from tests.unit.test_fix16_executor_health import sealed_fixture
    return sealed_fixture(tmp_path,monkeypatch)


def test_manifest_hash_is_read_from_committed_plan_and_verified(tmp_path,monkeypatch):
    g1,plan,digest=committed_plan_fixture(tmp_path,monkeypatch)
    assert launch.require_g1(g1)==digest
    (g1/'manifest.json').write_text('{}')
    plan.write_text('Fix 16 G1 manifest SHA-256: '+launch.sha(g1/'manifest.json')+'\n')
    with pytest.raises(ValueError,match='SHA-256 mismatch'):launch.require_g1(g1)


def test_manifest_mismatch_blocks_launcher_before_any_input_or_container_work(tmp_path,monkeypatch):
    g1,_,_=committed_plan_fixture(tmp_path,monkeypatch)
    (g1/'manifest.json').write_text('{}')
    monkeypatch.setattr(launch,'require_frozen_head',lambda *a:'freeze')
    monkeypatch.setattr(launch,'validate_inputs',lambda *a:pytest.fail('input work after manifest mismatch'))
    monkeypatch.setattr(launch,'execute',lambda *a,**k:pytest.fail('launch after manifest mismatch'))
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        launch.main(['--execute','--freeze-tag','unit-freeze','--health-preflight',str(g1),'--output',str(tmp_path/'out')])


def test_pytest3_timeout_attribution_uses_normalized_identity_and_keeps_unicode():
    from reliability.verifier.container import run_from_capture
    from reliability.verifier.selection import TestRunner
    active='tests/test_real.py::TestReal::test_body[é::()::雪]'
    other='tests/test_real.py::TestReal::test_other'
    raw=b'tests/test_real.py::TestReal::()::test_body['+'é::()::雪'.encode()+b']\n'
    events=({'event':'start','batch':0,'ids':[active,other],'offset':0},
        {'event':'end','batch':0,'timed_out':True,'missing_ids':[active,other],'offset':len(raw)},
        {'event':'not_reached','module':'tests/test_real.py','ids':[active,other],'elapsed_s':10})
    run=run_from_capture(TestRunner('pytest','fixture'),(active,other),runner_log=raw,events=events,timed_out=True,budget_s=10)
    assert run.by_id()[active].status is TestStatus.TIMEOUT
    assert run.by_id()[other].status is TestStatus.NOT_REACHED


@pytest.mark.parametrize('exception',[KeyboardInterrupt,SystemExit])
@pytest.mark.parametrize('record_failure',[False,True])
def test_guarded_pair_records_and_reraises_interruptions(tmp_path,monkeypatch,exception,record_failure):
    from tests.unit.test_fix14_health import G1_module
    module=G1_module(monkeypatch);spec=task_spec(tmp_path)
    def interrupt(*args,**kwargs):raise exception('stop')
    monkeypatch.setattr(launch,'FrozenContainer',interrupt)
    original_write=launch.write
    def write(path,value):
        if record_failure and path.name=='health.json':raise PermissionError('pair receipt denied')
        return original_write(path,value)
    monkeypatch.setattr(launch,'write',write)
    out=tmp_path/'g1'
    with pytest.raises(exception) as caught:module.guarded_pair(spec,False,out)
    path=out/'interruption.json' if record_failure else out/'tasks/task/base/health.json'
    record=json.loads(path.read_text())
    assert record['interruption']==exception.__name__ and record['status']=='INTERRUPTED'
    assert not record['gate_evaluated'] and caught.value.g1_record==record


def test_exception_matching_requires_tree_and_registered_stage():
    from reliability.verifier.run_health import allowed_failure
    row=dict(instance_id='task',module='tests/test_real.py',stages=['module_execution'],trees=['base'],
        required_message='known dependency',cause='KNOWN')
    assert allowed_failure([row],'task',row['module'],'module_execution','known dependency',tree='base')=='KNOWN'
    assert allowed_failure([row],'task',row['module'],'module_execution','known dependency',tree='patched') is None
    assert allowed_failure([row],'task',row['module'],'native_collection','known dependency',tree='base') is None
    assert allowed_failure([row],'task',row['module'],'module_execution','known dependency') is None


@pytest.mark.parametrize('tree,stage,allowed',[('base','module_execution',True),('patched','module_execution',False),('base','native_collection',False)])
def test_module_execution_exception_on_real_collection_and_capture_paths(tmp_path,monkeypatch,tree,stage,allowed):
    from tests.unit.test_fix14_health import LocalContainer
    from reliability.verifier.container import ContainerTestExecutor
    from reliability.verifier.selection import TestRunner
    import reliability.verifier.run_health as health
    import subprocess
    root=tmp_path/'repo';root.mkdir();subprocess.run(['git','init','-q'],cwd=root,check=True)
    marker=root/'body_ran'
    (root/'test_real.py').write_text('import sys\nif "--collect-only" not in sys.argv:\n    raise RuntimeError("known module execution guard")\ndef test_body():\n    open("body_ran","w").write("bad")\n')
    class Container(LocalContainer):
        def set_patched(self,value):self._patch_applied=value
        def generated_snapshot(self,*a,**k):return {'files':{}}
    row=dict(instance_id='fixture',module='test_real.py',stages=[stage],trees=['base'],
        required_message='known module execution guard',cause='KNOWN')
    monkeypatch.setattr(health,'exception_rules',lambda:[row])
    run=ContainerTestExecutor(Container(root),runner=TestRunner('pytest','fixture'),evidence_dir=tmp_path/'evidence').run(
        ('test_real.py::test_body',),patched=tree=='patched',timeout_s=30)
    stages=[s for s in run.stage_health if s['stage']=='module_execution']
    assert stages and bool(stages[-1]['allowed_exception'])==allowed
    assert not marker.exists() and run.results[0].status is TestStatus.NOT_RUN
    assert not health.zero_output(run.stage_health)['halt']
    record=health_for_run('fixture',tree,run,{'admitted_ids':[],'g1_collected_ids':['test_real.py::test_body']})
    assert not record['G1_collected_guard']['halt']
    assert record['G1_collected_guard']['lost_count']==1


@pytest.mark.parametrize('tree,allowed',[('base',True),('patched',False)])
def test_native_collection_exception_tree_scope_on_real_driver(tmp_path,monkeypatch,tree,allowed):
    from tests.unit.test_fix14_health import repository
    import reliability.verifier.collection as collection_module
    from reliability.verifier.selection import TestRunner
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text('raise RuntimeError("known native guard")\ndef test_body(): raise AssertionError("body ran")\n')
    row=dict(instance_id='fixture',module='test_real.py',stages=['native_collection'],trees=['base'],required_message='known native guard',cause='KNOWN')
    monkeypatch.setattr(collection_module,'exception_rules',lambda:[row])
    receipt=collection_module.validate_in_container(container,('test_real.py::test_body',),TestRunner('pytest','fixture'),tree=tree)
    assert bool(receipt.stage_health[0]['allowed_exception'])==allowed
    assert receipt.records[0].collector_fallback==(not allowed)
