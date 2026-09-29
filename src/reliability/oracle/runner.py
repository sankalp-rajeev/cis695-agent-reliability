"""The oracle runner, and the ordering guard that protects it (Phase 8.1).

The oracle is the only component allowed to read ground truth, and it must run
*after* the agent has claimed and the verifier has decided. If it could run
earlier, nothing in the artifacts would show that it had — a resolution status
present on disk before the verifier ran is indistinguishable afterwards from one
written after, and the whole design rests on the verifier never having seen it.

So the ordering is enforced rather than documented. `assert_ready()` refuses to
evaluate a task until both the repair record and the verification record already
exist and parse, and the runner calls it before touching the harness. The check
is on the *artifacts*, not on a flag a caller passes, because a caller that
forgot to run the verifier is exactly the caller who would also pass the wrong
flag.

`require_verification=False` exists for the Phase 1 harness controls, which
evaluate gold and deliberately-wrong patches that no agent produced and no
verifier judged. It is a named argument with an explicit default of True, so
skipping the guard is a visible decision at the call site rather than an
omission.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.agent.records import RepairRecord
from reliability.env import clean_env
from reliability.oracle.records import (
    OracleOutcome,
    OracleRecord,
    record_from_report,
)
from reliability.verifier.record import VerificationRecord

REPAIR_RECORD = "repair_record.json"
ORACLE_RECORD = "oracle_record.json"
PATCH_FILE = "patch.diff"

#: Written by the verifier, one per configuration. Any of them satisfies the
#: guard: the point is that verification happened before the answer was known,
#: not which policy was applied.
VERIFICATION_GLOB = "verification_record.*.json"

DATASET_NAME = "SWE-bench/SWE-bench_Verified"
DATASET_SPLIT = "test"


class OracleOrderingError(RuntimeError):
    """Raised when the oracle is asked to run before the pipeline is ready.

    A distinct type rather than a bare RuntimeError so a test can assert this
    specific failure, and so it can never be swallowed by a broad handler that
    was meant for harness flakiness.
    """


@dataclass(frozen=True, slots=True)
class Readiness:
    """What exists for a task, and therefore whether the oracle may run."""

    task_dir: Path
    has_repair_record: bool
    has_verification_record: bool
    has_patch: bool
    verification_configs: tuple[str, ...] = ()

    @property
    def is_ready(self) -> bool:
        return (self.has_repair_record and self.has_verification_record
                and self.has_patch)

    def missing(self) -> tuple[str, ...]:
        absent = []
        if not self.has_repair_record:
            absent.append(REPAIR_RECORD)
        if not self.has_verification_record:
            absent.append(VERIFICATION_GLOB)
        if not self.has_patch:
            absent.append(PATCH_FILE)
        return tuple(absent)


def inspect_task(task_dir: Path) -> Readiness:
    """Report what exists, without deciding anything.

    Separated from `assert_ready` so a caller can survey a whole run and report
    which tasks are not ready, instead of discovering it one exception at a time.
    """
    configs = tuple(
        sorted(p.name.split(".")[1] for p in task_dir.glob(VERIFICATION_GLOB))
    )
    return Readiness(
        task_dir=task_dir,
        has_repair_record=(task_dir / REPAIR_RECORD).is_file(),
        has_verification_record=bool(configs),
        has_patch=(task_dir / PATCH_FILE).is_file(),
        verification_configs=configs,
    )


def assert_ready(task_dir: Path, *, require_verification: bool = True) -> Readiness:
    """Refuse to proceed unless the prior stages have already written their records.

    Both records must also *parse*. A truncated or half-written record means the
    stage that produced it did not finish, and treating a corrupt file as
    evidence that verification happened would defeat the guard while appearing
    to satisfy it.
    """
    if not task_dir.is_dir():
        raise OracleOrderingError(f"no such task directory: {task_dir}")

    readiness = inspect_task(task_dir)

    required_missing = [
        m for m in readiness.missing()
        if require_verification or m != VERIFICATION_GLOB
    ]
    if required_missing:
        raise OracleOrderingError(
            f"refusing to run the oracle for {task_dir.name}: "
            f"missing {', '.join(required_missing)}. The oracle runs last; the "
            "repair and verification records must already exist."
        )

    try:
        RepairRecord.read(task_dir / REPAIR_RECORD)
    except Exception as exc:
        raise OracleOrderingError(
            f"{task_dir.name}: repair record does not parse, so the agent stage "
            f"did not complete: {exc}"
        ) from exc

    if require_verification:
        for path in sorted(task_dir.glob(VERIFICATION_GLOB)):
            try:
                VerificationRecord.read(path)
            except Exception as exc:
                raise OracleOrderingError(
                    f"{task_dir.name}: {path.name} does not parse, so the "
                    f"verifier stage did not complete: {exc}"
                ) from exc

    return readiness


def assert_patch_unchanged(task_dir: Path, record: RepairRecord) -> str:
    """Re-check the patch against the hash recorded at freeze time.

    A verdict attributed to a patch that changed after the agent produced it is
    worse than no verdict, because it still looks like evidence.
    """
    frozen = FrozenPatch(
        path=task_dir / PATCH_FILE,
        sha256=record.patch.sha256,
        size_bytes=record.patch.size_bytes,
    )
    return read_patch(frozen).decode("utf-8")


def run_oracle(
    task_dir: Path,
    *,
    require_verification: bool = True,
    timeout_s: int = 1800,
    python: Path | None = None,
    repo_root: Path | None = None,
) -> OracleRecord:
    """Evaluate one frozen patch and write its oracle record.

    Count-agnostic and parallel-safe like every other stage: it takes one task
    directory, never a manifest or an instance count, and writes only inside
    that directory.
    """
    task_dir = Path(task_dir).resolve()
    repo_root = repo_root or Path(__file__).resolve().parents[3]
    python = python or (repo_root / ".venv/bin/python")

    assert_ready(task_dir, require_verification=require_verification)

    record = RepairRecord.read(task_dir / REPAIR_RECORD)
    patch_text = assert_patch_unchanged(task_dir, record)
    started = datetime.now(tz=UTC)

    if not patch_text.strip():
        return _write(task_dir, OracleRecord(
            instance_id=record.instance_id,
            experiment_id=record.experiment_id,
            patch_sha256=record.patch.sha256,
            outcome=OracleOutcome.EMPTY_PATCH,
            resolved=None,
            error_detail="agent produced no diff; the harness was not invoked",
            evaluated_at=started.isoformat(),
        ))

    run_id = f"{record.experiment_id}__{record.instance_id}"
    predictions = task_dir / "predictions.jsonl"
    predictions.write_text(json.dumps({
        "instance_id": record.instance_id,
        "model_name_or_path": record.model_id.replace("/", "_"),
        "model_patch": patch_text,
    }) + "\n", encoding="utf-8")

    proc = _invoke_harness(
        python, repo_root, task_dir, record, run_id, predictions, timeout_s)

    report = _find_instance_report(repo_root, run_id, record.instance_id)
    elapsed = (datetime.now(tz=UTC) - started).total_seconds()

    if report is None:
        # No report means the harness did not reach a verdict. That is an
        # infrastructure error, not an unresolved patch, and recording it as
        # the latter would bias the resolution rate downward invisibly.
        return _write(task_dir, OracleRecord(
            instance_id=record.instance_id,
            experiment_id=record.experiment_id,
            patch_sha256=record.patch.sha256,
            outcome=OracleOutcome.INFRA_ERROR,
            resolved=None,
            infrastructure_error=True,
            error_detail=(
                f"harness produced no report for {record.instance_id} "
                f"(exit {proc.returncode}); see harness.log"),
            harness_exit_code=proc.returncode,
            harness_run_id=run_id,
            duration_s=elapsed,
            evaluated_at=started.isoformat(),
        ))

    path, payload = report
    return _write(task_dir, record_from_report(
        payload,
        instance_id=record.instance_id,
        experiment_id=record.experiment_id,
        patch_sha256=record.patch.sha256,
        evaluated_at=started.isoformat(),
        harness_exit_code=proc.returncode,
        harness_run_id=run_id,
        report_file=str(path),
        duration_s=elapsed,
    ))


def _invoke_harness(python, repo_root, task_dir, record, run_id, predictions, timeout_s):
    cmd = [
        str(python), "-m", "swebench.harness.run_evaluation",
        "--dataset_name", DATASET_NAME,
        "--split", DATASET_SPLIT,
        "--predictions_path", str(predictions),
        "--instance_ids", record.instance_id,
        "--max_workers", "1",
        "--run_id", run_id,
        "--report_dir", str(task_dir),
        "--timeout", str(timeout_s),
    ]
    # clean_env because ROS leaks 3.12 site-packages into this 3.11 venv, and a
    # shadowed import inside an evaluation would be near-invisible afterwards.
    # check=False: the returncode is recorded, and a harness failure is data.
    with (task_dir / "harness.log").open("w", encoding="utf-8") as log:
        return subprocess.run(
            cmd, cwd=repo_root, stdout=log, stderr=subprocess.STDOUT,
            env=clean_env(), check=False,
        )


def _find_instance_report(repo_root: Path, run_id: str, instance_id: str):
    """Locate the harness's per-instance report.

    The per-instance file is used rather than the run-level summary because it
    is the only one carrying `tests_status` and `infra_failure` — the summary
    would give a resolved flag with no way to tell a real negative from a
    broken environment.
    """
    root = repo_root / "logs" / "run_evaluation" / run_id
    for path in sorted(root.glob(f"*/{instance_id}/report.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if instance_id in payload:
            return path, payload[instance_id]
    return None


def _write(task_dir: Path, record: OracleRecord) -> OracleRecord:
    path = task_dir / ORACLE_RECORD
    if path.exists():
        raise FileExistsError(
            f"refusing to overwrite an existing oracle record: {path}. "
            "A re-evaluation belongs in a new run directory."
        )
    record.write(path)
    return record


__all__ = [
    "ORACLE_RECORD",
    "OracleOrderingError",
    "Readiness",
    "assert_patch_unchanged",
    "assert_ready",
    "inspect_task",
    "run_oracle",
]
