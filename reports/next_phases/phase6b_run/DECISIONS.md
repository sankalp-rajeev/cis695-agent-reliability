# Phase 6b decisions

- 2026-11-14: The frozen plan section h overrides prompt-level per-task infrastructure retries: an infrastructure halt publishes no numbers and requires amendment/restart; if changing the frozen rule is necessary, hard stop.
- 2026-11-14: Use the project .venv Python 3.11.17; host default Python 2.7 cannot run the harness.
- 2026-11-14: Existing captures omit child executable, argv, environment and scope identity; report those fields as unavailable rather than infer them from flags, then add observation-only instrumentation before child-rule repairs.
- 2026-11-14: Secret scans inspect explicitly staged blobs and reject restricted paths; the repository-wide scanner would open forbidden label files, so it is not used.
- 2026-11-14: No external messages, notifications or model API calls will be made; ordinary local progress/checkpoints only.
