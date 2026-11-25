#!/usr/bin/env python3
"""Publish a new registry from disjoint already VERIFIED task registries."""

import argparse
import json
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.task_prep.core import run, write_new

if __name__ == "__main__":
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registries", type=Path, nargs="+", required=True)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    entries = []
    for path in args.registries:
        source = json.loads(path.read_text())
        if source["schema"] != "task_spec_registry/1":
            raise ValueError("Unsupported registry schema")
        entries.extend(source["tasks"])
    if len(entries) != len({t["instance_id"] for t in entries}):
        raise ValueError("Source registries overlap")
    if any(t["integrity_preflight"]["status"] != "VERIFIED" for t in entries):
        raise ValueError("Unverified task in source registry")
    write_new(
        args.out,
        {
            "schema": "task_spec_registry/1",
            "cohort": args.cohort,
            "built_by_commit": run(["git", "rev-parse", "HEAD"], text=True).stdout.strip(),
            "tasks": sorted(entries, key=lambda t: t["instance_id"]),
        },
    )
    print(f"Published {len(entries)} VERIFIED tasks")
