# Stage 0 Feasibility Report

**Project:** Trust but Verify — Execution-Grounded Verification of LLM-Generated Software Repairs
**Gate:** Checklist 1.4
**Date:** 2026-09-15
**Evidence:** `runs/1.2_gold_sanity`, `runs/1.3_empty_control`, `runs/1.3b_wrong_patch`, `runs/1.4_disk_model`

This report states what Phase 1 measured, what it did not, and what the numbers
imply for a 10-task pilot and a 50–75-task main study. Every figure below is
either measured on this machine or explicitly labelled as a bound or an estimate.

---

## 1. Summary

The environment is viable. The harness resolves gold patches, refuses empty
ones, and correctly fails a patch that applies but does not fix the bug. Nine
harness evaluations produced zero infrastructure failures.

The disk constraint recorded during 1.2 has been resolved and, separately, was
based on a wrong cost model. Free space on the Docker VHDX drive went from
58.9 GB to **308 GB**, and the per-instance image cost is lower and far more
variable than the flat ~4.9 GB previously assumed.

Nothing here has cost money yet. No API key has been used, and no model has been
selected.

---

## 2. Environment

| item | value |
|---|---|
| Host | WSL2 (Ubuntu) on Windows, kernel 6.18.33.2 |
| CPU / RAM available to Docker | 32 CPU, 16.6 GB |
| Docker | Desktop 28.5.1, WSL2 integration, non-root |
| Project disk (ext4) | 947 GB free — holds the repo and `runs/`, **not** images |
| Image disk (Docker VHDX on `C:`) | **308 GB free** of 928 GB |
| Python | 3.11.16, `uv`-managed venv |
| Harness | `swebench==5.0.2` (PyPI; see Deviations) |
| Agent scaffold | `mini-swe-agent==2.4.6`, not yet exercised |

### Images are pulled, not built

`swebench` 5.0.2 evaluates SWE-bench Verified instances against **prebuilt
images** published as `swebench/sweb.eval.x86_64.<repo>_1776_<id>:latest`. There
is no local Docker build and no per-repo environment compilation.

This materially lowers Stage 0 risk: the dominant failure mode in older SWE-bench
workflows — per-repo environment builds that fail on a subset of repositories —
does not apply. It also changes the cost profile. Image acquisition is network
and disk bound rather than CPU bound, it is one-time per instance, and it is
what the disk model in §5 measures.

Two consequences follow. Image storage lives on the Docker Desktop VHDX on the
Windows drive, so `df -h ~` is the wrong instrument for image headroom. And the
project depends on the continued availability of those published images; a
registry change would not be recoverable by rebuilding locally.

---

## 3. Time per instance

Measured across nine evaluations. "Acquisition" is a registry pull; "evaluation"
is the harness running the instance's test suites in the container.

| phase | acquisition (s) | evaluation (s) |
|---|---|---|
| 1.2 gold (cold images) | 51 / 31 / 129 | 31 / 38 / 122 |
| 1.3 empty (warm) | 4 / 4 / 3 | 5 / 5 / 6 |
| 1.3b wrong patch (warm) | 4 / 4 / 3 | 31 / 36 / 122 |

**Evaluation time is stable and instance-determined.** Gold and wrong-patch runs
produced nearly identical times per instance (31 vs 31, 38 vs 36, 122 vs 122),
so evaluation cost is a property of the instance's test suite, not of the patch.

- Evaluation: **mean 63 s, median 36 s** per instance.
- Acquisition, cold: **mean 48 s** across nine pulls (range 14–129 s).
- Acquisition, warm: 3–4 s (digest check only).
- Empty patches: 5–6 s, because the harness short-circuits before running tests.

`matplotlib-25287` is a consistent outlier at 122 s, roughly 3× the median; its
`PASS_TO_PASS` set is 786 tests against 17 for `django-12304`. The mean is
therefore pulled upward by one instance out of three, and **the median is the
better planning figure** for a sample that is not matplotlib-heavy.

Per fresh instance, one oracle pass costs roughly **111 s at the mean, 84 s at
the median**, including acquisition. A re-run against a local image is ~63 s.

---

## 4. Failure rate

| measure | result |
|---|---|
| Harness evaluations attempted | 9 |
| `infra_failure_instances` | **0** |
| Image pulls attempted | 9 |
| Pull failures | **0** |
| Evaluations that actually executed tests | 6 of 9 |

The three that did not execute tests are the 1.3 empty-patch runs, which the
harness short-circuits by design. Infrastructure reliability is 9/9, but the
sample is small and covers three repositories, so this should be treated as
"no problems observed" rather than a rate.

---

## 5. Disk per instance

This is the section that changed most, and the original model in the checklist
was wrong in mechanism as well as magnitude.

### The sharing unit is the build cohort, not the repository

SWE-bench's published images are built and pushed in batches. **Layer sharing
follows the batch, not the repository.** Measured from the layer graph
(`scripts/layer_overlap.py`), across nine local images:

- `django-12304` and `django-13212` are both django, but from the 2026-08-12
  batch, and share **only the generic 1.516 GB base** — there is no
  django-specific shared layer between them.
- `django-11815/11848/11999/12125` are the 2026-08-15 batch and share
  **2.876 GB** with each other (base plus a django environment layer).
- Cross-batch images share just 0.088 GB, regardless of repository.

The dataset's `environment_setup_commit` does **not** predict sharing.
`django-12304` and `django-13212` sit in different `environment_setup_commit`
groups yet share exactly as much as django↔sympy does.

### Measured marginal cost

Ground truth is the deduplicated store delta across a pull. Docker's per-image
`SharedSize`/`UniqueSize` attribution was found unreliable — summing per-image
`UniqueSize` exceeded the reported store total, implying a negative shared
remainder — so it is not used here.

| instance | delta (GB) | situation |
|---|---:|---|
| `django-12304` | 4.19 | first image of its batch |
| `sympy-15599` | 1.78 | batch base already present |
| `matplotlib-25287` | 8.61 | batch base present, but a 10.8 GB image |
| `django-12125` | 4.08 | first image of a *different* batch |
| `django-13212` | 2.02 | only the generic base shared |
| `django-11815` | 0.25 | shares base + django env layer |
| `django-11848` | 0.26 | shares base + django env layer |
| `django-11999` | 0.25 | shares base + django env layer |
| `sympy-13043` | 3.81 | first image of a different batch |

Nine images occupy **25.25 GB**, an average of 2.81 GB each. That average is not
a safe planning number on its own: the sample is deliberately repo-clustered
(six django), which maximises sharing.

The real determinant is how many of an image's layers are already on disk:

| case | cost |
|---|---:|
| Shares base **and** repo env layer (same repo, same batch) | **~0.25 GB** |
| Shares only the generic base | **~2 GB** |
| Shares nothing meaningful (new batch) | **~4 GB** |
| Unusually large image (e.g. matplotlib) | **up to 8.6 GB** |

### Why no single extrapolation is given

The total depends on which batches the sampled instances happen to land in, and
that is not knowable until the manifest exists. Worse, Phase 2.3 requires
stratified sampling across repositories and task types, which **actively erodes
layer sharing** — the sampling strategy and the cheap-disk case pull in opposite
directions.

Bounding cases for 75 tasks:

| scenario | footprint | fits 308 GB? |
|---|---:|---|
| Every instance a fresh batch (~4.1 GB each) | ~307 GB | marginal |
| Realistic: ~12 repos × 2–3 batches, remainder clustered | ~120–200 GB | yes |
| Heavy clustering within few batches | ~60–80 GB | yes |

A 10-task pilot is comfortable under every scenario (~10–45 GB).

**Action for Phase 2.3:** once `manifests/pilot.csv` exists, compute the exact
figure by grouping the sampled instance ids by image batch and applying the table
above, rather than multiplying by an average. The stated deliverable of this
section is the cost *model*, not a single number the model does not support.

### Retention policy

Image retention is the default; the harness leaves images resident, which is what
makes re-runs cheap (1.3b re-evaluated three instances in 200 s total because the
images were local). Pruning is a **manual fallback** for disk pressure only and is
deliberately not built into the pipeline. The current store is 100 % reclaimable
if ever needed, at a cost of ~48 s per instance to re-pull.

---

## 6. What the controls established

### 1.2 — gold patches resolve

3/3 resolved, 0 infrastructure failures. The environment executes real repairs
correctly.

### 1.3 — empty patches are refused

0/3 resolved. **But the harness short-circuits empty predictions**: all three
were classified `empty_patch_ids` with `completed_instances: 0`, so the test
suites never ran. This proves the harness will not pass a no-op submission. It
proves nothing about whether the tests discriminate.

### 1.3b — a patch that applies but does not fix the bug

3/3 unresolved, with the tests actually executed:

| instance | applied | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|---|
| `django-12304` | yes | 0 pass / 1 fail | 17 pass / 0 fail |
| `sympy-15599` | yes | 0 pass / 1 fail | 80 pass / 0 fail |
| `matplotlib-25287` | yes | 0 pass / 2 fail | 786 pass / 0 fail |

`empty_patch_instances: 0` and `completed_instances: 1` per instance, versus 3
and 0 in 1.3 — the suites ran. 883 `PASS_TO_PASS` tests passed, so the failures
are the discriminating tests doing their job rather than a broken environment.

**Be precise about what this shows.** The patch is an appended comment, so the
code is semantically identical to the unfixed base. What 1.3b demonstrates is
that the harness executes the suites and that `FAIL_TO_PASS` fails on **unfixed
code** — exactly the blind spot 1.3 left, which is why the gate passes.

It is **not** a test of discrimination against a *plausible but wrong* repair. No
patch of that kind has been evaluated yet. That case is exercised for free once
the agent begins producing patches in Phase 3, and it is the scientifically
interesting one, because the failure mode this project studies is a patch that
looks right and is not. If it is ever wanted earlier, the correct construction is
a gold patch with one condition inverted — not an inert edit.

### A constraint discovered while building 1.3b

The first attempt borrowed a gold patch from a different instance in the same
repository. **It does not work.** `django-13212`, `django-11815`, and
`django-11999` all failed `git apply --check` at `django-12304`'s base commit,
tested inside that instance's own evaluation image.

Base commits within a single repository drift far enough apart that patches
cannot be transplanted between instances. This is worth recording beyond 1.3b: it
rules out any later design that reuses one instance's patch against another —
cross-instance patch transfer, "apply the neighbouring fix" baselines, or
mutation controls built by borrowing. A patch that fails to apply is also the
worst possible control, because the tests never run and it silently reproduces
1.3's blind spot.

---

## 7. Cost

**Spent to date: $0.** No API key has been used; Phase 1 is entirely local
Docker execution on owned hardware. Marginal compute and storage cost is zero.

The per-task API cost **cannot be estimated yet** and is deliberately not
guessed here: no model has been selected (`configs/model/primary.yaml` leaves
`provider` and `model_id` null by design, per the technical design's decision to
choose after the pilot), and no agent trajectory has ever been run, so
tokens-per-task is unmeasured.

What can be stated is the **configured ceiling**, which is a real budget bound
rather than a price estimate. `configs/model/primary.yaml` sets
`max_cost_usd_per_task: 5.00`:

| scale | upper bound on API spend |
|---|---:|
| 10-task pilot | **≤ $50** |
| 75-task main study | **≤ $375** |

These are hard ceilings enforced per task, not forecasts; actual spend is
expected to be well below them. Phase 10.2 replaces them with measured
per-task cost from pilot trajectories.

### Wall-clock for 75 tasks

| component | 75-task time | basis |
|---|---:|---|
| Oracle evaluation + image acquisition | **1.8–2.3 h** | measured (§3) |
| Verifier regression runs | 1–2 h expected; **≤ 18.8 h** bound | unmeasured; bound from `timeout_s: 900` |
| Agent runs | **≤ 37.5 h** bound | unmeasured; bound from `per_task_timeout_s: 1800` |

Only the first row is measured. The total is dominated by the agent stage, which
has never been run. The honest statement is: **the oracle and verification
infrastructure costs 2–3 hours at 75 tasks, and the end-to-end figure is bounded
below ~59 hours by configured timeouts but will not be known until the pilot.**
Phase 10.2 produces the real number.

---

## 8. Deviations and open items

- **`swebench` pinned by PyPI version, not git SHA.** Checklist 1.1 asks for a
  commit SHA; the package is installed from PyPI as `swebench==5.0.2`, so none
  exists. Provenance is the locked artifact in `uv.lock`. Switch to a git
  checkout before the Phase 10 freeze if a SHA is required for the writeup.
- **Model unselected.** Blocks any cost figure and must be filled before Phase 3,
  which is the first API spend.
- **Interpreter contamination is a live host hazard.** ROS 2 Jazzy exports
  `PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages`, injecting Python 3.12
  packages into this 3.11 venv. It broke `pytest` outright, but the dangerous
  case is a silently shadowed import inside an agent or verifier run. Entry
  points now clear it, and `provenance.py` records `pythonpath`, `sys_path`, and
  `foreign_sys_path_entries` into every `meta.yaml` so contamination is
  detectable in the record rather than invisible.
- **The 1.3 caveat stands in the record.** It is kept rather than edited away,
  because the reason 1.3b exists is only legible alongside it.

---

## 9. Verdict

Feasible. The harness is sound, infrastructure reliability is 9/9, disk is no
longer a constraint at pilot scale and is manageable at 75 tasks under every
realistic scenario, and the measured oracle cost is ~2–3 hours at full scale.

The unquantified risks are all downstream of Phase 3: per-task API cost, agent
wall-clock, and how many tasks yield a `RESOLVED` claim worth verifying. Those
are what the pilot exists to measure.
