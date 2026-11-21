# Study v1.5 status

Plan: `reports/study_v1_5/PLAN.md` · Branch: `study/v1.5-200` · Final presentation: Thu 26 Nov
Last updated: Sat 21 Nov 2026

Status key: ✅ done · 🔄 in progress · ⏳ not started · ⛔ blocked · ✂️ cut (by a cut rule)

## Current state

Phase 6 (dev gold run) passed all gates. Phase 3 part F (amendments A6–A8, from the Phase 6 review) is done: gold pytest-7236 and pytest-7521 were re-verified in `runs/study_dev_gold_f` with V2 now running, and the 51 gold decisions are recomputed ([PART_F.md](build/PART_F.md)). Phase 7 (calibrate on arm B with --reuse-v4-from runs/study_dev_gold) is next; it must be sealed by Mon 23 Nov 12:00 or v1.5 freezes with all switches off (amendment A5).

## Pre-flight checks

| Check | Result |
|---|---|
| S3 trajectories reachable | ✅ `aws s3 ls --no-sign-request` lists task folders |
| Disk for test batch 1 | ✅ 250 GB free; images average ~1.4 GB |
| Dev images | ✅ 83 of 83 present with pinned ids (add9 checked after merge) |
| DeepSeek balance | ✅ $9.03 confirmed by the provider balance API on 20 Nov; ≥ $7 → two-pass V4 (superseded by amendment A1: one pass). $8.64 on 21 Nov at the V4 freeze |

## Phases

| # | Phase | What it does | Why | Status | Result / link |
|---|---|---|---|---|---|
| 1 | Pre-register | Merge task-prep, write PROTOCOL.md, tag `study-v1.5-prereg` | Rules are fixed before we see any data | ✅ | tag study-v1.5-prereg @ 52186c0; unit baseline: no new issues |
| 2 | Fetch patches | Download public patches for 200 tasks, draw the test set | Patches from 6 agents of different strength, without running agents ourselves | ✅ | `176a2062226dbf37b22a5ecfc34071948c733a6e` · [FETCH.md](inputs/FETCH.md) · 1,332 fetched, 34 empty, 0 missing, 0 malformed |
| 3 | Build | Paired-skip, V2 fallback, per-requirement V4, reuse flag, v1.5 rules | The two fixes for what held the verifier back | ✅ | part F: `5d88c07b49b2ef92e53e6a00265799d72d5455cb` · [PART_F.md](build/PART_F.md) · A6 V3 pre-existing, A7 paired collection errors, A8 r6b · part E: `720d581b78a7d49a6451377ff83f4eb95a403fb4` · [PART_E.md](build/PART_E.md) · A3 audit: pilot 1 and pilot 2 exit 0, 0 leaks · truth table differs from v1.4.1 in 16 A4 (ii) cases · part D follow-up: `87a40c978e909481ad327d1ccd9a31eafa99fb1f` · parts A-D done: `c87d8b3eb27c168151fc7d78b4b20b09abc1cdd3` · [PART_D.md](build/PART_D.md) · truth table 8,640/8,640 equal to v1.4.1 with switches off · part C done: `4d714c12b4ca2b85a32a918594037ca33f31c0d5` · [PART_C.md](build/PART_C.md) · part B done: `74f0488320256dc2f7cc9984b64d654f07ff725c` · [PART_B.md](build/PART_B.md) · part A done: `cae8769394a67b4e8584e971fd20cfc6583d6ea4` · [PART_A.md](build/PART_A.md) |
| 4 | V4 pilot | New V4 on 10 gold patches | Check cost, coverage and leakage before spending on full runs | ⛔ | `53303bccba0df7d49fa02795bccb442461f0baec` · [PILOT.md](pilot/PILOT.md) · G1 ⛔ $0.670 total, $0.0670/task, max $0.1585 · G2 ✅ 10/10 covered · G3 ⛔ audit exit 1 · G4 ✅ 0 error tasks |
| 4b | V4 prompt fix + re-pilot | Prompt fix (no invented expected values; no incidental state; explicit arguments), one V4 pass, re-pilot on the same 10 gold patches | Fix what the pass-1 review of 4 gold tasks found, then re-check cost, coverage, leakage and gold V4 failures | ✅ | `6cf1c2b54b1b39a01df56047fe1a9f6847912959` · [PILOT2.md](pilot/PILOT2.md) · G1 ✅ $0.331 total, $0.0331/task, max $0.0665 · G2 ✅ 10/10 covered · G3 ✅ 0 lines outside model, 17 model-written · G4 ✅ 0 error tasks · G5 ✅ 2 with V4 FAIL, 8 full passes |
| 5 | Freeze V4 | Tag `study-v4-frozen` | The test generator can't change after this | ✅ | `79e8a2e1b9594bc08560652d28c303b316fb6511` (tag study-v4-frozen) · [V4_FREEZE.md](V4_FREEZE.md) · [AMENDMENT_2026-11-21.md](AMENDMENT_2026-11-21.md) · fingerprint bc19ba97cbe016479903222bb1578db6 · balance $8.64 · unit gate = baseline · truth table unchanged · v1.4.1 replay 51/51 |
| 6 | Dev gold run | Verify 51 gold patches, generate and freeze V4 | Shows what the verifier wrongly blocks (costs) | ✅ | `6c084c3d81105307d3cb1c9f2011c5c833a02e4b` · [DEV_GOLD.md](dev_gold/DEV_GOLD.md) · sealed ✅ · ledger ✅ $1.373 (cap $4.0010) · audit ✅ exit 0 · infra ✅ 2 error tasks · 40 V4 full passes, 5 with V4 FAIL · A/F/R off 25/26/0, all on 31/16/4 · recall 48 lines in 16 tasks · fingerprints 1223/1223 match pin |
| 7 | Calibrate | Re-verify arm B's 51 patches, apply thresholds, write ADOPTION.md | Decides which new rules to keep, using only the practice set | ⏳ | |
| 8 | Freeze v1.5 | Set switches, tag `v1.5-frozen` | The verifier can't change before the exam | ⏳ | |
| 9 | Dev public systems | Public patches on the practice set (only if the machine is idle) | Descriptive only; first to be cut | ⏳ | |
| 10 | Prepare batch 1 | Pull and check images for the first 60 test tasks | The exam set must be ready before the runs | ✅ | `b02834f6fb7b368c104522af54ee4e3afe51d949` · [PREP_BATCH1.md](inputs/PREP_BATCH1.md) · 60/60 pinned images, 4 replacements, 32.87 GiB root disk used, 217G available |
| 11 | Test gold run | Verify 60 gold patches, generate V4 for the exam | Gold cost on unseen tasks (H3) plus the shared V4 tests | ⏳ | |
| 12 | Test public systems | Verify each system's patches with the frozen V4 | The headline result | ⏳ | |
| 12b | Batch 2 | Same for the remaining 48 tasks (if time) | More power; optional | ⏳ | |
| 13 | Labels | Fetch official SWE-bench labels after each seal; cross-check with our grader | Find out which patches were really correct, from an independent source | ⏳ | |
| 14 | Analysis script | Write, test on fake labels, tag `study-analysis-frozen` | The analysis is fixed before real labels are joined | ⏳ | |
| 15 | Results | Join labels, compute H1–H3 and per-system numbers | Answers RQ1, RQ2 and RQ5 | ⏳ | |
| 16 | Ablations | Signal drop-outs, S/C/P, old vs new V4 (one vs two passes dropped, amendment A1) | Answers RQ3 and RQ4 | ⏳ | |
| 17 | Presentation | Final deck | Thu 26 Nov | ⏳ | |

## Phase 2 public patch totals

Includes the 22 reserve IDs per system.

| System | Fetched | Empty (blank) | Empty (null) | Missing | Malformed |
|---|---:|---:|---:|---:|---:|
| `gpt-4.1-mini-2025-04-14` | 222 | 0 | 8 | 0 | 0 |
| `claude-sonnet-4-20250514` | 222 | 0 | 0 | 0 | 0 |
| `gpt-4.1-2025-04-14` | 222 | 8 | 0 | 0 | 0 |
| `gemini-2.5-flash` | 222 | 7 | 0 | 0 | 0 |
| `o4-mini-2025-04-16` | 222 | 4 | 0 | 0 | 0 |
| `qwen3-coder-480b-a35b-instruct` | 222 | 7 | 0 | 0 | 0 |

## Decisions and deviations log

One line per entry, newest last: date, what was decided or deviated from the plan, and why.

- 20 Nov: plan revised after the validation pass (16 changes, PLAN.md §0).
- 20 Nov: Phase 1 test gate clarified to "no new failures beyond the documented baseline" (`reports/next_phases/MERGE_NOTES.md`).
- 20 Nov: V4 mode set to two passes (balance ~$9 ≥ $7 rule).
- 20 Nov: model_patch null counted as empty (no-patch), same as blank; absent or non-string recorded as malformed. Clarifies 'empty' in PROTOCOL §6; no rule changed.
- 20 Nov: The live downloader finished the Claude Sonnet 4 requests and checked 49 GPT-4.1 development keys before the gate failure was observed and the process was stopped. The downloader now enforces the gate after each recorded key.
- 20 Nov: v1.0.0 submissions store <id>/<id>.traj.json, not <id>.pred; the 404s were a wrong file name in the plan, not missing predictions. Drops withdrawn; fetch layout corrected per system. No protocol rule changed.
- 20 Nov: The first Qwen3-Coder development task folder listed zero filenames. The format check stopped before any corrected prediction downloads.
- 20 Nov: Qwen3-Coder's metadata.yaml trajs prefix is capitalised but the bucket folder is lowercase; prefix overridden with the confirmed bucket path. Not dropped. No protocol rule changed.
- 20 Nov: Phase 10 used the task-prep default container Git archive path and `--allow-pull`. 4 slots used ordered reserve replacements after source or environment verification failures. See PREP_BATCH1.md for each ID and reason.
- 20 Nov: Docker Hub reached its pull-rate limit during Phase 10. The tmux job waited for quota and resumed at the prescribed registry and image tags.
- 20 Nov: Retried `django__django-13925` on its prescribed Docker tag after a manifest lookup error. The original ID passed on retry.
- 20 Nov: Retried `sphinx-doc__sphinx-8269` on its prescribed Docker tag after a manifest lookup error. The original ID passed on retry.
- 20 Nov: Retried `sympy__sympy-23262` on its prescribed Docker tag after a manifest lookup error. The original ID passed on retry.
- 20 Nov: Retried `django__django-14493` on its prescribed Docker tag after a manifest lookup error. The original ID passed on retry.
- 20 Nov: scripts/export_frozen_registry.py gained an ordered multi-registry mode for batch 1; the original nine-task mode is unchanged; covered by unit tests.
- 20 Nov: V2 fallback clarified before freeze: tries every probed test layout (Tier 1 uses only the discovered one) and is capped at 5 files, because the code has no 'Tier 2 limit' as PLAN §4 assumed. No rule threshold changed.
- 20 Nov: requirement list capped at 4; tests named per requirement and pass; NO_RESULT and UNCOVERED map to V4 NOT_AVAILABLE
- 20 Nov: Phase 2 manifests converted to run inputs by make_verify_inputs.py; --reference-patches records gold input rather than relaxing a guard (the guard never matched 'reference'); gold-overlap audit excludes lines present in the issue, '-' lines or the base tree
- 20 Nov: v1.5 policy built as v1.4.1 plus three default-off switches; with switches off it equals v1.4.1 on every truth-table case; R7's likely_right means V2 PASS or at least one V4 requirement PASS
- 20 Nov: R3 extended conditions require V4 FAIL, so missing V4 evidence never REJECTs; headline decisions come only from decide_v1_5.py --frozen (switches read at tag v1.5-frozen); live run records keep v1.4.1 decisions, identical to v1.5 with switches off
- 21 Nov: Phase 4 pilot ids drawn as random.Random(20261121).sample(sorted 51 arm B patch ids, 10), in sample order: matplotlib__matplotlib-25479, django__django-13807, django__django-15572, django__django-16667, pytest-dev__pytest-5809, django__django-12965, django__django-16631, django__django-11095, astropy__astropy-13398, sympy__sympy-13480.
- 21 Nov: DeepSeek balance confirmed at $9.03 by the API, so two-pass V4 stands. The generator returned fingerprint bc19ba97cbe016479903222bb1578db6, not the aeb56401ca74e127821c4f9126dcb669 recorded in generator.yaml. The run does not check the fingerprint. It is recorded in PILOT.md and the config is unchanged.
- 21 Nov: The Phase 4 run used --mode pilot, because audited needs the Phase 5 tag. The header records git_dirty true because the pre-flight files were uncommitted at launch. The 51-id dev reference list is in reports/study_v1_5/pilot/dev_reference_ids.json.
- 21 Nov: G3 diagnosis: all 122 GOLD_LINE_IN_GENERATOR findings (20 distinct lines, 7 tasks) are model-written. Each first appears in the generator's own reasoning, and some were also written into /tmp scratch fix checks. There is no environment leak and no audit false positive, and no gold line is in any frozen test. See [G3_DIAGNOSIS.md](pilot/G3_DIAGNOSIS.md).
- 21 Nov: Phase 4b: V4 prompt fix (no invented expected values; no incidental state; explicit arguments) and one-pass re-pilot, from the pass-1 review of 4 gold tasks; no labels used.
- 21 Nov: Phase 4b sets v4_passes from 2 to 1. This overrides the two-pass mode chosen from the balance rule (PROTOCOL change 4). policy_version in v1_5.yaml was bumped to v1.4.1-full.1 under that file's rule. No code reads this key, and live records keep v1.4.1-full from the policy code.
- 21 Nov: Phase 4b unit gate: 1,836 passed, 6 skipped, 6 failed and 17 errors. The failing and erroring IDs equal unit_baseline_phase1.json. The four two-pass V4 tests now pin passes=2 explicitly, and one new test pins the study config at one pass. The v1.4.1 replay matched 51/51 decisions and 51/51 V2 outcomes. v1.5 with switches off matched 51/51, and the truth table still equals v1.4.1 with switches off.
- 21 Nov: Phase 4b re-pilot gates were fixed before launch. G1: mean ≤ $0.06 per task and no task above $0.15. G2: ≥ 7/10 tasks fully covered. G3: no gold line whose first appearance is outside the model's own messages; model-written recall is counted and does not fail. G4: infrastructure errors on ≤ 1 task. G5: fewer than 3 gold patches with any V4 FAIL and at least 6 V4 full passes; if G5 fails, keep the old prompts.
- 21 Nov: Phase 4b re-pilot passed: G1 ✅ $0.331 total, $0.0331/task, max $0.0665 · G2 ✅ 10/10 covered · G3 ✅ 0 lines outside model, 17 model-written · G4 ✅ 0 error tasks · G5 ✅ 2 with V4 FAIL, 8 full passes. See PILOT2.md.
- 21 Nov: Phase 5 step 1: the generator trajectories already record `extra.response.system_fingerprint` on every response (re-pilot: 858 of 858, all bc19ba97cbe016479903222bb1578db6). generation_calls does not record it. No code was added, because the prompt allowed a change only if the trajectories lacked the field.
- 21 Nov: `scripts/verify_model.py --config configs/model/generator.yaml --update`: PASS. Fingerprint aeb56401ca74e127821c4f9126dcb669 → bc19ba97cbe016479903222bb1578db6, cost $0.00011237. DeepSeek balance $8.64 (provider API, 16:05 UTC). This is $0.39 below the $9.03 reading, while the ledger shows $1.00 spent on the two pilots. The gap is not explained and is recorded as read.
- 21 Nov: Amendment A1: one V4 pass with the 4b prompts. FAIL-confirmed is removed. Extended R3 = V4 FAIL and (≥2 failing requirements or a V3 failure). The one-vs-two-pass ablation is dropped. G1 is a budget gate.
- 21 Nov: Amendment A2: the fingerprint is pinned now, and every run logs per-response fingerprints. A change by Phase 11 is a logged deviation, not a stop.
- 21 Nov: Amendment A3: stop on a gold line first seen outside the model's own messages, or on any other CONFIRMED finding. Model-written gold lines and gold lines in kept tests are recorded per task. There is a sensitivity analysis on tasks without recall. The first pilot stays failed G3, and the rule applies from Phase 6.
- 21 Nov: Amendment A4: adoption rules (i)-(vi). This adds a cap of 1 REJECT among arm B's 25 correct patches, sends V2 FAIL with partial V4 PASS to R5, narrows R6's V2-NOT_AVAILABLE branch to nothing-to-check, sets a 70% bar on newly ACCEPTed patches, adds a no-fallback V2 switch, and compares old and new V4 in Phase 7. The code is due before Phase 7.
- 21 Nov: Amendment A5: one restart per run, from scratch, for infrastructure-only failures. If Phase 7 is not sealed by Mon 23 Nov 12:00, v1.5 is frozen with all switches off.
- 21 Nov: Phase 5 gates: unit 1,836 passed, 6 skipped, 6 failed, 17 errors, with failing and erroring IDs equal to Phase 4b and the baseline. test_policy_v1_5.py passes, including switches-off = v1.4.1 on every truth-table case. The v1.4.1 replay matched 51/51 decisions and 51/51 V2 outcomes, and v1.5 with switches off matched 51/51. Tag study-v4-frozen.
- 21 Nov: Part E (A3): the reference audit classifies each gold line by its first appearance per conversation. Model-written text (assistant content, reasoning_content, tool-call arguments) gives GENERATOR_RECALL, recorded. Pass-prompt lines count as model-written only if the model wrote them into requirements.json. Anywhere else gives GOLD_LINE_LEAK, confirmed. Kept frozen tests are scanned (GOLD_LINE_IN_FROZEN_TEST, recorded), newer-copy checks run on reference trajectories, and --reference-summary writes per-task hashes.
- 21 Nov: Part E A3 gate, read-only on the sealed pilots, seals unchanged: pilot 1 exit 0, 0 leaks, 20 recall lines in 7 tasks. Pilot 2 exit 0, 0 leaks, 17 recall lines, equal row by row to g3_classification.json. 0 frozen-test lines in either. The first pilot keeps its failed G3.
- 21 Nov: Part E A4 (ii): V2 FAIL with per-requirement V4 NOT_AVAILABLE, ≥1 requirement PASS and none failing → R5 FLAG signals_disagree (default rule). The truth table is now 11,520 cases (V2 absence added). With switches off it differs from v1.4.1 in exactly 16 cases, all in that class (R3b REJECT → R5 FLAG).
- 21 Nov: Part E A4 (iii): the r6 switch accepts V2 NOT_AVAILABLE only with absence nothing_to_check. On arm B this removes 5 of Part D's 9 all-on R6 ACCEPTs (4 V2 incomplete, 1 V2 error). The all-on diff is now 11 (7 REJECTs unchanged, 4 ACCEPTs).
- 21 Nov: Part E A4 (v): `decide_v1_5.py --no-v2-fallback` reads the sealed selection.json. A fallback-only selection gives V2 NOT_AVAILABLE (nothing to check). It refuses when the selection does not show the fallback tests or mixes them with others. The stored records do show them, so there was no stop.
- 21 Nov: Part E gates: unit 1,869 passed, 6 skipped, 6 failed, 17 errors, IDs equal to the baseline. v1.4.1 replay 51/51 decisions and 51/51 V2 outcomes. v1.5 switches off on arm B 51/51. Nothing in V4_FREEZE.md or configs/ changed.
- 21 Nov: Amendment A4 (iii) revised (`43d1820854b0094afa01796b2826e14210ea0ca3`): the R6 switch also accepts V2 incomplete, if no test timed out or crashed on the patched tree; never error, timeout or unreliable baseline. It was prompted by part E's arm B replay with old-V4 signals, so arm B outcomes were known; no Phase 6 or test-set data exists. Gates: unit 1,879 passed, 6 skipped, 6 failed, 17 errors, IDs equal to the baseline; truth table (17,280 cases) differs from v1.4.1 only in the 16 A4 (ii) cases; v1.4.1 replay 51/51. All-on diff on arm B: 14 (7 REJECTs, 7 R6 ACCEPTs; django-11095 is excluded by a patched crash).
- 21 Nov: Phase 6 dev gold run passed: sealed ✅ · ledger ✅ $1.373 (cap $4.0010) · audit ✅ exit 0 · infra ✅ 2 error tasks · 40 V4 full passes, 5 with V4 FAIL · A/F/R off 25/26/0, all on 31/16/4 · recall 48 lines in 16 tasks · fingerprints 1223/1223 match pin. See DEV_GOLD.md.
- 21 Nov: Correction: the pilot 2 fingerprint count is 286 of 286 responses with bc19ba97cbe016479903222bb1578db6, not 858 of 858 (the combined trajectory was counted with the per-conversation files, three times in all). The conclusion is unchanged. Noted in AMENDMENT_2026-11-21.md and V4_FREEZE.md; recorded hashes unchanged.
- 21 Nov: Amendments A6 (V3 pre-existing failures), A7 (V2 paired collection errors) and A8 (switch r6b, default off), from the Phase 6 dev gold review; dev data only, arm B outcomes known from part E, no test-set data. Part F code: unit 1,946 passed, 6 skipped, 6 failed, 17 errors, IDs equal to the baseline; truth table differs from v1.4.1 only in the 16 A4 (ii) cases, and r6b off changes nothing; v1.4.1 replay 51/51 decisions and 51/51 V2 outcomes.
- 21 Nov: Part F step 4: gold pytest-7236 and pytest-7521 re-verified in runs/study_dev_gold_f (audited, tag study-dev-gold-f-launch, --reuse-v4-from runs/study_dev_gold): COMPLETE, seal MATCH (105 files), 0 generator and 0 ledger calls. A7 excluded 3 and 2 paired modules; V2 error → incomplete; infrastructure flags cleared. Phase 6 gold decisions with these two tasks: switches off 25/26/0 (A/F/R); all on with r6b 37/11/3; r2, r6, r6b on 37/14/0. Arm B (old V4): 20/27/4; 27/13/11; 27/18/6. Decisions changed by fix 1: gold django-16631 (R8→R7 off; R2 REJECT→R7 FLAG with r2), arm B matplotlib-23476 (R2→R3 all on; R2 REJECT→R4 FLAG with r3 off). By fix 2: gold pytest-7236 and pytest-7521, FLAG R8 → ACCEPT R6 with r6 on. Final unit gate 1,947 passed, 6 skipped, 6 failed, 17 errors, IDs equal to the baseline.
- 21 Nov: Second amendment AMENDMENT_2026-11-21b.md (B1–B8, `75da45c78de5edb76ec12a154ebee5cc5b67b8d8`), written before any test-set run. B1 order gpt-4.1-mini, Claude Sonnet 4, Gemini 2.5 Flash, then gpt-4.1, o4-mini, Qwen3-Coder; minimum set = first three. B2 headline excludes 5 ids (2 batch 1, 3 batch 2) found in manifests/pilot.csv and other files run on before the prereg tag; whole-dataset lists don't count, and verified200.json doesn't count because no run used it (checked run headers and reports; task-prep REPORT.md says nothing was pulled or built for the 200). configs/study_v1_5/headline_exclusions.json. B3 headline scope; B4 added analyses; B5 H3 as an estimate with Wilson bound; B6 label hash check, o4-mini out of pooled numbers, grader agreement sample of 30 from 177 pairs (configs/study_v1_5/grader_agreement_sample.json), official labels only after study-analysis-frozen; B7 calibration model; B8 V1 blocks patches adding sitecustomize.py or files under v4_repro/. Unit gate: 1,956 passed, 6 skipped, 6 failed, 17 errors, IDs equal to the baseline.
