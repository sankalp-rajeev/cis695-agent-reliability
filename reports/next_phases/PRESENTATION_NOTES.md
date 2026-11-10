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

## Phase 4 — Sealed attempt 4 and post-hoc analysis

- Status: completed and sealed; post-hoc analysis completed after the seal. The executor, sealed results and every tag are unchanged.
- Seal: `phase4-run-sealed` at `e40d60afac6534bba03a20168ea681fca24228af`. The 1,799-file run manifest was reverified before analysis and after both deterministic executions.
- Labels: 69 correct, 14 incorrect. Candidate-bound source: `/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/correctness_sidecar.json`; SHA-256 `cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990`.
- Tables and raw-capture audit: `phase4_posthoc/analysis.md` and `phase4_posthoc/analysis.json`. Per-test and per-task details are retained; no new tests or Docker execution.
- Result commits: sealed runtime results `e40d60a`; post-hoc report is this commit (resolve with `git log -1 --format=%h -- reports/next_phases/phase4_posthoc/analysis.json`).

### Sealed quantities and INVALID_ID sensitivity

| Quantity | Sealed value | Registered result |
|---|---:|---|
| H1 primary | 35774/37614 = 95.11% | prediction met; not falsified |
| H1b fixed residual | 12013/13853 = 86.72% | prediction met; not falsified |
| H2 C yes/no primary | 58/83 | prediction met; not falsified |
| H3 S yes/no | 26/83 versus B2 = 21 | descriptive; no prediction/falsification threshold |

H1 secondary informational, INVALID_ID removed from B1: 35774/37074 = 96.49%. H2 secondary including REGRESSION_ERROR: 59/83. Primary C coverage is **58 versus 48** with INVALID_ID excluded versus treated as missing; S is **26 versus 25**. No sealed number was recomputed or changed.

### Verdict × label tables

| Policy | Verdict | Correct | Incorrect |
|---|---|---:|---:|
| C_invalid_excluded | PASS | 43 | 9 |
| C_invalid_excluded | FAIL | 5 | 1 |
| C_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| C_invalid_excluded | INCOMPLETE | 15 | 4 |
| C_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| C_invalid_missing | PASS | 33 | 9 |
| C_invalid_missing | FAIL | 5 | 1 |
| C_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| C_invalid_missing | INCOMPLETE | 25 | 4 |
| C_invalid_missing | NOT_AVAILABLE | 5 | 0 |
| S_invalid_excluded | PASS | 14 | 6 |
| S_invalid_excluded | FAIL | 5 | 1 |
| S_invalid_excluded | REGRESSION_ERROR | 1 | 0 |
| S_invalid_excluded | INCOMPLETE | 44 | 7 |
| S_invalid_excluded | NOT_AVAILABLE | 5 | 0 |
| S_invalid_missing | PASS | 13 | 6 |
| S_invalid_missing | FAIL | 5 | 1 |
| S_invalid_missing | REGRESSION_ERROR | 1 | 0 |
| S_invalid_missing | INCOMPLETE | 45 | 7 |
| S_invalid_missing | NOT_AVAILABLE | 5 | 0 |

Frozen original V2 native comparison (no invented original Policy S or INVALID_ID replay):

| Verdict | Correct | Incorrect |
|---|---:|---:|
| PASS | 20 | 5 |
| FAIL | 5 | 1 |
| REGRESSION_ERROR | 0 | 0 |
| INCOMPLETE | 33 | 6 |
| NOT_AVAILABLE | 11 | 2 |

### Detection, false alarms and missed incorrect PASS

All intervals below are exact two-sided 95% Clopper-Pearson. Primary positive = FAIL; secondary positive = FAIL or REGRESSION_ERROR. The conditional denominator is PASS+FAIL for primary, and PASS+FAIL+REGRESSION_ERROR for secondary. No verdict is reclassified.

| Policy | Rule | Detection /14 | Detection among verdicted incorrect | False alarms /69 | False alarms among verdicted correct | Missed PASS /14 | Missed among verdicted incorrect |
|---|---|---|---|---|---|---|---|
| C_invalid_excluded | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/48 = 10.42% [3.47%, 22.66%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/49 = 12.24% [4.63%, 24.77%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_missing | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/38 = 13.16% [4.41%, 28.09%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| C_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/10 = 10.00% [0.25%, 44.50%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/39 = 15.38% [5.86%, 30.53%] | 9/14 = 64.29% [35.14%, 87.24%] | 9/10 = 90.00% [55.50%, 99.75%] |
| S_invalid_excluded | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/19 = 26.32% [9.15%, 51.20%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_excluded | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/20 = 30.00% [11.89%, 54.28%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/18 = 27.78% [9.69%, 53.48%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| S_invalid_missing | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/7 = 14.29% [0.36%, 57.87%] | 6/69 = 8.70% [3.26%, 17.97%] | 6/19 = 31.58% [12.58%, 56.55%] | 6/14 = 42.86% [17.66%, 71.14%] | 6/7 = 85.71% [42.13%, 99.64%] |
| original_V2_native | primary_FAIL_only | 1/14 = 7.14% [0.18%, 33.87%] | 1/6 = 16.67% [0.42%, 64.12%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/25 = 20.00% [6.83%, 40.70%] | 5/14 = 35.71% [12.76%, 64.86%] | 5/6 = 83.33% [35.88%, 99.58%] |
| original_V2_native | secondary_FAIL_plus_REGRESSION_ERROR | 1/14 = 7.14% [0.18%, 33.87%] | 1/6 = 16.67% [0.42%, 64.12%] | 5/69 = 7.25% [2.39%, 16.11%] | 5/25 = 20.00% [6.83%, 40.70%] | 5/14 = 35.71% [12.76%, 64.86%] | 5/6 = 83.33% [35.88%, 99.58%] |

### Witnesses and captured execution

- Of the seven grader-failing existing tests, six now pass on both trees. Only `matplotlib__matplotlib-25479::test_register_cmap` remains base-pass/patched-fail. `django__django-13297::test_template_params_warning` passes on both trees while the task remains INCOMPLETE. The five Pylint witnesses pass on both trees; both incorrect-labelled Pylint tasks are PASS under C and S.
- All six known regression witnesses remain base-pass/patched-fail. They belong to five correct-labelled tasks that receive FAIL under C and S; the report treats these as false alarms relative to the project labels.
- All 72 isolated confirmation calls have positive native-capture proofs. Twelve candidates satisfy base PASS 3/3 and patched FAILED/ERROR/CRASH 3/3. The five Django-10973 candidates have patched ERROR 3/3; that correct-labelled task adds one secondary false alarm, with raw exception signatures reported.
- Among the four incorrect patches in the fixed 13-task skip-dependent original PASS set, Django-16667 and Matplotlib-23299 remain C PASS but S INCOMPLETE; Pylint-6528 and Pylint-7277 remain PASS under both policies.

### Why old tests miss bad patches — grader-gap follow-up

The nominal ceiling is **4 of 14 incorrect-labelled patches (28.6%)** with any historical grader-failing pre-existing test. The seven recorded witnesses require qualification: five Pylint entries were native **CPU skips**, despite appearing in the grader's failure bucket. With 1024 CPU shares, Pylint detects one CPU and skips them; our executor's 2048 shares makes it detect two, and all five unchanged tests pass. Ten fresh official SWE-bench 5.0.2 single-test replays reproduce those skips both with and without `test_patch`.

Django-13297's archived grader applied a different candidate (`25022237…`) from the frozen candidate (`69181c9a…`). The archived patch removes the warning the old test requires; the frozen patch retains it and passes both fresh single-test variants. The oracle changes the enclosing class but leaves the test method unchanged. Matplotlib-25479 remains the positive control: the same candidate fails `test_register_cmap` in the grader and our sealed run. These gaps therefore do not demonstrate six assertion failures missed by the executor. Labels and sealed results remain unchanged; the Django provenance mismatch is disclosed rather than repaired here. Evidence, source/helper diffs, exact commands, environment measurements, and per-test classifications: [grader_gap/analysis.md](phase4_posthoc/grader_gap/analysis.md) and [classification.csv](phase4_posthoc/grader_gap/classification.csv). This follow-up adds twelve isolated diagnostic test invocations and three resource-only probes; it does not rerun the benchmark suite.

### Cap hit and four disclosures

- Cap: `sympy__sympy-24562`, base and patched, each hits 1,800 seconds with 463 NOT_REACHED and one TIMEOUT. No cap retry was performed.
- **INVALID_ID sensitivity:** C yes/no coverage changes from 58 to 48 when invalid IDs are missing rather than excluded; the full label tables and conditional denominators change accordingly.
- **Six non-cap NOT_REACHED:** one `ForcedTimeZoneDatabaseTests.test_write_datetime` per tree in Django-13297, 14631 and 15930. Each batch exits 0 with an OK summary after other tests finish. Neither ForcedTimeZoneDatabaseTests method emits a result/start; there is no explicit class-skip record establishing the underlying cause. These are normal-exit unreported requests, not supported crash collateral. The companion sealed CRASH attributions fail the pre-registered process-death requirement; all sealed statuses and verdicts are preserved.
- **COLLECTION_ERROR is the main remaining loss category:** 1,934 initial selected tree slots, the largest overall missing-evidence status category. This statement is about all initial selected tree slots, not its share within the fixed B1 residual. The complete task/module/signature breakdown and 15 largest distinct modules are in the analysis report.
- **CPU-conditioned outcomes were reported at seal:** all 38 concrete tests (76 tree instances across the two Pylint tasks, within 12 fixed selected families) passed once they ran. This post-hoc analysis lists their statuses and labels; it creates no new execution evidence.

Earlier Fix 13 prelaunch checks were historical milestones, superseded by the completed v4 attempt. Their report remains at `phase4_rerun/fix13_report.md`. Quarantined attempts were not used for this analysis.

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
