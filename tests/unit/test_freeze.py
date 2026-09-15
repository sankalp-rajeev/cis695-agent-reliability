"""Phase 3.4 gate: a frozen patch cannot be mutated and its hash is stable."""

from __future__ import annotations

import dataclasses
import os
import stat

import pytest

from reliability.agent.freeze import (
    FrozenPatchError,
    digest_bytes,
    freeze_patch,
    is_frozen,
    read_patch,
    verify,
)

PATCH = b"""diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -1,1 +1,1 @@
-old
+new
"""


@pytest.fixture
def frozen(tmp_path):
    return freeze_patch(tmp_path / "patch.diff", PATCH)


# --- the gate --------------------------------------------------------------


def test_write_to_a_frozen_patch_raises(frozen):
    with pytest.raises(PermissionError), open(frozen.path, "w") as fh:
        fh.write("tampered")


def test_append_to_a_frozen_patch_raises(frozen):
    with pytest.raises(PermissionError), open(frozen.path, "a") as fh:
        fh.write("extra")


def test_binary_write_to_a_frozen_patch_raises(frozen):
    with pytest.raises(PermissionError):
        frozen.path.write_bytes(b"tampered")


def test_hash_is_stable_across_reads(frozen):
    first = digest_bytes(frozen.path.read_bytes())
    for _ in range(5):
        assert digest_bytes(frozen.path.read_bytes()) == first
    assert first == frozen.sha256


def test_hash_matches_content(frozen):
    assert frozen.sha256 == digest_bytes(PATCH)
    assert frozen.size_bytes == len(PATCH)


# --- tamper detection ------------------------------------------------------


def test_verify_passes_for_an_untouched_patch(frozen):
    verify(frozen)


def test_verify_detects_content_replacement(frozen):
    """Permissions can be forced; the hash is what makes tampering detectable."""
    os.chmod(frozen.path, 0o644)
    frozen.path.write_bytes(b"different content entirely")

    with pytest.raises(FrozenPatchError, match="was modified"):
        verify(frozen)


def test_verify_detects_a_patch_left_writable(frozen):
    os.chmod(frozen.path, 0o644)
    with pytest.raises(FrozenPatchError, match="writable"):
        verify(frozen)


def test_verify_detects_a_missing_patch(frozen):
    os.chmod(frozen.path, 0o644)
    frozen.path.unlink()
    with pytest.raises(FrozenPatchError, match="missing"):
        verify(frozen)


def test_read_patch_verifies_before_returning(frozen):
    assert read_patch(frozen) == PATCH

    os.chmod(frozen.path, 0o644)
    frozen.path.write_bytes(b"swapped")
    with pytest.raises(FrozenPatchError):
        read_patch(frozen)


# --- freezing semantics ----------------------------------------------------


def test_mode_is_read_only(frozen):
    mode = stat.S_IMODE(frozen.path.stat().st_mode)
    assert mode == 0o444
    assert is_frozen(frozen.path)


def test_refuses_to_freeze_over_an_existing_patch(tmp_path):
    path = tmp_path / "patch.diff"
    freeze_patch(path, PATCH)
    with pytest.raises(FrozenPatchError, match="refusing to overwrite"):
        freeze_patch(path, b"second attempt")


def test_creates_parent_directories(tmp_path):
    frozen = freeze_patch(tmp_path / "a" / "b" / "patch.diff", PATCH)
    assert frozen.path.exists()


def test_accepts_str_content_as_utf8(tmp_path):
    frozen = freeze_patch(tmp_path / "p.diff", PATCH.decode())
    assert frozen.sha256 == digest_bytes(PATCH)


def test_empty_patch_is_a_real_outcome_not_an_error(tmp_path):
    """An agent that produced no diff must still be recorded."""
    frozen = freeze_patch(tmp_path / "empty.diff", b"")
    assert frozen.is_empty
    assert frozen.size_bytes == 0
    verify(frozen)


def test_bytes_are_preserved_exactly(tmp_path):
    """git apply is sensitive to line endings, so no text round-trip is allowed."""
    crlf = b"diff --git a/x b/x\r\n--- a/x\r\n+++ b/x\r\n"
    frozen = freeze_patch(tmp_path / "crlf.diff", crlf)
    assert frozen.path.read_bytes() == crlf
    assert b"\r\n" in frozen.path.read_bytes()


def test_frozen_patch_object_is_immutable(frozen):
    with pytest.raises(dataclasses.FrozenInstanceError):
        frozen.sha256 = "sha256:0"  # type: ignore[misc]


def test_is_frozen_false_for_a_normal_file(tmp_path):
    path = tmp_path / "plain.diff"
    path.write_bytes(PATCH)
    assert not is_frozen(path)


def test_distinct_tasks_freeze_independently(tmp_path):
    """Parallel-safety: per-task paths, no shared mutable state."""
    a = freeze_patch(tmp_path / "task_a" / "patch.diff", b"AAA")
    b = freeze_patch(tmp_path / "task_b" / "patch.diff", b"BBB")

    assert a.sha256 != b.sha256
    verify(a)
    verify(b)
