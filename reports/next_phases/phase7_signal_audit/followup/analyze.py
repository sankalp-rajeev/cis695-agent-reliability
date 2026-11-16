"""Report-only follow-up; read raw evidence without changing sealed results."""
import ast
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
RUNS = ['main_2_rerun_mpl','main_3_rerun_infra','main_50_a','main_50_b']
ACCOUNTS = ['original','C_invalid_excluded','C_invalid_missing','S_invalid_excluded','S_invalid_missing']
LABELS = {'original':'original_label','audited_default':'audited_label_default','CPU_2048':'CPU_2048_sensitivity_label'}
INPUTS = {}


def save(name, rows):
    assert rows, name
    with (OUT/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def emit(name, value):
    (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def raw(path, role):
    p=Path(path)
    data=p.read_bytes()
    name=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    INPUTS[name]={'path':name,'sha256':hashlib.sha256(data).hexdigest(),'role':role}
    return data


def strip(value):
    if isinstance(value,dict):
        return {k:strip(v) for k,v in value.items() if not any(s in k.lower() for s in ('oracle','resolved','label','grader'))}
    return [strip(v) for v in value] if isinstance(value,list) else value


def data(path, role):
    return json.loads(raw(path,role))


def csv_data(path,role):
    return list(csv.DictReader(raw(path,role).decode().splitlines()))


def save(name,rows,fields=None):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def emit(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def module(name,path):
    raw(path,'unchanged verifier source')
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


frozen={t['instance_id']:t for t in data(ROOT/'reports/v2_discovery_cleanup/frozen_83/tasks.json','frozen task metadata')}
members={}
for run in RUNS:
    rows=csv_data(ROOT/'manifests'/(run+'.csv'),'manifest IDs only')
    key=next(k for k in ['instance_id','task_id','id'] if k in rows[0]);members[run]={r[key] for r in rows}
records,paths={},{}
for task in sorted(set.union(*members.values())):
    dirs=[ROOT/'runs'/r/'tasks'/task for r in RUNS]
    available=[d for d in dirs if d.is_dir()];reruns=[d for d in available if d.parts[-3] in RUNS[:2]];mains=[d for d in available if d.parts[-3] in RUNS[2:]]
    assert len(reruns)<=1 and len(mains)<=1
    d=(reruns or mains or [None])[0]
    if d and (d/'verification_record.full.json').is_file():
        p=d/'verification_record.full.json';records[task]=strip(data(p,'selected verification record'));paths[task]=p.relative_to(ROOT)
assert len(records)==100 and set(frozen)<=set(records)
phase4={r['task']:r for r in strip(data(ROOT/'reports/next_phases/phase4_rerun/attempt4_seal/results.json','sealed Phase 4 per-task statuses'))['per_task']}
labels={r['task']:r for r in csv_data(ROOT/'reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv','post-hoc audited labels')}
gaps=csv_data(ROOT/'reports/next_phases/phase4_posthoc/grader_gap/classification.csv','post-hoc gap classifications')
assert set(frozen)==set(labels)==set(phase4)
decision=module('followup_decision',ROOT/'src/reliability/verifier/decision.py')
parser=module('followup_patch',ROOT/'src/reliability/verifier/patch.py')
test_source=raw(ROOT/'src/reliability/verifier/integrity.py','unchanged test-path conventions').decode()
test_patterns=next(ast.literal_eval(n.value) for n in ast.parse(test_source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEST_PATTERNS' for t in n.targets))
is_test=lambda path:any(re.search(pattern,path) for pattern in test_patterns)
mapping={'PASS':'PASS','FAIL':'FAIL','REGRESSION_ERROR':'FAIL','INCOMPLETE':'NOT_AVAILABLE','NOT_AVAILABLE':'NOT_AVAILABLE'}
matrix=[]
for task in sorted(frozen):
    r=records[task];assert r['decision']['policy_version']=='v1.3.0-full'
    expected=frozen[task]['patch_sha256'];assert r['patch_sha256'].split(':')[-1]==labels[task]['frozen_candidate_sha256']==expected
    flags=r['integrity']['findings']
    def decide(v2):
        return decision.FullPolicy().decide(decision.Evidence(
            integrity=decision.SignalOutcome(r['integrity']['outcome']),regression=decision.SignalOutcome(v2),
            static=decision.SignalOutcome(r['static']['outcome']),reproduction=decision.SignalOutcome(r['reproduction']['outcome']),
            patch_applies=flags['patch_applies'],prohibited_manipulation=flags['prohibited_manipulation'],high_severity_risk=flags['high_severity_risk'])).decision.value
    assert decide(r['regression']['outcome'])==r['decision']['decision']
    row=dict(task=task,**{s:labels[task][c] for s,c in LABELS.items()},audit_classification=labels[task]['classification'])
    row.update({'decision_original':r['decision']['decision']})
    for accounting in ACCOUNTS[1:]:
        status=phase4[task]['policies'][accounting];assert status in mapping
        row['decision_'+accounting]=decide(mapping[status])
    claim_path=Path('/original')/paths[task].parent/'repair_record.json'
    row['claim_status']=data(claim_path,'stored agent claim')['claim']['status']
    row['grader_gap_classification']=';'.join(sorted({g['classification'] for g in gaps if g['task']==task})) or 'NOT_AVAILABLE: task absent from gap classification table'
    matrix.append(row)
save('posthoc_task_matrix.csv',matrix)


def wilson(k,n):
    if not n:return ['NOT_AVAILABLE']*3
    z=1.959963984540054;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [f'{v:.10f}' for v in (p,mid-half,mid+half)]


metrics,fas,claim_metrics,policies=[],[],[],[]
for account in ACCOUNTS:
    counts=Counter(r['decision_'+account] for r in matrix)
    policies.append(dict(accounting=account,ACCEPT=counts['ACCEPT'],FLAG=counts['FLAG'],REJECT=counts['REJECT'],preregistered_primary='yes' if account=='S_invalid_excluded' else 'no',sealed_audit_headline='yes' if account=='S_invalid_missing' else 'no'))
    accepted=[r for r in matrix if r['decision_'+account]=='ACCEPT']
    for label in LABELS:
        assert all(r[label] in ['correct','incorrect'] for r in matrix)
        good=sum(r[label]=='correct' for r in accepted);rate,lo,hi=wilson(good,len(accepted));cover,clo,chi=wilson(len(accepted),83)
        false=[r for r in accepted if r[label]=='incorrect']
        metrics.append(dict(accounting=account,labels=label,tasks=83,accepts=len(accepted),correct_accepts=good,false_accepts=len(false),precision=rate,wilson_low=lo,wilson_high=hi,coverage=cover,coverage_wilson_low=clo,coverage_wilson_high=chi,false_accept_tasks=';'.join(r['task'] for r in false)))
        fas.extend(dict(accounting=account,labels=label,task=r['task'],audit_classification=r['audit_classification'],grader_gap_classification=r['grader_gap_classification']) for r in false)
for label in LABELS:
    positive=[r for r in matrix if r['claim_status']=='RESOLVED'];good=sum(r[label]=='correct' for r in positive);rate,lo,hi=wilson(good,len(positive))
    claim_metrics.append(dict(labels=label,tasks=83,positive_claims=len(positive),correct_claims=good,false_claims=len(positive)-good,precision=rate,wilson_low=lo,wilson_high=hi))
save('policy_counts.csv',policies);save('posthoc_accept_metrics.csv',metrics);save('posthoc_false_accepts.csv',fas);save('posthoc_claim_metrics.csv',claim_metrics)

patches,files=[],[]
for task in sorted(records):
    candidate=(ROOT/'reports/v2_discovery_cleanup/frozen_83'/frozen[task]['patch_path']) if task in frozen else Path('/original')/paths[task].parent/'patch.diff'
    blob=raw(candidate,'agent candidate patch');sha=hashlib.sha256(blob).hexdigest();assert sha==records[task]['patch_sha256'].split(':')[-1]
    text=blob.decode();parsed=parser.parse_patch(text) if text.strip() else []
    existing=[];added=[]
    for file in parsed:
        names={file.path,file.old_path}-{None};matches=sorted(n for n in names if is_test(n));kind=file.kind.value
        if matches:(added if kind=='added' else existing).extend(matches)
        files.append(dict(task=task,cohort='frozen83' if task in frozen else 'other17',old_path=file.old_path or file.path,new_path=file.path,kind=kind,test_paths=';'.join(matches),existing_test_edit='yes' if matches and kind!='added' else 'no'))
    assert not existing, 'A test-edit candidate requires explicit assertion review: '+task
    patches.append(dict(task=task,cohort='frozen83' if task in frozen else 'other17',candidate=str(candidate),sha256=sha,bytes=len(blob),file_changes=len(parsed),existing_test_files=len(set(existing)),added_test_files=len(set(added)),assertions_removed=0,assertions_loosened=0,review='NOT_APPLICABLE: no pre-existing test edits'))
save('v1_patch_inventory.csv',patches);save('v1_changed_files.csv',files)

v3=[]
for task in ['matplotlib__matplotlib-23299','pallets__flask-5014']:
    r=records[task];s=r['static'];f=s['findings'];status=f['summary']['import'];assert status=='PASS'
    v3.append(dict(task=task,record=str(paths[task]),aggregate_v3=s['outcome'],decision=r['decision']['decision'],import_status=status,import_failure_reason='NOT_APPLICABLE: import PASS',base_import_status='NOT_RECORDED',same_import_failure_on_base='UNKNOWN: no baseline import result',actual_new_failures=';'.join(f['new_failures']),actual_failure_detail='NOT_AVAILABLE: per-check failure output not retained',genuine_or_environmental='UNKNOWN for actual failure; no import failure to classify',recorded_static_detail=s['detail']))
save('v3_record_review.csv',v3)

configs={name:raw(ROOT/name,'read-only resource configuration').decode() for name in ['configs/verifier/full.yaml','configs/agent/v4_generator.yaml','configs/model/generator.yaml']}
def number(text,key):
    return float(re.search(r'(?m)^\s*'+re.escape(key)+r':\s*([0-9]+(?:\.[0-9]+)?)',text).group(1))
limits=[(key,number(configs['configs/verifier/full.yaml'],key),'configs/verifier/full.yaml') for key in ['max_tests','retries','generator_max_steps','generator_max_cost_usd','generator_timeout_s','per_command_timeout_s','screen_runs','patched_runs','per_run_timeout_s','max_test_bytes']]
limits.append(('max_output_tokens',number(configs['configs/model/generator.yaml'],'max_output_tokens'),'configs/model/generator.yaml'))
save('configured_limits.csv',[dict(key=k,value=format(v,'g'),source=s) for k,v,s in limits])
agent_source=raw('/inputs/default_agent.py','current installed agent guard source; not executed').decode()
assert '0 < self.config.step_limit <= self.n_calls or 0 < self.config.cost_limit <= self.cost' in agent_source
assert 'raise TimeExceeded' in agent_source
for name in ['src/reliability/verifier/reproduction_freeze.py','src/reliability/verifier/reproduction.py','src/reliability/verifier/static_checks.py']:
    raw(ROOT/name,'read-only source explaining retained fields')
v4=[]
for task in sorted(frozen):
    r=records[task]['reproduction']
    if r['outcome']!='NOT_AVAILABLE':continue
    assert r['detail'].startswith('generator wrote no test files (')
    f=r['findings'];g=f['generation'];b=f['setup']['budget'];tokens=f['setup']['generator']['max_output_tokens']
    assert all(float(b[k])==v for k,v,s in limits if k!='max_output_tokens') and tokens==8192
    assert g['termination']=='LimitsExceeded' and g['n_steps']==b['generator_max_steps'] and g['cost_usd']<b['generator_max_cost_usd']
    v4.append(dict(task=task,record=str(paths[task]),termination=g['termination'],recorded_fired_limit='UNKNOWN: no limit subtype retained',steps=g['n_steps'],cost_usd=format(g['cost_usd'],'.12g'),step_cap_reached='yes',cost_cap_reached='no',supported_inference='STEPS under inspected agent guard; subtype not explicitly recorded',generator_elapsed_s='UNKNOWN',token_usage='UNKNOWN',max_output_tokens_per_response=tokens,**b))
assert len(v4)==14
save('v4_limits.csv',v4)
plan=raw(ROOT/'reports/next_phases/phase4_plan.md','pre-registration policy').decode()
assert 'Policy S (skip-strict, primary for claims about PASS)' in plan
assert '`INVALID_ID` is excluded from the denominator and reported.' in plan
save('input_hashes.csv',sorted(INPUTS.values(),key=lambda r:r['path']))
counts=dict(policy_counts={r['accounting']:{k:r[k] for k in ['ACCEPT','FLAG','REJECT']} for r in policies},posthoc_metric_rows=len(metrics),claim_metric_rows=len(claim_metrics),candidate_cohorts={group:dict(available=sum(r['cohort']==group for r in patches),patches_editing_existing_tests=sum(r['cohort']==group and r['existing_test_files']>0 for r in patches),assertions_removed=sum(r['assertions_removed'] for r in patches if r['cohort']==group),assertions_loosened=sum(r['assertions_loosened'] for r in patches if r['cohort']==group)) for group in ['frozen83','other17']},v3_import_statuses={r['task']:r['import_status'] for r in v3},v4_cases=len(v4),v4_recorded_limit_subtype_unknown=len(v4),v4_step_caps_reached=sum(r['step_cap_reached']=='yes' for r in v4),v4_cost_caps_reached=sum(r['cost_cap_reached']=='yes' for r in v4))
emit('counts.json',counts)
print(json.dumps(counts,indent=2))
