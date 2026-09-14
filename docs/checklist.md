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

- [~] **0.1 Initialize repository** — environment done, directory scaffold still missing
  - [x] `uv init`, `pyproject.toml`, Python version pinned — Python 3.11 pinned via `.python-version`; `uv.lock` committed; `swebench` and `mini-swe-agent` held at exact `==` versions as experimental apparatus
  - [ ] Directory skeleton per technical design — **not done.** Only `src/reliability/__init__.py` exists. Still missing `src/reliability/{benchmark,agent,verifier,analysis,reporting}`, `configs/`, `manifests/`, `runs/`, `reports/`, `tests/`
  - [~] `.gitignore` excludes `runs/`, `*.jsonl`, `.env`, Docker volumes — **partial.** Covers `runs/`, `.env`, `.venv/`, `__pycache__/`, tool caches, `reports/{figures,tables}/`. Does **not** yet cover `*.jsonl` or Docker volumes
  - [x] `README.md` stub with the research question and the three-layer separation principle
  - **GATE PASSED** 2026-09-14 — `uv run --frozen python -c "import reliability; print(reliability.__version__)"` → `0.1.0`, exit 0
  - Held at `[~]` deliberately: the gate passes, but the scaffold is materially incomplete, so this is not finishable as `[x]` yet.

- [ ] **0.2 Secrets and config hygiene**
  - [ ] `.env.example` committed; real `.env` git-ignored
  - [ ] API key loaded from env only — never hardcoded, never logged
  - [ ] `configs/` has one YAML per layer (agent, model, verifier, experiment)
  - **GATE:** `git log -p | grep -iE "sk-ant|sk-proj"` returns nothing

- [ ] **0.3 Run-metadata recorder**
  - [ ] `reliability/provenance.py` writes the reproducibility block (task manifest hash, git commit, agent version, exact model id, temperature, step/token limits, timeout, verifier version, docker image, timestamp)
  - [ ] Every run directory gets one `meta.yaml`
  - **GATE:** `pytest tests/unit/test_provenance.py` passes — asserts all required keys present and non-null

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

  - [ ] **1.3b Non-empty wrong-patch control (proposed, not yet run)** — submit a syntactically valid but semantically wrong patch (e.g. a whitespace/no-op edit that still applies) so the harness is forced to actually run `FAIL_TO_PASS` and report `unresolved` with a populated `failure_reasons`. This is what closes the discrimination argument. Cost is low: images are already local, so ~1–2 min for all 3.

- [ ] **1.4 Feasibility numbers written down**
  - [ ] `reports/feasibility.md` with: minutes/instance, GB/instance, failure rate, estimated cost for 10 and for 75 tasks
  - **GATE:** file exists and the 75-task extrapolation is stated in hours and dollars

  🔴 **Hard constraint discovered in 1.2 — read before writing 1.4.** Docker images live on the Docker Desktop VHDX on the Windows `C:` drive, which has **58.9 GB free** (868.9 GB used of ~928 GB). Measured image cost is **~4.9 GB per instance** and the harness deliberately leaves images resident.

  | scale | image footprint if never pruned | fits in 58.9 GB free? |
  |---|---:|---|
  | 3 (done) | 14.6 GB | yes |
  | 10-task pilot | ~49 GB | barely, with no margin |
  | 50 tasks | ~245 GB | **no** |
  | 75 tasks | ~368 GB | **no** |

  The ext4 947 GB measured in 1.1 is irrelevant to this — it holds the repo and `runs/`, not images. Mitigations to decide before the pilot: prune each image after its eval (82 % of the current 18.32 GB store is already reclaimable), relocate the Docker VHDX to a larger drive, or free space on `C:`. Pruning trades disk for re-pull time (~70 s/instance observed).

---

## Phase 2 — Pilot task manifest

- [ ] **2.1 Load SWE-bench Verified**
  - [ ] `benchmark/loader.py` loads the 500-instance split
  - **GATE:** `pytest tests/unit/test_loader.py` — asserts exactly 500 instances and required fields present

- [ ] **2.2 Oracle-field quarantine (critical)**
  - [ ] Loader returns two separate objects: `AgentTask` (issue, repo, base_commit) and `OracleRecord` (patch, test_patch, FAIL_TO_PASS, PASS_TO_PASS)
  - [ ] `AgentTask` is a frozen dataclass with no oracle fields reachable
  - **GATE:** `pytest tests/unit/test_no_leakage.py` — serializes an `AgentTask` to JSON and asserts the strings `patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS` do not appear anywhere in the payload

- [ ] **2.3 Stratified sample of 10**
  - [ ] Sampler draws across repositories and task types (framework/API, ORM/DB, numerical, state/behavior, system/runtime)
  - [ ] Seeded and deterministic
  - [ ] No selection based on known model performance
  - [ ] Written to `manifests/pilot.csv` with a content hash
  - **GATE:** rerunning the sampler with the same seed reproduces the identical hash; manifest spans ≥3 distinct repositories

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

---

## Decisions log

_(record here: date, decision, rationale — especially anything settled with Dr. Hassan)_

- **2026-09-14 · Environment moved to WSL2 ext4.** Project relocated from `C:\Umich\Fall2026\Capstone` to `~/projects/cis695-agent-reliability` to avoid line-ending and permission problems with Docker. `core.autocrlf=false`; `.gitattributes` sets `*.patch -text` and `*.diff -text` so frozen patch artifacts stay byte-exact. The Windows copy is retained as an untouched fallback.
- **2026-09-14 · `swebench` pinned by PyPI version, not git SHA.** Checklist 1.1 asks for a pinned commit SHA, but the package is installed from PyPI as `swebench==5.0.2`, so no commit SHA exists. Provenance is the locked PyPI artifact in `uv.lock`. If a SHA is required for the writeup, switch to a git checkout before the Phase 10 freeze. `mini-swe-agent==2.4.6` is pinned the same way — both are experimental apparatus, so exact `==`, while ordinary dependencies stay on lower bounds.
- **2026-09-14 · Sanity-run instances chosen for repo diversity and traceability.** `django__django-12304`, `sympy__sympy-15599`, `matplotlib__matplotlib-25287` — three distinct repositories spanning framework/API, symbolic-numerical, and state/styling behaviour, and all three are already cited as worked examples in the technical design. Not chosen on any knowledge of model performance.
- **2026-09-14 · Verified images are pulled, not built.** Each instance carries a prebuilt `swebench/sweb.eval.x86_64.*` image, so there is no local build step and no per-repo environment compilation. This materially lowers Stage 0 risk. Corollary: image storage lives on the Docker Desktop VHDX on the Windows drive, *not* the WSL2 ext4 disk, so `df -h ~` is the wrong instrument for image-disk headroom.
