"""Split manifests/main_100.csv into two seeded halves of 50.

Usage: split_manifest.py [--seed 20261007]

Writes manifests/main_50_a.csv and manifests/main_50_b.csv plus their sha256
sidecars. Refuses a split that is not disjoint, that does not cover main_100,
that is uneven by task type, or that contains a pilot instance.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reliability.benchmark.sampler import ManifestRow, write_manifest
from reliability.benchmark.split import FRONT_REPOS, SPLIT_SEED, split_halves

REPO = Path(__file__).resolve().parents[1]


def _load(path: Path) -> list[ManifestRow]:
    with path.open(newline="") as fh:
        return [
            ManifestRow(
                instance_id=row["instance_id"],
                repo=row["repo"],
                task_type=row["task_type"],
                base_commit=row["base_commit"],
            )
            for row in csv.DictReader(fh)
        ]


def _ids(path: Path) -> set[str]:
    with path.open(newline="") as fh:
        return {row["instance_id"] for row in csv.DictReader(fh)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SPLIT_SEED)
    parser.add_argument("--source", type=Path, default=REPO / "manifests" / "main_100.csv")
    parser.add_argument("--pilot", type=Path, default=REPO / "manifests" / "pilot.csv")
    parser.add_argument("--out-a", type=Path, default=REPO / "manifests" / "main_50_a.csv")
    parser.add_argument("--out-b", type=Path, default=REPO / "manifests" / "main_50_b.csv")
    args = parser.parse_args()

    source = _load(args.source)
    half_a, half_b = split_halves(source, seed=args.seed)
    ids_a = {row.instance_id for row in half_a}
    ids_b = {row.instance_id for row in half_b}
    ids_src = {row.instance_id for row in source}
    pilot = _ids(args.pilot)

    if ids_a & ids_b:
        raise SystemExit(f"halves overlap: {sorted(ids_a & ids_b)}")
    if ids_a | ids_b != ids_src:
        raise SystemExit("union of the halves is not the source manifest")
    leaked = (ids_a | ids_b) & pilot
    if leaked:
        raise SystemExit(f"pilot instances in a half: {sorted(leaked)}")

    digest_a = write_manifest(args.out_a, half_a)
    digest_b = write_manifest(args.out_b, half_b)
    flask = [row for row in (*half_a, *half_b) if row.repo == "pallets/flask"]
    front = [row.instance_id for row in half_a if row.repo in FRONT_REPOS]
    print(f"seed {args.seed}")
    print(f"main_50_a  n={len(half_a)}  {digest_a}")
    print(f"main_50_b  n={len(half_b)}  {digest_b}")
    print(f"half A front ({len(front)}): {front}")
    for row in flask:
        half = "A" if row in half_a else "B"
        print(f"flask {row.instance_id} lands in half {half}")
    print("disjoint: yes")
    print("union equals source: yes")
    print("pilot overlap: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
