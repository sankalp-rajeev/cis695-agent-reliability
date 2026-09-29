# CIS 695 — Development Checklist

**Project:** Trust but Verify — Execution-Grounded Verification of LLM-Generated Software Repairs
**Repo:** `cis695-agent-reliability`
**Scope of this checklist:** Stage 0 → Stage 1 (feasibility + 10-task pilot), per the plan sent to Dr. Hassan.

## Rules

1. **One task at a time.** Do not start a task until the previous task's gate has passed.
2. **Every task has a GATE** — a command that exits 0, or a stated artifact that exists and has been inspected. No gate, no checkmark.
3. **Gates are run, not assumed.** Paste the actual output when checking a box.
4. If a gate fails twice for the same reason, stop and record it under *Blockers* rather than working around it silently.

Legend: `[ ]` not started · `[~]` in progress · `[x]` gate passed · `[!]` blocked

---

## Phase 0 — Repo scaffold and environment

- [x] **0.1 Initialize repository**
  - [x] `uv init`, `pyproject.toml`, Python version pinned — Python 3.11 pinned via `.python-version`; `uv.lock` committed; `swebench` and `mini-swe-agent` held at exact `==` versions as experimental apparatus
  - [x] Directory skeleton per technical design — **done** 2026-09-15, per §19 of the technical design. `src/reliability/{benchmark,agent,verifier,analysis,reporting}` each created with an `__init__.py` stating that layer's isolation rule; `configs/{agent,model,verifier,experiments}`, `manifests/`, `reports/{figures,tables,cases}`, `tests/{unit,integration,golden}`. Individual modules (`loader.py`, `integrity.py`, …) are deliberately **not** stubbed — each has its own phase and gate, and an empty file that imports cleanly would let a gate pass against nothing
  - [x] `.gitignore` excludes `runs/`, `*.jsonl`, `.env`, Docker volumes — **completed** 2026-09-15. Added `*.jsonl` (ignored by extension as well as location, since a stray predictions file can carry gold patches), `.docker/`, `docker-volumes/`, and `*.patch`/`*.diff` at the repo root
  - [x] `README.md` stub with the research question and the three-layer separation principle
  - **GATE PASSED** 2026-09-15 — `uv run --frozen python -c "import reliability; print(reliability.__version__)"` → `0.1.0`, exit 0, and the skeleton now matches the technical design

- [x] **0.2 Secrets and config hygiene**
  - [x] `.env.example` committed; real `.env` git-ignored
  - [x] API key loaded from env only — never hardcoded, never logged. Configs name the *variable* (`api_key_env`), never the value
  - [x] `configs/` has one YAML per layer — `configs/agent/mini_swe_agent.yaml`, `configs/model/primary.yaml`, `configs/verifier/{full,baseline}.yaml`, `configs/experiments/pilot.yaml`
  - ⚠️ **`configs/model/primary.yaml` deliberately leaves `provider`, `model_id`, and `api_key_env` null.** The technical design selects the model after the pilot. A plausible-looking pinned id here would be a fabricated value that could survive into the writeup unnoticed. **Must be filled before Phase 3**, which is the first API spend
  - **GATE PASSED** 2026-09-15 — `scripts/audit_secrets.sh` → `PASS: no credentials in history, working tree, or index`, exit 0
  - **Deviation from the stated gate.** The checklist specifies `git log -p | grep -iE "sk-ant|sk-proj"`, which can never pass: this file contains those literals in the line documenting the gate, so the grep matches its own definition. Matching bare prefixes is also the wrong test — what is dangerous is a prefix *followed by key material*. `scripts/audit_secrets.sh` requires the trailing secret, scans full history (a key committed and later removed is still published), the working tree, and the index

- [x] **0.3 Run-metadata recorder**
  - [x] `src/reliability/provenance.py` writes the reproducibility block — task manifest hash, git commit, git dirty flag, agent scaffold + version, exact model id, temperature, step/token limits, timeout, verifier policy version, docker image, `swebench` version, timestamp
  - [x] Every run directory gets one `meta.yaml`. `write_meta` refuses to overwrite an existing block unless asked explicitly, so a rerun cannot masquerade as the original
  - [x] Validation rejects missing, null, blank, and *unexpected* keys. Falsey-but-real values (`git_dirty: False`, `temperature: 0.0`) are accepted — emptiness is checked per type, not by truthiness
  - [x] **Interpreter import state recorded** — `pythonpath`, `sys_path`, `foreign_sys_path_entries`, `python_version`, `python_executable`, captured by `RunProvenance.capture()` from the live process rather than passed in by a caller that never looked. See the ROS hazard in the Decisions log
  - **GATE PASSED** 2026-09-15 — `bash scripts/test.sh` → `60 passed`, exit 0 (37 provenance + 23 interpreter-environment)

---

## Phase 1 — SWE-bench harness feasibility

> This is the phase that decides whether the semester plan is viable. Do it before anything else that costs API money.

- [x] **1.1 Docker + harness install**
  - [x] Docker daemon running, non-root access confirmed — Docker Desktop 28.5.1 with WSL2 integration; `docker` runs as user `rajee` with no `sudo`. Daemon reports `OSType=linux`, `x86_64`, 32 CPU. **RAM 10.42 GB as of 2026-09-15** (was 16.6 GB), following the WSL2 memory cap — see Decisions log
  - [~] SWE-bench installed at a pinned commit (record the SHA) — **deviation, see Decisions log.** Installed from PyPI as `swebench==5.0.2`, not a git checkout, so no commit SHA exists. Provenance is the locked PyPI artifact recorded in `uv.lock`
  - [x] Free disk measured and recorded — **947 GB free** of 1007 GB on `/dev/sdd` (WSL2 ext4), 1 % used, measured 2026-09-14. ⚠️ Note: this is *not* where Docker images land — see Blockers/notes on the separate Docker VHDX
  - **GATE PASSED** 2026-09-14 — `docker run --rm hello-world` → exit 0 (as non-root); `python -m swebench.harness.run_evaluation --help` → exit 0

- [x] **1.2 Gold-patch sanity run**
  - [x] Run the official evaluation on **3 instances using their gold patches** as predictions — gold patches taken from the Verified dataset's own `patch` field (`scripts/image_for.py`, `scripts/harness_sanity.sh`); predictions at `runs/1.2_gold_sanity/predictions_gold.jsonl`
  - [x] Confirm the harness reports `resolved` for all 3
  - [x] Record: wall-clock per instance, peak disk, image build time

  | instance | pull s | eval s | total s | cumulative image store |
  |---|---:|---:|---:|---:|
  | `django__django-12304` | 51 | 31 | 82 | 7.93 GB |
  | `sympy__sympy-15599` | 31 | 38 | 69 | 9.71 GB |
  | `matplotlib__matplotlib-25287` | 129 | 122 | 251 | 18.32 GB |
  | **total** | **211** | **191** | **402** (6 m 42 s) | **+14.6 GB** |

  - **Image acquisition is a pull, not a build.** Verified instances ship prebuilt images (`swebench/sweb.eval.x86_64.<repo>-<id>:latest`), so there is no local Docker build step. Pull was ~53 % of wall-clock and is one-time per instance.
  - **Disk grew 3.74 GB → 18.32 GB, i.e. ~4.9 GB per instance.** The harness leaves images behind (`unremoved_images`), which is what makes re-runs cheap.
  - ⚠️ **Images do not consume the 947 GB ext4 disk.** Docker's root is `/var/lib/docker` inside the Docker Desktop VM, backed by a VHDX on the Windows drive. Disk headroom for images must be tracked on Windows, not via `df -h ~`.
  - **GATE PASSED** 2026-09-14 — `python scripts/score_reports.py runs/1.2_gold_sanity 3` → `evaluated=3 resolved=3 infra_failures=0`, exit 0. Environment is sound: gold patches genuinely resolve.

- [x] **1.3 Empty-patch negative control**
  - [x] Run the same 3 instances with empty predictions — `runs/1.3_empty_control/predictions_empty.jsonl`, `model_patch: ""`
  - [x] Confirm the harness reports `unresolved` for all 3 — 0/3 resolved, 0 infra failures. Wall-clock collapsed to 9 s per instance (vs 69–251 s in 1.2) because images were already local
  - **GATE PASSED** 2026-09-14 — `python scripts/score_reports.py runs/1.3_empty_control 0` → `evaluated=3 resolved=0 infra_failures=0 empty_patches=3`, exit 0

  ⚠️ **Caveat on what this control actually proves.** The harness *short-circuits* empty patches: all 3 were classified `empty_patch_ids` with `completed_instances: 0`, meaning the test suites were **never executed**. So this gate proves the harness will not pass a no-op submission, but it does **not** prove the `FAIL_TO_PASS` tests discriminate a wrong patch from a right one — the stated intent of the gate. The discrimination claim currently rests only on 1.2 (gold resolves) plus this (empty is refused before testing).

- [x] **1.3b Non-empty wrong-patch control**
  - [x] Submit a patch that applies cleanly but does not fix the bug, forcing the harness to actually run the suites — `runs/1.3b_wrong_patch/predictions_wrong.jsonl`, built by `scripts/make_wrong_patch.sh`
  - [x] 3/3 `unresolved`, 0 infra failures, `empty_patch_instances: 0` and `completed_instances: 1` per instance (versus 3 and 0 in 1.3), so the suites genuinely executed

  | instance | applied | FAIL_TO_PASS | PASS_TO_PASS | eval s |
  |---|---|---|---|---:|
  | `django__django-12304` | yes | 0 pass / 1 fail | 17 pass / 0 fail | 31 |
  | `sympy__sympy-15599` | yes | 0 pass / 1 fail | 80 pass / 0 fail | 36 |
  | `matplotlib__matplotlib-25287` | yes | 0 pass / 2 fail | 786 pass / 0 fail | 122 |

  - **GATE PASSED** 2026-09-15 — `python scripts/score_reports.py runs/1.3b_wrong_patch 0` → `evaluated=3 resolved=0 infra_failures=0 empty_patches=0`, exit 0. 883 `PASS_TO_PASS` tests passed, so the `FAIL_TO_PASS` failures are the discriminating tests working, not a broken environment. Evaluation times matched 1.2 almost exactly (31/36/122 vs 31/38/122), confirming evaluation cost is a property of the instance, not the patch.

  ⚠️ **Be precise about what this proved.** The patch is an appended comment, so the code is semantically identical to the unfixed base. 1.3b shows the harness executes the suites and that `FAIL_TO_PASS` fails on **unfixed code** — exactly the blind spot 1.3 left, which is why the gate passes. It is **not** a test against a *plausible but wrong* repair; no such patch has been evaluated yet. That case gets exercised for free in Phase 3 once the agent produces patches, and it is the scientifically interesting one, since the failure mode this project studies is a patch that looks right and is not. If it is ever wanted earlier, the construction is a **gold patch with one condition inverted**, not an inert edit.

  🔴 **Constraint discovered here — patches cannot be transplanted between instances.** The first attempt borrowed gold patches from other django instances. `django-13212`, `django-11815`, and `django-11999` **all failed `git apply --check`** at `django-12304`'s base commit, tested inside that instance's own image. Base commits within one repository drift too far apart. This rules out any later design that reuses one instance's patch against another — cross-instance transfer, "apply the neighbouring fix" baselines, or mutation controls built by borrowing. A non-applying patch is also the worst possible control: the tests never run, silently reproducing 1.3's blind spot.

- [x] **1.4 Feasibility numbers written down**
  - [x] `reports/feasibility.md` with: minutes/instance, GB/instance, failure rate, estimated cost for 10 and for 75 tasks
  - **GATE PASSED** 2026-09-15 — `reports/feasibility.md` exists and states the 75-task extrapolation in hours (oracle + acquisition **1.8–2.3 h measured**; end-to-end bounded **≤ ~59 h** by configured timeouts) and dollars (**≤ $50** at 10 tasks, **≤ $375** at 75, from the `max_cost_usd_per_task: 5.00` ceiling).

  ✅ **The 1.2 disk constraint is resolved, and the model behind it was wrong.** `C:` free space went from 58.9 GB to **308 GB**, so the pilot is unblocked outright. Separately, the flat "~4.9 GB per instance" figure — and the 368 GB extrapolation built on it — was wrong in mechanism: it ignored layer sharing entirely.

  **The sharing unit is the image build cohort, not the repository.** Measured across nine images (`runs/1.4_disk_model`, `scripts/layer_overlap.py`):

  | case | marginal cost |
  |---|---:|
  | Shares base **and** repo env layer (same repo, same build batch) | **~0.25 GB** |
  | Shares only the generic 1.516 GB base | **~2 GB** |
  | Shares nothing meaningful (new build batch) | **~4 GB** |
  | Unusually large image (e.g. matplotlib, 10.8 GB) | **up to 8.6 GB** |

  `django-12304` and `django-13212` are both django but from different build batches and share **only the generic base** — no django-specific layer. `django-11815/11848/11999` share 2.876 GB with `django-12125` and cost 0.25 GB each. The dataset's `environment_setup_commit` does **not** predict sharing.

  **No single 75-task number is given, deliberately.** The total depends on which batches the sample lands in, which is unknowable until the manifest exists — and Phase 2.3's stratified sampling actively erodes sharing. Realistic range is **~120–200 GB**, worst case ~307 GB, best ~60–80 GB; a 10-task pilot is comfortable (~10–45 GB) under every scenario. **Action for 2.3:** compute the exact figure by grouping `manifests/pilot.csv` by image batch, not by multiplying an average.

  **Retention is the default.** Pruning is a manual fallback for disk pressure only and is deliberately *not* in the pipeline — resident images are what made 1.3b re-evaluate three instances in 200 s. Re-pull costs ~48 s/instance if ever needed.

  ⚠️ Docker's per-image `SharedSize`/`UniqueSize` is unreliable here — summing per-image `UniqueSize` exceeded the reported store total, implying a negative shared remainder. Use the deduplicated store delta across a pull as ground truth.

---

## Phase 2 — Pilot task manifest

- [x] **2.1 Load SWE-bench Verified**
  - [x] `src/reliability/benchmark/loader.py` loads the 500-instance split. `load_verified()` raises `DatasetIntegrityError` unless the population is exactly 500 with all required columns — a different count means the wrong dataset or revision, which would silently change the population every downstream number is computed over
  - **GATE PASSED** 2026-09-15 — `bash scripts/test.sh tests/unit/test_loader.py` → 10 passed, exit 0. Asserts exactly 500 instances, unique ids, required agent and oracle columns present, every instance yielding a populated task with a 40-char base commit, and ≥3 distinct repositories (which Phase 2.3's stratification needs)

- [x] **2.2 Oracle-field quarantine (critical)**
  - [x] `load_instance()` returns two separate objects — `AgentTask` (instance_id, repo, base_commit, problem_statement) and `OracleRecord`. Both are returned so a caller must choose a half explicitly; there is no combined object that could be passed along by mistake
  - [x] `AgentTask` is a **frozen, slotted** dataclass. Slots mean no `__dict__`, so the raw dataset row cannot be stashed on an instance even privately. Verified directly: `setattr(task, "_row", …)` raises `TypeError`, field mutation raises `FrozenInstanceError`
  - [x] Built by explicit field reads rather than `**row`, so a new upstream column is ignored by default instead of silently becoming agent-visible (`test_unexpected_columns_do_not_reach_the_agent`)
  - **GATE PASSED** 2026-09-15 — `bash scripts/test.sh tests/unit/test_no_leakage.py` → 7 passed, exit 0. Written and shown failing (`ModuleNotFoundError: reliability.benchmark.loader`) before the loader existed

  **Two extra columns are withheld beyond the four the gate names.** `eval_script` carries the harness's own evaluation commands, and `hints_text` is free-text discussion from the originating pull request that frequently contains the fix or a direct description of it. `hints_text` is not ground truth, which is exactly why it is the easiest leak to overlook; it is withheld with the oracle fields. `environment_setup_commit`, `image`, and `log_parser` are execution metadata the harness needs and the agent does not, so they stay oracle-side too.

  ⚠️ **The gate as stated has a false-positive trap.** Asserting the bare string `patch` is absent from the payload fails on honest input — a real issue text may legitimately say "the attached patch fixes…". The test therefore checks *field names* against a controlled synthetic task, and checks real instances against the actual oracle **values** (the gold patch text, and every `FAIL_TO_PASS`/`PASS_TO_PASS` test name), which is what would do harm if an agent saw it. Sampled across the dataset, not just one instance.

- [x] **2.3 Stratified sample of 10**
  - [x] Sampler draws across repositories and task types — `src/reliability/benchmark/sampler.py`. Task types filled round-robin so no category is crowded out by django's 46 % share; within a type, repositories are visited round-robin before any is reused
  - [x] Seeded and deterministic — seed 695. Every collection is sorted before use and the only randomness is a seeded `random.Random`, so set/dict iteration order never reaches an ordering decision
  - [x] **No selection based on known model performance.** Stronger property: selection uses *only agent-visible fields*. Task type is derived from `repo` and `problem_statement`, never from the gold patch's touched paths — the obvious classifier, but one that would make the sample a function of oracle data. `sampler.py` does not import `OracleRecord`
  - [x] Written to `manifests/pilot.csv` with a content hash, plus sidecar `manifests/pilot.csv.sha256`

  | instance | repo | task type |
  |---|---|---|
  | `astropy__astropy-12907` | astropy/astropy | numerical |
  | `django__django-14373` | django/django | ORM/DB |
  | `django__django-14725` | django/django | ORM/DB |
  | `django__django-16899` | django/django | framework/API |
  | `matplotlib__matplotlib-26113` | matplotlib/matplotlib | state/behavior |
  | `mwaskom__seaborn-3187` | mwaskom/seaborn | state/behavior |
  | `psf__requests-1921` | psf/requests | framework/API |
  | `pylint-dev__pylint-6386` | pylint-dev/pylint | system/runtime |
  | `scikit-learn__scikit-learn-12973` | scikit-learn/scikit-learn | numerical |
  | `sphinx-doc__sphinx-10449` | sphinx-doc/sphinx | system/runtime |

  - **GATE PASSED** 2026-09-15 — rerunning `scripts/build_manifest.py` reproduces `sha256:f03000ed3228b9ffff62a91ba29e84e70a42892f3f8bb4ffa0150465b0494873`; verified identical across five fresh processes. Manifest spans **8 distinct repositories** (requirement ≥3) and all **5 task types, exactly 2 each**. `bash scripts/test.sh tests/unit/test_sampler.py` → 17 passed, including determinism under reversed input order.

  **Exact disk cost for this manifest: ~31 GB** (`scripts/manifest_disk_cost.py`, output in `runs/2.3_manifest_disk/`). Computed by resolving every image's real layer list from the registry via `docker manifest inspect` — **no pull** — and taking the union of distinct layer digests: 8.590 GB compressed against a naive per-image sum of 13.902 GB, so sharing saves 38 %. Applying the 3.615× compressed→on-disk ratio calibrated from the nine local images (6.984 GB compressed → 25.25 GB measured) gives ~31 GB, under 11 % of the 308 GB free.

  The ten instances span 8 repositories but only **2 build cohorts** (nine share seven base layers; `astropy-12907` shares two), which independently confirms the 1.4 finding that cohort membership is unrelated to repository.

  ⚠️ One transient failure worth noting: the first run of `test_sampler.py` errored in every dataset-backed fixture with `TypeError` inside `re/_parser.py`, from a first-call path in `datasets`. It has not recurred across eight subsequent runs, and hash stability was confirmed across five fresh interpreter processes. Recorded rather than dismissed, since this phase's whole claim is determinism.

  ✅ **Not a live risk.** The manifest is now a frozen artifact: downstream code reads `manifests/pilot.csv` and never re-runs the sampler, so a sampling fault cannot affect a run. The worst it could do is produce a *different* manifest, which the committed content hash would expose immediately. `sampler.py` is provenance — the record of how the manifest was derived — not a runtime dependency.

---

## Phase 3 — Repair agent runner

> **Design constraints applying to everything in this phase and downstream.** Both are cheap now and expensive to retrofit.
> - **Count-agnostic.** Nothing downstream of the manifest may hardcode `10` or `pilot.csv`. `run_manifest()` takes a `Manifest` and iterates whatever it holds; there is no default manifest path in `runner.py` or `manifest.py`. Gated by `test_runner.py::test_runs_whatever_size_manifest_it_is_given` (parametrised 1/2/3) and `test_manifest.py::test_loads_a_manifest_of_any_size` (parametrised 1/10/75/500). The 75-task main study runs this code unchanged.
> - **Parallel-safe.** Each task owns `tasks/<instance_id>/` and writes only inside it. No shared mutable file exists — no appended log, no aggregate JSON rewritten per task — so concurrent tasks never contend. `max_workers` defaults to 1 for the serial pilot; raising it requires no other change. Gated by `test_concurrent_execution_produces_the_same_records` (serial vs. 3 workers, identical records and patch hashes) and `test_each_task_writes_only_inside_its_own_directory`.

- [x] **3.1 mini-SWE-agent integration** — **GATE PASSED on a smoke model**, 2026-09-15. Ran end to end on `psf__requests-1921` and produced a non-empty patch that the harness accepted and resolved. See `reports/smoke_3.1.md`. ⚠️ The **study** model is still undecided; `configs/model/primary.yaml` stays null pending advisor approval, and the smoke run is `run_role: smoke` so none of its numbers are citable.
  - [x] Runner wired — `src/reliability/agent/runner.py`. `AgentBackend` is a protocol, so orchestration (freeze → parse → record) is gated against recorded fixtures rather than a live API call. `MiniSweAgentBackend` is wired and pinned at scaffold version 2.4.6
  - [x] Refuses to run without an explicit model — constructing `MiniSweAgentBackend(model_id=None)` raises `AgentConfigurationError`. `configs/model/primary.yaml` deliberately holds `provider: null`, `model_id: null`, and a silent fallback would put an unrecorded model into the provenance block
  - [x] Run directory layout and resume — per-task dirs hold `patch.diff`, `trajectory.jsonl`, `agent_output.txt`, `repair_record.json`; the run root holds only `manifest.csv` + `manifest.sha256`. Tasks with an existing record are skipped, so an interrupted run resumes without overwriting evidence (`test_interrupted_run_resumes_without_redoing_work`)
  - [x] Installed at a pinned version (2.4.6), runs one instance end-to-end in Docker and emits a patch — 608-byte fix to `requests/models.py`, 10 model calls / 37 shell commands, terminated `completed`
  - [x] Backend implemented — `MiniSweAgentBackend.run()` builds the Docker environment through `get_sb_environment`, which derives the image name from `instance_id` alone, so **no oracle field is read to run the agent**. Claim and patch are split out of one submission on `<<<END_CLAIM>>>`
  - [x] **Platform support verified against the installed packages, not from memory** — litellm 1.100.1 routes `gemini/<model>` to provider `gemini` reading `GEMINI_API_KEY`; mini-swe-agent's `get_model_class()` falls through to `LitellmModel`, which sends `tools=[BASH_TOOL]` on every call, so function calling is mandatory. ⚠️ The Gemini 2.0/2.5 families now 404 on this key **including `gemini-2.5-flash`, which still appears in `ListModels`** — litellm's static cost map is not evidence a model still serves
  - **GATE PASSED:** a non-empty patch exists for a pilot instance and the harness applied and evaluated it (`resolved: true`). `pytest tests/unit/test_runner.py` (25 passed) gates the orchestration around it

- [x] **3.2 Structured final claim** — **GATE PASSED**, `pytest tests/unit/test_claim_parser.py` → **35 passed**
  - [x] `src/reliability/agent/claim_parser.py` parses `FINAL_STATUS: RESOLVED | UNRESOLVED` plus `VALIDATION_EVIDENCE`; missing or malformed gives an explicit `UNPARSEABLE` carrying an `UnparseableReason` (`missing` / `invalid_value` / `ambiguous` / `empty_output`), never a silent default. `test_never_silently_defaults_to_unresolved` states that failure mode directly
  - [x] Fixtures cover all four required classes: **well-formed** (7 cases incl. markdown-wrapped, tight spacing, lowercase), **malformed** (5 invalid values + conflicting markers), **missing** (empty, whitespace, `None`, prose-only, evidence-without-status), **adversarial** (8 cases incl. "I think it's resolved", bare `RESOLVED`, `Status: resolved`, `final status: resolved`)
  - [x] **Prompt modified to require the markers, and confirmed to elicit them from a live model.** `configs/agent/swebench_claim.yaml` rewrites mini-swe-agent 2.4.6's builtin Submission section: the agent writes `claim.txt`, then submits it ahead of the patch behind a `<<<END_CLAIM>>>` delimiter. A file rather than inline `echo`s because the model never has to shell-quote free-form evidence, and because the submit command uses `;` not `&&` — a missing claim still submits and parses as `UNPARSEABLE` rather than hanging the agent. The prompt explicitly legitimises `UNRESOLVED`, since a prompt that made it feel like failure would bias the study's dependent variable. Live result on `psf__requests-1921`: `FINAL_STATUS: RESOLVED` with substantive evidence, re-parsing identically from the stored raw output
  - ⚠️ Precisely what that shows: the markers *can* be elicited from one model on one task, not that they always will be. The first smoke attempt produced no claim at all (throttled before submission), so the `UNPARSEABLE` path is not hypothetical and capture rate stays a measured quantity
  - Three parsing decisions recorded in the module docstring, each defensible the other way: formatting is forgiven but structure is not; **conflicting markers are `UNPARSEABLE`, not last-wins** (taking the last would fabricate a resolution to real ambiguity); and missing evidence does not void an otherwise well-formed status, since claim capture rate (9.3) and evidence quality are different measurements
  - ⚠️ Known boundary, pinned by a test rather than left implicit: an agent that writes the marker while *explaining* the format ("I should end with FINAL_STATUS: RESOLVED") is read as claiming it. Separating mention from use needs the final message alone, which is what the runner passes

- [x] **3.3 Repair record schema** — **GATE PASSED**, `pytest tests/unit/test_repair_record.py` → **30 passed**
  - [x] `src/reliability/agent/records.py` — pydantic, `frozen=True`, `extra="forbid"`. Records patch (path + sha256 + size), trajectory path, commands run, tests run, claim, termination, duration, tokens in/out, API cost
  - [x] Strict validation: every identity field required and non-empty, negative tokens/cost/duration rejected, unexpected keys rejected (the renamed-field-silently-loses-its-value failure), patch digest must be a well-formed `sha256:`. **`usage` is required, not defaulted — an unrecorded cost is not a zero cost**, and Phase 10.2 extrapolates the main-study budget from exactly these numbers
  - [x] `run_role` (`smoke` / `pilot` / `main`) has **no default**; `is_citable_as_result` is `False` for smoke runs, so a pipeline-proving run cannot be cited as a pilot result
  - [x] `termination` (`completed` / `step_limit` / `timeout` / `error`) is kept distinct from the claim: an agent killed at its step limit has *not* claimed `UNRESOLVED`, and collapsing the two would corrupt the 9.3 capture rate
  - [x] `load_records()` reads per-task files rather than a shared aggregate; `summarise()` computes the Phase 9 counts from disk with no model calls
  - [x] **"One real record from 3.1 validates against it" — done.** Both smoke records, written by the live runner, re-validate through `RepairRecord.read()` with `extra="forbid"`. That includes the rate-limited run, so the schema represents a truncated run without special-casing
  - [x] `Termination.RATE_LIMITED` added after the first smoke run was throttled. Kept distinct from `ERROR`: a truncated trajectory looks exactly like an agent that gave up, and folding the two together would license reading a quota limit as a capability finding

- [x] **3.4 Patch freeze** — **GATE PASSED**, `pytest tests/unit/test_freeze.py` → **19 passed**
  - [x] `src/reliability/agent/freeze.py` — patch written `0o444` and hashed on termination. Mutation raises: `open(w)`, `open(a)`, and `write_bytes` all raise `PermissionError` (three separate tests)
  - [x] Enforced twice, because either alone is weak. Permissions stop a stray writer anywhere in the codebase without it knowing about this module; the **content hash makes tampering detectable after the fact**, since a determined caller can `chmod` or replace the file. `verify()` catches content replacement, a patch left writable, and a deleted patch
  - [x] Bytes end to end, no text round-trip — `git apply` turns on exact line endings, so a CRLF patch round-trips byte-identical (`test_bytes_are_preserved_exactly`). Same reason `.gitattributes` marks `*.patch`/`*.diff` as `-text`
  - [x] `freeze_patch` refuses to overwrite an existing patch: a second freeze means a rerun writing over evidence, or a bug
  - [x] An empty patch is a real outcome, not an error — recorded with `is_empty`, since "the agent produced no diff" is a finding

**Supporting module.** `src/reliability/benchmark/manifest.py` (gated by `test_manifest.py`, **15 passed**) is the boundary between Phase 2 and everything after it. It recomputes the content hash from the file's bytes rather than trusting the sidecar, so a manifest edited after it was drawn fails loudly instead of running a different task set under the recorded identity. The committed `manifests/pilot.csv` loads and verifies against its recorded hash `sha256:f03000ed…` in the test suite.

---

## Phase 4 — Verifier V1: patch integrity

- [x] **4.1 Integrity checks implemented** — **GATE PASSED**, `pytest tests/unit/test_integrity.py` → **37 passed**, including all five handcrafted fixtures the gate names (clean, conflict markers, deletes a test file, touches config, won't apply)
  - [x] Applies cleanly to base commit — `git apply --check` against a real git repository built in the test, since that is the only honest way to test the property
  - [x] No conflict markers — checked on **added lines only**: a marker in removed content means the patch is *cleaning one up*, which is the opposite of the problem
  - [x] No binary blobs — `GIT binary patch` and `Binary files … differ`
  - [x] No modification of harness/benchmark files — `conftest.py`, `.github/`, `tox.ini`, `swebench/`, `run_evaluation`. A patch touching these is editing the exam, not the code
  - [x] No deletion or weakening of existing project tests — deletion rejects outright; weakening catches **two shapes**: removing assertions without replacing them (net loss of strength), and adding `skip`/`xfail` to an existing test, which leaves it "passing" while switched off
  - [x] No unexpected config manipulation — `setup.py`, `setup.cfg`, `pyproject.toml`, `pytest.ini`, `requirements*.txt`, `Makefile`. Editing these can green a suite without fixing behaviour (e.g. `addopts = --ignore=…`)
  - [x] Modifications within allowed scope — optional `allowed_paths` prefix whitelist
  - [x] **Malformed input rejects rather than passing vacuously.** The dangerous failure is a garbage patch parsing as "no changes", which every downstream check then passes. `parse_patch` raises on diff content with no file header, and an empty patch is its own violation
  - ⚠️ Finding worth carrying: `git apply` rejects thin-context hunks even when their line counts are self-consistent and the content matches — realistic surrounding context is required. Related to the borrowed-patch failure recorded under 1.3b, and the reason the "applies cleanly" fixture carries full context

- [x] **4.2 Risk features recorded (not auto-failing)** — **GATE PASSED**, fixture patch produces the expected feature vector (`test_expected_feature_vector`)
  - [x] files changed, LOC ±, net lines, source/test ratio, directories touched, unrelated dirs touched, broad `except` added, API surface change, adds-new-files, deletes-files
  - [x] **The separation is structural, not conventional.** `IntegrityReport.decision` is computed from `findings` alone and never reads `risk`; `compute_risk_features` is a pure measurement that cannot reject anything. `test_a_maximally_risky_patch_still_passes` pins it with a patch carrying a broad except, an API change and an unrelated directory, which returns PASS
  - Why it must not reject: the study needs to know whether these features *predict* failure, and that cannot be learned from a pipeline that rejects on them a priori
  - [x] "Unrelated" is measured relative to the patch's centre of mass — the top-level directory holding the most changed lines — rather than a hardcoded source root, which varies by repository. Private (`_`-prefixed) definitions do not count toward API surface

---

## Phase 5 — Verifier V2: regression tests

- [x] **5.1 Test-selection policy — written before code** — **GATE PASSED**, `pytest tests/unit/test_selection.py` → **22 passed**. Policy committed at `docs/VERIFIER_POLICY.md`; `src/reliability/verifier/selection.py` implements it, and where the two could diverge the policy wins
  - [x] Selection reads only the candidate patch and the base-commit tree
  - [x] Explicitly **does not** consult PASS_TO_PASS — and this is enforced structurally rather than by discipline. `select_tests` takes exactly `(patch, tree, config)`; there is **no parameter through which an oracle field could be supplied**, `SelectionConfig` has no such field, and the `RepoTree` interface exposes only `list_files`/`read_text` with no dataset row behind it. `test_select_tests_cannot_be_given_oracle_data` asserts the signature
  - [x] **§3.1 convention discovery** — test layout is derived per repository (sibling / mirrored / suffix / flat) by sampling source files and scoring which layout locates a matching test most often. Winner and hit rate are returned for the verification record, so the mapping used is auditable after the fact. Below a 0.2 hit rate the repo is `CONVENTION_UNKNOWN` and falls through to Tier 2 only
  - [x] **§3.3 tiers, capped at Tier 2 (decision on §8 open question 1).** Tier 1 direct correspondence, Tier 2 symbol reference. **Tier 0 whole-suite is behind `enable_tier0`, defaulted off**, and Tier 3 behind `max_tier` — both flags, so enabling either as an ablation later needs no code change. The trade: Tier 0 maximises evidence but also maximises overlap with `PASS_TO_PASS`, making the regression signal least distinguishable from half the oracle's criterion. Capped for interpretive cleanliness
  - [x] Tier 2 earns its place — `test_tier2_finds_the_cross_module_test` covers the ORM case where a compiler change is exercised through a queryset test that naming convention alone would never find
  - [x] Tests are unioned **in tier order**, so a budget cut drops the weakest evidence rather than an arbitrary slice (§3.4)
  - [x] **§5.3** agent-authored tests are excluded from the regression set — they are the agent's own claim about correctness, and admitting them would let it write its own acceptance criteria
  - [x] Config and code cannot drift: `test_shipped_configs_match_code_defaults` asserts `configs/verifier/{full,baseline}.yaml` match `SelectionConfig()` defaults, so a config claiming `enable_tier0: false` against a code default of true would fail the suite

- [x] **5.2 Runner implemented** — **GATE PASSED**, `pytest tests/unit/test_regression.py` → **32 passed**, covering every outcome
  - [x] Selects tests per policy and runs them with a timeout. The executor is a protocol, so classification is gated against fixtures rather than requiring Docker in the unit suite — same pattern as the Phase 3 agent backend
  - [x] **§3.2 baseline pass implemented.** Selected tests run twice, on the unpatched base and on the patched tree, and **only pass-to-fail transitions count as regressions**. Without it, every pre-existing failure — environment-dependent tests, skips resolving differently, tests simply broken at that commit — would be blamed on the candidate patch, inflating the rejection rate with noise and making the verifier look far more discriminating than it is
  - [x] **Baseline cached per instance** (`runs/_baseline_cache/<instance_id>.baseline.json`, written via temp-file-and-rename so a concurrent reader never sees a partial file). The base commit never changes, so it is computed once and reused across verifier configurations — which also keeps ablations comparable, since they then differ only in the patched pass
  - [x] Outcomes distinguish `PASS` / `REGRESSION` / `PRE_EXISTING_FAIL` / `NEWLY_PASSING` / `FLAKY` / `ERROR` / `TIMEOUT` / `NOT_RUN`; signals are `PASS` / `FAIL` / `NOT_AVAILABLE` / `BASELINE_UNRELIABLE`
  - [x] **Unexecuted tests are never passes.** `NOT_RUN` and `TIMEOUT` are outcomes in their own right; a test missing from either pass is `NOT_RUN`, and a test with no baseline result is `NOT_RUN` rather than a pass because no transition can be established. The signal is `PASS` only when regressions are zero **and** at least one test actually executed — `test_signal_pass_requires_both_zero_regressions_and_execution` pins that zero-regressions alone is not sufficient
  - [x] **§4.1 flake handling** — a `REGRESSION` is re-run once in isolation and marked `FLAKY` if it then passes, with the disagreement recorded. Rejecting a correct patch over a nondeterministic test would land in the false-rejection rate and distort the risk–coverage curve directly
  - [x] **§5.5 `BASELINE_UNRELIABLE`** — above half the selected tests failing on base, the environment is suspect rather than the repository; routed away from `PASS`
  - [x] **§8 open question 4** — `NEWLY_PASSING` is recorded but does not drive the signal, matching the policy's current position

- [ ] **5.3 Overlap audit**
  - [ ] Log how much the selected set overlaps PASS_TO_PASS (**analysis only, after the fact — never fed back into selection**)
  - **GATE:** overlap number computed and recorded for one instance. This is the number Dr. Hassan will ask about.

---

## Phase 6 — Verifier V3: static and build checks

- [x] **6.1 Per-repo check discovery** — **GATE PASSED**, `pytest tests/unit/test_static_checks.py` → **32 passed**. `src/reliability/verifier/static_checks.py`
  - [x] Detects available tooling per repository: syntax/compile, import check, linter (ruff / flake8 / pylint), type checker (mypy / pyright), package build. Discovery reads config files and `pyproject.toml` / `setup.cfg` / `tox.ini` sections, and records the evidence for each decision so the availability call is auditable after the fact
  - [x] A `tox.ini` present for unrelated reasons is not flake8 configuration — section sources only count when they carry the tool's section (`test_tox_ini_without_the_section_does_not_count`)
  - [x] **Unavailable tools are `NOT_AVAILABLE`, never a pass.** Same principle as `NOT_RUN` in Phase 5: absence of a check is never evidence of correctness. `CheckStatus.NOT_AVAILABLE.is_pass` is False, an unconfigured tool is never invoked at all (`test_unconfigured_tools_are_never_executed`), and every `CheckKind` resolves to an explicit status so no check can be silently omitted
  - [x] **Absolute vs relative checks.** Syntax, import and build are properties of the patched tree alone and need no baseline — a tree that will not compile is broken regardless of the base commit. Lint and typecheck are compared against the base, because repositories carry pre-existing violations and attributing them to the candidate patch would be the same mistake the §3.2 baseline pass exists to prevent
  - [x] Config and code cannot drift: `test_shipped_config_matches_the_absolute_relative_split` asserts `configs/verifier/full.yaml` matches `ABSOLUTE_CHECKS` / `RELATIVE_CHECKS` and `StaticConfig()` defaults

- [ ] **6.2 Executed inside the task container** — wiring built and gated, `pytest tests/unit/test_container.py` → **22 passed**. `src/reliability/verifier/container.py`
  - [x] `TaskContainer` runs one container per instance from the prebuilt `swebench/sweb.eval.x86_64.*` image, named uniquely, `--network none`, removed on exit even when a check raises. Parallel-safe by construction: nothing is shared between concurrent verifications
  - [x] The image is **derived from the instance id**, not looked up in the dataset, so standing a container up touches no oracle surface (`test_image_derivation_reads_no_oracle_field`)
  - [x] `set_patched()` moves the tree between the base and patched states by applying and reverting the frozen patch, which is what makes both Phase 5's baseline pass and Phase 6's relative checks affordable in a single container
  - [x] `ContainerRepoTree` exposes exactly `list_files` / `read_text` — selection cannot reach anything else through it (`test_repo_tree_satisfies_the_selection_protocol`)
  - [x] `ContainerTestExecutor` returns a result for **every requested test**; anything pytest never reported on comes back `NOT_RUN` rather than being dropped from the set, which is precisely where an unexecuted test would otherwise stop counting
  - **GATE (pending):** static checks produce results for all 10 pilot instances with availability tallied per repo. Needs the pilot images pulled and a real agent run to produce patches; deferred with Phase 5's live run

---

## Phase 7 — Decision policy and verification record

- [x] **7.1 Rule-based policy implemented** — **GATE PASSED**, `pytest tests/unit/test_decision.py` → **50 passed**, `tests/unit/test_evidence.py` → **32 passed**
  - [x] REJECT / ACCEPT / FLAG exactly as specified in technical design §12, implemented literally rather than paraphrased
  - [x] **The combining rule lives in its own module.** `src/reliability/verifier/decision.py` imports **no signal implementation** — not integrity, not regression, not static checks — and works entirely on a neutral `SignalOutcome` vocabulary. `src/reliability/verifier/evidence.py` adapts each signal's native report at the boundary. So a second policy can be written without touching signal code, and a signal can change its internals without touching policy. Enforced structurally: `test_decision_module_imports_no_signal_implementation` fails the moment such an import appears
  - [x] **Policy version string recorded in every decision.** `test_every_decision_carries_a_reason_and_a_version` asserts across all 648 evidence combinations that no decision is emitted without a version, a policy name, and at least one non-empty reason — a decision with no recorded reason is not auditable. `test_shipped_config_version_matches_the_policy` prevents a config claiming one version while code implements another
  - [x] **ACCEPT is currently unreachable under the full policy, and this is deliberate.** §12's third ACCEPT condition requires "at least one issue-specific execution signal supports repair", and the only such signal is V4's issue-derived reproduction tests, which are out of scope. An absent signal has **not met** its condition, so every otherwise-clean patch resolves to `FLAG` rather than `ACCEPT`. Quietly dropping the condition would weaken the policy in a way no reader of the design would expect; treating absence as a met condition is the exact error `NOT_RUN` and `NOT_AVAILABLE` exist to prevent. `test_full_policy_cannot_accept_while_v4_is_absent` pins this so it cannot be lost, and `test_the_same_run_accepts_once_v4_reports` shows ACCEPT becomes reachable when V4 lands **with no change to the rule**
  - [x] **Risk never rejects** (Phase 4.2 carried through). A high-severity flag downgrades ACCEPT to FLAG and nothing more, so the cost of a false positive is a human look rather than a discarded patch. `test_risk_never_rejects` sweeps every combination. The flag list is short on purpose — `broad_excepts_added` because swallowing an exception is the canonical way to make a failing test pass without repairing anything, and `deletes_files` because deletion removes behaviour the selected tests may no longer cover
  - [x] **`NOT_AVAILABLE` can never improve a decision.** `test_unavailable_is_never_treated_as_pass` asserts, for each of the four signals across all 648 combinations, that swapping a `PASS` for `NOT_AVAILABLE` never moves the decision up the REJECT → FLAG → ACCEPT ranking
  - **GATE:** truth-table test over every combination of integrity × regression × static × risk — 3⁴ signal states × 2³ boolean flags = **648 combinations, each asserted to yield a defined `Decision`**, for both policies

- [x] **7.2 Baseline verifier condition** — **GATE PASSED**
  - [x] `BaselinePolicy` = integrity + regression only
  - [x] **Not the full policy with layers switched off.** It does not require an issue-specific signal, so it reaches ACCEPT on evidence the full policy only FLAGs — and that asymmetry *is* the measurement, since a weaker verifier accepting more is exactly the false-acceptance difference the study exists to quantify (`test_baseline_accepts_where_full_only_flags`)
  - [x] It **ignores** the static and reproduction signals outright rather than reading them as `NOT_AVAILABLE`, so enabling those layers later cannot perturb baseline decisions and invalidate the comparison (`test_baseline_ignores_static_and_reproduction`)
  - [x] The two policies are held in a fixed relationship: they agree on every rejection, and the baseline is never stricter than the full policy (`test_baseline_never_rejects_where_full_accepts`, `test_baseline_is_never_stricter_than_full`)
  - **GATE:** both `full` and `baseline` produce a decision for identical evidence, over the entire truth table

- [ ] **7.3 Verification record schema**
  - **GATE:** `pytest tests/unit/test_verification_record.py` passes and one real record validates

---

## Phase 8 — Oracle runner

- [ ] **8.1 Oracle invoked only on frozen patches**
  - [ ] Runner refuses to execute unless both the repair record and verification record already exist for that task
  - **GATE:** `pytest tests/integration/test_ordering.py` — asserts oracle run raises when the verification record is absent

- [ ] **8.2 Oracle record written**
  - [ ] resolved, FAIL_TO_PASS result, PASS_TO_PASS result, infrastructure error flag
  - [ ] Infrastructure errors counted separately from unresolved
  - **GATE:** schema test passes; the 3 gold-patch instances from 1.2 replay to `resolved: true`

- [ ] **8.3 Full leakage audit**
  - [ ] Grep every agent prompt and verifier input in `runs/` for oracle fields
  - **GATE:** `scripts/audit_leakage.sh` exits 0 across all pilot runs. **This gate is non-negotiable — a failure invalidates the experiment.**

---

## Phase 9 — 10-task pilot

- [ ] **9.1 Dry run on 2 tasks**
  - [ ] Full chain: agent → freeze → verifier → oracle → records
  - **GATE:** 2/2 produce all four records with no manual intervention

- [ ] **9.2 Full pilot run**
  - [ ] All 10 tasks, single pass, no retries, no config changes mid-run
  - **GATE:** ≥8/10 complete without infrastructure failure. Below that, fix infrastructure and rerun — do not analyze a broken pilot.

- [ ] **9.3 Claim capture rate**
  - **GATE:** ≥9/10 produce a parseable `FINAL_STATUS`. Below that, revise the prompt and rerun.

- [ ] **9.4 Enough RESOLVED claims to study**
  - **GATE:** ≥4/10 agent `RESOLVED` claims. Below that, the model is too weak for the reliability question — trigger Gate 2 and escalate model before freeze.

---

## Phase 10 — Pilot analysis and freeze decisions

- [ ] **10.1 Metrics regenerate from stored records**
  - [ ] `analysis/metrics.py` computes FSR_agent, FAR_verifier, coverage, precision/recall from disk only — no LLM calls
  - **GATE:** `pytest tests/golden/test_metrics.py` reproduces known values from a fixture run directory

- [ ] **10.2 Cost and time model**
  - [ ] Per-task cost, latency, verifier CPU time → extrapolation to 50 / 65 / 75 tasks
  - **GATE:** table in `reports/pilot_summary.md`

- [ ] **10.3 Power estimate**
  - [ ] Given observed resolve rate and accept rate, state the expected size of the ACCEPT denominator at 50/75 tasks and the resulting CI width
  - **GATE:** number written down. If the denominator is under ~20, raise the k-patches-per-task or released-predictions option with Dr. Hassan before freezing.

- [ ] **10.4 Freeze**
  - [ ] Final task count, model + exact version, prompts, verifier policy, sampling strategy — all locked and hashed
  - **GATE:** `manifests/main_frozen.csv` committed with a tagged release. Nothing changes after this point.

---

## Blockers

_(record here: date, task id, what failed, what was tried)_

**None open.** No gate has failed twice for the same reason.

For the record, two failures during 1.2 were in my own tooling, not the gate, and are not blockers:

1. **2026-09-14 · 1.2 · launcher quoting.** First background launch used a nested `bash -c` whose escaped quotes leaked into redirect targets, so nothing ran (`"runs/.../run.log": No such file or directory`). Fixed by moving the runner into a real script file, `scripts/harness_sanity.sh`. No harness invocation had occurred, so no gate attempt was consumed.
2. **2026-09-14 · 1.2 · scoring denominator.** First scoring pass summed `submitted_instances` (3 per report, since the predictions file holds 3 rows) instead of `total_instances` (1 per single-instance run), reporting a false `3/9 FAIL`. The underlying run was already correct. Fixed in `scripts/score_reports.py`, which now uses `total_instances` and asserts `infra_failure_instances == 0`.

Three further toolchain faults were found on 2026-09-15 while working 1.3b/1.4. All are fixed; none is a blocker, but each would have caused a silent or misattributed failure later, so they are recorded.

3. **2026-09-15 · toolchain · CRLF contamination.** The editor saved files as CRLF, including `scripts/harness_sanity.sh`, which nothing in this session had edited. With `core.autocrlf=false` and no `text=auto` rule, CRLF would have been committed byte-for-byte, and a CRLF shell script fails at runtime — reproduced directly: `set: pipefail: invalid option name`. **Any rerun of 1.2 or 1.3 would have failed.** Fixed the three affected files; `.gitattributes` now pins `eol=lf` for source types, ordered so the existing `-text` rules for `*.patch`/`*.diff`/`*.jsonl` still win as later matches.
4. **2026-09-15 · toolchain · `image_for.py` unusable.** Looked up an image name by iterating all 500 dataset rows with every column materialised, pulling multi-kilobyte `problem_statement`/`patch`/`test_patch` text per row; each lookup took 10+ minutes and stalled the first 1.4 measurement run. Image names are derivable from the instance id (`__` → `_1776_`, lowercased), verified against all five known local images. `scripts/oracle_field.py` selects columns before iterating for the same reason.
5. **2026-09-15 · toolchain · ROS 2 leaks into the venv.** See the Decisions log entry; this is the one with consequences beyond tooling.

---

## Decisions log

_(record here: date, decision, rationale — especially anything settled with Dr. Hassan)_

- **2026-09-14 · Environment moved to WSL2 ext4.** Project relocated from `C:\Umich\Fall2026\Capstone` to `~/projects/cis695-agent-reliability` to avoid line-ending and permission problems with Docker. `core.autocrlf=false`; `.gitattributes` sets `*.patch -text` and `*.diff -text` so frozen patch artifacts stay byte-exact. The Windows copy is retained as an untouched fallback.
- **2026-09-14 · `swebench` pinned by PyPI version, not git SHA.** Checklist 1.1 asks for a pinned commit SHA, but the package is installed from PyPI as `swebench==5.0.2`, so no commit SHA exists. Provenance is the locked PyPI artifact in `uv.lock`. If a SHA is required for the writeup, switch to a git checkout before the Phase 10 freeze. `mini-swe-agent==2.4.6` is pinned the same way — both are experimental apparatus, so exact `==`, while ordinary dependencies stay on lower bounds.
- **2026-09-14 · Sanity-run instances chosen for repo diversity and traceability.** `django__django-12304`, `sympy__sympy-15599`, `matplotlib__matplotlib-25287` — three distinct repositories spanning framework/API, symbolic-numerical, and state/styling behaviour, and all three are already cited as worked examples in the technical design. Not chosen on any knowledge of model performance.
- **2026-09-29 · Model decision settled: open-weight, DeepSeek V4 Flash via LiteLLM.** `configs/model/primary.yaml` pins `deepseek/deepseek-v4-flash` on litellm's native `deepseek/` route, reading `DEEPSEEK_API_KEY`. Open weights matter beyond cost here: the study's claim is about an agent's self-assessment, and a model whose weights can be re-obtained keeps the apparatus reproducible after a provider retires an endpoint — not hypothetical, since the Gemini 2.0 and 2.5 families were withdrawn mid-project and took the 3.1 smoke configuration with them. ✅ **Verified 2026-09-29 by a live tool-calling request** — the model returned a well-formed `bash` tool call with `finish_reason: tool_calls` (308 in / 54 out tokens, $0.00012). Presence in litellm's cost map was explicitly *not* accepted as evidence, for the reason recorded below. The `verified:` block is written only by `scripts/verify_model.py` after a real request succeeds, never by hand, and that write is a surgical edit of the block alone — an earlier `yaml.dump` round-trip stripped every rationale comment from this file, which is exactly the provenance the config exists to carry.
- **2026-09-29 · With V4 out of scope, the full policy cannot reach ACCEPT — and the rule was implemented literally anyway.** Technical design §12 makes ACCEPT conditional on "at least one issue-specific execution signal supports repair". The only such signal is V4's issue-derived reproduction tests, which are not built. Two options: drop the condition so ACCEPT stays reachable, or treat the absent signal as a condition not met and let every otherwise-clean patch fall through to FLAG. The second was chosen. Dropping it would silently weaken the policy in a way no reader of the design would detect from its output, and treating an absent check as satisfied is the precise error that `NOT_RUN` (Phase 5) and `NOT_AVAILABLE` (Phase 6) exist to prevent — it would be inconsistent to enforce that principle on individual signals and then abandon it in the rule that combines them. **Consequence to state plainly in any interim writeup: until V4 lands, the full verifier's outputs are REJECT and FLAG only, and a FLAG does not mean the patch looked suspicious — it usually means one layer has not been built.** The baseline condition is unaffected, since it never required that signal, which is why the two policies remain comparable today. `test_full_policy_cannot_accept_while_v4_is_absent` pins the behaviour and `test_the_same_run_accepts_once_v4_reports` shows ACCEPT returns when V4 reports, with no change to the rule.
- **2026-09-29 · The combining rule shares no types with the signals it combines.** `verifier/decision.py` imports nothing from integrity, regression, static checks, selection, or patch; it reads a neutral three-valued `SignalOutcome` vocabulary, and `verifier/evidence.py` adapts each signal's report at the boundary. This is what makes a second policy a new class rather than an edit to every signal, and it also concentrates the "did not run" mapping in one auditable place — the adapter is the only code that can turn a signal's absence into something a policy sees, so the guarantee is checkable by reading one file. Enforced by a test that reads the module source, because a convention this load-bearing should not depend on reviewers noticing an import.
- **2026-09-29 · Selection capped at Tier 2; Tier 0 is a flag, not a code path.** Answers §8 open question 1 of the verifier policy. Running the whole suite where it fits maximises evidence, but it also maximises overlap with `PASS_TO_PASS` and makes the regression signal least distinguishable from half the oracle's own criterion. The cap trades evidential strength for interpretive cleanliness, and because Tier 0 sits behind `enable_tier0` (default false) the opposite choice can be run later as an ablation with a config edit and a `policy_version` bump — no code change, and therefore no risk that the ablation differs from the main run in some other way.
- **2026-09-15 · Free tier cannot run the pilot: 20 requests per day, per model.** Gemini's free tier caps `GenerateRequestsPerDayPerProjectPerModel-FreeTier` at 20, and an agent loop spends 10–40 model calls per instance. That is roughly one instance per model per day, so the 10-task pilot is infeasible on free keys regardless of patience. The quota is *per model*, which is why the throttled smoke run could be retried immediately on a different one — a useful trick for smoke tests, not a strategy for a study, since varying the model varies the thing being measured. The pilot needs a paid key; this constrains scheduling, not design.
- **2026-09-15 · A listed model is not a servable model.** `gemini-2.5-flash` appears in the live `ListModels` response and in litellm's cost map, yet returns `404 … no longer available` on this key. Availability was verified by issuing real tool-calling requests to each candidate rather than trusting either listing. Any later model pin should be validated the same way, since a config naming a dead model fails only at first API spend.
- **2026-09-15 · The end-to-end smoke run is not pilot data, and the schema enforces it.** Once Phase 3 is gated, one or two instances will run on a cheap or open model purely to prove the pipeline end to end. Those runs go in `runs/3.1_smoke_<model>/` with `run_role: smoke` on every record, and `is_citable_as_result` returns `False` for them. The marker is on each record rather than only in the directory name because a number, once copied into a table, loses its directory. A smoke run says something about the plumbing and nothing about any model's repair ability, and it is on a model the study does not use.
- **2026-09-15 · The model backend refuses to guess.** `MiniSweAgentBackend` raises rather than falling back to a default when `model_id` is unset. `configs/model/primary.yaml` stays `null` until advisor approval, and a fabricated pin is exactly the kind of thing that survives into a report unnoticed — the same reasoning that kept the config null in the first place. The failure is at construction, before any API call, so it cannot be discovered mid-run.
- **2026-09-15 · WSL2 memory capped at 10 GB; cap is active.** The host crashed during a multi-image pull. WSL2 defaults to claiming up to half of host RAM (~16 GB of 32 GB here) and image extraction is memory-hungry, so WSL and Windows were competing. `%UserProfile%\.wslconfig` now sets `memory=10GB`, `swap=8GB` (so an extraction spike degrades into swap rather than an OOM kill) and `autoMemoryReclaim=gradual` (freed page cache returns to Windows instead of the VM holding its high-water mark). Applied via `wsl --shutdown` and **verified active** 2026-09-15: `free -h` reports 9.7 GiB with 8 GB swap, and Docker's daemon allocation moved from 16.6 GB to 10.42 GB. The cap governs the `docker-desktop` VM too, since that is also a WSL2 distro — intended, and the reason the daemon figure changed.
- **2026-09-15 · The pilot manifest is a frozen artifact; the sampler is not a runtime dependency.** Downstream code reads `manifests/pilot.csv` and never re-runs the sampler. `sampler.py` exists to document and reproduce how the manifest was drawn, not to draw it again at run time. Consequence: the transient `datasets` failure recorded under 2.3 cannot affect any run — a sampling fault could only ever produce a *different manifest*, which the committed content hash would immediately expose. The manifest and its hash are the provenance; the sampler is the derivation.
- **2026-09-15 · Image sharing follows the build cohort, not the repository.** The 1.2 model assumed a flat ~4.9 GB per instance and extrapolated 368 GB at 75 tasks. Measured across nine images, marginal cost ranges from 0.25 GB to 8.6 GB depending purely on how many of an image's layers are already resident, and batch membership — not repo, and not `environment_setup_commit` — is what determines that. Consequence for Phase 2.3: stratified sampling across repositories, which the design requires, *reduces* layer sharing, so disk planning must be computed from the actual manifest rather than from an average. Full analysis in `reports/feasibility.md` §5.
- **2026-09-15 · Image retention is the default; pruning is a manual fallback.** Resident images are what make re-runs cheap (1.3b re-evaluated three instances in 200 s). With 308 GB free on `C:`, disk no longer justifies building prune-after-each-eval into the pipeline, which would trade ~48 s/instance of re-pull for space that is not scarce. Pruning stays available for manual use under disk pressure.
- **2026-09-15 · Patches cannot be transplanted between instances of the same repository.** Discovered building 1.3b: three django gold patches all failed `git apply --check` at another django instance's base commit. Base commits drift too far. Rules out cross-instance patch transfer in any later design, and means a borrowed patch is unusable as a control — it would fail to apply, leaving the tests unrun.
- **2026-09-15 · ROS 2 Jazzy contaminates the interpreter; contamination is recorded, not just cleared.** The host exports `PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages` into every shell, placing Python 3.12 packages ahead of this 3.11 venv. The visible symptom was `pytest` autoloading ROS plugins and dying on a missing `lark`, but the dangerous case is quieter: an agent or verifier run importing a shadowed module and producing a subtly different result that nothing in the record would explain. Two defences, because clearing alone is not auditable — every entry point clears it (`scripts/*.sh`, `reliability.env.clean_env` for subprocesses), **and** `provenance.py` records `pythonpath`, `sys_path`, and `foreign_sys_path_entries` into every `meta.yaml`, so a contaminated run is detectable after the fact even if it was launched through a path that forgot to clear. `reliability.env.assert_clean_interpreter()` fails fast where that is preferable.
- **2026-09-14 · Verified images are pulled, not built.** Each instance carries a prebuilt `swebench/sweb.eval.x86_64.*` image, so there is no local build step and no per-repo environment compilation. This materially lowers Stage 0 risk. Corollary: image storage lives on the Docker Desktop VHDX on the Windows drive, *not* the WSL2 ext4 disk, so `df -h ~` is the wrong instrument for image-disk headroom.
