"""Opt-in mini-swe-agent UM route. No secret is kept in model configuration."""

from __future__ import annotations

import contextlib
import io
import json
import logging
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse

import httpx
import litellm
import yaml
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.actions_toolcall import BASH_TOOL
from openai import OpenAI

from reliability.umgpt_spend import BudgetCap, SpendLedger

BASE = "https://api.toolkit.umgpt.umich.edu/v1"
PRICES = {"gpt-4.1": (2.0, .5, 8.0), "gpt-4.1-mini": (.4, .1, 1.6),
          "gpt-4o-mini": (.15, .075, .6), "gpt-4.1-nano": (.1, .025, .4)}


def sanitize(value):
    text = str(value)
    secret = os.environ.get("UMGPT_API_KEY")
    if secret:
        text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)bearer\s+[^\s\"',}]+", "Bearer [REDACTED]", text)
    return text


def safe_object(value):
    return json.loads(sanitize(json.dumps(value, default=str)))


def error_record(exc):
    response = getattr(exc, "response", None)
    status = getattr(exc, "status_code", None) or getattr(response, "status_code", None)
    body = getattr(response, "text", None)
    if not body:
        body = getattr(exc, "body", None) or getattr(exc, "message", None) or str(exc)
    body = sanitize(body)[:8000]
    if status in (401, 403):
        termination = "AUTH_ERROR"
    elif status == 402 or (status == 429 and any(
        word in body.lower() for word in ("quota", "budget", "exceeded", "insufficient"))):
        termination = "BUDGET_CAP"
    elif status == 429:
        termination = "RATE_LIMITED"
    else:
        termination = "API_ERROR"
    return {"termination": termination, "classification": "infrastructure",
            "status_code": status, "response_body": body}


class UMInfrastructureError(RuntimeError):
    def __init__(self, record):
        self.record = record
        super().__init__(f"{record['termination']}: {record['response_body']}")


@dataclass
class Runtime:
    ledger: SpendLedger
    task: str
    task_cap: float
    stage: str
    calls: list = field(default_factory=list)
    halt: dict | None = None


ACTIVE: ContextVar[Runtime | None] = ContextVar("umgpt_runtime", default=None)


def usage_cost(response, cfg):
    usage = response.model_dump().get("usage") or {}
    incoming, outgoing = usage.get("prompt_tokens"), usage.get("completion_tokens")
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
    if not isinstance(incoming, int) or not isinstance(outgoing, int):
        raise BudgetCap("response missing token usage; reservation retained")
    if min(incoming, outgoing, cached) < 0 or cached > incoming:
        raise BudgetCap("invalid token usage; reservation retained")
    prices = cfg["pricing"]
    cost = ((incoming - cached) * prices["input_per_million"]
            + cached * prices["cached_input_per_million"]
            + outgoing * prices["output_per_million"]) / 1_000_000
    try:
        computed = litellm.completion_cost(completion_response=response, model=cfg["model_id"])
    except Exception:  # noqa: BLE001 - explicit list-price fallback is recorded
        computed = None
    return {"input_tokens": incoming, "cached_input_tokens": cached,
            "output_tokens": outgoing, "cost_usd": cost,
            "litellm_cost_usd": computed,
            "provider": "umgpt", "model_id": cfg["model_id"],
            "served_model": response.model,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "api_base_host": urlparse(cfg["api_base"]).hostname}


@contextlib.contextmanager
def quiet_transport():
    # This opt-in serial runner discards client diagnostics that can contain headers.
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            yield
    finally:
        logging.disable(previous)


class UMModel(LitellmModel):
    abort_exceptions: ClassVar[list] = [
        *LitellmModel.abort_exceptions, BudgetCap, UMInfrastructureError]

    def __init__(self, *, umgpt_config, **kwargs):
        self.route = yaml.safe_load(Path(umgpt_config).read_text())
        if (self.route.get("provider") != "umgpt" or self.route["api_base"] != BASE
                or self.route.get("api_key_env") != "UMGPT_API_KEY"):
            raise ValueError("UM route requires the pinned UM endpoint")
        if kwargs.get("model_name") != self.route["model_id"]:
            raise ValueError("Requested model differs from UM configuration")
        # The parent holds only safe decoding parameters, never credentials.
        kwargs["model_kwargs"] = {}
        super().__init__(**kwargs)

    def _query(self, messages, **kwargs):
        runtime = ACTIVE.get()
        if runtime is None:
            raise BudgetCap("UM calls require an active persistent spend ledger")
        cfg = self.route
        key = os.environ.get(cfg["api_key_env"])
        if not key:
            record = {"termination": "AUTH_ERROR", "classification": "infrastructure",
                      "status_code": None, "response_body": "UMGPT_API_KEY is not set"}
            runtime.halt = record
            raise UMInfrastructureError(record)
        output_limit = int(cfg["max_completion_tokens"])
        # UTF-8 bytes plus 2048 exceeds tokenized text, tool schema and chat framing.
        input_bound = len(json.dumps([messages, BASH_TOOL], ensure_ascii=False).encode()) + 2048
        prices = cfg["pricing"]
        bound = (input_bound * prices["input_per_million"]
                 + output_limit * prices["output_per_million"]) / 1_000_000
        try:
            call_id = runtime.ledger.reserve(bound, task=runtime.task, task_cap=runtime.task_cap,
                                              stage=runtime.stage, model_id=cfg["model_id"])
        except BudgetCap as exc:
            runtime.halt = {"termination": "BUDGET_CAP", "classification": "infrastructure",
                            "response_body": str(exc), "status_code": None}
            raise
        transport_result = {}

        def capture_response(response):
            response.read()
            # Do not retain request headers or general response headers.
            transport_result.update(status_code=response.status_code,
                                    response_body=sanitize(response.text)[:8000],
                                    rate_limit_headers={k: sanitize(v) for k, v in
                                        response.headers.items() if k.lower().startswith("x-ratelimit-")})

        try:
            with quiet_transport():  # noqa: SIM117 - silence client construction and teardown
                with httpx.Client(event_hooks={"response": [capture_response]}) as http_client:
                    client = OpenAI(api_key=key, base_url=cfg["api_base"],
                                    http_client=http_client, max_retries=0)
                    response = litellm.completion(
                        model=cfg["model_id"], messages=messages, tools=[BASH_TOOL],
                        api_base=cfg["api_base"], api_key=key, client=client,
                        temperature=cfg["temperature"], top_p=cfg["top_p"],
                        max_completion_tokens=output_limit, drop_params=True,
                        timeout=cfg["limits"]["request_timeout_s"], num_retries=0,
                    )
        except Exception as exc:  # noqa: BLE001 - sanitize every provider failure
            if transport_result.get("response_body"):
                error = RuntimeError(transport_result["response_body"])
                error.status_code = transport_result["status_code"]
                record = error_record(error)
            else:
                record = error_record(exc)
            record.update(provider="umgpt", model_id=cfg["model_id"],
                          served_model=None, system_fingerprint=None,
                          api_base_host=urlparse(cfg["api_base"]).hostname,
                          rate_limit_headers=transport_result.get("rate_limit_headers", {}))
            runtime.calls.append(record)
            # Definite client rejections have no generation. Ambiguous transport
            # failures keep their reservation, so a restart cannot spend it twice.
            if record["status_code"] and 400 <= record["status_code"] < 500:
                runtime.ledger.settle(call_id, 0.0, error=record)
            if record["termination"] == "RATE_LIMITED":
                raise litellm.RateLimitError(record["response_body"],
                                            llm_provider="openai", model=cfg["model_id"]) from None
            runtime.halt = record
            raise UMInfrastructureError(record) from None
        try:
            with quiet_transport():
                call = safe_object(usage_cost(response, cfg))
            call["rate_limit_headers"] = transport_result.get("rate_limit_headers", {})
            runtime.calls.append(call)
            runtime.ledger.settle(call_id, call["cost_usd"], **{
                k: v for k, v in call.items() if k != "cost_usd"})
            response._hidden_params["umgpt_cost"] = call["cost_usd"]
        except BudgetCap as exc:
            runtime.halt = {"termination": "BUDGET_CAP", "classification": "infrastructure",
                            "response_body": str(exc), "status_code": None}
            raise
        # Return a sanitized response, so model output cannot echo a credential.
        if key in json.dumps(response.model_dump()):
            clean = litellm.ModelResponse(**safe_object(response.model_dump()))
            clean._hidden_params["umgpt_cost"] = call["cost_usd"]
            return clean
        return response

    def _calculate_cost(self, response):
        return {"cost": response._hidden_params["umgpt_cost"]}
