"""Serial E2E orchestration, sealed patches, resumable verification and stops."""

from __future__ import annotations

import json
import shutil
import signal
import subprocess
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path

from reliability.agent.freeze import FrozenPatch, freeze_patch, is_frozen, read_patch
from reliability.provider_spend import account_totals
from reliability.umgpt_spend import BudgetCap
from reliability.verifier import container as containers
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalKind
from reliability.verifier.run_v1_4_1 import TaskBudgetStop, VerificationRecordV141
from reliability.verifier.reproduction_reuse import V4ReuseError
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import ROOT, sha, write


def now():
    return datetime.now(UTC).isoformat()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def require_frozen_head(tag):
    """A clean HEAD at the annotated freeze tag, or a descendant of it whose every change
    since the tag is under reports/ (report commits between audited runs, amendment B10)."""
    if not tag or git('cat-file', '-t', 'refs/tags/' + tag) != 'tag':
        raise ValueError('Audited mode requires an annotated freeze tag')
    head = git('rev-parse', 'HEAD')
    frozen = git('rev-parse', 'refs/tags/' + tag + '^{}')
    if git('status', '--porcelain'):
        raise ValueError('Audited mode requires clean HEAD at the freeze tag')
    if frozen != head:
        descends = subprocess.run(['git', 'merge-base', '--is-ancestor', frozen, head], cwd=ROOT,
                                  capture_output=True, check=False).returncode == 0
        changed = git('diff', '--name-only', frozen, head).splitlines() if descends else ['?']
        if not descends or any(not path.startswith('reports/') for path in changed):
            raise ValueError('Audited mode requires clean HEAD at the freeze tag '
                             '(or only report commits after it)')
    return head


def validate_mode(mode, freeze_tag, verify_only_from, skip_v4):
    if mode == 'audited':
        if skip_v4:
            raise ValueError('--skip-v4 is refused in audited mode')
        require_frozen_head(freeze_tag)
    elif freeze_tag:
        raise ValueError('--freeze-tag is for audited mode only')
    if skip_v4 and verify_only_from is None:
        raise ValueError('--skip-v4 is for verification-only checks')


def frozen_patch(task_dir):
    path = task_dir / 'patch.diff'
    if not path.exists():
        return None
    if not is_frozen(path):
        raise SourceIntegrityError({'mismatches': [{'path': 'patch.diff', 'reason': 'frozen patch is writable'}]})
    marker = task_dir / 'frozen_patch.json'
    data = json.loads(marker.read_text()) if marker.exists() else {
        'sha256': 'sha256:' + sha(path), 'size_bytes': path.stat().st_size}
    patch = FrozenPatch(path, data['sha256'], data['size_bytes'])
    try:
        read_patch(patch)
    except Exception as exc:
        raise SourceIntegrityError({'mismatches': [{'path': 'patch.diff', 'reason': type(exc).__name__}]}) from exc
    if not marker.exists():
        write(marker, data)
    return patch


def ensure_patch(instance_id, task_dir, agent_stage):
    patch = frozen_patch(task_dir)
    if patch is not None:
        return patch
    task_dir.mkdir(parents=True, exist_ok=True)
    agent_stage(instance_id, task_dir)
    patch = frozen_patch(task_dir)
    if patch is None:
        raise ValueError('Agent stage did not freeze a patch')
    return patch


def restart_verification(task_dir):
    folder = task_dir / 'verification'
    record = task_dir / 'verification_record.full-v1.4.1.json'
    provider_stop = task_dir / 'provider_stop.json'
    if not folder.exists() and not record.exists() and not provider_stop.exists():
        return None
    attempts = task_dir / 'attempts'
    attempts.mkdir(exist_ok=True)
    index = 1
    while (attempts / ('verification_' + str(index).zfill(4))).exists():
        index += 1
    destination = attempts / ('verification_' + str(index).zfill(4))
    destination.mkdir()
    if folder.exists():
        folder.rename(destination / 'verification')
    if record.exists():
        record.rename(destination / record.name)
    completion = task_dir / 'task_completion.json'
    if completion.exists():
        completion.rename(destination / completion.name)
    if provider_stop.exists():
        provider_stop.rename(destination / provider_stop.name)
    return str(destination.relative_to(task_dir))


def infrastructure(record):
    return any(record.signals[k].outcome is SignalOutcome.NOT_AVAILABLE and
               record.signals[k].findings.get('infrastructure', False)
               for k in (SignalKind.REGRESSION, SignalKind.STATIC))


MIN_FREE_BYTES = 20 * 10**9
CONSECUTIVE_START_FAILURES = 3


def _docker_info():
    """`docker info` as a dict, or None if the daemon cannot be reached."""
    try:
        proc = subprocess.run([containers._docker_bin(), 'info', '--format', '{{json .}}'],
                              capture_output=True, text=True, timeout=60, check=False)
        return json.loads(proc.stdout) if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def machine_status(output):
    """Amendment B9 (7a): the machine-level conditions that stop a run, or None.

    Only these stop a run: the Docker daemon is unreachable, or less than 20 GB is
    free where the run writes or where Docker stores containers. Consecutive
    container-start failures are counted by the run loop itself.
    """
    info = _docker_info()
    if not info:
        return 'docker daemon unreachable'
    for path in (Path(output), Path(info.get('DockerRootDir') or output)):
        try:
            free = shutil.disk_usage(path).free
        except OSError:
            continue
        if free < MIN_FREE_BYTES:
            return f'disk below 20 GB: {free / 10**9:.1f} GB free at {path}'
    return None


CAP_FIELDS = ('deepseek_cap_usd', 'um_cap_usd', 'um_job_cap_usd')


def resume_identity(header):
    return {key: value for key, value in header.items() if key not in CAP_FIELDS}


def _reuse_usage(reuse, ledgers, output):
    paths = {ledger.path: ledger for ledger in ledgers}
    calls = [call for ledger in paths.values() for call in ledger.snapshot()['calls']
             if call['job'] == str(output)]
    return {'generator_calls': reuse.generator.calls, 'ledger_calls': len(calls),
            'ledger_cost_usd': sum((call['cost_usd'] for call in calls), 0.0)}


def run_batch(instance_ids, output, header, agent_stage, verify_stage, *, ledgers=(), reuse_v4=None,
              machine_check=None):
    """All stop paths persist completion; a complete patch is never regenerated.

    Amendment B9 (7a): a task never stops the run. A task's exception is recorded on
    that task and the run moves on. Only machine-level failures stop it:
    `machine_check()` before each task (Docker daemon, disk), or three consecutive
    tasks whose container starts all failed. Budget, interrupt and run-level V4
    reuse checks are not task failures and keep their own stops.
    """
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / 'runs').resolve()):
        raise ValueError('--output must be under runs/')
    output.mkdir(parents=True, exist_ok=True)
    header_path = output / 'header.json'
    resumed = header_path.exists()
    if resumed:
        if resume_identity(json.loads(header_path.read_text())) != resume_identity(header):
            raise ValueError('Resume requires identical non-cap header fields, including ledger file')
    else:
        if any(output.iterdir()):
            raise ValueError('New run output must be empty')
        write(header_path, header)
    attempts_path = output / 'attempt.json'
    attempts = json.loads(attempts_path.read_text()) if attempts_path.exists() else {'attempts': []}
    attempt = {'index': len(attempts['attempts']) + 1, 'resumed': resumed, 'started_utc': now(),
               'caps': {key: header[key] for key in CAP_FIELDS if key in header},
               'spent_at_start': [], 'tasks': []}
    attempts['attempts'].append(attempt)
    write(attempts_path, attempts)
    completed, task_errors, current = [], [], None
    start_failure_streak = 0
    status, error = 'COMPLETE', None
    def terminate(*args):
        raise KeyboardInterrupt
    previous_termination = signal.signal(signal.SIGTERM, terminate)
    try:
        if reuse_v4 is not None and any(_reuse_usage(reuse_v4, ledgers, output).values()):
            raise V4ReuseError(output, 'V4 reuse requires zero previous generator and ledger calls')
        snapshots = {}
        for ledger in ledgers:
            if ledger.path not in snapshots:
                snapshots[ledger.path] = ledger.snapshot()
        attempt['spent_at_start'] = [dict(row, ledger_file=str(path))
            for path, data in snapshots.items() for row in account_totals(data)]
        for ledger in ledgers:
            if not any(row['ledger_file'] == str(ledger.path) and row['provider'] == ledger.provider
                       and row['account'] == ledger.account for row in attempt['spent_at_start']):
                attempt['spent_at_start'].append({'ledger_file': str(ledger.path),
                    'provider': ledger.provider, 'account': ledger.account, 'spent_usd': 0.0})
        write(attempts_path, attempts)
        budget_checked = False
        for iid in instance_ids:
            current = iid
            directory = output / 'tasks' / iid
            done = directory / 'task_completion.json'
            if done.exists() and json.loads(done.read_text()).get('complete'):
                frozen_patch(directory)
                VerificationRecordV141.read(directory / 'verification_record.full-v1.4.1.json')
                completed.append(iid)
                continue
            if machine_check is not None and (reason := machine_check()):
                status, error = 'STOPPED_MACHINE', reason
                break
            if not budget_checked:
                if reuse_v4 is None:
                    for ledger in ledgers:
                        ledger.check_current_budget(snapshots[ledger.path])
                budget_checked = True
            starts_before = len(containers.START_EVENTS)
            try:
                ensure_patch(iid, directory, agent_stage)
                archived = restart_verification(directory)
                attempt['tasks'].append({'instance_id': iid, 'previous_verification': archived,
                                         'patch_sha256': sha(directory / 'patch.diff'), 'started_utc': now()})
                write(attempts_path, attempts)
                stop = None
                try:
                    with reuse_v4.prohibit_generation() if reuse_v4 is not None else nullcontext():
                        record = verify_stage(iid, directory)
                except TaskBudgetStop as exc:
                    record, stop = exc.record, exc
                write(done, {'complete': stop is None, 'completed_utc': now(), 'skip_v4': header['skip_v4'],
                             'patch_sha256': record.patch_sha256, 'infrastructure': infrastructure(record)})
                if stop:
                    raise stop
                completed.append(iid)
            except (BudgetCap, V4ReuseError):
                # Not task failures: the spending cap, and a breach of the shared frozen V4.
                raise
            except Exception as exc:  # noqa: BLE001 - a task never stops the run (B9, 7a)
                task_errors.append(iid)
                receipt = {'instance_id': iid, 'error': type(exc).__name__ + ': ' + str(exc)[:2000],
                           'recorded_utc': now()}
                if isinstance(exc, SourceIntegrityError):
                    receipt['receipt'] = exc.receipt
                directory.mkdir(parents=True, exist_ok=True)
                write(directory / 'task_error.json', receipt)
                write(done, {'complete': False, 'completed_utc': now(), 'skip_v4': header['skip_v4'],
                             'task_error': receipt['error'], 'infrastructure': False})
            events = containers.START_EVENTS[starts_before:]
            start_failure_streak = start_failure_streak + 1 if events and not any(events) else 0
            if start_failure_streak >= CONSECUTIVE_START_FAILURES:
                status = 'STOPPED_MACHINE'
                error = f'{CONSECUTIVE_START_FAILURES} consecutive tasks with only container-start failures'
                break
        if status == 'COMPLETE' and task_errors:
            status = 'COMPLETE_WITH_TASK_ERRORS'
    except SourceIntegrityError as exc:
        status, error = 'ABORTED_INTEGRITY', str(exc)
        write(output / 'integrity_abort.json', {'instance_id': current, 'receipt': exc.receipt})
    except BudgetCap as exc:
        status = 'STOPPED_AUTH' if getattr(exc, 'termination', '') == 'AUTH_ERROR' else 'STOPPED_BUDGET'
        error = str(exc)
        if current:
            write(output / 'tasks' / current / 'provider_stop.json', {'reason': status, 'error': error})
    except KeyboardInterrupt:
        status, error = 'STOPPED_INTERRUPT', 'Interrupted'
    except Exception as exc:
        status, error = 'ABORTED_RUNNER', type(exc).__name__ + ': ' + str(exc)
    finally:
        signal.signal(signal.SIGTERM, previous_termination)
        reuse_summary = {}
        if reuse_v4 is not None:
            try:
                reuse_summary['v4_reuse'] = usage = _reuse_usage(reuse_v4, ledgers, output)
                if any(usage.values()):
                    status = 'ABORTED_INTEGRITY'
                    error = error or 'V4 reuse recorded a generator or ledger call'
            except (OSError, ValueError, KeyError, TypeError) as exc:
                status, error = 'ABORTED_INTEGRITY', 'V4 reuse ledger could not be verified: ' + str(exc)
        attempt.update(status=status, error=error, finished_utc=now())
        write(attempts_path, attempts)
        agent_infrastructure, no_patch = [], []
        for iid in instance_ids:
            directory = output / 'tasks' / iid
            receipt = directory / 'agent_absence.json'
            if receipt.exists() and json.loads(receipt.read_text()).get('infrastructure'):
                agent_infrastructure.append(iid)
            elif (directory / 'patch.diff').exists() and not (directory / 'patch.diff').read_bytes().strip():
                no_patch.append(iid)
        write(output / 'completion.json', {'status': status, 'completed_tasks': completed,
              'not_completed_tasks': [iid for iid in instance_ids if iid not in completed],
              'task_errors': task_errors,
              'current_task': current, 'error': error, 'skip_v4': header['skip_v4'],
              'agent_infrastructure_tasks': agent_infrastructure, 'no_patch_tasks': no_patch, **reuse_summary})
        write(output / 'seal.json', {'status': status, 'files_sha256': {
            str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
            if p.is_file() and p.name != 'seal.json'}})
    return status
