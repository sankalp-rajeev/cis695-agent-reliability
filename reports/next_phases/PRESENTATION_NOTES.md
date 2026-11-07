# Presentation notes

At the end of every phase, update this file and its small CSV with actual results, evidence references and the result commit, then commit and push the update. Do not start a new phase as part of maintaining these notes.

Planned CSVs contain roadmap scope, baseline or threshold values, not experimental results. Planned entries cite the roadmap commit; Phase 1 cites its result commit, with the new archive confirmations supplied by this notes commit. E/F are retrospective categories added after Phase 1 inspection.

## Phase 1 — Known grader-failing existing tests

- Status: done
- Headline: Of 7 witnesses, 1 was blocked by a property-load abort with 24 collateral requests per tree, 5 skipped and 1 already detected, while the fresh Pylint CPU helper reports 1 by default and 2 with either 2048 shares or a two-CPU quota.
- Table or chart data: reports/next_phases/presentation_data/phase1.csv (7-witness classification); reports/next_phases/presentation_data/phase1_cpu.csv (3 CPU probes)
- Example: Pylint-6528 / test_multiprocessing[1]: its CPU-count skip guard is consistent with the measured default helper result 1; reports/next_phases/phase1_known_failures/cpu_check.md:261.
- Caveat: The fresh CPU probe does not prove historical cgroup values, and E/F were added after inspecting the Phase 1 data.
- Commit: 4d7c529 (CPU check); 8db4978 (classification)

## Phase 2 — Causes of incomplete evidence

- Status: done
- Headline: Across 83 tasks, 942 aborts on 32 tasks strand 3,138/31,179 native NOT_RUN slots (10.06%), 13 PASS tasks accept skips (0 retain strict PASS; 2 CPU-only for ordinary skips, 0 including XFAIL; 4 incorrect-labelled post-hoc), and yes/no projections are 42/83 with current policy plus parser replay versus 20/83 with strict skips plus replay.
- Table or chart data: reports/next_phases/phase2_incomplete_causes/charts/policy_projections.csv
- Example: Django-13297 / test_template_params_warning: its property-load batch loses 24 collateral requests per tree, within 824 collateral slots across all task aborts (412/tree); reports/next_phases/phase2_incomplete_causes/charts/batch_collateral_top5.csv:2 and reports/next_phases/phase2_incomplete_causes/batch_aborts.csv:178.
- Caveat: These are completeness-only projections retaining all 6 confirmed FAILs; source-derived reasons and ambiguous candidates stay explicit, and the 4/13 post-hoc label count does not establish detection.
- Commit: this commit (resolve with git log -1 --format=%h -- reports/next_phases/phase2_incomplete_causes/BATCH_AND_POLICY_PROJECTIONS.md)

## Phase 3 — Repair V2 execution

- Status: in progress
- Headline: Fixes 1–5 are implemented. Fix 4 preserves collection/runner failures as missing, isolates execution by module and retries only unreported valid IDs. Fix 5 adds the native SymPy bin/test -C --verbose adapter with exact family filtering and a distinct-outcome parser. Fixes 6–8 remain planned.
- Table or chart data: reports/next_phases/phase3_fix5/base_smoke_summary.csv; phase3_fix5/base_smokes/*/module_processes.csv; phase3_fix4/corrected_collection/corrected_counts.csv; phase3_fix5/stored_accounting/policy_counts.csv; presentation_data/phase3_fix5.csv.
- Example: Final base-only Django smoke: 82 module processes, no retries, 3123 admitted / 28 missing / 16 invalid under C, 109.73 s. SymPy-13480: native runner replaces frozen pytest, 14 initial processes + 16 fallback processes, 638 admitted / 125 missing / 18 invalid under C, 335.32 s total. SymPy hit the unchanged 300 s execution cap and was not rerun; its 107 timed-out/unreached slots stay missing. Outcomes were not compared with correctness labels.
- Caveat: Corrected historical collection-only counts remain Django 16 INVALID_ID + 26 COLLECTION_ERROR; Astropy 16 + 105; old SymPy pytest 0 INVALID_ID + 781 RUNNER_UNAVAILABLE. Fresh native SymPy instead has 16 execution collection errors, two test errors and 18 successfully uncollected disabled-module IDs. The 83-task stored-data sensitivity is 42/21 PASS/FAIL yes/no under C/S with invalid IDs either excluded or missing; no task differs (REGRESSION_ERROR-inclusive: 43/22). H1 is only a stored projection, 23761/37614 primary and 23761/37116 informational secondary; invalid IDs add no admissions. Full suite: 1103 passed, 6 failed, 6 skipped, 17 setup errors, with the exact pre-existing failure/error set and all 18 new Fix 5 tests passing.
- Commit: this Fix 5 commit (resolve from phase3_fix5/SUMMARY.md); Fix 4 28f93e3; accounting guard pushed first in ec918ba. B1/B2 and thresholds remain unchanged. No correctness sidecars or joins were used. Stop after Fix 5.

## Phase 3 Fixes 6–8 — resources, deadlines, confirmation, and cost

- Status: completed; three base-only cost probes finished within the 1,800 s budget.
- Headline: All containers request CPU shares 2048 without a CPU-time cap. Each tree has a recorded 1,800 s collection-plus-execution budget; unreached slots carry elapsed time. Each new assertion failure or REGRESSION_ERROR requires three isolated base and three isolated patched observations; unstable candidates become FLAKY.
- Table or chart data: reports/next_phases/phase3_fix678/base_probe_summary.csv; estimates.json and stage_aware_estimates.json in that directory; unit_summary.json.
- Example: SymPy's warning environment now matches SWE-bench's UserWarning/SyntaxWarning filters. The requested base quantum-printing load check validated all 16 IDs in 26.47 s without executing test bodies. Largest base probes: Django-13297 314.82 s, Astropy-13977 344.26 s, SymPy-13480 1,152.48 s; no cap hits. Initial 83×2-tree estimates span 4.08–4.86 h serial, 2.04–2.43 h at two containers, 1.02–1.22 h at four. The range reflects selected-ID versus stage-aware models, not confidence bounds.
- Caveat: Final unit suite: 1,141 passed, 6 failed, 6 skipped, 17 setup errors; the exact pre-existing failure/error set is unchanged. Cost probes use selection sizes alone, base trees only, and no correctness comparison. Confirmation cost depends on future paired failures and is separate from the 166 initial-pass estimate. No Phase 4 concurrency has been selected.
- Commits: plan 171dbfc; SymPy alignment 9c0f387; Fix 6 24b1822; Fix 7 a8e1691; Fix 8 de3090f; cost driver 92c55b9; host-only active-timeout reader correction 0f193b4 (all three capture replays unchanged).

## Phase 4 — Controlled V2 rerun

- Status: executor and launcher prepared for tag approval; no new controlled attempt launched
- Headline: Fixed draft baselines are B1 = 37,614 addressable slots and B2 = 21/83 projected strict yes/no verdicts with XFAIL/XPASS separate; H1 predicts at least 60% recovery and is falsified below 30%, while Policy C targets 50/83 and is falsified below 42/83.
- Table or chart data: reports/next_phases/phase4_baselines/B1_B2.csv
- Example: Seaborn-3069 has 5 XFAIL concrete tests on both trees and no ordinary skip, adding one strict projected PASS to the old 20/83; reports/next_phases/phase4_baselines/B2_tasks.csv:52.
- Caveat: H1 is already met offline at 63.17%, largely from parsing. H1b, explicitly added after Fix 5 and before Phase 4, tests live admission of the fixed 13,853-slot residual: prediction at least 6,927, falsified below 25% (3,463); invalid IDs never count as admitted. H2 primary yes/no means PASS or FAIL; a secondary count adds REGRESSION_ERROR. B2 is an offline projection, H3 is descriptive, and the fixed plan permits one run with a 1,800 s per-pass cap and a 12 h stopping rule. Attempt 1 is quarantined as aborted, not analyzed; none of its outcomes informed Fix 9/10. No accepted controlled rerun result is claimed.
- Commit: c4d17c8

- Integrity update: Fix 9/10 pristine preflight verified **83/83 images** in 171.26 s: 18 task-level export-subst proofs and seven task-level pre_install proofs (eight files), with no remaining mismatches. The project stays on swebench 5.0.2; the isolated, hash-pinned 4.0.4 wheel supplies AST-only pre_install specs. Only four dataset metadata columns were decoded. All seven affected images recorded "no image script" at the checked setup paths. Runtime changes to generated untracked version modules are flagged without halting.
- Launcher verification: all 83 specs validated without containers. The fresh serial launcher requires a new annotated tag at clean HEAD, rechecks pristine source before runtime, uses CPU shares 2048/network none/1,800 s per pass, confirms each new failure 3x per tree, and aborts on integrity errors or the 12 h stop. No notifications. Full unit suite: **1,192 passed, 6 failed, 6 skipped, 17 errors**; exact pre-existing failure/error set, no new failures. All 29 Fix 10/launcher cases pass. Report: reports/next_phases/phase4_rerun/fix10_integrity_preflight.md; launcher: phase4_launcher.md in that directory.

## Phase 5 — Offline selector and ordering replay

- Status: planned
- Headline: Plan: replay 30, 60, 120 and 300 s budgets against 20 seeded random orderings, useful if the rule retains at least 90% of reference regressions at 120 s and its median time to first regression beats the random orderings’ 25th percentile.
- Table or chart data: reports/next_phases/presentation_data/phase5.csv
- Example: Historical reference example, not a replay result: Matplotlib-25479 / test_register_cmap has a confirmed base-pass/patched-fail observation to retain; reports/next_phases/phase1_known_failures/phase1_known_failures.csv:3.
- Caveat: The Phase 4 reference does not exist yet, and ROADMAP.md requires case-by-case reporting when regressions are few.
- Commit: 15c3d9b

## Phase 6 — Runtime instrumentation: tracing and coverage selection

- Status: planned
- Headline: Plan: trace 13 known tests in 6a and trial about 15 tasks in 6b, succeeding at file level with 100% reference regressions and all reachable known tests retained plus at least 50% fewer patched executions, failing on any missed reference regression or changed traced outcome, and adopting only if total cost beats full-list execution.
- Table or chart data: reports/next_phases/presentation_data/phase6.csv
- Example: Historical example to account for before tracing, not a runtime trace: pylint-6528 / test_multiprocessing[1] was skipped by the needs_two_cores collection guard; reports/next_phases/phase1_known_failures/confirmations.md:62.
- Caveat: 6a is post-hoc diagnosis with all 13 traces or explicit failure reasons required, while 6b must count cold-start tracing cost and report patch-only functions, non-Python dependencies and data-file blind spots.
- Commit: 15c3d9b
