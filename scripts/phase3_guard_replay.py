#!/usr/bin/env python3
"""Correct the three stored collection-only receipts without executing any tests."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from reliability.verifier.collection import classify_collector_failure
from reliability.verifier.id_validation import IDValidation, merge_native

ROOT = Path(__file__).resolve().parents[1]


def main(args):
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    source = ROOT / "reports/next_phases/phase3_fix3/collection_only"
    rows = []
    inputs = {}
    for folder in sorted(source.iterdir()):
        data = json.loads((folder / "collection.json").read_text())
        messages = json.loads((folder / "messages.json").read_text())
        metadata = json.loads((folder / "summary.json").read_text())
        groups = {g["module"]: g for g in data["groups"]}
        corrected = []
        for row in data["records"]:
            static_reason = row.get("static_reason", "")
            # The old receipt retained the static reason and owner-instance plan.
            planned = (
                ()
                if static_reason
                else tuple(row.get("owner_instances", ()))
                if row.get("expanded")
                else ()
                if static_reason
                else (row["selected_id"],)
            )
            static = IDValidation(
                row["selected_id"],
                row["category"],
                runnable_ids=planned if not static_reason else (),
                reason=static_reason,
                owner=row["owner"],
                owner_is_testcase=row["owner_is_testcase"],
                decorators=tuple(row["decorators"]),
                expanded=bool(row.get("expanded")),
            )
            native = {}
            if not row["reason"]:
                native = {
                    tid: {"ids": [tid], "completed": True, "returncode": 0}
                    for tid in (planned or (row["selected_id"],))
                }
            else:
                message = messages.get(row["message_sha256"], "")
                for tid, reason in row["invalid_instances"]:
                    module = tid.split("::")[0]
                    group = groups[module]
                    code = group.get("returncode")
                    failed = (
                        reason
                        in ("native_load_error", "collection_timeout", "native_identity_mismatch")
                        or code != 0
                    )
                    status = classify_collector_failure(message) if failed else "COMPLETE"
                    native[tid] = {
                        "ids": [],
                        "reason": status.lower() if failed else "native_not_found",
                        "message": message,
                        "completed": not failed,
                        "collection_status": status,
                        "returncode": code,
                    }
                for tid in planned:
                    native.setdefault(tid, {"ids": [tid], "completed": True, "returncode": 0})
                if not planned:
                    native.setdefault(
                        row["selected_id"],
                        {
                            "ids": [],
                            "reason": "native_not_found",
                            "completed": True,
                            "returncode": 0,
                        },
                    )
            updated = merge_native((static,), native)[0]
            corrected.append(updated.to_dict())
        counts = Counter(r["validation_status"] for r in corrected)
        rows.append(
            {
                "instance_id": folder.name,
                "selected_slots": len(corrected),
                "VALID": counts["VALID"],
                "INVALID_ID": counts["INVALID_ID"],
                "COLLECTION_ERROR": counts["COLLECTION_ERROR"],
                "RUNNER_UNAVAILABLE": counts["RUNNER_UNAVAILABLE"],
                "old_INVALID_ID": metadata["INVALID_ID"],
                "tests_executed": 0,
                "scope": "corrected stored collection receipts; no new collection/execution",
            }
        )
        (args.output / (folder.name + ".json")).write_text(json.dumps(corrected, indent=2) + "\n")
        for name in ("collection.json", "messages.json", "summary.json"):
            path = folder / name
            inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    with (args.output / "corrected_counts.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "input_sha256": inputs,
                "scope": "reclassification only; immutable original receipts retained",
                "correctness_labels_read": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
