# Phase 12b: batch 2 gold run

Status: ⛔ FAILED: audit.

Verify-only run of the 48 test batch 2 gold (reference) patches with V4 generated fresh (one pass, Phase 4b prompts; [V4_FREEZE.md](../V4_FREEZE.md)) and v1.5 frozen ([V1_5_FREEZE.md](../V1_5_FREEZE.md)), `--mode audited --freeze-tag v1.5-frozen-2`, HEAD `e7cfcadf52eb9de1a37791a6c6635f983a40984e`, git_dirty false. No test-set label was opened. Gold-patch lines are never shown.

The run ended with status `COMPLETE`. The seal check is `MATCH` over 2820 files; seal sha256 `ec51a00e11dd45299be287820f4331db3580cee4a5a51efec1ad3cbbd9ff8e34`. The ledger records 1550 calls for this job, 0 unsettled.

## Gates (as in Phase 6, fixed before launch)

| Gate | Rule | Measured | Result |
|---|---|---|---|
| Sealed | run COMPLETE and seal matches | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Ledger | job and DeepSeek account total within the cap, nothing unsettled | job $1.9282, account $6.3380, cap $7.4098, 0 unsettled | ✅ pass |
| Audit | A3 leakage audit exit 0 | exit 1; confirmed: newer-copy-path 1 | ⛔ fail |
| Infrastructure | errors on ≤ 2 of 48 tasks | 0 (none) | ✅ pass |

An infrastructure error is a task that did not complete, has an infrastructure flag, has no record, or has V4 absence `error` (PILOT.md definition).

**This run failed: audit. Nothing was restarted.**

## Per task (gold patches, label-free)

Format as in DEV_GOLD.md. Decisions come from `scripts/decide_v1_5.py --frozen` (tag v1.5-frozen (switches identical at v1.5-frozen-2)).

| instance_id | repo | reqs | kept p1/p2 | verdicts | V4 full pass | V2 (P) | decision | rule | min | cost |
|---|---|---:|---:|---|---|---|---|---|---:|---:|
| scikit-learn__scikit-learn-13496 | scikit-learn/scikit-learn | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 11.4 | $0.0285 |
| mwaskom__seaborn-3187 | mwaskom/seaborn | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 8.6 | $0.1206 |
| scikit-learn__scikit-learn-13439 | scikit-learn/scikit-learn | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 1.8 | $0.0081 |
| scikit-learn__scikit-learn-14053 | scikit-learn/scikit-learn | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 2.0 | $0.0187 |
| pytest-dev__pytest-7571 | pytest-dev/pytest | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 5.7 | $0.0154 |
| sphinx-doc__sphinx-9461 | sphinx-doc/sphinx | 4 | 4/0 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | PASS | ACCEPT | R6 | 7.9 | $0.0982 |
| django__django-16493 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 4.1 | $0.0227 |
| sympy__sympy-13372 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 64.4 | $0.0338 |
| sympy__sympy-20801 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 5.8 | $0.0169 |
| sphinx-doc__sphinx-8548 | sphinx-doc/sphinx | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 6.6 | $0.0852 |
| django__django-15280 | django/django | 3 | 3/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:PASS | no | PASS | FLAG | R4 | 2.6 | $0.0166 |
| django__django-14351 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 6.6 | $0.1053 |
| pytest-dev__pytest-8399 | pytest-dev/pytest | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 9.6 | $0.0292 |
| django__django-11734 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 8.5 | $0.0854 |
| scikit-learn__scikit-learn-25232 | scikit-learn/scikit-learn | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 20.7 | $0.0275 |
| django__django-15731 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 9.9 | $0.0215 |
| django__django-13410 | django/django | 4 | 4/0 | R1:PASS, R2:FAIL_SINGLE, R3:PASS, R4:FAIL_SINGLE | no | PASS | FLAG | R4 | 2.4 | $0.0075 |
| django__django-13551 | django/django | 2 | 1/0 | R1:NO_RESULT, R2:UNCOVERED | no | PASS | FLAG | R7 | 3.0 | $0.0213 |
| django__django-16899 | django/django | 1 | 1/0 | R1:PASS | yes | FAIL | FLAG | R5 | 4.9 | $0.0089 |
| django__django-12713 | django/django | 3 | 3/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE | no | PASS | FLAG | R4 | 2.6 | $0.0161 |
| django__django-11885 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 12.7 | $0.0325 |
| django__django-14007 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 32.3 | $0.0180 |
| sphinx-doc__sphinx-9698 | sphinx-doc/sphinx | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 1.2 | $0.0162 |
| pytest-dev__pytest-7205 | pytest-dev/pytest | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 3.7 | $0.0244 |
| django__django-13513 | django/django | 3 | 0/0 | R1:UNCOVERED, R2:UNCOVERED, R3:UNCOVERED | no | PASS | FLAG | R7 | 4.9 | $0.0569 |
| pydata__xarray-3095 | pydata/xarray | 4 | 4/0 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 18.9 | $0.0688 |
| django__django-13363 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 2.7 | $0.0172 |
| matplotlib__matplotlib-26466 | matplotlib/matplotlib | 1 | 1/0 | R1:PASS | yes | FAIL | FLAG | R5 | 9.7 | $0.0138 |
| sphinx-doc__sphinx-8638 | sphinx-doc/sphinx | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 13.3 | $0.1982 |
| django__django-13837 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | 5.8 | $0.0286 |
| django__django-14855 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | 2.6 | $0.0217 |
| django__django-11239 | django/django | 4 | 4/0 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | yes | PASS | ACCEPT | R6 | 2.8 | $0.0184 |
| matplotlib__matplotlib-20859 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 8.6 | $0.0192 |
| pylint-dev__pylint-6386 | pylint-dev/pylint | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 8.2 | $0.0577 |
| sympy__sympy-13031 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 8.2 | $0.0767 |
| django__django-12143 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 4.9 | $0.0458 |
| scikit-learn__scikit-learn-14983 | scikit-learn/scikit-learn | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 1.7 | $0.0064 |
| django__django-11964 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 12.8 | $0.0401 |
| sympy__sympy-21930 | sympy/sympy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | 22.8 | $0.0121 |
| sympy__sympy-16792 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 40.0 | $0.0478 |
| django__django-16950 | django/django | 2 | 2/0 | R1:PASS, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 6.6 | $0.0862 |
| django__django-13568 | django/django | 3 | 2/0 | R1:PASS, R2:UNCOVERED, R3:PASS | no | PASS | ACCEPT | R6b | 3.4 | $0.0293 |
| django__django-11265 | django/django | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 4.2 | $0.0487 |
| django__django-16642 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 3.1 | $0.0207 |
| django__django-16662 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 3.5 | $0.0304 |
| astropy__astropy-14995 | astropy/astropy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 1.9 | $0.0078 |
| sphinx-doc__sphinx-9711 | sphinx-doc/sphinx | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | ACCEPT | R6 | 1.5 | $0.0208 |
| django__django-15022 | django/django | 0 | 0/0 | REQUIREMENTS_UNAVAILABLE | no | NOT_AVAILABLE | FLAG | R7 | 5.5 | $0.0763 |

## Totals

- Minutes: total 436.3, median 5.7 per task, max 64.4.
- DeepSeek cost: $1.9282 total, $0.0402 per task.
- Gold V4 full passes: 36 of 48. Gold with any V4 FAIL: 8 of 48.
- Gold decisions, frozen switches (tag v1.5-frozen (switches identical at v1.5-frozen-2)): ACCEPT 30, FLAG 18, REJECT 0.
- Recall (A3, recorded): 40 model-written gold lines in 20 tasks (71 messages); 0 gold lines in kept frozen tests (0 tasks); 0 leak lines. Per-task hashes: [test_gold_b2_recall.json](test_gold_b2_recall.json).
- Generator fingerprints: 1548 responses in 95 conversation files; 1548 match the pin `bc19ba97cbe016479903222bb1578db6`, 0 do not (bc19ba97cbe016479903222bb1578db6 1548).

Machine-readable results: `reports/study_v1_5/test_gold_b2/test_gold_b2_results.json`.
