"""Fix 14 health regressions through collection, mapping and launcher paths."""
import json
import os
import sys
import subprocess
from pathlib import Path

from reliability.env import clean_env
from reliability.verifier.collection import validate_in_container
from reliability.verifier.id_validation import IDValidation, merge_native
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.run_health import health_for_run
from reliability.verifier.selection import TestRunner


class LocalContainer:
    """Run real collection drivers and uploads in a confined temporary tree."""
    instance_id='fixture'
    def __init__(self, root):
        self.root=root
        self.temp=root/'driver_files';self.temp.mkdir()
    def environment(self):
        env=clean_env();env["PATH"]=str(Path(sys.executable).parent)+os.pathsep+env.get("PATH", "")
        return env
    def command(self, command):
        return command.replace('/tmp/verifier_',str(self.temp/'verifier_'))
    def exec(self, command, **kwargs):
        proc=subprocess.run(self.command(command),shell=True,cwd=self.root,env=self.environment(),capture_output=True,text=True,timeout=kwargs.get('timeout_s',60))
        return proc.returncode,proc.stdout+proc.stderr
    def exec_input(self, command, data, **kwargs):
        # Python program literals and request strings refer to the same isolated paths.
        proc=subprocess.run(self.command(command),input=self.command(data),shell=True,cwd=self.root,env=self.environment(),capture_output=True,text=True,timeout=kwargs.get('timeout_s',60))
        return proc.returncode,proc.stdout+proc.stderr


def repository(tmp_path):
    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    return LocalContainer(tmp_path)


def test_static_not_found_native_hook_collects_it(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text('def generated(): raise AssertionError("body ran")\nglobals()["test_dynamic"] = generated\n')
    identity='test_real.py::test_dynamic'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    record=validation.records[0]
    assert record.static_reason=='not_found' and record.valid and record.native_disagrees
    assert record.runnable_ids==(identity,)


def test_all_static_invalid_ids_still_reach_native_and_G2_halts(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text('def helper(): pass\ndef test_real(): raise AssertionError("body ran")\n')
    identity='test_real.py::helper'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.groups and validation.records[0].to_dict()['validation_status']=='INVALID_ID'
    run=RunResult(results=(TestResult(identity,TestStatus.INVALID_ID),),requested_tests=(identity,),validation=(validation.records[0].to_dict(),))
    assert health_for_run('task','base',run,[identity])['G2']['halt']


def test_reference_pass_now_ordinary_skipped_is_lost():
    identity='test_real.py::test_body'
    run=RunResult(results=(TestResult(identity,TestStatus.SKIPPED),),requested_tests=(identity,))
    reference={'admitted_ids':[identity],'module_skip_blocked_ids':[identity]}
    assert health_for_run('task','base',run,reference)['G2']['lost_ids']==[identity]


def test_static_rejection_needs_successful_native_absence():
    identity='test_real.py::helper'
    static=(IDValidation(identity,'helper',reason='helper'),)
    assert merge_native(static,{})[0].unavailable
    assert merge_native(static,{identity:{'ids':[],'completed':True,'returncode':0}})[0].reason=='helper'


def test_empty_original_uses_G1_native_set_and_halts_on_loss(tmp_path):
    from tests.unit.test_phase4_launcher import launch, task_spec
    spec=task_spec(tmp_path)
    g1=tmp_path/'g1'
    for tree in ('base','patched'):
        launch.write(g1/'tasks'/spec.instance_id/tree/'collection.json',{'records':[
            IDValidation(spec.tests[0],'runnable_test',spec.tests,stage='native').to_dict()]})
    refs=launch.with_g1_references({'task':{'base':[],'patched':[]}},[spec],g1)
    run=RunResult(results=(TestResult(spec.tests[0],TestStatus.NOT_RUN),),requested_tests=spec.tests)
    health=health_for_run('task','base',run,refs['task']['base'])
    assert health['G2']['reference_source']=='G1_NATIVE_COLLECTION'
    assert health['G2']['halt'] and health['G2']['lost_ids']==list(spec.tests)
    assert health_for_run('task','base',run,[])['G2']['missing_G1_reference']
    # A broken executor cannot bypass the sealed G1 set by dropping requested_tests.
    assert health_for_run('task','base',RunResult(),refs['task']['base'])['G2']['halt']


import pytest
from tests.unit.test_phase4_launcher import launch, task_spec


class ContainerShell:
    def __init__(self,*args,**kwargs):self.source_integrity={'status':'VERIFIED'}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def generated_snapshot(self):return {'files':{}}


@pytest.mark.parametrize('failure',['crash','zero_output','loss'])
def test_confirmation_guards_halt_inside_call_before_result_scoring(tmp_path,monkeypatch,failure):
    spec=task_spec(tmp_path);calls=[]
    class Executor:
        def __init__(self,*args,**kwargs):pass
        def run(self,tests,*,patched,timeout_s):
            calls.append(patched)
            if len(calls)>2:
                if failure=='crash':raise RuntimeError('confirmation crashed')
                return RunResult(results=(TestResult(tests[0],TestStatus.NOT_RUN),),requested_tests=tests,
                    stage_health=({'stage':'native_collection','input_count':1,'output_count':0},) if failure=='zero_output' else ())
            return RunResult(results=(TestResult(tests[0],TestStatus.FAILED if patched else TestStatus.PASSED),),requested_tests=tests,evidence_complete=True)
    monkeypatch.setattr(launch,'FrozenContainer',ContainerShell)
    monkeypatch.setattr(launch,'ContainerTestExecutor',Executor)
    scored=[]
    original=launch.run_regression
    def scoring(*args,**kwargs):
        report=original(*args,**kwargs)
        scored.append(report)
        return report
    monkeypatch.setattr(launch,'run_regression',scoring)
    health=tmp_path/'health.jsonl'
    with pytest.raises(launch.RunHealthError):
        launch.run_task(spec,tmp_path/'task','fixture',{'base':spec.tests,'patched':spec.tests},health)
    assert calls==[False,True,False] and not scored
    record=json.loads(health.read_text().splitlines()[-1])
    assert record['halt'] and record['scope']=='confirmation'
    if failure=='loss':assert record['G2']['lost_ids']==list(spec.tests)
    assert not (tmp_path/'task'/'result.json').exists()


def test_partial_fallback_is_separate_from_admitted_slots():
    from reliability.verifier.collection import ValidationPass
    from reliability.verifier.validated_run import apply_validation
    ids=('test_real.py::test_native','test_real.py::test_fallback')
    validation=ValidationPass((IDValidation(ids[0],'runnable_test',(ids[0],),stage='native'),
        IDValidation(ids[1],'runnable_test',(ids[1],),stage='collector_fallback',collector_fallback=True)))
    run=apply_validation(RunResult(results=tuple(TestResult(t,TestStatus.PASSED) for t in ids)),validation)
    assert run.validation[0]['admitted'] and not run.validation[1]['admitted']
    health=health_for_run('task','base',run,ids)
    assert health['admitted_ids']==1 and health['admitted_share']==0.5
    assert health['COLLECTOR_FALLBACK_slots']==1
    assert health['G2']['lost_ids']==[ids[1]]


def test_G3_removes_only_agreed_absence_and_reports_all_proven_invalid(tmp_path):
    from reliability.verifier.run_health import zero_output
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text('def helper(): raise AssertionError("body ran")\n')
    identity='test_real.py::helper'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.records[0].native_proven_absent
    stage=validation.stage_health[0]
    assert stage['original_input_count']==1 and stage['proven_absent_count']==1
    assert stage['status']=='ALL_PROVEN_INVALID' and stage['input_count']==0
    assert not zero_output(validation.stage_health)['halt']


def test_G3_static_invalid_without_native_receipt_still_halts(tmp_path):
    from reliability.verifier.collection import collection_stages
    from reliability.verifier.run_health import zero_output
    identity='test_real.py::helper'
    merged=merge_native((IDValidation(identity,'helper',reason='helper'),),{})
    stages=collection_stages('task',(identity,),{'ids':{}},(),merged)
    assert not merged[0].native_proven_absent
    assert stages[0]['input_count']==1 and zero_output(stages)['halt']


def test_all_selected_ids_in_native_skipped_module_are_MODULE_SKIPPED(tmp_path):
    from reliability.verifier.validated_run import apply_validation
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text('import pytest\npytest.skip("optional module",allow_module_level=True)\ndef helper(): raise AssertionError("body ran")\n')
    ids=('test_real.py::helper','test_real.py::missing')
    validation=validate_in_container(container,ids,TestRunner('pytest','fixture'))
    assert all(r.to_dict()['validation_status']=='MODULE_SKIPPED' for r in validation.records)
    run=apply_validation(RunResult(),validation)
    assert all(r.status is TestStatus.SKIPPED for r in run.results)


def test_non_test_module_requires_native_directory_proof_without_explicit_import(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'pytest.ini').write_text('[pytest]\npython_files = *test_*.py\ntestpaths = tests\n')
    folder=tmp_path/'tests'/'functional';folder.mkdir(parents=True)
    (folder/'test_real.py').write_text('def test_body(): raise AssertionError("body ran")\n')
    (folder/'consider_using_with_open.py').write_text('raise RuntimeError("lint input was imported")\ndef test_body(): pass\n')
    identity='tests/functional/consider_using_with_open.py::test_body'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    record=validation.records[0]
    assert record.reason=='not_a_test_module' and record.native_proven_absent
    assert validation.groups[0]['command'][-1]=='tests/functional'
    assert validation.groups[0]['directory_collection']['file_collected'] is False
    assert all(g['command'][-1]!='tests/functional/consider_using_with_open.py' for g in validation.groups)
    assert 'lint input was imported' not in record.message


def test_native_directory_custom_hook_overrides_static_file_pattern(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'example.py').write_text('def test_body(): raise AssertionError("body ran")\n')
    (tmp_path/'conftest.py').write_text('import pytest\ndef pytest_collect_file(file_path,parent):\n    if file_path.name == "example.py":\n        return pytest.Module.from_parent(parent,path=file_path)\n')
    identity='example.py::test_body'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.records[0].valid and validation.records[0].native_disagrees
    assert validation.groups[0]['command'][-1]=='.'
    assert validation.groups[0]['directory_collection']['command'][-1]=='.'
    assert validation.groups[0]['directory_collection']['file_collected']


def test_SymPy_disabled_is_observed_inside_native_test_file(tmp_path):
    from tests.unit.test_sympy_adapter import fake_repo
    program,canary=fake_repo(tmp_path)
    native=tmp_path/'sympy/testing/runtests.py'
    source=native.read_text().replace('  functions=[fn for name,fn in gl.items()',
        '  disabled = gl.get("disabled", False)\n  if disabled: return\n  functions=[fn for name,fn in gl.items()')
    native.write_text(source)
    (tmp_path/'sympy/tests/test_sample.py').write_text('disabled = True\ndef test_one(): raise AssertionError("body ran")\n')
    identity='sympy/tests/test_sample.py::test_one'
    proc=subprocess.run([sys.executable,str(program),'collect','sympy/tests/test_sample.py'],cwd=tmp_path,env=clean_env(),input=json.dumps({'ids':[identity]}),capture_output=True,text=True,check=True)
    record=json.loads(proc.stdout)['ids'][identity]
    assert record['collection_status']=='MODULE_SKIPPED' and record['module_skip_reason']=='disabled'
    assert record['message']=='module_skip: disabled' and not canary.exists()


def test_RunHealthError_task1_stops_task2_end_to_end_without_fake_health_records(tmp_path,monkeypatch):
    from dataclasses import replace
    spec=task_spec(tmp_path)
    spec=replace(spec,instance_id='task1',tests=('test_real.py::helper',))
    other=replace(spec,instance_id='task2')
    root=tmp_path/'repository';root.mkdir()
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    (root/'test_real.py').write_text('def helper(): raise AssertionError("body ran")\ndef test_real(): raise AssertionError("body ran")\n')
    started=[]
    class RealCollectionContainer(LocalContainer):
        def __init__(self,instance_id,*args,**kwargs):
            super().__init__(root)
            started.append(instance_id);self.instance_id=instance_id
            self.source_integrity={'status':'VERIFIED'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def set_patched(self,value):pass
        def generated_snapshot(self,*args,**kwargs):return {'files':{}}
    monkeypatch.setattr(launch,'FrozenContainer',RealCollectionContainer)
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    monkeypatch.setattr(launch,'require_frozen_head',lambda tag:'unit-test-commit')
    monkeypatch.setattr(launch,'plan_for',lambda specs:{'task_order':[s.instance_id for s in specs]})
    monkeypatch.setattr(launch,'run_regression',lambda *args,**kwargs:pytest.fail('Scoring after health halt'))
    output=tmp_path/'runs'/'attempt'
    reference={s.instance_id:{'base':s.tests,'patched':s.tests} for s in (spec,other)}
    assert launch.execute([spec,other],output,'unit-freeze',reference)==2
    assert started==['task1']
    record=json.loads((output/'health.jsonl').read_text())
    assert record['halt'] and all(t['G2']['lost_ids']==list(spec.tests) for t in record['trees'])
    assert json.loads((output/'completion.json').read_text())['status']=='ABORTED_HEALTH'
    assert not (output/'tasks'/'task2').exists()


def G1_module(monkeypatch):
    import importlib.util
    monkeypatch.setitem(sys.modules,'phase4_launch',launch)
    path=Path(__file__).resolve().parents[2]/'scripts/phase4_stage_preflight.py'
    spec=importlib.util.spec_from_file_location('fix14_G1_tested',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('failure',['mkdir','health_write','base_exception'])
def test_G1_records_per_pair_failures_and_still_visits_every_pair(tmp_path,monkeypatch,failure):
    from dataclasses import replace
    from types import SimpleNamespace
    module=G1_module(monkeypatch)
    spec=replace(task_spec(tmp_path),source=SimpleNamespace(pre_install=SimpleNamespace(repo='example/repo',version='1')))
    specs=[spec,replace(spec,instance_id='second')]
    monkeypatch.setattr(launch,'validate_inputs',lambda *args:specs)
    monkeypatch.setattr(launch,'load_reference',lambda *args:{})
    monkeypatch.setattr(launch,'plan_for',lambda specs:{})
    visited=[]
    class Container(ContainerShell):
        def __init__(self,iid,*args,**kwargs):
            super().__init__();self.iid=iid
            if failure=='base_exception' and iid=='task':raise SystemExit('native startup aborted')
        def set_patched(self,value):visited.append((self.iid,value))
        def generated_snapshot(self,*args,**kwargs):return {'files':{}}
    monkeypatch.setattr(launch,'FrozenContainer',Container)
    from reliability.verifier.collection import ValidationPass
    monkeypatch.setattr(module,'validate_in_container',lambda *args,**kwargs:ValidationPass())
    monkeypatch.setattr(module,'runner_startup',lambda *args,**kwargs:{'stage':'runner_startup','status':'COMPLETE','input_count':1,'output_count':1})
    original_mkdir=Path.mkdir;original_write=launch.write
    def mkdir(path,*args,**kwargs):
        if failure=='mkdir' and path.name=='base' and path.parent.name=='task':raise PermissionError('pair directory denied')
        return original_mkdir(path,*args,**kwargs)
    def write(path,value):
        if failure=='health_write' and path.name=='health.json' and path.parent.parent.name=='task':raise OSError('pair receipt denied')
        return original_write(path,value)
    monkeypatch.setattr(Path,'mkdir',mkdir);monkeypatch.setattr(launch,'write',write)
    output=tmp_path/'g1'
    assert module.main(output)==1
    summary=json.loads((output/'summary.json').read_text())
    assert summary['task_tree_count']==4 and summary['exhaustive'] and not summary['launch_allowed']
    assert ('second',False) in visited and ('second',True) in visited
    assert 'denied' in (output/'failures.csv').read_text() or 'SystemExit' in (output/'failures.csv').read_text()


def test_non_ASCII_parameter_identity_through_real_native_collection(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'pytest.ini').write_text('[pytest]\ndisable_test_id_escaping_and_forfeit_all_rights_to_community_support = True\n')
    (tmp_path/'test_real.py').write_text('import pytest\n@pytest.mark.parametrize("value",[1],ids=["é::()::雪"])\ndef test_param(value): raise AssertionError("body ran")\n')
    identity='test_real.py::test_param[é::()::雪]'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.records[0].valid and validation.runnable_ids==(identity,)


def test_confirmation_reference_preserves_initial_expansion_members():
    from reliability.verifier.collection import ValidationPass
    from reliability.verifier.validated_run import apply_validation
    slot='tests/base.py::Base::test_body';member='tests/test_real.py::TestReal::test_body'
    initial=apply_validation(RunResult(results=(TestResult(member,TestStatus.PASSED),)),
        ValidationPass((IDValidation(slot,'runnable_test',(member,),expanded=True),)))
    reference=launch.confirmation_reference(initial,(member,))
    assert reference['admitted_ids']==[member]
    missing=RunResult(results=(TestResult(member,TestStatus.INVALID_ID),),requested_tests=(member,))
    assert health_for_run('task','base',missing,reference)['G2']['halt']


def test_native_parent_probe_does_not_create_false_G3_for_cross_module_expansion(tmp_path):
    from reliability.verifier.run_health import zero_output
    container=repository(tmp_path)
    folder=tmp_path/'tests';folder.mkdir();(folder/'__init__.py').write_text('')
    (folder/'base.py').write_text('class Mixin:\n    def test_body(self): raise AssertionError("body ran")\n')
    (folder/'test_real.py').write_text('from tests.base import Mixin\nclass TestReal(Mixin): pass\n')
    identity='tests/base.py::Mixin::test_body'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.records[0].valid and validation.records[0].expanded
    assert validation.runnable_ids==('tests/test_real.py::TestReal::test_body',)
    assert not zero_output(validation.stage_health)['halt']
    parent=next(s for s in validation.stage_health if s['module']=='tests/base.py')
    assert parent['status']=='ALL_PROVEN_INVALID' and parent['input_count']==0
    assert parent['original_input_count']==1 and parent['proven_absent_count']==1


@pytest.mark.parametrize('declaration',['import pytest\n@pytest.fixture',
    'from pytest import fixture as resource\n@resource()',
    'import pytest as pt\n@pt.fixture(scope="module")'])
def test_native_absent_fixture_is_agreed_static_helper_not_collector_fallback(tmp_path,declaration):
    container=repository(tmp_path)
    (tmp_path/'test_real.py').write_text(declaration+'\ndef test_fixture(): raise AssertionError("fixture body ran")\n')
    identity='test_real.py::test_fixture'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    record=validation.records[0]
    assert record.to_dict()['validation_status']=='INVALID_ID'
    assert record.native_proven_absent and not record.collector_fallback
    assert validation.stage_health[0]['status']=='ALL_PROVEN_INVALID'


def test_native_absence_disagreement_never_falls_back_as_if_collector_crashed():
    from reliability.verifier.collection import contain_collection,collection_stages
    identity='test_real.py::test_body'
    static=(IDValidation(identity,'runnable_test',(identity,)),)
    native={'ids':{identity:{'ids':[],'reason':'native_not_found','completed':True,
                             'collection_status':'COMPLETE','returncode':0}}}
    merged=merge_native(static,native['ids'])
    contained=contain_collection(static,merged,'task',())
    assert contained[0].unavailable and not contained[0].collector_fallback
    assert collection_stages('task',(identity,),native,(),merged)[0]['status']=='COLLECTION_ERROR'


def test_native_directory_positive_discovery_is_followed_by_selected_file_collection(tmp_path):
    container=repository(tmp_path)
    (tmp_path/'example.py').write_text('def test_body(): raise AssertionError("body ran")\n')
    (tmp_path/'test_unselected.py').write_text('import _fix14_missing_unselected_\n')
    (tmp_path/'conftest.py').write_text('import pytest\ndef pytest_collect_file(file_path,parent):\n    if file_path.name == "example.py":\n        return pytest.Module.from_parent(parent,path=file_path)\n')
    identity='example.py::test_body'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    assert validation.records[0].valid and not validation.records[0].collector_fallback
    assert validation.stage_health[0]['status']=='COMPLETE'
    group=validation.groups[0]
    assert group['command'][-1]=='example.py' and group['returncode']==0
    assert group['directory_collection']['file_collected']
    assert group['directory_collection']['returncode']==2
    assert group['directory_collection']['collection_errors']


@pytest.mark.parametrize('unrelated_error',[False,True])
def test_directory_doctest_helper_never_gets_explicit_test_module_import(tmp_path,unrelated_error):
    container=repository(tmp_path)
    (tmp_path/'pytest.ini').write_text('[pytest]\naddopts = --doctest-modules\nnorecursedirs = driver_files\nfilterwarnings = error::pytest.PytestCollectionWarning\n')
    (tmp_path/'helper.py').write_text('class TestRunner:\n    def __init__(self): pass\ndef raises():\n    def test_foo(): raise AssertionError("body ran")\n')
    if unrelated_error:(tmp_path/'test_bad.py').write_text('import _fix14_missing_unselected_\n')
    identity='helper.py::raises::test_foo'
    validation=validate_in_container(container,(identity,),TestRunner('pytest','fixture'))
    record=validation.records[0]
    assert validation.groups[0]['command'][-1]=='.'
    assert 'cannot collect test class' not in record.message
    assert record.unavailable==unrelated_error
    assert record.native_proven_absent==(not unrelated_error)
