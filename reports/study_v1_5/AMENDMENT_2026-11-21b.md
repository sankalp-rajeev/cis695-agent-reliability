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
