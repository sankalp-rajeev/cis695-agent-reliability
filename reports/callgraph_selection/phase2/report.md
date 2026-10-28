# Phase 2-lite: offline static test selection

2026-10-22. Selectors and eligibility were frozen before this analysis. No oracle comparison, gold patch, benchmark import/collection/execution, Docker or network was used. No commits or phase 3.

## Plain-language answer (seven lines)

Call graphs receive the following support from the registered decision map: **Do not use on this experiment's evidence**.
C1 is partly met (2/6 fixed large cases; threshold 5).
C2 is partly met (2/6 fixed large cases; threshold 5).
C3 is partly met (3/7 eligible NOT_AVAILABLE cases; threshold 4).
The graph-only selector can return fewer candidates; C keeps the full V2 union and changes its order before budget prefixes.
Qualified partial graphs and ambiguous-edge results are reported separately and cannot change that decision.
These are static candidate counts, not evidence of runtime savings or defect detection.

Nothing in the primary evaluation confirms that a selected test actually exercises the changed code.

## Deviations and incidents

- A usage-limit pause interrupted phase-2 implementation; the agent resumed after auditing the full worktree, README, existing tests and absence of selector outputs. The complete pre-resume file inventory is in `resume_state.md` / `resume_state.json`.
- The first execution failed before constructing any candidate because the tar root directory was stored as `testbed`, while the reader required `testbed/`. The reader now accepts either root-directory spelling; a synthetic archive regression test was added. The failed attempt's files, hashes and pre-fix code hashes are preserved under `failed_attempts/archive_root_check/`.
- The next foreground execution ended abruptly during the interrupted chat/tool session. Abrupt termination during an interrupted chat/tool session; exact exit cause unrecorded. No selector timeout exists, no traceback/stderr/exit status survived; cgroup reports zero OOM kills. External interruption is consistent with the recorded turn abort, but timeout/signal/crash cannot be conclusively distinguished from stored evidence. The stored log has 23 completed-task records ending at `django__django-15103`; the user reported 24 tasks. No completed 24th-task record survived, so both counts are recorded without inventing an exit status. Partial files were moved to `failed_attempts/interrupted_foreground_run/` and hashed only as failed-attempt evidence, never treated as a successful selector freeze or analyzed for results.
- Long execution was restarted from scratch under `nohup`, retaining stdout/stderr and an exit-status file. The original eligibility files were reused unchanged. Execution and output freezing are now separate stages; all 83 task IDs and an explicit completion line were verified before any successful-output hash or analysis.

**No ranking rule, eligibility rule or frozen parameter changed. No selector output was seen before the fixes:** candidate IDs, scores, selected-set counts, summaries and criterion outcomes were not inspected; only progress logs, file metadata and gzip integrity were checked. The selector/ranking module matches its pre-fix hash. The frozen design remains unchanged.

Eligibility-freeze file SHA-256 (`eligibility_freeze.json`): `be9ebf5ba3c1222fa57d4ce23a26f83c79a6bf136bd4513dc798fa04cfbd0b0c`.

Frozen eligibility payload SHA-256 (`eligibility.json`): `bce2b74f6e043759123768e2012e2c770cabc4e777c81f810f9d2a7844ef073e`. It was written and frozen **before any selector output**: the runner persists both files before entering the selector writer, and the same eligibility digest is already recorded in the archive-reader failure manifest. The freeze files were not rewritten on either restart.

Report-only correction after the selector freeze: the secondary C3 row's denominator note now names its frozen eligible NOT_AVAILABLE pool, rather than incorrectly saying 'fixed six'. All counts, thresholds, criteria and decisions are unchanged. The correction source and original/final report hashes are recorded in `report_corrections.json`; frozen selector/code inputs are untouched.

Every autonomous rerun is listed below; the failure manifests retain the earlier attempts:

| Rerun | Launch | Outcome | Task records | Exit |
|---|---|---|---:|---:|
| 1 | nohup bash reports/callgraph_selection/phase2/run_background.sh; log background_attempt_1.log | failed before selector start: The detached nohup launcher returned, but no execution.log or exit/completion record appeared and its stdout/stderr log stayed empty. The child did not persist after its enclosing sandbox command exited. No selector candidate was produced; exact signal is unrecorded. Keep the launching parent alive with wait while polling the background child log. | 0 | unrecorded |
| 2 | nohup bash reports/callgraph_selection/phase2/run_background.sh; log background_attempt_2.log; parent waits while child runs | completed: completed without a selector exception | 83 | 0 |

Conservative readings: an unrecorded termination cause is reported as unknown, rather than assigned to a timeout or crash. Finished partials with other omission reasons have diagnostic-only results and never enter either evaluation stratum. Unmappable IDs retain missing graph features and cannot manufacture reachability; base identities use the existing production extractor and diagnostic normalizer only. The shared-tail interpretation was explicitly approved by the user and recorded before execution.

## Frozen inputs, populations and outcomes

Design commit: `72ad21bce666aa766cc329c9bef8057f790c0ef5`; code revision: `72ad21bce666aa766cc329c9bef8057f790c0ef5`, with uncommitted code pinned by SHA-256 in `inputs.json`. The design is unchanged. `selector_freeze.json` binds the selector outputs before analysis; `outputs.sha256.json` and its SHA-256 sidecar bind the final report bundle. Every consumed graph, archive, snapshot, patch-export and manifest input is hashed. The original phase-1 graphs, run artifacts, policies and manifests are unchanged.

All 83 candidate patches match the verified export manifest; CSV source_run is final-study provenance. The export is read directly from the previously supplied local frozen_patches_export.tgz. Base test identities use stored local exact-commit task archives, without importing or executing source. A and C use only the exact stored selection IDs/order for the 19 study_snapshot tasks; no V2 rerun occurs.

| Stratum | All 83 tasks | Stored-selection tasks | Evaluation status |
|---|---:|---:|---|
| PRIMARY_COMPLETE | 54 | 11 | Separate evaluation |
| EXTENDED_PARTIAL | 22 | 6 | Separate evaluation |
| EXCLUDED | 7 | 2 | Diagnostic only / unavailable |

B runs on every finished graph with a verified patch and resolved seeds, including diagnostic-only partials with other omission reasons. Those EXCLUDED results never enter primary or extended evaluation. Zero resolved seeds, ambiguous-only seeds, missing graphs and empty reachability are distinct. `eligibility.json` and its hash were written before traversal; the C3 primary denominator is fixed at 7 tasks.

| Excluded task | Reason | Graph | Resolved / ambiguous / unresolved names |
|---|---|---|---|
| django__django-16082 | NO_EXTRACTED_SEEDS | partial | 0 / 0 / 0 |
| matplotlib__matplotlib-24637 | NO_EXTRACTED_SEEDS | complete | 0 / 0 / 0 |
| pylint-dev__pylint-6528 | PARTIAL_GRAPH_OTHER_REASONS | partial | 4 / 0 / 1 |
| pylint-dev__pylint-6903 | PARTIAL_GRAPH_OTHER_REASONS | partial | 2 / 0 / 0 |
| pylint-dev__pylint-7277 | PARTIAL_GRAPH_OTHER_REASONS | partial | 1 / 0 / 0 |
| sympy__sympy-13480 | AMBIGUOUS_ONLY_SEEDS | partial | 0 / 1 / 0 |
| sympy__sympy-24562 | AMBIGUOUS_ONLY_SEEDS | complete | 0 / 1 / 0 |

## Registered criteria and decision map

Only PRIMARY_RESOLVED_ONLY on PRIMARY_COMPLETE decides. “Partly met” means some successes below the registered threshold; its formal result is FAIL. C1/C2 keep all six fixed rows in their denominators, including the partial Django-14631. C3 uses only its pre-frozen eligible denominator.

| Criterion | Result | Successes / denominator | Eligible | Required | Formal result |
|---|---|---:|---:|---:|---|
| C1 | **partly met** | 2 / 6 | 5 | 5 | FAIL |
| C2 | **partly met** | 2 / 6 | 5 | 5 | FAIL |
| C3 | **partly met** | 3 / 7 | 7 | 4 | FAIL |

C1: B at d=2 has 1–250 unbudgeted tests. C2: C at d=2, K=100 contains a stored V2 candidate with a resolved path of length ≤2 to a resolved changed seed. C3: B at d=3 selects a pre-existing test for at least half the eligible NOT_AVAILABLE tasks.

**Decision-map outcome: Do not use on this experiment's evidence.** Rank/filter support requires C1 AND C2; fallback support requires C3. This experiment alone cannot support replacing Tier 2.

| Separate descriptive counterpart | Variant | Criterion | Hits / denominator | Note |
|---|---|---|---:|---|
| EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | C1 | 0 / 1 | Eligible extended subset only; never pooled |
| EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | C2 | 0 / 1 | Eligible extended subset only; never pooled |
| EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | C3 | 0 / 3 | Eligible extended subset only; never pooled |
| PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C1 | 3 / 6 | Fixed six; secondary does not decide |
| PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C2 | 4 / 6 | Fixed six; secondary does not decide |
| PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C3 | 3 / 7 | Frozen eligible NOT_AVAILABLE pool; secondary does not decide |
| EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C1 | 0 / 1 | Eligible extended subset only; never pooled |
| EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C2 | 0 / 1 | Eligible extended subset only; never pooled |
| EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C3 | 0 / 3 | Eligible extended subset only; never pooled |

## Six large cases

B columns are unbudgeted; “V2 reachable” counts candidates in the full C union with graph paths at each depth. C prefix sizes are reported in K order 25/50/100/250/500 and are identical across depths; unbudgeted C always retains all V2 candidates. Counts do not establish execution coverage.

### PRIMARY_RESOLVED_ONLY

| Task | Stratum | V2 | B d1 / d2 / d3 | V2 reachable d1 / d2 | C sizes by K, all d | C K100 d2 reachable |
|---|---|---:|---|---|---|---:|
| django__django-13212 | PRIMARY_COMPLETE | 1383 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |
| astropy__astropy-13977 | PRIMARY_COMPLETE | 3082 | 1 / 1 / 324 | 1 / 1 | 25 / 50 / 100 / 250 / 500 | 1 |
| django__django-12209 | PRIMARY_COMPLETE | 3319 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |
| django__django-13297 | PRIMARY_COMPLETE | 8155 | 1 / 1 / 1 | 1 / 1 | 25 / 50 / 100 / 250 / 500 | 1 |
| django__django-14140 | PRIMARY_COMPLETE | 2334 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |
| django__django-14631 | EXTENDED_PARTIAL | 4469 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |

| Task | Changed seeds: depth-3 fan-in, weight | Model.save fan-in, weight | Does specificity favor changed seeds over this hub? |
|---|---|---|---|
| django__django-13212 | DecimalValidator: 0, 1/1; EmailValidator.validate_domain_part: 0, 1/1; EmailValidator: 0, 1/1; FileExtensionValidator: 0, 1/1; ProhibitNullCharactersValidator: 0, 1/1; RegexValidator: 0, 1/1; URLValidator: 0, 1/1; validate_ipv46_address: 0, 1/1; validate_ipv4_address: 0, 1/1; validate_ipv6_address: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| astropy__astropy-13977 | Quantity: 324, 1/325 | Absent | Could not assess this comparison: no Model.save in this base graph. |
| django__django-12209 | Model: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-13297 | RedirectView: 1, 1/2; TemplateResponseMixin: 0, 1/1; TemplateView: 0, 1/1; _wrap_url_kwargs_with_deprecation_warning.access_value: 0, 1/1; _wrap_url_kwargs_with_deprecation_warning: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-14140 | Q: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-14631 | BoundField.label_tag: 0, 1/1; BoundField: 0, 1/1; BaseForm._clean_fields: 0, 1/1; BaseForm.changed_data: 0, 1/1; BaseForm.errors: 0, 1/1; BaseForm.media: 0, 1/1; BaseForm: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |

### SECONDARY_RESOLVED_PLUS_AMBIGUOUS

| Task | Stratum | V2 | B d1 / d2 / d3 | V2 reachable d1 / d2 | C sizes by K, all d | C K100 d2 reachable |
|---|---|---:|---|---|---|---:|
| django__django-13212 | PRIMARY_COMPLETE | 1383 | 16 / 17 / 17 | 16 / 17 | 25 / 50 / 100 / 250 / 500 | 17 |
| astropy__astropy-13977 | PRIMARY_COMPLETE | 3082 | 1 / 4 / 327 | 1 / 4 | 25 / 50 / 100 / 250 / 500 | 4 |
| django__django-12209 | PRIMARY_COMPLETE | 3319 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |
| django__django-13297 | PRIMARY_COMPLETE | 8155 | 1 / 1 / 1 | 1 / 1 | 25 / 50 / 100 / 250 / 500 | 1 |
| django__django-14140 | PRIMARY_COMPLETE | 2334 | 254 / 260 / 262 | 254 / 259 | 25 / 50 / 100 / 250 / 500 | 100 |
| django__django-14631 | EXTENDED_PARTIAL | 4469 | 0 / 0 / 0 | 0 / 0 | 25 / 50 / 100 / 250 / 500 | 0 |

| Task | Changed seeds: depth-3 fan-in, weight | Model.save fan-in, weight | Does specificity favor changed seeds over this hub? |
|---|---|---|---|
| django__django-13212 | DecimalValidator: 1, 1/2; EmailValidator.validate_domain_part: 0, 1/1; EmailValidator: 7, 1/8; FileExtensionValidator: 1, 1/2; ProhibitNullCharactersValidator: 1, 1/2; RegexValidator: 8, 1/9; URLValidator: 0, 1/1; validate_ipv46_address: 0, 1/1; validate_ipv4_address: 0, 1/1; validate_ipv6_address: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| astropy__astropy-13977 | Quantity: 327, 1/328 | Absent | Could not assess this comparison: no Model.save in this base graph. |
| django__django-12209 | Model: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-13297 | RedirectView: 1, 1/2; TemplateResponseMixin: 0, 1/1; TemplateView: 0, 1/1; _wrap_url_kwargs_with_deprecation_warning.access_value: 0, 1/1; _wrap_url_kwargs_with_deprecation_warning: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-14140 | Q: 262, 1/263 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |
| django__django-14631 | BoundField.label_tag: 0, 1/1; BoundField: 0, 1/1; BaseForm._clean_fields: 0, 1/1; BaseForm.changed_data: 0, 1/1; BaseForm.errors: 0, 1/1; BaseForm.media: 0, 1/1; BaseForm: 0, 1/1 | 0, 1/1 | No: it could not prefer a changed seed over Model.save by observed fan-in. Model.save has zero represented test reachability, so the static model gives it maximum weight. |

## Every NOT_AVAILABLE task

Values are pre-existing candidate counts at d=1/2/3. Zero is measured empty reachability; NA is unavailable, never an empty set. The primary C3 numerator uses only the complete, eligible d=3 rows. Diagnostic excluded rows and qualified extended rows are kept separate.

| Task | Stratum / reason | PRIMARY B d1 / d2 / d3 | SECONDARY B d1 / d2 / d3 | Primary d3 any? |
|---|---|---|---|---|
| astropy__astropy-13977 | PRIMARY_COMPLETE / ELIGIBLE | 1 / 1 / 324 | 1 / 4 / 327 | yes |
| astropy__astropy-14365 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 2 / 2 | 0 / 2 / 2 | yes |
| astropy__astropy-14508 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| matplotlib__matplotlib-14623 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| matplotlib__matplotlib-24177 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| matplotlib__matplotlib-25287 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| pydata__xarray-4966 | PRIMARY_COMPLETE / ELIGIBLE | 0 / 8 / 8 | 0 / 8 / 8 | yes |
| pylint-dev__pylint-6903 | EXCLUDED / PARTIAL_GRAPH_OTHER_REASONS | 0 / 0 / 0 | 0 / 0 / 0 | no |
| sympy__sympy-13480 | EXCLUDED / AMBIGUOUS_ONLY_SEEDS | NA / NA / NA | NA / NA / NA | NA |
| sympy__sympy-14711 | EXTENDED_PARTIAL / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| sympy__sympy-17318 | EXTENDED_PARTIAL / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| sympy__sympy-19783 | EXTENDED_PARTIAL / ELIGIBLE | 0 / 0 / 0 | 0 / 0 / 0 | no |
| sympy__sympy-24562 | EXCLUDED / AMBIGUOUS_ONLY_SEEDS | NA / NA / NA | NA / NA / NA | NA |

## Candidate efficiency: all frozen depths and budgets

“19” is the historical stored-selection cohort, separately limited to common-evaluable tasks in each stratum. “B broader” is the new graph-only analysis of confirmed patches, not an 83-task A/B/C comparison. Each table is separate: do not pool strata or variants. All five budgets and ALL are shown. Quantiles use the existing diagnostic linear interpolation. Reductions/expansions compare the same task and same budget with A; total reduction uses summed counts, not a runtime estimate. A is repeated across depth/variant only to align configurations, not as independent evidence. `selector_summary.csv` also gives per-repository results, direct/transitive proportions, distance bins and V2 retention.

<details><summary>PRIMARY_COMPLETE — PRIMARY_RESOLVED_ONLY: every depth and budget</summary>

| Scope / selector | d | K | n / cohort | Median | Mean | p75 | p90 | Max | Tasks ≥1000 | Reduced / expanded vs A | Total reduction vs A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| B broader / B | 1 | 25 | 54 / 54 | 0 | 3.15 | 1 | 12.8 | 25 | 0 | NA | NA |
| B broader / B | 1 | 50 | 54 / 54 | 0 | 3.91 | 1 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 1 | 100 | 54 / 54 | 0 | 3.91 | 1 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 1 | 250 | 54 / 54 | 0 | 3.91 | 1 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 1 | 500 | 54 / 54 | 0 | 3.91 | 1 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 1 | ALL | 54 / 54 | 0 | 3.91 | 1 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 2 | 25 | 54 / 54 | 0 | 3.44 | 2 | 12.8 | 25 | 0 | NA | NA |
| B broader / B | 2 | 50 | 54 / 54 | 0 | 4.39 | 2 | 12.8 | 50 | 0 | NA | NA |
| B broader / B | 2 | 100 | 54 / 54 | 0 | 4.43 | 2 | 12.8 | 52 | 0 | NA | NA |
| B broader / B | 2 | 250 | 54 / 54 | 0 | 4.43 | 2 | 12.8 | 52 | 0 | NA | NA |
| B broader / B | 2 | 500 | 54 / 54 | 0 | 4.43 | 2 | 12.8 | 52 | 0 | NA | NA |
| B broader / B | 2 | ALL | 54 / 54 | 0 | 4.43 | 2 | 12.8 | 52 | 0 | NA | NA |
| B broader / B | 3 | 25 | 54 / 54 | 0 | 4.35 | 3 | 21.7 | 25 | 0 | NA | NA |
| B broader / B | 3 | 50 | 54 / 54 | 0 | 5.76 | 3 | 21.7 | 50 | 0 | NA | NA |
| B broader / B | 3 | 100 | 54 / 54 | 0 | 6.8 | 3 | 21.7 | 100 | 0 | NA | NA |
| B broader / B | 3 | 250 | 54 / 54 | 0 | 9.57 | 3 | 21.7 | 250 | 0 | NA | NA |
| B broader / B | 3 | 500 | 54 / 54 | 0 | 10.94 | 3 | 21.7 | 324 | 0 | NA | NA |
| B broader / B | 3 | ALL | 54 / 54 | 0 | 10.94 | 3 | 21.7 | 324 | 0 | NA | NA |
| 19 / A | 1 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / A | 2 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / A | 3 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / B | 1 | 25 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 97.8% |
| 19 / B | 1 | 50 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 98.9% |
| 19 / B | 1 | 100 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.4% |
| 19 / B | 1 | 250 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.7% |
| 19 / B | 1 | 500 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.8% |
| 19 / B | 1 | ALL | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 100.0% |
| 19 / B | 2 | 25 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 97.8% |
| 19 / B | 2 | 50 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 98.9% |
| 19 / B | 2 | 100 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.4% |
| 19 / B | 2 | 250 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.7% |
| 19 / B | 2 | 500 | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 99.8% |
| 19 / B | 2 | ALL | 11 / 11 | 0 | 0.55 | 1 | 1 | 3 | 0 | 11 / 0 | 100.0% |
| 19 / B | 3 | 25 | 11 / 11 | 0 | 3.09 | 2 | 4 | 25 | 0 | 10 / 0 | 87.6% |
| 19 / B | 3 | 50 | 11 / 11 | 0 | 5.36 | 2 | 4 | 50 | 0 | 10 / 0 | 89.2% |
| 19 / B | 3 | 100 | 11 / 11 | 0 | 9.91 | 2 | 4 | 100 | 0 | 10 / 0 | 89.4% |
| 19 / B | 3 | 250 | 11 / 11 | 0 | 23.55 | 2 | 4 | 250 | 0 | 10 / 0 | 87.8% |
| 19 / B | 3 | 500 | 11 / 11 | 0 | 30.27 | 2 | 4 | 324 | 0 | 11 / 0 | 91.4% |
| 19 / B | 3 | ALL | 11 / 11 | 0 | 30.27 | 2 | 4 | 324 | 0 | 11 / 0 | 98.3% |
| 19 / C | 1 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / C | 2 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / C | 3 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |

</details>

<details><summary>PRIMARY_COMPLETE — SECONDARY_RESOLVED_PLUS_AMBIGUOUS: every depth and budget</summary>

| Scope / selector | d | K | n / cohort | Median | Mean | p75 | p90 | Max | Tasks ≥1000 | Reduced / expanded vs A | Total reduction vs A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| B broader / B | 1 | 25 | 54 / 54 | 0 | 4.54 | 2 | 21.7 | 25 | 0 | NA | NA |
| B broader / B | 1 | 50 | 54 / 54 | 0 | 5.76 | 2 | 21.7 | 50 | 0 | NA | NA |
| B broader / B | 1 | 100 | 54 / 54 | 0 | 6.69 | 2 | 21.7 | 100 | 0 | NA | NA |
| B broader / B | 1 | 250 | 54 / 54 | 0 | 9.46 | 2 | 21.7 | 250 | 0 | NA | NA |
| B broader / B | 1 | 500 | 54 / 54 | 0 | 9.54 | 2 | 21.7 | 254 | 0 | NA | NA |
| B broader / B | 1 | ALL | 54 / 54 | 0 | 9.54 | 2 | 21.7 | 254 | 0 | NA | NA |
| B broader / B | 2 | 25 | 54 / 54 | 0 | 5.37 | 9.5 | 21.7 | 25 | 0 | NA | NA |
| B broader / B | 2 | 50 | 54 / 54 | 0 | 6.78 | 9.5 | 21.7 | 50 | 0 | NA | NA |
| B broader / B | 2 | 100 | 54 / 54 | 0 | 7.78 | 9.5 | 21.7 | 100 | 0 | NA | NA |
| B broader / B | 2 | 250 | 54 / 54 | 0 | 10.56 | 9.5 | 21.7 | 250 | 0 | NA | NA |
| B broader / B | 2 | 500 | 54 / 54 | 0 | 10.74 | 9.5 | 21.7 | 260 | 0 | NA | NA |
| B broader / B | 2 | ALL | 54 / 54 | 0 | 10.74 | 9.5 | 21.7 | 260 | 0 | NA | NA |
| B broader / B | 3 | 25 | 54 / 54 | 0.5 | 6.61 | 12.25 | 23.7 | 25 | 0 | NA | NA |
| B broader / B | 3 | 50 | 54 / 54 | 0.5 | 8.48 | 12.25 | 23.7 | 50 | 0 | NA | NA |
| B broader / B | 3 | 100 | 54 / 54 | 0.5 | 10.48 | 12.25 | 23.7 | 100 | 0 | NA | NA |
| B broader / B | 3 | 250 | 54 / 54 | 0.5 | 16.04 | 12.25 | 23.7 | 250 | 0 | NA | NA |
| B broader / B | 3 | 500 | 54 / 54 | 0.5 | 17.69 | 12.25 | 23.7 | 327 | 0 | NA | NA |
| B broader / B | 3 | ALL | 54 / 54 | 0.5 | 17.69 | 12.25 | 23.7 | 327 | 0 | NA | NA |
| 19 / A | 1 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / A | 2 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / A | 3 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / B | 1 | 25 | 11 / 11 | 1 | 5.45 | 8.5 | 16 | 25 | 0 | 10 / 0 | 78.2% |
| 19 / B | 1 | 50 | 11 / 11 | 1 | 7.73 | 8.5 | 16 | 50 | 0 | 10 / 0 | 84.4% |
| 19 / B | 1 | 100 | 11 / 11 | 1 | 12.27 | 8.5 | 16 | 100 | 0 | 10 / 0 | 86.8% |
| 19 / B | 1 | 250 | 11 / 11 | 1 | 25.91 | 8.5 | 16 | 250 | 0 | 10 / 0 | 86.6% |
| 19 / B | 1 | 500 | 11 / 11 | 1 | 26.27 | 8.5 | 16 | 254 | 0 | 11 / 0 | 92.5% |
| 19 / B | 1 | ALL | 11 / 11 | 1 | 26.27 | 8.5 | 16 | 254 | 0 | 11 / 0 | 98.6% |
| 19 / B | 2 | 25 | 11 / 11 | 1 | 6 | 10.5 | 18 | 25 | 0 | 10 / 0 | 76.0% |
| 19 / B | 2 | 50 | 11 / 11 | 1 | 8.27 | 10.5 | 18 | 50 | 0 | 10 / 0 | 83.3% |
| 19 / B | 2 | 100 | 11 / 11 | 1 | 12.82 | 10.5 | 18 | 100 | 0 | 10 / 0 | 86.2% |
| 19 / B | 2 | 250 | 11 / 11 | 1 | 26.45 | 10.5 | 18 | 250 | 0 | 10 / 0 | 86.3% |
| 19 / B | 2 | 500 | 11 / 11 | 1 | 27.36 | 10.5 | 18 | 260 | 0 | 11 / 0 | 92.2% |
| 19 / B | 2 | ALL | 11 / 11 | 1 | 27.36 | 10.5 | 18 | 260 | 0 | 11 / 0 | 98.5% |
| 19 / B | 3 | 25 | 11 / 11 | 1 | 8.82 | 20.5 | 25 | 25 | 0 | 9 / 0 | 64.7% |
| 19 / B | 3 | 50 | 11 / 11 | 1 | 13.36 | 20.5 | 50 | 50 | 0 | 9 / 0 | 73.1% |
| 19 / B | 3 | 100 | 11 / 11 | 1 | 22.45 | 20.5 | 100 | 100 | 0 | 9 / 0 | 75.9% |
| 19 / B | 3 | 250 | 11 / 11 | 1 | 49.73 | 20.5 | 250 | 250 | 0 | 9 / 0 | 74.2% |
| 19 / B | 3 | 500 | 11 / 11 | 1 | 57.82 | 20.5 | 262 | 327 | 0 | 11 / 0 | 83.6% |
| 19 / B | 3 | ALL | 11 / 11 | 1 | 57.82 | 20.5 | 262 | 327 | 0 | 11 / 0 | 96.8% |
| 19 / C | 1 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / C | 2 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |
| 19 / C | 3 | 25 | 11 / 11 | 25 | 25 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 50 | 11 / 11 | 50 | 49.64 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 100 | 11 / 11 | 100 | 93.09 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 250 | 11 / 11 | 250 | 193.09 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 500 | 11 / 11 | 500 | 352.18 | 500 | 500 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | ALL | 11 / 11 | 736 | 1825.36 | 2708 | 3319 | 8155 | 5 | 0 / 0 | 0.0% |

</details>

<details><summary>EXTENDED_PARTIAL — PRIMARY_RESOLVED_ONLY: every depth and budget</summary>

| Scope / selector | d | K | n / cohort | Median | Mean | p75 | p90 | Max | Tasks ≥1000 | Reduced / expanded vs A | Total reduction vs A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| B broader / B | 1 | 25 | 22 / 22 | 0 | 1.73 | 0.75 | 3 | 25 | 0 | NA | NA |
| B broader / B | 1 | 50 | 22 / 22 | 0 | 2.86 | 0.75 | 3 | 50 | 0 | NA | NA |
| B broader / B | 1 | 100 | 22 / 22 | 0 | 3.36 | 0.75 | 3 | 61 | 0 | NA | NA |
| B broader / B | 1 | 250 | 22 / 22 | 0 | 3.36 | 0.75 | 3 | 61 | 0 | NA | NA |
| B broader / B | 1 | 500 | 22 / 22 | 0 | 3.36 | 0.75 | 3 | 61 | 0 | NA | NA |
| B broader / B | 1 | ALL | 22 / 22 | 0 | 3.36 | 0.75 | 3 | 61 | 0 | NA | NA |
| B broader / B | 2 | 25 | 22 / 22 | 0 | 2.45 | 0.75 | 4.8 | 25 | 0 | NA | NA |
| B broader / B | 2 | 50 | 22 / 22 | 0 | 3.59 | 0.75 | 4.8 | 50 | 0 | NA | NA |
| B broader / B | 2 | 100 | 22 / 22 | 0 | 4.09 | 0.75 | 4.8 | 61 | 0 | NA | NA |
| B broader / B | 2 | 250 | 22 / 22 | 0 | 4.09 | 0.75 | 4.8 | 61 | 0 | NA | NA |
| B broader / B | 2 | 500 | 22 / 22 | 0 | 4.09 | 0.75 | 4.8 | 61 | 0 | NA | NA |
| B broader / B | 2 | ALL | 22 / 22 | 0 | 4.09 | 0.75 | 4.8 | 61 | 0 | NA | NA |
| B broader / B | 3 | 25 | 22 / 22 | 0 | 2.55 | 0.75 | 5 | 25 | 0 | NA | NA |
| B broader / B | 3 | 50 | 22 / 22 | 0 | 3.68 | 0.75 | 5 | 50 | 0 | NA | NA |
| B broader / B | 3 | 100 | 22 / 22 | 0 | 4.18 | 0.75 | 5 | 61 | 0 | NA | NA |
| B broader / B | 3 | 250 | 22 / 22 | 0 | 4.18 | 0.75 | 5 | 61 | 0 | NA | NA |
| B broader / B | 3 | 500 | 22 / 22 | 0 | 4.18 | 0.75 | 5 | 61 | 0 | NA | NA |
| B broader / B | 3 | ALL | 22 / 22 | 0 | 4.18 | 0.75 | 5 | 61 | 0 | NA | NA |
| 19 / A | 1 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / A | 2 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / A | 3 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / B | 1 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 1 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 1 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 1 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 1 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 1 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / B | 2 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 2 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 2 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 2 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 2 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 2 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / B | 3 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 3 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 3 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 3 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 3 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 3 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / C | 1 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / C | 2 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / C | 3 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |

</details>

<details><summary>EXTENDED_PARTIAL — SECONDARY_RESOLVED_PLUS_AMBIGUOUS: every depth and budget</summary>

| Scope / selector | d | K | n / cohort | Median | Mean | p75 | p90 | Max | Tasks ≥1000 | Reduced / expanded vs A | Total reduction vs A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| B broader / B | 1 | 25 | 22 / 22 | 0 | 3.27 | 2.5 | 8.6 | 25 | 0 | NA | NA |
| B broader / B | 1 | 50 | 22 / 22 | 0 | 5.55 | 2.5 | 8.6 | 50 | 0 | NA | NA |
| B broader / B | 1 | 100 | 22 / 22 | 0 | 8.32 | 2.5 | 8.6 | 100 | 0 | NA | NA |
| B broader / B | 1 | 250 | 22 / 22 | 0 | 8.55 | 2.5 | 8.6 | 105 | 0 | NA | NA |
| B broader / B | 1 | 500 | 22 / 22 | 0 | 8.55 | 2.5 | 8.6 | 105 | 0 | NA | NA |
| B broader / B | 1 | ALL | 22 / 22 | 0 | 8.55 | 2.5 | 8.6 | 105 | 0 | NA | NA |
| B broader / B | 2 | 25 | 22 / 22 | 0 | 4.45 | 4.5 | 16.7 | 25 | 0 | NA | NA |
| B broader / B | 2 | 50 | 22 / 22 | 0 | 6.73 | 4.5 | 16.7 | 50 | 0 | NA | NA |
| B broader / B | 2 | 100 | 22 / 22 | 0 | 9.5 | 4.5 | 16.7 | 100 | 0 | NA | NA |
| B broader / B | 2 | 250 | 22 / 22 | 0 | 9.73 | 4.5 | 16.7 | 105 | 0 | NA | NA |
| B broader / B | 2 | 500 | 22 / 22 | 0 | 9.73 | 4.5 | 16.7 | 105 | 0 | NA | NA |
| B broader / B | 2 | ALL | 22 / 22 | 0 | 9.73 | 4.5 | 16.7 | 105 | 0 | NA | NA |
| B broader / B | 3 | 25 | 22 / 22 | 0 | 4.55 | 4.5 | 16.9 | 25 | 0 | NA | NA |
| B broader / B | 3 | 50 | 22 / 22 | 0 | 6.82 | 4.5 | 16.9 | 50 | 0 | NA | NA |
| B broader / B | 3 | 100 | 22 / 22 | 0 | 9.59 | 4.5 | 16.9 | 100 | 0 | NA | NA |
| B broader / B | 3 | 250 | 22 / 22 | 0 | 9.82 | 4.5 | 16.9 | 105 | 0 | NA | NA |
| B broader / B | 3 | 500 | 22 / 22 | 0 | 9.82 | 4.5 | 16.9 | 105 | 0 | NA | NA |
| B broader / B | 3 | ALL | 22 / 22 | 0 | 9.82 | 4.5 | 16.9 | 105 | 0 | NA | NA |
| 19 / A | 1 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 1 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / A | 2 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 2 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / A | 3 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / A | 3 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / B | 1 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 1 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 1 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 1 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 1 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 1 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / B | 2 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 2 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 2 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 2 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 2 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 2 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / B | 3 | 25 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 95.3% |
| 19 / B | 3 | 50 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 97.3% |
| 19 / B | 3 | 100 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 98.5% |
| 19 / B | 3 | 250 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.4% |
| 19 / B | 3 | 500 | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.6% |
| 19 / B | 3 | ALL | 6 / 6 | 0 | 0.83 | 0 | 2.5 | 5 | 0 | 6 / 0 | 99.9% |
| 19 / C | 1 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 1 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / C | 2 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 2 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |
| 19 / C | 3 | 25 | 6 / 6 | 23 | 17.83 | 25 | 25 | 25 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 50 | 6 / 6 | 35.5 | 30.33 | 50 | 50 | 50 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 100 | 6 / 6 | 60.5 | 55.33 | 100 | 100 | 100 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 250 | 6 / 6 | 135.5 | 130.33 | 250 | 250 | 250 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | 500 | 6 / 6 | 146.5 | 213.67 | 426.5 | 489 | 500 | 0 | 0 / 0 | 0.0% |
| 19 / C | 3 | ALL | 6 / 6 | 146.5 | 875.17 | 426.5 | 2473.5 | 4469 | 1 | 0 / 0 | 0.0% |

</details>

## Candidate graph_status counts per task

`graph_status_by_task.csv` gives every task/strategy/variant/depth; `per_task.csv` additionally gives selected-prefix counts at each K. The full A and C unions have identical status counts; only their order differs. B candidates are reachable pre-existing tests only; its other two status counts are zero when available, and missing when unavailable. The table gives depth-1/2/3 triplets; NA is unavailable.

<details><summary>All 83 tasks, both variants: B and full stored-union status counts</summary>

| Task | Stratum | Variant | B reachable d1/d2/d3 | A/C reachable d1/d2/d3 | A/C mapped-unreachable d1/d2/d3 | A/C unmappable d1/d2/d3 |
|---|---|---|---|---|---|---|
| astropy__astropy-13977 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 1 / 1 / 324 | 1 / 1 / 249 | 3077 / 3077 / 2829 | 4 / 4 / 4 |
| astropy__astropy-13977 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 4 / 327 | 1 / 4 / 252 | 3077 / 3074 / 2826 | 4 / 4 / 4 |
| astropy__astropy-14365 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| astropy__astropy-14365 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| astropy__astropy-14508 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| astropy__astropy-14508 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| astropy__astropy-7606 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| astropy__astropy-7606 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-10973 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-10973 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 1 / 6 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11095 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 23 / 23 / 23 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11095 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 23 / 23 / 23 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11299 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 8 / 8 / 8 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11299 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 8 / 8 / 8 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11820 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-11820 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-12209 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 3306 / 3306 / 3306 | 13 / 13 / 13 |
| django__django-12209 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 3306 / 3306 / 3306 | 13 / 13 / 13 |
| django__django-12965 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-12965 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13023 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13023 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13033 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13033 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13158 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 14 / 14 / 14 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13158 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 14 / 14 / 14 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13212 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 1371 / 1371 / 1371 | 12 / 12 / 12 |
| django__django-13212 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 16 / 17 / 17 | 16 / 17 / 17 | 1355 / 1354 / 1354 | 12 / 12 / 12 |
| django__django-13297 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 1 / 1 / 1 | 1 / 1 / 1 | 8134 / 8134 / 8134 | 20 / 20 / 20 |
| django__django-13297 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 1 / 1 | 1 / 1 / 1 | 8134 / 8134 / 8134 | 20 / 20 / 20 |
| django__django-13569 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13569 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13786 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13786 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13807 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 1 / 1 / 1 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13807 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 1 / 1 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13820 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 26 / 26 / 26 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-13820 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 26 / 26 / 26 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-14140 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 2334 / 2334 / 2334 | 0 / 0 / 0 |
| django__django-14140 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 254 / 260 / 262 | 254 / 259 / 261 | 2080 / 2075 / 2073 | 0 / 0 / 0 |
| django__django-14631 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 4464 / 4464 / 4464 | 5 / 5 / 5 |
| django__django-14631 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 4464 / 4464 / 4464 | 5 / 5 / 5 |
| django__django-15037 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15037 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15103 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 3 / 3 / 5 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15103 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 9 / 14 / 16 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15278 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15278 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15375 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15375 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15499 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15499 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15572 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15572 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 3 / 8 / 8 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15930 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-15930 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 105 / 105 / 105 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16082 | EXCLUDED | PRIMARY_RESOLVED_ONLY | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16082 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16136 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 1 / 1 / 1 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16136 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 1 / 1 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16255 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 3 / 3 / 3 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16255 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 3 / 3 / 3 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16315 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16315 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16612 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 61 / 61 / 61 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16612 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 61 / 61 / 61 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| django__django-16631 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 5 / 5 / 5 | 5 / 5 / 5 | 473 / 473 / 473 | 0 / 0 / 0 |
| django__django-16631 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 5 / 5 / 5 | 5 / 5 / 5 | 473 / 473 / 473 | 0 / 0 / 0 |
| django__django-16667 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 272 / 272 / 272 | 0 / 0 / 0 |
| django__django-16667 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 272 / 272 / 272 | 0 / 0 / 0 |
| matplotlib__matplotlib-14623 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-14623 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-20488 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-20488 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 21 / 21 / 21 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-20676 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 1 / 1 / 1 | 1 / 1 / 1 | 735 / 735 / 735 | 0 / 0 / 0 |
| matplotlib__matplotlib-20676 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 1 / 1 | 1 / 1 / 1 | 735 / 735 / 735 | 0 / 0 / 0 |
| matplotlib__matplotlib-22719 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-22719 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-22871 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 6 / 10 / 10 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-22871 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 6 / 10 / 10 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-23299 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 4 | 0 / 0 / 0 | 46 / 46 / 46 | 0 / 0 / 0 |
| matplotlib__matplotlib-23299 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 4 | 0 / 0 / 0 | 46 / 46 / 46 | 0 / 0 / 0 |
| matplotlib__matplotlib-23476 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 3 / 3 / 3 | 3 / 3 / 3 | 690 / 690 / 690 | 3 / 3 / 3 |
| matplotlib__matplotlib-23476 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 16 / 18 / 24 | 16 / 17 / 17 | 677 / 676 / 676 | 3 / 3 / 3 |
| matplotlib__matplotlib-24026 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24026 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24177 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24177 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24637 | EXCLUDED | PRIMARY_RESOLVED_ONLY | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24637 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24970 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-24970 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-25122 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 2 / 3 / 3 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-25122 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 2 / 10 / 20 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-25287 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-25287 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-25479 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 88 / 88 / 88 | 0 / 0 / 0 |
| matplotlib__matplotlib-25479 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 88 / 88 / 88 | 0 / 0 / 0 |
| matplotlib__matplotlib-26291 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| matplotlib__matplotlib-26291 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| mwaskom__seaborn-3069 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 150 / 150 / 150 | 0 / 0 / 0 |
| mwaskom__seaborn-3069 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 150 / 150 / 150 | 0 / 0 / 0 |
| pallets__flask-5014 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 50 / 50 / 50 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pallets__flask-5014 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 50 / 50 / 50 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4629 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 21 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4629 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 21 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4695 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4695 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4966 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 8 / 8 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-4966 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 8 / 8 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-6599 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-6599 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-6744 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pydata__xarray-6744 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pylint-dev__pylint-4661 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 4 / 4 | 0 / 0 / 0 |
| pylint-dev__pylint-4661 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 4 / 4 | 0 / 0 / 0 |
| pylint-dev__pylint-4970 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 1 / 17 / 17 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pylint-dev__pylint-4970 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 17 / 17 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pylint-dev__pylint-6528 | EXCLUDED | PRIMARY_RESOLVED_ONLY | 29 / 31 / 31 | 29 / 31 / 31 | 188 / 186 / 186 | 1 / 1 / 1 |
| pylint-dev__pylint-6528 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 29 / 31 / 31 | 29 / 31 / 31 | 188 / 186 / 186 | 1 / 1 / 1 |
| pylint-dev__pylint-6903 | EXCLUDED | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pylint-dev__pylint-6903 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pylint-dev__pylint-7277 | EXCLUDED | PRIMARY_RESOLVED_ONLY | 1 / 1 / 1 | 1 / 1 / 1 | 69 / 69 / 69 | 0 / 0 / 0 |
| pylint-dev__pylint-7277 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 1 / 1 | 1 / 1 / 1 | 69 / 69 / 69 | 0 / 0 / 0 |
| pytest-dev__pytest-10051 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-10051 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-5787 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-5787 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-5809 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 4 / 4 | 3 / 3 / 3 |
| pytest-dev__pytest-5809 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 4 / 4 | 3 / 3 / 3 |
| pytest-dev__pytest-6202 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-6202 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7236 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7236 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7432 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7432 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7521 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 2 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| pytest-dev__pytest-7521 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 2 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-10908 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-10908 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-12585 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 40 / 52 / 56 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-12585 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 40 / 54 / 58 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14141 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 1 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14141 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 1 / 2 / 2 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14629 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 10 / 10 / 10 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14629 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 10 / 10 / 10 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14894 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| scikit-learn__scikit-learn-14894 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-10323 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 22 / 22 / 22 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-10323 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 22 / 22 / 22 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-10435 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 90 / 90 / 90 | 0 / 0 / 0 |
| sphinx-doc__sphinx-10435 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 90 / 90 / 90 | 0 / 0 / 0 |
| sphinx-doc__sphinx-10466 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-10466 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-7910 | PRIMARY_COMPLETE | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sphinx-doc__sphinx-7910 | PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 13 / 13 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-13480 | EXCLUDED | PRIMARY_RESOLVED_ONLY | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-13480 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-14711 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-14711 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-17318 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | 0 / 0 / 0 | 21 / 21 / 21 | 0 / 0 / 0 |
| sympy__sympy-17318 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | 0 / 0 / 0 | 21 / 21 / 21 | 0 / 0 / 0 |
| sympy__sympy-19783 | EXTENDED_PARTIAL | PRIMARY_RESOLVED_ONLY | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-19783 | EXTENDED_PARTIAL | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | 0 / 0 / 0 | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-24562 | EXCLUDED | PRIMARY_RESOLVED_ONLY | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| sympy__sympy-24562 | EXCLUDED | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | NA / NA / NA | NA / NA / NA | NA / NA / NA | NA / NA / NA |

</details>

## Graphs, identities and bounded provenance

| Repository | Tasks | Complete / partial | Eligible primary / extended | Files | Nodes | Resolved / ambiguous / unresolved calls | Parse failures / omissions |
|---|---:|---|---|---:|---:|---|---|
| astropy/astropy | 4 | 4 / 0 | 4 / 0 | 3533 | 71140 | 49916 / 18809 / 294480 | 0 / 0 |
| django/django | 31 | 16 / 15 | 16 / 14 | 83199 | 1174952 | 703541 / 337649 / 3558643 | 15 / 0 |
| matplotlib/matplotlib | 15 | 15 / 0 | 14 / 0 | 13399 | 173399 | 167056 / 87403 / 755413 | 0 / 0 |
| mwaskom/seaborn | 1 | 1 / 0 | 1 / 0 | 150 | 2790 | 2223 / 1798 / 15443 | 0 / 0 |
| pallets/flask | 1 | 1 / 0 | 1 / 0 | 80 | 1650 | 613 / 112 / 3208 | 0 / 0 |
| psf/requests | 0 | 0 / 0 | 0 / 0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 |
| pydata/xarray | 5 | 5 / 0 | 5 / 0 | 784 | 27665 | 59736 / 7738 / 123593 | 0 / 0 |
| pylint-dev/pylint | 5 | 0 / 5 | 0 / 2 | 6931 | 43356 | 13852 / 5152 / 65188 | 53 / 6 |
| pytest-dev/pytest | 7 | 4 / 3 | 4 / 3 | 1487 | 35035 | 16225 / 6536 / 100949 | 3 / 0 |
| scikit-learn/scikit-learn | 5 | 5 / 0 | 5 / 0 | 3648 | 42044 | 69504 / 4742 / 268501 | 0 / 0 |
| sphinx-doc/sphinx | 4 | 4 / 0 | 4 / 0 | 2165 | 30378 | 24474 / 5929 / 82359 | 0 / 0 |
| sympy/sympy | 5 | 1 / 4 | 0 / 3 | 6650 | 161225 | 526970 / 197100 / 1116863 | 0 / 43 |

Counts sum task-specific base snapshots, not unique files across a repository. Unresolved calls include external/dynamic/unsupported calls; the table is not an internal-call resolution rate. `graph_diagnostics.csv` lists every omitted/unparseable path, seed status, call reason, graph location and base-identity mapping count. All qualified partials retain their full reasons in `eligibility.json`; no missing file becomes resolved.

Test-ID matching calls the existing diagnostic `canonical`, `family`, and `match_test` functions, with an empty gold-identity map and only base/selected IDs. Exact identities and documented explicit parameter families only; no fuzzy, bare-name or Django docstring guessing. The production `node_ids` supplies base candidates. Legacy nested-class IDs, duplicate definitions and parse/omission gaps stay unmappable. `unmatched_v2_ids.csv` lists all 61 unmappable stored candidates (one inventory per task, not duplicated by d/K/variant).

Every frozen candidate has graph_status reachable / mapped_unreachable / unmappable; per-task rows contain candidate and selected counts for each. Mapped-unreachable scores are 0; unmappable scores/direct counts/distances remain null. Their common C tail uses computable module/package features and original V2 position, without priority for mapping status.

Full paths retained by variant: {'PRIMARY_RESOLVED_ONLY': 963, 'SECONDARY_RESOLVED_PLUS_AMBIGUOUS': 1561}; the maximum is 22,950 per variant / 45,900 overall. Only top 25 B/C candidates per task/variant/depth carry up to three lexical-seed paths of at most three hops. Budgets share those rows; all later ranks and omitted seed paths are aggregated by distance and budget membership. Secondary provenance flags each ambiguous hop, original call site, candidate targets and reasons, and records whether resolved-only reachability exists at the same depth. Ambiguity on a selected shortest path does not prove it is required.

`paired_variants.csv` provides common-task primary/secondary counts and resolved-only retention; it never pools variants or changes the primary decision.

## Validation and reproduction

Synthetic fixtures only; benchmark tests are not run. The exact test output is in `tests.txt`. `validation.json` checks frozen inputs/outputs, budgets, identities, shared-tail ranking, strata, criteria and provenance caps.

```bash
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py reports/callgraph_selection/phase2/test_phase2.py -q -p no:cacheprovider -o addopts=
# Detached execution used for this run; wait for BACKGROUND_RUN_COMPLETE exit=0, then freeze:
nohup bash reports/callgraph_selection/phase2/run_background.sh > reports/callgraph_selection/phase2/background_attempt_2.log 2>&1 < /dev/null &
cg_selector_pid=$!
printf "%s\n" "$cg_selector_pid" > reports/callgraph_selection/phase2/selector_pid.txt
wait "$cg_selector_pid"  # Keep the sandbox parent alive; poll the background log from another call.
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage freeze
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage report
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/finalize_report.py
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/validate.py
```

The select stage refuses to overwrite an existing selector freeze. Reproduce selection in a clean copy containing the pinned code/README and local inputs but none of the generated phase-2 outputs; report-only reproduction verifies the existing freeze and does not rerun selection. All changes remain inside reports/callgraph_selection/ and uncommitted. Work stops at this report, before phase 3.
