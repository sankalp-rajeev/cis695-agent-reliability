#!/usr/bin/env python3
"""Dry-run 200/500 disk and time projections; registry metadata only."""

import argparse
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.task_prep.projection import project

if __name__ == "__main__":
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-dir", type=Path, default=Path("configs/e2e/cohorts"))
    parser.add_argument(
        "--metadata-cache", type=Path, default=Path("runs/task_prep_image_metadata")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("reports/next_phases/task_prep/projection.json")
    )
    args = parser.parse_args()
    project(args.cohort_dir, args.metadata_cache, args.out)
