"""Serial E2E orchestration, sealed patches, resumable verification and stops."""

from __future__ import annotations

import json
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from reliability.agent.freeze import FrozenPatch, freeze_patch, is_frozen, read_patch
from reliability.umgpt_spend import BudgetCap
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.record import SignalKind
from reliability.verifier.run_v1_4_1 import TaskBudgetStop, VerificationRecordV141
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import ROOT, sha, write


def now():
    return datetime.now(UTC).isoformat()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def require_frozen_head(tag):
    if not tag or git('cat-file', '-t', 'refs/tags/' + tag) != 'tag':
        raise ValueError('Audited mode requires an annotated freeze tag')
    head = git('rev-parse', 'HEAD')
    if git('rev-parse', 'refs/tags/' + tag + '^{}') != head or git('status', '--porcelain'):
        raise ValueError('Audited mode requires clean HEAD at the freeze tag')
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


def systemic(flags):
    return (len(flags) >= 3 and all(flags[-3:])) or (len(flags) >= 10 and sum(flags) / len(flags) >= .2)


def run_batch(instance_ids, output, header, agent_stage, verify_stage):
    """All stop paths persist completion; a complete patch is never regenerated."""
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / 'runs').resolve()):
        raise ValueError('--output must be under runs/')
    output.mkdir(parents=True, exist_ok=True)
    header_path = output / 'header.json'
    resumed = header_path.exists()
    if resumed:
        if json.loads(header_path.read_text()) != header:
            raise ValueError('Resume requires identical HEAD, manifest, configs, registries and caps')
    else:
        if any(output.iterdir()):
            raise ValueError('New run output must be empty')
        write(header_path, header)
    attempts_path = output / 'attempt.json'
    attempts = json.loads(attempts_path.read_text()) if attempts_path.exists() else {'attempts': []}
    attempt = {'index': len(attempts['attempts']) + 1, 'resumed': resumed, 'started_utc': now(), 'tasks': []}
    attempts['attempts'].append(attempt)
    write(attempts_path, attempts)
    completed, flags, current = [], [], None
    status, error = 'COMPLETE', None
    def terminate(*args):
        raise KeyboardInterrupt
    previous_termination = signal.signal(signal.SIGTERM, terminate)
    try:
        for iid in instance_ids:
            current = iid
            directory = output / 'tasks' / iid
            done = directory / 'task_completion.json'
            if done.exists() and json.loads(done.read_text()).get('complete'):
                frozen_patch(directory)
                record = VerificationRecordV141.read(directory / 'verification_record.full-v1.4.1.json')
                completed.append(iid)
                flags.append(infrastructure(record))
                if systemic(flags):
                    status = 'STOPPED_SYSTEMIC'
                    break
                continue
            ensure_patch(iid, directory, agent_stage)
            archived = restart_verification(directory)
            attempt['tasks'].append({'instance_id': iid, 'previous_verification': archived,
                                     'patch_sha256': sha(directory / 'patch.diff'), 'started_utc': now()})
            write(attempts_path, attempts)
            stop = None
            try:
                record = verify_stage(iid, directory)
            except TaskBudgetStop as exc:
                record, stop = exc.record, exc
            write(done, {'complete': stop is None, 'completed_utc': now(), 'skip_v4': header['skip_v4'],
                         'patch_sha256': record.patch_sha256, 'infrastructure': infrastructure(record)})
            if stop:
                raise stop
            completed.append(iid)
            flags.append(infrastructure(record))
            if systemic(flags):
                status = 'STOPPED_SYSTEMIC'
                break
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
        attempt.update(status=status, error=error, finished_utc=now())
        write(attempts_path, attempts)
        write(output / 'completion.json', {'status': status, 'completed_tasks': completed,
              'not_completed_tasks': [iid for iid in instance_ids if iid not in completed],
              'current_task': current, 'error': error, 'skip_v4': header['skip_v4']})
        write(output / 'seal.json', {'status': status, 'files_sha256': {
            str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
            if p.is_file() and p.name != 'seal.json'}})
    return status
