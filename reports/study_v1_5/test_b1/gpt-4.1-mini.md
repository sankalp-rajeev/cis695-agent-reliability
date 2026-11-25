# Phase 12: gpt-4.1-mini, test batch 1

Status: ✅ all gates pass.

Verify-only run of gpt-4.1-mini's 60 batch 1 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b1`, HEAD `26d42df0fd708bb2cf015b7da87a780dc66dd264`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $4.4098 ≤ cap $4.5098 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audited, exit 0 | ✅ pass |
| Decisions | 60 of 60 | ✅ pass |

## Totals

- Decisions, all 60 tasks: ACCEPT 11, FLAG 22, REJECT 27.
- Decisions, the 60 non-empty patches: ACCEPT 11, FLAG 22, REJECT 27.
- Empty patches: 0 (none).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 4.
- Patches applied, by grader command (B12): `git apply --verbose` 52, `git apply --verbose --3way` 6; fail every command: 2 (django__django-11149, sphinx-doc__sphinx-8035).
- Minutes: total 432.4, median 3.0, max 64.5.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| pydata__xarray-4356 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 29.0 |  |
| sympy__sympy-22714 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 21.9 |  |
| sympy__sympy-14248 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.5 |  |
| django__django-15695 |  | FAIL | NOT_AVAILABLE (error) | FAIL | FAIL | REJECT | R1 | 1.4 |  |
| django__django-12273 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 38.2 |  |
| django__django-14539 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 1.6 |  |
| sympy__sympy-22456 |  | PASS | NOT_AVAILABLE (error) | PASS | PASS | FLAG | R8 | 4.4 |  |
| matplotlib__matplotlib-26342 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 8.4 |  |
| django__django-14559 |  | PASS | NOT_AVAILABLE (error) | FAIL | FAIL | FLAG | R4 | 6.4 |  |
| django__django-11951 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 2.5 |  |
| astropy__astropy-13453 |  | FAIL | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 3.1 |  |
| django__django-12419 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| matplotlib__matplotlib-25960 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.7 |  |
| astropy__astropy-12907 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | REJECT | R1 | 0.2 |  |
| django__django-13925 |  | PASS | FAIL | FAIL | FAIL | REJECT | R3 | 13.9 |  |
| scikit-learn__scikit-learn-25931 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.2 |  |
| django__django-15863 |  | PASS | NOT_AVAILABLE (error) | PASS | FAIL | FLAG | R4 | 6.1 |  |
| django__django-14434 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 31.3 |  |
| django__django-13343 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 3.4 |  |
| django__django-13449 |  | PASS | NOT_AVAILABLE (error) | FAIL | PASS | FLAG | R8 | 2.3 |  |
| pydata__xarray-7229 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.2 |  |
| pydata__xarray-6721 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 3.1 |  |
| django__django-11451 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | ACCEPT | R6 | 31.3 |  |
| django__django-16801 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.8 |  |
| django__django-17084 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.5 |  |
| sympy__sympy-15017 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| sympy__sympy-20590 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-11149 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| sphinx-doc__sphinx-9591 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | FAIL | REJECT | R1 | 0.2 |  |
| django__django-11333 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 21.7 |  |
| django__django-13346 |  | PASS | FAIL | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R3b | 13.2 |  |
| django__django-13109 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 4.6 |  |
| astropy__astropy-7671 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 3.1 |  |
| astropy__astropy-13236 |  | FAIL | FAIL | PASS | PASS | REJECT | R1 | 19.8 |  |
| sympy__sympy-17630 |  | PASS | NOT_AVAILABLE (error) | PASS | PASS | FLAG | R8 | 2.7 |  |
| scikit-learn__scikit-learn-12973 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 3.4 |  |
| django__django-10554 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.1 |  |
| django__django-12039 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.9 |  |
| django__django-13512 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.2 |  |
| django__django-12193 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | FLAG | R4 | 8.9 |  |
| sympy__sympy-14531 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.5 |  |
| django__django-12308 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| pydata__xarray-3151 |  | PASS | NOT_AVAILABLE (nothing_to_check) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.2 |  |
| sphinx-doc__sphinx-9658 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 0.9 |  |
| scikit-learn__scikit-learn-25973 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 15.5 |  |
| sympy__sympy-12096 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 3.1 |  |
| sphinx-doc__sphinx-8035 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| sphinx-doc__sphinx-8269 |  | FAIL | FAIL | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 6.6 |  |
| sympy__sympy-23262 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | ACCEPT | R6b | 5.6 |  |
| sympy__sympy-23824 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 3.3 |  |
| django__django-15957 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 4.7 |  |
| pydata__xarray-3677 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 3.1 |  |
| django__django-11728 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-13401 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.4 |  |
| pydata__xarray-7393 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.2 |  |
| django__django-14534 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 7.0 |  |
| sympy__sympy-13551 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 64.5 |  |
| sympy__sympy-15809 |  | PASS | NOT_AVAILABLE (error) | PASS | PASS | FLAG | R8 | 2.4 |  |
| pydata__xarray-4687 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 4.9 |  |
| django__django-14493 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.2 |  |

Machine-readable: `reports/study_v1_5/test_b1/gpt-4.1-mini.json`.
