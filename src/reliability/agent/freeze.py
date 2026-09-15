"""Freeze an agent's patch as immutable evidence (Phase 3.4).

Once the agent terminates, its patch is the artifact every later stage is
judged against: the verifier inspects it, the oracle applies it, and the
analysis attributes outcomes to it. If any of those stages could modify it - even
by rewriting it "equivalently" - the causal chain from agent output to measured
result would be broken, and no stored result could be trusted to describe the
patch that actually ran.

Freezing is therefore enforced twice, because either alone is weak:

1. **Filesystem.** The file is written `0o444`. A stray `open(path, "w")`
   anywhere in the codebase fails with `PermissionError` without needing to know
   about this module.
2. **Content hash.** Permissions can be changed by a determined caller, and a
   file can be replaced rather than written. `verify()` recomputes the digest, so
   tampering is detectable after the fact rather than merely discouraged.

Patches are handled as bytes end to end. A patch is applied with `git apply`,
where a single altered line ending changes whether it applies at all, so no
text-mode round-trip is permitted anywhere in this module. `.gitattributes`
marks `*.patch` and `*.diff` as `-text` for the same reason.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

READ_ONLY = 0o444


class FrozenPatchError(RuntimeError):
    """Raised on any attempt to modify, replace, or re-freeze a frozen patch."""


@dataclass(frozen=True, slots=True)
class FrozenPatch:
    """A patch that has been written, hashed, and made read-only."""

    path: Path
    sha256: str
    size_bytes: int

    @property
    def is_empty(self) -> bool:
        """An agent that produced no diff. A real outcome, not an error."""
        return self.size_bytes == 0


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def freeze_patch(path: Path, content: bytes | str) -> FrozenPatch:
    """Write `content` to `path`, hash it, and make it read-only.

    Refuses to overwrite an existing file. A second freeze for the same task
    means either a rerun writing over evidence or a bug, and both should stop
    rather than silently replace the record.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    if path.exists():
        raise FrozenPatchError(f"refusing to overwrite an existing patch: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.chmod(path, READ_ONLY)

    return FrozenPatch(path=path, sha256=digest_bytes(content), size_bytes=len(content))


def read_patch(frozen: FrozenPatch) -> bytes:
    """Read a frozen patch, verifying it still matches its recorded digest."""
    verify(frozen)
    return frozen.path.read_bytes()


def verify(frozen: FrozenPatch) -> None:
    """Raise unless the file on disk still matches the recorded hash and mode."""
    if not frozen.path.exists():
        raise FrozenPatchError(f"frozen patch is missing: {frozen.path}")

    payload = frozen.path.read_bytes()
    actual = digest_bytes(payload)
    if actual != frozen.sha256:
        raise FrozenPatchError(
            f"frozen patch was modified: {frozen.path}\n"
            f"  recorded {frozen.sha256}\n  actual   {actual}"
        )

    mode = stat.S_IMODE(frozen.path.stat().st_mode)
    if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        raise FrozenPatchError(
            f"frozen patch is writable (mode {oct(mode)}): {frozen.path}"
        )


def is_frozen(path: Path) -> bool:
    if not path.exists():
        return False
    mode = stat.S_IMODE(path.stat().st_mode)
    return not (mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
