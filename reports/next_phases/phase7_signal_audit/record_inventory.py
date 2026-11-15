"""Label-free preflight: inspect approved IDs and directory existence only."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUNS = ("main_2_rerun_mpl", "main_3_rerun_infra", "main_50_a", "main_50_b")


def main():
    tasks = json.loads(
        (ROOT / "reports/v2_discovery_cleanup/frozen_83/tasks.json").read_text()
    )
    ids = [t["instance_id"] for t in tasks]
    assert len(ids) == len(set(ids)) == 83
    members = {}
    for run in RUNS:
        with (ROOT / "manifests" / (run + ".csv")).open(newline="") as f:
            reader = csv.DictReader(f)
            key = next(k for k in ("instance_id", "task_id", "id") if k in reader.fieldnames)
            members[run] = {row[key] for row in reader}
    # This preflight deliberately stops before any record can be opened.
    # A restored run directory requires another, full record-selection pass.
    assert all(not (ROOT / "runs" / run).exists() for run in RUNS)
    reason = "All four directory-rule run roots are absent; no record can exist at an allowed location."
    with (OUT / "missing_records.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "task", "manifest_runs", "status", "reason", "absent_run_roots"
        ])
        writer.writeheader()
        for task in ids:
            membership = [r for r in RUNS if task in members[r]]
            assert any(r in membership for r in ("main_50_a", "main_50_b"))
            writer.writerow({
                "task": task,
                "manifest_runs": ";".join(membership),
                "status": "NOT_AVAILABLE",
                "reason": reason,
                "absent_run_roots": ";".join("runs/" + r for r in RUNS),
            })
    print("Frozen tasks: 83; missing records: 83; hard-stop threshold: >17.")


if __name__ == "__main__":
    main()
