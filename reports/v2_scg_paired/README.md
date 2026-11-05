# Frozen updated V2 vs corrected SCG paired harness

Review package, 2026-11-05. **No live execution is authorized or performed.**

The branch starts at V2 `9654fc7`. Corrected SCG source is read from the fetched
`origin/experiment/callgraph-typeprop` at
`e1a3ed1c74fd304493c3fe3811de755af77e306c`, without merging. Its existing
headline configuration is B, depth 3, ALL, PRIMARY_RESOLVED_ONLY. No ranking,
selection cap, graph limit, production budget or verdict rule is changed.

## Implementation

- `scripts/v2_scg_paired.py`: preflight, immutable preparation, validation,
  scoped launch plans, guarded collection and paired/post-hoc summaries.
- `scripts/v2_scg_select.py`: isolated selection worker. Benchmark files are
  archive/AST data; no benchmark imports, tests or containers run during selection.
- `tests/unit/test_v2_scg_paired.py`: focused invariants and synthetic dry runs.

`prepare` copies the original 83-task V2 freeze and preserves every task ID,
candidate byte/hash, base commit/archive hash, runner and historical image field.
The version-2 paired protocol adds a separate host-local image binding; historical
image availability is never used as current Ubuntu availability.
It measures a fresh reproduction of each updated V2 selection and requires exact
list and runner equality with the original freeze. The original list remains
authoritative. Each SCG worker independently builds its graph from the same base
archive, uses the corrected qualified AST mapper and unchanged traversal/features/
ranking functions, then writes one ordered selection. SCG inventories base test
IDs with the existing extractor; it never invokes V2 selection/discovery. No
correctness, historical outcome, gold patch or known witness input is accepted
by preparation or collection.

The SCG source snapshot is exported byte for byte from the pinned Git revision
and sealed with the selections. The original normalizer is used by SCG identity
mapping with `changed={}`; its post-hoc analysis entry points are never called.
Both execution arms use the same current V2 `ContainerTestExecutor`, raw-ID
accounting, evidence hash checks, `run_regression`, confirmation rules and frozen
shadow-only classifier through the unchanged `v2_evaluation.execute_one`.

Both lists are fixed before any execution and reused unchanged for the initial
base and patched passes. Existing confirmation subsets remain unchanged. Both
arms check the identical union of selected test files and original V2 relevant
source files against the verified archive, using the same bound host-local image ID and
runner. Image HEAD differences remain recorded, as in V2; relevant-source
equivalence does not establish complete historical image identity.

Preparation and selection use fresh subprocesses; each execution arm uses a
fresh UUID-named container and a separate raw-evidence directory. There is no
baseline cache, fallback to other image tags/IDs, image pull, networking or shared writable
container/volume state. Task order is lexicographic; arm order alternates by
cohort index, including when a pilot selects a subset. The unchanged limits are
300 seconds per pass and the existing 600-second nominal pair metadata, with
the existing production patched confirmation and shadow base observations.
There is no newly imposed total-time cutoff or selection truncation.

The historical V2 protocol and host inventory remain immutable. Offline input
verification permits a different Ubuntu host/platform; preflight reports host
differences. Preparation seals the actual interpreter, package and platform
inventory for both arms. Validation refuses subsequent host drift. Prepare and
review a new paired freeze on the intended execution host; do not copy an
already prepared WSL freeze to Ubuntu and launch it there.

## Ubuntu-host image binding

`bind-images` inspects each exact frozen tag with `docker image inspect`, without
pulling/building images or starting containers. It records all 83 tasks, the
Docker daemon ID, current host inventory hash, actual host-local image ID,
historical ID/digest/environment status, availability and ID comparison. A
historical null ID may become available; a different historical ID is recorded
as a mismatch, not silently reused or rejected as proof of wrong source.

Matching tags/IDs and image availability do **not** establish source fidelity.
Bindings explicitly say NOT_VERIFIED. The existing archive hashes and common
selected/changed-source check remain required before benchmark execution for
either arm. A source mismatch retains ENVIRONMENT_MISMATCH and no verdict.

Pass the binding inventory explicitly to `prepare --image-bindings`. Its exact
bytes and SHA-256 are sealed in the new paired freeze/protocol. Task records keep
their historical `image_id`, `image_digest` and `environment_status` unchanged;
`image_binding.host_image_id` is the execution ID supplied to the shared V2
executor for **both** arms. Paired result `image_id` is this actual execution ID,
with the historical ID and complete binding recorded separately.

Preparation, validation, plan creation and launch re-inspect the exact tags and
check the same Docker daemon. Each arm checks again immediately before its
executor boundary. Retagging, deletion, a formerly missing image appearing, or
an inspection/daemon error blocks further execution; there is no automatic
rebinding, fallback to the historical ID, or continued use of a stale tag
resolution. Immutable image IDs still pin the container at launch. Missing
images stay explicitly MISSING with a null host ID. Docker permission, CLI or
daemon failures are INSPECTION_ERROR and block preparation rather than being
reported as missing images.

If bindings drift, collect a new inventory and prepare/review a new freeze and
pilot plan. Existing version-1 paired freezes and their plans cannot launch with
this fix; they must be recreated. Original V2 artifacts and historical reports
are never edited or resealed.

## Missing evidence and accounting

Available empty selections are `[]` with ZERO_SELECTION and the native
NOT_AVAILABLE verdict, without starting a container. An unavailable SCG
selection is `null`, never an empty list or a V2 fallback. Missing archives,
worker errors, no resolved seeds and resource-limited graphs remain explicit.
Partial graphs retain their parse failures/omissions and form separate metric
strata. A native PASS on a partial graph describes complete evidence for the
selected tests, not graph completeness or patch correctness. It is not promoted
to a broader correctness claim.

The shared source check and V2 list reproduction must be available before either
arm executes. Missing tests, timeouts, raw-ID gaps, runner failures, baseline
failures, unexecuted patched passes and unavailable images remain represented by
the original V2 evidence and verdict states. Missing evidence never creates a
PASS. An evidence-integrity exception yields an execution error with no verdict.
As in V2, FAIL has precedence over other evidence gaps; completeness remains a
separate field. Binary completed outcomes and abstentions are counted separately,
with all native signal and completeness counts retained.

Each task produces `tasks/<id>/paired.json`, two `paired_arm.json` files and the
original V2 result/raw/environment artifacts. `results.json` and `metrics.json`
contain paired selection overlap/count differences, execution coverage/missing
evidence, binary coverage/abstentions, regression detections and cost summaries.
Only task scopes with both binary outcomes enter the paired binary detection
table; unavailable/incomplete outcomes stay in the all-task signal table.

Costs include V2 selection reproduction, SCG input extraction and graph building,
SCG ID inventory/mapping/ranking, base/patched execution, production/shadow
confirmation execution, arm totals and complete per-task preparation + execution
wall time. Worker totals include process startup/import overhead; whole-collection
wall time is separate. Cgroup CPU (v1/v2), peak memory, runner time, evidence bytes,
selection-process CPU and peak RSS are retained when available. Missing timings
are null with measurement counts. If the existing V2 executor exits with an
exception before publishing its call ledger, phase/confirmation measurements
remain unavailable; overall attempt wall time is still recorded.

Correctness and witness sidecars are accepted only by `summarize`, after the
entire reviewed task scope has a completion marker and sealed result digest.
Sidecars must match candidate hashes and the reviewed scope. Witness selection
is unknown for unavailable selections, not false. The existing normalized
selected-ID witness schema and native V2 precision/recall/F1 definitions remain
unchanged; historical witnesses are not assumed to reproduce in a new environment.

## Validation performed

The original validation remains in `validation.json`, `unit.xml`,
`scg_source_manifest.json` and `preflight.json`. The image-binding fix has its
own report and test/lint evidence in `image_binding_fix/`.
The focused and existing selector/executor/regression/integrity suites pass.
Tests exercise exact IDs and budgets, production confirmation, flaky outcomes,
baseline guards, timeouts, missing tests, evidence tampering, independent arm
state, missing environments, empty/unavailable/partial/resource-limited graphs,
the corrected mapper, no SCG-to-V2 fallback, host/source/input drift, scope-bound
approval, aggregate missingness and post-hoc label barriers.

A synthetic all-83 manifest dry run verifies one artifact per arm per task and
original candidate/base/environment identity; it uses deliberately unavailable
SCG inputs. A synthetic one-task collection verifies paired abstention output
and summary generation. These are unit-test fixtures, not experiment results.
The real preflight verifies all 83 archive hashes and frozen input seals without
running task selectors, inspecting Docker or executing benchmark tests. It
records 39 historical pinned images and 44 historically unavailable environments;
these are frozen inventory records, not a claim about current Ubuntu availability.

No real all-83 paired selection preparation, benchmark execution, live pilot,
model invocation or oracle run was performed. No detection/accuracy or comparative
performance result is claimed. The real paired selection freeze is created by
the separate static `prepare` command below, before a pilot can be planned.

## Exact Ubuntu commands: offline review and preflight only

Run from the Ubuntu repository checkout. The detached review worktree preserves
the current branch and local changes; it does not merge either experimental arm.
Choose a new path/output name if any listed destination already exists.

```bash
git fetch origin experiment/v2-scg-paired-harness experiment/callgraph-typeprop
git worktree add --detach ../cis695-v2-scg-paired-review origin/experiment/v2-scg-paired-harness
cd ../cis695-v2-scg-paired-review
uv sync --frozen
export PYTHONPATH="$PWD/src"
uv run --no-sync python -B -m pytest \
  tests/unit/test_v2_scg_paired.py tests/unit/test_v2_evaluation.py \
  tests/unit/test_v2_scg_images.py \
  tests/unit/test_v2_integrity.py tests/unit/test_selection.py \
  tests/unit/test_container.py tests/unit/test_regression.py
uv run --no-sync ruff check scripts/v2_scg_paired.py scripts/v2_scg_select.py \
  scripts/v2_scg_images.py tests/unit/test_v2_scg_paired.py tests/unit/test_v2_scg_images.py
uv run --no-sync python -B scripts/v2_scg_paired.py preflight \
  --archives "$HOME/cg_repos/task_archives" \
  --out reports/v2_scg_paired/ubuntu_preflight_01.json
uv run --no-sync python -B scripts/v2_scg_paired.py bind-images \
  --out runs/ubuntu_image_bindings_01.json
python3 -m json.tool runs/ubuntu_image_bindings_01.json
git status --short
```

Preflight requires the existing verified task archives and the Git-frozen input
files. The offline preflight never calls Docker; the separate `bind-images`
command performs read-only Docker inspections. Neither downloads or replaces
environments. A remote pin mismatch fails closed for review. Do not change
frozen tags or historical image metadata to make preflight pass. Review the
binding inventory, including missing images and historical ID differences.

## Static preparation after preflight review; still no live execution

This separately builds all 83 static graphs and reproduces selections, potentially
taking substantial time under the unchanged per-graph limits. It runs no tests.
Use a new destination; interrupted or existing freezes are never overwritten.

```bash
uv run --no-sync python -B scripts/v2_scg_paired.py prepare \
  --archives "$HOME/cg_repos/task_archives" \
  --image-bindings runs/ubuntu_image_bindings_01.json --out runs/v2_scg_frozen_02
uv run --no-sync python -B scripts/v2_scg_paired.py validate --frozen runs/v2_scg_frozen_02
```

After the user identifies a pilot scope, create a plan with one `--task` per
reviewed task. For example, the syntax for a single task is:

```bash
uv run --no-sync python -B scripts/v2_scg_paired.py plan \
  --frozen runs/v2_scg_frozen_02 --task pytest-dev__pytest-5809 \
  --out runs/v2_scg_pilot_plan_02.json
sha256sum runs/v2_scg_frozen_02/protocol.json runs/v2_scg_pilot_plan_02.json
```

The example task is illustrative, not an authorized pilot. Review the selections,
protocol, environment availability, scope and plan hash before any launch.
`run --frozen ... --plan ... --out ... --approved-plan-sha256 ...` is the live
entry point. It requires the exact hash of the explicitly approved plan; there
is no default full-cohort run. **Stop here pending explicit pilot authorization.**

After an authorized pilot completes, summarize to a new file. Labels must cover
exactly the collected pilot scope; witness task IDs must be a subset. Formats
are the existing V2 sidecar formats (`patch_sha256` plus `correctness`, or
`patch_sha256` plus normalized `test_ids`). Neither sidecar can influence a
selection, execution request or verdict.

```bash
uv run --no-sync python -B scripts/v2_scg_paired.py summarize \
  --results runs/APPROVED_PILOT_RESULTS --out runs/NEW_PILOT_SUMMARY.json
```
