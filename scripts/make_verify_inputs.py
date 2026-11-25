#!/usr/bin/env python3
"""Copy hash-checked Phase 2 patches into an E2E verify-only input folder."""

import argparse
import json
import re
from pathlib import Path

from reliability.study_inputs import copy_inputs

if __package__:
    from .run_e2e import manifest_ids
else:
    from run_e2e import manifest_ids

ROOT = Path(__file__).resolve().parents[1]


def build_verify_inputs(manifest: Path, ids: Path, output: Path, *, repo_root: Path = ROOT):
    return copy_inputs(manifest, ids, manifest_ids(ids), output, root=repo_root.resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Phase 2 tasks.json")
    parser.add_argument("--ids", type=Path, required=True, help="ordered instance ID list")
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", args.run_name):
        parser.error("--run-name must be a safe single directory name")
    output = ROOT / "runs/study_v1_5/verify_inputs" / args.run_name
    print(json.dumps(build_verify_inputs(args.manifest, args.ids, output)))


if __name__ == "__main__":
    main()
