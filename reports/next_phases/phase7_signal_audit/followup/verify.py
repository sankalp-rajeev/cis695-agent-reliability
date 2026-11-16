"""Independent standard-library-only reconstruction; no producer imports."""
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
RUNS=['main_2_rerun_mpl','main_3_rerun_infra','main_50_a','main_50_b']
ACCOUNTS=['original','C_invalid_excluded','C_invalid_missing','S_invalid_excluded','S_invalid_missing']
SETS=['original','audited_default','CPU_2048']
inputs={};checked=[]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def get(path,role):
    p=Path(path);blob=p.read_bytes()
    try:name=str(p.relative_to(ROOT))
    except ValueError:name=str(p)
    inputs[name]=dict(path=name,sha256=hashlib.sha256(blob).hexdigest(),role=role)
    return blob


def obj(path,role):
    return json.loads(get(path,role))


def sanitize(x):
    if type(x) is dict:
        return {k:sanitize(v) for k,v in x.items() if not any(s in k.lower() for s in ['oracle','grader','label','resolved'])}
    return [sanitize(v) for v in x] if type(x) is list else x


def rows(path,role):
    return list(csv.DictReader(get(path,role).decode().splitlines()))


def compare(name,expected):
    with (OUT/name).open(newline='') as f:
        reader=csv.DictReader(f);actual=list(reader);columns=reader.fieldnames
    assert all(set(r)==set(columns) for r in expected),(name,'schema mismatch')
    values=lambda data:Counter(tuple(str(r[k]) for k in columns) for r in data)
    a,e=values(actual),values(expected)
    assert a==e,(name,'table mismatch',list((a-e).elements())[:1],list((e-a).elements())[:1])
    checked.append(name)


def decide(record,v2):
    f=record['integrity']['findings'];i=record['integrity']['outcome'];v4=record['reproduction']['outcome']
    if not f['patch_applies'] or i=='FAIL' or f['prohibited_manipulation'] or (v2=='FAIL' and v4!='PASS'):
        return 'REJECT'
    if i=='PASS' and v2=='PASS' and v4=='PASS' and not f['high_severity_risk']:
        return 'ACCEPT'
    return 'FLAG'


def interval(k,n):
    if n==0:return ['NOT_AVAILABLE']*3
    z=1.959963984540054;den=n+z*z;center=(k+z*z/2)/den;half=z*math.sqrt(k*(n-k)/n+z*z/4)/den
    return [format(x,'.10f') for x in (k/n,center-half,center+half)]


def main():
    frozen={r['instance_id']:r for r in obj(ROOT/'reports/v2_discovery_cleanup/frozen_83/tasks.json','frozen task metadata')}
    assert len(frozen)==83
    members={}
    for run in RUNS:
        source=rows(ROOT/'manifests'/(run+'.csv'),'manifest IDs only');key=next(k for k in ['instance_id','task_id','id'] if k in source[0]);members[run]={r[key] for r in source}
    records,paths={},{}
    for task in sorted(set.union(*members.values())):
        reruns=[];main_dirs=[]
        for run in RUNS:
            folder=ROOT/'runs'/run/'tasks'/task
            if folder.is_dir():
                assert task in members[run]
                (reruns if run in RUNS[:2] else main_dirs).append(folder)
        assert len(reruns)<=1 and len(main_dirs)<=1
        folder=(reruns or main_dirs or [None])[0]
        if folder and (folder/'verification_record.full.json').is_file():
            path=folder/'verification_record.full.json';records[task]=sanitize(obj(path,'selected verification record'));paths[task]=path.relative_to(ROOT)
    assert len(records)==100 and set(frozen)<=set(records)
    phase4={r['task']:r for r in sanitize(obj(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal/results.json','sealed Phase 4 per-task statuses'))['per_task']}
    labels={r['task']:r for r in rows(ROOT/'reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv','post-hoc audited labels')}
    gaps=rows(ROOT/'reports/next_phases/phase4_posthoc/grader_gap/classification.csv','post-hoc gap classifications')
    assert set(frozen)==set(phase4)==set(labels)
    matrix=[]
    for task in sorted(frozen):
        r=records[task];assert r['decision']['policy_version']=='v1.3.0-full'
        assert decide(r,r['regression']['outcome'])==r['decision']['decision']
        assert labels[task]['frozen_candidate_sha256']==frozen[task]['patch_sha256']==r['patch_sha256'].split(':')[-1]
        label=labels[task]
        row=dict(task=task,original=label['original_label'],audited_default=label['audited_label_default'],CPU_2048=label['CPU_2048_sensitivity_label'],audit_classification=label['classification'],decision_original=r['decision']['decision'])
        for account in ACCOUNTS[1:]:
            status=phase4[task]['policies'][account]
            assert status in ['PASS','FAIL','REGRESSION_ERROR','INCOMPLETE','NOT_AVAILABLE']
            outcome='PASS' if status=='PASS' else 'FAIL' if status in ['FAIL','REGRESSION_ERROR'] else 'NOT_AVAILABLE'
            row['decision_'+account]=decide(r,outcome)
        path=Path('/original')/paths[task].parent/'repair_record.json'
        row['claim_status']=obj(path,'stored agent claim')['claim']['status']
        row['grader_gap_classification']=';'.join(sorted({g['classification'] for g in gaps if g['task']==task})) or 'NOT_AVAILABLE: task absent from gap classification table'
        matrix.append(row)
    compare('posthoc_task_matrix.csv',matrix)
    metrics,fas,claims,policies=[],[],[],[]
    for account in ACCOUNTS:
        counts=Counter(r['decision_'+account] for r in matrix)
        policies.append(dict(accounting=account,ACCEPT=counts['ACCEPT'],FLAG=counts['FLAG'],REJECT=counts['REJECT'],preregistered_primary='yes' if account=='S_invalid_excluded' else 'no',sealed_audit_headline='yes' if account=='S_invalid_missing' else 'no'))
        accepted=[r for r in matrix if r['decision_'+account]=='ACCEPT']
        for label in SETS:
            assert all(r[label] in ['correct','incorrect'] for r in matrix)
            false=[r for r in accepted if r[label]=='incorrect'];good=len(accepted)-len(false)
            rate,lo,hi=interval(good,len(accepted));coverage,clo,chi=interval(len(accepted),83)
            metrics.append(dict(accounting=account,labels=label,tasks=83,accepts=len(accepted),correct_accepts=good,false_accepts=len(false),precision=rate,wilson_low=lo,wilson_high=hi,coverage=coverage,coverage_wilson_low=clo,coverage_wilson_high=chi,false_accept_tasks=';'.join(r['task'] for r in false)))
            fas.extend(dict(accounting=account,labels=label,task=r['task'],audit_classification=r['audit_classification'],grader_gap_classification=r['grader_gap_classification']) for r in false)
    for label in SETS:
        positive=[r for r in matrix if r['claim_status']=='RESOLVED'];good=sum(r[label]=='correct' for r in positive);rate,lo,hi=interval(good,len(positive))
        claims.append(dict(labels=label,tasks=83,positive_claims=len(positive),correct_claims=good,false_claims=len(positive)-good,precision=rate,wilson_low=lo,wilson_high=hi))
    for name,expected in [('policy_counts.csv',policies),('posthoc_accept_metrics.csv',metrics),('posthoc_false_accepts.csv',fas),('posthoc_claim_metrics.csv',claims)]:compare(name,expected)
    # Parse Git file headers directly, independently of the verifier's parser.
    files,patches=[],[]
    def test(path):
        parts=path.split('/');filename=parts[-1]
        return any(p in ['test','tests','testing'] for p in parts[:-1]) or (filename.startswith('test_') and filename.endswith('.py')) or filename.endswith('_test.py')
    for task in sorted(records):
        candidate=ROOT/'reports/v2_discovery_cleanup/frozen_83'/frozen[task]['patch_path'] if task in frozen else Path('/original')/paths[task].parent/'patch.diff'
        blob=get(candidate,'agent candidate patch');digest=hashlib.sha256(blob).hexdigest();assert digest==records[task]['patch_sha256'].split(':')[-1]
        changes=[]
        for line in blob.decode().splitlines():
            if line.startswith('diff --git '):
                header=re.fullmatch(r'diff --git a/(.+?) b/(.+)',line);assert header
                changes.append(dict(old=header[1],new=header[2],kind='modified'))
            elif changes and line.startswith('new file mode '):changes[-1]['kind']='added'
            elif changes and line.startswith('deleted file mode '):changes[-1]['kind']='deleted'
            elif changes and line.startswith('rename from '):changes[-1].update(old=line[len('rename from '):].strip(),kind='renamed')
            elif changes and line.startswith('rename to '):changes[-1].update(new=line[len('rename to '):].strip(),kind='renamed')
        assert not blob.strip() or changes
        cohort='frozen83' if task in frozen else 'other17';existing=set();added=set()
        for c in changes:
            tests=sorted({n for n in [c['old'],c['new']] if test(n)})
            (added if c['kind']=='added' else existing).update(tests)
            files.append(dict(task=task,cohort=cohort,old_path=c['old'],new_path=c['new'],kind=c['kind'],test_paths=';'.join(tests),existing_test_edit='yes' if tests and c['kind']!='added' else 'no'))
        assert not existing,('existing test requires assertion review',task)
        patches.append(dict(task=task,cohort=cohort,candidate=str(candidate),sha256=digest,bytes=len(blob),file_changes=len(changes),existing_test_files=len(existing),added_test_files=len(added),assertions_removed=0,assertions_loosened=0,review='NOT_APPLICABLE: no pre-existing test edits'))
    compare('v1_changed_files.csv',files);compare('v1_patch_inventory.csv',patches)
    v3=[]
    for task in ['matplotlib__matplotlib-23299','pallets__flask-5014']:
        r=records[task];s=r['static'];f=s['findings'];assert f['summary']['import']=='PASS'
        v3.append(dict(task=task,record=str(paths[task]),aggregate_v3=s['outcome'],decision=r['decision']['decision'],import_status='PASS',import_failure_reason='NOT_APPLICABLE: import PASS',base_import_status='NOT_RECORDED',same_import_failure_on_base='UNKNOWN: no baseline import result',actual_new_failures=';'.join(f['new_failures']),actual_failure_detail='NOT_AVAILABLE: per-check failure output not retained',genuine_or_environmental='UNKNOWN for actual failure; no import failure to classify',recorded_static_detail=s['detail']))
    compare('v3_record_review.csv',v3)
    configs={n:get(ROOT/n,'read-only resource configuration').decode() for n in ['configs/verifier/full.yaml','configs/agent/v4_generator.yaml','configs/model/generator.yaml']}
    def scalar(text,key):
        found=[]
        for line in text.splitlines():
            match=re.fullmatch(r'\s*'+re.escape(key)+r':\s*([0-9]+(?:\.[0-9]+)?)(?:\s+#.*)?\s*',line)
            if match:found.append(float(match[1]))
        assert len(found)==1,(key,'configuration ambiguity')
        return found[0]
    keys=['max_tests','retries','generator_max_steps','generator_max_cost_usd','generator_timeout_s','per_command_timeout_s','screen_runs','patched_runs','per_run_timeout_s','max_test_bytes']
    expected_limits={k:scalar(configs['configs/verifier/full.yaml'],k) for k in keys}
    config_rows=[dict(key=k,value=format(expected_limits[k],'g'),source='configs/verifier/full.yaml') for k in keys]
    tokens=scalar(configs['configs/model/generator.yaml'],'max_output_tokens')
    config_rows.append(dict(key='max_output_tokens',value=format(tokens,'g'),source='configs/model/generator.yaml'))
    compare('configured_limits.csv',config_rows)
    guard=get('/inputs/default_agent.py','current installed agent guard source; not executed').decode()
    assert '0 < self.config.step_limit <= self.n_calls or 0 < self.config.cost_limit <= self.cost' in guard and 'raise TimeExceeded' in guard
    for n in ['src/reliability/verifier/reproduction_freeze.py','src/reliability/verifier/reproduction.py','src/reliability/verifier/static_checks.py']:get(ROOT/n,'read-only source explaining retained fields')
    v4=[]
    for task in sorted(frozen):
        s=records[task]['reproduction']
        if s['outcome']!='NOT_AVAILABLE':continue
        assert s['detail'].startswith('generator wrote no test files (')
        g=s['findings']['generation'];b=s['findings']['setup']['budget'];cap=s['findings']['setup']['generator']['max_output_tokens']
        assert all(float(b[k])==expected_limits[k] for k in keys) and cap==tokens
        assert g['termination']=='LimitsExceeded' and g['n_steps']==b['generator_max_steps'] and g['cost_usd']<b['generator_max_cost_usd']
        v4.append(dict(task=task,record=str(paths[task]),termination=g['termination'],recorded_fired_limit='UNKNOWN: no limit subtype retained',steps=g['n_steps'],cost_usd=format(g['cost_usd'],'.12g'),step_cap_reached='yes',cost_cap_reached='no',supported_inference='STEPS under inspected agent guard; subtype not explicitly recorded',generator_elapsed_s='UNKNOWN',token_usage='UNKNOWN',max_output_tokens_per_response=cap,**b))
    assert len(v4)==14
    compare('v4_limits.csv',v4)
    plan=get(ROOT/'reports/next_phases/phase4_plan.md','pre-registration policy').decode()
    assert 'Policy S (skip-strict, primary for claims about PASS)' in plan and '`INVALID_ID` is excluded from the denominator and reported.' in plan
    frozen_plan=Path('/inputs/phase4_plan_frozen.md').read_text();prereg=json.loads((OUT/'preregistration_evidence.json').read_text())
    assert hashlib.sha256(frozen_plan.encode()).hexdigest()==prereg['blob_sha256'] and prereg['policy_excerpt'] in frozen_plan
    assert 'Policy S (skip-strict, primary for claims about PASS)' in prereg['policy_excerpt'] and '`INVALID_ID` is excluded' in prereg['policy_excerpt']
    for n in ['decision.py','patch.py']:get(ROOT/'src/reliability/verifier'/n,'unchanged verifier source')
    get(ROOT/'src/reliability/verifier/integrity.py','unchanged test-path conventions')
    compare('input_hashes.csv',sorted(inputs.values(),key=lambda r:r['path']))
    counts=dict(policy_counts={r['accounting']:{k:r[k] for k in ['ACCEPT','FLAG','REJECT']} for r in policies},posthoc_metric_rows=len(metrics),claim_metric_rows=len(claims),candidate_cohorts={group:dict(available=sum(r['cohort']==group for r in patches),patches_editing_existing_tests=sum(r['cohort']==group and r['existing_test_files']>0 for r in patches),assertions_removed=sum(r['assertions_removed'] for r in patches if r['cohort']==group),assertions_loosened=sum(r['assertions_loosened'] for r in patches if r['cohort']==group)) for group in ['frozen83','other17']},v3_import_statuses={r['task']:r['import_status'] for r in v3},v4_cases=len(v4),v4_recorded_limit_subtype_unknown=len(v4),v4_step_caps_reached=sum(r['step_cap_reached']=='yes' for r in v4),v4_cost_caps_reached=sum(r['cost_cap_reached']=='yes' for r in v4))
    assert json.loads((OUT/'counts.json').read_text())==counts,('counts.json','count mismatch')
    baseline=json.loads((OUT/'baseline_seal.json').read_text())
    for row in baseline['sealed_artifacts']:assert sha(ROOT/row['path'])==row['sha256'],('sealed artifact changed',row['path'])
    assert set(checked)=={str(f.relative_to(OUT)) for f in OUT.glob('*.csv')},'Unchecked CSV'
    result=dict(status='PASS',mismatches=0,standard_library_only=True,producer_modules_imported=[],csv_tables_compared=len(checked),csv_tables=sorted(checked),raw_inputs_checked=len(inputs),sealed_artifacts_unchanged=len(baseline['sealed_artifacts']),registered_primary='S_invalid_excluded',registered_primary_counts=counts['policy_counts']['S_invalid_excluded'],posthoc_metric_rows=15,patches_checked=100,existing_test_edits=0,v3_import_passes=2,v4_step_caps_reached=14,v4_explicit_subtypes_unknown=14)
    (OUT/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    try:main()
    except Exception as e:
        (OUT/'independent_verification.json').write_text(json.dumps(dict(status='FAIL',error=repr(e),completed_tables=checked,no_seal=True),indent=2)+'\n')
        raise
