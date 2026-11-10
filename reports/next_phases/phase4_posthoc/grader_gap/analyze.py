#!/usr/bin/env python3
"""Build the analysis-only grader-gap report from pinned sources and raw evidence.

No test execution. replay.py is the separate opt-in Docker entry point.
Does not relabel patches or modify sealed artifacts, the executor, or tags.
"""
import ast
import csv
import difflib
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RAW = ROOT / 'runs/phase4_grader_gap'
OLD = Path('/home/sankalp/projects/cis695-agent-reliability')
RUN = ROOT / 'runs/phase4_v4_attempt4_20261109T185713Z'
sys.path.insert(0,str(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal'))
import compute_seal

PINNED_MANIFEST = '69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25'
PINNED_POSTHOC = '6bb5963b5502b962245a38e4ff88fc41c988bb72'
INPUTS = {}

def digest(b):return hashlib.sha256(b).hexdigest()

def read(p):
 p=Path(p);b=p.read_bytes();INPUTS[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=digest(b);return b

def jread(p):return json.loads(read(p))

def node(source,qualname):
 body=ast.parse(source).body
 for part in qualname.split('.'):
  n=next(n for n in body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)) and n.name==part)
  body=n.body
 start=min([n.lineno]+[d.lineno for d in n.decorator_list])
 text='\n'.join(source.splitlines()[start-1:n.end_lineno])+'\n'
 return text,{'first_line':start,'last_line':n.end_lineno,'sha256':digest(text.encode())}

def unified(a,b,name,before_label='pre-existing',after_label='test_patch'):
 return ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=before_label+'/'+name,tofile=after_label+'/'+name,n=3))


def sources(row,pin,targets):
 iid=row['instance_id'];archive=Path(pin['archive_path'])
 assert digest(read(archive))==pin['archive_sha256']
 changed=re.findall(r'^\+\+\+ b/(.+)$',row['test_patch'],re.M)
 # These files cover target-local helpers, project test fixtures, native
 # collection hooks, warning handling, config, and the explicit data fixtures.
 paths=set(changed)|{t.split('::')[0] for t in targets}
 if iid.startswith('pylint'):
  paths.update(['tests/conftest.py','pylint/lint/run.py','pylint/testutils/__init__.py','pylint/testutils/_run.py','pylint/testutils/lint_module_test.py','pylint/testutils/reporter_for_tests.py','pylint/testutils/utils.py','pylint/reporters/__init__.py','pyproject.toml','setup.cfg','pylintrc','tests/testutils.py'])
  paths.update('tests/regrtest_data/'+x for x in ['unused_variable.py','special_attr_scope_lookup_crash.py','syntax_error.py','wildcard.py','wrong_import_position.py'])
 elif iid.startswith('django'):
  paths.update(['tests/generic_views/views.py','tests/generic_views/models.py','tests/generic_views/urls.py','tests/generic_views/templates/generic_views/about.html','django/test/testcases.py','django/test/client.py','django/test/utils.py','django/utils/deprecation.py','tests/runtests.py','tests/test_sqlite.py'])
 else:
  paths.update(['lib/matplotlib/tests/conftest.py','lib/matplotlib/testing/conftest.py','lib/matplotlib/testing/__init__.py','lib/matplotlib/testing/decorators.py','pytest.ini','setup.cfg'])
 before={}
 with tarfile.open(archive) as tar:
  # Entire bad_package directory is consumed by custom_should_analyze_file.
  if iid.endswith('6528'):paths.update(m.name.removeprefix('testbed/') for m in tar.getmembers() if m.isfile() and m.name.startswith('testbed/tests/regrtest_data/bad_package/'))
  if iid.startswith('pylint'):paths.update(m.name.removeprefix('testbed/') for m in tar.getmembers() if m.isfile() and m.name.endswith(('empty.pylintrc','testing_pylintrc')))
  for p in sorted(paths):
   try:before[p]=tar.extractfile('testbed/'+p).read()
   except KeyError:pass
 with tempfile.TemporaryDirectory(prefix='source-diff-',dir=RAW) as td:
  td=Path(td)
  for p,b in before.items():
   dest=td/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  applied=subprocess.run(['patch','--batch','--fuzz=0','-p1'],cwd=td,input=row['test_patch'].encode(),capture_output=True)
  assert applied.returncode==0,applied.stdout+applied.stderr
  after={p:(td/p).read_bytes() for p in sorted(paths) if (td/p).is_file()}
 helpers=[]
 for p in sorted(set(before)|set(after)):
  helpers.append({'file':p,'before_sha256':digest(before[p]) if p in before else None,'after_sha256':digest(after[p]) if p in after else None,'changed':before.get(p)!=after.get(p)})
 comparisons=[]
 for t in targets:
  p,*names=t.split('::');qual='.'.join(re.sub(r'\[.*','',n) for n in names)
  a,ah=node(before[p].decode(),qual);b,bh=node(after[p].decode(),qual)
  comparisons.append({'test':t,'file_touched':p in changed,'target_body_changed':a!=b,'before':ah,'after':bh,'diff':unified(a,b,t)})
 scopes=[]
 extra=[]
 if iid.startswith('pylint'):
  extra=[('tests/test_self.py','TestRunTC'),('tests/test_self.py','TestRunTC._run_pylint'),('tests/test_self.py','TestRunTC._clean_paths'),('tests/test_self.py','TestRunTC._test_output'),('tests/conftest.py','pytest_collection_modifyitems'),('pylint/lint/run.py','_query_cpu'),('pylint/lint/run.py','_cpu_count')]
  if iid.endswith('6528'):extra.append(('tests/lint/unittest_lint.py','_CustomPyLinter'))
 elif iid.startswith('django'):extra=[('tests/generic_views/test_base.py','DeprecationTests'),('django/test/testcases.py','SimpleTestCase.assertRaisesMessage'),('django/test/testcases.py','SimpleTestCase._assert_raises_or_warns_cm')]
 for p,q in extra:
  a,ah=node(before[p].decode(),q);b,bh=node(after[p].decode(),q)
  scopes.append({'file':p,'scope':q,'before':ah,'after':bh,'changed':a!=b,'diff':unified(a,b,p+':'+q)})
 configs={p:b.decode(errors='replace') for p,b in before.items() if p.endswith(('pyproject.toml','setup.cfg','pytest.ini')) and b'filterwarnings' in b}
 warning_lines={p:[{'line':n,'text':line} for n,line in enumerate(b.decode(errors='replace').splitlines(),1) if re.search(r'warnings\.(simplefilter|filterwarnings|catch_warnings)|filterwarnings',line)] for p,b in before.items() if p.endswith(('.py','.toml','.ini','.cfg'))}
 return {'test_patch_sha256':digest(row['test_patch'].encode()),'test_patch_touched_files':changed,'targets':comparisons,'scopes':scopes,'files':helpers,'warning_configuration':configs,'warning_filter_source_lines':{p:v for p,v in warning_lines.items() if v}}


def historical(row,pin):
 iid=row['instance_id'];source='main_50_a' if iid.startswith('pylint') else 'main_50_b'
 task=OLD/'runs'/source/'tasks'/iid
 log=OLD/'logs/run_evaluation'/(source+'__'+iid)/'deepseek_deepseek-v4-flash'/iid
 oracle=jread(task/'oracle_record.json')
 report=jread(log/'report.json')[iid]
 text=read(log/'test_output.txt').decode(errors='replace')
 evaluation=read(log/'eval.sh').decode();runlog=read(log/'run_instance.log').decode(errors='replace')
 frozen=read(task/'patch.diff');actual=read(log/'patch.diff')
 assert digest(frozen)==pin['patch_sha256']
 repair=jread(task/'repair_record.json')
 predictions=[json.loads(line) for line in read(task/'predictions.jsonl').decode().splitlines() if line]
 assert len(predictions)==1 and predictions[0]['instance_id']==iid
 assert digest(predictions[0]['model_patch'].encode())==digest(frozen)
 assert repair['patch']['sha256'].removeprefix('sha256:')==digest(frozen)
 assert oracle['patch_sha256'].removeprefix('sha256:')==digest(frozen)
 assert str(log/'report.json')==oracle['report_file']
 patch=re.search(r"git apply -v - <<'([^']+)'\n(.*?)\n\1",evaluation,re.S)[2]
 assert patch.rstrip()==row['test_patch'].rstrip()
 return {'task':iid,'oracle_record_path':str(task/'oracle_record.json'),'oracle_report_path':oracle.get('report_file'),'historical_log_dir':str(log),'report':report,'recorded_command':next(x for x in evaluation.splitlines() if x.startswith(('pytest ','./tests/runtests.py '))),'explicit_environment_exports':[x for x in evaluation.splitlines() if x.startswith('export ')],'environment_setup_commands':[x for x in evaluation.splitlines() if x.startswith(('source ','conda activate','python -m pip','sed -i'))],'runtime_version_lines':[x for x in text.splitlines() if x.startswith(('platform ','plugins:'))],'PYTHONHASHSEED_recorded':False,'historical_exact_cgroup_recorded':False,'frozen_candidate_sha256':digest(frozen),'logged_applied_candidate_sha256':digest(actual),'candidate_matches':frozen==actual,'declared_oracle_candidate_sha256':oracle.get('patch_sha256'),'candidate_diff':unified(frozen.decode(),actual.decode(),'candidate-patch-text','frozen-candidate','archived-grader-candidate'),'raw_relevant_lines':[{'line':n,'text':s} for n,s in enumerate(text.splitlines(),1) if ('SKIPPED [' in s and ('Need 2 or more cores' in s)) or ('test_template_params_warning' in s) or ('RemovedInDjango40Warning not raised' in s) or ('test_register_cmap' in s) or ('assert mpl.colormaps[target] == new_cm' in s)],'log_text':text,'run_log_has_actual_patch':actual.decode().strip() in runlog}


def main():
 entries,verification=compute_seal.verify_run();assert verification['sha256']==PINNED_MANIFEST
 pins={x['instance_id']:x for x in jread(RUN/'plan.json')['task_specs']}
 original=jread(ROOT/'reports/next_phases/phase4_posthoc/analysis.json')
 expected=subprocess.check_output(['git','show',PINNED_POSTHOC+':reports/next_phases/phase4_posthoc/analysis.json'],cwd=ROOT)
 assert digest(expected)==digest((ROOT/'reports/next_phases/phase4_posthoc/analysis.json').read_bytes())
 labels=jread(ROOT/'reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/correctness_sidecar.json')
 assert sum(x['correctness']=='wrong' for x in labels.values())==14
 assert sum(x['correctness']=='right' for x in labels.values())==69
 oracle_inputs=jread(RAW/'oracle_inputs.json')
 assert digest(read(oracle_inputs['parquet_path']))==oracle_inputs['parquet_sha256']
 import pyarrow.parquet as pq
 rows={r['instance_id']:r for r in oracle_inputs['rows']}
 cached=pq.read_table(oracle_inputs['parquet_path'],columns=list(next(iter(rows.values())))).to_pylist()
 for row in cached:
  if row['instance_id'] in rows:
   for key,value in rows[row['instance_id']].items():
    assert row[key]==value,(row['instance_id'],key)
 read(OUT/'replay.py');read(OUT/'analyze.py')
 definition=original['witness_groups']['grader_failing_pre_existing']
 replays=jread(RAW/'replay_results.json');assert len(replays)==12
 for r in replays:
  log=ROOT/r['log_dir'];assert digest(read(log/'test_output.txt'))==r['test_output_sha256'];assert digest(read(log/'eval.sh'))==r['eval_script_sha256'];assert digest(read(log/'report.json'))==r['report_sha256']
  # Successful candidate application is in run_instance.log; an all-skipped
  # one-test report can say patch_successfully_applied=false because its
  # parser found no PASS/FAIL records. That is not evidence of apply failure.
  runtime_log=read(log/'run_instance.log').decode()
  assert 'Applied Patch' in runtime_log or 'APPLY_PATCH_PASS' in runtime_log,log
 probes=jread(RAW/'executor_environment.json');assert len(probes)==3
 distribution=jread(RAW/'harness_distribution.json')
 tables=[];static={};history={}
 for iid,row in rows.items():
  tests=[x['test_id'] for x in definition if x['task']==iid]
  static[iid]=sources(row,pins[iid],tests)
  history[iid]=historical(row,pins[iid]);logtext=history[iid].pop('log_text')
  for t in tests:
   assert labels[iid]['correctness']=='wrong'
   assert labels[iid]['patch_sha256'].removeprefix('sha256:')==pins[iid]['patch_sha256']
   oracle_id=t
   if iid.startswith('django'):
    p,cls,name=t.split('::');oracle_id=name+' ('+p.removeprefix('tests/').removesuffix('.py').replace('/','.')+'.'+cls+')'
   assert oracle_id in history[iid]['report']['tests_status']['PASS_TO_PASS']['failure']
   existing=next(x for x in definition if x['task']==iid and x['test_id']==t)
   paired={r['variant']:r for r in replays if r['task']==iid and r['test']==t}
   if iid.startswith('pylint'):
    assert all(r['status']=='SKIPPED' and r['environment']['pylint_cpu_count']==1 for r in paired.values()) and len(paired)==2
    status='SKIPPED';classification='ENVIRONMENT';cause='CPU shares: native needs_two_cores guard; default 1024 -> pylint 1, executor 2048 -> pylint 2.'
   elif iid.startswith('django'):
    assert all(r['status']=='PASS' for r in paired.values()) and len(paired)==2
    assert not history[iid]['candidate_matches']
    status='FAIL';classification='OTHER';cause='Archived grader applied a different candidate that removes the URL-kwargs warning; sealed candidate retains it.'
   else:
    status='FAIL';classification='OTHER';cause='Positive control: same candidate; unchanged test; FAIL in archived grader and sealed patched tree.'
   check=next(x for x in static[iid]['targets'] if x['test']==t)
   tables.append({'task':iid,'test':t,'label':'incorrect','historical_grader_bucket':'PASS_TO_PASS.failure','historical_native_status':status,'sealed_base':existing['trees']['base']['status'].upper(),'sealed_patched':existing['trees']['patched']['status'].upper(),'test_file_touched':check['file_touched'],'target_function_changed':check['target_body_changed'],'with_test_patch':paired.get('with_test_patch',{}).get('status','not rerun (control already agrees)'),'without_test_patch':paired.get('without_test_patch',{}).get('status','not rerun (control already agrees)'),'classification':classification,'factor_or_explanation':cause})
 tasks=sorted({x['task'] for x in tables});assert len(tasks)==4
 executor_commands={}
 for iid in rows:
  target_ids={compute_seal.django_label(x['test_id']) if iid.startswith('django') else x['test_id'] for x in definition if x['task']==iid}
  events=jread(RUN/'tasks'/iid/'patched.json')['events']
  executor_commands[iid]=[e['argv'] for e in events if e.get('event')=='start' and target_ids.intersection(e.get('ids',[]))]
  assert executor_commands[iid],iid
 result={'scope':'Post-hoc explanation only; no relabeling or reclassification of sealed results.','manifest_verification':verification,'historical_candidate_provenance_warning':'django__django-13297: report and applied patch disagree with the declared candidate binding. Labels retained unchanged.','ceiling':{'tasks_with_historical_grader_failing_preexisting_tests':4,'incorrect_tasks':14,'proportion':4/14,'interpretation':'Historical report-bucket ceiling, not four validated assertion-failure witnesses.'},'classifications':tables,'test_patch_comparisons':static,'historical_grader_evidence':history,'official_harness_distribution':distribution,'single_test_replays':replays,'executor_resource_probes':probes,'sealed_executor_argv_for_target_batches':executor_commands,'input_sha256':dict(sorted(INPUTS.items()))}
 (OUT/'evidence.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=list(tables[0]),lineterminator='\n');w.writeheader();w.writerows(tables);(OUT/'classification.csv').write_text(stream.getvalue())
 write_markdown(result)
 print(json.dumps({'rows':len(tables),'replays':len(replays),'classifications':{k:sum(t['classification']==k for t in tables) for k in ['ENVIRONMENT','OTHER']},'outputs':{f:digest((OUT/f).read_bytes()) for f in ['analysis.md','classification.csv','evidence.json']}},sort_keys=True))


def write_markdown(r):
 lines=['# Why the six historical grader witnesses pass in Phase 4','',
 'Five Pylint witnesses were **SKIPPED**, not failed assertions, in the archived official grader output. Docker CPU shares explain the change from SKIPPED to PASS. The Django witness failed on a **different candidate patch** in the archived grader log. Its frozen candidate passes with and without the official test patch. The Matplotlib control fails in both the archived grader and the sealed patched tree.','',
 'This is analysis after `phase4-run-sealed`. Executor sources, sealed results, labels, tags, and the original artifacts are unchanged. The sealed directory was reverified against all 1,799 manifest entries before this analysis. Twelve official-harness invocations each selected exactly one test; three further containers only measured resources. No full-suite or full-benchmark rerun was performed.','',
 '## Per-test classification','',
 '| Task | Test | Historical native status | Frozen candidate with / without test_patch | Sealed patched | Classification |',
 '|---|---|---|---|---|---|']
 for t in r['classifications']:
  test=t['test'].split('::')[-1]
  pair=t['with_test_patch']+' / '+t['without_test_patch'] if t['task'].startswith(('pylint','django')) else 'not rerun; control already agrees'
  lines.append(f"| {t['task']} | `{test}` | {t['historical_native_status']} | {pair} | {t['sealed_patched']} | {t['classification']} |")
 lines+=['', '**Ceiling:** 4 of 14 incorrect patches (28.6%) have any pre-existing test in the historical grader’s failure bucket. That bucket includes five CPU skips and a Django candidate-binding mismatch; it is not evidence that four frozen candidates have old tests that fail assertions. No test is causally classified TEST_PATCH_CHANGED, and no gap remains GRADER_ONLY_FAILURE_UNEXPLAINED under the evidence below.','',
 '## Test-patch comparison','',
 'The cached SWE-bench Verified revision is `78f471bf655a3137b2e8a75af1501690ec009ec3`. Every cached `test_patch` matches the archived grader’s applied test-patch heredoc after stripping trailing newlines. Base sources are the exact hash-pinned task archives from the sealed launch plan. The evidence JSON records archive, oracle, source-scope, helper/fixture, and log hashes. The comparison applies only `test_patch` to isolated copies; it never applies the gold solution. All seven target function bodies **including decorators** are byte-identical before/after. Every test’s file is nevertheless touched.','',
 '- Pylint 6528: the oracle adds recursive-ignore tests and an unused ignored-subdirectory fixture. `_CustomPyLinter`, the CPU collection hook, scoring helpers, and all fixtures read by the targets are unchanged. The full `TestRunTC` class gains unrelated methods/docstrings, shown below; jobs_score itself is unchanged.',
 '- Pylint 7277: the oracle extends `test_modify_sys_path`; jobs_score, its helper chain, its unused_variable.py fixture, CPU query, and collection guard are unchanged.',
 '- Django 13297: the oracle changes the enclosing class from SimpleTestCase to TestCase, adds a RequestFactory and a new filtering test. The warning method and warning assertion helpers are unchanged. This is different enclosing test code, but the paired replay shows that it does not cause the gap for the frozen candidate.',
 '- Matplotlib 25479: the oracle changes sibling colormap-equality expectations and adds a mismatched-name test. test_register_cmap and its test infrastructure are unchanged. It has no explicit fixture arguments and exercises the same colormap APIs in both versions.','']
 for iid,check in r['test_patch_comparisons'].items():
  lines+=['### '+iid,'','| Target scope | Before lines | After lines | Scope SHA-256 (same in both) |','|---|---|---|---|']
  for t in check['targets']:
   a,b=t['before'],t['after'];assert a['sha256']==b['sha256']
   lines.append(f"| `{t['test']}` | {a['first_line']}–{a['last_line']} | {b['first_line']}–{b['last_line']} | `{a['sha256']}` |")
  changed=[s for s in check['scopes'] if s['changed']]
  for s in changed:lines+=['',f"Enclosing class diff (`{s['file']}:{s['scope']}`):",'', '```diff',s['diff'].rstrip(),'```']
  lines+=['','Compared helpers/fixtures (whole-file hashes or named scopes in evidence.json):','']
  lines.append('; '.join('`'+x['file']+'`' for x in check['files'] if not x['changed'])+'.')
  if check['scopes']:lines+=['','Named helper comparisons: '+', '.join('`'+s['scope']+'` '+('changed (diff above)' if s['changed'] else 'identical') for s in check['scopes'])+'.']
 lines+=['','## Archived official grader evidence','',
 'All four official report/log sets exist behind the label sidecars. `evidence.json` records their absolute paths and SHA-256 digests, and preserves the report buckets separately from native test status. A fresh partial-task harness report is not a replacement task label. Historical exact cgroup counters, os.cpu_count, PYTHONHASHSEED values, and the live warning-filter list were not logged. Absence of an export is reported as absence of evidence, not proof of a historical environment value.','']
 for iid,h in r['historical_grader_evidence'].items():
  lines+=['### '+iid,'',f"Log directory: `{h['historical_log_dir']}`.",'', 'Exact recorded test command:','', '```sh',h['recorded_command'],'```','', 'Recorded setup:','', '```sh','\n'.join(h['environment_setup_commands']+h['explicit_environment_exports']),'```']
  lines+=['','Recorded versions: '+(' / '.join(h['runtime_version_lines']) or 'Python 3.6 paths in the Django traceback; no pytest header.')]
  lines+=['','Native evidence (`test_output.txt` line numbers):','']
  for x in h['raw_relevant_lines']:lines.append(f"- L{x['line']}: `{x['text'].strip()}`")
  lines+=['',f"Frozen candidate SHA-256: `{h['frozen_candidate_sha256']}`.",f"Archived applied candidate SHA-256: `{h['logged_applied_candidate_sha256']}`. Match: **{h['candidate_matches']}**.",'']
 lines+=['## The Django binding mismatch','',
 'The frozen 1,770-byte candidate is also the patch in the original repair record/prediction and the hash declared by oracle_record.json. The official grader directory instead contains a 4,454-byte patch; run_instance.log records applying that patch. The archived patch removes the warning machinery, while the frozen patch retains it and wraps kwargs after get_context_data. The target requires RemovedInDjango40Warning to be raised when the context values are read. Its archived failure, “RemovedInDjango40Warning not raised”, follows directly from removing that machinery. The original label stays unchanged; this report does not claim the archived failure belongs to the frozen patch.','',
 'This is classified **OTHER: evaluated candidate differs**. The official single-test pair on the frozen incorrect-labelled candidate returns PASS with and without test_patch, so neither the class-base change nor warning flags is required to explain the observed agreement in those replays.','',
 'Candidate patch-text difference (not a new candidate or a committed patch file):','', '```diff',r['historical_grader_evidence']['django__django-13297']['candidate_diff'].rstrip(),'```','',
 '## Fresh official harness and environment comparison','',
 'Installed SWE-bench **5.0.2** entry points `make_test_spec` and `run_instance` were called directly. Six relevant installed modules match their distribution RECORD hashes (recorded in evidence.json). Each pair differs only in applying the official test_patch. The suite command is narrowed to one exact node; image tags are replaced with the immutable image IDs used at seal; a read-only environment probe is inserted before the test-output marker. The historical locale/setup commands and all test-command flags are preserved. Each invocation uses a fresh container with the official default resource profile. No native skip guard is overridden.','',
 'The replay logs retain the full original task FAIL_TO_PASS/PASS_TO_PASS references, so their task-resolution reports are intentionally partial and are **not new labels**. In all-skipped single-test Pylint runs, the parser can return no PASS/FAIL entries and leave patch_successfully_applied false; run_instance.log explicitly proves candidate application succeeded. Pylint 6528’s stock final git checkout also mentions the newly added fixture path absent from the base tree; its pathspec diagnostic occurs after the test and is not an assertion failure.','',
 '| Task/profile | os.cpu_count / affinity | cgroup cpu.shares | cpu.max | Pylint _query_cpu / _cpu_count | PYTHONHASHSEED / PYTHONWARNINGS |','|---|---|---|---|---|---|']
 for iid in ['pylint-dev__pylint-6528','pylint-dev__pylint-7277','django__django-13297']:
  official=next(x for x in r['single_test_replays'] if x['task']==iid)['environment']
  executor=next(x for x in r['executor_resource_probes'] if x['task']==iid)['environment']
  for profile,e in [('official default (measured now)',official),('executor resource profile (measured now)',executor)]:
   shares=e['cgroup'].get('/sys/fs/cgroup/cpu/cpu.shares',e['cgroup'].get('/sys/fs/cgroup/cpu.shares','absent'))
   lines.append(f"| {iid} / {profile} | {e['os_cpu_count']} / {e['affinity_count']} | {shares} | {e['cgroup'].get('/sys/fs/cgroup/cpu.max','absent (cgroup v1)')} | {e.get('pylint_query_cpu','n/a')} / {e.get('pylint_cpu_count','n/a')} | {e['PYTHONHASHSEED']} / {e['PYTHONWARNINGS']} |")
 lines+=['',
 'These are current replay measurements, not a reconstruction of unlogged historical counters. The archived skip message plus the unchanged `_cpu_count() < 2` guard proves why the historical Pylint tests did not run. On cgroup v1, Pylint uses int(cpu.shares / 1024) when quota is unlimited, even though shares express scheduling weight rather than a CPU-count limit. Our executor’s 2048 shares therefore make its query return 2 instead of 1; the sealed captures show all five tests actually PASS.','',
 'Warning/flag comparison:','',
 '- Official Pylint: `pytest -rA <one node>`; sealed executor: `python -m pytest -p no:cacheprovider -v -- <selected IDs>`. Neither adds -W or xdist parallel flags. The tests themselves retain jobs=1/2, and jobs_score explicitly passes `--jobs=2 -ry`; its helper ignores warnings inside a catch_warnings block in both source versions.',
 '- Official Django: `./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 <one dotted test>`. Sealed executor: `python tests/runtests.py --verbosity=2 <dotted selections>`; this task’s frozen django_parallel_one is false, so no explicit --parallel is added. The unchanged runner defaults to --parallel=0 (automatic), sets DJANGO_SETTINGS_MODULE to test_sqlite unless already provided, and promotes RemovedInDjango40Warning/41Warning, ResourceWarning and RuntimeWarning to errors. These source filter rules apply on both paths; the target uses assertRaisesMessage on the warning category. No explicit -W or -p flag is used on either Django path.',
 '- Official Matplotlib command has only -rA. Its sealed executor uses the same pytest flag pattern as Pylint. The archived and sealed target failures agree; no extra replay was needed for this control.',
 '- Fresh interpreter startup warning filters, sys.warnoptions, exact cgroup quota/period files, image IDs, Python versions and the two allowlisted environment values are recorded for each replay/probe in evidence.json. These are startup probes, not a claim to have captured the live pytest/Django in-test filter stack. Project warning configuration is preserved there; the Django assertion uses the identical assertRaisesMessage helper, so helper-induced warning differences are ruled out. Historical in-test warning filters were not recorded.','',
 '## Reproduction and limits','',
 'From the project root, `env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/grader_gap/analyze.py` regenerates the report and CSV without executing tests. `replay.py --execute` is a separate explicit twelve-invocation diagnostic and refuses to overwrite existing logs. Raw logs and oracle inputs stay in ignored `runs/phase4_grader_gap/`; no runs/, logs/, or *.patch file is committed. Full archived logs, rather than a newly inferred grader status, support all historical statements.','',
 'The report explains the six observed gaps. It does not establish that the frozen Django candidate is correct, that old tests cover the benchmark’s new behavior, or that the historical task label can be transferred across different patch bytes. The two incorrect-labelled Pylint candidates pass these unchanged CPU-enabled old tests; recursive-ignore/sys.path behavior is outside these witnesses. Their grader-derived labels do not, by themselves, prove a semantic bug in those candidates, particularly when the report failures are skips. The Matplotlib old test remains a useful assertion-failure control.']
 # Unified diffs retain space-only context lines in evidence.json; trim
 # their display in Markdown so the committed report passes whitespace checks.
 (OUT/'analysis.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(lines).splitlines())+'\n')

if __name__=='__main__':main()
