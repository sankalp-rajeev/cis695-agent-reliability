# Lightweight receiver type propagation

Read [report.md](report.md) for the research question, exact before/after results,
limitations, audit corrections, runtime measurements and recommendation.

All changes are confined to this directory. The implementation is a static-only
wrapper over the unchanged Graph/AmendedGraph builders; production verifier,
V2 discovery, ranking and execution budgets are unchanged.

- `typeprop_graph.py`: constructor facts, bounded parameter propagation, evidence and conservative receiver resolution.
- `test_typeprop.py` / `focused_tests.txt`: synthetic correctness cases and existing graph regression checks.
- `evaluate.py` / `protocol.json`: exact frozen-baseline replay, full-corpus comparison and process batching.
- `validate_experiment.py` / `validation.json`: independent streaming checks, source hashes and original-worktree preservation.
- `benchmark_runtime.py`: matched fresh-process timing sample, one task per represented repository.
- `audit_candidates.json` / `audit_review.json`: deterministic stratified source review.
- `render_report.py`: render the report from validated data, runtime measurements and explicit audit decisions.
- `callsite_changes.csv`, `changed_symbol_changes.csv`, `repository_summary.csv`, `task_summary.csv`: complete comparison inventories.
- `selection_summary.csv`, `selection_changes.csv`, `selection_paths.csv`, `specificity_changes.csv`: unchanged selector policy evaluated on each graph.
- `analyze_seed_reachability.py` / `changed_seed_reachability*.csv`: per-changed-method gains, including improvements that leave selected test unions unchanged.
- `incidents.json` and `attempts/`: superseded code/results and the audit findings that required corrections.

Bulk graph/fact caches and superseded large tables stay local and ignored.
The evaluator refuses to overwrite an existing protocol, and resume requires
identical source hashes and file membership. Reproduction should start from a
clean worktree at `0c0c87f`, copying only this experiment's source files from
`experiment/callgraph-typeprop` before capturing a fresh original-worktree
fingerprint. See the report's reproduction section for the execution sequence.

No benchmark source is imported/executed, no oracle labels influence the graph,
and no Git push is part of this experiment.
