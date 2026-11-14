# Phase 6b decisions

- 2026-11-14: The frozen plan section h overrides prompt-level per-task infrastructure retries: an infrastructure halt publishes no numbers and requires amendment/restart; if changing the frozen rule is necessary, hard stop.
- 2026-11-14: Use the project .venv Python 3.11.17; host default Python 2.7 cannot run the harness.
- 2026-11-14: Existing captures omit child executable, argv, environment and scope identity; report those fields as unavailable rather than infer them from flags, then add observation-only instrumentation before child-rule repairs.
- 2026-11-14: Secret scans inspect explicitly staged blobs and reject restricted paths; the repository-wide scanner would open forbidden label files, so it is not used.
- 2026-11-14: No external messages, notifications or model API calls will be made; ordinary local progress/checkpoints only.
- 2026-11-14: Prepared the requested append-only A1; it was not committed or pushed because automatic approval review rejected it.
- 2026-11-14: Automatic review rejected the first amendment commit because the draft included extra child-handling definitions; removed them and verified the complete frozen plan is an unchanged prefix. Only the exact explicitly requested A1 scope/secondary-selection clarification is appended.
- 2026-11-14: A second review rejected even the narrowed, explicitly requested A1 append; restored phase6b_plan.md byte-for-byte to HEAD, stopped dependent implementation/freezing/evaluation, and requested approval. No plan change or tag was published.
- 2026-11-14: Observation smokes finished with unchanged rules: incomplete 1/4, 4/4 and 16/16; all observed exec children were non-Python, and all outcomes matched. Parallel smoke correctly halted at its existing 5% gate. These are diagnostic evidence only, not experiment metrics.
- 2026-11-14: Preserve observation-only instrumentation and SHA-256 manifest without tagging/sealing; A1 rejection blocks dependent repair, harness freeze and evaluation. Raw traces remain under ignored runs/.
