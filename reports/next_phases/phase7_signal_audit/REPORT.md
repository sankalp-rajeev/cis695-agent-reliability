# Signal audit: attempt 2

Completed on branch `analysis/signal-audit`. All reported counts and tables passed the separate standard-library verifier: 25 CSV tables, eight JSON artifacts, 14 V1 reruns, zero mismatches. There are 83 frozen tasks, zero missing records, and 100 distinct selected tasks across 105 physical records; five superseded copies are replaced by the directory rule.

Attempt 1 was aborted after label exposure; this attempt used a fresh session and a file whitelist. The annotated `signal-audit-labelfree` tag at `d2cc07ab1036bf5a36225fcf8acf2698b5b6e8c4` was pushed before any task-label source was opened; Stage 5 is post-hoc, never used for any decision.

The first independent verification run mismatched because of a bug in the verification script itself: it passed a list where the analysis passed a tuple, changing raw diagnostic text. The one-line runtime correction was committed separately in `cf58a54`; the pre-rerun argument review also corrected the expected case-spec constructor to use the JSON array actually stored by the producer (`770a717`). No comparison was loosened and no field was excluded. The corrected full rerun passed, including exact raw V1 diagnostic equality. All 65 Stage 1–5 artifacts, including every CSV and result file, remained byte-identical to pre-fix commit `5fae0db`; the failed run remains preserved in [independent_verification.json](independent_verification.json), alongside [its evidence](stage6_mismatch_evidence.json). See [successful rerun](independent_verification_rerun.json) and [before/after hashes](analysis_outputs_unchanged.json).

## V1

V1 caught most tested violations but missed semantic assertion weakening. Changing a pre-existing assertion to `assert True` passed V1.

The suite met 13/14 expectations: 10/11 rejection probes caught and 3/3 controls passed. The clean control was the smallest candidate with stored V1 PASS: `scikit-learn__scikit-learn-14141`, 348 bytes, selected without correctness information. The two breadth/directory risk controls both passed. [Cases and evidence](v1_adversarial.csv).

Limits: the suite uses three pristine members of one real task source archive and synthetic diffs; it does not establish completeness across all repositories or patch shapes. No verifier code was changed.

## V3

V3 never drove a decision under the stored `v1.3.0-full` policy. Two frozen tasks have V3 FAIL alongside ACCEPT: `matplotlib__matplotlib-23299` and `pallets__flask-5014`.

| Check | Frozen 83: PASS / FAIL / NOT_AVAILABLE | All 100: PASS / FAIL / NOT_AVAILABLE |
|---|---:|---:|
| syntax | 83 / 0 / 0 | 89 / 0 / 11 |
| import | 81 / 2 / 0 | 87 / 2 / 11 |
| build | 0 / 1 / 82 | 0 / 1 / 99 |
| lint | 19 / 1 / 63 | 19 / 1 / 80 |
| typecheck | 7 / 0 / 76 | 7 / 0 / 93 |

The unchanged policy ignores its static field; setting it separately to PASS, FAIL, and NOT_AVAILABLE changed zero decisions in either cohort. [Per-repository counts and recorded absence reasons](v3_outcomes.csv); [task counterfactuals](v3_decision_effects.csv).

Limits: these are stored check outcomes, not fresh static-tool executions. Missing per-check records retain their recorded aggregate reason and count as unavailable.

## V4

The recorded unavailable signals are accounted for without guessing. The frozen cohort has 14 generator no-output cases; none records another absence class.

| Outcome or absence class | Frozen 83 | All 100 |
|---|---:|---:|
| PASS | 68 | 72 |
| FAIL | 1 | 1 |
| NOT_AVAILABLE | 14 | 27 |
| NA: UNKNOWN | 0 | 0 |
| NA: environment or network | 0 | 0 |
| NA: execution error or timeout | 0 | 0 |
| NA: generator produced no usable test | 14 | 16 |
| NA: other | 0 | 11 |
| NA: output parsing problem | 0 | 0 |
| NA: test did not fail on the unpatched tree (filtered out) | 0 | 0 |
| NA: test unstable across repeats | 0 | 0 |

The 16 all-task no-output cases explicitly report `LimitsExceeded`; the 11 other cases explicitly say the patch is empty. The only V4 FAIL is `django__django-10973`: one of three stable generated tests still fails because the subprocess environment does not inherit `os.environ`. [Classification evidence](v4_not_available_breakdown.csv), [failure](v4_failures.csv), [excerpts](v4_excerpts.md).

Limits: no-output is generator-side under the recorded budget; the record does not identify which cap fired or prove permanent inability. Empty-patch skip accounting is a tooling issue. Raw generator stdout is NOT_AVAILABLE, so recorded-detail excerpts are supplied separately; generated tests were not rerun.

## Recompute

Only V2 was replaced; V1, V3, V4 and stored integrity flags were retained. Under the predeclared conservative `S_invalid_missing` accounting, ACCEPT/FLAG/REJECT changes from 52/30/1 to 13/68/2.

| Accounting | ACCEPT | FLAG | REJECT |
|---|---:|---:|---:|
| original | 52 | 30 | 1 |
| C_invalid_excluded | 41 | 40 | 2 |
| C_invalid_missing | 32 | 49 | 2 |
| S_invalid_excluded | 14 | 67 | 2 |
| S_invalid_missing (primary) | 13 | 68 | 2 |

The outcome mapping was committed before applying it: PASS→PASS; FAIL and REGRESSION_ERROR→FAIL; INCOMPLETE and NOT_AVAILABLE→NOT_AVAILABLE. Zero statuses were unmapped. The primary has 44 changed decisions. FLAG with regression NOT_AVAILABLE increases from 13 to 57; FLAG solely caused by that absence, measured by changing only V2 to PASS, increases from 10 to 49. [All 83 decisions](recompute_decisions.csv), [every transition](transitions.csv), [all accounting variants](recompute_sensitivity.csv).

Limits: strict completeness with invalid IDs retained as missing was chosen under the conservative-default instruction before labels; other accounting variants remain explicit. These are inherited Phase 4 outcomes and unchanged-policy recomputations, not new regression runs or changes to verifier policy.

## Post-hoc labels

Six of the seven original false accepts survive default auditing; five survive CPU-2048 sensitivity. One newly incorrect original ACCEPT offsets the removed default false accept, so the total under original decisions remains seven.

| Decisions | Label set | Correct / accepted | False accepts | Precision, Wilson 95% CI |
|---|---|---:|---:|---|
| original | original | 45/52 | 7 | 86.54% (74.73–93.32%) |
| original | audited_default | 45/52 | 7 | 86.54% (74.73–93.32%) |
| original | CPU_2048 | 46/52 | 6 | 88.46% (77.03–94.60%) |
| recomputed | original | 10/13 | 3 | 76.92% (49.74–91.82%) |
| recomputed | audited_default | 10/13 | 3 | 76.92% (49.74–91.82%) |
| recomputed | CPU_2048 | 11/13 | 2 | 84.62% (57.77–95.67%) |

Coverage is unchanged across label sets: original 52/83 = 62.65% (51.90–72.28%); recomputed 13/83 = 15.66% (9.39–24.98%). Every false accept in all six cases, with label-audit and available grader-gap classifications, is listed in [false_accepts.csv](posthoc_labels/false_accepts.csv).

All 83 stored agent claims are RESOLVED. Their precision is:

| Labels | Correct / claims | Precision, Wilson 95% CI |
|---|---:|---|
| original | 69/83 | 83.13% (73.66–89.68%) |
| audited_default | 70/83 | 84.34% (75.02–90.61%) |
| CPU_2048 | 72/83 | 86.75% (77.81–92.44%) |

Default labels change three tasks: `astropy__astropy-13977` and `django__django-13297` become correct; `pydata__xarray-6599` becomes incorrect. CPU sensitivity additionally makes `pylint-dev__pylint-6528` and `pylint-dev__pylint-7277` correct. The django-13297 and xarray-6599 changes add and remove one original correct ACCEPT respectively; the CPU change to pylint-7277 adds one correct ACCEPT under both decision sets. Other changes affect neither accepted numerator; all coverage deltas are zero. [Task-level effects](posthoc_labels/changed_labels.csv).

Limits: labels and gap classifications are inherited from the existing audit, not regraded here. Original oracle flags and recorded candidate hashes were cross-checked; absent grader-gap entries remain NOT_AVAILABLE. CPU-2048 is a sensitivity label set, not a replacement for the default audit.

## Findings that need a decision

- **V1 assertion weakening:** `assertion_loosened` applies cleanly and returns PASS. Consider flagging semantic edits to existing assertions or adding conservative AST checks, with adversarial tests. Evidence: [fixture](v1_fixtures/assertion_loosened.patch) and [observations](v1_raw_observations.json).

- **V3 combining-policy gap:** two recorded V3 FAILs coexist with ACCEPT because `FullPolicy` ignores static. Decide whether FAIL should block acceptance and version any policy change. Evidence: [V3 failures](v3_failures.csv) and [decision counterfactuals](v3_decision_effects.csv).

- **V4 evidence retention:** fourteen frozen tasks have no generated tests and only `LimitsExceeded` as the recorded termination reason. Consider retaining the exact cap and sanitized generator stdout; a parser cannot recover absent tests. Evidence: [absence breakdown](v4_not_available_breakdown.csv).

- **Repaired V2 accounting:** ACCEPT ranges from 13 to 41 across the four sealed Phase 4 variants. Decide which accounting variant to adopt for future reporting; this report keeps the predeclared conservative primary and all sensitivities. Evidence: [policy totals](recompute_policy_totals.csv).

No suggested verifier, policy, configuration, or frozen-artifact change was applied. The audit-script representation corrections and preserved first-run failure are documented above and in [DECISIONS.md](DECISIONS.md). The final annotated tag `signal-audit-sealed` binds this report, its receipts and SHA-256 manifest.
