# Predeclared repaired V2 mapping

This document is written, committed, and pushed before applying any replacement or running the recomputed decisions.

Primary source: reports/next_phases/phase4_rerun/attempt4_seal/results.json, per_task[].policies.S_invalid_missing.

The file presents four Phase 4 accounting policies, without one uniquely named replacement for the old V2 signal. Under the user's instruction to take the conservative reading where silent, choose S_invalid_missing: strict completeness, with invalid IDs retained as missing. Report all four alternatives as sensitivity tables. This accounting choice is made without labels, not fitted to correctness. It does not change decision.py, any configuration, or any frozen artifact.

PASS -> PASS; FAIL -> FAIL; REGRESSION_ERROR -> FAIL; INCOMPLETE -> NOT_AVAILABLE; NOT_AVAILABLE -> NOT_AVAILABLE; unknown/missing -> NOT_AVAILABLE plus the unmapped list. The error mapping follows unchanged src/reliability/verifier/evidence.py. No observed status has an ambiguous outcome mapping; distinct Phase 4 policies are kept explicit rather than conflated.

V1, V3, V4, patch-applies, prohibited-manipulation, and high-severity flags remain the stored values. Use unchanged FullPolicy v1.3.0-full, matching every selected frozen record. Validate original decisions before recomputation.

FLAG attribution: report both FLAG with regression NOT_AVAILABLE and the stricter counterfactual count, FLAG that would become ACCEPT if only regression were PASS. The latter measures FLAG solely caused by regression unavailability.
