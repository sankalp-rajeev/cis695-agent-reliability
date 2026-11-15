# Signal audit status

Started: 2026-11-15T01:03:54.670699+00:00. Wall-clock limit: six hours from this timestamp.
Stage 0: prior output archived; fresh session and input whitelist in effect.
No prior attempt file contents, task labels, or oracle records have been opened.
Stages 1-6: NOT_RUN. No outcomes or seals claimed.
Branch: analysis/signal-audit.

Updated: 2026-11-15T01:06:10.650554+00:00.

HARD STOP during the pre-Stage-1 record availability check: 83 of 83 required records are missing, exceeding the allowed maximum of 17. All four permitted run roots are absent.

- Step 0 archived and checkpointed at c00779d; push to origin/analysis/signal-audit succeeded.
- missing_records.csv enumerates all 83 task IDs, manifest membership, missing status, and reason.
- record_inventory.py generated the inventory using only the frozen task list, manifest IDs, and directory existence.
- verify_preflight.py independently checked the raw IDs and filesystem, and compared every inventory row. It imported no analysis code. Result: PASS for the blocker inventory only.
- Stages 1, 2, 3, 4, 5, 6: NOT_RUN. V1 cases caught, V3 decision effects, V4 breakdown, decision counts, and false accepts: NOT_AVAILABLE because the hard stop prevents the audit.
- Stage 6 verification and both requested seals: NOT_RUN; no signal-audit tags created.
- No selected verification records exist here to open. No prior attempt contents, task-label sources, grader outputs, oracle records, .env, or API credentials were opened. Whitelisted verifier/policy source was inspected; no task label tables were read.
- No verifier, policy, configuration, or frozen artifact was changed. No model calls or task execution occurred. Network use was limited to the project's own GitHub push.
- Stop after committing and pushing this blocker checkpoint; do not continue to Stage 1 while this hard stop holds.
