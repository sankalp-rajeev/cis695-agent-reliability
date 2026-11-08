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
