"""Ledger instrumentation around the unchanged native DeepSeek/UM routes."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')

import litellm
import yaml
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.actions_toolcall import BASH_TOOL

from reliability.provider_spend import AuthStop
from reliability.umgpt import ACTIVE, Runtime
from reliability.umgpt_spend import BudgetCap


def prices(config):
    if 'pricing' in config:
        return {key: float(config['pricing'][key]) for key in
                ('input_per_million', 'cached_input_per_million', 'output_per_million')}
    entry = litellm.model_cost.get(config['model_id'])
    if not entry:
        raise ValueError('Model needs explicit per-call pricing in its config')
    return {'input_per_million': float(entry['input_cost_per_token']) * 1_000_000,
            'cached_input_per_million': float(entry.get('cache_read_input_token_cost', entry['input_cost_per_token'])) * 1_000_000,
            'output_per_million': float(entry['output_cost_per_token']) * 1_000_000}


@contextmanager
def paid_stage(config, ledger, task, stage, cap):
    with ledger.stage(task, stage, cap):
        runtime = Runtime(ledger, task, cap, stage)
        token = ACTIVE.set(runtime)
        try:
            yield runtime
            if runtime.halt:
                if runtime.halt['termination'] == 'AUTH_ERROR':
                    raise AuthStop('AUTH_ERROR')
                raise BudgetCap(runtime.halt['termination'])
        finally:
            ACTIVE.reset(token)


def model_options(path):
    config = yaml.safe_load(Path(path).read_text())
    if config['provider'] == 'umgpt':
        return {'model_class': 'reliability.umgpt.UMModel', 'umgpt_config': str(Path(path).resolve())}
    if config['provider'] != 'deepseek':
        raise ValueError('Unsupported paid provider')
    return {'model_class': 'reliability.paid_models.DeepSeekLedgerModel',
            'provider_config': str(Path(path).resolve()),
            'model_kwargs': {**config.get('model_kwargs', {}), 'temperature': config.get('temperature', 0.0),
                             'top_p': config.get('top_p', 1.0), 'max_tokens': config['max_output_tokens'], 'num_retries': 0},
            'cost_tracking': 'ignore_errors'}


class DeepSeekLedgerModel(LitellmModel):
    abort_exceptions = [*LitellmModel.abort_exceptions, BudgetCap, AuthStop]

    def __init__(self, provider_config, **kwargs):
        self.route = yaml.safe_load(Path(provider_config).read_text())
        if self.route['provider'] != 'deepseek' or kwargs.get('model_name') != self.route['model_id']:
            raise ValueError('DeepSeek route/model configuration mismatch')
        self.prices = prices(self.route)
        super().__init__(**kwargs)

    def _query(self, messages, **kwargs):
        runtime = ACTIVE.get()
        if runtime is None or runtime.ledger.provider != 'deepseek':
            raise BudgetCap('DeepSeek calls require the active account ledger')
        if runtime.halt:
            raise BudgetCap(runtime.halt['termination'])
        bound_in = len(json.dumps([messages, BASH_TOOL], ensure_ascii=False).encode()) + 2048
        bound_out = int(self.route['max_output_tokens'])
        bound = (bound_in * self.prices['input_per_million'] + bound_out * self.prices['output_per_million']) / 1_000_000
        try:
            call_id = runtime.ledger.reserve(bound, task=runtime.task, task_cap=runtime.task_cap,
                                             stage=runtime.stage, model_id=self.route['model_id'])
        except BudgetCap:
            runtime.halt = {'termination': 'BUDGET_CAP', 'classification': 'infrastructure'}
            raise
        try:
            response = super()._query(messages, **kwargs)
        except Exception as exc:
            code = getattr(exc, 'status_code', None)
            message = str(exc).casefold()
            budget = code == 402 or 'insufficient balance' in message or 'insufficient_balance' in message
            auth = code in (401, 403)
            if code is not None and 400 <= code < 500:
                runtime.ledger.settle(call_id, 0.0, error_type=type(exc).__name__, status_code=code)
            runtime.halt = {'termination': 'BUDGET_CAP' if budget else 'AUTH_ERROR' if auth else 'API_ERROR',
                            'classification': 'infrastructure', 'status_code': code}
            if auth:
                raise AuthStop('DeepSeek authentication stopped') from None
            if budget:
                raise BudgetCap('DeepSeek balance exhausted') from None
            raise BudgetCap('Ambiguous DeepSeek request; reservation retained') from None
        usage = response.model_dump().get('usage') or {}
        incoming, outgoing = usage.get('prompt_tokens'), usage.get('completion_tokens')
        cached = usage.get('prompt_cache_hit_tokens', (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0)) or 0
        if (not all(type(v) is int for v in (incoming, outgoing, cached)) or
            min(incoming, outgoing, cached) < 0 or cached > incoming):
            runtime.halt = {'termination': 'BUDGET_CAP', 'classification': 'infrastructure'}
            raise BudgetCap('Missing/invalid DeepSeek billed usage; reservation retained')
        cost = ((incoming - cached) * self.prices['input_per_million'] + cached * self.prices['cached_input_per_million']
                + outgoing * self.prices['output_per_million']) / 1_000_000
        call = {'input_tokens': incoming, 'cached_input_tokens': cached, 'output_tokens': outgoing,
                'provider': 'deepseek', 'model_id': self.route['model_id'], 'stage': runtime.stage,
                'unit_prices': self.prices}
        try:
            runtime.ledger.settle(call_id, cost, **call)
        except BudgetCap:
            runtime.halt = {'termination': 'BUDGET_CAP', 'classification': 'infrastructure'}
            raise
        runtime.calls.append(dict(call, id=call_id, cost_usd=cost))
        response._hidden_params['ledger_cost_usd'] = cost
        return response

    def _calculate_cost(self, response):
        return {'cost': response._hidden_params['ledger_cost_usd']}
