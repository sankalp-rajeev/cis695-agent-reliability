#!/usr/bin/env python3
"""Compare three fresh preparations with phase4_launch.validate_inputs."""

import argparse
import gzip
import json
from dataclasses import asdict
from pathlib import Path

import phase4_launch as launch
from reliability.env import assert_clean_interpreter
from reliability.task_prep.core import FROZEN, PROVENANCE, WHEEL, write_new


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    specs = launch.validate_inputs(
        FROZEN, Path("/home/sankalp/cg_repos/task_archives"), WHEEL, PROVENANCE, launch.PREFLIGHT
    )
    expected = {s.instance_id: s for s in specs}
    actual = json.loads(args.registry.read_text())["tasks"]
    if {t["repo"] for t in actual} != {"django/django", "sympy/sympy", "pytest-dev/pytest"} or len(
        actual
    ) != 3:
        raise ValueError("Parity requires exactly Django, SymPy and pytest representatives")
    results = []
    for task in actual:
        spec = expected[task["instance_id"]]
        identity = json.loads(
            (launch.PREFLIGHT / "tasks" / task["instance_id"] / "identity.json").read_text()
        )
        runner = asdict(spec.runner)
        if runner["name"] != "django":
            runner["django_parallel_one"] = None
        fields = {
            "archive_sha256": spec.source.archive_sha256,
            "image_id": spec.image_id,
            "pre_install_spec": spec.source.pre_install.resolve(),
            "preflight_identity": {
                k: identity[k] for k in ("image_id", "base_commit", "archive_sha256")
            },
            "runner": runner,
        }
        observed = {
            "archive_sha256": task["archive"]["sha256"],
            "image_id": task["image"]["id"],
            "pre_install_spec": task["pre_install"]["spec"],
            "preflight_identity": task["preflight_identity"],
            "runner": task["runner"],
        }
        baseline = json.loads(
            gzip.decompress(
                (
                    launch.PREFLIGHT / "tasks" / task["instance_id"] / "source_receipt.json.gz"
                ).read_bytes()
            )
        )
        fresh = json.loads(Path(task["integrity_preflight"]["receipt_path"]).read_text())
        # File receipts carry all source byte proofs, not container names/paths.
        checks = {k: fields[k] == observed[k] for k in fields}
        checks["source_receipt"] = baseline == fresh
        results.append({"instance_id": task["instance_id"], "checks": checks, "expected": fields})
    passed = all(all(r["checks"].values()) for r in results)
    write_new(
        args.out, {"passed": passed, "authority": "phase4_launch.validate_inputs", "tasks": results}
    )
    print(
        json.dumps(
            {
                "passed": passed,
                "tasks": [
                    {"instance_id": r["instance_id"], "checks": r["checks"]} for r in results
                ],
            },
            indent=2,
        )
    )
    return not passed


if __name__ == "__main__":
    raise SystemExit(main())
