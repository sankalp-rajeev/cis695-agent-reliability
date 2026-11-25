# Study plan: verifier v1.5 on 200 tasks

Status: plan, not yet pre-registered. Phase 1 turns the decisions below into `PROTOCOL.md` and tags it.
Branch: `study/v1.5-200`, created from `origin/experiment/paired-skip`. Worktree: `~/projects/wt-study`.

## 0. Changes from the 20 Nov draft (validation pass)

| # | Change | Why |
|---|---|---|
| C1 | Added R3b: V2 FAIL with V4 not a full PASS and no V4 failure → REJECT | The draft table sent this case to FLAG (R8). v1.4.1 REJECTs it (`regression_failed_without_v4_pass`), so v1.5 would have silently weakened an existing rule |
| C2 | R5 (V2 FAIL, V4 full PASS) is fixed at FLAG, no longer a REJECT candidate | Dr. Hassan's steer (superseded assertions stay FLAG for a human) and the v1.3.0 design. On arm B, REJECTing it would also have rejected 1 of 25 correct patches |
| C3 | R6 keeps v1.4.1's ACCEPT conditions: no high-severity risk flag, V1 analysis complete | The draft dropped both, which would loosen ACCEPT without saying so |
| C4 | Rules are first-match in listed order, with a truth-table unit test over every signal combination | Removes overlap or gap ambiguity |
| C5 | Adoption thresholds count rejections **added** relative to v1.4.1-P, and cap **total** gold REJECTs across all rules | Each rule alone could pass at 2 gold rejections while the sum breaks H3 |
| C6 | Development gold run is the 51 arm B patch tasks, not all 92 | Arm B's 41 no-patch tasks contribute nothing to calibration. Saves about 9 machine-hours and about $1.50, and makes one-pass V4 fit in the current $4 |
| C7 | Public-system labels: the official SWE-bench per-instance results (fetched only after the run is sealed) are primary; our grader is an agreement check on the second machine. Gold runs are not graded | Grading 120–180 patches serially doesn't fit before Wed, and grading next to a run changes labels (pylint-7277). Official labels are also independent of us |
| C8 | System priority is now gpt-4.1-mini, claude-sonnet-4, gpt-4.1 (weak, strong, middle) | If cut rule 6 fires, the two systems that remain span the capability range |
| C9 | Patch fetch reads each system's `assets.trajs` path from its `metadata.yaml`, never builds it from the folder name | Qwen3's S3 prefix is `...Qwen3-Coder-480B-A35B-Instruct` (S3 keys are case-sensitive). o4-mini's `logs` come from a different run name, so its official labels may not match these trajectories: o4-mini uses our grader |
| C10 | Gold patches enter through a declared `--reference-patches` mode recorded in the run header | `run_e2e.py` refuses supplied patches whose path contains "gold", "oracle" or "label". Renaming folders to get past that guard would look like evasion in an audit |
| C11 | Leakage gate adds a check that no V4 generator message contains an added line of the gold patch | The gold patch is on the host while V4 is generated in the gold runs. The generator container never gets it, and this proves it |
| C12 | Grader pin corrected to swebench **5.0.2** (`scripts/grade_arm.py`) | The draft said 4.0.4. That wheel is the task-prep provenance pin in `task_specs_83.json`, not the grader. Arm B was graded with 5.0.2 |
| C13 | Phase 1 merges `feature/task-prep` into the study branch | `task_specs_add9_e2e_v141.json` and the task-prep job exist only on that branch |
| C14 | Test batch 1 is prepared on Saturday, while the machine is idle during the build | 60 images (about 180 GB) fit next to the 92. Preparing during a run competes for CPU and disk |
| C15 | Ablations and the RQ mapping are pre-specified in the protocol (section 6), not left exploratory | They answer RQ3 and RQ4 directly; pre-specifying them makes them evidence rather than exploration |
| C16 | Per-requirement V4 defines NO_RESULT, for a requirement whose kept tests were all dropped on the patched code | Under v1.2.1, flaky, erroring or timed-out tests are dropped on the patched run. Without this case, "covered" was undefined after patching |

## 1. Goal

Show, on tasks the rules were never tuned on, that the verifier catches wrong patches and accepts correct ones, across several repair models.

The headline result is the **test set**. The 92 existing tasks are the **development set**: the v1.5 rules are built and calibrated there. Whatever the test set shows is reported as it comes out.

## 2. What this study is not

- No new repair-agent runs. Patches come from public SWE-bench submissions and the gold reference patches. Arm A (DeepSeek repair) is dropped.
- No rule changes after the v1.5 freeze tag. If something is wrong after the tag, stop and report; do not patch and continue.
- No labels, grader output, `FAIL_TO_PASS`/`PASS_TO_PASS`, official `results`/`logs`/`per_instance_details.json`, or `git_peek_suspicious_commits.md` files are opened before the run they concern is sealed.

## 3. Data

| Set | Tasks | Patches | Role |
|---|---|---|---|
| Development | the 92 arm B tasks (`task_specs_83.json` + `task_specs_add9_e2e_v141.json`, same manifest as arm B). Gold run and calibration use the **51 with an arm B patch** | gold (51), arm B's 51 gpt-4.1-mini patches; public systems descriptive only | build and calibrate v1.5 |
| Test | 108 new SWE-bench Verified tasks, seeded random draw, in two batches | gold, public systems | headline result |

**Public systems** (all mini-SWE-agent, bash-only; v0.0.0 for gpt-4.1-mini, v1.0.0 for the rest). Patch = `model_patch` from `<assets.trajs>/<id>/<id>.pred`, with `assets.trajs` read from `SWE-bench/experiments: evaluation/verified/<folder>/metadata.yaml`.

| Priority | System folder | Resolved on all 500 | Labels |
|---|---|---|---|
| 1 | `20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14` | 23.9% | official |
| 2 | `20250726_mini-v1.0.0_claude-sonnet-4-20250514` | 64.9% | official |
| 3 | `20250726_mini-v1.0.0_gpt-4.1-2025-04-14` | 39.6% | official |
| 4 | `20250726_mini-v1.0.0_gemini-2.5-flash` | 28.7% | official |
| 5 | `20250726_mini-v1.0.0_o4-mini-2025-04-16` | 45.0% | our grader (logs come from another run) |
| 6 | `20250802_mini-v1.0.0_qwen3-coder-480b-a35b-instruct` | 55.4% | official |

**Minimum set:** gold plus priorities 1–2 on test batch 1. Priorities 3–6 are added in order as time allows. This cut is fixed now, not chosen after seeing results.

**Test-set draw:** from the 500 Verified tasks, remove the 92 development tasks and every `psf__requests` task, then shuffle with seed `20261120`. Batch 1 is the first 60 in that order, batch 2 the next 48. If a task fails task prep (source-integrity check, image, or environment), record the reason and take the next task in the shuffled order. Stop and report if more than 12 tasks in batch 1 (20%) fail prep.

**Labels** (fetched only after the run is sealed):
- *Public systems:* `resolved` from the official per-instance `report.json` under the system's `assets.logs`. That file's per-test status gives the R/U/X wrong-patch type. Where our grader also runs (second machine, as time allows), agreement is reported. Disagreements are listed and the official label stands.
- *Arm B:* existing labels (swebench 5.0.2, `scripts/grade_arm.py`).
- *o4-mini:* our grader.
- *Gold:* correct by construction, not graded.

## 4. Changes to the verifier

### V2 (regression tests)

1. **Paired-skip (Policy P), already built** on `experiment/paired-skip`. A test skipped on both the original and the patched code is left out; a test skipped only after the patch is missing evidence. Becomes the primary V2 accounting in v1.5. S and C stay recorded as sensitivities.
2. **Fallback when no tests are selected (new).** If Tier 1 and Tier 2 select nothing, select the existing test file(s) that mirror the changed module's path (for example `pkg/mod.py` to `tests/test_mod.py` or `pkg/tests/test_mod.py`), capped at the existing Tier 2 limit. If none exist, V2 stays NOT_AVAILABLE with reason `NO_SELECTION`. Selection is still label-free and patch-independent apart from the changed file list, as today.

### V4 (reproduction tests)

3. **Requirement list (new).** One generator call per task writes a numbered list of the separate behaviours the issue asks for (`requirements.json`), from the issue text and the original code only. The list is frozen and hashed before any test is written.
4. **Tests per requirement, one or two independent passes (new).** Each pass is a separate generator conversation that writes one test per requirement on the frozen list, tagged with its requirement id. Existing rules are unchanged: issue, original code and the frozen list only, network off, package caches masked, each test must fail on the original code deterministically, and every kept test is frozen and hashed before any patch is seen. **Mode is chosen before Phase 4 from the confirmed DeepSeek balance: two passes if the balance is at least $7, otherwise one pass.** Recorded in `ADOPTION.md`.
5. **Coverage and per-requirement verdicts (new).** A requirement is *covered* if at least one kept test is tagged with it. On the patched code, each covered requirement gets:
   - **PASS:** all its kept tests pass.
   - **FAIL-confirmed:** kept tests from both passes fail (two-pass mode only).
   - **FAIL-single:** some kept test fails, but not confirmed by both passes.
   - **NO_RESULT:** every kept test for it was dropped on the patched run (flaky, error or timeout, per v1.2.1).

   V4 is a **full PASS** only if every requirement is covered and every requirement is PASS. Uncovered requirements, the counts of each verdict, and every kept test's result with its pass number and requirement id are stored, so ablations can be recomputed offline.
6. **Reuse frozen V4 (new flag `--reuse-v4-from <run dir>`).** Loads the frozen tests and `requirements.json` from an earlier run, checks every sha256 against that run's records, and makes zero generator calls (fail the run if a call is attempted). A task with no frozen V4 there gets V4 NOT_AVAILABLE with reason `NO_FROZEN_V4`, never PASS. This is how every system on a task faces the same tests.
7. **Reference-patch mode (new flag `--reference-patches`).** Required to verify gold patches. It is recorded in the run header, allowed only with `--verify-only-from`, and lifts the forbidden-path check for that one input directory only.

### Decision rules (v1.5)

First match wins, in this order. A unit test covers every combination of V1–V4 outcomes and the risk and analysis flags.

| # | Situation | Decision | Status |
|---|---|---|---|
| R1 | patch doesn't apply, integrity fails, or tests are tampered with | REJECT | unchanged |
| R2 | V3 syntax or import failure | REJECT | candidate |
| R3 | V4 failure that is backed up: any FAIL-confirmed requirement, or 2+ failing requirements, or a V4 failure together with V2 FAIL or a V3 failure | REJECT | candidate (V4 + V2 part unchanged from v1.4.1) |
| R3b | V2 FAIL and V4 not a full PASS, with no V4 failure (NOT_AVAILABLE, uncovered or NO_RESULT) | REJECT | unchanged from v1.4.1 |
| R4 | V4 failure not backed up (one FAIL-single requirement, nothing else failing) | FLAG "likely wrong" | new label |
| R5 | V2 FAIL and V4 full PASS (signals disagree) | FLAG "signals disagree" | unchanged from v1.3.0 |
| R6 | V1 PASS with analysis complete, no V3 failure, V4 full PASS, no high-severity risk flag, and V2 PASS (or V2 NOT_AVAILABLE, if adopted) | ACCEPT | V2-NOT_AVAILABLE branch is a candidate |
| R7 | V4 not a full PASS and nothing failing | FLAG "likely right" if any signal passed | new label |
| R8 | anything else | FLAG | — |

"Likely wrong", "likely right" and "signals disagree" are labels for ordering human review, not new decisions.

## 5. Adoption thresholds (fixed before the gold run)

Applied once, in Phase 7, to the development data: dev gold (51) for costs, arm B's 51 for benefits. Each candidate has one switch in `configs/verifier/v1_5.yaml`.

- **A REJECT candidate (R2, R3 beyond v1.4.1) is adopted** only if it REJECTs at most 1 of the 51 dev gold patches **and** REJECTs at least 2 of arm B's 26 wrong patches that v1.4.1-P did not already REJECT. Otherwise that situation stays FLAG ("likely wrong"). (Same rate as the draft's 2 of 92, counted as new catches rather than totals.)
- **Total gold cost:** the adopted candidates together add at most 1 dev gold REJECT beyond what v1.4.1-P already REJECTs. If they add more, drop adopted candidates in the order R2, then R3, until this holds. Gold REJECTs from the unchanged rules (R1, R3b) are reported, not tuned.
- **The R6 V2-NOT_AVAILABLE branch is adopted** only if, on arm B, v1.5 ACCEPT precision is at least 80% (v1.4.1's) **and** v1.5 accepts at least as many correct patches as v1.4.1-P. Otherwise R6 requires V2 PASS. (On current signals it would reach 23 correct of 29 ACCEPTs, 79%, just under the bar. The new V4 may move it either way.)
- **The V2 fallback (change 2) is kept** only if no dev gold patch gets a V2 FAIL that comes only from fallback-selected tests. One such case disables the fallback.
- The outcome of each threshold, and the V4 mode, are written to `reports/study_v1_5/ADOPTION.md` before the freeze tag.

## 6. Hypotheses, metrics and RQ mapping (test set, v1.5)

Gold patches never enter pooled precision, base rate or held-back numbers. They are reported on their own (H3 and the coverage ceiling).

- **H1.** Pooled ACCEPT precision over public-system patches is above their pooled base rate (correct ÷ non-empty patches). Task-clustered bootstrap, 95% CI lower bound above the base rate.
- **H2.** Wrong patches are held back (not ACCEPTed) more often than correct patches. Pooled difference with a task-clustered bootstrap CI above 0.
- **H3.** v1.5 REJECTs at most 3% of test-set gold patches (point estimate: at most 1 of batch 1's 60). Report the count and Wilson upper bound.
- **Per system:** decision counts, base rate, ACCEPT precision (Wilson), coverage, correct accepted, wrong held back, held-back difference (Newcombe), two-sided Fisher exact. Same methods as arm B.
- **Same task in several systems:** pooled numbers resample whole tasks, never individual patches.
- No-patch (empty) submissions are counted and excluded from precision, as in arm B. Sensitivity: count them as wrong.

| RQ | Answered by |
|---|---|
| RQ1 Agent reliability | Per system: share of submitted (non-empty) patches that are correct, plus empty-submission rate. With the DeepSeek main study and arm B as earlier evidence |
| RQ2 Verification value | H1, H2; per-system precision against base rate |
| RQ3 Signal contribution | Pre-specified ablations on the test set, recomputed from stored signals: each of V1–V4 forced to PASS (same definition as arm B's `exploratory_ablation.csv`); old V4 vs per-requirement V4 on arm B's patches; one V4 pass vs two (pass-1 tests only); with vs without the V2 fallback |
| RQ4 Coverage trade-off | Correct patches held back per system; S vs C vs P; v1.4.1 vs v1.5; gold coverage ceiling (share of gold ACCEPTed, with the cause of every gold FLAG/REJECT: superseded assertion, no covering test, issue not reproducible, verifier fault) |
| RQ5 Failure modes | Wrong-patch type (R/U/X, from official per-test status) by decision; every false ACCEPT described; per repository; V4 generator audit; sensitivity excluding tasks on each system's `git_peek_suspicious_commits` list |

## 7. Phases

Each phase ends with a commit. A gate must pass before the next phase starts. "Stop" means stop and report, not fix and continue.

### Stage A: development set

| Phase | Work | Gate |
|---|---|---|
| 1. Pre-register | Merge `feature/task-prep` into the study branch. Turn sections 3–6 into `reports/study_v1_5/PROTOCOL.md`; record the seed, the batch split and the system list. Tag `study-v1.5-prereg`. | Tag pushed before any download or new code |
| 2. Fetch patches | `scripts/fetch_public_patches.py`: for each system, read `assets.trajs` from its `metadata.yaml`; download only `<id>/<id>.pred` for the 92 dev and the 108 test ids; use `model_patch`; write `<id>.patch` and `tasks.json` (id, path, sha256, empty, s3 key). The script must refuse any key under `logs/` or outside `trajs/`. Gold from the cached dataset's `patch` field. Test ids come from the section 3 draw, run label-free here. | No system missing more than 5 tasks per set; otherwise drop that system and take the next priority |
| 3. Build | V2 fallback (change 2) behind a switch; per-requirement V4 with passes, coverage and NO_RESULT (3–5); `--reuse-v4-from` (6); `--reference-patches` (7); v1.5 rules R1–R8 with one switch per candidate (R2, R3 beyond v1.4.1, R6's V2-NOT_AVAILABLE branch) in `configs/verifier/v1_5.yaml`; gold-line overlap check in the leakage audit; S/C/P and v1.4.1 still computable from stored signals. Unit tests for every new path and switch, plus the rule truth table. | Full offline test suite passes; a replay of arm B's stored decisions under v1.4.1 is unchanged; a v1.5 replay of arm B with old-V4 signals gives no REJECT that v1.4.1 didn't give, except via R2 or R3 |
| 4. V4 pilot | Verify-only run of gold patches on 10 dev tasks with the new V4 on DeepSeek, `--deepseek-cap-usd 1`. Record minutes per task. | Cost per task ≤ $0.06; at least 7 of 10 tasks have every requirement covered; leakage audit passes on generator trajectories. Otherwise stop. |
| 5. Freeze V4 | Commit and tag `study-v4-frozen`. | No generator or prompt changes after this |
| 6. Gold run, development | Verify-only, `--reference-patches`, gold patches for the 51 arm B patch tasks, new V4 generated here and frozen: `runs/study_dev_gold`. All candidate signals recorded (V2 fallback on). Seal. | Sealed; ledger within cap; leakage audit passes |
| 7. Calibrate | Re-verify arm B's 51 patches with `--reuse-v4-from runs/study_dev_gold`: `runs/study_dev_armB`. Seal. Use arm B's existing labels (check each patch's sha256 against arm B's frozen patch; no re-grading). Apply section 5; write `ADOPTION.md`. | `ADOPTION.md` committed |
| 8. Freeze v1.5 | Set the switches in `configs/verifier/v1_5.yaml` exactly as `ADOPTION.md` says, commit, tag `v1.5-frozen`. | Tag pushed; nothing in `src/` or `configs/` changes after it |
| 9. Public systems, development (descriptive) | Only when the machine would otherwise be idle. Needs a dev gold V4 for the tasks used. | Each sealed; ledger $0 |

### Stage B: test set (two seeded batches)

| Phase | Work | Gate |
|---|---|---|
| 10. Prepare batch 1 | Saturday, during Phase 3. Run `docker system df` first, then prepare the first 60 test tasks with the `feature/task-prep` job, applying the replacement rule. | At most 12 replacements; task specs committed |
| 11. Gold run, test batch 1 | Verify-only, `--reference-patches`, frozen V4 generator generating V4 here: `runs/study_test1_gold`. Seal. | Sealed; ledger within cap; leakage audit passes |
| 12. Public systems, test batch 1 | Verify-only with `--reuse-v4-from runs/study_test1_gold`, in priority order: `runs/study_test1_<system>`. Seal each, then fetch that system's official labels. | Each sealed; ledger $0 |
| 12b. Batch 2 (if time) | Same as 10–12 for the next 48 tasks, `test2` in place of `test1`. | Same gates |

### Stage C: labels and analysis

| Phase | Work | Gate |
|---|---|---|
| 13. Labels | For each sealed public-system run: fetch the official per-instance reports for its ids only; record their sha256. On the second machine, run `scripts/grade_arm.py` (swebench 5.0.2) on sealed copies as time allows, for agreement. o4-mini: our grader only. | Every non-empty patch has a label or a recorded reason it has none |
| 14. Analysis script | Write and freeze `scripts/analyze_study.py` (based on `analyze_rerun_arm.py`); test it on made-up labels; tag `study-analysis-frozen`. | Tag pushed before real labels are joined |
| 15. Results | Join labels; section 6 metrics for the test set (headline), plus arm B under v1.5 and the gold runs. Sensitivities: exclude tasks with CONFIRMED audit findings; exclude `git_peek` tasks. | Report committed |
| 16. Ablations | The pre-specified RQ3/RQ4 tables from section 6. | Tables committed |
| 17. Presentation | Architecture, changes, v1.5 rules and why, test results per RQ, ablations, limits, 500-task plan. | — |

## 8. Budget, disk, time

- **DeepSeek (V4 only):** about $0.02 per generator call per task (arm B: $1.03 for 51 tasks). One pass is 2 calls (about $0.03–0.04 a task), two passes 3 calls (about $0.05–0.06).

  | Mode | Pilot (10) | Dev gold (51) | Test batch 1 (60) | Total | Batch 2 (48) |
  |---|---|---|---|---|---|
  | One pass | $0.35 | $1.80 | $2.10 | **~$4.25** | +$1.70 |
  | Two passes | $0.55 | $2.80 | $3.30 | **~$6.65** | +$2.70 |

  Available: $4. One pass runs batch 1 with a ~$0.5 top-up or a tighter per-call cost, which the pilot measures. Two passes need about $3 more (rule in change 4: two passes only with ≥ $7 confirmed). Pass `--deepseek-cap-usd` per run: 1 for the pilot, 3 for dev gold, 4 for test gold.
- **U-M key:** not used. Kept in reserve.
- **Disk:** 92 images now, about 280–300 GB free. Batch 1 needs about 180 GB and fits alongside. Batch 2 needs the 92 removed first.
- **Time** (estimate from arm B timestamps: about 9 minutes of verification per patch, outliers to 80–105 minutes on matplotlib; the new V4 adds generator calls). Replace with Phase 4's measured minutes per task.

  | Run | Patches | Estimate |
  |---|---|---|
  | Phase 6 dev gold | 51 | 10–12 h |
  | Phase 7 arm B re-verify (no generation) | 51 | 6–8 h |
  | Phase 11 test gold | 60 | 12–14 h |
  | Phase 12, per system (no generation) | ≤ 60 | 8–10 h |

## 9. Stop conditions (any phase)

- Leakage audit failure on any generator trajectory, including any gold-patch line found in a generator message.
- A ledger cap reached before a run completes.
- Infrastructure errors on more than 5% of tasks in a run.
- Any sha256 mismatch when reusing V4 or loading a patch.
- Any change needed to `src/` or `configs/` after `v1.5-frozen`.

## 10. Schedule (final presentation Thursday 26 Nov) and cut rules

| Day | Work |
|---|---|
| Fri 20 | Phase 1 (merge task-prep, pre-register, tag). Phase 2 (fetch patches). Ask about the DeepSeek top-up. |
| Sat 21 | Phase 3 (build). Phase 10 (prepare batch 1) on the idle machine. |
| Sun 22 | Finish Phase 3. Phase 4 (pilot), Phase 5 (freeze V4). Start Phase 6 by 22:00. |
| Mon 23 | Phase 6 finishes. Phase 7, then Phase 8 (freeze v1.5). Phase 14 (analysis script) while runs go. Start Phase 11 overnight. |
| Tue 24 | Phase 11 finishes. Phase 12 system 1, then system 2 overnight. Labels for each run as it seals. |
| Wed 25 | Phase 12 system 2 finishes; system 3 only if it can finish by the cutoff. **Analysis cutoff 18:00.** Phases 15–16. |
| Thu 26 | Phase 17 (presentation). |

**Cut rules, fixed now and applied in this order:**

1. Phase 9 runs only when the machine would otherwise be idle. It is skipped first.
2. Systems 3–6 run only after systems 1–2 have finished on batch 1.
3. Batch 2 runs only after systems 1–3 have finished on batch 1.
4. **Results at the cutoff use only runs that are sealed and labelled.** A system is included only if it completed every task in the batch. The cutoff is a time, not a result.
5. **V4 fallback:** if the per-requirement V4 (changes 3–5) does not pass Phase 3's tests by Sunday 22:00, use the current V4 design (one generator pass, up to three tests). Coverage and FAIL-confirmed are then unavailable, and R3's backing-up rule becomes "2+ failing tests, or a V4 failure with V2 FAIL or a V3 failure". Record which design was used in `ADOPTION.md`.
6. If Phase 6 takes more than 14 hours, system 2 is the last system run on batch 1 and system 3 is reported later.

Anything that does not finish by the cutoff goes into the final report after the presentation, labelled with its date.

## 11. Scaling to 500 (after the final presentation)

Same frozen v1.5 and V4 generator, remaining tasks in batches of about 90 (prepare, gold run, public systems, seal, labels, remove images). About 300 more tasks, roughly $10–12 of DeepSeek for one-pass V4 or $15–18 for two passes, and about 2–3 weeks of machine time.
