# Phase 11: batch 1 gold run

Status: ⛔ FAILED: audit.

Verify-only run of the 60 test batch 1 gold (reference) patches with V4 generated fresh (one pass, Phase 4b prompts; [V4_FREEZE.md](../V4_FREEZE.md)) and v1.5 frozen ([V1_5_FREEZE.md](../V1_5_FREEZE.md)), `--mode audited --freeze-tag v1.5-frozen`, HEAD `569bb7fc2e4cd860dbbc0fdd54c838d208af3b11`, git_dirty false. No test-set label was opened. Gold-patch lines are never shown.

The run ended with status `COMPLETE`. The seal check is `MATCH` over 3182 files; seal sha256 `8776eb8e24dfe2e4448823177136f4f83774e936cff76893796a54d8efdf8d12`. The ledger records 1742 calls for this job, 0 unsettled.

## Gates (as in Phase 6, fixed before launch)

| Gate | Rule | Measured | Result |
|---|---|---|---|
| Sealed | run COMPLETE and seal matches | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Ledger | job and DeepSeek account total within the cap, nothing unsettled | job $2.0360, account $4.4098, cap $5.3739, 0 unsettled | ✅ pass |
| Audit | A3 leakage audit exit 0 | exit 1; confirmed: GOLD_LINE_LEAK 5 | ⛔ fail |
| Infrastructure | errors on ≤ 2 of 60 tasks | 0 (none) | ✅ pass |

An infrastructure error is a task that did not complete, has an infrastructure flag, has no record, or has V4 absence `error` (PILOT.md definition).

**This run failed: audit. Nothing was restarted.**

## Per task (gold patches, label-free)

Format as in DEV_GOLD.md. Decisions come from `scripts/decide_v1_5.py --frozen` (tag v1.5-frozen).

| instance_id | repo | reqs | kept p1/p2 | verdicts | V4 full pass | V2 (P) | decision | rule | min | cost |
|---|---|---:|---:|---|---|---|---|---|---:|---:|
| pydata__xarray-4356 | pydata/xarray | 2 | 2/0 | R1:PASS, R2:FAIL_SINGLE | no | NOT_AVAILABLE | FLAG | R4 | 1.1 | $0.0092 |
| sympy__sympy-22714 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 17.4 | $0.0138 |
| sympy__sympy-14248 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:FAIL_SINGLE, R3:FAIL_SINGLE | no | FAIL | REJECT | R3 | 12.8 | $0.0400 |
| django__django-15695 | django/django | 2 | 2/0 | R1:FAIL_SINGLE, R2:PASS | no | NOT_AVAILABLE | FLAG | R4 | 5.7 | $0.0514 |
| django__django-12273 | django/django | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | NOT_AVAILABLE | FLAG | R4 | 7.3 | $0.0667 |
| django__django-14539 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 2.9 | $0.0165 |
| sympy__sympy-22456 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:FAIL_SINGLE, R3:PASS | no | NOT_AVAILABLE | FLAG | R4 | 9.6 | $0.0248 |
| matplotlib__matplotlib-26342 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | FAIL | FLAG | R5 | 10.5 | $0.0151 |
| django__django-14559 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 2.6 | $0.0105 |
| django__django-11951 | django/django | 2 | 1/0 | R1:PASS, R2:UNCOVERED | no | PASS | ACCEPT | R6b | 4.2 | $0.0407 |
| astropy__astropy-13453 | astropy/astropy | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 13.7 | $0.0200 |
| django__django-12419 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 1.8 | $0.0088 |
| matplotlib__matplotlib-25960 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 6.2 | $0.0284 |
| astropy__astropy-12907 | astropy/astropy | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 1.6 | $0.0068 |
| django__django-13925 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 12.6 | $0.0504 |
| scikit-learn__scikit-learn-25931 | scikit-learn/scikit-learn | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 40.2 | $0.0073 |
| django__django-15863 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 2.2 | $0.0122 |
| django__django-14434 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 2.9 | $0.0240 |
| django__django-13343 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 7.9 | $0.0206 |
| django__django-13449 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 8.1 | $0.0504 |
| pydata__xarray-7229 | pydata/xarray | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 17.5 | $0.0093 |
| pydata__xarray-6721 | pydata/xarray | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 3.3 | $0.0380 |
| django__django-11451 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 62.4 | $0.0260 |
| django__django-16801 | django/django | 2 | 1/0 | R1:PASS, R2:UNCOVERED | no | PASS | ACCEPT | R6b | 3.2 | $0.0301 |
| django__django-17084 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 5.4 | $0.0528 |
| sympy__sympy-15017 | sympy/sympy | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 3.1 | $0.0046 |
| sympy__sympy-20590 | sympy/sympy | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 4.1 | $0.0148 |
| django__django-11149 | django/django | 4 | 0/0 | R1:UNCOVERED, R2:UNCOVERED, R3:UNCOVERED, R4:UNCOVERED | no | PASS | FLAG | R7 | 8.5 | $0.1818 |
| sphinx-doc__sphinx-9591 | sphinx-doc/sphinx | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 1.5 | $0.0295 |
| django__django-11333 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 7.9 | $0.0424 |
| django__django-13346 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 3.9 | $0.0485 |
| django__django-13109 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 2.9 | $0.0149 |
| astropy__astropy-7671 | astropy/astropy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 4.4 | $0.0248 |
| astropy__astropy-13236 | astropy/astropy | 4 | 4/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE, R4:FAIL_SINGLE | no | PASS | FLAG | R4 | 3.7 | $0.0328 |
| sympy__sympy-17630 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 6.7 | $0.0555 |
| scikit-learn__scikit-learn-12973 | scikit-learn/scikit-learn | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 20.7 | $0.0168 |
| django__django-10554 | django/django | 3 | 0/0 | R1:UNCOVERED, R2:UNCOVERED, R3:UNCOVERED | no | PASS | FLAG | R7 | 14.5 | $0.2415 |
| django__django-12039 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 7.2 | $0.0251 |
| django__django-13512 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 5.2 | $0.0274 |
| django__django-12193 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 3.4 | $0.0284 |
| sympy__sympy-14531 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 3.2 | $0.0145 |
| django__django-12308 | django/django | 2 | 2/0 | R1:PASS, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 5.3 | $0.0398 |
| pydata__xarray-3151 | pydata/xarray | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 2.6 | $0.0247 |
| sphinx-doc__sphinx-9658 | sphinx-doc/sphinx | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 4.9 | $0.0485 |
| scikit-learn__scikit-learn-25973 | scikit-learn/scikit-learn | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 40.2 | $0.0131 |
| sympy__sympy-12096 | sympy/sympy | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 3.2 | $0.0123 |
| sphinx-doc__sphinx-8035 | sphinx-doc/sphinx | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 9.5 | $0.1135 |
| sphinx-doc__sphinx-8269 | sphinx-doc/sphinx | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 1.3 | $0.0206 |
| sympy__sympy-23262 | sympy/sympy | 2 | 1/0 | R1:PASS, R2:UNCOVERED | no | PASS | ACCEPT | R6b | 4.4 | $0.0150 |
| sympy__sympy-23824 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 4.9 | $0.0213 |
| django__django-15957 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 5.9 | $0.0449 |
| pydata__xarray-3677 | pydata/xarray | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 33.1 | $0.0067 |
| django__django-11728 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 1.0 | $0.0088 |
| django__django-13401 | django/django | 4 | 4/0 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 6.8 | $0.0545 |
| pydata__xarray-7393 | pydata/xarray | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 12.0 | $0.0131 |
| django__django-14534 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | FAIL | FLAG | R5 | 5.3 | $0.0188 |
| sympy__sympy-13551 | sympy/sympy | 2 | 2/0 | R1:FAIL_SINGLE, R2:PASS | no | PASS | FLAG | R4 | 4.9 | $0.0343 |
| sympy__sympy-15809 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 2.9 | $0.0090 |
| pydata__xarray-4687 | pydata/xarray | 3 | 3/0 | R1:FAIL_SINGLE, R2:PASS, R3:FAIL_SINGLE | no | PASS | FLAG | R4 | 13.2 | $0.0496 |
| django__django-14493 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 2.0 | $0.0103 |

## Totals

- Minutes: total 527.3, median 5.2 per task, max 62.4.
- DeepSeek cost: $2.0360 total, $0.0339 per task.
- Gold V4 full passes: 46 of 60. Gold with any V4 FAIL: 9 of 60.
- Gold decisions, frozen switches (tag v1.5-frozen): ACCEPT 39, FLAG 20, REJECT 1.
- Recall (A3, recorded): 39 model-written gold lines in 22 tasks (96 messages); 0 gold lines in kept frozen tests (0 tasks); 5 leak lines. Per-task hashes: [test_gold_b1_recall.json](test_gold_b1_recall.json).
- Generator fingerprints: 1742 responses in 120 conversation files; 1742 match the pin `bc19ba97cbe016479903222bb1578db6`, 0 do not (bc19ba97cbe016479903222bb1578db6 1742).

Machine-readable results: `reports/study_v1_5/test_gold_b1/test_gold_b1_results.json`.

## Addendum, 22 Nov 2026: re-audit under amendment B11

The audit gate above failed on 5 GOLD_LINE_LEAK lines in `astropy__astropy-7671` (requirements conversation, message 10). They come from `git show` of commits that are ancestors of the task's base commit. Amendment B11 ([AMENDMENT_2026-11-21b.md](../AMENDMENT_2026-11-21b.md)) records such lines as BASE_HISTORY.

The audit was re-run read-only on the sealed run (`runs/study_test_gold_b1`, unchanged): **exit 0**, 5 BASE_HISTORY lines, all in astropy-7671 (sha256 `25486da2…`, `9bbd4487…`, `cbcc8441…`, `2609f67b…`, `265cfc95…`), **0 leaks**; every other task's summary is unchanged (log `runs/study_v1_5/phase11_reaudit_b11.log`). **The audit gate now passes**, so all four gates pass: sealed ✅, ledger ✅ $2.036 (cap $5.3739), audit ✅, infrastructure ✅ 0 error tasks.

astropy-7671's two kept frozen tests contain none of the lines, and it is excluded from the headline (B11). Its decision is unchanged.
