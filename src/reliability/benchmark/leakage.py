"""Detect oracle data in agent-visible or verifier-input artifacts (Phase 8.3).

The gate this backs is non-negotiable: if ground truth reached the agent or the
verifier's selection step, the experiment measures nothing, and no other result
in the study survives it.

Two kinds of check, because either alone is insufficient:

**Field names.** `FAIL_TO_PASS`, `test_patch`, `hints_text` and friends appearing
in a prompt or a verifier input means oracle plumbing reached somewhere it
should not. Cheap, and catches the structural mistakes — a dataset row passed
whole, a debug dump left in.

**Field content.** A leak does not have to carry its label. Gold patch text
pasted into a prompt, or a `FAIL_TO_PASS` test name appearing in a repository
that does not contain that test, is a leak whether or not the word
"FAIL_TO_PASS" appears anywhere. This check compares against the actual oracle
values for the instance, so it catches a leak that was laundered through
reformatting.

Two scoping decisions that matter for the result to mean anything:

- **The oracle's own outputs are out of scope.** `oracle_record.json` and the
  harness logs are *supposed* to contain `FAIL_TO_PASS` names and resolution
  status; that is what they are for. Scanning them would guarantee a hit and
  train the reader to ignore the audit. Scope is defined by an allowlist of
  agent-visible and verifier-input filenames rather than a denylist, so a new
  artifact is out of scope until someone adds it deliberately, instead of being
  scanned by accident and producing noise.

- **Scanning nothing is a failure, not a pass.** `audit()` returns
  `scanned_files == 0` as a hard failure. An audit that silently covered no
  files would exit clean and mean nothing, which is the same error as counting
  an unrun test as a pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

#: Filenames that are agent-visible or feed the verifier. Everything else is out
#: of scope until added here on purpose.
IN_SCOPE = (
    "trajectory.jsonl",      # the full agent conversation, prompts included
    "agent_output.txt",
    "submission_raw.txt",
    "repair_record.json",
    "patch.diff",
    "prompt.txt",
    "system_prompt.txt",
)

#: Verification records are in scope too, matched by pattern.
IN_SCOPE_PATTERNS = ("verification_record.*.json",)

#: Deliberately *not* scanned: these are the oracle's own output and are
#: supposed to contain ground truth. Listed explicitly so the exclusion is a
#: documented decision rather than an accident of the allowlist.
OUT_OF_SCOPE = (
    "oracle_record.json",
    "oracle_verdict.json",
    "harness.log",
    "predictions.jsonl",
)

#: Oracle column names. Any of these appearing in an in-scope file means oracle
#: plumbing reached somewhere it should not.
ORACLE_FIELD_NAMES = (
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "test_patch",
    "hints_text",
    "eval_script",
    "environment_setup_commit",
    "golden_patch",
    "gold_patch",
)

#: Minimum length for a gold-patch line to be usable as a probe. Short lines
#: like `)` or `return` occur naturally in any repository and would produce
#: constant false positives.
MIN_PROBE_LENGTH = 24

#: How many distinctive lines to draw from each oracle text.
MAX_PROBES = 40


class Severity(str, Enum):
    """How much a finding implies.

    `CONFIRMED` means oracle content or an oracle field name was found where it
    cannot legitimately be. `REVIEW` means a match that has an innocent
    explanation worth ruling out by hand. Only `CONFIRMED` fails the gate, so a
    reviewable finding cannot be quietly ignored but also cannot block on a
    coincidence.
    """

    CONFIRMED = "confirmed"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    kind: str
    path: str
    detail: str
    line_no: int | None = None

    def __str__(self) -> str:
        where = f":{self.line_no}" if self.line_no else ""
        return f"[{self.severity.value}] {self.kind} {self.path}{where}: {self.detail}"


@dataclass(frozen=True, slots=True)
class OracleProbes:
    """The values to search for, derived from one instance's oracle record."""

    instance_id: str
    patch_lines: tuple[str, ...] = ()
    test_patch_lines: tuple[str, ...] = ()
    fail_to_pass: tuple[str, ...] = ()
    hints_lines: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.patch_lines or self.test_patch_lines
                    or self.fail_to_pass or self.hints_lines)


def _not_in_problem_statement(
    lines: tuple[str, ...], problem_statement: str
) -> tuple[str, ...]:
    """Drop probes the agent was legitimately given.

    A string that appears in the problem statement cannot distinguish a leak
    from the agent doing its job, so using it as a probe can only generate false
    positives. This matters most for `hints_text`, which is drawn from the same
    pull-request thread as the problem statement and frequently quotes it
    outright.
    """
    if not problem_statement:
        return lines
    return tuple(line for line in lines if line not in problem_statement)


@dataclass
class AuditResult:
    findings: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    scanned_tasks: int = 0
    content_checked_tasks: int = 0

    @property
    def confirmed(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.CONFIRMED]

    @property
    def review(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.REVIEW]

    @property
    def passed(self) -> bool:
        """An audit that scanned nothing has not passed.

        Same rule as NOT_RUN in Phase 5 and NOT_AVAILABLE in Phase 6: the
        absence of a check is never evidence of correctness, and an audit
        reporting clean over zero files is exactly that.
        """
        return self.scanned_files > 0 and not self.confirmed


def distinctive_lines(text: str, *, limit: int = MAX_PROBES) -> tuple[str, ...]:
    """Pull searchable lines out of a diff or a free-text field.

    Added and removed lines are stripped of their diff marker, because a leak
    would be reproduced as source, not as a diff. Lines shorter than
    `MIN_PROBE_LENGTH` are dropped: `)` and `return None` appear in every
    repository and would make every run look like a leak.
    """
    seen: list[str] = []
    for raw in text.splitlines():
        # Structural diff lines are not content and would only ever match
        # another diff, so they are dropped rather than stripped.
        if raw.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        line = (raw[1:] if raw[:1] in "+-" else raw).strip()
        if len(line) < MIN_PROBE_LENGTH:
            continue
        if line not in seen:
            seen.append(line)
        if len(seen) >= limit:
            break
    return tuple(seen)


def probes_from_oracle(record, problem_statement: str = "") -> OracleProbes:
    """Build probes from an `OracleRecord` from the dataset loader.

    Takes the loader's record rather than an instance id so this module never
    loads the dataset itself — the caller that already has oracle access passes
    it in, and nothing here acquires it.

    `problem_statement` is the agent-visible half, used to *subtract* probes
    rather than to search for anything. Without it the audit reports a leak
    every time an agent quotes the issue it was asked to fix.
    """
    return OracleProbes(
        instance_id=record.instance_id,
        patch_lines=_not_in_problem_statement(
            distinctive_lines(record.patch), problem_statement),
        test_patch_lines=_not_in_problem_statement(
            distinctive_lines(record.test_patch), problem_statement),
        fail_to_pass=tuple(record.fail_to_pass),
        hints_lines=_not_in_problem_statement(
            distinctive_lines(record.hints_text, limit=10), problem_statement),
    )


def in_scope(path: Path) -> bool:
    if path.name in OUT_OF_SCOPE:
        return False
    if path.name in IN_SCOPE:
        return True
    return any(path.match(p) for p in IN_SCOPE_PATTERNS)


def scan_files(task_dir: Path) -> list[Path]:
    return sorted(p for p in task_dir.iterdir() if p.is_file() and in_scope(p))


def scan_field_names(path: Path, text: str) -> list[Finding]:
    """Look for oracle column names in an agent-visible or verifier-input file."""
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name in ORACLE_FIELD_NAMES:
            if name in line:
                findings.append(Finding(
                    severity=Severity.CONFIRMED,
                    kind="oracle-field-name",
                    path=str(path),
                    detail=f"{name!r} appears in an in-scope artifact",
                    line_no=line_no,
                ))
    return findings


def scan_content(path: Path, text: str, probes: OracleProbes) -> list[Finding]:
    """Look for actual oracle values, which a leak need not have labelled."""
    findings = []

    # hints_text is REVIEW rather than CONFIRMED. It is discussion from the same
    # pull-request thread the problem statement was drawn from, so it restates
    # the issue in the issue's own vocabulary, and an agent reproducing the bug
    # writes similar lines independently. Observed on the first real run of this
    # audit: hints carried `s.headers['Accept-Encoding'] = None` while the
    # problem statement carried `session.headers['Accept-Encoding'] = None`, so
    # subtracting the problem statement did not catch it and the agent's own
    # abbreviation matched. The gold patch and test patch have no such overlap —
    # they are the fix and the grading tests — so those stay CONFIRMED.
    for label, lines, severity in (
        ("gold-patch", probes.patch_lines, Severity.CONFIRMED),
        ("test-patch", probes.test_patch_lines, Severity.CONFIRMED),
        ("hints-text", probes.hints_lines, Severity.REVIEW),
    ):
        for probe in lines:
            if probe in text:
                findings.append(Finding(
                    severity=severity,
                    kind=f"{label}-content",
                    path=str(path),
                    detail=f"oracle {label} line present: {probe[:60]!r}",
                ))
                break  # one hit per field is enough; the rest is noise

    # FAIL_TO_PASS names are reviewable rather than confirmed. Most are added by
    # the test patch and so cannot legitimately appear, but some already exist at
    # the base commit and an agent that read the test file would reproduce them
    # innocently. Failing on that would make the gate cry wolf; ignoring it would
    # miss a real leak, so it is surfaced for a human instead.
    for name in probes.fail_to_pass:
        symbol = _test_symbol(name)
        if symbol and re.search(rf"\b{re.escape(symbol)}\b", text):
            findings.append(Finding(
                severity=Severity.REVIEW,
                kind="fail-to-pass-name",
                path=str(path),
                detail=(f"FAIL_TO_PASS test {symbol!r} named in an in-scope "
                        "artifact; confirm it exists at the base commit"),
            ))
    return findings


def _test_symbol(node_id: str) -> str:
    """The test function name out of a pytest node id or a unittest path."""
    tail = node_id.split("::")[-1].split("[")[0].strip()
    return tail if tail.startswith("test") and len(tail) > 4 else ""


def audit_task(
    task_dir: Path, probes: OracleProbes | None = None
) -> tuple[list[Finding], int]:
    """Audit one task directory. Returns its findings and how many files it read."""
    findings: list[Finding] = []
    files = scan_files(task_dir)

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(
                severity=Severity.CONFIRMED, kind="unreadable", path=str(path),
                detail=f"could not be scanned, so it cannot be cleared: {exc}",
            ))
            continue

        findings.extend(scan_field_names(path, text))
        if probes is not None and not probes.is_empty:
            findings.extend(scan_content(path, text, probes))

    return findings, len(files)


def audit(
    task_dirs: list[Path], probes_by_instance: dict[str, OracleProbes] | None = None
) -> AuditResult:
    """Audit every task directory given.

    `probes_by_instance` is optional so the structural half can run without
    dataset access, but a caller that omits it gets `content_checked_tasks` of
    zero, and the gate script treats a partial audit as a failure rather than
    reporting it as clean.
    """
    probes_by_instance = probes_by_instance or {}
    result = AuditResult()

    for task_dir in task_dirs:
        probes = probes_by_instance.get(task_dir.name)
        findings, n_files = audit_task(task_dir, probes)

        result.findings.extend(findings)
        result.scanned_files += n_files
        result.scanned_tasks += 1
        if probes is not None and not probes.is_empty:
            result.content_checked_tasks += 1

    return result


def find_task_dirs(runs_root: Path) -> list[Path]:
    """Every agent-produced task directory under a runs root.

    Keyed on the presence of a repair record, which excludes the Phase 1 harness
    controls. Those legitimately contain gold patches — they exist to evaluate
    them — and scanning them would produce a guaranteed hit that trains the
    reader to ignore this audit.
    """
    return sorted(p.parent for p in runs_root.glob("*/tasks/*/repair_record.json"))


__all__ = [
    "ORACLE_FIELD_NAMES",
    "AuditResult",
    "Finding",
    "OracleProbes",
    "Severity",
    "audit",
    "audit_task",
    "distinctive_lines",
    "find_task_dirs",
    "in_scope",
    "probes_from_oracle",
]
