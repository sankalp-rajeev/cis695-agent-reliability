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
  - [x] Docker daemon running, non-root access confirmed — Docker Desktop 28.5.1 with WSL2 integration; `docker` runs as user `rajee` with no `sudo`. Daemon reports `OSType=linux`, `x86_64`, 32 CPU, 16.6 GB RAM
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

---

## Phase 3 — Repair agent runner

- [ ] **3.1 mini-SWE-agent integration**
  - [ ] Installed at a pinned version
  - [ ] Runs one instance end-to-end in Docker and emits a patch
  - **GATE:** a non-empty `.patch` file exists for one pilot instance and `git apply --check` succeeds against the base commit

- [ ] **3.2 Structured final claim**
  - [ ] Prompt modified to require `FINAL_STATUS: RESOLVED | UNRESOLVED` plus `VALIDATION_EVIDENCE`
  - [ ] `agent/claim_parser.py` parses it; missing or malformed claim → explicit `UNPARSEABLE`, never a silent default
  - **GATE:** `pytest tests/unit/test_claim_parser.py` passes on a fixture set of well-formed, malformed, missing, and adversarial ("I think it's resolved") outputs

- [ ] **3.3 Repair record schema**
  - [ ] Writes the full record: patch path, trajectory path, commands run, tests run, claim, duration, tokens in/out, API cost
  - **GATE:** `pytest tests/unit/test_repair_record.py` validates the schema; one real record from 3.1 validates against it

- [ ] **3.4 Patch freeze**
  - [ ] Patch is hashed and written read-only once the agent terminates
  - [ ] Any downstream write to a frozen patch raises
  - **GATE:** `pytest tests/unit/test_freeze.py` — asserts mutation attempt raises and hash is stable

---

## Phase 4 — Verifier V1: patch integrity

- [ ] **4.1 Integrity checks implemented**
  - [ ] Applies cleanly to base commit
  - [ ] No conflict markers, no binary blobs
  - [ ] No modification of harness/benchmark files
  - [ ] No deletion or weakening of existing project tests
  - [ ] No unexpected config manipulation
  - [ ] Modifications within allowed scope
  - **GATE:** `pytest tests/unit/test_integrity.py` passes against handcrafted fixture patches — one clean, one with conflict markers, one deleting a test file, one touching config, one that won't apply

- [ ] **4.2 Risk features recorded (not auto-failing)**
  - [ ] files changed, LOC ±, source/test ratio, unrelated dirs touched, broad `except`, API surface change
  - **GATE:** fixture patch produces the expected feature vector

---

## Phase 5 — Verifier V2: regression tests

- [ ] **5.1 Test-selection policy — written before code**
  - [ ] Policy documented in `docs/VERIFIER_POLICY.md`: how the relevant test set is chosen from the *patch and repo alone*
  - [ ] Explicitly **does not** consult PASS_TO_PASS
  - **GATE:** policy doc reviewed and committed; a reader can apply it by hand and get the same test set

- [ ] **5.2 Runner implemented**
  - [ ] Selects tests per policy, runs in the task container with a timeout
  - [ ] Distinguishes `PASS` / `FAIL` / `ERROR` / `TIMEOUT` / `NOT_AVAILABLE` — a crashed suite is never counted as a pass
  - **GATE:** `pytest tests/unit/test_regression.py` covers all five outcomes on fixtures

- [ ] **5.3 Overlap audit**
  - [ ] Log how much the selected set overlaps PASS_TO_PASS (**analysis only, after the fact — never fed back into selection**)
  - **GATE:** overlap number computed and recorded for one instance. This is the number Dr. Hassan will ask about.

---

## Phase 6 — Verifier V3: static and build checks

- [ ] **6.1 Per-repo check discovery**
  - [ ] Detects available tooling: syntax/compile, import check, linter, type checker, package build
  - [ ] Unavailable tools recorded as `NOT_AVAILABLE`, never counted as pass
  - **GATE:** `pytest tests/unit/test_static_checks.py` — asserts a repo with no mypy config yields `NOT_AVAILABLE`, not `PASS`

- [ ] **6.2 Executed inside the task container**
  - **GATE:** static checks produce results for all 10 pilot instances, with availability tallied per repo

---

## Phase 7 — Decision policy and verification record

- [ ] **7.1 Rule-based policy implemented**
  - [ ] REJECT / ACCEPT / FLAG exactly as specified in the technical design
  - [ ] Policy version string recorded in every decision
  - **GATE:** `pytest tests/unit/test_decision.py` — truth-table test over every combination of integrity × regression × static × risk; no input produces an undefined decision

- [ ] **7.2 Baseline verifier condition**
  - [ ] Implement `baseline` = integrity + regression only (this is the comparison Dr. Hassan will ask for)
  - **GATE:** both `full` and `baseline` policies produce a decision for the same frozen patch

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
- **2026-09-15 · Image sharing follows the build cohort, not the repository.** The 1.2 model assumed a flat ~4.9 GB per instance and extrapolated 368 GB at 75 tasks. Measured across nine images, marginal cost ranges from 0.25 GB to 8.6 GB depending purely on how many of an image's layers are already resident, and batch membership — not repo, and not `environment_setup_commit` — is what determines that. Consequence for Phase 2.3: stratified sampling across repositories, which the design requires, *reduces* layer sharing, so disk planning must be computed from the actual manifest rather than from an average. Full analysis in `reports/feasibility.md` §5.
- **2026-09-15 · Image retention is the default; pruning is a manual fallback.** Resident images are what make re-runs cheap (1.3b re-evaluated three instances in 200 s). With 308 GB free on `C:`, disk no longer justifies building prune-after-each-eval into the pipeline, which would trade ~48 s/instance of re-pull for space that is not scarce. Pruning stays available for manual use under disk pressure.
- **2026-09-15 · Patches cannot be transplanted between instances of the same repository.** Discovered building 1.3b: three django gold patches all failed `git apply --check` at another django instance's base commit. Base commits drift too far. Rules out cross-instance patch transfer in any later design, and means a borrowed patch is unusable as a control — it would fail to apply, leaving the tests unrun.
- **2026-09-15 · ROS 2 Jazzy contaminates the interpreter; contamination is recorded, not just cleared.** The host exports `PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages` into every shell, placing Python 3.12 packages ahead of this 3.11 venv. The visible symptom was `pytest` autoloading ROS plugins and dying on a missing `lark`, but the dangerous case is quieter: an agent or verifier run importing a shadowed module and producing a subtly different result that nothing in the record would explain. Two defences, because clearing alone is not auditable — every entry point clears it (`scripts/*.sh`, `reliability.env.clean_env` for subprocesses), **and** `provenance.py` records `pythonpath`, `sys_path`, and `foreign_sys_path_entries` into every `meta.yaml`, so a contaminated run is detectable after the fact even if it was launched through a path that forgot to clear. `reliability.env.assert_clean_interpreter()` fails fast where that is preferable.
- **2026-09-14 · Verified images are pulled, not built.** Each instance carries a prebuilt `swebench/sweb.eval.x86_64.*` image, so there is no local build step and no per-repo environment compilation. This materially lowers Stage 0 risk. Corollary: image storage lives on the Docker Desktop VHDX on the Windows drive, *not* the WSL2 ext4 disk, so `df -h ~` is the wrong instrument for image-disk headroom.
