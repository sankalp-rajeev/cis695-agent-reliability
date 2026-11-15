"""Independent standard-library check of the blocker, not a Stage 6 seal."""

import csv
import json
import os
from pathlib import Path


base = Path(__file__).resolve().parents[3]
output = Path(__file__).resolve().parent
raw = json.loads((base / "reports/v2_discovery_cleanup/frozen_83/tasks.json").read_text())
expected_ids = {item["instance_id"] for item in raw}
assert len(raw) == len(expected_ids) == 83
runs = ["main_2_rerun_mpl", "main_3_rerun_infra", "main_50_a", "main_50_b"]
assert not set(runs).intersection(entry.name for entry in os.scandir(base / "runs"))
raw_memberships = {task: set() for task in expected_ids}
for run in runs:
    with (base / "manifests" / (run + ".csv")).open(newline="") as f:
        rows = csv.reader(f)
        header = next(rows)
        column = next(header.index(name) for name in ("instance_id", "task_id", "id") if name in header)
        for row in rows:
            if row[column] in expected_ids:
                raw_memberships[row[column]].add(run)
with (output / "missing_records.csv").open(newline="") as f:
    inventory = list(csv.DictReader(f))
assert len(inventory) == 83
assert {row["task"] for row in inventory} == expected_ids
for row in inventory:
    assert row["status"] == "NOT_AVAILABLE"
    assert set(row["manifest_runs"].split(";")) == raw_memberships[row["task"]]
    assert set(row["absent_run_roots"].split(";")) == {"runs/" + run for run in runs}
    assert row["reason"] == "All four directory-rule run roots are absent; no record can exist at an allowed location."
assert len(inventory) > 17
print("Independent preflight verification: PASS; 83/83 missing; four allowed run roots absent.")
print("Audit Stages 1-6: NOT_RUN. No audit counts or seal verified.")
