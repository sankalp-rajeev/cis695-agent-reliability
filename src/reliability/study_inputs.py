"""Bind study verification inputs to the Phase 2 manifest that supplied them."""

import hashlib
import json
import re
import shutil
from pathlib import Path

PATCHES = Path("runs/study_v1_5/patches")
REFERENCE_MANIFEST = PATCHES / "reference/tasks.json"


def phase2_rows(path: Path, root: Path) -> tuple[dict, str]:
    relative = path.resolve().relative_to(root)
    if relative.parent.parent != PATCHES or relative.name != "tasks.json":
        raise ValueError("Expected a Phase 2 patch manifest")
    raw = path.read_bytes()
    rows = {}
    for row in json.loads(raw)["tasks"]:
        iid = row["instance_id"]
        if iid in rows:
            raise ValueError("Duplicate Phase 2 manifest ID: " + iid)
        rows[iid] = row
    return rows, hashlib.sha256(raw).hexdigest()


def patch_digest(rows, iid):
    row = rows.get(iid)
    if row is None or row.get("missing") or row.get("malformed"):
        raise ValueError("No Phase 2 patch for " + iid)
    expected = row.get("patch_sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Invalid Phase 2 patch SHA-256 for " + iid)
    return expected


def verification_source(folder, reference_patches: bool, root: Path) -> tuple[dict, dict | None]:
    """Validate the opt-in and return its header fields and manifest rows."""
    if folder is None and reference_patches:
        raise ValueError("--reference-patches requires --verify-only-from")
    source_path = folder / "source.json" if folder is not None else None
    source_sha, rows, is_reference = None, None, False
    if source_path is not None and (source_path.exists() or source_path.is_symlink()):
        if source_path.is_symlink():
            raise ValueError("source.json must be a regular file in the input folder")
        raw = source_path.read_bytes()
        source = json.loads(raw)
        if not isinstance(source, dict) or not isinstance(source.get("source_manifest"), str):
            raise ValueError("source.json must name a Phase 2 manifest")
        manifest = root / source["source_manifest"]
        rows, digest = phase2_rows(manifest, root)
        if source.get("source_manifest_sha256") != digest:
            raise ValueError("Phase 2 manifest SHA-256 mismatch in source.json")
        source_sha = hashlib.sha256(raw).hexdigest()
        is_reference = manifest.resolve() == root / REFERENCE_MANIFEST
    if reference_patches != is_reference:
        raise ValueError("--reference-patches must match the reference manifest named in source.json")
    return {
        "reference_patches": reference_patches,
        "verify_only_input_folder": str(folder) if folder is not None else None,
        "verify_only_source_sha256": source_sha,
    }, rows


def copy_inputs(manifest, ids_path, ids, output, *, root):
    rows, manifest_sha = phase2_rows(manifest, root)
    output.mkdir(parents=True, exist_ok=False)
    try:
        inputs, empty = [], 0
        for iid in ids:
            expected = patch_digest(rows, iid)
            source = root / rows[iid]["patch_path"]
            canonical = manifest.resolve().parent / f"{iid}.patch"
            if source != canonical or source.resolve() != source:
                raise ValueError("Unexpected Phase 2 patch path for " + iid)
            destination = output / source.name
            shutil.copyfile(source, destination)
            raw = destination.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("Patch SHA-256 mismatch on copy for " + iid)
            empty += not raw
            destination.chmod(0o444)
            inputs.append({"instance_id": iid, "patch_path": destination.name, "patch_sha256": expected})
        provenance = {
            "source_manifest": manifest.resolve().relative_to(root).as_posix(),
            "source_manifest_sha256": manifest_sha,
            "id_list": str(ids_path.resolve()),
            "id_list_sha256": hashlib.sha256(ids_path.read_bytes()).hexdigest(),
            "counts": {"patches": len(inputs), "empty": empty},
        }
        for name, data in (("tasks.json", inputs), ("source.json", provenance)):
            (output / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return provenance["counts"]
    except BaseException:
        shutil.rmtree(output)
        raise
