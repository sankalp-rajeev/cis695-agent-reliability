"""Exclude one oracle verdict as an infrastructure failure, with a reason.

Used when the harness reached a verdict that its own infrastructure detection
should have caught, for example a test that calls an external service which
answered 502. It does not relabel the result: `resolved` becomes null, never
true, the harness's original record is kept beside the new one, and the
exclusion is listed in the run's `exclusions.json`.

    .venv/bin/python scripts/exclude_oracle_record.py runs/pilot_14 psf__requests-1921 \\
        --reason "..." [--evidence "..."]...
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from reliability.oracle.records import exclude_task_as_infrastructure


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root")
    parser.add_argument("instance_id")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--evidence", action="append", default=[],
                        help="a file or log line supporting the reason; repeatable")
    args = parser.parse_args()

    run_root = pathlib.Path(args.run_root)
    record = exclude_task_as_infrastructure(
        run_root / "tasks" / args.instance_id, args.reason)

    log_path = run_root / "exclusions.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else []
    log.append({
        "instance_id": args.instance_id,
        "excluded_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "reason": args.reason,
        "evidence": args.evidence,
        "original_record": "oracle_record.harness_original.json",
    })
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"{args.instance_id}: outcome={record.outcome.value} "
          f"resolved={record.resolved} infrastructure_error={record.infrastructure_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
