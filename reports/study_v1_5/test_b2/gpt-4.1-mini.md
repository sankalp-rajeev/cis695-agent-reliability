# Phase 12b: gpt-4.1-mini, test batch 2

Status: ✅ all gates pass.

Verify-only run of gpt-4.1-mini's 48 batch 2 patches (empty patches included), `--mode audited --freeze-tag v1.5-frozen-2`, V4 reused from `/home/sankalp/projects/wt-study/runs/study_test_gold_b2`, HEAD `d35e6f2a69d1a7534c87bf76d37ff6b651da5964`. Decisions under the frozen switches (`decide_v1_5.py --frozen`), label-free. No official label, log or results file was opened.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | run `COMPLETE`, seal `MATCH` | ✅ pass |
| Zero generation | generator calls 0, ledger calls 0 (job rows 0), account $6.3380 ≤ cap $6.4380 | ✅ pass |
| Audit | exit 1; nothing in scope; reused V4 audit exit 0 (phase12b_gold_b2_audit_b15.exit) | ✅ pass |
| Decisions | 48 of 48 | ✅ pass |

## Totals

- Decisions, all 48 tasks: ACCEPT 8, FLAG 17, REJECT 23.
- Decisions, the 45 non-empty patches: ACCEPT 8, FLAG 17, REJECT 20.
- Empty patches: 3 (django__django-13513, django__django-16899, sympy__sympy-13031).
- Errors: 0 (none); task errors recorded by the run: 0.
- V2 early exits (B10): 8.
- Patches applied, by grader command (B12): `git apply --verbose` 37, `patch --batch --forward --fuzz=5 -p1 -i` 2, `git apply --verbose --3way` 6; fail every command: 0 (none).
- Minutes: total 214.5, median 1.9, max 38.5.

## Per task

| instance_id | empty | V1 | V2 | V3 | V4 | decision | rule | min | error |
|---|---|---|---|---|---|---|---|---:|---|
| scikit-learn__scikit-learn-13496 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 9.6 |  |
| mwaskom__seaborn-3187 |  | FAIL | PASS | PASS | FAIL | REJECT | R1 | 1.3 |  |
| scikit-learn__scikit-learn-13439 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 2.2 |  |
| scikit-learn__scikit-learn-14053 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 0.9 |  |
| pytest-dev__pytest-7571 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | FAIL | FLAG | R4 | 5.1 |  |
| sphinx-doc__sphinx-9461 |  | FAIL | NOT_AVAILABLE (error) | FAIL | FAIL | REJECT | R1 | 1.8 |  |
| django__django-16493 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 6.4 |  |
| sympy__sympy-13372 |  | PASS | NOT_AVAILABLE (error) | PASS | FAIL | FLAG | R4 | 5.5 |  |
| sympy__sympy-20801 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 8.7 |  |
| sphinx-doc__sphinx-8548 |  | FAIL | NOT_AVAILABLE (error) | FAIL | FAIL | REJECT | R1 | 1.4 |  |
| django__django-15280 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | FAIL | REJECT | R2 | 8.2 |  |
| django__django-14351 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 0.7 |  |
| pytest-dev__pytest-8399 |  | FAIL | NOT_AVAILABLE (incomplete) | PASS | PASS | REJECT | R1 | 10.3 |  |
| django__django-11734 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 6.3 |  |
| scikit-learn__scikit-learn-25232 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 3.2 |  |
| django__django-15731 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.3 |  |
| django__django-13410 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 1.8 |  |
| django__django-13551 |  | PASS | PASS | FAIL | NOT_AVAILABLE (nothing_to_check) | ACCEPT | R6b | 1.3 |  |
| django__django-16899 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| django__django-12713 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.3 |  |
| django__django-11885 |  | PASS | NOT_AVAILABLE (error) | FAIL | NOT_AVAILABLE (nothing_to_check) | REJECT | R2 | 1.5 |  |
| django__django-14007 |  | PASS | FAIL | FAIL | FAIL | REJECT | R3 | 38.5 |  |
| sphinx-doc__sphinx-9698 |  | FAIL | NOT_AVAILABLE (nothing_to_check) | FAIL | PASS | REJECT | R1 | 0.2 |  |
| pytest-dev__pytest-7205 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | PASS | ACCEPT | R6 | 0.2 |  |
| django__django-13513 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| pydata__xarray-3095 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 22.3 |  |
| django__django-13363 |  | PASS | NOT_AVAILABLE (nothing_to_check) | FAIL | FAIL | FLAG | R4 | 0.3 |  |
| matplotlib__matplotlib-26466 |  | PASS | PASS | FAIL | FAIL | FLAG | R4 | 1.6 |  |
| sphinx-doc__sphinx-8638 |  | FAIL | PASS | FAIL | FAIL | REJECT | R1 | 0.9 |  |
| django__django-13837 |  | PASS | FAIL | PASS | FAIL | REJECT | R3 | 3.9 |  |
| django__django-14855 |  | PASS | NOT_AVAILABLE (incomplete) | PASS | PASS | ACCEPT | R6 | 6.3 |  |
| django__django-11239 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.2 |  |
| matplotlib__matplotlib-20859 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 5.0 |  |
| pylint-dev__pylint-6386 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.2 |  |
| sympy__sympy-13031 | yes | FAIL | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | NOT_AVAILABLE (error) | REJECT | R1 | 0.0 |  |
| django__django-12143 |  | PASS | PASS | PASS | PASS | ACCEPT | R6 | 2.3 |  |
| scikit-learn__scikit-learn-14983 |  | PASS | FAIL | PASS | PASS | FLAG | R5 | 12.0 |  |
| django__django-11964 |  | PASS | NOT_AVAILABLE (incomplete) | FAIL | PASS | FLAG | R8 | 3.6 |  |
| sympy__sympy-21930 |  | PASS | NOT_AVAILABLE (error) | PASS | FAIL | FLAG | R4 | 2.1 |  |
| sympy__sympy-16792 |  | PASS | NOT_AVAILABLE (error) | FAIL | FAIL | REJECT | R2 | 1.8 |  |
| django__django-16950 |  | FAIL | NOT_AVAILABLE (incomplete) | FAIL | FAIL | REJECT | R1 | 6.1 |  |
| django__django-13568 |  | PASS | NOT_AVAILABLE (error) | PASS | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 2.0 |  |
| django__django-11265 |  | PASS | NOT_AVAILABLE (nothing_to_check) | PASS | FAIL | FLAG | R4 | 0.2 |  |
| django__django-16642 |  | PASS | PASS | PASS | FAIL | FLAG | R4 | 1.5 |  |
| django__django-16662 |  | PASS | FAIL | PASS | NOT_AVAILABLE (nothing_to_check) | REJECT | R3b | 14.9 |  |
| astropy__astropy-14995 |  | FAIL | FAIL | PASS | PASS | REJECT | R1 | 5.7 |  |
| sphinx-doc__sphinx-9711 |  | FAIL | PASS | FAIL | PASS | REJECT | R1 | 2.8 |  |
| django__django-15022 |  | PASS | PASS | FAIL | NOT_AVAILABLE (nothing_to_check) | FLAG | R7 | 1.1 |  |

Machine-readable: `reports/study_v1_5/test_b2/gpt-4.1-mini.json`.
