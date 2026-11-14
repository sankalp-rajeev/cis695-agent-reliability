# Phase 5 offline replay — Amendment A1

Sealed Phase 4 reference: `69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25`; all 1,799 files verified before and after replay.

Tier gate: before **64**, after **19**, neither **0**. Exact content and order plus exact tier union required. When both match, before wins; both matches are recorded.

Execution-only is primary. All module end-event durations in the initial patched pass are summed, including split parents, retries and fallback processes. Isolated confirmation execution costs are reported separately. Collection-group time is separate and added in the second variant. No per-test times are estimated.

Source order means first module appearance through the frozen V2 list, expanding inherited families to native modules only with their recorded validation mappings. Partially reached families are counted separately. Changed-module names use exact basenames with conventional test affixes removed, using only frozen SCG mapping paths. Modules mixing tiers take the lowest tier.

A module starts before the deadline; completion at the deadline counts. A crossing module is attempted, but its reference outcomes count only under the optimistic bound. `>budget` means right-censored, not zero. Random columns are the 25th/median/75th percentiles over seeds 0..19.

These are recorded module-process cost replays. They do not establish outcomes or costs of tests outside the V2 reference, or of a newly executed reduced module. Reaching a module does not turn its skipped or collection-error IDs into executed tests.

## Exclusions

| Task | Reason |
|---|---|
| `astropy__astropy-14508` | Empty V2 reference selection |
| `django__django-16082` | Frozen SCG selection has no changed-module paths; name priority unavailable |
| `matplotlib__matplotlib-14623` | Empty V2 reference selection |
| `matplotlib__matplotlib-24177` | Empty V2 reference selection |
| `pydata__xarray-4966` | Empty V2 reference selection |
| `pylint-dev__pylint-6903` | Empty V2 reference selection |
| `sympy__sympy-24562` | Phase 4 patched pass censored; missing/truncated module durations cannot be invented |

Tier-gate exclusions: None.

## Seven regression cases: selectors

Counts are kept/missed reference IDs; exact names appear below and in selector_replay.csv. Outside-reference selections count separately and never become kept or missed reference regressions.

| Task | Tier 1 kept/missed | V2 kept/missed | SCG kept/missed | SCG outside reference |
|---|---:|---:|---:|---:|
| `django__django-10973` | 0/5 | 5/0 | 0/5 | 0 |
| `django__django-12209` | 0/1 | 1/0 | 0/1 | 0 |
| `django__django-14140` | 0/2 | 2/0 | 0/2 | 0 |
| `django__django-14631` | 1/0 | 1/0 | 0/1 | 0 |
| `matplotlib__matplotlib-25479` | 0/1 | 1/0 | 0/1 | 0 |
| `pytest-dev__pytest-5809` | 0/1 | 1/0 | 0/1 | 0 |
| `sphinx-doc__sphinx-10435` | 0/1 | 1/0 | 0/1 | 0 |

| Task | Selector | Reference regressions kept (named) | Reference regressions missed (named) |
|---|---|---|---|
| `django__django-10973` | v2_tier1 | none | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` |
| `django__django-10973` | v2_tier1_tier2 | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` | none |
| `django__django-10973` | corrected_scg | none | `tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_basic`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_column`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_escape_characters`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_nopass`<br>`tests/dbshell/test_postgresql.py::PostgreSqlDbshellCommandTestCase::test_sigint_handler` |
| `django__django-12209` | v2_tier1 | none | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` |
| `django__django-12209` | v2_tier1_tier2 | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | none |
| `django__django-12209` | corrected_scg | none | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` |
| `django__django-14140` | v2_tier1 | none | `tests/queries/test_q.py::QTests::test_deconstruct`<br>`tests/queries/test_q.py::QTests::test_deconstruct_negated` |
| `django__django-14140` | v2_tier1_tier2 | `tests/queries/test_q.py::QTests::test_deconstruct`<br>`tests/queries/test_q.py::QTests::test_deconstruct_negated` | none |
| `django__django-14140` | corrected_scg | none | `tests/queries/test_q.py::QTests::test_deconstruct`<br>`tests/queries/test_q.py::QTests::test_deconstruct_negated` |
| `django__django-14631` | v2_tier1 | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | none |
| `django__django-14631` | v2_tier1_tier2 | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | none |
| `django__django-14631` | corrected_scg | none | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` |
| `matplotlib__matplotlib-25479` | v2_tier1 | none | `lib/matplotlib/tests/test_colors.py::test_register_cmap` |
| `matplotlib__matplotlib-25479` | v2_tier1_tier2 | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | none |
| `matplotlib__matplotlib-25479` | corrected_scg | none | `lib/matplotlib/tests/test_colors.py::test_register_cmap` |
| `pytest-dev__pytest-5809` | v2_tier1 | none | `testing/test_pastebin.py::TestPaste::test_create_new_paste` |
| `pytest-dev__pytest-5809` | v2_tier1_tier2 | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | none |
| `pytest-dev__pytest-5809` | corrected_scg | none | `testing/test_pastebin.py::TestPaste::test_create_new_paste` |
| `sphinx-doc__sphinx-10435` | v2_tier1 | none | `tests/test_build_latex.py::test_latex_code_role` |
| `sphinx-doc__sphinx-10435` | v2_tier1_tier2 | `tests/test_build_latex.py::test_latex_code_role` | none |
| `sphinx-doc__sphinx-10435` | corrected_scg | none | `tests/test_build_latex.py::test_latex_code_role` |

## Ordering: execution_only

Each time is seconds. Nonbinding budgets are non-informative.

| Task | Budget | Binds | Rule start | Random start q25/median/q75 | Rule end | Random end q25/median/q75 | Rule kept start/end |
|---|---:|---|---:|---|---:|---|---|
| `django__django-10973` | 30 | no | 0.590 | 0.292/0.297/0.370 | 0.903 | 0.606/0.610/0.683 | 5/5 |
| `django__django-10973` | 60 | no | 0.590 | 0.292/0.297/0.370 | 0.903 | 0.606/0.610/0.683 | 5/5 |
| `django__django-10973` | 120 | no | 0.590 | 0.292/0.297/0.370 | 0.903 | 0.606/0.610/0.683 | 5/5 |
| `django__django-10973` | 300 | no | 0.590 | 0.292/0.297/0.370 | 0.903 | 0.606/0.610/0.683 | 5/5 |
| `django__django-12209` | 30 | yes | >budget | 14.413/>budget/>budget | >budget | 14.986/>budget/>budget | 0/0 |
| `django__django-12209` | 60 | yes | 33.359 | 14.413/30.354/37.220 | 33.932 | 14.986/30.927/37.793 | 1/1 |
| `django__django-12209` | 120 | no | 33.359 | 14.413/30.354/37.220 | 33.932 | 14.986/30.927/37.793 | 1/1 |
| `django__django-12209` | 300 | no | 33.359 | 14.413/30.354/37.220 | 33.932 | 14.986/30.927/37.793 | 1/1 |
| `django__django-14140` | 30 | no | 17.463 | 3.619/7.023/15.821 | 17.878 | 4.033/7.437/16.235 | 2/2 |
| `django__django-14140` | 60 | no | 17.463 | 3.619/7.023/15.821 | 17.878 | 4.033/7.437/16.235 | 2/2 |
| `django__django-14140` | 120 | no | 17.463 | 3.619/7.023/15.821 | 17.878 | 4.033/7.437/16.235 | 2/2 |
| `django__django-14140` | 300 | no | 17.463 | 3.619/7.023/15.821 | 17.878 | 4.033/7.437/16.235 | 2/2 |
| `django__django-14631` | 30 | yes | 0.000 | 14.774/>budget/>budget | 0.509 | 15.283/>budget/>budget | 1/1 |
| `django__django-14631` | 60 | yes | 0.000 | 14.774/32.141/49.783 | 0.509 | 15.283/32.650/50.292 | 1/1 |
| `django__django-14631` | 120 | no | 0.000 | 14.774/32.141/49.783 | 0.509 | 15.283/32.650/50.292 | 1/1 |
| `django__django-14631` | 300 | no | 0.000 | 14.774/32.141/49.783 | 0.509 | 15.283/32.650/50.292 | 1/1 |
| `matplotlib__matplotlib-25479` | 30 | no | 0.000 | 0.000/0.000/0.000 | 3.989 | 3.989/3.989/3.989 | 1/1 |
| `matplotlib__matplotlib-25479` | 60 | no | 0.000 | 0.000/0.000/0.000 | 3.989 | 3.989/3.989/3.989 | 1/1 |
| `matplotlib__matplotlib-25479` | 120 | no | 0.000 | 0.000/0.000/0.000 | 3.989 | 3.989/3.989/3.989 | 1/1 |
| `matplotlib__matplotlib-25479` | 300 | no | 0.000 | 0.000/0.000/0.000 | 3.989 | 3.989/3.989/3.989 | 1/1 |
| `pytest-dev__pytest-5809` | 30 | no | 0.000 | 0.000/0.000/0.000 | 0.326 | 0.326/0.326/0.326 | 1/1 |
| `pytest-dev__pytest-5809` | 60 | no | 0.000 | 0.000/0.000/0.000 | 0.326 | 0.326/0.326/0.326 | 1/1 |
| `pytest-dev__pytest-5809` | 120 | no | 0.000 | 0.000/0.000/0.000 | 0.326 | 0.326/0.326/0.326 | 1/1 |
| `pytest-dev__pytest-5809` | 300 | no | 0.000 | 0.000/0.000/0.000 | 0.326 | 0.326/0.326/0.326 | 1/1 |
| `sphinx-doc__sphinx-10435` | 30 | no | 0.000 | 0.000/1.487/1.487 | 6.600 | 6.600/8.087/8.087 | 1/1 |
| `sphinx-doc__sphinx-10435` | 60 | no | 0.000 | 0.000/1.487/1.487 | 6.600 | 6.600/8.087/8.087 | 1/1 |
| `sphinx-doc__sphinx-10435` | 120 | no | 0.000 | 0.000/1.487/1.487 | 6.600 | 6.600/8.087/8.087 | 1/1 |
| `sphinx-doc__sphinx-10435` | 300 | no | 0.000 | 0.000/1.487/1.487 | 6.600 | 6.600/8.087/8.087 | 1/1 |

**Pre-registered evidence verdict: inconclusive.**

optimistic: 12 reference IDs kept; integer threshold 11 of 12. Rule task-median 0.000 s; random q25 of per-seed task-medians 0.292 s. Strict time improvement: True; arithmetic criterion met: True.
conservative: 12 reference IDs kept; integer threshold 11 of 12. Rule task-median 3.989 s; random q25 of per-seed task-medians 3.989 s. Strict time improvement: False; arithmetic criterion met: False.

Bound disagreement: True. All seven 120 s budgets nonbinding: True.


## Ordering: execution_plus_collection

Each time is seconds. Nonbinding budgets are non-informative.

| Task | Budget | Binds | Rule start | Random start q25/median/q75 | Rule end | Random end q25/median/q75 | Rule kept start/end |
|---|---:|---|---:|---|---:|---|---|
| `django__django-10973` | 30 | no | 1.144 | 0.551/0.594/0.731 | 1.732 | 1.138/1.181/1.319 | 5/5 |
| `django__django-10973` | 60 | no | 1.144 | 0.551/0.594/0.731 | 1.732 | 1.138/1.181/1.319 | 5/5 |
| `django__django-10973` | 120 | no | 1.144 | 0.551/0.594/0.731 | 1.732 | 1.138/1.181/1.319 | 5/5 |
| `django__django-10973` | 300 | no | 1.144 | 0.551/0.594/0.731 | 1.732 | 1.138/1.181/1.319 | 5/5 |
| `django__django-12209` | 30 | yes | >budget | 21.216/>budget/>budget | >budget | 22.080/>budget/>budget | 0/0 |
| `django__django-12209` | 60 | yes | 45.561 | 21.216/42.694/52.747 | 46.426 | 22.080/43.559/53.612 | 1/1 |
| `django__django-12209` | 120 | no | 45.561 | 21.216/42.694/52.747 | 46.426 | 22.080/43.559/53.612 | 1/1 |
| `django__django-12209` | 300 | no | 45.561 | 21.216/42.694/52.747 | 46.426 | 22.080/43.559/53.612 | 1/1 |
| `django__django-14140` | 30 | yes | 27.688 | 5.213/10.621/23.882 | 28.437 | 5.962/11.370/24.631 | 2/2 |
| `django__django-14140` | 60 | no | 27.688 | 5.213/10.621/23.882 | 28.437 | 5.962/11.370/24.631 | 2/2 |
| `django__django-14140` | 120 | no | 27.688 | 5.213/10.621/23.882 | 28.437 | 5.962/11.370/24.631 | 2/2 |
| `django__django-14140` | 300 | no | 27.688 | 5.213/10.621/23.882 | 28.437 | 5.962/11.370/24.631 | 2/2 |
| `django__django-14631` | 30 | yes | 0.000 | 18.849/>budget/>budget | 0.771 | 19.619/>budget/>budget | 1/1 |
| `django__django-14631` | 60 | yes | 0.000 | 18.849/43.412/>budget | 0.771 | 19.619/44.182/>budget | 1/1 |
| `django__django-14631` | 120 | no | 0.000 | 18.849/43.412/69.640 | 0.771 | 19.619/44.182/70.410 | 1/1 |
| `django__django-14631` | 300 | no | 0.000 | 18.849/43.412/69.640 | 0.771 | 19.619/44.182/70.410 | 1/1 |
| `matplotlib__matplotlib-25479` | 30 | no | 0.000 | 0.000/0.000/0.000 | 4.731 | 4.731/4.731/4.731 | 1/1 |
| `matplotlib__matplotlib-25479` | 60 | no | 0.000 | 0.000/0.000/0.000 | 4.731 | 4.731/4.731/4.731 | 1/1 |
| `matplotlib__matplotlib-25479` | 120 | no | 0.000 | 0.000/0.000/0.000 | 4.731 | 4.731/4.731/4.731 | 1/1 |
| `matplotlib__matplotlib-25479` | 300 | no | 0.000 | 0.000/0.000/0.000 | 4.731 | 4.731/4.731/4.731 | 1/1 |
| `pytest-dev__pytest-5809` | 30 | no | 0.000 | 0.000/0.000/0.000 | 0.466 | 0.466/0.466/0.466 | 1/1 |
| `pytest-dev__pytest-5809` | 60 | no | 0.000 | 0.000/0.000/0.000 | 0.466 | 0.466/0.466/0.466 | 1/1 |
| `pytest-dev__pytest-5809` | 120 | no | 0.000 | 0.000/0.000/0.000 | 0.466 | 0.466/0.466/0.466 | 1/1 |
| `pytest-dev__pytest-5809` | 300 | no | 0.000 | 0.000/0.000/0.000 | 0.466 | 0.466/0.466/0.466 | 1/1 |
| `sphinx-doc__sphinx-10435` | 30 | no | 0.000 | 0.000/1.835/1.835 | 6.984 | 6.984/8.819/8.819 | 1/1 |
| `sphinx-doc__sphinx-10435` | 60 | no | 0.000 | 0.000/1.835/1.835 | 6.984 | 6.984/8.819/8.819 | 1/1 |
| `sphinx-doc__sphinx-10435` | 120 | no | 0.000 | 0.000/1.835/1.835 | 6.984 | 6.984/8.819/8.819 | 1/1 |
| `sphinx-doc__sphinx-10435` | 300 | no | 0.000 | 0.000/1.835/1.835 | 6.984 | 6.984/8.819/8.819 | 1/1 |

**Pre-registered evidence verdict: inconclusive.**

optimistic: 12 reference IDs kept; integer threshold 11 of 12. Rule task-median 0.000 s; random q25 of per-seed task-medians 0.551 s. Strict time improvement: True; arithmetic criterion met: True.
conservative: 12 reference IDs kept; integer threshold 11 of 12. Rule task-median 4.731 s; random q25 of per-seed task-medians 4.731 s. Strict time improvement: False; arithmetic criterion met: False.

Bound disagreement: True. All seven 120 s budgets nonbinding: True.

## Mixed-tier modules

| Task | Module | Tiers |
|---|---|---|
| None | — | — |

## Budget binding and cost completeness for all tasks

Binding uses the replayed sum of module process durations (plus collection groups in the second variant). Recorded wall durations, which also include setup and validation overhead, are separate columns in per_task_costs.csv. A censored original pass has no known complete cost; its observed cost is a lower bound that can still establish binding when already above a budget.

| Task | Execution s | Collection groups s | Execution binding budgets | With collection binding budgets |
|---|---:|---:|---|---|
| `astropy__astropy-13977` | 204.706 | 91.301 | 30, 60, 120 | 30, 60, 120 |
| `astropy__astropy-14365` | 0.878 | 0.839 | none | none |
| `astropy__astropy-14508` | 0.000 | 0.000 | none | none |
| `astropy__astropy-7606` | 189.466 | 9.764 | 30, 60, 120 | 30, 60, 120 |
| `django__django-10973` | 0.903 | 0.829 | none | none |
| `django__django-11095` | 23.409 | 5.257 | none | none |
| `django__django-11299` | 12.871 | 2.542 | none | none |
| `django__django-11820` | 62.847 | 28.072 | 30, 60 | 30, 60 |
| `django__django-12209` | 64.587 | 26.090 | 30, 60 | 30, 60 |
| `django__django-12965` | 0.561 | 0.281 | none | none |
| `django__django-13023` | 14.921 | 9.076 | none | none |
| `django__django-13033` | 0.767 | 0.309 | none | none |
| `django__django-13158` | 16.584 | 2.862 | none | none |
| `django__django-13212` | 18.394 | 9.207 | none | none |
| `django__django-13297` | 197.617 | 83.353 | 30, 60, 120 | 30, 60, 120 |
| `django__django-13569` | 9.603 | 2.066 | none | none |
| `django__django-13786` | 6.726 | 2.379 | none | none |
| `django__django-13807` | 3.713 | 1.161 | none | none |
| `django__django-13820` | 3.582 | 1.230 | none | none |
| `django__django-14140` | 21.645 | 11.977 | none | 30 |
| `django__django-14631` | 76.750 | 24.651 | 30, 60 | 30, 60 |
| `django__django-15037` | 15.722 | 2.795 | none | none |
| `django__django-15103` | 1.434 | 0.978 | none | none |
| `django__django-15278` | 3.425 | 1.516 | none | none |
| `django__django-15375` | 2.746 | 1.544 | none | none |
| `django__django-15499` | 8.703 | 2.031 | none | none |
| `django__django-15572` | 0.801 | 0.491 | none | none |
| `django__django-15930` | 60.898 | 18.845 | 30, 60 | 30, 60 |
| `django__django-16082` | 0.490 | 0.514 | none | none |
| `django__django-16136` | 72.716 | 16.925 | 30, 60 | 30, 60 |
| `django__django-16255` | 0.766 | 0.478 | none | none |
| `django__django-16315` | 0.360 | 0.230 | none | none |
| `django__django-16612` | 16.823 | 4.268 | none | none |
| `django__django-16631` | 5.049 | 1.846 | none | none |
| `django__django-16667` | 2.332 | 1.375 | none | none |
| `matplotlib__matplotlib-14623` | 0.000 | 0.000 | none | none |
| `matplotlib__matplotlib-20488` | 125.835 | 5.998 | 30, 60, 120 | 30, 60, 120 |
| `matplotlib__matplotlib-20676` | 110.027 | 8.558 | 30, 60 | 30, 60 |
| `matplotlib__matplotlib-22719` | 3.980 | 1.767 | none | none |
| `matplotlib__matplotlib-22871` | 4.022 | 0.869 | none | none |
| `matplotlib__matplotlib-23299` | 7.911 | 2.350 | none | none |
| `matplotlib__matplotlib-23476` | 108.886 | 11.156 | 30, 60 | 30, 60, 120 |
| `matplotlib__matplotlib-24026` | 83.016 | 3.085 | 30, 60 | 30, 60 |
| `matplotlib__matplotlib-24177` | 0.000 | 0.000 | none | none |
| `matplotlib__matplotlib-24637` | 2.791 | 0.712 | none | none |
| `matplotlib__matplotlib-24970` | 3.689 | 0.698 | none | none |
| `matplotlib__matplotlib-25122` | 11.645 | 0.978 | none | none |
| `matplotlib__matplotlib-25287` | 2.263 | 0.662 | none | none |
| `matplotlib__matplotlib-25479` | 3.989 | 0.742 | none | none |
| `matplotlib__matplotlib-26291` | 7.211 | 1.427 | none | none |
| `mwaskom__seaborn-3069` | 13.180 | 1.300 | none | none |
| `pallets__flask-5014` | 2.479 | 1.404 | none | none |
| `pydata__xarray-4629` | 2.768 | 2.656 | none | none |
| `pydata__xarray-4695` | 14.304 | 2.734 | none | none |
| `pydata__xarray-4966` | 0.000 | 0.000 | none | none |
| `pydata__xarray-6599` | 7.470 | 2.458 | none | none |
| `pydata__xarray-6744` | 75.274 | 12.824 | 30, 60 | 30, 60 |
| `pylint-dev__pylint-4661` | 0.763 | 0.673 | none | none |
| `pylint-dev__pylint-4970` | 74.948 | 7.985 | 30, 60 | 30, 60 |
| `pylint-dev__pylint-6528` | 82.896 | 18.208 | 30, 60 | 30, 60 |
| `pylint-dev__pylint-6903` | 0.000 | 0.000 | none | none |
| `pylint-dev__pylint-7277` | 17.626 | 0.948 | none | none |
| `pytest-dev__pytest-10051` | 12.898 | 1.011 | none | none |
| `pytest-dev__pytest-5787` | 10.289 | 0.661 | none | none |
| `pytest-dev__pytest-5809` | 0.326 | 0.140 | none | none |
| `pytest-dev__pytest-6202` | 18.721 | 1.462 | none | none |
| `pytest-dev__pytest-7236` | 2.242 | 0.175 | none | none |
| `pytest-dev__pytest-7432` | 10.322 | 0.855 | none | none |
| `pytest-dev__pytest-7521` | 6.110 | 0.283 | none | none |
| `scikit-learn__scikit-learn-10908` | 1.139 | 0.631 | none | none |
| `scikit-learn__scikit-learn-12585` | 93.188 | 13.845 | 30, 60 | 30, 60 |
| `scikit-learn__scikit-learn-14141` | 0.869 | 0.394 | none | none |
| `scikit-learn__scikit-learn-14629` | 392.014 | 87.890 | 30, 60, 120, 300 | 30, 60, 120, 300 |
| `scikit-learn__scikit-learn-14894` | 242.082 | 47.458 | 30, 60, 120 | 30, 60, 120 |
| `sphinx-doc__sphinx-10323` | 2.419 | 0.361 | none | none |
| `sphinx-doc__sphinx-10435` | 8.087 | 0.732 | none | none |
| `sphinx-doc__sphinx-10466` | 26.909 | 5.389 | none | 30 |
| `sphinx-doc__sphinx-7910` | 0.446 | 0.428 | none | none |
| `sympy__sympy-13480` | 1104.188 | 8.739 | 30, 60, 120, 300 | 30, 60, 120, 300 |
| `sympy__sympy-14711` | 297.946 | 9.535 | 30, 60, 120 | 30, 60, 120, 300 |
| `sympy__sympy-17318` | 26.368 | 0.529 | none | none |
| `sympy__sympy-19783` | 445.888 | 14.720 | 30, 60, 120, 300 | 30, 60, 120, 300 |
| `sympy__sympy-24562` | 1771.837 | 8.352 | 30, 60, 120, 300 | 30, 60, 120, 300 |

No aggregate regression rate is reported over the seven cases. The reading uses the registered integer coverage threshold and task medians only. Nonbinding budgets provide no budget-pressure evidence. No extrapolation beyond these cases. Synthetic unit checks are supplied but were not executed, as requested. No Docker, benchmark execution, model calls, correctness labels or oracle inputs. Phase 6b was not started.
