# Study plan: verifier v1.5 on 200 tasks

Status: plan, not yet pre-registered. Phase 1 turns the decisions below into `PROTOCOL.md` and tags it.
Branch: `study/v1.5-200`, created from `origin/experiment/paired-skip`. Worktree: `~/projects/wt-study`.

## 1. Goal

Show, on tasks the rules were never tuned on, that the verifier catches wrong patches and accepts correct ones, across several repair models.

The headline result is the **108 new test tasks**. The 92 existing tasks are the **development set**: the v1.5 rules are built and calibrated there.

## 2. What this study is not

- No new repair-agent runs. Patches come from public SWE-bench submissions and the gold reference patches. Arm A (DeepSeek repair) is dropped.
- No rule changes after the v1.5 freeze tag. If something is wrong after the tag, stop and report; do not patch and continue.
- No labels, grader output or `FAIL_TO_PASS`/`PASS_TO_PASS` are read before a run is sealed.

## 3. Data

| Set | Tasks | Patches | Role |
|---|---|---|---|
| Development | the 92 arm B tasks (`task_specs_83.json` + `task_specs_add9_e2e_v141.json`, same manifest as arm B) | gold, arm B's 51 gpt-4.1-mini patches, 6 public systems | build and calibrate v1.5; descriptive results |
| Test | 108 new SWE-bench Verified tasks, seeded random draw | gold, 6 public systems | headline result |

**Public systems** (`s3://swe-bench-submissions/bash-only/<name>/trajs/<id>/<id>.pred`, field `model_patch`; all used mini-SWE-agent, only the model differs):

| Priority | System folder | Resolved on all 500 |
|---|---|---|
| 1 | `20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14` | 23.9% |
| 2 | `20250726_mini-v1.0.0_gpt-4.1-2025-04-14` | 39.6% |
| 3 | `20250726_mini-v1.0.0_claude-sonnet-4-20250514` | 64.9% |
| 4 | `20250726_mini-v1.0.0_gemini-2.5-flash` | 28.7% |
| 5 | `20250726_mini-v1.0.0_o4-mini-2025-04-16` | 45.0% |
| 6 | `20250802_mini-v1.0.0_qwen3-coder-480b-a35b-instruct` | 55.4% |

**Minimum set if time runs short:** gold plus priorities 1–3 (weak, middle, strong) on both sets. Priorities 4–6 are added in order as time allows. This cut is fixed now, not chosen after seeing results.

**Test-set draw:** from the 500 Verified tasks, remove the 92 development tasks and every `psf__requests` task, then shuffle with seed `20261120` and take the first 108. If a task fails task prep (source-integrity check, image, or environment), record the reason and take the next task in the shuffled order. Stop and report if more than 22 tasks (20%) fail prep.

## 4. Changes to the verifier

### V2 (regression tests)

1. **Paired-skip (Policy P), already built** on `experiment/paired-skip`. A test skipped on both the original and the patched code is left out; a test skipped only after the patch is missing evidence. Becomes the primary V2 accounting in v1.5. S and C stay recorded as sensitivities.
2. **Fallback when no tests are selected (new).** If Tier 1 and Tier 2 select nothing, select the existing test file(s) that mirror the changed module's path (for example `pkg/mod.py` to `tests/test_mod.py` or `pkg/tests/test_mod.py`), capped at the existing Tier 2 limit. If none exist, V2 stays NOT_AVAILABLE with reason `NO_SELECTION`. Selection is still label-free and patch-independent apart from the changed file list, as today.

### V4 (reproduction tests)

3. **Requirement list (new).** One generator call per task writes a numbered list of the separate behaviours the issue asks for (`requirements.json`), from the issue text and the original code only. The list is frozen and hashed before any test is written.
4. **Tests per requirement, two independent passes (new).** Two separate generator conversations each write one test per requirement on the frozen list, tagged with its requirement id. Existing rules are unchanged: issue, original code and the frozen list only, network off, package caches masked, each test must fail on the original code deterministically, and every kept test is frozen and hashed before any patch is seen. **Fallback if the DeepSeek top-up is not confirmed before Phase 4: one pass.** Decided before the pilot, not after.
5. **Coverage and per-requirement verdicts (new).** A requirement is *covered* if at least one kept test is tagged with it. On the patched code, each requirement gets:
   - **PASS:** all its kept tests pass.
   - **FAIL-confirmed:** kept tests from both passes fail (two-pass mode only).
   - **FAIL-single:** some kept test fails, but not confirmed by both passes.
   V4 is a **full PASS** only if every requirement is covered and every requirement is PASS. Uncovered requirements, the counts of each verdict, and every kept test's result with its pass number and requirement id are stored, so ablations can be recomputed offline.
6. **Reuse frozen V4 (new flag `--reuse-v4-from <run dir>`).** Loads the frozen tests and `requirements.json` from an earlier run, checks every sha256 against that run's records, and makes zero generator calls (fail the run if a call is attempted). A task with no frozen V4 there gets V4 NOT_AVAILABLE with reason `NO_FROZEN_V4`, never PASS. This is how every system on a task faces the same tests.

### Decision rules (v1.5): candidates, adopted or not by the thresholds in section 5

| # | Situation | Candidate decision |
|---|---|---|
| R1 | patch doesn't apply, integrity fails, or tests are tampered with | REJECT (unchanged) |
| R2 | V3 syntax or import failure | REJECT |
| R3 | V4 failure that is backed up: any FAIL-confirmed requirement, or 2+ failing requirements, or a V4 failure together with V2 FAIL or a V3 failure | REJECT |
| R4 | V4 failure not backed up (one FAIL-single requirement, nothing else failing) | FLAG, marked "likely wrong" |
| R5 | V2 FAIL and V4 full PASS (signals disagree) | REJECT if the gold threshold is met, otherwise FLAG for a human |
| R6 | V1 PASS, no V3 failure, V4 full PASS, and V2 PASS or NOT_AVAILABLE | ACCEPT |
| R7 | V4 not a full PASS and nothing failing (missing or uncovered) | FLAG, marked "likely right" if any signal passed |
| R8 | anything else | FLAG |

"Likely wrong" and "likely right" are reported labels for ordering human review. They are not new decisions.

## 5. Adoption thresholds (fixed before the gold run)

Applied once, in Phase 7, to the development data: gold-92 for costs, arm B's 51 for benefits.

- **A REJECT rule (R2, R3, R5) is adopted** only if it would REJECT at most 2 of the 92 gold patches **and** REJECT at least 3 of arm B's 26 wrong patches. Otherwise that situation stays FLAG ("likely wrong").
- **The ACCEPT rule R6 is adopted** only if, on arm B, v1.5 ACCEPT precision is at least 80% (the strict rule's value) **and** v1.5 accepts at least as many correct patches as the strict rule. If not, R6 is restricted to V2 PASS only (V2 NOT_AVAILABLE goes to FLAG "likely right").
- **The V2 fallback (change 2) is kept** only if no gold patch gets a V2 FAIL that comes only from fallback-selected tests. One such case disables the fallback.
- The outcome of each threshold is written to `reports/study_v1_5/ADOPTION.md` before the freeze tag.

## 6. Hypotheses and metrics (test set, v1.5, per system and pooled)

- **H1.** Pooled ACCEPT precision is above the pooled base rate (correct ÷ patch tasks). Task-clustered bootstrap, 95% CI lower bound above the base rate.
- **H2.** Wrong patches are held back (not ACCEPTed) more often than correct patches. Pooled difference with task-clustered bootstrap CI above 0.
- **H3.** v1.5 REJECTs at most 3% of the 108 gold patches. Report the count and Wilson upper bound.
- **Per system:** decision counts, base rate, ACCEPT precision (Wilson), coverage, correct accepted, wrong held back, held-back difference (Newcombe), two-sided Fisher exact. Same methods as arm B.
- **By wrong-patch type** (R regression, U under-solved, X other; from grader evidence only, as in the arm B protocol): share caught.
- **Gold:** every FLAG and REJECT on a gold patch, with the signal that caused it.
- **Same task in several systems:** pooled numbers resample whole tasks, never individual patches.
- No-patch (empty) submissions are counted and excluded from precision, as in arm B. Sensitivity: count them as wrong.

## 7. Phases

Each phase ends with a commit. A gate must pass before the next phase starts. "Stop" means stop and report, not fix and continue.

### Stage A: development set (92 tasks; images already on disk)

| Phase | Work | Gate |
|---|---|---|
| 1. Pre-register | Turn sections 3–6 into `reports/study_v1_5/PROTOCOL.md`; record the test-set seed and the system list. Tag `study-v1.5-prereg`. | Tag pushed before any download or new code |
| 2. Fetch patches | Script `scripts/fetch_public_patches.py`: for each system, download `<id>.pred` for all 200 tasks; use `model_patch`; write `<id>.patch` and `tasks.json` (id, path, sha256, empty, s3 key). Gold from the cached dataset's `patch` field. Test-set ids come from the seeded draw (Phase 9 logic, run label-free here). | No system missing more than 5 tasks per set; otherwise drop that system and take the next priority |
| 3. Build | V2 fallback (change 2), behind an on/off switch; per-requirement V4 with passes and coverage (3–5); `--reuse-v4-from` (6); v1.5 decision rules R1–R8 with one on/off switch per candidate (R2, R3, R5, R6's V2-NOT_AVAILABLE branch) in `configs/verifier/v1_5.yaml`; S/C/P and v1.4.1 still computable from stored signals. Unit tests for every new path and every switch. | Full offline test suite passes; a replay of arm B's stored decisions under v1.4.1 is unchanged |
| 4. V4 pilot | Verify-only run of gold patches on 10 development tasks with the new V4 on DeepSeek, `--deepseek-cap-usd 1`. | Cost per task ≤ $0.06; at least 7 of 10 tasks have every requirement covered; leakage audit passes on generator trajectories. Otherwise stop. |
| 5. Freeze V4 | Commit and tag `study-v4-frozen`. | No generator or prompt changes after this |
| 6. Gold run, development | Verify-only, gold patches, all 92 tasks, new V4 generated here and frozen: `runs/study_dev_gold`. All candidate signals recorded (V2 fallback switched on) so Phase 7 can evaluate every switch offline. Seal. | Sealed; ledger within cap; leakage audit passes |
| 7. Calibrate | Re-verify arm B's 51 patches with `--reuse-v4-from runs/study_dev_gold`: `runs/study_dev_armB`. Seal. Use arm B's existing labels (check each patch's sha256 matches arm B's frozen patch; no re-grading). Apply section 5 thresholds; write `ADOPTION.md`. | `ADOPTION.md` committed |
| 8. Freeze v1.5 | Set the switches in `configs/verifier/v1_5.yaml` exactly as `ADOPTION.md` says, commit, tag `v1.5-frozen`. | Tag pushed; nothing in `src/` or `configs/` changes after it |
| 9. Public systems, development | Verify-only with `--reuse-v4-from runs/study_dev_gold`, one system at a time in priority order: `runs/study_dev_<system>`. Seal each. | Each sealed; ledger $0 |

### Stage B: test set (108 tasks)

| Phase | Work | Gate |
|---|---|---|
| 10. Swap images | After every Stage A run is sealed, remove the 92 task images. Prepare the 108 test tasks with the task-prep job used for the 9 added tasks (branch `feature/task-prep`), applying the replacement rule from section 3. | At most 22 replacements; task specs committed |
| 11. Gold run, test | Verify-only, gold patches, 108 tasks, frozen V4 generator (`study-v4-frozen` settings) generating V4 here: `runs/study_test_gold`. Seal. | Sealed; ledger within cap; leakage audit passes |
| 12. Public systems, test | Verify-only with `--reuse-v4-from runs/study_test_gold`, priority order: `runs/study_test_<system>`. Seal each. | Each sealed; ledger $0 |

### Stage C: grading and analysis

| Phase | Work | Gate |
|---|---|---|
| 13. Grade | In `~/projects/wt-grading`, `scripts/grade_arm.py --sealed <run> --out runs/grading_<run>` for every sealed run, pinned swebench 4.0.4 wheel. Only after that run is sealed. | Every patch has a resolved / not resolved label or a recorded harness error |
| 14. Analysis script | Write and freeze `scripts/analyze_study.py` (based on `analyze_rerun_arm.py`); test it on made-up labels; tag `study-analysis-frozen`. | Tag pushed before real labels are joined |
| 15. Results | Join labels; produce section 6 metrics for test (headline), development and all 200. Leakage sensitivity: exclude tasks with CONFIRMED audit findings. | Report committed |
| 16. Ablations (offline, exploratory) | From stored signals: drop each of V1–V4; old V4 (arm B) vs new V4 on arm B's patches; S vs C vs P; v1.4.1 vs v1.5; one V4 pass vs two (pass 1 tests alone, from stored per-test results); with vs without the V2 fallback. | Tables committed, labelled exploratory |
| 17. Presentation | Architecture, changes, v1.5 rules and why, test-set results, development results, ablations, limits, 500-task plan. | — |

## 8. Budget, disk, time

- **DeepSeek (V4 only):** about $0.02 per generator call per task (arm B: $1.03 for 51 tasks). Requirement list plus two test passes is about $0.05 per task: about $0.50 for the pilot, $4.60 for the development gold run and $5.40 for the test gold run, **about $10.50 in total**. One-pass fallback is about $0.03 per task, **about $6.50 in total**.
- **Available: $4, which is not enough for either version.** It covers the pilot plus the development gold run only in one-pass mode. **A top-up is required before Phase 4: $10 for two passes (recommended), at least $5 for one pass.** Choose the mode from the confirmed balance before Phase 4, per section 4.
- Pass `--deepseek-cap-usd` per run: 1 for the pilot, 6 per gold run.
- **U-M key:** not used. Kept in reserve.
- **Disk:** 92 images now (on `C:`, about 280–300 GB free). The 108 test tasks need about 320 GB, which is why Phase 10 removes the 92 first. Check with `docker system df` before Phase 10.
- **Time:** measure on Phase 6. Arm B took 18 hours for 92 tasks including the repair agent. Expect a verify-only run to take less. Grading time scales with patch count. If the final presentation comes first, present the minimum set (section 3) and label anything unfinished.

## 9. Stop conditions (any phase)

- Leakage audit failure on any generator trajectory.
- A ledger cap reached before a run completes.
- Infrastructure errors on more than 5% of tasks in a run.
- Any sha256 mismatch when reusing V4.
- Any change needed to `src/` or `configs/` after `v1.5-frozen`.

## 10. Scaling to 500 (after the final presentation)

Same frozen v1.5 and V4 generator, remaining tasks in batches of about 90 (prepare, gold run, public systems, seal, remove images). About 300 more tasks, roughly $6–9 of DeepSeek for one-pass V4 or double for two passes, and about 2–3 weeks of machine time.
