# Phase 6: dev gold run

Status: ✅ all gates pass.

Verify-only run of the 51 dev gold (reference) patches with the frozen V4 (one pass, Phase 4b prompts; [V4_FREEZE.md](../V4_FREEZE.md)), `--mode audited --freeze-tag study-dev-gold-launch`, HEAD `1269060a753df00ccf46cb09707fdf7416b5f0e2`, git_dirty false. No labels were used. Gold-patch lines are never shown.

The run ended with status `COMPLETE`. The seal check is `MATCH` over 2823 files; seal sha256 `c7c24dd2e167a7feaf783b8a9de96b13a066dd66fbbb51945065e103ce7daa03`. The ledger records 1223 calls for this job, 0 unsettled.

## Gates (fixed before launch)

| Gate | Rule | Measured | Result |
|---|---|---|---|
| Sealed | run COMPLETE and seal matches | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Ledger | job and DeepSeek account total within the cap, nothing unsettled | job $1.3728, account $2.3739, cap $4.0010, 0 unsettled | ✅ pass |
| Audit | A3 leakage audit exit 0 | exit 0; confirmed: none | ✅ pass |
| Infrastructure | errors on ≤ 2 of 51 tasks | 2 (pytest-dev__pytest-7236, pytest-dev__pytest-7521) | ✅ pass |

An infrastructure error is a task that did not complete, has an infrastructure flag, has no record, or has V4 absence `error` (PILOT.md definition).

## Per task (gold patches, label-free)

Format as in PILOT2.md. Decisions come from `scripts/decide_v1_5.py --switches r2=0,r3=0,r6=0` (off) and `--switches r2=1,r3=1,r6=1` (all on).

| instance_id | repo | reqs | kept p1/p2 | verdicts | V4 full pass | V2 (P) | decision | rule | all-on decision | all-on rule | min | cost |
|---|---|---:|---:|---|---|---|---|---|---|---|---:|---:|
| astropy__astropy-13398 | astropy/astropy | 4 | 4/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE, R4:PASS | no | NOT_AVAILABLE | FLAG | R4 | REJECT | R3 | 6.7 | $0.0495 |
| astropy__astropy-14365 | astropy/astropy | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 2.3 | $0.0189 |
| astropy__astropy-14508 | astropy/astropy | 3 | 2/0 | R1:PASS, R2:PASS, R3:UNCOVERED | no | NOT_AVAILABLE | FLAG | R7 | FLAG | R7 | 2.3 | $0.0267 |
| astropy__astropy-7606 | astropy/astropy | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 8.2 | $0.0077 |
| django__django-11095 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | FLAG | R8 | FLAG | R8 | 4.1 | $0.0235 |
| django__django-12965 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.8 | $0.0516 |
| django__django-13023 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 2.6 | $0.0141 |
| django__django-13158 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 3.3 | $0.0222 |
| django__django-13212 | django/django | 4 | 4/0 | R1:PASS, R2:PASS, R3:PASS, R4:FAIL_SINGLE | no | NOT_AVAILABLE | FLAG | R4 | FLAG | R4 | 9.5 | $0.0420 |
| django__django-13297 | django/django | 3 | 3/0 | R1:FAIL_SINGLE, R2:PASS, R3:FAIL_SINGLE | no | PASS | FLAG | R4 | REJECT | R3 | 6.1 | $0.0654 |
| django__django-13786 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 1.9 | $0.0100 |
| django__django-13807 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.5 | $0.0356 |
| django__django-13820 | django/django | 2 | 1/0 | R1:PASS, R2:UNCOVERED | no | PASS | FLAG | R7 | FLAG | R7 | 3.7 | $0.0382 |
| django__django-14140 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 7.6 | $0.0421 |
| django__django-15103 | django/django | 3 | 2/0 | R1:PASS, R2:PASS, R3:UNCOVERED | no | PASS | FLAG | R7 | FLAG | R7 | 2.4 | $0.0163 |
| django__django-15278 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.7 | $0.0319 |
| django__django-15499 | django/django | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 2.1 | $0.0136 |
| django__django-15572 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.4 | $0.0329 |
| django__django-16082 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 2.5 | $0.0187 |
| django__django-16255 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 2.2 | $0.0200 |
| django__django-16612 | django/django | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 1.4 | $0.0178 |
| django__django-16631 | django/django | 3 | 3/0 | R1:NO_RESULT, R2:NO_RESULT, R3:NO_RESULT | no | PASS | FLAG | R8 | REJECT | R2 | 4.4 | $0.0505 |
| django__django-16667 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 2.2 | $0.0112 |
| matplotlib__matplotlib-20488 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.9 | $0.0314 |
| matplotlib__matplotlib-22871 | matplotlib/matplotlib | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.4 | $0.0240 |
| matplotlib__matplotlib-23476 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 6.3 | $0.0717 |
| matplotlib__matplotlib-24026 | matplotlib/matplotlib | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 6.3 | $0.0236 |
| matplotlib__matplotlib-24627 | matplotlib/matplotlib | 3 | 3/0 | R1:PASS, R2:PASS, R3:FAIL_SINGLE | no | NOT_AVAILABLE | FLAG | R4 | FLAG | R4 | 1.7 | $0.0155 |
| matplotlib__matplotlib-24637 | matplotlib/matplotlib | 1 | 1/0 | R1:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 17.3 | $0.0208 |
| matplotlib__matplotlib-24970 | matplotlib/matplotlib | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 2.3 | $0.0072 |
| matplotlib__matplotlib-25122 | matplotlib/matplotlib | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 4.8 | $0.0291 |
| matplotlib__matplotlib-25287 | matplotlib/matplotlib | 3 | 2/0 | R1:PASS, R2:PASS, R3:UNCOVERED | no | PASS | FLAG | R7 | FLAG | R7 | 4.2 | $0.0369 |
| matplotlib__matplotlib-25332 | matplotlib/matplotlib | 1 | 1/0 | R1:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 8.9 | $0.0085 |
| matplotlib__matplotlib-25479 | matplotlib/matplotlib | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 10.5 | $0.0465 |
| matplotlib__matplotlib-26291 | matplotlib/matplotlib | 2 | 2/0 | R1:PASS, R2:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 17.6 | $0.0264 |
| pydata__xarray-6744 | pydata/xarray | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 13.1 | $0.0168 |
| pylint-dev__pylint-6903 | pylint-dev/pylint | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 2.3 | $0.0324 |
| pylint-dev__pylint-7277 | pylint-dev/pylint | 2 | 1/0 | R1:PASS, R2:UNCOVERED | no | PASS | FLAG | R7 | FLAG | R7 | 2.5 | $0.0152 |
| pytest-dev__pytest-5809 | pytest-dev/pytest | 2 | 2/0 | R1:PASS, R2:PASS | yes | FAIL | FLAG | R5 | FLAG | R5 | 2.1 | $0.0139 |
| pytest-dev__pytest-6202 | pytest-dev/pytest | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 4.6 | $0.0494 |
| pytest-dev__pytest-7236 | pytest-dev/pytest | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | FLAG | R8 | 2.0 | $0.0179 |
| pytest-dev__pytest-7432 | pytest-dev/pytest | 2 | 2/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | REJECT | R3 | 1.8 | $0.0148 |
| pytest-dev__pytest-7521 | pytest-dev/pytest | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | FLAG | R8 | 1.5 | $0.0146 |
| scikit-learn__scikit-learn-10908 | scikit-learn/scikit-learn | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 3.4 | $0.0106 |
| scikit-learn__scikit-learn-12585 | scikit-learn/scikit-learn | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 5.7 | $0.0083 |
| scikit-learn__scikit-learn-14141 | scikit-learn/scikit-learn | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 1.8 | $0.0115 |
| sphinx-doc__sphinx-10323 | sphinx-doc/sphinx | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 8.2 | $0.0839 |
| sphinx-doc__sphinx-10466 | sphinx-doc/sphinx | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 4.0 | $0.0306 |
| sphinx-doc__sphinx-7910 | sphinx-doc/sphinx | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 4.0 | $0.0322 |
| sympy__sympy-13480 | sympy/sympy | 1 | 1/0 | R1:PASS | yes | NOT_AVAILABLE | FLAG | R8 | ACCEPT | R6 | 42.4 | $0.0117 |
| sympy__sympy-19783 | sympy/sympy | 1 | 1/0 | R1:PASS | yes | PASS | ACCEPT | R6 | ACCEPT | R6 | 17.9 | $0.0071 |

## Totals

- Minutes: total 294.4, median 3.7 per task, max 42.4.
- DeepSeek cost: $1.3728 total, $0.0269 per task.
- Gold V4 full passes: 40 of 51. Gold with any V4 FAIL: 5 of 51.
- Gold decisions, switches off: ACCEPT 25, FLAG 26, REJECT 0.
- Gold decisions, all switches on: ACCEPT 31, FLAG 16, REJECT 4.
- Recall (A3, recorded): 48 model-written gold lines in 16 tasks (59 messages); 0 gold lines in kept frozen tests (0 tasks); 0 leak lines. Per-task hashes: [dev_gold_recall.json](dev_gold_recall.json).
- Generator fingerprints: 1223 responses in 102 conversation files; 1223 match the pin `bc19ba97cbe016479903222bb1578db6`, 0 do not (bc19ba97cbe016479903222bb1578db6 1223).

Machine-readable results: `reports/study_v1_5/dev_gold/dev_gold_results.json`.
