"""Read-only historical V2 migration check; writes one CSV, never edits records.

No oracle, gold, failure-analysis label or decision-policy tuning is involved.
Populations are separate: on-disk verification files, preserved snapshots,
the committed 83-patch table, and the three fresh paired audit replays.
"""
import csv
import json
from collections import Counter
from pathlib import Path

from reliability.verifier.container import _parse_output, account_raw_output
from reliability.verifier.regression import (
    RunResult,
    TestResult,
    TestStatus,
    completeness_of,
    integrity_verdict,
    run_from_dict,
)
from reliability.verifier.selection import TestRunner

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/v2_stabilization'


def historical_state(record):
    signal = record['regression']
    findings = signal.get('findings',{})
    if findings.get('base') and findings.get('patched'):
        return completeness_of(tuple(record.get('selected_tests',())),
            run_from_dict(findings['base']),run_from_dict(findings['patched']))
    summary = findings.get('summary',{})
    known = [f"stored summary {kind}={summary[kind]}" for kind in ('NOT_RUN','TIMEOUT','ERROR')
             if summary.get(kind,0)]
    if known:
        return 'INCOMPLETE_CONFIRMED',tuple(known)
    return 'UNVERIFIABLE',('Historical paired raw outcomes/ID accounting/runner exits not stored',)


def row(population,key,iid,old,state,evidence):
    new = integrity_verdict(old,state)
    assert new==old or (old,new)==('PASS','INCOMPLETE'),(key,old,new)
    return {'population':population,'record':key,'instance_id':iid,'original_v2':old,
            'new_v2':new,'completeness':state,'evidence':'; '.join(evidence),
            'unexpected_transition':False}


def main():
    rows=[]
    for path in sorted((ROOT/'runs').glob('*/tasks/*/verification_record.*.json')):
        record=json.loads(path.read_text())
        state,reasons=historical_state(record)
        rows.append(row('stored_verification_files',str(path.relative_to(ROOT)),
                        record['instance_id'],record['regression']['outcome'],state,reasons))
    projection=json.loads((ROOT/'reports/next_steps/v2_projection.json').read_text())
    for iid, record in sorted(projection.items()):
        state,reasons=historical_state(record)
        rows.append(row('preserved_study_snapshots','reports/next_steps/v2_projection.json:'+iid,
                        iid,record['regression']['outcome'],state,reasons))
    reruns=json.loads((ROOT/'reports/failure_analysis/group4_regression_rerun.json').read_text())
    for record in reruns['tasks']:
        state,reasons=historical_state({'regression':{'findings':{'summary':record['summary']}}})
        rows.append(row('stored_v2_regression_reruns',
                        'reports/failure_analysis/group4_regression_rerun.json:'+record['instance_id'],
                        record['instance_id'],record['signal'],state,reasons))
    metadata=json.loads((ROOT/'reports/next_steps/nonoracle_metadata.json').read_text())
    # Commit table supplies only V2 labels here; do not read its oracle column.
    for iid,meta in sorted(metadata.items()):
        old=meta['v2_outcome']
        if iid in projection:
            state,reasons=historical_state(projection[iid])
            evidence=('confirmed final-study snapshot: '+str(projection[iid].get('source_lines')),)+reasons
        else:
            state='UNVERIFIABLE'
            evidence=('Committed headline only; no final-study paired raw evidence. Local-only records are not substituted.',)
        rows.append(row('headline_83','docs/results_100.csv:'+iid,iid,old,state,evidence))
    audit=ROOT/'reports/v2_scoring_audit/resume_20261026'
    inputs=json.loads((audit.parent/'frozen_inputs/selections.json').read_text())
    replay=json.loads((audit/'parser_comparison.json').read_text())
    for iid,comparison in replay.items():
        runs=[]
        tests=tuple(inputs[iid]['selected_tests'])
        runner=TestRunner(inputs[iid]['runner'],'frozen audit')
        for tree in ('base','patched'):
            folder=audit/'phase2'/iid/tree/'initial'
            output=(folder/'runner.raw').read_text(errors='replace')
            statuses=_parse_output(runner,output,tests)
            raw,mapping,unmatched=account_raw_output(runner,output,tests)
            events=tuple(json.loads(s) for s in (folder/'batch_events.jsonl').read_text().splitlines())
            # Capture attempt and batch evidence exist for these fresh replays.
            attempt=json.loads((folder/'attempt.json').read_text())
            runs.append(RunResult(results=tuple(TestResult(t,statuses.get(t,TestStatus.NOT_RUN)) for t in tests),
                raw_results=raw,raw_id_map=mapping,unmatched_ids=unmatched,
                timed_out=attempt['driver_state']=='timeout',events=events,evidence_complete=True))
        state,reasons=completeness_of(tests,*runs)
        rows.append(row('paired_audit_replays',str(audit.relative_to(ROOT))+':'+iid,
                        iid,comparison['old']['v2_label'],state,reasons))
    path=OUT/'verdict_diff.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    counts={}
    for pop in sorted({r['population'] for r in rows}):
        group=[r for r in rows if r['population']==pop]
        counts[pop]={'n':len(group),'old':dict(Counter(r['original_v2'] for r in group)),
            'new':dict(Counter(r['new_v2'] for r in group)),
            'completeness':dict(Counter(r['completeness'] for r in group)),
            'pass_transitions_by_evidence':dict(Counter(r['completeness'] for r in group if r['original_v2']!=r['new_v2']))}
    (OUT/'verdict_counts.json').write_text(json.dumps(counts,indent=2,sort_keys=True)+'\n')
    print(json.dumps(counts,indent=2))


if __name__=='__main__':main()
