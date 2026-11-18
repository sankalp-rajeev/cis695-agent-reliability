# Arm B rerun results

The gpt-4.1-mini repair agent produced 51 patches on 92 tasks. Of these patches, 25 resolved the task (49.0%). Under the live verifier accounting, 4 of 5 ACCEPTs were correct (80.0%, 95% CI 37.6–96.4%), and 21 of 25 correct patches were withheld. The primary data do not show separation beyond chance under A3's criterion.

## Primary results

The primary accounting is Policy S with `INVALID_ID` excluded. Across all 92 tasks the verifier recorded 5 ACCEPT, 42 FLAG, and 45 REJECT. The table covers the 51 patch tasks. The arm also had 40 no-patch tasks, 1 provider-blocked task, and 0 agent-infrastructure tasks. Withheld means FLAG or REJECT.

| Decision | Correct | Wrong | Total |
| --- | ---: | ---: | ---: |
| ACCEPT | 4 | 1 | 5 |
| FLAG | 21 | 21 | 42 |
| REJECT | 0 | 4 | 4 |
| **Total** | **25** | **26** | **51** |

| A3 metric | Fraction | Estimate | 95% interval |
| --- | ---: | ---: | ---: |
| 2. ACCEPT precision | 4/5 | 80.0% | 37.6–96.4% |
| 3. Base rate | 25/51 | 49.0% | 35.9–62.3% |
| 4. Wrong patches withheld | 25/26 | 96.2% | 81.1–99.3% |
| 4. All patches withheld | 46/51 | 90.2% | 79.0–95.7% |
| 4. Difference, wrong minus all | 25/26 − 46/51 | +6.0 pp | −10.1 to +17.6 pp |
| 5. Correct patches withheld | 21/25 | 84.0% | 65.3–93.6% |
| Supplementary difference d′, wrong minus correct | 25/26 − 21/25 | +12.2 pp | −5.7 to +31.1 pp |

Proportions use Wilson intervals. Differences use Newcombe method 10. The wrong-minus-all interval is approximate because the cohorts overlap. The two-sided Fisher exact test for correctness by ACCEPT status gave `p = 0.191`. [Checked metrics](metrics.csv)

## Wrong-patch types

| Graded type | Wrong patches | ACCEPT | FLAG | REJECT | Withheld, Wilson 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| R | 12 | 0 | 10 | 2 | 12/12, 100.0% (75.8–100.0%) |
| U | 11 | 1 | 10 | 0 | 10/11, 90.9% (62.3–98.4%) |
| X | 3 | 0 | 1 | 2 | 3/3, 100.0% (43.9–100.0%) |

All labels are as graded. The X notes draw on `reports/rerun_v1/arm_B/DECISIONS.md` at grading results head `9b07499`.

- `django__django-13023` submitted a malformed diff with a range-less hunk header. V1 marked it unparseable. The harness failed to apply it twice and recorded `infra_error`.
- `django__django-16667` submitted text without diff headers. V1 marked it unparseable. The harness failed to apply it twice and recorded `infra_error`.
- `django__django-14140` applied cleanly. Django then crashed on import with a `register_lookup` TypeError, so no tests ran and the harness reported `patch_apply_failed`. By mechanism, this is a patch that breaks all tests because the application cannot import.

## Signal attribution

The 21 correct and 25 wrong non-ACCEPT patches produced the following V1–V4 outcomes. Absence reasons are the recorded categories.

| Signal | Correct PASS / FAIL / absent | Correct absences | Wrong PASS / FAIL / absent | Wrong absences |
| --- | --- | --- | --- | --- |
| V1 | 21 / 0 / 0 | — | 23 / 2 / 0 | — |
| V2 | 1 / 1 / 19 | 16 incomplete, 2 nothing to check, 1 error | 3 / 8 / 14 | 6 incomplete, 3 nothing to check, 5 errors |
| V3 | 21 / 0 / 0 | — | 19 / 3 / 3 | 3 errors |
| V4 | 20 / 1 / 0 | — | 11 / 9 / 5 | 2 nothing to check, 3 errors |

| Recorded decision reason | Correct | Wrong |
| --- | ---: | ---: |
| V2 unavailable | 19 | 12 |
| V2 FAIL and V4 PASS disagree | 1 | 6 |
| V4 failed | 1 | 7 |
| V4 unavailable | 0 | 3 |
| Integrity check failed | 0 | 2 |
| Regression test failed | 0 | 2 |
| V3 absolute failure | 0 | 3 |

A task can have more than one reason. [Per-task attribution](signal_attribution.csv) · [Exact reason text and counts](reason_counts.csv)

## Sensitivities

| Sensitivity | Tasks | ACCEPT / FLAG / REJECT | ACCEPT precision, Wilson 95% CI | Base rate | Correct withheld | d′, 95% CI (pp) |
| --- | ---: | --- | --- | ---: | ---: | --- |
| (a) Count no-patch as wrong | 91 | 5 / 42 / 44 | 4/5, 80.0% (37.6–96.4%) | 27.5% | 84.0% | +14.5 (+2.8 to +33.2) |
| (b) Also count provider-blocked as no-patch | 92 | 5 / 42 / 45 | 4/5, 80.0% (37.6–96.4%) | 27.2% | 84.0% | +14.5 (+2.9 to +33.2) |
| (c) S, `INVALID_ID` as missing | 51 | 5 / 42 / 4 | 4/5, 80.0% (37.6–96.4%) | 49.0% | 84.0% | +12.2 (−5.7 to +31.1) |
| (c) C, `INVALID_ID` excluded | 51 | 20 / 27 / 4 | 16/20, 80.0% (58.4–91.9%) | 49.0% | 36.0% | +48.6 (+22.0 to +66.9) |
| (c) C, `INVALID_ID` as missing | 51 | 13 / 34 / 4 | 9/13, 69.2% (42.4–87.3%) | 49.0% | 64.0% | +20.6 (−3.4 to +42.2) |
| (d) Exclude T4 | 51 | 5 / 42 / 4 | 4/5, 80.0% (37.6–96.4%) | 49.0% | 84.0% | +12.2 (−5.7 to +31.1) |
| (e) Also exclude T3-name | 47 | 5 / 39 / 3 | 4/5, 80.0% (37.6–96.4%) | 48.9% | 82.6% | +13.2 (−5.9 to +33.3) |

Sensitivities (a), (b), and Policy C with `INVALID_ID` excluded meet A3's better-than-chance criterion. The complete tables cross all four accountings with all five cohorts. [Full results](results.md)

The audit found no T4 cases. It found T3-name evidence on 4 tasks, T3-content evidence on 30 tasks, and awareness evidence on 33 tasks. Sensitivity (e) excludes the four T3-name cases. [Audit counts](leakage_counts.csv)

## Exploratory findings

| Signal forced to PASS | ACCEPT / FLAG / REJECT | Correct ACCEPTs |
| --- | --- | ---: |
| V1 | 5 / 44 / 2 | 4 |
| V2 | 36 / 13 / 2 | 24 |
| V3 | 5 / 42 / 4 | 4 |
| V4 | 9 / 40 / 2 | 5 |

| Repository | Patch tasks | Correct | ACCEPT / FLAG / REJECT | Correct ACCEPTs |
| --- | ---: | ---: | --- | ---: |
| astropy | 4 | 1 | 1 / 3 / 0 | 0 |
| django | 19 | 8 | 2 / 14 / 3 | 2 |
| matplotlib | 12 | 6 | 0 / 11 / 1 | 0 |
| xarray | 1 | 0 | 0 / 1 / 0 | 0 |
| pylint | 2 | 1 | 0 / 2 / 0 | 0 |
| pytest | 5 | 5 | 0 / 5 / 0 | 0 |
| scikit-learn | 3 | 3 | 2 / 1 / 0 | 2 |
| sphinx | 3 | 0 | 0 / 3 / 0 | 0 |
| sympy | 2 | 1 | 0 / 2 / 0 | 0 |

Total ledger spend was $17.89 across both providers. The cost was $4.47 per correct ACCEPT, with median spend of $0.20 per completed task. [Cost table](exploratory_cost.csv)

## Deviations

1. **Stage 1 session-1 status exposure.** After A3 was drafted and before the analysis freeze, the first executing session ran the grading status command and saw a partial aggregate. That session stopped. The fresh session then froze the analysis code under the blinding conditions recorded in A3. The disclosure has SHA-256 `e8005aa5c76e3bd2133f8951752ae8779ad130242b451bd985ec8170f34f9594`. [Session-1 disclosure](armB_stage1_session1.md)
2. **Audit discovery fix, label-free and before unblinding.** Commit `073294a` added the explicit sealed V4 trajectory layout. Coverage rose from 91 repair plus 0 V4 trajectories to 91 repair plus 51 V4, matching the seal manifest. [Audit decision log](DECISIONS.md)
3. **Grading adapter fix, after unblinding.** Commit `8b864b4` affected only `pylint-dev__pylint-8898`, whose sealed patch is empty. A sealed absence record allowed the grader to use the existing empty-patch rule. The grading branch records all other task outcomes as before.

## Limits

The ACCEPT denominator was five. Its 95% precision interval spans 58.8 percentage points, from 37.6% to 96.4%. The primary wrong-minus-correct interval also includes zero.

## Input and checker

The labels and summary came from grading commit `bf832e9` and are byte-identical at results head `9b07499`. The grading verifier passed. The frozen analysis ran once, and the independent checker found zero mismatches across 13 CSVs, 5,107 rows, and `counts.json`. [Input provenance](input_provenance.json) · [Checker receipt](checker_receipt.json)
