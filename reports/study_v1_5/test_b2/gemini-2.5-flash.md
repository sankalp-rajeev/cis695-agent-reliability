# Phase 12b: gemini-2.5-flash, test batch 2

Status: ✅ all gates pass.

Verify-only run of gemini-2.5-flash's 48 batch 2 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b2`, HEAD `93cf56d42dbdfe1b438c5485febf8e0fcf39092e`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $6.3380 ≤ cap $6.4380 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audit exit 0 (phase12b_gold_b2_audit_b15.exit) | ✅ pass |
| Decisions | 48 of 48 | ✅ pass |

## Totals

- Decisions, all 48 tasks: ACCEPT 11, FLAG 11, REJECT 26.
- Decisions, the 46 non-empty patches: ACCEPT 11, FLAG 11, REJECT 24.
- Empty patches: 2 (pytest-dev__pytest-7571, sphinx-doc__sphinx-9461).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 5.
- Patches applied, by grader command (B12): `git apply --verbose` 37, `git apply --verbose --3way` 4, `patch --batch --forward --fuzz=5 -p1 -i` 1; fail every command: 4 (sphinx-doc__sphinx-8548, pydata__xarray-3095, sympy__sympy-13031, django__django-16662).
- Minutes: total 206.6, median 1.4, max 62.5.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| scikit-learn__scikit-learn-13496 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 4.1 |  |
| mwaskom__seaborn-3187 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.1 |  |
| scikit-learn__scikit-learn-13439 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 10.8 |  |
| scikit-learn__scikit-learn-14053 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 0.9 |  |
| pytest-dev__pytest-7571 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| sphinx-doc__sphinx-9461 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| django__django-16493 |  | PASS | FAIL | FAIL | PASS | REJECT | R2 | 7.3 |  |
| sympy__sympy-13372 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | FLAG | R8 | 62.5 |  |
| sympy__sympy-20801 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 8.3 |  |
| sphinx-doc__sphinx-8548 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-15280 |  | PASS | FAIL | PASS | NOT_AVAILABLE (nothing_to_check) | REJECT | R3b | 6.1 |  |
| django__django-14351 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.0 |  |
| pytest-dev__pytest-8399 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 7.5 |  |
| django__django-11734 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 6.3 |  |
| scikit-learn__scikit-learn-25232 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.9 |  |
| django__django-15731 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 5.9 |  |
| django__django-13410 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| django__django-13551 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| django__django-16899 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 4.2 |  |
| django__django-12713 |  | PASS | NOT_AVAILABLE (nothing_to_check) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.3 |  |
| django__django-11885 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| django__django-14007 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 15.2 |  |
| sphinx-doc__sphinx-9698 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | PASS | REJECT | R1 | 0.3 |  |
| pytest-dev__pytest-7205 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 2.2 |  |
| django__django-13513 |  | FAIL | FAIL | PASS | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 18.9 |  |
| pydata__xarray-3095 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.0 |  |
| django__django-13363 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 1.8 |  |
| matplotlib__matplotlib-26466 |  | FAIL | PASS | FAIL | PASS | REJECT | R1 | 1.9 |  |
| sphinx-doc__sphinx-8638 |  | FAIL | FAIL | FAIL | FAIL | REJECT | R1 | 3.6 |  |
| django__django-13837 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 4.0 |  |
| django__django-14855 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.5 |  |
| django__django-11239 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.2 |  |
| matplotlib__matplotlib-20859 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.7 |  |
| pylint-dev__pylint-6386 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.4 |  |
| sympy__sympy-13031 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| django__django-12143 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 2.4 |  |
| scikit-learn__scikit-learn-14983 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.4 |  |
| django__django-11964 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.3 |  |
| sympy__sympy-21930 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.3 |  |
| sympy__sympy-16792 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 10.7 |  |
| django__django-16950 |  | PASS | NOT_AVAILABLE (error) | FAIL | FAIL | REJECT | R2 | 0.9 |  |
| django__django-13568 |  | PASS | PASS | PASS | NOT_AVAILABLE (nothing_to_check) | ACCEPT | R6b | 1.2 |  |
| django__django-11265 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| django__django-16642 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.5 |  |
| django__django-16662 |  | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.1 |  |
| astropy__astropy-14995 |  | FAIL | PASS | PASS | PASS | REJECT | R1 | 1.4 |  |
| sphinx-doc__sphinx-9711 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R1 | 0.3 |  |
| django__django-15022 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 3.6 |  |

Machine-readable: `reports/study_v1_5/test_b2/gemini-2.5-flash.json`.
