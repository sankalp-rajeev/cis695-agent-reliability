# Phase 3 Part C

`scripts/make_verify_inputs.py` copies the selected Phase 2 patches in ID-list order, checks each SHA-256 and records the manifest and ID-list hashes in `source.json`. The existing `frozen_inputs()` loader resolves the resulting plain-list manifest. Reference verification requires `--reference-patches` and matching provenance.

`--reuse-v4-from` verifies the source seal, V4 settings and each task's frozen evidence before running the kept tests on the patched tree. The completion record checks generator attempts and provider ledger usage for the destination run. Tests used synthetic freezes, patched verdicts and generator conversations. The existing leakage audit checks reference patch additions against the generator messages after subtracting lines from the issue, removed lines and the task's canonical base archive. Findings report the task, conversation, message index and line SHA-256.

## Offline gates

- Gate (a) passed. `scripts/replay_paired_skip_arm_b.py primary-config` reproduced 51 of 51 stored Arm B decisions under `full_v1_4_1.yaml`, using 40 stored captures and 11 stored V2 absences.
- Gate (b) passed. The full offline unit suite had 1,755 passed, 6 skipped, 6 failed and 17 setup errors. Every failure and error ID matched `unit_baseline_phase1.json`. The log is `runs/study_v1_5/unit_part_c.log` with SHA-256 `e9c1466ee0079bf780876537b4b8ac673c40b3323cd98615f24e3d8319a0194c`.
- Gate (c) passed. All eight temporary folders built successfully, and `frozen_inputs()` resolved every ID in the requested order. The temporary folders were deleted after validation.

| Run inputs | Patches | Empty |
|---|---:|---:|
| Dev reference | 51 | 0 |
| Test batch 1 reference | 60 | 0 |
| Test batch 1 GPT-4.1 mini | 60 | 0 |
| Test batch 1 Claude Sonnet 4 | 60 | 0 |
| Test batch 1 GPT-4.1 | 60 | 6 |
| Test batch 1 Gemini 2.5 Flash | 60 | 3 |
| Test batch 1 o4-mini | 60 | 2 |
| Test batch 1 Qwen3-Coder | 60 | 1 |
