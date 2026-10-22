# Current V2 stored-artifact diagnostic

POST-HOC ANALYSIS ONLY. Never feed these comparisons into selection or decisions.

No selection, verification, repair, oracle evaluation, Docker, or network was run.

Reproduce from repository root:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/v2_diagnostic/oracle_posthoc.py --dataset-arrow /home/rajee/.cache/huggingface/datasets/SWE-bench___swe-bench_verified/default/0.0.0/78f471bf655a3137b2e8a75af1501690ec009ec3/swe-bench_verified-test.arrow
```

## Population and evidence

83 non-empty headline patches. Committed oracle classifications: {'resolved': 69, 'unresolved': 14}.
Committed decisions and V2 outcomes always come from docs/results_100.csv.
Artifact origins: {'committed_table_only': 59, 'study_snapshot': 19, 'local_record_final_identity_unverified': 5}.
Study snapshots take precedence over local records. Local-only records are reported separately as final identity unverified; matching aggregate labels do not prove they are the final study run. Only the study-snapshot cohort supplies confirmed detailed main-study evidence. Other local evidence is exploratory. No pilot or alternate-run substitution.

## V2 baseline (all included committed rows)

| V2 | Tasks |
|---|---:|
| FAIL | 6 |
| NOT_AVAILABLE | 13 |
| PASS | 64 |

## Available-artifact distributions

These are availability-limited, failure-enriched subsets, not unbiased 83-task estimates. Quantiles use linear interpolation. Averages of task ratios are distinct from pooled execution coverage. Zero selections give undefined ratios.
Counts follow existing Outcome.executed: ERROR and PRE_EXISTING_FAIL count as executed, TIMEOUT and NOT_RUN do not. Runtime is stored V2 duration, which may include baseline/cache work and flake reruns.

| Cohort | Metric | Available / tasks | Missing | Min | P25 | Median | P75 | P90 | Max | Mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| study snapshots only | total_selected_tests | 19/19 | 0 | 4 | 79.0000 | 272 | 1858.5000 | 3549.0000 | 8155 | 1348.3158 |
| study snapshots only | number_executed | 19/19 | 0 | 0 | 47.0000 | 191 | 758.5000 | 2000.0000 | 2929 | 615.5263 |
| study snapshots only | timeout_fraction | 19/19 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1690 | 1.0000 | 0.0971 |
| study snapshots only | execution_coverage | 19/19 | 0 | 0.0000 | 0.5366 | 0.7699 | 0.8793 | 0.9058 | 1.0000 | 0.6474 |
| study snapshots only | v2_runtime_s | 19/19 | 0 | 0.9433 | 18.0537 | 52.0113 | 260.7686 | 420.4878 | 601.3547 | 152.7813 |
| all available (exploratory) | total_selected_tests | 24/83 | 59 | 4 | 83.5000 | 274.5000 | 897.7500 | 3247.9000 | 8155 | 1115.5833 |
| all available (exploratory) | number_executed | 24/83 | 59 | 0 | 52.0000 | 189.0000 | 350.0000 | 1637.4000 | 2929 | 522.1250 |
| all available (exploratory) | timeout_fraction | 24/83 | 59 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0769 |
| all available (exploratory) | execution_coverage | 24/83 | 59 | 0.0000 | 0.5413 | 0.8061 | 0.8835 | 0.9061 | 1.0000 | 0.6745 |
| all available (exploratory) | v2_runtime_s | 24/83 | 59 | 0.9433 | 16.5422 | 53.6494 | 167.9309 | 349.7528 | 601.3547 | 134.8936 |

Confirmed study snapshots paired totals: 25618 selected, 11695 executed; pooled coverage 0.4565.

All available (exploratory) paired totals: 26774 selected, 12531 executed; pooled coverage 0.4680.

## Pathological cases

Descriptive thresholds: selected ≥1,000 or TIMEOUT/selected >0.5. These labels do not alter selection or policy.

| Instance | Origin | Selected | Executed | TIMEOUT | Timeout fraction | Coverage |
|---|---|---:|---:|---:|---:|---:|
| django__django-13212 | study_snapshot | 1383 | 1137 | 0 | 0.0000 | 0.8221 |
| astropy__astropy-13977 | study_snapshot | 3082 | 0 | 3082 | 1.0000 | 0.0000 |
| django__django-12209 | study_snapshot | 3319 | 2929 | 0 | 0.0000 | 0.8825 |
| django__django-13297 | study_snapshot | 8155 | 1265 | 6890 | 0.8449 | 0.1551 |
| django__django-14140 | study_snapshot | 2334 | 1797 | 0 | 0.0000 | 0.7699 |
| django__django-14631 | study_snapshot | 4469 | 2812 | 0 | 0.0000 | 0.6292 |

## By repository

Counts cover the committed population; exploratory averages cover available artifacts (including unverified local-only records) only. Missing evidence is never counted as zero.

| Repository | Tasks | PASS / FAIL / NA | Detailed records | Mean selected | Mean executed | Mean timeout fraction | Mean coverage | Mean V2 seconds |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| astropy/astropy | 4 | 1 / 0 / 3 | 1/4 | 3082 | 0 | 1.0000 | 0.0000 | 601.3547 |
| django/django | 31 | 28 / 3 / 0 | 7/31 | 2915.7143 | 1483.4286 | 0.1207 | 0.6417 | 191.1708 |
| matplotlib/matplotlib | 15 | 11 / 1 / 3 | 4/15 | 391.5000 | 208.7500 | 0.0000 | 0.6747 | 174.0466 |
| mwaskom/seaborn | 1 | 1 / 0 / 0 | 1/1 | 150 | 134 | 0.0000 | 0.8933 | 52.0113 |
| pallets/flask | 1 | 1 / 0 / 0 | 1/1 | 208 | 187 | 0.0000 | 0.8990 | 12.0685 |
| pydata/xarray | 5 | 4 / 0 / 1 | 3/5 | 202 | 165 | 0.0000 | 0.8455 | 62.8253 |
| pylint-dev/pylint | 5 | 4 / 0 / 1 | 3/5 | 97.3333 | 84 | 0.0000 | 0.8968 | 62.0923 |
| pytest-dev/pytest | 7 | 6 / 1 / 0 | 2/7 | 174.5000 | 79 | 0.0000 | 0.5109 | 69.6042 |
| scikit-learn/scikit-learn | 5 | 5 / 0 / 0 | 0/5 | — | — | — | — | — |
| sphinx-doc/sphinx | 4 | 3 / 1 / 0 | 1/4 | 90 | 86 | 0.0000 | 0.9556 | 22.7263 |
| sympy/sympy | 5 | 0 / 0 / 5 | 1/5 | 21 | 0 | 0.0000 | 0.0000 | 0.9433 |

## POST-HOC ORACLE-ONLY: selection overlap

POST-HOC ANALYSIS ONLY. Never feed these comparisons into selection or decisions.

Matching: exact node identity; deterministic Django node-to-dotted and unittest label normalization (including redundant method suffix); explicit parameterized case → selected function-family matching. Bare names resolve only to a unique exact function identity in the stored gold diff. No fuzzy, substring, or generic tail matching. Django docstring-style names remain unresolved, not guessed. A hit can identify the old function even when the official body was rewritten.

| Cohort | Official group | Applicable nonempty lists + stored selection | Positive tasks | No exact-ID hit | Unresolved tasks | Missing selection/list |
|---|---|---:|---:|---:|---:|---:|
| confirmed study snapshots | F2P | 19 | 6 | 11 | 2 | 0 |
| confirmed study snapshots | P2P | 17 | 15 | 1 | 1 | 0 |
| all available (exploratory) | F2P | 24 | 7 | 15 | 2 | 59 |
| all available (exploratory) | P2P | 22 | 19 | 2 | 1 | 59 |

Unmatched official IDs and their matching methods/reasons are fully listed in `oracle_test_matches.csv` (including matched rows) and per-task JSON arrays in `patches.csv`. Missing selection is unknown, not a failed match. An empty official list is not applicable. Positive counts are demonstrable lower bounds; a no-exact-ID hit is not proof that a renamed pre-existing counterpart was absent. Such mappings cannot be invented from name similarity. These are post-hoc coverage observations, not a selector or a proposed test set.

## POST-HOC ORACLE-ONLY: known wrong patches

Relevant test means an official FAIL_TO_PASS test the patch fails, from the stored oracle record. P2P-only failures are explicitly not applicable here. Added/rewritten means the official test version did not exist at base; an older function may still have been selected. Categories are per test and need not be mutually exclusive per task.
Per-test execution outcomes are absent in current records. Partial timeout totals cannot identify which test timed out. Pre-existing-failure totals likewise cannot identify a particular test. Such cases remain missing, never guessed.

| Wrong patch | Decision / V2 | Failed F2P count | Matched failed F2P IDs | Observed regressions | Categories |
|---|---|---:|---:|---:|---|
| django__django-13212 | ACCEPT / PASS | 2 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 2 |
| django__django-16667 | ACCEPT / PASS | 1 | 1 | 0 | gold class scope unresolved: not attributed to selection failure: 1 |
| matplotlib__matplotlib-20676 | FLAG / PASS | 2 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 2 |
| pylint-dev__pylint-6528 | FLAG / PASS | 0 | 0 | 0 | not applicable: oracle records no failed FAIL_TO_PASS tests: 1 |
| pylint-dev__pylint-7277 | ACCEPT / PASS | 0 | 0 | 0 | not applicable: oracle records no failed FAIL_TO_PASS tests: 1 |
| astropy__astropy-13977 | FLAG / NOT_AVAILABLE | 8 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 8 |
| django__django-13297 | ACCEPT / PASS | 0 | 0 | 0 | not applicable: oracle records no failed FAIL_TO_PASS tests: 1 |
| django__django-16631 | FLAG / PASS | 1 | 0 | 0 | gold class scope unresolved: not attributed to selection failure: 1 |
| matplotlib__matplotlib-23299 | ACCEPT / PASS | 1 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 1 |
| matplotlib__matplotlib-23476 | ACCEPT / PASS | 1 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 1 |
| matplotlib__matplotlib-25479 | REJECT / FAIL | 2 | 1 | 1 | relevant test did not exist at base (added or rewritten by gold test patch): 2 |
| mwaskom__seaborn-3069 | FLAG / PASS | 1 | 0 | 0 | gold class scope unresolved: not attributed to selection failure: 1 |
| pylint-dev__pylint-4661 | ACCEPT / PASS | 1 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 1 |
| sympy__sympy-17318 | FLAG / NOT_AVAILABLE | 1 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 1 |

Category task counts: {'gold class scope unresolved: not attributed to selection failure': 3, 'not applicable: oracle records no failed FAIL_TO_PASS tests': 3, 'relevant test did not exist at base (added or rewritten by gold test patch)': 8}.
Detailed identities, normalization methods and provenance are in `wrong_patch_tests.csv`. matplotlib-25479 is the one wrong patch with V2 FAIL and one observed regression: detection at patch level is recorded, but the missing per-test outcomes prevent attributing that regression to a particular failed F2P test.

## Missing evidence, assumptions, and discrepancies

- Tier 1/Tier 2 membership exists in Selection.by_tier at runtime but is not serialized by VerificationRecord. Both requested tier counts remain blank. The recorded union/order cannot reconstruct overlapping tier memberships.
- Candidate Python source files and symbols are derived using the existing parse_patch/touched_symbols and selector source-file definition. These are diff-derived names, not a call graph or a complete semantic change inventory.
- Every main CSV value has `_status` (recorded/inferred/missing) and `_source`. Sparse histogram keys become inferred zero only if the histogram covers the entire selected union; missing records remain blank.
- Full selected-ID unions remain in the hashed input records rather than being duplicated as enormous CSV cells. Matched IDs are in the oracle-only detail CSV; every unmatched official ID is listed there as well.
- No base-tree discovery or test execution is repeated. Existing Group 4 rerun outputs were inspected but are not substituted for main-study evidence.
- The extracted snapshot covers 19 deliberately chosen failure-analysis cases. The cached Arrow benchmark supplies only post-hoc official lists and gold diffs; it supplies no missing selection or execution evidence. The input manifest records code and input paths and SHA-256 hashes; no dataset loader/download is invoked.

| Field | Recorded | Inferred | Missing |
|---|---:|---:|---:|
| changed_source_files | 0 | 24 | 59 |
| changed_symbols | 0 | 24 | 59 |
| test_layout_convention | 24 | 0 | 59 |
| tier1_selected_count | 0 | 0 | 83 |
| tier2_selected_count | 0 | 0 | 83 |
| total_selected_tests | 0 | 24 | 59 |
| number_executed | 24 | 0 | 59 |
| number_timed_out | 2 | 22 | 59 |
| number_pre_existing_failures | 11 | 13 | 59 |
| number_observed_regressions | 6 | 18 | 59 |
| v2_runtime_s | 24 | 0 | 59 |
| per_test_outcomes | 0 | 0 | 83 |

- pytest-7432: committed=resolved; local=patch_apply_failed; committed classification retained. Local harness says applied cleanly; test output records segfault/139.
- django-13297: the failed-F2P set is empty (its oracle failure is P2P). Its 6,890/8,155 timeouts establish partial V2 evidence, not the individual warning test's execution status. PASS requires some execution and zero observed regressions (VERIFIER_POLICY.md §4), not full selection completion.
- pylint-7277: aggregate PRE_EXISTING_FAIL does not prove the outcome of test_jobs_score. The earlier narrative's likely explanation is not promoted to data.
- django-12209: the official F2P string is a functools.partial docstring, not a resolvable test identity. It stays unmatched.
- A gold diff may omit the enclosing test class. Exact file/function evidence with missing class scope is reported unresolved rather than guessed or called a selection failure. Renamed tests and docstring-only IDs without an exact stored identity mapping are likewise unresolved; no fuzzy correspondence is used.
