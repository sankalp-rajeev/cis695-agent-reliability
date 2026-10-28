"""Generic v2 structural checks, not the familiar historical cases."""
import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from reliability.verifier.regression import (
    Outcome,
    RegressionReport,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
)
from reliability.verifier.superseded_rule_v2 import classify
from reliability.verifier.superseded_shadow_v2 import run_shadow, shadow_from_report

CONFIG={'minimum_observations_per_tree':2}
TID='tests/test_settings.py::test_output'


def packet():
    return {'issue':'The mode is changed from old to new.',
        'candidate_patch':'--- a/lib/settings.py\n+++ b/lib/settings.py\n@@ -1 +1 @@\n- "mode": "old",\n+ "mode": "new",\n',
        'test_source':"def test_output(settings):\n    out=settings.build()\n    mode='old'\n    assert 'mode=%s' % mode in out\n",
        'base_output':[{'stdout':TID+' PASSED\n','stderr':'','returncode':0,'timed_out':False} for _ in range(2)],
        'patched_output':[{'stdout':TID+" FAILED\n> assert 'mode=%s' % mode in out\nE AssertionError: assert 'mode=old' in 'mode=new'\n",
                           'stderr':'','returncode':1,'timed_out':False} for _ in range(2)]}


def manifest(tmp_path):
    from reliability.verifier import superseded_shadow_v2
    folder=Path(superseded_shadow_v2.__file__).parent
    data={'config':CONFIG,'implementation_sha256':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
        for name in ('superseded_rule_v2.py','superseded_shadow_v2.py','superseded_shadow.py')}}
    data['frozen_rule_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    path=tmp_path/'v2.json';path.write_text(json.dumps(data));return path


def test_two_consistent_observations_suffice():
    assert classify(packet(),CONFIG)['prediction']=='LIKELY_SUPERSEDED_ASSERTION'


def test_unrelated_infrastructure_needs_verified_candidate_scope():
    data=packet()
    for r in data['base_output']+data['patched_output']:
        clean=deepcopy(r)
        r['stdout']='ERROR: not found: unrelated.py::missing\n'+r['stdout']
        assert classify(data,CONFIG)['prediction']=='UNCERTAIN'
        r['target_output']={**clean,'requested_ids':[TID]}
    assert classify(data,CONFIG)['prediction']=='LIKELY_SUPERSEDED_ASSERTION'


@pytest.mark.parametrize('condition',['target_collection_error','disagreement','other_assertion','timeout','one_observation'])
def test_uncertain_conditions_are_not_suppressed(condition):
    data=packet()
    if condition=='target_collection_error':
        data['patched_output'][0]['stdout']='ERROR collecting tests/test_settings.py\n'+data['patched_output'][0]['stdout']
    elif condition=='disagreement':data['base_output'][0]['stdout']=TID+' FAILED\n'
    elif condition=='other_assertion':data['patched_output'][0]['stdout']+='other.py::bad FAILED\n'
    elif condition=='timeout':data['base_output'][0]['timed_out']=True
    else:data['base_output'].pop()
    assert classify(data,CONFIG)['prediction']=='UNCERTAIN'


def test_issue_patch_test_relationship_guard_is_unchanged():
    data=packet();data['issue']='Unrelated request.'
    assert classify(data,CONFIG)['prediction']=='UNCERTAIN'


def test_v2_worker_still_cannot_open_oracle_files(tmp_path):
    canary=tmp_path/'oracle_labels';canary.write_text('prohibited')
    result=run_shadow([packet()],manifest=manifest(tmp_path),probes=[str(canary)])
    assert result['isolation']['probe_results'][str(canary)]=='DENIED'
    assert result['predictions'][0]['prediction']=='LIKELY_SUPERSEDED_ASSERTION'


@pytest.mark.parametrize('signal',[Signal.PASS,Signal.INCOMPLETE,Signal.NOT_AVAILABLE])
def test_non_fail_candidates_never_add_executions(signal):
    class Executor:
        def run(self,*args,**kwargs):raise AssertionError('No execution permitted')
    report=RegressionReport(instance_id='fixture',signal=signal)
    result=shadow_from_report(report,'','',None,Executor())
    assert result['costs']['additional_base_runs']==0
    assert result['costs']['additional_patched_runs']==0


def structured_run(data):
    raw=data['stdout'].encode()
    status=TestStatus.PASSED if data['returncode']==0 else TestStatus.FAILED
    return RunResult(results=(TestResult(TID,status),),raw_results=(TestResult(TID,status),),
        requested_tests=(TID,),raw_id_map={TID:(TID,)},evidence_complete=True,
        runner_log_b64=base64.b64encode(raw).decode(),events=(
            {'event':'start','batch':1,'ids':[TID],'offset':0},
            {'event':'end','batch':1,'offset':len(raw),'returncode':data['returncode'],'duration_s':0.01},
            {'event':'complete'}))


def test_only_one_extra_base_reuses_patch_confirmation_and_preserves_signal(tmp_path):
    p=packet();base=structured_run(p['base_output'][0]);patched=structured_run(p['patched_output'][0])
    report=RegressionReport(instance_id='fixture',signal=Signal.FAIL,original_signal=Signal.FAIL,
        outcomes={TID:Outcome.REGRESSION},baseline=base,patched=patched,confirmations=(patched,))
    class Container:
        def __init__(self):self.states=[]
        def set_patched(self,value):self.states.append(value)
    class Executor:
        container=Container()
        def __init__(self):self.calls=[]
        def run(self,tests,*,patched,timeout_s):
            self.calls.append((tuple(tests),patched));return base
    class Tree:
        def read_text(self,path):return p['test_source']
    executor=Executor()
    result=shadow_from_report(report,p['issue'],p['candidate_patch'],Tree(),executor,
                              manifest=manifest(tmp_path))
    assert executor.calls==[((TID,),False)]
    assert executor.container.states==[True]
    assert result['costs']['reused_patched_runs']==1
    assert result['costs']['additional_base_runs']==1
    assert result['costs']['additional_patched_runs']==0
    assert result['predictions'][0]['prediction']=='LIKELY_SUPERSEDED_ASSERTION'
    assert report.signal is Signal.FAIL and report.outcomes[TID] is Outcome.REGRESSION
