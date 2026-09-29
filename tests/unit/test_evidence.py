"""Phase 7: the adapter from signal reports to the decision vocabulary.

The truth table in `test_decision.py` proves the combining rule is total over
the neutral vocabulary. These tests prove the translation *into* that vocabulary
is faithful — in particular that no signal's "did not run" state is ever mapped
to PASS on the way in, which would defeat the policy without touching it.
"""

from __future__ import annotations

import pytest

from reliability.verifier.decision import Decision, FullPolicy, SignalOutcome
from reliability.verifier.evidence import (
    build_evidence,
    has_high_severity_risk,
    has_prohibited_manipulation,
    high_severity_flags,
    integrity_outcome,
    regression_outcome,
    static_outcome,
)
from reliability.verifier.integrity import (
    Finding,
    IntegrityReport,
    RiskFeatures,
    Violation,
)
from reliability.verifier.regression import Outcome, RegressionReport, Signal
from reliability.verifier.static_checks import (
    CheckKind,
    CheckResult,
    CheckStatus,
    StaticReport,
)

PASS = SignalOutcome.PASS
FAIL = SignalOutcome.FAIL
NA = SignalOutcome.NOT_AVAILABLE


def integrity(*violations, **risk) -> IntegrityReport:
    return IntegrityReport(
        findings=tuple(Finding(v, detail="fixture") for v in violations),
        risk=RiskFeatures(**risk),
    )


def regression(signal: Signal, **kwargs) -> RegressionReport:
    return RegressionReport(instance_id="fixture__repo-1", signal=signal, **kwargs)


def static(*results: CheckResult) -> StaticReport:
    return StaticReport(results=results)


def check(kind, status, baseline=None) -> CheckResult:
    return CheckResult(kind=kind, status=status, tool="tool", baseline_status=baseline)


# --- integrity -------------------------------------------------------------


def test_clean_integrity_passes():
    assert integrity_outcome(integrity()) is PASS


def test_any_violation_fails_integrity():
    assert integrity_outcome(integrity(Violation.CONFLICT_MARKERS)) is FAIL


def test_does_not_apply_sets_patch_applies_false():
    evidence = build_evidence(integrity=integrity(Violation.DOES_NOT_APPLY))
    assert evidence.patch_applies is False
    assert FullPolicy().decide(evidence).decision is Decision.REJECT


@pytest.mark.parametrize("violation", [
    Violation.HARNESS_FILE_EDIT,
    Violation.TEST_DELETED,
    Violation.TEST_WEAKENED,
    Violation.UNEXPECTED_CONFIG_EDIT,
])
def test_manipulation_violations_are_flagged_as_manipulation(violation):
    assert has_prohibited_manipulation(integrity(violation))


@pytest.mark.parametrize("violation", [
    Violation.CONFLICT_MARKERS, Violation.BINARY_BLOB, Violation.EMPTY])
def test_non_manipulation_violations_are_not(violation):
    assert not has_prohibited_manipulation(integrity(violation))


# --- risk ------------------------------------------------------------------


def test_deleting_files_raises_a_high_severity_flag():
    assert has_high_severity_risk(integrity(deletes_files=True))
    assert "deletes_files" in high_severity_flags(integrity(deletes_files=True))


def test_swallowing_exceptions_raises_a_high_severity_flag():
    assert has_high_severity_risk(integrity(broad_excepts_added=1))


def test_a_large_but_ordinary_patch_raises_no_flag():
    """Size alone is a measurement, not a severity signal."""
    assert not has_high_severity_risk(
        integrity(files_changed=40, lines_added=900, net_lines=800))


def test_risk_does_not_change_the_integrity_signal():
    """Phase 4.2 again: risk is recorded beside the decision, not inside it."""
    assert integrity_outcome(integrity(deletes_files=True, broad_excepts_added=3)) is PASS


def test_risk_only_downgrades_accept():
    risky = build_evidence(integrity=integrity(deletes_files=True))
    assert risky.high_severity_risk
    assert FullPolicy().decide(risky).decision is not Decision.REJECT


# --- regression ------------------------------------------------------------


@pytest.mark.parametrize("signal,expected", [
    (Signal.PASS, PASS),
    (Signal.FAIL, FAIL),
    (Signal.NOT_AVAILABLE, NA),
    (Signal.BASELINE_UNRELIABLE, NA),
])
def test_regression_signal_mapping(signal, expected):
    assert regression_outcome(regression(signal)) is expected


def test_unreliable_baseline_flags_rather_than_accepting_or_rejecting():
    """Policy §5.5: an untrustworthy baseline is not the patch's fault, and is
    also not evidence the patch is fine."""
    evidence = build_evidence(
        integrity=integrity(), regression=regression(Signal.BASELINE_UNRELIABLE))
    assert FullPolicy().decide(evidence).decision is Decision.FLAG


def test_nothing_executed_never_accepts():
    evidence = build_evidence(
        integrity=integrity(),
        regression=regression(Signal.NOT_AVAILABLE, n_executed=0),
        reproduction=PASS)
    assert FullPolicy().decide(evidence).decision is Decision.FLAG


def test_pre_existing_failures_do_not_fail_the_signal():
    report = regression(Signal.PASS, outcomes={
        "t1": Outcome.PASS, "t2": Outcome.PRE_EXISTING_FAIL}, n_executed=2)
    assert regression_outcome(report) is PASS


# --- static ----------------------------------------------------------------


def test_static_passes_when_configured_checks_pass():
    report = static(
        check(CheckKind.SYNTAX, CheckStatus.PASS),
        check(CheckKind.LINT, CheckStatus.PASS))
    assert static_outcome(report) is PASS


def test_new_failure_fails_the_static_signal():
    report = static(
        check(CheckKind.SYNTAX, CheckStatus.PASS),
        check(CheckKind.LINT, CheckStatus.FAIL, baseline=CheckStatus.PASS))
    assert static_outcome(report) is FAIL


def test_pre_existing_lint_failure_does_not_fail_the_static_signal():
    report = static(
        check(CheckKind.LINT, CheckStatus.FAIL, baseline=CheckStatus.FAIL))
    assert static_outcome(report) is PASS


def test_a_repo_configuring_nothing_is_not_available_not_pass():
    """The Phase 6 principle, carried into Phase 7 unchanged."""
    report = static(*[
        CheckResult(kind=k, status=CheckStatus.NOT_AVAILABLE) for k in CheckKind])
    assert static_outcome(report) is NA
    assert static_outcome(report) is not PASS


def test_all_checks_timing_out_is_not_a_pass():
    report = static(*[
        CheckResult(kind=k, status=CheckStatus.TIMEOUT) for k in CheckKind])
    assert static_outcome(report) is not PASS


# --- assembling ------------------------------------------------------------


def test_absent_signals_default_to_not_available():
    evidence = build_evidence()
    assert evidence.integrity is NA
    assert evidence.regression is NA
    assert evidence.static is NA
    assert evidence.reproduction is NA


def test_absent_integrity_does_not_invent_a_risk_flag():
    evidence = build_evidence()
    assert evidence.high_severity_risk is False
    assert evidence.prohibited_manipulation is False


def test_reproduction_is_passed_through_as_a_raw_outcome():
    """V4's report type is not invented here; the adapter leaves a typed slot."""
    assert build_evidence(reproduction=PASS).reproduction is PASS


def test_a_clean_run_today_flags_for_want_of_v4():
    """End to end through the adapter: the best evidence available right now."""
    evidence = build_evidence(
        integrity=integrity(),
        regression=regression(Signal.PASS, n_executed=12),
        static=static(check(CheckKind.SYNTAX, CheckStatus.PASS)))

    record = FullPolicy().decide(evidence)
    assert record.decision is Decision.FLAG
    assert record.reasons == ((
        "no issue-specific execution signal supports repair "
        "(reproduction is NOT_AVAILABLE)"
    ),)


def test_the_same_run_accepts_once_v4_reports():
    evidence = build_evidence(
        integrity=integrity(),
        regression=regression(Signal.PASS, n_executed=12),
        static=static(check(CheckKind.SYNTAX, CheckStatus.PASS)),
        reproduction=PASS)
    assert FullPolicy().decide(evidence).decision is Decision.ACCEPT
