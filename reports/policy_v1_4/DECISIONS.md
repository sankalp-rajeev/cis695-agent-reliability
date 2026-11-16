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
