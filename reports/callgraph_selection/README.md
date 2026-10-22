# Phase 1b: base AST graphs only

The design is pre-registered in commit `05bdd1144e2013f7c1884066ce3fa05c6d52eedc`
(`Pre-register call-graph selection design`). The committed design remains
unchanged. Later explicit instructions authorize the acquisition and graph
construction steps in phase 1; selectors and post-hoc evaluation remain deferred.

The user completed acquisition with `scripts/fetch_cg_repos.sh`. Read-only clones
are under `~/cg_repos`; exact-base archives are
`~/cg_repos/task_archives/<instance_id>.tar`, rooted at `testbed/`. The preserved
[inputs.json](inputs.json) records the cached Arrow metadata provenance, 12 clone
HEADs, 83 verified base commits, archive hashes, and acquisition code/input hashes.
The 83 headline tasks span 11 repositories; the requests clone has no headline
task. The graph builder does not access the network or mutate/read clone worktrees.

From the project root, reproduce all graph outputs and summaries:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_outputs.py
```

An explicit three-task sample was built before the full run:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py --tasks astropy__astropy-14365 django__django-13297 pallets__flask-5014
```

Sample CSV/aggregate measurements are retained with `sample_` prefixes; graph
directories are superseded by the full build. Sample execution checks graph
construction on archived source; it executes no benchmark code or tests.

Each task is hash/commit checked, safely extracted to `/tmp/cis695-cg-*`, parsed
with `ast` only, and deleted before graph outputs persist. No imports, installs,
test collection/execution, Docker, oracle analysis, gold patches or selectors are
used. Candidate seed names reuse the existing patch parser and symbol extractor,
and do not alter the base graph. Missing frozen candidates remain `patch missing`.
Confirmed snapshot and local, final-identity-unverified provenance remain split.

Outputs:

- [report.md](report.md): repository-level feasibility and limitations.
- [base_feasibility.csv](base_feasibility.csv): 83 per-task rows, blank seed
  measurements for missing candidates.
- [feasibility.json](feasibility.json): repository and overall aggregate metrics.
- `graphs/<instance_id>/nodes.jsonl.gz`, `edges.jsonl.gz`, `scopes.jsonl.gz`:
  definitions, call sites and lexical/import metadata; no source trees.
- `graphs/<instance_id>/changed_symbols.json`, `diagnostics.json`: exact file/name
  seed mapping, parse/resource failures, uncertainty reasons, hashes and runtimes.
- [graph_inputs.json](graph_inputs.json): graph-job code/input/output hashes;
  acquisition metadata is preserved in its original file.
- [validation.json](validation.json): stored-output provenance and accounting checks.

`test_static_graph.py` supplies synthetic resolver/projection/seed checks for later
review. They were **not executed**, respecting the no-test-execution instruction.
The validator only reads stored outputs; it runs neither tests nor benchmark code.
The old `feasibility.py` is the preceding source-availability inventory, not this
archive-driven graph pipeline.

Nothing in the primary evaluation confirms that a selected test actually
exercises changed code. Static resolution is a proxy, not dynamic coverage.
All phase-1b changes remain uncommitted. Stop here for review; no selectors yet.
