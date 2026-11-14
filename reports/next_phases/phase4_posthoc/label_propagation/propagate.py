#!/usr/bin/env python3
"""Read-only label propagation over fixed reported decisions and cohorts.

Writes only this analysis directory, a NEW audited_labels.csv, and presentation
notes. Does not run Docker, models, benchmarks, verifiers, or original scripts.
A/B/B-cpu are label overlays; every recorded prediction/threshold stays fixed.
"""
import collections
import csv
import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AUDIT=OUT.parent/'label_audit'
OLD=Path('/home/sankalp/projects/cis695-agent-reliability')
PAIRED=ROOT/'reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z'
sys.path.insert(0,str(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal'))
import compute_seal
import root_cause
from scipy.stats import beta
INPUTS={}
VALUES={}
FAMILIES={}
SETS=('A','B','B-cpu')


def sha(b):return hashlib.sha256(b).hexdigest()


def read(path):
 p=Path(path);b=p.read_bytes();INPUTS[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(b);return b


def load(path):return json.loads(read(path))


def rows(path):return list(csv.DictReader(io.StringIO(read(path).decode())))


def dump(path,x):path.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')


def csvout(path,data,fields=None):
 out=io.StringIO();w=csv.DictWriter(out,fieldnames=fields or list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data);path.write_text(out.getvalue())


def cp(k,n):
 assert 0<=k<=n
 return [0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1.0 if k==n else float(beta.ppf(.975,k+1,n-k))] if n else None


def value(setname,context,metric,k,n=None,kind='count'):
 key=(context,metric)
 if n is None:v={'value':k,'numerator':None,'denominator':None,'CI95':None,'kind':kind}
 else:v={'value':k/n if n else None,'numerator':k,'denominator':n,'CI95':cp(k,n) if kind=='proportion' else None,'kind':kind}
 assert setname not in VALUES.setdefault(key,{ }),key
 VALUES[key][setname]=v


def ratio(s,c,m,k,n):value(s,c,m,k,n,'proportion')


def score(s,c,m,k,n):value(s,c,m,k,n,'derived_score_not_binomial')


def register(context,reports,unit='task'):
 FAMILIES[context]={'reports':reports,'unit':unit}


def signals(context,signals,labels,reports,positive=('FAIL',)):
 register(context,reports)
 ids=sorted(signals)
 for sn,labs in labels.items():
  good=[i for i in ids if labs.get(i)=='correct'];bad=[i for i in ids if labs.get(i)=='incorrect']
  eligible=good+bad;n=len(eligible)
  value(sn,context,'label.correct',len(good));value(sn,context,'label.incorrect',len(bad))
  ratio(sn,context,'label.incorrect_share',len(bad),n)
  binary=[i for i in eligible if signals[i] in set(positive)|{'PASS'}]
  ratio(sn,context,'binary_coverage',len(binary),n)
  for label,group in [('correct',good),('incorrect',bad)]:
   for outcome in sorted(set(signals.values())):
    k=sum(signals[i]==outcome for i in group)
    value(sn,context,f'{label}.{outcome}.count',k)
    ratio(sn,context,f'{label}.{outcome}.share',k,len(group))
  tp=sum(signals[i] in positive for i in bad);fp=sum(signals[i] in positive for i in good)
  fn=sum(signals[i]=='PASS' for i in bad);tn=sum(signals[i]=='PASS' for i in good)
  value(sn,context,'TP_wrong_FAIL',tp);value(sn,context,'FP_correct_FAIL',fp);value(sn,context,'FN_wrong_PASS',fn)
  ratio(sn,context,'detection_all_incorrect',tp,len(bad));ratio(sn,context,'detection_verdicted_incorrect',tp,tp+fn)
  ratio(sn,context,'false_alarm_all_correct',fp,len(good));ratio(sn,context,'false_alarm_verdicted_correct',fp,fp+tn)
  ratio(sn,context,'missed_all_incorrect',fn,len(bad));ratio(sn,context,'missed_verdicted_incorrect',fn,tp+fn)
  ratio(sn,context,'FAIL_precision',tp,tp+fp)
  score(sn,context,'F1_binary',2*tp,2*tp+fp+fn);score(sn,context,'F1_all_labelled',2*tp,tp+fp+len(bad))


def policy(context,decisions,labels,reports):
 register(context,reports)
 for sn,labs in labels.items():
  ids=sorted(decisions);good=[i for i in ids if labs[i]=='correct'];bad=[i for i in ids if labs[i]!='correct']
  for name,g in [('correct',good),('incorrect_or_empty',bad)]:
   value(sn,context,'label.'+name,len(g))
   for d in ['ACCEPT','FLAG','REJECT']:
    k=sum(decisions[i]==d for i in g);value(sn,context,name+'.'+d,k);ratio(sn,context,name+'.'+d+'.share',k,len(g))
  for name in ['incorrect','empty']:
   g=[i for i in ids if labs[i]==name]
   for d in ['ACCEPT','FLAG','REJECT']:
    k=sum(decisions[i]==d for i in g);value(sn,context,name+'.'+d,k);ratio(sn,context,name+'.'+d+'.share',k,len(g))
  accepted=[i for i in ids if decisions[i]=='ACCEPT'];tp=sum(labs[i]=='correct' for i in accepted);fp=len(accepted)-tp
  fn=len(good)-tp;tn=len(bad)-fp
  value(sn,context,'accepted_right',tp);value(sn,context,'false_accepts',fp)
  ratio(sn,context,'ACCEPT_precision',tp,len(accepted));ratio(sn,context,'false_acceptance_proportion',fp,len(accepted))
  ratio(sn,context,'correct_acceptance_recall',tp,len(good));ratio(sn,context,'wrong_withholding_recall',tn,len(bad))
  ratio(sn,context,'ACCEPT_coverage',len(accepted),len(ids));ratio(sn,context,'accuracy',tp+tn,len(ids))
  ratio(sn,context,'unsafe_detection_precision',tn,tn+fn)
  score(sn,context,'F1_accept_correct',2*tp,2*tp+fp+fn);score(sn,context,'F1_withhold_wrong',2*tn,2*tn+fp+fn)


def audited_labels(audit):
 labels={sn:{} for sn in SETS};out=[];gh={(g['task'],g['profile']):g for g in audit['audited_grades']}
 for r in audit['all_tasks']:
  iid=r['task'];a=r['original_label'];b=a if r['classification']=='SUPPORTED' else gh[iid,'default']['audited_grade']
  cpu=gh[iid,'cpu2048']['audited_grade'] if (iid,'cpu2048') in gh else b
  labels['A'][iid]=a;labels['B'][iid]=b;labels['B-cpu'][iid]=cpu
  source='SUPPORTED original' if r['classification']=='SUPPORTED' else 'regrade'
  gd=gh.get((iid,'default'),{}).get('artifact_sha256',{});gc=gh.get((iid,'cpu2048'),{}).get('artifact_sha256',{})
  out.append({'task':iid,'frozen_candidate_sha256':r['frozen_patch_sha256'],'original_label':a,'audited_label_default':b,'CPU_2048_sensitivity_label':cpu,'source':source,'CPU_source':'regrade cpu2048' if gc else source,'classification':r['classification'],'original_labels_SHA256':'cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990','audit_analysis_SHA256':sha(read(AUDIT/'analysis.json')),'original_grader_report_SHA256':audit['input_sha256'].get(r['label_report_path'],''),'default_report_SHA256':gd.get('report.json',''),'default_test_output_SHA256':gd.get('test_output.txt',''),'CPU_report_SHA256':gc.get('report.json',''),'CPU_test_output_SHA256':gc.get('test_output.txt','')})
 assert collections.Counter(labels['A'].values())=={'correct':69,'incorrect':14}
 assert collections.Counter(labels['B'].values())=={'correct':70,'incorrect':13}
 assert collections.Counter(labels['B-cpu'].values())=={'correct':72,'incorrect':11}
 csvout(AUDIT/'audited_labels.csv',out)
 return labels


def cohorts(main):
 # Existing sensitivity populations are retained, with original labels outside
 # the frozen 83 left unchanged. No audited grade is transferred by task ID
 # to any different-patch excluded/pilot run.
 return {'headline83':[r for r in main if r['stratum']=='headline' and r['oracle'] in ['resolved','unresolved']],
  'all_nonempty89':[r for r in main if r['oracle'] in ['resolved','unresolved']],
  'requests_nonempty6':[r for r in main if r['stratum']=='requests' and r['oracle'] in ['resolved','unresolved']],
  'all100_sensitivity':main,'headline93_including_empty':[r for r in main if r['stratum']=='headline'],
  'half_A50':[r for r in main if r['half']=='A'],'half_B50':[r for r in main if r['half']=='B']}


def propagate(audit,labels):
 main=rows(ROOT/'docs/results_100.csv');assert len(main)==100
 all_labels={sn:{r['instance_id']:labels[sn].get(r['instance_id'],{'resolved':'correct','unresolved':'incorrect','empty_patch':'empty'}[r['oracle']]) for r in main} for sn in SETS}
 mainby={r['instance_id']:r for r in main};frozen_policy=rows(ROOT/'reports/policy_comparison/per_task.csv');pb={r['instance_id']:r for r in frozen_policy}
 for r in main:
  assert pb[r['instance_id']]['oracle']==r['oracle']
  assert pb[r['instance_id']]['full_decision']==r['verifier_decision']
 for name,group in cohorts(main).items():
  ids={r['instance_id'] for r in group}
  for sig,field in [('V1','integrity'),('V2','regression'),('V3','static'),('V4','reproduction')]:
   signals('main/'+name+'/'+sig,{r['instance_id']:r[field] for r in group},all_labels,['docs/results_100.md','reports/failure_analysis/failure_analysis.md','reports/next_steps/report.md','reports/v2_diagnostic/report.md'])
  for pol in ['baseline','full']:
   policy('policy/'+name+'/'+pol,{i:pb[i][pol+'_decision'] for i in ids},all_labels,['reports/policy_comparison/report.md','docs/results_100.md'])
  c='claims/'+name;register(c,['docs/results_100.md','src/reliability/analysis/metrics.py'])
  for sn,labs in all_labels.items():
   valid=[r for r in group if r['oracle'] in ['resolved','unresolved']];claimed=[r for r in valid if r['claim']=='RESOLVED']
   correct=sum(labs[r['instance_id']]=='correct' for r in claimed)
   ratio(sn,c,'RESOLVED_claim_precision',correct,len(claimed));ratio(sn,c,'resolution_rate',sum(labs[r['instance_id']]=='correct' for r in valid),len(valid))
   value(sn,c,'correct_count',sum(labs[r['instance_id']]=='correct' for r in valid));value(sn,c,'incorrect_count',sum(labs[r['instance_id']]=='incorrect' for r in valid))
  # Keep the original policy comparison's exact paired tests and fixed seed.
  if name in ['headline83','all_nonempty89']:
   sys.path.insert(0,str(ROOT/'reports/policy_comparison'))
   import statistics_core as stats
   read(ROOT/'reports/policy_comparison/statistics_core.py')
   for sn,labs in all_labels.items():
    rr=[dict(r,oracle='resolved' if labs[r['instance_id']]=='correct' else 'unresolved') for r in frozen_policy if r['instance_id'] in ids]
    paired=stats.paired_exact(rr);ctx='paired_policy/'+name;register(ctx,['reports/policy_comparison/report.md'])
    for metric in ['stopped_count','stopped_wrong','stopped_right','baseline_accepted_wrong']:
     value(sn,ctx,metric,paired[metric])
    ratio(sn,ctx,'stopped_wrong_share',paired['stopped_wrong'],paired['stopped_count'])
    for metric in ['enrichment_exact_one_sided_p','correctness_mcnemar_exact_two_sided_p']:
     value(sn,ctx,metric,paired[metric],kind='exact_test_p_value')
    if name=='headline83':
     boot,_=stats.paired_bootstrap(rr,seed=stats.BOOTSTRAP_SEED,resamples=stats.BOOTSTRAP_RESAMPLES)
     for metric,b in boot['differences'].items():
      for key,v in b.items():
       if isinstance(v,(int,float)) and not isinstance(v,bool):value(sn,ctx,'bootstrap_difference.'+metric+'.'+key,v,kind='paired_bootstrap_summary')
  # The previously published hypothetical pytest-7432 label sensitivity is
  # retained as such, not substituted for its actual audited grade.
  if name in ['headline83','all_nonempty89']:
   hypothetical={sn:dict(l,**{'pytest-dev__pytest-7432':'incorrect'}) for sn,l in all_labels.items()}
   for pol in ['baseline','full']:policy('policy/'+name+'/PYTEST7432_hypothetical/'+pol,{i:pb[i][pol+'_decision'] for i in ids},hypothetical,['reports/policy_comparison/report.md'])
 # Headline per-repository signal/error tables from next_steps and scoring audit.
 for repo in sorted({r['repo'] for r in cohorts(main)['headline83']}):
  g=[r for r in cohorts(main)['headline83'] if r['repo']==repo]
  for sig,field in [('V1','integrity'),('V2','regression'),('V3','static'),('V4','reproduction')]:signals('main/repo/'+repo+'/'+sig,{r['instance_id']:r[field] for r in g},all_labels,['reports/next_steps/phase2_counts_by_repo.csv','reports/v2_scoring_audit/resume_20261026/metrics_by_repo.csv'])
 # Fixed original V2 vs SCG execution: use stored final outcomes only.
 for arm in ['v2','scg']:
  inventory=rows(PAIRED/'task_arm_inventory.csv');outcomes={r['instance_id']:r['signal'] or 'NO_VERDICT' for r in inventory if r['arm']==arm}
  assert len(outcomes)==83
  signals('paired83/'+arm,outcomes,labels,[str((PAIRED/'FINAL_SCIENTIFIC_REPORT.md').relative_to(ROOT)),'scripts/v2_scg_paired.py'])
 # Sealed Phase 4 policies, including the registered secondary REGRESSION_ERROR.
 seal=load(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal/results.json')
 for p in compute_seal.POLICIES:
  outcomes={r['task']:r['policies'][p] for r in seal['per_task']}
  signals('phase4/'+p,outcomes,labels,['reports/next_phases/phase4_posthoc/analysis.md','reports/next_phases/phase4_posthoc/label_audit/analysis.md','reports/next_phases/PRESENTATION_NOTES.md'])
  signals('phase4/'+p+'/secondary',outcomes,labels,['reports/next_phases/phase4_posthoc/analysis.md'],positive=('FAIL','REGRESSION_ERROR'))
 # Existing raw scoring audit cohorts and outcomes; no replay or rescoring.
 old=rows(ROOT/'reports/v2_scoring_audit/resume_20261026/old_vs_fixed.csv');ob={r['instance_id']:r for r in old}
 met=rows(ROOT/'reports/v2_scoring_audit/resume_20261026/metrics_before_after.csv')
 for r in met:
  ids=json.loads(r['subset_ids']);version=r['version'];col={'committed_original_same_new_raw_subset':'original_study_v2','old_parser_replay_same_raw':'old_parser_on_audit_raw','proposed_parser_replay_same_raw':'fixed_parser_on_same_raw'}[version]
  context='scoring_audit/'+r['population']+'/'+version
  signals(context,{i:ob[i][col] or 'NO_VERDICT' for i in ids},labels,['reports/v2_scoring_audit/resume_20261026/report.md'])
  for repo in sorted({mainby[i]['repo'] for i in ids}):
   signals(context+'/repo/'+repo,{i:ob[i][col] or 'NO_VERDICT' for i in ids if mainby[i]['repo']==repo},labels,['reports/v2_scoring_audit/resume_20261026/metrics_by_repo.csv'])
  for sn,labs in labels.items():
   wrong=sum(v=='incorrect' for v in labs.values());ratio(sn,context,'requested_global_wrong_rate',wrong,83)
   prec=VALUES[context,'FAIL_precision'][sn]['value']
   value(sn,context,'FAIL_precision_minus_global_wrong_rate',prec-wrong/83 if prec is not None else None,kind='derived_difference')
 signals('scoring_audit/original_targeted8',{r['instance_id']:r['original_study_v2'] for r in old},labels,['reports/v2_scoring_audit/report.md','reports/v2_scoring_audit/resume_20261026/report.md'])
 ctx='scoring_audit/blocked_global_reference';register(ctx,['reports/v2_scoring_audit/metrics_before_after.csv','reports/v2_scoring_audit/report.md'])
 for sn,labs in labels.items():ratio(sn,ctx,'global_wrong_rate',sum(v=='incorrect' for v in labs.values()),83)
 # Published skip-dependent and historical witness cohorts remain fixed.
 posthoc=load(ROOT/'reports/next_phases/phase4_posthoc/analysis.json')
 groups={'skip_dependent13':posthoc['skip_dependent']['tasks'] if isinstance(posthoc['skip_dependent'].get('tasks'),list) else []}
 # Fixed preregistered IDs are supplied by the historical labels table.
 skip=rows(ROOT/'reports/next_phases/phase2_incomplete_causes/accepted_PASS_labels_POST_HOC_ONLY.csv')
 groups['skip_dependent13']=sorted({r['task'] if 'task' in r else r['instance_id'] for r in skip})
 witnesses=posthoc['witness_groups']['grader_failing_pre_existing'];groups['grader_witness_tasks4']=sorted({r['task'] for r in witnesses})
 ctx='cohort/grader_witness_tests7';register(ctx,['reports/next_phases/phase4_posthoc/analysis.md','reports/next_phases/phase4_posthoc/grader_gap/analysis.md'],'test identity, clustered within task')
 for sn,labs in labels.items():
  wrong=[r for r in witnesses if labs[r['task']]=='incorrect']
  passing=sum(r['trees']['patched']['status']=='passed' for r in wrong)
  value(sn,ctx,'incorrect_labelled_test_count',len(wrong));value(sn,ctx,'PASS_on_incorrect_patch',passing)
  ratio(sn,ctx,'passing_share_on_incorrect_labelled_tasks',passing,len(wrong))
 ctx='provenance/frozen83';register(ctx,['reports/next_phases/phase4_posthoc/label_audit/analysis.md'])
 for sn in SETS:ratio(sn,ctx,'binding_mismatch_share',9,83)
 for name,ids in groups.items():
  ctx='cohort/'+name;register(ctx,['reports/next_phases/PRESENTATION_NOTES.md','reports/next_phases/phase2_incomplete_causes/ACCEPTED_SKIP_LABELS_POST_HOC_ONLY.md','reports/next_phases/phase4_posthoc/grader_gap/analysis.md'])
  for sn,labs in labels.items():
   bad=sum(labs[i]=='incorrect' for i in ids);value(sn,ctx,'incorrect_count',bad);ratio(sn,ctx,'incorrect_share',bad,len(ids))
   if name=='grader_witness_tasks4':ratio(sn,ctx,'witness_ceiling_over_all_incorrect',bad,sum(l=='incorrect' for l in labs.values()))
 # Selector retention counts have already-frozen test identities. Reweight only
 # their task-label cohorts, retaining all historical identity caveats.
 retain=rows(ROOT/'reports/next_steps/phase3_metrics.csv')
 for selector in sorted({r['selector'] for r in retain}):
  rr=[r for r in retain if r['selector']==selector];ctx='selector_wrong_cohort/'+selector;register(ctx,['reports/next_steps/report.md','reports/next_steps/phase3_metrics.csv'],'test identity within task')
  for sn,labs in labels.items():
   wrong=[r for r in rr if labs[r['instance_id']]=='incorrect'];value(sn,ctx,'incorrect_tasks',len(wrong))
   for prefix in ['official_failures','official_changed_behavior_F2P','existing_suite_opportunity_witnesses']:
    measured=[r for r in wrong if r[prefix+'_total']!='' and r[prefix+'_retained']!='']
    value(sn,ctx,prefix+'.unknown_tasks',len(wrong)-len(measured))
    total=sum(int(r[prefix+'_total']) for r in measured);kept=sum(int(r[prefix+'_retained']) for r in measured)
    value(sn,ctx,prefix+'.total',total);value(sn,ctx,prefix+'.retained',kept);ratio(sn,ctx,prefix+'.retention',kept,total)
 # Diagnostic's original wrong-patch test inventory: the captured old grader
 # tests remain fixed. Do not relabel old captures as new regrade observations.
 wp=rows(ROOT/'reports/v2_diagnostic/wrong_patch_tests.csv');ctx='diagnostic/fixed_failure_inventory';register(ctx,['reports/v2_diagnostic/report.md'],'recorded test identity')
 for sn,labs in labels.items():
  rr=[r for r in wp if labs.get(r['instance_id'])=='incorrect'];value(sn,ctx,'test_rows_on_incorrect_labelled_tasks',len(rr))
  for cat in sorted({r['category'] for r in wp}):
   k=sum(r['category']==cat for r in rr);value(sn,ctx,'category.'+cat,k);ratio(sn,ctx,'category.'+cat+'.share',k,len(rr))
 sample=rows(ROOT/'reports/v2_diagnostic/sample_patches.csv')
 signals('diagnostic/sample3',{r['instance_id']:r['v2_outcome'] for r in sample},labels,['reports/v2_diagnostic/sample_report.md'])
 sampletests=rows(ROOT/'reports/v2_diagnostic/sample_wrong_patch_tests.csv');ctx='diagnostic/sample_fixed_failure_inventory';register(ctx,['reports/v2_diagnostic/sample_report.md'],'recorded test identity')
 for sn,labs in labels.items():
  rr=[r for r in sampletests if labs[r['instance_id']]=='incorrect'];value(sn,ctx,'test_rows_on_incorrect_labelled_tasks',len(rr))
  for cat in sorted({r['category'] for r in sampletests}):value(sn,ctx,'category.'+cat,sum(r['category']==cat for r in rr))
 # Historical five shadow cases use independent superseded-assertion class
 # labels, not patch correctness. Those agreements must not be relabelled.
 ctx='shadow/historical_wrong_patch_detection';register(ctx,['scripts/v2_stabilization_finish.py','reports/v2_stabilization/classifier_v2/downstream_audit.json'])
 for sn,labs in labels.items():ratio(sn,ctx,'historical_detection_over_wrong',1,sum(l=='incorrect' for l in labs.values()))
 ctx='cohort/independent_superseded_cases5';register(ctx,['reports/failure_analysis/group4_gold_check.json','reports/v2_stabilization/classifier_v2/downstream_audit.json'])
 ids=[r['instance_id'] for r in load(ROOT/'reports/v2_stabilization/shadow_predictions.json')['cases']]
 for sn,labs in labels.items():ratio(sn,ctx,'correct_labelled_share',sum(labs[i]=='correct' for i in ids),len(ids))
 return main,all_labels


CONSUMERS=[
 ('Main study signals and claims','src/reliability/analysis/metrics.py;scripts/metrics.py;scripts/interim_report.py;scripts/run_pilot.py','docs/results_100.md;reports/pilot_summary.md;reports/smoke_3.1.md','main/*;claims/*;policy/*','Original headline, half and all-study populations; pilot/alternate-candidate rows are not relabelled by task ID.'),
 ('Baseline versus Full assessment','reports/policy_comparison/compare.py;reports/policy_comparison/reconstruction.py;reports/policy_comparison/statistics_core.py;reports/policy_comparison/render_report.py','reports/policy_comparison/report.md;reports/policy_comparison/metrics.csv','policy/*;paired_policy/*','Frozen ACCEPT/FLAG/REJECT decisions; original hypothetical pytest-7432 sensitivity retained.'),
 ('Failure diagnosis','reports/failure_analysis/extract_evidence.py;reports/failure_analysis/compact_overview.py;reports/failure_analysis/rerun_group4_regression.py;scripts/old_assertion_check.py;scripts/old_assertion_check_gold.py','reports/failure_analysis/failure_analysis.md;reports/failure_analysis/failure_analysis.csv','main/headline83/*;cohort/grader_witness_tasks4','Task label annotations and main-study counts propagate; independent superseded-assertion classes and raw historical test statuses do not.'),
 ('V2 oracle post-hoc diagnosis','reports/v2_diagnostic/oracle_posthoc.py;reports/v2_diagnostic/diagnostic.py','reports/v2_diagnostic/report.md;reports/v2_diagnostic/sample_report.md;reports/v2_diagnostic/patches.csv;reports/v2_diagnostic/wrong_patch_tests.csv','main/headline83/V2;diagnostic/*','The fixed old failure inventory is not made into fresh grader evidence for mismatched candidates.'),
 ('Earlier selector opportunity analysis','reports/next_steps/analyze.py','reports/next_steps/report.md;reports/next_steps/phase2_counts_by_repo.csv;reports/next_steps/phase3_metrics.csv','main/repo/*;selector_wrong_cohort/*','Selector identities and historical reference lists stay fixed; label-cohort weighting only.'),
 ('V2 raw-scoring audit','reports/v2_scoring_audit/audit.py;reports/v2_scoring_audit/finish_blocked.py;reports/v2_scoring_audit/resume_20261026/analyze_resume.py;reports/v2_scoring_audit/resume_20261026/finish_resume.py','reports/v2_scoring_audit/report.md;reports/v2_scoring_audit/resume_20261026/report.md;reports/v2_scoring_audit/resume_20261026/metrics_before_after.csv','scoring_audit/*;main/headline83/V2;main/repo/*/V2','Original 8-target and exact three-/one-task observed cohorts retained; unavailable raw data never becomes a new verdict.'),
 ('Frozen V2 versus SCG','scripts/v2_evaluation.py;scripts/v2_scg_paired.py;reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/analyze_completed.py;reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/finalize_analysis.py','reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/FINAL_SCIENTIFIC_REPORT.md;reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/PRESENTATION_SUMMARY.md','paired83/*','Recorded final V2/SCG outcomes, including no-verdict states, preserved. Label-free runtime/selection comparisons unchanged.'),
 ('Sidecar binding','reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/prepare_posthoc_evaluation.py','reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/sidecar_provenance.json','cohort/*','This joined CSV labels and frozen export hashes without checking the archived applied-patch hash; original sidecar remains untouched.'),
 ('Exploratory shadow classification','scripts/v2_stabilization_finish.py;scripts/v2_shadow_five.py;scripts/v2_shadow_five_v2.py','reports/v2_stabilization/classifier_v2/downstream_audit.json;reports/v2_stabilization/classifier_v2/live_summary.json','shadow/*','Five superseded-assertion class labels are independent labels, not patch-correctness labels. Their class agreement is unchanged; global wrong-patch denominator propagates.'),
 ('Skip-dependent post-hoc labels','scripts/phase2_policy_projection.py','reports/next_phases/phase2_incomplete_causes/ACCEPTED_SKIP_LABELS_POST_HOC_ONLY.md;reports/next_phases/phase2_incomplete_causes/accepted_PASS_labels_POST_HOC_ONLY.json','cohort/skip_dependent13','Exactly the frozen 13-task cohort; no selection or skip policy changes.'),
 ('Known old-test witnesses','scripts/phase1_known_failures.py;reports/next_phases/phase4_posthoc/grader_gap/analyze.py','reports/next_phases/phase1_known_failures/SUMMARY.md;reports/next_phases/phase4_posthoc/grader_gap/analysis.md','cohort/grader_witness_tasks4','Historical nominal ceiling is qualified by skips and mismatched patch binding; root cause does not edit old test outcomes.'),
 ('Sealed post-hoc quantities','reports/next_phases/phase4_posthoc/analysis.py;reports/next_phases/phase4_posthoc/label_audit/audit.py','reports/next_phases/phase4_posthoc/analysis.md;reports/next_phases/phase4_posthoc/label_audit/analysis.md','phase4/*','All four policies and registered secondary REGRESSION_ERROR counting; pre-registered H1/H1b/H2/H3 label-free and unchanged.'),
 ('Presentation restatements','static report notes','reports/next_phases/PRESENTATION_NOTES.md;reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/PRESENTATION_SUMMARY.md','main/*;policy/*;paired83/*;phase4/*;cohort/*','Only a new integrity slide note is added. Older reports remain historical originals; this report supplies the corrections.')]


def consumer_inventory():
 consumer_rows=[dict(zip(['consumer','code','reports','metric_families','scope'],r)) for r in CONSUMERS]
 csvout(OUT/'consumers.csv',consumer_rows)
 truecode={p for r in consumer_rows for p in r['code'].split(';')}
 # Broad lexical inventory includes static prose and false matches (oracle-
 # blind guards, terminology, independent class labels). It is not presented
 # as evidence that every occurrence is a label consumer.
 matches=[]
 paths=subprocess.check_output(['git','ls-files','--','*.py','*.md'],cwd=ROOT,text=True).splitlines()
 for relative in paths:
  if not relative.startswith(('src/','scripts/','reports/','docs/','README')):continue
  if relative.startswith('reports/next_phases/phase4_posthoc/label_propagation/'):continue
  if relative.startswith('reports/next_phases/phase4_rerun/'):continue # quarantined run reports are not evidence inputs
  p=ROOT/relative
  if not p.exists():continue
  text=subprocess.check_output(['git','show','8541dd58ef0aff811720975c7d0f94a12709cbef:'+relative],cwd=ROOT).decode() if relative=='reports/next_phases/PRESENTATION_NOTES.md' else p.read_text(errors='replace')
  lines=text.splitlines()
  hits=[(n,l) for n,l in enumerate(lines,1) if re.search(r'correctness|oracle|wrong.patch|false.accept|false.positive',l,re.I)]
  if not hits:continue
  kind='label consumer (mapped above)' if relative in truecode else 'static result/restatement' if p.suffix=='.md' and any(re.search(r'\d',l) and re.search(r'precision|recall|correct|resolved|wrong|false',l,re.I) for _,l in hits) else 'guard, terminology, test, or independent-label use; not a new correctness calculation'
  for n,l in hits:matches.append({'file':relative,'line':n,'classification':kind,'text':l.strip()[:420].rstrip()})
 csvout(OUT/'label_references.csv',matches)
 return consumer_rows,matches


def fmt(v):
 if v['value'] is None:return 'undefined'
 if v['kind']=='count':return str(v['value'])
 if v['kind']=='proportion':
  lo,hi=v['CI95'];return f"{v['numerator']}/{v['denominator']} = {100*v['value']:.2f}% [{100*lo:.2f}%, {100*hi:.2f}%]"
 return f"{v['value']:.6g}"


def emit_tables():
 detailed=[];changed=[]
 for (context,metric),versions in sorted(VALUES.items()):
  assert set(versions)==set(SETS),(context,metric,set(versions))
  for sn in SETS:
   v=versions[sn];ci=v['CI95'] or [None,None]
   detailed.append({'context':context,'metric':metric,'label_set':sn,'kind':v['kind'],'value':v['value'],'numerator':v['numerator'],'denominator':v['denominator'],'CI95_lower':ci[0],'CI95_upper':ci[1]})
  if not (versions['A']==versions['B']==versions['B-cpu']):
   row={'context':context,'metric':metric,'kind':versions['A']['kind'],'A':fmt(versions['A']),'B':fmt(versions['B']),'B-cpu':fmt(versions['B-cpu'])}
   for sn in SETS:
    v=versions[sn];row[sn+'_value']=v['value'];row[sn+'_numerator']=v['numerator'];row[sn+'_denominator']=v['denominator'];row[sn+'_CI95']=json.dumps(v['CI95'])
   changed.append(row)
 csvout(OUT/'metrics.csv',detailed);csvout(OUT/'changed_numbers.csv',changed)
 return changed


def validate(audit):
 # Published original headline confusion matrices must reproduce exactly.
 assert VALUES['policy/headline83/full','accepted_right']['A']['value']==45
 assert VALUES['policy/headline83/full','false_accepts']['A']['value']==7
 assert VALUES['policy/headline83/baseline','accepted_right']['A']['value']==53
 assert VALUES['policy/headline83/baseline','false_accepts']['A']['value']==11
 names={'A':'A_original','B':'B_audited_default','B-cpu':'B_cpu2048_sensitivity'}
 measures=['detection_all_incorrect','detection_verdicted_incorrect','false_alarm_all_correct','false_alarm_verdicted_correct','missed_all_incorrect','missed_verdicted_incorrect']
 for sn,oldname in names.items():
  for p in compute_seal.POLICIES:
   for suffix,rule in [('', 'primary_FAIL_only'),('/secondary','secondary_FAIL_plus_REGRESSION_ERROR')]:
    for metric in measures:
     got=VALUES['phase4/'+p+suffix,metric][sn];expected=audit['tables'][oldname][p]['metrics'][rule][metric]
     assert (got['numerator'],got['denominator'],got['CI95'])==(expected['count'],expected['denominator'],expected['ci95']),(sn,p,metric)
 assert VALUES['cohort/grader_witness_tests7','PASS_on_incorrect_patch']['B-cpu']['value']==0


def render(root,consumers,refs,changed,labels):
 headlines=[('claims/headline83','RESOLVED_claim_precision'),('main/headline83/V1','detection_all_incorrect'),('main/headline83/V2','detection_all_incorrect'),('main/headline83/V3','detection_all_incorrect'),('main/headline83/V4','detection_all_incorrect'),('policy/headline83/full','ACCEPT_precision'),('policy/headline83/full','false_accepts'),('policy/headline83/baseline','ACCEPT_precision'),('policy/headline83/full','correct_acceptance_recall'),('policy/headline83/baseline','correct_acceptance_recall'),('paired83/v2','detection_all_incorrect'),('paired83/scg','detection_all_incorrect'),('phase4/C_invalid_excluded','detection_all_incorrect'),('phase4/C_invalid_excluded','detection_verdicted_incorrect'),('phase4/C_invalid_excluded','false_alarm_all_correct'),('phase4/C_invalid_excluded','false_alarm_verdicted_correct'),('phase4/C_invalid_excluded','missed_all_incorrect'),('phase4/S_invalid_excluded','missed_all_incorrect'),('cohort/skip_dependent13','incorrect_count'),('cohort/grader_witness_tasks4','witness_ceiling_over_all_incorrect')]
 lines=['# Label provenance root cause and propagation','',
 'All computations below are post-hoc label sensitivities. The pre-registered labels, sealed results, executor, predictions, selectors, thresholds, and tags are unchanged. B is primary for interpretation; B-cpu is the requested resource sensitivity. No Docker, agent or benchmark execution is performed.','',
 '## Root cause','',
 'The nine frozen candidates are the final answers from the replacement agent attempts; each raw submission, trajectory exit message, extracted diff, repair record, and frozen SHA agrees. Every mismatched grader patch is instead the exact final answer of an earlier excluded halted attempt, retained in `_excluded_main_50_a_halted` or `_excluded_main_50_b_halted` (one later excluded attempt happens to submit identical bytes too). This is stale evaluation reuse, not a faulty claim/diff extraction or an intermediate agent patch.','',
 'The source run directories were archived and the halves restarted using the same experiment IDs. The external `logs/run_evaluation/<experiment>__<instance>/<model>/<instance>/report.json` namespace survived. The official harness checks whether that path exists and skips completed instances without comparing the prediction hash. All nine newer harness.log files explicitly say **already run, skipping / No instances to run**. The oracle wrapper verifies the new local frozen patch, writes new predictions, then reads the old report and stamps it with `record.patch.sha256`. Later, prepare_posthoc_evaluation.py joins the pinned CSV oracle status to independently checked export hashes; it never checks the actual patch behind the linked report. Thus the original sidecar has a genuine new frozen hash attached to an old attempt’s grade.','',
 '| Task | Earlier final answer: UTC start → finish | Replacement final answer: UTC start → finish | Earlier / replacement launch commits |','|---|---|---|---|']
 for c in root['cases']:
  a,b=c['archived_graded_final_answer'],c['current_final_answer']
  lines.append(f"| {c['task']} | {a['started_at_UTC']} → {a['finished_at_UTC']} | {b['started_at_UTC']} → {b['finished_at_UTC']} | `{a['launch_commit'][:7]}` / `{b['launch_commit'][:7]}` |")
 lines+=['','The complete root_cause.json records both trajectory SHA-256 IDs, exit-message row numbers, submission/frozen hashes and byte sizes, all excluded intermediate attempts, oracle timestamps, first grader-log timestamps, cache-hit lines, and historical source-code hashes/line anchors. Naive grader log timestamps are retained verbatim; agent/oracle timestamps explicitly record UTC. No file modification timestamp is used as the chronology.','',
 'Agent extraction: mini-SWE-agent 2.4.6 → `_split_submission` at `<<<END_CLAIM>>>`, removing only leading LF separators → `freeze_patch` writes exact bytes and a hash, refusing overwrite. The restart created a new task directory rather than overwriting the old read-only patch. The current final answer is authoritative for the frozen experiment; the earlier answer was real but belonged to the excluded attempt. The sidecar preparer was committed at `'+root['sidecar_preparation_commit']+'`.','',
 '## Exposure in other batches','',
 '| Locally retained batch | Oracle/patch records scanned | Explicit cache hits | Hash mismatches | Cache hits with matching hashes | Missing binding evidence |','|---|---:|---:|---:|---:|---:|']
 for batch in sorted({r['batch'] for r in root['all_batch_cache_scan']}):
  rr=[r for r in root['all_batch_cache_scan'] if r['batch']==batch]
  lines.append(f"| {batch} | {len(rr)} | {sum(r['cache_hit'] for r in rr)} | {sum(r['hash_matches'] is False for r in rr)} | {sum(r['cache_hit'] and r['hash_matches'] is True for r in rr)} | {sum(r['missing_binding_evidence'] for r in rr)} |")
 lines+=['','The same structural risk applies to any reuse of experiment/model/instance IDs, including explicit oracle reruns after a changed prediction. The second halted main_50_a attempt demonstrates reuse before the final run; matching hashes on a cache hit demonstrate that a stale grade can remain invisible to a mismatch-only audit. The separately named main_2_rerun_mpl and main_3_rerun_infra records have distinct namespaces and no local cache-hit evidence. The older smoke record is also inventoried; its applied-patch evidence is unavailable locally, so its binding cannot be certified. This is a census of retained local records, not a claim that deleted or unavailable pilot batches are safe. No excluded attempt is pooled into propagated performance metrics.','',
 '## Separate audited label artifact','',
 '`../label_audit/audited_labels.csv` contains all 83 frozen hashes, A/B/B-cpu labels, SUPPORTED-original versus regrade provenance, and original/default/CPU report and output hashes. It is a new artifact; correctness_sidecar.json and the pinned CSV remain unchanged and remain the pre-registered A set.','',
 '| Set | Correct | Incorrect |','|---|---:|---:|']
 for sn in SETS:lines.append(f"| {sn} | {sum(x=='correct' for x in labels[sn].values())} | {sum(x=='incorrect' for x in labels[sn].values())} |")
 lines+=['','A→B changes: Astropy-13977 and Django-13297 become correct; Xarray-6599 becomes incorrect. B→B-cpu changes: Pylint-6528 and Pylint-7277 become correct. These are analytical assignments from audited grades, never replacements for original labels. Labels outside the audited 83 (six nonempty requests and empty-patch rows) retain their original values in the 89/93/100-task sensitivity tables. Different-patch excluded/pilot records are never assigned audited labels just by instance ID.','',
 '## Consumer inventory','',
 f'`consumers.csv` lists {len(consumers)} report families and their code/report paths. `label_references.csv` lists {len(refs)} source/prose keyword references with line numbers, distinguishing direct consumers from static restatements and oracle-blind guards. The inventory covers original V1–V4, combined policy, claims, earlier diagnostics and scoring audits, V2/SCG, Phase 2 skip cohorts, selector retention cohorts, Phase 4 policies, and presentation restatements.','',
 '| Consumer | Code | Reports | Propagated family / limit |','|---|---|---|---|']
 for c in consumers:lines.append('| '+c['consumer']+' | '+c['code'].replace(';','<br>')+' | '+c['reports'].replace(';','<br>')+' | '+c['metric_families']+'; '+c['scope']+' |')
 lines+=['','The H1/H1b/H2/H3 completeness hypotheses, runtimes, test counts, label-free selector criteria, native verdict counts, and independent superseded-assertion class agreement do not consume patch correctness labels and therefore do not move. Labels used as historical annotations move only in this separate analysis. Original reports remain archived originals.','',
 '## Headline numbers under A → B → B-cpu','',
 'Every binomial proportion has an exact two-sided 95% Clopper-Pearson interval. Selector-retention sums include only measured entries; blank historical counts remain unknown and are counted separately, never replaced by zero. `changed_numbers.csv` is the exhaustive flat table of every changed count, numerator, denominator, proportion, interval, derived score or paired statistical summary produced by these registered metric families; `metrics.csv` also retains unchanged values. Values include explicit undefined zero denominators.','',
 '| Context | Measure | A | B | B-cpu |','|---|---|---|---|---|']
 for key in headlines:
  vv=VALUES[key];lines.append('| '+key[0]+' | '+key[1]+' | '+' | '.join(fmt(vv[sn]) for sn in SETS)+' |')
 lines+=['',f'Total changed metric rows: **{len(changed)}**. These rows include the originally reported repository, population and raw-scoring-subset sensitivities; duplicate prose citations map to the same computation rather than pretending to be new experiments.','',
 '## Interpretation and statistical limits','',
 '- B is the primary default-environment interpretation. B-cpu must remain visible because Pylint’s default environment can make otherwise passing old tests skip. No favorable environment is selected as primary after seeing the outcome. Signal correctness rates exclude empty patches, which are not correct/incorrect nonempty candidates; combined-policy including-empty sensitivities preserve the original unsafe-negative convention and retain separate empty columns.',
 '- The original label binding defect is independent of whether a label changes after regrading: all nine mismatches remain provenance failures even when B agrees with A.',
 '- Label propagation cannot repair old grader captures, testcase code, alternative candidate bytes or selector/reference provenance. Historical diagnostic and selector-retention tables keep their fixed identities and are explicitly label sensitivities, not new detection observations. The fixed four-task old-witness ceiling is not expanded with new witnesses found by regrades.',
 '- For signals, FAIL predicts an incorrect patch; PASS is the other binary verdict; incomplete/unavailable outcomes abstain. Phase 4 additionally retains the registered FAIL+REGRESSION_ERROR secondary. For combined policies, ACCEPT predicts correct and FLAG/REJECT withhold. All definitions are unchanged.',
 '- The exact CP intervals apply to binomial proportions. F1 and paired-bootstrap summaries are derived statistics, not binomial proportions, so CP is mathematically inapplicable to them. Existing paired-bootstrap seed 695, 10,000 resamples and row order are retained for policy-score differences; exact McNemar/hypergeometric tests retain their original formulas. Per-test identity proportions are descriptive and clustered within tasks; their CP intervals are not evidence of independent test sampling.',
 '- This analysis does not establish semantic ground truth for harness-resolved patches. The audited labels are grades in the stated environment, and all original metrics remain reproducible under A.','',
 '## Reproduction','',
 '`env -u PYTHONPATH .venv/bin/python reports/next_phases/phase4_posthoc/label_propagation/propagate.py` reads stored evidence only and regenerates the new artifacts plus the added presentation note. The run manifest is verified before data reads. analysis.json records every evidence/code hash, frozen metric family, root trace and numeric value. Run twice and compare output bytes; no historical report generator is invoked and no existing report is overwritten.']
 (OUT/'analysis.md').write_text('\n'.join(l.rstrip() for l in '\n'.join(lines).splitlines())+'\n')
 # Add one explicit slide note; keep both historical notes and audit intact.
 p=ROOT/'reports/next_phases/PRESENTATION_NOTES.md';notes=p.read_text();heading='### Label integrity slide — provenance and propagated headlines'
 note=heading+'\n\n**9/83 mismatched bindings; 3 default label changes; 2 CPU-dependent Pylint labels.** Binding mismatch proportion: '+fmt(VALUES['provenance/frozen83','binding_mismatch_share']['A'])+' (exact 95% CP). Reused harness IDs retained grades from excluded attempts; the wrapper attached current frozen hashes to those cached grades. A stays pre-registered, B is primary for interpretation, and B-cpu is sensitivity.\n\n'
 note+='Changed headline counts (A → B → B-cpu): '+ '; '.join(f"{title}: "+' → '.join(fmt(VALUES[c,m][sn]) for sn in SETS) for title,c,m in [('correct labels','claims/headline83','correct_count'),('Full ACCEPT correct','policy/headline83/full','accepted_right'),('Full false accepts','policy/headline83/full','false_accepts'),('Phase 4 C incorrect PASS','phase4/C_invalid_excluded','FN_wrong_PASS'),('incorrect in fixed skip cohort','cohort/skip_dependent13','incorrect_count'),('old-test PASS on incorrect patches','cohort/grader_witness_tests7','PASS_on_incorrect_patch')])+'. Full rates and exact intervals: [propagation report](phase4_posthoc/label_propagation/analysis.md) and [all changed numbers](phase4_posthoc/label_propagation/changed_numbers.csv). Original labels, sealed results, executor and tags are unchanged.\n\n'
 if heading in notes:
  a=notes.index(heading);b=notes.index('### Cap hit and four disclosures',a);notes=notes[:a]+note+notes[b:]
 else:notes=notes.replace('### Cap hit and four disclosures',note+'### Cap hit and four disclosures')
 p.write_text(notes)


def main():
 _,verification=compute_seal.verify_run()
 audit=load(AUDIT/'analysis.json')
 committed=subprocess.check_output(['git','show','8541dd58ef0aff811720975c7d0f94a12709cbef:reports/next_phases/phase4_posthoc/label_audit/analysis.json'],cwd=ROOT)
 assert sha(committed)==sha((AUDIT/'analysis.json').read_bytes())
 assert sha(read(PAIRED/'correctness_sidecar.json'))=='cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990'
 labels=audited_labels(audit)
 provenance=root_cause.build(audit,read,load,sha);dump(OUT/'root_cause.json',provenance)
 mainrows,all_labels=propagate(audit,labels)
 validate(audit)
 consumers,refs=consumer_inventory();changed=emit_tables()
 read(OUT/'propagate.py');read(OUT/'root_cause.py')
 dump(OUT/'analysis.json',{'manifest_verification':verification,'labels':labels,'root_cause':provenance,'metric_families':FAMILIES,'values':[{'context':c,'metric':m,'sets':v} for (c,m),v in sorted(VALUES.items())],'consumer_families':consumers,'changed_metric_rows':len(changed),'input_sha256':dict(sorted(INPUTS.items())),'executor_or_threshold_changes':False,'new_benchmark_runs':0})
 render(provenance,consumers,refs,changed,labels)
 print(json.dumps({'binding_mismatches_traced':len(provenance['cases']),'source_records_scanned':len(provenance['all_batch_cache_scan']),'consumer_families':len(consumers),'metric_keys':len(VALUES),'changed_metric_rows':len(changed),'output_sha256':{p.name:sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file()}},sort_keys=True))

if __name__=='__main__':main()
