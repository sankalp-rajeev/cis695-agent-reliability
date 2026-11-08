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
