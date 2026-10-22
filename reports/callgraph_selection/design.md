# Offline call-graph selection experiment — design for review

**Phase 1 only. UNCOMMITTED DRAFT.** These parameters are specified before new
selector outputs or oracle comparisons exist. They become frozen only when the
user explicitly requests a commit of this file. No phase-2 selector work starts
before phase-1 review; no new post-hoc oracle code may run before the design is
committed and phase 3 is authorized.

The prior V2 diagnostic is committed separately as `a4137d1`. Production V2,
`VERIFIER_POLICY.md`, decisions, experiment configs, manifests, committed study
classifications, and existing run artifacts remain unchanged.

## 1. Question, phases, and stop points

Does base-only static reachability reduce candidate count and concentrate
pre-existing tests around changed production definitions? Can the same evidence
rank the stored V2 union more efficiently?

1. **Design and base-source feasibility.** Inspect existing representations,
   inventory verified base sources, measure static parsing feasibility where
   sources exist, and document graph-model limitations. Stop for review. This
   phase does not implement selectors or execute post-hoc oracle analysis.
2. **Selectors and oracle-blind evaluation.** After approval, implement the
   graph, seed mapping, and A/B/C offline comparison under this specification.
   Freeze candidate IDs, scores, provenance, all inputs, code revision, and the
   design commit hash. Stop for review before any oracle comparison.
3. **Post-hoc evaluation.** Only after separate approval and a committed design,
   run an isolated module labeled **POST-HOC ANALYSIS ONLY — MUST NEVER FEED
   BACK INTO SELECTION OR POLICY**. Stop for review. No production integration.

There is no model access, network data acquisition, test collection, test
execution, repair/verifier/oracle rerun, or import of benchmark source code.
The explicitly requested Git push of the preceding diagnostic is separate from
the offline research workflow. No recommendation is made before measurements.

## 2. Existing code to reuse

- `src/reliability/verifier/patch.py`: `parse_patch`, `touched_symbols`. These
  expose a diff-based inventory, including hunk/context names; they are not a
  complete semantic change analysis.
- `selection.py`: `RepoTree`, `is_test_file` (from integrity), `node_ids`,
  `django_label`, and existing test-layout conventions. Current Tier 2 is a
  word-boundary reference search over test files, not an implemented import graph.
- `Selection.by_tier` exists transiently; `VerificationRecord` does not persist
  it. Historical Tier 1/Tier 2 counts cannot be recovered from union order.
- `regression.py`: existing outcome meanings. Aggregate counts cannot establish
  which particular test executed, timed out, or was a pre-existing failure.
- `reports/v2_diagnostic/oracle_posthoc.py`: **reuse its existing `canonical`,
  `family`, and post-hoc `match_test` functions; do not create a second ID
  normalizer.** Phase 1 neither imports nor executes that module. In phase 2,
  any identity adapter must call only the existing pure normalization functions
  on base/selected IDs, with no oracle inputs and no diagnostic `main/build`
  invocation. All actual gold comparisons remain exclusive to phase 3.

No reusable production AST call-graph/import resolver was found. A new graph
implementation will therefore live under this report directory, never `src/`.

## 3. Populations and candidate-patch provenance

The immutable population input is the committed 83-row
`reports/v2_diagnostic/patches.csv`. Read only its explicit identity/provenance
columns for cohort membership; do not read oracle columns to construct/rank a
graph. Base commits come from the existing `manifests/main_100.csv`, whose
sidecar is validated using the existing manifest loader. Neither file is edited.

**Historical like-for-like comparison:** A vs B vs C is limited to the **19
`study_snapshot` tasks** with confirmed stored V2 selections. Retain all 19
rows, even when graph/source/patch reconstruction fails; report missing values
and common-evaluable denominators. Do not substitute pilot or alternate runs.

**Separate new offline analysis:** B alone runs on every population task with a
reconstructable candidate patch and a verified base snapshot. Report this as a
new analysis, not an 83-task historical comparison. Keep the five local-only
records with unverified final-run identity in a separate exploratory stratum.
The other 59 tasks currently lack detailed patch/selection artifacts; missing
patches do not become empty selections or zeros.

Candidate bytes may come from the committed failure-analysis snapshot's
`agent_patch` field (19 confirmed cases) or hash-checked local frozen candidate
diffs (separate exploratory provenance). A whitelist projection may expose only
instance/run identity, candidate diff, and stored selection fields from the
snapshot. Gold fields, official test lists, labels, issue hindsight, and failure
categories must not reach graph/selector functions. Record the containing
artifact hash and derived candidate hash; do not claim a missing original
repair-record hash was available.

## 4. Where base repositories come from

Preferred source: **an existing local Git clone/object store** containing the
exact manifest `base_commit`. Read tracked blobs using `git ls-tree` and `git
show <base_commit>:<path>`; never check out, reset, clean, install, import, or
execute the repository. Set `GIT_NO_LAZY_FETCH=1`, disable prompts and fsmonitor,
and fail on missing objects rather than fetching them.

Alternative: **read-only extraction from an already-local evaluation image**
`swebench/sweb.eval.x86_64.<derived-instance>:latest`. Record its immutable image
digest. Copy `/testbed` from an unstarted temporary container into a separate
research cache, retaining Git objects, then read the exact base commit as above.
No image pull/build, container start, `docker exec`, package/cache source reads,
or test process is allowed. Do not reuse the production `TaskContainer`, which
starts containers and applies patches. Extraction requires a usable local Docker
engine and is not performed by the phase-1 inventory tool.

Every source mapping records instance ID, source kind (`local_clone` or
`image_extraction`), local path, base SHA, and image digest where applicable.
Hashes of sorted tracked paths and Python blob contents bind the graph inputs.
The worktree may be dirty because only base-commit blobs are read; worktree
contents never supply graph code. Unverified trees, installed package copies,
gold diffs, snippets, and filename-only fixtures are not substitute base repos.

**Current feasibility finding:** no benchmark clones were found in the inspected
project/cache locations. The available `docker` command is a WSL placeholder
reporting unavailable integration; no local Unix Docker socket was found. No
base repository has yet been verified. Graph construction success, parsing
rates, and changed-symbol resolution are therefore **unmeasured**, not zero.
An availability inventory is not evidence that the graph model works.

## 5. Graph model and fixed resource limits

Use Python 3.11's `ast.parse` on base-commit `.py` blobs, without importing them.
Record syntax/encoding failures, including unsupported newer Python syntax.
Graph identities contain path, lexical qualified name, definition kind, and
source location. Candidate test IDs reuse the existing representation; preserve
and report any ambiguity between legacy IDs and nested-class graph identities.

Nodes: modules, classes, functions, methods, test functions, and test methods.
Containment/import-reference edges are metadata. Traversable call edges point
**caller → callee** and are classified as resolved, ambiguous, or unresolved.

Resolve only uniquely supported lexical/local-module names, explicit import
aliases to known first-party definitions, and statically identifiable attributes.
`self`/`cls`, inheritance, constructors, decorators, and receiver rebinding require
explicit checks; record ambiguity rather than choose a global same-name target.
Do not fabricate fixture/setup calls, monkey-patch effects, generated functions,
reflection/getattr targets, dynamic imports, or external dependency behavior.
Constructor calls may identify the class, but do not invent an implicit
class→`__init__` call edge. Custom decorators and ambiguous inheritance are
uncertainty, not permission to traverse every candidate target.

Primary traversal uses **resolved call edges only**. Ambiguous/unresolved call
sites and all candidate targets/reasons are counted separately; they are not
converted into primary reachability. "Resolved" means unique under the static
model, not verified at runtime.

Fixed limits per task/base snapshot:

| Limit | Value | On exhaustion |
|---|---:|---|
| Tracked Python files | 50,000 | Mark resource-limited; do not score a partial graph |
| Individual source blob | 2 MiB | Record omitted file; incomplete-graph flag |
| Total Python source bytes | 512 MiB | Mark resource-limited |
| AST nodes inspected | 5,000,000 | Mark resource-limited |
| Definitions | 1,000,000 | Mark resource-limited |
| Call sites/edge records | 2,000,000 | Mark resource-limited |
| Graph construction wall time | 600 seconds | Mark resource-limited; no automatic retry |

Syntax failures and omitted files make a graph partial and must be reported.
Only complete graphs enter the primary comparison; partial diagnostics remain
visible. Resource failures remain in feasibility denominators. Never reduce
depth, change thresholds, or silently truncate a graph to manufacture success.

## 6. Changed symbols and exact distance definition

Reuse candidate diff parsing and `touched_symbols`. Restrict seeds to changed
production Python paths under the existing source-file definition. Match names
to base definitions within their actual changed file, not globally by name.
Unique file/name identity resolves a seed; multiple same-name definitions remain
ambiguous. New symbols absent at base, syntax failures, and unmatched names are
separate unresolved reasons. Do not substitute a module/class-wide seed merely
to increase reachability. Record total/resolved/ambiguous/unresolved counts and
resolution rate; missing source graphs yield missing rates, not zero.

Distance is the **number of caller→callee call edges from a test definition to a
changed production seed**. A direct test→seed call has distance **1**. Thus
"direct" and "distance ≤1" describe the same configuration, not two independent
results. Evaluate **d ∈ {1, 2, 3}** separately. Reverse traversal for discovery
does not reverse the meaning of the recorded path. Module containment, imports,
decorators, fixture injection, and class membership do not add shortcut edges.

For a given test/seed, retain one shortest path, breaking equal-length ties by
lexical graph-node ID. Traversal is cycle-safe and bounded at exactly d. Distance
3 is not enabled/disabled after observing outcomes; resource failures are
reported under the fixed graph limits instead.

## 7. Specificity and frozen ranking features

Let S be the resolved changed production seeds. Let `fan_in(s)` be the number of
**distinct pre-existing base test definitions** with a resolved path of length
1–3 to s. Compute it over all base tests, not only V2 candidates or accepted
patches. Parameter instances do not multiply a test-function family.

Freeze the oracle-blind specificity weight:

`weight(s) = 1 / (1 + fan_in(s))`.

High fan-in therefore receives lower weight. Compute fan-in once at depth 3 for
every depth configuration, so changing d does not redefine symbol specificity.
For configuration d:

`specificity_score(t,d) = Σ weight(s) / distance(t,s)`

over resolved seeds reachable from t within d. An unreachable test has score 0;
an unresolvable graph/test identity is missing, not evidence of distance zero.

Rank lexicographically, with these features in this exact order:

1. Descending specificity score.
2. Descending count of changed seeds called directly (distance 1).
3. Ascending minimum distance to a changed seed; unreachable follows reachable.
4. Descending same-module indicator (test module contains a changed definition).
5. Descending same-package indicator (same immediate dotted module parent).
6. For C, original stored V2 position; for B, lexical test ID.
7. Lexical test ID as the final deterministic tie-break.

No outcome, gold string, benchmark test list, historical timeout identity, or
post-hoc case label is a feature. Historical tier membership is not a feature
because it was not serialized. No learned coefficients or fitted thresholds.

## 8. A, B, C and fixed budgets

Budgets are **K ∈ {25, 50, 100, 250, 500}**, all reported separately. Selection
under a budget takes at most K tests; never pad from the oracle or another
strategy. Also report each strategy's unbudgeted candidate count.

- **A CURRENT_V2:** exact historical stored union and order, unchanged. Report
  its full set and original-order prefixes at every K, on the 19-task cohort.
- **B CALLGRAPH_ONLY:** resolved reachable pre-existing tests within d, ranked
  as above, at every K and unbudgeted. No filename fallback. Empty reachability
  and missing graph/source/patch are separate outcomes.
- **C CALLGRAPH_RANKED_V2:** rank the exact stored V2 union using the frozen
  features; retain unreachable candidates after reachable ones, preserving
  historical order on remaining ties. Apply every K. No new test may enter C.

Compare like budgets on the common-evaluable subset of the fixed 19 tasks,
reporting all unavailable rows and actual denominators. Do not call selection
size a runtime measurement. B's broader reconstructable-patch cohort is a
separate new offline analysis, with confirmed and exploratory provenance split.

## 9. Bounded per-test provenance

Freeze this cap before evaluation: per `(instance, strategy B/C, d)`, store full
paths for the **top 25 ranked tests only**, at most **three seed paths per test**,
one lexically deterministic shortest path per seed. Budgets share these rows;
do not duplicate full paths for every K. Each path has at most three call edges.

For at most 83 B tasks plus 19 C tasks, the upper bound is
`(83 + 19) × 3 depths × 25 tests × 3 paths = 22,950` full-path rows.

`per_test_provenance.csv` records changed seed, test ID, rank, path, distance,
selection reason, uncertainty flags, source identity, and the applicable budgets
for those rows. For the rest, emit aggregate counts by task/strategy/depth,
distance bin (1/2/3/unreachable/unresolved), and selection/budget membership.
Report additional seed paths omitted by the cap. Full ranked IDs/scores may be
frozen separately without full paths; the provenance CSV must not grow with
every candidate or every tied path. Cap exclusions never alter selection.

## 10. Primary oracle-blind evaluation and its limits

Report base availability, complete/partial graph construction, parsing failures,
resolved/ambiguous/unresolved calls, changed-symbol resolution, and resource
failures with explicit task/repository denominators. Report selected-set
mean/median/p75/p90/max, ≥1,000-test counts, and matched-task size reduction and
expansion relative to A. Give direct/transitive proportions, distance
distributions, V2 retention at each K, and repository breakdowns.

Stored aggregate execution counts are context only. Do not claim that a ranked
prefix would rescue a particular timed-out test: historical per-test outcomes
are missing. Do not manufacture per-test costs from aggregate durations.

**Nothing in the primary evaluation confirms that a selected test actually
exercises the changed code.** Static reachability and ranking are proxies, not
dynamic coverage, correctness, or defect-detection measurements. This sentence
must appear in the phase-2/final report.

## 11. Phase-3 oracle-only evaluation, after a committed freeze

The separate post-hoc module must verify the design commit and frozen-selector
output hashes before reading any oracle fields. It must not import into or
provide inputs to graph construction, ranking, selection, production code, or
future tuning of this experiment. Reuse the existing diagnostic ID normalizer
and exact matching rules, with unmatched IDs listed and no fuzzy matching.

Separate official F2P tests that existed at base, tests newly added by gold,
rewritten tests, and unresolved identities. A rewritten official body is not
the same executable evidence as its old counterpart. Only exact/documented
base counterparts support the existing-at-base comparison; new gold tests are
not selector misses. P2P overlaps remain demonstrable post-hoc observations.

Inspect the requested case studies and six large-selection cases only after
outputs are frozen, without retuning. Preserve all missing-evidence limitations,
including the authoritative committed `resolved` label and separate local
`patch_apply_failed` note for pytest-7432. No recommendations to replace, rank,
add, or fall back to call graphs are made until measured results are presented.

## 12. Outputs and review gate

Phase 1: this design, README, source-availability/AST-feasibility utility,
`base_feasibility.csv`, `feasibility.json`, and `report.md`. An optional
`--base-sources` mapping supplies existing local sources; it is a research input,
not a modification of the study manifests. No source copies are checked in.

Phase 2, only after approval: graph/seed/ranking implementation and unit tests;
`per_task.csv`, bounded `per_test_provenance.csv`, `selector_summary.csv`, frozen
ranked outputs, graph diagnostics, and an oracle-blind report. Phase 3 adds the
isolated post-hoc module and report after its own approval.

**Current stop:** present phase-1 design and unavailable-source evidence for
review. Leave all new call-graph files uncommitted. Commit this design only when
the user asks, and never run phase 3 before that commit exists.
