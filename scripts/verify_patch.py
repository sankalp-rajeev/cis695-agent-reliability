"""CLI for verifying a frozen patch (Phase 4–7).

    .venv/bin/python scripts/verify_patch.py runs/<exp>/tasks/<instance_id>
    .venv/bin/python scripts/verify_patch.py <task_dir> --no-container
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from reliability.verifier.run import verify_task


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", help="a tasks/<instance_id>/ directory")
    parser.add_argument("--config", action="append", dest="configs",
                        help="policy to apply; repeatable. Default: full and baseline")
    parser.add_argument("--no-container", action="store_true",
                        help="integrity only; regression and static record DISABLED")
    parser.add_argument("--replace", action="store_true",
                        help="overwrite an existing verification record")
    args = parser.parse_args()

    configs = tuple(args.configs) if args.configs else ("full", "baseline")
    records = verify_task(
        pathlib.Path(args.task_dir),
        configs=configs,
        use_container=not args.no_container,
        replace=args.replace,
    )
    for record in records:
        print(f"\n=== verification: {record.instance_id} [{record.verifier_config}] ===")
        for kind, signal in record.signals.items():
            suffix = f" ({signal.absence.value})" if signal.absence else ""
            print(f"  {kind.value:<13}: {signal.outcome.value}{suffix}  {signal.detail}")
        print(f"  decision     : {record.decision.decision.value} "
              f"[{record.decision.policy_version}]")
        for reason in record.decision.reasons:
            print(f"                 - {reason}")
        print(f"  complete     : {record.is_complete} "
              f"({len(record.signals_reported)}/4 layers reported)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
