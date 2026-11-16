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
    rows = []
    for task in ids:
        membership = [r for r in RUNS if task in members[r]]
        assert any(r in membership for r in ("main_50_a", "main_50_b"))
        directories = [ROOT / "runs" / r / "tasks" / task for r in RUNS]
        present = [p for p in directories if p.is_dir()]
        rerun = [p for p in present if p.parts[-3] in RUNS[:2]]
        originals = [p for p in present if p.parts[-3] in RUNS[2:]]
        assert len(rerun) <= 1 and len(originals) <= 1
        selected = (rerun or originals or [None])[0]
        record = selected / "verification_record.full.json" if selected else None
        available = record is not None and record.is_file()
        if selected:
            assert selected.parts[-3] in membership
        rows.append({
            "task": task,
            "manifest_runs": ";".join(membership),
            "record_path": str(record.relative_to(ROOT)) if record else "",
            "status": "AVAILABLE" if available else "NOT_AVAILABLE",
            "reason": "Directory-rule selected record exists; no outcome inferred."
                if available else "Directory-rule selected record is missing; no fallback after selecting a directory.",
        })
    fields = ["task", "manifest_runs", "record_path", "status", "reason"]
    for name, selected_rows in (
        ("record_inventory.csv", rows),
        ("missing_records.csv", [r for r in rows if r["status"] == "NOT_AVAILABLE"]),
    ):
        with (OUT / name).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected_rows)
    missing = sum(r["status"] == "NOT_AVAILABLE" for r in rows)
    print(f"Frozen tasks: {len(ids)}; available records: {len(ids)-missing}; missing records: {missing}; hard-stop threshold: >17.")


if __name__ == "__main__":
    main()
