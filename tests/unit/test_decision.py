"""Phase 7 gate: the decision policy.

The named gate is a truth table over every combination of integrity,
regression, static and risk, asserting that no input produces an undefined
decision. That exhaustive sweep is `test_truth_table_is_total`; the tests around
it pin the specific rulings the design names, so a future policy change that
still happens to be total cannot pass unnoticed.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

import pytest

from reliability.verifier.decision import (
    POLICIES,
    BaselinePolicy,
    Decision,
    DecisionRecord,
    Evidence,
    FullPolicy,
    SignalOutcome,
    get_policy,
)

PASS = SignalOutcome.PASS
FAIL = SignalOutcome.FAIL
NA = SignalOutcome.NOT_AVAILABLE

ALL_OUTCOMES = tuple(SignalOutcome)
BOOLS = (False, True)

#: Decisions ordered by how favourable they are to the patch. Used to assert
#: that weakening a signal never improves a decision.
RANK = {Decision.REJECT: 0, Decision.FLAG: 1, Decision.ACCEPT: 2}


def every_evidence():
    """The full cartesian product of every field a policy can read."""
    for integrity, regression, static, reproduction in itertools.product(
        ALL_OUTCOMES, repeat=4
    ):
        for risk, manipulation, applies in itertools.product(BOOLS, repeat=3):
            yield Evidence(
                integrity=integrity, regression=regression, static=static,
                reproduction=reproduction, high_severity_risk=risk,
                prohibited_manipulation=manipulation, patch_applies=applies,
            )


# --- the named gate --------------------------------------------------------


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
def test_truth_table_is_total(policy):
    """No combination of signals may produce an undefined decision."""
    seen = 0
    for evidence in every_evidence():
        record = policy.decide(evidence)
        assert isinstance(record, DecisionRecord)
        assert isinstance(record.decision, Decision), evidence
        assert record.decision in set(Decision), evidence
        seen += 1

    assert seen == len(ALL_OUTCOMES) ** 4 * 2 ** 3 == 648


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
def test_every_decision_is_deterministic(policy):
    for evidence in every_evidence():
        assert policy.decide(evidence).decision is policy.decide(evidence).decision


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
def test_every_decision_carries_a_reason_and_a_version(policy):
    """A decision with no recorded reason is not auditable."""
    for evidence in every_evidence():
        record = policy.decide(evidence)
        assert record.reasons, evidence
        assert all(r.strip() for r in record.reasons)
        assert record.policy_version
        assert record.policy_name


# --- policy_version --------------------------------------------------------


def test_policy_version_is_recorded_in_the_record_dict():
    record = FullPolicy().decide(Evidence())
    assert record.as_dict()["policy_version"] == FullPolicy().version


def test_policies_have_distinct_versions():
    assert FullPolicy().version != BaselinePolicy().version


def test_record_serialises_its_evidence():
    payload = FullPolicy().decide(Evidence(integrity=PASS)).as_dict()
    assert payload["evidence"]["integrity"] == "PASS"
    assert payload["evidence"]["reproduction"] == "NOT_AVAILABLE"


# --- REJECT conditions from the design -------------------------------------


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
@pytest.mark.parametrize("evidence,reason", [
    (Evidence(patch_applies=False), "apply"),
    (Evidence(integrity=FAIL), "integrity"),
    (Evidence(regression=FAIL), "regression"),
    (Evidence(prohibited_manipulation=True), "manipulation"),
])
def test_reject_conditions(policy, evidence, reason):
    record = policy.decide(evidence)
    assert record.decision is Decision.REJECT
    assert any(reason in r for r in record.reasons)


def test_reject_dominates_every_other_signal_baseline():
    """Baseline has no V4 signal, so every reject condition still dominates."""
    for evidence in every_evidence():
        rejecting = (
            not evidence.patch_applies
            or evidence.integrity.is_fail
            or evidence.regression.is_fail
            or evidence.prohibited_manipulation
        )
        if rejecting:
            assert BaselinePolicy().decide(evidence).decision is Decision.REJECT, evidence


def test_reject_dominates_every_other_signal_full_except_v4_disagreement():
    """Full: every reject condition dominates, *except* a regression FAIL that
    V4's reproduction signal disagrees with (v1.3.0, §5.6) — that one case
    FLAGs instead. Every other combination that would have rejected still does.
    """
    for evidence in every_evidence():
        other_rejecting = (
            not evidence.patch_applies
            or evidence.integrity.is_fail
            or evidence.prohibited_manipulation
        )
        regression_disagreement = (
            evidence.regression.is_fail and evidence.reproduction.is_pass
        )
        decision = FullPolicy().decide(evidence).decision
        if other_rejecting:
            assert decision is Decision.REJECT, evidence
        elif evidence.regression.is_fail and not regression_disagreement:
            assert decision is Decision.REJECT, evidence
        elif regression_disagreement:
            assert decision is not Decision.REJECT, evidence


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
def test_reject_reasons_list_every_failing_condition(policy):
    record = policy.decide(Evidence(
        patch_applies=False, integrity=FAIL, regression=FAIL,
        prohibited_manipulation=True))
    assert len(record.reasons) == 4


# --- ACCEPT conditions -----------------------------------------------------


def test_full_policy_accepts_only_with_a_reproduction_signal():
    accepting = Evidence(integrity=PASS, regression=PASS, static=PASS, reproduction=PASS)
    assert FullPolicy().decide(accepting).decision is Decision.ACCEPT


def test_full_policy_cannot_accept_while_v4_is_absent():
    """V4 is built, and an absent reproduction signal still cannot ACCEPT.

    Once the build-order state; now the case where V4 ran but kept no test
    (nothing failed deterministically on the base commit), could not place the
    frozen bytes, or broke. The third ACCEPT condition is unmet either way and
    every otherwise-acceptable patch falls through to FLAG.
    """
    decisions = {
        FullPolicy().decide(e).decision
        for e in every_evidence() if e.reproduction is NA
    }
    assert Decision.ACCEPT not in decisions


def test_absent_reproduction_flags_rather_than_raising():
    record = FullPolicy().decide(Evidence(integrity=PASS, regression=PASS, static=PASS))
    assert record.decision is Decision.FLAG
    assert any("issue-specific" in r for r in record.reasons)


def test_high_severity_risk_downgrades_accept_to_flag():
    base = Evidence(integrity=PASS, regression=PASS, static=PASS, reproduction=PASS)
    assert FullPolicy().decide(base).decision is Decision.ACCEPT

    flagged = FullPolicy().decide(Evidence(
        integrity=PASS, regression=PASS, static=PASS, reproduction=PASS,
        high_severity_risk=True))
    assert flagged.decision is Decision.FLAG
    assert any("risk" in r for r in flagged.reasons)


def test_risk_never_rejects():
    """Phase 4.2: risk features are recorded, never a rejection reason."""
    for evidence in every_evidence():
        with_risk = replace(evidence, high_severity_risk=True)
        without = replace(evidence, high_severity_risk=False)
        if FullPolicy().decide(without).decision is not Decision.REJECT:
            assert FullPolicy().decide(with_risk).decision is not Decision.REJECT


# --- NOT_AVAILABLE is never a pass -----------------------------------------


ALL_PASS = Evidence(integrity=PASS, regression=PASS, static=PASS, reproduction=PASS)


@pytest.mark.parametrize("field", ["integrity", "regression"])
def test_unavailable_signal_never_accepts(field):
    assert FullPolicy().decide(replace(ALL_PASS, **{field: NA})).decision is Decision.FLAG


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
@pytest.mark.parametrize("field", ["integrity", "regression", "static", "reproduction"])
def test_unavailable_is_never_treated_as_pass(policy, field):
    """Swapping a PASS for NOT_AVAILABLE must never improve the decision."""
    for evidence in every_evidence():
        if getattr(evidence, field) is not PASS:
            continue
        downgraded = replace(evidence, **{field: NA})
        assert RANK[policy.decide(downgraded).decision] <= \
            RANK[policy.decide(evidence).decision], evidence


def test_empty_evidence_flags():
    """Nothing measured is not the same as nothing wrong."""
    for policy in (FullPolicy(), BaselinePolicy()):
        assert policy.decide(Evidence()).decision is Decision.FLAG


# --- baseline vs full ------------------------------------------------------


def test_baseline_accepts_where_full_only_flags():
    """The measurement: a weaker verifier accepts more."""
    evidence = Evidence(integrity=PASS, regression=PASS)
    assert BaselinePolicy().decide(evidence).decision is Decision.ACCEPT
    assert FullPolicy().decide(evidence).decision is Decision.FLAG


def test_baseline_ignores_static_and_reproduction():
    """Enabling later layers must not perturb the baseline comparison."""
    for static, reproduction in itertools.product(ALL_OUTCOMES, repeat=2):
        record = BaselinePolicy().decide(Evidence(
            integrity=PASS, regression=PASS, static=static, reproduction=reproduction))
        assert record.decision is Decision.ACCEPT


def test_baseline_ignores_risk():
    record = BaselinePolicy().decide(
        Evidence(integrity=PASS, regression=PASS, high_severity_risk=True))
    assert record.decision is Decision.ACCEPT


#: v1.3.0, §5.6: the one evidence combination where this invariant is now
#: expected to break, named so a failure elsewhere stays a real failure.
V4_DISAGREEMENT = Evidence(regression=FAIL, reproduction=PASS)


def _is_v4_disagreement(evidence: Evidence) -> bool:
    return evidence.regression.is_fail and evidence.reproduction.is_pass


def _other_reject_condition(evidence: Evidence) -> bool:
    """A reject reason neither policy's v1.3.0 exception touches."""
    return (
        not evidence.patch_applies
        or evidence.integrity.is_fail
        or evidence.prohibited_manipulation
    )


def test_baseline_never_rejects_where_full_accepts():
    """The two policies must agree on rejection *outside* the one named
    v1.3.0 exception (§5.6): full never ACCEPTs on a regression FAIL, but it
    does FLAG a V4 disagreement that baseline — which cannot see V4 — still
    REJECTs. That specific divergence is covered and pinned separately by
    `test_baseline_is_never_stricter_than_full_except_the_named_v4_disagreement`.
    """
    for evidence in every_evidence():
        if _is_v4_disagreement(evidence) and not _other_reject_condition(evidence):
            continue
        if FullPolicy().decide(evidence).decision is not Decision.REJECT:
            assert BaselinePolicy().decide(evidence).decision is not Decision.REJECT


def test_baseline_is_never_stricter_than_full_except_the_named_v4_disagreement():
    """v1.3.0, §5.6: baseline can reject what full only flags, in exactly one
    case — regression FAIL disagreeing with a V4 PASS, and nothing else wrong.
    Baseline has no V4 signal to disagree with regression, so it stays strict;
    full does, and is deliberately more lenient. Recorded as the measurement
    working as intended, not as a broken invariant. Any *other* reject
    condition present at the same time still dominates both policies equally,
    so the ordering holds there too. Every remaining combination holds the
    original ordering unchanged.
    """
    for evidence in every_evidence():
        baseline_rank = RANK[BaselinePolicy().decide(evidence).decision]
        full_rank = RANK[FullPolicy().decide(evidence).decision]
        if _is_v4_disagreement(evidence) and not _other_reject_condition(evidence):
            assert baseline_rank < full_rank, evidence
        else:
            assert baseline_rank >= full_rank, evidence


def test_baseline_rejects_the_v4_disagreement_full_only_flags():
    """Pin the one exception concretely, not just inside the sweep above."""
    assert BaselinePolicy().decide(V4_DISAGREEMENT).decision is Decision.REJECT
    assert FullPolicy().decide(V4_DISAGREEMENT).decision is Decision.FLAG


# --- module boundary -------------------------------------------------------


def test_decision_module_imports_no_signal_implementation():
    """A second policy must be addable without touching signal code.

    Enforced structurally rather than by convention: if this import ever
    appears, the separation has already been lost.
    """
    import reliability.verifier.decision as module

    source = (module.__file__ or "")
    assert source
    text = open(source, encoding="utf-8").read()  # noqa: SIM115
    for signal_module in ("integrity", "regression", "static_checks", "selection", "patch"):
        assert f"import {signal_module}" not in text
        assert f"verifier.{signal_module}" not in text


def test_registry_exposes_both_policies():
    from reliability.verifier.decision import RelaxedPolicy

    assert set(POLICIES) == {"full", "baseline", "relaxed"}
    assert isinstance(get_policy("full"), FullPolicy)
    assert isinstance(get_policy("baseline"), BaselinePolicy)
    relaxed = get_policy("relaxed")
    assert isinstance(relaxed, RelaxedPolicy)
    assert relaxed.version == "v1.3.0-relaxed"
    assert get_policy("full").version == "v1.3.0-full"


def test_unknown_policy_raises():
    with pytest.raises(KeyError):
        get_policy("nope")


# --- config and code must not drift ----------------------------------------


def load_config(name: str) -> dict:
    import pathlib

    import yaml

    return yaml.safe_load(pathlib.Path(f"configs/verifier/{name}.yaml").read_text())


@pytest.mark.parametrize("name,policy", [("full", FullPolicy()), ("baseline", BaselinePolicy())])
def test_shipped_config_version_matches_the_policy(name, policy):
    """A config claiming one version while code implements another would make
    every recorded decision unattributable."""
    cfg = load_config(name)
    assert cfg["policy_version"] == policy.version
    assert cfg["decision"]["policy"] == policy.name


def test_full_config_records_that_reproduction_is_implemented():
    decision = load_config("full")["decision"]
    assert decision["require_reproduction"] is FullPolicy().require_reproduction
    assert decision["reproduction_implemented"] is True


def test_reproduction_fail_flags_rather_than_rejects():
    """A generated test is weaker evidence than the repository's own tests."""
    record = FullPolicy().decide(
        Evidence(integrity=PASS, regression=PASS, static=PASS, reproduction=FAIL))
    assert record.decision is Decision.FLAG


# --- v1.3.0, §5.6: regression/reproduction disagreement ---------------------
#
# Validated against the two real cases: django__django-16899 (pilot_14 and
# pilot_15, regression FAIL on the admin.E035 wording, reproduction PASS,
# oracle resolved) and sphinx-doc__sphinx-10449 under the Tier 0 ablation
# (regression FAIL on its own FAIL_TO_PASS test once Tier 0 selects it,
# reproduction PASS, oracle resolved). Both REJECTed under v1.2.2; both FLAG
# under this rule. See the decisions log, 2026-10-05.


def test_regression_fail_with_reproduction_pass_flags_not_rejects():
    """The exact case this policy version exists for."""
    record = FullPolicy().decide(
        Evidence(integrity=PASS, regression=FAIL, static=PASS, reproduction=PASS))
    assert record.decision is Decision.FLAG


def test_disagreement_reason_is_recorded_verbatim():
    record = FullPolicy().decide(
        Evidence(integrity=PASS, regression=FAIL, static=PASS, reproduction=PASS))
    assert "signals disagree: regression FAIL, reproduction PASS" in record.reasons


@pytest.mark.parametrize("reproduction", [FAIL, NA])
def test_regression_fail_still_rejects_when_v4_does_not_pass(reproduction):
    """No second signal to disagree with regression means the old rule holds."""
    record = FullPolicy().decide(
        Evidence(integrity=PASS, regression=FAIL, static=PASS,
                 reproduction=reproduction))
    assert record.decision is Decision.REJECT
    assert any("regression" in r for r in record.reasons)


def test_disagreement_never_reaches_accept():
    """FLAG escalates the disagreement; it is not a second vote for ACCEPT."""
    for static, risk in itertools.product(ALL_OUTCOMES, BOOLS):
        record = FullPolicy().decide(Evidence(
            integrity=PASS, regression=FAIL, static=static, reproduction=PASS,
            high_severity_risk=risk))
        assert record.decision is Decision.FLAG


@pytest.mark.parametrize("other_reject", [
    Evidence(patch_applies=False, regression=FAIL, reproduction=PASS),
    Evidence(integrity=FAIL, regression=FAIL, reproduction=PASS),
    Evidence(prohibited_manipulation=True, regression=FAIL, reproduction=PASS),
])
def test_other_reject_conditions_still_dominate_a_v4_disagreement(other_reject):
    """The exception is narrow: it only ever softens regression-FAIL-alone."""
    record = FullPolicy().decide(other_reject)
    assert record.decision is Decision.REJECT


def test_baseline_is_unaffected_by_the_disagreement_rule():
    """Baseline ignores reproduction entirely; it has no signal to disagree
    with regression, so it must still reject on regression FAIL alone."""
    for reproduction in ALL_OUTCOMES:
        record = BaselinePolicy().decide(
            Evidence(integrity=PASS, regression=FAIL, reproduction=reproduction))
        assert record.decision is Decision.REJECT


def test_disagreement_rule_does_not_change_decisions_where_v4_is_absent_or_fails():
    """Exhaustive check over every combination: swapping reproduction between
    FAIL and NOT_AVAILABLE while holding everything else fixed must never
    change the decision when regression is FAIL. The rule only has an effect
    through the PASS case."""
    for evidence in every_evidence():
        if not evidence.regression.is_fail:
            continue
        as_fail = replace(evidence, reproduction=FAIL)
        as_na = replace(evidence, reproduction=NA)
        assert FullPolicy().decide(as_fail).decision == \
            FullPolicy().decide(as_na).decision, evidence


def test_baseline_config_declares_what_it_ignores():
    assert set(load_config("baseline")["decision"]["ignores"]) == {
        "static", "reproduction", "high_severity_risk"}


def test_configured_risk_features_match_the_adapter():
    from reliability.verifier.evidence import HIGH_SEVERITY_RISK

    configured = load_config("full")["decision"]["high_severity_risk_features"]
    assert set(configured) == set(HIGH_SEVERITY_RISK)
