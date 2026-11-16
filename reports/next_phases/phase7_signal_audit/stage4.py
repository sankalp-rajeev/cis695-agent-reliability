"""Replace V2 only, using the mapping committed before this script ran."""
import csv
import json
from collections import Counter
from audit_common import OUT, ROOT, evidence, policy_module, sanitize, selected_records, tasks, write_csv, write_json

PRIMARY = 'S_invalid_missing'
with (OUT / 'v2_mapping.csv').open(newline='') as f:
    mapping = {r['phase4_status']: r['regression_outcome'] for r in csv.DictReader(f)}
data = sanitize(json.loads((ROOT / 'reports/next_phases/phase4_rerun/attempt4_seal/results.json').read_text()))
phase4 = {r['task']: r for r in data['per_task']}
assert len(phase4) == len(data['per_task']) == 83
records = selected_records()
module = policy_module()
policy = module.FullPolicy()
policies = sorted(set().union(*(r['policies'].keys() for r in phase4.values())))
assert PRIMARY in policies
originals, primary_rows, sensitivity, unmapped, transitions = [], [], [], [], []
totals = {}


def flags(rows, repaired):
    unavailable = solely = 0
    for task, record, decision, v2 in rows:
        if decision == 'FLAG' and v2 == 'NOT_AVAILABLE':
            unavailable += 1
            if policy.decide(evidence(module, record, regression='PASS')).decision.value == 'ACCEPT':
                solely += 1
    return dict(flags_with_regression_unavailable=unavailable,
                flags_solely_due_to_regression_unavailable=solely)


for task in sorted(t['instance_id'] for t in tasks()):
    path, record = records[task]
    assert record['decision']['policy_version'] == policy.version
    old = policy.decide(evidence(module, record))
    assert old.decision.value == record['decision']['decision']
    originals.append((task, record, old.decision.value, record['regression']['outcome']))
totals['original'] = dict(decisions=dict(Counter(x[2] for x in originals)),
                          regression_outcomes=dict(Counter(x[3] for x in originals)),
                          **flags(originals, False))
for accounting in policies:
    evaluated = []
    for task, record, original, old_v2 in originals:
        path = records[task][0]
        status = phase4.get(task, {}).get('policies', {}).get(accounting, 'MISSING')
        repaired = mapping.get(status, 'NOT_AVAILABLE')
        if status not in mapping or status == 'UNMAPPED':
            unmapped.append(dict(task=task, policy=accounting, phase4_status=status,
                                 outcome='NOT_AVAILABLE', reason='No clean predeclared mapping; never PASS.'))
        new = policy.decide(evidence(module, record, regression=repaired))
        row = dict(task=task, original_decision=original, new_decision=new.decision.value,
                   v1=record['integrity']['outcome'], original_v2=old_v2, v2=repaired,
                   v3=record['static']['outcome'], v4=record['reproduction']['outcome'],
                   phase4_policy=accounting, phase4_status=status,
                   reason='; '.join(new.reasons), record=path)
        sensitivity.append(row)
        evaluated.append((task, record, new.decision.value, repaired))
        if accounting == PRIMARY:
            primary_rows.append(row)
            if original != new.decision.value:
                transitions.append(dict(task=task, original_decision=original,
                                        new_decision=new.decision.value,
                                        original_v2=old_v2, new_v2=repaired,
                                        phase4_status=status,
                                        cause='Only regression replaced: ' + old_v2 + ' -> ' + repaired + '; ' + '; '.join(new.reasons)))
    totals[accounting] = dict(decisions=dict(Counter(x[2] for x in evaluated)),
                              regression_outcomes=dict(Counter(x[3] for x in evaluated)),
                              changed_decisions=sum(x[2] != y[2] for x, y in zip(evaluated, originals)),
                              **flags(evaluated, True))
fields = ['task', 'original_decision', 'new_decision', 'v1', 'original_v2', 'v2', 'v3', 'v4', 'phase4_policy', 'phase4_status', 'reason', 'record']
write_csv('recompute_decisions.csv', primary_rows, fields)
write_csv('recompute_sensitivity.csv', sensitivity, fields)
write_csv('transitions.csv', transitions, ['task', 'original_decision', 'new_decision', 'original_v2', 'new_v2', 'phase4_status', 'cause'])
write_csv('recompute_unmapped.csv', unmapped, ['task', 'policy', 'phase4_status', 'outcome', 'reason'])
write_json('recompute_counts.json', dict(primary=PRIMARY, tasks=83, unmapped=len(unmapped), populations=totals))
write_csv('recompute_policy_totals.csv', [dict(policy=k, **{d: v['decisions'].get(d, 0) for d in ('ACCEPT', 'FLAG', 'REJECT')}, **{q:v[q] for q in ('flags_with_regression_unavailable','flags_solely_due_to_regression_unavailable')}) for k,v in totals.items()], ['policy', 'ACCEPT', 'FLAG', 'REJECT', 'flags_with_regression_unavailable', 'flags_solely_due_to_regression_unavailable'])
(OUT / 'recompute_notes.md').write_text(
    'Only V2 changed. Every original decision was reproduced by unchanged FullPolicy v1.3.0-full before replacement. '
    'Primary repaired accounting is the predeclared conservative S_invalid_missing; all four alternatives remain explicit. '
    'No status was unmapped.\n\n' + str(totals) + '\n\nA FLAG with regression NOT_AVAILABLE can have several unmet conditions. '
    'The solely-caused count uses a one-variable counterfactual: setting regression PASS must produce ACCEPT. '
    'The repaired signal values are inherited from the sealed Phase 4 per_task policy statuses, not fresh test execution.\n')
print(json.dumps(dict(primary=PRIMARY, unmapped=len(unmapped), totals=totals), indent=2))
