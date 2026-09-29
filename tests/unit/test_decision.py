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


@pytest.mark.parametrize("policy", [FullPolicy(), BaselinePolicy()], ids=["full", "baseline"])
def test_reject_dominates_every_other_signal(policy):
    """A rejecting condition rejects no matter how good everything else looks."""
    for evidence in every_evidence():
        rejecting = (
            not evidence.patch_applies
            or evidence.integrity.is_fail
            or evidence.regression.is_fail
            or evidence.prohibited_manipulation
        )
        if rejecting:
            assert policy.decide(evidence).decision is Decision.REJECT, evidence


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
    """The consequence of implementing §12 literally, pinned so it is not lost.

    With no issue-specific execution signal, the third ACCEPT condition is never
    met and every otherwise-acceptable patch falls through to FLAG. When V4
    lands this test should be updated, not deleted.
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


def test_baseline_never_rejects_where_full_accepts():
    """The two policies must agree on rejection; they differ only above it."""
    for evidence in every_evidence():
        if FullPolicy().decide(evidence).decision is not Decision.REJECT:
            assert BaselinePolicy().decide(evidence).decision is not Decision.REJECT


def test_baseline_is_never_stricter_than_full():
    for evidence in every_evidence():
        assert RANK[BaselinePolicy().decide(evidence).decision] >= \
            RANK[FullPolicy().decide(evidence).decision], evidence


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
    assert set(POLICIES) == {"full", "baseline"}
    assert isinstance(get_policy("full"), FullPolicy)
    assert isinstance(get_policy("baseline"), BaselinePolicy)


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


def test_full_config_records_that_reproduction_is_unimplemented():
    decision = load_config("full")["decision"]
    assert decision["require_reproduction"] is FullPolicy().require_reproduction
    assert decision["reproduction_implemented"] is False


def test_baseline_config_declares_what_it_ignores():
    assert set(load_config("baseline")["decision"]["ignores"]) == {
        "static", "reproduction", "high_severity_risk"}


def test_configured_risk_features_match_the_adapter():
    from reliability.verifier.evidence import HIGH_SEVERITY_RISK

    configured = load_config("full")["decision"]["high_severity_risk_features"]
    assert set(configured) == set(HIGH_SEVERITY_RISK)
