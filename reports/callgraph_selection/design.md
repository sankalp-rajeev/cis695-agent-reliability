# Offline call-graph selection experiment — registered design and pending addenda

**Phase 1b accepted; selector execution remains gated.** The original design
was registered in `05bdd11`. The omission amendment and secondary-variant
specification were approved on **2026-10-21** and committed in `9a58037`.
Amendment 2 and the success-criteria/extended-stratum appendices below are
**uncommitted drafts for user review**, not implemented rules or measured
selector results. The user commits design changes; this agent does not commit.
Earlier source/patch availability findings in sections 3–4 are historical; the
current artifact inventory below records the accepted graph state and verified
export. No rebuild, changed-symbol rerun, selector or oracle evaluation occurs
in this drafting step. Phase 2-lite requires the user's separate go after the
four-graph rebuild/all-83 resolution review; phase 3 retains its separate gate.

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

**Current stop:** show the pending design diff and artifact-only eligibility
inventory, then stop. Do not commit, rebuild graphs, rerun changed-symbol
resolution, run selectors or read oracle data in this drafting step. After the
user commits the pending addenda, the next authorized execution is limited to
the four SymPy rebuilds and all-83 changed-symbol resolution, followed by review.
Phase 2-lite still waits for the user's separate go; phase 3 remains separately
authorized after the required freeze.

<!-- amendment-2026-10-21-draft -->

## Amendment — 2026-10-21 — file-level AST-budget omissions

**APPROVED 2026-10-21. NOT IMPLEMENTED.** This specification was committed in
`9a58037`; approval does not mean the four graphs have been rebuilt. Amendment 2
below is a pending accounting clarification and must be committed by the user
before execution resumes. Accepted phase-1b artifacts remain unchanged. No
selector or oracle execution is authorized at the present drafting stop.

**Observed reason, without oracle information.** Four verified SymPy base
snapshots cross the cumulative 5,000,000 inspected-AST-node limit. The existing
exception is handled outside the file loop, so the entire graph stops before
call resolution. The crossing file is not necessarily large or invalid; earlier
files already consumed most of the allowance. The exact tasks/files/counters
are documented in `sympy_limit_stops.csv` and `report.md`, using AST-only counter
replay of archived base sources. No oracle, gold patch, official test list,
repair correctness label, or selector outcome informs this proposal.

**Approved specification: largest-first whole-file omissions.** Before constructing
any graph, preflight every eligible regular base `.py` file with `ast.parse`
and count the entries from `ast.walk`, including context/operator entries as
in the current counter. Inspect files in ascending repository-relative POSIX
path order. Existing syntax/encoding failures, Python links and files over the
2 MiB blob limit retain their existing explicit omission/failure handling.

Let T be the sum of AST counts of all successfully preflighted eligible files.
If T exceeds **5,000,000 retained AST nodes**, sort those files by
`(-preflight_ast_nodes, repository_relative_posix_path)` and omit whole files
in that order until the retained sum is <= 5,000,000. Ties use ascending path;
stop at the first fitting sum, including exact equality. Do not refill an
omitted file or retain a prefix of it. If T already fits, omit no file for
this quota. This replaces the lexical admission/skip rule completely; lexical
order determines inspection and ties, never preferential file retention.

The preflight still has the **10,000,000 inspected-AST-node hard ceiling**,
including nodes in files later omitted. Stop before inspecting node 10,000,001;
if a complete inventory cannot be obtained within that ceiling, mark preflight
`resource_limited`, list the uncounted/current files and do not claim a global
largest-first omission set from the partial inventory. A complete inventory of
exactly 10,000,000 nodes is permitted. Keep the 600-second task wall ceiling and
all other fixed limits. Preflight and graph construction share the task wall
budget; re-reading a preflighted AST must not hide inspection work or reset the
counter. Record whether trees are retained/reused or revisited; every additional
AST-node inspection counts against the same ceiling. A budget-only dry run
makes no claim that graph construction will fit the remaining work/time budget.

Omission ranking uses only base AST size and path. Test status, candidate patch,
changed symbols/packages, oracle information and official test identities never
change which files are omitted. Only after fixing omission lists, annotate test
files using the existing `is_test_file` and package overlap using hash-verified
frozen candidates and the existing patch parser/symbol extractor. Same package
means the exact immediate dotted module parent under the existing `src`/`lib`
layout convention; no ancestor-package or fuzzy matching. Missing/unverified
patches or unestablished changed symbols make overlap unavailable, never false.

Any AST-quota omission makes the graph **partial**. Record each omitted path,
byte/hash identity, full AST count, removal rank, retained total before/after,
reason `largest_first_retained_ast_quota`, test-file status, and separate package
overlap evidence. References and changed symbols in omitted files remain
unavailable/uncertain with an explicit file-omission reason. Never infer coverage
or correctness from file size, omission, retention, or package proximity.

**Approved budget change; accounting clarification pending in Amendment 2.** Today's 5,000,000 limit measures
all *inspected* nodes; simply moving its catch inside the loop would immediately
stop again at the next file. This proposal therefore separates retained graph
cost from inspection work. Freeze a proposed **10,000,000 inspected-AST-node
hard ceiling per task**, including all omitted/preflighted work, alongside the
5,000,000 retained quota. Reaching the inspected ceiling still ends the task as
`resource_limited`, records the current path/counters, and does not retry. Stop
counting a file when the hard work ceiling is reached; do not fully walk it for
a diagnostic count after that ceiling. All other limits, including the 2 MiB
blob limit and 600-second wall limit, remain unchanged. This is a proposed
change to AST accounting and its work budget, not a claim of the old policy's
same resource bound. The round two-times work ceiling is a bounded proposal,
not a value tuned to outcomes or a promise that all four builds will finish.

**Eligibility and preservation.** Partial graphs remain ineligible for the
primary comparison. Preserve all accepted phase-1b graphs/statuses and report any
approved future run as a separately versioned diagnostic with new code/input
hashes. Do not overwrite the frozen study or reinterpret current resource
stops as successes. Keep all distances, selection budgets, ranking features,
cohorts and oracle separation unchanged. The specification is approved; the
current execution gate still requires the user's commit of pending Amendment 2
before any rebuild, followed by review before selectors.

## Secondary traversal variant — 2026-10-21

**APPROVED 2026-10-21. NOT IMPLEMENTED.** This specification was committed in
`9a58037`. Approval of the specification does not authorize selector execution
at the current stop. Freeze the pending success criteria before any selector
outputs or post-hoc oracle evaluation. The primary design remains
`PRIMARY_RESOLVED_ONLY`, following resolved call edges only. A separately named
`SECONDARY_RESOLVED_PLUS_AMBIGUOUS` also follows each recorded candidate target
of an ambiguous call site. Sites with no candidate targets and unresolved sites
add no traversable edges. Neither variant may invent targets or change the
existing graph resolution classifications or resolved changed-seed mapping.

Both variants use d in {1,2,3}, K in {25,50,100,250,500}, the same populations,
base graphs, candidate bytes, eligibility rules and deterministic tie-breaks.
Each candidate call edge counts as one hop, with no fitted discount. Compute
fan-in at depth 3, distances, direct-seed counts and specificity using each
variant's fixed traversal edge set and the existing formulas/ranking order.
All other ranking features are unchanged. Keep the shortest path per test/seed,
break equal-length ties by lexical node IDs, and report all depths/budgets.
A vs B vs C remains limited to the 19 stored-selection tasks; broader B remains
a separate offline analysis with confirmed and local provenance split.

Every secondary path using ambiguity must record `uses_ambiguous_edge=true`,
the number and positions of ambiguous hops, original call-site IDs/locations,
recorded candidate targets and uncertainty reasons. Preserve edge-level resolved
versus ambiguous status. Also record whether a test is reachable using resolved
edges alone at the same depth; an ambiguous chosen shortest path alone does not
prove the test requires ambiguity. Aggregate ambiguity-use and resolved-only
reachability for provenance rows beyond the existing top-test/path cap.

Store `edge_variant` in every comparison/provenance output. Report secondary
results in separate tables and paired, common-evaluable comparisons with the
primary; never pool or relabel them as primary. Apply the existing cap of top
25 tests, <=3 seed paths/test and <=3 hops/path separately per variant, sharing
paths across K. The full-path upper bound becomes 22,950 per variant and 45,900
overall; emit aggregates for the rest. Partial graphs remain ineligible for the
primary comparison; this secondary does not relax graph eligibility either.

Freeze these choices before results. Do not select a depth/budget, change edge
weights, prune candidates or choose between variants using outcomes, oracle
fields, official tests or case-study hindsight. Phase-3 oracle analysis remains
separate and requires the existing approval/freeze gate. Ambiguous reachability
is a static possibility, not evidence that a selected test exercises changed
code. No production verifier or policy behavior changes are proposed here.


## Amendment 2 — 2026-10-21 — preflight node accounting and indexing visits

**DRAFT FOR USER COMMIT. NOT IMPLEMENTED.** This amendment supersedes only the
additional-inspection accounting language in the largest-first amendment. Do
not rebuild any graph or rerun changed-symbol resolution before the user commits
this amendment. No phase-2-lite execution is authorized by this draft.

**Rule.** Count each AST node occurrence once toward the **10,000,000-node
ceiling**, during the complete preflight. Use the existing AST-count convention
(`ast.walk` entries, including context/operator occurrences); shared CPython
operator/context objects still count at each tree occurrence. This is a count
of preflighted AST input, not a cumulative count of later traversal visits.
Files later omitted still contribute their full preflight cost. If preflight
cannot finish within this ceiling, preserve the existing `resource_limited`
hard stop; do not infer a global largest-first ranking from a prefix.

Use preflighted ASTs for indexing the retained files. **Report indexing visits
separately** from preflight node counts, together with the retained AST-node
sum, omitted paths, reuse/reparse status and timing. Reusing a retained tree for
indexing does not charge its nodes a second time against the preflight ceiling.
The indexing input remains bounded by the **5,000,000 retained-AST-node quota**;
that quota is not an extra allowance to retain additional files. Keep the
**600-second per-task wall limit unchanged**, shared by preflight, omission,
indexing and call resolution. Do not reset its timer between stages. This
amendment does not permit an unreported rescan, hidden counter reset, increase
in retained input, or a change to any other graph cap.

**Reason, without outcomes or oracle information.** Literal double-counting of
a full indexing traversal makes all four stopped SymPy tasks arithmetically
unable to finish within the previous cumulative 10,000,000-inspection ceiling:
preflight uses 6.96–9.55 million AST entries and the retained indexing input is
4.76–4.98 million entries (up to the fixed five-million retained quota). The
recorded preflight plus retained-input sums are:

| Task | Preflight nodes | Retained AST nodes | Double-counted total |
|---|---:|---:|---:|
| sympy-13480 | 6,958,393 | 4,762,362 | 11,720,755 |
| sympy-14711 | 7,106,521 | 4,910,490 | 12,017,011 |
| sympy-17318 | 9,260,685 | 4,961,401 | 14,222,086 |
| sympy-19783 | 9,551,134 | 4,976,923 | 14,528,057 |

These are AST-input accounting sums, not measured implementation-specific
indexer-visit totals or predictions of graph-build runtime. They come only from
the verified base archives and deterministic largest-first preflight. No repair
outcome, oracle information, gold patch, official test list or selector result
informs this amendment. Separating input size from indexing visits makes both
resource measures explicit; it does not establish dynamic coverage or success.

All other largest-first omission rules, partial-graph labels/eligibility,
primary resolved-only traversal, separately reported ambiguous-edge secondary,
cohorts, distances, budgets, ranking formulas, provenance caps and oracle gates
remain unchanged. After the user commits this amendment, perform only the four
SymPy rebuilds and the all-83 changed-symbol resolution already requested, then
stop for review. Phase 2-lite still requires the user's separate go.


## Pre-registered success criteria — 2026-10-21

**DRAFT FOR USER COMMIT. NOT EVALUATED.** Correction to the record: commit
`9a58037` has the message "Pre-register SymPy largest-first omission, secondary
variant and success criteria", but its `design.md` contains no explicit success
criteria. The C1–C3 criteria are introduced in this appendix now, after stored
source/graph feasibility and AST-size dry runs, but before any selector outputs
or post-hoc oracle evaluation. Do not backdate them to that commit. Commit this
appendix before running phase 2-lite; no outcome or oracle fields inform it.

`git show --stat 9a58037` confirms that commit touched only
`reports/callgraph_selection/design.md`: one file, 126 insertions. Its message
does not establish that success criteria were present; the file content did not
contain C1–C3 or a success-criteria appendix.

**Primary eligibility:** a complete graph, a confirmed final-study candidate
patch, and at least one resolved changed production seed. Confirm candidate
bytes against the export manifest and use its `csv_source_run` as final-study
provenance. Resource-limited, missing, partial, unconfirmed-patch and zero-resolved-
seed tasks are unavailable for primary evaluation, not empty selections. Keep
all fixed-cohort rows and reasons visible; do not replace an ineligible task.

The fixed six large cases are django-13212, astropy-13977, django-12209,
django-13297, django-14140 and django-14631 (full IDs in the inventory below).
Only PRIMARY/resolved-only results decide the criteria. Interpret d<=2 as the
fixed radius-2 configuration, and d<=3 as the fixed radius-3 configuration;
do not choose a favorable depth after observing results.

- **C1:** for **at least 5 of those fixed 6 tasks**, B PRIMARY with distance
  <=2 returns a non-empty **unbudgeted** set containing **at most 250** tests.
  Apply no top-K truncation to make the count fit. An ineligible task remains
  one of the six fixed rows and cannot count toward the five successes.
- **C2:** for **at least 5 of those fixed 6 tasks**, C PRIMARY's **top 100** at
  distance configuration 2 contains **at least one stored V2 candidate** with
  a resolved-only path of length <=2 to a resolved changed seed. Use the exact
  stored V2 union and the existing ID-normalization/matching rules; no extra
  candidate or fuzzy match may supply a hit. If fewer than 100 candidates
  exist, inspect all returned candidates. Missing mappings remain unavailable,
  never manufactured matches, and cannot count toward the five successes.
- **C3:** for **at least half of the eligible tasks** in the fixed **13-task
  NOT_AVAILABLE cohort**, B PRIMARY with distance <=3 selects at least one
  pre-existing base test. Freeze the eligible denominator after the approved
  four-graph rebuild and all-83 patch/seed resolution, before running selectors.
  For n eligible tasks the threshold is ceil(n/2). If n=0, C3 is NOT_EVALUABLE,
  not a vacuous pass. Report every excluded task and its reason.

**Pre-registered decision map.** Define rank/filter support as C1 AND C2, and
fallback support as C3. A single C1 or C2 pass is insufficient for rank/filter
support. This makes partial combinations explicit without choosing afterward:

| C1 AND C2 | C3 | Supported use from these criteria |
|---|---|---|
| pass | not passed | Rank/filter layer over Tier 2 |
| not passed | pass | Fallback only |
| pass | pass | Both rank/filter layer over Tier 2 and fallback |
| not passed | not passed | Do not use on this experiment's evidence |

Retain FAIL versus NOT_EVALUABLE in the underlying results; "not passed" in the
decision table includes either and does not turn missing evidence into measured
failure. The secondary ambiguous-edge variant is reported separately and never
decides C1/C2/C3 pass/fail or rescues a primary criterion. The extended partial
stratum below also never contributes to primary thresholds or recommendations.

**"Replace Tier 2" cannot be supported by this experiment alone.** C uses the
stored V2 union; tier membership was not serialized. Static reachability and
these criteria do not establish dynamic execution, correctness, regression
sensitivity or test-runtime savings. Nothing in the primary evaluation confirms
that a selected test exercises the changed code. No primary/secondary result is
evaluated during this drafting step.

## Artifact-only graph inventory for the success cohorts — 2026-10-21

This is the **current stored graph state**, not a forecast under an unexecuted
amendment. Source: each task's `graphs/<instance_id>/diagnostics.json`, with
baseline counters in `base_feasibility.csv`. NOT_AVAILABLE membership projects
only identity, source run and `v2_outcome` from the committed V2 diagnostic CSV;
no oracle columns are used. Graph completeness describes construction coverage,
not proof that every call resolves or a test exercises changed code.

All 83 exported final-study patch hashes and `csv_source_run` identities have
been verified (`patch_export_verification_83.json`); the four alternative-run
ambiguity notes remain recorded. Fresh all-83 changed-seed resolution has not
run. Therefore completeness alone does not establish current primary eligibility
or the final C3 denominator. Historical seed counts are not substituted for that
pending resolution against the verified export.

### Six large cases: five complete, one partial

| Task | Stored graph state | Reason / evidence |
|---|---|---|
| [django__django-13212](graphs/django__django-13212/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [astropy__astropy-13977](graphs/astropy__astropy-13977/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [django__django-12209](graphs/django__django-12209/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [django__django-13297](graphs/django__django-13297/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [django__django-14140](graphs/django__django-14140/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [django__django-14631](graphs/django__django-14631/diagnostics.json) | partial | `tests/test_runner_apps/tagged/tests_syntax_error.py`: SyntaxError, line 11 (invalid decimal literal). |

The five complete graphs satisfy the graph component of primary eligibility.
Django-14631 cannot contribute a primary success while partial; its reason is
permitted in the proposed extended stratum, subject to the same confirmed-patch
and resolved-seed requirements. C1 and C2 still require five successes among
the original six; do not silently shrink that fixed cohort.

### Thirteen NOT_AVAILABLE cases: eight complete, one partial, four resource-limited

| Task | Stored graph state | Reason / evidence |
|---|---|---|
| [astropy__astropy-14365](graphs/astropy__astropy-14365/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [astropy__astropy-14508](graphs/astropy__astropy-14508/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [matplotlib__matplotlib-14623](graphs/matplotlib__matplotlib-14623/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [matplotlib__matplotlib-25287](graphs/matplotlib__matplotlib-25287/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [astropy__astropy-13977](graphs/astropy__astropy-13977/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [matplotlib__matplotlib-24177](graphs/matplotlib__matplotlib-24177/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [pydata__xarray-4966](graphs/pydata__xarray-4966/diagnostics.json) | complete | No recorded parse/omission/resource failure. |
| [pylint-dev__pylint-6903](graphs/pylint-dev__pylint-6903/diagnostics.json) | partial | 10 syntax/encoding parse failures plus 2 Python symlink omissions; full paths below. Not eligible for the proposed extended stratum. |
| [sympy__sympy-13480](graphs/sympy__sympy-13480/diagnostics.json) | resource_limited | Original cumulative 5,000,000 AST-node cap; graph stopped before call resolution. Largest-first rebuild has not run. |
| [sympy__sympy-14711](graphs/sympy__sympy-14711/diagnostics.json) | resource_limited | Original cumulative 5,000,000 AST-node cap; graph stopped before call resolution. Largest-first rebuild has not run. |
| [sympy__sympy-17318](graphs/sympy__sympy-17318/diagnostics.json) | resource_limited | Original cumulative 5,000,000 AST-node cap; graph stopped before call resolution. Largest-first rebuild has not run. |
| [sympy__sympy-19783](graphs/sympy__sympy-19783/diagnostics.json) | resource_limited | Original cumulative 5,000,000 AST-node cap; graph stopped before call resolution. Largest-first rebuild has not run. |
| [sympy__sympy-24562](graphs/sympy__sympy-24562/diagnostics.json) | complete | No recorded parse/omission/resource failure. |

Astropy-13977 appears in both cohorts; there are **18 distinct tasks** across the
two tables. Resource-limited is a third state, not relabeled partial. The four
SymPy preflights predict omission sets but are not rebuilt graphs. The eight
complete NOT_AVAILABLE graphs are only a graph-complete pool; the final C3
eligible denominator may be smaller after confirmed-patch/seed checks.

Pylint-6903's exact stored partial reasons are:

| File | Reason | Line |
|---|---|---:|
| `tests/functional/s/star/star_needs_assignment_target_py37.py` | SyntaxError | 15 |
| `tests/functional/s/syntax/syntax_error.py` | SyntaxError | 1 |
| `tests/functional/s/syntax/syntax_error_jython.py` | SyntaxError | 1 |
| `tests/functional/t/tokenize_error.py` | SyntaxError | 6 |
| `tests/functional/t/tokenize_error_jython.py` | SyntaxError | 7 |
| `tests/functional/u/unknown_encoding_jython.py` | SyntaxError | 0 |
| `tests/input/func_w0122_py_30.py` | SyntaxError | 5 |
| `tests/regrtest_data/bad_package/__init__.py` | SyntaxError | 2 |
| `tests/regrtest_data/descriptor_crash.py` | SyntaxError | 20 |
| `tests/regrtest_data/syntax_error.py` | SyntaxError | 1 |
| `tests/functional/s/symlink/_binding/__init__.py` | archive_link_or_special_file_not_followed |  |
| `tests/functional/s/symlink/_binding/symlink_module.py` | archive_link_or_special_file_not_followed |  |

The two symlink omissions independently disqualify pylint-6903 from an extended
stratum restricted to unparseable-file and largest-first reasons. All reasons
remain visible; do not drop the disqualifying reasons from eligibility checks.

## Extended partial-graph stratum — 2026-10-21

**DRAFT FOR USER COMMIT. SEPARATE, DESCRIPTIVE STRATUM.** Include a task only if:

1. Its finished graph is explicitly partial, not resource-limited or missing.
2. Every incompleteness reason is either a file that failed `ast.parse`
   (SyntaxError/encoding, UnicodeError, ValueError or RecursionError at parsing)
   or a whole-file `largest_first_retained_ast_quota` omission under the approved
   rule. The full reason/path list is required; missing reasons do not qualify.
3. Its final-study candidate patch is confirmed by export SHA-256 and CSV source
   run, and at least one changed production seed resolves in retained base code.

Exclude partials with symlink/special-file omissions, over-size blob omissions,
other resource/failure reasons or incomplete provenance. Keep symbols in omitted
or unparseable files unavailable with their reasons; do not infer them resolved.
Current resource-limited SymPy artifacts do not qualify. A future successfully
finished, largest-first partial graph may qualify only after its actual final
reasons and seed mapping are checked. Do not forecast eligibility from preflight.

This stratum contains **qualified partial graphs only**; complete graphs remain
in PRIMARY_COMPLETE. Report EXTENDED_PARTIAL separately with task IDs, all
omitted/unparseable paths, confirmed-patch and resolved-seed counts, selection
metrics and its own denominators. Separate primary-edge and secondary-edge
results within each stratum. Never pool its rows, numerator or denominator with
the complete-graph primary, use it to meet C1/C2/C3, or substitute it for a missing
primary task. Any parallel descriptive criterion counts are labeled extended,
not primary pass/fail. Freeze strata after approved rebuild/seed resolution and
before selector execution. No result-dependent reclassification or tuning.
