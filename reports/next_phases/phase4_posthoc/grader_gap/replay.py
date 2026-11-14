#!/usr/bin/env python3
"""Opt-in, one-test-at-a-time official SWE-bench 5.0.2 diagnostic replay.

Never runs the benchmark suite or modifies the executor/sealed artifacts.
Raw logs go only to ignored runs/phase4_grader_gap. Installed harness files
must match distribution RECORD. The frozen candidate, not the possibly
mismatched historical grader candidate, is used in every replay.
"""
import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / 'runs/phase4_grader_gap'
OLD = Path('/home/sankalp/projects/cis695-agent-reliability')
RUN = ROOT / 'runs/phase4_v4_attempt4_20261109T185713Z'
TARGETS = [
 ('pylint-dev__pylint-6528','tests/lint/unittest_lint.py::test_custom_should_analyze_file'),
 ('pylint-dev__pylint-6528','tests/lint/unittest_lint.py::test_multiprocessing[1]'),
 ('pylint-dev__pylint-6528','tests/lint/unittest_lint.py::test_multiprocessing[2]'),
 ('pylint-dev__pylint-6528','tests/test_self.py::TestRunTC::test_jobs_score'),
 ('pylint-dev__pylint-7277','tests/test_self.py::TestRunTC::test_jobs_score'),
 ('django__django-13297','tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning'),
]
# Python 3.6 compatible inside the oldest image. No full environment dump.
PROBE = r'''
import os,sys,json,warnings,importlib
r={'os_cpu_count':os.cpu_count(),'affinity_count':len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'PYTHONHASHSEED':os.environ.get('PYTHONHASHSEED'),'PYTHONWARNINGS':os.environ.get('PYTHONWARNINGS'),'sys_warnoptions':sys.warnoptions,'warning_filters':[repr(x) for x in warnings.filters],'python':sys.version,'cgroup':{}}
for p in ['/sys/fs/cgroup/cpu/cpu.shares','/sys/fs/cgroup/cpu.shares','/sys/fs/cgroup/cpu/cpu.cfs_quota_us','/sys/fs/cgroup/cpu/cpu.cfs_period_us','/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.weight']:
 try:
  with open(p) as f:r['cgroup'][p]=f.read().strip()
 except (IOError,OSError):pass
try:
 m=importlib.import_module('pylint.lint.run');r['pylint_cpu_count']=m._cpu_count();r['pylint_query_cpu']=m._query_cpu()
except ImportError:pass
print('PHASE4_GAP_ENV='+json.dumps(r,sort_keys=True))
'''

def sha(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check_harness():
 import base64
 d=importlib.metadata.distribution('swebench')
 assert d.version=='5.0.2'
 files=['swebench/harness/docker_utils.py','swebench/harness/grading.py','swebench/harness/log_parsers/python.py','swebench/harness/run_evaluation.py','swebench/harness/utils.py','swebench/types.py']
 out=[]
 for f in d.files:
  if str(f) in files:
   p=d.locate_file(f);h=hashlib.sha256(p.read_bytes())
   assert f.hash.mode=='sha256' and base64.urlsafe_b64encode(h.digest()).decode().rstrip('=')==f.hash.value
   out.append({'file':str(f),'sha256':h.hexdigest(),'matches_distribution_RECORD':True})
 assert len(out)==len(files)
 (RAW/'harness_distribution.json').write_text(json.dumps({'version':d.version,'module_checks':out},indent=2)+'\n')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
 if not args.execute:ap.error('Use --execute for the twelve explicitly scoped single-test replays.')
 # The seal verifier checks both the file set and every hash before new reads.
 sys.path.insert(0,str(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal'))
 import compute_seal
 compute_seal.verify_run()
 check_harness()
 import docker
 import swebench.harness.run_evaluation as harness
 from swebench.harness.utils import make_test_spec
 client=docker.from_env(timeout=1800)
 harness.RUN_EVALUATION_LOG_DIR=RAW/'harness_logs'
 rows={r['instance_id']:r for r in json.loads((RAW/'oracle_inputs.json').read_text())['rows']}
 pins={r['instance_id']:r for r in json.loads((RUN/'plan.json').read_text())['task_specs']}
 records=[]
 for n,(iid,target) in enumerate(TARGETS,1):
  source='main_50_a' if iid.startswith('pylint') else 'main_50_b'
  patch=OLD/'runs'/source/'tasks'/iid/'patch.diff'
  assert sha(patch)==pins[iid]['patch_sha256']
  image=pins[iid]['image_id'];client.images.get(image) # Missing image stops; no pulls.
  row=rows[iid]
  command=('pytest -rA '+shlex.quote(target)) if iid.startswith('pylint') else './tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 generic_views.test_base.DeprecationTests.test_template_params_warning'
  for with_patch in (True,False):
   variant='with_test_patch' if with_patch else 'without_test_patch'
   runid='phase4-gap-%02d-%s'%(n,variant.replace('_','-'))
   dest=harness.RUN_EVALUATION_LOG_DIR/runid/'phase4_grader_gap'/iid
   assert not dest.exists(), 'Refusing to overwrite existing diagnostic logs: '+str(dest)
   script=row['eval_script']
   if not with_patch:
    script,count=re.subn(r"git apply -v - <<'([^']+)'\n.*?\n\1\n",'',script,flags=re.S)
    assert count==1
   start=script.index(": '>>>>> Start Test Output'")
   end=script.index(": '>>>>> End Test Output'",start)
   script=script[:start]+'python -c '+shlex.quote(PROBE)+'\n'+": '>>>>> Start Test Output'\n"+command+'\n'+script[end:]
   spec=dataclasses.replace(make_test_spec(dict(row,eval_script=script)),image=image)
   print('START',n,variant,iid,target,flush=True)
   returned=harness.run_instance(spec,{'instance_id':iid,'model_name_or_path':'phase4_grader_gap','model_patch':patch.read_text()},client,runid,timeout=300)
   assert returned is not None, 'Harness did not produce a report'
   output=(dest/'test_output.txt').read_text(errors='replace')
   envs=re.findall(r'^PHASE4_GAP_ENV=(.*)$',output,re.M)
   assert len(envs)==1
   test_region=output.split('>>>>> Start Test Output',1)[-1].split('>>>>> End Test Output',1)[0]
   if re.search(r'\b[1-9]\d* skipped\b',test_region):status='SKIPPED'
   elif re.search(r'\b[1-9]\d* passed\b',test_region) or re.search(r'^OK\s*$',test_region,re.M):status='PASS'
   elif re.search(r'\b[1-9]\d* failed\b',test_region) or 'FAILED (' in test_region:status='FAIL'
   else:raise AssertionError('No unambiguous single-test status: '+str(dest))
   rec={'task':iid,'test':target,'variant':variant,'status':status,'image_id':image,'candidate_sha256':sha(patch),'command':command,'environment':json.loads(envs[0]),'log_dir':str(dest.relative_to(ROOT)),'test_output_sha256':sha(dest/'test_output.txt'),'eval_script_sha256':sha(dest/'eval.sh'),'report_sha256':sha(dest/'report.json')}
   records.append(rec)
   (RAW/'replay_results.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
   print('DONE',n,variant,status,'pylint_cpu=',rec['environment'].get('pylint_cpu_count'),flush=True)
 # Resource-only probes: same images and executor resource flags, no tests.
 probes=[]
 for iid in dict(TARGETS):
  image=pins[iid]['image_id']
  c=client.containers.create(image=image,command='tail -f /dev/null',detach=True,cpu_shares=2048,network_disabled=True)
  try:
   c.start();c.reload()
   code,out=c.exec_run(['/bin/bash','-lc','source /opt/miniconda3/bin/activate && conda activate testbed && cd /testbed && python -c '+shlex.quote(PROBE)])
   assert code==0,(iid,out[-1000:])
   env=json.loads(re.search(rb'^PHASE4_GAP_ENV=(.*)$',out,re.M)[1])
   probes.append({'task':iid,'image_id':image,'profile':'executor','CpuShares':c.attrs['HostConfig']['CpuShares'],'NetworkMode':c.attrs['HostConfig']['NetworkMode'],'environment':env})
   (RAW/'executor_environment.json').write_text(json.dumps(probes,indent=2,sort_keys=True)+'\n')
   print('ENV',iid,env.get('pylint_cpu_count'),flush=True)
  finally:c.remove(force=True)
 assert len(records)==12
 print('COMPLETE: 12 single-test runs; 3 resource-only probes',flush=True)

if __name__=='__main__':main()
