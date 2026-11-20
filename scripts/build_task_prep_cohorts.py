#!/usr/bin/env python3
"""Inspect local images only, project stored run statuses, publish nested IDs."""

import argparse
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.task_prep.cohorts import build

if __name__ == "__main__":
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-dir", type=Path, default=Path("configs/e2e/cohorts"))
    parser.add_argument(
        "--eligibility-out",
        type=Path,
        default=Path("reports/next_phases/task_prep/eligibility.json"),
    )
    parser.add_argument(
        "--status-out", type=Path, default=Path("reports/next_phases/task_prep/run_status.json")
    )
    args = parser.parse_args()
    build(args.cohort_dir, args.eligibility_out, args.status_out)
