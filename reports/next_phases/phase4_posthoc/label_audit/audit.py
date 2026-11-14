#!/usr/bin/env python3
"""Post-seal label-integrity audit. Never writes labels or sealed/executor files.

Default: regenerate deterministic reports from archived and audited evidence.
--inventory: inventory only, writes a snapshot under ignored runs/.
--grade: opt-in official 5.0.2 full-task grades of non-SUPPORTED candidates.
The original default-environment grade defines B. CPU-2048 is a separate
resource sensitivity, not a replacement for the primary audited grade.
"""
import argparse
import base64
import collections
import csv
import dataclasses
import hashlib
import importlib.metadata
import io
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RAW = ROOT/'runs/phase4_label_audit'
OLD = Path('/home/sankalp/projects/cis695-agent-reliability')
SIDECARS = ROOT/'reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z'
sys.path.insert(0,str(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal'))
import compute_seal
from swebench.harness.utils import make_test_spec
from swebench.harness.log_parsers import PARSER_REGISTRY
from swebench.harness.grading import _resolve_case

RUN=compute_seal.RUN
LABELS_SHA='cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990'
PREVIOUS_ANALYSIS_SHA='7227e3830b5341f82478746146ff9ce744407ec3bb5a799e7c916d4d5b31b9bb'
DATASET=Path('/home/sankalp/.cache/huggingface/hub/datasets--SWE-bench--SWE-bench_Verified/blobs/030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25')
DATASET_SHA=DATASET.name
DATASET_COLUMNS=['instance_id','repo','base_commit','version','test_patch','FAIL_TO_PASS','PASS_TO_PASS','eval_script','image','log_parser','eval_type']
PASSING={'PASSED','XFAIL'}
CLASSES=['SUPPORTED','SKIP_ONLY','BINDING_MISMATCH','NO_GRADER_RECORD']
POLICIES=compute_seal.POLICIES
VERDICTS=['PASS','FAIL','REGRESSION_ERROR','INCOMPLETE','NOT_AVAILABLE']
INPUTS={}


def sha(b):return hashlib.sha256(b).hexdigest()


def read(p):
 p=Path(p);b=p.read_bytes();INPUTS[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(b);return b


def load(p):return json.loads(read(p))


def write_json(p,value):p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def preconditions():
 _,verification=compute_seal.verify_run()
 assert subprocess.check_output(['git','rev-parse','phase4-run-sealed^{}'],cwd=ROOT,text=True).strip()=='e40d60afac6534bba03a20168ea681fca24228af'
 assert sha(read(SIDECARS/'correctness_sidecar.json'))==LABELS_SHA
 assert sha(read(DATASET))==DATASET_SHA
 assert importlib.metadata.version('swebench')=='5.0.2'
 return verification


def distribution():
 d=importlib.metadata.distribution('swebench');checks=[]
 wanted={'swebench/harness/run_evaluation.py','swebench/harness/grading.py','swebench/harness/docker_utils.py','swebench/harness/utils.py','swebench/harness/log_parsers/python.py','swebench/types.py'}
 for f in d.files:
  if str(f) in wanted:
   b=d.locate_file(f).read_bytes();assert f.hash.mode=='sha256'
   assert base64.urlsafe_b64encode(hashlib.sha256(b).digest()).decode().rstrip('=')==f.hash.value
   checks.append({'file':str(f),'sha256':sha(b),'matches_distribution_RECORD':True})
 assert len(checks)==len(wanted)
 return {'version':d.version,'module_checks':checks}


def dataset():
 import pyarrow.parquet as pq
 return {r['instance_id']:r for r in pq.read_table(DATASET,columns=DATASET_COLUMNS).to_pylist()}


def native_status(test,sm,text,iid,source_scopes):
 key=_resolve_case(test,sm)
 if key is not None:return sm[key],{'method':'official 5.0.2 parser','parsed_key':key}
 # -rA summarizes native skips by source file/line, without node IDs.
 # Bind those five Pylint nodes using the previously verified patched-source
 # spans, rather than calling an absent parser key a failed assertion.
 if iid in source_scopes:
  scope=next((x for x in source_scopes[iid]['targets'] if x['test']==test),None)
  if scope:
   file=test.split('::')[0];line=scope['after']['first_line']
   pattern=r'^SKIPPED \[(\d+)\] '+re.escape(file)+':'+str(line)+r': (.*)$'
   matches=list(re.finditer(pattern,text,re.M))
   if matches:
    assert len(matches)==1
    m=matches[0]
    return 'SKIPPED',{'method':'native pytest skip summary bound to patched source span','summary':m[0],'log_line':text[:m.start()].count('\n')+1,'source_scope':scope}
 return 'ABSENT',{'method':'not present in native parser map or source-bound skip summary'}


def inventory(rows,pins,labels,bindings):
 previous=load(ROOT/'reports/next_phases/phase4_posthoc/grader_gap/evidence.json')
 expected_previous=subprocess.check_output(['git','show','b84354ce2e90dedf4b71861d7d0bb1d388710a4d:reports/next_phases/phase4_posthoc/grader_gap/evidence.json'],cwd=ROOT)
 assert sha(expected_previous)==sha((ROOT/'reports/next_phases/phase4_posthoc/grader_gap/evidence.json').read_bytes())
 provenance=load(SIDECARS/'sidecar_provenance.json')
 pinned_csv=read(SIDECARS/'correctness_source_pinned.csv')
 assert sha(pinned_csv)==provenance['label_source_pinned_sha256']
 csv_labels={r['instance_id']:r for r in csv.DictReader(io.StringIO(pinned_csv.decode()))}
 source_scopes=previous['test_patch_comparisons']
 records=[]
 for binding in sorted(bindings,key=lambda x:x['instance_id']):
  iid=binding['instance_id'];label='correct' if labels[iid]['correctness']=='right' else 'incorrect'
  source=binding['source_run_final_csv'];task=OLD/'runs'/source/'tasks'/iid
  assert csv_labels[iid]['oracle']==('resolved' if label=='correct' else 'unresolved')
  assert csv_labels[iid]['source_run']==source
  frozen=read(task/'patch.diff')
  assert sha(frozen)==pins[iid]['patch_sha256']==binding['patch_sha256']==labels[iid]['patch_sha256']
  rec={'task':iid,'original_label':label,'source_run':source,'label_source_pinned_csv':str(SIDECARS/'correctness_source_pinned.csv'),'label_sidecar':str(SIDECARS/'correctness_sidecar.json'),'frozen_patch_path':str(task/'patch.diff'),'frozen_patch_sha256':sha(frozen),'frozen_patch_bytes':len(frozen),'frozen_image_id':pins[iid]['image_id'],'classification':None,'missing_records':[]}
  oracle_path=task/'oracle_record.json'
  if not oracle_path.exists():
   rec['missing_records'].append(str(oracle_path));rec['classification']='NO_GRADER_RECORD';records.append(rec);continue
  oracle=load(oracle_path);rec['oracle_record_path']=str(oracle_path);rec['oracle_declared_candidate_sha256']=oracle.get('patch_sha256')
  report_path=Path(oracle['report_file']);log=report_path.parent
  rec['grader_directory']=str(log);rec['label_report_path']=str(report_path)
  required=[report_path,log/'run_instance.log',log/'test_output.txt']
  rec['missing_records']=[str(p) for p in required if not p.exists()]
  if rec['missing_records']:
   rec['classification']='NO_GRADER_RECORD';records.append(rec);continue
  report=load(report_path)[iid];text=read(log/'test_output.txt').decode(errors='replace');runlog=read(log/'run_instance.log').decode(errors='replace')
  patch_path=log/'patch.diff'
  if patch_path.exists():
   applied=read(patch_path);rec['applied_patch_evidence']='grader-directory patch.diff'
  else:
   # Standard run_instance logs put the exact pre-test git diff between these
   # two timestamped messages. No trailing-newline normalization is performed.
   match=re.search(r' - INFO - Git diff before:\n(.*?)(?=\n\d{4}-\d\d-\d\d .* - INFO - )',runlog,re.S)
   if match:
    applied=match[1].encode();rec['applied_patch_evidence']='run_instance.log Git diff before'
   else:
    rec['missing_records'].append(str(patch_path)+' and extractable applied diff');rec['classification']='NO_GRADER_RECORD';records.append(rec);continue
  rec.update({'applied_patch_sha256':sha(applied),'applied_patch_bytes':len(applied),'binding_matches':sha(applied)==sha(frozen),'patch_present_in_run_log':applied.decode(errors='replace').strip() in runlog,'application_success_logged':'Applied Patch' in runlog,'grader_report_resolved':bool(report.get('resolved')),'label_attached_to':'matching frozen/applied candidate' if sha(applied)==sha(frozen) else 'linked archived report describes applied candidate; sidecar/oracle metadata declares frozen hash but applied bytes differ'})
  assert report.get('resolved')==(label=='correct'),(iid,'sidecar/report disagree')
  assert oracle.get('resolved')==report.get('resolved')
  assert oracle['patch_sha256'].removeprefix('sha256:')==sha(frozen)
  spec=make_test_spec(rows[iid]);sm=PARSER_REGISTRY[spec.log_parser](text,spec)
  groups={}
  for group in ['FAIL_TO_PASS','PASS_TO_PASS']:
   g=report['tests_status'][group];expected=getattr(spec,group)
   assert set(expected)==set(g['success']+g['failure']),(iid,group,'reference-list mismatch')
   non=[]
   for test in expected:
    status,proof=native_status(test,sm,text,iid,source_scopes)
    if status not in PASSING:
     non.append({'test':test,'native_status':status,'archived_report_bucket':'failure' if test in g['failure'] else 'success','evidence':proof})
   groups[group]={'expected_count':len(expected),'report_success_count':len(g['success']),'report_failure_count':len(g['failure']),'not_passing':non}
  rec['FAIL_TO_PASS']=groups['FAIL_TO_PASS']
  pp=groups['PASS_TO_PASS'];rec['PASS_TO_PASS']=dict(pp,by_native_status={
   'FAILED_ERROR':[x for x in pp['not_passing'] if x['native_status'] in ['FAILED','ERROR']],
   'SKIPPED':[x for x in pp['not_passing'] if x['native_status']=='SKIPPED'],
   'absent':[x for x in pp['not_passing'] if x['native_status']=='ABSENT'],
   'other':[x for x in pp['not_passing'] if x['native_status'] not in ['FAILED','ERROR','SKIPPED','ABSENT']]})
  rec['report_failure_lists']={g:report['tests_status'][g]['failure'] for g in ['FAIL_TO_PASS','PASS_TO_PASS']}
  if not rec['binding_matches']:rec['classification']='BINDING_MISMATCH'
  elif label=='incorrect':
   if rec['FAIL_TO_PASS']['not_passing'] or rec['PASS_TO_PASS']['by_native_status']['FAILED_ERROR']:rec['classification']='SUPPORTED'
   elif pp['not_passing'] and all(x['native_status'] in ['SKIPPED','ABSENT'] for x in pp['not_passing']):rec['classification']='SKIP_ONLY'
   else:raise AssertionError((iid,'Incorrect label has no registered basis'))
  else:
   assert not groups['FAIL_TO_PASS']['not_passing'] and not pp['not_passing'],(iid,'correct label has nonpassing tests')
   rec['classification']='SUPPORTED'
  records.append(rec)
 assert len(records)==83
 return records


def run_grades(records,rows,pins):
 import docker
 import swebench.harness.run_evaluation as harness
 receipt=distribution();client=docker.from_env(timeout=1800)
 harness.RUN_EVALUATION_LOG_DIR=RAW/'harness_logs'
 # The default branch delegates unchanged. For the resource sensitivity,
 # update only CpuShares before start; equivalent to docker --cpu-shares 2048.
 original_create=harness.create_container
 grades=[]
 existing=load(RAW/'audited_grades.json') if (RAW/'audited_grades.json').exists() else []
 jobs=[(r,p) for r in records if r['classification']!='SUPPORTED' for p in (['default','cpu2048'] if r['classification']=='SKIP_ONLY' else ['default'])]
 for n,(r,profile) in enumerate(jobs,1):
  iid=r['task'];runid='phase4-label-audit-'+profile
  dest=harness.RUN_EVALUATION_LOG_DIR/runid/'label_audit'/iid
  prior=next((g for g in existing if g['task']==iid and g['profile']==profile),None)
  if prior:
   assert prior['candidate_sha256']==r['frozen_patch_sha256']
   for name,h in prior['artifact_sha256'].items():assert sha(read(dest/name))==h
   grades.append(prior);print('CACHED',n,len(jobs),iid,profile,flush=True);continue
  assert not dest.exists(),'Refusing to overwrite an incomplete grade: '+str(dest)
  image=pins[iid]['image_id'];client.images.get(image) # Stop if absent, never pull.
  host_config={}
  def create(spec,cl,run_id,logger):
   container=original_create(spec,cl,run_id,logger)
   if profile=='cpu2048':container.update(cpu_shares=2048)
   container.reload();h=container.attrs['HostConfig']
   host_config.update({k:h.get(k) for k in ['CpuShares','CpuQuota','CpuPeriod','NanoCpus','CpusetCpus','NetworkMode']})
   return container
  harness.create_container=create
  # Keep the dataset's entire eval script, all F2P and all P2P lists. Only
  # replace the mutable image tag by the sealed immutable image identity.
  spec=dataclasses.replace(make_test_spec(rows[iid]),image=image)
  patch=read(r['frozen_patch_path']);assert sha(patch)==r['frozen_patch_sha256']
  print('START',n,'/',len(jobs),iid,profile,'F2P',len(spec.FAIL_TO_PASS),'P2P',len(spec.PASS_TO_PASS),flush=True)
  returned=harness.run_instance(spec,{'instance_id':iid,'model_name_or_path':'label_audit','model_patch':patch.decode()},client,runid,timeout=1800)
  harness.create_container=original_create
  # A failed/timed-out invocation is recorded as no usable audited grade;
  # it does not silently become an incorrect patch label.
  artifacts={p.name:sha(read(p)) for p in dest.iterdir() if p.is_file()}
  report=load(dest/'report.json')[iid] if (dest/'report.json').exists() else None
  log=(dest/'run_instance.log').read_text(errors='replace') if (dest/'run_instance.log').exists() else ''
  usable=bool(report and 'tests_status' in report and 'Applied Patch' in log)
  grade={'task':iid,'profile':profile,'candidate_sha256':sha(patch),'image_id':image,'full_task_F2P_count':len(spec.FAIL_TO_PASS),'full_task_P2P_count':len(spec.PASS_TO_PASS),'host_config':host_config,'report':report,'audited_grade':('correct' if report['resolved'] else 'incorrect') if usable else None,'usable':usable,'log_dir':str(dest.relative_to(ROOT)),'artifact_sha256':artifacts,'harness_distribution':receipt,'timeout_seconds':1800,'returned_report':returned is not None}
  grades.append(grade);write_json(RAW/'audited_grades.json',grades)
  print('DONE',n,'/',len(jobs),iid,profile,grade['audited_grade'],flush=True)
 assert len(grades)==len(jobs)
 print('COMPLETE',len(grades),'full-task audited grades',flush=True)


def proportion(k,n):
 from scipy.stats import beta
 assert 0<=k<=n
 return {'count':k,'denominator':n,'defined':bool(n),'fraction':k/n if n else None,'ci95':[0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1.0 if k==n else float(beta.ppf(.975,k+1,n-k))] if n else None}


def evaluate(verdicts,labels):
 matrix={v:{'correct':0,'incorrect':0} for v in VERDICTS}
 for iid,label in labels.items():matrix[verdicts[iid]][label]+=1
 metrics={};nr=sum(l=='correct' for l in labels.values());nw=sum(l=='incorrect' for l in labels.values())
 for name,positive in [('primary_FAIL_only',{'FAIL'}),('secondary_FAIL_plus_REGRESSION_ERROR',{'FAIL','REGRESSION_ERROR'})]:
  decisions={'PASS'}|positive
  detected=[i for i,l in labels.items() if l=='incorrect' and verdicts[i] in positive]
  false=[i for i,l in labels.items() if l=='correct' and verdicts[i] in positive]
  missed=[i for i,l in labels.items() if l=='incorrect' and verdicts[i]=='PASS']
  nvwrong=sum(l=='incorrect' and verdicts[i] in decisions for i,l in labels.items());nvright=sum(l=='correct' and verdicts[i] in decisions for i,l in labels.items())
  metrics[name]={'detection_all_incorrect':proportion(len(detected),nw),'detection_verdicted_incorrect':proportion(len(detected),nvwrong),'false_alarm_all_correct':proportion(len(false),nr),'false_alarm_verdicted_correct':proportion(len(false),nvright),'missed_all_incorrect':proportion(len(missed),nw),'missed_verdicted_incorrect':proportion(len(missed),nvwrong),'detected_tasks':detected,'false_alarm_tasks':false,'missed_tasks':missed}
 return {'label_counts':{'correct':nr,'incorrect':nw,'excluded':83-len(labels)},'verdict_by_label':matrix,'metrics':metrics}


def format_p(p):
 if not p['denominator']:return f"{p['count']}/0 (undefined)"
 lo,hi=p['ci95']
 return f"{p['count']}/{p['denominator']} = {100*p['fraction']:.2f}% [{100*lo:.2f}%, {100*hi:.2f}%]"


def csv_write(name,rows,fields=None):
 s=io.StringIO();writer=csv.DictWriter(s,fieldnames=fields or list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows);(OUT/name).write_text(s.getvalue())


def report(records,verification):
 previous_bytes=read(ROOT/'reports/next_phases/phase4_posthoc/analysis.json')
 assert sha(previous_bytes)==PREVIOUS_ANALYSIS_SHA
 previous=json.loads(previous_bytes)
 sealed_bytes=read(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal/results.json')
 assert sha(sealed_bytes)=='94786d24848b9707eaeb73dd353affd108d95d50ddc773d0f23ed539341d7530'
 sealed=json.loads(sealed_bytes)
 verdicts={p:{r['task']:r['policies'][p] for r in sealed['per_task']} for p in POLICIES}
 original={r['task']:r['original_label'] for r in records}
 grades=load(RAW/'audited_grades.json');expected_jobs={(r['task'],p) for r in records if r['classification']!='SUPPORTED' for p in (['default','cpu2048'] if r['classification']=='SKIP_ONLY' else ['default'])}
 assert {(g['task'],g['profile']) for g in grades}==expected_jobs
 assert len(grades)==len(expected_jobs)
 rows=dataset();grade_by_key={}
 source_scopes=load(ROOT/'reports/next_phases/phase4_posthoc/grader_gap/evidence.json')['test_patch_comparisons']
 for g in grades:
  iid=g['task'];folder=ROOT/g['log_dir']
  for name,expected in g['artifact_sha256'].items():assert sha(read(folder/name))==expected,(iid,name)
  r=next(r for r in records if r['task']==iid)
  assert g['candidate_sha256']==r['frozen_patch_sha256']
  if 'patch.diff' in g['artifact_sha256']:assert g['artifact_sha256']['patch.diff']==g['candidate_sha256']
  else:assert not g['usable']
  if g['host_config']:assert g['host_config']['CpuShares']==(2048 if g['profile']=='cpu2048' else 0)
  else:assert not g['usable']
  spec=dataclasses.replace(make_test_spec(rows[iid]),image=g['image_id'])
  if 'eval.sh' in g['artifact_sha256']:assert sha(spec.eval_script.encode())==g['artifact_sha256']['eval.sh'],iid
  else:assert not g['usable']
  assert g['full_task_F2P_count']==len(spec.FAIL_TO_PASS) and g['full_task_P2P_count']==len(spec.PASS_TO_PASS)
  if g['usable']:
   rr=g['report']
   for group in ['FAIL_TO_PASS','PASS_TO_PASS']:
    got=rr['tests_status'][group]
    assert sorted(got['success']+got['failure'])==sorted(getattr(spec,group)),(iid,group)
   assert g['audited_grade']==('correct' if rr['resolved'] else 'incorrect')
   text=read(folder/'test_output.txt').decode(errors='replace');sm=PARSER_REGISTRY[spec.log_parser](text,spec)
   native_nonpassing={}
   for group in ['FAIL_TO_PASS','PASS_TO_PASS']:
    native_nonpassing[group]=[]
    for test in getattr(spec,group):
     status,proof=native_status(test,sm,text,iid,source_scopes)
     if status not in PASSING:native_nonpassing[group].append({'test':test,'native_status':status,'evidence':proof})
   g['native_nonpassing_references']=native_nonpassing
   referenced={_resolve_case(t,sm) for t in spec.FAIL_TO_PASS+spec.PASS_TO_PASS}
   g['parser_FAILED_ERROR_outside_reference_lists']=[{'test':k,'native_status':v} for k,v in sm.items() if v in ['FAILED','ERROR'] and k not in referenced]
  grade_by_key[iid,g['profile']]=g
 audited={r['task']:r['original_label'] if r['classification']=='SUPPORTED' else grade_by_key[r['task'],'default']['audited_grade'] for r in records}
 audited={k:v for k,v in audited.items() if v is not None}
 # This extra projection uses only the two requested resource sensitivities.
 # It is explicitly not primary set B, which always uses default environment.
 cpu_labels=dict(audited)
 for r in records:
  if r['classification']=='SKIP_ONLY':
   grade=grade_by_key[r['task'],'cpu2048']['audited_grade']
   if grade is None:cpu_labels.pop(r['task'],None)
   else:cpu_labels[r['task']]=grade
 tables={name:{p:evaluate(verdicts[p],labelset) for p in POLICIES} for name,labelset in [('A_original',original),('B_audited_default',audited),('B_cpu2048_sensitivity',cpu_labels)]}
 metric_names=['detection_all_incorrect','detection_verdicted_incorrect','false_alarm_all_correct','false_alarm_verdicted_correct','missed_all_incorrect','missed_verdicted_incorrect']
 for p in POLICIES:
  assert tables['A_original'][p]['verdict_by_label']==previous['policies'][p]['verdict_by_label']
  for rule in ['primary_FAIL_only','secondary_FAIL_plus_REGRESSION_ERROR']:
   for m in metric_names:assert tables['A_original'][p]['metrics'][rule][m]==previous['policies'][p]['metrics'][rule][m],(p,rule,m)
 for labelset in tables.values():
  for table in labelset.values():
   n=sum(table['label_counts'][k] for k in ['correct','incorrect'])
   assert sum(sum(v.values()) for v in table['verdict_by_label'].values())==n
   for rule in table['metrics'].values():
    for m in metric_names:
     pr=rule[m];assert 0<=pr['count']<=pr['denominator']
     if pr['denominator']:
      # Independent exact-binomial inversion cross-check of beta quantiles.
      from scipy.stats import binomtest
      ci=binomtest(pr['count'],pr['denominator']).proportion_ci(confidence_level=.95,method='exact')
      assert abs(ci.low-pr['ci95'][0])<1e-10 and abs(ci.high-pr['ci95'][1])<1e-10
 changes=[{'task':iid,'A_original':original[iid],'B_audited_default':audited.get(iid,'excluded'),'classification':next(r['classification'] for r in records if r['task']==iid)} for iid in sorted(original) if original[iid]!=audited.get(iid)]
 counts={c:sum(r['classification']==c for r in records) for c in CLASSES}
 read(OUT/'audit.py')
 result={'scope':'Post-hoc label audit only. Original labels, policy verdicts, sealed results, executor, tags are immutable.','manifest_verification':verification,'classification_counts':counts,'all_tasks':records,'audited_grades':grades,'label_sets':{'A_original':original,'B_audited_default':audited,'B_cpu2048_sensitivity':cpu_labels},'label_set_definitions':{'A_original':'Original 69 correct / 14 incorrect labels, unchanged.','B_audited_default':'Original where SUPPORTED; fresh official default-environment grade elsewhere; exclude if no usable grade.','B_cpu2048_sensitivity':'B with only the two SKIP_ONLY labels taken from their fresh CPU-2048 grades; informational, not set B primary.'},'label_changes_A_to_B':changes,'tables':tables,'interval_method':'Exact two-sided 95% Clopper-Pearson beta quantiles; undefined when denominator=0.','conditional_denominator':'Primary: PASS+FAIL; secondary: PASS+FAIL+REGRESSION_ERROR. Denominators use each label set separately.','grader_semantics':'PASSED/XFAIL count as passing. Native SKIPPED is kept separate from absent parser entries using source-bound skip summaries. Audited labels follow official resolved, not a claim of semantic correctness.','harness_distribution':distribution(),'input_sha256':dict(sorted(INPUTS.items()))}
 write_json(OUT/'analysis.json',result)
 csvrows=[]
 for r in records:
  f=r.get('FAIL_TO_PASS',{});p=r.get('PASS_TO_PASS',{}).get('by_native_status',{})
  gr=grade_by_key.get((r['task'],'default'),{});cpu=grade_by_key.get((r['task'],'cpu2048'),{})
  csvrows.append({'task':r['task'],'classification':r['classification'],'A_original_label':r['original_label'],'B_audited_default_label':audited.get(r['task'],'excluded'),'cpu2048_audited_grade':cpu.get('audited_grade','not run'),'frozen_candidate_sha256':r['frozen_patch_sha256'],'frozen_candidate_bytes':r['frozen_patch_bytes'],'grader_applied_sha256':r.get('applied_patch_sha256','missing'),'grader_applied_bytes':r.get('applied_patch_bytes','missing'),'original_label_attached_to':r.get('label_attached_to','missing record'),'source_run':r['source_run'],'label_report_path':r.get('label_report_path','missing'),'F2P_not_passing':json.dumps(f.get('not_passing',[]),sort_keys=True),'P2P_FAILED_ERROR':json.dumps(p.get('FAILED_ERROR',[]),sort_keys=True),'P2P_SKIPPED':json.dumps(p.get('SKIPPED',[]),sort_keys=True),'P2P_absent':json.dumps(p.get('absent',[]),sort_keys=True),'P2P_other':json.dumps(p.get('other',[]),sort_keys=True),'missing_records':json.dumps(r['missing_records']),'audited_default_log_dir':gr.get('log_dir','not run')})
 csv_write('tasks.csv',csvrows)
 # A separate long-form CSV keeps every metric and exact interval machine-readable.
 metricrows=[]
 for setname,pt in tables.items():
  for policy,table in pt.items():
   for rule,ms in table['metrics'].items():
    for m in metric_names:
     v=ms[m];ci=v['ci95'] or [None,None]
     metricrows.append({'label_set':setname,'policy':policy,'rule':rule,'metric':m,'numerator':v['count'],'denominator':v['denominator'],'fraction':v['fraction'],'CI95_low':ci[0],'CI95_high':ci[1]})
 csv_write('metrics.csv',metricrows)
 render_markdown(result,metric_names)
 print(json.dumps({'classification_counts':counts,'audited_grade_count':len(grades),'label_counts':{name:ts['C_invalid_excluded']['label_counts'] for name,ts in tables.items()},'label_changes_A_to_B':changes,'output_sha256':{f:sha((OUT/f).read_bytes()) for f in ['analysis.md','analysis.json','tasks.csv','metrics.csv']}},sort_keys=True))


def render_markdown(r,metric_names):
 tables=r['tables'];A=tables['A_original'];B=tables['B_audited_default'];cpu=tables['B_cpu2048_sensitivity'];changes=r['label_changes_A_to_B']
 lines=['# Phase 4 label-integrity audit','',
 'This is post-hoc, after `phase4-run-sealed`. The original labels, sealed results, executor, and all tags stay unchanged. Audited grades below are separate measurements, never replacement labels. All 1,799 sealed run files were reverified before each audit/report execution.','',
 '## Binding and label basis across all 83 tasks','',
 '| Classification | Tasks |','|---|---:|']
 for c,n in r['classification_counts'].items():lines.append(f'| {c} | {n} |')
 lines+=['','Every archived record was located using the final CSV source-run binding, including the four `rerun` aliases. The inventory checks the frozen patch against the launch plan, correctness sidecar, and binding manifest. The original label comes from the pinned results CSV; it agrees with the archived oracle/report resolved status in all 83 cases. All applied-patch bytes are present verbatim in run_instance.log, and successful application is logged. Matching declared hashes in oracle_record.json do not repair mismatching actual applied bytes.','',
 'For nine tasks, the linked archived grading evidence describes a different **applied candidate** from the candidate named by the label metadata. The CSV label and linked report grade agree on correct/incorrect, but that agreement does not repair the frozen-candidate binding or establish how the provenance mismatch arose. This includes both correct and incorrect labels. No semantic patch equivalence is inferred from a byte mismatch.','',
 '| Task | Original CSV label / linked archived report grade | Frozen bytes | Applied bytes | Source run |','|---|---|---:|---:|---|']
 for t in r['all_tasks']:
  if t['classification']=='BINDING_MISMATCH':lines.append(f"| {t['task']} | {t['original_label']} / {'correct' if t['grader_report_resolved'] else 'incorrect'} | {t['frozen_patch_bytes']} | {t['applied_patch_bytes']} | {t['source_run']} |")
 lines+=['','Full SHA-256 values for every mismatch:','']
 for t in r['all_tasks']:
  if t['classification']=='BINDING_MISMATCH':
   lines += [f"- **{t['task']}**: frozen `{t['frozen_patch_sha256']}` ({t['frozen_patch_bytes']} bytes); archived applied `{t['applied_patch_sha256']}` ({t['applied_patch_bytes']} bytes). Original label metadata (`{t['original_label']}`) claims the frozen hash; linked archived report `{t['label_report_path']}` grades the applied hash as `{'correct' if t['grader_report_resolved'] else 'incorrect'}`."]
 lines+=['','SUPPORTED means binding matches and the report/log support the original grade: all expected references pass for a correct label; an unmet F2P (including absent F2P) or a genuine FAILED/ERROR supports an incorrect label. SKIP_ONLY means an incorrect grade has no unmet F2P or genuine P2P assertion/error, only skipped or absent P2P tests. BINDING_MISMATCH takes precedence over outcome basis. Missing report, raw log, oracle record or applied-patch evidence would be NO_GRADER_RECORD; none is missing.','',
 'Official parsing counts PASSED and XFAIL as passing. The five Pylint skip results are bound to native file/line summaries through the previously checked patched-source spans; the parser alone omits their IDs. SKIPPED and absent stay distinct in this audit. Tests outside the F2P/P2P references do not support a task label merely because they failed.','',
 '## Nonpassing references, task by task','',
 'The following table lists **every task**, including tasks with empty lists. The CSV and JSON preserve each test ID, native status, report success/failure bucket, and any source-bound skip proof. `none` means an empty list, not a missing record.','',
 '| Task | Original | Classification | F2P not passing | P2P FAILED/ERROR | P2P SKIPPED | P2P absent |','|---|---|---|---|---|---|---|']
 def entries(xs):return '<br>'.join('`'+x['test']+'` ('+x['native_status']+')' for x in xs).replace('|','&#124;') or 'none'
 for t in r['all_tasks']:
  pp=t.get('PASS_TO_PASS',{}).get('by_native_status',{})
  lines.append(f"| {t['task']} | {t['original_label']} | {t['classification']} | {entries(t.get('FAIL_TO_PASS',{}).get('not_passing',[]))} | {entries(pp.get('FAILED_ERROR',[]))} | {entries(pp.get('SKIPPED',[]))} | {entries(pp.get('absent',[]))} |")
 lines+=['','## Fresh full-task audited grades','',
 'Official SWE-bench **5.0.2** `make_test_spec` and `run_instance` were used, with the full dataset eval script, official test_patch, and every F2P/P2P reference. The installed harness modules match distribution RECORD. Fresh containers use the same immutable image identities as the sealed run, preventing mutable-tag drift; the default resource settings and entire test command are otherwise unchanged. The two SKIP_ONLY tasks also receive a fresh grade with only CPU shares set to 2048 before container start (equivalent to `--cpu-shares 2048`). No executor code is involved or edited.','',
 'Each invocation has a 1,800-second safety timeout. A timeout, application failure or missing usable report is recorded as no audited grade, not silently classified incorrect. Set B uses the **default-environment** audited grade. The extra CPU-2048 projection is a separate sensitivity. Raw logs stay under ignored `runs/phase4_label_audit/`; report JSON records their hashes, full reference counts, exact image IDs and resource settings.','',
 '| Task | Basis | Profile | F2P / P2P references | Audited grade | F2P not met | P2P not met |','|---|---|---|---|---|---:|---:|']
 for g in r['audited_grades']:
  basis=next(t['classification'] for t in r['all_tasks'] if t['task']==g['task']);report=g.get('report') or {};ts=report.get('tests_status',{})
  lines.append(f"| {g['task']} | {basis} | {g['profile']} | {g['full_task_F2P_count']} / {g['full_task_P2P_count']} | {g['audited_grade'] or 'unavailable/excluded'} | {len(ts.get('FAIL_TO_PASS',{}).get('failure',[]))} | {len(ts.get('PASS_TO_PASS',{}).get('failure',[]))} |")
 outside=[g for g in r['audited_grades'] if g.get('parser_FAILED_ERROR_outside_reference_lists')]
 if outside:
  lines+=['','FAILED/ERROR parser entries outside official reference lists (these can include expected nested pytester child results, not top-level task failures; they are not used to invent a different task grade):','']
  for g in outside:
   lines.append('- '+g['task']+' / '+g['profile']+': '+', '.join('`'+x['test']+'` ('+x['native_status']+')' for x in g['parser_FAILED_ERROR_outside_reference_lists'])+'.')
 lines+=['','## Label sets and changed assignments','',
 'A preserves the original labels. B preserves original labels for SUPPORTED tasks, uses the fresh default audited grade elsewhere, and excludes tasks with neither. These are analytical label-set mappings; the source labels are never written.','',
 '| Label set | Correct | Incorrect | Excluded |','|---|---:|---:|---:|']
 for name,table in [('A original',A),('B audited default',B),('B CPU-2048 sensitivity',cpu)]:
  n=table['C_invalid_excluded']['label_counts'];lines.append(f"| {name} | {n['correct']} | {n['incorrect']} | {n['excluded']} |")
 lines+=['','| Task whose assignment differs | A | B | Original classification |','|---|---|---|---|']
 for x in changes:lines.append(f"| {x['task']} | {x['A_original']} | {x['B_audited_default']} | {x['classification']} |")
 if not changes:lines.append('| none | | | |')
 lines+=['','## §3a — verdict × label, A and B side by side','',
 'Policy verdicts are read unchanged from the hash-pinned sealed result. INVALID_ID excluded is primary; INVALID_ID missing is sensitivity. Original-A matrices and every proportion/interval reproduce the previous post-hoc report exactly.','',
 '| Policy | Verdict | A correct | A incorrect | B correct | B incorrect |','|---|---|---:|---:|---:|---:|']
 for p in POLICIES:
  for v in VERDICTS:
   a=A[p]['verdict_by_label'][v];b=B[p]['verdict_by_label'][v]
   lines.append(f"| {p} | {v} | {a['correct']} | {a['incorrect']} | {b['correct']} | {b['incorrect']} |")
 lines+=['','## §3b — detection, false alarms and missed PASS','',
 'All intervals are exact two-sided **95% Clopper-Pearson** intervals. Primary positive = FAIL alone; secondary positive = FAIL or REGRESSION_ERROR. Conditional denominators include PASS+FAIL for primary and PASS+FAIL+REGRESSION_ERROR for secondary. INCOMPLETE and NOT_AVAILABLE stay in the all-labelled denominators but not the conditional denominators. Each set uses its own correct/incorrect totals; undefined 0-denominator rates are explicit. These intervals describe the observed proportions and do not turn audited harness grades into semantic ground truth.','',
 '| Policy | Positive rule | Proportion | A original [95% CI] | B audited default [95% CI] |','|---|---|---|---|---|']
 titles={'detection_all_incorrect':'Detection / all incorrect','detection_verdicted_incorrect':'Detection / verdicted incorrect','false_alarm_all_correct':'False alarms / all correct','false_alarm_verdicted_correct':'False alarms / verdicted correct','missed_all_incorrect':'Missed PASS / all incorrect','missed_verdicted_incorrect':'Missed PASS / verdicted incorrect'}
 for p in POLICIES:
  for rule in ['primary_FAIL_only','secondary_FAIL_plus_REGRESSION_ERROR']:
   for m in metric_names:lines.append(f"| {p} | {rule} | {titles[m]} | {format_p(A[p]['metrics'][rule][m])} | {format_p(B[p]['metrics'][rule][m])} |")
 lines+=['','## CPU-2048 resource sensitivity (not primary B)','',
 '| Policy | Verdict | Correct | Incorrect |','|---|---|---:|---:|']
 for p in POLICIES:
  for v in VERDICTS:
   x=cpu[p]['verdict_by_label'][v];lines.append(f"| {p} | {v} | {x['correct']} | {x['incorrect']} |")
 lines+=['','The JSON and metrics.csv provide every CPU-sensitivity proportion with the same exact interval and denominator rules. These extra rows expose resource-dependent audited grades without choosing a more favorable primary grade.','',
 '## Provenance, reproduction and limits','',
 '- Source labels: `'+str(SIDECARS/'correctness_sidecar.json')+'`; SHA-256 `'+LABELS_SHA+'`.',
 '- Cached Verified dataset revision: `78f471bf655a3137b2e8a75af1501690ec009ec3`; Parquet SHA-256 `'+DATASET_SHA+'`. Only explicit grading/source columns are loaded; gold solution patches are not needed.',
 '- All 83 archived reports, oracle records, native logs, applied patch files and frozen candidates are hash-inventoried in analysis.json. The four rerun aliases are taken from the existing pinned binding records, not guessed from directory names.',
 '- `env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/label_audit/audit.py` regenerates reports without running tests. `--grade` is the explicit full-task execution mode; completed grades are hash-verified before reuse. `--inventory` only inventories archived evidence.',
 '- The report is generated twice from the same raw grade artifacts and compared byte-for-byte. No rerun of grades is needed to check deterministic analysis.',
 '- A mismatched applied patch invalidates the binding, regardless of whether the original and audited labels happen to agree. A SUPPORTED label can be supported by unmet F2P without an assertion traceback. A successful audited grade establishes the official harness result in the stated environment, not an independent proof of correctness.',
 '- The sealed runtime measurements and all original-A figures remain immutable. Any interpretive effect of changed labels appears only in this separate report.']
 (OUT/'analysis.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(lines).splitlines())+'\n')
 notes_path=ROOT/'reports/next_phases/PRESENTATION_NOTES.md'
 notes=notes_path.read_text();heading='### Label integrity — post-hoc audit'
 nA=A['C_invalid_excluded']['label_counts'];nB=B['C_invalid_excluded']['label_counts'];nCPU=cpu['C_invalid_excluded']['label_counts']
 paragraph=f"{heading}\n\nThe 83-task audit finds **{r['classification_counts']['SUPPORTED']} SUPPORTED, {r['classification_counts']['BINDING_MISMATCH']} BINDING_MISMATCH, {r['classification_counts']['SKIP_ONLY']} SKIP_ONLY, {r['classification_counts']['NO_GRADER_RECORD']} missing records**. Applied patch bytes in nine archived graders differ from the frozen candidates, including labels on both sides. Fresh official SWE-bench 5.0.2 full-task grading covers every non-SUPPORTED candidate, with additional CPU-2048 grades for the two skip-only Pylint tasks. The original {nA['correct']}/{nA['incorrect']} labels are unchanged; analytical set B uses default audited grades and has {nB['correct']} correct, {nB['incorrect']} incorrect and {nB['excluded']} excluded. The separate CPU-2048 sensitivity has {nCPU['correct']}/{nCPU['incorrect']} labels, with {nCPU['excluded']} excluded. {len(changes)} assignments differ between A and B.\n\n"
 paragraph+='Primary FAIL-only rates with exact 95% Clopper-Pearson intervals: '+ '; '.join(f"{p[0]}: detection {format_p(A[p]['metrics']['primary_FAIL_only']['detection_all_incorrect'])} → {format_p(B[p]['metrics']['primary_FAIL_only']['detection_all_incorrect'])}; false alarms {format_p(A[p]['metrics']['primary_FAIL_only']['false_alarm_all_correct'])} → {format_p(B[p]['metrics']['primary_FAIL_only']['false_alarm_all_correct'])}" for p in ['C_invalid_excluded','S_invalid_excluded'])+'. All verdict × label tables, conditional rates, REGRESSION_ERROR-inclusive results and INVALID_ID sensitivities are reported side by side in [label_audit/analysis.md](phase4_posthoc/label_audit/analysis.md), with [per-task evidence](phase4_posthoc/label_audit/tasks.csv). Audited grades are separate measurements, never replacements for the original labels. Sealed results, executor and tags remain unchanged.\n\n'
 if heading in notes:
  a=notes.index(heading);b=notes.index('### Cap hit and four disclosures',a);notes=notes[:a]+paragraph+notes[b:]
 else:notes=notes.replace('### Cap hit and four disclosures',paragraph+'### Cap hit and four disclosures')
 notes_path.write_text(notes)

def main():
 ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group();mode.add_argument('--inventory',action='store_true');mode.add_argument('--grade',action='store_true');args=ap.parse_args()
 verification=preconditions();pins={r['instance_id']:r for r in load(RUN/'plan.json')['task_specs']}
 rows=dataset();labels=load(SIDECARS/'correctness_sidecar.json');bindings=load(SIDECARS/'label_candidate_bindings.json')
 assert collections.Counter(x['correctness'] for x in labels.values())=={'right':69,'wrong':14}
 records=inventory(rows,pins,labels,bindings)
 if args.inventory:
  write_json(RAW/'inventory.json',{'tasks':records,'classification_counts':dict(collections.Counter(r['classification'] for r in records)),'input_sha256':dict(sorted(INPUTS.items()))})
  print(json.dumps({'classification_counts':dict(collections.Counter(r['classification'] for r in records)),'tasks':len(records)},sort_keys=True))
 elif args.grade:run_grades(records,rows,pins)
 else:report(records,verification)

if __name__=='__main__':main()
