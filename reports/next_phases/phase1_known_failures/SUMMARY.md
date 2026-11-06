# Phase 1: seven existing-test grader failures

**POST-HOC ANALYSIS ONLY.**
Seven witnesses across four incorrect-labelled patches were inspected using stored full-83 captures and hash-pinned execution provenance/scoring source. All seven were selected; 40 capture hashes verify.

| Bucket | Tests | Finding |
|---|---:|---|
| A — not reached | 1 | Django batch loader failure on both trees |
| E — skipped on both trees | 5 | Four Pylint-6528 witnesses and one Pylint-7277 witness |
| F — already detected | 1 | Matplotlib-25479 confirmed regression |

**Buckets E (skipped) and F (already detected) were added after Phase 1 inspection of the data.** They were not preregistered. Frozen selectors, outcomes and verdicts remain unchanged. The roadmap amendment records the retrospective addition.

## Django-13297: exact error and effect on the verdict

Target: `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning`; module `generic_views.test_base` (the capture prints `Importing application generic_views`). Batch 3 also requests `django.test.runner.RemoteTestResult.test_index`. The traceback does not name the exact offending test label, so that label is not asserted to be the culprit.

**base tree:** `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/base_b801df1e75a04136a31773e481cc700e/runner.raw:88` (traceback lines 88–99).

```text
88: Traceback (most recent call last):
89:   File "tests/runtests.py", line 577, in <module>
90:     options.start_at, options.start_after, options.pdb, options.buffer,
91:   File "tests/runtests.py", line 315, in django_tests
92:     extra_tests=extra_tests,
93:   File "/testbed/django/test/runner.py", line 705, in run_tests
94:     suite = self.build_suite(test_labels, extra_tests)
95:   File "/testbed/django/test/runner.py", line 562, in build_suite
96:     tests = self.test_loader.loadTestsFromName(label)
97:   File "/opt/miniconda3/envs/testbed/lib/python3.6/unittest/loader.py", line 213, in loadTestsFromName
98:     raise TypeError("don't know how to make test from: %s" % obj)
99: TypeError: don't know how to make test from: <property object at 0x7f5340435728>
```

**patched tree:** `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/patched_b55fb9e09e194de3ae5bacaeac3bba5e/runner.raw:88` (traceback lines 88–99).

```text
88: Traceback (most recent call last):
89:   File "tests/runtests.py", line 577, in <module>
90:     options.start_at, options.start_after, options.pdb, options.buffer,
91:   File "tests/runtests.py", line 315, in django_tests
92:     extra_tests=extra_tests,
93:   File "/testbed/django/test/runner.py", line 705, in run_tests
94:     suite = self.build_suite(test_labels, extra_tests)
95:   File "/testbed/django/test/runner.py", line 562, in build_suite
96:     tests = self.test_loader.loadTestsFromName(label)
97:   File "/opt/miniconda3/envs/testbed/lib/python3.6/unittest/loader.py", line 213, in loadTestsFromName
98:     raise TypeError("don't know how to make test from: %s" % obj)
99: TypeError: don't know how to make test from: <property object at 0x7f9839134728>
```

The exception occurs on **both** trees; each batch exits 1 without a timeout. The failing frame is Python 3.6 `unittest.loader.loadTestsFromName`, line 213. Calling frames are `tests/runtests.py` and `django/test/runner.py`. The candidate changes only `django/views/generic/base.py`: neither the failing frame nor any listed calling frame is candidate-modified. The candidate file names/digest and stored scoring source hash are recorded in `phase1_evidence.json`.

V2 records selected status **NOT_RUN on base and NOT_RUN on patched**, with no concrete raw observation. Its paired per-test outcome is NOT_RUN. Both missing statuses appear in the recorded incompleteness list. The task's original PASS is converted to **INCOMPLETE** (`INCOMPLETE_CONFIRMED`); this gap contributes alongside other gaps, without being scored as a candidate regression. Since the error is not patched-only, this case does not trigger the proposed additional patched-only REGRESSION_ERROR roadmap item.

## Five Pylint skips: exact saved text and limits

| Task | Test | Captured reason string, on each tree | Skip mechanism | Base / patched selected status |
|---|---|---|---|---|
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | not printed | unknown from captures | SKIPPED / SKIPPED |
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[1]` | `Need 2...` (truncated) | unknown from captures | NOT_RUN / NOT_RUN |
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[2]` | `Need 2...` (truncated) | unknown from captures | NOT_RUN / NOT_RUN |
| pylint-dev__pylint-6528 | `tests/test_self.py::TestRunTC::test_jobs_score` | `Need 2 or mo...` (truncated) | unknown from captures | SKIPPED / SKIPPED |
| pylint-dev__pylint-7277 | `tests/test_self.py::TestRunTC::test_jobs_score` | `Need 2 or mo...` (truncated) | unknown from captures | SKIPPED / SKIPPED |

The saved lines prove SKIPPED for all five concrete tests on both trees. They do **not** preserve the full reason strings or identify a marker, importorskip, version guard or platform guard. The recorded raw-result `message` fields are empty. `Need 2...` and `Need 2 or mo...` are reported verbatim; their expansions and mechanisms are not inferred. No source archives were inspected, no benchmark code was imported, and no Docker/rerun/environment probe was performed.

**Final task verdicts: pylint-6528 PASS / COMPLETE; pylint-7277 PASS / COMPLETE, both with zero recorded incompleteness reasons.** These skips were accepted for completeness. The frozen scorer treats SKIPPED as `base_ok`/`patched_ok`, producing per-test PASS for the three exact selected IDs. For the two multiprocessing parameter cases, the bare selected family stays NOT_RUN, but mapped raw SKIPPED cases satisfy the completeness recovery rule. Thus these PASS verdicts relied on accepting skipped selected evidence. Under the requested stricter missing-evidence rule, the existing PASS→INCOMPLETE gate would block those PASS decisions; no native record is rescored here.

Stored policy evidence: `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50/src/reliability/verifier/regression.py` — completeness recovery at lines 232–237, skip-to-PASS classification at lines 311–315, and PASS→INCOMPLETE at line 266. Its hash matches the completed run provenance. Phase 3 therefore adds **treat SKIPPED selected tests as missing evidence for PASS**, including mapped parameter cases.

## Artifacts and accounting

`phase1_known_failures.csv` has seven rows and the requested `base_outcome`, `patched_outcome`, `skip_or_error_reason`, `v2_task_verdict`, `evidence_path:line` fields. The outcome columns are the runner's selected-ID statuses; concrete parameter SKIPPED states remain in `base_raw_status`/`patched_raw_status`, and skip mechanisms are explicitly unknown. Every evidence reference names each tree separately.

`phase1_observations.csv` has all 16 observations; `phase1_evidence.json` retains status/traceback excerpts, source/capture hashes, task completeness, and event/byte ranges. Matplotlib retains PASS→FAIL, patched confirmation FAIL, additional base PASS, native REGRESSION and task FAIL. No C or D case was observed. No Phase 2 work was performed.
