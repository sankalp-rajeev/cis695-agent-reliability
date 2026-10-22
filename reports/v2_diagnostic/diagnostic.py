"""Stored V2 evidence only. No oracle inputs, selection, execution, or decisions.

The caller supplies a projection of an existing verification record and the
candidate diff. Tier membership cannot be recovered from the recorded union.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from reliability.verifier.integrity import is_test_file
from reliability.verifier.patch import parse_patch, touched_symbols
from reliability.verifier.regression import Outcome
from reliability.verifier.record import VerificationRecord

FIELDS = (
    "instance_id", "repo", "source_run", "verifier_decision", "v2_outcome",
    "changed_source_files", "changed_symbols", "test_layout_convention",
    "tier1_selected_count", "tier2_selected_count", "total_selected_tests",
    "number_executed", "number_timed_out", "number_not_run",
    "number_pre_existing_failures", "number_observed_regressions", "v2_runtime_s",
    "v2_signal", "not_available_reason", "timeout_fraction", "execution_coverage",
    "selected_test_ids", "per_test_outcomes", "artifact_kind", "artifact_note",
)


def put(row: dict, field: str, value, status: str = "recorded", source: str = "") -> None:
    """Every value has independent provenance; missing is never numeric zero."""
    if status not in {"recorded", "inferred", "missing"}:
        raise ValueError(status)
    if value is None:
        status = "missing"
    row[field] = value
    row[field + "_status"] = status
    row[field + "_source"] = source


def project_local(path: Path) -> dict:
    """Validate the existing schema; expose only the fields this reader needs."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    record = VerificationRecord.model_validate(raw)
    projected = {
        "decision": record.decision.decision.value,
        "regression": raw["regression"],
        "patch_sha256": record.patch_sha256,
    }
    # Schema defaults are useful for execution, but are not recorded evidence.
    for key in ("selected_tests", "selection_convention"):
        if key in raw:
            projected[key] = raw[key]
    return projected


def collect(identity: dict, evidence: dict | None, patch_text: str | None,
            *, source: str, patch_source: str, artifact_kind: str, note: str) -> dict:
    """Extract stored facts and mechanically derived candidate-only fields."""
    row: dict = {}
    for field in FIELDS:
        put(row, field, None, source="not stored in available study artifacts")
    for field in ("instance_id", "repo", "source_run", "verifier_decision", "v2_outcome"):
        put(row, field, identity[field], source="docs/results_100.csv")
    put(row, "artifact_kind", artifact_kind, "inferred", source)
    put(row, "artifact_note", note, "inferred", source)

    if patch_text is not None:
        patch = parse_patch(patch_text)
        # Same source-file definition and symbol extractor as select_tests().
        files = [f.path for f in patch if f.path.endswith(".py")
                 and not is_test_file(f.path) and not f.is_binary]
        put(row, "changed_source_files", files, "inferred", patch_source)
        put(row, "changed_symbols", list(touched_symbols(patch)), "inferred", patch_source)
    if evidence is None:
        return row

    for field, key in (("test_layout_convention", "selection_convention"),
                       ("selected_test_ids", "selected_tests")):
        if key in evidence:
            put(row, field, evidence[key], source=source)
    selected = evidence.get("selected_tests")
    if selected is not None:
        put(row, "total_selected_tests", len(selected), "inferred", source + ":selected_tests")

    reg = evidence.get("regression") or {}
    findings = reg.get("findings") or {}
    for field, value in (("v2_runtime_s", reg.get("duration_s")),
                         ("v2_signal", findings.get("signal")),
                         ("number_executed", findings.get("n_executed"))):
        put(row, field, value, source=source + ":regression")
    if reg.get("outcome") != identity["v2_outcome"]:
        raise ValueError(f"V2 disagrees with committed row: {identity['instance_id']}")
    if evidence.get("decision") != identity["verifier_decision"]:
        raise ValueError(f"decision disagrees with committed row: {identity['instance_id']}")

    summary = findings.get("summary")
    # Missing keys are known zeros only when the complete sparse histogram
    # accounts for every selected test. Otherwise leave them missing.
    complete = (isinstance(summary, dict) and selected is not None
                and sum(summary.values()) == len(selected))
    mapping = {
        "number_timed_out": Outcome.TIMEOUT.value,
        "number_not_run": Outcome.NOT_RUN.value,
        "number_pre_existing_failures": Outcome.PRE_EXISTING_FAIL.value,
        "number_observed_regressions": Outcome.REGRESSION.value,
    }
    for field, key in mapping.items():
        if summary is not None and key in summary:
            put(row, field, summary[key], source=source + ":regression.findings.summary")
        elif complete:
            put(row, field, 0, "inferred", source + ":complete sparse outcome histogram")
    if complete and row["number_executed"] is not None:
        executed = sum(n for name, n in summary.items() if Outcome(name).executed)
        if executed != row["number_executed"]:
            raise ValueError("stored n_executed disagrees with existing Outcome.executed semantics")
    if identity["v2_outcome"] == "NOT_AVAILABLE" and reg:
        reason = "; ".join(str(x) for x in (reg.get("absence"), reg.get("detail")) if x)
        put(row, "not_available_reason", reason or None, source=source + ":regression")
    count = row["total_selected_tests"]
    if count:
        for field, numerator in (("timeout_fraction", "number_timed_out"),
                                 ("execution_coverage", "number_executed")):
            if row[numerator] is not None:
                put(row, field, row[numerator] / count, "inferred", numerator + "/selected")
    return row


def distribution(values: list[float | int | None]) -> dict:
    """Linear-interpolated quantiles; missing and zero are distinct."""
    available = sorted(v for v in values if v is not None)
    result = {"n": len(available), "missing": len(values) - len(available)}
    if not available:
        return result

    def quantile(p):
        index = (len(available) - 1) * p
        lo = int(index)
        hi = min(lo + 1, len(available) - 1)
        return available[lo] + (available[hi] - available[lo]) * (index - lo)

    result.update(min=available[0], p25=quantile(.25), median=statistics.median(available),
                  p75=quantile(.75), p90=quantile(.9), max=available[-1],
                  mean=statistics.mean(available), total=sum(available))
    return result


def encoded(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return value
