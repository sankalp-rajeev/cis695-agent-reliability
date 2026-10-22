# Phase 1b: base-only AST graph feasibility

Attempted graphs for **83/83** frozen non-empty headline tasks. Status counts: `{"complete": 56, "partial": 23, "resource_limited": 4}`.

Sources are the user's already-acquired, exact-base-commit Git archives under `~/cg_repos/task_archives/`, rooted at `testbed/`. No clone/worktree is modified or read for code. Every archive SHA-256 and PAX commit was checked against the preserved acquisition `inputs.json`. Each tree was extracted into `/tmp/cis695-cg-*`, parsed only with Python 3.11 `ast`, and deleted before retaining graph outputs. Links and special files are never followed; omitted Python links make a graph partial.

Design pre-registration: `05bdd1144e2013f7c1884066ce3fa05c6d52eedc`. The committed `design.md` is unchanged. The later explicit acquisition/phase-1b instructions authorize archives and graph construction in phase 1. No selectors, reachability/ranking calculations, oracle analysis, benchmark imports/installations, network, Docker, or tests were run. All changes in this phase remain uncommitted; Git index/history were untouched.

## Per repository

Counts sum task snapshots, including repeated files/definitions across different bases; they are not unique-repo counts. Complete/partial/resource-limited counts retain all task denominators. Graph seconds exclude archive hashing/extraction and output serialization; total task seconds include them. Resource-limited tasks have blank edge-resolution and changed-symbol measurements, and contribute no such measurements to repository totals. Their inspected AST counts and retained prefix nodes remain diagnostic lower bounds. Definitions counted during AST inspection can exceed definitions actually indexed before a resource stop.

| Repository | Tasks | Complete / partial / limited | Python files / parsed | Parse failures / omitted | Nodes | Resolved / ambiguous / unresolved edges | Changed symbols R / A / U | Resolution rate | Graph / total seconds |
|---|---:|---|---|---|---:|---|---|---|---|
| astropy/astropy | 4 | 4 / 0 / 0 | 3,533 / 3,533 | 0 / 0 | 71,140 | 49,916 / 18,809 / 294,480 | 1 / 0 / 0 | 100.0% | 14.35 / 19.12 |
| django/django | 31 | 16 / 15 / 0 | 83,199 / 83,184 | 15 / 0 | 1,174,952 | 703,541 / 337,649 / 3,558,643 | 27 / 3 / 4 | 79.4% | 174.90 / 257.39 |
| matplotlib/matplotlib | 15 | 15 / 0 / 0 | 13,399 / 13,399 | 0 / 0 | 173,399 | 167,056 / 87,403 / 755,413 | 7 / 0 / 0 | 100.0% | 39.47 / 58.37 |
| mwaskom/seaborn | 1 | 1 / 0 / 0 | 150 / 150 | 0 / 0 | 2,790 | 2,223 / 1,798 / 15,443 | 1 / 0 / 0 | 100.0% | 0.59 / 0.81 |
| pallets/flask | 1 | 1 / 0 / 0 | 80 / 80 | 0 / 0 | 1,650 | 613 / 112 / 3,208 | 1 / 0 / 0 | 100.0% | 0.14 / 0.22 |
| psf/requests | 0 | — | — | — | — | — | — | — | — |
| pydata/xarray | 5 | 5 / 0 / 0 | 784 / 784 | 0 / 0 | 27,665 | 59,736 / 7,738 / 123,593 | 4 / 1 / 0 | 80.0% | 6.15 / 8.45 |
| pylint-dev/pylint | 5 | 0 / 5 / 0 | 6,931 / 6,878 | 53 / 6 | 43,356 | 13,852 / 5,152 / 65,188 | 8 / 0 / 1 | 88.9% | 3.84 / 6.29 |
| pytest-dev/pytest | 7 | 4 / 3 / 0 | 1,487 / 1,484 | 3 / 0 | 35,035 | 16,225 / 6,536 / 100,949 | 5 / 0 / 0 | 100.0% | 4.23 / 6.39 |
| scikit-learn/scikit-learn | 5 | 5 / 0 / 0 | 3,648 / 3,648 | 0 / 0 | 42,044 | 69,504 / 4,742 / 268,501 | — | — | 10.91 / 15.15 |
| sphinx-doc/sphinx | 4 | 4 / 0 / 0 | 2,165 / 2,165 | 0 / 0 | 30,378 | 24,474 / 5,929 / 82,359 | 1 / 0 / 0 | 100.0% | 4.40 / 6.90 |
| sympy/sympy | 5 | 1 / 0 / 4 | 6,650 / 3,772 | 0 / 0 | 96,060 | 153,442 / 33,425 / 147,074 | — | — | 58.98 / 64.41 |

## Candidate provenance and changed symbols

Patch availability: `{"available": 25, "patch missing": 58}`. Provenance: `{"confirmed_study_snapshot": 19, "local_final_identity_unverified": 6, "missing": 58}`.

Confirmed candidates are projected from the hash-pinned committed mixed failure-analysis snapshot using only `instance_id`, `source_run`, and `agent_patch`. All other JSON values are lexically skipped without decoding. No gold/official-test/oracle/issue values reach the graph or symbol functions. Snapshot candidate hashes are derived from the stored strings; original frozen repair hashes are unavailable there. Local candidates are read only from the exact cohort source-run path and verified using the existing frozen-patch reader, recorded SHA-256 and byte size. Their final-run identity remains unverified and exploratory. Missing patches do not prevent base graph builds, are explicitly `patch missing`, and have blank symbol totals/rates; no alternate run is substituted.

Changed production Python paths use the existing `is_test_file`, `parse_patch`, and `touched_symbols`. Names are matched exactly within the changed base file (old path for renames). Duplicate simple names are ambiguous; no global matching or invented module seed is used. The extractor includes diff context/hunk names, so this is a diff-based inventory, not proof of semantic changes. New/absent symbols cannot be distinguished from unmatched context names without more evidence and are explicitly grouped. Rates are resolved/extracted names on available patches only, not on all 83 tasks; zero extracted names have a blank rate. Partial graph rates are marked as such.

| Repository | Unresolved/ambiguous/no-name reasons |
|---|---|
| astropy/astropy | `{}` |
| django/django | `{"multiple_same_name_definitions_in_file": 3, "symbol_absent_at_base_or_diff_context_name": 4}` |
| matplotlib/matplotlib | `{}` |
| mwaskom/seaborn | `{}` |
| pallets/flask | `{}` |
| psf/requests | `{}` |
| pydata/xarray | `{"multiple_same_name_definitions_in_file": 1}` |
| pylint-dev/pylint | `{"symbol_absent_at_base_or_diff_context_name": 1}` |
| pytest-dev/pytest | `{}` |
| scikit-learn/scikit-learn | `{}` |
| sphinx-doc/sphinx | `{}` |
| sympy/sympy | `{}` |

## Graph interpretation and limits

Each recorded edge is an AST call site with caller, path, line/column, expression, target candidates and reason. Only a single, unqualified static binding is resolved. Lexical names and explicit first-party imports/aliases are indexed; import cycles, rebinding, conditional definitions/imports, module collisions, custom decorators, inheritance and dynamic receiver dispatch retain uncertainty. All decorated targets (including possibly shadowed builtin decorators) are conservatively ambiguous. Calls inside comprehensions/lambdas/annotations are unresolved because their scope/evaluation is not modeled. Assignment-based aliases, instance types, inherited lookup, external libraries, star-import expansion, fixtures, reflection and monkey-patching are not inferred. Constructor calls may point to a class; there is no fabricated class-to-`__init__` edge. Module containment and imports are metadata, not call edges. Static resolution does not guarantee a runtime target.

Syntax/encoding failures or omitted Python files make a graph **partial**, even if all remaining files build. The committed resource caps are unchanged, with exhausted builds marked resource-limited. Only complete graphs are eligible for a later primary comparison. Parse details and edge uncertainty histograms are retained per task.

**Nothing in the primary evaluation confirms that a selected test exercises the changed code.** This phase provides no dynamic coverage, runtime-test behavior, correctness measurement or selector recommendation. A/B/C remains restricted to the 19 confirmed historical selections; any broader B analysis is a separate future phase.

## Outputs and reproduction

`base_feasibility.csv`: one row per task. `feasibility.json`: aggregate/per-repository metrics. `graphs/<instance_id>/`: compressed nodes, call edges, scope/import binding metadata, changed-symbol diagnostics, and parse/resource/provenance diagnostics. `graph_inputs.json`: code, inputs, archive, candidate, base-source and output SHA-256 hashes, plus the committed design revision. Acquisition `inputs.json` is preserved unchanged.

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py --refresh-accounting
```

No test suite was executed under the no-test-execution constraint. Verification consists of archive/source hashes, PAX commit checks, AST-only parsing, and stored-output consistency checks. These establish provenance and internal accounting, not the semantic soundness/completeness of the static resolver.

**Stopped after phase 1b. No selectors or post-hoc evaluation have run.**
<!-- stored-validation-supplement -->

## Stored-output checks and provenance strata

All 83 task artifacts passed hash and accounting checks. Every completed graph's call-site total and all retained edge target IDs were checked; resource-limit prefixes were checked as incomplete diagnostics. All extraction trees were removed. AST-only import inspection found no post-hoc module import under `src/` or this graph implementation. Synthetic unit checks are supplied in `test_static_graph.py` but were not run.

Interpreter: `3.11.16 (main, Sep  1 2026, 14:18:37) [Clang 22.1.3 ]`. No benchmark source was imported or executed.

| Candidate provenance | Tasks / symbol-measured tasks | Complete / partial / limited graphs | Resolved / ambiguous / unresolved symbols | Rate |
|---|---|---|---|---|
| confirmed_study_snapshot | 19 / 18 | 11 / 7 / 1 | 46 / 3 / 5 | 85.2% |
| local_final_identity_unverified | 6 / 6 | 5 / 1 / 0 | 9 / 1 / 0 | 90.0% |
| missing | 58 / 0 | 40 / 15 / 3 | — | — |

Per-repository strata are in `changed_symbol_by_provenance.csv`. Local candidates remain exploratory; their hashes do not establish final-run identity. Historical and broader offline comparisons have not run.

The exact source-run directory also contains a hash-verified local candidate for `pytest-dev__pytest-6202`, in addition to the five previously inventoried local candidates. It remains in the same unverified-local stratum; no alternate run was substituted. The confirmed historical cohort remains 19 tasks.

Graph definition IDs encode file, lexical name, kind and location; they are not normalized runner test IDs. No test-ID adapter, Django docstring-name mapping, or second normalizer was introduced in this phase.

Failure paths/reasons and their task-snapshot frequencies are in `parse_failure_summary.csv`. There are 71 syntax/encoding parse failures across task snapshots and six Python symlink members omitted without following their targets. Four SymPy snapshots hit the unchanged 5,000,000 AST-node limit. The most frequent stored failures are:

| Repository | Path | Reason | Snapshots |
|---|---|---|---:|
| django/django | `tests/test_runner_apps/tagged/tests_syntax_error.py` | SyntaxError | 15 |
| pylint-dev/pylint | `tests/functional/t/tokenize_error.py` | SyntaxError | 5 |
| pylint-dev/pylint | `tests/functional/t/tokenize_error_jython.py` | SyntaxError | 5 |
| pylint-dev/pylint | `tests/functional/u/unknown_encoding_jython.py` | SyntaxError | 5 |
| pylint-dev/pylint | `tests/input/func_w0122_py_30.py` | SyntaxError | 5 |
| pylint-dev/pylint | `tests/regrtest_data/bad_package/__init__.py` | SyntaxError | 5 |

No syntax fixture or source directory was silently excluded to obtain a complete graph. Partial graphs remain in feasibility denominators and are ineligible for the later primary comparison.

Validate these stored artifacts without rebuilding graphs:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_outputs.py
```

## Accounting correction

Initial output validation found one omitted call per graph in five tasks: a call appearing directly as an annotation root. The AST visitor was corrected to retain these as unresolved calls. Only those five graphs were rebuilt; all four AST-node-limit stops were preserved without retry. Reused graph provenance and initial implementation hashes/source snapshots are recorded in `graph_inputs.json`. Resource-limited symbol and edge-resolution measurements are blank, never failed/zero scores.

Rebuilt tasks: `sphinx-doc__sphinx-7910`, `pylint-dev__pylint-4661`, `sphinx-doc__sphinx-10323`, `sphinx-doc__sphinx-10435`, `sphinx-doc__sphinx-10466`.

Commands used during this diagnostic (a fresh build with the corrected code needs only the first and last):

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py --refresh-accounting
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_outputs.py
```
