"""Pull a manifest's images in batches, before the experiment starts.

Failures are appended to a log that is not an experiment stat file. Nothing
under runs/ is written. A failed pull is not an infrastructure failure and
does not enter a half's summary.

Usage:
    .venv/bin/python scripts/prepull_images.py manifests/main_50_a.csv

Repo-grouped pull-and-delete (pull one repository, run it, remove its images,
then the next) is not implemented. That scheme is only a proposal for the
case where the layer-union need exceeds free space minus 40 GB.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reliability.verifier.container import image_for

#: 40 GiB. The C: volume is where the WSL disk lives, so a pull that grows
#: the Docker data disk is charged against this number.
MIN_FREE_BYTES = 40 * 1024 ** 3
DISK_PATH = Path("/mnt/c")


def _instances(path: Path) -> list[str]:
    import csv
    with path.open(newline="") as fh:
        return [row["instance_id"] for row in csv.DictReader(fh)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument(
        "--failure-log", type=Path,
        default=Path("logs/prepull_failures.log"),
    )
    parser.add_argument("--disk", type=Path, default=DISK_PATH)
    parser.add_argument("--min-free-bytes", type=int, default=MIN_FREE_BYTES)
    args = parser.parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")

    images = [image_for(instance_id) for instance_id in _instances(args.manifest)]
    args.failure_log.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    pulled = 0
    for start in range(0, len(images), args.batch_size):
        batch = images[start:start + args.batch_size]
        print(f"batch {start // args.batch_size + 1}: {len(batch)} image(s)", flush=True)
        for image in batch:
            free = shutil.disk_usage(args.disk).free
            if free < args.min_free_bytes:
                print(
                    f"STOP {args.disk} free={free} bytes "
                    f"is below {args.min_free_bytes}; no further pulls",
                    flush=True,
                )
                print(
                    f"pulled={pulled} failed={failures} stopped=disk "
                    f"failure_log={args.failure_log}"
                )
                return 2
            proc = subprocess.run(
                ["docker", "pull", image], check=False,
            )
            if proc.returncode != 0:
                failures += 1
                line = (
                    f"{datetime.now(UTC).isoformat()} FAIL {image} "
                    f"exit={proc.returncode}\n"
                )
                with args.failure_log.open("a", encoding="utf-8") as fh:
                    fh.write(line)
                print(f"  FAIL {image} (logged to {args.failure_log})", flush=True)
            else:
                pulled += 1
                print(f"  ok   {image}", flush=True)
    print(f"pulled={len(images) - failures} failed={failures} "
          f"failure_log={args.failure_log}")
    print("failures are not experiment stats")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
