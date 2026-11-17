"""Offline regressions for provider retries and empty-patch routing."""

import json
from contextlib import contextmanager
from types import SimpleNamespace

import litellm
import pytest
import yaml
from minisweagent.agents.default import DefaultAgent
from minisweagent.exceptions import Submitted
from minisweagent.models import litellm_model

from reliability import e2e_models, e2e_runner
from reliability.agent.freeze import freeze_patch, is_frozen
from reliability.agent.runner import AgentLimits
from reliability.paid_models import DeepSeekLedgerModel, ProviderStageError, model_options, paid_stage
from reliability.provider_errors import ProviderTransientError
from reliability.provider_spend import AuthStop, ProviderLedger
from reliability.umgpt import UMInfrastructureError, UMModel
from reliability.umgpt_spend import BudgetCap
from reliability.verifier.decision import Decision, SignalOutcome
from reliability.verifier.run_v1_4_1 import default_reproduction_setup, verify_task
from reliability.verifier.task_specs import ROOT


PATCH = 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new\n'


@pytest.fixture(params=['deepseek', 'umgpt'])
def route(request, tmp_path, monkeypatch):
    provider = request.param
    source = ROOT / ('configs/model/primary.yaml' if provider == 'deepseek'
                     else 'configs/model/primary_umgpt.yaml')
    cfg = yaml.safe_load(source.read_text())
    path = tmp_path / 'route.yaml'
    path.write_text(yaml.safe_dump(cfg))
    options = model_options(path)
    options.pop('model_class')
    cls = DeepSeekLedgerModel if provider == 'deepseek' else UMModel
    model = cls(model_name=cfg['model_id'], **options)
    ledger = ProviderLedger(tmp_path / 'ledger.json', provider=provider, job='unit',
                            total_usd=20, job_usd=20)
    monkeypatch.setenv('UMGPT_API_KEY', 'offline-unit-only')
    monkeypatch.delenv('MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT', raising=False)
    waits = []
    native_retry = litellm_model.retry
    def no_sleep(**kwargs):
        retry = native_retry(**kwargs)
        retry.sleep = lambda seconds: waits.append(float(seconds))
        return retry
    monkeypatch.setattr(litellm_model, 'retry', no_sleep)
    return cfg, path, model, ledger, waits


def response(command='true'):
    return litellm.ModelResponse(model='offline-unit', choices=[{
        'index': 0, 'finish_reason': 'tool_calls', 'message': {
            'role': 'assistant', 'content': 'continue', 'tool_calls': [{
                'id': 'call-unit', 'type': 'function', 'function': {
                    'name': 'bash', 'arguments': json.dumps({'command': command})}}]}}],
        usage={'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110})


def failure(kind, body='temporary provider failure'):
    if isinstance(kind, int):
        exc = RuntimeError(body)
        exc.status_code = kind
        return exc
    return getattr(litellm, kind)(body, model='offline-unit', llm_provider='openai')


@pytest.mark.parametrize('stage', ['agent', 'V4'])
@pytest.mark.parametrize('kind', [408, 429, 500, 502, 503, 504, 'Timeout',
                                  'RateLimitError', 'APIConnectionError', 'ServiceUnavailableError'])
def test_transient_attempt_keeps_bound_then_scaffold_retries(route, monkeypatch, stage, kind):
    cfg, _, model, ledger, waits = route
    attempts, bounds = [], []
    reserve = ledger.reserve
    def capture_bound(amount, **kwargs):
        bounds.append(amount)
        return reserve(amount, **kwargs)
    monkeypatch.setattr(ledger, 'reserve', capture_bound)
    def completion(**kwargs):
        attempts.append(kwargs)
        if len(attempts) == 1:
            raise failure(kind, 'rate limit exceeded; try again')
        return response()
    monkeypatch.setattr(litellm, 'completion', completion)
    with paid_stage(cfg, ledger, 'demo__repo-1', stage, 2) as runtime:
        result = model.query([{'role': 'user', 'content': 'issue'}])
        assert runtime.halt is None
    assert len(attempts) == 2 and waits == [4]
    assert result['extra']['actions'][0]['command'] == 'true'
    calls = ledger.snapshot()['calls']
    assert len(calls) == 2
    assert calls[0]['reservation_retained'] is True
    assert calls[0]['cost_usd'] == bounds[0]
    assert calls[0]['cost_usd'] > calls[1]['cost_usd'] > 0
    assert not any(isinstance(ProviderTransientError('Timeout', 408), t)
                   for t in model.abort_exceptions)


@pytest.mark.parametrize('status,body,termination', [
    (401, 'bad key', 'AUTH_ERROR'), (403, 'forbidden', 'AUTH_ERROR'),
    (402, 'payment required', 'BUDGET_CAP'), (400, 'Insufficient Balance', 'BUDGET_CAP'),
    (429, 'quota exhausted', 'BUDGET_CAP'), (429, 'balance exhausted', 'BUDGET_CAP'),
    (400, 'invalid request', 'API_ERROR'), (400, 'context length exceeded', 'API_ERROR')])
def test_permanent_errors_keep_existing_stop_semantics(route, monkeypatch, status, body, termination):
    cfg, _, model, ledger, waits = route
    calls = []
    def completion(**kwargs):
        calls.append(kwargs)
        raise failure(status, body)
    monkeypatch.setattr(litellm, 'completion', completion)
    expected = UMInfrastructureError if cfg['provider'] == 'umgpt' else {
        'AUTH_ERROR': AuthStop, 'BUDGET_CAP': BudgetCap, 'API_ERROR': ProviderStageError}[termination]
    with pytest.raises(expected):
        with paid_stage(cfg, ledger, 'demo__repo-1', 'agent', 2) as runtime:
            model.query([])
    assert runtime.halt['termination'] == termination
    assert len(calls) == 1 and waits == []
    assert ledger.snapshot()['calls'][0]['cost_usd'] == 0


def test_timeout_on_call_k_continues_real_agent_trajectory(route, monkeypatch):
    cfg, _, model, ledger, waits = route
    calls = []
    def completion(**kwargs):
        calls.append(kwargs)
        if len(calls) == 11:
            raise failure('Timeout')
        return response('submit' if len(calls) == 13 else 'true')
    monkeypatch.setattr(litellm, 'completion', completion)
    class Environment:
        def get_template_vars(self):
            return {}
        def serialize(self):
            return {}
        def execute(self, action):
            if action['command'] == 'submit':
                raise Submitted({'role': 'exit', 'content': '', 'extra': {
                    'exit_status': 'Submitted', 'submission': PATCH}})
            return {'returncode': 0, 'output': 'continued', 'exception_info': ''}
    agent = DefaultAgent(model, Environment(), system_template='system', instance_template='{{task}}')
    with paid_stage(cfg, ledger, 'demo__repo-1', 'agent', 2) as runtime:
        result = agent.run('issue')
        assert runtime.halt is None
    assert result['exit_status'] == 'Submitted' and result['submission'] == PATCH
    assert agent.n_calls == 12 and len(calls) == 13 and waits == [4]
    assert sum(c.get('reservation_retained', False) for c in ledger.snapshot()['calls']) == 1
    assert sum(m['role'] == 'assistant' for m in agent.messages) == 12


@pytest.mark.parametrize('generator,patch,returncode', [
    (False, PATCH, 0), (False, '', 0), (False, PATCH, 1), (True, '', 0)])
def test_exhausted_retries_capture_diff_or_abort_v4(route, monkeypatch, tmp_path, generator, patch, returncode):
    cfg, path, model, ledger, waits = route
    attempts, commands, lifecycle = [], [], []
    def completion(**kwargs):
        attempts.append(kwargs)
        raise failure('Timeout')
    monkeypatch.setattr(litellm, 'completion', completion)
    @contextmanager
    def pristine(*args, **kwargs):
        try:
            yield object()
        finally:
            lifecycle.append('container closed')
    class Environment:
        def get_template_vars(self):
            return {}
        def serialize(self):
            return {}
        def execute(self, action):
            commands.append(action['command'])
            assert not lifecycle
            return {'returncode': returncode, 'output': patch}
    env = Environment()
    agent = DefaultAgent(model, env, system_template='system', instance_template='{{task}}')
    monkeypatch.setattr(e2e_models, 'pristine', pristine)
    monkeypatch.setattr(e2e_models, 'attached_environment', lambda *a: env)
    monkeypatch.setattr(e2e_models, 'configured_agent', lambda *a: agent)
    monkeypatch.setattr(e2e_models, '_read_out', lambda *a: pytest.fail('incomplete V4 suite'))
    task = SimpleNamespace(instance_id='demo__repo-1', problem_statement='issue')
    with pytest.raises(ProviderTransientError):
        with paid_stage(cfg, ledger, task.instance_id, 'V4' if generator else 'agent', 2) as runtime:
            if generator:
                setup = default_reproduction_setup()
                e2e_models.PinnedGenerator(task, setup, path, tmp_path, 'unit').generate('issue', task.instance_id)
            else:
                e2e_models.PinnedBackend(model_id=cfg['model_id'], task_spec=task,
                    model_config_path=path, agent_config_path=ROOT / 'configs/agent/swebench_claim.yaml'
                ).run(task, tmp_path, AgentLimits())
    assert runtime.halt is None and len(attempts) == 10
    assert lifecycle == ['container closed']
    assert waits == [4, 4, 4, 8, 16, 32, 60, 60, 60]
    assert sum(c.get('reservation_retained', False) for c in ledger.snapshot()['calls']) == 10
    if not generator:
        assert commands == ['git diff --']
        if returncode:
            assert not (tmp_path / 'patch.diff').exists()
        else:
            assert (tmp_path / 'patch.diff').read_bytes() == patch.encode()
            assert is_frozen(tmp_path / 'patch.diff')
        assert json.loads((tmp_path / 'agent_absence.json').read_text()) == {
            'reason': 'AGENT_INFRA:Timeout', 'infrastructure': True}
        assert json.loads((tmp_path / 'trajectory.jsonl').read_text().splitlines()[-1])['role'] == 'exit'


@pytest.mark.parametrize('patch', [b'', b' \n\t\r\n'])
@pytest.mark.parametrize('skip_v4', [False, True])
def test_empty_patch_cannot_start_containers_or_v4(tmp_path, monkeypatch, patch, skip_v4):
    from reliability.verifier import run_v1_4_1 as runtime
    def forbidden(*args, **kwargs):
        pytest.fail('empty patch must not start any executor or paid V4')
    for name in ('run_v2', 'run_v3', 'FrozenContainer', 'guarded_pair'):
        monkeypatch.setattr(runtime, name, forbidden)
    freeze_patch(tmp_path / 'patch.diff', patch)
    record = verify_task(tmp_path, instance_id='demo__repo-1', task_spec=None,
        experiment_id='unit', v4_runner=forbidden, skip_v4=skip_v4)
    assert record.integrity.outcome is SignalOutcome.FAIL
    assert record.decision.decision is Decision.REJECT
    assert record.decision.policy_version == 'v1.4.1-full'
    assert record.v4_run_status == 'NOT_RUN'
    for signal in (record.regression, record.static, record.reproduction):
        assert signal.outcome is SignalOutcome.NOT_AVAILABLE
        assert signal.findings == {'absence_reason': 'EMPTY_PATCH', 'infrastructure': False}
    assert not e2e_runner.infrastructure(record)


def test_empty_patch_batch_continues_and_reports_repair_infrastructure_separately(tmp_path, monkeypatch):
    monkeypatch.setattr(e2e_runner, 'ROOT', tmp_path)
    output = tmp_path / 'runs/empty'
    ids = [f'demo__repo-{i}' for i in range(10)]
    def agent(iid, directory):
        freeze_patch(directory / 'patch.diff', b'')
        if iid == ids[0]:
            (directory / 'agent_absence.json').write_text(json.dumps({
                'reason': 'AGENT_INFRA:Timeout', 'infrastructure': True}))
    def verify(iid, directory):
        return verify_task(directory, instance_id=iid, task_spec=None, experiment_id='unit',
                           v4_runner=lambda *a: pytest.fail('paid V4 on empty patch'))
    assert e2e_runner.run_batch(ids, output, {'skip_v4': False}, agent, verify) == 'COMPLETE'
    done = json.loads((output / 'completion.json').read_text())
    assert done['completed_tasks'] == ids
    assert done['agent_infrastructure_tasks'] == ids[:1]
    assert done['no_patch_tasks'] == ids[1:]
