"""Phase 8.2 gate: the oracle record schema.

The property under test throughout is that an infrastructure error is never
counted as an unresolved patch. A crashed harness and a patch that did not work
look identical in aggregate, so the schema refuses to let them be recorded
identically — `resolved` is `None` when no verdict was reached, and there is no
value of it that reads as "no" when the truth is "we do not know".

The second half of this file is the replay gate: the three gold-patch instances
from Phase 1.2 must parse to `resolved: true` through the real mapping.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reliability.oracle.records import (
    HARNESS_ORIGINAL,
    OracleOutcome,
    OracleRecord,
    TestSuiteResult,
    exclude_task_as_infrastructure,
    load_records,
    outcome_from_report,
    record_from_report,
    summarise,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DIGEST = "sha256:" + "cd" * 32

GOLD_INSTANCES = (
    "django__django-12304",
    "sympy__sympy-15599",
    "matplotlib__matplotlib-25287",
)


def make_record(**overrides) -> OracleRecord:
    fields = {
        "instance_id": "psf__requests-1921",
        "experiment_id": "test",
        "patch_sha256": DIGEST,
        "outcome": OracleOutcome.RESOLVED,
        "resolved": True,
        "evaluated_at": "2026-09-29T00:00:00Z",
    }
    fields.update(overrides)
    return OracleRecord(**fields)


def report(**overrides) -> dict:
    payload = {
        "patch_is_None": False,
        "patch_exists": True,
        "patch_successfully_applied": True,
        "resolved": True,
        "infra_failure": False,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["test_a"], "failure": []},
            "PASS_TO_PASS": {"success": ["test_b", "test_c"], "failure": []},
        },
    }
    payload.update(overrides)
    return payload


# --- infrastructure errors are never unresolved ----------------------------


def test_an_infrastructure_error_cannot_claim_a_verdict():
    """The invariant this schema exists to hold."""
    with pytest.raises(ValidationError, match="not an unresolved patch"):
        make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=False,
                    infrastructure_error=True)


def test_an_infrastructure_error_cannot_claim_resolution_either():
    with pytest.raises(ValidationError, match="not an unresolved patch"):
        make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=True,
                    infrastructure_error=True)


def test_an_infrastructure_error_records_none():
    record = make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=None,
                         infrastructure_error=True)
    assert record.resolved is None
    assert not record.counts_toward_resolution_rate


@pytest.mark.parametrize("outcome", [
    OracleOutcome.INFRA_ERROR, OracleOutcome.EMPTY_PATCH, OracleOutcome.NOT_RUN])
def test_outcomes_without_a_verdict_require_resolved_none(outcome):
    with pytest.raises(ValidationError):
        make_record(outcome=outcome, resolved=False,
                    infrastructure_error=outcome is OracleOutcome.INFRA_ERROR)


def test_the_flag_and_the_outcome_must_agree():
    with pytest.raises(ValidationError, match="must agree"):
        make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=None,
                    infrastructure_error=False)
    with pytest.raises(ValidationError, match="must agree"):
        make_record(outcome=OracleOutcome.UNRESOLVED, resolved=False,
                    infrastructure_error=True)


def test_resolved_must_match_its_outcome():
    with pytest.raises(ValidationError, match="RESOLVED but resolved is not True"):
        make_record(outcome=OracleOutcome.RESOLVED, resolved=False)
    with pytest.raises(ValidationError, match="UNRESOLVED but resolved is not False"):
        make_record(outcome=OracleOutcome.UNRESOLVED, resolved=True)


def test_only_findings_about_the_patch_count():
    assert OracleOutcome.RESOLVED.is_a_finding_about_the_patch
    assert OracleOutcome.UNRESOLVED.is_a_finding_about_the_patch
    assert OracleOutcome.PATCH_APPLY_FAILED.is_a_finding_about_the_patch
    assert not OracleOutcome.INFRA_ERROR.is_a_finding_about_the_patch
    assert not OracleOutcome.EMPTY_PATCH.is_a_finding_about_the_patch
    assert not OracleOutcome.NOT_RUN.is_a_finding_about_the_patch


# --- counting --------------------------------------------------------------


def test_infrastructure_errors_are_counted_separately():
    """Never folded into unresolved, and never in the denominator."""
    records = [
        make_record(),
        make_record(outcome=OracleOutcome.UNRESOLVED, resolved=False),
        make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=None,
                    infrastructure_error=True),
    ]
    summary = summarise(records)

    assert summary["n_resolved"] == 1
    assert summary["n_unresolved"] == 1
    assert summary["n_infrastructure_error"] == 1
    assert summary["n_evaluated"] == 2
    assert summary["resolution_rate"] == 0.5     # not 1/3


def test_an_all_infrastructure_run_has_no_resolution_rate():
    """A rate of zero would assert something; None asserts nothing."""
    summary = summarise([make_record(
        outcome=OracleOutcome.INFRA_ERROR, resolved=None, infrastructure_error=True)])
    assert summary["resolution_rate"] is None
    assert summary["n_evaluated"] == 0
    assert summary["n_not_evaluated"] == 1


def test_empty_patches_are_counted_but_not_evaluated():
    summary = summarise([
        make_record(),
        make_record(outcome=OracleOutcome.EMPTY_PATCH, resolved=None)])
    assert summary["n_empty_patch"] == 1
    assert summary["resolution_rate"] == 1.0


def test_summary_counts_every_outcome_kind():
    assert set(summarise([make_record()])["outcomes"]) == {o.value for o in OracleOutcome}


# --- test suite results ----------------------------------------------------


def test_names_are_kept_not_just_counts():
    """Phase 5.3 needs the PASS_TO_PASS names to compute selection overlap."""
    record = make_record(pass_to_pass=TestSuiteResult(success=("test_b", "test_c")))
    assert record.pass_to_pass.success == ("test_b", "test_c")
    assert record.pass_to_pass.n_total == 2


def test_an_empty_suite_is_not_all_passed():
    """Nothing executed, so nothing was demonstrated."""
    assert not TestSuiteResult().all_passed
    assert TestSuiteResult(success=("t",)).all_passed
    assert not TestSuiteResult(success=("t",), failure=("u",)).all_passed


# --- mapping harness output ------------------------------------------------


def test_a_resolved_report_maps_to_resolved():
    assert outcome_from_report(report()) is OracleOutcome.RESOLVED


def test_an_unresolved_report_maps_to_unresolved():
    assert outcome_from_report(report(resolved=False)) is OracleOutcome.UNRESOLVED


def test_infra_failure_is_checked_before_resolution():
    """A crashed run can still carry a stale resolved flag; it is not a verdict."""
    payload = report(resolved=False, infra_failure=True)
    assert outcome_from_report(payload) is OracleOutcome.INFRA_ERROR

    record = record_from_report(
        payload, instance_id="a__a-1", experiment_id="t",
        patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")
    assert record.resolved is None
    assert record.infrastructure_error


def test_a_patch_that_did_not_apply_is_its_own_outcome():
    payload = report(resolved=False, patch_successfully_applied=False)
    assert outcome_from_report(payload) is OracleOutcome.PATCH_APPLY_FAILED


def test_a_failure_to_apply_still_counts_as_a_finding():
    """Unlike a crashed harness, this is a fact about the patch."""
    record = record_from_report(
        report(resolved=False, patch_successfully_applied=False),
        instance_id="a__a-1", experiment_id="t",
        patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")
    assert record.counts_toward_resolution_rate
    assert record.resolved is False


def test_a_missing_patch_maps_to_empty():
    assert outcome_from_report(report(patch_is_None=True)) is OracleOutcome.EMPTY_PATCH


def test_test_statuses_are_carried_through():
    record = record_from_report(
        report(), instance_id="a__a-1", experiment_id="t",
        patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")
    assert record.fail_to_pass.success == ("test_a",)
    assert record.pass_to_pass.success == ("test_b", "test_c")


def test_a_report_with_no_tests_status_does_not_crash():
    record = record_from_report(
        report(tests_status={}), instance_id="a__a-1", experiment_id="t",
        patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")
    assert record.fail_to_pass.n_total == 0
    assert not record.fail_to_pass.all_passed


# --- the replay gate -------------------------------------------------------


@pytest.mark.parametrize("instance_id", GOLD_INSTANCES)
def test_gold_patches_replay_to_resolved(instance_id):
    """Phase 8.2 gate: the three gold instances from 1.2 must map to resolved.

    Parses the harness reports those runs actually produced, so this exercises
    the real mapping against real output rather than a fixture that agrees with
    it by construction.
    """
    path = next(
        (REPO_ROOT / "logs" / "run_evaluation").glob(
            f"1.2_gold_sanity__{instance_id}/*/{instance_id}/report.json"),
        None,
    )
    if path is None:
        pytest.skip(f"no stored 1.2 harness report for {instance_id}")

    payload = json.loads(path.read_text())[instance_id]
    record = record_from_report(
        payload, instance_id=instance_id, experiment_id="1.2_gold_sanity",
        patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")

    assert record.outcome is OracleOutcome.RESOLVED
    assert record.resolved is True
    assert not record.infrastructure_error
    assert record.fail_to_pass.all_passed
    assert record.pass_to_pass.all_passed
    assert record.fail_to_pass.failure == ()


def test_the_wrong_patch_control_replays_to_unresolved():
    """The negative half. A control that also replayed to resolved would mean
    the mapping is not reading the report at all."""
    paths = sorted((REPO_ROOT / "logs" / "run_evaluation").glob(
        "1.3b_wrong_patch__*/*/*/report.json"))
    if not paths:
        pytest.skip("no stored 1.3b harness reports")

    for path in paths:
        instance_id = path.parent.name
        payload = json.loads(path.read_text())[instance_id]
        record = record_from_report(
            payload, instance_id=instance_id, experiment_id="1.3b_wrong_patch",
            patch_sha256=DIGEST, evaluated_at="2026-09-29T00:00:00Z")

        assert record.resolved is False, instance_id
        assert record.outcome is not OracleOutcome.RESOLVED
        assert not record.infrastructure_error, instance_id


# --- persistence -----------------------------------------------------------


def test_round_trips_through_json(tmp_path):
    original = make_record(
        fail_to_pass=TestSuiteResult(success=("test_a",)),
        pass_to_pass=TestSuiteResult(success=("test_b",), failure=("test_c",)))
    path = original.write(tmp_path / "oracle_record.json")
    assert OracleRecord.read(path) == original


def test_resolved_none_survives_serialisation(tmp_path):
    """Read back as null, not as false."""
    record = make_record(outcome=OracleOutcome.INFRA_ERROR, resolved=None,
                         infrastructure_error=True)
    path = record.write(tmp_path / "oracle_record.json")

    payload = json.loads(path.read_text())
    assert payload["resolved"] is None
    assert payload["infrastructure_error"] is True


def test_refuses_to_overwrite(tmp_path):
    path = tmp_path / "oracle_record.json"
    make_record().write(path)
    with pytest.raises(FileExistsError):
        make_record().write(path)


def test_load_reads_per_task_files(tmp_path):
    for instance in ("a__a-1", "b__b-2"):
        make_record(instance_id=instance).write(
            tmp_path / "tasks" / instance / "oracle_record.json")
    assert [r.instance_id for r in load_records(tmp_path)] == ["a__a-1", "b__b-2"]


@pytest.mark.parametrize("field", ["gold_patch", "test_patch", "hints_text"])
def test_record_rejects_unexpected_fields(field):
    with pytest.raises(ValidationError):
        make_record(**{field: "x"})


# --- excluding a verdict the harness should have called an infrastructure error ---


def _unresolved_task(tmp_path):
    record = OracleRecord(
        instance_id="psf__requests-1921", experiment_id="x", patch_sha256="sha256:" + "a" * 64,
        outcome=OracleOutcome.UNRESOLVED, resolved=False,
        fail_to_pass=TestSuiteResult(success=("f1",)),
        pass_to_pass=TestSuiteResult(success=("p1",), failure=("p2",)),
        evaluated_at="2026-09-30T00:00:00Z")
    task = tmp_path / "tasks" / "psf__requests-1921"
    record.write(task / "oracle_record.json")
    return task, record


def test_an_exclusion_is_no_verdict_not_a_relabel(tmp_path):
    task, _ = _unresolved_task(tmp_path)
    excluded = exclude_task_as_infrastructure(task, "httpbin.org answered 502")
    assert excluded.outcome is OracleOutcome.INFRA_ERROR
    assert excluded.resolved is None          # not False, and never True
    assert excluded.infrastructure_error is True
    assert "502" in excluded.error_detail
    assert "'unresolved'" in excluded.error_detail   # what the harness said survives
    assert excluded.pass_to_pass.failure == ("p2",)  # the harness's data is untouched
    assert OracleRecord.read(task / "oracle_record.json") == excluded


def test_the_harness_original_is_kept_verbatim(tmp_path):
    task, original = _unresolved_task(tmp_path)
    before = (task / "oracle_record.json").read_text()
    exclude_task_as_infrastructure(task, "reason")
    kept = task / HARNESS_ORIGINAL
    assert kept.read_text() == before
    assert OracleRecord.read(kept) == original


def test_an_exclusion_leaves_the_resolution_rate_and_counts_it_separately(tmp_path):
    task, _ = _unresolved_task(tmp_path)
    exclude_task_as_infrastructure(task, "reason")
    summary = summarise(load_records(tmp_path))
    assert summary["n_infrastructure_error"] == 1
    assert summary["n_unresolved"] == 0
    assert summary["n_evaluated"] == 0


def test_an_exclusion_cannot_be_applied_twice_or_without_a_reason(tmp_path):
    task, _ = _unresolved_task(tmp_path)
    with pytest.raises(ValueError, match="reason"):
        exclude_task_as_infrastructure(task, "  ")
    exclude_task_as_infrastructure(task, "reason")
    with pytest.raises(FileExistsError):
        exclude_task_as_infrastructure(task, "reason again")
