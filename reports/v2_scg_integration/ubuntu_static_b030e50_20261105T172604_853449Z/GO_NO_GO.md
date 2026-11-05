# Ubuntu paired harness static preparation — 2026-11-05

**GO: static preparation and immutable-freeze validation passed. NO-GO: pilot/full benchmark launch until separate review and authorization.**

Preparation exited successfully with code 0 after **1433.36 seconds (23.89 minutes)**. A separate invocation of the updated harness's `validate --frozen ...` passed: `{"verified": true, "tasks": 83, "containers_started": 0}`.

| Identity | Value |
|---|---|
| Harness commit | `b030e508d849926b9a2260c70e1091adebfee993` |
| Detached review worktree | `/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50` |
| Corrected SCG revision | `e1a3ed1c74fd304493c3fe3811de755af77e306c` |
| Original V2 revision | `9654fc7c4168da0ff0c1bdf786f99a8a38d0c006` |
| Paired protocol version/status | **2 / PREPARED_FOR_REVIEW_NOT_AUTHORIZED** |
| Protocol SHA-256 | `2eaf8341274099cf4210674e6418a4b1e44ea2d0babb09a1c2243f77258c5153` |
| Paired freeze | `/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen` |
| Image-binding SHA-256 | `af2e5c19b0a875b53f93f734798c151767b46412083e18dfe3fb60a19bcc1329` |

The requested `GIT_TERMINAL_PROMPT=0 git -c credential.helper= fetch origin` was attempted, but HTTPS authentication failed with terminal prompts disabled. This is a fetch warning: the exact requested commit was already present locally, and the connected GitHub API independently confirmed that `origin/experiment/v2-scg-paired-harness` was at that same full SHA. The detached worktree was created directly at that commit. No branch was merged, and existing worktrees/untracked files were preserved. The review worktree remains clean. See `setup.json`, `remote_branches_verified.json` and `worktree_preservation_final.json`.

`uv sync --frozen` succeeded in the new worktree, creating its own Python **3.11.17** environment with **156 packages**. Package versions exactly match the historical inventory; the lockfile is unchanged. Commands used the README's worktree-specific `PYTHONPATH`, preventing inherited ROS/system packages from shadowing dependencies. The README's complete documented unit suite passed **234 tests, 0 failures, 0 errors, 0 skips**, in **32.13 seconds**. Ruff passed for all five documented files. No selector, classifier, candidate, verdict, ranking, timeout, graph limit or policy code was modified.

The offline `preflight` passed for **83/83 unique task identities and archive SHA-256 hashes**, using the existing `/home/sankalp/cg_repos/task_archives` path. Base commits and candidate identities are preserved. The new `bind-images` command found **83 AVAILABLE, 0 MISSING, 0 INSPECTION_ERROR**. It separately recorded **39 historical ID differences** and **44 historical null IDs**. Historical IDs, digests and environment-status fields remain unchanged; both arms use each task's separately sealed actual Ubuntu `host_image_id`. Binding validation re-inspected exact tags and checked daemon/host identity. No image was pulled, built, retagged, substituted or deleted.

| Static selection result | Updated V2 | Corrected SCG |
|---|---:|---:|
| Task selections prepared/accounted | 83 | 83 |
| Exactly reproduced original V2 lists and runners | **83/83** | Not applicable |
| Available selections, including empty | 83 | 81 |
| Nonempty selections | 78 | 13 |
| Empty selections (`[]`) | 5 | 68 |
| Unavailable selections (`null`) | 0 | 2 |
| Total ordered selected IDs across tasks | 57,682 | 131 |

SCG retains the existing **B / depth 3 / ALL / PRIMARY_RESOLVED_ONLY** configuration. Its **56 complete / 27 partial graphs** include **0 resource-limited graphs** and **0 worker exceptions**. The two unavailable selections are `django__django-13569` and `django__django-16082`, both `UNAVAILABLE_NO_RESOLVED_SEEDS`; neither is converted into an empty list or a V2 fallback. These are explicit selector abstentions, not missing-image failures. The 68 empty SCG selections remain explicit ZERO_SELECTION outcomes. Preparation has produced no V2/SCG test verdicts.

Partial graphs retain their diagnostics: **71 SyntaxError records, 6 archive-link/special-file omissions, and 43 largest-first retained-AST quota omissions**, summed across task snapshots. Counts include repeated repository versions and are not unique-source counts. These limitations are preserved in the freeze and must remain visible in later analysis. Static availability does not imply all 83 tasks will produce two binary benchmark outcomes. See `warnings.json` and the per-task inventory.

| Static preparation cost | Measured value |
|---|---:|
| Entire prepare command, including final checks | 1433.36 s |
| Protocol's preparation measurement | 1431.88 s |
| V2 selection computation, summed over 83 | 33.64 s |
| V2 workers including startup, summed over 83 | 54.41 s |
| SCG archive extraction, summed over 83 | 41.35 s |
| SCG graph construction, summed over 83 | 924.37 s |
| SCG ID inventory/mapping/ranking, summed over 83 | 343.45 s |
| SCG workers including startup, summed over 83 | 1360.44 s |
| Largest SCG graph-build time | 56.30 s |
| Maximum SCG worker peak RSS | 2,562,646,016 bytes (2.39 GiB) |

All reported arm costs have 83 measured tasks. These are static preparation measurements, not benchmark execution performance. The protocol timer stops before final sealing/validation; the outer command measurement includes that work. Per-task times, graph counts, RSS, CPU and diagnostics are retained in `task_preparation_inventory.json` and each selection manifest.

The shared archive/source manifest is **FROZEN_UNION for 83/83 tasks**, covering **1,546 task-specific source-file entries**, with **0 missing files**. It preserves all 1,536 original V2 relevant-source hashes and adds 10 SCG-selected source-file entries. Both arms will use the same union. The entire historical V2 freeze remains copied and unchanged: **252 original sealed artifacts verified**. The new paired freeze has **765 sealed artifacts**, and all **10 SCG source snapshot files** match the pinned Git revision. Task IDs, repositories, base commits, original archive hashes, candidate bytes, issue text, V2 selections and historical environment metadata all match the original freeze.

**Archive fidelity is not runtime import fidelity.** No benchmark container or benchmark test was launched during this work; the documented unit tests use synthetic fixtures/executors. Actual container source checks and imports remain **NOT VERIFIED by static preparation** and must be confirmed in a separately authorized pilot. Matching image tags/IDs alone are not treated as source proof. No correctness labels or known witnesses were supplied to preparation, and no outcomes were used to change selection.

Remaining review items are the 27 partial graphs, 68 empty SCG selections, 2 SCG abstentions, and runtime source/import fidelity during an authorized pilot. There is no detected static input/seal, dependency, image-binding or preparation-worker blocker. Git HTTPS authentication remains unavailable for future fetches. No pilot scope/plan was created, no `run` CLI command was invoked, and no full comparison, commit or push was performed.

Evidence and artifacts:

- `paired_frozen/protocol.json`, `paired_frozen/artifact_hashes.json`, `paired_frozen/tasks.json`: new frozen artifact set, protocol/hash seals and task identities.
- `paired_frozen/selections/<instance_id>/v2.json` and `scg.json`: exact ordered selections, graph diagnostics and measured costs; worker stdout/stderr are retained beside them.
- `ubuntu_image_bindings.json` and its identical sealed copy `paired_frozen/image_bindings.json`: all 83 Ubuntu bindings.
- `offline_preflight.json`: archive/identity/host checks.
- `unit.xml`, `unit.stdout`, `unit.stderr`, `lint.stdout`, `lint.stderr`: Ubuntu unit/lint evidence.
- `prepare.result.json`, `prepare.stdout`, `prepare.stderr`, `validate.result.json`, `validate.stdout`, `validate.stderr`: complete stage records. Preparation and validation return codes are both 0; stderr is empty.
- `task_preparation_inventory.csv` / `task_preparation_inventory.json`: all 83 identities, bindings, selections, graph states, times and shared-source counts.
- `static_preparation_summary.json`, `warnings.json`: machine-readable aggregate counts and explicit caveats.

Stop point: **static preparation and validation complete; freeze ready for review, benchmark execution not authorized.**
