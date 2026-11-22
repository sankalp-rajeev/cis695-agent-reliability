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

## B10. V2 stops after three confirmed regressions (22 Nov 2026)

**When it was written.** After Phase 11 (batch 1 gold) and before any exam system patch was verified. The code changes after tag `v1.5-frozen` and is frozen again at tag `v1.5-frozen-2`.

- **Old.** V2 confirms every regression candidate on both trees (three isolated runs each), so a patch that breaks many tests spends most of V2's time confirming failures that cannot change the outcome.
- **New.** V2 stops confirming after 3 confirmed regressions: passed on base, failed on patched, and reproduced in all three isolated runs on each tree. V2 is then FAIL and records `regressions >= 3, stopped early`, the confirmed regressions, the candidates not confirmed, the tests executed and the confirmation runs so far (`early_exit` in the V2 findings). Every V2 policy (live and replayed) uses the same stop, so all policies stop at the same point of the one captured call sequence. Below 3 confirmed regressions nothing changes. Code: `RegressionConfig.stop_after_regressions`, `guarded_v2.V2_STOP_AFTER_REGRESSIONS = 3`; tests: `tests/unit/test_v2_early_exit.py`.
- **Outcome check on every stored V2 record** (`runs/study_v1_5/b10_outcome_check.json`): 168 records (dev gold 51 and the part F pair, arm B run 1 15 and run 2 40, Phase 11 gold 60); 141 have captured V2 executions, and replaying each with the primary accounting reproduces its stored outcome. Five tasks have 3 or more confirmed regressions, all stored V2 FAIL, and with the stop each is still FAIL: arm B run 1 django-13786 (5 confirmed), arm B run 2 django-16631 (19), matplotlib-20488 (90), matplotlib-24637 (56), pylint-7277 (4). No gold record has 3 or more. No task's outcome after its third confirmed regression is anything but FAIL.
- **Reason.** Outcome-preserving on every stored record, and checked on all of them before any exam system patch was verified. It bounds V2's time on badly broken patches, which the exam systems produce more often than gold.

## B11. Base-commit git history in the reference audit; astropy-7671 out of the headline (22 Nov 2026)

**When it was written.** After the Phase 11 audit failed and before any exam system patch was verified.

**What happened.** The Phase 11 A3 audit failed on 5 GOLD_LINE_LEAK lines, all in `astropy__astropy-7671`, requirements conversation, message 10. They are the output of `git show 48550710d -- astropy/utils/introspection.py …` and `git show 5ac728616 -- …`, commits that are ancestors of the task's base commit: the gold patch restores code an earlier commit removed. No future commit is reachable in the image. The two kept frozen tests contain none of the lines, were written in the pass 1 conversation, which never read history, and assert only behaviour stated in the issue (`minversion` with `1.14.3` against `1.14dev`). Base-commit history is legitimate input, like the base tree.

- **Old (A3).** A gold line whose first appearance in a conversation is not model-written is GOLD_LINE_LEAK, confirmed.
- **New.** Such a line is **BASE_HISTORY**, recorded per task and not failing, when its first appearance is a tool output whose command only reads git history (every segment is `cd`, or `git show` / `git log` piped only through `head`, `tail`, `sed -n 'N,Mp'` or `grep`) and the commit it came from (the nearest `commit <sha>` header above it, else every revision the command names) is verified, by git in the task's pinned image with no network, to be an ancestor of the task's base commit. Lines from non-ancestor commits, package caches, any other command or any other non-model source, or whose ancestry cannot be verified, stay GOLD_LINE_LEAK. Code: `leakage.history_revisions`, `leakage.verify_ancestors`; tests: `tests/unit/test_reference_base_history.py`.
- **Re-audit (read-only, sealed runs).** Phase 11 (`runs/study_test_gold_b1`): exit 0, 5 BASE_HISTORY lines, all in astropy-7671, 0 leaks; every other task's summary unchanged. Phase 6 (`runs/study_dev_gold`): exit 0, output unchanged. The Phase 11 audit gate now passes; see the addendum in [test_gold_b1/TEST_GOLD_B1.md](test_gold_b1/TEST_GOLD_B1.md).
- **Headline.** `astropy__astropy-7671` is added to [configs/study_v1_5/headline_exclusions.json](../../configs/study_v1_5/headline_exclusions.json) (batch 1 now excludes 3, total 6): its generator read gold lines in pre-base history. It stays in the all-tasks sensitivity analysis. Decided before any exam system patch was verified.
- **Reason.** The rule was refined after this failure. A3 is meant to catch gold lines the generator could not have seen in its inputs, and the base commit's own history is part of those inputs. Excluding the task from the headline keeps the headline free of a task where the generator saw the fix's lines at all.

**Gates before Phase 12.** Unit gate: 2,072 tests, 2,043 passed, 6 skipped, 6 failed, 17 errors; failing and erroring IDs within `unit_baseline_phase1.json` (no rerun needed). Truth table: `test_policy_v1_5.py` 114 passed. `configs/verifier/v1_5.yaml` is byte-identical to tag `v1.5-frozen` (switches r2, r6, r6b on, unchanged), and the other eight V4_FREEZE.md sha256 values match.

## B12. V1 applies patches exactly as the SWE-bench grader (22 Nov 2026)

**When it was written.** After the Phase 12 preflight and before any exam system patch was verified. The preflight checks format only: it makes no decision and reads no label.

**What happened.** The preflight of the 180 batch 1 exam patches found that the v1.0.0 submissions of Claude Sonnet 4 and Gemini 2.5 Flash (`info.submission`, fetched unchanged) end without a final newline, and 14 Gemini patches have text before the first `diff --git`. V1 checked with a single `git apply`, which rejects both, so every non-empty Claude (60) and Gemini (57) patch would have been V1 FAIL (R1 REJECT). The official grader applies patches more leniently.

- **Old (B9).** V1 and the container apply the patch with one `git apply`; a rejection is V1 FAIL.
- **New.** V1's apply check and the container's patch application are exactly the installed SWE-bench 5.0.2 grader's sequence (`swebench/harness/run_evaluation.py`, `GIT_APPLY_CMDS`): the stored patch bytes are written unchanged to `/tmp/patch.diff` (no newline fix, no stripping), then `git apply --verbose`, `git apply --verbose --3way`, `git apply --verbose --reject` and `patch --batch --forward --fuzz=5 -p1 -i` run in order in `/testbed`, with the grader's `git checkout -- . ; git clean -fd` before every attempt after the first, and `git apply --check --reverse` if none exits 0. A patch applies iff one command exits 0, and V1 records which (`apply_command`). Reverting to base restores the pristine tree saved before the first application (files, new files including `.orig` backups, and the git index), whichever command applied the patch. V1's AST check skips text before the first file header. Code: `container.HARNESS_APPLY_COMMANDS`, `TaskContainer.set_patched`, `apply_check`; tests: `tests/unit/test_harness_apply.py` (clean, no final newline, text before the diff, needs fuzz, fails every command, bytes unchanged, already applied, constants equal the installed grader's).
- **Dev impact** (`runs/study_v1_5/b12_dev_impact.json`). All 51 dev gold patches apply by `git apply --verbose`, as before. Of arm B's 51 (merged set), one result changes: django-13158, which `git apply` rejected, now applies by `patch --batch --forward --fuzz=5 -p1 -i`. django-13023 and django-16667 still fail every command. django-13158 was re-verified in `runs/study_dev_armb_3` (audited, tag `study-dev-armb-launch-3`, V4 reused from `runs/study_dev_gold`, 0 generator and 0 ledger calls, seal MATCH): V1 PASS, V2 NOT_AVAILABLE (nothing to check), V3 PASS, V4 FAIL, decision FLAG.
- **Adoption** ([ADOPTION_B12.md](ADOPTION_B12.md), `adoption_b12.json`), recomputed with the same pre-set rules on the merged 51 (11 from `runs/study_dev_armb`, 39 from `runs/study_dev_armb_2`, django-13158 from `runs/study_dev_armb_3`): all gates pass, the chosen V4 and every switch's result are unchanged, and the adopted set is still **r2, r6, r6b**. The switches in `v1_5.yaml` are unchanged.
- **Reason.** V1 should reject a patch only if the grader that produces the labels cannot apply it; a stricter apply check measures the patch's serialization, not the patch.

**Gates.** Unit gate: 2,082 tests, 2,053 passed, 6 skipped, 6 failed, 17 errors; failing and erroring IDs within `unit_baseline_phase1.json` (no rerun needed). Truth table: 114 passed. `v1_5.yaml` identical to `v1.5-frozen`; the other eight V4_FREEZE.md hashes match. Frozen at tag `v1.5-frozen-2`.
