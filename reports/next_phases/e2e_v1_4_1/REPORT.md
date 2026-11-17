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
