"""Phase 3.1 end-to-end smoke test. NOT pilot data.

Proves the pipeline runs end to end on a real model: agent -> frozen patch ->
parsed claim -> validated record. Repair success is explicitly not the gate. An
UNRESOLVED claim or a patch that fails the tests is a perfectly good smoke
result, because what is under test is the plumbing.

Every record is stamped `run_role: smoke`, which makes `is_citable_as_result`
False. The model here is chosen for being free, not for being good, and its
numbers say nothing about any model's repair ability.

Usage:
    .venv/bin/python scripts/run_smoke.py --instance psf__requests-1921
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import yaml

from reliability.agent.records import RunRole
from reliability.agent.runner import (
    AgentLimits,
    MiniSweAgentBackend,
    run_task,
)
from reliability.benchmark.manifest import load_manifest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_env_file(path: pathlib.Path) -> None:
    """Load KEY=VALUE pairs into the environment without echoing any value.

    Tolerates whitespace around the key, which a hand-edited .env can easily
    pick up (`GEMINI_API_KEY =...`), and which would otherwise export a variable
    whose name has a trailing space and silently never be found.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="manifests/pilot.csv",
                        help="task manifest to draw the instance from")
    parser.add_argument("--instance", required=True, help="instance_id to run")
    parser.add_argument("--model-config", default="configs/model/smoke_gemini.yaml")
    parser.add_argument("--agent-config", default="configs/agent/swebench_claim_smoke.yaml")
    parser.add_argument("--run-root", default=None)
    parser.add_argument("--model-id", default=None,
                        help="override the config's model_id. Free-tier quota is "
                             "per model, so a throttled run can retry on another.")
    args = parser.parse_args()

    load_env_file(REPO_ROOT / ".env")

    model_cfg = yaml.safe_load((REPO_ROOT / args.model_config).read_text())
    if model_cfg.get("role") != "smoke":
        raise SystemExit(
            f"{args.model_config} is not marked role: smoke. This script only runs "
            "smoke configs; pilot and main-study runs go through the pilot runner."
        )

    key_env = model_cfg["api_key_env"]
    if not os.environ.get(key_env):
        raise SystemExit(f"{key_env} is not set (expected in .env, which is gitignored)")

    manifest = load_manifest(REPO_ROOT / args.manifest)
    matches = [e for e in manifest if e.instance_id == args.instance]
    if not matches:
        raise SystemExit(
            f"{args.instance} is not in {args.manifest}. Available:\n  "
            + "\n  ".join(manifest.instance_ids)
        )
    entry = matches[0]

    model_id = args.model_id or model_cfg["model_id"]
    slug = model_id.split("/")[-1]
    run_root = REPO_ROOT / (args.run_root or f"runs/3.1_smoke_{slug}")

    limits = AgentLimits(
        max_steps=model_cfg["limits"]["max_steps"],
        per_command_timeout_s=60,
        per_task_timeout_s=model_cfg["limits"]["request_timeout_s"],
    )

    backend = MiniSweAgentBackend(
        model_id=model_id,
        agent_config_path=REPO_ROOT / args.agent_config,
        model_kwargs={
            "model_kwargs": model_cfg.get("model_kwargs", {}),
            "cost_tracking": "ignore_errors",
        },
    )

    print(f"instance   : {entry.instance_id} ({entry.repo}, {entry.task_type})")
    print(f"model      : {model_id}   [SMOKE ONLY - not the study model]")
    print(f"run root   : {run_root.relative_to(REPO_ROOT)}")
    print(f"step limit : {limits.max_steps}")
    print(f"manifest   : {manifest.path.name} @ {manifest.content_hash[:19]}...")
    print("\nrunning...\n", flush=True)

    record = run_task(
        entry, backend, run_root,
        experiment_id=f"3.1_smoke_{slug}",
        run_role=RunRole.SMOKE,
        manifest_hash=manifest.content_hash,
        limits=limits,
    )

    print("\n=== smoke result (pipeline integrity, NOT repair success) ===")
    print(f"  termination  : {record.termination.value}")
    print(f"  claim status : {record.claim.status.value}"
          + (f" ({record.claim.reason.value})" if record.claim.reason else ""))
    print(f"  evidence     : {'present' if record.claim.evidence else 'MISSING'}")
    print(f"  patch        : {record.patch.size_bytes} bytes  {record.patch.sha256[:23]}...")
    print(f"  commands     : {len(record.commands_run)}")
    print(f"  tokens       : {record.usage.tokens_in} in / {record.usage.tokens_out} out")
    print(f"  nominal cost : ${record.usage.api_cost_usd:.6f}  (list price; free tier actual = $0)")
    print(f"  duration     : {record.duration_s:.1f}s")
    print(f"  citable      : {record.is_citable_as_result}  (smoke runs never are)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
