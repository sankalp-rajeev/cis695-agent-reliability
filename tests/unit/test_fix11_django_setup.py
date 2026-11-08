"""Version-aware collection setup; test bodies must never be called."""

import ast
import json
import subprocess
import sys

import pytest

from reliability.env import clean_env
from reliability.verifier.collection import _DJANGO_COLLECT, django_setup_entry_point


@pytest.mark.parametrize('entry,signature', [
    ('setup','verbosity, test_labels, parallel'),
    ('setup','verbosity, test_labels, parallel, start_at, start_after'),
    ('setup_run_tests','verbosity, start_at, start_after, test_labels=None'),
])
def test_each_supported_bootstrap_collects_without_entering_test_body(tmp_path, entry, signature):
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/runtests.py').write_text(
        'from pathlib import Path\n'
        'def '+entry+'('+signature+'):\n'
        ' Path("setup_used").write_text("'+entry+'")\n'
    )
    (tmp_path/'tests/test_sample.py').write_text(
        'import unittest\nclass Case(unittest.TestCase):\n'
        ' def test_body(self): raise AssertionError("collection ran a test body")\n')
    proc = subprocess.run([sys.executable,'-c',_DJANGO_COLLECT], cwd=tmp_path,
        env=clean_env(),input=json.dumps({'labels':['test_sample.Case.test_body'],'module':'test_sample'}),
        capture_output=True,text=True,check=True)
    value=json.loads(proc.stdout)['test_sample.Case.test_body']
    assert value['completed'] and value['ids']==['test_sample.Case.test_body']
    assert value['setup_entry_point']==entry
    assert (tmp_path/'setup_used').read_text()==entry
    assert django_setup_entry_point([entry])==entry


@pytest.mark.parametrize('source,reason', [
    ('def unknown(): pass\n','Unsupported Django runtests setup API'),
    ('def setup_run_tests(unrecognized_required): pass\n','Unsupported Django setup parameters'),
    ('def setup_run_tests(verbosity, start_at, start_after, test_labels=None):\n raise RuntimeError("bootstrap broke")\n','bootstrap broke'),
])
def test_unsupported_or_broken_setup_fails_closed_with_reason(tmp_path, source, reason):
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/runtests.py').write_text(source)
    proc=subprocess.run([sys.executable,'-c',_DJANGO_COLLECT],cwd=tmp_path,env=clean_env(),
        input=json.dumps({'labels':['sample.Case.test_body'],'module':'sample'}),
        capture_output=True,text=True,check=True)
    value=json.loads(proc.stdout)['sample.Case.test_body']
    assert not value['completed'] and value['collection_status']=='COLLECTION_ERROR'
    assert value['ids']==[] and reason in value['message']


def test_bootstrap_capability_choice_is_closed_and_historical_syntax_supported():
    assert django_setup_entry_point(['setup','setup_run_tests'])=='setup'
    with pytest.raises(ValueError,match='Unsupported'):
        django_setup_entry_point(['setup_collect_tests'])
    ast.parse(_DJANGO_COLLECT,feature_version=(3,6))
