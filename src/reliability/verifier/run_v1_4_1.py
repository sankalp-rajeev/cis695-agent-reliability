"""Full v1.4.1 verification; task failures become attributed signal absences."""

from __future__ import annotations

import signal
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from reliability.umgpt_spend import BudgetCap
from reliability.verifier.archive_tree import ArchiveTree
from reliability.verifier.container import ContainerRepoTree, ContainerTestExecutor
from reliability.verifier.evidence import has_high_severity_risk, has_prohibited_manipulation, integrity_outcome
from reliability.verifier.guarded_v2 import FrozenContainer, ReplayMismatch, run_policies
from reliability.verifier.inline_g1 import guarded_pair, proposed_failure_category
from reliability.verifier.integrity import Violation
from reliability.verifier.integrity_v1_4 import check_integrity
from reliability.verifier.native_reference import collection_reference, empty_reference, load_drift
from reliability.verifier.policy_v1_4 import evidence_from_signals
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.record import DecisionEntry, SignalAbsence, SignalKind, SignalRecord, VerificationRecord
from reliability.verifier.run import signal_from_regression
from reliability.verifier.run_health import RunHealthError, append_health, zero_output
from reliability.verifier.selection import SelectionConfig, select_tests
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.static_v1_4 import ContainerEvidenceExecutor, run_static_checks
from reliability.verifier.task_specs import sha, write
from reliability.verifier.task_specs import ROOT


def default_reproduction_setup(generator_config=None):
    from dataclasses import replace
    from reliability.verifier.reproduction_freeze import GeneratorModel, ReproductionSetup
    setup = ReproductionSetup.load(verifier_config=ROOT / 'configs/verifier/full_v1_4_1.yaml', repo_root=ROOT)
    path = Path(generator_config or ROOT / 'configs/model/generator.yaml').resolve()
    return replace(setup, model=GeneratorModel.load(path, repo_root=ROOT if path.is_relative_to(ROOT) else None))


class VerificationRecordV141(VerificationRecord):
    skip_v4: bool = False
    image_id: str | None = None
    archive_sha256: str | None = None
    pristine_receipt_sha256: str | None = None
    selection_sha256: str | None = None
    g1_receipt_sha256: dict[str, str] = {}
    provenance: dict = {}
    v4_run_status: str = 'NOT_RUN'


class TaskWallTime(BaseException):
    """Bypasses adapter exception handlers; caught at the per-task V2 boundary."""


class TaskBudgetStop(BudgetCap):
    def __init__(self, record):
        self.record = record
        super().__init__('BUDGET_STOP')


@contextmanager
def v2_deadline(seconds=10800):
    def expired(*args):
        raise TaskWallTime('V2_WALL_TIME_3H')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def absence(kind, reason, *, infrastructure=False, timeout=False):
    result = SignalRecord.absent(kind, SignalAbsence.TIMEOUT if timeout else SignalAbsence.ERROR, reason)
    result.findings.update(absence_reason=reason, infrastructure=infrastructure)
    return result


@dataclass(frozen=True)
class ExecutionSpec:
    instance_id: str
    image_id: str
    source: object
    runner: object
    patch_path: Path
    tests: tuple[str, ...]


def integrity_signal(patch_text, tree):
    report = check_integrity(patch_text, tree=tree)
    record = SignalRecord(kind=SignalKind.INTEGRITY, outcome=integrity_outcome(report),
        detail='; '.join(str(f) for f in report.findings) or 'no violations',
        findings={'violations': [v.value for v in report.violations],
                  'patch_applies': Violation.DOES_NOT_APPLY not in report.violations,
                  'prohibited_manipulation': has_prohibited_manipulation(report),
                  'high_severity_risk': has_high_severity_risk(report),
                  'ast_analysis': list(report.analysis)})
    return report, record


def run_v2(task, patch_path, selection, folder, *, experiment, drift, stamps):
    spec = ExecutionSpec(task.instance_id, task.image_id, task.source, task.runner, patch_path, selection.tests)
    references, blocked = {}, []
    for patched in (False, True):
        tree = 'patched' if patched else 'base'
        health = guarded_pair(spec, patched, folder / 'g1',
                              empty_reference(task.instance_id, tree, selection.tests, drift))
        append_health(folder / 'health.jsonl', {'scope': 'G1', **health})
        receipt = folder / 'g1/tasks' / task.instance_id / tree / 'collection.json'
        if receipt.exists():
            stamps['g1_receipt_sha256'][tree] = sha(receipt)
        if health['status'] != 'READY':
            failed = [stage for stage in health.get('stages', ()) if
                      stage['status'] in ('COLLECTION_ERROR', 'RUNNER_UNAVAILABLE', 'NOT_REACHED', 'ERROR')
                      or zero_output([stage])['halt']]
            blocked.append(proposed_failure_category(failed[0]) if failed else 'stage_error_requires_review')
        else:
            import json
            references[tree] = collection_reference(task.instance_id, tree, selection.tests,
                                                    json.loads(receipt.read_bytes()), drift)
    if blocked:
        error = RunHealthError({'task': task.instance_id, 'halt': True, 'halt_reasons': blocked})
        error.g1_category = blocked[0]
        raise error
    receipt_path = folder / 'pristine_source_receipt.json'
    with FrozenContainer(task.instance_id, patch_path.read_text(), image=task.image_id,
        experiment_id=experiment, source_spec=task.source, source_receipt_path=receipt_path) as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        stamps['pristine_receipt_sha256'] = sha(receipt_path)
        write(folder / 'pristine_generated_inputs.json', container.generated_snapshot())
        executor = ContainerTestExecutor(container, runner=task.runner, evidence_dir=folder / 'raw')
        reports = run_policies(task.instance_id, selection, executor, references, folder)
    return signal_from_regression(reports['S_invalid_excluded'])


def run_v3(task, patch_text, patch, folder, *, experiment):
    with FrozenContainer(task.instance_id, patch_text, image=task.image_id,
        experiment_id=experiment, source_spec=task.source,
        source_receipt_path=folder / 'v3_pristine_source_receipt.json') as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        write(folder / 'v3_pristine_generated_inputs.json', container.generated_snapshot())
        return run_static_checks(patch, ContainerRepoTree(container), ContainerEvidenceExecutor(container))


def verify_task(task_dir, *, instance_id, task_spec, experiment_id, skip_v4=False,
                provenance=None, v4_runner=None, drift=None, v2_runner=None, v3_runner=None,
                reproduction_setup=None):
    """Never swallow source-integrity errors; V2 absence does not skip V3/V4."""
    task_dir = Path(task_dir)
    folder = task_dir / 'verification'
    folder.mkdir(parents=True, exist_ok=True)
    patch_path = task_dir / 'patch.diff'
    patch_text = patch_path.read_text()
    setup = reproduction_setup or default_reproduction_setup()
    started = time.monotonic()
    signals, selection, integrity = {}, None, None
    stamps = {'g1_receipt_sha256': {}, 'pristine_receipt_sha256': None, 'selection_sha256': None}
    try:
        if task_spec is None:
            integrity, signals[SignalKind.INTEGRITY] = integrity_signal(patch_text, None)
        else:
            with ArchiveTree(task_spec.source.archive_path) as tree:
                integrity, signals[SignalKind.INTEGRITY] = integrity_signal(patch_text, tree)
                if integrity.patch is not None:
                    selection = select_tests(integrity.patch, tree, SelectionConfig())
                    # Commands use the registry's frozen Django parallel choice.
                    from dataclasses import replace
                    selection = replace(selection, runner=task_spec.runner)
    except SourceIntegrityError:
        raise
    except Exception as exc:
        signals[SignalKind.INTEGRITY] = absence(SignalKind.INTEGRITY, 'V1_EXCEPTION:' + type(exc).__name__)
    if selection is not None:
        from dataclasses import asdict
        write(folder / 'selection.json', asdict(selection))
        stamps['selection_sha256'] = sha(folder / 'selection.json')
    if task_spec is None:
        signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'NO_TASK_SPEC')
        signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'NO_TASK_SPEC')
    else:
        try:
            if selection is None:
                signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'NO_SELECTION')
            else:
                with v2_deadline():
                    signals[SignalKind.REGRESSION] = (v2_runner or run_v2)(
                        task_spec, patch_path, selection, folder, experiment=experiment_id,
                        drift=drift if drift is not None else load_drift(), stamps=stamps)
        except SourceIntegrityError:
            raise
        except TaskWallTime:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'V2_WALL_TIME_3H', infrastructure=True, timeout=True)
        except ReplayMismatch:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'REPLAY_MISMATCH', infrastructure=True)
        except RunHealthError as exc:
            reason = ('RUN_HEALTH_G1:' + exc.g1_category) if hasattr(exc, 'g1_category') else 'RUN_HEALTH:' + str(exc)
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, reason, infrastructure=True)
        except Exception as exc:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'EXECUTOR_EXCEPTION:' + type(exc).__name__, infrastructure=True)
        try:
            if integrity is None or integrity.patch is None:
                signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'NO_PARSEABLE_PATCH')
            else:
                signals[SignalKind.STATIC] = (v3_runner or run_v3)(task_spec, patch_text, integrity.patch, folder, experiment=experiment_id)
        except SourceIntegrityError:
            raise
        except Exception as exc:
            signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'EXECUTOR_EXCEPTION:' + type(exc).__name__, infrastructure=True)
    budget_stop = False
    if skip_v4:
        signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'SKIP_V4_FOR_CHECK')
    elif v4_runner is None:
        signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'NO_V4_RUNTIME')
    else:
        try:
            signals[SignalKind.REPRODUCTION] = v4_runner(instance_id, patch_text, signals[SignalKind.INTEGRITY])
        except SourceIntegrityError:
            raise
        except BudgetCap:
            budget_stop = True
            signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'BUDGET_STOP', infrastructure=True)
        except Exception as exc:
            signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'V4_EXCEPTION:' + type(exc).__name__, infrastructure=True)
    policy = FullPolicyV141()
    result = VerificationRecordV141(instance_id=instance_id, experiment_id=experiment_id,
        verifier_config='full-v1.4.1', patch_sha256='sha256:' + sha(patch_path),
        integrity=signals[SignalKind.INTEGRITY], regression=signals[SignalKind.REGRESSION],
        static=signals[SignalKind.STATIC], reproduction=signals[SignalKind.REPRODUCTION],
        decision=DecisionEntry.from_record(policy.decide(evidence_from_signals(signals))),
        risk_features=integrity.risk.as_vector() if integrity else {},
        selected_tests=selection.tests if selection else (), selection_runner=task_spec.runner.name if task_spec else '',
        duration_s=time.monotonic() - started, verified_at=datetime.now(UTC).isoformat(), skip_v4=skip_v4,
        image_id=task_spec.image_id if task_spec else None,
        archive_sha256=task_spec.source.archive_sha256 if task_spec else None,
        reproduction_generator=setup.identity(),
        provenance=provenance or {}, v4_run_status='NOT_RUN' if skip_v4 or budget_stop or v4_runner is None else 'RAN', **stamps)
    result.write(task_dir / 'verification_record.full-v1.4.1.json')
    if budget_stop:
        raise TaskBudgetStop(result)
    return result
