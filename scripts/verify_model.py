"""Verify a pinned model actually serves, with a real tool-calling request.

Existing in a provider's listing is not evidence a model serves. `gemini-2.5-flash`
appeared in both litellm's static cost map and the provider's own ListModels
response while returning 404 on every real request, which cost a smoke run to
discover. This script issues an actual request with an actual tool definition and
reports what came back.

Tool calling specifically, not a plain completion: mini-swe-agent's LitellmModel
sends `tools=[BASH_TOOL]` on every call, so a model that chats fine but cannot
emit a tool call is useless to this pipeline and would fail at step 1 of a run.

    .venv/bin/python scripts/verify_model.py                      # primary.yaml
    .venv/bin/python scripts/verify_model.py --config configs/model/smoke_gemini.yaml
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_env_file(path: pathlib.Path) -> None:
    """Load KEY=VALUE pairs without echoing any value.

    Tolerates whitespace around the key, which a hand-edited .env picks up easily
    (`DEEPSEEK_API_KEY =...`) and which would otherwise export a name with a
    trailing space that nothing ever finds.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if value.strip():
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/model/primary.yaml")
    parser.add_argument("--model-id", default=None, help="override the config's model_id")
    parser.add_argument("--update", action="store_true",
                        help="on success, record verified.status: ok in the config")
    parser.add_argument("--umgpt-candidates", action="store_true",
                        help="verify the three UM candidates, then pin both new UM configs")
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env")

    config_path = REPO_ROOT / args.config
    cfg = yaml.safe_load(config_path.read_text())
    if cfg.get("provider") == "umgpt":
        from reliability.umgpt_verify import verify
        return verify(config_path, update=args.update, candidates=args.umgpt_candidates,
                      model_id=args.model_id, record_verified=record_verified)
    model_id = args.model_id or cfg.get("model_id")
    key_env = cfg.get("api_key_env")

    if not model_id:
        print(f"FAIL  {args.config} has no model_id pinned.")
        return 2
    if not key_env:
        print(f"FAIL  {args.config} has no api_key_env.")
        return 2
    if not os.environ.get(key_env):
        print(f"FAIL  {key_env} is not set.")
        print("      Add it to .env (gitignored). See .env.example.")
        return 2

    import litellm
    from minisweagent.models.utils.actions_toolcall import BASH_TOOL

    litellm.suppress_debug_info = True

    print(f"config   : {args.config}")
    print(f"model_id : {model_id}")
    print(f"key      : {key_env} present ({len(os.environ[key_env])} chars)")
    print(f"in litellm cost map: {model_id in litellm.model_cost}"
          "   (note: presence here is NOT evidence it serves)")
    print("\nissuing a real tool-calling request...\n")

    try:
        response = litellm.completion(
            model=model_id,
            messages=[{"role": "user",
                       "content": "Use the bash tool to list the files in the current directory."}],
            tools=[BASH_TOOL],
            **(cfg.get("model_kwargs") or {}),
        )
    except Exception as exc:  # noqa: BLE001 - reporting the failure IS the job
        # Deliberately broad. The whole purpose is to surface whatever the
        # provider does: 404 for a withdrawn model, auth failure, unsupported
        # params, timeout. Narrowing this would let the interesting case escape.
        print(f"FAIL  {type(exc).__name__}")
        print(f"      {str(exc)[:600]}")
        return 1

    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    try:
        cost = f"${litellm.cost_calculator.completion_cost(response, model=model_id):.8f}"
    except Exception as exc:  # noqa: BLE001 - missing pricing must not fail the check
        # A model can serve correctly while being absent from litellm's cost map.
        # That is worth reporting, not worth failing verification over.
        cost = f"unavailable ({type(exc).__name__})"

    print("  responded    : yes")
    print(f"  tool calls   : {len(tool_calls)}")
    if tool_calls:
        call = tool_calls[0]
        print(f"  tool name    : {call.function.name}")
        print(f"  arguments    : {str(call.function.arguments)[:120]}")
    print(f"  finish reason: {response.choices[0].finish_reason}")
    print(f"  tokens       : {response.usage.prompt_tokens} in / "
          f"{response.usage.completion_tokens} out")
    print(f"  cost         : {cost}")

    if not tool_calls:
        print("\nFAIL  model responded but emitted no tool call. mini-swe-agent sends")
        print("      tools=[BASH_TOOL] on every request, so this model cannot drive")
        print("      the agent loop.")
        return 1

    print("\nPASS  model serves and emits well-formed tool calls.")

    served_model = getattr(response, "model", None) or "unreported"
    fingerprint = getattr(response, "system_fingerprint", None) or "unreported"
    print(f"  served model : {served_model}")
    print(f"  fingerprint  : {fingerprint}")

    if args.update:
        record_verified(config_path, model_id,
                        served_model=served_model, system_fingerprint=fingerprint)
        print(f"      recorded verified.status: ok in {args.config}")
    return 0


def record_verified(
    config_path: Path, model_id: str, *,
    served_model: str = "unreported", system_fingerprint: str = "unreported",
    metadata: dict | None = None,
) -> None:
    """Rewrite only the `verified:` block, leaving the rest of the file alone.

    A `yaml.safe_load` / `yaml.dump` round-trip would be far simpler, but it
    discards every comment in the file. The comments in `configs/model/*.yaml`
    carry the rationale for the pin — why open weights, why this route, why a
    listing is not evidence a model serves — and that rationale is the
    provenance. Losing it to a verification step would be a poor trade for four
    lines of convenience.
    """
    today = datetime.now(tz=UTC).date().isoformat()
    block = (
        "verified:\n"
        f"  status: ok\n"
        f"  method: scripts/verify_model.py\n"
        f"  checked: {today}\n"
        f"  model_id: {model_id}\n"
        f"  tool_calling: true\n"
        f"  served_model: {served_model}\n"
        f"  system_fingerprint: {system_fingerprint}\n"
    )
    if metadata is not None:
        block += "".join("  " + line + "\n" for line in
                         yaml.safe_dump(metadata, sort_keys=False).splitlines())

    lines = config_path.read_text().splitlines(keepends=True)
    out, i = [], 0
    replaced = False
    while i < len(lines):
        if lines[i].startswith("verified:"):
            out.append(block)
            i += 1
            # Drop the old block's indented body; comments above it are kept,
            # since they explain the pin rather than the verification result.
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                if not lines[i].strip():
                    break
                i += 1
            replaced = True
            continue
        out.append(lines[i])
        i += 1

    if not replaced:
        raise SystemExit(f"{config_path} has no `verified:` block to update")

    config_path.write_text("".join(out))


if __name__ == "__main__":
    raise SystemExit(main())
