"""Build a task manifest (Phase 2.3).

Usage: build_manifest.py [--out manifests/pilot.csv] [--n 10] [--seed 695]
                          [--exclude-manifest manifests/pilot.csv ...]

Rerunning with the same seed must reproduce the identical content hash; that is
the gate. The hash is printed so it can be pasted into the checklist.

`--exclude-manifest` reads the `instance_id` column of one or more existing
manifests and removes those instances from the population before sampling.
Used to draw the main-study manifest excluding the pilot's instances, which the
verifier was tuned looking at (selection policy, V4 budget, the v1.3.0 decision
rule) and which a later run must not be measured against.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from reliability.benchmark.sampler import build_pilot_manifest


def _load_exclusions(paths: list[Path]) -> frozenset[str]:
    ids: set[str] = set()
    for path in paths:
        with path.open(newline="") as fh:
            ids.update(row["instance_id"] for row in csv.DictReader(fh))
    return frozenset(ids)


parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, default=Path("manifests/pilot.csv"))
parser.add_argument("--n", type=int, default=10)
parser.add_argument("--seed", type=int, default=695)
parser.add_argument(
    "--exclude-manifest", type=Path, nargs="*", default=[],
    help="manifest CSV(s) whose instance_id column is excluded from sampling")
args = parser.parse_args()

exclude = _load_exclusions(args.exclude_manifest)
if exclude:
    print(f"excluding {len(exclude)} instance(s) from {len(args.exclude_manifest)} "
          f"manifest(s): {sorted(exclude)}")

rows, digest = build_pilot_manifest(args.out, n=args.n, seed=args.seed, exclude=exclude)

for row in rows:
    print(f"  {row.instance_id:34s} {row.repo:26s} {row.task_type}")

print()
print("by task type:", dict(sorted(Counter(r.task_type for r in rows).items())))
print("distinct repositories:", len({r.repo for r in rows}))
print(f"seed: {args.seed}")
print(f"content hash: {digest}")
print(f"written: {args.out}")
