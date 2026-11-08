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
        cleaned=clean_reference(reference[tree],collection)
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
    assert clean_reference(reference,collection)['admitted_ids']==[identity]


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
    monkeypatch.setattr(launch,'load_reference',lambda *args:{'task':{'base':['lost'],'patched':['lost']}})
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
    if confirmation_status is TestStatus.COLLECTION_ERROR:
        from reliability.verifier.run_health import RunHealthError
        with pytest.raises(RunHealthError):launch.run_task(spec,out,'fixture',{'base':spec.tests,'patched':spec.tests},health)
        assert len(count)==3 and not (out/'result.json').exists()
    else:
        launch.run_task(spec,out,'fixture',{'base':spec.tests,'patched':spec.tests},health)
        report=json.loads((out/'result.json').read_text())['policies']['C_invalid_excluded']
        assert report['outcomes'][spec.tests[0]]==Outcome.FLAKY.value
        assert len(count)==8
        rows=[json.loads(line) for line in health.read_text().splitlines()]
        assert all(not r['halt'] for r in rows)
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


def test_frozen_nonempty_reference_still_enforces_full_admission_loss():
    identity='tests/test_real.py::test_a'
    run=RunResult(results=(TestResult(identity,TestStatus.NOT_REACHED),),requested_tests=(identity,))
    record=health_for_run('task','base',run,{'admitted_ids':[identity],'g1_collected_ids':[identity]})
    assert record['G2']['halt'] and not record['G1_collected_guard']['halt']


def committed_plan_fixture(tmp_path,monkeypatch):
    import subprocess,hashlib
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    g1=tmp_path/'g1';g1.mkdir()
    manifest=g1/'manifest.json';manifest.write_text(json.dumps({'source_sha256':{},'receipt_sha256':{}}))
    (g1/'summary.json').write_text(json.dumps(dict(launch_allowed=True,task_tree_count=166,exhaustive=True,gate_evaluated_after_all_pairs=True)))
    plan=tmp_path/'reports/next_phases/phase4_plan.md';plan.parent.mkdir(parents=True)
    digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
    plan.write_text('Fix 15 G1 manifest SHA-256: '+digest+'\n')
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True)
    subprocess.run(['git','-c','user.name=Unit Test','-c','user.email=unit@example.invalid','commit','-qm','seal'],cwd=tmp_path,check=True)
    return g1,plan,digest


def test_manifest_hash_is_read_from_committed_plan_and_verified(tmp_path,monkeypatch):
    g1,plan,digest=committed_plan_fixture(tmp_path,monkeypatch)
    assert launch.require_g1(g1)==digest
    (g1/'manifest.json').write_text('{}')
    plan.write_text('Fix 15 G1 manifest SHA-256: '+launch.sha(g1/'manifest.json')+'\n')
    with pytest.raises(ValueError,match='SHA-256 mismatch'):launch.require_g1(g1)


def test_manifest_mismatch_blocks_launcher_before_any_input_or_container_work(tmp_path,monkeypatch):
    g1,_,_=committed_plan_fixture(tmp_path,monkeypatch)
    (g1/'manifest.json').write_text('{}')
    monkeypatch.setattr(launch,'require_frozen_head',lambda *a:'freeze')
    monkeypatch.setattr(launch,'validate_inputs',lambda *a:pytest.fail('input work after manifest mismatch'))
    monkeypatch.setattr(launch,'execute',lambda *a,**k:pytest.fail('launch after manifest mismatch'))
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        launch.main(['--execute','--freeze-tag','unit-freeze','--health-preflight',str(g1),'--output',str(tmp_path/'out')])
