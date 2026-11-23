# Phase 12: gemini-2.5-flash, test batch 1

Status: ✅ all gates pass.

Verify-only run of gemini-2.5-flash's 60 batch 1 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b1`, HEAD `60f5ac11c2d1f315abef27fdf1dc4b2cce6cbf17`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $4.4098 ≤ cap $4.5098 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audited, exit 0 | ✅ pass |
| Decisions | 60 of 60 | ✅ pass |

## Totals

- Decisions, all 60 tasks: ACCEPT 8, FLAG 17, REJECT 35.
- Decisions, the 57 non-empty patches: ACCEPT 8, FLAG 17, REJECT 32.
- Empty patches: 3 (django__django-14493, django__django-15957, sphinx-doc__sphinx-8035).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 5.
- Patches applied, by grader command (B12): `git apply --verbose` 37, `git apply --verbose --3way` 5, `patch --batch --forward --fuzz=5 -p1 -i` 2; fail every command: 13 (pydata__xarray-4356, sympy__sympy-22714, django__django-15695, django__django-14539, astropy__astropy-12907, django__django-13925, scikit-learn__scikit-learn-25931, django__django-11333, sympy__sympy-17630, django__django-12308, sympy__sympy-23824, django__django-11728, pydata__xarray-7393).
- Minutes: total 375.8, median 1.3, max 70.4.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| pydata__xarray-4356 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.0 |  |
| sympy__sympy-22714 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| sympy__sympy-14248 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 1.5 |  |
| django__django-15695 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-12273 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 10.1 |  |
| django__django-14539 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| sympy__sympy-22456 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 20.1 |  |
| matplotlib__matplotlib-26342 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.8 |  |
| django__django-14559 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 2.8 |  |
| django__django-11951 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 2.6 |  |
| astropy__astropy-13453 |  | FAIL | PASS | PASS | PASS | REJECT | R1 | 2.3 |  |
| django__django-12419 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| matplotlib__matplotlib-25960 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 4.3 |  |
| astropy__astropy-12907 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-13925 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| scikit-learn__scikit-learn-25931 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-15863 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.3 |  |
| django__django-14434 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.4 |  |
| django__django-13343 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.0 |  |
| django__django-13449 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 9.8 |  |
| pydata__xarray-7229 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 6.2 |  |
| pydata__xarray-6721 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | FAIL | REJECT | R1 | 0.4 |  |
| django__django-11451 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.9 |  |
| django__django-16801 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | ACCEPT | R6b | 1.6 |  |
| django__django-17084 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 2.0 |  |
| sympy__sympy-15017 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 2.7 |  |
| sympy__sympy-20590 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-11149 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| sphinx-doc__sphinx-9591 |  | FAIL | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 1.3 |  |
| django__django-11333 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-13346 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.8 |  |
| django__django-13109 |  | FAIL | FAIL | FAIL | PASS | REJECT | R1 | 68.2 |  |
| astropy__astropy-7671 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 3.1 |  |
| astropy__astropy-13236 |  | FAIL | FAIL | PASS | PASS | REJECT | R1 | 19.7 |  |
| sympy__sympy-17630 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| scikit-learn__scikit-learn-12973 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 16.5 |  |
| django__django-10554 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 1.0 |  |
| django__django-12039 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 2.4 |  |
| django__django-13512 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.9 |  |
| django__django-12193 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.2 |  |
| sympy__sympy-14531 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.4 |  |
| django__django-12308 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| pydata__xarray-3151 |  | PASS | PASS | FAIL | PASS | REJECT | R2 | 1.0 |  |
| sphinx-doc__sphinx-9658 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | FAIL | REJECT | R1 | 0.2 |  |
| scikit-learn__scikit-learn-25973 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.7 |  |
| sympy__sympy-12096 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 3.4 |  |
| sphinx-doc__sphinx-8035 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| sphinx-doc__sphinx-8269 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 4.7 |  |
| sympy__sympy-23262 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | ACCEPT | R6b | 3.1 |  |
| sympy__sympy-23824 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-15957 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| pydata__xarray-3677 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 0.9 |  |
| django__django-11728 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-13401 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 68.5 |  |
| pydata__xarray-7393 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.0 |  |
| django__django-14534 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 18.2 |  |
| sympy__sympy-13551 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 70.4 |  |
| sympy__sympy-15809 |  | PASS | NOT_AVAILABLE (error) | PASS | PASS | FLAG | R8 | 2.3 |  |
| pydata__xarray-4687 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 9.7 |  |
| django__django-14493 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |

Machine-readable: `reports/study_v1_5/test_b1/gemini-2.5-flash.json`.
