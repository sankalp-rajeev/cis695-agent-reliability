"""Classify V4 absence only where a stored field supplies the reason."""
from collections import Counter
from audit_common import OUT, groups, selected_records, write_csv, write_json

CLASSES = (
    'generator produced no usable test',
    'test did not fail on the unpatched tree (filtered out)',
    'test unstable across repeats',
    'execution error or timeout',
    'output parsing problem',
    'environment or network',
    'other',
    'UNKNOWN',
)


def classify(signal):
    detail = signal.get('detail', '')
    if detail.startswith('generator wrote no test files ('):
        return CLASSES[0], 'inherent to the generator under the recorded budget', 'No test bytes exist for a parser to recover; the record explicitly reports no test files.'
    if detail == 'patch is empty':
        return 'other', 'fixable by parser or tooling (skip accounting only)', 'V4 was skipped for an empty patch; tooling can distinguish this skip, but cannot manufacture repair evidence.'
    return 'UNKNOWN', 'NOT_AVAILABLE', 'The record does not supply an explicit supported classification; do not guess.'


records = selected_records()
rows, failures, class_counts = [], [], []
stats = {}
for cohort, group in groups(records).items():
    counts = Counter()
    outcomes = Counter()
    for task, (path, record) in group.items():
        signal = record['reproduction']
        outcomes[signal['outcome']] += 1
        if signal['outcome'] == 'NOT_AVAILABLE':
            category, remediation, reason = classify(signal)
            counts[category] += 1
            rows.append(dict(cohort=cohort, task=task, category=category,
                             remediation=remediation, evidence=signal.get('detail', ''),
                             remediation_evidence=reason, record=path,
                             raw_output_status='NOT_AVAILABLE: no raw generator output stored in this verification record'))
        elif signal['outcome'] == 'FAIL':
            details = []
            for test in signal.get('findings', {}).get('patched', []):
                if test.get('verdict') == 'fail':
                    assertions = [line.split('AssertionError:', 1)[1].strip().split(': {', 1)[0]
                                  for run in test.get('runs', [])
                                  for line in run.get('tail', '').splitlines() if 'AssertionError:' in line]
                    details.append(test['path'] + ': ' + (assertions[0] if assertions else 'recorded repeat verdict fail'))
            failures.append(dict(cohort=cohort, task=task,
                                 reason=signal.get('detail', '') + '; ' + '; '.join(details), record=path))
    for category in CLASSES:
        class_counts.append(dict(cohort=cohort, category=category, count=counts[category]))
    stats[cohort] = dict(tasks=len(group), outcomes=dict(outcomes),
                         unavailable_classes={c: counts[c] for c in CLASSES})
write_csv('v4_not_available_breakdown.csv', rows, ['cohort', 'task', 'category', 'remediation', 'evidence', 'remediation_evidence', 'record', 'raw_output_status'])
write_csv('v4_class_counts.csv', class_counts, ['cohort', 'category', 'count'])
write_csv('v4_failures.csv', failures, ['cohort', 'task', 'reason', 'record'])
write_json('v4_counts.json', stats)
excerpts = ['# V4 evidence excerpts\n',
            'Raw generator output is NOT_AVAILABLE in the approved records for every observed absence class. '
            'The following are recorded detail excerpts, not fabricated raw-output excerpts. '
            'No external trajectory or unapproved analysis output was opened.\n']
for category in CLASSES:
    example = next((r for r in rows if r['category'] == category), None)
    excerpts.append('\n## ' + category + '\n')
    if example:
        excerpts.extend(['Record: ' + example['record'] + '\n',
                         'Raw-output excerpt: NOT_AVAILABLE (not stored in the verification record).\n',
                         'Recorded detail excerpt (first 20 lines):\n\n```text\n' + '\n'.join(example['evidence'].splitlines()[:20]) + '\n```\n',
                         'Remediation: ' + example['remediation'] + '. ' + example['remediation_evidence'] + '\n'])
    else:
        excerpts.append('NOT_AVAILABLE: no selected record belongs to this class; no example or remediation claim is supported.\n')
(OUT / 'v4_excerpts.md').write_text('\n'.join(excerpts))
(OUT / 'v4_notes.md').write_text(
    'Stored V4 availability is fully accounted for by explicit recorded details; no unknown reason was inferred.\n\n'
    + str(stats) + '\n\nThe only FAIL task is django__django-10973: one stable generated test still fails '
    'on the patched tree because the subprocess environment does not inherit os.environ. '
    'No generated tests were rerun. The no-output records report LimitsExceeded and no frozen test files; '
    'they cannot distinguish a step, cost, or time limit or establish permanent generator inability. '
    'The generator-side remediation category is conditional on the stored budget, not a claim that a budget change cannot help. '
    'Raw generator stdout is absent; requested raw excerpts are NOT_AVAILABLE, with recorded-detail excerpts supplied separately.\n')
print(stats)
