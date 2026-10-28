# Phase 2-lite: frozen offline selectors

Design: `72ad21bce666aa766cc329c9bef8057f790c0ef5`, unchanged.
User authorized phase 2-lite on 2026-10-22; no phase 3 is authorized.

## Interpretation recorded before selector execution

The user's clarification of C's shared tail is binding: candidates with a
reachable path (specificity > 0) rank first under the frozen feature order.
Mapped-unreachable candidates (score 0) and unmappable candidates (graph
features missing) share one tail. Neither mapping status receives priority.
Within that tail, compare the still-computable same-module and same-package
features, then original V2 position and lexical ID. Direct-call counts and
minimum distance cannot distinguish tail candidates without imputing missing
values; they are not imputed. Missing scores remain null, never numeric zero.
Every frozen candidate has `graph_status`: `reachable`, `mapped_unreachable`,
or `unmappable`. Task rows count all three. No design amendment is made.

## Fixed execution and representations

- d = 1, 2, 3; K = 25, 50, 100, 250, 500, plus unbudgeted counts.
- PRIMARY_RESOLVED_ONLY decides criteria. SECONDARY_RESOLVED_PLUS_AMBIGUOUS
  traverses recorded ambiguous candidate targets too and is reported separately.
- Specificity uses each variant's distinct base-test-definition fan-in at depth
  3, weight 1/(1+fan-in), and the frozen ranking order. Exact rational scores
  avoid floating-point changes to ties. No outcome-dependent choice is made.
- Candidate identities come from the existing `selection.node_ids` applied to
  archive text, not test collection. Canonical/family identities and exact
  parameter-family checks call the existing diagnostic normalizer functions.
  No new normalizer, fuzzy match, docstring guess or bare-name fallback exists.
  Legacy innermost-class IDs that cannot uniquely identify a graph definition
  stay unmappable. Test-looking nested definitions are not proof of collection.
- Fan-in counts distinct graph test definitions represented by a base test-ID
  family, including multiple definitions behind an ambiguous legacy identity;
  B can emit only uniquely mapped, pre-existing base candidate IDs. Parameter
  instances never multiply a definition. Missing or omitted code is not covered.
- Equal-length paths compare complete caller-to-seed node-ID tuples. Multiple
  call sites with the identical node path use lexical call-site identity only
  to choose provenance; this cannot alter distance, score or selection.
- Provenance retains top 25 B/C tests per task/variant/depth, at most three
  paths per test in lexical seed-ID order. Paths are shared across budgets;
  paths beyond the cap and tests beyond rank 25 are represented by aggregates.
- A and C are restricted to the fixed 19 stored `study_snapshot` tasks. B's
  broader confirmed-patch analysis is separate. Primary complete graphs and
  qualified extended partial graphs never share a summary denominator.
  Finished partials with other omission reasons have diagnostic-only B/C
  outputs when seeds resolve, satisfying the all-applicable-task inventory;
  these EXCLUDED rows never enter either evaluation stratum or criterion.
- Eligibility and the C3 denominator are written and hashed before selection.
  Selector outputs are frozen by hash before summary/criteria/report code runs.

Only stored graph artifacts, verified frozen candidate patches, stored V2 IDs,
and verified base archives are inputs. No oracle fields, gold patches, issue
descriptions, network, Docker, benchmark import, test collection or benchmark
test execution. Synthetic unit tests of this research code are run separately.
All changes remain uncommitted. Reproduction commands appear in report.md.

## Runtime isolation after the interrupted foreground attempt

The archive-root fix accepts both `testbed` and `testbed/` directory entries.
The earlier partial foreground run is preserved under failed_attempts/; no
candidate IDs, scores, selection counts or criterion outcomes were inspected.
Its exact exit cause was not recorded. Long execution now runs under nohup,
with stdout/stderr, exit status and an explicit per-task completion marker.
The `execute` stage never freezes partial outputs: `freeze` is separate and
requires every task plus SELECTOR_RUN_COMPLETE. Original eligibility JSON and
eligibility_freeze.json remain byte-identical. These are file-handling/runtime
changes only; no ranking, eligibility or frozen experiment parameter changes.
