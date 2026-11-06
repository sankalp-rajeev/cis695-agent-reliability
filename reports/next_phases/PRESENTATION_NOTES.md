# Presentation notes

At the end of every phase, update this file and its small CSV with actual results, evidence references and the result commit, then commit and push the update. Do not start a new phase as part of maintaining these notes.

Planned CSVs contain roadmap scope, baseline or threshold values, not experimental results. Planned entries cite the roadmap commit; Phase 1 cites its result commit, with the new archive confirmations supplied by this notes commit. E/F are retrospective categories added after Phase 1 inspection.

## Phase 1 — Known grader-failing existing tests

- Status: done
- Headline: Of 7 witnesses, 1 was blocked by a loader abort, 5 were skipped under CPU-count markers and 1 was already detected, while the Django abort also left 24 real test requests unexecuted per tree.
- Table or chart data: reports/next_phases/presentation_data/phase1.csv
- Example: Django-13297 / test_template_params_warning: a selected @property at batch position 9 aborted all 25 requests on both trees; reports/next_phases/phase1_known_failures/confirmations.md:28.
- Caveat: E/F were added after inspection, and static skip conditions do not measure the container CPU count or prove repaired tests would pass.
- Commit: 8db4978

## Phase 2 — Causes of incomplete evidence

- Status: planned
- Headline: Plan: explain all 39 INCOMPLETE cases and repeat the counts for 13 NOT_AVAILABLE cases from 780 captures, succeeding when every INCOMPLETE task has an evidenced cause and no gap is unexplained.
- Table or chart data: reports/next_phases/presentation_data/phase2.csv
- Example: Historical example, not a Phase 2 result: Django-13297 / test_template_params_warning stayed NOT_RUN after a loader abort; reports/next_phases/phase1_known_failures/confirmations.md:28.
- Caveat: ROADMAP.md specifies complete attribution and a parser-only recovery measurement, not a numeric recovery target, and no Phase 2 analysis has run.
- Commit: 15c3d9b

## Phase 3 — Repair V2 execution

- Status: planned
- Headline: Plan: repair the 7 listed executor behaviours without changing V2 selection, succeeding when all checks pass and the Phase 4 plan is committed.
- Table or chart data: reports/next_phases/presentation_data/phase3.csv
- Example: Historical example, not a repaired result: pylint-7277 / TestRunTC::test_jobs_score was skipped while its task received PASS / COMPLETE; reports/next_phases/phase1_known_failures/confirmations.md:65.
- Caveat: The repairs are unimplemented and ROADMAP.md requires a written plan before checks, including the three largest tasks per runner type, with any unexplained disappearing original FAIL treated as a bug.
- Commit: 15c3d9b

## Phase 4 — Controlled V2 rerun

- Status: planned
- Headline: Hypothesis: frozen V2 selection with the repaired executor raises yes/no verdicts from 31/83 to at least 50/83, falsified below 42/83, in one run with a 1,800 s per-pass cap and a 12 h stopping rule.
- Table or chart data: reports/next_phases/presentation_data/phase4.csv
- Example: Historical example for reconfirmation, not a rerun result: Matplotlib-25479 / test_register_cmap passed on base and failed on patched with confirmation; reports/next_phases/phase1_known_failures/phase1_known_failures.csv:3.
- Caveat: No repaired run exists, and post-hoc label metrics must follow sealed run metrics without executor changes after labels are read.
- Commit: 15c3d9b

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
