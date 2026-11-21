# Phase 3 Part B

The study config enables per-requirement V4 with a requirement call of up to 40 steps, a four-requirement cap and two independent test passes of up to 80 steps each. The requirement list is written and hashed before either test pass. Each pass gets the issue and the same frozen list in a fresh base-only environment. Test names include the requirement and pass. The existing exit-code runner screens and executes the frozen bytes. The legacy config retains its original prompt, freeze, and decision input.

V4 records requirement hashes, verdicts and counts, uncovered IDs, and each kept test with its requirement, pass, hash, screening runs and patched runs. Stable fails yield V4 FAIL, and full PASS requires every requirement to pass. `UNCOVERED`, `NO_RESULT`, and `REQUIREMENTS_UNAVAILABLE` are recorded as V4 NOT_AVAILABLE when no requirement fails.

Each generator conversation retains the configured call cap. The provider ledger charges all conversations to the same run budget and limits each stage escrow to the remaining aggregate budget. V4 records billed cost and token usage per conversation and in total.

## Offline gates

- Gate (a) passed. `scripts/replay_paired_skip_arm_b.py primary-config` reproduced 51 of 51 stored Arm B decisions under `full_v1_4_1.yaml`, using 40 stored captures and 11 stored V2 absences.
- Gate (b) passed. The full offline `tests/unit` suite had 1,734 passed, 6 skipped, 6 failed, and 17 setup errors. All failure and error IDs matched `unit_baseline_phase1.json`. There were zero new issues.

The 130 focused tests included synthetic V4 generation, screening, patched evaluation, and provider ledger accounting. No Docker runs or model calls were used for verification. The raw unit log is `runs/study_v1_5/unit_part_b.log` with SHA-256 `dc7f29d00311ba4bc5566abe97841994add5a90d7cfda1866bac81d63d617432`.
