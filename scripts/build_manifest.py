"""Build the pilot task manifest (Phase 2.3).

Usage: build_manifest.py [--out manifests/pilot.csv] [--n 10] [--seed 695]

Rerunning with the same seed must reproduce the identical content hash; that is
the gate. The hash is printed so it can be pasted into the checklist.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from reliability.benchmark.sampler import build_pilot_manifest

parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, default=Path("manifests/pilot.csv"))
parser.add_argument("--n", type=int, default=10)
parser.add_argument("--seed", type=int, default=695)
args = parser.parse_args()

rows, digest = build_pilot_manifest(args.out, n=args.n, seed=args.seed)

for row in rows:
    print(f"  {row.instance_id:34s} {row.repo:26s} {row.task_type}")

print()
print("by task type:", dict(sorted(Counter(r.task_type for r in rows).items())))
print("distinct repositories:", len({r.repo for r in rows}))
print(f"seed: {args.seed}")
print(f"content hash: {digest}")
print(f"written: {args.out}")
