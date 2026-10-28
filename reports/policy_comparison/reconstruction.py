"""Pure read-only evaluation of the implemented policies on frozen signals.

There is intentionally no oracle argument. No signal implementations execute.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from reliability.verifier.decision import BaselinePolicy, FullPolicy, Evidence, SignalOutcome


def policy_results(v1, v2, v3, v4, high_risk=None):
    if v1 not in {"PASS", "FAIL"}:
        raise ValueError("cannot identify ancillary integrity predicates when V1 is unavailable")
    # The adapter makes V1 PASS imply no integrity violations, hence applies=True
    # and manipulation=False. With V1 FAIL, its rejection dominates every value
    # of these additional predicates; defaults here are not recorded findings.
    def evidence(risk):
        return Evidence(integrity=SignalOutcome(v1), regression=SignalOutcome(v2),
                        static=SignalOutcome(v3), reproduction=SignalOutcome(v4),
                        high_severity_risk=risk, patch_applies=True, prohibited_manipulation=False)
    baseline = BaselinePolicy().decide(evidence(False))
    choices = (False, True) if high_risk is None else (high_risk,)
    full = [FullPolicy().decide(evidence(value)) for value in choices]
    return dict(baseline_decision=baseline.decision.value, baseline_reasons=list(baseline.reasons),
                baseline_version=baseline.policy_version, full_version=FullPolicy().version,
                full_possible_decisions=sorted({r.decision.value for r in full}),
                full_reasons=sorted({reason for r in full for reason in r.reasons}))


def explicit_high_risks(committed_report):
    """Read explicit findings from the committed merged report, not an oracle label."""
    result = {}
    for line in committed_report.splitlines():
        if line.startswith("| ") and "high-severity risk flag present" in line:
            cells = [part.strip() for part in line.split("|")]
            if len(cells) > 2 and "__" in cells[1]:
                result[cells[1]] = True
    return result


def reconstruct(raw, high_risk_evidence):
    v1, v2, v3, v4 = (raw[k] for k in ("integrity", "regression", "static", "reproduction"))
    risk = high_risk_evidence.get(raw["instance_id"])
    risk_status = "recorded_in_committed_report" if risk is not None else "missing"
    risk_source = "HEAD:docs/results_100.md explicit high-severity reason" if risk is not None else "not serialized in merged CSV"
    result = policy_results(v1, v2, v3, v4, risk)
    independent = True
    if len(result["full_possible_decisions"]) > 1:
        # Full decisions are authoritative observations. This implication is
        # explicitly non-independent and is never used to reconstruct Baseline.
        if raw["verifier_decision"] not in {"ACCEPT", "FLAG"}:
            raise ValueError("unexpected committed decision in risk-dependent branch")
        risk = raw["verifier_decision"] == "FLAG"
        risk_status = "inferred_policy_implication_not_independent"
        risk_source = "committed Full decision + implemented FullPolicy accept conditions"
        result = policy_results(v1, v2, v3, v4, risk)
        independent = False
    if raw["verifier_decision"] not in result["full_possible_decisions"]:
        raise ValueError("committed Full decision conflicts with implemented policy: " + raw["instance_id"])
    row = dict(instance_id=raw["instance_id"], source_run=raw["source_run"], repo=raw["repo"],
        stratum=raw["stratum"], oracle=raw["oracle"], oracle_status="recorded_authoritative",
        oracle_source="HEAD:docs/results_100.csv", V1=v1, V2=v2, V3=v3, V4=v4,
        signal_status="recorded", signal_source="HEAD:docs/results_100.csv",
        high_severity_risk=risk, high_severity_risk_status=risk_status, high_severity_risk_source=risk_source,
        high_severity_risk_decision_relevant=v1 == v2 == v4 == "PASS",
        patch_applies=True if v1 == "PASS" else None,
        prohibited_manipulation=False if v1 == "PASS" else None,
        ancillary_integrity_status="inferred_from_V1_PASS" if v1 == "PASS" else "missing_but_V1_FAIL_dominates",
        ancillary_integrity_source="integrity.IntegrityReport.passed + evidence.build_evidence adapter contract",
        baseline_decision=result["baseline_decision"], baseline_version=result["baseline_version"],
        baseline_status="reconstructed_independently_from_frozen_signals",
        baseline_source="src/reliability/verifier/decision.py:BaselinePolicy.decide",
        baseline_reasons=result["baseline_reasons"],
        full_decision=raw["verifier_decision"], full_code_version=result["full_version"],
        full_recorded_policy_version=None, full_recorded_policy_version_status="missing_from_merged_csv",
        full_status="recorded_authoritative", full_source="HEAD:docs/results_100.csv:verifier_decision",
        full_code_check="matches_with_independent_or_invariant_risk_evidence" if independent else "matches_conditional_on_inferred_risk_not_independent",
        full_code_possible_reasons=result["full_reasons"], decision_changed=result["baseline_decision"] != raw["verifier_decision"],
        acceptance_changed=(result["baseline_decision"] == "ACCEPT") != (raw["verifier_decision"] == "ACCEPT"),
        transition_type=result["baseline_decision"] + " -> " + raw["verifier_decision"])
    return row
