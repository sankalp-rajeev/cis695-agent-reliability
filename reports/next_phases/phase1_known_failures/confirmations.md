# Phase 1 confirmations from frozen selection, captures and base archives

**POST-HOC ANALYSIS ONLY.** This follow-up adds static archive evidence to the capture-only Phase 1 report; it performs no Docker calls, benchmark execution, imports of benchmark code or changes to frozen artifacts.

## Django-13297 batch 3

**Confirmed:** `django/test/runner.py::RemoteTestResult::test_index` is in the frozen V2 selection and is request 9 in batch 3 on both trees. The hash-verified base archive defines it with `@property` at line 123 and `def test_index` at line 124.

```python
123:     @property
124:     def test_index(self):
125:         return self.testsRun - 1
```

Source: `/home/sankalp/cg_repos/task_archives/django__django-13297.tar!testbed/django/test/runner.py:123`; source SHA-256 `857710c1d9ed3f31e926a7033077265e03125e5cf3ede4ecdd0b35603d37c712`.

**Observed accounting:** 25/25 requested selected IDs are NOT_RUN on base and 25/25 on patched (50 tree-ID slots). One is the invalid property request; 24 are real test functions collaterally not executed by the loader abort. Each batch exits 1 before any test outcome, has `split=false`, and has no timeout. The only exception in this batch segment is the property-object TypeError. This establishes the immediate batch-level cause, not a counterfactual guarantee that all 24 would run or pass after removing the property.

| Position | Exact requested label | Kind | Base | Patched |
|---:|---|---|---|---|
| 1 | `generic_views.test_base.GetContextDataTest.test_object_at_custom_name_in_context_data` | test function | NOT_RUN | NOT_RUN |
| 2 | `generic_views.test_base.GetContextDataTest.test_object_in_get_context_data` | test function | NOT_RUN | NOT_RUN |
| 3 | `generic_views.test_base.UseMultipleObjectMixinTest.test_use_queryset_from_view` | test function | NOT_RUN | NOT_RUN |
| 4 | `generic_views.test_base.UseMultipleObjectMixinTest.test_overwrite_queryset` | test function | NOT_RUN | NOT_RUN |
| 5 | `generic_views.test_base.SingleObjectTemplateResponseMixinTest.test_template_mixin_without_template` | test function | NOT_RUN | NOT_RUN |
| 6 | `generic_views.test_base.DeprecationTests.test_template_params` | test function | NOT_RUN | NOT_RUN |
| 7 | `generic_views.test_base.DeprecationTests.test_extra_template_params` | test function | NOT_RUN | NOT_RUN |
| 8 | `generic_views.test_base.DeprecationTests.test_template_params_warning` | test function | NOT_RUN | NOT_RUN |
| 9 | `django.test.runner.RemoteTestResult.test_index` | property | NOT_RUN | NOT_RUN |
| 10 | `admin_autodiscover.tests.AdminAutoDiscoverTests.test_double_call_autodiscover` | test function | NOT_RUN | NOT_RUN |
| 11 | `admin_changelist.test_date_hierarchy.DateHierarchyTests.test_bounded_params` | test function | NOT_RUN | NOT_RUN |
| 12 | `admin_changelist.test_date_hierarchy.DateHierarchyTests.test_bounded_params_with_time_zone` | test function | NOT_RUN | NOT_RUN |
| 13 | `admin_changelist.test_date_hierarchy.DateHierarchyTests.test_bounded_params_with_dst_time_zone` | test function | NOT_RUN | NOT_RUN |
| 14 | `admin_changelist.test_date_hierarchy.DateHierarchyTests.test_invalid_params` | test function | NOT_RUN | NOT_RUN |
| 15 | `admin_changelist.tests.ChangeListTests.test_specified_ordering_by_f_expression` | test function | NOT_RUN | NOT_RUN |
| 16 | `admin_changelist.tests.ChangeListTests.test_specified_ordering_by_f_expression_without_asc_desc` | test function | NOT_RUN | NOT_RUN |
| 17 | `admin_changelist.tests.ChangeListTests.test_select_related_preserved` | test function | NOT_RUN | NOT_RUN |
| 18 | `admin_changelist.tests.ChangeListTests.test_select_related_as_tuple` | test function | NOT_RUN | NOT_RUN |
| 19 | `admin_changelist.tests.ChangeListTests.test_select_related_as_empty_tuple` | test function | NOT_RUN | NOT_RUN |
| 20 | `admin_changelist.tests.ChangeListTests.test_get_select_related_custom_method` | test function | NOT_RUN | NOT_RUN |
| 21 | `admin_changelist.tests.ChangeListTests.test_result_list_empty_changelist_value` | test function | NOT_RUN | NOT_RUN |
| 22 | `admin_changelist.tests.ChangeListTests.test_result_list_set_empty_value_display_on_admin_site` | test function | NOT_RUN | NOT_RUN |
| 23 | `admin_changelist.tests.ChangeListTests.test_result_list_set_empty_value_display_in_model_admin` | test function | NOT_RUN | NOT_RUN |
| 24 | `admin_changelist.tests.ChangeListTests.test_result_list_html` | test function | NOT_RUN | NOT_RUN |
| 25 | `admin_changelist.tests.ChangeListTests.test_result_list_editable_html` | test function | NOT_RUN | NOT_RUN |

Capture references:
- base: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/base_b801df1e75a04136a31773e481cc700e/events.jsonl:5` (start) and `:6` (exit); `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/base_b801df1e75a04136a31773e481cc700e/runner.raw:88` (traceback, through line 99).
- patched: `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/patched_b55fb9e09e194de3ae5bacaeac3bba5e/events.jsonl:5` (start) and `:6` (exit); `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results/tasks/django__django-13297/v2/raw/patched_b55fb9e09e194de3ae5bacaeac3bba5e/runner.raw:88` (traceback, through line 99).

The property is the sole non-test descriptor among these 25 definitions, matching the loader TypeError, and its module is unchanged by the candidate patch; no rerun was used to isolate it experimentally.

## Pylint skip conditions from stored base source

**All five use the full reason:** `Need 2 or more cores for test to be meaningful`.

Mechanism: the test has `@pytest.mark.needs_two_cores`; `tests/conftest.py::pytest_collection_modifyitems` checks `_cpu_count() < 2` and adds `pytest.mark.skip(reason=...)` to marked items. This is a CPU-count collection marker, not importorskip or a direct version/platform guard. `_cpu_count` is imported from `pylint.lint.run`.

| Task | Concrete test | Marker line | Hook condition line | Full-reason line |
|---|---|---|---|---|
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/lint/unittest_lint.py:774` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/conftest.py:122` | 124 |
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[1]` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/lint/unittest_lint.py:803` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/conftest.py:122` | 124 |
| pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[2]` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/lint/unittest_lint.py:803` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/conftest.py:122` | 124 |
| pylint-dev__pylint-6528 | `tests/test_self.py::TestRunTC::test_jobs_score` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/test_self.py:1050` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar!testbed/tests/conftest.py:122` | 124 |
| pylint-dev__pylint-7277 | `tests/test_self.py::TestRunTC::test_jobs_score` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-7277.tar!testbed/tests/test_self.py:909` | `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-7277.tar!testbed/tests/conftest.py:120` | 122 |

All three archive SHA-256 values match their frozen base metadata; individual inspected source hashes are retained in `confirmations.json`. The complete reason and mechanism come from static base source; the earlier captures printed truncated/absent reasons. The test bodies were recorded SKIPPED on both trees, and both Pylint task verdicts remain PASS / COMPLETE.

## CPU count and Docker launch

**Directly recorded:** Docker daemon `NCPU = 16`, in `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/pilot_20261105T183041_929325Z/docker_and_launch_checks.json:13` and `/home/sankalp/projects/cis695-agent-reliability/reports/v2_discovery_cleanup/ubuntu_readonly_preflight_20261105T171113_732025Z/docker_health.json:36`. Django also prints “with up to 16 processes” in the batch capture at line 84. These are not measurements of Pylint’s `_cpu_count()` result.

**Not recorded:** the exact Pylint container `_cpu_count()` return, affinity count, CPU quota/period and CPU shares. A scoped stored-field search of the integration evidence found only the daemon count, not a per-Pylint numeric count. The guard and skips are consistent with the helper returning less than 2; do not report an observed value of 1.

**Docker launch:** the pinned `TaskContainer.run_args()` at `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50/src/reliability/verifier/container.py:102` constructs `docker run -d --name ... [--label ...] -w /testbed --network none IMAGE sleep infinity` without `--cpus`, `--cpu-quota` or `--cpuset-cpus`; `LocalOnlyContainer` adds only `--pull=never` at `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50/scripts/v2_evaluation.py:206`. Both source files match the completed run’s recorded source hashes.

The stored Pylint `_cpu_count()` combines cgroup quota/shares with CPU affinity or multiprocessing count and takes a minimum when cgroup data exists (6528 `pylint/lint/run.py:30–74`; 7277 `:34–90`). Thus daemon NCPU=16 and a CPU-guard skip are not contradictory; missing cgroup readings prevent attributing the skip to a measured resource setting.

## Source archive hashes

- `/home/sankalp/cg_repos/task_archives/django__django-13297.tar` — `4f499ef39fae21bfb9ce3eb9cbf2b3878158435323828e5e1a480e90aa810da4`.
- `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-6528.tar` — `ca2fab439b584b5b1e770fe335e2f3a7376fd13a43262c38a8969801e6f8a99c`.
- `/home/sankalp/cg_repos/task_archives/pylint-dev__pylint-7277.tar` — `baac4682f2541d8489225f5e3049f46e605e14fb89a70290d447e50c1ed46aa2`.
