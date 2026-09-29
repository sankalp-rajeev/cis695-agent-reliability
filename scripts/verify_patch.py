"""Run the verifier over a frozen patch and write a verification record.

Reads a task directory written by the agent runner, re-checks the patch against
the hash recorded at freeze time, runs whichever verifier layers are available,
and writes `verification_record.<config>.json` beside the repair record.

    .venv/bin/python scripts/verify_patch.py runs/<exp>/tasks/<instance_id>
    .venv/bin/python scripts/verify_patch.py <task_dir> --config baseline

Layers that cannot run in the current environment record `NOT_AVAILABLE` with a
reason, rather than being skipped. Running without `--container` is therefore a
legitimate, weaker verification whose weakness is visible in the record — which
is the point of attributing absences rather than merely noting them.

Count-agnostic and parallel-safe like the runner: it takes one task directory,
never a manifest or an instance count, and writes only inside that directory.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.agent.records import RepairRecord
from reliability.verifier.decision import SignalOutcome, get_policy
from reliability.verifier.evidence import (
    has_high_severity_risk,
    has_prohibited_manipulation,
    integrity_outcome,
    static_outcome,
)
from reliability.verifier.integrity import Violation, check_integrity
from reliability.verifier.patch import parse_patch
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
)
from reliability.verifier.selection import SelectionConfig, select_tests
from reliability.verifier.static_checks import StaticConfig, run_static_checks

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

#: V4 issue-derived reproduction tests. The layer exists in the schema and in
#: the decision policy; when it is built, this is the only line that changes.
REPRODUCTION_IMPLEMENTED = False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", help="a tasks/<instance_id>/ directory")
    parser.add_argument("--config", default="full", choices=["full", "baseline"])
    parser.add_argument("--container", action="store_true",
                        help="start the task container to run tests and static checks")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    started = time.monotonic()
    task_dir = pathlib.Path(args.task_dir).resolve()
    record = RepairRecord.read(task_dir / "repair_record.json")

    # Re-verify against the freeze-time hash. A verdict attributed to a patch
    # that changed afterwards is worse than no verdict, because it looks like
    # evidence.
    frozen = FrozenPatch(
        path=task_dir / "patch.diff",
        sha256=record.patch.sha256,
        size_bytes=record.patch.size_bytes,
    )
    patch_text = read_patch(frozen).decode("utf-8")
    print(f"patch verified: {record.patch.sha256[:23]}... "
          f"({record.patch.size_bytes} bytes)")

    container = tree = None
    try:
        if args.container:
            from reliability.verifier.container import (
                ContainerCommandExecutor,
                ContainerRepoTree,
                TaskContainer,
            )

            container = TaskContainer(
                instance_id=record.instance_id, patch_text=patch_text)
            container.start()
            tree = ContainerRepoTree(container)
            executor = ContainerCommandExecutor(container)
            print(f"container up: {container.name}")
        else:
            executor = None

        signals, extras = run_layers(patch_text, tree, executor)
    finally:
        if container is not None:
            container.stop()

    policy = get_policy(args.config)
    evidence = build_evidence_from(signals)
    produced = policy.decide(evidence)

    verification = VerificationRecord(
        instance_id=record.instance_id,
        experiment_id=record.experiment_id,
        verifier_config=args.config,
        patch_sha256=record.patch.sha256,
        integrity=signals[SignalKind.INTEGRITY],
        regression=signals[SignalKind.REGRESSION],
        static=signals[SignalKind.STATIC],
        reproduction=signals[SignalKind.REPRODUCTION],
        decision=DecisionEntry.from_record(produced),
        risk_features=extras["risk_features"],
        selected_tests=extras["selected_tests"],
        selection_convention=extras["selection_convention"],
        duration_s=time.monotonic() - started,
        verified_at=datetime.now(tz=UTC).isoformat(),
    )

    out = task_dir / f"verification_record.{args.config}.json"
    if out.exists():
        out.unlink()  # re-verification of the same config replaces its own record
    verification.write(out)

    report(verification)
    return 0


def run_layers(patch_text, tree, executor):
    """Run each layer, recording an attributed absence where one cannot run."""
    signals: dict[SignalKind, SignalRecord] = {}
    extras = {"risk_features": {}, "selected_tests": (), "selection_convention": ""}

    # -- V1 integrity. Always runs; it needs only the patch.
    integrity = check_integrity(patch_text)
    signals[SignalKind.INTEGRITY] = SignalRecord(
        kind=SignalKind.INTEGRITY,
        outcome=integrity_outcome(integrity),
        detail="; ".join(str(f) for f in integrity.findings) or "no violations",
        findings={
            "violations": [v.value for v in integrity.violations],
            "patch_applies": Violation.DOES_NOT_APPLY not in integrity.violations,
            "prohibited_manipulation": has_prohibited_manipulation(integrity),
            "high_severity_risk": has_high_severity_risk(integrity),
        },
    )
    extras["risk_features"] = integrity.risk.as_vector()

    patch = integrity.patch or (parse_patch(patch_text) if patch_text.strip() else None)

    # -- V2 regression and V3 static both need the repository.
    if tree is None or patch is None:
        absence, reason = (
            (SignalAbsence.DISABLED, "no repository available; run with --container")
            if patch is not None else
            (SignalAbsence.NOTHING_TO_CHECK, "patch is empty or unparseable")
        )
        for kind in (SignalKind.REGRESSION, SignalKind.STATIC):
            signals[kind] = SignalRecord.absent(kind, absence, reason)
    else:
        selection = select_tests(patch, tree, SelectionConfig())
        extras["selected_tests"] = selection.tests
        extras["selection_convention"] = selection.convention.convention.value

        signals[SignalKind.REGRESSION] = regression_signal(selection)
        static = run_static_checks(patch, tree, executor, StaticConfig())
        signals[SignalKind.STATIC] = SignalRecord(
            kind=SignalKind.STATIC,
            outcome=static_outcome(static),
            absence=(SignalAbsence.NOT_CONFIGURED
                     if static_outcome(static) is SignalOutcome.NOT_AVAILABLE else None),
            detail=f"{static.n_ran}/{static.n_available} checks ran",
            findings={"summary": static.summary,
                      "new_failures": [r.kind.value for r in static.new_failures]},
        )

    # -- V4 reproduction. Not built yet; the absence is attributed so records
    # written before it existed can be found and excluded once it lands.
    if REPRODUCTION_IMPLEMENTED:  # pragma: no cover - flipped when V4 ships
        raise NotImplementedError("wire the V4 layer here")
    signals[SignalKind.REPRODUCTION] = SignalRecord.absent(
        SignalKind.REPRODUCTION, SignalAbsence.NOT_IMPLEMENTED,
        "V4 issue-derived reproduction tests are not built yet",
    )

    return signals, extras


def regression_signal(selection) -> SignalRecord:
    """Selection runs without a test executor; execution does not.

    Distinguishing the two cases matters: "no tests match the changed files" is
    a fact about the repository, while "tests selected but not executed" is a
    fact about this invocation, and only the first would stay true under
    --container.
    """
    if not selection.tests:
        return SignalRecord.absent(
            SignalKind.REGRESSION, SignalAbsence.NOTHING_TO_CHECK,
            "selection found no tests for the changed files")
    return SignalRecord.absent(
        SignalKind.REGRESSION, SignalAbsence.DISABLED,
        f"{len(selection.tests)} tests selected but not executed in this pass")


def build_evidence_from(signals):
    from reliability.verifier.decision import Evidence

    integrity = signals[SignalKind.INTEGRITY]
    return Evidence(
        integrity=integrity.outcome,
        regression=signals[SignalKind.REGRESSION].outcome,
        static=signals[SignalKind.STATIC].outcome,
        reproduction=signals[SignalKind.REPRODUCTION].outcome,
        high_severity_risk=bool(integrity.findings.get("high_severity_risk")),
        prohibited_manipulation=bool(integrity.findings.get("prohibited_manipulation")),
        patch_applies=bool(integrity.findings.get("patch_applies", True)),
    )


def report(record: VerificationRecord) -> None:
    print(f"\n=== verification: {record.instance_id} [{record.verifier_config}] ===")
    for kind, signal in record.signals.items():
        suffix = f" ({signal.absence.value})" if signal.absence else ""
        print(f"  {kind.value:<13}: {signal.outcome.value}{suffix}  {signal.detail}")
    print(f"  decision     : {record.decision.decision.value} "
          f"[{record.decision.policy_version}]")
    for reason in record.decision.reasons:
        print(f"                 - {reason}")
    print(f"  complete     : {record.is_complete} "
          f"({len(record.signals_reported)}/4 layers reported)")


if __name__ == "__main__":
    raise SystemExit(main())
