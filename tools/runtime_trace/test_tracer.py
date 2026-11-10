"""Synthetic verification; never imports or executes benchmark source."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('phase6_driver',HERE/'driver.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)


def exercise(tmp_path,source,enabled=True):
 (tmp_path/'example.py').write_text(source)
 definitions=driver.functions(source,'example.py')
 changed=next(d for d in definitions if d['name']=='changed')
 test=next(d for d in definitions if d['name']=='test_case')
 config={'source_root':str(tmp_path),'test_id':'example.py::test_case','tree':'synthetic','test_function':test,'changed_functions':[dict(changed,id='changed')]}
 (tmp_path/'config.json').write_text(json.dumps(config));(tmp_path/'output').mkdir()
 env=dict(os.environ,PYTHONPATH=str(HERE),RUNTIME_TRACE_ENABLE='1' if enabled else '0',RUNTIME_TRACE_CONFIG=str(tmp_path/'config.json'),RUNTIME_TRACE_OUTPUT=str(tmp_path/'output'))
 result=subprocess.run([sys.executable,str(tmp_path/'example.py')],env=env,capture_output=True,text=True)
 events=[json.loads(l) for p in (tmp_path/'output').glob('*.jsonl') for l in p.read_text().splitlines()]
 return result,events


def test_first_entry_stack_hops_and_no_duplicate(tmp_path):
 result,events=exercise(tmp_path,'def changed():\n    return 7\ndef wrapper():\n    return changed()\ndef test_case():\n    assert wrapper()==7\n    assert wrapper()==7\ntest_case()\n')
 assert result.returncode==0 and result.stdout==''
 entries=[e for e in events if e['event']=='entry']
 assert len(entries)==2
 under=next(e for e in entries if e['phase']=='first_under_test')
 assert under['hops']==2
 assert [f['name'] for f in under['stack'][-3:]]==['test_case','wrapper','changed']
 assert not [e for e in events if e['event']=='trace_error']


def test_setup_entry_has_no_fabricated_test_hop(tmp_path):
 result,events=exercise(tmp_path,'def changed():\n    return 1\ndef test_case():\n    changed()\nchanged()\ntest_case()\n')
 assert result.returncode==0
 entries=[e for e in events if e['event']=='entry']
 first=next(e for e in entries if e['phase']=='first_any')
 under=next(e for e in entries if e['phase']=='first_under_test')
 assert first['hops'] is None and first['test_frame_index'] is None
 assert under['hops']==1


def test_disabled_does_not_install_trace_or_change_result(tmp_path):
 result,events=exercise(tmp_path,'import sys\ndef changed():\n    return 1\ndef test_case():\n    assert sys.gettrace() is None\n    print(changed())\ntest_case()\n',False)
 assert result.returncode==0 and result.stdout=='1\n' and events==[]


def test_exception_is_not_swallowed(tmp_path):
 result,events=exercise(tmp_path,'def changed():\n    raise ValueError("sentinel")\ndef test_case():\n    changed()\ntest_case()\n')
 assert result.returncode!=0 and 'ValueError: sentinel' in result.stderr
 assert any(e['event']=='entry' for e in events)


def test_fork_gets_distinct_process_receipts(tmp_path):
 result,events=exercise(tmp_path,'import os\ndef changed():\n    return 1\ndef test_case():\n    pid=os.fork()\n    if pid==0:\n        changed()\n        os._exit(0)\n    os.waitpid(pid,0)\n    changed()\ntest_case()\n')
 assert result.returncode==0
 entries=[e for e in events if e['event']=='entry' and e['phase']=='first_under_test']
 assert len({e['pid'] for e in entries})==2
 assert {e['fork_after_install'] for e in entries}=={False,True}


def test_python35_grammar_and_decorated_function_mapping():
 for minor in range(5,12):
  ast.parse((HERE/'sitecustomize.py').read_text(),feature_version=(3,minor))
 definitions=driver.functions('class A:\n    @property\n    def value(self):\n        return 1\n','a.py')
 assert definitions[0]['qualname']=='A.value'
 assert definitions[0]['decorator_start']==2 and definitions[0]['start']==3 and definitions[0]['end']==4


def test_thread_blind_spot_has_receipt_without_fabricated_entry(tmp_path):
 result,events=exercise(tmp_path,'import threading\ndef changed():\n    return 1\ndef test_case():\n    worker=threading.Thread(target=changed)\n    worker.start()\n    worker.join()\ntest_case()\n')
 assert result.returncode==0
 assert any(e['event']=='test_enter' for e in events)
 assert any(e['event']=='thread_start' for e in events)
 assert not any(e['event']=='entry' for e in events)
 assert next(e for e in events if e['event']=='finished')['hook_active_at_finish']


def test_summary_does_not_hide_perturbation_or_missing_results():
 sys.path.insert(0,str(HERE))
 import summarize
 assert summarize.pair_status({'outcome':'PASSED','returncode':0},{'outcome':'FAILED','returncode':1})=='TRACE_PERTURBS'
 assert summarize.pair_status({'outcome':'PASSED','returncode':0},{'outcome':'PASSED','returncode':1})=='TRACE_PERTURBS'
 assert summarize.pair_status({'outcome':'NO_RECORDED_RESULT'},{'outcome':'NO_RECORDED_RESULT'})=='UNVERIFIED'
 assert summarize.pair_status({'outcome':'FAILED','returncode':1},{'outcome':'FAILED','returncode':1})=='MATCH'


def test_static_reachability_uses_resolved_edges_and_keeps_unbounded_distance():
 sys.path.insert(0,str(HERE))
 import summarize
 nodes={str(i):{'id':str(i),'path':'x.py','qualname':name} for i,name in enumerate(['test_case','a','b','c','changed','ambiguous'])}
 edges=[{'caller':str(i),'targets':[str(i+1)],'status':'resolved'} for i in range(4)]
 edges.append({'caller':'0','targets':['5'],'status':'ambiguous'})
 comparison=summarize.Comparison('synthetic',{}, {'nodes':nodes,'edges':edges})
 assert comparison.distance('x.py::test_case',{'path':'x.py','qualname':'changed'})==4
 assert comparison.distance('x.py::test_case',{'path':'x.py','qualname':'ambiguous'}) is None
 assert comparison.distance('x.py::test_case',{'path':'x.py','qualname':'patch_only'}) is None
