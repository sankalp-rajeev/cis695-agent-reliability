#!/usr/bin/env python3
"""Export prepared registries for the pinned E2E v1.4.1 validator."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from reliability.task_prep import frozen_export as adapter


def export_ordered_registries(registries, order, output):
    adapter.assert_clean_interpreter()
    if (
        adapter.git("cat-file", "-t", adapter.TAG) != "tag"
        or adapter.git("rev-parse", adapter.TAG + "^{}") != adapter.COMMIT
    ):
        raise ValueError("Frozen annotated tag identity changed")
    # The tag is the schema authority even when the E2E checkout has advanced.
    frozen = {}
    for path, expected in adapter.FROZEN_HASHES.items():
        raw = subprocess.check_output(["git", "show", f"{adapter.TAG}:{path}"], cwd=adapter.ROOT)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Frozen schema/input identity changed: " + path)
        frozen[path] = raw

    output = output.absolute()
    sidecar = output.with_suffix(".provenance.json")
    for path in (output, sidecar):
        if path.exists() or path.is_symlink():
            raise FileExistsError("Output already exists: " + str(path))

    ids = [slot["instance_id"] for slot in json.loads(order.read_text())]
    sources, prepared = [], {}
    for path in registries:
        path = path.resolve()
        source = json.loads(path.read_text())
        rows = source.pop("tasks")
        if source["schema"] != "task_spec_registry/1":
            raise ValueError("Unsupported source registry schema")
        sources.append(
            {
                "path": str(path),
                "sha256": adapter.sha(path),
                "metadata": source,
                "task_order": [row["instance_id"] for row in rows],
            }
        )
        for row in rows:
            iid = row["instance_id"]
            if iid in prepared:
                raise ValueError("Duplicate source registry ID: " + iid)
            prepared[iid] = row

    frozen_ids = set(frozen["configs/e2e/tasks_83.txt"].decode().splitlines())
    if not ids or len(ids) != len(set(ids)) or set(ids) != set(prepared) or set(ids) & frozen_ids:
        raise ValueError(
            "Ordered IDs must match the prepared registries and be disjoint from the frozen IDs"
        )

    stable_wheel = adapter.INPUTS / adapter.WHEEL.name
    adapter.copy_verified(adapter.WHEEL, stable_wheel, adapter.WHEEL_SHA256)
    entries, provenance = [], {}
    copied = {str(stable_wheel): adapter.WHEEL_SHA256}
    for iid in ids:
        row = prepared[iid]
        if set(row) != adapter.TASK_FIELDS | adapter.SIDECAR_FIELDS:
            raise ValueError("Unexpected source task fields: " + iid)
        receipt = row["integrity_preflight"]
        if row["origin"] != "prepared" or receipt["status"] != "VERIFIED":
            raise ValueError("Task must be prepared and VERIFIED: " + iid)
        pre = row["pre_install"].copy()
        if (
            set(pre) != {"wheel_sha256", "dataset_projection_sha256", "spec"}
            or pre["wheel_sha256"] != adapter.WHEEL_SHA256
        ):
            raise ValueError("Unexpected source pre-install proof: " + iid)
        projection = Path(receipt["receipt_path"]).with_name("dataset_projection.json")
        digest = pre["dataset_projection_sha256"]
        stable_projection = adapter.INPUTS / f"dataset_projection_{digest}.json"
        adapter.copy_verified(projection, stable_projection, digest)
        pre.update(wheel_path=str(stable_wheel), dataset_projection_path=str(stable_projection))
        entries.append({**{key: row[key] for key in adapter.TASK_FIELDS}, "pre_install": pre})
        provenance[iid] = {key: row[key] for key in adapter.SIDECAR_FIELDS}
        copied[str(stable_projection)] = digest

    adapter.write_new(output, {**sources[0]["metadata"], "tasks": entries})
    adapter.write_new(
        sidecar,
        {
            "registry_path": str(output),
            "registry_sha256": adapter.sha(output),
            "source_registries": sources,
            "frozen_tag": adapter.TAG,
            "frozen_commit": adapter.COMMIT,
            "frozen_input_sha256": adapter.FROZEN_HASHES,
            "stable_input_sha256": copied,
            "tasks": provenance,
        },
    )
    print(f"EXPORTED: {len(entries)} tasks, registry SHA-256 {adapter.sha(output)}")


def main():
    if len(sys.argv) == 1:
        adapter.export()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registries", type=Path, nargs="+", required=True)
    parser.add_argument("--order", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    export_ordered_registries(args.registries, args.order, args.out)


if __name__ == "__main__":
    main()
