"""UM opt-in route: exercise real LiteLLM/OpenAI serialization without a network."""

import json
import logging
from pathlib import Path

import httpx
import pytest
import yaml

from reliability.umgpt import (
    ACTIVE,
    PRICES,
    Runtime,
    UMInfrastructureError,
    UMModel,
)
from reliability.umgpt_spend import BudgetCap, SpendLedger

ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "unit-test-credential-do-not-persist"


@pytest.fixture
def route(tmp_path, monkeypatch):
    monkeypatch.setenv("UMGPT_API_KEY", SENTINEL)
    monkeypatch.setenv("MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT", "2")
    cfg = yaml.safe_load((ROOT / "configs/model/primary_umgpt.yaml").read_text())
    path = tmp_path / "route.yaml"
    path.write_text(yaml.safe_dump(cfg))
    ledger = SpendLedger(tmp_path / "ledger.json", job="test")
    runtime = Runtime(ledger, "task", .85, "agent")
    token = ACTIVE.set(runtime)
    yield path, runtime
    ACTIVE.reset(token)


def install_transport(monkeypatch, statuses=(200,), body=None, success_update=None):
    captured = []

    def handle(request):
        captured.append((request.url, json.loads(request.content)))
        status = statuses[min(len(captured) - 1, len(statuses) - 1)]
        assert request.headers["authorization"] == "Bearer " + SENTINEL
        logging.getLogger("httpx").warning("Authorization: Bearer " + SENTINEL)
        data = body if status != 200 else {
            "id": "chatcmpl-unit", "object": "chat.completion", "created": 1,
            "model": "served-unit", "system_fingerprint": "fp-unit",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [{
                    "id": "call-unit", "type": "function", "function": {
                        "name": "bash", "arguments": '{"command":"ls"}'}}]}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10,
                      "total_tokens": 110, "prompt_tokens_details": {"cached_tokens": 50}},
        }
        if status == 200 and success_update:
            success_update(data)
        return httpx.Response(status, json=data, request=request,
                              headers={"x-ratelimit-remaining-requests": "7"})

    transport = httpx.MockTransport(handle)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request:
                        transport.handle_request(request))
    return captured


@pytest.mark.parametrize("role", ["primary", "generator"])
def test_real_http_serialization_and_no_secret(route, monkeypatch, caplog, role):
    path, runtime = route
    cfg = yaml.safe_load(path.read_text())
    cfg["role"] = role
    path.write_text(yaml.safe_dump(cfg))
    captured = install_transport(monkeypatch)
    model = UMModel(umgpt_config=path, model_name=cfg["model_id"],
                    model_kwargs={"max_tokens": 999})
    result = model.query([{"role": "user", "content": "List files"}])
    url, payload = captured[0]
    assert url.host == "api.toolkit.umgpt.umich.edu"
    assert url.path == "/v1/chat/completions"
    assert payload["max_completion_tokens"] == 8192
    assert "max_tokens" not in payload
    assert payload["temperature"] == 0
    assert payload["top_p"] == 1
    assert payload["tools"][0]["function"]["name"] == "bash"
    assert SENTINEL not in caplog.text
    assert SENTINEL not in json.dumps(result)
    assert SENTINEL not in json.dumps(model.serialize())
    assert SENTINEL not in json.dumps(runtime.ledger.snapshot())
    call = runtime.calls[-1]
    assert call["provider"] == "umgpt" and call["served_model"] == "served-unit"
    assert call["system_fingerprint"] == "fp-unit"
    assert call["cached_input_tokens"] == 50
    assert call["cost_usd"] > 0
    assert call["litellm_cost_usd"] > 0


@pytest.mark.parametrize("status,body,termination", [
    (402, "Payment required", "BUDGET_CAP"),
    (429, "quota exhausted", "BUDGET_CAP"),
    (429, "budget exhausted", "BUDGET_CAP"),
    (429, "allocation exceeded", "BUDGET_CAP"),
    (429, "insufficient credit", "BUDGET_CAP"),
    (401, "Invalid credential", "AUTH_ERROR"),
    (403, "Forbidden", "AUTH_ERROR"),
])
def test_http_errors_halt_without_retry_and_redact(route, monkeypatch, caplog,
                                                 status, body, termination):
    path, runtime = route
    captured = install_transport(monkeypatch, (status,), {
        "error": {"message": body + " Bearer " + SENTINEL}})
    cfg = yaml.safe_load(path.read_text())
    model = UMModel(umgpt_config=path, model_name=cfg["model_id"])
    with pytest.raises(UMInfrastructureError):
        model.query([{"role": "user", "content": "List files"}])
    assert len(captured) == 1
    assert runtime.halt["termination"] == termination
    assert runtime.halt["classification"] == "infrastructure"
    assert runtime.halt["rate_limit_headers"] == {"x-ratelimit-remaining-requests": "7"}
    assert body in runtime.halt["response_body"]
    assert SENTINEL not in json.dumps(runtime.calls)
    assert SENTINEL not in caplog.text
    assert SENTINEL not in json.dumps(runtime.ledger.snapshot())
    assert runtime.ledger.spend(runtime.ledger.snapshot()) == 0


def test_plain_429_keeps_scaffold_retry(route, monkeypatch):
    path, runtime = route
    captured = install_transport(monkeypatch, (429, 200), {
        "error": {"message": "Too many requests; slow down"}})
    cfg = yaml.safe_load(path.read_text())
    result = UMModel(umgpt_config=path, model_name=cfg["model_id"]).query(
        [{"role": "user", "content": "List files"}])
    assert len(captured) == 2
    assert result["extra"]["cost"] > 0
    assert runtime.halt is None


def test_ledger_accumulates_across_jobs_and_restarts(tmp_path):
    path = tmp_path / "ledger.json"
    first = SpendLedger(path, job="first", total_usd=20, job_usd=3)
    call = first.reserve(.7, task="a", task_cap=.85, stage="agent", model_id="unit")
    first.settle(call, .6, input_tokens=100, cached_input_tokens=25, output_tokens=10)
    resumed = SpendLedger(path, job="first", total_usd=20, job_usd=3)
    assert resumed.spend(resumed.snapshot(), job="first") == .6
    call = resumed.reserve(.2, task="a", task_cap=.85, stage="V4", model_id="unit")
    resumed.settle(call, .1)
    other = SpendLedger(path, job="second", total_usd=1, job_usd=3)
    with pytest.raises(BudgetCap, match="account"):
        other.before_task("b", .5)
    assert other.spend(other.snapshot()) == pytest.approx(.7)


def test_job_cap_task_cap_and_pending_reservation(tmp_path):
    ledger = SpendLedger(tmp_path / "ledger.json", job="probe", job_usd=1)
    call = ledger.reserve(.7, task="a", task_cap=.85, stage="agent", model_id="unit")
    with pytest.raises(BudgetCap, match="unsettled"):
        ledger.before_task("a", .85)
    ledger.settle(call, .7)
    with pytest.raises(BudgetCap, match="job cap"):
        ledger.before_task("b", .85)
    with pytest.raises(BudgetCap, match="per-task"):
        ledger.reserve(.2, task="a", task_cap=.85, stage="V4", model_id="unit")


def test_missing_usage_preserves_reservation(route, monkeypatch):
    import litellm
    path, runtime = route
    # ModelResponse can supply zeros automatically: explicitly remove usage.
    def missing(**kw):
        response = litellm.ModelResponse(model="unit")
        response.usage = None
        return response
    monkeypatch.setattr(litellm, "completion", missing)
    cfg = yaml.safe_load(path.read_text())
    with pytest.raises(BudgetCap, match="missing token usage"):
        UMModel(umgpt_config=path, model_name=cfg["model_id"]).query([])
    assert runtime.ledger.snapshot()["calls"][0]["state"] == "reserved"


def test_guard_refuses_before_http(route, monkeypatch):
    path, runtime = route
    runtime.task_cap = .000001
    captured = install_transport(monkeypatch)
    cfg = yaml.safe_load(path.read_text())
    with pytest.raises(BudgetCap):
        UMModel(umgpt_config=path, model_name=cfg["model_id"]).query([])
    assert not captured
    assert runtime.halt["termination"] == "BUDGET_CAP"


def test_production_backend_and_v4_factories_use_um(route, monkeypatch, tmp_path):
    import dataclasses
    from types import SimpleNamespace

    from reliability.agent.runner import AgentLimits, MiniSweAgentBackend
    from reliability.benchmark.loader import AgentTask
    from reliability.verifier.reproduction_freeze import MiniSweGenerator
    from reliability.verifier.run import default_reproduction_setup

    path, runtime = route
    cfg = yaml.safe_load(path.read_text())
    captured = install_transport(monkeypatch)
    env = SimpleNamespace(container_id="unit", cleanup=lambda: None,
                          execute=lambda action: {"output": "", "returncode": 0})

    class OneCallAgent:
        def __init__(self, model, environment, **kwargs):
            self.model = model
            self.messages = []
            self.n_calls = 1
            self.cost = 0

        def run(self, task):
            self.messages.append(self.model.query([{"role": "user", "content": task}]))
            self.cost = self.messages[-1]["extra"]["cost"]
            return {"exit_status": "Submitted", "submission": ""}

    monkeypatch.setattr("minisweagent.agents.default.DefaultAgent", OneCallAgent)
    monkeypatch.setattr("minisweagent.run.benchmarks.swebench.get_sb_environment",
                        lambda *a: env)
    monkeypatch.setattr("reliability.agent.runner.assert_network_none", lambda *a: None)
    monkeypatch.setattr("reliability.agent.isolation.assert_network_none", lambda *a: None)
    backend = MiniSweAgentBackend(cfg["model_id"],
                                  agent_config_path=ROOT / "configs/agent/swebench_claim.yaml",
                                  model_kwargs={"model_class": "reliability.umgpt.UMModel",
                                                "umgpt_config": str(path)})
    backend.run(AgentTask("unit", "unit/repo", "abc", "List files"), tmp_path, AgentLimits())
    setup = default_reproduction_setup()
    setup = dataclasses.replace(setup,
                                model=dataclasses.replace(setup.model, model_id=cfg["model_id"]),
                                prompt_path="configs/agent/v4_generator_umgpt.yaml")
    # The production V4 prompt selects UMModel, which removes the frozen
    # generator's max_tokens and supplies endpoint/key at call time.
    MiniSweGenerator(setup, ROOT).generate("List files", "unit")
    assert len(captured) == 2
    for url, body in captured:
        assert url.host == "api.toolkit.umgpt.umich.edu"
        assert "max_completion_tokens" in body and "max_tokens" not in body
        assert body["temperature"] == 0 and body["tools"]
    assert len(runtime.calls) == 2


@pytest.mark.parametrize("name", ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"])
def test_candidate_list_price_and_litellm_cost_on_custom_base(route, monkeypatch, name):
    path, runtime = route
    cfg = yaml.safe_load(path.read_text())
    incoming, cached, outgoing = PRICES[name]
    cfg.update(model_id=f"openai/{name}", pricing={"input_per_million": incoming,
               "cached_input_per_million": cached, "output_per_million": outgoing})
    path.write_text(yaml.safe_dump(cfg))
    install_transport(monkeypatch)
    UMModel(umgpt_config=path, model_name=cfg["model_id"]).query([])
    call = runtime.calls[-1]
    assert call["cost_usd"] == pytest.approx((50 * incoming + 50 * cached + 10 * outgoing) / 1e6)
    assert call["litellm_cost_usd"] > 0


@pytest.mark.parametrize("statuses,exit_code,chosen,requests", [
    ((200, 200, 200), 0, "openai/gpt-4.1-mini", 3),
    ((401, 200, 200), 2, None, 1),
    ((404, 404, 404), 2, None, 1),
])
def test_verification_writes_only_after_success(route, monkeypatch, tmp_path,
                                               statuses, exit_code, chosen, requests):
    from scripts.verify_model import record_verified

    from reliability import umgpt_verify

    config_dir = tmp_path / "configs/model"
    config_dir.mkdir(parents=True)
    for role in ("primary", "generator"):
        cfg = yaml.safe_load((ROOT / f"configs/model/{role}_umgpt.yaml").read_text())
        cfg.pop("verified", None)
        (config_dir / f"{role}_umgpt.yaml").write_text(yaml.safe_dump(cfg))
    monkeypatch.setattr(umgpt_verify, "ROOT", tmp_path)
    captured = install_transport(monkeypatch, statuses, {"error": {"message": "not served"}})
    result = umgpt_verify.verify(config_dir / "primary_umgpt.yaml", update=True,
                                 candidates=True, model_id=None, record_verified=record_verified)
    assert result == exit_code and len(captured) == requests
    for role in ("primary", "generator"):
        cfg = yaml.safe_load((config_dir / f"{role}_umgpt.yaml").read_text())
        if chosen:
            assert cfg["model_id"] == chosen
            assert cfg["verified"]["status"] == "ok"
            assert cfg["verified"]["served_model"] == "served-unit"
            assert cfg["verified"]["provider"] == "umgpt"
            assert cfg["verified"]["rate_limit_headers"] == {"x-ratelimit-remaining-requests": "7"}
        else:
            assert "verified" not in cfg


@pytest.mark.parametrize('finish,detected,filtered,stop', [
    ('tool_calls', True, False, False),
    ('tool_calls', True, True, True),
    ('content_filter', False, False, True),
])
def test_filtering_recorded_and_hard_stop(route, monkeypatch, finish, detected, filtered, stop):
    path, runtime = route
    def update(data):
        data['choices'][0].update(finish_reason=finish, content_filter_results={
            'protected_material_code': {'detected': detected, 'filtered': filtered}})
    captured = install_transport(monkeypatch, success_update=update)
    cfg = yaml.safe_load(path.read_text())
    model = UMModel(umgpt_config=path, model_name=cfg['model_id'])
    if stop:
        with pytest.raises(UMInfrastructureError):
            model.query([])
        with pytest.raises(UMInfrastructureError):
            model.query([])
        assert len(captured) == 1
        assert runtime.halt['termination'] == 'CONTENT_FILTER'
        assert runtime.halt['step'] == 1
    else:
        model.query([])
    call = runtime.calls[0]
    assert call['finish_reason'] == finish
    assert call['protected_material_code_detected'] is detected
    assert call['protected_material_code_filtered'] is filtered
    assert runtime.ledger.snapshot()['calls'][0]['state'] == 'settled'
    assert call['id'] == runtime.ledger.snapshot()['calls'][0]['id']


def test_any_filter_category_stops(route, monkeypatch):
    path, runtime = route
    captured = install_transport(monkeypatch, success_update=lambda data:
        data.update(prompt_filter_results=[{'content_filter_results': {
            'unknown_future_category': {'filtered': True}}}]))
    cfg = yaml.safe_load(path.read_text())
    with pytest.raises(UMInfrastructureError):
        UMModel(umgpt_config=path, model_name=cfg['model_id']).query([])
    assert len(captured) == 1 and runtime.calls[0]['any_filtered']


def test_single_call_ceiling_precedes_http(route, monkeypatch):
    path, runtime = route
    captured = install_transport(monkeypatch)
    cfg = yaml.safe_load(path.read_text())
    with pytest.raises(BudgetCap, match='single-call'):
        UMModel(umgpt_config=path, model_name=cfg['model_id']).query([
            {'role': 'user', 'content': 'a' * 800000}])
    assert not captured
    assert not runtime.ledger.snapshot()['calls']


def test_probe_three_repair_then_direct_v14_runs(route, monkeypatch, tmp_path):
    import sys
    from types import SimpleNamespace

    from scripts import run_umgpt_probe as probe

    from reliability.benchmark.loader import AgentTask
    from reliability.benchmark.manifest import Manifest, ManifestEntry
    from reliability.verifier.run_v1_4 import default_reproduction_setup

    path, _ = route
    captured = install_transport(monkeypatch)
    root = tmp_path / 'probe'
    root.mkdir()
    (root / '.env').write_text('')
    files = ['configs/experiments/umgpt_probe.yaml', 'configs/model/primary_umgpt.yaml',
             'configs/model/generator_umgpt.yaml', 'configs/agent/mini_swe_agent.yaml',
             'configs/agent/v4_generator_umgpt.yaml']
    for relative in files:
        dest = root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / relative).read_bytes())
    for role in ('primary', 'generator'):
        dest = root / f'configs/model/{role}_umgpt.yaml'
        cfg = yaml.safe_load(dest.read_text())
        cfg['verified'] = {'status': 'ok', 'model_id': cfg['model_id'],
                           'served_model': 'served-unit', 'system_fingerprint': 'fp-unit',
                           'checked': '2026-11-16'}
        dest.write_text(yaml.safe_dump(cfg))
    manifest_path = root / 'manifest.csv'
    manifest_path.write_text('unit fixture')
    manifest = Manifest(manifest_path, 'sha256:unit', tuple(
        ManifestEntry(i, 'unit/repo', 'unit', 'abc') for i in probe.IDS))
    monkeypatch.setattr(probe, 'ROOT', root)
    monkeypatch.setattr(probe, 'load_manifest', lambda _: manifest)
    monkeypatch.setattr(probe, 'git_dirty', lambda _: False)
    monkeypatch.setattr(probe, 'git_commit', lambda _: 'unit-commit')
    monkeypatch.setattr(probe, 'config_identity', lambda _: {})
    monkeypatch.setattr(probe, 'ensure_docker', lambda: None)
    setup = default_reproduction_setup()
    monkeypatch.setattr(probe, 'default_reproduction_setup', lambda: setup)
    monkeypatch.setattr(probe, 'load_agent_task', lambda i: AgentTask(i, 'unit/repo', 'abc', 'issue'))
    monkeypatch.setattr(sys, 'argv', ['run_umgpt_probe.py'])
    order = []
    def query(stage):
        runtime = ACTIVE.get()
        assert runtime.stage == stage
        cfg = yaml.safe_load(path.read_text())
        UMModel(umgpt_config=path, model_name=cfg['model_id']).query([])
    def repair(entry, backend, run_root, **kwargs):
        assert kwargs['agent_task'].instance_id == entry.instance_id
        assert kwargs['limits'].max_cost_usd == .6
        order.append((entry.instance_id, 'agent'))
        assert ACTIVE.get().task_cap == .6
        query('agent')
        patch = run_root / 'tasks' / entry.instance_id / 'patch.diff'
        patch.parent.mkdir(parents=True, exist_ok=True)
        patch.write_text('unit patch')
        return SimpleNamespace(termination=SimpleNamespace(value='completed'), duration_s=1.,
            patch=SimpleNamespace(path=str(patch.relative_to(run_root)), size_bytes=10))
    def reproduction(instance_id, patch_text, setup, **kwargs):
        order.append((instance_id, 'V4'))
        assert setup.budget.generator_max_steps == 80
        assert .74 < setup.budget.generator_max_cost_usd < .75
        assert ACTIVE.get().task_cap == .75
        assert kwargs['use_container'] and kwargs['generator'].setup.model.model_id == 'openai/gpt-4.1-mini'
        query('V4')
        return SimpleNamespace(findings={'generation_evidence': {'steps_used': 1,
            'fired_limit_subtype': None, 'token_usage_status': 'reported'}})
    monkeypatch.setattr(probe, 'run_task', repair)
    monkeypatch.setattr(probe, 'run_reproduction', reproduction)
    assert probe.main() == 0
    assert order == [(i, stage) for i in probe.IDS for stage in ('agent', 'V4')]
    assert len(captured) == 6
    rows = json.loads((root / 'runs/umgpt_probe/summary.json').read_text())
    assert all(r['V2'] == 'not run in probe' and r['oracle'] == 'not run in probe' for r in rows)
    assert all(r['repair']['input_tokens'] == 100 and r['V4']['input_tokens'] == 100 for r in rows)


def test_run_task_agent_projection_avoids_withheld_fields(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from reliability.agent import runner
    from reliability.agent.records import RunRole, Termination
    from reliability.benchmark.loader import AgentTask
    from reliability.benchmark.manifest import ManifestEntry
    def forbidden(*args):
        raise AssertionError('withheld loader must not be called')
    monkeypatch.setattr(runner, 'load_instance', forbidden)
    backend = SimpleNamespace(scaffold='unit', version='1', model_id='unit',
        run=lambda *a: runner.AgentOutcome('', b'', Termination.COMPLETED))
    record = runner.run_task(ManifestEntry('unit', 'unit/repo', 'unit', 'abc'), backend,
        tmp_path, experiment_id='unit', run_role=RunRole.SMOKE, manifest_hash='unit',
        agent_task=AgentTask('unit', 'unit/repo', 'abc', 'issue'))
    assert record.instance_id == 'unit'
