# Phase 3 Part A

`configs/verifier/v1_5.yaml` enables `P_invalid_excluded` as the V2 decision input and turns on the fallback with a five-file cap. The E2E entry point accepts the study config through `--verifier-config`. The v1.4.1 config retains `S_invalid_excluded` and has the fallback disabled. Guarded execution keeps one native capture and stores all six C, S, and P reports.

The study run records `primary_accounting`, `fallback_used`, `fallback_tests`, and `fallback_candidates_total` in its V2 findings. `test_results` records `from_fallback` for each classified outcome, including concrete parameter cases. The fallback runs after agent-authored tests are excluded from Tiers 1 and 2. It probes each changed Python source file in patch order and each layout in `_PROBED` order, including `TESTS_TREE` last. Candidate files are deduplicated and counted before the cap. An empty result records `NO_SELECTION`.

## Offline replay

```bash
env -u PYTHONPATH PYTHONPATH=src HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
  LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python \
  scripts/replay_paired_skip_arm_b.py primary-config
```

The check used 40 stored Arm B captures and 11 stored V2 absences for tasks without executed tests. The comparison used the sealed task decisions and `reports/paired_skip/armB/decisions_label_free.csv`.

- Gate (a) passed. `full_v1_4_1.yaml` reproduced 51 of 51 stored Arm B decisions.
- Gate (b) passed. `v1_5.yaml` matched 51 of 51 values in `v2_P_invalid_excluded`.

## Offline unit suite

The 124 focused tests passed, including the ordered exporter and its no-argument entry point.

Gate (c) passed. The full offline `tests/unit` suite had 1,711 passed, 6 skipped, 6 failed, and 17 setup errors. Every failure and error ID matched `unit_baseline_phase1.json`. New failures and errors were both zero.

The raw log is `runs/study_v1_5/unit_part_a.log`. Its SHA-256 is `5ee54ff1825887bdfa728a64bf44905c25bdedd7ebe4197a85a09721c13de6ca`.
