# UM cost probe status

Done: preflight, 69 focused tests, 38 unchanged frozen files, all three real model verifications ($0.00031875), numeric-only old-run extraction.

Running: repair launcher environment cleanup; first startup stopped before any task API calls because inherited Python import paths mixed incompatible packages. Preserved under runs/umgpt_probe/precall_bootstrap_20261116.

Next: launch same three gpt-4.1-mini tasks with PYTHONPATH/PYTHONHOME cleared, then audit/report/commit/push. No paid task has been retried.
