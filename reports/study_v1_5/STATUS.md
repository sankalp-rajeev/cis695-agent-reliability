# Study v1.5 status

Plan: `reports/study_v1_5/PLAN.md` · Branch: `study/v1.5-200` · Final presentation: Thu 26 Nov
Last updated: Fri 20 Nov 2026

Status key: ✅ done · 🔄 in progress · ⏳ not started · ⛔ blocked · ✂️ cut (by a cut rule)

## Current state

Phase 2 stopped at the fetch gate. Claude Sonnet 4 exceeded the missing-prediction limit in both sets. The partial GPT-4.1 development fetch also exceeded the limit. Coverage and drop decisions are recorded in [FETCH.md](inputs/FETCH.md).

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
| 2 | Fetch patches | Download public patches for 200 tasks, draw the test set | Patches from 6 agents of different strength, without running agents ourselves | ⛔ | [FETCH.md](inputs/FETCH.md) · 493/1,332 checked, 222 fetched, 8 empty (0 blank, 8 null), 271 missing, 0 malformed |
| 3 | Build | Paired-skip, V2 fallback, per-requirement V4, reuse flag, v1.5 rules | The two fixes for what held the verifier back | ⏳ | |
| 4 | V4 pilot | New V4 on 10 gold patches | Check cost, coverage and leakage before spending on full runs | ⏳ | |
| 5 | Freeze V4 | Tag `study-v4-frozen` | The test generator can't change after this | ⏳ | |
| 6 | Dev gold run | Verify 51 gold patches, generate and freeze V4 | Shows what the verifier wrongly blocks (costs) | ⏳ | |
| 7 | Calibrate | Re-verify arm B's 51 patches, apply thresholds, write ADOPTION.md | Decides which new rules to keep, using only the practice set | ⏳ | |
| 8 | Freeze v1.5 | Set switches, tag `v1.5-frozen` | The verifier can't change before the exam | ⏳ | |
| 9 | Dev public systems | Public patches on the practice set (only if the machine is idle) | Descriptive only; first to be cut | ⏳ | |
| 10 | Prepare batch 1 | Pull and check images for the first 60 test tasks | The exam set must be ready before the runs | ⏳ | |
| 11 | Test gold run | Verify 60 gold patches, generate V4 for the exam | Gold cost on unseen tasks (H3) plus the shared V4 tests | ⏳ | |
| 12 | Test public systems | Verify each system's patches with the frozen V4 | The headline result | ⏳ | |
| 12b | Batch 2 | Same for the remaining 48 tasks (if time) | More power; optional | ⏳ | |
| 13 | Labels | Fetch official SWE-bench labels after each seal; cross-check with our grader | Find out which patches were really correct, from an independent source | ⏳ | |
| 14 | Analysis script | Write, test on fake labels, tag `study-analysis-frozen` | The analysis is fixed before real labels are joined | ⏳ | |
| 15 | Results | Join labels, compute H1–H3 and per-system numbers | Answers RQ1, RQ2 and RQ5 | ⏳ | |
| 16 | Ablations | Signal drop-outs, S/C/P, old vs new V4, one vs two passes | Answers RQ3 and RQ4 | ⏳ | |
| 17 | Presentation | Final deck | Thu 26 Nov | ⏳ | |

## Decisions and deviations log

One line per entry, newest last: date, what was decided or deviated from the plan, and why.

- 20 Nov: plan revised after the validation pass (16 changes, PLAN.md §0).
- 20 Nov: Phase 1 test gate clarified to "no new failures beyond the documented baseline" (`reports/next_phases/MERGE_NOTES.md`).
- 20 Nov: V4 mode set to two passes (balance ~$9 ≥ $7 rule).
- 20 Nov: model_patch null counted as empty (no-patch), same as blank; absent or non-string recorded as malformed. Clarifies 'empty' in PROTOCOL §6; no rule changed.
- 20 Nov: The live downloader finished the Claude Sonnet 4 requests and checked 49 GPT-4.1 development keys before the gate failure was observed and the process was stopped. The downloader now enforces the gate after each recorded key.
