"""v1.5 decision rules R1-R8 (PROTOCOL §4 "Decision rules", §5 switches)."""

import itertools
from dataclasses import replace

import pytest

from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.policy_v1_5 import (
    REVIEW_LABELS,
    RULE_DECISIONS,
    EvidenceV15,
    FullPolicyV15,
    evidence_from_signals,
)

P, F, NA = SignalOutcome.PASS, SignalOutcome.FAIL, SignalOutcome.NOT_AVAILABLE
OUTCOMES = (P, F, NA)
SWITCHES = tuple(
    dict(zip(("r2_v3_reject", "r3_extended_reject", "r6_accept_v2_not_available"), bits))
    for bits in itertools.product((False, True), repeat=3)
)


def consistent(v4, design, confirmed, failing, passing):
    """The V4 summary counts a real record can carry for a V4 outcome.

    V4 PASS is a full pass: nothing failing and at least one unit at PASS.
    V4 FAIL needs at least one failing unit. V4 NOT_AVAILABLE has no failing
    unit (UNCOVERED / NO_RESULT / absent); under the legacy design it has no
    passing test either, since one stable pass makes legacy V4 PASS.
    FAIL-confirmed requirements are failing requirements, and the legacy
    design (one pass) has none.
    """
    if confirmed > failing:
        return False
    if design == "legacy" and confirmed:
        return False
    if v4 is P:
        return failing == 0 and passing >= 1
    if v4 is F:
        return failing >= 1
    return failing == 0 and not (design == "legacy" and passing)


def truth_table():
    for (integrity, v2, v4, applies, prohibited, v3, v1_incomplete, risk, design,
         confirmed, failing, passing) in itertools.product(
            OUTCOMES, OUTCOMES, OUTCOMES, (True, False), (False, True), (False, True),
            (False, True), (False, True), ("per_requirement", "legacy"), (0, 1), (0, 1, 2),
            (0, 1)):
        if not consistent(v4, design, confirmed, failing, passing):
            continue
        yield EvidenceV15(
            integrity=integrity, regression=v2, reproduction=v4, patch_applies=applies,
            prohibited_manipulation=prohibited, v3_absolute_failure=v3,
            v1_analysis_incomplete=v1_incomplete, high_severity_risk=risk,
            v4_design=design, v4_full_pass=v4 is P, v4_fail_confirmed=confirmed,
            v4_failing_units=failing, v4_pass_units=passing,
        )


CASES = tuple(truth_table())


def ev(**kw):
    """Evidence that ACCEPTs under every policy unless a field says otherwise."""
    base = dict(integrity=P, regression=P, reproduction=P, v4_design="per_requirement",
                v4_full_pass=True, v4_pass_units=2)
    base.update(kw)
    return EvidenceV15(**base)


def v4_fail(**kw):
    return ev(**{"reproduction": F, "v4_full_pass": False, "v4_failing_units": 1,
                 "v4_pass_units": 1, **kw})


def test_truth_table_size_is_reported():
    # 3^2 integrity/V2 outcomes x 2^5 flags = 288, times 17 consistent
    # (V4 outcome, design, confirmed, failing, passing) combinations:
    # PASS 1+1, FAIL 8 per_requirement + 4 legacy, NOT_AVAILABLE 2 + 1.
    assert len(CASES) == 288 * 17 == 4896


@pytest.mark.parametrize("switches", SWITCHES, ids=lambda s: "".join(str(int(v)) for v in s.values()))
def test_every_case_returns_one_decision_and_a_rule(switches):
    policy = FullPolicyV15(**switches)
    for evidence in CASES:
        record = policy.decide(evidence)
        assert isinstance(record.decision, Decision)
        assert record.rule_id in RULE_DECISIONS
        assert record.decision is RULE_DECISIONS[record.rule_id]
        assert record.review_label in REVIEW_LABELS
        assert record.reasons and all(r.strip() for r in record.reasons)
        assert record.policy_name == "full-v1.5" and record.policy_version == "v1.5.0-full"
        assert record.as_dict()["rule_id"] == record.rule_id
        assert record.as_dict()["review_label"] == record.review_label


def test_switches_off_equals_v1_4_1_on_every_case():
    policy, old = FullPolicyV15(), FullPolicyV141()
    differing = [e for e in CASES if policy.decide(e).decision is not old.decide(e).decision]
    assert differing == []


@pytest.mark.parametrize("switches", SWITCHES, ids=lambda s: "".join(str(int(v)) for v in s.values()))
def test_switches_only_change_decisions_through_their_own_rules(switches):
    policy, old = FullPolicyV15(**switches), FullPolicyV141()
    allowed = {("R2", Decision.REJECT)} if switches["r2_v3_reject"] else set()
    if switches["r3_extended_reject"]:
        allowed.add(("R3", Decision.REJECT))
    if switches["r6_accept_v2_not_available"]:
        allowed.add(("R6", Decision.ACCEPT))
    for evidence in CASES:
        new, before = policy.decide(evidence), old.decide(evidence).decision
        if new.decision is not before:
            assert before is Decision.FLAG
            assert (new.rule_id, new.decision) in allowed
            if new.rule_id == "R3":
                assert any("extended" in r for r in new.reasons)
            if new.rule_id == "R6":
                assert evidence.regression is NA


def test_defaults_and_identity():
    policy = FullPolicyV15()
    assert (policy.name, policy.version) == ("full-v1.5", "v1.5.0-full")
    assert not (policy.r2_v3_reject or policy.r3_extended_reject
                or policy.r6_accept_v2_not_available)


# One explicit test per rule.

@pytest.mark.parametrize("field,value", [
    ("patch_applies", False), ("integrity", F), ("prohibited_manipulation", True)])
def test_r1_rejects(field, value):
    record = FullPolicyV15().decide(ev(**{field: value}))
    assert (record.decision, record.rule_id, record.review_label) == (Decision.REJECT, "R1", "none")


def test_r2_rejects_v3_failure_only_when_switched_on():
    evidence = ev(v3_absolute_failure=True)
    assert FullPolicyV15(r2_v3_reject=True).decide(evidence).rule_id == "R2"
    assert FullPolicyV15(r2_v3_reject=True).decide(evidence).decision is Decision.REJECT
    assert FullPolicyV15().decide(evidence).decision is Decision.FLAG


def test_r3_rejects_v4_fail_with_v2_fail_always():
    for switches in SWITCHES:
        record = FullPolicyV15(**switches).decide(v4_fail(regression=F))
        assert (record.decision, record.rule_id) == (Decision.REJECT, "R3")


@pytest.mark.parametrize("evidence", [
    v4_fail(v4_fail_confirmed=1),
    v4_fail(v4_failing_units=2),
    v4_fail(v3_absolute_failure=True),
], ids=["confirmed", "two-failing", "v3"])
def test_r3_extended_rejects_only_when_switched_on(evidence):
    on = FullPolicyV15(r3_extended_reject=True).decide(evidence)
    assert (on.decision, on.rule_id) == (Decision.REJECT, "R3")
    assert any("extended" in r for r in on.reasons)
    off = FullPolicyV15().decide(evidence)
    assert (off.decision, off.rule_id, off.review_label) == (Decision.FLAG, "R4", "likely_wrong")


def test_r3_extended_leaves_a_single_unconfirmed_failure_alone():
    record = FullPolicyV15(r3_extended_reject=True).decide(v4_fail())
    assert (record.decision, record.rule_id) == (Decision.FLAG, "R4")


@pytest.mark.parametrize("v4", [NA], ids=["v4-NA"])
def test_r3b_rejects_v2_fail_without_v4_verdict(v4):
    record = FullPolicyV15().decide(ev(regression=F, reproduction=v4, v4_full_pass=False,
                                       v4_pass_units=0))
    assert (record.decision, record.rule_id) == (Decision.REJECT, "R3b")


def test_r4_flags_v4_fail_as_likely_wrong():
    record = FullPolicyV15().decide(v4_fail())
    assert (record.decision, record.rule_id, record.review_label) == (
        Decision.FLAG, "R4", "likely_wrong")


def test_r5_flags_disagreement():
    record = FullPolicyV15().decide(ev(regression=F))
    assert (record.decision, record.rule_id, record.review_label) == (
        Decision.FLAG, "R5", "signals_disagree")


def test_r6_accepts():
    record = FullPolicyV15().decide(ev())
    assert (record.decision, record.rule_id, record.review_label) == (Decision.ACCEPT, "R6", "none")


def test_r6_accepts_v2_not_available_only_when_switched_on():
    evidence = ev(regression=NA)
    assert FullPolicyV15(r6_accept_v2_not_available=True).decide(evidence).rule_id == "R6"
    off = FullPolicyV15().decide(evidence)
    assert (off.decision, off.rule_id) == (Decision.FLAG, "R8")


@pytest.mark.parametrize("field,value", [
    ("integrity", NA), ("v1_analysis_incomplete", True), ("high_severity_risk", True)])
def test_r6_requires_every_accept_condition(field, value):
    for switches in SWITCHES:
        record = FullPolicyV15(**switches).decide(ev(**{field: value}))
        assert record.decision is Decision.FLAG and record.rule_id == "R8"


def test_r6_requires_v4_full_pass():
    evidence = ev(v4_full_pass=False)
    assert FullPolicyV15(r6_accept_v2_not_available=True).decide(evidence).decision is Decision.FLAG


@pytest.mark.parametrize("v2,passing,label", [
    (P, 0, "likely_right"), (NA, 1, "likely_right"), (NA, 0, "none"), (P, 1, "likely_right")])
def test_r7_labels(v2, passing, label):
    record = FullPolicyV15().decide(ev(regression=v2, reproduction=NA, v4_full_pass=False,
                                       v4_pass_units=passing))
    assert (record.decision, record.rule_id, record.review_label) == (Decision.FLAG, "R7", label)


def test_r8_flags_everything_else_with_reasons():
    record = FullPolicyV15().decide(ev(reproduction=NA, v4_full_pass=False, v4_pass_units=0,
                                       v3_absolute_failure=True))
    assert (record.decision, record.rule_id, record.review_label) == (Decision.FLAG, "R8", "none")
    assert "v3_absolute_failure" in record.reasons


# Precedence.

def test_r1_over_r2():
    record = FullPolicyV15(r2_v3_reject=True).decide(ev(integrity=F, v3_absolute_failure=True))
    assert record.rule_id == "R1"


def test_r3_over_r5_is_impossible_to_confuse():
    # V2 FAIL with V4 FAIL is R3, never R5, under every switch.
    for switches in SWITCHES:
        assert FullPolicyV15(**switches).decide(v4_fail(regression=F)).rule_id == "R3"


def test_r3_extended_over_r5_never_applies_to_v4_pass():
    # R5 (V2 FAIL, V4 PASS) is not pre-empted by the extended R3, which needs a V4 failure.
    for switches in SWITCHES:
        if switches["r2_v3_reject"]:
            continue
        assert FullPolicyV15(**switches).decide(ev(regression=F)).rule_id == "R5"


def test_r3b_fires_for_v2_fail_and_v4_not_available_under_every_switch():
    for switches in SWITCHES:
        record = FullPolicyV15(**switches).decide(
            ev(regression=F, reproduction=NA, v4_full_pass=False, v4_pass_units=0))
        assert record.rule_id == "R3b"


def test_r5_never_rejects_under_any_switch():
    for switches in SWITCHES:
        for record in (FullPolicyV15(**switches).decide(e) for e in CASES):
            if record.rule_id == "R5":
                assert record.decision is Decision.FLAG


def test_r6_never_fires_with_v4_fail_or_v2_fail():
    for switches in SWITCHES:
        policy = FullPolicyV15(**switches)
        for evidence in CASES:
            if evidence.reproduction is F or evidence.regression is F:
                assert policy.decide(evidence).decision is not Decision.ACCEPT


# Adapter.

def _signals(reproduction_outcome, findings, regression=P):
    from reliability.verifier.record import SignalKind, SignalRecord

    def sig(kind, outcome, f=None):
        return SignalRecord(kind=kind, outcome=outcome, detail="x", findings=f or {},
                            **({} if outcome is not NA else {"absence": "nothing_to_check"}))

    return {
        SignalKind.INTEGRITY: sig(SignalKind.INTEGRITY, P, {"ast_analysis": []}),
        SignalKind.REGRESSION: sig(SignalKind.REGRESSION, regression),
        SignalKind.STATIC: sig(SignalKind.STATIC, P, {"summary": {"syntax": "PASS"}}),
        SignalKind.REPRODUCTION: sig(SignalKind.REPRODUCTION, reproduction_outcome, findings),
    }


def _per_requirement(passes, counts, full_pass=False):
    verdicts = {f"R{i}": v for i, v in enumerate(
        [k for k, n in counts.items() for _ in range(n)], 1)}
    return {"setup": {"design": "per_requirement", "passes": passes},
            "requirement_verdicts": verdicts, "full_pass": full_pass,
            "verdict_counts": {k: counts.get(k, 0) for k in (
                "UNCOVERED", "NO_RESULT", "PASS", "FAIL_CONFIRMED", "FAIL_SINGLE")}}


def test_adapter_per_requirement_counts():
    evidence = evidence_from_signals(_signals(
        F, _per_requirement(2, {"PASS": 1, "FAIL_CONFIRMED": 1, "FAIL_SINGLE": 1})))
    assert (evidence.v4_design, evidence.v4_full_pass, evidence.v4_fail_confirmed,
            evidence.v4_failing_units, evidence.v4_pass_units) == (
        "per_requirement", False, 1, 2, 1)


def test_adapter_full_pass_needs_v4_pass():
    evidence = evidence_from_signals(_signals(P, _per_requirement(2, {"PASS": 3}, True)))
    assert evidence.v4_full_pass and evidence.v4_pass_units == 3


def test_one_pass_evidence_never_reaches_the_fail_confirmed_branch():
    # Even a record that claims FAIL_CONFIRMED is read as unconfirmed with one pass.
    evidence = evidence_from_signals(_signals(F, _per_requirement(1, {"FAIL_CONFIRMED": 1})))
    assert evidence.v4_fail_confirmed == 0 and evidence.v4_failing_units == 1
    record = FullPolicyV15(r3_extended_reject=True).decide(evidence)
    assert (record.decision, record.rule_id) == (Decision.FLAG, "R4")


def test_adapter_legacy_derives_units_from_kept_tests():
    findings = {"setup": {}, "patched": [
        {"verdict": "fail"}, {"verdict": "fail"}, {"verdict": "pass"}, {"verdict": "flaky"}]}
    evidence = evidence_from_signals(_signals(F, findings))
    assert (evidence.v4_design, evidence.v4_full_pass, evidence.v4_fail_confirmed,
            evidence.v4_failing_units, evidence.v4_pass_units) == ("legacy", False, 0, 2, 1)


def test_adapter_legacy_absent_v4_has_no_units():
    evidence = evidence_from_signals(_signals(NA, {"absence_reason": "EMPTY_PATCH"}))
    assert (evidence.v4_design, evidence.v4_full_pass, evidence.v4_failing_units,
            evidence.v4_pass_units) == ("legacy", False, 0, 0)


def test_adapter_keeps_v1_4_fields():
    evidence = evidence_from_signals(_signals(P, {"setup": {}, "patched": [{"verdict": "pass"}]},
                                              regression=F))
    assert evidence.regression is F and evidence.integrity is P
    assert evidence.v3_absolute_failure is False and evidence.v1_analysis_incomplete is False
    assert evidence.as_dict()["v4_design"] == "legacy"


# Registration.

def test_registered_for_config_selection(tmp_path):
    from reliability.verifier.decision import get_policy
    from reliability.verifier.policy_v1_5 import policy_from_config

    assert isinstance(get_policy("full-v1.5"), FullPolicyV15)
    config = tmp_path / "v.yaml"
    config.write_text("v1_5:\n  decision_policy: full-v1.5\n  r2_v3_reject: false\n"
                      "  r3_extended_reject: true\n  r6_accept_v2_not_available: false\n")
    assert policy_from_config(config) == FullPolicyV15(r3_extended_reject=True)
    config.write_text("v1_5:\n  decision_policy: full-v1.5\n  r2_v3_reject: 1\n")
    with pytest.raises(ValueError):
        policy_from_config(config)


def test_study_config_selects_v1_5_with_switches_off():
    from reliability.verifier.policy_v1_5 import policy_from_config
    from reliability.verifier.task_specs import ROOT

    assert policy_from_config(ROOT / "configs/verifier/v1_5.yaml") == FullPolicyV15()


def test_replace_keeps_v1_5_fields():
    evidence = replace(ev(v4_failing_units=0), regression=NA)
    assert isinstance(evidence, EvidenceV15) and evidence.v4_design == "per_requirement"
