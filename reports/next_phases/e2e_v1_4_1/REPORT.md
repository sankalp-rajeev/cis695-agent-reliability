**PASS — A1–A7 are complete. The v1.4.1 pipeline is ready for a pilot or audited run using a manifest, validated task registries, and model configs. No repair-model rerun, model call, correctness grading, or push was performed.**

| Check | Verdict | Evidence |
|---|---|---|
| A1 selection | PASS, 83/83 | Package ArchiveTree + unchanged select_tests reproduce the same IDs in the same order; [A1.json](A1.json). |
| A2 guarded V2 replay | PASS, 83/83 | All four policies' per-test outcomes and signals equal the sealed result.json; zero health halts; [A2.json](A2.json). |
| A3 decision replay | PASS | 14 ACCEPT / 67 FLAG / 2 REJECT, equal to Phase 7 S_invalid_excluded; zero differences and zero unattributed differences; [A3.json](A3.json), [decisions_83.csv](decisions_83.csv). |
| A4 live Docker | PASS, 3/3 | Fresh VERIFIED pristine receipts, identical selected/concrete native G1 identity sets, identical per-test outcomes/signals under all four policies; --skip-v4 stamped on every record; [A4.json](A4.json). |
| A4b registry interface | PASS | Hand-prepared existing task in another cohort/origin yields the same operational TaskSpec/BaseSourceSpec; wrong hash, duplicate ID and missing field refused; [A4b.json](A4b.json). |
| A5 fault injection | PASS | All 61 e2e mocked/unit checks pass, including 13 added for resumable caps, strict non-cap headers, attempt audit trails and ledger seeding; [A5.json](A5.json). |
| A6 unit/preservation | PASS by test ID | Zero new failed/error IDs versus the supplied machine reference; every new test passes; both frozen manifests match (75 entries); [unit_comparison.review.json](unit_comparison.review.json). |
| A7 independent check | PASS | Standard-library-only script independently rehashes the registry/frozen inputs and compares raw policy outcomes and live receipts; [A7.json](A7.json). A1 uses recorded selector output, explicitly disclosed below. |

## Review fixes (17 November 2026)

The first unpublished local `e2e-v1.4.1-frozen` tag (object `abd2d70`, commit `272717e27f87eb72cc4c4704a1274bc986ad8fc3`) was withdrawn at the user's request before this review. Reviewed implementation HEAD is **`8789c9ffb9df7146677d22d203663f567b9ee7a1`**; the final release HEAD is the recreated annotated `e2e-v1.4.1-frozen^{commit}`, adding only this report and check evidence to that implementation commit. The final commit ID is also returned with delivery. Nothing is pushed.

Resume now permits changes to only `deepseek_cap_usd`, `um_cap_usd` and `um_job_cap_usd`. Every other header field, including the ledger path, remains strict. The original header keeps its first-attempt caps and remains the task-provenance authority. Each attempt records its caps and provider/account costs at start in `attempt.json`; unresolved request reservations count conservatively. A lowered cap below existing account/job commitments stops with `STOPPED_BUDGET` before any new paid call. A raised cap resumes the stopped task and retains complete frozen repair patches. Paid work and per-task ceilings never reset.

`scripts/seed_provider_ledger.py --from <probe ledger>` makes a SHA-256-verified byte copy to the shared ledger, refuses a non-empty destination and prints per-account totals. A mocked legacy $0.66 UM seed is charged against the new account cap. The runbook places this one-time step before the first paid pilot, uses audited UM account/job caps of $20/$20, and explains DeepSeek's funded-balance margin and cap increases on resume. No real provider ledger was seeded during review.

The exact full-suite command below was repeated: **1566 passed, 7 skipped, 6 failed, 17 errors in 67.53 seconds**. Comparison by ID finds **zero new failed/error IDs**, identical failed/error statuses to the first release, no reference failures now passing, and no `SANDBOX_ONLY` failures. All **61 old and new e2e tests pass** in the focused run (4.59 seconds). Logs: `runs/e2e_v1_4_1_checks/pytest.review.out` and `pytest.e2e.review.out`; [ID comparison](unit_comparison.review.json).

A1–A4 were **not rerun**: verifier code, verifier configs and task registries remain byte-identical. This command produces **empty output**, saved in [verifier_diff.review.stat](verifier_diff.review.stat), and is checked again against the final release HEAD:

```bash
git diff --stat 272717e27f87eb72cc4c4704a1274bc986ad8fc3 HEAD -- src/reliability/verifier/ configs/verifier/ configs/e2e/
```

The independent checker was rerun successfully with `env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_e2e_v1_4_1.py`; its output remains exactly the seven PASS lines reproduced below, also saved in [independent_verification.review.out](independent_verification.review.out). Registry SHA, all 75 frozen hashes, raw A2 outcomes and A4 receipts are unchanged. A read-only full seal recheck again verified all **1,799 files / 3,488,110,239 bytes**; [seal_check.review.json](seal_check.review.json). No model calls, labels, pushes, or sealed-folder writes occurred.

## Frozen implementation and inputs

Policy version: `v1.4.1-full`. `FullPolicyV141` subclasses `FullPolicyV14` and changes only the version string. Every v1.4.0 reproduction file and every file listed by the UM freeze manifest remains byte-identical. The new verifier config, setup and record format live beside the old ones; `run_pilot.py` is untouched.

Registry: `configs/e2e/task_specs_83.json`, SHA-256 **`9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb`**, origin `phase4_freeze`. It contains only patch-independent preparation data. The committed builder verifies the frozen protocol/tasks, patch and selection hashes, archives/PAX commits, SWE-bench 4.0.4 wheel/projection, preflight receipts and Django command-source hashes. The final registry was generated at committed builder HEAD `e567e3eb5c49a3e1a56b2f1468d44214165924b8`. Rebuilding changes only `built_by_commit`: every task row and all 83 operational TaskSpecs are identical to the registry used by the final offline replay, as verified in [registry_operational_equivalence.json](registry_operational_equivalence.json).

The sealed capture root was read only by absolute path:

```
/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/phase4_v4_attempt4_20261109T185713Z
```

All **1,799 files / 3,488,110,239 bytes** were verified before replay, against manifest SHA-256 `69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25` and its authority in the seal's results.json. No file in that source folder was written, moved, touched or copied into. [seal_check.json](seal_check.json) retains the verification result. The final offline captures are under `runs/e2e_v1_4_1_checks/offline_final/`.

All 31 Django sources were hash-verified before argv-only whitelist projection. Their exact file/hash list and the byte-only golden.csv exception are recorded in [DECISIONS.md](DECISIONS.md). No outcome field from those command sources was decoded or recorded. All 83 pinned images are present locally; no image pull or build occurred ([pinned_images.json](pinned_images.json)).

## Runtime and accounting decisions

The full path is `scripts/run_e2e.py`: repair agent, freeze, V1, archive selection, inline G1, guarded V2, V3, V4, then the unchanged v1.4 decision rule. It accepts any valid registry cohort and refuses duplicate IDs across files. A missing spec creates V2/V3 `NO_TASK_SPEC` absences. The shared schema and its two optional local artifact-path fields are documented in `docs/TASK_SPEC_SCHEMA.md`.

V2 runs serially in the pinned image with `--pull=never`, network none, CPU shares 2048, a BaseSourceSpec and a fresh VERIFIED receipt before runtime. It snapshots generated inputs, disables the baseline cache, uses 1800 seconds per pass, and retains guards G1–G6. C_invalid_excluded captures live execution and confirmation calls; the other policies replay those calls without I/O. The decision uses **S_invalid_excluded**. Reports are in each task's `verification/v2_policies.json`, health records in `verification/health.jsonl`.

G1 and G2 references are computed for the actual patch/selection. The published pylint-4970 exclusions apply to the current selected intersection, with the same native absence proof; a new repair patch is not required to reproduce the old 16-ID selection. Base drift IDs are the Fix 16 intersection; patched drift IDs are empty. No historical positive G1 reference or committed G1 collection constant is used by live verification.

A per-task V2 health/executor/replay/3-hour failure becomes an attributed absence and continues through V3, V4 and the decision. Three consecutive infrastructure absences, or 20% after at least ten completed tasks, stop systemically. Source integrity aborts the batch. Budget/auth/interrupt stops write completed/not-completed task lists and a seal. Resume preserves a complete frozen repair patch and archives unfinished verification. Patch bytes, including line endings, are preserved and rechecked before the decision.

Every paid E2E route uses the persistent per-provider/account ledger. Legacy untagged ledger entries count as UM/default-account calls. Both repair arms share the DeepSeek account cap through one ledger file. Default DeepSeek cap is $4.00, stamped in the header; costs come from per-call response usage and the ledger, never old V4 telemetry. Before V4, the full configured ceiling is escrowed; an unfundable stage is NOT_RUN/BUDGET_STOP, while a halt after paid calls is marked PARTIAL. Resume does not reset a spent per-task ceiling. Detailed one-line reasons are in [DECISIONS.md](DECISIONS.md).

## Live checks and integration

Final live outputs: `/home/sankalp/projects/wt-e2e/runs/e2e_v1_4_1_checks/live_frozen`. The run used `--mode pilot --verify-only-from <paired_frozen> --skip-v4`, with both model configs explicit and hashed. Each task record binds image, archive, pristine receipt, selection, patch and G1 receipt hashes to the run header. The independent checker verifies those stamps.

| Instance | Native runner | Selected IDs | Four-policy comparison |
|---|---|---:|---|
| django__django-13033 | Django | 4 | Exact |
| sympy__sympy-17318 | SymPy bin/test | 21 | Exact |
| matplotlib__matplotlib-25287 | pytest | 2 | Exact |

No frozen Django command requests `--parallel 1`; all 31 choices were checked. Every live decision is FLAG because V4 was intentionally skipped. There were no live differences needing a flaky/timeout attribution.

The latest `origin/feature/umgpt-routing` was fetched with `--no-tags` and merged with `git merge --no-edit` (no rebase). Git reported `Already up to date.` Its tip is `983c3f403948949fb159eeb5448e42391b5cad65`, included in this branch; [routing_merge.json](routing_merge.json) records the result.

The approved cache copy contains only Verified's dataset and matching Hub entry: **15,423,138 file/symlink bytes**, [hf_cache_copy.json](hf_cache_copy.json). The full suite ran from this worktree with its own environment:

```bash
env -u PYTHONPATH HF_HOME=/home/sankalp/projects/wt-e2e/runs/hf_home HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE
```

The first post-merge result was **1553 passed, 7 skipped, 6 failed, 17 errors**; the review run above adds 13 passing tests. Acceptance is based on IDs: **zero** failed/error IDs beyond `/home/sankalp/projects/unit_baseline_7fefe1d/failing_ids.txt`; the failed/error IDs and statuses are identical before and after the merge and review. All 30 sandbox cache errors are resolved; `SANDBOX_ONLY` is empty. **No reference failure now passes**, so there is no repaired-reference-failure list to explain. All 61 e2e tests pass. Full logs remain in `runs/e2e_v1_4_1_checks/`.

## Independent checker output

```text
PASS registry: 83 frozen task identities and artifact hashes; SHA-256 9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb
PASS frozen artifacts: 75 matching hashes; golden CSV hashed as bytes only
PASS A1: 83/83 identical ordered lists (RECORDED_OUTPUT_ONLY; selector not independently reimplemented)
PASS A2: 83/83 raw four-policy per-test/signal equality, zero recorded health halts
PASS G1 authority: sealed launch manifest SHA-256 d2c4277141abcc2bfdf20fb87ee82a92a10dd44b251879b74c0f30c5d8ccc3bb
PASS A4: VERIFIED pristine receipts, sealed selected/concrete native identity sets and all four policy outcomes for django__django-13033, sympy__sympy-17318, matplotlib__matplotlib-25287
PASS independent checker; standard library only; no model calls
```

## Known limitations

- New instances require the task-prep job's registries and prepared artifacts; no specs for the 17 new instances were built here.
- The patched-tree environment-drift guard is weaker. Fix 16 supplies the base reference only; fresh native G1 remains required on both trees.
- A4 used `--skip-v4`. Paid repair and generator calls were tested with mocks; no paid pilot/audited rerun or correctness grading was performed.
- A7 checks A1's recorded selection arrays and their order against frozen inputs. It does not independently reimplement the multi-tier selector; primary A1 executes the actual package selector on all 83 archives/patches.
- Paid work is not refunded or given a new per-task ceiling on resume. A budget stop can leave tasks unfinished; the shared account cap persists across output folders and arms.
- Source-scope note: a source-location search opened Phase 7 stage5 code/recompute notes and V1 probe code outside the narrow decision-table/recompute-input allowance. No referenced label/oracle files or correctness fields were opened; acceptance computations use the permitted frozen data, policy snapshots and decision table.

The release tag is the recreated annotated local `e2e-v1.4.1-frozen`, at the final documentation commit after all checks. Publication is left to the user: **no branch or tag push is made**. [RUNBOOK.md](RUNBOOK.md) gives exact pilot/audited/check commands.

## Pilot findings and v1.4.2 fixes

Reviewed on 17 November 2026: the user confirmed matplotlib-25287's selected SVG cases are skipped in this image, an expected environment limit, and authorized continuation. Its V2 behavior is unchanged. The published `e2e-v1.4.1-frozen` tag remains unchanged; the new release is the local annotated `e2e-v1.4.2-frozen` tag.

The label-free pilot evidence is in `runs/e2e_v1_4_1_pilot_A/tasks/`. Django-13033 has an 885-byte patch, PASS for V1–V4 and decision ACCEPT. Sympy-17318 has a zero-byte patch, V1 FAIL (`empty: patch is empty`), V2 absence `RUN_HEALTH_G1:stage_error_requires_review`, V3 absence `EXECUTOR_EXCEPTION:ContainerError`, and decision REJECT. Its eleventh repair call timed out; v1.4.1 converted the transient failure to an aborting `ProviderStageError`, then froze an empty patch. These records are historical pilot evidence, not rerun results.

Matplotlib-25287 has a nonempty 1,181-byte patch. Its `verification_record.full-v1.4.1.json` records V2 outcome `NOT_AVAILABLE`, absence `incomplete`, no `findings.absence_reason`, and this exact `detail`:

```text
V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]
```

Its `verification/selection.json` supplies these two ordered IDs, both from tier 2 (tier 1 is empty):

```text
lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image
lib/matplotlib/tests/test_skew.py::test_skew_rectangle
```

The selection uses runner `pytest`, evidence `pytest.ini or conftest.py; pytest referenced in tox.ini`, and `django_parallel_one: null`. Its convention is `sibling_tests`, hit rate 0.1 over 200 samples; convention scores are `sibling_tests: 0.1` and zero for `mirrored_tree`, `suffix`, `flat`, and `tests_tree`. Symbols are `XAxis` and `YAxis`; `excluded_agent_tests` is empty. V1, V3 and V4 PASS, while the unchanged policy returns FLAG.

all selected tests skipped on both trees, so NOT_AVAILABLE; expected, not infrastructure

**Transient-provider fix.** DeepSeek repair, UM repair, and both V4 routes share one classifier. Timeout/408, ordinary rate-limit/429, 500/502/503/504, APIConnectionError and ServiceUnavailableError propagate as `ProviderTransientError`, outside `abort_exceptions`. Each attempted request retains its entire conservative reservation as spent (`reservation_retained: true`); the ledger entry is settled at that bound so its existing unsettled-request guard permits the next reservation. No uncertain charge is refunded and `runtime.halt` stays unset. Auth 401/403, payment/balance/quota, and other client errors keep their stop/stage semantics. A rate-limit body saying “rate limit exceeded” alone is transient, not a quota stop.

After the native query retries exhaust, repair captures `git diff --` through the attached environment, using the submit prompt's diff extraction against the current tracked working tree rather than a possibly absent or stale `patch.txt`. The patch is frozen before container teardown; trajectory and `agent_absence.json` retain `AGENT_INFRA:<original exception type>` with `infrastructure: true`. There is no agent-failure repair record for this absence. A failed diff extraction leaves the task unfinished instead of inventing an empty patch. `completion.json` separates `agent_infrastructure_tasks` from `no_patch_tasks`, including infrastructure tasks whose diff really is empty. V4 exhaustion propagates out of generation before an incomplete suite can be screened and becomes `V4_INFRA:<type>` infrastructure absence.

**Retry/timeout comparability.** `uv.lock` pins mini-swe-agent 2.4.6 and LiteLLM 1.100.1. The main-study `scripts/run_pilot.py` and `MiniSweAgentBackend` use the native `LitellmModel.query` retry loop: 10 total attempts (9 retries), `reraise=True`, exponential waits with multiplier 1, minimum 4 seconds and maximum 60 seconds. The nine waits are 4, 4, 4, 8, 16, 32, 60, 60, 60 seconds; the existing `MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT` override remains supported. E2E repair and V4 inherit this exact loop. `configs/model/primary.yaml` declares `request_timeout_s: 600`; the main-study runner does not forward that limits field, and neither agent prompt config supplies a model request timeout. The pinned LiteLLM chat resolver independently defaults to 600 seconds, so the effective timeout is still 600 seconds. E2E preserves that default and the unchanged 120-second command / 1800-second repair-task ceilings. No timeout was increased. Details, including inner-client retry handling, are in [DECISIONS.md](DECISIONS.md).

**Empty-patch fix.** V1 and `FullPolicyV141` / `v1.4.1-full` are unchanged. Zero-byte or parsed empty patches (including nonzero whitespace-only files) receive V2/V3/V4 absences with `EMPTY_PATCH` and `infrastructure: false`; no G1/container or paid V4 runtime starts, and V4 is `NOT_RUN`. V1 still FAILs and the decision is REJECT. A nonempty patch with zero selected tests receives V2 `NOT_AVAILABLE` / `nothing_to_check`, detail `no tests selected`, without an infrastructure flag; V3 and V4 continue. No selected-test skips are upgraded to PASS, and the Matplotlib result above remains unchanged. Guards, selection, policy, and billed-usage cost calculation are unchanged.

**Validation.** The final full suite used the same copied `HF_HOME` and both offline flags as the preceding release: **1641 passed, 7 skipped, 6 failed, 17 errors in 69.54 seconds**. All 23 failed/error IDs and statuses match `/home/sankalp/projects/unit_baseline_7fefe1d/failing_ids.txt`: zero new failures/errors and no reference failures newly passing. The focused run passed **140 tests**. Logs and the ID comparison are in `runs/e2e_v1_4_2_checks/`. Mocked regressions exercise both providers and stages, success after a transient eleventh call through the real agent trajectory, ten exhausted attempts with the exact native wait schedule, retained conservative charges, auth/budget/client stops, frozen nonempty and genuinely empty working-tree diffs, failed diff extraction without an invented patch, V4 infrastructure attribution, empty-patch runtime suppression, and ten consecutive empty-patch tasks without a systemic stop. No real model calls or live container checks were launched for this release.

The focused provider/E2E/UM run passes **140/140** tests in 11.69 seconds (`pytest.focused.final.out`). The final full-suite log is `pytest.full.final.out`, and `unit_comparison.json` records the exact reference-ID comparison. All 135 files hashed in the pilot folder, pilot log and shared ledger retain their original bytes (`evidence_before.json`).

Fresh offline replay in `runs/e2e_v1_4_2_checks/offline` passes **A1 83/83 and A2 83/83**, with all four policies equal and zero health halts, after verifying the read-only seal's **1,799 files / 3,488,110,239 bytes**. The fresh A1/A2 outputs are byte-identical to the committed inputs used by the rerun A3: **14 ACCEPT / 67 FLAG / 2 REJECT**, zero differences and zero unattributed changes. `scripts/verify_e2e_v1_4_1.py` passes all registry, 75 frozen-artifact, A1/A2 and frozen A4 checks; registry and all recorded frozen check outputs remain unchanged. Logs are `offline.out`, `decisions.final.out` and `independent.out` under the same checks directory. Offline verifier import leaves LiteLLM uninitialized. All **135** pilot/log/ledger files retain their pre-change SHA-256 hashes. The original annotated tag object and c5b352c target are unchanged. No labels were read, no sealed Phase 4 file was written, and nothing was pushed.

The release diff from `e2e-v1.4.1-frozen` contains only these twelve files:

- `src/reliability/provider_errors.py`: shared retry classification and safe transient exception.
- `src/reliability/paid_models.py`: DeepSeek retry routing and retained-bound accounting attribution.
- `src/reliability/umgpt.py`: identical transient routing for UM.
- `src/reliability/e2e_models.py`: infrastructure diff capture and V4 propagation.
- `scripts/run_e2e.py`: preserve infrastructure receipts and captured patches.
- `src/reliability/e2e_runner.py`: separate repair-infrastructure/no-patch completion lists.
- `src/reliability/verifier/run_v1_4_1.py`: empty-patch/no-selection routing and V4 infrastructure attribution.
- `tests/unit/test_e2e_v1_4_2.py`: mocked provider/trajectory/exhaustion/batch regressions.
- `tests/unit/test_e2e_runtime.py`: task-spec empty patches, zero selection, V4 infrastructure regressions.
- `reports/next_phases/e2e_v1_4_1/REPORT.md`: pilot findings and release validation.
- `reports/next_phases/e2e_v1_4_1/DECISIONS.md`: retry/timeout evidence and implementation choices.
- `reports/next_phases/e2e_v1_4_1/RUNBOOK.md`: v1.4.2 tag, new output folders, and no old-pilot resume.

## v1.4.3: generic GIS_GUARD rule

The label-free v1.4.2 pilot completed 4/4 with zero problem calls. Its newly prepared Django-12663 patch selected 1,729 tests. Four GIS modules (99 selected tests) hit the SQLite GIS-backend guard on both trees. The existing 49 per-task/module exceptions include 47 GIS entries tied to modules selected by the frozen patches; a new patch can select a different GIS module and block G1 for the entire task. The supplied 36/32 module counts differ from the artifacts: both the pilot and fresh `selection.json` contain **33 distinct module paths: 4 GIS and 29 others**. Their bytes and ordered IDs are identical (SHA-256 `40a8c3938b4bd2e434701f852f1ba8c43feec7242830e404e096cc1432833112`). Three selected nested helpers in `tests/db_functions/datetime/test_extract_trunc.py` are natively proven invalid; 1,627 tests remain runnable after the 99 GIS-unavailable selections.

`configs/verifier/run_health_generic_exceptions.json` now contains exactly one rule, `django_sqlite_gis_guard`, SHA-256 **133b1718eeb53df319c53042a3a37ffd59f2f97b2955d9871e51543a79928f13**. It requires repo `django/django`, a normalized module path under `tests/gis_tests/`, stage `native_collection` or `module_execution`, and the literal message `A GIS database backend is required to run gis_tests` on both base and patched trees. Additional exceptions, changed guard text, other repositories, other paths and other stages are not excused. There is no generic xmlschema or matplotlib exception.

Per-task entry presence takes priority for the entire (task, module), including a per-task entry whose stage, tree or message does not match. Generic candidates use the existing unavailable-module accounting and stay provisional until paired evidence is checked. G1 cannot open on a single-tree candidate. V2 checks its own pair again and verifies confirmation exceptions against the opposite initial tree. Every application is recorded in `health.jsonl` with `exception_source: generic_rule`, `rule_id`, `rules_file_sha256` and `both_trees_confirmed: true`. The rules-file path and SHA-256 are stamped in the run header and health records. Selection, guard thresholds, accounting, test statuses and the decision rule remain unchanged.

The final full unit suite used the usual offline-cache command and passed **1,665 tests**, with **7 skipped, 6 failed and 17 errors in 73.56 seconds**. All 23 failed/error IDs and statuses exactly match `/home/sankalp/projects/unit_baseline_7fefe1d/failing_ids.txt`: zero new failed/error IDs and no reference failure newly passing. The 24 new tests include real local native collectors and V2 execution, both-tree GIS success, one-tree and different-message halts, non-Django rejection, per-task priority and identical unavailable accounting, mixed failures, path/stage scope, module-execution pairing, provenance, a failure that changes between G1 and V2, and strict source-amendment checks. Evidence: `runs/e2e_v1_4_3_checks/pytest.release.final.out` and `unit_comparison.json`; the earlier focused run passed 96 tests.

The first live attempt, `runs/e2e_v1_4_3_checks/live_django_12663`, is **sandbox-blocked, no collection**: both Docker starts were denied access to `/var/run/docker.sock`. Its folder is preserved unchanged. The second attempt, `live_django_12663_docker`, is **operator error: log path inside output**: the empty-output preflight stopped before creating a header or collecting, and its folder is also preserved. The user approved a corrected Docker-access retry in the previously absent `live_django_12663_final` path, with its log beside the output folder. Actual Docker inspection records network mode `none` in that output's `docker_network.json`.

The corrected retry uses `configs/e2e/gis_guard_check_1.txt`, both requested registries, the frozen v1.4.2 pilot patch, `--mode pilot --verify-only-from runs/e2e_v1_4_2_pilot_A --skip-v4`. It completed with **zero health halts**. G1 is **READY on both trees**, with paired generic applications for `tests/gis_tests/distapp/tests.py` (25), `tests/gis_tests/geoapp/test_functions.py` (37), `tests/gis_tests/geoapp/tests.py` (31), and `tests/gis_tests/test_gis_tests_utils.py` (6). V2 runs the other **29 modules** and reports **INCOMPLETE, n_executed = 1,627**, outcome NOT_AVAILABLE and decision FLAG. Base and patched counts are identical: 1,376 passed, 248 skipped, 2 xfail, 1 error, 99 environment-unavailable collection errors and 3 proven invalid IDs. Skips and unavailable evidence retain their existing semantics; no status is promoted to PASS. V4 is NOT_RUN with `SKIP_V4_FOR_CHECK`. The rules-file stamps, receipt hashes, module execution set and byte-identical selection were checked in `runs/e2e_v1_4_3_checks/live_summary.json`; the log is `live_django_12663_final.out`.

Fresh offline replay in `runs/e2e_v1_4_3_checks/offline` passes **A1 83/83 and A2 83/83**, with identical outcomes and signals in all four policies and zero health halts. It verifies the read-only seal's **1,799 files / 3,488,110,239 bytes**. **0/83 tasks would use the generic rule** after per-task priority. A3 consumes that fresh A2 output through the new `--offline`/`--output` options and returns **14 ACCEPT / 67 FLAG / 2 REJECT**, zero differences and zero unattributed changes. Evidence: `offline.out`, `offline/A2.json`, `decisions.out`, and `decisions/A3.json` under the same checks directory.

The independent checker's first attempt detected that the historical UM probe pins `collection.py` and `run_health.py`, both changed by this authorized implementation. The published `reports/umgpt_probe/frozen_files.json` is preserved. `configs/e2e/v1_4_3_source_amendments.json` registers exactly these two historical-to-release SHA-256 transitions, bound to base commit `8a0aea302cce60c4aee6791c668422346fb9382f`; its own SHA-256 is pinned in the independent checker. The original artifact preflight remains strict. The release checker separately verifies each historical hash against that manifest and each new hash against the current source, with distinct `APPROVED_RELEASE_SOURCE` records. Unknown mismatches remain fatal. Five additional tests cover exact transitions, unknown changes, historical/current/hash-manifest tampering and missing evidence.

`scripts/verify_e2e_v1_4_1.py` **passes**: registry identities, 73 unchanged historical artifact hashes, the 2 exact source amendments, A1/A2, sealed G1 authority and frozen three-runner A4. A4 reads the existing `runs/e2e_v1_4_1_checks/live_frozen` evidence; the new-patch GIS check is reported separately above. The fresh checker output and generated reports are retained as `independent.final.out`, `independent_A4.json` and `independent_A7.json` under `runs/e2e_v1_4_3_checks/`; the historical committed A4/A7 snapshots retain their bytes.

All **328** protected pilot/log/ledger files retain their pre-change SHA-256 hashes, and the existing `e2e-v1.4.1-frozen` and `e2e-v1.4.2-frozen` annotated tag objects are unchanged. Both unsuccessful setup-attempt folders remain untouched. `preservation.json` and `acceptance_summary.json` record the final checks. No paid model calls were made, no labels were decoded for acceptance, no sealed Phase 4 file was written, and nothing was pushed.

The release is committed and frozen by the local annotated tag **`e2e-v1.4.3-frozen`**. The changed files (`git diff --stat e2e-v1.4.2-frozen HEAD`) are:

```text
 configs/e2e/gis_guard_check_1.txt                  |   1 +
 configs/e2e/v1_4_3_source_amendments.json          |  18 ++
 .../verifier/run_health_generic_exceptions.json    |  14 ++
 reports/next_phases/e2e_v1_4_1/REPORT.md           |  44 ++++
 reports/next_phases/e2e_v1_4_1/RUNBOOK.md          |  33 ++-
 scripts/check_e2e_decisions.py                     |  11 +-
 scripts/check_e2e_offline.py                       |  29 ++-
 scripts/run_e2e.py                                 |   4 +-
 scripts/verify_e2e_v1_4_1.py                       |  43 +++-
 src/reliability/verifier/collection.py             |   8 +-
 src/reliability/verifier/generic_health.py         | 107 ++++++++
 src/reliability/verifier/guarded_v2.py             |  16 ++
 src/reliability/verifier/inline_g1.py              |  31 +++
 src/reliability/verifier/run_health.py             |  23 +-
 src/reliability/verifier/run_v1_4_1.py             |  13 +-
 tests/unit/test_e2e_v1_4_3.py                      | 277 +++++++++++++++++++++
 16 files changed, 644 insertions(+), 28 deletions(-)
```
