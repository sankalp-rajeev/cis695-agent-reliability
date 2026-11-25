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
NOTHING = "nothing_to_check"
INCOMPLETE = "incomplete"
#: V2 outcome, its absence, and whether a patched-side test timed out or
#: crashed. An absent V2 had nothing to check, was incomplete (with or without
#: a patched-side timeout or crash), or could not run (any other absence,
#: represented by "error").
V2_CASES = ((P, None, False), (F, None, False), (NA, NOTHING, False), (NA, INCOMPLETE, False),
            (NA, INCOMPLETE, True), (NA, "error", False))


def r6_branch_allowed(evidence):
    """Amendment A4 (iii) revised: nothing to check, or incomplete with no patched timeout/crash."""
    return evidence.regression is NA and (
        evidence.v2_absence == NOTHING
        or (evidence.v2_absence == INCOMPLETE and not evidence.v2_patched_timeout_or_crash))
SWITCHES = tuple(
    dict(zip(("r2_v3_reject", "r3_extended_reject", "r6_accept_v2_not_available"), bits))
    for bits in itertools.product((False, True), repeat=3)
)


def consistent(v4, design, confirmed, failing, passing):
    """The V4 summary counts a real record can carry for a V4 outcome.

    V4 PASS is a full pass: nothing failing and at least one unit at PASS.
    V4 FAIL needs at least one failing unit. V4 NOT_AVAILABLE can carry any
    counts: frozen bytes that could not be placed (FROZEN_BYTES_NOT_IN_PLACE)
    make V4 NOT_AVAILABLE whatever the other tests did, so failing and passing
    units with V4 NOT_AVAILABLE are real cases. FAIL-confirmed requirements
    are failing requirements, and the legacy design (one pass) has none.
    """
    if confirmed > failing:
        return False
    if design == "legacy" and confirmed:
        return False
    if v4 is P:
        return failing == 0 and passing >= 1
    if v4 is F:
        return failing >= 1
    return True


def truth_table():
    for (integrity, (v2, v2_absence, v2_crash), v4, applies, prohibited, v3, v1_incomplete, risk, design,
         confirmed, failing, passing) in itertools.product(
            OUTCOMES, V2_CASES, OUTCOMES, (True, False), (False, True), (False, True),
            (False, True), (False, True), ("per_requirement", "legacy"), (0, 1), (0, 1, 2),
            (0, 1)):
        if not consistent(v4, design, confirmed, failing, passing):
            continue
        yield EvidenceV15(
            integrity=integrity, regression=v2, v2_absence=v2_absence,
            v2_patched_timeout_or_crash=v2_crash, reproduction=v4,
            patch_applies=applies,
            prohibited_manipulation=prohibited, v3_absolute_failure=v3,
            v1_analysis_incomplete=v1_incomplete, high_severity_risk=risk,
            v4_design=design, v4_full_pass=v4 is P, v4_fail_confirmed=confirmed,
            v4_failing_units=failing, v4_pass_units=passing,
        )


CASES = tuple(truth_table())


def in_a4_ii_class(evidence):
    """Amendment A4 (ii): V2 FAIL, per-requirement V4 NOT_AVAILABLE, a PASS and nothing failing."""
    return (evidence.regression is F and evidence.reproduction is NA
            and evidence.v4_design == "per_requirement"
            and evidence.v4_pass_units >= 1 and evidence.v4_failing_units == 0)


def r1_applies(evidence):
    return (not evidence.patch_applies or evidence.integrity is F
            or evidence.prohibited_manipulation)


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
    # 3 integrity outcomes x 6 V2 cases (PASS, FAIL, NOT_AVAILABLE with nothing
    # to check, incomplete without and with a patched timeout/crash, another
    # absence) x 2^5 flags = 576, times 30 consistent (V4 outcome, design,
    # confirmed, failing, passing) combinations:
    # PASS 1+1, FAIL 8 per_requirement + 4 legacy, NOT_AVAILABLE 10 + 6.
    assert len(CASES) == 576 * 30 == 17280


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


def test_switches_off_equals_v1_4_1_except_the_a4_ii_class():
    # Amendment A4 (ii) is a default rule: with switches off, v1.5 differs from
    # v1.4.1 exactly on the A4 (ii) cases that R1 does not REJECT first, where
    # v1.4.1's R3b REJECT becomes R5 FLAG "signals disagree". 3 integrity x 2^5
    # flags = 96 cases are in the class; integrity PASS or NOT_AVAILABLE with
    # the patch applying and no manipulation leaves 2 x 2^3 = 16 that change.
    policy, old = FullPolicyV15(), FullPolicyV141()
    differing = [e for e in CASES if policy.decide(e).decision is not old.decide(e).decision]
    assert all(in_a4_ii_class(e) for e in differing)
    assert len([e for e in CASES if in_a4_ii_class(e)]) == 96
    assert len(differing) == 16
    for evidence in differing:
        assert old.decide(evidence).decision is Decision.REJECT
        record = policy.decide(evidence)
        assert (record.decision, record.rule_id, record.review_label) == (
            Decision.FLAG, "R5", "signals_disagree")
    unchanged = [e for e in CASES if in_a4_ii_class(e) and e not in differing]
    assert all(r1_applies(e) for e in unchanged)


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
            if in_a4_ii_class(evidence) and (new.rule_id, new.decision) == ("R5", Decision.FLAG):
                assert before is Decision.REJECT
                continue
            assert before is Decision.FLAG
            assert (new.rule_id, new.decision) in allowed
            if new.rule_id == "R3":
                assert any("extended" in r for r in new.reasons)
            if new.rule_id == "R6":
                assert r6_branch_allowed(evidence)


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


@pytest.mark.parametrize("confirmed,failing", [(0, 2), (1, 1), (1, 2)])
def test_r3_extended_needs_v4_fail(confirmed, failing):
    # Failing units with V4 NOT_AVAILABLE (e.g. FROZEN_BYTES_NOT_IN_PLACE) are
    # missing V4 evidence, not a V4 failure: FLAG, never REJECT.
    policy = FullPolicyV15(r2_v3_reject=True, r3_extended_reject=True,
                           r6_accept_v2_not_available=True)
    record = policy.decide(ev(reproduction=NA, v4_full_pass=False, v4_fail_confirmed=confirmed,
                              v4_failing_units=failing, v4_pass_units=0))
    assert record.decision is Decision.FLAG and record.rule_id != "R3"


def test_v4_not_available_with_two_failing_units_flags_under_all_switches():
    policy = FullPolicyV15(r2_v3_reject=True, r3_extended_reject=True,
                           r6_accept_v2_not_available=True)
    record = policy.decide(ev(reproduction=NA, v4_full_pass=False, v4_failing_units=2,
                              v4_pass_units=0))
    assert record.decision is Decision.FLAG


def test_r3_extended_never_rejects_without_v4_fail():
    for switches in SWITCHES:
        policy = FullPolicyV15(**switches)
        for evidence in CASES:
            record = policy.decide(evidence)
            if record.rule_id == "R3":
                assert evidence.reproduction is F


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
    evidence = ev(regression=NA, v2_absence=NOTHING)
    assert FullPolicyV15(r6_accept_v2_not_available=True).decide(evidence).rule_id == "R6"
    off = FullPolicyV15().decide(evidence)
    assert (off.decision, off.rule_id) == (Decision.FLAG, "R8")


@pytest.mark.parametrize("absence", [
    "error", "timeout", "disabled", "not_configured", "not_implemented", None])
def test_r6_switch_never_accepts_a_v2_that_could_not_run(absence):
    # Amendment A4 (iii) revised: error (which includes an unreliable
    # baseline), timeout and every other absence stay FLAG.
    record = FullPolicyV15(r6_accept_v2_not_available=True).decide(
        ev(regression=NA, v2_absence=absence))
    assert (record.decision, record.rule_id) == (Decision.FLAG, "R8")


def test_r6_switch_accepts_incomplete_v2_without_patched_timeout_or_crash():
    record = FullPolicyV15(r6_accept_v2_not_available=True).decide(
        ev(regression=NA, v2_absence=INCOMPLETE, v2_patched_timeout_or_crash=False))
    assert (record.decision, record.rule_id) == (Decision.ACCEPT, "R6")
    assert any("incomplete" in reason for reason in record.reasons)
    off = FullPolicyV15().decide(ev(regression=NA, v2_absence=INCOMPLETE))
    assert (off.decision, off.rule_id) == (Decision.FLAG, "R8")


def test_r6_switch_rejects_incomplete_v2_with_patched_timeout_or_crash():
    record = FullPolicyV15(r6_accept_v2_not_available=True).decide(
        ev(regression=NA, v2_absence=INCOMPLETE, v2_patched_timeout_or_crash=True))
    assert (record.decision, record.rule_id) == (Decision.FLAG, "R8")


def test_a4_ii_flags_v2_fail_with_partial_v4_pass_as_disagreement():
    evidence = ev(regression=F, reproduction=NA, v4_full_pass=False, v4_pass_units=1,
                  v4_failing_units=0)
    for switches in SWITCHES:
        record = FullPolicyV15(**switches).decide(evidence)
        assert (record.decision, record.rule_id, record.review_label) == (
            Decision.FLAG, "R5", "signals_disagree")
    assert FullPolicyV141().decide(evidence).decision is Decision.REJECT


@pytest.mark.parametrize("kw", [
    dict(v4_pass_units=0, v4_failing_units=0),
    dict(v4_pass_units=1, v4_failing_units=1),
    dict(v4_pass_units=1, v4_failing_units=0, v4_design="legacy"),
], ids=["no-pass", "one-failing", "legacy"])
def test_a4_ii_needs_a_pass_no_failure_and_per_requirement_v4(kw):
    evidence = ev(regression=F, reproduction=NA, v4_full_pass=False, **kw)
    record = FullPolicyV15().decide(evidence)
    assert (record.decision, record.rule_id) == (Decision.REJECT, "R3b")


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


def test_adapter_records_v2_absence():
    from reliability.verifier.record import SignalKind, SignalRecord

    signals = _signals(P, {"setup": {}, "patched": [{"verdict": "pass"}]}, regression=NA)
    assert evidence_from_signals(signals).v2_absence == NOTHING
    signals[SignalKind.REGRESSION] = SignalRecord(
        kind=SignalKind.REGRESSION, outcome=NA, absence="error", detail="x")
    assert evidence_from_signals(signals).v2_absence == "error"
    assert evidence_from_signals(_signals(P, {"setup": {}, "patched": []})).v2_absence is None
    assert evidence_from_signals(signals).as_dict()["v2_absence"] == "error"


def _incomplete_v2(patched=None, confirmations=()):
    from reliability.verifier.record import SignalKind, SignalRecord

    findings = {"confirmations": list(confirmations)}
    if patched is not None:
        findings["patched"] = patched
    signals = _signals(P, {"setup": {}, "patched": [{"verdict": "pass"}]}, regression=NA)
    signals[SignalKind.REGRESSION] = SignalRecord(
        kind=SignalKind.REGRESSION, outcome=NA, absence=INCOMPLETE, detail="x", findings=findings)
    return evidence_from_signals(signals)


def _run(*statuses, timed_out=False, tree=None, key="results"):
    run = {"results": [], "raw_results": [], "execution_results": [], "timed_out": timed_out}
    run[key] = [{"test_id": f"t{i}", "status": s} for i, s in enumerate(statuses)]
    if tree:
        run["confirmation"] = {"tree": tree}
    return run


@pytest.mark.parametrize("patched,confirmations,expected", [
    (_run("passed", "skipped"), (), False),
    (_run("passed", "timeout"), (), True),
    (_run("passed", "crash", key="raw_results"), (), True),
    (_run("passed", "timeout", key="execution_results"), (), True),
    (_run("passed", timed_out=True), (), True),
    (_run("passed", "error", "collection_error"), (), False),
    (_run("passed"), (_run("crash", tree="patched"),), True),
    (_run("passed"), (_run("crash", tree="base"),), False),
    (None, (), True),
], ids=["clean", "timeout", "raw-crash", "execution-timeout", "pass-timed-out", "error-only",
        "patched-confirmation-crash", "base-confirmation-crash", "no-patched-run"])
def test_adapter_records_patched_timeout_or_crash(patched, confirmations, expected):
    assert _incomplete_v2(patched, confirmations).v2_patched_timeout_or_crash is expected


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


def test_study_config_selects_v1_5_with_the_adopted_switches():
    """Phase 8 (tag v1.5-frozen) set the switches ADOPTION.md adopted: r2, r6, r6b."""
    from reliability.verifier.policy_v1_5 import policy_from_config
    from reliability.verifier.task_specs import ROOT

    assert policy_from_config(ROOT / "configs/verifier/v1_5.yaml") == FullPolicyV15(r2_v3_reject=True, r6_accept_v2_not_available=True, r6b_accept_one_uncovered=True)


def test_replace_keeps_v1_5_fields():
    evidence = replace(ev(v4_failing_units=0), regression=NA)
    assert isinstance(evidence, EvidenceV15) and evidence.v4_design == "per_requirement"


# Amendment A8: switch r6b, between R6 and R7.

R6B = "r6b_accept_one_uncovered"


def r6b_table():
    """Per-requirement V4 NOT_AVAILABLE with uncovered and NO_RESULT requirement counts."""
    for (integrity, (v2, v2_absence, v2_crash), applies, prohibited, v3, v1_incomplete, risk,
         uncovered, no_result, failing, passing) in itertools.product(
            OUTCOMES, V2_CASES, (True, False), (False, True), (False, True), (False, True),
            (False, True), (0, 1, 2), (0, 1), (0, 1), (0, 1, 2)):
        yield EvidenceV15(
            integrity=integrity, regression=v2, v2_absence=v2_absence,
            v2_patched_timeout_or_crash=v2_crash, reproduction=NA, patch_applies=applies,
            prohibited_manipulation=prohibited, v3_absolute_failure=v3,
            v1_analysis_incomplete=v1_incomplete, high_severity_risk=risk,
            v4_design="per_requirement", v4_full_pass=False, v4_failing_units=failing,
            v4_pass_units=passing, v4_uncovered_units=uncovered, v4_no_result_units=no_result,
        )


R6B_CASES = tuple(r6b_table())


def r6b_conditions(e):
    return (e.v4_design == "per_requirement" and e.reproduction is NA and e.regression is P
            and e.v4_uncovered_units == 1 and e.v4_failing_units == 0 and e.v4_no_result_units == 0
            and e.v4_pass_units >= 1 and e.integrity is P and e.patch_applies
            and not e.prohibited_manipulation and not e.v3_absolute_failure
            and not e.v1_analysis_incomplete and not e.high_severity_risk)


def test_r6b_is_off_by_default_and_in_the_switch_names():
    from reliability.verifier.policy_v1_5 import SWITCH_NAMES
    assert R6B in SWITCH_NAMES and getattr(FullPolicyV15(), R6B) is False
    assert RULE_DECISIONS["R6b"] is Decision.ACCEPT


@pytest.mark.parametrize("switches", SWITCHES, ids=lambda s: "".join(str(int(v)) for v in s.values()))
def test_r6b_off_changes_nothing(switches):
    # With r6b off the uncovered and NO_RESULT counts it reads are ignored, and the
    # main truth table (no uncovered requirement) is unchanged by turning r6b on.
    off, on = FullPolicyV15(**switches), FullPolicyV15(**switches, **{R6B: True})
    for evidence in R6B_CASES:
        record = off.decide(evidence)
        assert record.rule_id != "R6b"
        zeroed = replace(evidence, v4_uncovered_units=0, v4_no_result_units=0)
        assert record.decision is off.decide(zeroed).decision
    for evidence in CASES:
        assert on.decide(evidence).decision is off.decide(evidence).decision


@pytest.mark.parametrize("switches", SWITCHES, ids=lambda s: "".join(str(int(v)) for v in s.values()))
def test_r6b_on_accepts_exactly_its_class(switches):
    off, on = FullPolicyV15(**switches), FullPolicyV15(**switches, **{R6B: True})
    for evidence in R6B_CASES:
        before, after = off.decide(evidence), on.decide(evidence)
        if r6b_conditions(evidence):
            assert (after.decision, after.rule_id) == (Decision.ACCEPT, "R6b")
            assert before.decision is Decision.FLAG and before.rule_id == "R7"
        else:
            assert after.rule_id != "R6b" and after.decision is before.decision


def r6b_ev(**kw):
    base = dict(reproduction=NA, v4_full_pass=False, v4_pass_units=2, v4_uncovered_units=1)
    base.update(kw)
    return ev(**base)


def test_r6b_accepts_one_uncovered_requirement_when_switched_on():
    record = FullPolicyV15(**{R6B: True}).decide(r6b_ev())
    assert (record.decision, record.rule_id, record.review_label) == (Decision.ACCEPT, "R6b", "none")
    assert any("uncovered" in reason for reason in record.reasons)
    off = FullPolicyV15().decide(r6b_ev())
    assert (off.decision, off.rule_id, off.review_label) == (Decision.FLAG, "R7", "likely_right")


@pytest.mark.parametrize("kw", [
    dict(v4_uncovered_units=2), dict(v4_uncovered_units=0), dict(v4_no_result_units=1),
    dict(v4_failing_units=1), dict(v4_pass_units=0), dict(regression=NA, v2_absence=NOTHING),
    dict(v4_design="legacy"), dict(high_severity_risk=True), dict(v3_absolute_failure=True),
    dict(v1_analysis_incomplete=True), dict(integrity=NA),
], ids=lambda kw: ",".join(f"{k}={v}" for k, v in kw.items()))
def test_r6b_needs_every_condition(kw):
    record = FullPolicyV15(**{R6B: True}).decide(r6b_ev(**kw))
    assert record.rule_id != "R6b" and record.decision is not Decision.ACCEPT


def test_adapter_reads_uncovered_and_no_result_counts():
    evidence = evidence_from_signals(_signals(NA, _per_requirement(1, {"PASS": 2, "UNCOVERED": 1, "NO_RESULT": 1})))
    assert (evidence.v4_uncovered_units, evidence.v4_no_result_units, evidence.v4_pass_units) == (1, 1, 2)
    legacy = evidence_from_signals(_signals(F, {"setup": {}, "patched": [{"verdict": "fail"}]}))
    assert (legacy.v4_uncovered_units, legacy.v4_no_result_units) == (0, 0)
