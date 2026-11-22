"""Full v1.4.1 verification; task failures become attributed signal absences."""

from __future__ import annotations

import signal
import time
from contextlib import contextmanager
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import yaml

from reliability.umgpt_spend import BudgetCap
from reliability.provider_errors import ProviderTransientError
from reliability.agent.freeze import FrozenPatch, FrozenPatchError, read_patch, verify as verify_frozen_patch
from reliability.verifier.archive_tree import ArchiveTree
from reliability.verifier.container import ContainerRepoTree, ContainerTestExecutor, PatchApplyError
from reliability.verifier.evidence import has_high_severity_risk, has_prohibited_manipulation, integrity_outcome
from reliability.verifier.guarded_v2 import (
    DEFAULT_V2_ACCOUNTING, V2_ACCOUNTINGS, FrozenContainer, ReplayMismatch, fallback_results,
    run_policies,
)
from reliability.verifier.inline_g1 import guarded_pair, proposed_failure_category, finalize_generic_pair
from reliability.verifier.generic_health import paired_exception_scope
from reliability.verifier.integrity import Finding, IntegrityReport, Violation
from reliability.verifier.integrity_v1_4 import check_integrity
from reliability.verifier.native_reference import collection_reference, empty_reference, load_drift
from reliability.verifier.policy_v1_4 import evidence_from_signals
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.record import DecisionEntry, SignalAbsence, SignalKind, SignalRecord, VerificationRecord
from reliability.verifier.run import signal_from_regression
from reliability.verifier.run_health import RunHealthError, append_health, zero_output
from reliability.verifier.selection import Selection, SelectionConfig, select_tests
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.static_v1_4 import ContainerEvidenceExecutor, run_static_checks
from reliability.verifier.task_specs import sha, write
from reliability.verifier.task_specs import ROOT

DEFAULT_VERIFIER_CONFIG = ROOT / 'configs/verifier/full_v1_4_1.yaml'


@dataclass(frozen=True)
class V2Settings:
    primary_accounting: str
    selection: SelectionConfig


def load_v2_settings(path: Path) -> V2Settings | None:
    block = yaml.safe_load(path.read_text(encoding='utf-8')).get('v1_5')
    if block is None or block == {}:
        return None
    if not isinstance(block, dict):
        raise ValueError('v1_5 must be a mapping')
    accounting = block.get('v2_primary_accounting', DEFAULT_V2_ACCOUNTING)
    fallback = block.get('v2_fallback_any_convention', False)
    max_files = block.get('v2_fallback_max_files', 5)
    if not isinstance(accounting, str) or accounting not in V2_ACCOUNTINGS:
        raise ValueError('v2_primary_accounting must name one of the six V2 reports')
    if type(fallback) is not bool or type(max_files) is not int or max_files < 0:
        raise ValueError('V2 fallback requires a boolean switch and a nonnegative file cap')
    return V2Settings(accounting, SelectionConfig(
        fallback_any_convention=fallback, fallback_max_files=max_files))


def v2_signal_for_decision(reports, settings: V2Settings | None = None):
    key = settings.primary_accounting if settings is not None else DEFAULT_V2_ACCOUNTING
    report = reports[key]
    signal = signal_from_regression(report)
    if settings is not None:
        selection = report.selection if report.selection is not None else Selection()
        signal.findings.update(primary_accounting=key, **selection.fallback_metadata(),
                               test_results=fallback_results(report))
    return signal


def default_reproduction_setup(generator_config=None, *, verifier_config=DEFAULT_VERIFIER_CONFIG):
    from dataclasses import replace
    from reliability.verifier.reproduction_freeze import GeneratorModel, ReproductionSetup
    setup = ReproductionSetup.load(verifier_config=verifier_config, repo_root=ROOT)
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
    def __init__(self, record, termination='BUDGET_CAP'):
        self.record = record
        self.termination = termination
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
    experiment_id: str = 'e2e_v1_4_1'


def integrity_signal(patch_text, tree):
    report = check_integrity(patch_text, tree=tree)
    return report, integrity_record(report)


def integrity_record(report, **extra):
    record = SignalRecord(kind=SignalKind.INTEGRITY, outcome=integrity_outcome(report),
        detail='; '.join(str(f) for f in report.findings) or 'no violations',
        findings={'violations': [v.value for v in report.violations],
                  'patch_applies': Violation.DOES_NOT_APPLY not in report.violations,
                  'prohibited_manipulation': has_prohibited_manipulation(report),
                  'high_severity_risk': has_high_severity_risk(report),
                  'ast_analysis': list(getattr(report, 'analysis', ()))})
    record.findings.update(extra)
    return record


def with_does_not_apply(report, detail):
    """Amendment B9: a patch the container's `git apply` rejects fails V1 (R1 REJECT)."""
    finding = Finding(Violation.DOES_NOT_APPLY, detail=(detail or '')[:300] or 'git apply --check failed')
    if report is None:
        return IntegrityReport(findings=(finding,))
    if Violation.DOES_NOT_APPLY in report.violations:
        return report
    return replace(report, findings=report.findings + (finding,))


def container_apply_check(task, patch_text, folder, experiment):
    """V1's apply check (B9): the task's verified pristine container runs the same
    `git apply` the container uses to apply the patch, so the two cannot disagree."""
    with FrozenContainer(task.instance_id, patch_text, image=task.image_id, experiment_id=experiment,
                         source_spec=task.source,
                         source_receipt_path=folder / 'v1_pristine_source_receipt.json') as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        return container.apply_check()


def run_v2(task, patch_path, selection, folder, *, experiment, drift, stamps, v2_settings=None):
    with paired_exception_scope(task.instance_id, task.source.pre_install.repo):
        return _run_v2(task, patch_path, selection, folder, experiment=experiment, drift=drift,
                       stamps=stamps, v2_settings=v2_settings)


_BLOCKING = ('COLLECTION_ERROR', 'RUNNER_UNAVAILABLE', 'NOT_REACHED', 'ERROR')
_PYTEST_E = re.compile(r'^E\s+((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*): ')
_PLAIN_EXC = re.compile(r'^((?:[A-Za-z_]\w*\.)*[A-Z]\w*): ')
_NOT_EXCEPTIONS = frozenset({'Hint', 'Traceback', 'Note', 'ERROR', 'FAILED'})


def collection_exception_type(text):
    """The exception a module's collection failed with: pytest `E   Type:` lines first."""
    text = text or ''
    lines = [line.strip() for line in text.splitlines()]
    # A bare `Name: text` line is an exception only after a Python traceback; a
    # runner that prints and exits (e.g. "Aborting: ...") has no exception type.
    patterns = (_PYTEST_E, _PLAIN_EXC) if 'Traceback (most recent call last)' in text else (_PYTEST_E,)
    for pattern in patterns:
        for line in reversed(lines):
            match = pattern.match(line)
            if match and match.group(1).rsplit('.', 1)[-1] not in _NOT_EXCEPTIONS:
                return match.group(1)
    return None


def _blocking_stages(health):
    return [stage for stage in health.get('stages', ())
            if stage['status'] in _BLOCKING or zero_output([stage])['halt']]


def paired_collection_exclusions(healths):
    """Amendment A7: modules whose collection fails on both trees with the same exception type.

    Returns None unless both trees are BLOCKED only by per-module native
    collection errors, every one with a known exception type, and the same
    module -> exception type map on both trees.
    """
    if sorted(h.get('tree') for h in healths) != ['base', 'patched']:
        return None
    per_tree = {}
    for health in healths:
        if health.get('status') != 'BLOCKED' or health.get('generic_pair_halt_reasons'):
            return None
        stages = _blocking_stages(health)
        if not stages:
            return None
        found = {}
        for stage in stages:
            if stage.get('allowed_exception'):
                # A prelisted environment guard (e.g. GIS) that G1 already allows; it
                # never blocks, so it neither prevents nor joins the exclusion (B9).
                continue
            if (stage.get('stage') != 'native_collection' or stage.get('status') != 'COLLECTION_ERROR'
                    or not stage.get('module')):
                return None
            exc = collection_exception_type('\n'.join(stage.get('messages') or ()) + '\n'
                                            + str(stage.get('message') or ''))
            if exc is None or found.get(stage['module'], exc) != exc:
                return None
            found[stage['module']] = exc
        if not found:
            return None
        per_tree[health['tree']] = found
    if per_tree['base'] != per_tree['patched']:
        return None
    return [{'module': module, 'exception_type': exc} for module, exc in sorted(per_tree['base'].items())]


_MACHINE_SIGNS = ('No space left on device', 'Cannot connect to the Docker daemon', 'OCI runtime',
                  'OOMKilled', 'Out of memory', 'ContainerStartError')


def _stage_text(stage):
    return '\n'.join(stage.get('messages') or ()) + '\n' + str(stage.get('message') or '')


def _machine_failure(stage):
    """A harness or machine failure: an exception in the verifier itself, or a Docker,
    disk or out-of-memory signature. Never something the patch or the image causes."""
    return (stage.get('status') in ('ERROR', 'INTERRUPTED')
            or any(sign in _stage_text(stage) for sign in _MACHINE_SIGNS)
            or 137 in (stage.get('collector_exit_codes') or ()))


def _tree_clean(health):
    """A tree is clean when G1 is READY, or when every blocking stage is a prelisted
    environment guard (allowed, or revoked only because the other tree did not match)."""
    if health.get('status') == 'READY':
        return True
    stages = _blocking_stages(health)
    return bool(stages) and all(s.get('allowed_exception') or s.get('generic_rule_rejected') for s in stages)


def g1_attribution(healths):
    """Amendment B9: who caused a G1 run-health block.

    infrastructure: a machine or harness failure on either tree (Docker, container,
        disk, out of memory, a verifier exception). Only these set the infrastructure flag.
    patch: the base tree is clean and the patched tree is blocked (e.g. django-14140).
    environment: both trees are blocked by the code under test or the image (a
        collector or dependency gap that A7 could not exclude). Not infrastructure.
    """
    if any(h.get('status') == 'INTERRUPTED' for h in healths) or any(
            _machine_failure(stage) for h in healths for stage in _blocking_stages(h)):
        return 'infrastructure'
    trees = {h.get('tree'): h for h in healths}
    base, patched = trees.get('base'), trees.get('patched')
    if base is not None and patched is not None and _tree_clean(base) and patched.get('status') != 'READY':
        return 'patch'
    return 'environment'


def _g1(task, spec, folder, output, tests, drift, stamps, scope, suffix=''):
    references, blocked, healths = {}, [], []
    for patched in (False, True):
        tree = 'patched' if patched else 'base'
        health = guarded_pair(spec, patched, output,
                              empty_reference(task.instance_id, tree, tests, drift))
        healths.append(health)
    finalize_generic_pair(spec, output, healths)
    for health in healths:
        tree = health['tree']
        append_health(folder / 'health.jsonl', {'scope': scope, **health})
        receipt = output / 'tasks' / task.instance_id / tree / 'collection.json'
        if receipt.exists():
            stamps['g1_receipt_sha256'][tree + suffix] = sha(receipt)
        if health['status'] != 'READY':
            failed = _blocking_stages(health)
            blocked.append(proposed_failure_category(failed[0]) if failed else 'stage_error_requires_review')
        else:
            import json
            references[tree] = collection_reference(task.instance_id, tree, tests,
                                                    json.loads(receipt.read_bytes()), drift)
    return healths, references, blocked


def g1_with_paired_exclusion(task, patch_path, selection, folder, *, experiment, drift, stamps):
    """G1 on both trees, then amendment A7's paired exclusion. Collection only: no test runs.

    Raises RunHealthError with `g1_category` and `attribution` (B9) if G1 stays blocked.
    Returns (selection, references, exclusions).
    """
    spec = ExecutionSpec(task.instance_id, task.image_id, task.source, task.runner, patch_path, selection.tests, experiment)
    healths, references, blocked = _g1(task, spec, folder, folder / 'g1', selection.tests, drift, stamps, 'G1')
    exclusions = []
    if blocked:
        paired = paired_collection_exclusions(healths) or []
        modules = {entry['module'] for entry in paired}
        remaining = tuple(t for t in selection.tests if t.split('::', 1)[0] not in modules)
        if paired and remaining:
            # Amendment A7: drop the paired modules, record them, and re-check G1 on the rest.
            for entry in paired:
                entry.update(excluded_tests=[t for t in selection.tests if t.split('::', 1)[0] == entry['module']],
                             trees=['base', 'patched'])
            fallback = tuple(t for t in selection.fallback_tests if t in remaining)
            selection = replace(selection, tests=remaining, fallback_tests=fallback, fallback_used=bool(fallback))
            spec = replace(spec, tests=remaining)
            healths, references, blocked = _g1(task, spec, folder, folder / 'g1_after_paired_exclusion',
                                               remaining, drift, stamps, 'G1_after_paired_exclusion',
                                               '_after_paired_exclusion')
            exclusions = paired
    if blocked:
        error = RunHealthError({'task': task.instance_id, 'halt': True, 'halt_reasons': blocked})
        error.g1_category = blocked[0]
        error.attribution = g1_attribution(healths)
        raise error
    return selection, references, exclusions


def _run_v2(task, patch_path, selection, folder, *, experiment, drift, stamps, v2_settings=None):
    selection, references, exclusions = g1_with_paired_exclusion(
        task, patch_path, selection, folder, experiment=experiment, drift=drift, stamps=stamps)
    receipt_path = folder / 'pristine_source_receipt.json'
    with FrozenContainer(task.instance_id, patch_path.read_bytes().decode('utf-8'), image=task.image_id,
        experiment_id=experiment, source_spec=task.source, source_receipt_path=receipt_path) as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        stamps['pristine_receipt_sha256'] = sha(receipt_path)
        write(folder / 'pristine_generated_inputs.json', container.generated_snapshot())
        executor = ContainerTestExecutor(container, runner=task.runner, evidence_dir=folder / 'raw')
        options = {'primary_accounting': v2_settings.primary_accounting} if v2_settings else {}
        reports = run_policies(task.instance_id, selection, executor, references, folder, **options)
    signal = v2_signal_for_decision(reports, v2_settings)
    if exclusions:
        signal.findings['paired_collection_exclusions'] = exclusions
    return signal


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
                reproduction_setup=None, v2_settings=None, v4_reuse_evidence=None, apply_check=None):
    """Never swallow source-integrity errors; V2 absence does not skip V3/V4.

    A patch the container's `git apply` rejects fails V1, and V2/V3 are then not run
    (amendment B9); `apply_check` defaults to the container check.
    """
    task_dir = Path(task_dir)
    folder = task_dir / 'verification'
    folder.mkdir(parents=True, exist_ok=True)
    patch_path = task_dir / 'patch.diff'
    frozen = FrozenPatch(patch_path, 'sha256:' + sha(patch_path), patch_path.stat().st_size)
    try:
        patch_text = read_patch(frozen).decode('utf-8')
    except FrozenPatchError as exc:
        raise SourceIntegrityError({'mismatches': [{'path': 'patch.diff', 'reason': str(exc)}]}) from exc
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
                    selection_config = v2_settings.selection if v2_settings else SelectionConfig()
                    selection = select_tests(integrity.patch, tree, selection_config)
                    # Commands use the registry's frozen Django parallel choice.
                    from dataclasses import replace
                    selection = replace(selection, runner=task_spec.runner)
    except SourceIntegrityError:
        raise
    except Exception as exc:
        signals[SignalKind.INTEGRITY] = absence(SignalKind.INTEGRITY, 'V1_EXCEPTION:' + type(exc).__name__)
    apply_status = None

    def does_not_apply(detail):
        nonlocal integrity
        integrity = with_does_not_apply(integrity, detail)
        signals[SignalKind.INTEGRITY] = integrity_record(integrity, apply_check=apply_status)

    if task_spec is not None and patch_text.strip():
        try:
            applies, detail = (apply_check or container_apply_check)(task_spec, patch_text, folder, experiment_id)
        except SourceIntegrityError:
            raise
        except Exception as exc:
            apply_status = 'UNAVAILABLE:' + type(exc).__name__
            signals[SignalKind.INTEGRITY].findings['apply_check'] = apply_status
        else:
            apply_status = 'PASS' if applies else 'FAIL'
            if applies:
                signals[SignalKind.INTEGRITY].findings['apply_check'] = apply_status
            else:
                does_not_apply(detail)

    def rejected():
        return integrity is not None and Violation.DOES_NOT_APPLY in integrity.violations
    if selection is not None:
        write(folder / 'selection.json', selection.to_dict(include_fallback=v2_settings is not None))
        stamps['selection_sha256'] = sha(folder / 'selection.json')
    empty_patch = not patch_text.strip() or (
        integrity is not None and integrity.patch is not None and integrity.patch.is_empty)
    if empty_patch:
        signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'EMPTY_PATCH')
        signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'EMPTY_PATCH')
    elif task_spec is None:
        signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'NO_TASK_SPEC')
        signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'NO_TASK_SPEC')
    else:
        try:
            if selection is None:
                signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'NO_SELECTION')
            elif rejected():
                signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'PATCH_DOES_NOT_APPLY')
            elif not selection.tests:
                signals[SignalKind.REGRESSION] = SignalRecord.absent(
                    SignalKind.REGRESSION, SignalAbsence.NOTHING_TO_CHECK, 'no tests selected')
                if v2_settings and v2_settings.selection.fallback_any_convention:
                    signals[SignalKind.REGRESSION].findings['absence_reason'] = 'NO_SELECTION'
            else:
                with v2_deadline():
                    options = {'v2_settings': v2_settings} if v2_settings else {}
                    signals[SignalKind.REGRESSION] = (v2_runner or run_v2)(
                        task_spec, patch_path, selection, folder, experiment=experiment_id,
                        drift=drift if drift is not None else load_drift(), stamps=stamps, **options)
        except SourceIntegrityError:
            raise
        except TaskWallTime:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'V2_WALL_TIME_3H', infrastructure=True, timeout=True)
        except ReplayMismatch:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'REPLAY_MISMATCH', infrastructure=True)
        except RunHealthError as exc:
            reason = ('RUN_HEALTH_G1:' + exc.g1_category) if hasattr(exc, 'g1_category') else 'RUN_HEALTH:' + str(exc)
            # Amendment B9: only a machine or harness failure is infrastructure.
            attribution = getattr(exc, 'attribution', 'infrastructure')
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, reason,
                                                     infrastructure=attribution == 'infrastructure')
            signals[SignalKind.REGRESSION].findings['attribution'] = attribution
        except PatchApplyError as exc:
            does_not_apply(str(exc))
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'PATCH_DOES_NOT_APPLY')
        except Exception as exc:
            signals[SignalKind.REGRESSION] = absence(SignalKind.REGRESSION, 'EXECUTOR_EXCEPTION:' + type(exc).__name__, infrastructure=True)
        try:
            if integrity is None or integrity.patch is None:
                signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'NO_PARSEABLE_PATCH')
            elif rejected():
                signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'PATCH_DOES_NOT_APPLY')
            else:
                signals[SignalKind.STATIC] = (v3_runner or run_v3)(task_spec, patch_text, integrity.patch, folder, experiment=experiment_id)
        except SourceIntegrityError:
            raise
        except PatchApplyError as exc:
            does_not_apply(str(exc))
            signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'PATCH_DOES_NOT_APPLY')
        except Exception as exc:
            signals[SignalKind.STATIC] = absence(SignalKind.STATIC, 'EXECUTOR_EXCEPTION:' + type(exc).__name__, infrastructure=True)
    regression_findings = signals[SignalKind.REGRESSION].findings
    if v2_settings is not None and 'primary_accounting' not in regression_findings:
        v2_selection = selection if selection is not None else Selection()
        regression_findings.update(primary_accounting=v2_settings.primary_accounting,
                                   **v2_selection.fallback_metadata(), test_results={})
    budget_stop, stop_termination, paid_before_stop = False, 'BUDGET_CAP', 0
    no_frozen_v4 = v4_reuse_evidence is not None and 'suite_sha256' not in v4_reuse_evidence
    if empty_patch and not no_frozen_v4:
        signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'EMPTY_PATCH')
    elif skip_v4:
        signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'SKIP_V4_FOR_CHECK')
    elif v4_runner is None:
        signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'NO_V4_RUNTIME')
    else:
        try:
            signals[SignalKind.REPRODUCTION] = v4_runner(instance_id, patch_text, signals[SignalKind.INTEGRITY])
        except SourceIntegrityError:
            raise
        except ProviderTransientError as exc:
            signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION,
                'V4_INFRA:' + exc.error_type, infrastructure=True)
        except BudgetCap as exc:
            budget_stop = True
            stop_termination = getattr(exc, 'termination', 'BUDGET_CAP')
            paid_before_stop = getattr(exc, 'paid_calls', 0)
            signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION,
                'AUTH_STOP' if stop_termination == 'AUTH_ERROR' else 'BUDGET_STOP', infrastructure=True)
        except Exception as exc:
            signals[SignalKind.REPRODUCTION] = absence(SignalKind.REPRODUCTION, 'V4_EXCEPTION:' + type(exc).__name__, infrastructure=True)
    if v4_reuse_evidence is not None:
        signals[SignalKind.REPRODUCTION].findings.update(v4_reuse_evidence)
    policy = FullPolicyV141()
    try:
        verify_frozen_patch(frozen)
    except FrozenPatchError as exc:
        raise SourceIntegrityError({'mismatches': [{'path': 'patch.diff', 'reason': str(exc)}]}) from exc
    result = VerificationRecordV141(instance_id=instance_id, experiment_id=experiment_id,
        verifier_config='full-v1.5' if v2_settings else 'full-v1.4.1', patch_sha256=frozen.sha256,
        integrity=signals[SignalKind.INTEGRITY], regression=signals[SignalKind.REGRESSION],
        static=signals[SignalKind.STATIC], reproduction=signals[SignalKind.REPRODUCTION],
        decision=DecisionEntry.from_record(policy.decide(evidence_from_signals(signals))),
        risk_features=integrity.risk.as_vector() if integrity else {},
        selected_tests=selection.tests if selection else (), selection_runner=task_spec.runner.name if task_spec else '',
        duration_s=time.monotonic() - started, verified_at=datetime.now(UTC).isoformat(), skip_v4=skip_v4,
        image_id=task_spec.image_id if task_spec else None,
        archive_sha256=task_spec.source.archive_sha256 if task_spec else None,
        reproduction_generator=setup.identity(),
        provenance=provenance or {}, v4_run_status=('PARTIAL' if budget_stop and paid_before_stop else
            'NOT_RUN' if empty_patch or skip_v4 or budget_stop or v4_runner is None else 'RAN'), **stamps)
    result.write(task_dir / 'verification_record.full-v1.4.1.json')
    if budget_stop:
        raise TaskBudgetStop(result, stop_termination)
    return result
