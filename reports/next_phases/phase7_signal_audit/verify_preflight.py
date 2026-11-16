"""Independent standard-library availability check, not a Stage 6 seal."""

import csv
import json
from pathlib import Path


base = Path(__file__).resolve().parents[3]
output = Path(__file__).resolve().parent
raw = json.loads((base / "reports/v2_discovery_cleanup/frozen_83/tasks.json").read_text())
expected_ids = {item["instance_id"] for item in raw}
assert len(raw) == len(expected_ids) == 83
runs = ["main_2_rerun_mpl", "main_3_rerun_infra", "main_50_a", "main_50_b"]
raw_memberships = {task: set() for task in expected_ids}
for run in runs:
    with (base / "manifests" / (run + ".csv")).open(newline="") as f:
        rows = csv.reader(f)
        header = next(rows)
        column = next(header.index(name) for name in ("instance_id", "task_id", "id") if name in header)
        for row in rows:
            if row[column] in expected_ids:
                raw_memberships[row[column]].add(run)
with (output / "record_inventory.csv").open(newline="") as f:
    inventory = list(csv.DictReader(f))
assert len(inventory) == 83
assert {row["task"] for row in inventory} == expected_ids
missing = []
for row in inventory:
    assert set(row["manifest_runs"].split(";")) == raw_memberships[row["task"]]
    reruns = []
    main = []
    for run in runs:
        location = base / "runs" / run / "tasks" / row["task"]
        if location.is_dir():
            (reruns if run.startswith("main_2_") or run.startswith("main_3_") else main).append(location)
    assert len(reruns) <= 1 and len(main) <= 1
    directory = next(iter(reruns), next(iter(main), None))
    path = directory / "verification_record.full.json" if directory else None
    assert row["record_path"] == (str(path.relative_to(base)) if path else "")
    exists = bool(path and path.is_file())
    assert row["status"] == ("AVAILABLE" if exists else "NOT_AVAILABLE")
    assert row["reason"] == (
        "Directory-rule selected record exists; no outcome inferred." if exists
        else "Directory-rule selected record is missing; no fallback after selecting a directory."
    )
    if not exists:
        missing.append(row)
with (output / "missing_records.csv").open(newline="") as f:
    assert list(csv.DictReader(f)) == missing
assert len(missing) <= 17
print(f"Independent preflight verification: PASS; {83-len(missing)}/83 available; {len(missing)} missing.")
print("Scope: record availability and selection only; not Stage 6.")
