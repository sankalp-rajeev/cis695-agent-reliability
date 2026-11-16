# Decisions

- Preserve old policy implementations, default selection and serialized results.
  New signal implementations and configuration are version-specific opt-ins.
- No frozen configuration or sealed audit artifact will be edited. Reuse audit
  fixtures and case specifications read-only; write all new proof here.
- An existing REJECT remains REJECT when V3 fails. The V3 gate downgrades an
  otherwise ACCEPT to FLAG with v3_absolute_failure; it never overrides rejection.
- AST comparison uses complete base and patched files, not isolated diff lines.
  Unavailable, non-Python and unparseable test inputs are explicitly recorded;
  incomplete analysis blocks ACCEPT conservatively, without inventing a violation.
- Relative checks retain base results even when the patched check passes.
  New findings are exact diagnostic-line multiset differences, recorded as such.
- Stored golden proof uses original stored V2 outcomes, not audit projections.
  Accounting defaults affect reporting only and never V2 execution.
- Secret scanning before each commit is limited to explicitly staged blobs and
  this branch's changes, avoiding forbidden label files and local .env.
- Use a new CLI, scripts/verify_patch_v1_4.py, and a new runner/registry. All
  pre-existing source files remain byte-identical to origin/main. Only the
  explicitly requested version section will be appended to the policy document.
- Match existing test scopes by qualified name. Compare assertion counts within
  each pre-existing scope, so assertions in a new test cannot mask a loss in an
  old test. Nontrivial assertion-expression edits alone are not removals; an
  expression replacement rejects when it becomes constant true or a tautology.
  Adding a skip to a newly added test does not disable a pre-existing test.
- Existing assertion helper calls remain counted. Unparseable/non-Python inputs
  block ACCEPT with v1_analysis_incomplete; no guessed AST verdict is emitted.
- Generator elapsed time covers the entire generate invocation, including its
  setup/readout/cleanup. If usage is unavailable, retain null plus an explicit
  explanation rather than claiming zero. Simultaneous step/cost limits are
  classified as steps, matching the existing agent runner's precedence.
- The first full-suite comparison exposed one extra environment failure because
  the offline guard's /tmp import path contaminated sys.path. The guard now
  loads by file without modifying sys.path; no production fix was needed.
