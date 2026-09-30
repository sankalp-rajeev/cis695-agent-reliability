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
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from reliability.agent.claim_parser import ClaimStatus, UnparseableReason, parse_claim
from reliability.agent.freeze import freeze_patch
from reliability.agent.isolation import (
    IsolationError,
    assert_network_none,
    prepare_environment,
)
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

logger = logging.getLogger(__name__)


class AgentConfigurationError(RuntimeError):
    """Raised when a backend cannot run as configured."""


@dataclass(frozen=True, slots=True)
class AgentLimits:
    """Ceilings from configs/agent/*.yaml and configs/model/*.yaml."""

    max_steps: int = 50
    per_command_timeout_s: int = 120
    per_task_timeout_s: int = 1800
    max_cost_usd: float = 5.0


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
    agent_config_path: Path | None = None
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    scaffold: str = "mini-swe-agent"
    version: str = "2.4.6"

    def __post_init__(self) -> None:
        if not self.model_id:
            raise AgentConfigurationError(
                "no model_id configured. configs/model/primary.yaml intentionally "
                "leaves provider/model_id null until the model decision is made; "
                "set it explicitly before the first API spend."
            )

    def run(self, task: AgentTask, workdir: Path, limits: AgentLimits) -> AgentOutcome:
        # Imported lazily: mini-SWE-agent pulls in litellm and prints a startup
        # banner, which the model-independent unit tests should not pay for.
        import litellm
        import yaml
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.config import builtin_config_dir
        from minisweagent.models import get_model
        from minisweagent.run.benchmarks.swebench import get_sb_environment

        config_path = self.agent_config_path or (
            Path(builtin_config_dir) / "benchmarks" / "swebench.yaml"
        )
        config = yaml.safe_load(Path(config_path).read_text())
        config.setdefault("agent", {})["step_limit"] = limits.max_steps
        config["agent"]["cost_limit"] = limits.max_cost_usd
        config.setdefault("environment", {})["timeout"] = limits.per_command_timeout_s
        # --network none has to be in run_args. mini-SWE-agent splices that
        # list into docker run; a network key anywhere else never arrives.
        prepare_environment(config)

        model_config = {**config.get("model", {}), **self.model_kwargs}
        model_config["model_name"] = self.model_id
        model = get_model(self.model_id, model_config)

        # Only instance_id is needed: mini-SWE-agent derives the image name from
        # it by the same rule the harness uses, so no oracle field is read here.
        env = get_sb_environment(config, {"instance_id": task.instance_id})
        try:
            if not env.container_id:
                raise IsolationError("agent container did not start")
            # Inspect the container Docker started. A flag that only exists in
            # the config we passed is not isolation.
            assert_network_none(env.container_id)
        except IsolationError:
            try:
                env.cleanup()
            except Exception as exc:  # noqa: BLE001
                logger.warning("cleanup after isolation failure for %s: %s",
                               task.instance_id, exc)
            raise

        agent_config = {k: v for k, v in config["agent"].items()}
        agent_config["wall_time_limit_seconds"] = limits.per_task_timeout_s
        agent = DefaultAgent(model, env, **agent_config)

        rate_limited = False
        try:
            result = agent.run(task.problem_statement)
            exit_status = result.get("exit_status", "")
            submission = result.get("submission", "") or ""
        except litellm.exceptions.RateLimitError:
            # The scaffold already retried with exponential backoff and still
            # could not get through. Reported as throttling, not agent failure.
            rate_limited, exit_status, submission = True, "RateLimited", ""
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            exit_status, submission = f"{type(exc).__name__}: {exc}"[:500], ""
        finally:
            try:
                env.cleanup()
            except Exception as exc:  # noqa: BLE001 - must not mask the result
                # A leaked container is a disk problem, not a run outcome, so it
                # is logged rather than raised over whatever the agent produced.
                logger.warning("container cleanup failed for %s: %s",
                               task.instance_id, exc)

        claim_text, patch_bytes = _split_submission(submission)
        (workdir / "submission_raw.txt").write_text(submission, encoding="utf-8")

        return AgentOutcome(
            final_output=claim_text,
            patch=patch_bytes,
            termination=_termination_for(
                exit_status, rate_limited,
                step_limit_reached=_step_limit_reached(agent, limits.max_steps)),
            commands_run=_commands_from(agent.messages),
            tests_run=(),
            tokens_in=_sum_tokens(agent.messages, "prompt_tokens"),
            tokens_out=_sum_tokens(agent.messages, "completion_tokens"),
            api_cost_usd=float(getattr(agent, "cost", 0.0)),
            trajectory=tuple(_serialisable(m) for m in agent.messages),
        )


#: Separates the model's claim from its patch inside a single submitted output.
CLAIM_DELIMITER = "<<<END_CLAIM>>>"


def _split_submission(submission: str) -> tuple[str, bytes]:
    """Split a submission into claim text and patch bytes.

    The configured prompt emits `claim … <<<END_CLAIM>>> … patch`. If the
    delimiter is absent the agent did not follow the submission format, so the
    whole output is treated as the patch and also handed to the claim parser -
    which will report UNPARSEABLE unless the markers happen to appear inline.
    """
    if CLAIM_DELIMITER in submission:
        claim, _, patch = submission.partition(CLAIM_DELIMITER)
        return claim, patch.lstrip("\n").encode("utf-8")
    return submission, submission.encode("utf-8")


def _step_limit_reached(agent: Any, max_steps: int) -> bool | None:
    """Whether the call count hit the step limit. None if it cannot be told."""
    n_calls = getattr(agent, "n_calls", None)
    if not isinstance(n_calls, int) or max_steps <= 0:
        return None
    return n_calls >= max_steps


def _termination_for(
    exit_status: str, rate_limited: bool, *, step_limit_reached: bool | None = None
) -> Termination:
    if rate_limited:
        return Termination.RATE_LIMITED
    if exit_status == "LimitsExceeded":
        # One exception covers both budgets. The step check runs first in the
        # agent, so a run that did not reach the step limit hit the cost limit.
        return Termination.COST_LIMIT if step_limit_reached is False else Termination.STEP_LIMIT
    return {
        "Submitted": Termination.COMPLETED,
        "LimitsExceeded": Termination.STEP_LIMIT,
        "TimeExceeded": Termination.TIMEOUT,
    }.get(exit_status, Termination.ERROR)


def _sum_tokens(messages: list[dict[str, Any]], field_name: str) -> int:
    total = 0
    for message in messages:
        usage = (message.get("extra", {}).get("response", {}) or {}).get("usage") or {}
        if isinstance(usage, dict):
            total += int(usage.get(field_name) or 0)
    return total


def _commands_from(messages: list[dict[str, Any]]) -> tuple[str, ...]:
    commands = []
    for message in messages:
        for action in message.get("extra", {}).get("actions", []) or []:
            if isinstance(action, dict) and (cmd := action.get("command")):
                commands.append(cmd)
    return tuple(commands)


def _serialisable(message: dict[str, Any]) -> dict[str, Any]:
    """Round-trip a message through JSON, stringifying anything exotic."""
    return json.loads(json.dumps(message, default=str))


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
    claim_reason = claim.reason
    if claim.status is ClaimStatus.UNPARSEABLE and outcome.termination is not Termination.COMPLETED:
        # The run ended before it submitted. That is not a status stated badly.
        claim_reason = UnparseableReason.NEVER_FINISHED

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
            reason=claim_reason,
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
