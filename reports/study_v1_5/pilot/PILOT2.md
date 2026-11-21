# Phase 4b: V4 one-pass re-pilot

Status: ✅ all five gates pass.

This re-pilot runs the same 10 dev gold patches and the same command shape as the first pilot ([PILOT.md](PILOT.md)), with the Phase 4b prompt fix and `v4_passes: 1` (commit `fa1b016`). No labels were used. Gold-patch lines are never shown.

The run ended with status `COMPLETE`. The seal check is `MATCH`, over 610 files, and the seal sha256 is `ea17e98b2333cb81bae254b4a58404d421cbbe02c5c28bed0e3f6c2982d4bddb`. The ledger records 286 calls for this job, 0 of them unsettled.

## Gates (fixed before launch)

| Gate | Rule | Measured | Result |
|---|---|---|---|
| G1 cost | mean ≤ $0.06 per task and no task above $0.15 | total $0.3307, mean $0.0331, max task $0.0665 | ✅ pass |
| G2 coverage | ≥ 7 of 10 tasks with every requirement covered | 10 of 10 | ✅ pass |
| G3 leakage | no gold line first appears outside the model's own messages; model-written recall is counted, not failed | 0 lines first appear outside the model's messages; 55 GOLD_LINE_IN_GENERATOR findings (17 distinct lines, all model-written if the first number is 0); 0 other confirmed findings; audit complete, exit 1 | ✅ pass |
| G4 infrastructure | errors on ≤ 1 of 10 tasks | 0 (none) | ✅ pass |
| G5 gold V4 | fewer than 3 gold patches with any V4 FAIL, and ≥ 6 V4 full passes (first pilot, pass 1: 3 and 6) | 2 with a FAIL, 8 full passes | ✅ pass |

The audit exit code is non-zero whenever there are GOLD_LINE_IN_GENERATOR findings. G3 instead uses the G3_DIAGNOSIS.md first-appearance classification. G3 also fails if the audit has any other confirmed finding or did not finish its content check. A gold line that first appears in a pass prompt counts as model-written only if the model itself wrote it into `requirements.json`. G4 uses the same error definition as PILOT.md.

## Per task (gold patches, label-free)

Each requirement's verdict is shown as `id:verdict`. A requirement is UNCOVERED when it has no kept test. The decision and rule come from `scripts/decide_v1_5.py --switches r2=0,r3=0,r6=0`.

| instance_id | repo | reqs | kept p1/p2 | verdicts | V4 full pass | V2 (P) | decision | rule | min | cost |
|---|---|---:|---:|---|---|---|---|---|---:|---:|
| matplotlib__matplotlib-25479 | matplotlib/matplotlib | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | FAIL | FLAG | R5 | 12.1 | $0.0665 |
| django__django-13807 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 3.1 | $0.0290 |
| django__django-15572 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 2.6 | $0.0213 |
| django__django-16667 | django/django | 3 | 3/0 | R1:PASS, R2:PASS, R3:PASS | yes | PASS | ACCEPT | R6 | 2.8 | $0.0203 |
| pytest-dev__pytest-5809 | pytest-dev/pytest | 1 | 1/0 | R1:PASS | yes | FAIL | FLAG | R5 | 1.7 | $0.0083 |
| django__django-12965 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | PASS | ACCEPT | R6 | 4.6 | $0.0483 |
| django__django-16631 | django/django | 2 | 2/0 | R1:PASS, R2:FAIL_SINGLE | no | PASS | FLAG | R4 | 5.7 | $0.0534 |
| django__django-11095 | django/django | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 3.5 | $0.0141 |
| astropy__astropy-13398 | astropy/astropy | 4 | 4/0 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE, R4:FAIL_SINGLE | no | NOT_AVAILABLE | FLAG | R4 | 6.1 | $0.0580 |
| sympy__sympy-13480 | sympy/sympy | 2 | 2/0 | R1:PASS, R2:PASS | yes | NOT_AVAILABLE | FLAG | R8 | 40.4 | $0.0116 |

## Totals

- Minutes per task: median 4.0, max 40.4.
- Total DeepSeek cost: $0.3307.
- Gold patches with any V4 FAIL: 2 of 10. V4 full passes: 8 of 10.

## Comparison with the first pilot

The first pilot's verdicts are recomputed from its pass-1 kept tests only, as a one-pass setup would give them (any failing test → FAIL_SINGLE). Requirements are re-extracted in each pilot, so the ids need not mean the same behaviour. The first pilot's decision is the one recorded for its two-pass run in PILOT.md. The pilot 2 decision comes from `decide_v1_5.py --switches r2=0,r3=0,r6=0`.

| instance_id | pilot 1 (pass 1) verdicts | pilot 1 decision (two-pass) | pilot 2 verdicts | pilot 2 decision |
|---|---|---|---|---|
| matplotlib__matplotlib-25479 | R1:PASS, R2:PASS, R3:PASS | FLAG (R5) | R1:PASS, R2:PASS, R3:PASS | FLAG (R5) |
| django__django-13807 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | ACCEPT (R6) | R1:PASS, R2:PASS, R3:PASS | ACCEPT (R6) |
| django__django-15572 | R1:PASS, R2:PASS, R3:PASS, R4:PASS | ACCEPT (R6) | R1:PASS, R2:PASS, R3:PASS | ACCEPT (R6) |
| django__django-16667 | R1:FAIL_SINGLE, R2:PASS | FLAG (R4) | R1:PASS, R2:PASS, R3:PASS | ACCEPT (R6) |
| pytest-dev__pytest-5809 | R1:PASS | FLAG (R5) | R1:PASS | FLAG (R5) |
| django__django-12965 | R1:PASS, R2:PASS | ACCEPT (R6) | R1:PASS, R2:PASS | ACCEPT (R6) |
| django__django-16631 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:PASS, R4:PASS | FLAG (R4) | R1:PASS, R2:FAIL_SINGLE | FLAG (R4) |
| django__django-11095 | R1:NO_RESULT, R2:PASS, R3:PASS | FLAG (R7) | R1:PASS, R2:PASS | FLAG (R8) |
| astropy__astropy-13398 | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE, R4:FAIL_SINGLE | FLAG (R4) | R1:FAIL_SINGLE, R2:FAIL_SINGLE, R3:FAIL_SINGLE, R4:FAIL_SINGLE | FLAG (R4) |
| sympy__sympy-13480 | R1:PASS, R2:PASS, R3:PASS | FLAG (R8) | R1:PASS, R2:PASS | FLAG (R8) |

Machine-readable results: `reports/study_v1_5/pilot/pilot2_results.json`.
