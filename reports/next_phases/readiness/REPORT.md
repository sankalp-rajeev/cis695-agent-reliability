# End-to-end readiness check (report-only)

Branch `analysis/e2e-readiness`, base `7fefe1d` (policy v1.4.0 frozen). Static code reading only: no code, config, policy or label changes, no model calls, no containers run. Nothing below was executed, so every claim is from reading the source.

## Verdict

**No, not as it stands.** `scripts/run_pilot.py` calls `verify_task` in `run.py`, which reaches the repaired test executor (native collection, parsers, SymPy adapter, INVALID_ID handling, runner start-up health). But `verify_task` builds its container without the pinned pristine source that this executor now requires, so V2 would raise `ValueError` on the first task. The guards G1-G6 enforcement and the Policy S accounting exist only in `scripts/phase4_launch.py`, and the v1.4 runner (`run_v1_4.verify_task`) is not wired into `run_pilot.py`.

## 1. Call path, run_pilot.py to V2 execution

Entry: `scripts/run_pilot.py:main` -> `_run_one` (per task), stages in order:

| # | Stage | Module / function |
|---|---|---|
| 1 | Agent | `reliability.agent.runner.run_task` (MiniSweAgentBackend); writes `repair_record.json`, frozen `patch.diff` |
| 2 | Verify entry | `run_pilot._run_one` -> `reliability.verifier.run.verify_task(task_dir, configs=("full","baseline"), use_container=True, reproduction=default_reproduction_setup())` (`run.py:84`) |
| 3 | Container | `container.TaskContainer(instance_id, patch_text, experiment_id)` with default `image_for()` tag, **no `source_spec`**; `ContainerRepoTree`, `ContainerCommandExecutor`, `ContainerTestExecutor(evidence_dir=task_dir/"v2_evidence")` |
| 4 | Layers | `run.run_layers` (`run.py:177`) |
| 4a | V1 | `integrity.check_integrity` (v1.3 version) |
| 4b | Selection | `selection.select_tests`; sets `test_executor.runner` |
| 4c | V2 | `regression.run_regression(RegressionConfig(baseline_cache_dir=runs/_baseline_cache))` -> `ContainerTestExecutor.run` (base, then patched, then 3+3 confirmations per suspect) |
| 4d | V2 inside the executor | `_run_audited`: `set_patched` -> `collection.validate_in_container` (native collection, id_validation, sympy_adapter program) -> `run_health.runner_startup` -> in-container `_BATCH_DRIVER` -> `run_from_capture` (`result_parser`) -> `validated_run.apply_validation` -> `run_health.module_execution_stages` -> stage_health |
| 4e | V2 signal | `run.signal_from_regression` |
| 4f | V3 | `static_checks.run_static_checks` (v1.3 version) |
| 5 | V4 | `run.run_reproduction` -> `reproduction_freeze` / `reproduction.py` (own base/patched containers, generator cap 40 steps from `configs/verifier/full.yaml`) |
| 6 | Decision | `run._evidence_from` -> `decision.get_policy("full"/"baseline").decide`; writes `verification_record.full.json` and `.baseline.json` |
| 7 | Oracle | `oracle.runner.run_oracle` (outside scope) |

Blocking defect at step 3/4c: `ContainerTestExecutor.run` (`container.py:467`) raises `ValueError("Fix 9 requires a pinned BaseSourceSpec")` when `container.source_spec is None`, and again unless `source_integrity.status == 'VERIFIED'`. `verify_task` only catches `ContainerError`, so the `ValueError` escapes; `run_pilot` would log `verifier_error` for every task. (Static reading; not run.)

## 2. Repaired components: reached by the end-to-end path?

| Component | Reached by e2e? | Chain / where it lives |
|---|---|---|
| Native collection | YES, but blocked by the source_spec check | `ContainerTestExecutor._run_audited` -> `collection.validate_in_container` |
| Result parsers (Django, Astropy fixes) | YES (same blocker) | `run_from_capture` -> `result_parser.mapping_for`, `module_identity_failures`, `active_test` |
| Parametrized ID handling | YES (same blocker) | `collection.py` / `id_validation.py` / `node_ids.normalize_pytest_id` / `validated_run.apply_validation` |
| SymPy `bin/test` adapter | YES (same blocker) | `collection.py` imports `sympy_adapter._SYMPY_PROGRAM`; `run_health.runner_startup` has the sympy branch |
| INVALID_ID handling | YES (same blocker) | `regression.py` status/outcome, `completeness_of(... invalid_as_missing)`; default `False` means INVALID_ID is excluded |
| Policy S accounting | NO as the default. Reachable only by replay | `run_regression` default is `skip_compatible=True` (Policy C). Policy S (`skip_compatible=False`) and `h1_accounting` are used only by `phase4_launch.run_task` (4 replay reports) and `scripts/phase3_accounting_replay.py` |
| Guards G1 | ONLY VIA `phase4_launch.py` | `g1_reference`, `with_g1_references`, `require_g1`, `Calls.run` |
| Guards G2, G3, environment drift | ONLY VIA `phase4_launch.py` | `run_health.health_for_run` is called only from `phase4_launch.run_task`/`Calls.run` and `g1_reference.py` |
| Guards G4-G6 | ONLY VIA `phase4_launch.py` | `run_health.explicit_executor_failures` / `RunHealthError` / `append_health` raised and handled only in `phase4_launch.py` (`phase6b_run.py` uses `explicit_executor_failures` too) |
| Partial health inside the executor | YES | `run_health.runner_startup` and `module_execution_stages` run in `ContainerTestExecutor`, but they only record stage health; nothing halts on it in `run.py` |
| Integrity preflight | ONLY VIA `phase4_launch.py` | `source_integrity.verify_base_source` runs only if `TaskContainer.source_spec` is set (`FrozenContainer` path); `scripts/phase4_integrity_preflight.py` is a separate script |
| Frozen run-health exceptions | N/A to new tasks | `run_health_exceptions.json` has 49 entries keyed to the frozen task ids |

## 3. What in phase4_launch.py is specific to the 83 frozen patches

| Item | Location | Needs generalizing for e2e? |
|---|---|---|
| `TASK_COUNT = 83`, cohort check | `phase4_launch.py:49`, `validate_inputs` | Yes (drop the count check; take the task list from the run manifest) |
| `FROZEN_TASKS_SHA256`, `FROZEN_PROTOCOL_SHA256`, `frozen/tasks.json`, `protocol.json`, per-task selection/patch hashes | `:46-47`, `validate_inputs` | Yes (patches are produced at run time; hash the produced patch instead) |
| Absolute paths `/home/sankalp/...paired_frozen` and `/home/sankalp/cg_repos/task_archives` | `:44`, `main` | Yes (per-task base-source archives must exist for new tasks) |
| Dataset projection with 83 rows (4 columns) and wheel/provenance pins | `PROVENANCE`, `load_specs` | Yes (needs rows for new instance ids) |
| Pristine-source archives + `archive_sha256`, `PREFLIGHT` receipts | `validate_inputs`, `PREFLIGHT` | Yes (build and hash per new task, then run the integrity preflight) |
| Image id pins (`sha256:` 71-char) with `--pull=never` (`FrozenContainer`) | `validate_inputs`, `FrozenContainer` | Yes, or keep tag-based images and accept weaker provenance |
| Admission reference `fix13_reference` and drift reference `fix16_reference` | `load_reference` | Yes (new tasks have no reference; G2 must fall back to the G1 native-collection reference) |
| G1 manifest (`fix18b_g1`) and committed manifest SHA read from plan text | `require_g1`, `committed_g1_manifest_sha`, `with_g1_references` | Yes (the G1 collection must be generated per new task before or during the run; the pin cannot be a committed constant) |
| `run_health_exceptions.json` (49 entries by task id) | `run_health.exception_rules` | No code change needed: new tasks simply have no exceptions, which is the strict default |
| Freeze-tag / clean-HEAD requirement, 12 h stop, no-resume, `runs/` output rule | `require_frozen_head`, `STOP_S`, `execute` | Decide: keep tag requirement for audited runs; drop it for pilots |
| `covering_order` first-of-each-(runner,repo,version) ordering | `run_health.covering_order` | Optional |
| Experiment id `phase4_v2_<name>`, serial execution | `execute` | Minor |

## 4. V1/V3/V4 call sites and the policy version stamped

| Signal | Call site in the existing path | Version stamped on the decision |
|---|---|---|
| V1 integrity | `run.run_layers` -> `integrity.check_integrity` | `decision.policy_version = v1.3.0-full` (config `full`) and `v1.2.2-baseline` (config `baseline`) |
| V2 regression | `run.run_layers` -> `run_regression` | same |
| V3 static | `run.run_layers` -> `static_checks.run_static_checks` | same |
| V4 reproduction | `run.run_reproduction` (generator cap 40 steps, `full.yaml`) | same |
| Run header | `run_pilot.py:267` | `verifier_policy_version = "v1.3.0-full+v1.2.2-baseline"` |

Only the decision records a policy version; the per-signal records carry no separate version. The v1.4 path (`run_v1_4.verify_task`) stamps `v1.4.0-full` and writes `verification_record.full-v1.4.json`, using `integrity_v1_4` (AST analysis), `static_v1_4`, `reproduction_v1_4` (telemetry, 80-step cap from `full_v1_4.yaml`), and `policy_v1_4.FullPolicyV14` (v3 absolute failure and v1 incomplete analysis become FLAG reasons). It reuses the same `ContainerTestExecutor` and `run_regression`, so it has the same source_spec blocker and the same lack of guards.

## 5. Where V2 outcomes are written, and Policy S accounting

- Per task, in `verification_record.<config>.json`: `regression.findings` holds `outcomes` (per selected id, including `INVALID_ID`), `summary`, `completeness`, `incompleteness`, `base` and `patched` (`run_to_dict`, raw bytes not inline), `confirmations`, and `confirmation_summary`. The record also stores `selected_tests`.
- Raw evidence goes to `task_dir/v2_evidence/` (stdout, stderr, runner log, events, `validation.json`, `generated_inputs.json` per pass, with SHA-256 in the run).
- Health stage records live inside each run (`stage_health`), but no `health.jsonl` is written outside `phase4_launch`.
- Can Policy S primary accounting (INVALID_ID excluded) be computed from this? **Mostly yes, offline.** Slots are `selected_tests`; admitted slots and `INVALID_ID` come from the `base`/`patched` results in the record, so `accounting.h1_accounting` can be applied after the fact. But the signal and decision recorded in the record are Policy C (`skip_compatible=True`), not Policy S, and only one policy is scored. Policy S would need a replay over the saved runs (as `phase4_launch.Replay` does) or a config change. Also, `baseline_cache_dir` is set, so on a cache hit the base pass is not rerun and has no fresh capture for the base-side guards.

## 6. Wiring needed for v1.4 with repaired V2 and Policy S

| Step | File(s) to change |
|---|---|
| 1. Call the v1.4 verifier instead of v1.3 | `scripts/run_pilot.py` (import and call `reliability.verifier.run_v1_4.verify_task`; `configs=("full-v1.4",)`; use `run_v1_4.default_reproduction_setup()`; the v1.4 entry rejects a non-v1.4 setup) |
| 2. Fix record names and policy stamps | `scripts/run_pilot.py` (`verification_record.full.json` -> `.full-v1.4.json`, drop the baseline config, header `verifier_policy_version=v1.4.0-full`, `_summarise` / `_tasks_still_spending`), `src/reliability/run_plan.py` (`pending_stages` checks `verification_record.full.json`), `reliability.verifier.record.load_records(config=...)` callers |
| 3. Give the container a pinned pristine source | `src/reliability/verifier/run_v1_4.py` (`verify_task` builds `TaskContainer` without `source_spec`; construct a `BaseSourceSpec`, a receipt path, and a pinned image as `phase4_launch.FrozenContainer` does), plus a per-task spec builder (new, e.g. `src/reliability/verifier/task_spec.py`) |
| 4. Provide per-task source inputs | New archive build + hash step and dataset-projection rows for the new tasks; extends `pre_install.load_specs` inputs |
| 5. Switch V2 to Policy S with INVALID_ID excluded | `src/reliability/verifier/run_v1_4.py` (`RegressionConfig(skip_compatible=False, invalid_as_missing=False, baseline_cache_dir=None)`), and record `h1_accounting` output in the record or a sidecar |
| 6. Enforce G1-G6 per task | Move `Calls`, `confirmation_reference`, `health_for_run` use, `RunHealthError` handling out of `scripts/phase4_launch.py` into the package, wrap the executor in `run_v1_4.verify_task`; write `health.jsonl` |
| 7. Make the G1 native reference available | Collection-only pass per new task before the run (`g1_reference.py` builder), and the pinned-manifest logic in `phase4_launch.require_g1` generalized |
| 8. Decide the halt behavior | A halted task must surface as an attributed absence on the V2 signal (not abort the batch) in `run_v1_4.verify_task`; today `phase4_launch.execute` aborts the whole attempt |
| 9. V4 80-step cap and telemetry | Already in `run_v1_4` via `reproduction_v1_4` and `full_v1_4.yaml`: no further change once step 1 is done |
| 10. Header and provenance fields | `scripts/run_pilot.py` experiment record: add v1.4 config hash and the G1 manifest hash |

## Gaps, ordered by effort (smallest first)

1. **Record naming and header stamping** (`run_pilot.py`, `run_plan.py`): small; mechanical.
2. **Policy S switch and INVALID_ID-excluded accounting stored in the record** (`run_v1_4.py`): small.
3. **Call `run_v1_4.verify_task` from `run_pilot.py`** (steps 1-2): small once the blocker below is fixed.
4. **Package the guards G1-G6** out of `phase4_launch.py` and wrap the executor: medium.
5. **Attributed-absence handling for a halted task** instead of aborting the batch: medium; a policy decision as well as code.
6. **Source-integrity blocker**: build a `BaseSourceSpec` and pinned image in `verify_task`: medium; this is what stops the path from running at all.
7. **Per-task G1 collection reference generation and non-constant manifest pin**: medium to large.
8. **Per-task base-source archives, dataset-projection rows and pre_install provenance for new instances**: large, mostly infrastructure and data work, and it needs the swebench wheel pin to cover the new instances.
