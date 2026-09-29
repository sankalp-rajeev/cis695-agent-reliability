"""Phase 7.3 gate: the verification record schema.

The property under test throughout is that an absent signal is *represented*
rather than assumed away. A layer that did not run must occupy its field, say
so, and say why — because a record missing a key and a record whose checks all
passed read identically to anything downstream, and only one of them is
evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reliability.verifier.decision import (
    BaselinePolicy,
    Decision,
    Evidence,
    FullPolicy,
    SignalOutcome,
)
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
    evidence_from_record,
    load_records,
    summarise,
)

DIGEST = "sha256:" + "ab" * 32
PASS = SignalOutcome.PASS
FAIL = SignalOutcome.FAIL
NA = SignalOutcome.NOT_AVAILABLE


def signal(kind, outcome=PASS, **kwargs) -> SignalRecord:
    return SignalRecord(kind=kind, outcome=outcome, **kwargs)


def absent(kind, absence=SignalAbsence.NOT_IMPLEMENTED) -> SignalRecord:
    return SignalRecord.absent(kind, absence, detail="fixture")


def make_record(**overrides) -> VerificationRecord:
    fields = {
        "instance_id": "psf__requests-1921",
        "experiment_id": "test",
        "verifier_config": "full",
        "patch_sha256": DIGEST,
        "integrity": signal(SignalKind.INTEGRITY),
        "regression": signal(SignalKind.REGRESSION),
        "static": signal(SignalKind.STATIC),
        "reproduction": signal(SignalKind.REPRODUCTION),
        "decision": DecisionEntry(
            decision=Decision.ACCEPT, policy_name="full",
            policy_version="v1.0.0-full", reasons=("all accept conditions met",)),
        "verified_at": "2026-09-29T00:00:00Z",
    }
    fields.update(overrides)
    return VerificationRecord(**fields)


# --- the named gate: absent signals are represented, not assumed -----------


def test_every_signal_is_a_required_field():
    """A layer cannot be omitted from the record; it must say it did not run."""
    for missing in ("integrity", "regression", "static", "reproduction"):
        fields = {k: v for k, v in make_record().model_dump().items() if k != missing}
        with pytest.raises(ValidationError):
            VerificationRecord(**fields)


def test_a_record_with_no_v4_still_validates():
    """The case that exists today: V4 is built but this run predates it."""
    record = make_record(reproduction=absent(SignalKind.REPRODUCTION))

    assert record.reproduction.outcome is NA
    assert record.reproduction.absence is SignalAbsence.NOT_IMPLEMENTED
    assert SignalKind.REPRODUCTION in record.signals_absent
    assert not record.is_complete


def test_all_four_absent_still_validates():
    """A verification where nothing ran is a valid record of nothing running."""
    record = make_record(**{k.value: absent(k) for k in SignalKind})
    assert set(record.signals_absent) == set(SignalKind)
    assert record.signals_reported == ()


def test_an_unattributed_absence_is_rejected():
    """NOT_AVAILABLE with no reason cannot be interpreted later, so it is invalid."""
    with pytest.raises(ValidationError, match="absence reason"):
        SignalRecord(kind=SignalKind.STATIC, outcome=NA)


def test_an_absence_reason_on_a_reporting_signal_is_rejected():
    with pytest.raises(ValidationError, match="absence"):
        SignalRecord(
            kind=SignalKind.STATIC, outcome=PASS,
            absence=SignalAbsence.NOT_CONFIGURED)


@pytest.mark.parametrize("absence", list(SignalAbsence))
def test_every_absence_reason_is_recordable(absence):
    record = SignalRecord.absent(SignalKind.STATIC, absence, detail="why")
    assert record.absence is absence
    assert not record.reported


def test_absence_reasons_are_distinguishable_after_the_fact():
    """The query that makes attribution worth recording.

    A run predating V4 and a run where V4 had nothing to check are both
    incomplete, but only the first should be excluded from a coverage number.
    """
    record = make_record(
        reproduction=absent(SignalKind.REPRODUCTION, SignalAbsence.NOT_IMPLEMENTED),
        static=absent(SignalKind.STATIC, SignalAbsence.NOT_CONFIGURED))

    assert record.absent_because(SignalAbsence.NOT_IMPLEMENTED) == (
        SignalKind.REPRODUCTION,)
    assert record.absent_because(SignalAbsence.NOT_CONFIGURED) == (SignalKind.STATIC,)
    assert record.absent_because(SignalAbsence.TIMEOUT) == ()


def test_completeness_is_reported_not_enforced():
    """An incomplete verification is weaker, not invalid — the analysis needs to
    be able to say which."""
    assert make_record().is_complete
    assert not make_record(static=absent(SignalKind.STATIC)).is_complete


# --- signals cannot be filed in the wrong slot -----------------------------


def test_a_signal_in_the_wrong_field_is_rejected():
    with pytest.raises(ValidationError, match="holds a"):
        make_record(static=signal(SignalKind.REGRESSION))


def test_signals_map_keys_by_kind():
    record = make_record()
    assert set(record.signals) == set(SignalKind)
    assert record.signals[SignalKind.INTEGRITY] is record.integrity


# --- binding to the patch --------------------------------------------------


def test_patch_digest_is_required_and_validated():
    with pytest.raises(ValidationError, match="not a sha256 digest"):
        make_record(patch_sha256="deadbeef")


def test_patch_digest_must_carry_its_prefix():
    with pytest.raises(ValidationError):
        make_record(patch_sha256="ab" * 32)


# --- no oracle data --------------------------------------------------------


@pytest.mark.parametrize("field", [
    "FAIL_TO_PASS", "PASS_TO_PASS", "fail_to_pass", "pass_to_pass",
    "gold_patch", "test_patch", "hints_text", "resolved",
])
def test_record_cannot_carry_oracle_fields(field):
    """extra='forbid' turns an accidental oracle field into a validation error
    rather than a silent extra key nobody notices."""
    with pytest.raises(ValidationError):
        make_record(**{field: "anything"})


def test_selected_tests_are_recorded_for_the_overlap_audit():
    """Phase 5.3 computes overlap with PASS_TO_PASS after the fact. That is the
    only point at which selection and the oracle may meet."""
    record = make_record(
        selected_tests=("tests/test_a.py::test_x",), selection_convention="mirrored_tree")
    assert record.selected_tests == ("tests/test_a.py::test_x",)


# --- the decision ----------------------------------------------------------


def test_decision_requires_a_version_and_a_reason():
    with pytest.raises(ValidationError):
        DecisionEntry(decision=Decision.FLAG, policy_name="full",
                      policy_version="", reasons=("x",))
    with pytest.raises(ValidationError):
        DecisionEntry(decision=Decision.FLAG, policy_name="full",
                      policy_version="v1", reasons=())


def test_a_blank_reason_is_rejected():
    with pytest.raises(ValidationError, match="not a reason"):
        DecisionEntry(decision=Decision.FLAG, policy_name="full",
                      policy_version="v1", reasons=("  ",))


def test_decision_entry_round_trips_from_a_policy():
    produced = FullPolicy().decide(Evidence(integrity=SignalOutcome.PASS))
    entry = DecisionEntry.from_record(produced)

    assert entry.decision is produced.decision
    assert entry.policy_version == produced.policy_version
    assert entry.reasons == produced.reasons


# --- replaying a stored record through a policy ----------------------------


def test_evidence_can_be_rebuilt_from_a_stored_record():
    """A second policy must be applicable to a finished study without
    re-running any layer."""
    record = make_record(
        reproduction=absent(SignalKind.REPRODUCTION),
        integrity=signal(SignalKind.INTEGRITY, findings={"patch_applies": True}))

    evidence = evidence_from_record(record)
    assert evidence.integrity is PASS
    assert evidence.reproduction is NA
    assert FullPolicy().decide(evidence).decision is Decision.FLAG
    assert BaselinePolicy().decide(evidence).decision is Decision.ACCEPT


def test_rebuilt_evidence_reproduces_the_stored_decision():
    for reproduction in (PASS, FAIL, NA):
        signals = {
            "integrity": signal(SignalKind.INTEGRITY, findings={"patch_applies": True}),
            "regression": signal(SignalKind.REGRESSION),
            "static": signal(SignalKind.STATIC),
            "reproduction": (
                absent(SignalKind.REPRODUCTION) if reproduction is NA
                else signal(SignalKind.REPRODUCTION, reproduction)),
        }
        produced = FullPolicy().decide(evidence_from_record(make_record(**signals)))
        record = make_record(decision=DecisionEntry.from_record(produced), **signals)
        assert record.decision.decision is produced.decision


def test_rebuilt_evidence_carries_integrity_flags():
    record = make_record(integrity=signal(
        SignalKind.INTEGRITY, FAIL,
        findings={"patch_applies": False, "prohibited_manipulation": True}))

    evidence = evidence_from_record(record)
    assert evidence.patch_applies is False
    assert evidence.prohibited_manipulation is True
    assert FullPolicy().decide(evidence).decision is Decision.REJECT


# --- persistence -----------------------------------------------------------


def test_round_trips_through_json(tmp_path):
    original = make_record(
        reproduction=absent(SignalKind.REPRODUCTION),
        risk_features={"files_changed": 2, "deletes_files": False})

    path = original.write(tmp_path / "verification_record.full.json")
    assert VerificationRecord.read(path) == original


def test_absence_survives_serialisation(tmp_path):
    """The reason must be readable from the file, not only from the object."""
    record = make_record(reproduction=absent(SignalKind.REPRODUCTION))
    path = record.write(tmp_path / "verification_record.full.json")

    payload = json.loads(path.read_text())
    assert payload["reproduction"]["outcome"] == "NOT_AVAILABLE"
    assert payload["reproduction"]["absence"] == "not_implemented"


def test_refuses_to_overwrite(tmp_path):
    """One verification, one record. A re-verification belongs in a new file."""
    path = tmp_path / "verification_record.full.json"
    make_record().write(path)
    with pytest.raises(FileExistsError):
        make_record().write(path)


def test_the_same_patch_can_be_verified_under_two_configs(tmp_path):
    full = make_record(verifier_config="full")
    baseline = make_record(verifier_config="baseline")
    full.write(tmp_path / "verification_record.full.json")
    baseline.write(tmp_path / "verification_record.baseline.json")

    assert full.patch_sha256 == baseline.patch_sha256


# --- loading and summarising -----------------------------------------------


def test_load_reads_per_task_files(tmp_path):
    for instance in ("a__a-1", "b__b-2"):
        make_record(instance_id=instance).write(
            tmp_path / "tasks" / instance / "verification_record.full.json")

    records = load_records(tmp_path)
    assert [r.instance_id for r in records] == ["a__a-1", "b__b-2"]


def test_load_can_filter_by_config(tmp_path):
    make_record(verifier_config="full").write(
        tmp_path / "tasks" / "a__a-1" / "verification_record.full.json")
    make_record(verifier_config="baseline").write(
        tmp_path / "tasks" / "a__a-1" / "verification_record.baseline.json")

    assert len(load_records(tmp_path)) == 2
    assert len(load_records(tmp_path, config="baseline")) == 1


def test_summary_reports_completeness_beside_decisions():
    """Decision counts without a completeness count would overstate what the
    verifier demonstrated."""
    records = [
        make_record(),
        make_record(reproduction=absent(SignalKind.REPRODUCTION)),
        make_record(static=absent(SignalKind.STATIC, SignalAbsence.NOT_CONFIGURED)),
    ]
    summary = summarise(records)

    assert summary["n"] == 3
    assert summary["n_complete"] == 1
    assert summary["signals_absent"] == {
        "reproduction:not_implemented": 1, "static:not_configured": 1}


def test_summary_lists_every_policy_version_present():
    """Two versions in one summary means the rules changed mid-study."""
    other = DecisionEntry(
        decision=Decision.FLAG, policy_name="full",
        policy_version="v2.0.0-full", reasons=("x",))
    summary = summarise([make_record(), make_record(decision=other)])
    assert summary["policy_versions"] == ["v1.0.0-full", "v2.0.0-full"]


def test_summary_counts_every_decision_kind():
    assert set(summarise([make_record()])["decisions"]) == {d.value for d in Decision}


def test_records_are_frozen():
    import dataclasses

    record = make_record()
    with pytest.raises((ValidationError, dataclasses.FrozenInstanceError)):
        record.instance_id = "other"


# --- the named gate: a real record validates -------------------------------


REAL_RECORD = Path(
    "runs/3.1_smoke_gemini-3.1-flash-lite/tasks/"
    "psf__requests-1921/verification_record.full.json"
)


def test_a_real_record_validates():
    """The other half of the 7.3 gate: a record the pipeline actually wrote.

    This is the absent-signal case the schema was built for — V4 is in scope
    and occupies its field, but this run predates the layer, so the field says
    `NOT_AVAILABLE (not_implemented)` rather than being omitted. A fixture
    would agree with the schema by construction; this one cannot.
    """
    if not REAL_RECORD.is_file():
        pytest.skip(f"no stored verification record at {REAL_RECORD}")

    record = VerificationRecord.read(REAL_RECORD)

    assert record.instance_id == "psf__requests-1921"
    assert record.verifier_config == "full"
    assert record.patch_sha256.startswith("sha256:")
    assert len(record.patch_sha256) == len("sha256:") + 64

    # Every layer occupies its slot. None of the four may be missing.
    assert set(record.signals) == set(SignalKind)

    assert record.integrity.outcome is PASS
    assert record.integrity.absence is None

    # Container layers were not invoked; that is a named disable, not a pass.
    assert record.regression.outcome is NA
    assert record.regression.absence is SignalAbsence.DISABLED
    assert record.static.outcome is NA
    assert record.static.absence is SignalAbsence.DISABLED

    # V4 is load-bearing: the slot is present, the absence is attributed, and
    # the decision names the unmet condition rather than pretending it passed.
    assert record.reproduction.outcome is NA
    assert record.reproduction.absence is SignalAbsence.NOT_IMPLEMENTED
    assert record.decision.decision is Decision.FLAG
    assert any("issue-specific" in r for r in record.decision.reasons)
    assert not record.is_complete

    rebuilt = FullPolicy().decide(evidence_from_record(record))
    assert rebuilt.decision is record.decision.decision
