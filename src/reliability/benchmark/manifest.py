"""Read a task manifest (Phase 2.3 output, consumed by Phase 3 onward).

The manifest - not the sampler - is the frozen artifact. Downstream code reads a
CSV and never re-derives the sample, so a sampling fault cannot affect a run; the
worst it could do is produce a *different* manifest, which the recorded content
hash exposes immediately.

Nothing here knows how many tasks a manifest holds or what it is called. The
same code must run the 10-task pilot and the 75-task main study unchanged, so the
size is whatever the file contains and the path is always supplied by the caller.
There is deliberately no default path.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS = ("instance_id", "repo", "task_type", "base_commit")


class ManifestError(RuntimeError):
    """Raised when a manifest is malformed or fails its integrity check."""


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    instance_id: str
    repo: str
    task_type: str
    base_commit: str


@dataclass(frozen=True, slots=True)
class Manifest:
    """A task list and the hash identifying exactly this list."""

    path: Path
    content_hash: str
    entries: tuple[ManifestEntry, ...]

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    @property
    def instance_ids(self) -> tuple[str, ...]:
        return tuple(e.instance_id for e in self.entries)

    @property
    def repos(self) -> tuple[str, ...]:
        return tuple(sorted({e.repo for e in self.entries}))


def content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_manifest(path: Path, *, verify_sidecar: bool = True) -> Manifest:
    """Load a manifest of any size, verifying its sidecar hash when present.

    The hash is recomputed from the file's bytes rather than trusted, so a
    manifest edited after it was drawn fails loudly instead of running a
    different task set under the recorded identity.
    """
    path = Path(path)
    if not path.exists():
        raise ManifestError(f"manifest not found: {path}")

    payload = path.read_bytes()
    digest = content_hash(payload)

    sidecar = path.with_suffix(path.suffix + ".sha256")
    if verify_sidecar and sidecar.exists():
        recorded = sidecar.read_text(encoding="utf-8").split()[0]
        if recorded != digest:
            raise ManifestError(
                f"manifest content hash mismatch for {path}\n"
                f"  recorded {recorded}\n  actual   {digest}"
            )

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise ManifestError(f"manifest is empty: {path}")

    missing = sorted(set(REQUIRED_COLUMNS) - set(rows[0]))
    if missing:
        raise ManifestError(f"manifest is missing columns {missing}: {path}")

    entries = tuple(
        ManifestEntry(
            instance_id=r["instance_id"],
            repo=r["repo"],
            task_type=r["task_type"],
            base_commit=r["base_commit"],
        )
        for r in rows
    )

    ids = [e.instance_id for e in entries]
    if len(set(ids)) != len(ids):
        raise ManifestError(f"manifest contains duplicate instance ids: {path}")

    return Manifest(path=path, content_hash=digest, entries=entries)
