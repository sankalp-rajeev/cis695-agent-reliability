"""Run a repair agent over a task manifest (Phase 3.1).

Two structural commitments, both cheaper to make now than to retrofit:

**Count-agnostic.** Nothing here knows the manifest's size or name. `run_manifest`
iterates whatever it is handed, so the same code runs the 10-task pilot and the
75-task main study unchanged. There is no default manifest path anywhere in this
module.

**Parallel-safe.** Each task owns a directory under `tasks/<instance_id>/` and
writes only inside it. There is no shared mutable file - no appended log, no
aggregate JSON updated per task - so concurrent tasks never contend, and a run
interrupted midway leaves completed tasks intact. `max_workers` defaults to 1
because the pilot runs serially, but raising it requires no other change.

The model sits behind `AgentBackend`. That keeps orchestration - freeze, parse,
record - testable against recorded fixtures rather than live API calls, which is
what lets Phases 3.2-3.4 be gated while the model decision is still pending.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from reliability.agent.claim_parser import parse_claim
from reliability.agent.freeze import freeze_patch
from reliability.agent.records import (
    ClaimRecord,
    PatchRecord,
    RepairRecord,
    RunRole,
    Termination,
    UsageRecord,
)
from reliability.benchmark.loader import AgentTask, load_instance
from reliability.benchmark.manifest import Manifest, ManifestEntry


class AgentConfigurationError(RuntimeError):
    """Raised when a backend cannot run as configured."""


@dataclass(frozen=True, slots=True)
class AgentLimits:
    """Ceilings from configs/agent/*.yaml."""

    max_steps: int = 50
    per_command_timeout_s: int = 120
    per_task_timeout_s: int = 1800


@dataclass(frozen=True, slots=True)
class AgentOutcome:
    """Everything a backend reports back about one task."""

    final_output: str
    patch: bytes
    termination: Termination
    commands_run: tuple[str, ...] = ()
    tests_run: tuple[str, ...] = ()
    tokens_in: int = 0
    tokens_out: int = 0
    api_cost_usd: float = 0.0
    trajectory: tuple[dict[str, Any], ...] = ()


class AgentBackend(Protocol):
    """Anything that can attempt a repair and report what it did."""

    model_id: str
    scaffold: str
    version: str

    def run(self, task: AgentTask, workdir: Path, limits: AgentLimits) -> AgentOutcome:
        ...


@dataclass
class MiniSweAgentBackend:
    """mini-SWE-agent integration (Phase 3.1).

    Wired but not yet exercised: the primary model is selected after advisor
    approval, and `configs/model/primary.yaml` deliberately holds `model_id:
    null` until then. Constructing this backend without a concrete model id
    raises rather than falling back to a default, because a silent default would
    put an unrecorded model into the provenance block.
    """

    model_id: str | None
    scaffold: str = "mini-swe-agent"
    version: str = "2.4.6"
    _limits: AgentLimits = field(default_factory=AgentLimits)

    def __post_init__(self) -> None:
        if not self.model_id:
            raise AgentConfigurationError(
                "no model_id configured. configs/model/primary.yaml intentionally "
                "leaves provider/model_id null until the model decision is made; "
                "set it explicitly before the first API spend."
            )

    def run(self, task: AgentTask, workdir: Path, limits: AgentLimits) -> AgentOutcome:
        raise NotImplementedError(
            "live mini-SWE-agent execution is pending the model decision; "
            "Phase 3.1's gate is deferred (see docs/checklist.md)"
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def task_dir_for(run_root: Path, instance_id: str) -> Path:
    """Per-task directory. The unit of isolation for concurrent runs."""
    return run_root / "tasks" / instance_id


def run_task(
    entry: ManifestEntry,
    backend: AgentBackend,
    run_root: Path,
    *,
    experiment_id: str,
    run_role: RunRole,
    manifest_hash: str,
    limits: AgentLimits | None = None,
    dataset=None,
) -> RepairRecord:
    """Run one task and write its frozen patch, trajectory, and record.

    Writes only inside this task's own directory.
    """
    limits = limits or AgentLimits()
    workdir = task_dir_for(run_root, entry.instance_id)
    workdir.mkdir(parents=True, exist_ok=True)

    task, _oracle = load_instance(entry.instance_id, dataset)

    started = _utc_now()
    t0 = datetime.now(UTC)
    outcome = backend.run(task, workdir, limits)
    duration = (datetime.now(UTC) - t0).total_seconds()
    finished = _utc_now()

    frozen = freeze_patch(workdir / "patch.diff", outcome.patch)

    trajectory_path = workdir / "trajectory.jsonl"
    with trajectory_path.open("w", encoding="utf-8", newline="\n") as fh:
        for step in outcome.trajectory:
            fh.write(json.dumps(step) + "\n")

    (workdir / "agent_output.txt").write_text(outcome.final_output, encoding="utf-8")

    claim = parse_claim(outcome.final_output)

    record = RepairRecord(
        instance_id=entry.instance_id,
        experiment_id=experiment_id,
        run_role=run_role,
        manifest_hash=manifest_hash,
        agent_scaffold=backend.scaffold,
        agent_version=backend.version,
        model_id=backend.model_id,
        patch=PatchRecord(
            path=str(frozen.path.relative_to(run_root)),
            sha256=frozen.sha256,
            size_bytes=frozen.size_bytes,
        ),
        trajectory_path=str(trajectory_path.relative_to(run_root)),
        commands_run=outcome.commands_run,
        tests_run=outcome.tests_run,
        claim=ClaimRecord(
            status=claim.status,
            evidence=claim.evidence,
            reason=claim.reason,
            raw_output=outcome.final_output,
        ),
        termination=outcome.termination,
        duration_s=duration,
        usage=UsageRecord(
            tokens_in=outcome.tokens_in,
            tokens_out=outcome.tokens_out,
            api_cost_usd=outcome.api_cost_usd,
        ),
        started_at=started,
        finished_at=finished,
    )
    record.write(workdir / "repair_record.json")
    return record


def run_manifest(
    manifest: Manifest,
    backend: AgentBackend,
    run_root: Path,
    *,
    experiment_id: str,
    run_role: RunRole,
    limits: AgentLimits | None = None,
    max_workers: int = 1,
    dataset=None,
    skip_completed: bool = True,
) -> list[RepairRecord]:
    """Run every task in `manifest`, whatever its size.

    Tasks with an existing record are skipped by default, so an interrupted run
    resumes without redoing completed work or overwriting its evidence.
    """
    run_root.mkdir(parents=True, exist_ok=True)

    # Copy the manifest alongside the results: the run is only interpretable
    # against the exact task list it used.
    (run_root / "manifest.csv").write_bytes(manifest.path.read_bytes())
    (run_root / "manifest.sha256").write_text(
        f"{manifest.content_hash}  {manifest.path.name}\n", encoding="utf-8"
    )

    pending = [
        entry for entry in manifest
        if not (skip_completed
                and (task_dir_for(run_root, entry.instance_id) / "repair_record.json").exists())
    ]

    def _one(entry: ManifestEntry) -> RepairRecord:
        return run_task(
            entry, backend, run_root,
            experiment_id=experiment_id,
            run_role=run_role,
            manifest_hash=manifest.content_hash,
            limits=limits,
            dataset=dataset,
        )

    if max_workers == 1:
        records = [_one(entry) for entry in pending]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            records = list(pool.map(_one, pending))

    return sorted(records, key=lambda r: r.instance_id)
