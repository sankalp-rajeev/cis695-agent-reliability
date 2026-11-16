"""Selectable v1.4 combining rule; v1.3 objects and serialization are unchanged."""

from dataclasses import dataclass

from reliability.verifier.decision import Decision, Evidence, FullPolicy


@dataclass(frozen=True, slots=True)
class EvidenceV14(Evidence):
    v3_absolute_failure: bool = False
    v1_analysis_incomplete: bool = False

    def as_dict(self):
        return {
            **Evidence.as_dict(self),
            "v3_absolute_failure": self.v3_absolute_failure,
            "v1_analysis_incomplete": self.v1_analysis_incomplete,
        }


@dataclass(frozen=True, slots=True)
class FullPolicyV14(FullPolicy):
    name: str = "full-v1.4"
    version: str = "v1.4.0-full"

    def decide(self, evidence):
        record = super(FullPolicyV14, self).decide(evidence)
        reasons = []
        if getattr(evidence, "v3_absolute_failure", False):
            reasons.append("v3_absolute_failure")
        if getattr(evidence, "v1_analysis_incomplete", False):
            reasons.append("v1_analysis_incomplete")
        if reasons and record.decision is not Decision.REJECT:
            return self._record(
                Decision.FLAG,
                tuple(reasons) + (record.reasons if record.decision is Decision.FLAG else ()),
                evidence,
            )
        return record


def evidence_from_signals(signals):
    from reliability.verifier.record import SignalKind
    from reliability.verifier.run import _evidence_from

    base = _evidence_from(signals)
    checks = signals[SignalKind.STATIC].findings.get("summary", {})
    analysis = signals[SignalKind.INTEGRITY].findings.get("ast_analysis", [])
    return EvidenceV14(
        **{k: getattr(base, k) for k in Evidence.__dataclass_fields__},
        v3_absolute_failure=any(checks.get(k) == "FAIL" for k in ("syntax", "import")),
        v1_analysis_incomplete=any(r["status"] != "checked" for r in analysis),
    )


def get_policy(name="full-v1.4"):
    if name not in ("full-v1.4", "v1.4.0-full"):
        raise KeyError("v1.4 entry point requires full-v1.4")
    return FullPolicyV14()
