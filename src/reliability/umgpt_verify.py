"""Live verification invoked only by scripts/verify_model.py for UM configs."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from reliability.umgpt import ACTIVE, BASE, PRICES, Runtime, UMModel, safe_object
from reliability.umgpt_spend import SpendLedger

ROOT = Path(__file__).resolve().parents[2]
JOB = "umgpt_probe"


def verify(path, *, update, candidates, model_id, record_verified):
    cfg = yaml.safe_load(path.read_text())
    models = ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"] if candidates else [
        (model_id or cfg["model_id"]).removeprefix("openai/")]
    output = ROOT / "runs/umgpt_probe"
    output.mkdir(parents=True, exist_ok=True)
    results_path = output / "verification.json"
    if results_path.exists():
        raise SystemExit("verification.json exists; refusing to repeat paid verification")
    ledger = SpendLedger(ROOT / "runs/umgpt_spend_ledger.json", job=JOB,
                         total_usd=cfg["budget"]["total_usd"], job_usd=3.0)
    results = []
    chosen = None
    for name in models:
        incoming, cached, outgoing = PRICES[name]
        candidate = {**cfg, "model_id": f"openai/{name}",
                     "pricing": {"input_per_million": incoming,
                                 "cached_input_per_million": cached,
                                 "output_per_million": outgoing,
                                 "note": "List-price estimate; UM billing unconfirmed"}}
        candidate_path = output / f"{name}.yaml"
        candidate_path.write_text(yaml.safe_dump(candidate, sort_keys=False))
        runtime = Runtime(ledger, f"verify:{name}", .15, "verification")
        token = ACTIVE.set(runtime)
        result = {"model_id": candidate["model_id"], "provider": "umgpt",
                  "api_base_host": BASE.split("/")[2], "passed": False}
        try:
            model = UMModel(umgpt_config=candidate_path, model_name=candidate["model_id"])
            message = model.query([{"role": "user", "content":
                "Use the bash tool to list the files in the current directory."}])
            response = message["extra"]["response"]
            calls = response["choices"][0]["message"].get("tool_calls") or []
            passed = response["choices"][0]["finish_reason"] == "tool_calls" and bool(calls)
            for call in calls:
                args = json.loads(call["function"]["arguments"])
                passed = passed and call["function"]["name"] == "bash" and isinstance(
                    args.get("command"), str) and bool(args["command"].strip())
            result.update(runtime.calls[-1], passed=bool(passed))
            if passed and chosen is None:
                chosen = (candidate, result)
        except Exception as exc:  # noqa: BLE001 - verification records provider failures
            result["error"] = safe_object(runtime.halt or {"message": str(exc)})
        finally:
            ACTIVE.reset(token)
        result["calls"] = runtime.calls
        results.append(result)
        results_path.write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps({k: v for k, v in result.items() if k != "calls"}, indent=2))
        if runtime.halt and runtime.halt["termination"] in ("AUTH_ERROR", "BUDGET_CAP"):
            return 2
    if chosen is None:
        return 1
    if update:
        candidate, result = chosen
        targets = [ROOT / "configs/model/primary_umgpt.yaml",
                   ROOT / "configs/model/generator_umgpt.yaml"] if candidates else [path]
        for target in targets:
            target_cfg = yaml.safe_load(target.read_text())
            target_cfg.update(model_id=candidate["model_id"], pricing=candidate["pricing"])
            target_cfg["verified"] = {}  # Only this verification script creates the block.
            target.write_text(yaml.safe_dump(target_cfg, sort_keys=False))
            record_verified(target, candidate["model_id"],
                            served_model=result["served_model"],
                            system_fingerprint=result.get("system_fingerprint") or "unreported",
                            metadata={"provider": "umgpt", "api_base_host": BASE.split("/")[2],
                                      "rate_limit_headers": result["rate_limit_headers"],
                                      "usage": {k: result[k] for k in (
                                          "input_tokens", "cached_input_tokens", "output_tokens")},
                                      "cost_usd": result["cost_usd"],
                                      "litellm_cost_usd": result["litellm_cost_usd"]})
    return 0
