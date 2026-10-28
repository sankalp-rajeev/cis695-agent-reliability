# Phase 1b: accepted AST baseline and follow-ups

## Approved Amendment 2 rebuild — 2026-10-22

The current versioned inventory is **56 complete and 27 partial graphs**. Only the four SymPy graphs were rebuilt under the committed largest-first rule and Amendment 2: 6/6/14/17 files omitted, respectively. SHA-256 checks preserve all files of the other 79 graphs (and the four original stopped graphs).

All 83 exported final-study patches were hash-verified, with `csv_source_run` as provenance. Fresh changed-symbol resolution is **147/187 (78.6%) including newly added names**, and **147/168 (87.5%) excluding 19 inferred newly added names**; the remaining 21 are ambiguous, with no other unresolved names. See the [current report and every omitted file](amendment2_72ad21b/report.md), [per-repository rates](amendment2_72ad21b/repository_resolution.csv), [versioned feasibility table](amendment2_72ad21b/base_feasibility.csv), and [graph overlay manifest](amendment2_72ad21b/graph_manifest.json). The committed design and original baseline CSV/graphs remain unchanged. No selectors, benchmark execution or oracle analysis ran; work stops after step 3.

## Historical baseline and earlier follow-ups

Original code and artifacts were committed by the user as `f8c610d`. These follow-ups are uncommitted. No graph, selector, verifier, repair, oracle or benchmark test was rerun. Base archive code is only parsed with `ast`; there is no benchmark import/install/execution, Docker, network, gold-patch use or oracle analysis.

**83 graph attempts: 56 complete, 23 partial, four resource-limited.** Original graph outputs and `base_feasibility.csv`, `feasibility.json`, `graph_inputs.json`, `inputs.json`, and `validation.json` are preserved. The original registered design is unchanged before the appended, pending amendment; its recorded SHA-256 still pins that prefix. The amendment below it is a proposal, not an active rule.

## Synthetic tests

The seven original checks passed. Additional follow-up checks cover namespace classification and new-name denominators; the exact selected-file pytest result and command are in `synthetic_tests.txt`. The initial plain invocation failed during third-party ROS plugin startup (`ModuleNotFoundError: lark`), before collection. Clearing `PYTHONPATH` and disabling plugin autoload avoids that environment dependency. Only `reports/callgraph_selection/test_static_graph.py` was collected. Synthetic fixture source is parsed, never executed.

Final selected-file result: **13 passed in 0.04s**.

```bash
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py -q -p no:cacheprovider -o addopts=
```

## Why the four SymPy builds stopped

The frozen **5,000,000 AST-node limit is cumulative per task**, not per file. The files below crossed the remaining task allowance; they do not individually contain five million nodes. `Graph.check()` raises `ResourceLimit`, which is caught outside the whole file/build loop. Consequently, a limit in any file exits the build, skips import expansion and call resolution, and yields `resource_limited`. Syntax exceptions are instead caught inside the file loop and processing continues. This is the implemented frozen rule, not evidence of a malformed SymPy file. Checks occur every 4,096 nodes within a file and at file boundaries, explaining the small counter overshoot. The four stopped artifacts contain zero emitted edges; edge resolution was unavailable, not an observed absence of calls.

The original resource diagnostics did **not** store the stopping path. Paths and per-file counts below are **inferred by deterministic AST-counter replay** over the hash-verified base tar, with the same lexical order and Python 3.11 checkpoint schedule. Every replay exactly matches the stored stop counter and parsed-file count. This recount neither constructs/retries a graph nor changes the stored artifacts.

| Task | Crossing file | Nodes before file | Nodes in whole file | Recorded stop |
|---|---|---:|---:|---:|
| sympy__sympy-13480 | `sympy/physics/quantum/tests/test_spin.py` | 4,913,971 | 161,696 | 5,004,084 |
| sympy__sympy-14711 | `sympy/physics/quantum/tests/test_qubit.py` | 4,999,026 | 2,204 | 5,001,230 |
| sympy__sympy-17318 | `sympy/integrals/rubi/rules/miscellaneous_trig.py` | 4,907,224 | 96,193 | 5,001,433 |
| sympy__sympy-19783 | `sympy/integrals/rubi/rules/miscellaneous_trig.py` | 4,965,787 | 93,752 | 5,002,652 |

Full counters, inspected portion, file sizes, hashes and evidence status are in `sympy_limit_stops.csv`. A dated **DRAFT / NOT APPROVED / NOT APPLIED** amendment is appended to `design.md`. It proposes whole-file omission with a partial flag and explicit file list. Because today's limit counts cumulative inspected work, continuing requires an explicit budget-semantics change, not merely catching the same exception inside the loop. The draft separates a 5,000,000 retained-AST quota from a proposed 10,000,000 inspected-node work ceiling; the latter remains a task-wide hard stop. No counterfactual success or benefit is claimed, and no oracle information was used to diagnose or propose this change.

## Call-resolution boundary

Counts below partition the **79 completed full/partial graph artifacts**. All four resource-limit tasks have unavailable call classification and are omitted from this denominator. The historical resolved/ambiguous/unresolved labels are preserved; this is a separate diagnostic annotation, not resolver or verifier behavior.

1. **Internal resolved:** recorded unique first-party definition target.
2. **Internal ambiguous/unresolved:** a recorded first-party candidate, definition/receiver binding, or explicit first-party module/import namespace, with no unique resolved target.
3. **External/builtin:** unshadowed builtin name, or an explicit import/module namespace whose root is outside the base first-party module inventory.
4. **Unknown boundary:** parameters, assignments/rebinding, mixed origins, star-import/global/nonlocal uncertainty, dynamic receivers, and unsupported scopes without sufficient namespace evidence. These cannot honestly be forced into the other three buckets.

Lexical binding lookup reuses stored scopes. Explicit import origins lost by the original import expansion are recovered from AST-only base imports using the existing `Indexer` import representation. Module inventory includes unparsed Python paths and namespace parents, so a missing internal parse is not automatically called external. Internal/external refers to nominal static namespace evidence, not proven runtime provenance; internal reexports, inherited third-party methods and monkey-patching remain limitations. No fuzzy matching or second test-ID normalizer is introduced.

| Repository | Tasks | Internal resolved | Internal ambiguous/unresolved | External/builtin | Unknown boundary |
|---|---:|---:|---:|---:|---:|
| astropy/astropy | 4 | 49,916 | 49,316 | 152,051 | 111,922 |
| django/django | 31 | 703,541 | 2,139,819 | 641,136 | 1,115,337 |
| matplotlib/matplotlib | 15 | 167,056 | 161,645 | 303,457 | 377,714 |
| mwaskom/seaborn | 1 | 2,223 | 2,685 | 7,452 | 7,104 |
| pallets/flask | 1 | 613 | 321 | 1,026 | 1,973 |
| psf/requests | 0 | 0 | 0 | 0 | 0 |
| pydata/xarray | 5 | 59,736 | 13,606 | 62,733 | 54,992 |
| pylint-dev/pylint | 5 | 13,852 | 13,074 | 34,829 | 22,437 |
| pytest-dev/pytest | 7 | 16,225 | 12,959 | 25,823 | 68,703 |
| scikit-learn/scikit-learn | 5 | 69,504 | 27,364 | 136,280 | 109,599 |
| sphinx-doc/sphinx | 4 | 24,474 | 18,794 | 28,116 | 41,378 |
| sympy/sympy | 1 | 153,442 | 40,915 | 34,107 | 105,477 |
| **Total** | **79** | **1,260,582** | **2,480,498** | **1,427,010** | **2,016,636** |

Partition total: **7,184,726 recorded call sites**. Per-task and repository tables are in `call_resolution_by_task.csv` and `call_resolution_by_repository.csv`; evidence/reason counts are in `followup_summary.json`. Unknown calls are not counted as internal failures or external calls.

## Changed names: including and excluding new definitions

Frozen candidates are available for **25 tasks: 19 confirmed historical snapshots and six local candidates with unverified final-run identity**. There are 58 missing patches. Changed-name resolution is measured on 24 tasks (18 confirmed, six local); `sympy__sympy-17318` has an available candidate but no usable graph and retains blank measurements. Missing candidates are never substituted from another run.

The existing `parse_patch` and `touched_symbols` are reused on the candidate's added and removed diff sides. A name is classified newly added only when the base diagnostic establishes its absence in a parsed changed file, a definition with that name occurs on added lines, and none occurs on removed definition lines. This identifies five names below. These are unavailable base seeds, **not graph-resolution failures**. This remains the existing file/simple-name inventory, including hunk context; a same-name addition alongside a base definition cannot be split into separate lexical seeds by that representation and is not guessed to be new.

| Provenance | Denominator | Resolved | Ambiguous | Unresolved | Resolution rate |
|---|---|---:|---:|---:|---:|
| all | 64 (including new names) | 55 | 4 | 5 | 85.9% |
| all | 59 (excluding new names) | 55 | 4 | 0 | 93.2% |
| confirmed_study_snapshot | 54 (including new names) | 46 | 3 | 5 | 85.2% |
| confirmed_study_snapshot | 49 (excluding new names) | 46 | 3 | 0 | 93.9% |
| local_final_identity_unverified | 10 (including new names) | 9 | 1 | 0 | 90.0% |
| local_final_identity_unverified | 10 (excluding new names) | 9 | 1 | 0 | 90.0% |

| Task | File | Newly added name |
|---|---|---|
| pylint-dev__pylint-6528 | `pylint/lint/expand_modules.py` | `_is_ignored_file` |
| django__django-14631 | `django/forms/boundfield.py` | `_did_change` |
| django__django-14631 | `django/forms/forms.py` | `_bound_items` |
| django__django-16631 | `django/contrib/auth/base_user.py` | `_get_session_auth_hash` |
| django__django-16631 | `django/contrib/auth/base_user.py` | `get_session_auth_fallback_hash` |

All four remaining ambiguities are multiple same-name definitions in the changed file. Name origins and original classifications are preserved in `changed_symbol_origins.csv`; paired rates are in `changed_symbol_rates.csv`. Existing graph/seed artifacts remain unchanged.

## Every partial graph, by file

**23 partial graphs, 77 file-level reasons:** 71 syntax/encoding failures and six Python symlink omissions across task snapshots. The complete task → file → reason → line/message listing is in [partial_graphs.md](partial_graphs.md) and `partial_graph_files.csv`. It includes all 15 partial Django, five partial pylint, and three partial pytest graphs. Each omitted file remains visible; none was excluded to turn a partial graph into a complete one.

## Original feasibility by repository

Counts below sum task snapshots, not unique files across repositories. Times are original graph-build measurements, not test runtimes. Resource-limit prefix file/node counts are lower bounds. Only the 56 complete graphs are eligible under the current design; 11 of the confirmed historical 19 are complete. Partial handling in the proposed amendment does not make partial graphs eligible for the primary comparison.

| Repository | Complete / partial / limited | Python files / indexed parsed files | Parse failures / omitted | Nodes | Graph / total seconds |
|---|---|---|---|---:|---|
| astropy/astropy | 4 / 0 / 0 | 3,533 / 3,533 | 0 / 0 | 71,140 | 14.35 / 19.12 |
| django/django | 16 / 15 / 0 | 83,199 / 83,184 | 15 / 0 | 1,174,952 | 174.90 / 257.39 |
| matplotlib/matplotlib | 15 / 0 / 0 | 13,399 / 13,399 | 0 / 0 | 173,399 | 39.47 / 58.37 |
| mwaskom/seaborn | 1 / 0 / 0 | 150 / 150 | 0 / 0 | 2,790 | 0.59 / 0.81 |
| pallets/flask | 1 / 0 / 0 | 80 / 80 | 0 / 0 | 1,650 | 0.14 / 0.22 |
| psf/requests | 0 / 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0.00 / 0.00 |
| pydata/xarray | 5 / 0 / 0 | 784 / 784 | 0 / 0 | 27,665 | 6.15 / 8.45 |
| pylint-dev/pylint | 0 / 5 / 0 | 6,931 / 6,878 | 53 / 6 | 43,356 | 3.84 / 6.29 |
| pytest-dev/pytest | 4 / 3 / 0 | 1,487 / 1,484 | 3 / 0 | 35,035 | 4.23 / 6.39 |
| scikit-learn/scikit-learn | 5 / 0 / 0 | 3,648 / 3,648 | 0 / 0 | 42,044 | 10.91 / 15.15 |
| sphinx-doc/sphinx | 4 / 0 / 0 | 2,165 / 2,165 | 0 / 0 | 30,378 | 4.40 / 6.90 |
| sympy/sympy | 1 / 0 / 4 | 6,650 / 3,772 | 0 / 0 | 96,060 | 58.98 / 64.41 |

## Provenance, validation and reproduction

Base sources are the user's read-only acquired archives under `~/cg_repos/task_archives/<instance_id>.tar`, with a `testbed/` prefix. The acquisition manifest pins all 83 base SHAs and archive hashes, and 12 clone HEADs; 11 repositories have headline tasks and requests has none. No clone worktree is read or modified. Follow-up AST metadata/counting reads verified tar members directly without retaining or executing source.

The 19 confirmed candidate strings come from the hash-pinned snapshot's whitelist projection (`instance_id`, `source_run`, `agent_patch` only); all other values are skipped without decoding. Local candidates come only from the matching source-run path and pass the existing frozen-patch hash/size checks. The sixth local candidate, pytest-6202, was found during phase 1b; it remains exploratory.

Original artifact validation passed all 83 tasks. It checked hashes, graph/CSV accounting, edge IDs, missing fields, cleanup and static post-hoc import boundaries. The earlier five root-annotation call omissions were corrected before the accepted commit; initial code hashes and reused/rebuilt provenance remain in `graph_inputs.json`. No new graph correction is applied in these follow-ups. Current `followup_inputs.json` pins the follow-up code, accepted graph manifest, pending design and derived outputs; original validation hashes describe the original report, not this updated report.

Reproduce the read-only follow-up tables/report from the accepted stored baseline and local archives:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/followup_analysis.py
```

Do not rerun `build_graphs.py` or treat the draft as active. The old validator checks an immutable design hash; this follow-up verifies the original prefix and separately hashes the pending amendment. The follow-up performs no selection, reachability ranking or oracle comparisons.

**Nothing in the primary evaluation confirms that a selected test exercises the changed code.** Static resolution, including the new namespace categories, is a proxy and not dynamic coverage or correctness evidence.

**Stopped before selectors. The amendment is pending approval and has not been implemented.**
