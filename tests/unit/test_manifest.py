"""Manifest loading: size-agnostic, and integrity-checked against its hash."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from reliability.benchmark.manifest import (
    Manifest,
    ManifestError,
    content_hash,
    load_manifest,
)

HEADER = "instance_id,repo,task_type,base_commit"


def write_manifest(path: Path, n: int, *, sidecar: bool = True) -> Path:
    lines = [HEADER] + [
        f"repo{i}__repo{i}-{i},org/repo{i},numerical,{str(i) * 40}" for i in range(n)
    ]
    payload = ("\n".join(lines) + "\n").encode()
    path.write_bytes(payload)
    if sidecar:
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{content_hash(payload)}  {path.name}\n", encoding="utf-8"
        )
    return path


@pytest.mark.parametrize("n", [1, 10, 75, 500])
def test_loads_a_manifest_of_any_size(tmp_path, n):
    """Nothing may assume 10; the main study reuses this unchanged."""
    manifest = load_manifest(write_manifest(tmp_path / "m.csv", n))
    assert len(manifest) == n
    assert len(manifest.instance_ids) == n


def test_exposes_entries_and_repos(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path / "m.csv", 3))
    assert manifest.repos == ("org/repo0", "org/repo1", "org/repo2")
    assert manifest.entries[0].task_type == "numerical"


def test_is_iterable(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path / "m.csv", 4))
    assert len(list(manifest)) == 4


def test_hash_is_recomputed_from_bytes(tmp_path):
    path = write_manifest(tmp_path / "m.csv", 3)
    manifest = load_manifest(path)
    assert manifest.content_hash == content_hash(path.read_bytes())


def test_tampered_manifest_fails_its_sidecar_check(tmp_path):
    """A manifest edited after it was drawn must not run under the old identity."""
    path = write_manifest(tmp_path / "m.csv", 3)
    path.write_bytes(path.read_bytes() + b"extra__extra-9,org/x,numerical," + b"9" * 40 + b"\n")

    with pytest.raises(ManifestError, match="content hash mismatch"):
        load_manifest(path)


def test_missing_sidecar_is_tolerated(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path / "m.csv", 2, sidecar=False))
    assert len(manifest) == 2


def test_missing_file_raises(tmp_path):
    with pytest.raises(ManifestError, match="not found"):
        load_manifest(tmp_path / "nope.csv")


def test_empty_manifest_raises(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text(HEADER + "\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="empty"):
        load_manifest(path)


def test_missing_columns_raise(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text("instance_id,repo\na__a-1,org/a\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="missing columns"):
        load_manifest(path)


def test_duplicate_instance_ids_raise(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text(
        HEADER + "\n" + f"a__a-1,org/a,numerical,{'1' * 40}\n" * 2, encoding="utf-8"
    )
    with pytest.raises(ManifestError, match="duplicate"):
        load_manifest(path)


def test_loads_the_real_pilot_manifest():
    """The committed artifact must load and verify against its committed hash."""
    manifest = load_manifest(Path("manifests/pilot.csv"))

    assert len(manifest) == 10
    assert len(manifest.repos) == 8
    assert manifest.content_hash == (
        "sha256:f03000ed3228b9ffff62a91ba29e84e70a42892f3f8bb4ffa0150465b0494873"
    )


def test_manifest_is_immutable(tmp_path):
    manifest = load_manifest(write_manifest(tmp_path / "m.csv", 2))
    with pytest.raises(dataclasses.FrozenInstanceError):
        manifest.content_hash = "sha256:0"  # type: ignore[misc]
    assert isinstance(manifest, Manifest)
