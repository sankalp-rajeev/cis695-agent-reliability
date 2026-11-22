# Phase 3 Part G: fixes after the false systemic stop of Phase 7 (amendment B9)

The first Phase 7 run (`runs/study_dev_armb`) stopped at 15 of 51 tasks on `STOPPED_SYSTEMIC`. Two patch-caused failures and one collector gap had been counted as infrastructure. The rules are amendment item B9 in [AMENDMENT_2026-11-21b.md](../AMENDMENT_2026-11-21b.md). Nothing listed in [V4_FREEZE.md](../V4_FREEZE.md) changed: all nine recorded sha256 values still match. `configs/` gains only the two Phase 7 id lists. Every change started with a failing test. No labels were opened, and no test-set data exists.

## 1. Patch application (V1)

- `container.git_apply_command(reverse=, check=)` builds the one `git apply` command. `TaskContainer.set_patched` applies with it, and the new `TaskContainer.apply_check()` checks with it (`git apply --check -`), so the two cannot disagree.
- `run_v1_4_1.container_apply_check` starts the task's frozen image, verifies its pristine source (receipt `verification/v1_pristine_source_receipt.json`) and runs `apply_check()`. It runs in the container, not on the host, because the host's git (2.25.1) is not the images' git (2.34.1).
- `verify_task`: a rejection adds `does_not_apply` to V1 (FAIL, R1 REJECT) and records `apply_check: FAIL`. V2 and V3 are then not run: NOT_AVAILABLE, absence error, reason `PATCH_DOES_NOT_APPLY`, infrastructure false. V4 sees `patch_applies: false` and has nothing to check. An unparseable patch keeps V2 `NO_SELECTION` and V3 `NO_PARSEABLE_PATCH`, as before.
- A rejection that still reaches the container in V2 or V3 is a new `PatchApplyError` (a `ContainerError`). G1 re-raises it, and `verify_task` records it exactly as above.
- If the apply check cannot run, V1 records `apply_check: UNAVAILABLE:<type>` and keeps its other checks; V2 and V3 run. A source-integrity error is never swallowed.

## 2. Infrastructure attribution

`run_v1_4_1.g1_attribution(healths)` classifies a G1 run-health block:
- **infrastructure**: a stage on either tree with status ERROR or INTERRUPTED (a verifier exception), exit code 137, or a Docker, container-start, disk or out-of-memory message;
- **patch**: the base tree is clean (READY, or blocked only by stages that are prelisted or whose generic rule was revoked because the patched tree failed) and the patched tree is blocked;
- **environment**: anything else, i.e. both trees blocked by the code or the image.

`g1_with_paired_exclusion` (G1 plus A7, split out of `_run_v2` so the preflight runs the same code) attaches it to the `RunHealthError`. `verify_task` records `attribution` and sets `infrastructure` only for infrastructure. A patch or environment block is absence error, which R6 never accepts; a test pins that with every switch on.

## 3. A7 on the Django runner

`paired_collection_exclusions` skips stages with `allowed_exception` (prelisted guards such as the GIS module, which G1 already allows and which never block), instead of giving up. A tree with no other blocking module still gives no exclusion.

## 4. Run stops (7a replaces the systemic guard)

`e2e_runner.run_batch` no longer has `systemic()`.
- A task's exception, including a per-task source-integrity error, is written to `tasks/<id>/task_error.json` and to `task_completion.json` (`complete: false`). It is listed in `completion.json` `task_errors`, and the run moves on. A run with task errors ends `COMPLETE_WITH_TASK_ERRORS`, which `decide_v1_5.py` refuses.
- `machine_status(output)` is checked before each task. It reports the Docker daemon unreachable (`docker info`), or less than 20·10⁹ bytes free at the run folder or at Docker's root. `container.START_EVENTS` records every container start; three consecutive tasks whose starts all failed stop the run. Either case gives `STOPPED_MACHINE`. `run_e2e.py` passes `machine_check=lambda: machine_status(output)`.
- Still run stops: the budget cap (`BudgetCap`), an interrupt, and `V4ReuseError` (the frozen V4 source changed or a generator call was attempted). A run-level reuse check before the first task is unchanged.
- Changed tests: the three `test_e2e_runtime.py` tests of the old systemic and integrity-abort behaviour now assert the new behaviour, and the runtime helper stubs the apply check.

## 5. Finish robustness

- `decide_v1_5.py`: `main` reports `decide_v1_5: cannot decide <run>: <error>` on stderr and exits 2, with no traceback. New `--kept-run`, `--kept-ids`, `--expect-ids` (and `decide_run(kept=, expected_ids=)`) merge tasks kept from a sealed stopped run (seal must match; each kept task needs a sealed completion file saying complete). It refuses a task present in both runs and a merged set that is not exactly the expected ids. The CSV gains `source_run` only when merging, so existing outputs are byte-identical.
- `runs/study_v1_5/phase7_adoption.py` (the run 1 version is kept as `phase7_adoption_run1.py`): it takes `--rerun-run`, `--kept-run` and `--kept-ids`, adds a merged-set gate, checks both seals and both runs' zero-generation evidence, and records each task's source run in ADOPTION.md ("Task sources") and in adoption.json. Any missing or incomplete input gives a failed ADOPTION.md listing the gates, never a crash.
- `runs/study_v1_5/phase7_armb_2_finish.sh` has the same steps as run 1's finish script, for the merged set. With `DRY_RUN=1 DRY_DIR=…` every output goes to `DRY_DIR` and a copy of STATUS.md is edited, with no chmod, commit or push.

**Dry runs (7c):**
- **Stopped run**, `OUT=runs/study_dev_armb` (outputs in `runs/study_v1_5/phase7_armb_2_dryrun_partial/`): exit 0. Seal MATCH, unchanged (`81fa418a…`). `decide_v1_5` reported "run seal is not COMPLETE" (exit 2). Adoption wrote a failed ADOPTION.md (sealed and merge gates failed, every missing and duplicate task listed) without reading labels. The STATUS.md copy row became ⛔. The run folder and the working tree were untouched.
- **Complete run**, a stand-in sealed COMPLETE run of the 40 rerun ids under `runs/study_v1_5/dryrun_armb2_complete/`, with run 1's header and Phase 6 records copied in as stand-in data (outputs in `runs/study_v1_5/phase7_armb_2_dryrun_complete/`): exit 0. All five gates computed and passed: sealed, merged set 11 + 40 = 51 with no problems, zero generation, audit (nothing in scope), and labels with patch hashes checked. Decisions on the merged 51 were written, the Task sources table names both runs, and the STATUS.md copy was updated. The stand-in's adoption numbers are meaningless and were not looked at.

## 6. Preflight (7b)

`scripts/preflight.py` reuses the verifier's own functions: `integrity_signal` and `select_tests` on the archive, `container_apply_check`, `run_v3`, and `g1_with_paired_exclusion` under the generic-rule scope (G1 and A7, collection only). It runs tasks in parallel processes (`--workers`) and checks `machine_status` before and after. It writes `preflight_rows.json`, `preflight_summary.json` and `preflight_table.md`, and exits 0 only with no run-stopping condition and no unclassified exception. Exception classes: `PatchApplyError` → patch does not apply; `ContainerStartError` → container start (three in a row are run-stopping); anything else → unclassified. Unit tests: `tests/unit/test_preflight.py`.

Run on arm B's 51 patches (`runs/study_v1_5/preflight_armb/`, log `runs/study_v1_5/preflight_armb.log`): **pass**. 51/51 tasks in 15.7 minutes with 6 workers; 0 run-stopping conditions, 0 unclassified exceptions, 0 exceptions, 0 infrastructure flags. Listed (all classified):

| task | V1 apply | V3 | V2 G1 | attribution |
|---|---|---|---|---|
| django__django-13023 | FAIL | not run | not run | – |
| django__django-13158 | FAIL | not run | not run | – |
| django__django-14140 | PASS | FAIL | BLOCKED (prelisted_missing_evidence) | patch |
| django__django-16667 | FAIL | not run | not run | – |
| sphinx-doc__sphinx-10323 | PASS | FAIL | BLOCKED (zero_collection_without_recorded_module_skip) | patch |

django-15103 is G1 READY after A7 excludes `tests/forms_tests/tests/test_forms.py`. django-16667 (not reached by run 1) is a third patch that does not apply in its container.

## 7. Sealed records under the new classification (step 6)

`scripts/part_g_rederive.py` recomputes each stored record as part G would record it, with the container apply check run live in each task's image (the only part that needs Docker) and the G1 attribution and A7 recomputed from the stored health. Output: [part_g_rederive.json](part_g_rederive.json).

**Dev gold (51; pytest-7236 and pytest-7521 from `runs/study_dev_gold_f`):** 51 of 51 apply in their containers. No V1–V4 outcome, absence, reason, infrastructure flag or decision (v1.4.1, v1.5 switches off, v1.5 all on) changes. Infrastructure-flagged tasks: 0 before, 0 after.

**Arm B, 15 completed tasks of the stopped run** (outcomes and flags only; old → new):

| task | container apply | V1 | V2 | V3 | V4 | task infrastructure flag | Phase 7 |
|---|---|---|---|---|---|---|---|
| astropy__astropy-13398 | PASS | PASS → PASS | NOT_AVAILABLE (nothing_to_check, NO_SELECTION) → NOT_AVAILABLE (nothing_to_check, NO_SELECTION) | PASS → PASS | PASS → PASS | no → no | kept |
| astropy__astropy-14365 | PASS | PASS → PASS | PASS → PASS | PASS → PASS | PASS → PASS | no → no | kept |
| astropy__astropy-14508 | PASS | PASS → PASS | NOT_AVAILABLE (nothing_to_check, NO_SELECTION) → NOT_AVAILABLE (nothing_to_check, NO_SELECTION) | PASS → PASS | NOT_AVAILABLE (nothing_to_check, UNCOVERED) → NOT_AVAILABLE (nothing_to_check, UNCOVERED) | no → no | kept |
| astropy__astropy-7606 | PASS | PASS → PASS | PASS → PASS | PASS → PASS | PASS → PASS | no → no | kept |
| django__django-11095 | PASS | PASS → PASS | NOT_AVAILABLE (incomplete) → NOT_AVAILABLE (incomplete) | PASS → PASS | PASS → PASS | no → no | kept |
| django__django-12965 | PASS | PASS → PASS | NOT_AVAILABLE (incomplete) → NOT_AVAILABLE (incomplete) | PASS → PASS | FAIL → FAIL | no → no | kept |
| django__django-13023 | FAIL | FAIL → FAIL | NOT_AVAILABLE (error, NO_SELECTION) → NOT_AVAILABLE (error, NO_SELECTION) | NOT_AVAILABLE (error, NO_PARSEABLE_PATCH) → NOT_AVAILABLE (error, NO_PARSEABLE_PATCH) | NOT_AVAILABLE (error, V4_EXCEPTION:ContainerError) → NOT_AVAILABLE (nothing_to_check) | no → no | rerun |
| django__django-13158 | FAIL | PASS → FAIL | NOT_AVAILABLE (nothing_to_check, NO_SELECTION) → NOT_AVAILABLE (error, PATCH_DOES_NOT_APPLY) | NOT_AVAILABLE (error, EXECUTOR_EXCEPTION:ContainerError) → NOT_AVAILABLE (error, PATCH_DOES_NOT_APPLY) | NOT_AVAILABLE (error, V4_EXCEPTION:ContainerError) → NOT_AVAILABLE (nothing_to_check) | yes → no | rerun |
| django__django-13212 | PASS | PASS → PASS | NOT_AVAILABLE (incomplete) → NOT_AVAILABLE (incomplete) | PASS → PASS | FAIL → FAIL | no → no | kept |
| django__django-13297 | PASS | PASS → PASS | PASS → PASS | PASS → PASS | FAIL → FAIL | no → no | kept |
| django__django-13786 | PASS | PASS → PASS | FAIL → FAIL | PASS → PASS | PASS → PASS | no → no | kept |
| django__django-13807 | PASS | PASS → PASS | NOT_AVAILABLE (incomplete) → NOT_AVAILABLE (incomplete) | PASS → PASS | PASS → PASS | no → no | kept |
| django__django-13820 | PASS | PASS → PASS | PASS → PASS | PASS → PASS | NOT_AVAILABLE (nothing_to_check, UNCOVERED) → NOT_AVAILABLE (nothing_to_check, UNCOVERED) | no → no | kept |
| django__django-14140 | PASS | PASS → PASS | NOT_AVAILABLE (error, RUN_HEALTH_G1:prelisted_missing_evidence) → NOT_AVAILABLE (error, RUN_HEALTH_G1:prelisted_missing_evidence) | FAIL → FAIL | NOT_AVAILABLE (nothing_to_check, NO_RESULT) → NOT_AVAILABLE (nothing_to_check, NO_RESULT) | yes → no | rerun |
| django__django-15103 | PASS | PASS → PASS | NOT_AVAILABLE (error, RUN_HEALTH_G1:module_import_dependency_failure) → NOT_AVAILABLE (error, RUN_HEALTH_G1:module_import_dependency_failure) | PASS → PASS | FAIL → FAIL | yes → rerun | rerun |

"rerun" for django-15103 means A7 now excludes `tests/forms_tests/tests/test_forms.py`, so V2 runs and its outcome can only come from the rerun. None of the 15 would count toward a stop under the new rules: none has a machine-level failure.

## 8. Gates

Unit: 2,042 tests, 2,013 passed, 6 skipped, 6 failed, 17 errors; the failing and erroring IDs equal `unit_baseline_phase1.json` (no new failures or errors). Truth table: `test_policy_v1_5.py` 114 passed; 17,280 cases, differing from v1.4.1 only in the 16 A4 (ii) cases (the policy code is unchanged). v1.4.1 replay: `scripts/replay_paired_skip_arm_b.py` matched 51/51 stored decisions and 51/51 V2 outcomes; v1.5 switches off 51/51; the log is byte-identical to part F's. V4_FREEZE.md: all nine recorded sha256 values match. Preflight of arm B's 51 patches (`runs/study_v1_5/preflight_armb/`): 51/51 checked in 15.7 minutes with 6 workers; 0 run-stopping conditions, 0 unclassified exceptions, 0 exceptions of any kind, 0 infrastructure flags.
