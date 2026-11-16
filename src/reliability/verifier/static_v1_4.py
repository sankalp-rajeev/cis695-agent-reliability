"""V3 command evidence with separate byte-bounded streams, opt-in for v1.4."""

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
        if kind in RELATIVE_CHECKS or (kind is CheckKind.IMPORT and patched["status"] == "FAIL"):
            base = capture(executor, command, False, config.timeout_s)
            entry["base_result"] = bounded(base)
            if kind in RELATIVE_CHECKS:
                findings = Counter(output.splitlines()) - Counter(
                    (base["stdout"] + base["stderr"]).splitlines()
                )
                entry["new_findings"] = list(findings.elements())
                entry["finding_comparison"] = "exact diagnostic-line multiset difference"
    summary = {r["kind"]: r["status"] for r in records}
    available = any(s in ("PASS", "FAIL") for s in summary.values())
    failed = any(summary.get(k) == "FAIL" for k in ("syntax", "import"))
    return SignalRecord(
        kind=SignalKind.STATIC,
        outcome=SignalOutcome.FAIL
        if failed
        else (SignalOutcome.PASS if available else SignalOutcome.NOT_AVAILABLE),
        absence=None if available else SignalAbsence.NOTHING_TO_CHECK,
        detail="v1.4 V3 command evidence; only syntax/import FAIL gates ACCEPT",
        findings={"summary": summary, "checks": records, "v3_absolute_failure": failed},
    )
