import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from reliability.agent.freeze import freeze_patch
from reliability import e2e_runner
from reliability.umgpt_spend import BudgetCap
from reliability.provider_spend import AuthStop
from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.guarded_v2 import ReplayMismatch
from reliability.verifier.policy_v1_4 import EvidenceV14, FullPolicyV14
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.record import SignalKind, SignalRecord
from reliability.verifier.run_health import RunHealthError
from reliability.verifier.run_v1_4_1 import TaskBudgetStop, TaskWallTime, verify_task
from reliability.verifier.selection import TestRunner
from reliability.verifier.source_integrity import BaseSourceSpec, SourceIntegrityError

PATCH = 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-def f(): return 1\n+def f(): return 2\n'


@pytest.fixture
def task(tmp_path):
    archive = tmp_path / 'base.tar'
    with tarfile.open(archive, 'w') as stream:
        for name, text in {'foo.py': 'def f(): return 1\n',
                           'tests/test_foo.py': 'from foo import f\ndef test_f(): assert f() == 1\n'}.items():
            data = text.encode()
            member = tarfile.TarInfo('testbed/' + name)
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
    return SimpleNamespace(instance_id='demo__repo-1', image_id='sha256:' + 'a' * 64,
        source=BaseSourceSpec('a' * 40, archive, 'b' * 64), runner=TestRunner('pytest', 'fixture'))


def good(kind):
    return SignalRecord(kind=kind, outcome=SignalOutcome.PASS,
                        findings={'summary': {'syntax': 'PASS', 'import': 'PASS'}} if kind is SignalKind.STATIC else {})


def verify(directory, task, *, failure=None, v4_failure=None):
    called = []
    def v2(*args, **kwargs):
        called.append('V2')
        if failure:
            raise failure
        return good(SignalKind.REGRESSION)
    def v3(*args, **kwargs):
        called.append('V3')
        return good(SignalKind.STATIC)
    def v4(*args):
        called.append('V4')
        if v4_failure:
            raise v4_failure
        return good(SignalKind.REPRODUCTION)
    result = verify_task(directory, instance_id=task.instance_id, task_spec=task,
        experiment_id='mock', v2_runner=v2, v3_runner=v3, v4_runner=v4, drift={})
    return result, called


@pytest.mark.parametrize('failure,reason', [
    (RunHealthError({'halt': True, 'halt_reasons': ['injected']}), 'RUN_HEALTH:'),
    (ReplayMismatch('unrecorded'), 'REPLAY_MISMATCH'),
    (OSError('executor'), 'EXECUTOR_EXCEPTION:OSError'),
    (TaskWallTime(), 'V2_WALL_TIME_3H'),
])
def test_v2_absence_cannot_accept_and_continues_v3_v4(tmp_path, task, failure, reason):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record, called = verify(tmp_path, task, failure=failure)
    assert record.regression.outcome is SignalOutcome.NOT_AVAILABLE
    assert record.regression.detail.startswith(reason)
    assert record.decision.decision is Decision.FLAG
    assert called == ['V2', 'V3', 'V4']
    assert record.decision.policy_version == 'v1.4.1-full'


def test_no_task_spec_gives_both_absences(tmp_path):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    record = verify_task(tmp_path, instance_id='demo__repo-1', task_spec=None,
                         experiment_id='mock', skip_v4=True)
    assert record.regression.detail == record.static.detail == 'NO_TASK_SPEC'
    assert record.regression.outcome is record.static.outcome is SignalOutcome.NOT_AVAILABLE


def test_verification_preserves_frozen_patch_line_endings(tmp_path, task, monkeypatch):
    from reliability.verifier import run_v1_4_1 as runtime
    raw = PATCH.replace('\n', '\r\n').encode()
    frozen = freeze_patch(tmp_path / 'patch.diff', raw)
    seen, original = [], runtime.integrity_signal
    def integrity(text, tree):
        seen.append(text.encode())
        return original(text, tree)
    monkeypatch.setattr(runtime, 'integrity_signal', integrity)
    record, _ = verify(tmp_path, task)
    assert seen == [raw]
    assert record.patch_sha256 == frozen.sha256


def test_version_subclass_changes_only_version():
    evidence = EvidenceV14(integrity=SignalOutcome.PASS, regression=SignalOutcome.NOT_AVAILABLE,
        static=SignalOutcome.PASS, reproduction=SignalOutcome.PASS)
    old, new = FullPolicyV14().decide(evidence).as_dict(), FullPolicyV141().decide(evidence).as_dict()
    assert new['decision'] == 'FLAG'
    assert {k: v for k, v in old.items() if k != 'policy_version'} == {
        k: v for k, v in new.items() if k != 'policy_version'}


def test_source_integrity_is_not_converted_to_a_task_absence(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    error = SourceIntegrityError({'mismatches': [{'path': 'foo.py', 'reason': 'bytes'}]})
    with pytest.raises(SourceIntegrityError):
        verify(tmp_path, task, failure=error)


def test_v4_budget_stop_writes_not_run_record_before_stopping(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    with pytest.raises(TaskBudgetStop) as stopped:
        verify(tmp_path, task, v4_failure=BudgetCap('preflight'))
    assert stopped.value.record.v4_run_status == 'NOT_RUN'
    assert stopped.value.record.reproduction.detail == 'BUDGET_STOP'
    assert (tmp_path / 'verification_record.full-v1.4.1.json').exists()


def test_paid_v4_stop_does_not_claim_generation_never_started(tmp_path, task):
    freeze_patch(tmp_path / 'patch.diff', PATCH)
    error = BudgetCap('provider balance stopped after paid calls')
    error.paid_calls = 1
    with pytest.raises(TaskBudgetStop) as stopped:
        verify(tmp_path, task, v4_failure=error)
    assert stopped.value.record.v4_run_status == 'PARTIAL'
    assert stopped.value.record.decision.decision is Decision.FLAG


def test_skip_v4_is_refused_in_audited_mode():
    with pytest.raises(ValueError, match='refused in audited'):
        e2e_runner.validate_mode('audited', 'unused', Path('/tmp/patches'), True)


def batch(tmp_path, monkeypatch, task, *, count=4, failure=None, stop_agent=False):
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    ids = ['demo__repo-' + str(i) for i in range(count)]
    def agent(iid, directory):
        if stop_agent:
            raise stop_agent if isinstance(stop_agent, BaseException) else BudgetCap('UM cap')
        freeze_patch(directory / 'patch.diff', PATCH)
    def verification(iid, directory):
        return verify(directory, task, failure=failure)[0]
    output = tmp_path / 'runs/batch'
    status = e2e_runner.run_batch(ids, output, {'skip_v4': False}, agent, verification)
    return status, json.loads((output / 'completion.json').read_text())


def test_three_consecutive_infrastructure_absences_stop_systemically(tmp_path, monkeypatch, task):
    status, completion = batch(tmp_path, monkeypatch, task,
        failure=RunHealthError({'halt': True, 'halt_reasons': ['injected']}))
    assert status == 'STOPPED_SYSTEMIC'
    assert completion['completed_tasks'] == ['demo__repo-0', 'demo__repo-1', 'demo__repo-2']
    assert completion['not_completed_tasks'] == ['demo__repo-3']


def test_systemic_twenty_percent_rule_starts_at_ten_completed():
    assert not e2e_runner.systemic([True, False, True])
    assert not e2e_runner.systemic([True, False, True] + [False] * 6)
    assert e2e_runner.systemic([True, False, True] + [False] * 7)


def test_integrity_abort_writes_completion_and_receipt(tmp_path, monkeypatch, task):
    error = SourceIntegrityError({'mismatches': [{'path': 'foo.py', 'reason': 'bytes'}]})
    status, completion = batch(tmp_path, monkeypatch, task, failure=error)
    assert status == 'ABORTED_INTEGRITY'
    assert completion['completed_tasks'] == []
    assert len(completion['not_completed_tasks']) == 4
    assert (tmp_path / 'runs/batch/integrity_abort.json').exists()


@pytest.mark.parametrize('error,expected', [(BudgetCap('UM cap'), 'STOPPED_BUDGET'), (AuthStop('UM auth'), 'STOPPED_AUTH')])
def test_um_budget_stop_ends_batch_cleanly(tmp_path, monkeypatch, task, error, expected):
    status, completion = batch(tmp_path, monkeypatch, task, stop_agent=error)
    assert status == expected
    assert completion['completed_tasks'] == []
    assert len(completion['not_completed_tasks']) == 4


def test_resume_reuses_frozen_patch_and_archives_partial_verification(tmp_path, monkeypatch, task):
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    output, calls = tmp_path / 'runs/resume', []
    def agent(iid, directory):
        calls.append('agent')
        freeze_patch(directory / 'patch.diff', PATCH)
    def interrupted(iid, directory):
        (directory / 'verification').mkdir()
        (directory / 'verification/partial.json').write_text('{}')
        raise KeyboardInterrupt
    ids, header = ['demo__repo-1'], {'skip_v4': False}
    assert e2e_runner.run_batch(ids, output, header, agent, interrupted) == 'STOPPED_INTERRUPT'
    def complete(iid, directory):
        return verify(directory, task)[0]
    assert e2e_runner.run_batch(ids, output, header, agent, complete) == 'COMPLETE'
    assert calls == ['agent']
    assert (output / 'tasks/demo__repo-1/attempts/verification_0001/verification/partial.json').exists()
    attempts = json.loads((output / 'attempt.json').read_text())['attempts']
    assert len(attempts) == 2 and attempts[1]['resumed']


def test_v4_budget_stop_keeps_task_incomplete_and_resume_archives_record(tmp_path, monkeypatch, task):
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    output, calls = tmp_path / 'runs/resume_budget', []
    def agent(iid, directory):
        calls.append('agent')
        freeze_patch(directory / 'patch.diff', PATCH)
    def stopped(iid, directory):
        return verify(directory, task, v4_failure=BudgetCap('not enough for full V4'))[0]
    header, ids = {'skip_v4': False}, ['demo__repo-1']
    assert e2e_runner.run_batch(ids, output, header, agent, stopped) == 'STOPPED_BUDGET'
    completion = json.loads((output / 'completion.json').read_text())
    assert completion['completed_tasks'] == [] and completion['not_completed_tasks'] == ids
    def complete(iid, directory):
        return verify(directory, task)[0]
    assert e2e_runner.run_batch(ids, output, header, agent, complete) == 'COMPLETE'
    assert calls == ['agent']
    archived = output / 'tasks/demo__repo-1/attempts/verification_0001'
    assert (archived / 'verification_record.full-v1.4.1.json').exists()
    assert not json.loads((archived / 'task_completion.json').read_text())['complete']


def test_sigterm_writes_completion_without_losing_frozen_patch(tmp_path, monkeypatch):
    import signal
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    output = tmp_path / 'runs/terminated'
    def agent(iid, directory):
        freeze_patch(directory / 'patch.diff', PATCH)
    def terminate(iid, directory):
        signal.raise_signal(signal.SIGTERM)
    status = e2e_runner.run_batch(['demo__repo-1'], output, {'skip_v4': False}, agent, terminate)
    assert status == 'STOPPED_INTERRUPT'
    completion = json.loads((output / 'completion.json').read_text())
    assert completion['not_completed_tasks'] == ['demo__repo-1']
    assert (output / 'seal.json').exists()
    assert e2e_runner.frozen_patch(output / 'tasks/demo__repo-1') is not None
