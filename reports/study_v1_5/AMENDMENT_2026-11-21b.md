# Protocol amendment B, 21 Nov 2026

This is the second amendment to [PROTOCOL.md](PROTOCOL.md) (tag `study-v1.5-prereg`) and [PLAN.md](PLAN.md), after [AMENDMENT_2026-11-21.md](AMENDMENT_2026-11-21.md).

**When it was written.** Before any test-set run: no test-set patch has been verified, no test-set gold run exists, and no test-set label has been fetched or opened. Dev data seen so far is the Phase 6 dev gold run, the part F reruns, and arm B's outcomes under the v1.5 rules (part E and part F, label-free). Arm B's labels are read only by the Phase 7 finish script. The analysis items of audit M1–M6 that AMENDMENT_2026-11-21.md deferred are B4–B6.

Each item gives the old rule, the new rule and the reason.

## B1. System order and minimum set

- **Old.** PROTOCOL priority order: gpt-4.1-mini, Claude Sonnet 4, gpt-4.1, Gemini 2.5 Flash, o4-mini, Qwen3-Coder. PLAN C8 calls the first three weak, strong and middle. Cut rule 2: systems 3–6 run only after systems 1–2 have finished on batch 1.
- **New.** Order: gpt-4.1-mini, Claude Sonnet 4, Gemini 2.5 Flash, then gpt-4.1, o4-mini, Qwen3-Coder. The **minimum set** is the first three: gpt-4.1-mini, Claude Sonnet 4 and Gemini 2.5 Flash. The cut rules apply to this order, so systems 4–6 run only after the minimum set has finished on batch 1.
- **Reason.** gpt-4.1-mini is the calibration model (arm B), and gpt-4.1 is from the same family. A second family with a lower base rate tests whether the verifier generalizes beyond the model it was calibrated on.

## B2. Headline exclusions

- **Old.** The test set is the 500 Verified tasks minus the 92 development tasks and every `psf__requests` task, shuffled with seed `20261120`. No other task is excluded.
- **New.** A batch 1 or batch 2 id is excluded from the headline if it appears in a task manifest or id list committed before tag `study-v1.5-prereg`, other than the study's own test lists. The list and its sources are in [configs/study_v1_5/headline_exclusions.json](../../configs/study_v1_5/headline_exclusions.json). The headline excludes these ids. "All tasks" is a sensitivity analysis.
  - **What counts.** Files that something was actually run on count: pilot, calibration, probe and study manifests, run inputs, and experiment reports. Whole-dataset lists don't count: `configs/e2e/cohorts/verified500.json`, and task-prep `eligibility.json`, `image_sizes.json` and `projection.json`. Counting them would exclude all 108 batch ids.
  - **The `verified200.json` check.** The cohort definition `configs/e2e/cohorts/verified200.json` would count only if a run had used it as input. I searched every local worktree's `runs/` (run headers and run metadata), `configs/`, `scripts/`, `src/` and reports. It appears only in the cohort-definition and size-projection code, and in `reports/next_phases/task_prep/`. That report states: "No image layers were pulled and no archives were built for the 200/492 expansion" and "No expansion is authorized or attempted." No run used it, so its ids are not excluded on its account.
  - **Result.** 5 ids are excluded: 2 in batch 1 (`astropy__astropy-12907`, `scikit-learn__scikit-learn-12973`) and 3 in batch 2 (`django__django-16899`, `mwaskom__seaborn-3187`, `pylint-dev__pylint-6386`). Each is in `manifests/pilot.csv`, and most also appear in calibration, probe or experiment files.
- **Reason.** A task that was used during development can't count as unseen. Excluding these tasks keeps the headline on tasks the verifier was never tuned on, and the all-tasks sensitivity analysis shows whether the exclusion matters.

## B3. Headline scope

- **Old.** Batch 2 runs only if time allows (Phase 12b, cut rule 3). Results at the cutoff use only runs that are sealed and labelled (cut rule 4). There was no rule for a batch 2 that is only partly done.
- **New.** The headline is batch 1, plus batch 2 if all three minimum-set systems are sealed on batch 2 by the analysis cutoff (Wed 25 Nov 18:00). Otherwise batch 2 is reported separately.
- **Reason.** Pooling a batch 2 that has only some of the systems would change the system mix between batches and bias the pooled rates. Requiring the whole minimum set keeps the headline's system mix the same.

## B4. Added analyses

- **Old.** PROTOCOL §6: H1–H3 and the RQ tables.
- **New.** These analyses are added, all from stored signals and labels:
  - lift over an accept-weighted base rate;
  - a within-task comparison on tasks where systems disagree;
  - false-accept rate and recall, with CIs;
  - v1.5 against a V1+V2-only baseline;
  - V4 on correct public patches, against gold on the same tasks;
  - H1–H3 restricted to tasks with no generator recall (amendment A3).
- **Reason.** Each answers a question the original analyses leave open:
  - The plain base rate ignores which systems produce more patches.
  - Agreement across systems on a task confounds task difficulty with verifier quality.
  - Precision alone hides how many wrong patches are accepted and how many correct ones are missed.
  - V3 and V4's added value needs a baseline without them.
  - V4's cost on correct agent patches needs a comparison with gold on the same tasks.
  - Generator recall could inflate V4.

## B5. H3 reporting

- **Old.** H3: "v1.5 REJECTs at most 3% of test-set gold patches (point estimate: at most 1 of batch 1's 60). Report the count and Wilson upper bound." It reads as pass/fail.
- **New.** H3 is reported as a point estimate (gold REJECTs ÷ gold patches) with its Wilson 95% upper bound. It is not a pass/fail test.
- **Reason.** With 60 gold patches, the 3% threshold sits between 1 and 2 REJECTs. A pass/fail reading would rest on one patch, while the estimate and bound show the uncertainty.

## B6. Labels

- **Old.** PLAN Phase 13: fetch the official per-instance reports for each sealed run's ids and record their sha256. Our grader runs on a second machine as time allows, to measure agreement. o4-mini is graded by our grader only.
- **New.**
  - Before an official label is used, the patch hash in its log must match our sealed patch for that (system, id). A mismatch means no label, with the reason recorded.
  - o4-mini is out of the pooled numbers.
  - Grader agreement is measured on `random.Random(20261121).sample(population, 30)`. The population is the non-empty (system, id) pairs from batch 1 for the minimum set, read from the committed Phase 2 patch manifests only, and sorted by (system folder, id). The sample is fixed now in [configs/study_v1_5/grader_agreement_sample.json](../../configs/study_v1_5/grader_agreement_sample.json): a population of 177 pairs, with 13 gpt-4.1-mini, 10 Claude Sonnet 4 and 7 Gemini 2.5 Flash drawn.
  - Official labels are fetched only after tag `study-analysis-frozen`.
- **Reason.** A label only says something about the patch it graded. o4-mini has no official labels, so it would pool our grader's labels with official ones. A sample fixed before any grading can't be chosen to look good. Fetching labels after the analysis freeze keeps the analysis blind.

## B7. Calibration model

- **Old.** No statement.
- **New.** gpt-4.1-mini is the calibration model. Phase 7's adoption thresholds were set on its arm B patches. Claims about other models rest on Claude Sonnet 4 and Gemini 2.5 Flash.
- **Reason.** Results on the calibration model are optimistic by construction, so generalization has to be shown on models the rules were not tuned on.

## B8. Patches that add `sitecustomize.py` or files under `v4_repro/`

- **Old.** V1 does not look at either path.
- **New.** V1 blocks a patch that adds, or renames to, any `sitecustomize.py`, or any file under the top-level `v4_repro/` directory. The violation is `HARNESS_FILE_EDIT`, which counts as prohibited manipulation and gives integrity FAIL (R1 REJECT). The code is `INJECTION_PATTERNS` in `src/reliability/verifier/integrity.py`, with `tests/unit/test_v1_injection_paths.py`.
- **Reason.** Python imports a `sitecustomize.py` on its path when it starts, and V4 places its frozen tests in `v4_repro/`. A patch adding either could run code inside the verifier's own test processes, or shadow V4's tests.
- **Effect on dev data.** No arm B, dev gold or test-set patch adds either path. One public dev patch does: o4-mini's `pylint-dev__pylint-7277` touches `sitecustomize.py`. It is a dev-set public patch, used only in Phase 9, which is descriptive.

## B9. Phase 7 stopped on a false systemic alarm (21 Nov 2026)

**When it was written.** After the first Phase 7 run stopped and before any adoption result existed. No test-set data exists. Arm B's labels were already known before the first Phase 7 run. The fixes were written from that run's label-free outcomes and the code, without opening labels.

**What happened.** The first Phase 7 run (`runs/study_dev_armb`, tag `study-dev-armb-launch`) stopped with `STOPPED_SYSTEMIC` after 15 of 51 tasks, because 3 of 15 tasks (20%) carried the infrastructure flag. None was a machine failure:
- `django__django-13158`: the patch does not apply. `git apply` in the container rejects it ("patch with only garbage at line 5"). V1 had no apply check against the task tree, so the rejection surfaced as a V3 executor exception (`ContainerError`), which counted as infrastructure. Patch-caused.
- `django__django-14140`: the patched tree cannot import Django (`TypeError` in `register_lookup`), and the base tree collects cleanly except for the prelisted GIS guard modules. The run-health block counted as infrastructure. Patch-caused.
- `django__django-15103`: `tests/forms_tests/tests/test_forms.py` fails to import (`No module named 'tests'`) identically on both trees, a collector gap. A7 did not exclude it, because a prelisted GIS stage on the same task disabled the paired check. Counted as infrastructure.

The finish script then ran on the partial run. The adoption script crashed on a missing completion file, and the fallback failed report was committed (`a187e88`).

**Fixes (code: part G, [build/PART_G.md](build/PART_G.md)).** Each item gives the old rule and the new rule.

1. **Patch application.** *Old:* V1 checked the patch text only; a patch `git apply` rejects reached V2, V3 and V4 as a container exception. *New:* V1 runs `git apply --check` in the task's verified pristine container, built by the same function the container uses to apply the patch, so the two cannot disagree (the host's git, 2.25.1, differs from the images' git, 2.34.1, so a host check could). A rejection is V1 FAIL with `does_not_apply` (R1 REJECT); V2 and V3 are not run and are NOT_AVAILABLE with absence error and reason `PATCH_DOES_NOT_APPLY`, not infrastructure; V4 has nothing to check. A rejection met later in V2 or V3 is recorded the same way. If the check itself cannot run, V1 records `apply_check: UNAVAILABLE:<type>` and the other layers run.
2. **Infrastructure flag.** *Old:* every run-health (G1) block and every V2/V3 executor exception set the infrastructure flag. *New:* a G1 block is attributed:
   - **infrastructure**: a machine or harness failure on either tree (a verifier exception, Docker, container start, disk, out of memory). Only this sets the flag;
   - **patch**: the base tree is clean (G1 READY, or blocked only by prelisted environment guards that lost their pair proof because the patched tree failed) and the patched tree is blocked, as in django-14140;
   - **environment**: both trees are blocked by the code or the image after A7, a collector or dependency gap.
   Patch and environment blocks are V2 NOT_AVAILABLE with absence error and infrastructure false, so they never qualify for R6 (R6's V2 branch accepts only nothing-to-check and incomplete). V2 and V3 executor exceptions other than a rejected patch stay infrastructure. `V2_WALL_TIME_3H` and `REPLAY_MISMATCH` keep their infrastructure flag, because this rule cannot attribute them; under item 4 they no longer stop a run.
3. **A7 on the Django runner.** *Old:* any prelisted stage (such as a GIS guard module) made the paired check give up. *New:* prelisted stages, which G1 already allows and which never block, are skipped by the paired check. A module that fails to import with the same exception type on both trees is excluded and recorded, and V2 runs the rest (django-15103).
4. **Run stops.** *Old:* `STOPPED_SYSTEMIC` when the last 3 tasks, or at least 20% of at least 10 tasks, had the infrastructure flag. *New* (this replaces both thresholds): a task can never stop a run. A task's exception is recorded on that task (`task_error.json`; the run's `task_errors`; run status `COMPLETE_WITH_TASK_ERRORS`, which no decision script accepts) and the run moves on. Only machine-level failures stop it (`STOPPED_MACHINE`): the Docker daemon is unreachable or less than 20 GB (20·10⁹ bytes) is free where the run writes or where Docker stores containers, both checked before each task, or 3 consecutive tasks whose container starts all failed. The budget cap, an interrupt and a V4-reuse integrity breach (the frozen V4 source changed, or a generator call was attempted) remain run stops: none is a task failure, and the V4 freeze forbids continuing after the last.
5. **Finish robustness.** `decide_v1_5.py` and `phase7_adoption.py` report a missing or incomplete input instead of crashing: `decide_v1_5.py` exits 2 with one line; the adoption script writes a failed ADOPTION.md listing each gate. Both can merge tasks kept from a stopped sealed run with a rerun, and refuse unless the merged set is exactly the 51 arm B ids with no task from both runs.
6. **Preflight.** `scripts/preflight.py` runs only V1's apply check, V3 and V2's run-health collection on both trees, in the container, with no test execution, no decision and no label. A run is launched only if it reports no run-stopping condition and no unclassified exception.

**Effect on the sealed records (step 6, [build/part_g_rederive.json](build/part_g_rederive.json)).**
- Dev gold, 51 records (Phase 6, with pytest-7236 and pytest-7521 from the part F rerun): every patch applies in its container; no V1–V4 outcome, absence, infrastructure flag or decision (v1.4.1, v1.5 switches off, all on) changes.
- Arm B, the 15 completed tasks of the stopped run: 11 are identical in every V1–V4 outcome, absence and flag. django-13158 becomes V1 FAIL (does not apply), V2 and V3 `PATCH_DOES_NOT_APPLY`, V4 nothing to check, infrastructure flag cleared. django-14140 keeps V2 NOT_AVAILABLE (error), attributed to the patch, infrastructure flag cleared. django-15103: A7 now excludes `test_forms.py`, so V2 must rerun. django-13023 keeps its outcomes (V1 FAIL, V2–V4 NOT_AVAILABLE) and task flag (false), but its V4 changes from a `ContainerError` with the infrastructure flag to nothing to check, because its patch does not apply in the container either. Under the new rules none of the 15 would count toward a stop.

**Phase 7 continues as a deviation from A5.**
- *A5 says:* one restart per run, from scratch, for infrastructure-only failures.
- *Instead:* the stopped run stays sealed and read-only (seal sha256 `81fa418ab136416d59b954f336921a2425cfc60f200785052ded0b14ec452a28`). The 11 tasks whose outcomes and flags are identical under the new code are kept from it. The other **40** are rerun in `runs/study_dev_armb_2` (tag `study-dev-armb-launch-2`): django-13158, django-14140 and django-15103; the 36 tasks that never started; and django-13023, whose V4 signal and flag change. The plan named 12 kept and 39 rerun; django-13023 moved to the rerun under the rule that any task whose outcomes or flags differ is rerun. Lists: `configs/study_v1_5/phase7_kept_ids.json`, `configs/study_v1_5/phase7_rerun_ids.json`. The finish script merges the two, checks the merged set is exactly the 51 ids, records each task's run in ADOPTION.md and computes adoption on the merged 51.
- *Why:* the stop was not an infrastructure failure, so A5's restart does not cover it, and no adoption result had been produced. Arm B's labels were known before the run, so the rerun cannot be used to pick a result, and the kept tasks are byte-for-byte the records the first run sealed.

**Gates before the rerun.** Unit: 2,042 tests, 2,013 passed, 6 skipped, 6 failed, 17 errors; the failing and erroring IDs equal `unit_baseline_phase1.json` (no new failures or errors). Truth table: `test_policy_v1_5.py` 114 passed; 17,280 cases, differing from v1.4.1 only in the 16 A4 (ii) cases (the policy code is unchanged). v1.4.1 replay: `scripts/replay_paired_skip_arm_b.py` matched 51/51 stored decisions and 51/51 V2 outcomes; v1.5 switches off 51/51; the log is byte-identical to part F's. V4_FREEZE.md: all nine recorded sha256 values match. Preflight of arm B's 51 patches (`runs/study_v1_5/preflight_armb/`): 51/51 checked in 15.7 minutes with 6 workers; 0 run-stopping conditions, 0 unclassified exceptions, 0 exceptions of any kind, 0 infrastructure flags.
