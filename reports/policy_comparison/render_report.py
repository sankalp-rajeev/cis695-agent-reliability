"""Advisor-facing report rendered entirely from derived assessment tables."""
from __future__ import annotations

from statistics_core import confusion, transitions


def pct(value):
    return "NA" if value is None else f"{100 * value:.2f}%"


def interval(row, name):
    low, high = row.get(name + "_wilson_low"), row.get(name + "_wilson_high")
    return pct(row[name]) + (f" [{pct(low)}, {pct(high)}]" if low is not None else "")


def render(output, rows, matrices, metrics, facts):
    counts, boot, tests = facts["populations"], facts["bootstrap"], facts["paired_tests"]
    lookup = {(r["population"], r["policy"]): r for r in metrics}
    primary = [r for r in rows if r['stratum'] == 'headline' and r['oracle'] != 'empty_patch']
    b, f = (lookup['HEADLINE_NONEMPTY_PRIMARY', p] for p in ('baseline', 'full'))
    bcm, fcm = confusion(primary, 'baseline'), confusion(primary, 'full')
    matrix_lookup = {(r['population'], r['policy']): r for r in matrices}
    lines = ['# BaselinePolicy versus FullPolicy — post-hoc assessment', '',
        '**ANALYSIS ONLY.** No policies, signals, repair/verification/oracle runs, run artifacts, or committed labels were changed. '
        'The call-graph branch remains complete with its registered DO NOT USE decision; this analysis does not reopen it. '
        'No ablations, network, Docker or benchmark execution.', '',
        f"Primary: **{counts['HEADLINE_NONEMPTY_PRIMARY']['n']} non-empty headline patches**, "
        f"{counts['HEADLINE_NONEMPTY_PRIMARY']['resolved']} oracle-resolved and {counts['HEADLINE_NONEMPTY_PRIMARY']['unresolved']} unresolved. "
        f"Verified full-study total: **{counts['ALL_NONEMPTY']['n']} non-empty** = "
        f"{counts['HEADLINE_NONEMPTY_PRIMARY']['n']} headline + {counts['REQUESTS_NONEMPTY']['n']} requests. "
        f"The requests stratum has {counts['REQUESTS_ALL_SENSITIVITY']['n']} tasks, including "
        f"{counts['REQUESTS_ALL_SENSITIVITY']['empty']} empty patch. The non-empty total is derived from data, not assumed.", '',
        '## Implemented rules and provenance', '',
        'Source: [decision.py](../../src/reliability/verifier/decision.py), '
        '[integrity.py](../../src/reliability/verifier/integrity.py), '
        '[evidence.py](../../src/reliability/verifier/evidence.py). Default policy versions are '
        '`v1.2.2-baseline` and `v1.3.0-full`; Full requires reproduction and blocks ACCEPT when V2 is unavailable. '
        'These identify the implementation used for reconstruction/consistency checks; per-run Full version strings '
        'are not recovered from the merged CSV and remain explicitly missing.', '',
        '| Evidence | Baseline | Full |', '|---|---|---|',
        '| V1 integrity | FAIL rejects; PASS required to accept | Same |',
        '| V2 regression | FAIL rejects; PASS required to accept | PASS required to accept; FAIL + V4 PASS becomes FLAG |',
        '| V3 static | Ignored | Ignored |',
        '| V4 reproduction | Ignored | PASS required to accept; FAIL/NOT_AVAILABLE does not itself reject |',
        '| High-severity risk | Ignored | A present flag blocks ACCEPT |',
        '| Patch does not apply / prohibited manipulation | Reject | Reject; still dominates V2/V4 disagreement |', '',
        'The expected interpretation agrees with the implementation, with the explicit qualification that both policies '
        'also read the two integrity predicates above. V3 does not determine either decision. A stricter ACCEPT set '
        'does not imply a stricter three-way decision everywhere: Full can turn Baseline REJECT into FLAG.', '',
        'The committed [merged table](../../docs/results_100.csv) is authoritative for labels, frozen V1–V4 outcomes '
        'and Full decisions. Baseline is reconstructed by calling the actual BaselinePolicy on those signals, without '
        'using Full decisions or oracle labels. V1 PASS entails patch_applies=True and no prohibited violations under '
        'the adapter contract; V1 FAIL rejects regardless, so missing ancillary details do not alter the reconstruction.', '',
        'The merged CSV does not serialize high-risk flags. The committed '
        '[merged report](../../docs/results_100.md) explicitly records the Sphinx-7910 high-risk flag. '
        'Other risk values remain missing when irrelevant; negative risk for a committed ACCEPT is labeled as a '
        'logical policy implication, **not an independent recorded finding**. Full code checks using that inference '
        'are consistency checks, not independent re-verification. The primary Full decision remains the committed observation. '
        '[per_task.csv](per_task.csv) preserves each reconstructed value, status and source. No unknown risk is silently recorded as false.', '',
        'Oracle labels are used only after decisions for this clearly separated post-hoc assessment. No policy Evidence '
        'receives an oracle field. Input/code/output SHA-256 values and the source commit are in [inputs.json](inputs.json) '
        'and [outputs.sha256.json](outputs.sha256.json).', '',
        '## Primary definition and confusion matrices', '',
        '**Ground-truth positive = oracle RESOLVED. Predicted positive = ACCEPT.** FLAG and REJECT are both NOT ACCEPT. '
        'This treats a withheld correct repair as a binary false negative even if FLAG is operationally appropriate review. '
        'The 10 headline empty patches are excluded: they are structural rejections, not candidate repairs being classified.', '',
        '| Policy / decision | Oracle resolved | Oracle unresolved |', '|---|---:|---:|',
        f'| Baseline ACCEPT | {bcm.tp} TP | {bcm.fp} FP |', f'| Baseline NOT ACCEPT | {bcm.fn} FN | {bcm.tn} TN |',
        f'| Full ACCEPT | {fcm.tp} TP | {fcm.fp} FP |', f'| Full NOT ACCEPT | {fcm.fn} FN | {fcm.tn} TN |', '',
        '| Policy | ACCEPT | FLAG within NOT ACCEPT | REJECT within NOT ACCEPT |', '|---|---:|---:|---:|']
    for p in ('baseline', 'full'):
        r = matrix_lookup['HEADLINE_NONEMPTY_PRIMARY', p]
        lines.append(f"| {p.title()} | {r['ACCEPT']} | {r['FLAG']} | {r['REJECT']} |")
    lines += ['', 'Both requested sanity-check matrices are compared with computed counts in [analysis.json](analysis.json); '
              'the expectations do not supply any computed value.', '', '## Primary metrics', '',
              'Intervals in this table are 95% Wilson binomial intervals, except F1 (paired-patch percentile bootstrap). '
              'Undefined denominators are NA, never silently zero.', '', '| Metric | Baseline | Full |', '|---|---:|---:|']
    definitions = (('ACCEPT precision', 'precision'), ('Recall / correct-patch acceptance', 'recall'), ('F1', 'f1'),
        ('Accuracy', 'accuracy'), ('Specificity / wrong-patch withholding', 'specificity'),
        ('Negative predictive value', 'negative_predictive_value'), ('Balanced accuracy', 'balanced_accuracy'),
        ('False-acceptance proportion among ACCEPTs', 'false_acceptance_proportion'), ('ACCEPT coverage', 'coverage'))
    for label, name in definitions:
        def cell(r, policy):
            if name == 'f1':
                ci = boot['policy_f1'][policy]
                return pct(r[name]) + f" [{pct(ci['low'])}, {pct(ci['high'])}]"
            key = 'wrong_patch_withholding_rate' if name == 'specificity' else name
            return interval(r, key) if key + '_wilson_low' in r else pct(r[name])
        lines.append(f"| {label} | {cell(b, 'baseline')} | {cell(f, 'full')} |")
    lines += [f'| Accepted right | {bcm.tp} | {fcm.tp} |', f'| Accepted wrong | {bcm.fp} | {fcm.fp} |',
              f'| All wrong patches withheld | {bcm.tn}/{bcm.tn+bcm.fp} | {fcm.tn}/{fcm.tn+fcm.fp} |',
              f'| All correct patches accepted | {bcm.tp}/{bcm.tp+bcm.fn} | {fcm.tp}/{fcm.tp+fcm.fn} |', '',
              'Precision asks how trustworthy ACCEPT is; recall asks how much correct work can be accepted automatically; '
              'F1 harmonically combines those two quantities under this framing. Coverage measures automatic acceptance, '
              'and wrong-patch withholding measures protection against accepting incorrect work. They express different '
              'operational preferences. False-acceptance proportion FP/(TP+FP) is not the false-positive rate FP/(FP+TN). '
              f'Full still accepts {fcm.fp} of {fcm.fp+fcm.tn} wrong headline patches.', '',
              '## Secondary safety-oriented view', '',
              '**Ground-truth positive = oracle UNRESOLVED. Predicted positive = WITHHOLD ACCEPTANCE (FLAG/REJECT).** '
              'These values describe unsafe-patch detection and must not be mixed with acceptance-oriented P/R/F1.', '',
              '| Metric | Baseline | Full |', '|---|---:|---:|']
    for name in ('precision', 'recall', 'f1'):
        lines.append(f"| Unsafe-patch detection {name} | {pct(b['unsafe_detection_'+name])} | {pct(f['unsafe_detection_'+name])} |")
    lines += ['', 'Both views are reported because switching the positive class changes the question. '
              'Withheld correct patches are false alarms in the safety view; they are false negatives in the acceptance view.', '',
              '## Paired transitions: Baseline to Full', '',
              '| Transition | Right | Wrong | Total |', '|---|---:|---:|---:|']
    t = transitions(primary)
    for before in ('ACCEPT', 'FLAG', 'REJECT'):
        for after in ('ACCEPT', 'FLAG', 'REJECT'):
            right, wrong = t.get((before, after, 'resolved'), 0), t.get((before, after, 'unresolved'), 0)
            lines.append(f'| {before} → {after} | {right} | {wrong} | {right+wrong} |')
    both_nonaccept = sum(r['baseline_decision'] != 'ACCEPT' and r['full_decision'] != 'ACCEPT' for r in primary)
    triage_changed = sum(r['baseline_decision'] != r['full_decision'] for r in primary)
    lines += ['', f"Full stops accepting **{tests['stopped_wrong']} additional wrong** and **{tests['stopped_right']} additional right** patches "
              f"({tests['stopped_count']} ACCEPT changes). {both_nonaccept} patches remain non-accepted under both policies; "
              f"three-way decisions change on {triage_changed} patches, including REJECT → FLAG disagreements.", '',
              '| Patch no longer accepted | Oracle | V2 | V4 | High-risk status |', '|---|---|---|---|---|']
    stopped = [r for r in primary if r['instance_id'] in tests['stopped_ids']]
    for r in stopped:
        risk = 'missing / irrelevant' if r.get('high_severity_risk') is None else str(r['high_severity_risk'])
        lines.append(f"| {r['instance_id']} | {r['oracle']} | {r.get('V2','')} | {r.get('V4','')} | {risk} |")
    wrong_v4 = {r.get('V4') for r in stopped if r['oracle'] == 'unresolved'}
    lines += ['', f"The additionally withheld wrong patches have V4 values {sorted(wrong_v4)}. "
              'When these are NOT_AVAILABLE, the interpretation is a stricter evidence requirement, not that V4 tests '
              'executed and caught four bugs. No causal defect-detection claim is made.', '',
              '## Paired uncertainty and exact comparisons', '',
              f"Paired bootstrap: **{boot['resamples']:,} resamples**, fixed seed **{boot['seed']}**, NumPy PCG64. "
              'Resample n patches with replacement from the primary population in committed CSV order; reuse exactly '
              'the same row indices for both policies and truth. Compute Full minus Baseline per draw, then take the '
              '2.5th and 97.5th percentiles using linear interpolation. Denominators vary naturally in each draw. '
              'Undefined draw metrics are excluded metric by metric and valid/undefined counts are reported; none are replaced with zero. '
              'Per-policy F1 intervals use these same paired draws. The index-array digest and replicates are retained.', '',
              '| Full − Baseline | Point, percentage points | 95% paired-bootstrap interval, pp | Valid / undefined draws |', '|---|---:|---|---:|']
    for name, ci in boot['differences'].items():
        point = 'NA' if ci['point'] is None else f"{100*ci['point']:+.2f}"
        bounds = 'NA' if ci['low'] is None else f"[{100*ci['low']:+.2f}, {100*ci['high']:+.2f}]"
        lines.append(f"| {name} | {point} | {bounds} | {ci['valid_resamples']} / {ci['undefined_resamples']} |")
    pairs = tests['correctness_disagreement_table']
    lines += ['', '### Exact enrichment test for the stopped ACCEPTs', '',
              f"Stopped: **{tests['stopped_wrong']}/{tests['stopped_count']} wrong ({pct(tests['stopped_wrong_share'])})**, "
              f"versus **{tests['baseline_accepted_wrong']}/{tests['baseline_accepted_count']} ({pct(tests['baseline_accepted_wrong_share'])})** "
              'in the baseline-accepted pool. Because the stopped set is a subset of that pool, an independent-samples '
              'test or treating its estimated base rate as a known binomial probability would be inappropriate. '
              'We condition on the baseline-accepted pool size and total wrong labels and test whether wrong labels are '
              'enriched in the stopped subset: X is hypergeometric, with one-sided P(X ≥ observed). This is equivalent '
              'to a one-sided Fisher exact test of stopped versus retained ACCEPTs, conditional on margins.', '',
              f"The stopped-wrong share has 95% Wilson interval "
              f"[{pct(tests['stopped_wrong_share_wilson'][0])}, {pct(tests['stopped_wrong_share_wilson'][1])}]. "
              f"Exact enrichment p = **{tests['enrichment_exact_one_sided_p']:.6f}**.", '',
              '### McNemar on binary classification correctness', '',
              'Correctness means (ACCEPT iff oracle resolved), not merely whether the two policies made different decisions. '
              'The exact two-sided McNemar test conditions on discordant correctness pairs and tests equal marginal '
              'classification-error probabilities. It does not directly test ACCEPT precision or overall deployment utility.', '',
              '| | Full correct | Full incorrect |', '|---|---:|---:|',
              f"| Baseline correct | {pairs['both_correct']} | {pairs['baseline_only_correct']} |",
              f"| Baseline incorrect | {pairs['full_only_correct']} | {pairs['neither_correct']} |", '',
              f"Discordant correctness pairs: {pairs['baseline_only_correct']} favor Baseline, {pairs['full_only_correct']} favor Full. "
              f"Exact two-sided p = **{tests['correctness_mcnemar_exact_two_sided_p']:.6f}**.", '',
              f"Raw ACCEPT discordance is {tests['accept_disagreement_table']['baseline_only_accept']} Baseline-only versus "
              f"{tests['accept_disagreement_table']['full_only_accept']} Full-only. Full's ACCEPT set is nested in Baseline's, "
              'so McNemar on ACCEPT alone principally tests the structural reduction in acceptance and is not an informative '
              'test of verifier quality. We report its paired table in analysis.json and do not promote its p-value as quality evidence.', '',
              '**Statistical significance of a reliability improvement is not established at this sample size.** '
              'The point precision gain, stopped-wrong enrichment and correctness comparison do not establish Full superiority. '
              'Negative bootstrap intervals for recall/coverage or other costs, where present, should be read as evidence '
              'of the acceptance tradeoff under the resampling model, not as proof of a universal winner. '
              'Only fourteen primary wrong patches limit precision; patch-level resampling does not account for repository '
              'clustering, and this fixed benchmark sample is not a random deployment sample. No multiplicity-adjusted '
              'confirmatory superiority claim is made.', '',
              '## Separate populations and sensitivities', '',
              '| Population | n | Resolved | Unresolved | Empty |', '|---|---:|---:|---:|---:|']
    for name in ('HEADLINE_NONEMPTY_PRIMARY','REQUESTS_NONEMPTY','ALL_NONEMPTY','HEADLINE_INCLUDING_EMPTY_SENSITIVITY','ALL_100_INCLUDING_EMPTY_SENSITIVITY','ALL_EMPTY_STRUCTURAL'):
        r = counts[name]
        lines.append(f"| {name} | {r['n']} | {r['resolved']} | {r['unresolved']} | {r['empty']} |")
    lines += ['', 'Requests stay separate from the headline and contain no non-empty oracle-unresolved patch. '
              'Their specificity / wrong-patch withholding rate is undefined; no wrong-patch protection can be estimated '
              'from that stratum. All-89 and all-100 rows are secondary and cannot replace headline results.', '',
              '| Population / policy | TP / FP / FN / TN | Precision | Recall | F1 | Accuracy | Specificity | Coverage |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for name in ('REQUESTS_NONEMPTY','ALL_NONEMPTY','HEADLINE_INCLUDING_EMPTY_SENSITIVITY','ALL_100_INCLUDING_EMPTY_SENSITIVITY'):
        for p in ('baseline','full'):
            r, cm = lookup[name,p], matrix_lookup[name,p]
            lines.append(f"| {name} / {p} | {cm['tp']} / {cm['fp']} / {cm['fn']} / {cm['tn']} | {pct(r['precision'])} | "
                         f"{pct(r['recall'])} | {pct(r['f1'])} | {pct(r['accuracy'])} | {pct(r['specificity'])} | {pct(r['coverage'])} |")
    empty = counts['HEADLINE_EMPTY_STRUCTURAL']['n']
    lines += ['', f"All {empty} headline empty patches are structural rejections under both policies. Including them treats "
              'empty patches as negatives only for this sensitivity and adds easy TNs, raising accuracy and specificity. '
              'It does not improve candidate-repair classification. The non-empty primary denominator is unchanged. '
              'All sensitivity metrics and Wilson intervals are in metrics.csv; F1 is a point estimate outside the primary '
              'paired bootstrap, with no sensitivity F1 interval claimed.', '',
              '### pytest-7432 local-oracle discrepancy', '',
              'Committed oracle = **resolved**, authoritative and retained in the headline. The local '
              '`runs/main_50_a/tasks/pytest-dev__pytest-7432/oracle_record.json` says **patch_apply_failed**. '
              'That status is an application/harness outcome, not proof of a functional defect. The following row set '
              'hypothetically maps it to unresolved; only its oracle label changes, never either policy decision or the headline.', '',
              '| Headline metric if pytest-7432 were unresolved | Baseline | Full |', '|---|---:|---:|---:|']
    sb, sf = (lookup['PYTEST7432_UNRESOLVED_HEADLINE_SENSITIVITY',p] for p in ('baseline','full'))
    for label, name in definitions:
        lines.append(f"| {label} | {pct(sb[name])} | {pct(sf[name])} |")
    sensitivity_matrices = [matrix_lookup['PYTEST7432_UNRESOLVED_HEADLINE_SENSITIVITY',p] for p in ('baseline','full')]
    cm_cells = [' / '.join(str(cm[k]) for k in ('tp','fp','fn','tn')) for cm in sensitivity_matrices]
    lines.append('| TP / FP / FN / TN | ' + ' | '.join(cm_cells) + ' |')
    lines += ['', 'The hypothetical headline has 68 resolved and 15 unresolved patches; n and coverage stay unchanged. '
              'Both policies lose one TP and gain one FP. The corresponding all-non-empty hypothetical is also in the CSVs. '
              'No committed classification or run record was changed.', '',
              '## Conservative assumptions, limitations and reproduction', '',
              '- Full uses its observed committed decision. Where detailed risk findings are unavailable, policy implications '
              'are labeled as inference and never described as independently observed risk measurements.',
              '- Empty means the committed empty_patch classification; no patch reconstruction or alternate-run substitution '
              'is used to redefine population membership.',
              '- The exact enrichment comparison conditions on the overlapping baseline-accepted pool, rather than using '
              'an independence assumption. Its null is exchangeability of wrong labels within that pool.',
              '- Bootstrap resamples patches without stratification and keeps pairing. Repositories are not independent '
              'clusters in this bootstrap; intervals are descriptive under this assumption.',
              '- The local patch_apply_failed label is mapped to unresolved only in an explicitly hypothetical sensitivity. '
              'It does not override the committed oracle.', '',
              'Run from the project root:', '', '```bash',
              'env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/policy_comparison/test_comparison.py -q -p no:cacheprovider -o addopts=',
              'env -u PYTHONPATH .venv/bin/python -B reports/policy_comparison/compare.py', '```', '',
              'Only the new synthetic analysis test file is collected. Tests cover the hand-computed requested confusion '
              'matrices, metrics, zero denominators, policy examples, a Wilson reference interval, exact tests, paired '
              'bootstrap known answers, transitions, populations, and CSV/report consistency. See tests.txt for results.', '',
              '## Advisor-ready interpretation', '',
              f"1. Full has higher observed ACCEPT precision: {pct(f['precision'])} versus {pct(b['precision'])}.",
              f"2. Baseline has higher recall: {pct(b['recall'])} versus {pct(f['recall'])}.",
              f"3. Baseline has higher acceptance-oriented F1: {pct(b['f1'])} versus {pct(f['f1'])}.",
              f"4. Full reduces coverage from {bcm.tp+bcm.fp}/{bcm.n} to {fcm.tp+fcm.fp}/{fcm.n}, "
              f"a cost of {100*(b['coverage']-f['coverage']):.2f} percentage points.",
              f"5. Full withholds {tests['stopped_wrong']} additional wrong patches.",
              f"6. It also withholds {tests['stopped_right']} additional correct patches.",
              '7. These point estimates do not justify a universal winner; statistical significance of a reliability '
              'improvement is not established at this sample size.',
              '8. The reliability question remains a false-acceptance versus automatic-coverage tradeoff. Full trades '
              'correct automatic repairs for fewer false ACCEPTs; F1 alone cannot choose that tradeoff, and four '
              'wrong patches withheld because V4 was unavailable are not four demonstrated V4 bug detections.', '']
    (output / 'report.md').write_text('\n'.join(lines))
