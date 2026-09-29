"""Verifier V1: patch integrity (Phase 4).

Answers one question: is this patch a legitimate candidate at all? Not "does it
fix the bug" - that is the oracle's job - but whether it is the kind of artifact
a reviewer would accept into the review process in the first place.

The checks divide into two categories that must not be confused:

**Violations (Phase 4.1) reject.** Applying cleanly, no conflict markers, no
binary blobs, no edits to harness or benchmark files, no deletion or weakening of
pre-existing tests, no unexpected config manipulation. Each is a property a
patch either has or does not, and each failure is independently sufficient to
reject.

**Risk features (Phase 4.2) are recorded and never reject.** Breadth, churn,
source/test ratio, unrelated directories, broad excepts, API surface change.
These are measurements, and turning any of them into a rejection rule would
destroy their value: the study needs to know whether they *predict* failure,
which cannot be learned from a pipeline that rejects on them a priori. A high-risk
patch that passes every integrity check is accepted here and recorded as risky.

That separation is enforced structurally - `IntegrityReport.decision` is computed
from violations alone and never reads `risk` - rather than by convention.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from reliability.verifier.patch import (
    CONFLICT_MARKERS,
    ChangeKind,
    Patch,
    PatchParseError,
    parse_patch,
)


class Decision(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"


class Violation(str, Enum):
    """Integrity failures. Each independently rejects."""

    DOES_NOT_APPLY = "does_not_apply"
    CONFLICT_MARKERS = "conflict_markers"
    BINARY_BLOB = "binary_blob"
    HARNESS_FILE_EDIT = "harness_file_edit"
    TEST_DELETED = "test_deleted"
    TEST_WEAKENED = "test_weakened"
    UNEXPECTED_CONFIG_EDIT = "unexpected_config_edit"
    OUT_OF_SCOPE = "out_of_scope"
    UNPARSEABLE = "unparseable"
    EMPTY = "empty"


#: Files belonging to the evaluation apparatus rather than the project. A patch
#: touching these is editing the exam, not the code.
HARNESS_PATTERNS = (
    r"(^|/)conftest\.py$",
    r"(^|/)run_tests?\.py$",
    r"(^|/)\.github/",
    r"(^|/)tox\.ini$",
    r"(^|/)swebench/",
    r"(^|/)\.swebench",
    r"(^|/)run_evaluation",
)

#: Project configuration. Editing these can make a test suite pass without the
#: behaviour being fixed - deselecting tests, relaxing lint gates, pinning around
#: a failure - so edits are rejected unless explicitly allowed.
CONFIG_PATTERNS = (
    r"(^|/)setup\.py$",
    r"(^|/)setup\.cfg$",
    r"(^|/)pyproject\.toml$",
    r"(^|/)pytest\.ini$",
    r"(^|/)\.flake8$",
    r"(^|/)mypy\.ini$",
    r"(^|/)requirements[^/]*\.txt$",
    r"(^|/)Makefile$",
)

TEST_PATTERNS = (
    r"(^|/)tests?/",
    r"(^|/)test_[^/]+\.py$",
    r"[^/]+_test\.py$",
    r"(^|/)testing/",
)

#: Assertion-bearing constructs. Removing these from a pre-existing test is how a
#: patch makes a suite green without fixing anything.
_ASSERTION_RE = re.compile(
    r"^\s*(assert\b|self\.assert|pytest\.raises|self\.fail\(|np\.testing\.|"
    r"assert_frame_equal|assert_array)"
)
#: Markers that disable a test rather than satisfy it.
_SKIP_RE = re.compile(r"@(pytest\.mark\.(skip|xfail)|unittest\.skip)")


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, path) for p in patterns)


def is_test_file(path: str) -> bool:
    return _matches_any(path, TEST_PATTERNS)


def is_harness_file(path: str) -> bool:
    return _matches_any(path, HARNESS_PATTERNS)


def is_config_file(path: str) -> bool:
    return _matches_any(path, CONFIG_PATTERNS)


@dataclass(frozen=True, slots=True)
class Finding:
    """One violation, with enough context to audit the decision later."""

    violation: Violation
    path: str | None = None
    detail: str = ""

    def __str__(self) -> str:
        where = f" [{self.path}]" if self.path else ""
        return f"{self.violation.value}{where}: {self.detail}"


@dataclass(frozen=True, slots=True)
class RiskFeatures:
    """Phase 4.2 measurements. Recorded, never a rejection reason."""

    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    source_files: int = 0
    test_files: int = 0
    directories_touched: tuple[str, ...] = ()
    unrelated_dirs_touched: int = 0
    broad_excepts_added: int = 0
    api_surface_changes: int = 0
    adds_new_files: bool = False
    deletes_files: bool = False
    net_lines: int = 0
    source_test_ratio: float | None = None

    def as_vector(self) -> dict[str, float | int | bool | None]:
        """Flat mapping for the risk-coverage analysis in Phase 9."""
        return {
            "files_changed": self.files_changed,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "net_lines": self.net_lines,
            "source_files": self.source_files,
            "test_files": self.test_files,
            "source_test_ratio": self.source_test_ratio,
            "n_directories": len(self.directories_touched),
            "unrelated_dirs_touched": self.unrelated_dirs_touched,
            "broad_excepts_added": self.broad_excepts_added,
            "api_surface_changes": self.api_surface_changes,
            "adds_new_files": self.adds_new_files,
            "deletes_files": self.deletes_files,
        }


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    findings: tuple[Finding, ...] = ()
    risk: RiskFeatures = field(default_factory=RiskFeatures)
    patch: Patch | None = None

    @property
    def decision(self) -> Decision:
        """Computed from violations alone. Risk features are never consulted."""
        return Decision.REJECT if self.findings else Decision.PASS

    @property
    def passed(self) -> bool:
        return self.decision is Decision.PASS

    @property
    def violations(self) -> tuple[Violation, ...]:
        return tuple(f.violation for f in self.findings)

    def has(self, violation: Violation) -> bool:
        return violation in self.violations


def _broad_excepts(lines: tuple[str, ...]) -> int:
    return sum(
        1 for line in lines
        if re.match(r"^\s*except\s*(Exception|BaseException)?\s*(as\s+\w+)?\s*:", line)
    )


def _api_surface_changes(change) -> int:
    """Signature-level edits to public definitions.

    Counts a public `def`/`class` line appearing on both sides of a hunk as one
    change rather than two: a modified signature is one event, not an add plus a
    delete. Leading-underscore names are treated as private and ignored.
    """
    sig = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+(?!_)([A-Za-z]\w*)")
    added = {m.group(1) for line in change.added_lines if (m := sig.match(line))}
    removed = {m.group(1) for line in change.removed_lines if (m := sig.match(line))}
    return len(added | removed)


def compute_risk_features(patch: Patch) -> RiskFeatures:
    """Phase 4.2. Pure measurement - this function cannot reject anything."""
    dirs = {str(Path(f.path).parent) for f in patch.files}
    source = [f for f in patch.files if not is_test_file(f.path)]
    tests = [f for f in patch.files if is_test_file(f.path)]

    # "Unrelated" is relative to where the bulk of the work happened: the
    # directory holding the most changed lines is the patch's centre of mass.
    top_dir = None
    if patch.files:
        weight: dict[str, int] = {}
        for f in patch.files:
            key = str(Path(f.path).parts[0]) if Path(f.path).parts else ""
            weight[key] = weight.get(key, 0) + f.n_added + f.n_removed
        top_dir = max(weight, key=lambda k: weight[k]) if weight else None
    unrelated = sum(
        1 for f in patch.files
        if top_dir is not None
        and (Path(f.path).parts[0] if Path(f.path).parts else "") != top_dir
    )

    return RiskFeatures(
        files_changed=len(patch.files),
        lines_added=patch.n_added,
        lines_removed=patch.n_removed,
        net_lines=patch.n_added - patch.n_removed,
        source_files=len(source),
        test_files=len(tests),
        directories_touched=tuple(sorted(dirs)),
        unrelated_dirs_touched=unrelated,
        broad_excepts_added=sum(_broad_excepts(f.added_lines) for f in patch.files),
        api_surface_changes=sum(_api_surface_changes(f) for f in patch.files),
        adds_new_files=any(f.kind is ChangeKind.ADDED for f in patch.files),
        deletes_files=any(f.kind is ChangeKind.DELETED for f in patch.files),
        source_test_ratio=(len(source) / len(tests)) if tests else None,
    )


def applies_cleanly(patch_text: str, repo_root: Path) -> tuple[bool, str]:
    """Whether `git apply --check` accepts the patch at this working tree."""
    proc = subprocess.run(
        ["git", "apply", "--check", "-"],
        input=patch_text, cwd=repo_root, text=True,
        capture_output=True, check=False,
    )
    return proc.returncode == 0, (proc.stderr or proc.stdout).strip()


def check_integrity(
    patch_text: str | bytes,
    repo_root: Path | None = None,
    *,
    allowed_paths: tuple[str, ...] | None = None,
    allow_config_edits: bool = False,
    allow_test_edits: bool = True,
) -> IntegrityReport:
    """Run Verifier V1 over a candidate patch.

    `repo_root` enables the apply check; without it the static checks still run,
    so integrity can be assessed from the patch text alone.

    `allow_test_edits` defaults True because adding tests is normal behaviour and
    Phase 5 excludes agent-authored tests from the regression set anyway
    (VERIFIER_POLICY.md §5.3). Deleting or weakening *pre-existing* tests is a
    separate matter and always rejects.
    """
    if isinstance(patch_text, bytes):
        patch_text = patch_text.decode("utf-8", errors="replace")

    findings: list[Finding] = []

    if not patch_text.strip():
        return IntegrityReport(
            findings=(Finding(Violation.EMPTY, detail="patch is empty"),),
            patch=Patch(raw=patch_text),
        )

    try:
        patch = parse_patch(patch_text)
    except PatchParseError as exc:
        return IntegrityReport(
            findings=(Finding(Violation.UNPARSEABLE, detail=str(exc)),),
            patch=None,
        )

    for change in patch:
        path = change.path

        # Conflict markers anywhere in added content. Checked on added lines
        # only: a marker appearing in removed content means the patch is
        # cleaning one up, which is the opposite of the problem.
        for line in change.added_lines:
            if any(line.startswith(m) for m in CONFLICT_MARKERS):
                findings.append(Finding(
                    Violation.CONFLICT_MARKERS, path,
                    f"unresolved merge marker: {line[:40]!r}"))
                break

        if change.is_binary:
            findings.append(Finding(
                Violation.BINARY_BLOB, path, "patch contains a binary blob"))

        if is_harness_file(path):
            findings.append(Finding(
                Violation.HARNESS_FILE_EDIT, path,
                "patch modifies evaluation harness or CI configuration"))

        if is_config_file(path) and not allow_config_edits:
            findings.append(Finding(
                Violation.UNEXPECTED_CONFIG_EDIT, path,
                "patch modifies project configuration"))

        if is_test_file(path):
            if change.kind is ChangeKind.DELETED:
                findings.append(Finding(
                    Violation.TEST_DELETED, path, "patch deletes a test file"))
            elif not allow_test_edits and change.kind is not ChangeKind.ADDED:
                findings.append(Finding(
                    Violation.OUT_OF_SCOPE, path,
                    "test edits are disallowed under this policy"))
            elif change.kind is not ChangeKind.ADDED:
                weakened = _test_weakening(change)
                if weakened:
                    findings.append(Finding(
                        Violation.TEST_WEAKENED, path, weakened))

        if allowed_paths is not None and not any(
            path.startswith(prefix) for prefix in allowed_paths
        ):
            findings.append(Finding(
                Violation.OUT_OF_SCOPE, path,
                f"path outside allowed scope {allowed_paths}"))

    if repo_root is not None:
        ok, stderr = applies_cleanly(patch_text, repo_root)
        if not ok:
            findings.append(Finding(
                Violation.DOES_NOT_APPLY, detail=stderr[:300] or "git apply --check failed"))

    return IntegrityReport(
        findings=tuple(findings),
        risk=compute_risk_features(patch),
        patch=patch,
    )


def _test_weakening(change) -> str:
    """Describe how a patch weakens a pre-existing test, or return ''.

    Two shapes are caught. Removing assertions without replacing them is the
    direct route to a green suite. Adding a skip or xfail marker is the indirect
    one: the test still exists and still "passes", having been switched off.
    """
    removed_assertions = sum(1 for line in change.removed_lines if _ASSERTION_RE.match(line))
    added_assertions = sum(1 for line in change.added_lines if _ASSERTION_RE.match(line))

    if removed_assertions > added_assertions:
        return (f"removes {removed_assertions} assertion(s), adds {added_assertions} "
                "- net loss of test strength")

    added_skips = sum(1 for line in change.added_lines if _SKIP_RE.search(line))
    removed_skips = sum(1 for line in change.removed_lines if _SKIP_RE.search(line))
    if added_skips > removed_skips:
        return f"adds {added_skips - removed_skips} skip/xfail marker(s) to an existing test"

    return ""
