"""Print FSR_agent, FAR_verifier, and coverage for a run directory.

    .venv/bin/python scripts/metrics.py runs/pilot_15

No model calls. V4 NOT_AVAILABLE stays in the coverage denominator.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reliability.analysis.metrics import compute_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    report = compute_metrics(args.run)
    print(f"run {args.run}")
    print(f"n={report['n']}  valid={report['n_valid']}  "
          f"empty={report['n_empty']}  infra={report['n_infra']}")
    print(f"V4 NOT_AVAILABLE inside coverage denominator: "
          f"{report['n_v4_not_available_in_coverage']}")
    for name in ("fsr_agent", "far_verifier", "coverage"):
        block = report[name]
        rate = "n/a" if block["rate"] is None else f"{block['rate']:.4f}"
        print(f"{name:16} {block['numerator']}/{block['denominator']}  {rate}")
    print()
    print(f"{'instance':42} {'claim':12} {'decision':8} {'v4':14} {'oracle':14} valid")
    for row in report["rows"]:
        print(f"{row['instance_id']:42} {str(row['claim']):12} "
              f"{str(row['decision']):8} {str(row['reproduction']):14} "
              f"{str(row['oracle']):14} {row['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
