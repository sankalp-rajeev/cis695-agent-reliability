"""Phase 3.3 gate: the repair record schema validates.

The checklist also asks that one real record from 3.1 validate against this
schema. That half is pending the model decision - see the runner tests, which
validate a record built from a recorded fixture trajectory instead.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from reliability.agent.claim_parser import ClaimStatus, UnparseableReason
from reliability.agent.records import (
    ClaimRecord,
    PatchRecord,
    RepairRecord,
    RunRole,
    Termination,
    UsageRecord,
    load_records,
    summarise,
)

DIGEST = "sha256:" + "a" * 64


def make_record(**overrides) -> RepairRecord:
    base = {
        "instance_id": "django__django-14373",
        "experiment_id": "pilot_10",
        "run_role": RunRole.PILOT,
        "manifest_hash": "sha256:f03000ed",
        "agent_scaffold": "mini-swe-agent",
        "agent_version": "2.4.6",
        "model_id": "example-model-2026-01-01",
        "patch": PatchRecord(path="tasks/x/patch.diff", sha256=DIGEST, size_bytes=512),
        "trajectory_path": "tasks/x/trajectory.jsonl",
        "commands_run": ("pytest -q",),
        "tests_run": ("tests/test_x.py::test_y",),
        "claim": ClaimRecord(status=ClaimStatus.RESOLVED, evidence="suite green"),
        "termination": Termination.COMPLETED,
        "duration_s": 42.5,
        "usage": UsageRecord(tokens_in=1000, tokens_out=250, api_cost_usd=0.03),
        "started_at": "2026-09-15T00:00:00+00:00",
        "finished_at": "2026-09-15T00:00:42+00:00",
    }
    base.update(overrides)
    return RepairRecord(**base)


# --- schema ----------------------------------------------------------------


def test_a_complete_record_validates():
    record = make_record()
    assert record.instance_id == "django__django-14373"
    assert record.usage.total_tokens == 1250


def test_round_trips_through_json(tmp_path):
    path = make_record().write(tmp_path / "repair_record.json")
    assert RepairRecord.read(path) == make_record()


@pytest.mark.parametrize(
    "field",
    ["instance_id", "experiment_id", "run_role", "agent_scaffold", "model_id",
     "patch", "claim", "termination", "usage", "started_at"],
)
def test_missing_required_field_is_rejected(field):
    payload = json.loads(make_record().to_json())
    del payload[field]
    with pytest.raises(ValidationError):
        RepairRecord.validate_dict(payload)


def test_unexpected_field_is_rejected():
    """A renamed field that silently lost its value is the failure guarded against."""
    payload = json.loads(make_record().to_json())
    payload["duration_seconds"] = 42.5
    with pytest.raises(ValidationError):
        RepairRecord.validate_dict(payload)


def test_record_is_immutable():
    with pytest.raises(ValidationError):
        make_record().instance_id = "other"  # type: ignore[misc]


def test_empty_identity_strings_are_rejected():
    with pytest.raises(ValidationError):
        make_record(instance_id="")


# --- accounting ------------------------------------------------------------


@pytest.mark.parametrize("field", ["tokens_in", "tokens_out", "api_cost_usd"])
def test_negative_usage_is_rejected(field):
    with pytest.raises(ValidationError):
        UsageRecord(**{"tokens_in": 0, "tokens_out": 0, "api_cost_usd": 0.0, field: -1})


def test_usage_is_required_not_defaulted():
    """An unrecorded cost is not a zero cost."""
    payload = json.loads(make_record().to_json())
    del payload["usage"]
    with pytest.raises(ValidationError):
        RepairRecord.validate_dict(payload)


def test_negative_duration_is_rejected():
    with pytest.raises(ValidationError):
        make_record(duration_s=-1.0)


def test_patch_digest_must_look_like_sha256():
    for bad in ["abc", "md5:" + "a" * 32, "sha256:tooshort"]:
        with pytest.raises(ValidationError):
            PatchRecord(path="p", sha256=bad, size_bytes=1)


def test_empty_patch_is_representable():
    record = make_record(
        patch=PatchRecord(path="p", sha256="sha256:" + "b" * 64, size_bytes=0)
    )
    assert record.patch.is_empty


# --- run role and termination ---------------------------------------------


def test_run_role_has_no_default():
    payload = json.loads(make_record().to_json())
    del payload["run_role"]
    with pytest.raises(ValidationError):
        RepairRecord.validate_dict(payload)


def test_smoke_runs_are_not_citable():
    assert make_record(run_role=RunRole.SMOKE).is_citable_as_result is False
    assert make_record(run_role=RunRole.PILOT).is_citable_as_result is True


def test_unparseable_claim_is_representable():
    record = make_record(
        claim=ClaimRecord(
            status=ClaimStatus.UNPARSEABLE,
            reason=UnparseableReason.MISSING,
            raw_output="I think it's resolved.",
        )
    )
    assert not record.claim.is_parseable
    assert record.claim.reason is UnparseableReason.MISSING


def test_timeout_is_distinct_from_an_unresolved_claim():
    """An agent killed at its limit has not claimed UNRESOLVED."""
    record = make_record(
        termination=Termination.TIMEOUT,
        claim=ClaimRecord(status=ClaimStatus.UNPARSEABLE,
                          reason=UnparseableReason.EMPTY_OUTPUT),
    )
    assert record.termination is Termination.TIMEOUT
    assert record.claim.status is not ClaimStatus.UNRESOLVED


# --- aggregation -----------------------------------------------------------


def test_load_records_reads_per_task_files(tmp_path):
    for i, instance in enumerate(["a__a-1", "b__b-2", "c__c-3"]):
        make_record(instance_id=instance).write(
            tmp_path / "tasks" / instance / "repair_record.json"
        )

    records = load_records(tmp_path)
    assert len(records) == 3
    assert [r.instance_id for r in records] == ["a__a-1", "b__b-2", "c__c-3"]


def test_summarise_counts_the_phase_9_gates(tmp_path):
    records = [
        make_record(instance_id="a__a-1"),
        make_record(instance_id="b__b-2",
                    claim=ClaimRecord(status=ClaimStatus.UNRESOLVED)),
        make_record(instance_id="c__c-3",
                    claim=ClaimRecord(status=ClaimStatus.UNPARSEABLE,
                                      reason=UnparseableReason.MISSING),
                    termination=Termination.TIMEOUT),
    ]
    s = summarise(records)

    assert s["n"] == 3
    assert s["parseable_claims"] == 2
    assert s["resolved_claims"] == 1
    assert s["completed"] == 2
    assert s["roles"] == ["pilot"]


def test_write_refuses_to_overwrite(tmp_path):
    path = tmp_path / "repair_record.json"
    make_record().write(path)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        make_record().write(path)


def test_records_land_in_per_task_directories(tmp_path):
    """Parallel-safety: no shared mutable file for concurrent tasks to contend on."""
    a = make_record(instance_id="a__a-1").write(
        tmp_path / "tasks" / "a__a-1" / "repair_record.json")
    b = make_record(instance_id="b__b-2").write(
        tmp_path / "tasks" / "b__b-2" / "repair_record.json")

    assert a.parent != b.parent
    assert a.exists() and b.exists()
