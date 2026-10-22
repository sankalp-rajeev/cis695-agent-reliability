# Current V2 stored-artifact diagnostic

POST-HOC ANALYSIS ONLY. Never feed these comparisons into selection or decisions.

No selection, verification, repair, oracle evaluation, Docker, or network was run.

Reproduce from repository root:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/v2_diagnostic/oracle_posthoc.py --dataset-arrow /home/rajee/.cache/huggingface/datasets/SWE-bench___swe-bench_verified/default/0.0.0/78f471bf655a3137b2e8a75af1501690ec009ec3/swe-bench_verified-test.arrow --sample
```

## Population and evidence

3 non-empty headline patches. Committed oracle classifications: {'unresolved': 2, 'resolved': 1}.
Committed decisions and V2 outcomes always come from docs/results_100.csv.
Artifact origins: {'study_snapshot': 2, 'local_record_final_identity_unverified': 1}.
Study snapshots take precedence over local records. Local-only records are reported separately as final identity unverified; matching aggregate labels do not prove they are the final study run. Only the study-snapshot cohort supplies confirmed detailed main-study evidence. Other local evidence is exploratory. No pilot or alternate-run substitution.

## V2 baseline (all included committed rows)

| V2 | Tasks |
|---|---:|
| PASS | 3 |

## Available-artifact distributions

These are availability-limited, failure-enriched subsets, not unbiased 83-task estimates. Quantiles use linear interpolation. Averages of task ratios are distinct from pooled execution coverage. Zero selections give undefined ratios.
Counts follow existing Outcome.executed: ERROR and PRE_EXISTING_FAIL count as executed, TIMEOUT and NOT_RUN do not. Runtime is stored V2 duration, which may include baseline/cache work and flake reruns.

| Cohort | Metric | Available / tasks | Missing | Min | P25 | Median | P75 | P90 | Max | Mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| study snapshots only | total_selected_tests | 2/2 | 0 | 1383 | 3076.0000 | 4769.0000 | 6462.0000 | 7477.8000 | 8155 | 4769 |
| study snapshots only | number_executed | 2/2 | 0 | 1137 | 1169.0000 | 1201.0000 | 1233.0000 | 1252.2000 | 1265 | 1201 |
| study snapshots only | timeout_fraction | 2/2 | 0 | 0.0000 | 0.2112 | 0.4224 | 0.6337 | 0.7604 | 0.8449 | 0.4224 |
| study snapshots only | execution_coverage | 2/2 | 0 | 0.1551 | 0.3219 | 0.4886 | 0.6554 | 0.7554 | 0.8221 | 0.4886 |
| study snapshots only | v2_runtime_s | 2/2 | 0 | 82.1230 | 207.8791 | 333.6353 | 459.3915 | 534.8452 | 585.1477 | 333.6353 |
| all available (exploratory) | total_selected_tests | 3/3 | 0 | 342 | 862.5000 | 1383 | 4769.0000 | 6800.6000 | 8155 | 3293.3333 |
| all available (exploratory) | number_executed | 3/3 | 0 | 154 | 645.5000 | 1137 | 1201.0000 | 1239.4000 | 1265 | 852 |
| all available (exploratory) | timeout_fraction | 3/3 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.4224 | 0.6759 | 0.8449 | 0.2816 |
| all available (exploratory) | execution_coverage | 3/3 | 0 | 0.1551 | 0.3027 | 0.4503 | 0.6362 | 0.7478 | 0.8221 | 0.4758 |
| all available (exploratory) | v2_runtime_s | 3/3 | 0 | 82.1230 | 108.0904 | 134.0578 | 359.6027 | 494.9297 | 585.1477 | 267.1095 |

Confirmed study snapshots paired totals: 9538 selected, 2402 executed; pooled coverage 0.2518.

All available (exploratory) paired totals: 9880 selected, 2556 executed; pooled coverage 0.2587.

## Pathological cases

Descriptive thresholds: selected ≥1,000 or TIMEOUT/selected >0.5. These labels do not alter selection or policy.

| Instance | Origin | Selected | Executed | TIMEOUT | Timeout fraction | Coverage |
|---|---|---:|---:|---:|---:|---:|
| django__django-13212 | study_snapshot | 1383 | 1137 | 0 | 0.0000 | 0.8221 |
| django__django-13297 | study_snapshot | 8155 | 1265 | 6890 | 0.8449 | 0.1551 |

## By repository

Counts cover the committed population; exploratory averages cover available artifacts (including unverified local-only records) only. Missing evidence is never counted as zero.

| Repository | Tasks | PASS / FAIL / NA | Detailed records | Mean selected | Mean executed | Mean timeout fraction | Mean coverage | Mean V2 seconds |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| django/django | 2 | 2 / 0 / 0 | 2/2 | 4769 | 1201 | 0.4224 | 0.4886 | 333.6353 |
| pytest-dev/pytest | 1 | 1 / 0 / 0 | 1/1 | 342 | 154 | 0.0000 | 0.4503 | 134.0578 |

## POST-HOC ORACLE-ONLY: selection overlap

POST-HOC ANALYSIS ONLY. Never feed these comparisons into selection or decisions.

Matching: exact node identity; deterministic Django node-to-dotted and unittest label normalization (including redundant method suffix); explicit parameterized case → selected function-family matching. Bare names resolve only to a unique exact function identity in the stored gold diff. No fuzzy, substring, or generic tail matching. Django docstring-style names remain unresolved, not guessed. A hit can identify the old function even when the official body was rewritten.

| Cohort | Official group | Applicable nonempty lists + stored selection | Positive tasks | No exact-ID hit | Unresolved tasks | Missing selection/list |
|---|---|---:|---:|---:|---:|---:|
| confirmed study snapshots | F2P | 2 | 0 | 2 | 0 | 0 |
| confirmed study snapshots | P2P | 2 | 2 | 0 | 0 | 0 |
| all available (exploratory) | F2P | 3 | 0 | 3 | 0 | 0 |
| all available (exploratory) | P2P | 3 | 2 | 1 | 0 | 0 |

Unmatched official IDs and their matching methods/reasons are fully listed in `sample_oracle_test_matches.csv` (including matched rows) and per-task JSON arrays in `sample_patches.csv`. Missing selection is unknown, not a failed match. An empty official list is not applicable. Positive counts are demonstrable lower bounds; a no-exact-ID hit is not proof that a renamed pre-existing counterpart was absent. Such mappings cannot be invented from name similarity. These are post-hoc coverage observations, not a selector or a proposed test set.

## POST-HOC ORACLE-ONLY: known wrong patches

Relevant test means an official FAIL_TO_PASS test the patch fails, from the stored oracle record. P2P-only failures are explicitly not applicable here. Added/rewritten means the official test version did not exist at base; an older function may still have been selected. Categories are per test and need not be mutually exclusive per task.
Per-test execution outcomes are absent in current records. Partial timeout totals cannot identify which test timed out. Pre-existing-failure totals likewise cannot identify a particular test. Such cases remain missing, never guessed.

| Wrong patch | Decision / V2 | Failed F2P count | Matched failed F2P IDs | Observed regressions | Categories |
|---|---|---:|---:|---:|---|
| django__django-13212 | ACCEPT / PASS | 2 | 0 | 0 | relevant test did not exist at base (added or rewritten by gold test patch): 2 |
| django__django-13297 | ACCEPT / PASS | 0 | 0 | 0 | not applicable: oracle records no failed FAIL_TO_PASS tests: 1 |

Category task counts: {'not applicable: oracle records no failed FAIL_TO_PASS tests': 1, 'relevant test did not exist at base (added or rewritten by gold test patch)': 1}.
Detailed identities, normalization methods and provenance are in `sample_wrong_patch_tests.csv`. matplotlib-25479 is the one wrong patch with V2 FAIL and one observed regression: detection at patch level is recorded, but the missing per-test outcomes prevent attributing that regression to a particular failed F2P test.

## Missing evidence, assumptions, and discrepancies

- Tier 1/Tier 2 membership exists in Selection.by_tier at runtime but is not serialized by VerificationRecord. Both requested tier counts remain blank. The recorded union/order cannot reconstruct overlapping tier memberships.
- Candidate Python source files and symbols are derived using the existing parse_patch/touched_symbols and selector source-file definition. These are diff-derived names, not a call graph or a complete semantic change inventory.
- Every main CSV value has `_status` (recorded/inferred/missing) and `_source`. Sparse histogram keys become inferred zero only if the histogram covers the entire selected union; missing records remain blank.
- Full selected-ID unions remain in the hashed input records rather than being duplicated as enormous CSV cells. Matched IDs are in the oracle-only detail CSV; every unmatched official ID is listed there as well.
- No base-tree discovery or test execution is repeated. Existing Group 4 rerun outputs were inspected but are not substituted for main-study evidence.
- The extracted snapshot covers 19 deliberately chosen failure-analysis cases. The cached Arrow benchmark supplies only post-hoc official lists and gold diffs; it supplies no missing selection or execution evidence. The input manifest records code and input paths and SHA-256 hashes; no dataset loader/download is invoked.

| Field | Recorded | Inferred | Missing |
|---|---:|---:|---:|
| changed_source_files | 0 | 3 | 0 |
| changed_symbols | 0 | 3 | 0 |
| test_layout_convention | 3 | 0 | 0 |
| tier1_selected_count | 0 | 0 | 3 |
| tier2_selected_count | 0 | 0 | 3 |
| total_selected_tests | 0 | 3 | 0 |
| number_executed | 3 | 0 | 0 |
| number_timed_out | 1 | 2 | 0 |
| number_pre_existing_failures | 1 | 2 | 0 |
| number_observed_regressions | 0 | 3 | 0 |
| v2_runtime_s | 3 | 0 | 0 |
| per_test_outcomes | 0 | 0 | 3 |

- pytest-7432: committed=resolved; local=patch_apply_failed; committed classification retained. Local harness says applied cleanly; test output records segfault/139.
- django-13297: the failed-F2P set is empty (its oracle failure is P2P). Its 6,890/8,155 timeouts establish partial V2 evidence, not the individual warning test's execution status. PASS requires some execution and zero observed regressions (VERIFIER_POLICY.md §4), not full selection completion.
- pylint-7277: aggregate PRE_EXISTING_FAIL does not prove the outcome of test_jobs_score. The earlier narrative's likely explanation is not promoted to data.
- django-12209: the official F2P string is a functools.partial docstring, not a resolvable test identity. It stays unmatched.
- A gold diff may omit the enclosing test class. Exact file/function evidence with missing class scope is reported unresolved rather than guessed or called a selection failure. Renamed tests and docstring-only IDs without an exact stored identity mapping are likewise unresolved; no fuzzy correspondence is used.
