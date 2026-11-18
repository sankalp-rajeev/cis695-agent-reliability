# Arm B decisions

## Before grading

- The audited run reported `COMPLETE` for all 92 tasks. Read-only tmux and Docker checks found no tmux server or running containers. The independent SHA-256 inventory matched all 9,252 entries in the runner seal and added the runner seal itself. The source folder remained read-only.
- The seal summary takes decision counts from the live verifier record of each completed task. The ledger job key is the absolute arm directory. Repair calls use the ledger stage `agent`. Amendment A1 moves the one filtered empty-patch task, `django__django-13569`, from the runner's no-patch count to provider-blocked. Spend sums the 6,911 call costs for this job by provider and in total. All calls were settled and no stage escrows were active.
- Amendment A2 governs grading. The worktree and the arm header identify pipeline commit `2a3bf7fa9070ded3dbdb2600831bf83e4247b4b8`. Both `uv.lock` and the worktree interpreter report SWE-bench 5.0.2.
- The oracle ordering guard parses the main study's base `VerificationRecord` with extra fields forbidden. The E2E verifier writes the same base fields and eight additional V1.4.1 fields. The grading-folder adapter will copy only the base fields into `verification_record.full.json`, preserving their values. It will verify the source record's sealed hash and copy `patch.diff` and `repair_record.json` byte for byte. The oracle and its ordering guard stay at the frozen commit.
