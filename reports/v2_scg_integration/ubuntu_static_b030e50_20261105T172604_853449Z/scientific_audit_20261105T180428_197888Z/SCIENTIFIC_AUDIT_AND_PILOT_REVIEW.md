# Scientific audit and three-task pilot plan — 2026-11-05

**Recommendation: GO for a separately authorized three-task diagnostic pilot of this exact plan. The pilot has not run and is not authorized by this report. No static integrity or implementation blocker was found.** Runtime source/import fidelity remains a pilot check, and the partial graphs, empty selections and abstentions must remain explicit.

The harness is the clean detached worktree `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50` at `b030e508d849926b9a2260c70e1091adebfee993`. The protocol remains:

`2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153`

The unchanged harness `validate` command passed again for all **83 tasks**. It verifies the frozen source/configuration, host inventory, original V2 inputs, current Docker daemon/tag bindings and artifact seals. **765 sealed artifacts** match. Before/after snapshots prove all **766 frozen files**, including `artifact_hashes.json`, are byte-identical after the audit and plan creation. The freeze was not resealed. All 83 exact images remain bound and available, and archived source/base identities remain verified.

The audit independently rebuilt all 83 pinned static graphs from their verified base archives, using unchanged graph limits and the sealed corrected SCG source at `e1a3ed1c74fd304493c3fe3811de755af77e306c`. Graph status, counts, diagnostics, qualified mapping records, resolved seeds and ordered selection lists all reproduced exactly. A separate breadth-first implementation and independent Fraction-based specificity/ranking calculation then matched **all 83 memberships/orders**. Its **131 selected-test path proofs** contain only resolved edges: **64 minimum paths of length 1, 38 of length 2, and 29 of length 3**. The frozen canonicalization/index and graph builder were reused; this is an independent traversal/ranking check, not a new parser or a proof of complete Python runtime dispatch.

The four parallel audit workers took **515.93 seconds**. They read archive/AST data and wrote separate diagnostic evidence. They never imported benchmark source as executable modules, started containers or ran benchmark tests. These replay timings are verification costs and do not replace or alter the original serial preparation measurements.

The confirmed configuration is **B / depth 3 / ALL / PRIMARY_RESOLVED_ONLY**. Exact directly edited base definitions are seeds; the mapper uses path, qualified name, definition kind and location. Candidate-only definitions and module-level edits do not invent base seeds. Only resolved edges enter reverse traversal; eligible test definitions must reach a seed in one to three calls. Strategy-B ranking retains every eligible candidate because budget ALL applies no truncation. There is no V2 candidate-list filter, ambiguous-edge inclusion, whole-module/class fallback, test injection, correctness-label input or historical-regression-witness input.

Why the 13 / 68 / 2 split is produced:

| Result | Tasks | Audit conclusion |
|---|---:|---|
| Nonempty SCG | 13 | Resolved depth-1-to-3 paths produce exactly 131 ordered IDs; independent membership/ranking agrees. |
| Empty SCG (`[]`) | 68 | Every task has resolved seeds and a positive uniquely emittable base-test inventory (minimum 384), but **no graph test definition reaches a seed within three resolved calls**. This is not a missing inventory or mapping-error artifact. |
| Unavailable SCG (`null`) | 2 | No resolved base seeds under the corrected policy; retained as abstentions, never changed to empty lists. |

There are **106 resolved mapping records, 21 candidate-only definitions, and no ambiguous, unresolved or file-analysis-error mapping records**. All changed source files were present, and no graph-failure file was a candidate-changed file. No worker error or resource-limited graph occurred. The 68 zero lists exactly implement the policy on the retained graphs; they do **not** establish that real tests cannot call the changed code. The 47 zeros on mechanically complete graphs may still reflect unresolved calls, dynamic Python behavior or paths deeper than three. The 21 zeros on partial graphs additionally retain omitted/failed source coverage. The audit found no implementation discrepancy; it does not prove the static model is sound or complete for runtime behavior.

The two unavailable cases are specifically explained by base-source/patch evidence:

- `django__django-13569`: the patch introduces `Random.get_group_by_cols`. It has no base definition and is correctly classified as a candidate-only definition, leaving no seed. Its graph is complete.
- `django__django-16082`: the patch adds `Combinable.MOD` to module-level `_connector_combinations`. It does not directly edit a named definition, so the mapper emits `edits_outside_named_definitions` and no seed. Its separate partial-graph syntax-error fixture does not cause this seed absence.

Graph completeness and nonempty-selection concentration:

| Graph status | All tasks | Nonempty | Empty | Unavailable | Selected IDs |
|---|---:|---:|---:|---:|---:|
| Complete | 56 | 8 | 47 | 1 | 106 |
| Partial | 27 | 5 | 21 | 1 | 25 |
| Total | 83 | 13 | 68 | 2 | 131 |

Thus **8/13 nonempty tasks** and **106/131 IDs** come from complete graphs; **5/13 tasks** and **25/131 IDs** come from partial graphs. Relative to each stratum, nonempty rates are **8/56 (14.3%)** and **5/27 (18.5%)**. Nonempty selections are not confined to complete graphs. These are descriptive counts, not correctness/detection results. Partial graphs retain 71 SyntaxError records, 6 link/special-file omissions and 43 retained-AST quota omissions across repeated task snapshots; no omissions are erased by this audit.

Selection sizes (ordered IDs per task; linearly interpolated `(n-1)*p` quantiles):

| Population | Observed / unavailable | Zeros | Min | P25 | Median | P75 | P90 | Max | Mean | Total IDs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V2, all tasks | 83 / 0 | 5 | 0 | 46 | 217 | 711.5 | 2251 | 8152 | 694.96 | 57,682 |
| SCG, available lists | 81 / 2 | 68 | 0 | 0 | 0 | 0 | 2 | 56 | 1.62 | 131 |
| SCG, nonempty lists only | 13 / 0 | 0 | 1 | 2 | 4 | 10 | 20 | 56 | 10.08 | 131 |

The two null SCG lists are excluded from numerical size/overlap calculations, never imputed as zero. For the **81 tasks with both lists available**, task-specific counts sum to **120 shared IDs**, **57,039 V2-only IDs**, and **11 SCG-only IDs**. Comparable V2 total is 57,159, SCG total is 131, and union total is 57,170. **120/131 (91.6%)** of SCG IDs are already in V2; 10 of 13 nonempty SCG lists are V2 subsets. The other three tasks have SCG-only IDs, so SCG is not universally a V2 subset. Pooled Jaccard is **0.2099%**. Mean task Jaccard is **2.3719% over 76 defined cases**; five both-empty cases are undefined, not zero or perfect agreement. Counts sum per-task identities rather than deduplicating across repository versions. None is a test recall or accuracy estimate.

Original, unchanged preparation costs: **1,433.36 seconds (23m 53s)** for the command; V2 selection computation **33.64 seconds** and V2 workers **54.41 seconds**; SCG extraction **41.35 seconds**, graph construction **924.37 seconds**, mapping/ID inventory/ranking **343.45 seconds**, and SCG workers **1,360.44 seconds**. Each arm metric has 83 measured tasks. Maximum SCG worker RSS is **2,562,646,016 bytes (2.39 GiB)**. These static costs say nothing about benchmark execution speed or regression detection.

The final pilot tasks were chosen for the requested technical strata, three repositories, pytest plus native Django adapters, both frozen arm orders, the depth-3 boundary, SCG-only source coverage and explicit empty-arm handling. No correctness labels, known witnesses or prior outcomes were read. A provisional Astropy complete-graph example was replaced by Xarray solely because Xarray supplies five SCG-only IDs; the provisional rationale is retained separately. All three requested categories are available, so no category fallback is needed.

| Actual frozen schedule | Graph | V2 IDs | SCG IDs | Arm order | Technical coverage |
|---|---|---:|---:|---|---|
| `django__django-15103` | Partial | 47 | 1 | V2 → SCG | Django native labels, one resolved-call path; the syntax-error fixture is outside selected/changed files. |
| `matplotlib__matplotlib-25287` | Complete | 2 | 0 | SCG → V2 | Explicit empty SCG arm, V2 plotting/image-comparison setup; 2,475 emittable definitions but no eligible depth-3 path. |
| `pydata__xarray-4629` | Complete | 22 | 21 | V2 → SCG | All 21 SCG paths have depth 3; five IDs are absent from V2 and exercise extra shared-source/import coverage. |

Xarray's five SCG-only IDs are `xarray/tests/test_dask.py::test_lazy_array_equiv_merge`, `xarray/tests/test_dataset.py::TestDataset::test_combine_first`, `xarray/tests/test_options.py::TestAttrRetention::test_merge_attr_retention`, `xarray/tests/test_sparse.py::TestSparseDataArrayAndDataset::test_merge`, and `xarray/tests/test_units.py::test_merge_dataarray`. Optional dependencies, concrete parameter expansion, fixtures and imports remain runtime checks; they were not tested or assumed available during this audit. All pilot task image comparisons are historical-non-null DIFFERENT; this focused pilot does not exercise historical-null binding execution or the two no-seed abstentions.

The explicit plan was created by the unchanged harness `plan` command, with these three `--task` arguments and the existing freeze. Arm order follows **full-cohort indices 22, 47 and 52**, not a newly invented order for the subset. The exact plan is:

`/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/scientific_audit_20261105T180428_197888Z/pilot_plan.json`

Plan SHA-256:

`57c84e2ceb615ebe7df43a5a26cf140b300b5a838f706ce6f7f7a5d2b9a77f1d`

Plan status remains **PLAN_FOR_REVIEW_NOT_AUTHORIZED**. It binds the unchanged protocol hash transitively to all selections, candidate bytes, source hashes and image IDs. The complete **93 ordered ID slots** across its six arm lists, exact manifest paths/hashes, graph statuses and bindings are recorded in `pilot_scope_details.json`; no frozen list is truncated.

Expected separately authorized execution scope is **3 tasks / 6 arm records**. There are **5 nonempty arm invocations**, each with a fresh container if all checks pass; Matplotlib SCG records ZERO_SELECTION/native NOT_AVAILABLE without a container. Nominal initial base/patched coverage is **10 pass observations and 186 requested-ID slots**, before parameter expansion. Existing baseline-unreliable guards may omit a patched pass, and existing production confirmations/shadow observations may add passes. The 300-second per-pass budget and existing 600-second nominal pair metadata remain unchanged; 3,000 seconds across the five nominal pairs is not a new hard global timeout.

Docker event history for the exact plan-creation interval contains **zero container events**, including zero creates/starts; the daemon currently has zero containers. Independent before/after hashes show the freeze and seal unchanged. No benchmark tests ran, no pilot/full comparison was launched, no fallback or extra test was injected, no frozen artifact was resealed, and no selector/classifier source was modified. **Runtime import fidelity remains unverified and is a purpose of the separately authorized pilot.**

The scientific GO recommendation is for this limited diagnostic pilot only. Its 3 tasks/5 nonempty arms are not representative enough to estimate full-cohort comparative performance or detection. Retain partial graph strata and empty/unavailable arms in any later analysis. Stop here for plan review and explicit separate execution authorization.

Evidence files: `validate.stdout`, `graph_replay_summary.json`, `independent_audit_checks.json`, all `graph_replay/<instance_id>.json` path/diagnostic records, `selection_statistics.json`, `selection_comparison.json`, `pilot_selection_final_rationale.json`, `pilot_scope_details.json`, `pilot_plan.json`, `plan.result.json`, `plan_container_verification.json`, and `frozen_preservation_after_plan.json`. The audit procedure source is `audit_procedure.py`. All outputs are new and outside the freeze.
