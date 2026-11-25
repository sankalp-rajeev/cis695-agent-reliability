# Study v1.5 Phase 16: ablations (RQ3, RQ4)

*Pre-specified in PLAN §6; computed after labels were joined; not used to choose any rule.*

Headline scope throughout (results_final.md). Decisions: v1.5 with the switches at tag `v1.5-frozen-2` (`26d42df0fd70`) unless a row says otherwise. Pooled = gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash. Bootstrap: task-clustered, 10000 resamples, seed 20261126. Each table starts with the v1.5 frozen row.

## Gate G1

Frozen and V1+V2 decision counts recomputed here equal results_final.json per system and pooled: **pass** (8/8 checks; own decide() differs on 0 patches).

- frozen gpt-4.1-mini: A 13/5, F 6/32, R 3/39 (correct/wrong) — match
- frozen claude-sonnet-4: A 22/3, F 38/15, R 9/15 (correct/wrong) — match
- frozen gemini-2.5-flash: A 14/1, F 5/14, R 4/27 (correct/wrong) — match
- frozen pooled: A 49/9, F 49/61, R 16/81 (correct/wrong) — match
- v1v2 gpt-4.1-mini: A 7/9, F 11/42, R 4/25 (correct/wrong) — match
- v1v2 claude-sonnet-4: A 17/5, F 43/11, R 9/17 (correct/wrong) — match
- v1v2 gemini-2.5-flash: A 9/4, F 10/21, R 4/17 (correct/wrong) — match
- v1v2 pooled: A 33/18, F 64/74, R 17/59 (correct/wrong) — match

## 1. Signal drop-outs (RQ3)

Each signal forced to PASS in turn (V1 also clears apply, manipulation, risk and incomplete-analysis flags; V3 also clears the absolute-failure flag; V4 becomes a full pass), decided with the frozen rules. This shows how much each signal contributes: a row close to the frozen row means that signal changes little.

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| V1 forced PASS (32 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 85.7% [76.7%, 91.6%] | 1.99 | 1.68 | 63.2% [54.0%, 71.4%] | 7.9% [4.6%, 13.4%] | 49.0% [41.2%, 56.9%] | 10.5% [6.1%, 17.5%] | 35.8% [30.3%, 41.8%] | 55.2% [44.6%, 64.2%] | 1.63e-22  H1 [34.5%, 50.9%] ✓; H2 [42.9%, 67.3%] ✓ |
| V2 forced PASS (50 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 70.7% [60.7%, 79.0%] | 1.64 | 1.60 | 57.0% [47.8%, 65.7%] | 17.9% [12.6%, 24.8%] | 43.0% [35.4%, 51.0%] | 14.0% [8.8%, 21.6%] | 34.7% [29.2%, 40.6%] | 39.1% [27.7%, 49.3%] | 3.6e-11  H1 [18.4%, 37.3%] ✓; H2 [26.5%, 51.5%] ✓ |
| V3 forced PASS (41 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 85.2% [74.3%, 92.0%] | 1.98 | 1.86 | 45.6% [36.8%, 54.8%] | 6.0% [3.2%, 10.9%] | 29.1% [22.5%, 36.8%] | 10.5% [6.1%, 17.5%] | 55.8% [49.8%, 61.7%] | 39.7% [29.5%, 49.2%] | 1.79e-14  H1 [32.3%, 52.0%] ✓; H2 [27.9%, 51.1%] ✓ |
| V4 forced PASS (43 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 65.9% [55.3%, 75.1%] | 1.53 | 1.55 | 49.1% [40.1%, 58.2%] | 19.2% [13.7%, 26.2%] | 43.0% [35.4%, 51.0%] | 14.0% [8.8%, 21.6%] | 37.4% [31.8%, 43.3%] | 29.9% [18.5%, 40.5%] | 3.27e-07  H1 [14.1%, 31.5%] ✓; H2 [18.0%, 42.1%] ✓ |

## 2. With vs without the V2 fallback (RQ3)

Frozen rules with the fallback-selected V2 tests removed (decide_v1_5.without_v2_fallback). The fallback ran on 0 headline patches; removing it changes the V2 outcome on 0 and the decision on 0 scored patches; 0 could not be recomputed.

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| without V2 fallback (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |

## 3. Old vs per-requirement V4 on arm B (RQ3)

Arm B's 51 gpt-4.1-mini dev patches with arm B's dev labels (25 correct, 26 wrong), as in ADOPTION.md. v1.5 with switches off, once with the stored old (legacy) V4 signals and once with the new per-requirement V4; the first row is v1.5 frozen with the new V4. Task sources follow amendment B12 (adoption_b12.json): runs/study_dev_armb 11, runs/study_dev_armb_2 39, runs/study_dev_armb_3 1. Dev data, so one patch per task.

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen, new V4 (pooled) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06  H1 [20.7%, 49.7%] ✓; H2 [41.7%, 84.3%] ✓ |
| switches off, old V4 (pooled) | 51 | 49.0% [35.9%, 62.3%] | 80.0% [58.4%, 91.9%] | 1.63 | 1.63 | 64.0% [44.5%, 79.8%] | 15.4% [6.2%, 33.5%] | 15.4% [6.2%, 33.5%] | 0.0% [0.0%, 13.3%] | 52.9% [39.5%, 65.9%] | 48.6% [22.0%, 66.9%] | 0.000531  H1 [15.4%, 47.8%] ✓; H2 [24.4%, 71.5%] ✓ |
| switches off, new V4 (pooled) | 51 | 49.0% [35.9%, 62.3%] | 81.2% [57.0%, 93.4%] | 1.66 | 1.66 | 52.0% [33.5%, 70.0%] | 11.5% [4.0%, 29.0%] | 19.2% [8.5%, 37.9%] | 0.0% [0.0%, 13.3%] | 58.8% [45.2%, 71.2%] | 40.5% [15.0%, 59.9%] | 0.00253  H1 [13.7%, 51.0%] ✓; H2 [16.7%, 63.0%] ✓ |

Cross-check against adoption_b12.json: switches off new V4 equal, old V4 equal, frozen new V4 vs adopted equal. Decisions that change from old to new V4: 5 (django__django-13807, django__django-13820, django__django-15103, matplotlib__matplotlib-25287, pytest-dev__pytest-7432).

## 4. V2 accountings S/C/P (RQ4)

V2 recomputed from each task's stored per-accounting reports (verification/v2_policies.json, sealed), then decided with the frozen rules. The frozen v1.5 runs used P_invalid_excluded (199 tasks) as primary (PROTOCOL change 1, configs/verifier/v1_5.yaml `v2_primary_accounting`); the Phase 16 prompt names S_invalid_excluded as primary, so both are marked. Replaying the stored primary reproduces the stored V2 evidence on every task except 0 (none), which keep the frozen decision. 91 headline patches have no V2 reports (V2 never ran), so they are the same under every accounting.

| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | bootstrap H1 / H2 (95% CI, supported) |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|
| v1.5 frozen (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| S_invalid_excluded [prompt primary] (3 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 83.6% [71.7%, 91.1%] | 1.94 | 1.82 | 40.4% [31.8%, 49.5%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 42.6% [36.8%, 48.7%] | 34.4% [24.5%, 44.0%] | 5.43e-12  H1 [29.5%, 51.3%] ✓; H2 [22.3%, 46.5%] ✓ |
| S_invalid_missing (3 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 83.6% [71.7%, 91.1%] | 1.94 | 1.82 | 40.4% [31.8%, 49.5%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 42.6% [36.8%, 48.7%] | 34.4% [24.5%, 44.0%] | 5.43e-12  H1 [29.5%, 51.3%] ✓; H2 [22.3%, 46.5%] ✓ |
| C_invalid_excluded (0 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| C_invalid_missing (0 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| P_invalid_excluded [frozen primary] (0 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |
| P_invalid_missing (0 decisions change) (pooled) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13  H1 [30.9%, 51.7%] ✓; H2 [25.3%, 48.6%] ✓ |

S_invalid_excluded changes: gemini-2.5-flash/django__django-16801 ACCEPT → FLAG (correct); gemini-2.5-flash/sympy__sympy-23262 ACCEPT → FLAG (correct); gpt-4.1-mini/sympy__sympy-23262 ACCEPT → FLAG (correct).

S_invalid_missing changes: gemini-2.5-flash/django__django-16801 ACCEPT → FLAG (correct); gemini-2.5-flash/sympy__sympy-23262 ACCEPT → FLAG (correct); gpt-4.1-mini/sympy__sympy-23262 ACCEPT → FLAG (correct).

## 5. Gold coverage ceiling (RQ4)

All 108 test-set gold patches (batches 1 and 2), frozen rules. Gold ACCEPTed: 69/108 = 63.9% [54.5%, 72.3%] (Wilson). FLAG 38, REJECT 1. Recomputed decisions and rules differ from decisions_frozen on 0 tasks (none). This is the ceiling on coverage: a correct patch that looks like gold is held back at least this often.

| cause (first matching rule) | count |
|---|---:|
| verifier fault (V4 test asserts the wrong thing) | 16 |
| verifier fault (R8: regression is NOT_AVAILABLE, not PASS) | 11 |
| superseded assertion | 7 |
| issue not reproducible as a test | 5 |
| second cause: no covering test | 3 |

Superseded assertions confirmed (every failing V2 test file is modified by the task's test_patch): 5 of 7.

The per-task list gives each gold FLAG or REJECT with its rule and cause.

| task | decision | rule | cause | second cause | confirmed |
|---|---|---|---|---|---|
| astropy__astropy-13236 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| astropy__astropy-13453 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-10554 | FLAG | R7 | issue not reproducible as a test |  |  |
| django__django-11149 | FLAG | R7 | issue not reproducible as a test |  |  |
| django__django-11265 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-11333 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-11451 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-11964 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-12039 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-12273 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) | no covering test |  |
| django__django-12308 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-12713 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-13410 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-13449 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| django__django-13513 | FLAG | R7 | issue not reproducible as a test |  |  |
| django__django-13551 | FLAG | R7 | issue not reproducible as a test |  |  |
| django__django-13837 | FLAG | R5 | superseded assertion |  | yes |
| django__django-14534 | FLAG | R5 | superseded assertion |  | yes |
| django__django-15022 | FLAG | R7 | issue not reproducible as a test | no covering test |  |
| django__django-15280 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-15695 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| django__django-16899 | FLAG | R5 | superseded assertion |  | yes |
| django__django-16950 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| matplotlib__matplotlib-26342 | FLAG | R5 | superseded assertion |  | no |
| matplotlib__matplotlib-26466 | FLAG | R5 | superseded assertion |  | no |
| pydata__xarray-4356 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) | no covering test |  |
| pydata__xarray-4687 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| scikit-learn__scikit-learn-14983 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| scikit-learn__scikit-learn-25232 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| scikit-learn__scikit-learn-25931 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| scikit-learn__scikit-learn-25973 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| sphinx-doc__sphinx-8548 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| sphinx-doc__sphinx-8638 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| sympy__sympy-13372 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| sympy__sympy-13551 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
| sympy__sympy-14248 | REJECT | R3 | superseded assertion |  | yes |
| sympy__sympy-15809 | FLAG | R8 | verifier fault (R8: regression is NOT_AVAILABLE, not PASS) |  |  |
| sympy__sympy-21930 | FLAG | R5 | superseded assertion |  | yes |
| sympy__sympy-22456 | FLAG | R4 | verifier fault (V4 test asserts the wrong thing) |  |  |
