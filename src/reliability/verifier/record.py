"""The verification record: what the verifier concluded, and on what (Phase 7.3).

One record per task per verifier configuration, written beside the repair
record in that task's own run directory. The repair record is the agent's
account of what it produced; this is the verifier's account of what it found.
They stay separate files for the same reason the oracle verdict does — nothing
downstream should be able to read a verdict out of the agent's own account.

Three properties this schema is built to guarantee:

**A signal is never silently missing.** Every signal the verifier knows about
occupies a field, and every field is required. A layer that did not run records
`NOT_AVAILABLE` together with *why*, rather than being omitted from the record
or defaulted to something benign. Omission is the failure mode that matters
here: a record missing its `static` key and a record whose static checks all
passed are indistinguishable to a naive reader, and only one of them is
evidence.

**Absence is attributed, not just noted.** `SignalAbsence` separates "this layer
is not built yet" from "this repository configures no type checker" from "the
run timed out". These have the same effect on the decision — none of them is a
pass — but entirely different meanings in an analysis, and they are impossible
to tell apart after the fact if all three collapse to a bare `NOT_AVAILABLE`.
The distinction is what lets records written before a layer existed be found and
excluded later, rather than quietly diluting a coverage number.

**The verdict is bound to a specific patch.** `patch_sha256` is recorded and
must match the repair record's, so a verification can never be attributed to a
patch that changed after the agent froze it.

The record carries no oracle field. `extra="forbid"` makes an accidental one a
validation error rather than a silent extra key, and
`test_record_cannot_carry_oracle_fields` asserts it directly.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from reliability.verifier.decision import Decision, DecisionRecord, Evidence, SignalOutcome


class SignalKind(str, Enum):
    """The verifier layers, V1 through V4 of the technical design."""

    INTEGRITY = "integrity"        # V1, Phase 4
    REGRESSION = "regression"      # V2, Phase 5
    STATIC = "static"              # V3, Phase 6
    REPRODUCTION = "reproduction"  # V4, issue-derived tests


class SignalAbsence(str, Enum):
    """Why a signal did not report.

    Recorded whenever the outcome is `NOT_AVAILABLE`. All of these are equally
    "not a pass" to the decision policy, but they mean different things to an
    analysis, and collapsing them would make the difference unrecoverable.
    """

    NOT_IMPLEMENTED = "not_implemented"  # the layer does not exist yet
    NOT_CONFIGURED = "not_configured"    # the repo provides no such tooling
    DISABLED = "disabled"                # switched off in this configuration
    NOTHING_TO_CHECK = "nothing_to_check"  # ran, found nothing applicable
    ERROR = "error"                      # the layer itself broke
    TIMEOUT = "timeout"


class SignalRecord(BaseModel):
    """One layer's finding, with enough context to audit it.

    `detail` is required to be non-empty when the outcome is `NOT_AVAILABLE`:
    an unexplained absence is exactly the thing this record exists to prevent.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: SignalKind
    outcome: SignalOutcome
    absence: SignalAbsence | None = None
    detail: str = ""
    duration_s: float = Field(default=0.0, ge=0.0)

    #: Layer-specific findings, kept as an opaque mapping so a signal can record
    #: what it needs without this schema having to know every layer's internals.
    findings: dict[str, Any] = Field(default_factory=dict)

    @property
    def reported(self) -> bool:
        """Whether this layer actually produced evidence."""
        return self.outcome is not SignalOutcome.NOT_AVAILABLE

    @model_validator(mode="after")
    def _absence_is_explained(self) -> SignalRecord:
        if self.outcome is SignalOutcome.NOT_AVAILABLE:
            if self.absence is None:
                raise ValueError(
                    f"{self.kind.value} is NOT_AVAILABLE with no absence reason; "
                    "an unattributed absence cannot be interpreted later"
                )
        elif self.absence is not None:
            raise ValueError(
                f"{self.kind.value} reported {self.outcome.value} but also carries "
                f"absence={self.absence.value}"
            )
        return self

    @classmethod
    def absent(
        cls, kind: SignalKind, absence: SignalAbsence, detail: str
    ) -> SignalRecord:
        return cls(
            kind=kind, outcome=SignalOutcome.NOT_AVAILABLE,
            absence=absence, detail=detail,
        )


class DecisionEntry(BaseModel):
    """The policy's verdict, exactly as the policy produced it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: Decision
    policy_name: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    reasons: tuple[str, ...] = Field(min_length=1)

    @field_validator("reasons")
    @classmethod
    def _reasons_are_substantive(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(not r.strip() for r in v):
            raise ValueError("a blank reason is not a reason")
        return v

    @classmethod
    def from_record(cls, record: DecisionRecord) -> DecisionEntry:
        return cls(
            decision=record.decision,
            policy_name=record.policy_name,
            policy_version=record.policy_version,
            reasons=record.reasons,
        )


class VerificationRecord(BaseModel):
    """Everything the verifier concluded about one frozen patch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identity. `verifier_config` names which configuration produced this, since
    # the same patch is verified under both `full` and `baseline`.
    instance_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    verifier_config: str = Field(min_length=1)

    # Binding to the artifact judged. A verdict against a patch that has since
    # changed is worse than no verdict, because it looks like evidence.
    patch_sha256: str = Field(min_length=1)

    # Signals. All four are required fields; a layer that did not run says so.
    integrity: SignalRecord
    regression: SignalRecord
    static: SignalRecord
    reproduction: SignalRecord

    decision: DecisionEntry

    #: Phase 4.2 measurements, recorded beside the decision rather than inside
    #: it. Kept so the risk-coverage analysis has the features per instance.
    risk_features: dict[str, Any] = Field(default_factory=dict)

    #: Which tests the regression layer chose, and by what convention. Recorded
    #: so the selection is auditable and so Phase 5.3 can compute overlap with
    #: PASS_TO_PASS after the fact — the only point at which the two may meet.
    selected_tests: tuple[str, ...] = ()
    selection_convention: str = ""
    #: The winner's hit rate over the sampled source files, and every probed
    #: layout's. Discovery has no floor, so a weak winner is visible only here.
    selection_convention_hit_rate: float | None = None
    selection_convention_scores: dict[str, float] = Field(default_factory=dict)
    #: Which program runs those node ids, and the evidence for that choice.
    selection_runner: str = ""

    duration_s: float = Field(default=0.0, ge=0.0)
    verified_at: str = Field(min_length=1)

    @field_validator("patch_sha256")
    @classmethod
    def _looks_like_a_digest(cls, v: str) -> str:
        if not v.startswith("sha256:") or len(v) != len("sha256:") + 64:
            raise ValueError(f"not a sha256 digest: {v!r}")
        return v

    @model_validator(mode="after")
    def _signals_match_their_slots(self) -> VerificationRecord:
        """A regression report filed under `static` would be invisible otherwise."""
        for name, kind in (
            ("integrity", SignalKind.INTEGRITY),
            ("regression", SignalKind.REGRESSION),
            ("static", SignalKind.STATIC),
            ("reproduction", SignalKind.REPRODUCTION),
        ):
            signal: SignalRecord = getattr(self, name)
            if signal.kind is not kind:
                raise ValueError(
                    f"field {name!r} holds a {signal.kind.value} signal"
                )
        return self

    # -- reading ------------------------------------------------------------

    @property
    def signals(self) -> dict[SignalKind, SignalRecord]:
        return {s.kind: s for s in
                (self.integrity, self.regression, self.static, self.reproduction)}

    @property
    def signals_reported(self) -> tuple[SignalKind, ...]:
        return tuple(k for k, s in self.signals.items() if s.reported)

    @property
    def signals_absent(self) -> tuple[SignalKind, ...]:
        return tuple(k for k, s in self.signals.items() if not s.reported)

    @property
    def is_complete(self) -> bool:
        """Whether every layer reported.

        Deliberately not a pass/fail property. An incomplete verification is a
        weaker verification, and the analysis needs to be able to say so per
        instance rather than discovering it in aggregate.
        """
        return not self.signals_absent

    def absent_because(self, absence: SignalAbsence) -> tuple[SignalKind, ...]:
        """Which layers were absent for a given reason.

        The query that makes `SignalAbsence` worth recording: records written
        before a layer existed can be found and excluded, instead of being
        averaged in with runs where the layer genuinely had nothing to check.
        """
        return tuple(k for k, s in self.signals.items() if s.absence is absence)

    # -- writing ------------------------------------------------------------

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def write(self, path: Path) -> Path:
        """Refuses to overwrite: one verification, one record."""
        if path.exists():
            raise FileExistsError(f"refusing to overwrite an existing record: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: Path) -> VerificationRecord:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def validate_dict(cls, payload: dict[str, Any]) -> VerificationRecord:
        return cls.model_validate(payload)


def evidence_from_record(record: VerificationRecord) -> Evidence:
    """Rebuild the policy's input from a stored record.

    Lets a second policy be applied to an existing record without re-running any
    layer, which is how the baseline-versus-full comparison is computed over a
    finished study rather than by verifying everything twice.
    """
    return Evidence(
        integrity=record.integrity.outcome,
        regression=record.regression.outcome,
        static=record.static.outcome,
        reproduction=record.reproduction.outcome,
        high_severity_risk=bool(record.integrity.findings.get("high_severity_risk")),
        prohibited_manipulation=bool(
            record.integrity.findings.get("prohibited_manipulation")),
        patch_applies=bool(record.integrity.findings.get("patch_applies", True)),
    )


def load_records(run_dir: Path, config: str = "*") -> list[VerificationRecord]:
    """Load every verification record under a run directory.

    Per-task files rather than a shared aggregate, so concurrent verifications
    never contend for one file.
    """
    pattern = f"tasks/*/verification_record.{config}.json"
    return [VerificationRecord.read(p) for p in sorted(run_dir.glob(pattern))]


def summarise(records: list[VerificationRecord]) -> dict[str, Any]:
    """Counts for the Phase 9 and 10 tables.

    `n_complete` is reported alongside the decision counts on purpose: a table
    of ACCEPT/FLAG/REJECT with no indication of how many layers actually ran
    would overstate what the verifier demonstrated.
    """
    absences: dict[str, int] = {}
    for record in records:
        for kind in record.signals_absent:
            key = f"{kind.value}:{record.signals[kind].absence.value}"
            absences[key] = absences.get(key, 0) + 1

    return {
        "n": len(records),
        "n_complete": sum(r.is_complete for r in records),
        "decisions": {
            d.value: sum(r.decision.decision is d for r in records) for d in Decision
        },
        "signals_absent": dict(sorted(absences.items())),
        "policy_versions": sorted({r.decision.policy_version for r in records}),
    }


__all__ = [
    "DecisionEntry",
    "SignalAbsence",
    "SignalKind",
    "SignalRecord",
    "VerificationRecord",
    "evidence_from_record",
    "load_records",
    "summarise",
]
