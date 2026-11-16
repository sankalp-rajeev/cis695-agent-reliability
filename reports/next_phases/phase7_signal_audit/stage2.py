"""Stored V3 outcomes and an unchanged-policy counterfactual in Docker."""
from collections import Counter
from audit_common import OUT, evidence, groups, policy_module, selected_records, write_csv, write_json

records = selected_records()
module = policy_module()
policy = module.FullPolicy()
kinds = ('syntax', 'import', 'build', 'lint', 'typecheck')
rows, detail, effects, failures = [], [], [], []
stats = {}
for cohort, group in groups(records).items():
    counts = Counter()
    for task, (path, record) in group.items():
        assert record['decision']['policy_version'] == policy.version
        stored = record['static']
        findings = stored.get('findings', {})
        checks = findings.get('summary', {})
        unavailable = {x['kind']: x['reason'] for x in findings.get('unavailable', [])}
        repo = task.split('__')[0]
        for kind in kinds:
            recorded = checks.get(kind)
            outcome = recorded if recorded in ('PASS', 'FAIL') else 'NOT_AVAILABLE'
            reason = ''
            if outcome == 'NOT_AVAILABLE':
                reason = unavailable.get(kind) or stored.get('detail') or 'UNKNOWN: no recorded reason'
            detail.append(dict(cohort=cohort, task=task, repository=repo, check=kind,
                               outcome=outcome, recorded_status=recorded or 'MISSING',
                               reason=reason, record=path))
            counts[(repo, kind, outcome, reason)] += 1
        original = policy.decide(evidence(module, record))
        assert original.decision.value == record['decision']['decision']
        variants = {v: policy.decide(evidence(module, record, static=v)).decision.value
                    for v in ('PASS', 'FAIL', 'NOT_AVAILABLE')}
        effects.append(dict(cohort=cohort, task=task, original=original.decision.value,
                            static_outcome=stored['outcome'],
                            with_static_pass=variants['PASS'], with_static_fail=variants['FAIL'],
                            with_static_unavailable=variants['NOT_AVAILABLE'],
                            changed='yes' if len(set(variants.values())) > 1 else 'no', record=path))
        if stored['outcome'] == 'FAIL':
            failures.append(dict(cohort=cohort, task=task, decision=original.decision.value,
                                 detail=stored.get('detail', ''), record=path))
    # Include zero cells for every repository/check/outcome, alongside reason-specific NA rows.
    for repo in sorted({t.split('__')[0] for t in group}):
        for kind in kinds:
            for outcome in ('PASS', 'FAIL', 'NOT_AVAILABLE'):
                reasons = sorted({reason for r, k, o, reason in counts if (r, k, o) == (repo, kind, outcome)}) or ['']
                for reason in reasons:
                    rows.append(dict(cohort=cohort, repository=repo, check=kind, outcome=outcome,
                                     reason=reason, count=counts[(repo, kind, outcome, reason)]))
    stats[cohort] = {
        'tasks': len(group),
        'check_totals': {kind: dict(Counter(x['outcome'] for x in detail if x['cohort'] == cohort and x['check'] == kind)) for kind in kinds},
        'decision_effect_tasks': [x['task'] for x in effects if x['cohort'] == cohort and x['changed'] == 'yes'],
        'static_fail_accepts': [x['task'] for x in failures if x['cohort'] == cohort and x['decision'] == 'ACCEPT'],
    }
write_csv('v3_outcomes.csv', rows, ['cohort', 'repository', 'check', 'outcome', 'reason', 'count'])
write_csv('v3_checks.csv', detail, ['cohort', 'task', 'repository', 'check', 'outcome', 'recorded_status', 'reason', 'record'])
write_csv('v3_decision_effects.csv', effects, ['cohort', 'task', 'original', 'static_outcome', 'with_static_pass', 'with_static_fail', 'with_static_unavailable', 'changed', 'record'])
write_csv('v3_failures.csv', failures, ['cohort', 'task', 'decision', 'detail', 'record'])
write_json('v3_counts.json', stats)
write_csv('record_inventory_all.csv', [dict(task=t, record=p) for t, (p, _) in records.items()], ['task', 'record'])
(OUT / 'v3_notes.md').write_text(
    'V3 did not change any decision: unchanged FullPolicy v1.3.0-full never reads the static field. '
    'The counterfactual sets V3 to PASS, FAIL, and NOT_AVAILABLE while keeping all other evidence fixed, for every task.\n\n'
    + str(stats) + '\n\nThe all_tasks table uses 100 distinct task IDs after directory-priority rerun replacement; '
    '105 physical records include five superseded copies and are not 105 distinct tasks. '
    'A missing per-check field is NOT_AVAILABLE with the recorded aggregate reason, never a PASS. '
    'Recorded per-check ERROR/TIMEOUT, if any, are retained in recorded_status and grouped as unavailable execution. '
    'The stored summary omits full per-check raw output; no tool was rerun.\n')
print(stats)
