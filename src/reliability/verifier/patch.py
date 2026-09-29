"""Parse a unified diff into structured file changes.

Shared substrate for Phase 4 (integrity, risk features) and Phase 5 (test
selection reads the changed paths and touched symbols). Written here once rather
than re-derived per consumer, so that "which files did this patch change" has a
single answer across the verifier.

Deliberately a parser and nothing else: it makes no judgement about whether a
change is acceptable. Parsing and policy are separated because the risk features
in Phase 4.2 must be recorded without auto-failing, and mixing the two would make
it easy to leak a rejection into what is supposed to be a measurement.

No external dependency. `unidiff` would do this, but the patch is adversarial
input from a language model and the failure mode that matters - a malformed diff
silently parsing as "no changes", which every downstream check would then pass -
is easier to guard against in code we control. Malformed input raises.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


class ChangeKind(str, Enum):
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"


class PatchParseError(ValueError):
    """Raised when a diff cannot be parsed. Never silently treated as empty."""


@dataclass(frozen=True, slots=True)
class Hunk:
    old_start: int
    new_start: int
    added: tuple[str, ...]
    removed: tuple[str, ...]
    context: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FileChange:
    """One file's worth of a diff."""

    path: str
    kind: ChangeKind
    hunks: tuple[Hunk, ...] = ()
    old_path: str | None = None
    is_binary: bool = False
    old_mode: str | None = None
    new_mode: str | None = None

    @property
    def added_lines(self) -> tuple[str, ...]:
        return tuple(line for hunk in self.hunks for line in hunk.added)

    @property
    def removed_lines(self) -> tuple[str, ...]:
        return tuple(line for hunk in self.hunks for line in hunk.removed)

    @property
    def n_added(self) -> int:
        return len(self.added_lines)

    @property
    def n_removed(self) -> int:
        return len(self.removed_lines)


@dataclass(frozen=True, slots=True)
class Patch:
    """A parsed unified diff."""

    files: tuple[FileChange, ...] = ()
    raw: str = ""

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self):
        return iter(self.files)

    @property
    def is_empty(self) -> bool:
        return not self.files

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(f.path for f in self.files)

    @property
    def n_added(self) -> int:
        return sum(f.n_added for f in self.files)

    @property
    def n_removed(self) -> int:
        return sum(f.n_removed for f in self.files)


_DIFF_HEADER = re.compile(r"^diff --git a/(?P<a>.+?) b/(?P<b>.+?)$")
_HUNK_HEADER = re.compile(
    r"^@@ -(?P<old>\d+)(?:,(?P<oldn>\d+))? \+(?P<new>\d+)(?:,(?P<newn>\d+))? @@"
)


def parse_patch(text: str | bytes) -> Patch:
    """Parse a unified diff.

    An empty or whitespace-only input is an empty patch, which is a real agent
    outcome. Input that looks like a diff but cannot be parsed raises, because
    treating it as empty would let every downstream check pass vacuously.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    if not text.strip():
        return Patch(raw=text)

    lines = text.splitlines()
    files: list[FileChange] = []

    # State for the file currently being accumulated.
    path = old_path = None
    kind = ChangeKind.MODIFIED
    is_binary = False
    old_mode = new_mode = None
    hunks: list[Hunk] = []
    hunk: dict | None = None

    def close_hunk() -> None:
        nonlocal hunk
        if hunk is not None:
            hunks.append(Hunk(
                old_start=hunk["old_start"], new_start=hunk["new_start"],
                added=tuple(hunk["added"]), removed=tuple(hunk["removed"]),
                context=tuple(hunk["context"]),
            ))
            hunk = None

    def close_file() -> None:
        nonlocal path, old_path, kind, is_binary, old_mode, new_mode, hunks
        close_hunk()
        if path is not None:
            files.append(FileChange(
                path=path, kind=kind, hunks=tuple(hunks), old_path=old_path,
                is_binary=is_binary, old_mode=old_mode, new_mode=new_mode,
            ))
        path = old_path = None
        kind = ChangeKind.MODIFIED
        is_binary = False
        old_mode = new_mode = None
        hunks = []

    for line in lines:
        if (header := _DIFF_HEADER.match(line)) is not None:
            close_file()
            path = header.group("b")
            old_path = header.group("a")
            continue

        if path is None:
            # Content before any `diff --git`. Tolerated only if it is not itself
            # diff content; a bare hunk with no file header is unattributable.
            if line.startswith(("@@", "+++", "---")):
                raise PatchParseError(
                    f"diff content before any 'diff --git' header: {line[:60]!r}"
                )
            continue

        if line.startswith("new file mode"):
            kind = ChangeKind.ADDED
            new_mode = line.rsplit(" ", 1)[-1]
        elif line.startswith("deleted file mode"):
            kind = ChangeKind.DELETED
            old_mode = line.rsplit(" ", 1)[-1]
        elif line.startswith("rename to "):
            kind = ChangeKind.RENAMED
            path = line[len("rename to "):].strip()
        elif line.startswith("rename from "):
            kind = ChangeKind.RENAMED
            old_path = line[len("rename from "):].strip()
        elif line.startswith("old mode "):
            old_mode = line.rsplit(" ", 1)[-1]
        elif line.startswith("new mode "):
            new_mode = line.rsplit(" ", 1)[-1]
        elif line.startswith(("GIT binary patch", "Binary files ")):
            is_binary = True
        elif (hh := _HUNK_HEADER.match(line)) is not None:
            close_hunk()
            hunk = {
                "old_start": int(hh.group("old")), "new_start": int(hh.group("new")),
                "added": [], "removed": [], "context": [],
            }
        elif hunk is not None:
            if line.startswith("+"):
                hunk["added"].append(line[1:])
            elif line.startswith("-"):
                hunk["removed"].append(line[1:])
            elif line.startswith("\\"):
                pass  # "\ No newline at end of file"
            else:
                hunk["context"].append(line.removeprefix(" "))

    close_file()

    if not files:
        raise PatchParseError(
            "input is non-empty but contains no 'diff --git' file headers; "
            "refusing to report it as an empty patch"
        )
    return Patch(files=tuple(files), raw=text)


def touched_symbols(patch: Patch) -> tuple[str, ...]:
    """Names of functions and classes whose definitions the patch touches.

    Feeds Tier 2 of the selection policy (VERIFIER_POLICY.md §3.3). Reads both
    added and removed lines: a patch that deletes a function still changes the
    behaviour of whatever referenced it.

    Also picks up the enclosing definition from hunk context, because the common
    case is a change to a line *inside* a function rather than to its `def`.
    """
    pattern = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
    names: set[str] = set()
    for change in patch:
        if change.is_binary:
            continue
        for hunk in change.hunks:
            for line in (*hunk.added, *hunk.removed, *hunk.context):
                if (m := pattern.match(line)) is not None:
                    names.add(m.group(1))
    return tuple(sorted(names))
