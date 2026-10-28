"""Offline comparison of frozen parser proposal against identical captured logs.

Post-hoc correctness labels are opened only after raw collection is complete and
after diagnostic rows, parser fixtures and scoring outputs have been persisted.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit_resume', OUT/'resume.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
OLD = run.OLD
FIXED = run.parser_namespace(fixed=True)
TS = OLD['TestStatus']


def write_csv(name, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('x',newline='') as f:
        writer=csv.DictWriter(f,fields,lineterminator='\n')
        writer.writeheader()
        for r in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})


def family(t):
    return t.split('[',1)[0]


def read_events(folder):
    p=folder/'batch_events.jsonl'
    return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []


def coverage(folder,selected):
    """Missing outcomes remain missing, independently of either admission parser."""
    emitted=run.raw_cases(folder)
    results={s:[] for s in selected}
    completed=set()
    events=read_events(folder)
    starts={e['batch']:e for e in events if e['event']=='start'}
    for e in events:
        if e['event']=='end' and e['returncode'] in (0,1):
            completed.update(starts[e['batch']]['ids'])
    for tid,status in emitted.items():
        key=tid if tid in results else family(tid)
        if key in results:results[key].append((tid,status.value))
    return results,completed


def repeats(iid):
    folder=OUT/'phase3'/iid
    candidates=json.loads((folder/'candidates.json').read_text())['candidates']
    b=run.raw_cases(OUT/'phase2'/iid/'base/initial')
    p=run.raw_cases(OUT/'phase2'/iid/'patched/initial')
    rows=[]
    for index,tid in enumerate(candidates):
        row={'instance_id':iid,'raw_test_id':tid,'required_repeats_per_tree':3}
        all_statuses={}
        for tree,initial in (('base',b),('patched',p)):
            first=initial.get(tid)
            observed=[]
            attempts=[]
            for repeat in range(1,4):
                f=folder/tree/('candidate_%04d_repeat_%d'%(index,repeat))
                meta=json.loads((f/'attempt.json').read_text())
                status=run.raw_cases(f).get(tid)
                outcome=status.value if status is not None else ('timeout' if meta['driver_state']=='timeout' else 'not_run')
                observed.append(outcome)
                attempts.append({'repeat':repeat,'outcome':outcome,'driver_state':meta['driver_state'],
                                 'raw_log':str((f/'runner.raw').relative_to(OUT)),
                                 'duration_s':meta['duration_s']})
            first_status=first.value if first is not None else 'not_run'
            all_statuses[tree]=[first_status]+observed
            row[tree+'_initial_outcome']=first_status
            row[tree+'_initial_count']=int(first is not None)
            row[tree+'_repeat_outcomes']=observed
            row[tree+'_valid_completed_repeats']=sum(x in {'passed','failed','skipped'} for x in observed)
            for status in ('passed','failed','error','skipped','timeout','not_run'):
                row[tree+'_initial_'+status+'_count']=int(first_status==status)
                row[tree+'_repeat_'+status+'_count']=observed.count(status)
                row[tree+'_total_'+status+'_count']=all_statuses[tree].count(status)
            row[tree+'_attempts']=attempts
        if any('passed' in values and 'failed' in values for values in all_statuses.values()):
            stability='FLAKY'
        elif all(len(v)==4 and len(set(v))==1 and v[0] in {'passed','failed'} for v in all_statuses.values()):
            stability='STABLE'
        else:
            stability='UNKNOWN'
        row['stability']=stability
        if stability=='FLAKY':cause='FLAKY'
        elif stability=='UNKNOWN':cause='UNKNOWN'
        elif row['base_initial_outcome']=='failed':cause='PRE_EXISTING_FAILURE'
        elif row['base_initial_outcome']=='passed' and row['patched_initial_outcome']=='failed':cause='TRUE_REGRESSION'
        else:cause='OTHER'
        row['diagnostic_label']=cause
        row['claim_status']='confirmed' if stability!='UNKNOWN' else 'unresolved'
        rows.append(row)
    return rows


def score(ns, runner, selected, base_raw, patch_raw, stability_rows):
    # Each parser has its own Enum class. Use its own status values and classifier.
    from types import SimpleNamespace
    b=ns['_parse_output'](SimpleNamespace(name=runner),base_raw,tuple(selected))
    p=ns['_parse_output'](SimpleNamespace(name=runner),patch_raw,tuple(selected))
    status=ns['TestStatus']
    outcomes={tid:ns['classify'](tid,
        SimpleNamespace(status=b.get(tid,status.NOT_RUN)),
        SimpleNamespace(status=p.get(tid,status.NOT_RUN))).value for tid in selected}
    concrete_b=run.raw_cases(base_raw[1]) if isinstance(base_raw,tuple) else None
    # The saved audit confirmation evidence is identical for old and fixed.
    # Preserve the production rule: only regression outcomes can become FLAKY.
    for tid,outcome in list(outcomes.items()):
        if outcome!='REGRESSION':continue
        relevant=[r for r in stability_rows if (r['raw_test_id']==tid or family(r['raw_test_id'])==tid)
                  and r['base_initial_outcome']=='passed' and r['patched_initial_outcome']=='failed']
        if relevant and all(r['stability']=='FLAKY' for r in relevant):outcomes[tid]='FLAKY'
    executed_base=[v for v in b.values() if v not in (status.NOT_RUN,status.TIMEOUT)]
    failures=sum(v in (status.FAILED,status.ERROR) for v in executed_base)
    if executed_base and failures/len(executed_base)>0.5:
        signal='BASELINE_UNRELIABLE'
    elif not any(v not in ('NOT_RUN','TIMEOUT') for v in outcomes.values()):signal='NOT_AVAILABLE'
    elif 'REGRESSION' in outcomes.values():signal='FAIL'
    else:signal='PASS'
    return {'raw_signal':signal,'v2_label':'NOT_AVAILABLE' if signal=='BASELINE_UNRELIABLE' else signal,
            'outcome_counts':dict(Counter(outcomes.values())),
            'base_parsed_selected':len(b),'patched_parsed_selected':len(p),
            'regressions':sorted(t for t,v in outcomes.items() if v=='REGRESSION'),
            'base':{t:v.value for t,v in b.items()},'patched':{t:v.value for t,v in p.items()},
            'per_selected_outcomes':outcomes}


def diagnostic_analysis():
    assert (OUT/'collection_complete.json').exists(),'Raw-collection gate still closed'
    run.verify_frozen()
    completed=json.loads((OUT/'collection_complete.json').read_text())['completed_ids']
    # Freeze hashes of every captured raw log/event BEFORE old/fixed comparison.
    raw_manifest={str(p.relative_to(OUT)):run.sha(p.read_bytes()) for phase in ('phase2','phase3')
                  for p in (OUT/phase).rglob('*') if p.is_file()}
    run.save(OUT/'raw_collection.sha256.json',raw_manifest)
    run.save(OUT/'comparison_started.json',{'utc':run.datetime.now(run.timezone.utc).isoformat(),
             'oracle_labels_read':False,'raw_manifest_sha256':run.sha((OUT/'raw_collection.sha256.json').read_bytes()),
             'parser_proposal':'../parser_fix.diff; unchanged; pytest-family admission only'})
    snapshots=json.loads((run.AUDIT/'phase1_existing_v2_evidence.json').read_text())['snapshots']
    raw_rows=[];coverage_rows=[];stability_rows=[];comparison=[];environments=[];fixtures=[]
    detailed={}
    for iid,r in run.INPUTS.items():
        im=json.loads((OUT/'preflight'/f'{iid}.image.json').read_text())
        available=im['returncode']==0
        image=json.loads((OUT/'preflight'/f'{iid}.image.stdout').read_text()) if available else {}
        env={'instance_id':iid,'available_local_frozen_image':available,
             'frozen_tag':r['study_image_tag'],'current_image_id':image.get('Id'),
             'current_repo_digests':image.get('RepoDigests'),
             'study_image_digest':r['historical_image_digest'],'study_image_hash_match':'UNKNOWN',
             'reason':'No historical study image ID/digest stored; tag is not hash evidence',
             'patch_sha256':r['patch_sha256'],'frozen_selection_count':len(r['selected_tests']),
             'full_pass_timeout_s':300,'initial_pair_budget_s':600,'individual_rerun_timeout_s':300,
             'base_commit_matches_historical_record':'UNKNOWN: historical commit not in frozen inputs',
             'patch_applied':iid in completed,'historical_runner_version_match':'UNKNOWN',
             'claim_status':'confirmed current observations; unresolved historical identity'}
        folder=OUT/'phase2'/iid
        if iid not in completed:
            comparison.append({'instance_id':iid,'original_study_v2':snapshots[iid]['regression']['outcome'],
                 'old_parser_on_audit_raw':None,'fixed_parser_on_same_raw':None,'usable_v2':False,
                 'raw_rescoring_subset_member':False,'reason':'Local frozen image missing; no test attempt',
                 'claim_status':'unresolved audit result; confirmed environment blocker'})
            environments.append(env)
            continue
        env['observed_environment_stdout']=(folder/'environment.stdout').read_text()
        env['observed_environment_stderr']=(folder/'environment.stderr').read_text()
        env['observed_base_commit']=env['observed_environment_stdout'].splitlines()[0]
        env['patch_check_passed']=json.loads((folder/'patch_check.json').read_text())['returncode']==0
        sr=repeats(iid);stability_rows+=sr
        tree_cov={};tree_complete={};concretes={};texts={};metas={}
        for tree in ('base','patched'):
            f=folder/tree/'initial'
            tree_cov[tree],tree_complete[tree]=coverage(f,r['selected_tests'])
            concretes[tree]=run.raw_cases(f)
            texts[tree]=(f/'runner.raw').read_text(errors='replace')
            metas[tree]=json.loads((f/'attempt.json').read_text())
            env[tree+'_initial_duration_s']=metas[tree]['duration_s']
            env[tree+'_initial_driver_state']=metas[tree]['driver_state']
        for tid in sorted(concretes['base'].keys()|concretes['patched'].keys()):
            selected=tid if tid in tree_cov['base'] else family(tid)
            if selected not in tree_cov['base']:selected=None
            raw_rows.append({'instance_id':iid,'raw_test_id':tid,'selected_family_or_exact_id':selected,
                'base_outcome':concretes['base'][tid].value if tid in concretes['base'] else None,
                'patched_outcome':concretes['patched'][tid].value if tid in concretes['patched'] else None,
                'base_raw_ref':str((folder/'base/initial/runner.raw').relative_to(OUT)),
                'patched_raw_ref':str((folder/'patched/initial/runner.raw').relative_to(OUT)),
                'per_test_duration_s':None,'duration_note':'Not emitted by original verbose runner; batch durations stored separately',
                'claim_status':'confirmed raw verbose results'})
        for tid in r['selected_tests']:
            coverage_rows.append({'instance_id':iid,'selected_id':tid,
                'base_concrete_results':tree_cov['base'][tid],
                'patched_concrete_results':tree_cov['patched'][tid],
                'base_recorded_outcome':bool(tree_cov['base'][tid]),
                'patched_recorded_outcome':bool(tree_cov['patched'][tid]),
                'base_responsible_batch_completed':tid in tree_complete['base'],
                'patched_responsible_batch_completed':tid in tree_complete['patched'],
                'claim_status':'confirmed raw coverage; absent entries remain missing'})
        usable=all(any(v.value in ('passed','failed','skipped') for v in concretes[t].values()) for t in ('base','patched')) and all(
            tree_cov[t][tid] and tid in tree_complete[t] for t in ('base','patched') for tid in r['selected_tests'])
        old=score(OLD,r['runner'],r['selected_tests'],texts['base'],texts['patched'],sr)
        fixed=score(FIXED,r['runner'],r['selected_tests'],texts['base'],texts['patched'],sr)
        detailed[iid]={'old':old,'fixed':fixed,'usable':usable,
             'base_raw_count':len(concretes['base']),'patched_raw_count':len(concretes['patched']),
             'base_raw_coverage':sum(bool(v) for v in tree_cov['base'].values()),
             'patched_raw_coverage':sum(bool(v) for v in tree_cov['patched'].values())}
        comparison.append({'instance_id':iid,'original_study_v2':snapshots[iid]['regression']['outcome'],
            'old_parser_on_audit_raw':old['v2_label'],'fixed_parser_on_same_raw':fixed['v2_label'],
            'old_raw_signal':old['raw_signal'],'fixed_raw_signal':fixed['raw_signal'],
            'verdict_changed_by_proposal':old['v2_label']!=fixed['v2_label'],
            'old_base_parsed_selected':old['base_parsed_selected'],
            'fixed_base_parsed_selected':fixed['base_parsed_selected'],
            'old_patched_parsed_selected':old['patched_parsed_selected'],
            'fixed_patched_parsed_selected':fixed['patched_parsed_selected'],
            'old_outcome_counts':old['outcome_counts'],'fixed_outcome_counts':fixed['outcome_counts'],
            'base_raw_covered_selected':detailed[iid]['base_raw_coverage'],
            'patched_raw_covered_selected':detailed[iid]['patched_raw_coverage'],
            'selected_count':len(r['selected_tests']),'usable_v2':usable,
            'raw_rescoring_subset_member':True,
            'reason':'Paired new raw collection, identical raw logs and stability evidence for both parsers; historical raw unavailable',
            'claim_status':'confirmed replay result; no causal claim about original run'})
        # Exact observed lines and selected-ID context become fixtures, never gold data.
        for line in texts['base'].splitlines():
            match=OLD['_PYTEST_LINE'].match(line.strip())
            if not match:continue
            tid=match.group('id');key=tid if tid in r['selected_tests'] else family(tid)
            if key not in r['selected_tests']:continue
            kind='exact' if key==tid else 'parameter_family'
            if not any(f['kind']==kind for f in fixtures):
                fixtures.append({'kind':kind,'raw_line':line,'selected_id':key,'raw_test_id':tid,
                                 'observed_status':OLD['_PYTEST_OUTCOME'][match.group('outcome')].value,
                                 'source':str((folder/'base/initial/runner.raw').relative_to(OUT))})
        environments.append(env)
    write_csv('raw_test_outcomes.csv',raw_rows)
    write_csv('selected_coverage.csv',coverage_rows)
    write_csv('regression_reruns.csv',stability_rows)
    write_csv('old_vs_fixed.csv',comparison)
    write_csv('environment_sanity.csv',environments)
    run.save(OUT/'parser_comparison.json',detailed)
    run.save(OUT/'observed_parser_fixtures.json',fixtures)
    run.save(OUT/'diagnostics_frozen_before_labels.json',{'diagnostics_and_parser_outputs_saved':True,
        'oracle_labels_read':False,'utc':run.datetime.now(run.timezone.utc).isoformat(),
        'subset_ids':completed,'usable_ids':[iid for iid,d in detailed.items() if d['usable']]})
    return comparison,stability_rows,detailed


def main():
    diagnostic_analysis()
    print('OFFLINE DIAGNOSTICS SAVED BEFORE POST-HOC LABEL ACCESS',flush=True)


if __name__=='__main__':main()
