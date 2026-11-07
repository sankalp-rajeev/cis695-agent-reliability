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
- Headline: Fix 0 attributes all 3,683 collection/runner-error slots, with the top 10 signatures covering 3,634; Fixes 1–8 remain planned in the committed Phase 4 draft order.
- Table or chart data: reports/next_phases/phase4_baselines/fix0_top10.csv
- Example: Django-13297 / test_template_params_warning stayed NOT_RUN after a selected property aborted its batch; the property signature affects 200 slots across 4 tasks and is executor-fixable through validation/isolation; reports/next_phases/phase4_baselines/fix0_top10.csv:5.
- Caveat: Executor-fixable includes correct validation and accounting for invalid IDs, not a promise that every request can execute, and no Phase 3 code or cost run has happened.
- Commit: this plan-draft commit (resolve from reports/next_phases/phase4_plan.md history)

## Phase 4 — Controlled V2 rerun

- Status: planned
- Headline: Fixed draft baselines are B1 = 37,614 addressable slots and B2 = 21/83 projected strict yes/no verdicts with XFAIL/XPASS separate; H1 predicts at least 60% recovery and is falsified below 30%, while Policy C targets 50/83 and is falsified below 42/83.
- Table or chart data: reports/next_phases/phase4_baselines/B1_B2.csv
- Example: Seaborn-3069 has 5 XFAIL concrete tests on both trees and no ordinary skip, adding one strict projected PASS to the old 20/83; reports/next_phases/phase4_baselines/B2_tasks.csv:52.
- Caveat: B2 is an offline projection, H3 is descriptive, no controlled rerun exists, and the fixed plan permits one run with a 1,800 s per-pass cap and a 12 h stopping rule.
- Commit: this plan-draft commit (resolve from reports/next_phases/phase4_plan.md history)

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
