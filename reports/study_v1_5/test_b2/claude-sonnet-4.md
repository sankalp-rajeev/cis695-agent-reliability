# Phase 12b: claude-sonnet-4, test batch 2

Status: ✅ all gates pass.

Verify-only run of claude-sonnet-4's 48 batch 2 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b2`, HEAD `0fd9acd233901cd7feb69e864a5aa835e25e93b0`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $6.3380 ≤ cap $6.4380 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audit exit 0 (phase12b_gold_b2_audit_b15.exit) | ✅ pass |
| Decisions | 48 of 48 | ✅ pass |

## Totals

- Decisions, all 48 tasks: ACCEPT 12, FLAG 23, REJECT 13.
- Decisions, the 48 non-empty patches: ACCEPT 12, FLAG 23, REJECT 13.
- Empty patches: 0 (none).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 3.
- Patches applied, by grader command (B12): `git apply --verbose` 40, `patch --batch --forward --fuzz=5 -p1 -i` 2, `git apply --verbose --3way` 6; fail every command: 0 (none).
- Minutes: total 393.8, median 4.5, max 62.5.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| scikit-learn__scikit-learn-13496 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.0 |  |
| mwaskom__seaborn-3187 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 12.5 |  |
| scikit-learn__scikit-learn-13439 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 3.3 |  |
| scikit-learn__scikit-learn-14053 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | FLAG | R8 | 0.9 |  |
| pytest-dev__pytest-7571 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 0.8 |  |
| sphinx-doc__sphinx-9461 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 1.5 |  |
| django__django-16493 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 5.5 |  |
| sympy__sympy-13372 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | FLAG | R8 | 62.5 |  |
| sympy__sympy-20801 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 4.2 |  |
| sphinx-doc__sphinx-8548 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 5.4 |  |
| django__django-15280 |  | PASS | FAIL | FAIL | FAIL | REJECT | R3 | 34.8 |  |
| django__django-14351 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 7.9 |  |
| pytest-dev__pytest-8399 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 7.4 |  |
| django__django-11734 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 2.4 |  |
| scikit-learn__scikit-learn-25232 |  | PASS | PASS | FAIL | PASS | FLAG | R8 | 10.2 |  |
| django__django-15731 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.3 |  |
| django__django-13410 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.7 |  |
| django__django-13551 |  | PASS | PASS | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 1.3 |  |
| django__django-16899 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 7.2 |  |
| django__django-12713 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | FLAG | R4 | 7.2 |  |
| django__django-11885 |  | PASS | FAIL | FAIL | PASS | REJECT | R2 | 17.5 |  |
| django__django-14007 |  | PASS | FAIL | FAIL | PASS | FLAG | R5 | 14.6 |  |
| sphinx-doc__sphinx-9698 |  | FAIL | PASS | FAIL | PASS | REJECT | R1 | 2.3 |  |
| pytest-dev__pytest-7205 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-13513 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 0.2 |  |
| pydata__xarray-3095 |  | PASS | PASS | FAIL | PASS | ACCEPT | R6 | 2.9 |  |
| django__django-13363 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 4.8 |  |
| matplotlib__matplotlib-26466 |  | FAIL | PASS | FAIL | PASS | REJECT | R1 | 1.9 |  |
| sphinx-doc__sphinx-8638 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 4.9 |  |
| django__django-13837 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.2 |  |
| django__django-14855 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | REJECT | R2 | 4.3 |  |
| django__django-11239 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.2 |  |
| matplotlib__matplotlib-20859 |  | PASS | PASS | PASS | PASS | FLAG | R8 | 1.7 |  |
| pylint-dev__pylint-6386 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.4 |  |
| sympy__sympy-13031 |  | PASS | FAIL | FAIL | FAIL | REJECT | R3 | 4.7 |  |
| django__django-12143 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 2.3 |  |
| scikit-learn__scikit-learn-14983 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 13.4 |  |
| django__django-11964 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | REJECT | R2 | 42.8 |  |
| sympy__sympy-21930 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 21.5 |  |
| sympy__sympy-16792 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 6.8 |  |
| django__django-16950 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | FLAG | R4 | 16.4 |  |
| django__django-13568 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 7.7 |  |
| django__django-11265 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 7.1 |  |
| django__django-16642 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.5 |  |
| django__django-16662 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.3 |  |
| astropy__astropy-14995 |  | FAIL | PASS | PASS | PASS | REJECT | R1 | 1.4 |  |
| sphinx-doc__sphinx-9711 |  | FAIL | FAIL | FAIL | PASS | REJECT | R1 | 11.3 |  |
| django__django-15022 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 18.7 |  |

Machine-readable: `reports/study_v1_5/test_b2/claude-sonnet-4.json`.
