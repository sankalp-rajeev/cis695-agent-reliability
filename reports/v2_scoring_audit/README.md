# V2 scoring audit

Status: BLOCKED BEFORE TEST EXECUTION. See [report.md](report.md).

All five fixes and both interpretation notes are frozen in `protocol.json`. The eight authorized candidates and original selections are under `frozen_inputs/`.

`commands.jsonl` and `preflight/` preserve the exact Docker version commands and their failures. Both local Windows engine pipes were absent even outside the sandbox. No container or test ran.

`raw_test_outcomes.csv` is explicitly an unexecuted request inventory, not raw test observations. Empty outcome/ID/duration/log fields mean not collected. `regression_reruns.csv` has zero completed repeats. `old_vs_fixed.csv` leaves audit verdicts unknown. `metrics_before_after.csv` covers the same empty subset on both sides; undefined metrics must not be interpreted as zero rates or all-83 corrections.

`affected_stored_records.csv` is a source-only risk screen of all 83 records. `additional_reruns_needed.csv` lists all 75 non-target patches, not authorization to run them. `parser_fix.diff` is a source-only, unapplied, unvalidated proposal; `tests.txt` records why no actual-format fixtures or tests could be run.

Do not use post-hoc oracle labels for diagnosis, confirmation-test selection or scoring-rule tuning. Preserve all original artifacts. No network, commits, agents or models.
