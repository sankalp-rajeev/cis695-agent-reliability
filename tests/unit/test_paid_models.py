from types import SimpleNamespace

import pytest
import yaml
from minisweagent.models.litellm_model import LitellmModel

from reliability.paid_models import DeepSeekLedgerModel, ProviderStageError, paid_stage, prices
from reliability.provider_spend import ProviderLedger
from reliability.umgpt_spend import BudgetCap


@pytest.fixture
def configured(tmp_path):
    config = {'provider': 'deepseek', 'model_id': 'deepseek/deepseek-v4-flash', 'max_output_tokens': 100,
              'pricing': {'input_per_million': 1, 'cached_input_per_million': .1, 'output_per_million': 2}}
    path = tmp_path / 'model.yaml'
    path.write_text(yaml.safe_dump(config))
    model = DeepSeekLedgerModel(path, model_name=config['model_id'])
    ledger = ProviderLedger(tmp_path / 'ledger.json', provider='deepseek', job='arm', total_usd=4, job_usd=4)
    return config, model, ledger


def test_native_deepseek_response_usage_is_accounted_per_call(configured, monkeypatch):
    config, model, ledger = configured
    response = SimpleNamespace(model_dump=lambda: {'usage': {
        'prompt_tokens': 100, 'completion_tokens': 10, 'prompt_cache_hit_tokens': 20}}, _hidden_params={})
    calls = []
    def query(self, messages, **kwargs):
        calls.append(messages)
        return response
    monkeypatch.setattr(LitellmModel, '_query', query)
    with paid_stage(config, ledger, 'demo__repo-1', 'V4', 1):
        assert model._query([{'role': 'user', 'content': 'test'}]) is response
    recorded = ledger.snapshot()['calls']
    assert len(calls) == len(recorded) == 1
    assert recorded[0]['cost_usd'] == pytest.approx(.000102)
    assert recorded[0]['input_tokens'] == 100 and recorded[0]['cached_input_tokens'] == 20


@pytest.mark.parametrize('status,body', [(402, 'Payment required'), (400, 'Insufficient Balance')])
def test_deepseek_balance_response_stops_the_batch(configured, monkeypatch, status, body):
    config, model, ledger = configured
    error = RuntimeError(body)
    error.status_code = status
    def query(*args, **kwargs):
        raise error
    monkeypatch.setattr(LitellmModel, '_query', query)
    with pytest.raises(BudgetCap, match='balance exhausted'):
        with paid_stage(config, ledger, 'demo__repo-1', 'V4', 1):
            model._query([])
    assert ledger.snapshot()['calls'][0]['cost_usd'] == 0


def test_deepseek_without_active_ledger_cannot_make_a_call(configured, monkeypatch):
    _, model, _ = configured
    monkeypatch.setattr(LitellmModel, '_query', lambda *a, **k: pytest.fail('unguarded call'))
    with pytest.raises(BudgetCap, match='active account ledger'):
        model._query([])


def test_non_budget_provider_rejection_is_a_stage_failure(configured, monkeypatch):
    config, model, ledger = configured
    error = RuntimeError('invalid request')
    error.status_code = 400
    def query(*args, **kwargs):
        raise error
    monkeypatch.setattr(LitellmModel, '_query', query)
    with pytest.raises(ProviderStageError):
        with paid_stage(config, ledger, 'demo__repo-1', 'V4', 1):
            model._query([])
    assert ledger.snapshot()['calls'][0]['cost_usd'] == 0


def test_invalid_pricing_is_refused_before_a_paid_request():
    with pytest.raises(ValueError, match='Invalid per-call pricing'):
        prices({'pricing': {'input_per_million': 1, 'cached_input_per_million': -1, 'output_per_million': 2}})
