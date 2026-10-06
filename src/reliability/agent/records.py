"""The repair record: what one agent run produced (Phase 3.3).

One record per task, written to that task's own run directory. It is the only
account of what the agent did, so it must be complete enough to reconstruct the
run without the trajectory, and validated strictly enough that a missing cost or
an absent claim cannot pass as zero.

`extra="forbid"` and required fields throughout: a renamed field that silently
lost its value is the failure this guards against, which is the same reason
`provenance.validate()` rejects unexpected keys.

Two fields exist to prevent category errors in the written report:

- `run_role` separates smoke tests from pilot and main-study data. The Phase 3.1
  end-to-end smoke run happens on whatever model is cheapest and is *not* pilot
  data; without an explicit marker on every record, its numbers would eventually
  be cited as pilot results. There is no default - a caller must say which.
- `termination` distinguishes a clean finish from a timeout or a crash. An agent
  killed at its step limit has not claimed UNRESOLVED, and collapsing those two
  would corrupt the claim-capture rate that Phase 9.3 gates on.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from reliability.agent.claim_parser import ClaimStatus, UnparseableReason


class RunRole(str, Enum):
    """What a run's numbers may be used for."""

    SMOKE = "smoke"    # pipeline proving only; never cited as a result
    PILOT = "pilot"    # the 10-task pilot
    MAIN = "main"      # the frozen main study


class Termination(str, Enum):
    """How the agent's run ended.

    `RATE_LIMITED` is deliberately separate from `ERROR`. The agent loop makes
    many calls per instance and throttled tiers will exhaust the scaffold's retry
    budget, producing a truncated trajectory that looks exactly like an agent
    that gave up. That is a throughput result about the API quota, not a finding
    about the model's repair ability or a scaffold/model mismatch, and folding it
    into `ERROR` would license exactly that misreading.

    `INSUFFICIENT_BALANCE` is separate again, from both `ERROR` and
    `RATE_LIMITED`. The provider's own account ran out of funds mid-call (DeepSeek
    returns HTTP 402, body `"Insufficient Balance"`) — a billing state, not a
    throughput limit and not a finding about the model or the repair. Folding it
    into `RATE_LIMITED` would misreport a run that cannot be retried by waiting as
    one that can; folding it into `ERROR` would misreport a billing failure as an
    agent or scaffold failure. The pre-run billing guard (`src/reliability/
    billing.py`, called from `scripts/run_pilot.py` before any task starts) exists
    to make this outcome rare; this value is for the case it still happens
    mid-run (the balance was adequate at the guard check and was spent by
    concurrent or prior tasks before this one's call went out).

    `STEP_LIMIT` and `COST_LIMIT` are separate from each other and from
    `COMPLETED`. A run stopped by its budget never reached submission, so it has
    no final status to parse; counting it as a badly formatted status would send
    the fix to the wrong place (a parser, rather than a budget or a scaffold fit).
    mini-SWE-agent raises one exception for both budgets, so the runner tells
    them apart from the call count.
    """

    COMPLETED = "completed"
    STEP_LIMIT = "step_limit"
    COST_LIMIT = "cost_limit"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    ERROR = "error"


class ClaimRecord(BaseModel):
    """The parsed final claim, stored verbatim alongside its interpretation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ClaimStatus
    evidence: str | None = None
    reason: UnparseableReason | None = None
    raw_output: str = ""

    @property
    def is_parseable(self) -> bool:
        return self.status is not ClaimStatus.UNPARSEABLE


class PatchRecord(BaseModel):
    """Identity of the frozen patch this run produced."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    sha256: str
    size_bytes: int = Field(ge=0)

    @property
    def is_empty(self) -> bool:
        return self.size_bytes == 0

    @field_validator("sha256")
    @classmethod
    def _looks_like_a_digest(cls, v: str) -> str:
        if not v.startswith("sha256:") or len(v) != len("sha256:") + 64:
            raise ValueError(f"not a sha256 digest: {v!r}")
        return v


class UsageRecord(BaseModel):
    """Token and cost accounting.

    Required rather than optional: an unrecorded cost is not a zero cost, and
    Phase 10.2 extrapolates the main-study budget from exactly these numbers.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    api_cost_usd: float = Field(ge=0.0)

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out


class RepairRecord(BaseModel):
    """Everything one agent run produced, for one task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identity
    instance_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    run_role: RunRole
    manifest_hash: str = Field(min_length=1)

    # Apparatus
    agent_scaffold: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)
    model_id: str = Field(min_length=1)

    # Outputs
    patch: PatchRecord
    trajectory_path: str = Field(min_length=1)
    commands_run: tuple[str, ...] = ()
    tests_run: tuple[str, ...] = ()
    claim: ClaimRecord

    # Execution
    termination: Termination
    duration_s: float = Field(ge=0.0)
    usage: UsageRecord

    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)

    @property
    def is_citable_as_result(self) -> bool:
        """Smoke runs prove the pipeline; they are never evidence about models."""
        return self.run_role is not RunRole.SMOKE

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def write(self, path: Path) -> Path:
        """Write this record to its task directory.

        Refuses to overwrite: one run, one record. A rerun belongs in a new run
        directory rather than on top of the previous account of what happened.
        """
        if path.exists():
            raise FileExistsError(f"refusing to overwrite an existing record: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: Path) -> RepairRecord:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def validate_dict(cls, payload: dict[str, Any]) -> RepairRecord:
        return cls.model_validate(payload)


def load_records(run_dir: Path) -> list[RepairRecord]:
    """Load every repair record under a run directory.

    Reads per-task files rather than a shared aggregate, which is what keeps
    concurrent runs from contending for a single file.
    """
    records = []
    for path in sorted(run_dir.glob("tasks/*/repair_record.json")):
        records.append(RepairRecord.read(path))
    return records


def summarise(records: list[RepairRecord]) -> dict[str, Any]:
    """Counts used by the Phase 9 gates. Computed from disk, no model calls.

    An unparseable claim is split by cause. `never_finished` is a run that did
    not reach submission (budget, timeout, throttling, error), so there was
    nothing to parse. `unparseable_after_finishing` is a run that did submit and
    stated its status badly. They are fixed differently and are reported apart.
    """
    never_finished = [
        r for r in records
        if r.claim.reason is UnparseableReason.NEVER_FINISHED
    ]
    terminations: dict[str, int] = {}
    for r in records:
        terminations[r.termination.value] = terminations.get(r.termination.value, 0) + 1
    return {
        "n": len(records),
        "terminations": dict(sorted(terminations.items())),
        "never_finished": len(never_finished),
        "never_finished_by_termination": dict(sorted(
            _count(r.termination.value for r in never_finished).items())),
        "unparseable_after_finishing": sum(
            not r.claim.is_parseable
            and r.claim.reason is not UnparseableReason.NEVER_FINISHED
            for r in records),
        "parseable_claims": sum(r.claim.is_parseable for r in records),
        "resolved_claims": sum(r.claim.status is ClaimStatus.RESOLVED for r in records),
        "empty_patches": sum(r.patch.is_empty for r in records),
        "completed": sum(r.termination is Termination.COMPLETED for r in records),
        "total_cost_usd": round(sum(r.usage.api_cost_usd for r in records), 4),
        "total_tokens": sum(r.usage.total_tokens for r in records),
        "roles": sorted({r.run_role.value for r in records}),
    }


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return counts


__all__ = [
    "ClaimRecord",
    "PatchRecord",
    "RepairRecord",
    "RunRole",
    "Termination",
    "UsageRecord",
    "load_records",
    "summarise",
]
