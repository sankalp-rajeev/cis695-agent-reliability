# Phase 4 post-hoc analysis

Analysis follows the immutable `phase4-run-sealed` tag at `e40d60afac6534bba03a20168ea681fca24228af`. Labels: `/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/correctness_sidecar.json`, SHA-256 `cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990`; 69 correct and 14 incorrect, each bound to the manifested candidate patch hash.

## Verdict by correctness label

| Policy | Verdict | Correct | Incorrect |
|---|---|---:|---:|
| C_invalid_excluded | PASS | 43 | 9 |
| C_invalid_excluded | FAIL | 5 | 1 |
| C_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| C_invalid_excluded | INCOMPLETE | 15 | 4 |
| C_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| C_invalid_missing | PASS | 33 | 9 |
| C_invalid_missing | FAIL | 5 | 1 |
| C_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| C_invalid_missing | INCOMPLETE | 25 | 4 |
| C_invalid_missing | NOT_AVAILABLE | 5 | 0 |
| S_invalid_excluded | PASS | 14 | 6 |
| S_invalid_excluded | FAIL | 5 | 1 |
| S_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| S_invalid_excluded | INCOMPLETE | 44 | 7 |
| S_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| S_invalid_missing | PASS | 13 | 6 |
| S_invalid_missing | FAIL | 5 | 1 |
| S_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| S_invalid_missing | INCOMPLETE | 45 | 7 |
| S_invalid_missing | NOT_AVAILABLE | 5 | 0 |

## Detection, false alarms and missed incorrect PASS

All intervals below are exact two-sided 95% Clopper-Pearson. Primary positive = FAIL; secondary positive = FAIL or REGRESSION_ERROR. The conditional denominator is PASS+FAIL for primary, and PASS+FAIL+REGRESSION_ERROR for secondary. No verdict is reclassified.

| Policy | Rule | Detection /14 | Detection among verdicted incorrect | False alarms /69 | False alarms among verdicted correct | Missed PASS /14 | Missed among verdicted incorrect |
|---|---|---|---|---|---|---|---|
| C_invalid_excluded | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/48 = 10.42% [3.47%, 22.66%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/49 = 12.24% [4.63%, 24.77%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_missing | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/38 = 13.16% [4.41%, 28.09%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/39 = 15.38% [5.86%, 30.53%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| S_invalid_excluded | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/19 = 26.32% [9.15%, 51.20%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/20 = 30.00% [11.89%, 54.28%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/18 = 27.78% [9.69%, 53.48%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/19 = 31.58% [12.58%, 56.55%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| original_V2_native | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/6 = 16.67% [0.42%, 64.12%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/25 = 20.00% [6.83%, 40.70%] | 5/14 = 35.71% [12.76%, 64.86%] | 5/6 = 83.33% [35.88%, 99.58%] |
| original_V2_native | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/6 = 16.67% [0.42%, 64.12%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/25 = 20.00% [6.83%, 40.70%] | 5/14 = 35.71% [12.76%, 64.86%] | 5/6 = 83.33% [35.88%, 99.58%] |

## Frozen original V2 comparison

Original native verdicts only; no counterfactual original S or INVALID_ID policy has been fabricated.

| Verdict | Correct | Incorrect |
|---|---:|---:|
| PASS | 20 | 5 |
| FAIL | 5 | 1 |
| REGRESSION_ERROR | 0 | 0 |
| INCOMPLETE | 33 | 6 |
| NOT_AVAILABLE | 11 | 2 |

## Seven grader-failing existing tests

| Task | Test | Label | Original base / patched | Current base / patched | Policy C | Policy S |
|---|---|---|---|---|---|---|
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | incorrect | skipped / skipped | passed / passed | PASS | PASS |
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_multiprocessing[1]` | incorrect | skipped / skipped | passed / passed | PASS | PASS |
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_multiprocessing[2]` | incorrect | skipped / skipped | passed / passed | PASS | PASS |
| `pylint-dev__pylint-6528` | `tests/test_self.py::TestRunTC::test_jobs_score` | incorrect | skipped / skipped | passed / passed | PASS | PASS |
| `django__django-13297` | `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning` | incorrect | not_run / not_run | passed / passed | INCOMPLETE | INCOMPLETE |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | incorrect | passed / failed | passed / failed | FAIL | FAIL |
| `pylint-dev__pylint-7277` | `tests/test_self.py::TestRunTC::test_jobs_score` | incorrect | skipped / skipped | passed / passed | PASS | PASS |

## Six known regression witnesses

| Task | Test | Label | Original base / patched | Current base / patched | Policy C | Policy S |
|---|---|---|---|---|---|---|
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | correct | passed / failed | passed / failed | FAIL | FAIL |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | correct | passed / failed | passed / failed | FAIL | FAIL |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | correct | passed / failed | passed / failed | FAIL | FAIL |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | correct | passed / failed | passed / failed | FAIL | FAIL |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | correct | passed / failed | passed / failed | FAIL | FAIL |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | correct | passed / failed | passed / failed | FAIL | FAIL |

## Four incorrect patches among the 13 skip-dependent original PASS tasks

| Task | Original | C excluded | S excluded | C missing | S missing |
|---|---|---|---|---|---|
| `django__django-16667` | PASS | PASS | INCOMPLETE | PASS | INCOMPLETE |
| `matplotlib__matplotlib-23299` | PASS | PASS | INCOMPLETE | PASS | INCOMPLETE |
| `pylint-dev__pylint-6528` | PASS | PASS | PASS | PASS | PASS |
| `pylint-dev__pylint-7277` | PASS | PASS | PASS | PASS | PASS |

## CPU-conditioned outcomes reported at seal

These 38 concrete tests (76 tree instances) were already reported at seal. No new tests were run. Membership uses the 12 fixed selected families saved in the sealed results.

| Task | Native test | Original base / patched | Current base / patched |
|---|---|---|---|
| `pylint-dev__pylint-6528` | `tests/benchmark/test_baseline_benchmarks.py::TestEstablishBaselineBenchmarks::test_baseline_benchmark_check_parallel_j2` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/benchmark/test_baseline_benchmarks.py::TestEstablishBaselineBenchmarks::test_baseline_benchmark_j2` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/benchmark/test_baseline_benchmarks.py::TestEstablishBaselineBenchmarks::test_baseline_benchmark_j2_single_working_checker` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/benchmark/test_baseline_benchmarks.py::TestEstablishBaselineBenchmarks::test_baseline_lots_of_files_j2` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/benchmark/test_baseline_benchmarks.py::TestEstablishBaselineBenchmarks::test_baseline_lots_of_files_j2_empty_checker` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_multiprocessing[1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/lint/unittest_lint.py::test_multiprocessing[2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[1-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[1-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[1-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[10-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[10-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[10-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[2-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[2-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[2-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-1-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-1-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-1-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_compare_workers_to_single_proc[3-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[10-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[10-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[10-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[2-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[2-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[2-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-1-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-1-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-1-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-2-1]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-2-2]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallel::test_map_reduce[3-2-3]` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_check_parallel.py::TestCheckParallelFramework::test_worker_initialize_pickling` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-6528` | `tests/test_self.py::TestRunTC::test_jobs_score` | skipped / skipped | passed / passed |
| `pylint-dev__pylint-7277` | `tests/test_self.py::TestRunTC::test_jobs_score` | skipped / skipped | passed / passed |

## Stable confirmations and raw attribution

72 isolated tree calls cover 12 candidates. Positive raw-capture proofs verified: 72. Stability is base PASS 3/3 and patched FAILED/ERROR/CRASH 3/3; no broader non-PASS set is used. ERROR/CRASH is scored as ERROR, and the recorded outcomes remain unchanged.

| Task | Candidate | Label | Initial | Final | Base statuses | Patched statuses | Stable | Raw proofs |
|---|---|---|---|---|---|---|---|---|
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | correct | REGRESSION_ERROR | REGRESSION_ERROR | passed,passed,passed | error,error,error | True | True |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | correct | REGRESSION_ERROR | REGRESSION_ERROR | passed,passed,passed | error,error,error | True | True |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | correct | REGRESSION_ERROR | REGRESSION_ERROR | passed,passed,passed | error,error,error | True | True |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | correct | REGRESSION_ERROR | REGRESSION_ERROR | passed,passed,passed | error,error,error | True | True |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | correct | REGRESSION_ERROR | REGRESSION_ERROR | passed,passed,passed | error,error,error | True | True |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | incorrect | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | correct | REGRESSION | REGRESSION | passed,passed,passed | failed,failed,failed | True | True |

### Django-10973 REGRESSION_ERROR

This task is correct-labelled. Five candidates have base PASS 3/3 and patched ERROR 3/3; the task contributes only to secondary positive/false-alarm counts. Native patched signatures:
- `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic`: FileNotFoundError: [Errno 2] No such file or directory: 'psql': 'psql'
- `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass`: FileNotFoundError: [Errno 2] No such file or directory: 'psql': 'psql'
- `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column`: FileNotFoundError: [Errno 2] No such file or directory: 'psql': 'psql'
- `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters`: FileNotFoundError: [Errno 2] No such file or directory: 'psql': 'psql'
- `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler`: FileNotFoundError: [Errno 2] No such file or directory: 'psql': 'psql'

### All 72 confirmation calls

| Task | Candidate | Tree | Attempt | Recorded | Raw-derived | Proof |
|---|---|---|---:|---|---|---|
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | base | 1 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | base | 2 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | base | 3 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | patched | 1 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | patched | 2 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic` | patched | 3 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | base | 1 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | base | 2 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | base | 3 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | patched | 1 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | patched | 2 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass` | patched | 3 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | base | 1 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | base | 2 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | base | 3 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | patched | 1 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | patched | 2 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column` | patched | 3 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | base | 1 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | base | 2 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | base | 3 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | patched | 1 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | patched | 2 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters` | patched | 3 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | base | 1 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | base | 2 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | base | 3 | passed | passed | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | patched | 1 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | patched | 2 | error | error | native terminal cases |
| `django__django-10973` | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | patched | 3 | error | error | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | base | 1 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | base | 2 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | base | 3 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | patched | 1 | failed | failed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | patched | 2 | failed | failed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct` | patched | 3 | failed | failed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | base | 1 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | base | 2 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | base | 3 | passed | passed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | patched | 1 | failed | failed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | patched | 2 | failed | failed | native terminal cases |
| `django__django-14140` | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | patched | 3 | failed | failed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | base | 1 | passed | passed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | base | 2 | passed | passed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | base | 3 | passed | passed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | patched | 1 | failed | failed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | patched | 2 | failed | failed | native terminal cases |
| `pytest-dev__pytest-5809` | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | patched | 3 | failed | failed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | base | 1 | passed | passed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | base | 2 | passed | passed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | base | 3 | passed | passed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | patched | 1 | failed | failed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | patched | 2 | failed | failed | native terminal cases |
| `django__django-12209` | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | patched | 3 | failed | failed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | base | 1 | passed | passed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | base | 2 | passed | passed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | base | 3 | passed | passed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | patched | 1 | failed | failed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | patched | 2 | failed | failed | native terminal cases |
| `django__django-14631` | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | patched | 3 | failed | failed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | base | 1 | passed | passed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | base | 2 | passed | passed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | base | 3 | passed | passed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | patched | 1 | failed | failed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | patched | 2 | failed | failed | native terminal cases |
| `matplotlib__matplotlib-25479` | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | patched | 3 | failed | failed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | base | 1 | passed | passed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | base | 2 | passed | passed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | base | 3 | passed | passed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | patched | 1 | failed | failed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | patched | 2 | failed | failed | native terminal cases |
| `sphinx-doc__sphinx-10435` | `tests/test_build_latex.py::test_latex_code_role` | patched | 3 | failed | failed | native terminal cases |

## Recorded CRASH attribution audit

All six sealed CRASH attributions have progress but no process-death evidence: their batches exit 0 with an OK summary. They do not satisfy the pre-registered death requirement. The explanation below does not reclassify them; raw offsets, final terminal cases and excerpts are in analysis.json.

| Task | Tree | Module | Exit | Progress | Recorded active CRASH |
|---|---|---|---:|---|---|
| `django__django-15930` | base | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |
| `django__django-15930` | patched | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |
| `django__django-13297` | base | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |
| `django__django-13297` | patched | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |
| `django__django-14631` | base | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |
| `django__django-14631` | patched | `tests/timezones/tests.py` | 0 | True | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` |

## Six NOT_REACHED slots without a cap

Explanation only: these are normal-exit unreported requests, not supported crash collateral. The runner completes other tests successfully; neither omitted ForcedTimeZoneDatabaseTests method emits a result/start, and no explicit class-skip record establishes the underlying cause. No status or policy was reclassified.

| Task | Tree | NOT_REACHED test | Preceding CRASH | Exit | Crash collateral | Signature |
|---|---|---|---|---:|---|---|
| `django__django-15930` | base | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |
| `django__django-15930` | patched | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |
| `django__django-13297` | base | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |
| `django__django-13297` | patched | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |
| `django__django-14631` | base | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |
| `django__django-14631` | patched | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_write_datetime` | `tests/timezones/tests.py::ForcedTimeZoneDatabaseTests::test_read_datetime` | 0 | False |  |

## COLLECTION_ERROR: largest remaining missing-evidence category

1934 initial selected tree slots. Complete task/module/signature breakdown is in analysis.json; the 15 largest modules follow.

| Repository | Module | Slots | Base | Patched | Affected tasks | Signatures |
|---|---|---:|---:|---:|---:|---|
| `django` | `tests/gis_tests/geos_tests/test_geos.py` | 480 | 240 | 240 | 3 | SystemExit: 1 \| GIS database backend required (480) |
| `django` | `tests/gis_tests/distapp/tests.py` | 244 | 122 | 122 | 5 | SystemExit: 1 \| GIS database backend required (244) |
| `django` | `tests/gis_tests/geoapp/tests.py` | 178 | 89 | 89 | 3 | SystemExit: 1 \| GIS database backend required (178) |
| `django` | `tests/gis_tests/layermap/tests.py` | 146 | 73 | 73 | 4 | SystemExit: 1 \| GIS database backend required (146) |
| `django` | `tests/gis_tests/gdal_tests/test_raster.py` | 142 | 71 | 71 | 2 | SystemExit: 1 \| GIS database backend required (142) |
| `pytest-dev` | `testing/test_junitxml.py` | 130 | 65 | 65 | 1 | E   ModuleNotFoundError: No module named 'xmlschema' (130) |
| `django` | `tests/gis_tests/rasterapp/test_rasterfield.py` | 102 | 51 | 51 | 3 | SystemExit: 1 \| GIS database backend required (102) |
| `django` | `tests/gis_tests/test_geoforms.py` | 82 | 41 | 41 | 2 | SystemExit: 1 \| GIS database backend required (82) |
| `django` | `tests/gis_tests/geoapp/test_functions.py` | 74 | 37 | 37 | 1 | SystemExit: 1 \| GIS database backend required (74) |
| `django` | `tests/gis_tests/inspectapp/tests.py` | 64 | 32 | 32 | 4 | SystemExit: 1 \| GIS database backend required (64) |
| `django` | `tests/gis_tests/gis_migrations/test_operations.py` | 48 | 24 | 24 | 2 | SystemExit: 1 \| GIS database backend required (48) |
| `django` | `tests/gis_tests/geoapp/test_expressions.py` | 36 | 18 | 18 | 3 | SystemExit: 1 \| GIS database backend required (36) |
| `sympy` | `sympy/physics/quantum/tests/test_printing.py` | 32 | 16 | 16 | 1 | DeprecationWarning -> PyTestReporter._active_file during import of sympy/physics/quantum/tests/test_printing.py (32) |
| `django` | `tests/gis_tests/geoapp/test_regress.py` | 28 | 14 | 14 | 2 | SystemExit: 1 \| GIS database backend required (28) |
| `matplotlib` | `lib/matplotlib/tests/test_backend_bases.py` | 26 | 13 | 13 | 1 | E   AttributeError: module 'matplotlib.testing' has no attribute 'compare' (26) |

## Disclosures

- INVALID_ID sensitivity: Policy C primary yes/no is 58 with invalid IDs excluded versus 48 treated as missing; Policy S is 26 versus 25.
- The six non-cap NOT_REACHED slots are normal-exit unreported requests, not supported crash collateral. Their companion sealed CRASH attributions lack process-death evidence. Neither status is reclassified.
- COLLECTION_ERROR is the largest remaining unadmitted status category across all initial selected tree slots; this is not a claim about its share within the fixed B1 residual.
- CPU-conditioned outcomes were reported at seal, before labels were read.
- The frozen original comparison uses its recorded native policy, not a fabricated repaired-policy replay.

The executor, all sealed results, run files, and all tags remain unchanged. This script performs analysis only; no Docker or benchmark execution.
