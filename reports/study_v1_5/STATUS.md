# Study v1.5 status

Plan: `reports/study_v1_5/PLAN.md` · Branch: `study/v1.5-200` · Final presentation: Thu 26 Nov
Last updated: Fri 20 Nov 2026

Status key: ✅ done · 🔄 in progress · ⏳ not started · ⛔ blocked · ✂️ cut (by a cut rule)

## Current state

Phase 3 is in progress. Parts A through C passed their offline gates. The study config enables Policy P, the five-file V2 fallback, and per-requirement V4 with two independent test passes. Phase 2 patches can be converted to verified run inputs, and reference runs can be audited for overlap with generator conversations. The runner supports sealed V4 reuse. Phase 10 is complete with 60 pinned images and four ordered reserve replacements.

## Pre-flight checks

| Check | Result |
|---|---|
| S3 trajectories reachable | ✅ `aws s3 ls --no-sign-request` lists task folders |
| Disk for test batch 1 | ✅ 250 GB free; images average ~1.4 GB |
| Dev images | ✅ 83 of 83 present with pinned ids (add9 checked after merge) |
| DeepSeek balance | 🔄 ~$4 + $5 top-up → ~$9 → two-pass V4 (confirm on dashboard) |

## Phases

| # | Phase | What it does | Why | Status | Result / link |
|---|---|---|---|---|---|
| 1 | Pre-register | Merge task-prep, write PROTOCOL.md, tag `study-v1.5-prereg` | Rules are fixed before we see any data | ✅ | tag study-v1.5-prereg @ 52186c0; unit baseline: no new issues |
| 2 | Fetch patches | Download public patches for 200 tasks, draw the test set | Patches from 6 agents of different strength, without running agents ourselves | ✅ | `176a2062226dbf37b22a5ecfc34071948c733a6e` · [FETCH.md](inputs/FETCH.md) · 1,332 fetched, 34 empty, 0 missing, 0 malformed |
| 3 | Build | Paired-skip, V2 fallback, per-requirement V4, reuse flag, v1.5 rules | The two fixes for what held the verifier back | 🔄 | part C done: `4d714c12b4ca2b85a32a918594037ca33f31c0d5` · [PART_C.md](build/PART_C.md) · part B done: `74f0488320256dc2f7cc9984b64d654f07ff725c` · [PART_B.md](build/PART_B.md) · part A done: `cae8769394a67b4e8584e971fd20cfc6583d6ea4` · [PART_A.md](build/PART_A.md) |
| 4 | V4 pilot | New V4 on 10 gold patches | Check cost, coverage and leakage before spending on full runs | ⏳ | |
| 5 | Freeze V4 | Tag `study-v4-frozen` | The test generator can't change after this | ⏳ | |
| 6 | Dev gold run | Verify 51 gold patches, generate and freeze V4 | Shows what the verifier wrongly blocks (costs) | ⏳ | |
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
| 16 | Ablations | Signal drop-outs, S/C/P, old vs new V4, one vs two passes | Answers RQ3 and RQ4 | ⏳ | |
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
