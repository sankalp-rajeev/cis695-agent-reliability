"""Adapters from signal results to the neutral decision vocabulary (Phase 7).

The only place where signal types and policy types meet. `decision.py` imports
nothing from the signal modules and this module imports nothing from any policy,
so a new policy needs no change here and a signal changing its internals needs
no change there.

Every mapping below makes the same judgement in a different costume: a check
that did not run, was not configured, or found nothing to run against yields
`NOT_AVAILABLE`, never `PASS`.
"""

from __future__ import annotations

from collections.abc import Callable

from reliability.verifier.decision import Evidence, SignalOutcome
from reliability.verifier.integrity import IntegrityReport, Violation
from reliability.verifier.regression import RegressionReport, Signal
from reliability.verifier.static_checks import StaticReport

#: Integrity violations that constitute benchmark or test manipulation. These
#: reject on their own rather than merely failing the integrity signal, matching
#: the design's separate "prohibited manipulation" clause.
MANIPULATION_VIOLATIONS = (
    Violation.HARNESS_FILE_EDIT,
    Violation.TEST_DELETED,
    Violation.TEST_WEAKENED,
    Violation.UNEXPECTED_CONFIG_EDIT,
)

#: Risk features that raise a high-severity flag, with the predicate that does
#: it. Deliberately short: Phase 4.2 features are measurements first, and a
#: broad list here would reintroduce through the back door the auto-failing that
#: Phase 4.2 exists to avoid. Raising a flag downgrades ACCEPT to FLAG — it
#: never rejects — so the cost of a false positive is a human look, not a
#: discarded patch.
#:
#: `broad_excepts_added` is here because swallowing an exception is the
#: canonical way to make a failing test pass without repairing anything, which
#: is precisely the plausible-but-wrong patch this study is built to catch.
#: `deletes_files` is here because deletion removes behaviour that the selected
#: tests may simply no longer cover.
HIGH_SEVERITY_RISK: dict[str, Callable[[object], bool]] = {
    "deletes_files": lambda v: v is True,
    "broad_excepts_added": lambda v: isinstance(v, int) and v > 0,
}


def integrity_outcome(report: IntegrityReport) -> SignalOutcome:
    return SignalOutcome.PASS if report.passed else SignalOutcome.FAIL


def regression_outcome(report: RegressionReport) -> SignalOutcome:
    """Map the regression signal.

    `NOT_AVAILABLE` and `BASELINE_UNRELIABLE` both map to `NOT_AVAILABLE`:
    neither is a pass, and neither is the patch's fault. Policy §4 and §5.5 both
    say these route to FLAG rather than ACCEPT, which is what falls out of
    mapping them this way.
    """
    if report.signal is Signal.PASS:
        return SignalOutcome.PASS
    if report.signal is Signal.FAIL:
        return SignalOutcome.FAIL
    return SignalOutcome.NOT_AVAILABLE


def static_outcome(report: StaticReport) -> SignalOutcome:
    """Map the aggregate static signal.

    A new failure in any configured check fails the signal. If nothing was
    configured and nothing ran, the signal is `NOT_AVAILABLE` — a repository
    with no linter configured has not demonstrated that the patch is clean.
    """
    if report.new_failures:
        return SignalOutcome.FAIL
    if report.n_ran == 0:
        return SignalOutcome.NOT_AVAILABLE
    return SignalOutcome.PASS


def has_high_severity_risk(report: IntegrityReport) -> bool:
    vector = report.risk.as_vector()
    return any(pred(vector.get(key)) for key, pred in HIGH_SEVERITY_RISK.items())


def high_severity_flags(report: IntegrityReport) -> tuple[str, ...]:
    """Which flags fired, for the decision record's reasons."""
    vector = report.risk.as_vector()
    return tuple(
        key for key, pred in HIGH_SEVERITY_RISK.items() if pred(vector.get(key))
    )


def has_prohibited_manipulation(report: IntegrityReport) -> bool:
    return any(v in report.violations for v in MANIPULATION_VIOLATIONS)


def build_evidence(
    integrity: IntegrityReport | None = None,
    regression: RegressionReport | None = None,
    static: StaticReport | None = None,
    reproduction: SignalOutcome | None = None,
) -> Evidence:
    """Assemble the evidence bundle a policy will judge.

    Any signal passed as `None` is `NOT_AVAILABLE`. `reproduction` is taken as a
    raw outcome until V4's report type exists; inventing one here would guess at
    an interface the implementation should choose. The slot is required either
    way — V4 is load-bearing in the policy, not an optional extra.
    """
    return Evidence(
        integrity=(
            integrity_outcome(integrity) if integrity is not None
            else SignalOutcome.NOT_AVAILABLE
        ),
        regression=(
            regression_outcome(regression) if regression is not None
            else SignalOutcome.NOT_AVAILABLE
        ),
        static=(
            static_outcome(static) if static is not None
            else SignalOutcome.NOT_AVAILABLE
        ),
        reproduction=reproduction or SignalOutcome.NOT_AVAILABLE,
        high_severity_risk=(
            has_high_severity_risk(integrity) if integrity is not None else False
        ),
        prohibited_manipulation=(
            has_prohibited_manipulation(integrity) if integrity is not None else False
        ),
        patch_applies=(
            Violation.DOES_NOT_APPLY not in integrity.violations
            if integrity is not None else True
        ),
    )
