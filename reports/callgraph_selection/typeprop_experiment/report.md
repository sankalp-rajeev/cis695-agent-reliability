# Lightweight receiver type propagation: static call-graph experiment

2026-11-02. Local branch `experiment/callgraph-typeprop`; starting commit `0c0c87fda86cf0a2f7c33866020325856e7303de`. This is a new offline experiment, not a revision of the frozen capstone results.

## 1. Question

Can lightweight local and caller-to-parameter type propagation improve static call resolution and reachability from pre-existing tests to changed production symbols? The primary evidence is changed-symbol and test-selection impact; additional graph edges alone are insufficient.

## 2. Baseline

The frozen Amendment 2 overlay uses 79 original `Graph` outputs and four largest-first `AmendedGraph` SymPy outputs, pinned by `amendment2_72ad21b/graph_manifest.json`. Its 83 task snapshots span 11 represented repositories. All 419 manifest-listed graph artifacts were hash-verified before and after evaluation. Each enhanced build reproduced every baseline node and call edge exactly before adding type evidence. Baseline implementations, the original design, Phase 2 outputs and production code are unchanged.

The overlay has 56 complete, 27 partial and zero resource-limited graphs. The older pre-Amendment inventory (56 complete, 23 partial, four limited) is historical context and is not mixed into the comparison denominator. The original all-task named-symbol baseline is 147 resolved / 21 ambiguous / 19 unresolved, totaling 187. Source archives, base commits and frozen candidate patches retain their existing SHA-256 checks.

## 3. Method

`typeprop_graph.py` wraps the existing AST indexer and Graph/AmendedGraph builders. Nodes, lexical bindings and existing import resolution are reused. Single, unconditional assignments within a function or method may supply an exact constructor class; arbitrary factory returns, assignment aliases and module-level instance assignments are excluded. A local assignment must finish before the call on an earlier source line. Direct constructor arguments are supported.

Only calls resolved by the frozen baseline supply positive argument-to-parameter constraints. Required positional, positional-only and keyword-only parameters use explicit argument mapping. Defaults, variadics, expansions and invalid mappings remain unknown. Newly inferred receiver calls are deliberately not additional propagation sources. Parameter-to-parameter transfer uses a synchronous fixed point, bounded at 64 rounds and 16 possible classes per fact. Unknown evidence taints the result; overflow and non-convergence fail closed. Recursion and mutual recursion terminate. All 83 observed fixed points converged within six rounds. No benchmark module is imported or executed, and no external type engine or annotation inference is used.

Facts retain constructor locations or incoming call ordinals/actual arguments. Edge provenance distinguishes the existing resolver, local constructors, caller parameters and transitive caller parameters; enhanced edges also retain baseline status, reason and targets. A transitive attribution means transitive evidence participates, even when another direct witness also exists. Raw facts and enhanced edges are regenerable local artifacts under `task_artifacts/`.

## 4. Safety / conservative rules

- Preserve every previously resolved edge and target list; retain the baseline classification separately for newly refined edges. Several possible receiver classes remain ambiguous. Known and unknown callers together do not become uniquely resolved.
- Reject decorated/conditional/inherited classes, custom `__new__`, `__getattr__`, `__getattribute__`, detected reflective class members, uncertain class imports, star-import boundaries and redirected/mutated bindings.
- Preserve pre-expansion binding multiplicity: deduplicated unknown bindings must not hide reassignment or deletion. Global/nonlocal mutation and unsupported-scope stores taint their owners. Callable value escapes, including references inside unsupported scopes, block confident parameter facts.
- Preserve baseline self/cls behavior, but do not propagate their defining-class metadata as an exact instance type: subclasses may override methods.
- Detected attribute writes block new edges with that name. New private method names beginning with `__` and not ending in `__` remain unresolved because Python name mangling is not modeled.
- Preserve parse failures, omissions, all graph resource caps, unsupported lambda/comprehension/annotation call classifications, selector eligibility, depths, ranking, identities and budgets.

This is an observed-static-caller model, not an open-world soundness proof. Unseen external calls, reflection through dictionaries, mutation in unmodeled callees and arbitrary monkey-patching remain limitations. A unique static target does not establish successful runtime invocation, dynamic coverage or correctness.

## 5. Synthetic validation

**104 focused and existing graph checks passed.** Coverage includes constructor/import aliases, direct constructor arguments, keyword mapping, set-valued callers, unknown contamination, repeated stores/deletion, recursion, transitive transfer, defaults/expansions, dynamic/inherited classes, resource stops, self handling, private-name mangling, escaped lambda callables and nonlocal/comprehension mutation. Fixture source is parsed only. Exact output: `focused_tests.txt`.

The broader clean-baseline unit suite produced **891 passed, 6 skipped, 3 failed**. Those failures concern the reused editable-venv path, absent worktree-local `.venv/bin/python`, and a missing ignored baseline `.patch` fixture. `project_unit_tests.txt` retains exact failures and `validation.json` gives their test IDs. No unrelated verifier/V2 fix was attempted.

## 6. Corpus-wide results

All **83/83** tasks were compared: 56 complete / 27 partial / 0 resource-limited. There are **71** parse failures across task snapshots, unchanged; partial graphs remain partial. The builds account for **132,918,838** inspected/preflight AST entries and **8,691,718** call sites. These counts sum task snapshots, including repeated repository versions; they are not unique-source counts.

| Call-site status | Baseline | Enhanced | Change |
|---|---:|---:|---:|
| resolved | 1,634,110 | 1,659,985 | +25,875 |
| ambiguous | 672,968 | 673,095 | +127 |
| unresolved | 6,384,640 | 6,358,638 | -26,002 |

| Transition | Call sites |
|---|---:|
| unresolved -> resolved | 25,875 |
| unresolved -> ambiguous | 127 |
| ambiguous -> resolved | 0 |
| resolved -> ambiguous | 0 |
| resolved -> unresolved | 0 |
| ambiguous -> unresolved | 0 |

New resolved call sites: **25,875**; local constructor **25,806**, caller parameter **41**, transitive caller parameter **28**. The caller propagation contribution is **69** sites. Total resolution rises by **0.298 percentage points**; this is not a precision or coverage measurement.

| Repository | Tasks | Baseline R / A / U | Enhanced R / A / U | New resolved | Selection tasks changed |
|---|---:|---|---|---:|---:|
| astropy/astropy | 4 | 49,916 / 18,809 / 294,480 | 50,182 / 18,885 / 294,138 | 266 | 0 |
| django/django | 31 | 703,541 / 337,649 / 3,558,643 | 725,750 / 337,649 / 3,536,434 | 22,209 | 2 |
| matplotlib/matplotlib | 15 | 167,056 / 87,403 / 755,413 | 168,196 / 87,450 / 754,226 | 1,140 | 0 |
| mwaskom/seaborn | 1 | 2,223 / 1,798 / 15,443 | 2,272 / 1,798 / 15,394 | 49 | 0 |
| pallets/flask | 1 | 613 / 112 / 3,208 | 621 / 112 / 3,200 | 8 | 0 |
| pydata/xarray | 5 | 59,736 / 7,738 / 123,593 | 59,821 / 7,738 / 123,508 | 85 | 0 |
| pylint-dev/pylint | 5 | 13,852 / 5,152 / 65,188 | 13,966 / 5,152 / 65,074 | 114 | 0 |
| pytest-dev/pytest | 7 | 16,225 / 6,536 / 100,949 | 16,940 / 6,540 / 100,230 | 715 | 0 |
| scikit-learn/scikit-learn | 5 | 69,504 / 4,742 / 268,501 | 69,563 / 4,742 / 268,442 | 59 | 0 |
| sphinx-doc/sphinx | 4 | 24,474 / 5,929 / 82,359 | 24,881 / 5,929 / 81,952 | 407 | 0 |
| sympy/sympy | 5 | 526,970 / 197,100 / 1,116,863 | 527,793 / 197,100 / 1,116,040 | 823 | 0 |

`provenance_counts.csv`, `callsite_changes.csv`, `unresolved_reasons_before_after.csv` and `task_summary.csv` retain the detailed inventory. Zero resolved edges became ambiguous or unresolved; independently streamed target-list checks also confirm that every one of the 1,634,110 previously resolved target lists is identical.

## 7. Changed-symbol impact

Frozen candidate patches and the existing `changed_symbols` pipeline were reused for the exact same 187 extracted names. Both graphs yield **147 resolved / 21 ambiguous / 19 unresolved**. There are **zero status changes, zero gains and zero losses**; `changed_symbol_changes.csv` therefore contains its header only. Definition nodes are unchanged, and this extractor matches file/simple-name identity rather than using call reachability, so extra call edges cannot fix that particular lookup.

The separate reachability analysis finds **three affected tasks**. In the qualified partial graph for `pylint-dev__pylint-4970`, **16 existing test definitions** gain resolved-only paths to **two changed methods**, `Similar.run` and `Similar._compute_sims`: 32 new test/seed pairs. Their fan-in rises from 0 to 16 in each variant. All 16 tests were already reachable through the changed `Similar` class constructor; the overall test union remains 17 and its order is unchanged. This is an improvement in per-seed static evidence despite unchanged emitted selections. It occurs in EXTENDED_PARTIAL, not the complete-graph primary stratum. The changed `CreateModel` seed also gains six tests in each of two Django snapshots, under the ambiguous-edge variant only. `changed_seed_reachability.csv` separates all six task/seed/variant rows, and `changed_seed_reachability_paths.csv` retains all 76 new paths without pooling variants. `specificity_changes.csv` records the weight changes.

## 8. Test-selection impact

The existing Phase 2 `Identities`, `Traversal`, `features` and `rank_candidates` functions were reused for both graphs. Baseline selected counts match the frozen Phase 2 table for all **3,528** computed B/C configurations. The 19 stored V2 unions, eligibility strata, depths 1/2/3, budgets 25/50/100/250/500/ALL, specificity formula, identity mapping and ranking are unchanged. Missing/zero-seed configurations retain their frozen eligibility rather than becoming zero selections.

**Resolved-only B/C selections change on zero tasks. C changes on zero tasks at every budget and depth**, so all historical V2 prefix overlaps remain unchanged. Under `SECONDARY_RESOLVED_PLUS_AMBIGUOUS`, B at depth 3 changes on exactly two tasks:

| Task | Frozen stratum | Before / after | Added / removed |
|---|---|---|---|
| django__django-13786 | PRIMARY_COMPLETE | 0 / 6 | 6 / 0 |
| django__django-15499 | EXTENDED_PARTIAL | 0 / 6 | 6 / 0 |

These are the same six migration test IDs in two snapshots (12 task/test additions, six distinct ID strings). Each of the six budget configurations changes on each task: 12 changed configurations overall. No tests are removed. The path is test → newly resolved `MigrationAutodetector._detect_changes` → existing `generate_created_models` → ambiguous `CreateModel`. The retained ambiguity explains why resolved-only selection stays empty. `selection_changes.csv` lists every changed set, `selection_paths.csv` lists the source callsites and paths, and `specificity_changes.csv` gives fan-in/weight differences. Added tests have a plausible static connection; no execution, cost or defect-detection advantage is established.

Nothing in the primary evaluation confirms that a selected test exercises the changed code.

## 9. Manual edge audit

The deterministic sample selects one minimum-SHA256 newly resolved callsite per repository/provenance stratum, across all task snapshots. Final sample: **15**, classified **15 SUPPORTED / 0 QUESTIONABLE / 0 INCORRECT** by source-context inspection. This is the agent’s static review, not independent human adjudication or a corpus precision estimate. `audit_candidates.json` retains site/target/constructor/caller-chain snippets, and `audit_review.json` records each decision.

| Repository / provenance | Expression | Classification | Evidence |
|---|---|---|---|
| astropy/astropy / local_constructor | `hub.stop` | SUPPORTED | hub is assigned SAMPHubServer() once before stop(); that class directly defines stop. |
| django/django / local_constructor | `project_state.clone` | SUPPORTED | project_state is assigned ProjectState() immediately before clone(); clone is defined directly on ProjectState. |
| matplotlib/matplotlib / caller_parameter | `dmap.data2grid` | SUPPORTED | The observed integrator call receives dmap from DomainMap(grid, mask); DomainMap directly defines data2grid. |
| matplotlib/matplotlib / local_constructor | `dmap.mask2grid` | SUPPORTED | dmap is assigned DomainMap(grid, mask) before mask2grid(); the direct class member matches. |
| mwaskom/seaborn / local_constructor | `a.set_view_interval` | SUPPORTED | a is constructed as PseudoAxis and its class directly defines set_view_interval. |
| pallets/flask / local_constructor | `s.dumps` | SUPPORTED | s is constructed as TaggedJSONSerializer; registering tags does not replace its directly defined dumps method in the inspected context. |
| pydata/xarray / local_constructor | `g.map_dataarray_line` | SUPPORTED | g is constructed as FacetGrid before the kind branch; map_dataarray_line is a direct class method. |
| pylint-dev/pylint / caller_parameter | `writer.write` | SUPPORTED | All seven inspected fixture callers construct DiagramWriter and pass it into _setup(writer); DiagramWriter directly defines write. |
| pylint-dev/pylint / local_constructor | `store_.register_messages_from_checker` | SUPPORTED | store_ is constructed as MessageDefinitionStore before registration; register_messages_from_checker is directly defined on that class. |
| pytest-dev/pytest / caller_parameter | `s.accept` | SUPPORTED | expression receives a direct Scanner(input) argument; Scanner directly defines accept. |
| pytest-dev/pytest / caller_parameter_transitive | `s.accept` | SUPPORTED | Scanner(input) flows through expression, expr, and_expr and not_expr, including recursive calls; the receiver member is Scanner.accept. |
| pytest-dev/pytest / local_constructor | `matcher.fnmatch_lines` | SUPPORTED | matcher is constructed as LineMatcher immediately before fnmatch_lines; the direct method definition matches. |
| scikit-learn/scikit-learn / local_constructor | `grower.split_next` | SUPPORTED | grower is constructed as TreeGrower before split_next; constructor keyword values do not change the statically known class target. |
| sphinx-doc/sphinx / local_constructor | `parser.parse` | SUPPORTED | parser is constructed as Parser immediately before parse(); Parser directly defines parse. |
| sympy/sympy / local_constructor | `O.locatenew` | SUPPORTED | O is constructed as Point before locatenew(); Point directly defines that method. |

Audit-driven corrections are preserved in `incidents.json`. Early self-derived exact types and later lambda/nonlocal boundary cases were rejected before final evaluation. A superseded full-run audit found **one incorrect private-name edge in 15 samples**; all five affected new private-name callsites across the corpus are now rejected, a regression test was added, and all 83 tasks were rerun. The final sample was selected again from the corrected output. Superseded results are not pooled with final results.

Concrete positive propagation examples include `DomainMap` passed into matplotlib’s integrator and `Scanner` passed through pytest’s expression/expr/and_expr/not_expr recursion before `Scanner.accept`. Type annotations are not used to infer these facts.

## 10. Runtime/resource cost

The final corpus’s graph-build times sum to **583.73 s**; the frozen historical builds sum to **369.18 s**. These historical timings are not a controlled overhead estimate. The inference phase itself sums to **51.73 s**; indexing, provenance and retaining the baseline for comparison add other costs. Peak observed process RSS is **3.10 GiB**.

A matched timing sample uses the lexically first task per represented repository (11 tasks), one build per variant in a fresh process, alternating variant order by repository. Baseline graph time: **36.43 s**; enhanced: **52.16 s**, **1.43×** (**43.2%** increase). Largest sampled process RSS: **1.80 GiB** baseline and **1.80 GiB** enhanced. RSS includes interpreter/extraction high-water usage and is not incremental graph allocation. One repetition supports a descriptive comparison, not a stable performance distribution. Raw measurements and sampling rules are in `runtime_sample.json` / `runtime_protocol.json`.

One superseded long-process run exited 139 with a segmentation fault after 81 saved task records. The cause is unestablished; it is not relabeled an AST-quota failure or OOM. A fresh process finished its two pending tasks. The final corrected experiment uses batches of ten tasks per Python process under the same per-task limits. All final tasks completed and all persisted callsites were independently validated. The incident remains a robustness limitation.

## 11. Failure cases

Python remains difficult: factory-return types, aliases between local instances, container-held instances, inherited dispatch, subclassed self/cls, descriptor/decorator behavior, dynamic mutation, unobserved callers, defaults/variadics and unsupported scopes limit useful evidence. Private-name mangling is excluded rather than approximated. Escaped-callable and unknown-input rejection deliberately sacrifices recall. The graph still has millions of external, dynamic or unsupported callsites; its unresolved count is not an internal-call failure rate.

The small source audit caught a real semantic mistake, and cannot guarantee the remaining new edges are all correct. Graph resolution is unique only under the explicit static model; arbitrary dictionary/reflection effects and runtime monkey-patching are not proved absent. Most gains arise from local constructors in repeated snapshots; the advisor’s interprocedural pass adds only 69 resolved sites and does not improve resolved-only changed-seed test selection in this cohort.

## 12. Recommendation

**DO NOT ADOPT** this pass into the production test selector on this evidence. Preserve it as a reproducible research prototype: the proposed propagation works on real code and bounded synthetic cases, but it gives no resolved-only selection benefit for the study’s changed seeds, leaves changed-symbol lookup unchanged, adds measurable cost and has limited audited precision evidence plus a recorded process failure. The resolved-only per-method reachability gain in a partial pylint graph and the secondary-only six-test gain in two Django snapshots are positive static evidence, but neither establishes better regression detection. Broader independent source review, stronger mutation/boundary reasoning, and practical resolved-only gains would be needed before reconsidering adoption. No production policy, ranking, budgets or frozen study classifications change.

### Artifacts and reproduction

All new committed files live in this experiment directory. Bulk per-task graphs/facts, interrupted-run bulk data, caches and logs are ignored. The original dirty worktree’s branch, HEAD, Git status and content hashes of modified/untracked files match its starting fingerprint. Existing frozen graph hashes and tracked baseline files are unchanged. `validation.json` records exact independent checks.

Use the existing dependency interpreter by absolute path (or an equivalent locked environment), clear PYTHONPATH, disable pytest plugin autoload, and pass `-B`. Run the focused command listed below. For a new full evaluation, use a disposable clean worktree based on the starting commit `0c0c87f`, with only this experiment’s source files copied from `experiment/callgraph-typeprop` and no published generated outputs. Keep the local frozen baseline graph directories, archives and patch export accessible; capture a fresh `original_worktree_snapshot.json` with `evaluate.original_state`. The evaluator refuses to silently overwrite a protocol. Start with `evaluate.py --batch-size 10`, then repeat `--resume --batch-size 10` until its `COMPLETE` record. Resume requires the exact same source-file set and hashes as the first batch. Generate reports only after evaluation is complete.

```bash
export PYTHONDONTWRITEBYTECODE=1
typeprop_python=/home/rajee/projects/cis695-agent-reliability/.venv/bin/python
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$typeprop_python" -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py reports/callgraph_selection/phase2/test_phase2.py reports/callgraph_selection/typeprop_experiment/test_typeprop.py -q -p no:cacheprovider -o addopts=
# After the complete evaluation, run:
env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/validate_experiment.py
env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/benchmark_runtime.py
env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/analyze_seed_reachability.py
# Review audit_candidates.json and record classifications in audit_review.json, then:
env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/render_report.py
```

No benchmark code, model API, Docker, oracle evaluation, network acquisition, V2 discovery rerun or Git push was performed.
