#!/usr/bin/env python3
"""Export the validated Phase 4 freeze into the shared task registry schema."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import phase4_launch as launch
from reliability.env import assert_clean_interpreter
from reliability.task_prep.core import (
    FROZEN,
    PROVENANCE,
    ROOT,
    WHEEL,
    frozen_metadata,
    run,
    sha,
    write_new,
)


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "configs/e2e/task_specs_phase4.json")
    args = parser.parse_args()
    specs = launch.validate_inputs(
        FROZEN, Path("/home/sankalp/cg_repos/task_archives"), WHEEL, PROVENANCE, launch.PREFLIGHT
    )
    metadata = frozen_metadata()
    tasks = []
    for spec in specs:
        proof = spec.source.pre_install
        row = {k: getattr(proof, k) for k in ("instance_id", "repo", "version", "base_commit")}
        receipt_path = launch.PREFLIGHT / "tasks" / spec.instance_id / "source_receipt.json.gz"
        identity = json.loads((receipt_path.parent / "identity.json").read_text())
        runner = asdict(spec.runner)
        if runner["name"] != "django":
            runner["django_parallel_one"] = None
        resolved = proof.resolve()
        tasks.append(
            {
                **row,
                "image": {"tag": metadata[spec.instance_id]["image_tag"], "id": spec.image_id},
                "archive": {
                    "path": str(spec.source.archive_path.resolve()),
                    "sha256": spec.source.archive_sha256,
                    "pax_comment": spec.source.base_commit,
                },
                "pre_install": {
                    "wheel_sha256": resolved["wheel_sha256"],
                    "dataset_projection_sha256": proof.dataset_projection_sha256,
                    "spec": resolved,
                },
                "integrity_preflight": {
                    "status": "VERIFIED",
                    "receipt_path": str(receipt_path.resolve()),
                    "receipt_sha256": sha(receipt_path),
                },
                "runner": runner,
                "origin": "phase4_freeze",
                "dataset_projection_row": row,
                "preflight_identity": {
                    k: identity[k] for k in ("image_id", "base_commit", "archive_sha256")
                },
                "runner_provenance": {
                    "effective_name": "sympy" if row["repo"] == "sympy/sympy" else runner["name"],
                    "source": "phase4_launch.validate_inputs",
                },
            }
        )
    write_new(
        args.out,
        {
            "schema": "task_spec_registry/1",
            "cohort": "phase4",
            "built_by_commit": run(["git", "rev-parse", "HEAD"], text=True).stdout.strip(),
            "tasks": tasks,
        },
    )
    print(f"Exported {len(tasks)} validated frozen tasks")


if __name__ == "__main__":
    raise SystemExit(main())
