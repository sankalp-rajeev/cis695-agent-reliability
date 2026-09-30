"""Run every verifier layer against a frozen patch and write the records.

The CLI is `scripts/verify_patch.py`. This module is the callable the pilot
runner uses so it does not have to shell out, and so both policies can be
decided from one layer pass instead of running the tests twice.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
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
from reliability.verifier.decision import SignalOutcome, get_policy
from reliability.verifier.evidence import (
    has_high_severity_risk,
    has_prohibited_manipulation,
    integrity_outcome,
    regression_outcome,
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
from reliability.verifier.regression import (
    RegressionConfig,
    RegressionReport,
    Signal,
    run_regression,
)
from reliability.verifier.reproduction import (
    ContainerSandbox,
    base_container_sandbox,
    evaluate_frozen,
    not_run,
    signal_before_patch,
    signal_from_reproduction,
)
from reliability.verifier.reproduction_freeze import (
    BaseSandboxFactory,
    MiniSweGenerator,
    ReproductionConfigError,
    ReproductionSetup,
    ReproGenerator,
    freeze_tests,
)
from reliability.verifier.selection import SelectionConfig, select_tests
from reliability.verifier.static_checks import (
    CheckStatus,
    StaticConfig,
    StaticReport,
    run_static_checks,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def default_reproduction_setup() -> ReproductionSetup:
    return ReproductionSetup.load(
        verifier_config=REPO_ROOT / "configs/verifier/full.yaml",
        repo_root=REPO_ROOT,
    )


def verify_task(
    task_dir: Path,
    *,
    configs: tuple[str, ...] = ("full", "baseline"),
    use_container: bool = True,
    replace: bool = False,
    reproduction: ReproductionSetup | None = None,
    generator: ReproGenerator | None = None,
) -> list[VerificationRecord]:
    """Verify one frozen patch. Writes one record per policy configuration.

    Layers run once. Both policies read the same evidence, which is what makes
    the baseline-versus-full comparison a difference of rules rather than a
    difference of what was measured.
    """
    setup = reproduction or default_reproduction_setup()
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
                instance_id=record.instance_id, patch_text=patch_text)
            container.start()
            tree = ContainerRepoTree(container)
            command_executor = ContainerCommandExecutor(container)
            test_executor = ContainerTestExecutor(container)
        signals, extras = run_layers(
            patch_text, tree, command_executor, test_executor,
            instance_id=record.instance_id,
            baseline_cache_dir=task_dir.parent.parent / "_baseline_cache",
        )
    except ContainerError as exc:
        signals, extras = _container_failed(patch_text, str(exc))
    finally:
        if container is not None:
            container.stop()

    signals[SignalKind.REPRODUCTION] = run_reproduction(
        record.instance_id, patch_text, setup,
        use_container=use_container,
        patch_applies=bool(
            signals[SignalKind.INTEGRITY].findings.get("patch_applies", True)),
        cache_dir=task_dir.parent.parent / "_reproduction_cache",
        generator=generator,
    )

    evidence = _evidence_from(signals)
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

    patch = integrity.patch or (
        parse_patch(patch_text) if patch_text.strip() else None)

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
        extras["selection_convention"] = (
            selection.convention.convention.value if selection.convention else ""
        )
        if selection.convention is not None:
            extras["selection_convention_hit_rate"] = round(selection.convention.hit_rate, 4)
            extras["selection_convention_scores"] = dict(selection.convention.scores)
        extras["selection_runner"] = (
            f"{selection.runner.name}: {selection.runner.evidence}"
            if selection.runner else ""
        )
        if test_executor is not None and hasattr(test_executor, "runner"):
            test_executor.runner = selection.runner

        if test_executor is None:
            signals[SignalKind.REGRESSION] = (
                SignalRecord.absent(
                    SignalKind.REGRESSION, SignalAbsence.NOTHING_TO_CHECK,
                    "selection found no tests for the changed files")
                if not selection.tests else
                SignalRecord.absent(
                    SignalKind.REGRESSION, SignalAbsence.DISABLED,
                    f"{len(selection.tests)} tests selected but not executed")
            )
        else:
            report = run_regression(
                instance_id, selection, test_executor,
                RegressionConfig(baseline_cache_dir=baseline_cache_dir),
            )
            signals[SignalKind.REGRESSION] = signal_from_regression(report)

        if command_executor is None:
            signals[SignalKind.STATIC] = SignalRecord.absent(
                SignalKind.STATIC, SignalAbsence.DISABLED,
                "no command executor; run with --container")
        else:
            static = run_static_checks(patch, tree, command_executor, StaticConfig())
            signals[SignalKind.STATIC] = signal_from_static(static)

    # V4 runs in its own containers, from verify_task; see run_reproduction.
    signals[SignalKind.REPRODUCTION] = SignalRecord.absent(
        SignalKind.REPRODUCTION, SignalAbsence.DISABLED,
        "reproduction is run by verify_task, not by run_layers",
    )
    return signals, extras


def run_reproduction(
    instance_id: str,
    patch_text: str,
    setup: ReproductionSetup,
    *,
    use_container: bool,
    patch_applies: bool,
    cache_dir: Path,
    generator: ReproGenerator | None = None,
    base_sandbox: BaseSandboxFactory = base_container_sandbox,
    patched_sandbox=None,
    issue_text: str | None = None,
) -> SignalRecord:
    """V4: freeze issue-derived tests at the base commit, then run them patched.

    `patched_sandbox(instance_id, patch_text)` opens a context yielding a
    sandbox whose tree the patch has been applied to; the default is a fresh
    verifier container.
    """
    if not use_container:
        return not_run(SignalAbsence.DISABLED,
                       "no container; run with --container", setup)
    if not patch_text.strip():
        return not_run(SignalAbsence.NOTHING_TO_CHECK, "patch is empty", setup)
    if not patch_applies:
        return not_run(SignalAbsence.NOTHING_TO_CHECK,
                       "patch does not apply to the base commit", setup)

    started = time.monotonic()
    try:
        suite = freeze_tests(
            issue_text if issue_text is not None
            else load_agent_task(instance_id).problem_statement,
            instance_id,
            setup=setup, cache_dir=cache_dir,
            generator=generator or MiniSweGenerator(setup, REPO_ROOT),
            base_sandbox=base_sandbox,
        )
    except ReproductionConfigError:
        raise
    except Exception as exc:  # noqa: BLE001 - the layer broke; recorded as ERROR
        return not_run(SignalAbsence.ERROR,
                       f"freeze failed: {type(exc).__name__}: {exc}"[:400], setup)

    early = signal_before_patch(
        suite, setup, duration_s=time.monotonic() - started)
    if early is not None:
        return early

    opener = patched_sandbox or _patched_container_sandbox
    try:
        with opener(instance_id, patch_text) as sandbox:
            patched = evaluate_frozen(suite, patch_text, sandbox, setup)
    except ReproductionConfigError:
        raise
    except Exception as exc:  # noqa: BLE001
        return not_run(SignalAbsence.ERROR,
                       f"patched run failed: {type(exc).__name__}: {exc}"[:400],
                       setup)
    return signal_from_reproduction(
        suite, patched, setup, duration_s=time.monotonic() - started)


@contextmanager
def _patched_container_sandbox(instance_id: str, patch_text: str):
    with TaskContainer(instance_id=instance_id, patch_text=patch_text) as container:
        container.set_patched(True)
        yield ContainerSandbox(container)


def signal_from_regression(report: RegressionReport) -> SignalRecord:
    outcome = regression_outcome(report)
    absence = None
    if outcome is SignalOutcome.NOT_AVAILABLE:
        if report.signal is Signal.BASELINE_UNRELIABLE:
            absence = SignalAbsence.ERROR
        elif report.selection and report.selection.tests:
            # Tests were selected and none ran: the runner broke. That is the
            # layer failing, not the layer being switched off.
            absence = SignalAbsence.ERROR
        else:
            absence = SignalAbsence.NOTHING_TO_CHECK
    detail = "; ".join(report.notes) or (
        f"{report.n_executed} executed, {report.n_regressions} regressions")
    return SignalRecord(
        kind=SignalKind.REGRESSION, outcome=outcome, absence=absence,
        detail=detail, duration_s=report.duration_s,
        findings={
            "signal": report.signal.value,
            "summary": report.summary,
            "n_executed": report.n_executed,
            "notes": list(report.notes),
        },
    )


def signal_from_static(report: StaticReport) -> SignalRecord:
    outcome = static_outcome(report)
    absence = None
    if outcome is SignalOutcome.NOT_AVAILABLE:
        statuses = {r.status for r in report.results}
        if CheckStatus.TIMEOUT in statuses:
            absence = SignalAbsence.TIMEOUT
        elif CheckStatus.ERROR in statuses:
            absence = SignalAbsence.ERROR
        elif report.n_available == 0:
            absence = SignalAbsence.NOT_CONFIGURED
        else:
            absence = SignalAbsence.NOTHING_TO_CHECK
    notes = [
        f"{r.kind.value}: {r.detail}"
        for r in report.results
        if r.status is CheckStatus.NOT_AVAILABLE and r.detail
    ]
    return SignalRecord(
        kind=SignalKind.STATIC, outcome=outcome, absence=absence,
        detail="; ".join(
            [f"{report.n_ran}/{report.n_available} checks ran", *notes]
        ),
        findings={
            "summary": report.summary,
            "new_failures": [r.kind.value for r in report.new_failures],
            "unavailable": [
                {"kind": r.kind.value, "tool": r.tool, "reason": r.detail}
                for r in report.results
                if r.status is CheckStatus.NOT_AVAILABLE
            ],
        },
    )


def _container_failed(patch_text: str, detail: str):
    """Integrity still runs; container layers record the failure as ERROR."""
    signals, extras = run_layers(
        patch_text, tree=None, command_executor=None, test_executor=None,
        instance_id="unused")
    reason = f"container failed: {detail[:300]}"
    for kind in (SignalKind.REGRESSION, SignalKind.STATIC):
        signals[kind] = SignalRecord.absent(kind, SignalAbsence.ERROR, reason)
    return signals, extras


def _evidence_from(signals):
    from reliability.verifier.decision import Evidence

    integrity = signals[SignalKind.INTEGRITY]
    return Evidence(
        integrity=integrity.outcome,
        regression=signals[SignalKind.REGRESSION].outcome,
        static=signals[SignalKind.STATIC].outcome,
        reproduction=signals[SignalKind.REPRODUCTION].outcome,
        high_severity_risk=bool(integrity.findings.get("high_severity_risk")),
        prohibited_manipulation=bool(
            integrity.findings.get("prohibited_manipulation")),
        patch_applies=bool(integrity.findings.get("patch_applies", True)),
    )
