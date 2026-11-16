"""Post-hoc, never used for any decision; run only after the pushed tag."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from audit_common import OUT, ROOT, selected_records, tasks, write_csv, write_json

POST = OUT / 'posthoc_labels'
POST.mkdir(exist_ok=True)
label_path = ROOT / 'reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv'
gap_path = ROOT / 'reports/next_phases/phase4_posthoc/grader_gap/classification.csv'
with label_path.open(newline='') as f:
    labels = {r['task']: r for r in csv.DictReader(f)}
with gap_path.open(newline='') as f:
    gaps = list(csv.DictReader(f))
frozen = {t['instance_id']: t for t in tasks()}
assert set(labels) == set(frozen)
with (OUT / 'recompute_decisions.csv').open(newline='') as f:
    repaired = {r['task']: r for r in csv.DictReader(f)}
records = selected_records()
columns = {'original': 'original_label', 'audited_default': 'audited_label_default',
           'CPU_2048': 'CPU_2048_sensitivity_label'}
table, sources, digests = [], [], []
norm = lambda v: str(v).split(':', 1)[-1]
for task in sorted(frozen):
    path, record = records[task]
    label = labels[task]
    assert label['frozen_candidate_sha256'] == frozen[task]['patch_sha256']
    assert norm(record['patch_sha256']) == frozen[task]['patch_sha256']
    folder = Path('/original') / Path(path).parent
    oracle_path, claim_path = folder / 'oracle_record.json', folder / 'repair_record.json'
    oracle = json.loads(oracle_path.read_text()) if oracle_path.is_file() else {}
    claim = json.loads(claim_path.read_text()).get('claim', {}) if claim_path.is_file() else {}
    original_label = ('correct' if oracle.get('resolved') is True else 'incorrect'
                      if oracle.get('resolved') is False else 'NOT_AVAILABLE')
    assert original_label == label['original_label']
    assert norm(oracle.get('patch_sha256')) == frozen[task]['patch_sha256']
    classifications = sorted({r['classification'] for r in gaps if r['task'] == task})
    gap = ';'.join(classifications) or 'NOT_AVAILABLE: task absent from grader-gap classification table'
    row = dict(task=task, original_decision=record['decision']['decision'],
               recomputed_decision=repaired[task]['new_decision'],
               original=label['original_label'], audited_default=label['audited_label_default'],
               CPU_2048=label['CPU_2048_sensitivity_label'],
               audit_classification=label['classification'], grader_gap_classification=gap,
               claim_status=claim.get('status', 'NOT_AVAILABLE'))
    table.append(row)
    sources.append(dict(task=task, selected_record=path, oracle_source=str(oracle_path),
                        claim_source=str(claim_path), oracle_outcome=oracle.get('outcome', 'NOT_AVAILABLE'),
                        oracle_label=original_label, oracle_patch_sha256=norm(oracle.get('patch_sha256')),
                        frozen_candidate_sha256=frozen[task]['patch_sha256'], claim_status=row['claim_status']))
    for p in (oracle_path, claim_path):
        digests.append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for p in (label_path, gap_path):
    digests.append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))


def wilson(k, n):
    if n == 0:
        return 'NOT_AVAILABLE', 'NOT_AVAILABLE', 'NOT_AVAILABLE'
    z = 1.959963984540054
    rate = k / n
    center = (rate + z*z/(2*n)) / (1+z*z/n)
    half = z*math.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/(1+z*z/n)
    return f'{rate:.10f}', f'{center-half:.10f}', f'{center+half:.10f}'


metrics, false_accepts, claim_metrics, changes = [], [], [], []
for decision_set in ('original', 'recomputed'):
    accepted = [r for r in table if r[decision_set + '_decision'] == 'ACCEPT']
    for label_set in columns:
        scored = [r for r in accepted if r[label_set] in ('correct', 'incorrect')]
        correct = sum(r[label_set] == 'correct' for r in scored)
        precision, lo, hi = wilson(correct, len(scored))
        coverage, clo, chi = wilson(len(accepted), len(table))
        metrics.append(dict(decisions=decision_set, labels=label_set, tasks=len(table),
                            accepts=len(accepted), scored_accepts=len(scored), correct_accepts=correct,
                            false_accepts=len(scored)-correct, unscored_accepts=len(accepted)-len(scored),
                            precision=precision, precision_wilson_low=lo, precision_wilson_high=hi,
                            coverage=coverage, coverage_wilson_low=clo, coverage_wilson_high=chi))
        for r in scored:
            if r[label_set] == 'incorrect':
                false_accepts.append(dict(decisions=decision_set, labels=label_set, task=r['task'],
                                          audit_classification=r['audit_classification'],
                                          grader_gap_classification=r['grader_gap_classification']))
for label_set in columns:
    positive = [r for r in table if r['claim_status'] == 'RESOLVED']
    scored = [r for r in positive if r[label_set] in ('correct', 'incorrect')]
    correct = sum(r[label_set] == 'correct' for r in scored)
    rate, lo, hi = wilson(correct, len(scored))
    claim_metrics.append(dict(labels=label_set, tasks=len(table), positive_claims=len(positive),
                              scored_claims=len(scored), correct_claims=correct,
                              false_claims=len(scored)-correct, unscored_claims=len(positive)-len(scored),
                              precision=rate, wilson_low=lo, wilson_high=hi))
for r in table:
    for label_set in ('audited_default', 'CPU_2048'):
        if r['original'] != r[label_set]:
            delta = int(r[label_set] == 'correct') - int(r['original'] == 'correct')
            changes.append(dict(task=r['task'], labels=label_set, original_label=r['original'],
                                audited_label=r[label_set], audit_classification=r['audit_classification'],
                                original_decision=r['original_decision'], recomputed_decision=r['recomputed_decision'],
                                original_accept_correct_delta=delta if r['original_decision'] == 'ACCEPT' else 0,
                                recomputed_accept_correct_delta=delta if r['recomputed_decision'] == 'ACCEPT' else 0,
                                coverage_delta=0))
original_fa = {r['task'] for r in table if r['original_decision'] == 'ACCEPT' and r['original'] == 'incorrect'}
survivors = {k: sorted(r['task'] for r in table if r['task'] in original_fa and r[k] == 'incorrect')
             for k in ('audited_default', 'CPU_2048')}
stats = dict(tasks=83, original_false_accepts=sorted(original_fa),
             original_false_accepts_surviving=survivors,
             label_counts={k: dict(Counter(r[k] for r in table)) for k in columns},
             changed_labels={k: sum(r['labels'] == k for r in changes) for k in ('audited_default','CPU_2048')},
             claim_statuses=dict(Counter(r['claim_status'] for r in table)))
write_csv('posthoc_labels/task_table.csv', table, list(table[0]))
write_csv('posthoc_labels/original_sources.csv', sources, list(sources[0]))
write_csv('posthoc_labels/input_sha256.csv', digests, ['path','sha256'])
write_csv('posthoc_labels/accept_metrics.csv', metrics, list(metrics[0]))
write_csv('posthoc_labels/false_accepts.csv', false_accepts, ['decisions','labels','task','audit_classification','grader_gap_classification'])
write_csv('posthoc_labels/claim_metrics.csv', claim_metrics, list(claim_metrics[0]))
write_csv('posthoc_labels/changed_labels.csv', changes, ['task','labels','original_label','audited_label','audit_classification','original_decision','recomputed_decision','original_accept_correct_delta','recomputed_accept_correct_delta','coverage_delta'])
write_json('posthoc_labels/counts.json', stats)
(POST / 'README.md').write_text('Post-hoc, never used for any decision.\n\n'
    'All input label and claim access occurred after the pushed signal-audit-labelfree tag. '
    'Original oracle labels were checked against the audited CSV original column; all normalized oracle/verifier/candidate digests match frozen candidates. '
    'The original records are mounted read-only at /original; host prefix is /home/sankalp/projects/cis695-agent-reliability. '
    'All 83 claims are RESOLVED. Precision and coverage use Wilson 95% intervals with z=1.959963984540054. '
    'No inference is made from an absent grader-gap entry. Label changes cannot change acceptance coverage because decisions were already frozen.\n\n'
    + json.dumps(stats, indent=2) + '\n')
print(json.dumps({'counts':stats,'accept_metrics':metrics,'claim_metrics':claim_metrics},indent=2))
