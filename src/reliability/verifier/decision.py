"""Verifier decision policy (Phase 7).

The combining rule, and nothing else. This module imports no signal
implementation — not integrity, not regression, not static checks — and works
entirely on the neutral `SignalOutcome` vocabulary below. Adapters convert each
signal's native result type into that vocabulary at the boundary
(`evidence.py`), so a second policy can be written here without touching any
signal code, and a signal can change its internals without touching policy.

The rule is from the technical design §12:

    REJECT if:
        patch fails to apply
        OR regression test fails
        OR prohibited benchmark/test manipulation detected

    ACCEPT if:
        integrity passes
        AND relevant regression checks pass
        AND at least one issue-specific execution signal supports repair
        AND no high-severity risk flags

    FLAG otherwise

**V4 is load-bearing, not optional.** The third ACCEPT condition requires an
issue-specific execution signal, and that signal is V4's issue-derived
reproduction tests. An absent reproduction signal is treated as what it is: a
condition not met, so the decision falls through to FLAG. This is the same
principle as `NOT_RUN` in Phase 5 and `NOT_AVAILABLE` in Phase 6: absence of a
check is never evidence of correctness. A reproduction FAIL is likewise an
unmet condition rather than a REJECT, because a generated test is weaker
evidence than the repository's own tests. The rule was unchanged when V4 was
built in v1.2.0; only the signal started reporting.

**v1.3.0: a regression FAIL no longer dominates when V4 PASSes.** This is a
deliberate, named deviation from a literal reading of §12, made for the
failure mode documented in `docs/VERIFIER_POLICY.md` §5.6 (superseded
assertion). Regression failing because the patch broke something and
regression failing because the patch correctly changed behaviour an existing
test still asserts the old way are the same observation from inside the
oracle-blind constraint — the verifier cannot tell them apart by reading the
regression result alone. V4's reproduction tests are generated from the issue
text and are the one other oracle-blind signal that can disagree. When it
does — regression FAIL, reproduction PASS — the two signals disagree about the
same patch, and REJECT would discard a patch that the issue-derived evidence
says addresses the issue. The rule routes that disagreement to FLAG, not
ACCEPT: it is still unresolved evidence, not a second vote that overrides the
regression result. `evidence.py` records which test failed and why; this
module only sees the two outcomes and that they disagree. Every other REJECT
condition (patch does not apply, integrity failure, prohibited manipulation)
still dominates regardless of what V4 says, and the exception only ever
produces FLAG — a regression FAIL with reproduction FAIL or NOT_AVAILABLE
still REJECTs exactly as before, since there is no second signal to disagree
with it. See the decisions log, 2026-10-05, for the validating cases
(`django__django-16899`, `sphinx-doc__sphinx-10449` under the Tier 0 ablation).

The baseline policy is deliberately different, not a degraded copy — see
`BaselinePolicy`. It still ignores reproduction entirely, so this exception
does not apply to it: baseline has no V4 signal to disagree with regression,
so a regression FAIL still REJECTs under baseline exactly as before.

**Consequence, recorded rather than hidden: baseline can now be stricter than
full on one specific combination** (regression FAIL, reproduction PASS,
nothing else wrong) — baseline REJECTs, full FLAGs. Before v1.3.0 the two
policies agreed on every REJECT and baseline was never stricter; that
invariant held because both policies read the same reject conditions. It no
longer holds *everywhere*, but it still holds everywhere except this one named
case, because that is precisely the evidence baseline is defined not to see.
This is not a bug in the comparison; it is what the comparison is for — V4
is one of the things full has that baseline does not, and here it is shown
changing a REJECT into a FLAG rather than only changing a FLAG into an ACCEPT.
`tests/unit/test_decision.py` pins the narrowed invariant and the one
exception separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    FLAG = "FLAG"
    REJECT = "REJECT"


class SignalOutcome(str, Enum):
    """Neutral vocabulary every signal is mapped into.

    `NOT_AVAILABLE` covers a check that could not run, was not configured, or is
    not implemented yet. It is never equivalent to PASS.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"

    @property
    def is_pass(self) -> bool:
        return self is SignalOutcome.PASS

    @property
    def is_fail(self) -> bool:
        return self is SignalOutcome.FAIL


@dataclass(frozen=True, slots=True)
class Evidence:
    """Everything a policy is allowed to see.

    Signals default to `NOT_AVAILABLE` so a policy evaluated before a layer
    reports behaves correctly rather than raising. V4 occupies this slot the
    same way the others do; an unbuilt layer is an absence, not a missing field.
    """

    integrity: SignalOutcome = SignalOutcome.NOT_AVAILABLE
    regression: SignalOutcome = SignalOutcome.NOT_AVAILABLE
    static: SignalOutcome = SignalOutcome.NOT_AVAILABLE
    reproduction: SignalOutcome = SignalOutcome.NOT_AVAILABLE   # V4
    high_severity_risk: bool = False
    prohibited_manipulation: bool = False
    patch_applies: bool = True

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "integrity": self.integrity.value,
            "regression": self.regression.value,
            "static": self.static.value,
            "reproduction": self.reproduction.value,
            "high_severity_risk": self.high_severity_risk,
            "prohibited_manipulation": self.prohibited_manipulation,
            "patch_applies": self.patch_applies,
        }


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """A decision, with the policy that made it and why.

    `policy_version` is recorded on every decision (Phase 7.1). Two runs
    carrying the same version string must have been judged by the same rules,
    which is why changing any policy value requires bumping it.
    """

    decision: Decision
    policy_name: str
    policy_version: str
    reasons: tuple[str, ...] = ()
    evidence: Evidence = field(default_factory=Evidence)

    def as_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "reasons": list(self.reasons),
            "evidence": self.evidence.as_dict(),
        }


class DecisionPolicy(Protocol):
    name: str
    version: str

    def decide(self, evidence: Evidence) -> DecisionRecord: ...


@dataclass(frozen=True, slots=True)
class FullPolicy:
    """Technical design §12, implemented literally.

    Every branch returns a `Decision`; there is no path that falls off the end,
    which is what the Phase 7.1 truth-table gate asserts exhaustively.
    """

    name: str = "full"
    version: str = "v1.3.0-full"
    require_reproduction: bool = True
    #: Primary rule. The pre-declared secondary policy
    #: (`RelaxedPolicy`, `v1.3.0-relaxed`) sets this False: regression
    #: NOT_AVAILABLE then does not block ACCEPT when V4 PASSes. It is not
    #: selected by any experiment config.
    unavailable_regression_blocks_accept: bool = True

    def decide(self, evidence: Evidence) -> DecisionRecord:
        # v1.3.0 (§5.6): regression FAIL alone no longer rejects when V4's
        # issue-derived reproduction signal PASSes. The two oracle-blind
        # signals disagree about the same patch, and that disagreement is
        # escalated rather than resolved by assuming the regression result is
        # the correct one. Every other reject condition below still dominates.
        regression_disagreement = (
            evidence.regression.is_fail and evidence.reproduction.is_pass
        )

        reject: list[str] = []

        if not evidence.patch_applies:
            reject.append("patch fails to apply")
        if evidence.integrity.is_fail:
            reject.append("integrity check failed")
        if evidence.regression.is_fail and not regression_disagreement:
            reject.append("regression test failed")
        if evidence.prohibited_manipulation:
            reject.append("prohibited benchmark or test manipulation detected")

        if reject:
            return self._record(Decision.REJECT, tuple(reject), evidence)

        # ACCEPT requires every condition affirmatively met. A signal that is
        # NOT_AVAILABLE has not met its condition, and is not treated as if it had.
        unmet: list[str] = []
        if not evidence.integrity.is_pass:
            unmet.append(f"integrity is {evidence.integrity.value}, not PASS")
        if regression_disagreement:
            # evidence.reproduction.is_pass is true here by construction, so
            # the reproduction check below adds nothing redundant.
            unmet.append("signals disagree: regression FAIL, reproduction PASS")
        elif not evidence.regression.is_pass:
            # Secondary policy only: an unavailable regression is not a failed
            # one, and a V4 PASS is enough for this condition. Primary v1.3.0
            # leaves the flag True, so NOT_AVAILABLE still blocks ACCEPT.
            relaxed_gap = (
                not self.unavailable_regression_blocks_accept
                and evidence.regression is SignalOutcome.NOT_AVAILABLE
                and evidence.reproduction.is_pass
            )
            if not relaxed_gap:
                unmet.append(f"regression is {evidence.regression.value}, not PASS")
        if self.require_reproduction and not evidence.reproduction.is_pass:
            unmet.append(
                f"no issue-specific execution signal supports repair "
                f"(reproduction is {evidence.reproduction.value})"
            )
        if evidence.high_severity_risk:
            unmet.append("high-severity risk flag present")

        if not unmet:
            return self._record(
                Decision.ACCEPT, ("all accept conditions met",), evidence)

        return self._record(Decision.FLAG, tuple(unmet), evidence)

    def _record(self, decision, reasons, evidence) -> DecisionRecord:
        return DecisionRecord(
            decision=decision, policy_name=self.name,
            policy_version=self.version, reasons=reasons, evidence=evidence,
        )


@dataclass(frozen=True, slots=True)
class RelaxedPolicy(FullPolicy):
    """Secondary policy, pre-declared before either half is scored.

    Same rules as `FullPolicy` except a regression signal of NOT_AVAILABLE
    does not block ACCEPT when reproduction (V4) is PASS. A regression FAIL
    is unchanged. Not the policy the halves run under.
    """

    name: str = "relaxed"
    version: str = "v1.3.0-relaxed"
    unavailable_regression_blocks_accept: bool = False


@dataclass(frozen=True, slots=True)
class BaselinePolicy:
    """Integrity + regression only (Phase 7.2).

    The comparison that isolates what the static and issue-derived layers
    actually add. It is a *different policy*, not the full policy with layers
    switched off: it does not require an issue-specific signal, so it can reach
    ACCEPT on evidence where the full policy only reaches FLAG. That asymmetry
    is the measurement — a weaker verifier accepting more is exactly the
    false-acceptance difference the study is trying to quantify.

    It ignores `static` and `reproduction` entirely rather than reading them as
    NOT_AVAILABLE, so enabling those layers cannot accidentally change baseline
    decisions and destroy the comparison.
    """

    name: str = "baseline"
    version: str = "v1.2.2-baseline"

    def decide(self, evidence: Evidence) -> DecisionRecord:
        reject: list[str] = []

        if not evidence.patch_applies:
            reject.append("patch fails to apply")
        if evidence.integrity.is_fail:
            reject.append("integrity check failed")
        if evidence.regression.is_fail:
            reject.append("regression test failed")
        if evidence.prohibited_manipulation:
            reject.append("prohibited benchmark or test manipulation detected")

        if reject:
            return self._record(Decision.REJECT, tuple(reject), evidence)

        unmet: list[str] = []
        if not evidence.integrity.is_pass:
            unmet.append(f"integrity is {evidence.integrity.value}, not PASS")
        if not evidence.regression.is_pass:
            unmet.append(f"regression is {evidence.regression.value}, not PASS")

        if not unmet:
            return self._record(
                Decision.ACCEPT, ("integrity and regression both pass",), evidence)
        return self._record(Decision.FLAG, tuple(unmet), evidence)

    def _record(self, decision, reasons, evidence) -> DecisionRecord:
        return DecisionRecord(
            decision=decision, policy_name=self.name,
            policy_version=self.version, reasons=reasons, evidence=evidence,
        )


#: Registry so a run can name its policy in config rather than importing one.
POLICIES: dict[str, type] = {
    "full": FullPolicy,
    "baseline": BaselinePolicy,
    "relaxed": RelaxedPolicy,
}


def get_policy(name: str) -> DecisionPolicy:
    if name not in POLICIES:
        raise KeyError(f"unknown policy {name!r}; available: {sorted(POLICIES)}")
    return POLICIES[name]()
