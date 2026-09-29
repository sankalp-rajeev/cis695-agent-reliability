"""The oracle record: what SWE-bench found (Phase 8.2).

One record per task, written beside the repair and verification records. It is
kept in its own file for the same reason those two are: nothing downstream
should be able to read a resolution status out of the agent's own account of its
work, or out of the verifier's.

**The central distinction: an infrastructure error is not an unresolved patch.**
A container that failed to build, an image that would not pull, a harness that
crashed — none of these are findings about the patch, and every one of them
produces the same surface appearance as a patch that simply did not work. If the
two are folded together, the resolution rate is quietly biased downward by
however often the environment misbehaved, and the bias is invisible because the
failures look identical in aggregate.

So `resolved` is `bool | None`, and it is `None` exactly when the harness did not
reach a verdict. There is no value of `resolved` that can be read as "no" when
the truth is "we do not know" — the same reasoning that makes `NOT_RUN` an
outcome in Phase 5 rather than a silent zero, applied to the oracle.
`summarise()` reports `n_resolved`, `n_unresolved` and `n_infrastructure_error`
as three separate counts and never sums the last two.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OracleOutcome(str, Enum):
    """What the harness concluded.

    `INFRA_ERROR` and `EMPTY_PATCH` are separated from `UNRESOLVED` because
    neither is evidence about the repair. An empty patch is a fact about the
    agent — it produced nothing — while an infrastructure error is a fact about
    the environment, and only `UNRESOLVED` is a fact about the patch.
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    INFRA_ERROR = "infra_error"
    EMPTY_PATCH = "empty_patch"
    PATCH_APPLY_FAILED = "patch_apply_failed"
    NOT_RUN = "not_run"

    @property
    def is_a_finding_about_the_patch(self) -> bool:
        """Whether this outcome may be counted in a resolution rate."""
        return self in (
            OracleOutcome.RESOLVED,
            OracleOutcome.UNRESOLVED,
            OracleOutcome.PATCH_APPLY_FAILED,
        )


class TestSuiteResult(BaseModel):
    """One of the harness's two test groups, as it reported them.

    Names are kept, not just counts. Phase 5.3 needs the `PASS_TO_PASS` names to
    compute overlap with the verifier's independently chosen set — which is the
    single point in the pipeline where selection and oracle data are allowed to
    meet, and only after both are already fixed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    success: tuple[str, ...] = ()
    failure: tuple[str, ...] = ()

    @property
    def n_total(self) -> int:
        return len(self.success) + len(self.failure)

    @property
    def all_passed(self) -> bool:
        """True only if tests ran and none failed.

        An empty suite is not "all passed": no test executed, so nothing was
        demonstrated. Same rule as `NOT_RUN` in Phase 5.
        """
        return self.n_total > 0 and not self.failure


class OracleRecord(BaseModel):
    """SWE-bench's verdict on one frozen patch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instance_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)

    # Binds the verdict to the exact artifact judged, so it can never be
    # attributed to a patch that changed after the agent froze it.
    patch_sha256: str = Field(min_length=1)

    outcome: OracleOutcome

    #: None exactly when the harness reached no verdict. Never False in that case.
    resolved: bool | None = None

    fail_to_pass: TestSuiteResult = Field(default_factory=TestSuiteResult)
    pass_to_pass: TestSuiteResult = Field(default_factory=TestSuiteResult)

    #: Recorded separately from `outcome` so the flag is greppable and cannot be
    #: lost if the outcome vocabulary is ever extended.
    infrastructure_error: bool = False
    error_detail: str = ""

    patch_applied: bool | None = None
    harness_exit_code: int | None = None
    harness_run_id: str = ""
    report_file: str = ""

    duration_s: float = Field(default=0.0, ge=0.0)
    evaluated_at: str = Field(min_length=1)

    @model_validator(mode="after")
    def _resolved_agrees_with_outcome(self) -> OracleRecord:
        """The invariant this schema exists to hold.

        Without it, nothing stops a record saying `resolved: false` when the
        harness in fact crashed — which is precisely the conflation that biases
        the resolution rate downward.
        """
        if self.outcome is OracleOutcome.RESOLVED and self.resolved is not True:
            raise ValueError("outcome is RESOLVED but resolved is not True")
        if self.outcome is OracleOutcome.UNRESOLVED and self.resolved is not False:
            raise ValueError("outcome is UNRESOLVED but resolved is not False")
        if not self.outcome.is_a_finding_about_the_patch and self.resolved is not None:
            raise ValueError(
                f"outcome {self.outcome.value} reached no verdict, so resolved "
                f"must be None, not {self.resolved!r} — an infrastructure error "
                "is not an unresolved patch"
            )
        if (self.outcome is OracleOutcome.INFRA_ERROR) != self.infrastructure_error:
            raise ValueError(
                "outcome INFRA_ERROR and infrastructure_error must agree")
        return self

    @property
    def counts_toward_resolution_rate(self) -> bool:
        return self.outcome.is_a_finding_about_the_patch

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def write(self, path: Path) -> Path:
        """Refuses to overwrite: one evaluation, one record."""
        if path.exists():
            raise FileExistsError(f"refusing to overwrite an existing record: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: Path) -> OracleRecord:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def validate_dict(cls, payload: dict[str, Any]) -> OracleRecord:
        return cls.model_validate(payload)


def outcome_from_report(report: dict[str, Any]) -> OracleOutcome:
    """Classify one instance's harness report.

    Order matters: infrastructure failure is checked before resolution, because
    a crashed run can still carry a stale or partial `resolved: false` and must
    not be read as a verdict.
    """
    if report.get("infra_failure"):
        return OracleOutcome.INFRA_ERROR
    if report.get("patch_is_None") or not report.get("patch_exists", True):
        return OracleOutcome.EMPTY_PATCH
    if not report.get("patch_successfully_applied", True):
        return OracleOutcome.PATCH_APPLY_FAILED
    return (OracleOutcome.RESOLVED if report.get("resolved")
            else OracleOutcome.UNRESOLVED)


def _suite(report: dict[str, Any], key: str) -> TestSuiteResult:
    status = (report.get("tests_status") or {}).get(key) or {}
    return TestSuiteResult(
        success=tuple(status.get("success", ())),
        failure=tuple(status.get("failure", ())),
    )


def record_from_report(
    report: dict[str, Any],
    *,
    instance_id: str,
    experiment_id: str,
    patch_sha256: str,
    evaluated_at: str,
    **extra: Any,
) -> OracleRecord:
    """Build a record from the harness's per-instance report.

    The single place harness output is interpreted, so the mapping from its
    vocabulary to ours is auditable by reading one function.
    """
    outcome = outcome_from_report(report)
    resolved = (
        outcome is OracleOutcome.RESOLVED
        if outcome.is_a_finding_about_the_patch else None
    )

    return OracleRecord(
        instance_id=instance_id,
        experiment_id=experiment_id,
        patch_sha256=patch_sha256,
        outcome=outcome,
        resolved=resolved,
        fail_to_pass=_suite(report, "FAIL_TO_PASS"),
        pass_to_pass=_suite(report, "PASS_TO_PASS"),
        infrastructure_error=outcome is OracleOutcome.INFRA_ERROR,
        patch_applied=report.get("patch_successfully_applied"),
        evaluated_at=evaluated_at,
        **extra,
    )


def load_records(run_dir: Path) -> list[OracleRecord]:
    """Load every oracle record under a run directory."""
    return [OracleRecord.read(p)
            for p in sorted(run_dir.glob("tasks/*/oracle_record.json"))]


def summarise(records: list[OracleRecord]) -> dict[str, Any]:
    """Counts for the Phase 9 and 10 tables.

    `n_infrastructure_error` is reported on its own and is never added to
    `n_unresolved`. `resolution_rate` is computed over evaluated instances only,
    with `n_not_evaluated` alongside it so the denominator is never mistaken for
    the whole manifest.
    """
    evaluated = [r for r in records if r.counts_toward_resolution_rate]
    n_resolved = sum(r.resolved is True for r in evaluated)

    return {
        "n": len(records),
        "n_evaluated": len(evaluated),
        "n_not_evaluated": len(records) - len(evaluated),
        "n_resolved": n_resolved,
        "n_unresolved": sum(r.resolved is False for r in evaluated),
        "n_infrastructure_error": sum(r.infrastructure_error for r in records),
        "n_empty_patch": sum(
            r.outcome is OracleOutcome.EMPTY_PATCH for r in records),
        "resolution_rate": (
            round(n_resolved / len(evaluated), 4) if evaluated else None),
        "outcomes": {
            o.value: sum(r.outcome is o for r in records) for o in OracleOutcome
        },
    }


__all__ = [
    "OracleOutcome",
    "OracleRecord",
    "TestSuiteResult",
    "load_records",
    "outcome_from_report",
    "record_from_report",
    "summarise",
]
