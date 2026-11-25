# Study v1.5 Phase 16: failure modes (RQ5)

*Pre-specified in PLAN §6; computed after labels were joined; not used to choose any rule.*

Headline scope, frozen rules (tag `v1.5-frozen-2`). Pooled = gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash. Test names only; no patch or test-file contents.

## a. Every false ACCEPT

9 wrong patches were ACCEPTed. For each: the rule, the signals, the wrong-patch type, the tests the official grader saw fail, and why the verifier's signals did not catch it.

| system | task | repo | rule | V2 | V4 pass / uncovered | type | FAIL_TO_PASS failed | PASS_TO_PASS failed | why not caught |
|---|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4 | django__django-11728 | django/django | R6 | PASS | 2 / 0 | X | test_simplify_regex (admin_docs.test_views.AdminDocViewFunctionsTests) | test_builtin_fields (admin_docs.test_views.TestFieldType) | V2 PASS on the 7 tests it ran, none of them a PASS_TO_PASS test the grader saw fail (matched by test name); V4 passed 2 requirement(s) |
| claude-sonnet-4 | django__django-12308 | django/django | R6 | PASS | 2 / 0 | U | test_json_display_for_field (admin_utils.tests.UtilsTests), test_label_for_field (admin_utils.tests.UtilsTests) | — | the official failures are FAIL_TO_PASS only; V4 passed 2 requirement(s) (0 uncovered) without catching the missing behaviour; V2 PASS on the 30 tests it ran |
| claude-sonnet-4 | django__django-14534 | django/django | R6 | PASS | 2 / 0 | U | test_iterable_boundfield_select (forms_tests.tests.test_forms.FormsTestCase) | — | the official failures are FAIL_TO_PASS only; V4 passed 2 requirement(s) (0 uncovered) without catching the missing behaviour; V2 PASS on the 452 tests it ran |
| gemini-2.5-flash | django__django-13568 | django/django | R6b | PASS | 2 / 1 | R | — | test_username_partially_unique (auth_tests.test_checks.UserModelChecksTests) | V2 PASS on the 12 tests it ran, none of them a PASS_TO_PASS test the grader saw fail (matched by test name); V4 passed 2 requirement(s) |
| gpt-4.1-mini | django__django-11728 | django/django | R6 | NOT_AVAILABLE (nothing_to_check) | 2 / 0 | X | test_simplify_regex (admin_docs.test_views.AdminDocViewFunctionsTests), test_app_not_found (admin_docs.test_views.TestModelDetailView) | test_builtin_fields (admin_docs.test_views.TestFieldType), test_custom_fields (admin_docs.test_views.TestFieldType), test_field_name (admin_docs.test_views.TestFieldType), test_descriptions_render_correctly (admin_docs.test_views.TestModelDetailView) and 40 more | V2 had nothing to check (no test selected), none of them a PASS_TO_PASS test the grader saw fail (matched by test name); V4 passed 2 requirement(s) |
| gpt-4.1-mini | django__django-13109 | django/django | R6 | NOT_AVAILABLE (incomplete) | 3 / 0 | R | — | test_validate_foreign_key_uses_default_manager (model_forms.tests.ModelFormBasicTests) | V2 NOT_AVAILABLE (incomplete) on the 3115 tests it ran, none of them a PASS_TO_PASS test the grader saw fail (matched by test name); V4 passed 3 requirement(s) |
| gpt-4.1-mini | django__django-13551 | django/django | R6b | PASS | 1 / 1 | U | Updating the user email address invalidates the token., test_token_with_different_secret (auth_tests.test_tokens.TokenGeneratorTest) | — | the official failures are FAIL_TO_PASS only; V4 passed 1 requirement(s) (1 uncovered) without catching the missing behaviour; V2 PASS on the 20 tests it ran |
| gpt-4.1-mini | sympy__sympy-15017 | sympy/sympy | R6 | NOT_AVAILABLE (nothing_to_check) | 1 / 0 | X | test_ndim_array_initiation | test_ndim_array_converting, test_converting_functions | V2 had nothing to check (no test selected), none of them a PASS_TO_PASS test the grader saw fail (matched by test name); V4 passed 1 requirement(s) |
| gpt-4.1-mini | sympy__sympy-23824 | sympy/sympy | R6 | PASS | 2 / 0 | unknown | — | — | the grader could not apply the patch (patch_successfully_applied false), so there is no per-test status; our verifier applied it; V2 PASS on the 4 tests it ran; V4 passed 2 requirement(s) |

## b. Wrong-patch type × decision

Wrong patches by type (U: a FAIL_TO_PASS test does not pass, no PASS_TO_PASS fails; R: all FAIL_TO_PASS pass, a PASS_TO_PASS fails; X: both; unknown: no per-test status). It shows which kinds of wrong patch the verifier holds back. Sources: official report.json (claude-sonnet-4) 57, official report.json (claude-sonnet-4_b2) 45, official report.json (gemini-2.5-flash) 35, official report.json (gemini-2.5-flash_b2) 30, our grader (gpt-4.1-mini_ours) 55, our grader (gpt-4.1-mini_b2) 43. Unknown includes 24 wrong patches the grader could not apply (gpt-4.1-mini/astropy__astropy-13453, gpt-4.1-mini/django__django-10554, gpt-4.1-mini/django__django-11885, gpt-4.1-mini/django__django-12039, gpt-4.1-mini/django__django-12308, gpt-4.1-mini/django__django-13343, gpt-4.1-mini/django__django-13401, gpt-4.1-mini/django__django-14007, gpt-4.1-mini/django__django-14351, gpt-4.1-mini/django__django-14434, gpt-4.1-mini/django__django-14539, gpt-4.1-mini/django__django-14559, gpt-4.1-mini/django__django-15695, gpt-4.1-mini/django__django-15863, gpt-4.1-mini/django__django-15957, gpt-4.1-mini/django__django-16801, gpt-4.1-mini/pydata__xarray-4687, gpt-4.1-mini/pydata__xarray-6721, gpt-4.1-mini/pydata__xarray-7229, gpt-4.1-mini/pydata__xarray-7393, gpt-4.1-mini/sympy__sympy-12096, gpt-4.1-mini/sympy__sympy-13372, gpt-4.1-mini/sympy__sympy-14248, gpt-4.1-mini/sympy__sympy-23824).

| scope | type | ACCEPT | FLAG | REJECT |
|---|---|---:|---:|---:|
| pooled | R | 2 | 7 | 3 |
| pooled | U | 3 | 35 | 26 |
| pooled | X | 3 | 13 | 35 |
| pooled | unknown | 1 | 6 | 17 |
| claude-sonnet-4 | R | 0 | 2 | 1 |
| claude-sonnet-4 | U | 2 | 12 | 12 |
| claude-sonnet-4 | X | 1 | 1 | 2 |
| gemini-2.5-flash | R | 1 | 2 | 0 |
| gemini-2.5-flash | U | 0 | 7 | 5 |
| gemini-2.5-flash | X | 0 | 5 | 22 |
| gpt-4.1-mini | R | 1 | 3 | 2 |
| gpt-4.1-mini | U | 1 | 16 | 9 |
| gpt-4.1-mini | X | 2 | 7 | 11 |
| gpt-4.1-mini | unknown | 1 | 6 | 17 |

## c. Per repository (pooled)

Decisions on correct and wrong patches per repository; it shows where the verifier is accurate and where it holds back or lets through most.

| repo | ACCEPT c/w | FLAG c/w | REJECT c/w |
|---|---|---|---|
| astropy/astropy | 0/0 | 0/0 | 3/5 |
| django/django | 25/7 | 25/33 | 4/41 |
| matplotlib/matplotlib | 0/0 | 3/3 | 0/5 |
| pydata/xarray | 2/0 | 5/7 | 1/4 |
| pytest-dev/pytest | 6/0 | 0/1 | 1/0 |
| scikit-learn/scikit-learn | 6/0 | 5/3 | 0/5 |
| sphinx-doc/sphinx | 0/0 | 0/0 | 7/15 |
| sympy/sympy | 10/2 | 11/14 | 0/6 |

## d. git_peek sensitivity

The headline minus the (system, task) pairs listed in each system's git_peek_suspicious_commits.md (4 scored pairs removed). It shows whether trajectories that peeked at git history drive the result.

- gpt-4.1-mini: 2 listed; in headline scope: django__django-13513; `reports/study_v1_5/results/git_peek/gpt-4.1-mini/git_peek_suspicious_commits.md` sha256 `4f313ab983c2f3779acfea71a65e40a9fa86b2035f315e566f689fd7063338ac` (from https://raw.githubusercontent.com/SWE-bench/experiments/main/evaluation/verified/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/git_peek_suspicious_commits.md).
- claude-sonnet-4: 13 listed; in headline scope: django__django-13513; `reports/study_v1_5/results/git_peek/claude-sonnet-4/git_peek_suspicious_commits.md` sha256 `5ace9abcb21ffe1c45e391d68f2cc1200e2224d6090b9b3020d0897edfbae800` (from https://raw.githubusercontent.com/SWE-bench/experiments/main/evaluation/verified/20250726_mini-v1.0.0_claude-sonnet-4-20250514/git_peek_suspicious_commits.md).
- gemini-2.5-flash: 6 listed; in headline scope: django__django-12143, pydata__xarray-3151, sympy__sympy-21930; `reports/study_v1_5/results/git_peek/gemini-2.5-flash/git_peek_suspicious_commits.md` sha256 `f24e4954ae82eafa7d0bfaccdb440ecce68a6bfa46cb2f96d46a3aa9a8ab92ff` (from https://raw.githubusercontent.com/SWE-bench/experiments/main/evaluation/verified/20250726_mini-v1.0.0_gemini-2.5-flash/git_peek_suspicious_commits.md).

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| minus git_peek pairs (pooled) | 261 | 42.9% [37.1%, 49.0%] | 84.2% [72.6%, 91.5%] | 1.96 | 1.86 | 42.9% [34.1%, 52.1%] | 6.0% [3.2%, 11.1%] | 54.4% [46.4%, 62.2%] | 13.4% [8.3%, 20.9%] | 41.4% [35.6%, 47.4%] | 36.8% [26.7%, 46.5%] | 6.68e-13  H1 [30.6%, 51.6%] ✓; H2 [25.1%, 48.3%] ✓ |
| v1.5 frozen: claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 88.0% [70.0%, 95.8%] | 1.30 | 1.30 | 31.9% [22.1%, 43.6%] | 9.1% [3.1%, 23.6%] | 45.5% [29.8%, 62.0%] | 13.0% [7.0%, 23.0%] | 52.0% [42.4%, 61.4%] | 22.8% [5.3%, 35.9%] | 0.0137  n/a |
| v1.5 frozen: gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 93.3% [70.2%, 98.8%] | 2.64 | 2.64 | 60.9% [40.8%, 77.8%] | 2.4% [0.4%, 12.3%] | 64.3% [49.2%, 77.0%] | 17.4% [7.0%, 37.1%] | 29.2% [19.6%, 41.2%] | 58.5% [36.1%, 75.6%] | 1.68e-07  n/a |
| v1.5 frozen: gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 72.2% [49.1%, 87.5%] | 3.22 | 3.22 | 59.1% [38.7%, 76.7%] | 6.6% [2.8%, 14.5%] | 51.3% [40.3%, 62.2%] | 13.6% [4.7%, 33.3%] | 38.8% [29.7%, 48.7%] | 52.5% [30.7%, 70.6%] | 4.67e-07  n/a |
| minus git_peek pairs: claude-sonnet-4 | 101 | 68.3% [58.7%, 76.6%] | 88.0% [70.0%, 95.8%] | 1.29 | 1.29 | 31.9% [22.1%, 43.6%] | 9.4% [3.2%, 24.2%] | 46.9% [30.9%, 63.6%] | 13.0% [7.0%, 23.0%] | 51.5% [41.9%, 61.0%] | 22.5% [4.7%, 35.7%] | 0.0145  n/a |
| minus git_peek pairs: gemini-2.5-flash | 62 | 33.9% [23.3%, 46.3%] | 92.9% [68.5%, 98.7%] | 2.74 | 2.74 | 61.9% [40.9%, 79.2%] | 2.4% [0.4%, 12.6%] | 65.9% [50.5%, 78.4%] | 14.3% [5.0%, 34.6%] | 29.0% [19.2%, 41.3%] | 59.5% [36.1%, 76.9%] | 2.91e-07  n/a |
| minus git_peek pairs: gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 72.2% [49.1%, 87.5%] | 3.22 | 3.22 | 59.1% [38.7%, 76.7%] | 6.6% [2.8%, 14.5%] | 51.3% [40.3%, 62.2%] | 13.6% [4.7%, 33.3%] | 38.8% [29.7%, 48.7%] | 52.5% [30.7%, 70.6%] | 4.67e-07  n/a |

## e. V4 generator audit (A3 recall)

Gold tasks where the V4 generator wrote a gold-patch line itself (recall, recorded under A3; not a leak).

- batch 1: 22 of 60 tasks with recall (`reports/study_v1_5/test_gold_b1/test_gold_b1_recall.json`): astropy__astropy-13453, django__django-11951, django__django-12039, django__django-12193, django__django-12308, django__django-12419, django__django-13109, django__django-13343, django__django-13346, django__django-13401, django__django-13449, django__django-13512, django__django-14534, django__django-14539, django__django-14559, django__django-15957, django__django-16801, django__django-17084, pydata__xarray-4687, pydata__xarray-6721, scikit-learn__scikit-learn-12973, sphinx-doc__sphinx-8035.
- batch 2: 20 of 48 tasks with recall (`reports/study_v1_5/test_gold_b2/test_gold_b2_recall.json`): django__django-11239, django__django-11265, django__django-11734, django__django-13513, django__django-13551, django__django-13568, django__django-13837, django__django-16642, django__django-16662, django__django-16899, django__django-16950, mwaskom__seaborn-3187, pylint-dev__pylint-6386, pytest-dev__pytest-8399, scikit-learn__scikit-learn-13439, scikit-learn__scikit-learn-14053, scikit-learn__scikit-learn-25232, sphinx-doc__sphinx-9698, sphinx-doc__sphinx-9711, sympy__sympy-16792.

No-recall sensitivity is in results_final.md, scope 'sensitivity: headline minus tasks with generator recall': pooled n 163, ACCEPT precision 89.5% [75.9%, 95.8%], coverage 49.3% [37.8%, 60.8%], false-accept rate 4.3% [1.7%, 10.4%]; H1 [33.9%, 60.2%] ✓; H2 [29.1%, 59.9%] ✓.

## f. Empty-patch sensitivity (PLAN §6)

Every empty patch counted as a wrong patch held back (decision REJECT). It shows how much leaving empty patches out flatters the headline. Empty patches in the headline scope: gpt-4.1-mini 2, claude-sonnet-4 0, gemini-2.5-flash 5.

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| empty = wrong, REJECT (pooled) | 272 | 41.9% [36.2%, 47.8%] | 84.5% [73.1%, 91.6%] | 2.02 | 1.90 | 43.0% [34.3%, 52.2%] | 5.7% [3.0%, 10.5%] | 55.7% [47.9%, 63.2%] | 14.0% [8.8%, 21.6%] | 40.4% [34.8%, 46.4%] | 37.3% [27.4%, 46.8%] | 8.19e-14  H1 [32.0%, 52.9%] ✓; H2 [25.5%, 48.8%] ✓ |
| v1.5 frozen: claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 88.0% [70.0%, 95.8%] | 1.30 | 1.30 | 31.9% [22.1%, 43.6%] | 9.1% [3.1%, 23.6%] | 45.5% [29.8%, 62.0%] | 13.0% [7.0%, 23.0%] | 52.0% [42.4%, 61.4%] | 22.8% [5.3%, 35.9%] | 0.0137  n/a |
| v1.5 frozen: gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 93.3% [70.2%, 98.8%] | 2.64 | 2.64 | 60.9% [40.8%, 77.8%] | 2.4% [0.4%, 12.3%] | 64.3% [49.2%, 77.0%] | 17.4% [7.0%, 37.1%] | 29.2% [19.6%, 41.2%] | 58.5% [36.1%, 75.6%] | 1.68e-07  n/a |
| v1.5 frozen: gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 72.2% [49.1%, 87.5%] | 3.22 | 3.22 | 59.1% [38.7%, 76.7%] | 6.6% [2.8%, 14.5%] | 51.3% [40.3%, 62.2%] | 13.6% [4.7%, 33.3%] | 38.8% [29.7%, 48.7%] | 52.5% [30.7%, 70.6%] | 4.67e-07  n/a |
| empty = wrong, REJECT: claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 88.0% [70.0%, 95.8%] | 1.30 | 1.30 | 31.9% [22.1%, 43.6%] | 9.1% [3.1%, 23.6%] | 45.5% [29.8%, 62.0%] | 13.0% [7.0%, 23.0%] | 52.0% [42.4%, 61.4%] | 22.8% [5.3%, 35.9%] | 0.0137  H1 [7.1%, 33.3%] ✓; H2 [7.8%, 37.5%] ✓ |
| empty = wrong, REJECT: gemini-2.5-flash | 70 | 32.9% [23.0%, 44.5%] | 93.3% [70.2%, 98.8%] | 2.84 | 2.84 | 60.9% [40.8%, 77.8%] | 2.1% [0.4%, 11.1%] | 68.1% [53.8%, 79.6%] | 17.4% [7.0%, 37.1%] | 27.1% [18.1%, 38.5%] | 58.7% [36.7%, 75.8%] | 5.39e-08  H1 [45.2%, 74.3%] ✓; H2 [37.0%, 79.2%] ✓ |
| empty = wrong, REJECT: gpt-4.1-mini | 100 | 22.0% [15.0%, 31.1%] | 72.2% [49.1%, 87.5%] | 3.28 | 3.28 | 59.1% [38.7%, 76.7%] | 6.4% [2.8%, 14.1%] | 52.6% [41.6%, 63.3%] | 13.6% [4.7%, 33.3%] | 38.0% [29.1%, 47.8%] | 52.7% [30.9%, 70.7%] | 3.58e-07  H1 [31.1%, 69.7%] ✓; H2 [30.4%, 73.9%] ✓ |
