# BaselinePolicy versus FullPolicy — post-hoc assessment

**ANALYSIS ONLY.** No policies, signals, repair/verification/oracle runs, run artifacts, or committed labels were changed. The call-graph branch remains complete with its registered DO NOT USE decision; this analysis does not reopen it. No ablations, network, Docker or benchmark execution.

Primary: **83 non-empty headline patches**, 69 oracle-resolved and 14 unresolved. Verified full-study total: **89 non-empty** = 83 headline + 6 requests. The requests stratum has 7 tasks, including 1 empty patch. The non-empty total is derived from data, not assumed.

## Implemented rules and provenance

Source: [decision.py](../../src/reliability/verifier/decision.py), [integrity.py](../../src/reliability/verifier/integrity.py), [evidence.py](../../src/reliability/verifier/evidence.py). Default policy versions are `v1.2.2-baseline` and `v1.3.0-full`; Full requires reproduction and blocks ACCEPT when V2 is unavailable. These identify the implementation used for reconstruction/consistency checks; per-run Full version strings are not recovered from the merged CSV and remain explicitly missing.

| Evidence | Baseline | Full |
|---|---|---|
| V1 integrity | FAIL rejects; PASS required to accept | Same |
| V2 regression | FAIL rejects; PASS required to accept | PASS required to accept; FAIL + V4 PASS becomes FLAG |
| V3 static | Ignored | Ignored |
| V4 reproduction | Ignored | PASS required to accept; FAIL/NOT_AVAILABLE does not itself reject |
| High-severity risk | Ignored | A present flag blocks ACCEPT |
| Patch does not apply / prohibited manipulation | Reject | Reject; still dominates V2/V4 disagreement |

The expected interpretation agrees with the implementation, with the explicit qualification that both policies also read the two integrity predicates above. V3 does not determine either decision. A stricter ACCEPT set does not imply a stricter three-way decision everywhere: Full can turn Baseline REJECT into FLAG.

The committed [merged table](../../docs/results_100.csv) is authoritative for labels, frozen V1–V4 outcomes and Full decisions. Baseline is reconstructed by calling the actual BaselinePolicy on those signals, without using Full decisions or oracle labels. V1 PASS entails patch_applies=True and no prohibited violations under the adapter contract; V1 FAIL rejects regardless, so missing ancillary details do not alter the reconstruction.

The merged CSV does not serialize high-risk flags. The committed [merged report](../../docs/results_100.md) explicitly records the Sphinx-7910 high-risk flag. Other risk values remain missing when irrelevant; negative risk for a committed ACCEPT is labeled as a logical policy implication, **not an independent recorded finding**. Full code checks using that inference are consistency checks, not independent re-verification. The primary Full decision remains the committed observation. [per_task.csv](per_task.csv) preserves each reconstructed value, status and source. No unknown risk is silently recorded as false.

Oracle labels are used only after decisions for this clearly separated post-hoc assessment. No policy Evidence receives an oracle field. Input/code/output SHA-256 values and the source commit are in [inputs.json](inputs.json) and [outputs.sha256.json](outputs.sha256.json).

## Primary definition and confusion matrices

**Ground-truth positive = oracle RESOLVED. Predicted positive = ACCEPT.** FLAG and REJECT are both NOT ACCEPT. This treats a withheld correct repair as a binary false negative even if FLAG is operationally appropriate review. The 10 headline empty patches are excluded: they are structural rejections, not candidate repairs being classified.

| Policy / decision | Oracle resolved | Oracle unresolved |
|---|---:|---:|
| Baseline ACCEPT | 53 TP | 11 FP |
| Baseline NOT ACCEPT | 16 FN | 3 TN |
| Full ACCEPT | 45 TP | 7 FP |
| Full NOT ACCEPT | 24 FN | 7 TN |

| Policy | ACCEPT | FLAG within NOT ACCEPT | REJECT within NOT ACCEPT |
|---|---:|---:|---:|
| Baseline | 64 | 13 | 6 |
| Full | 52 | 30 | 1 |

Both requested sanity-check matrices are compared with computed counts in [analysis.json](analysis.json); the expectations do not supply any computed value.

## Primary metrics

Intervals in this table are 95% Wilson binomial intervals, except F1 (paired-patch percentile bootstrap). Undefined denominators are NA, never silently zero.

| Metric | Baseline | Full |
|---|---:|---:|
| ACCEPT precision | 82.81% [71.79%, 90.12%] | 86.54% [74.73%, 93.32%] |
| Recall / correct-patch acceptance | 76.81% [65.60%, 85.19%] | 65.22% [53.45%, 75.38%] |
| F1 | 79.70% [71.67%, 86.71%] | 74.38% [64.96%, 82.44%] |
| Accuracy | 67.47% | 62.65% |
| Specificity / wrong-patch withholding | 21.43% [7.57%, 47.59%] | 50.00% [26.80%, 73.20%] |
| Negative predictive value | 15.79% | 22.58% |
| Balanced accuracy | 49.12% | 57.61% |
| False-acceptance proportion among ACCEPTs | 17.19% [9.88%, 28.21%] | 13.46% [6.68%, 25.27%] |
| ACCEPT coverage | 77.11% [66.99%, 84.83%] | 62.65% [51.90%, 72.28%] |
| Accepted right | 53 | 45 |
| Accepted wrong | 11 | 7 |
| All wrong patches withheld | 3/14 | 7/14 |
| All correct patches accepted | 53/69 | 45/69 |

Precision asks how trustworthy ACCEPT is; recall asks how much correct work can be accepted automatically; F1 harmonically combines those two quantities under this framing. Coverage measures automatic acceptance, and wrong-patch withholding measures protection against accepting incorrect work. They express different operational preferences. False-acceptance proportion FP/(TP+FP) is not the false-positive rate FP/(FP+TN). Full still accepts 7 of 14 wrong headline patches.

## Secondary safety-oriented view

**Ground-truth positive = oracle UNRESOLVED. Predicted positive = WITHHOLD ACCEPTANCE (FLAG/REJECT).** These values describe unsafe-patch detection and must not be mixed with acceptance-oriented P/R/F1.

| Metric | Baseline | Full |
|---|---:|---:|
| Unsafe-patch detection precision | 15.79% | 22.58% |
| Unsafe-patch detection recall | 21.43% | 50.00% |
| Unsafe-patch detection f1 | 18.18% | 31.11% |

Both views are reported because switching the positive class changes the question. Withheld correct patches are false alarms in the safety view; they are false negatives in the acceptance view.

## Paired transitions: Baseline to Full

| Transition | Right | Wrong | Total |
|---|---:|---:|---:|
| ACCEPT → ACCEPT | 45 | 7 | 52 |
| ACCEPT → FLAG | 8 | 4 | 12 |
| ACCEPT → REJECT | 0 | 0 | 0 |
| FLAG → ACCEPT | 0 | 0 | 0 |
| FLAG → FLAG | 11 | 2 | 13 |
| FLAG → REJECT | 0 | 0 | 0 |
| REJECT → ACCEPT | 0 | 0 | 0 |
| REJECT → FLAG | 5 | 0 | 5 |
| REJECT → REJECT | 0 | 1 | 1 |

Full stops accepting **4 additional wrong** and **8 additional right** patches (12 ACCEPT changes). 19 patches remain non-accepted under both policies; three-way decisions change on 17 patches, including REJECT → FLAG disagreements.

| Patch no longer accepted | Oracle | V2 | V4 | High-risk status |
|---|---|---|---|---|
| django__django-10973 | resolved | PASS | FAIL | missing / irrelevant |
| django__django-13158 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| django__django-15037 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| matplotlib__matplotlib-20676 | unresolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| matplotlib__matplotlib-22871 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| pylint-dev__pylint-4970 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| pylint-dev__pylint-6528 | unresolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| sphinx-doc__sphinx-7910 | resolved | PASS | PASS | True |
| django__django-16631 | unresolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| matplotlib__matplotlib-24637 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| mwaskom__seaborn-3069 | unresolved | PASS | NOT_AVAILABLE | missing / irrelevant |
| sphinx-doc__sphinx-10323 | resolved | PASS | NOT_AVAILABLE | missing / irrelevant |

The additionally withheld wrong patches have V4 values ['NOT_AVAILABLE']. When these are NOT_AVAILABLE, the interpretation is a stricter evidence requirement, not that V4 tests executed and caught four bugs. No causal defect-detection claim is made.

## Paired uncertainty and exact comparisons

Paired bootstrap: **10,000 resamples**, fixed seed **695**, NumPy PCG64. Resample n patches with replacement from the primary population in committed CSV order; reuse exactly the same row indices for both policies and truth. Compute Full minus Baseline per draw, then take the 2.5th and 97.5th percentiles using linear interpolation. Denominators vary naturally in each draw. Undefined draw metrics are excluded metric by metric and valid/undefined counts are reported; none are replaced with zero. Per-policy F1 intervals use these same paired draws. The index-array digest and replicates are retained.

| Full − Baseline | Point, percentage points | 95% paired-bootstrap interval, pp | Valid / undefined draws |
|---|---:|---|---:|
| precision | +3.73 | [-1.34, +9.91] | 10000 / 0 |
| recall | -11.59 | [-19.44, -4.48] | 10000 / 0 |
| f1 | -5.32 | [-11.38, +0.10] | 10000 / 0 |
| accuracy | -4.82 | [-13.25, +3.61] | 10000 / 0 |
| coverage | -14.46 | [-22.89, -7.23] | 10000 / 0 |

### Exact enrichment test for the stopped ACCEPTs

Stopped: **4/12 wrong (33.33%)**, versus **11/64 (17.19%)** in the baseline-accepted pool. Because the stopped set is a subset of that pool, an independent-samples test or treating its estimated base rate as a known binomial probability would be inappropriate. We condition on the baseline-accepted pool size and total wrong labels and test whether wrong labels are enriched in the stopped subset: X is hypergeometric, with one-sided P(X ≥ observed). This is equivalent to a one-sided Fisher exact test of stopped versus retained ACCEPTs, conditional on margins.

The stopped-wrong share has 95% Wilson interval [13.81%, 60.94%]. Exact enrichment p = **0.114275**.

### McNemar on binary classification correctness

Correctness means (ACCEPT iff oracle resolved), not merely whether the two policies made different decisions. The exact two-sided McNemar test conditions on discordant correctness pairs and tests equal marginal classification-error probabilities. It does not directly test ACCEPT precision or overall deployment utility.

| | Full correct | Full incorrect |
|---|---:|---:|
| Baseline correct | 48 | 8 |
| Baseline incorrect | 4 | 23 |

Discordant correctness pairs: 8 favor Baseline, 4 favor Full. Exact two-sided p = **0.387695**.

Raw ACCEPT discordance is 12 Baseline-only versus 0 Full-only. Full's ACCEPT set is nested in Baseline's, so McNemar on ACCEPT alone principally tests the structural reduction in acceptance and is not an informative test of verifier quality. We report its paired table in analysis.json and do not promote its p-value as quality evidence.

**Statistical significance of a reliability improvement is not established at this sample size.** The point precision gain, stopped-wrong enrichment and correctness comparison do not establish Full superiority. Negative bootstrap intervals for recall/coverage or other costs, where present, should be read as evidence of the acceptance tradeoff under the resampling model, not as proof of a universal winner. Only fourteen primary wrong patches limit precision; patch-level resampling does not account for repository clustering, and this fixed benchmark sample is not a random deployment sample. No multiplicity-adjusted confirmatory superiority claim is made.

## Separate populations and sensitivities

| Population | n | Resolved | Unresolved | Empty |
|---|---:|---:|---:|---:|
| HEADLINE_NONEMPTY_PRIMARY | 83 | 69 | 14 | 0 |
| REQUESTS_NONEMPTY | 6 | 6 | 0 | 0 |
| ALL_NONEMPTY | 89 | 75 | 14 | 0 |
| HEADLINE_INCLUDING_EMPTY_SENSITIVITY | 93 | 69 | 14 | 10 |
| ALL_100_INCLUDING_EMPTY_SENSITIVITY | 100 | 75 | 14 | 11 |
| ALL_EMPTY_STRUCTURAL | 11 | 0 | 0 | 11 |

Requests stay separate from the headline and contain no non-empty oracle-unresolved patch. Their specificity / wrong-patch withholding rate is undefined; no wrong-patch protection can be estimated from that stratum. All-89 and all-100 rows are secondary and cannot replace headline results.

| Population / policy | TP / FP / FN / TN | Precision | Recall | F1 | Accuracy | Specificity | Coverage |
|---|---|---:|---:|---:|---:|---:|---:|
| REQUESTS_NONEMPTY / baseline | 3 / 0 / 3 / 0 | 100.00% | 50.00% | 66.67% | 50.00% | NA | 50.00% |
| REQUESTS_NONEMPTY / full | 2 / 0 / 4 / 0 | 100.00% | 33.33% | 50.00% | 33.33% | NA | 33.33% |
| ALL_NONEMPTY / baseline | 56 / 11 / 19 / 3 | 83.58% | 74.67% | 78.87% | 66.29% | 21.43% | 75.28% |
| ALL_NONEMPTY / full | 47 / 7 / 28 / 7 | 87.04% | 62.67% | 72.87% | 60.67% | 50.00% | 60.67% |
| HEADLINE_INCLUDING_EMPTY_SENSITIVITY / baseline | 53 / 11 / 16 / 13 | 82.81% | 76.81% | 79.70% | 70.97% | 54.17% | 68.82% |
| HEADLINE_INCLUDING_EMPTY_SENSITIVITY / full | 45 / 7 / 24 / 17 | 86.54% | 65.22% | 74.38% | 66.67% | 70.83% | 55.91% |
| ALL_100_INCLUDING_EMPTY_SENSITIVITY / baseline | 56 / 11 / 19 / 14 | 83.58% | 74.67% | 78.87% | 70.00% | 56.00% | 67.00% |
| ALL_100_INCLUDING_EMPTY_SENSITIVITY / full | 47 / 7 / 28 / 18 | 87.04% | 62.67% | 72.87% | 65.00% | 72.00% | 54.00% |

All 10 headline empty patches are structural rejections under both policies. Including them treats empty patches as negatives only for this sensitivity and adds easy TNs, raising accuracy and specificity. It does not improve candidate-repair classification. The non-empty primary denominator is unchanged. All sensitivity metrics and Wilson intervals are in metrics.csv; F1 is a point estimate outside the primary paired bootstrap, with no sensitivity F1 interval claimed.

### pytest-7432 local-oracle discrepancy

Committed oracle = **resolved**, authoritative and retained in the headline. The local `runs/main_50_a/tasks/pytest-dev__pytest-7432/oracle_record.json` says **patch_apply_failed**. That status is an application/harness outcome, not proof of a functional defect. The following row set hypothetically maps it to unresolved; only its oracle label changes, never either policy decision or the headline.

| Headline metric if pytest-7432 were unresolved | Baseline | Full |
|---|---:|---:|---:|
| ACCEPT precision | 81.25% | 84.62% |
| Recall / correct-patch acceptance | 76.47% | 64.71% |
| F1 | 78.79% | 73.33% |
| Accuracy | 66.27% | 61.45% |
| Specificity / wrong-patch withholding | 20.00% | 46.67% |
| Negative predictive value | 15.79% | 22.58% |
| Balanced accuracy | 48.24% | 55.69% |
| False-acceptance proportion among ACCEPTs | 18.75% | 15.38% |
| ACCEPT coverage | 77.11% | 62.65% |
| TP / FP / FN / TN | 52 / 12 / 16 / 3 | 44 / 8 / 24 / 7 |

The hypothetical headline has 68 resolved and 15 unresolved patches; n and coverage stay unchanged. Both policies lose one TP and gain one FP. The corresponding all-non-empty hypothetical is also in the CSVs. No committed classification or run record was changed.

## Conservative assumptions, limitations and reproduction

- Full uses its observed committed decision. Where detailed risk findings are unavailable, policy implications are labeled as inference and never described as independently observed risk measurements.
- Empty means the committed empty_patch classification; no patch reconstruction or alternate-run substitution is used to redefine population membership.
- The exact enrichment comparison conditions on the overlapping baseline-accepted pool, rather than using an independence assumption. Its null is exchangeability of wrong labels within that pool.
- Bootstrap resamples patches without stratification and keeps pairing. Repositories are not independent clusters in this bootstrap; intervals are descriptive under this assumption.
- The local patch_apply_failed label is mapped to unresolved only in an explicitly hypothetical sensitivity. It does not override the committed oracle.

Run from the project root:

```bash
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/policy_comparison/test_comparison.py -q -p no:cacheprovider -o addopts=
env -u PYTHONPATH .venv/bin/python -B reports/policy_comparison/compare.py
```

Only the new synthetic analysis test file is collected. Tests cover the hand-computed requested confusion matrices, metrics, zero denominators, policy examples, a Wilson reference interval, exact tests, paired bootstrap known answers, transitions, populations, and CSV/report consistency. See tests.txt for results.

## Advisor-ready interpretation

1. Full has higher observed ACCEPT precision: 86.54% versus 82.81%.
2. Baseline has higher recall: 76.81% versus 65.22%.
3. Baseline has higher acceptance-oriented F1: 79.70% versus 74.38%.
4. Full reduces coverage from 64/83 to 52/83, a cost of 14.46 percentage points.
5. Full withholds 4 additional wrong patches.
6. It also withholds 8 additional correct patches.
7. These point estimates do not justify a universal winner; statistical significance of a reliability improvement is not established at this sample size.
8. The reliability question remains a false-acceptance versus automatic-coverage tradeoff. Full trades correct automatic repairs for fewer false ACCEPTs; F1 alone cannot choose that tradeoff, and four wrong patches withheld because V4 was unavailable are not four demonstrated V4 bug detections.
