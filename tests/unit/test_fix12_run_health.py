"""Guard tests use admission only and synthetic collection failures."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.unit.test_phase4_launcher import launch, task_spec

from reliability.verifier.admission_reference import JSONProjection, original_admitted
from reliability.verifier.collection import (
    ValidationPass,
    contain_collection,
    validate_in_container,
)
from reliability.verifier.id_validation import IDValidation
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from reliability.verifier.run_health import (
    RunHealthError,
    allowed_failure,
    append_health,
    covering_order,
    health_for_run,
    monotonicity,
    runner_startup,
    zero_output,
)
from reliability.verifier.selection import TestRunner


def test_projection_never_decodes_verdict_or_unselected_fields(tmp_path,monkeypatch):
    data={'signal':'FORBIDDEN_VERDICT','outcomes':{'quoted':'FORBIDDEN { [ \\" }, ]'},
        'calls':[{'patched':False,'run':{'results':[{'test_id':'a','status':'passed'},
            {'test_id':'b','status':'skipped'},{'test_id':'missing','status':'not_run'}],
            'raw_stdout_b64':'FORBIDDEN_CAPTURE'}},
            {'patched':True,'run':{'results':[{'test_id':'a','status':'failed'}]}},
            {'patched':True,'run':{'results':[{'test_id':'c','status':'FORBIDDEN_CONFIRMATION'}]}}]}
    original=JSONProjection.scalar
    def scalar(self):
        value=original(self)
        assert not (isinstance(value,str) and value.startswith('FORBIDDEN'))
        return value
    monkeypatch.setattr(JSONProjection,'scalar',scalar)
    path=tmp_path/'original.json';path.write_text(json.dumps(data))
    result=original_admitted(path,hashlib.sha256(path.read_bytes()).hexdigest())
    assert result=={'base':['a','b'],'patched':['a']}
    with pytest.raises(ValueError,match='hash mismatch'):
        original_admitted(path,'wrong')


@pytest.mark.parametrize('count,lost,halt',[(0,0,False),(50,1,True),(1000,1,False),
    (1000,9,False),(1000,10,True),(2000,10,True)])
def test_admission_loss_thresholds_are_OR_and_exact(count,lost,halt):
    reference=set(range(count));admitted=set(range(count-lost))
    assert monotonicity(reference,admitted,())['halt']==halt


def test_proven_invalid_reference_is_still_lost():
    assert monotonicity({'one'},(),{'one'})['lost_count']==1
    assert monotonicity({'one'},(),())['halt']


def test_collector_crash_falls_back_only_to_validated_same_family():
    selected='test_module.py::test_body'
    class Container:
        instance_id='synthetic'
        def exec_input(self,*a,**k):return 0,''
        def exec(self,command,**k):
            if command.startswith('python -c '):
                return 0,json.dumps({'test_module.py':'def test_body(): raise AssertionError("no body")\n'})
            if command=='python /tmp/verifier_collect_driver.py':return 2,'collector crashed'
            return 0,''
    validation=validate_in_container(Container(),(selected,),TestRunner('pytest','fixture'))
    record=validation.records[0]
    assert record.collector_fallback and record.stage=='collector_fallback'
    assert record.runnable_ids==(selected,) and validation.runnable_ids==(selected,)
    assert 'collector crashed' in record.collector_message
    assert validation.to_dict()['collector_status']=='COLLECTION_ERROR'
    assert validation.stage_health[0]['output_count']==0
    # Fallback does not pretend that primary native collection succeeded.
    assert zero_output(validation.stage_health)['halt']
    invalid=IDValidation('test_module.py::helper','helper',reason='helper')
    broken=IDValidation(invalid.selected_id,'unknown',reason='collection_error',unavailable=True,failure_status='COLLECTION_ERROR')
    assert not contain_collection((invalid,),(broken,),'task',())[0].collector_fallback


def test_exception_scope_is_exact_and_never_a_blanket_task_exemption():
    exception={'instance_id':'task','module':'tests/gis_tests/a.py','stages':['native_collection'],
               'required_message':'GIS backend required','cause':'GIS_GUARD'}
    assert allowed_failure([exception],'task','tests/gis_tests/a.py','native_collection','GIS backend required')=='GIS_GUARD'
    assert allowed_failure([exception],'task','tests/other.py','native_collection','GIS backend required') is None
    assert allowed_failure([exception],'task','tests/gis_tests/a.py','runner_startup','GIS backend required') is None


def test_zero_output_halts_but_empty_input_and_exact_exception_are_explicit():
    stage={'stage':'native_collection','input_count':1,'output_count':0}
    assert zero_output([stage])['halt']
    assert not zero_output([{**stage,'input_count':0}])['halt']
    assert not zero_output([{**stage,'allowed_exception':'GIS_GUARD'}])['halt']


def test_order_covers_lowest_ID_per_combination_then_keeps_frozen_rest():
    def spec(i,repo,version):
        return SimpleNamespace(instance_id=i,runner=TestRunner('pytest','fixture'),
            source=SimpleNamespace(pre_install=SimpleNamespace(repo=repo,version=version)))
    frozen=[spec('z','a','1'),spec('s','sympy/sympy','1'),spec('b','a','2'),spec('a','a','1'),spec('y','a','1')]
    result=covering_order(frozen)
    assert [r.instance_id for r in result]==['a','b','s','z','y']
    assert [r.instance_id for r in covering_order(frozen)]==[r.instance_id for r in result]


def test_expanded_original_slot_needs_all_members_admitted():
    run=RunResult(results=(TestResult('slot',TestStatus.PASSED),),requested_tests=('slot',),
                  validation=({'selected_id':'slot','admitted':False,'expanded':True},))
    assert health_for_run('task','base',run,['slot'])['G2']['halt']


def test_losing_task_halts_and_health_is_written_before_scoring(tmp_path,monkeypatch):
    spec=task_spec(tmp_path)
    class Container:
        def __init__(self,*a,**k):self.source_integrity={'status':'VERIFIED'}
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def generated_snapshot(self):return {'files':{}}
    class Executor:
        def __init__(self,*a,**k):pass
        def run(self,tests,**k):
            return RunResult(results=tuple(TestResult(t,TestStatus.NOT_RUN) for t in tests),requested_tests=tests,
                stage_health=({'stage':'native_collection','input_count':1,'output_count':0},))
    monkeypatch.setattr(launch,'FrozenContainer',Container)
    monkeypatch.setattr(launch,'ContainerTestExecutor',Executor)
    monkeypatch.setattr(launch,'run_regression',lambda *a,**k:pytest.fail('Scored after a health halt'))
    health=tmp_path/'health.jsonl'
    with pytest.raises(RunHealthError):
        launch.run_task(spec,tmp_path/'task','fixture',{'base':spec.tests,'patched':spec.tests},health)
    row=json.loads(health.read_text())
    assert row['halt'] and all(r['G2']['halt'] and r['G3']['halt'] for r in row['trees'])
    assert not (tmp_path/'task/result.json').exists()


def test_health_record_is_flushed_before_starting_next_task(tmp_path,monkeypatch):
    monkeypatch.setattr(launch,'ROOT',tmp_path)
    monkeypatch.setattr(launch,'require_frozen_head',lambda tag:'executor')
    monkeypatch.setattr(launch,'plan_for',lambda specs:{})
    spec=task_spec(tmp_path);path=tmp_path/'runs/attempt'
    calls=[]
    def task(spec,folder,experiment,reference,health_path):
        if calls:
            assert len(health_path.read_text().splitlines())==len(calls)
        append_health(health_path,{'task':spec.instance_id,'halt':False})
        calls.append(spec.instance_id)
    monkeypatch.setattr(launch,'run_task',task)
    assert launch.execute([spec,spec],path,'new-freeze',{'task':{}})==0
    assert len((path/'health.jsonl').read_text().splitlines())==2


def test_runner_startup_uses_help_only_and_empty_output_is_unavailable():
    class Container:
        def exec(self,command,**k):
            assert '--help' in command
            return 0,''
    for kind in ['pytest','django','sympy']:
        record=runner_startup(Container(),kind)
        assert record['status']=='RUNNER_UNAVAILABLE' and record['tests_executed']==0


def test_G1_runs_both_trees_without_instantiating_an_execution_adapter(tmp_path,monkeypatch):
    path=Path(__file__).resolve().parents[2]/'scripts/phase4_stage_preflight.py'
    module_spec=importlib.util.spec_from_file_location('g1_tested',path)
    module=importlib.util.module_from_spec(module_spec)
    # The script imports the launcher by its CLI module name.
    monkeypatch.setitem(sys.modules,'phase4_launch',launch)
    module_spec.loader.exec_module(module)
    fake=task_spec(tmp_path)
    from dataclasses import replace
    fake=replace(fake,source=SimpleNamespace(pre_install=SimpleNamespace(repo='example/project',version='1')))
    monkeypatch.setattr(module.launch,'validate_inputs',lambda *a:(fake,))
    monkeypatch.setattr(module.launch,'load_reference',lambda *a:{fake.instance_id:{'base':[],'patched':[]}})
    monkeypatch.setattr(module.launch,'plan_for',lambda *a:{})
    monkeypatch.setattr(module.launch,'ContainerTestExecutor',lambda *a,**k:pytest.fail('G1 instantiated execution adapter'))
    patches=[]
    class Container:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def set_patched(self,value):patches.append(value)
        def generated_snapshot(self,*a):return {'files':{}}
    monkeypatch.setattr(module.launch,'FrozenContainer',Container)
    monkeypatch.setattr(module,'runner_startup',lambda *a,**k:{'stage':'runner_startup','status':'COMPLETE','input_count':1,'output_count':1,'tests_executed':0})
    monkeypatch.setattr(module,'validate_in_container',lambda *a,**k:ValidationPass(
        records=(IDValidation(fake.tests[0],'runnable_test',fake.tests),),
        stage_health=({'stage':'native_collection','status':'COMPLETE','input_count':1,'output_count':1},)))
    output=tmp_path/'g1'
    assert module.main(output)==0 and patches==[False,True]
    assert json.loads((output/'summary.json').read_text())['tests_executed']==0
