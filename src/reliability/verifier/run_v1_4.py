"""Opt-in v1.4 runner; use scripts/verify_patch_v1_4.py.

The V2 selection, execution, configuration and adapters are reused unchanged.
Existing entry points and records remain isolated from the new signal versions.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.agent.records import RepairRecord
from reliability.benchmark.loader import load_agent_task
from reliability.verifier.container import (
    ContainerCommandExecutor,
    ContainerError,
    ContainerRepoTree,
    ContainerTestExecutor,
    TaskContainer,
)
from reliability.verifier.evidence import (
    has_high_severity_risk,
    has_prohibited_manipulation,
    integrity_outcome,
)
from reliability.verifier.integrity import Violation
from reliability.verifier.patch import parse_patch
from reliability.verifier.policy_v1_4 import get_policy
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
)
from reliability.verifier.regression import (
    RegressionConfig,
    Signal,
    run_regression,
)
from reliability.verifier.reproduction_freeze import (
    ReproductionSetup,
    ReproGenerator,
)
from reliability.verifier.run import (
    signal_from_regression,
)
from reliability.verifier.selection import SelectionConfig, select_tests

REPO_ROOT = Path(__file__).resolve().parents[3]


def default_reproduction_setup() -> ReproductionSetup:
    return ReproductionSetup.load(
        verifier_config=REPO_ROOT / "configs/verifier/full_v1_4.yaml",
        repo_root=REPO_ROOT,
    )


def verify_task(
    task_dir: Path,
    *,
    configs: tuple[str, ...] = ("full-v1.4",),
    use_container: bool = True,
    replace: bool = False,
    reproduction: ReproductionSetup | None = None,
    generator: ReproGenerator | None = None,
) -> list[VerificationRecord]:
    """Verify a frozen patch under v1.4 and write a separate versioned record."""
    if not configs or any(name not in ("full-v1.4", "v1.4.0-full") for name in configs):
        raise ValueError("v1.4 entry point requires full-v1.4")
    setup = default_reproduction_setup()
    if reproduction is not None and reproduction != setup:
        raise ValueError("v1.4 requires its frozen reproduction setup")
    task_dir = Path(task_dir).resolve()
    record = RepairRecord.read(task_dir / "repair_record.json")
    frozen = FrozenPatch(
        path=task_dir / "patch.diff",
        sha256=record.patch.sha256,
        size_bytes=record.patch.size_bytes,
    )
    patch_text = read_patch(frozen).decode("utf-8")
    started = time.monotonic()

    container = tree = command_executor = test_executor = None
    try:
        if use_container:
            container = TaskContainer(
                instance_id=record.instance_id,
                patch_text=patch_text,
                experiment_id=record.experiment_id,
            )
            container.start()
            tree = ContainerRepoTree(container)
            command_executor = ContainerCommandExecutor(container)
            test_executor = ContainerTestExecutor(container, evidence_dir=task_dir / "v2_evidence")
        signals, extras = run_layers(
            patch_text,
            tree,
            command_executor,
            test_executor,
            instance_id=record.instance_id,
            baseline_cache_dir=task_dir.parent.parent / "_baseline_cache",
        )
    except ContainerError as exc:
        signals, extras = run_layers(
            patch_text,
            tree=None,
            command_executor=None,
            test_executor=None,
            instance_id=record.instance_id,
        )
        for kind in (SignalKind.REGRESSION, SignalKind.STATIC):
            signals[kind] = SignalRecord.absent(
                kind, SignalAbsence.ERROR, f"container failed: {str(exc)[:300]}"
            )
    finally:
        if container is not None:
            container.stop()

    from reliability.verifier.reproduction_v1_4 import run_reproduction as reproduction_runner

    signals[SignalKind.REPRODUCTION] = reproduction_runner(
        record.instance_id,
        patch_text,
        setup,
        use_container=use_container,
        patch_applies=bool(signals[SignalKind.INTEGRITY].findings.get("patch_applies", True)),
        cache_dir=task_dir.parent.parent / "_reproduction_cache_v1_4",
        generator=generator,
        experiment_id=record.experiment_id,
    )

    from reliability.verifier.policy_v1_4 import evidence_from_signals

    evidence = evidence_from_signals(signals)
    written: list[VerificationRecord] = []
    for name in configs:
        policy = get_policy(name)
        produced = policy.decide(evidence)
        verification = VerificationRecord(
            instance_id=record.instance_id,
            experiment_id=record.experiment_id,
            verifier_config=name,
            patch_sha256=record.patch.sha256,
            integrity=signals[SignalKind.INTEGRITY],
            regression=signals[SignalKind.REGRESSION],
            static=signals[SignalKind.STATIC],
            reproduction=signals[SignalKind.REPRODUCTION],
            decision=DecisionEntry.from_record(produced),
            risk_features=extras["risk_features"],
            selected_tests=extras["selected_tests"],
            selection_convention=extras["selection_convention"],
            selection_convention_hit_rate=extras["selection_convention_hit_rate"],
            selection_convention_scores=extras["selection_convention_scores"],
            selection_runner=extras["selection_runner"],
            reproduction_generator=setup.identity(),
            duration_s=time.monotonic() - started,
            verified_at=datetime.now(tz=UTC).isoformat(),
        )
        out = task_dir / f"verification_record.{name}.json"
        if out.exists():
            if not replace:
                written.append(VerificationRecord.read(out))
                continue
            out.unlink()
        verification.write(out)
        written.append(verification)
    return written


def run_layers(
    patch_text: str,
    tree,
    command_executor,
    test_executor,
    *,
    instance_id: str,
    baseline_cache_dir: Path | None = None,
    issue_text: str | None = None,
) -> tuple[dict[SignalKind, SignalRecord], dict]:
    """Run each layer, recording an attributed absence where one cannot run."""
    signals: dict[SignalKind, SignalRecord] = {}
    extras: dict = {
        "risk_features": {},
        "selected_tests": (),
        "selection_convention": "",
        "selection_convention_hit_rate": None,
        "selection_convention_scores": {},
        "selection_runner": "",
    }

    from reliability.verifier.integrity_v1_4 import check_integrity as check_v14

    integrity = check_v14(patch_text, tree=tree)
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
    signals[SignalKind.INTEGRITY].findings["ast_analysis"] = list(integrity.analysis)
    extras["risk_features"] = integrity.risk.as_vector()

    patch = integrity.patch or (parse_patch(patch_text) if patch_text.strip() else None)

    if tree is None or patch is None:
        absence, reason = (
            (SignalAbsence.DISABLED, "no repository available; run with --container")
            if patch is not None
            else (SignalAbsence.NOTHING_TO_CHECK, "patch is empty or unparseable")
        )
        for kind in (SignalKind.REGRESSION, SignalKind.STATIC):
            signals[kind] = SignalRecord.absent(kind, absence, reason)
    else:
        selection = select_tests(patch, tree, SelectionConfig())
        extras["selected_tests"] = selection.tests
        extras["selection_convention"] = (
            selection.convention.convention.value if selection.convention else ""
        )
        if selection.convention is not None:
            extras["selection_convention_hit_rate"] = round(selection.convention.hit_rate, 4)
            extras["selection_convention_scores"] = dict(selection.convention.scores)
        extras["selection_runner"] = (
            f"{selection.runner.name}: {selection.runner.evidence}" if selection.runner else ""
        )
        if test_executor is not None and hasattr(test_executor, "runner"):
            test_executor.runner = selection.runner

        if test_executor is None:
            signals[SignalKind.REGRESSION] = (
                SignalRecord.absent(
                    SignalKind.REGRESSION,
                    SignalAbsence.NOTHING_TO_CHECK,
                    "selection found no tests for the changed files",
                )
                if not selection.tests
                else SignalRecord.absent(
                    SignalKind.REGRESSION,
                    SignalAbsence.DISABLED,
                    f"{len(selection.tests)} tests selected but not executed",
                )
            )
        else:
            report = run_regression(
                instance_id,
                selection,
                test_executor,
                RegressionConfig(baseline_cache_dir=baseline_cache_dir),
            )
            signals[SignalKind.REGRESSION] = signal_from_regression(report)
            # Shadow only: no change to report.signal, evidence or decisions.
            from reliability.verifier.superseded_shadow_v2 import shadow_from_report

            try:
                if (
                    issue_text is None
                    and report.signal is Signal.FAIL
                    and isinstance(test_executor, ContainerTestExecutor)
                ):
                    issue_text = load_agent_task(instance_id).problem_statement
                shadow = shadow_from_report(report, issue_text, patch_text, tree, test_executor)
            except Exception as exc:  # noqa: BLE001 - shadow cannot change decisions
                shadow = {
                    "prediction": "UNCERTAIN",
                    "shadow_mode": True,
                    "suggest_suppress_v2_negative": False,
                    "reason": f"Shadow unavailable: {type(exc).__name__}: {exc}"[:400],
                }
            signals[SignalKind.REGRESSION].findings["superseded_shadow"] = shadow

        if command_executor is None:
            signals[SignalKind.STATIC] = SignalRecord.absent(
                SignalKind.STATIC,
                SignalAbsence.DISABLED,
                "no command executor; run with --container",
            )
        else:
            from reliability.verifier.static_v1_4 import ContainerEvidenceExecutor
            from reliability.verifier.static_v1_4 import run_static_checks as static_v14

            executor = (
                ContainerEvidenceExecutor(command_executor.container)
                if isinstance(command_executor, ContainerCommandExecutor)
                else command_executor
            )
            signals[SignalKind.STATIC] = static_v14(patch, tree, executor)

    # V4 runs in its own containers, from verify_task; see run_reproduction.
    signals[SignalKind.REPRODUCTION] = SignalRecord.absent(
        SignalKind.REPRODUCTION,
        SignalAbsence.DISABLED,
        "reproduction is run by verify_task, not by run_layers",
    )
    return signals, extras
