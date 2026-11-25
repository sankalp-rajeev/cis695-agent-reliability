"""V3 command evidence with separate byte-bounded streams, opt-in for v1.4."""

import re
import shlex
from collections import Counter

from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord
from reliability.verifier.static_checks import (
    RELATIVE_CHECKS,
    CheckKind,
    StaticConfig,
    _command_for,
    _missing_tool_reason,
    _patch_targets,
    discover_tools,
)


def tail(text):
    return text.encode("utf-8")[-4096:].decode("utf-8", errors="ignore")


class ContainerEvidenceExecutor:
    def __init__(self, container):
        self.container = container

    def run_capture(self, command, *, patched, timeout_s):
        self.container.set_patched(patched)
        rc, stdout, stderr, timed_out = self.container.exec_raw(shlex.join(command), timeout_s)
        return {
            "command": list(command),
            "exit_code": rc,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "timed_out": timed_out,
        }


def capture(executor, command, patched, timeout_s):
    try:
        result = executor.run_capture(command, patched=patched, timeout_s=timeout_s)
    except TimeoutError:
        result = {
            "command": list(command),
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timed_out": True,
        }
    result["command"] = list(command)
    result["status"] = (
        "TIMEOUT" if result.get("timed_out") else "PASS" if result["exit_code"] == 0 else "FAIL"
    )
    return result


_FRAME = re.compile(r'File "([^"]+)", line \d+')
_PAREN = re.compile(r"\(([^,()]+\.py), line \d+\)")
_EXC = re.compile(r"^(?:Sorry: )?((?:[A-Za-z_]\w*\.)*[A-Z]\w*): ")
_SYNTAX_TYPES = ("SyntaxError", "IndentationError", "TabError")
COUNTED = ("FAIL", "FAIL_BASE_UNKNOWN")


def _text(result):
    return ((result.get("stdout") or "") + "\n" + (result.get("stderr") or "")).strip()


def _exception_type(text):
    """The final exception type of a failed check (e.g. `TypeError`), or None."""
    for line in reversed(text.splitlines()):
        match = _EXC.match(line.strip())
        if match:
            return match.group(1)
    return None


def _failing_file(text, exc, targets):
    """The repository file the failure is in, matched to a check target when possible."""
    frames = [path[len("/testbed/"):] if path.startswith("/testbed/") else path
              for path in _FRAME.findall(text)]
    frames = [path for path in frames if not path.startswith(("<", "/"))]
    if exc and exc.rsplit(".", 1)[-1] in _SYNTAX_TYPES:
        candidates = frames[-1:] + _PAREN.findall(text)
    else:
        candidates = frames[:1]
    for found in candidates:
        for target in targets:
            if target == found or target.endswith("/" + found) or found.endswith("/" + target):
                return target
        return found
    return None


def _check_verdict(check, added):
    """A6 verdict for one syntax/import check; anything but FAIL keeps its status."""
    status = check.get("status")
    if status != "FAIL":
        return status
    base = check.get("base_result")
    if base is None:
        return "FAIL_BASE_UNKNOWN"
    targets = [part for part in check.get("command", ()) if part.endswith(".py")]
    if check["kind"] == "import":
        statement = next((part for part in check.get("command", ()) if part.startswith("import ")), "")
        targets = [m.strip()[len("import "):].replace(".", "/") + ".py"
                   for m in statement.split(";") if m.strip().startswith("import ")]
    patched_text, base_text = _text(check), _text(base)
    exc = _exception_type(patched_text)
    where = _failing_file(patched_text, exc, targets)
    new_target = any(t in added for t in targets)
    if where is not None and where in added:
        # No base version to compare: only a syntax error counts for a new module.
        return "FAIL" if check["kind"] == "syntax" else "BASE_UNKNOWN"
    if check["kind"] == "syntax" and new_target and where is None:
        return "FAIL"
    if base.get("status") != "FAIL" or exc is None or _exception_type(base_text) != exc:
        return "FAIL"
    base_where = _failing_file(base_text, exc, targets)
    if where is not None and base_where is not None:
        return "PRE_EXISTING" if where == base_where else "FAIL"
    return "FAIL" if new_target else "PRE_EXISTING"


def paired_v3(checks, added_paths=()):
    """Amendment A6: syntax/import failures paired with the same check on the base tree.

    A failure counts (FAIL) only if the same check does not fail the same way on
    base: base PASS, a different final exception type, or a different file.
    Same type in the same file is PRE_EXISTING. An import failure in a module
    the patch adds is BASE_UNKNOWN; a syntax error there always counts. Both
    PRE_EXISTING and BASE_UNKNOWN are V3 not available for that check. A FAIL
    with no stored base result stays a failure (FAIL_BASE_UNKNOWN).
    """
    added = tuple(added_paths or ())
    verdicts = {c["kind"]: _check_verdict(c, added) for c in checks
                if c.get("kind") in ("syntax", "import")}
    return {
        "failure": any(v in COUNTED for v in verdicts.values()),
        "checks": verdicts,
        "pre_existing": [k for k, v in verdicts.items() if v == "PRE_EXISTING"],
        "base_unknown": [k for k, v in verdicts.items() if v == "BASE_UNKNOWN"],
        "rule": "amendment A6",
    }


def bounded(result):
    return {**result, "stdout": tail(result["stdout"]), "stderr": tail(result["stderr"])}


def run_static_checks(patch, tree, executor, config=None):
    config = config or StaticConfig()
    availability = discover_tools(tree)
    targets = _patch_targets(patch)
    records = []
    for kind in CheckKind:
        spec = availability.tool_for(kind)
        entry = {
            "kind": kind.value,
            "tool": spec.name if spec else None,
            "command": [],
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "tool_version": "unavailable",
            "version_check": None,
            "base_result": None,
            "new_findings": [],
            "status": "NOT_AVAILABLE",
            "reason": availability.evidence.get(kind, ""),
        }
        records.append(entry)
        if spec is None or (kind in (CheckKind.SYNTAX, CheckKind.IMPORT) and not targets):
            if spec is not None:
                entry["reason"] = "patch touches no Python files"
            continue
        command = _command_for(kind, spec, targets)
        version_command = (
            ("python", "-m", "build", "--version")
            if kind is CheckKind.BUILD
            else (command[0], "--version")
        )
        version = capture(executor, version_command, True, config.timeout_s)
        entry["version_check"] = bounded(version)
        if version["exit_code"] == 0:
            entry["tool_version"] = tail((version["stdout"] + version["stderr"]).strip())
        patched = capture(executor, command, True, config.timeout_s)
        entry.update(bounded(patched))
        output = patched["stdout"] + patched["stderr"]
        missing = _missing_tool_reason(kind, spec, patched["exit_code"], output)
        if missing:
            entry.update(status="NOT_AVAILABLE", reason=missing)
        if kind in RELATIVE_CHECKS or (
                kind in (CheckKind.IMPORT, CheckKind.SYNTAX) and patched["status"] == "FAIL"):
            base = capture(executor, command, False, config.timeout_s)
            entry["base_result"] = bounded(base)
            if kind in RELATIVE_CHECKS:
                findings = Counter(output.splitlines()) - Counter(
                    (base["stdout"] + base["stderr"]).splitlines()
                )
                entry["new_findings"] = list(findings.elements())
                entry["finding_comparison"] = "exact diagnostic-line multiset difference"
    summary = {r["kind"]: r["status"] for r in records}
    added = sorted(f.path for f in patch if f.kind.value in ("added", "renamed"))
    available = any(s in ("PASS", "FAIL") for s in summary.values())
    failed = any(summary.get(k) == "FAIL" for k in ("syntax", "import"))
    return SignalRecord(
        kind=SignalKind.STATIC,
        outcome=SignalOutcome.FAIL
        if failed
        else (SignalOutcome.PASS if available else SignalOutcome.NOT_AVAILABLE),
        absence=None if available else SignalAbsence.NOTHING_TO_CHECK,
        detail="v1.4 V3 command evidence; only syntax/import FAIL gates ACCEPT",
        findings={"summary": summary, "checks": records, "v3_absolute_failure": failed,
                  "patch_added_paths": added, "v3_paired": paired_v3(records, added)},
    )
