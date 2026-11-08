"""Fix 14 health regressions through collection, mapping and launcher paths."""
import json
import os
import sys
import shlex
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
