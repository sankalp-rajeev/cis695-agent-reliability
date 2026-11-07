# Fix 9/10 compatible Phase 4 launcher

`scripts/phase4_launch.py` is prepared for review. **No new tag or controlled run has been created.** Attempt 1 remains quarantined; none of its captures or outcomes is used by this launcher.

## Frozen inputs and dry run

The launcher validates the pinned original protocol and tasks JSON hashes, all 83 V2 selection and candidate-patch seals, whole base archives and declared archive commits, immutable image IDs, the four-column dataset provenance and isolated 4.0.4 wheel, and all pristine-preflight receipt/source hashes. It neither selects new families nor reads correctness labels, previous result files, or attempt-1 data.

Dry run requires a fresh output path and never starts containers:

```bash
env -u PYTHONPATH .venv/bin/python scripts/phase4_launch.py \
  --dry-run --output /tmp/phase4_launcher_review_fresh
```

The ignored wheel must remain available at `runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl`, or be supplied with `--wheel`. Its published SHA-256 is verified; it is never installed/imported. No dataset loader is used by the launcher: it reads only the previously sealed four-column projection. The source snapshot, dataset and proof identities appear in every dry-run task specification.

[fix10_launcher_dry_run.json](fix10_launcher_dry_run.json) records successful validation of all 83 specs, both planned trees, zero containers and zero collection/test execution. It is input validation, not evidence of runtime test outcomes or a new freeze.

## Explicit execution barrier

Execution requires both `--execute` and `--freeze-tag <new-approved-annotated-tag>`. The tag must resolve to clean HEAD. The old `phase4-plan-frozen` name is explicitly rejected; the launcher never creates or moves tags, pushes, opens tmux, resumes an existing attempt, or sends notifications. Raw output must be a fresh directory under ignored `runs/`. A new attempt starts from task 1.

Each task uses one container pinned by frozen image ID, `--pull=never`, `--cpu-shares 2048`, `--network none`, and serial task order. `BaseSourceSpec` includes the frozen base commit/archive/hash and exact pre_install provenance. Container startup creates a **fresh pristine source receipt** before any patch application, native collection, execution or confirmation. An old preflight receipt cannot substitute for this check. GENERATED_INPUT_CHANGED remains non-halting evidence and is included in the native captures.

Both initial trees are captured with a recorded **1,800 s per-pass budget**, even if scoring later abstains on an unreliable base. The unchanged regression scorer then performs three isolated base and three isolated patched confirmations for each new FAIL/REGRESSION_ERROR. Four policy/accounting reports use those same native captures; replays cannot invoke additional native executions. There is no baseline cache. Unit tests verify the eight native passes for one stable new failure, rather than multiplying confirmation work by four policies.

A real 12 h timer interrupts the active stage and uses container cleanup; a separate boundary check prevents starting another task after the cap. NOT_REACHED within a pass retains the executor's elapsed-time accounting. A global stop can leave partial raw evidence for the active task; no complete result is manufactured for it.

SourceIntegrityError aborts the attempt immediately, records the failing receipt, and prevents the next task from starting. The abort receipt repeats the label-free repair/new executor/new tag/fresh task-1 rule. Completed/partial captures are retained and hash-manifested. Other unhandled runner failures and interrupts also stop the attempt with explicit status.

## Local evidence and verification

Only local files are written: `progress.jsonl` (task completion metadata, no verdict summaries), `plan.json`, `attempt.json`, per-task pristine receipts, generated inventories, `base.json`, `patched.json`, `raw/`, four-policy `result.json`, and final completion/abort metadata plus a capture hash manifest. Progress can be checked with `tail -f <new-run-directory>/progress.jsonl` after a separately approved launch.

All **12 launcher unit cases passed**, including zero-container dry run, frozen-input tampering, unverified receipt refusal, immediate integrity abort, no resume, both-tree capture despite base abstention, exactly one confirmation set, CPU/network/pull configuration, old-tag rejection and 12 h stop. The full unit suite is **1,192 passed, 6 failed, 6 skipped, 17 errors**, exactly the historical failure/error identities. No executor semantics, H1/H1b/H2 thresholds, B1, B2, or selection policy changed with the launcher.
