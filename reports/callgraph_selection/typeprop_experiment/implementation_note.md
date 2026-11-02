# Implementation note (written before implementation)

Starting commit: `0c0c87fda86cf0a2f7c33866020325856e7303de`.

`Graph.scopes` holds lexical parents, caller IDs, binding lists, redirected
(global/nonlocal) names and star-import flags. Definition IDs encode source path,
qualified name, kind and location. Functions do not close over class namespaces.
Parameters are `("unknown", "parameter")`; methods named self/cls receive an
explicit `("receiver", class_id)` first binding. Stores/deletes append unknown
bindings, so rebinding stays visible. Constructor calls target class nodes but
produce no instance binding and no implicit initializer edge. Explicit imports
are expanded through the existing cycle/depth-limited resolver. Attribute lookup
uses module/class bindings; instance assignments and unannotated parameters stay
unknown. Decorators, conditional definitions, inheritance and dynamic dispatch
retain uncertainty. Calls in unsupported scopes are recorded but not resolved.

Use a new wrapper in this directory, inheriting Graph/AmendedGraph and Indexer.
Capture small assignment/signature/call descriptors while the existing indexer
runs; do not change the baseline files. Reuse Graph.resolve for constructors,
imports and method lookup. Preserve baseline edges and add separate type facts
with provenance. Only frozen-baseline resolved calls propagate arguments; newly
inferred calls are not additional propagation constraints in this experiment.
A synchronous, bounded fixed point handles parameter-to-parameter transfer.
Unknown evidence taints a parameter; several known classes remain ambiguous.

Baseline: the Amendment 2 overlay manifest (79 original plus 4 amended SymPy
graphs), 83 tasks, 56 complete / 27 partial / 0 resource-limited. Original
historical pre-Amendment counts are 56 / 23 / 4 and are not mixed with this
comparison. Changed-symbol resolution is 147 resolved / 21 ambiguous / 19
unresolved (187 names). Matching definitions cannot improve through call edges;
report reachability separately. Raw ignored graphs will be read from the original
worktree without copying into or modifying it. All new outputs live here.

Static assumptions: observed, statically identifiable calls form the parameter
boundary. Unobserved external/plugin/runtime calls remain a limitation, not proof
of runtime types. Reject function values that escape through indexed non-callee
references; defaults/variadics, unknown calls/arguments, unsafe rebinding,
decorated/conditional definitions, inherited/custom-creation/dynamic classes,
unsupported scopes and detected attribute mutation do not provide unique types.

## Audit-driven corrections before the final corpus run

Import expansion deduplicates identical unknown bindings. The wrapper therefore
retains binding multiplicity before expansion, so repeated assignments/deletions
cannot vanish. Baseline self/cls receiver metadata denotes the defining class,
not an exact dynamic class; it is preserved for old edges but excluded as a
propagation source. Known attribute writes block new edges with that method
name. Classes with detected reflective/dynamic member behavior are excluded.
Global/nonlocal declarations taint their enclosing binding owners; unsupported
scope stores also taint evidence. Callable value references inside unsupported
scopes are considered escapes, never silently ignored to establish uniqueness.
Two interrupted attempts and their source-audit counterexamples are recorded in
`incidents.json`; they do not supply any final result denominators.

A later stratified source audit caught Python private-name mangling in a pylint
fixture: `another_obj.__test()` inside a different class does not refer to the
raw `AnotherClass.__test` definition. New receiver edges now exclude names
starting with `__` unless they also end with `__`. Baseline edges remain intact.
The full superseded 83-task output is retained in `attempts/private_name_audit/`;
the final output must come from a full rerun of the corrected code.
