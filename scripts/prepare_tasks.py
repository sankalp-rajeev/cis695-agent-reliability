#!/usr/bin/env python3
"""Prepare patch-independent SWE-bench registries; no pulls unless requested."""
import argparse
from pathlib import Path

from reliability.task_prep.core import WHEEL, manifest_ids, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--cohort', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--archives', type=Path, default=Path('/home/sankalp/cg_repos/task_archives'))
    parser.add_argument('--wheel', type=Path, default=WHEEL)
    parser.add_argument('--allow-pull', action='store_true')
    args = parser.parse_args()
    registry, failures, _ = prepare(manifest_ids(args.manifest), args.cohort, args.out,
                                   archives=args.archives, wheel=args.wheel, allow_pull=args.allow_pull)
    print(f"VERIFIED={len(registry['tasks'])} failures={len(failures)}")
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
