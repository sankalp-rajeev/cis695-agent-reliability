"""Historical pytest IDs exercise the actual collection and execution paths."""
import json
import subprocess
import sys

from reliability.env import clean_env
from reliability.verifier.collection import _PYTEST_PLUGIN
from reliability.verifier.container import _BATCH_DRIVER, run_from_capture
from reliability.verifier.node_ids import normalize_pytest_id
from reliability.verifier.regression import TestStatus
from reliability.verifier.selection import TestRunner


def test_pytest3_raw_nodeids_in_collection_and_execution(tmp_path):
    # Fixture strings include old instance IDs; modern pytest cannot emit these
    # naturally, so alter item.nodeid at the hook immediately before our receipt.
    (tmp_path/'test_real.py').write_text('class TestReal:\n    def test_body(self): raise AssertionError("body ran")\n')
    (tmp_path/'conftest.py').write_text('import pytest\n@pytest.hookimpl(tryfirst=True)\ndef pytest_collection_finish(session):\n    for item in session.items:\n        item._nodeid = item.nodeid.replace("::TestReal::", "::TestReal::()::")\n')
    plugin=tmp_path/'verifier_collect_plugin.py';plugin.write_text(_PYTEST_PLUGIN)
    env=clean_env();env['VERIFIER_COLLECTION_RECEIPT']=str(tmp_path/'nodes.json')
    proc=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q','-p','verifier_collect_plugin','test_real.py'],cwd=tmp_path,env=env,capture_output=True,text=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    selected='test_real.py::TestReal::test_body'
    assert json.loads((tmp_path/'nodes.json').read_text())['ids']==[selected]
    raw='test_real.py::TestReal::()::test_body PASSED\n'
    run=run_from_capture(TestRunner('pytest','fixture'),(selected,),runner_log=raw.encode(), events=(
        {'event':'start','batch':0,'offset':0},
        {'event':'end','batch':0,'offset':len(raw.encode()),'split':True,'observed_ids':[selected]},
        {'event':'complete'}))
    assert run.by_id()[selected].status is TestStatus.PASSED
    namespace={'__file__':str(tmp_path/'driver.py')}
    # The batch driver's shared parser must normalize too, before its seen() map.
    exec(_BATCH_DRIVER.split("import collections, json, os, pathlib")[0],namespace)
    assert namespace['mapping_for']((selected,),'pytest')('test_real.py::TestReal::()::test_body')==[selected]


def test_parameter_payload_and_trailing_instance():
    assert normalize_pytest_id('t.py::Test::()')=='t.py::Test'
    assert normalize_pytest_id('t.py::test_p[é::()::雪]::()')=='t.py::test_p[é::()::雪]'
    selected='t.py::Test::test_p[é::()::雪]'
    raw='t.py::Test::()::test_p[é::()::雪] PASSED\n'
    run=run_from_capture(TestRunner('pytest','fixture'),(selected,),runner_log=raw.encode())
    assert run.by_id()[selected].status is TestStatus.PASSED
