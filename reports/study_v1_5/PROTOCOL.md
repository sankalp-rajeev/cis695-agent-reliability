# Study protocol

- Git commit at writing `9d5fb6a97dab8e9674b40291beeab8e2529c544c`
- Test-set seed `20261120`
- Batch 1 = first 60 of the shuffled order
- Batch 2 = next 48 of the shuffled order
- V4 mode = two passes (DeepSeek balance confirmed at about $9)
- Grader `swebench 5.0.2`

Public systems in priority order (`SWE-bench/experiments`)

1. `gpt-4.1-mini-2025-04-14` — `evaluation/verified/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/metadata.yaml`
2. `claude-sonnet-4-20250514` — `evaluation/verified/20250726_mini-v1.0.0_claude-sonnet-4-20250514/metadata.yaml`
3. `gpt-4.1-2025-04-14` — `evaluation/verified/20250726_mini-v1.0.0_gpt-4.1-2025-04-14/metadata.yaml`
4. `gemini-2.5-flash` — `evaluation/verified/20250726_mini-v1.0.0_gemini-2.5-flash/metadata.yaml`
5. `o4-mini-2025-04-16` — `evaluation/verified/20250726_mini-v1.0.0_o4-mini-2025-04-16/metadata.yaml`
6. `qwen3-coder-480b-a35b-instruct` — `evaluation/verified/20250802_mini-v1.0.0_qwen3-coder-480b-a35b-instruct/metadata.yaml`

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

