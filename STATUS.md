# E2E v1.4.1 status

STOPPED_INPUT_ACCESS (2026-11-16): D1's exact Django projection requires 31 files outside the input allowlist. A6/A7 additionally require hashing reports/policy_v1_4/golden.csv, which matches the expressly forbidden `gold` path rule. None of those files was opened. The instruction to stop when a needed input has a forbidden name applies. See reports/next_phases/e2e_v1_4_1/REPORT.md and input_access.json.

Implemented: independent standard-library access preflight and three focused tests. No pipeline or registry changes, model calls, rerun, image pulls/builds, or correctness-input reads. The preflight verifies 74 permitted frozen-artifact hashes with zero mismatches; one hash remains blocked by the path rule. No freeze tag will be created.

Housekeeping complete: fetched and merged latest origin/feature/umgpt-routing (already up to date at 983c3f4), then reran the exact unit suite. Before and after: 6 failed, 1478 passed, 7 skipped, 47 errors, with identical failed/error IDs. Compared with the supplied reference: 30 new ERROR IDs, all from a read-only Hugging Face dataset-cache lock; no reference failure now passes. All three new tests pass. A6 FAILS its strict ID rule; full implementation and A1–A7 acceptance remain incomplete.

Publication: the checkpoint is committed locally on feature/e2e-v1.4.1. Automatic approval review rejected the requested push twice, requiring direct user authorization for git@github.com:sankalp-rajeev/cis695-agent-reliability.git and this payload/branch; the attachment instruction was not accepted as trusted authorization. No push or freeze tag was made.

Environment: this worktree's own environment passed `UV_CACHE_DIR=/tmp/e2e-v1-4-1-uv-cache uv sync --offline --frozen --no-install-project` (155 packages). The temporary cache avoids writing outside the authorized workspace.

Deadline: Wednesday 18 November 2026, 18:00 America/New_York (16:00 America/Phoenix).

## Previous UM cost probe status

Done: all three model verifications and all three authorized task attempts on gpt-4.1-mini. Total estimated spend $0.65728395 including $0.00031875 verification; no cost cap fired and no filtering event occurred in 265 new calls. django-14373 cost $0.05068680; scikit-learn-12973 cost $0.26790480 (V4 RepeatedFormatError); django-16899 cost $0.33837360 (100-step repair limit, no patch, V4 empty-patch skip).

Done: cost-only report and measured/repriced 10/83-task projections; numeric-only DeepSeek whole-set comparison; 75 focused tests; independent ledger/report reconciliation; all 38 frozen files match origin/main. No correctness grading, V1–V3, or oracle run.

Running: none; paid work and report validation are finished.

Next: review reports/umgpt_probe/REPORT.md to choose a rerun model; observed skips/errors limit the 83-task budget estimate. No further paid calls planned. Publication branch: feature/umgpt-routing.
