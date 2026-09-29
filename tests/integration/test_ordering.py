"""Phase 8.1 gate: the oracle runs last, and the guard is on the artifacts.

The named assertion is that an oracle run raises when the verification record is
absent. The rest of this file covers the ways that guard could be satisfied
without actually being satisfied — a corrupt record, a record for a different
task, a caller who passes the right flag having done the wrong thing.

The guard has to be structural because its failure is undetectable afterwards. A
resolution status sitting on disk before the verifier ran is indistinguishable
from one written after, and the entire design rests on the verifier never having
seen it. Nothing in the finished artifacts could tell you the ordering was
violated, so it cannot be left to discipline.
"""

from __future__ import annotations

import json

import pytest

from reliability.agent.claim_parser import ClaimStatus
from reliability.agent.freeze import freeze_patch
from reliability.agent.records import (
    ClaimRecord,
    PatchRecord,
    RepairRecord,
    RunRole,
    Termination,
    UsageRecord,
)
from reliability.oracle.runner import (
    OracleOrderingError,
    assert_ready,
    inspect_task,
    run_oracle,
)
from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
)

PATCH_TEXT = """diff --git a/a.py b/a.py
index 1..2 100644
--- a/a.py
+++ b/a.py
@@ -1,1 +1,1 @@
-x = 1
+x = 2
"""
INSTANCE = "psf__requests-1921"


def write_patch(task_dir, content: str = PATCH_TEXT) -> str:
    """Freeze a patch the way the runner does.

    Uses the real freezer rather than writing the bytes directly, so these
    fixtures inherit the read-only mode the freeze guard checks for. A
    hand-rolled file would be a weaker fixture than the thing it stands in for.
    """
    task_dir.mkdir(parents=True, exist_ok=True)
    return freeze_patch(task_dir / "patch.diff", content).sha256


def write_repair_record(task_dir, digest: str) -> RepairRecord:
    record = RepairRecord(
        instance_id=INSTANCE, experiment_id="ordering_test",
        run_role=RunRole.SMOKE, manifest_hash="deadbeef",
        agent_scaffold="mini-swe-agent", agent_version="2.4.6",
        model_id="test/model",
        patch=PatchRecord(path="patch.diff", sha256=digest,
                          size_bytes=len(PATCH_TEXT.encode())),
        trajectory_path="trajectory.jsonl",
        claim=ClaimRecord(status=ClaimStatus.RESOLVED, evidence="ran tests"),
        termination=Termination.COMPLETED, duration_s=1.0,
        usage=UsageRecord(tokens_in=1, tokens_out=1, api_cost_usd=0.0),
        started_at="2026-09-29T00:00:00Z", finished_at="2026-09-29T00:01:00Z",
    )
    record.write(task_dir / "repair_record.json")
    return record


def write_verification_record(task_dir, digest: str, config: str = "full"):
    record = VerificationRecord(
        instance_id=INSTANCE, experiment_id="ordering_test",
        verifier_config=config, patch_sha256=digest,
        integrity=SignalRecord(kind=SignalKind.INTEGRITY,
                               outcome=SignalOutcome.PASS),
        regression=SignalRecord.absent(
            SignalKind.REGRESSION, SignalAbsence.DISABLED, "fixture"),
        static=SignalRecord.absent(
            SignalKind.STATIC, SignalAbsence.NOT_CONFIGURED, "fixture"),
        reproduction=SignalRecord.absent(
            SignalKind.REPRODUCTION, SignalAbsence.NOT_IMPLEMENTED, "fixture"),
        decision=DecisionEntry(
            decision=Decision.FLAG, policy_name="full",
            policy_version="v1.0.0-full", reasons=("fixture",)),
        verified_at="2026-09-29T00:02:00Z",
    )
    record.write(task_dir / f"verification_record.{config}.json")
    return record


@pytest.fixture
def task_dir(tmp_path):
    return tmp_path / "tasks" / INSTANCE


@pytest.fixture
def repaired(task_dir):
    """Agent stage complete, verifier stage not."""
    digest = write_patch(task_dir)
    write_repair_record(task_dir, digest)
    return task_dir, digest


@pytest.fixture
def verified(repaired):
    """Both prior stages complete; the oracle may run."""
    task_dir, digest = repaired
    write_verification_record(task_dir, digest)
    return task_dir, digest


# --- the named gate --------------------------------------------------------


def test_oracle_raises_when_the_verification_record_is_absent(repaired):
    """The gate: an oracle run must refuse without a verification record."""
    task_dir, _ = repaired
    assert (task_dir / "repair_record.json").is_file()

    with pytest.raises(OracleOrderingError, match="verification_record"):
        run_oracle(task_dir)


def test_nothing_is_written_when_the_guard_refuses(repaired):
    """The refusal must leave no artifact that a later stage could mistake for
    a verdict."""
    task_dir, _ = repaired
    with pytest.raises(OracleOrderingError):
        run_oracle(task_dir)

    assert not (task_dir / "oracle_record.json").exists()
    assert not (task_dir / "harness.log").exists()
    assert not (task_dir / "predictions.jsonl").exists()


def test_oracle_raises_when_the_repair_record_is_absent(task_dir):
    digest = write_patch(task_dir)
    write_verification_record(task_dir, digest)

    with pytest.raises(OracleOrderingError, match="repair_record"):
        run_oracle(task_dir)


def test_oracle_raises_when_both_are_absent(task_dir):
    write_patch(task_dir)
    with pytest.raises(OracleOrderingError) as exc:
        run_oracle(task_dir)
    assert "repair_record.json" in str(exc.value)
    assert "verification_record" in str(exc.value)


def test_oracle_raises_on_an_empty_task_directory(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(OracleOrderingError):
        run_oracle(tmp_path / "empty")


def test_oracle_raises_on_a_missing_task_directory(tmp_path):
    with pytest.raises(OracleOrderingError, match="no such task directory"):
        run_oracle(tmp_path / "does_not_exist")


# --- the guard cannot be satisfied by a file that merely exists ------------


def test_a_corrupt_verification_record_does_not_satisfy_the_guard(repaired):
    """A half-written record means the verifier did not finish. Treating it as
    proof that verification happened would defeat the guard while appearing to
    satisfy it."""
    task_dir, _ = repaired
    (task_dir / "verification_record.full.json").write_text('{"truncated": ')

    with pytest.raises(OracleOrderingError, match="does not parse"):
        run_oracle(task_dir)


def test_a_verification_record_missing_a_signal_does_not_satisfy_the_guard(repaired):
    """Schema validity is the bar, not file presence."""
    task_dir, digest = repaired
    payload = json.loads(
        VerificationRecord(
            instance_id=INSTANCE, experiment_id="ordering_test",
            verifier_config="full", patch_sha256=digest,
            integrity=SignalRecord(kind=SignalKind.INTEGRITY,
                                   outcome=SignalOutcome.PASS),
            regression=SignalRecord.absent(
                SignalKind.REGRESSION, SignalAbsence.DISABLED, "f"),
            static=SignalRecord.absent(
                SignalKind.STATIC, SignalAbsence.DISABLED, "f"),
            reproduction=SignalRecord.absent(
                SignalKind.REPRODUCTION, SignalAbsence.NOT_IMPLEMENTED, "f"),
            decision=DecisionEntry(
                decision=Decision.FLAG, policy_name="full",
                policy_version="v1", reasons=("f",)),
            verified_at="2026-09-29T00:00:00Z",
        ).to_json())
    del payload["static"]
    (task_dir / "verification_record.full.json").write_text(json.dumps(payload))

    with pytest.raises(OracleOrderingError, match="does not parse"):
        run_oracle(task_dir)


def test_a_corrupt_repair_record_does_not_satisfy_the_guard(verified):
    task_dir, _ = verified
    (task_dir / "repair_record.json").write_text("{}")

    with pytest.raises(OracleOrderingError, match="does not parse"):
        run_oracle(task_dir)


def test_an_empty_verification_file_does_not_satisfy_the_guard(repaired):
    task_dir, _ = repaired
    (task_dir / "verification_record.full.json").write_text("")

    with pytest.raises(OracleOrderingError, match="does not parse"):
        run_oracle(task_dir)


# --- readiness is reportable without raising ------------------------------


def test_inspect_reports_what_is_missing_without_raising(repaired):
    """A survey of a whole run should not proceed one exception at a time."""
    task_dir, _ = repaired
    readiness = inspect_task(task_dir)

    assert readiness.has_repair_record
    assert not readiness.has_verification_record
    assert not readiness.is_ready
    assert readiness.missing() == ("verification_record.*.json",)


def test_inspect_reports_ready_when_both_exist(verified):
    task_dir, _ = verified
    readiness = inspect_task(task_dir)

    assert readiness.is_ready
    assert readiness.missing() == ()
    assert readiness.verification_configs == ("full",)


def test_any_verifier_config_satisfies_the_guard(repaired):
    """The point is that verification happened before the answer was known,
    not which policy was applied."""
    task_dir, digest = repaired
    write_verification_record(task_dir, digest, config="baseline")

    readiness = assert_ready(task_dir)
    assert readiness.verification_configs == ("baseline",)


def test_both_configs_are_reported_when_both_ran(repaired):
    task_dir, digest = repaired
    write_verification_record(task_dir, digest, config="full")
    write_verification_record(task_dir, digest, config="baseline")

    assert assert_ready(task_dir).verification_configs == ("baseline", "full")


# --- the harness-control escape hatch -------------------------------------


def test_verification_can_be_waived_explicitly(repaired):
    """Phase 1 controls evaluate gold and wrong patches that no verifier judged.

    Waiving is a named argument defaulting to True, so it is a visible decision
    at the call site rather than an omission.
    """
    task_dir, _ = repaired
    readiness = assert_ready(task_dir, require_verification=False)
    assert readiness.has_repair_record
    assert not readiness.has_verification_record


def test_waiving_verification_does_not_waive_the_repair_record(task_dir):
    write_patch(task_dir)
    with pytest.raises(OracleOrderingError, match="repair_record"):
        assert_ready(task_dir, require_verification=False)


def test_the_default_is_to_require_verification(repaired):
    task_dir, _ = repaired
    with pytest.raises(OracleOrderingError):
        assert_ready(task_dir)


# --- the patch must be the one that was verified --------------------------


def test_a_mutated_patch_is_refused(verified):
    """A verdict attributed to a patch that changed after freezing is worse
    than no verdict, because it still looks like evidence."""
    from reliability.agent.freeze import FrozenPatchError

    task_dir, _ = verified
    patch = task_dir / "patch.diff"
    patch.chmod(0o644)
    patch.write_text(PATCH_TEXT.replace("x = 2", "x = 3"))

    with pytest.raises(FrozenPatchError):
        run_oracle(task_dir)


def test_an_absent_patch_is_refused(verified):
    task_dir, _ = verified
    (task_dir / "patch.diff").unlink()

    with pytest.raises((OracleOrderingError, FileNotFoundError)):
        run_oracle(task_dir)


# --- ordering holds end to end --------------------------------------------


def test_an_empty_patch_short_circuits_without_the_harness(task_dir):
    """Still subject to the guard, and still writes an attributed record."""
    from reliability.oracle.records import OracleOutcome

    digest = write_patch(task_dir, content="")

    record = RepairRecord(
        instance_id=INSTANCE, experiment_id="ordering_test",
        run_role=RunRole.SMOKE, manifest_hash="deadbeef",
        agent_scaffold="mini-swe-agent", agent_version="2.4.6",
        model_id="test/model",
        patch=PatchRecord(path="patch.diff", sha256=digest, size_bytes=0),
        trajectory_path="trajectory.jsonl",
        claim=ClaimRecord(status=ClaimStatus.UNRESOLVED),
        termination=Termination.STEP_LIMIT, duration_s=1.0,
        usage=UsageRecord(tokens_in=1, tokens_out=1, api_cost_usd=0.0),
        started_at="2026-09-29T00:00:00Z", finished_at="2026-09-29T00:01:00Z",
    )
    record.write(task_dir / "repair_record.json")
    write_verification_record(task_dir, digest)

    result = run_oracle(task_dir)
    assert result.outcome is OracleOutcome.EMPTY_PATCH
    assert result.resolved is None          # not False
    assert not (task_dir / "harness.log").exists()


def test_the_oracle_refuses_to_overwrite_its_own_record(verified):
    """A re-evaluation belongs in a new run directory, not on top of the old
    verdict."""
    task_dir, _ = verified
    (task_dir / "oracle_record.json").write_text("{}")

    with pytest.raises((FileExistsError, OracleOrderingError)):
        run_oracle(task_dir)
