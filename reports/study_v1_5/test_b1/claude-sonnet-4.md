# Phase 12: claude-sonnet-4, test batch 1

Status: ✅ all gates pass.

Verify-only run of claude-sonnet-4's 60 batch 1 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b1`, HEAD `7b2ac913d175c470538517f6512e65e75ebe6290`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $4.4098 ≤ cap $4.5098 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audited, exit 0 | ✅ pass |
| Decisions | 60 of 60 | ✅ pass |

## Totals

- Decisions, all 60 tasks: ACCEPT 14, FLAG 33, REJECT 13.
- Decisions, the 60 non-empty patches: ACCEPT 14, FLAG 33, REJECT 13.
- Empty patches: 0 (none).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 3.
- Patches applied, by grader command (B12): `git apply --verbose` 52, `git apply --verbose --3way` 7, `patch --batch --forward --fuzz=5 -p1 -i` 1; fail every command: 0 (none).
- Minutes: total 775.0, median 3.7, max 73.6.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| pydata__xarray-4356 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | FLAG | R8 | 0.2 |  |
| sympy__sympy-22714 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 17.2 |  |
| sympy__sympy-14248 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 73.1 |  |
| django__django-15695 |  | PASS | FAIL | FAIL | FAIL | REJECT | R2 | 10.1 |  |
| django__django-12273 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | REJECT | R2 | 65.5 |  |
| django__django-14539 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.2 |  |
| sympy__sympy-22456 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 16.1 |  |
| matplotlib__matplotlib-26342 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.6 |  |
| django__django-14559 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 2.7 |  |
| django__django-11951 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 5.3 |  |
| astropy__astropy-13453 |  | FAIL | PASS | PASS | PASS | REJECT | R1 | 2.1 |  |
| django__django-12419 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| matplotlib__matplotlib-25960 |  | FAIL | FAIL | PASS | PASS | REJECT | R1 | 27.9 |  |
| astropy__astropy-12907 |  | FAIL | PASS | PASS | PASS | REJECT | R1 | 1.2 |  |
| django__django-13925 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 17.7 |  |
| scikit-learn__scikit-learn-25931 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.2 |  |
| django__django-15863 |  | PASS | PASS | FAIL | PASS | ACCEPT | R6 | 1.2 |  |
| django__django-14434 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 4.2 |  |
| django__django-13343 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 66.2 |  |
| django__django-13449 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 4.9 |  |
| pydata__xarray-7229 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 18.0 |  |
| pydata__xarray-6721 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 17.8 |  |
| django__django-11451 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 60.9 |  |
| django__django-16801 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 4.6 |  |
| django__django-17084 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 4.6 |  |
| sympy__sympy-15017 |  | PASS | PASS | FAIL | PASS | FLAG | R8 | 2.7 |  |
| sympy__sympy-20590 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-11149 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 7.2 |  |
| sphinx-doc__sphinx-9591 |  | FAIL | FAIL | FAIL | FAIL | REJECT | R1 | 3.7 |  |
| django__django-11333 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.3 |  |
| django__django-13346 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 4.5 |  |
| django__django-13109 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | REJECT | R2 | 10.2 |  |
| astropy__astropy-7671 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 3.2 |  |
| astropy__astropy-13236 |  | FAIL | FAIL | PASS | PASS | REJECT | R1 | 19.7 |  |
| sympy__sympy-17630 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 2.9 |  |
| scikit-learn__scikit-learn-12973 |  | PASS | PASS | FAIL | PASS | ACCEPT | R6 | 16.4 |  |
| django__django-10554 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 38.4 |  |
| django__django-12039 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | FLAG | R4 | 8.7 |  |
| django__django-13512 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | REJECT | R2 | 3.6 |  |
| django__django-12193 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | FLAG | R8 | 11.3 |  |
| sympy__sympy-14531 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 2.4 |  |
| django__django-12308 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.1 |  |
| pydata__xarray-3151 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.0 |  |
| sphinx-doc__sphinx-9658 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 0.8 |  |
| scikit-learn__scikit-learn-25973 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | FLAG | R8 | 40.0 |  |
| sympy__sympy-12096 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 3.8 |  |
| sphinx-doc__sphinx-8035 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 2.1 |  |
| sphinx-doc__sphinx-8269 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | PASS | REJECT | R1 | 0.3 |  |
| sympy__sympy-23262 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 3.1 |  |
| sympy__sympy-23824 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 3.4 |  |
| django__django-15957 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.3 |  |
| pydata__xarray-3677 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.0 |  |
| django__django-11728 |  | PASS | PASS | FAIL | PASS | ACCEPT | R6 | 1.1 |  |
| django__django-13401 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 39.2 |  |
| pydata__xarray-7393 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 26.2 |  |
| django__django-14534 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.5 |  |
| sympy__sympy-13551 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 73.6 |  |
| sympy__sympy-15809 |  | PASS | NOT_AVAILABLE (error) | PASS | PASS | FLAG | R8 | 2.4 |  |
| pydata__xarray-4687 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 9.6 |  |
| django__django-14493 |  | PASS | PASS | FAIL | PASS | FLAG | R8 | 1.2 |  |

Machine-readable: `reports/study_v1_5/test_b1/claude-sonnet-4.json`.
