"""V4 telemetry captured beside the new-version freeze, with no retry."""

import json
import re
import time
from pathlib import Path

from reliability.verifier.reproduction_freeze import MiniSweGenerator
from reliability.verifier.static_v1_4 import tail


def sanitize(output):
    output = re.sub(
        r"(?:sk-(?:ant-|proj-)?[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|"
        r"hf_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})",
        "[REDACTED]",
        output,
    )
    output = re.sub(
        r"(?i)(bearer\s+|(?:api[_-]?key|token|password|secret)\s*[=:]\s*)"
        r"[^\s\x22\x27,}]+",
        r"\1[REDACTED]",
        output,
    )
    return tail(output)


def telemetry(outcome, setup, elapsed):
    caps = {**setup.budget.as_dict(), "max_output_tokens_per_call": setup.model.max_output_tokens}
    usage = [
        m.get("extra", {}).get("response", {}).get("usage")
        for m in outcome.trajectory
        if isinstance(m.get("extra", {}).get("response", {}), dict) and m.get("role") == "assistant"
    ]
    known = bool(usage) and all(
        isinstance(u, dict) and "prompt_tokens" in u and "completion_tokens" in u for u in usage
    )
    reason = outcome.termination.lower()
    fired = None
    if "limit" in reason or "exceeded" in reason:
        if outcome.n_steps >= setup.budget.generator_max_steps:
            fired = "steps"
        elif outcome.cost_usd >= setup.budget.generator_max_cost_usd:
            fired = "cost"
        elif "time" in reason:
            fired = "time"
        elif "token" in reason:
            fired = "tokens"
        else:
            fired = "other"
    elif "time" in reason:
        fired = "time"
    output = "\n".join(
        str(m.get("content") or "")
        for m in outcome.trajectory
        if m.get("role") not in ("system", "user")
    )
    return {
        "fired_limit_subtype": fired,
        "steps_used": outcome.n_steps,
        "cost_usd": outcome.cost_usd,
        "elapsed_seconds": elapsed,
        "total_input_tokens": sum(u["prompt_tokens"] for u in usage) if known else None,
        "total_output_tokens": sum(u["completion_tokens"] for u in usage) if known else None,
        "token_usage_status": "reported" if known else "unreported by generator",
        "configured_caps": caps,
        "sanitized_output_tail": sanitize(output),
    }


class RecordingGenerator:
    def __init__(self, generator, setup, path):
        self.generator, self.setup, self.path = generator, setup, path

    def generate(self, issue_text, instance_id):
        started = time.monotonic()
        try:
            outcome = self.generator.generate(issue_text, instance_id)
        except Exception as exc:
            data = {
                "fired_limit_subtype": None,
                "steps_used": None,
                "cost_usd": None,
                "elapsed_seconds": time.monotonic() - started,
                "total_input_tokens": None,
                "total_output_tokens": None,
                "token_usage_status": "generation failed before outcome",
                "configured_caps": {
                    **self.setup.budget.as_dict(),
                    "max_output_tokens_per_call": self.setup.model.max_output_tokens,
                },
                "sanitized_output_tail": sanitize(f"{type(exc).__name__}: {exc}"),
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data, indent=2) + "\n")
            raise
        data = telemetry(outcome, self.setup, time.monotonic() - started)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n")
        return outcome


def run_reproduction(instance_id, patch_text, setup, **kwargs):
    from reliability.verifier.run import REPO_ROOT
    from reliability.verifier.run import run_reproduction as legacy_run

    directory = Path(kwargs["cache_dir"]) / instance_id
    path = directory / "generation_evidence.v1_4.json"
    generator = kwargs.pop("generator", None) or MiniSweGenerator(setup, REPO_ROOT)
    record = legacy_run(
        instance_id,
        patch_text,
        setup,
        generator=RecordingGenerator(generator, setup, path),
        **kwargs,
    )
    if path.is_file():
        evidence = json.loads(path.read_text())
    else:
        evidence = {
            "fired_limit_subtype": None,
            "steps_used": None,
            "cost_usd": None,
            "elapsed_seconds": None,
            "total_input_tokens": None,
            "total_output_tokens": None,
            "token_usage_status": "generator did not run",
            "configured_caps": {
                **setup.budget.as_dict(),
                "max_output_tokens_per_call": setup.model.max_output_tokens,
            },
            "sanitized_output_tail": "",
            "reason": record.detail,
        }
    record.findings["generation_evidence"] = evidence
    return record
