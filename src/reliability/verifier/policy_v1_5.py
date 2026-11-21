"""v1.5 decision rules R1-R8 (study PROTOCOL §4 "Decision rules", §5 switches).

v1.5 is v1.4.1 plus three candidate switches, all default False, and one
default rule from amendment A4 (ii). With every switch off it returns v1.4.1's
decision on every input except the A4 (ii) class, where v1.4.1's R3b REJECT
becomes R5 FLAG (the unit truth table pins this); what it adds is the matched rule (`rule_id`) and a review label for
ordering human review of FLAGs. First match wins:

    R1  REJECT  patch does not apply, integrity FAIL, or prohibited manipulation
    R2  REJECT  [r2_v3_reject] V3 syntax or import failure
    R3  REJECT  V4 FAIL and V2 FAIL; with [r3_extended_reject] also V4 FAIL
                with a FAIL-confirmed requirement, 2+ failing units, or a V3
                failure (failing units under V4 NOT_AVAILABLE never REJECT)
    R5  FLAG    (amendment A4 (ii), default) V2 FAIL with per-requirement V4
                NOT_AVAILABLE, 1+ requirement PASS and none failing
                                                           signals_disagree
    R3b REJECT  V2 FAIL and V4 neither PASS nor FAIL
    R4  FLAG    V4 FAIL                                        likely_wrong
    R5  FLAG    V2 FAIL and V4 PASS                            signals_disagree
    R6  ACCEPT  v1.4.1's ACCEPT conditions with a V4 full pass (with
                [r6_accept_v2_not_available], V2 NOT_AVAILABLE also counts
                when it had nothing to check, or was incomplete with no
                patched-side timeout or crash: amendment A4 (iii) revised)
    R7  FLAG    nothing failing, V4 not PASS        likely_right if V2 PASS or
                                                    a V4 unit passed, else none
    R8  FLAG    anything else, with v1.4.1's reasons

Like `decision.py`, this module imports no signal implementation at module
level; `evidence_from_signals` is the boundary adapter and imports lazily.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from reliability.verifier.decision import Decision, DecisionRecord, SignalOutcome
from reliability.verifier.policy_v1_4 import EvidenceV14
from reliability.verifier.policy_v1_4_1 import FullPolicyV141

SWITCH_NAMES = ("r2_v3_reject", "r3_extended_reject", "r6_accept_v2_not_available")
V4_DESIGNS = ("per_requirement", "legacy")
#: V2 absences the R6 switch can accept (SignalAbsence values). Incomplete
#: qualifies only without a patched-side timeout or crash (A4 (iii) revised).
V2_NOTHING_TO_CHECK = "nothing_to_check"
V2_INCOMPLETE = "incomplete"
_TIMEOUT_OR_CRASH = ("timeout", "crash")
REVIEW_LABELS = ("likely_wrong", "likely_right", "signals_disagree", "none")
RULE_DECISIONS = {
    "R1": Decision.REJECT, "R2": Decision.REJECT, "R3": Decision.REJECT,
    "R3b": Decision.REJECT, "R4": Decision.FLAG, "R5": Decision.FLAG,
    "R6": Decision.ACCEPT, "R7": Decision.FLAG, "R8": Decision.FLAG,
}


@dataclass(frozen=True, slots=True)
class EvidenceV15(EvidenceV14):
    v4_design: str = "legacy"
    v4_full_pass: bool = False
    v4_fail_confirmed: int = 0
    #: failing requirements (per_requirement) or failing kept tests (legacy)
    v4_failing_units: int = 0
    #: requirements (or kept tests) at PASS
    v4_pass_units: int = 0
    #: why V2 did not report (a SignalAbsence value), None when it reported
    v2_absence: str | None = None
    #: a test timed out or crashed on the patched tree (pass or patched
    #: confirmation), or no patched run is stored so it cannot be ruled out
    v2_patched_timeout_or_crash: bool = False

    def as_dict(self):
        return {
            **EvidenceV14.as_dict(self),
            "v4_design": self.v4_design,
            "v4_full_pass": self.v4_full_pass,
            "v4_fail_confirmed": self.v4_fail_confirmed,
            "v4_failing_units": self.v4_failing_units,
            "v4_pass_units": self.v4_pass_units,
            "v2_absence": self.v2_absence,
            "v2_patched_timeout_or_crash": self.v2_patched_timeout_or_crash,
        }


@dataclass(frozen=True, slots=True)
class DecisionRecordV15(DecisionRecord):
    rule_id: str = ""
    review_label: str = "none"

    def as_dict(self) -> dict:
        return {**DecisionRecord.as_dict(self), "rule_id": self.rule_id,
                "review_label": self.review_label}


@dataclass(frozen=True, slots=True)
class FullPolicyV15(FullPolicyV141):
    name: str = "full-v1.5"
    version: str = "v1.5.0-full"
    r2_v3_reject: bool = False
    r3_extended_reject: bool = False
    r6_accept_v2_not_available: bool = False

    def decide(self, evidence) -> DecisionRecordV15:
        v2, v4 = evidence.regression, evidence.reproduction
        v3 = getattr(evidence, "v3_absolute_failure", False)
        confirmed = getattr(evidence, "v4_fail_confirmed", 0)
        failing = getattr(evidence, "v4_failing_units", 0)
        # v1.4.1's verdict and reasons, reused for R6 and R8.
        old = FullPolicyV141.decide(self, evidence)

        r1 = [reason for condition, reason in (
            (not evidence.patch_applies, "patch fails to apply"),
            (evidence.integrity.is_fail, "integrity check failed"),
            (evidence.prohibited_manipulation,
             "prohibited benchmark or test manipulation detected"),
        ) if condition]
        if r1:
            return self._rule("R1", r1, evidence)
        if self.r2_v3_reject and v3:
            return self._rule("R2", ["v3_absolute_failure"], evidence)
        if v4.is_fail and v2.is_fail:
            return self._rule("R3", ["regression test failed", "reproduction FAIL"], evidence)
        if self.r3_extended_reject and v4.is_fail:
            # Only a V4 FAIL is backed up. Failing units under V4 NOT_AVAILABLE
            # (e.g. FROZEN_BYTES_NOT_IN_PLACE) are missing evidence and fall through.
            extended = [reason for condition, reason in (
                (confirmed >= 1, f"{confirmed} FAIL-confirmed V4 requirement(s)"),
                (failing >= 2, f"{failing} failing V4 units"),
                (v3, "reproduction FAIL with v3_absolute_failure"),
            ) if condition]
            if extended:
                return self._rule("R3", [f"extended: {r}" for r in extended], evidence)
        passing = getattr(evidence, "v4_pass_units", 0)
        if (v2.is_fail and v4 is SignalOutcome.NOT_AVAILABLE
                and getattr(evidence, "v4_design", "legacy") == "per_requirement"
                and passing >= 1 and failing == 0):
            # Amendment A4 (ii): a passing requirement is evidence against V2.
            return self._rule("R5", [
                "regression test failed",
                f"reproduction NOT_AVAILABLE with {passing} requirement(s) PASS and none failing",
            ], evidence, "signals_disagree")
        if v2.is_fail and not v4.is_pass and not v4.is_fail:
            return self._rule(
                "R3b", ["regression test failed", f"reproduction is {v4.value}"], evidence)
        if v4.is_fail:
            return self._rule("R4", old.reasons, evidence, "likely_wrong")
        if v2.is_fail and v4.is_pass:
            return self._rule("R5", old.reasons, evidence, "signals_disagree")

        accept_evidence = evidence
        absence = getattr(evidence, "v2_absence", None)
        if (self.r6_accept_v2_not_available and v2 is SignalOutcome.NOT_AVAILABLE
                and (absence == V2_NOTHING_TO_CHECK
                     or (absence == V2_INCOMPLETE
                         and not getattr(evidence, "v2_patched_timeout_or_crash", True)))):
            # Amendment A4 (iii) revised: error (including an unreliable
            # baseline), timeout and every other absence mean V2 could not run.
            accept_evidence = replace(evidence, regression=SignalOutcome.PASS)
        accept = old if accept_evidence is evidence else FullPolicyV141.decide(self, accept_evidence)
        if getattr(evidence, "v4_full_pass", False) and accept.decision is Decision.ACCEPT:
            reasons = list(accept.reasons)
            if accept_evidence is not evidence:
                reasons.append(f"regression NOT_AVAILABLE ({absence.replace('_', ' ')}) accepted "
                               "(r6_accept_v2_not_available)")
            return self._rule("R6", reasons, evidence)

        if not v2.is_fail and not v4.is_fail and not v3 and not v4.is_pass:
            likely_right = v2.is_pass or getattr(evidence, "v4_pass_units", 0) >= 1
            return self._rule("R7", old.reasons, evidence,
                              "likely_right" if likely_right else "none")
        return self._rule("R8", old.reasons, evidence)

    def _rule(self, rule_id, reasons, evidence, review_label="none") -> DecisionRecordV15:
        return DecisionRecordV15(
            decision=RULE_DECISIONS[rule_id], policy_name=self.name,
            policy_version=self.version, reasons=tuple(reasons),
            evidence=evidence, rule_id=rule_id, review_label=review_label,
        )


def _v4_fields(reproduction) -> dict:
    """Read the V4 summary part B wrote; legacy records get units from kept tests."""
    findings = reproduction.findings
    setup = findings.get("setup") or {}
    design = setup.get("design", "legacy")
    if design not in V4_DESIGNS:
        raise ValueError(f"unknown V4 design {design!r}")
    is_pass = reproduction.outcome is SignalOutcome.PASS
    if design == "per_requirement":
        counts = findings.get("verdict_counts") or {}
        # Only two independent passes can confirm a failure.
        confirmed = counts.get("FAIL_CONFIRMED", 0) if setup.get("passes") == 2 else 0
        return dict(
            v4_design=design,
            v4_full_pass=is_pass and findings.get("full_pass") is True,
            v4_fail_confirmed=confirmed,
            v4_failing_units=counts.get("FAIL_CONFIRMED", 0) + counts.get("FAIL_SINGLE", 0),
            v4_pass_units=counts.get("PASS", 0),
        )
    verdicts = [test.get("verdict") for test in findings.get("patched", ())]
    return dict(v4_design=design, v4_full_pass=is_pass, v4_fail_confirmed=0,
                v4_failing_units=verdicts.count("fail"), v4_pass_units=verdicts.count("pass"))


def patched_timeout_or_crash(findings) -> bool:
    """Whether a stored V2 patched run or patched confirmation has a timeout or crash.

    True also when no patched run is stored, because then it cannot be ruled out.
    """
    patched = findings.get("patched")
    if not isinstance(patched, dict):
        return True
    runs = [patched] + [run for run in findings.get("confirmations") or ()
                        if (run.get("confirmation") or {}).get("tree") == "patched"]
    return any(
        run.get("timed_out") is True
        or any(test.get("status") in _TIMEOUT_OR_CRASH
               for key in ("results", "raw_results", "execution_results")
               for test in run.get(key) or ())
        for run in runs)


def evidence_from_signals(signals) -> EvidenceV15:
    from reliability.verifier.policy_v1_4 import evidence_from_signals as v1_4_evidence
    from reliability.verifier.record import SignalKind

    base = v1_4_evidence(signals)
    regression = signals[SignalKind.REGRESSION]
    absence = regression.absence
    return EvidenceV15(
        **{k: getattr(base, k) for k in EvidenceV14.__dataclass_fields__},
        **_v4_fields(signals[SignalKind.REPRODUCTION]),
        v2_absence=absence.value if absence is not None else None,
        v2_patched_timeout_or_crash=patched_timeout_or_crash(regression.findings),
    )


def switches_from_config_text(text: str) -> dict[str, bool]:
    """The three switches from a verifier config's `v1_5` block."""
    import yaml

    block = (yaml.safe_load(text) or {}).get("v1_5") or {}
    if block.get("decision_policy") != "full-v1.5":
        raise ValueError("config does not select decision_policy: full-v1.5")
    switches = {name: block.get(name, False) for name in SWITCH_NAMES}
    if any(type(value) is not bool for value in switches.values()):
        raise ValueError("v1.5 switches must be booleans")
    return switches


def policy_from_config(path: Path) -> FullPolicyV15:
    """The v1.5 policy and switches named in a verifier config's `v1_5` block."""
    return FullPolicyV15(**switches_from_config_text(Path(path).read_text(encoding="utf-8")))


def get_policy(name: str = "full-v1.5", **switches) -> FullPolicyV15:
    if name not in ("full-v1.5", "v1.5.0-full"):
        raise KeyError("v1.5 entry point requires full-v1.5")
    return FullPolicyV15(**switches)
