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


def install_transport(monkeypatch, statuses=(200,), body=None):
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
    ((404, 200, 200), 0, "openai/gpt-4.1", 3),
    ((401, 200, 200), 2, None, 1),
    ((404, 404, 404), 1, None, 3),
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
