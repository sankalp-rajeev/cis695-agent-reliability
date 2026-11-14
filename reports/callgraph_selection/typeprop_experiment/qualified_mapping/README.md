# AST- and patch-aware qualified changed-symbol mapping

Evaluation-only extension. Frozen graph nodes/edges, call resolution, selector
functions, V2 policy, ranking and budgets are unchanged. The mapper consumes
verified base files plus the exact candidate diff, reconstructs candidate text
in memory, and associates actual edit lines with their innermost named AST
owner. It never imports or executes benchmark code.

Existing and newly introduced definitions are separate populations. Unchanged
context and patch headings are not evidence of an edit. Module-level edits,
unsupported files and failed reconstruction remain explicit diagnostics; no
whole-module or enclosing-class fallback seed is invented. A parent definition
is included only for edits it directly owns, not simply because a child changed.
Exact graph-source identity is distinct from runtime call-target certainty.

See `report.md`, `summary.json`, the per-definition results and the old-record
ledger for all-83-task evaluation and selection effects.
