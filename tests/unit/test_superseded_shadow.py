"""Generic pre-freeze rule checks; no five-case or gold-directed fixtures."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from reliability.verifier.superseded_rule import classify
from reliability.verifier.superseded_shadow import run_shadow

CONFIG={'minimum_observations_per_tree':4}


def packet():
    tid='tests/test_settings.py::test_output'
    return {'issue':'The mode is changed from old to new.',
        'candidate_patch':'--- a/lib/settings.py\n+++ b/lib/settings.py\n@@ -1 +1 @@\n- "mode": "old",\n+ "mode": "new",\n',
        'test_source':"def test_output(settings):\n    out=settings.build()\n    mode='old'\n    assert 'mode=%s' % mode in out\n",
        'base_output':[{'stdout':tid+' PASSED\n','stderr':'','returncode':0,'timed_out':False} for _ in range(4)],
        'patched_output':[{'stdout':tid+" FAILED\n> assert 'mode=%s' % mode in out\nE AssertionError: assert 'mode=old' in 'mode=new'\n",
                           'stderr':'','returncode':1,'timed_out':False} for _ in range(4)]}


def test_all_five_conditions_required_for_shadow_suggestion():
    result=classify(packet(),CONFIG)
    assert result['prediction']=='LIKELY_SUPERSEDED_ASSERTION'
    assert result['shadow_mode']
    assert all(result['checks'].values())


@pytest.mark.parametrize('change',[
    lambda p:p['base_output'].pop(),
    lambda p:p.update(issue='Something changed.'),
    lambda p:p.update(candidate_patch=''),
    lambda p:p['patched_output'][0].update(timed_out=True),
    lambda p:p['patched_output'][0].update(stdout='tests/test_settings.py::test_output ERROR\nE ImportError: missing'),
    lambda p:p['base_output'][0].update(stdout='ERROR: not found: another test\n'+p['base_output'][0]['stdout']),
    lambda p:p['patched_output'][0].update(stdout=p['patched_output'][0]['stdout']+'other.py::bad FAILED\n'),
    lambda p:p.update(oracle_label='right'),
])
def test_missing_or_conflicting_evidence_abstains(change):
    data=packet();change(data)
    result=classify(data,CONFIG)
    assert result['prediction']=='UNCERTAIN'
    assert not result['suggest_suppress_v2_negative']


def make_manifest(tmp_path):
    from reliability.verifier import superseded_shadow
    folder=Path(superseded_shadow.__file__).parent
    data={'config':deepcopy(CONFIG),'implementation_sha256':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
          for name in ('superseded_rule.py','superseded_shadow.py')}}
    data['frozen_rule_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    path=tmp_path/'rule.json';path.write_text(json.dumps(data));return path


def test_kernel_blocks_actual_file_access_in_classifier_process(tmp_path):
    canary=tmp_path/'oracle_canary';canary.write_text('must be inaccessible')
    result=run_shadow([packet()],manifest=make_manifest(tmp_path),probes=[str(canary)])
    assert result['isolation']['probe_results'][str(canary)]=='DENIED'
    assert result['predictions'][0]['prediction']=='LIKELY_SUPERSEDED_ASSERTION'


def test_changed_configuration_fails_closed(tmp_path):
    manifest=make_manifest(tmp_path)
    data=json.loads(manifest.read_text());data['config']['minimum_observations_per_tree']=1
    manifest.write_text(json.dumps(data))
    assert run_shadow([packet()],manifest=manifest)['predictions'][0]['prediction']=='UNCERTAIN'
