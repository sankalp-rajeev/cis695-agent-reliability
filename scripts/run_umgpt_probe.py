"""UM-only successor to run_pilot: exactly three repair + direct v1.4 V4 chains.

The probe does not run the oracle or read correctness labels. Costs are estimates.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import yaml

from reliability.agent.records import RepairRecord, RunRole, Termination
from reliability.agent.runner import AgentLimits, MiniSweAgentBackend, run_task
from reliability.benchmark.loader import load_agent_task
from reliability.benchmark.manifest import load_manifest
from reliability.env import assert_clean_interpreter, interpreter_environment
from reliability.provenance import git_commit, git_dirty, utc_now
from reliability.umgpt import ACTIVE, Runtime, safe_object
from reliability.umgpt_spend import SpendLedger
from reliability.verifier.reproduction_freeze import GeneratorModel, MiniSweGenerator
from reliability.verifier.reproduction_v1_4 import run_reproduction
from reliability.verifier.run_v1_4 import default_reproduction_setup

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDS = ("django__django-14373", "scikit-learn__scikit-learn-12973", "django__django-16899")


class UMBackend(MiniSweAgentBackend):
    def run(self, task, workdir, limits):
        outcome = super().run(task, workdir, limits)
        runtime = ACTIVE.get()
        if runtime and runtime.halt:
            termination = runtime.halt["termination"]
            if termination in ("BUDGET_CAP", "AUTH_ERROR"):
                return dataclasses.replace(outcome, termination=Termination(termination))
        return outcome


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe_object(data), indent=2) + "\n")


def config_identity(experiment):
    files = ["configs/experiments/umgpt_probe.yaml", experiment["model"],
             experiment["reproduction_generator"], experiment["benchmark"]["manifest"],
             experiment["agent"], "configs/agent/v4_generator_umgpt.yaml",
             "configs/verifier/full_v1_4.yaml"]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}


def load_env_file(path):
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_docker():
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("docker is not on PATH")
    result = subprocess.run([docker, "info"], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("docker unavailable: " + result.stderr[:300])


def stage_summary(calls):
    return {"calls": len(calls), **{k: sum(c.get(k, 0) or 0 for c in calls) for k in
            ("input_tokens", "cached_input_tokens", "output_tokens", "cost_usd")},
            "litellm_cost_usd": (sum(c["litellm_cost_usd"] for c in calls)
                                  if all(c.get("litellm_cost_usd") is not None for c in calls)
                                  else None)}


def run_v4(entry, repair, setup, run_root, runtime):
    """Direct V4 only; no policy decision or correctness grading is produced."""
    runtime.stage = "V4"
    runtime.task_cap = .75
    spent = runtime.ledger.spend(runtime.ledger.snapshot(), job="umgpt_probe", task=entry.instance_id)
    setup = dataclasses.replace(setup, budget=dataclasses.replace(
        setup.budget, generator_max_steps=80, generator_max_cost_usd=max(0., .75 - spent)))
    started = time.monotonic()
    signal = run_reproduction(
        entry.instance_id, (run_root / repair.patch.path).read_text(), setup,
        use_container=True, patch_applies=True,
        cache_dir=run_root / "_reproduction_cache_v1_4",
        generator=MiniSweGenerator(setup, ROOT), experiment_id="umgpt_probe")
    # Retain cost telemetry only; V4's generated-test execution is not correctness grading.
    evidence = signal.findings.get("generation_evidence", {})
    cache = run_root / "_reproduction_cache_v1_4" / entry.instance_id
    manifest = cache / "frozen.json"
    frozen = json.loads(manifest.read_text()) if manifest.exists() else {}
    tests_written = len(list((cache / "tests").glob("test_repro_*.py")))
    result = {"ran": evidence.get("token_usage_status") != "generator did not run",
              "steps": evidence.get("steps_used"),
              "fired_limit_subtype": evidence.get("fired_limit_subtype"),
              "tests_written": tests_written,
              "termination": frozen.get("termination"),
              "duration_s": time.monotonic() - started,
              "generation_evidence": evidence,
              "not_run_reason": evidence.get("reason"),
              "configured_budget": setup.budget.as_dict(),
              **stage_summary([c for c in runtime.calls if c.get("stage") == "V4"])}
    write_json(run_root / "tasks" / entry.instance_id / "v4_cost_record.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    assert_clean_interpreter()
    load_env_file(ROOT / ".env")
    if git_dirty(ROOT):
        raise SystemExit("Commit all changes before the paid probe")
    experiment = yaml.safe_load((ROOT / "configs/experiments/umgpt_probe.yaml").read_text())
    primary = yaml.safe_load((ROOT / experiment["model"]).read_text())
    generator_path = ROOT / experiment["reproduction_generator"]
    generator_cfg = yaml.safe_load(generator_path.read_text())
    if primary["model_id"] != "openai/gpt-4.1-mini" or generator_cfg["model_id"] != primary["model_id"]:
        raise SystemExit("Tasks are authorized on gpt-4.1-mini only")
    if primary.get("verified", {}).get("status") != "ok":
        raise SystemExit("Verify the UM candidates first")
    if primary["verified"]["model_id"] != primary["model_id"]:
        raise SystemExit("Primary verification does not match requested model")
    manifest = load_manifest(ROOT / experiment["benchmark"]["manifest"])
    if manifest.instance_ids != IDS or experiment["sampling"]["n_tasks"] != 3:
        raise SystemExit("This entry point is limited to the three authorized tasks")
    if (experiment["execution"]["task_cost_cap_usd"] > .75
            or primary["limits"]["max_cost_usd_per_task"] > .60
            or primary["budget"]["total_usd"] > 20):
        raise SystemExit("Authorized task/repair/account caps exceeded")
    if experiment["execution"]["job_cost_cap_usd"] > 3:
        raise SystemExit("Job ceiling cannot exceed $3.00")
    run_root = ROOT / "runs/umgpt_probe"
    run_root.mkdir(parents=True, exist_ok=True)
    identity = {"git_commit": git_commit(ROOT), "config_hashes": config_identity(experiment)}
    meta_path = run_root / "meta.yaml"
    provenance = {"provider": "umgpt", "model_id": primary["model_id"],
                  "served_model": primary["verified"]["served_model"],
                  "system_fingerprint": primary["verified"]["system_fingerprint"],
                  "api_base_host": "api.toolkit.umgpt.umich.edu",
                  "generator": generator_cfg["verified"]}
    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text())
        if not args.resume or any(meta[k] != v for k, v in identity.items()):
            raise SystemExit("Resume requires identical HEAD and configs")
        meta.setdefault("resumes", []).append(utc_now())
    else:
        if args.resume:
            raise SystemExit("No probe exists to resume")
        meta = {**identity, **provenance, "timestamp_utc": utc_now(), "git_dirty": False,
                "interpreter": interpreter_environment(),
                "max_workers": 1, "manifest_hash": manifest.content_hash,
                "task_cost_cap_usd": experiment["execution"]["task_cost_cap_usd"],
                "job_cost_cap_usd": 3.0, "billing": "list-price estimate; UM unconfirmed"}
    ensure_docker()
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False))
    (run_root / "manifest.csv").write_bytes(manifest.path.read_bytes())
    setup = default_reproduction_setup()
    prompt = "configs/agent/v4_generator_umgpt.yaml"
    setup = dataclasses.replace(setup, model=GeneratorModel.load(generator_path, repo_root=ROOT),
                                prompt_path=prompt, prompt_sha256="sha256:" +
                                hashlib.sha256((ROOT / prompt).read_bytes()).hexdigest())
    agent_limits = yaml.safe_load((ROOT / "configs/agent/mini_swe_agent.yaml").read_text())["limits"]
    limits = AgentLimits(max_steps=primary["limits"]["max_steps"],
                         max_cost_usd=primary["limits"]["max_cost_usd_per_task"],
                         per_command_timeout_s=agent_limits["per_command_timeout_s"],
                         per_task_timeout_s=agent_limits["per_task_timeout_s"])
    backend = UMBackend(model_id=primary["model_id"],
                        agent_config_path=ROOT / experiment["agent"],
                        model_kwargs={"model_class": "reliability.umgpt.UMModel",
                                      "umgpt_config": str(ROOT / experiment["model"])},
                        experiment_id="umgpt_probe")
    ledger = SpendLedger(ROOT / "runs/umgpt_spend_ledger.json", job="umgpt_probe",
                         total_usd=primary["budget"]["total_usd"], job_usd=3.0)
    cap = float(experiment["execution"]["task_cost_cap_usd"])
    rows = []
    for entry in manifest:
        directory = run_root / "tasks" / entry.instance_id
        summary_path = directory / "umgpt_record.json"
        if summary_path.exists():
            previous = json.loads(summary_path.read_text())
            if previous.get("complete"):
                rows.append(previous)
                continue
        status = ROOT / "STATUS.md"
        status.write_text(f"# UM cost probe status\n\nDone: preflight, model verification, mocked tests and implementation commit.\n\nRunning: {entry.instance_id} repair then direct V4 (80-step cap); {len(rows)} task records complete.\n\nNext: remaining authorized tasks, numeric DeepSeek comparison, spend audit, report and push.\n")
        runtime = Runtime(ledger, entry.instance_id, min(cap, .60), "agent")
        token = ACTIVE.set(runtime)
        row = {"instance_id": entry.instance_id, **provenance, "complete": False,
               "V1": "not run in probe", "V2": "not run in probe",
               "V3": "not run in probe", "oracle": "not run in probe"}
        try:
            ledger.before_task(entry.instance_id, cap)
            repair_path = directory / "repair_record.json"
            repair = RepairRecord.read(repair_path) if repair_path.exists() else run_task(
                entry, backend, run_root, experiment_id="umgpt_probe", run_role=RunRole.SMOKE,
                manifest_hash=manifest.content_hash, limits=limits,
                agent_task=load_agent_task(entry.instance_id))
            row.update(agent_termination=repair.termination.value,
                       patch_produced=repair.patch.size_bytes > 0,
                       patch_bytes=repair.patch.size_bytes,
                       repair={"termination": repair.termination.value,
                               "steps": sum(c.get("stage") == "agent" for c in runtime.calls),
                               "duration_s": repair.duration_s,
                               "patch_produced": repair.patch.size_bytes > 0,
                               "patch_bytes": repair.patch.size_bytes,
                               **stage_summary([c for c in runtime.calls if c.get("stage") == "agent"])})
            if not runtime.halt:
                row["V4"] = run_v4(entry, repair, setup, run_root, runtime)
                row["complete"] = runtime.halt is None
        except Exception as exc:  # noqa: BLE001 - infrastructure stop is persisted
            row["error"] = safe_object(str(exc))
            if runtime.halt is None:
                runtime.halt = {"termination": getattr(exc, "termination", "INFRASTRUCTURE_ERROR"),
                                "classification": "infrastructure", "response_body": str(exc)}
        finally:
            ACTIVE.reset(token)
            row["calls"] = runtime.calls
            row["halt"] = runtime.halt
            if runtime.halt:
                row["classification"] = "infrastructure"
            historical = [c for c in ledger.snapshot()["calls"]
                          if c["job"] == "umgpt_probe" and c["task"] == entry.instance_id]
            row["cost_usd"] = sum(c["cost_usd"] for c in historical)
            row["steps"] = sum(c.get("state") == "settled" and "input_tokens" in c for c in historical)
            for k in ("input_tokens", "cached_input_tokens", "output_tokens"):
                row[k] = sum(c.get(k, 0) for c in historical)
            write_json(summary_path, row)
            rows.append(row)
            write_json(run_root / "summary.json", rows)
            print(json.dumps({k: safe_object(v) for k, v in row.items() if k != "calls"}), flush=True)
        if runtime.halt:
            (ROOT / "reports/umgpt_probe/BLOCKED.md").write_text(
                f"Stopped at {entry.instance_id}: {runtime.halt['termination']}.\n"
                f"Sanitized reason: {safe_object(runtime.halt)}\n"
                "No further paid calls were made after this stop.\n")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
