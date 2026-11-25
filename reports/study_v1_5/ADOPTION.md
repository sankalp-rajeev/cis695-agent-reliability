# Phase 7: adoption (calibration on arm B)

Status: ✅ all gates pass.

Arm B's 51 gpt-4.1-mini patches were re-verified (audited, `--reuse-v4-from runs/study_dev_gold`): 40 in `runs/study_dev_armb_2` and 11 kept from the stopped first run `runs/study_dev_armb` after part G confirmed their outcomes unchanged (amendment B9). Rules: PROTOCOL §5 as amended by A4, A6–A8 ([AMENDMENT_2026-11-21.md](AMENDMENT_2026-11-21.md)). Arm B's existing labels (swebench 5.0.2) were read here only, each row checked against arm B's frozen patch sha256. No test-set data exists.

## Gates

| Gate | Measured | Result |
|---|---|---|
| Sealed | rerun `COMPLETE`, seal `MATCH`; kept run seal `MATCH` (status `STOPPED_SYSTEMIC`) | ✅ pass |
| Merged set | 11 kept + 40 rerun = 51 of 51, no duplicates | ✅ pass |
| Zero generation | study_dev_armb_2: generator calls 0, ledger calls 0; study_dev_armb: generator calls 0, ledger calls 0 (job rows 0), account $2.3739 ≤ cap $2.4739 | ✅ pass |
| Audit | exit 1; nothing in scope (no agent or generator artifacts in a verify-only reuse run); reused V4 audited in Phase 6, exit 0 | ✅ pass |
| Labels | 25 correct, 26 wrong (expected 25 / 26), every patch sha256 matched | ✅ pass |

Infrastructure-flagged tasks in the run: 0 (none). Run finished 2026-11-22T07:41:20.185295+00:00; before the A5 deadline (Mon 23 Nov 12:00).

## a. V4 version (A4 vi), switches off

| V4 | ACCEPT | correct ACCEPTs | ACCEPT precision |
|---|---:|---:|---:|
| new (per-requirement, this run) | 16 | 13 | 81.2% |
| old (arm B stored, V2 under P, A6) | 20 | 16 | 80.0% |

Rule: old V4 only if more correct ACCEPTs and precision at least as high. **Chosen: new (per-requirement) V4.**

## b. Each switch alone against switches off (chosen V4)

| switch | numbers | rule | result |
|---|---|---|---|
| r2 | gold newly REJECTed 0 (–); arm B correct newly REJECTed 0; arm B wrong newly REJECTed 2 | ≤ 1, ≤ 1, ≥ 2 | ✅ pass |
| r3 | gold newly REJECTed 3 (astropy__astropy-13398, django__django-13297, pytest-dev__pytest-7432); arm B correct newly REJECTed 2; arm B wrong newly REJECTed 4 | ≤ 1, ≤ 1, ≥ 2 | ⛔ fail |
| r6 | arm B newly ACCEPTed 6, of which correct 5 (83.3%); gold newly ACCEPTed 8 | ≥ 70% correct; none → off | ✅ pass |
| r6b | arm B newly ACCEPTed 2, of which correct 2 (100.0%); gold newly ACCEPTed 4 | ≥ 70% correct; none → off | ✅ pass |

Counts of correct patches REJECTed are the ones the switch newly REJECTs; totals are in the JSON.

## c. Adopted set

Passing individually: r2, r6, r6b. PROTOCOL §5 total gold cost (adopted switches together add ≤ 1 dev gold REJECT, else drop R2, then R3): dropped none.

**Adopted: r2, r6, r6b.**

## d. V2 fallback

Kept: yes. Dev gold V2 FAILs that came only from fallback-selected tests: 0 (none).

## Arm B (51 patches: 25 correct, 26 wrong)

| policy | ACCEPT c/w | FLAG c/w | REJECT c/w | ACCEPT precision | correct accepted | wrong rejected |
|---|---|---|---|---:|---:|---:|
| v1.4.1 (arm B stored signals, accounting P) | 16/4 | 9/18 | 0/4 | 80.0% | 16 | 4 |
| v1.5 switches off (new (per-requirement) V4) | 13/3 | 12/17 | 0/6 | 81.2% | 13 | 6 |
| v1.5 adopted (r2, r6, r6b) | 20/4 | 5/14 | 0/8 | 83.3% | 20 | 8 |

## Task sources (amendment B9)

| run | tasks | ids |
|---|---:|---|
| `runs/study_dev_armb_2` (rerun) | 40 | django__django-13023, django__django-13158, django__django-14140, django__django-15103, django__django-15278, django__django-15499, django__django-15572, django__django-16082, django__django-16255, django__django-16612, django__django-16631, django__django-16667, matplotlib__matplotlib-20488, matplotlib__matplotlib-22871, matplotlib__matplotlib-23476, matplotlib__matplotlib-24026, matplotlib__matplotlib-24627, matplotlib__matplotlib-24637, matplotlib__matplotlib-24970, matplotlib__matplotlib-25122, matplotlib__matplotlib-25287, matplotlib__matplotlib-25332, matplotlib__matplotlib-25479, matplotlib__matplotlib-26291, pydata__xarray-6744, pylint-dev__pylint-6903, pylint-dev__pylint-7277, pytest-dev__pytest-5809, pytest-dev__pytest-6202, pytest-dev__pytest-7236, pytest-dev__pytest-7432, pytest-dev__pytest-7521, scikit-learn__scikit-learn-10908, scikit-learn__scikit-learn-12585, scikit-learn__scikit-learn-14141, sphinx-doc__sphinx-10323, sphinx-doc__sphinx-10466, sphinx-doc__sphinx-7910, sympy__sympy-13480, sympy__sympy-19783 |
| `runs/study_dev_armb` (kept, sealed, read only) | 11 | astropy__astropy-13398, astropy__astropy-14365, astropy__astropy-14508, astropy__astropy-7606, django__django-11095, django__django-12965, django__django-13212, django__django-13297, django__django-13786, django__django-13807, django__django-13820 |

## Dev gold (51) under the adopted set

ACCEPT 37, FLAG 14, REJECT 0 (REJECTed: none).
Gold = Phase 6 run with pytest-7236 and pytest-7521 from `runs/study_dev_gold_f`.

Machine-readable: `reports/study_v1_5/adoption.json`.
