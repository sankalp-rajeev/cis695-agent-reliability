"""Lossless adapter for the immutable E2E v1.4.1 registry consumer."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from reliability.env import assert_clean_interpreter
from reliability.task_prep.core import ROOT, WHEEL, sha, write_new
from reliability.verifier.pre_install import WHEEL_SHA256

TAG = "e2e-v1.4.1-frozen"
COMMIT = "c5b352c83c6bd7e9afdcb465bf966535543192fc"
E2E = Path("/home/sankalp/projects/wt-e2e")
INPUTS = E2E / "runs/task_prep_inputs"
SOURCE = ROOT / "configs/e2e/task_specs_main100_rest10_final.json"
OUTPUT = ROOT / "configs/e2e/task_specs_add9_e2e_v141.json"
SIDECAR = OUTPUT.with_suffix(".provenance.json")
ORDER = ROOT / "configs/e2e/cohorts/main92_run_order.txt"
FROZEN_HASHES = {
    "docs/TASK_SPEC_SCHEMA.md": "adc57f77912799eddd1dcf0f3832abd93601c57763f05e837461e7fee49c596e",
    "src/reliability/verifier/task_specs.py": "f20461bc970ae7a3bf09802802e3b4c6ae496f4132cb129e0732eb642c4dbbf5",
    "configs/e2e/task_specs_83.json": "9e55c5a82501753f19f5f83cdcab69afe178a9800aaa848918867a5a8af1d5fb",
    "configs/e2e/tasks_83.txt": "09555d42c7c712ecd11cee691093eede7e28b29d95e866be2dfacffb1c25e9b9",
}
TASK_FIELDS = {
    "instance_id",
    "repo",
    "version",
    "base_commit",
    "image",
    "archive",
    "pre_install",
    "integrity_preflight",
    "runner",
    "origin",
}
SIDECAR_FIELDS = {"dataset_projection_row", "preflight_identity", "runner_provenance"}


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def frozen_inputs():
    if git("cat-file", "-t", TAG) != "tag" or git("rev-parse", TAG + "^{}") != COMMIT:
        raise ValueError("Frozen annotated tag identity changed")
    if git("rev-parse", "HEAD", cwd=E2E) != COMMIT or git("status", "--porcelain", cwd=E2E):
        raise ValueError("Frozen runner checkout must be clean at c5b352c")
    inputs = {}
    for path, expected in FROZEN_HASHES.items():
        raw = subprocess.check_output(["git", "show", TAG + ":" + path], cwd=ROOT)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Frozen schema/input identity changed: " + path)
        inputs[path] = raw
    return inputs


def copy_verified(source, destination, expected):
    """Copy bytes atomically to the sole authorized frozen-worktree folder."""
    if sha(source) != expected:
        raise ValueError("Source input SHA-256 mismatch: " + str(source))
    if destination.parent != INPUTS or INPUTS.is_symlink():
        raise ValueError("Input copy is outside the authorized folder")
    relative = str(destination.relative_to(E2E))
    subprocess.run(["git", "check-ignore", "--quiet", relative], cwd=E2E, check=True)
    INPUTS.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or sha(destination) != expected:
            raise ValueError("Existing stable input differs; refusing replacement")
        return destination
    fd, temporary = tempfile.mkstemp(prefix="." + destination.name, dir=INPUTS)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as stream:
            shutil.copyfileobj(stream, output)
            output.flush()
            os.fsync(output.fileno())
        if sha(temporary) != expected:
            raise ValueError("Copied input SHA-256 mismatch")
        os.link(temporary, destination)
    finally:
        os.unlink(temporary)
    if sha(destination) != expected:
        raise ValueError("Published input SHA-256 mismatch")
    return destination


def export():
    assert_clean_interpreter()
    frozen = frozen_inputs()
    for path in (OUTPUT, SIDECAR, ORDER):
        if path.exists():
            raise FileExistsError("Output already exists: " + str(path))
    source = json.loads(SOURCE.read_text())
    rows = source["tasks"]
    ids = [t["instance_id"] for t in rows]
    if len(ids) != 9 or len(set(ids)) != 9:
        raise ValueError("Expected nine distinct additions")
    if any(i.startswith("psf__requests-") or i == "sphinx-doc__sphinx-10614" for i in ids):
        raise ValueError("Ineligible or failed task in additions")
    frozen_order = frozen["configs/e2e/tasks_83.txt"].decode().splitlines()
    if len(frozen_order) != 83 or len(set(frozen_order)) != 83 or set(ids) & set(frozen_order):
        raise ValueError("Invalid frozen order or overlapping additions")
    stable_wheel = INPUTS / WHEEL.name
    copy_verified(WHEEL, stable_wheel, WHEEL_SHA256)
    entries, provenance, copied = [], {}, {str(stable_wheel): WHEEL_SHA256}
    for row in sorted(rows, key=lambda t: t["instance_id"]):
        if set(row) != TASK_FIELDS | SIDECAR_FIELDS:
            raise ValueError("Unexpected source task fields; no metadata may be lost")
        if row["origin"] != "prepared" or row["integrity_preflight"]["status"] != "VERIFIED":
            raise ValueError("Additions must be prepared and VERIFIED")
        entry = {key: copy.deepcopy(row[key]) for key in TASK_FIELDS}
        pre = entry["pre_install"]
        if set(pre) != {"wheel_sha256", "dataset_projection_sha256", "spec"}:
            raise ValueError("Unexpected source pre_install fields")
        if pre["wheel_sha256"] != WHEEL_SHA256:
            raise ValueError("Wrong pinned wheel")
        projection = (
            SOURCE.parent
            / (SOURCE.stem + "_evidence")
            / row["instance_id"]
            / "dataset_projection.json"
        )
        digest = pre["dataset_projection_sha256"]
        stable_projection = INPUTS / ("dataset_projection_" + digest + ".json")
        copy_verified(projection, stable_projection, digest)
        pre["wheel_path"] = str(stable_wheel)
        pre["dataset_projection_path"] = str(stable_projection)
        # Keep the resolved spec, archive and receipt identities byte-for-byte.
        provenance[row["instance_id"]] = {key: row[key] for key in SIDECAR_FIELDS}
        copied[str(stable_projection)] = digest
        entries.append(entry)
    write_new(
        OUTPUT,
        {
            "schema": source["schema"],
            "cohort": "main92_additions",
            "built_by_commit": git("rev-parse", "HEAD"),
            "tasks": entries,
        },
    )
    write_new(
        SIDECAR,
        {
            "registry_path": str(OUTPUT),
            "registry_sha256": sha(OUTPUT),
            "source_registry_path": str(SOURCE),
            "source_registry_sha256": sha(SOURCE),
            "source_registry_metadata": {k: v for k, v in source.items() if k != "tasks"},
            "source_task_order": ids,
            "frozen_tag": TAG,
            "frozen_commit": COMMIT,
            "frozen_input_sha256": FROZEN_HASHES,
            "stable_input_sha256": copied,
            "tasks": provenance,
        },
    )
    ORDER.parent.mkdir(parents=True, exist_ok=True)
    with ORDER.open("x") as stream:
        stream.write("\n".join(frozen_order + sorted(ids)) + "\n")
    if git("status", "--porcelain", cwd=E2E):
        raise ValueError("Frozen runner checkout became dirty")
    print(
        json.dumps(
            {
                "tasks": len(entries),
                "registry_sha256": sha(OUTPUT),
                "sidecar_sha256": sha(SIDECAR),
                "run_order_sha256": sha(ORDER),
                "stable_inputs": len(copied),
            },
            indent=2,
        )
    )
