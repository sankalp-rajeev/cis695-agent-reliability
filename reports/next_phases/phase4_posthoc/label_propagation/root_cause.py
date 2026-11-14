"""Read-only trace of agent submissions and the orphaned harness cache."""
import json
import importlib.metadata
import re
import subprocess
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[4]
OLD=Path('/home/sankalp/projects/cis695-agent-reliability')


def build(audit,read,load,sha):
 def attempt(folder):
  record=load(folder/'repair_record.json');raw=read(folder/'submission_raw.txt')
  trajectory_bytes=read(folder/'trajectory.jsonl');trajectory=[json.loads(l) for l in trajectory_bytes.splitlines()]
  exit_rows=[(n,m) for n,m in enumerate(trajectory,1) if m.get('role')=='exit']
  assert exit_rows and exit_rows[-1][1]['content'].encode()==raw
  patch=raw.decode().partition('<<<END_CLAIM>>>')[2].lstrip('\n').encode() if b'<<<END_CLAIM>>>' in raw else raw
  frozen=read(folder/'patch.diff');assert patch==frozen
  meta=yaml.safe_load(read(folder.parents[1]/'meta.yaml'))
  return {'directory':str(folder),'trajectory_id':sha(trajectory_bytes),'trajectory_exit_row':exit_rows[-1][0],
   'submission_raw_sha256':sha(raw),'submitted_patch_sha256':sha(patch),'submitted_patch_bytes':len(patch),
   'started_at_UTC':record['started_at'],'finished_at_UTC':record['finished_at'],'termination':record['termination'],
   'agent_scaffold':record['agent_scaffold'],'agent_version':record['agent_version'],'launch_commit':meta['git_commit'],
   'oracle_evaluated_at_UTC':load(folder/'oracle_record.json').get('evaluated_at') if (folder/'oracle_record.json').exists() else None}
 cases=[]
 for row in audit['all_tasks']:
  if row['classification']!='BINDING_MISMATCH':continue
  current=attempt(Path(row['frozen_patch_path']).parent)
  assert current['submitted_patch_sha256']==row['frozen_patch_sha256']
  prior=[attempt(d) for d in sorted(OLD.glob('runs/_excluded*/tasks/'+row['task']))]
  matched=[a for a in prior if a['submitted_patch_sha256']==row['applied_patch_sha256']]
  assert matched
  matched.sort(key=lambda a:a['started_at_UTC'])
  cache_log=read(Path(current['directory'])/'harness.log').decode(errors='replace')
  assert 'already run, skipping' in cache_log and 'No instances to run.' in cache_log
  oracle=load(Path(current['directory'])/'oracle_record.json')
  first_grade=matched[0]
  assert first_grade['finished_at_UTC']<current['started_at_UTC']
  assert first_grade['oracle_evaluated_at_UTC']<current['started_at_UTC']
  cases.append({'task':row['task'],'run_id':oracle['harness_run_id'],'current_final_answer':current,
   'archived_graded_final_answer':first_grade,'all_excluded_attempts':prior,
   'grader_applied_sha256':row['applied_patch_sha256'],'oracle_declares_current_hash':oracle['patch_sha256'],
   'replacement_oracle_evaluated_at_UTC':oracle['evaluated_at'],
   'harness_cache_hit_lines':[l for l in cache_log.splitlines() if 'already run' in l or 'No instances' in l],
   'grader_log_first_timestamp':read(Path(row['grader_directory'])/'run_instance.log').decode(errors='replace').splitlines()[0].split(' - INFO -')[0]})
 # All locally retained source batches, including matching hashes. This is a
 # provenance scan only; no excluded-run outcomes enter propagated metrics.
 scans=[]
 oracle_paths=list(OLD.glob('runs/*/tasks/*/oracle_record.json'))
 oracle_paths += [p for p in OLD.glob('runs/*/tasks/*/oracle_verdict.json') if not (p.parent/'oracle_record.json').exists()]
 for op in sorted(oracle_paths):
  oracle=load(op);folder=op.parent;frozen=folder/'patch.diff';report=oracle.get('report_file')
  if frozen.exists() and frozen.stat().st_size==0:continue # no harness invocation expected
  hlog=folder/'harness.log';text=read(hlog).decode(errors='replace') if hlog.exists() else ''
  graded=Path(report).parent/'patch.diff' if report else None
  fsha=sha(read(frozen)) if frozen.exists() else None
  gsha=sha(read(graded)) if graded is not None and graded.exists() else None
  scans.append({'batch':folder.parents[1].name,'task':folder.name,'run_id':oracle.get('harness_run_id'),
   'cache_hit':'already run, skipping' in text,'hash_matches':fsha==gsha if fsha and gsha else None,'frozen_sha256':fsha,'applied_sha256':gsha,'missing_binding_evidence':not(fsha and gsha)})
 code=[]
 for revision in sorted({a['launch_commit'] for c in cases for a in [c['current_final_answer'],*c['all_excluded_attempts']]}):
  for path in ['src/reliability/agent/runner.py','src/reliability/agent/freeze.py','src/reliability/oracle/runner.py','scripts/run_pilot.py']:
   data=subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT)
   text=data.decode();matches=[{'line':n,'text':l.strip()} for n,l in enumerate(text.splitlines(),1) if any(s in l for s in ['def _split_submission','partition(CLAIM_DELIMITER)','def freeze_patch','run_id = f','patch_sha256=record.patch.sha256','report = _find_instance_report','run_root already','already holds a run'])]
   code.append({'revision':revision,'path':path,'sha256':sha(data),'anchors':matches})
 preparer=ROOT/'reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/prepare_posthoc_evaluation.py'
 read(preparer)
 harness_path=ROOT/'.venv/lib/python3.11/site-packages/swebench/harness/run_evaluation.py'
 harness_source=read(harness_path).decode()
 harness={'version':importlib.metadata.version('swebench'),'path':str(harness_path),'sha256':sha(harness_source.encode()),'anchors':[{'line':n,'text':l.strip()} for n,l in enumerate(harness_source.splitlines(),1) if any(s in l for s in ['if report_path.exists():','if report_file.exists():','instances already run, skipping'])]}
 for path in ['src/reliability/agent/runner.py','src/reliability/agent/freeze.py','src/reliability/oracle/runner.py','scripts/run_pilot.py','docs/checklist.md']:
  read(ROOT/path)
 restart_notes=[{'path':'docs/checklist.md','line':n,'excerpt':l[:600]} for n,l in enumerate((ROOT/'docs/checklist.md').read_text().splitlines(),1) if 'main_50_' in l and ('halted' in l or 'restarts fresh' in l)]
 return {'cases':cases,'all_batch_cache_scan':scans,'historical_code':code,'harness_cache_implementation':harness,
  'restart_documentation':restart_notes,
  'sidecar_preparation_commit':subprocess.check_output(['git','log','-1','--format=%H %aI','--',str(preparer.relative_to(ROOT))],cwd=ROOT,text=True).strip(),
  'explanation':'Run directories were archived and fresh agents reused the same experiment/task identifiers. Harness reports under logs/run_evaluation retained the same run_id/model/task key. Cache reuse checks report existence, not prediction hash. The oracle stamped the current repair hash onto the cached report; the sidecar joined the CSV oracle status to a separately verified frozen hash.'}
