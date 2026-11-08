"""Native module skips are outcomes; zero output without one is still an error."""

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from reliability.env import clean_env
from reliability.verifier.admission_reference import original_admission_evidence
from reliability.verifier.collection import (
    _DJANGO_COLLECT,
    _NATIVE_DRIVER,
    _PYTEST_PLUGIN,
    ValidationPass,
    collection_stages,
)
from reliability.verifier.id_validation import IDValidation, merge_native
from reliability.verifier.module_skips import pytest_module_skip
from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    Signal,
    TestStatus,
    run_regression,
)
from reliability.verifier.run_health import health_for_run, zero_output
from reliability.verifier.selection import Selection
from reliability.verifier.validated_run import apply_validation


def collect(tmp_path,source,module='test_module.py'):
    path=tmp_path/module;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
    (tmp_path/'verifier_collect_plugin.py').write_text(_PYTEST_PLUGIN)
    request=tmp_path/'request.json';identity=module+'::test_body'
    request.write_text(json.dumps({'runner':'pytest','ids':[identity],'module_timeout_s':30}))
    program=_NATIVE_DRIVER.replace('/tmp/verifier_collect_request.json',str(request)).replace(
        '/tmp/verifier_collect_partial.json',str(tmp_path/'partial.json')).replace('/tmp/verifier_collect_pgid',str(tmp_path/'pgid'))
    driver=tmp_path/'driver.py';driver.write_text(program)
    proc=subprocess.run([sys.executable,str(driver)],cwd=tmp_path,env=clean_env(),capture_output=True,text=True,check=True)
    receipt=json.loads(proc.stdout)
    static=(IDValidation(identity,'runnable_test',(identity,)),)
    validation=ValidationPass(merge_native(static,receipt['ids']),stage_health=collection_stages('task',[identity],receipt,()))
    return identity,receipt,validation,apply_validation(RunResult(evidence_complete=True),validation)


@pytest.mark.parametrize('source,reason',[
    ('import pytest\npytest.importorskip("_fix13_missing_optional_package_")\ndef test_body(): raise AssertionError("body ran")\n','could not import'),
    ('import pytest\npytest.skip("optional dependency unavailable",allow_module_level=True)\ndef test_body(): raise AssertionError("body ran")\n','optional dependency unavailable'),
    ('import pytest\npytest.skip("\\x1b[31mcolored reason\\x1b[0m",allow_module_level=True)\ndef test_body(): raise AssertionError("body ran")\n','colored reason'),
])
def test_native_module_skip_becomes_reasoned_SKIPPED_without_execution(tmp_path,source,reason):
    identity,receipt,validation,run=collect(tmp_path,source)
    assert '-rs' in receipt['groups'][0]['command']
    assert receipt['ids'][identity]['collection_status']=='MODULE_SKIPPED'
    assert validation.runnable_ids==() and not validation.records[0].unavailable
    assert run.results[0].status is TestStatus.SKIPPED
    assert run.results[0].message.startswith('module_skip: ') and reason in run.results[0].message
    assert '\x1b' not in run.results[0].message
    assert run.validation[0]['admitted']
    assert not zero_output(validation.stage_health)['halt']
    class Executor:
        def run(self,*a,**k):return run
    assert run_regression('task',Selection(tests=(identity,)),Executor(),RegressionConfig(skip_compatible=True)).signal is Signal.PASS
    assert run_regression('task',Selection(tests=(identity,)),Executor(),RegressionConfig(skip_compatible=False)).signal is Signal.INCOMPLETE


def test_genuinely_empty_module_is_COLLECTION_ERROR_and_triggers_G3(tmp_path):
    identity,receipt,validation,run=collect(tmp_path,'VALUE = 1\n')
    assert receipt['ids'][identity]['collection_status']=='COMPLETE'
    # Static validity disagrees with native absence, so it remains missing.
    assert run.results[0].status is TestStatus.COLLECTION_ERROR
    assert zero_output(validation.stage_health)['halt']


def test_module_skip_without_reason_does_not_bypass_G3(tmp_path):
    _,_,validation,run=collect(tmp_path,'import pytest\npytest.skip("",allow_module_level=True)\n')
    assert run.results[0].status is TestStatus.COLLECTION_ERROR
    assert zero_output(validation.stage_health)['halt']


def test_package_initialization_skip_is_tied_to_descendant_module(tmp_path):
    (tmp_path/'package').mkdir();(tmp_path/'package/__init__.py').write_text(
        'import pytest\npytest.importorskip("_fix13_missing_package_dependency_")\n')
    _,_,validation,run=collect(tmp_path,'def test_body(): raise AssertionError("body ran")\n','package/test_module.py')
    assert validation.records[0].module_skip_reason and run.results[0].status is TestStatus.SKIPPED


def test_ANSI_summary_requires_matching_module_no_items_and_no_collection_errors():
    text='\x1b[33mSKIPPED [1] test_module.py:3: \x1b[31moptional: unavailable\x1b[0m'
    result=pytest_module_skip('test_module.py',[],[],text,5)
    assert result['reason']=='optional: unavailable'
    assert pytest_module_skip('other.py',[],[],text,5) is None
    assert pytest_module_skip('test_module.py',['test_module.py::test_body'],[],text,0) is None
    assert pytest_module_skip('test_module.py',[],[],text,2) is None
    assert pytest_module_skip('test_module.py',[],[],text,5,['ImportError']) is None


@pytest.mark.parametrize('original_status,blocked', [('skipped',False),('not_run',False),
    ('passed',True),('failed',True),('error',True),('xfail',True),('xpass',True)])
def test_G2_module_skip_may_not_replace_stronger_original_evidence(tmp_path,original_status,blocked):
    identity,_,_,run=collect(tmp_path,'import pytest\npytest.skip("optional",allow_module_level=True)\n')
    original=tmp_path/'original.json';original.write_text(json.dumps({'calls':[{'patched':False,
        'run':{'results':[{'test_id':identity,'status':original_status}]}}]}))
    reference=original_admission_evidence(original,hashlib.sha256(original.read_bytes()).hexdigest())['base']
    # G1 for this fixture also records a module skip, with no collected IDs.
    reference['g1_collected_ids']=[]
    health=health_for_run('task','base',run,reference)
    assert health['G2']['lost_count']==int(blocked)
    assert health['G2']['halt']==blocked
    assert health['admitted_ids']==int(not blocked)


def test_native_Django_module_skip_is_not_a_loader_error(tmp_path):
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/runtests.py').write_text('def setup(verbosity,test_labels,parallel): pass\n')
    (tmp_path/'tests/test_module.py').write_text('import unittest\nraise unittest.SkipTest("native optional dependency")\n')
    proc=subprocess.run([sys.executable,'-c',_DJANGO_COLLECT],cwd=tmp_path,env=clean_env(),
        input=json.dumps({'labels':['test_module.Case.test_body'],'module':'test_module'}),capture_output=True,text=True,check=True)
    row=json.loads(proc.stdout)['test_module.Case.test_body']
    assert row['collection_status']=='MODULE_SKIPPED' and row['module_skip_reason']=='native optional dependency'


def test_native_SymPy_module_skip_is_recorded_by_native_exception_type(tmp_path):
    from tests.unit.test_sympy_adapter import fake_repo
    program,canary=fake_repo(tmp_path)
    (tmp_path/'sympy/testing/pytest.py').write_text('class Skipped(Exception): pass\n')
    (tmp_path/'sympy/tests/test_sample.py').write_text('from sympy.testing.pytest import Skipped\nraise Skipped("optional sympy package")\n')
    path=tmp_path/'sympy/testing/runtests.py'
    source=path.read_text().replace('  functions=[fn for name,fn in gl.items()',
        '  except Exception:\n   import sys\n   self._reporter.test_exception(sys.exc_info());return\n  functions=[fn for name,fn in gl.items()')
    path.write_text(source)
    identity='sympy/tests/test_sample.py::test_one'
    proc=subprocess.run([sys.executable,str(program),'collect','sympy/tests/test_sample.py'],
        cwd=tmp_path,env=clean_env(),input=json.dumps({'ids':[identity]}),capture_output=True,text=True,check=True)
    record=json.loads(proc.stdout)['ids'][identity]
    assert record['collection_status']=='MODULE_SKIPPED'
    assert record['module_skip_reason']=='optional sympy package' and not canary.exists()


def test_partial_expansion_module_skip_is_unanimously_admitted_but_remains_a_strict_gap():
    selected='tests/base.py::Mixin::test_body';first='tests/a.py::CaseA::test_body';second='tests/b.py::CaseB::test_body'
    record=IDValidation(selected,'runnable_test',(first,second),expanded=True,
        module_skip_reason='optional dependency',module_skip_instances=((first,'optional dependency'),))
    from reliability.verifier.regression import TestResult
    run=apply_validation(RunResult(results=(TestResult(second,TestStatus.PASSED),),evidence_complete=True),ValidationPass((record,)))
    assert run.validation[0]['admitted'] and run.validation[0]['admitted_instances']==2
    assert any(r.status is TestStatus.SKIPPED for r in run.raw_results)
    health=health_for_run('task','base',run,{'admitted_ids':[selected],'module_skip_blocked_ids':[selected]})
    assert health['G2']['halt']


def test_collection_programs_keep_historical_Python36_syntax_and_API():
    from reliability.verifier.sympy_adapter import _SYMPY_PROGRAM
    for source in [_NATIVE_DRIVER,_DJANGO_COLLECT,_SYMPY_PROGRAM]:
        tree=ast.parse(source,feature_version=(3,6))
        assert not any(isinstance(n,ast.Attribute) and n.attr in ('removeprefix','removesuffix') for n in ast.walk(tree))


def test_exhaustive_G1_continues_after_failure_and_evaluates_only_at_end(tmp_path,monkeypatch):
    from dataclasses import replace
    from types import SimpleNamespace

    from tests.unit.test_phase4_launcher import launch, task_spec
    source=Path(__file__).resolve().parents[2]/'scripts/phase4_stage_preflight.py'
    module_spec=importlib.util.spec_from_file_location('g1_fix13_tested',source);g1=importlib.util.module_from_spec(module_spec)
    monkeypatch.setitem(sys.modules,'phase4_launch',launch);module_spec.loader.exec_module(g1)
    spec=task_spec(tmp_path);spec=replace(spec,source=SimpleNamespace(pre_install=SimpleNamespace(repo='example/project',version='1')))
    monkeypatch.setattr(g1.launch,'validate_inputs',lambda *a:(spec,))
    monkeypatch.setattr(g1.launch,'load_reference',lambda *a:{})
    monkeypatch.setattr(g1.launch,'plan_for',lambda *a:{})
    calls=[]
    class Container:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def set_patched(self,value):calls.append(value)
        def generated_snapshot(self,*a):return {'files':{}}
    monkeypatch.setattr(g1.launch,'FrozenContainer',Container)
    monkeypatch.setattr(g1,'runner_startup',lambda *a,**k:{'stage':'runner_startup','status':'COMPLETE','input_count':1,'output_count':1})
    def collection(*a,**k):
        failed=len(calls)==1
        return ValidationPass(stage_health=({'stage':'native_collection','module':'test_module.py',
            'status':'COLLECTION_ERROR' if failed else 'COMPLETE','input_count':1,'output_count':0 if failed else 1,
            'messages':['first collector failed'] if failed else []},))
    monkeypatch.setattr(g1,'validate_in_container',collection)
    output=tmp_path/'g1'
    assert g1.main(output)==1 and calls==[False,True]
    summary=json.loads((output/'summary.json').read_text())
    assert summary['exhaustive'] and summary['gate_evaluated_after_all_pairs'] and summary['task_tree_count']==2
    assert not summary['launch_allowed']
