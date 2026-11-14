"""UM-only successor to run_pilot: exactly three repair + unchanged V4 chains.

The probe does not run the oracle or read correctness labels. Costs are estimates.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import yaml

from reliability.agent.records import RepairRecord, RunRole, Termination
from reliability.agent.runner import AgentLimits, MiniSweAgentBackend, run_task
from reliability.benchmark.manifest import load_manifest
from reliability.provenance import git_commit, git_dirty, utc_now
from reliability.umgpt import ACTIVE, Runtime, safe_object
from reliability.umgpt_spend import SpendLedger
from reliability.verifier.reproduction_freeze import GeneratorModel, MiniSweGenerator
from reliability.verifier.run import default_reproduction_setup, verify_task
from run_pilot import ensure_docker, load_env_file

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
             "configs/verifier/full.yaml", "configs/verifier/baseline.yaml"]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    load_env_file(ROOT / ".env")
    if git_dirty(ROOT):
        raise SystemExit("Commit all changes before the paid probe")
    experiment = yaml.safe_load((ROOT / "configs/experiments/umgpt_probe.yaml").read_text())
    primary = yaml.safe_load((ROOT / experiment["model"]).read_text())
    generator_path = ROOT / experiment["reproduction_generator"]
    generator_cfg = yaml.safe_load(generator_path.read_text())
    if primary.get("verified", {}).get("status") != "ok":
        raise SystemExit("Verify the UM candidates first")
    if primary["verified"]["model_id"] != primary["model_id"]:
        raise SystemExit("Primary verification does not match requested model")
    manifest = load_manifest(ROOT / experiment["benchmark"]["manifest"])
    if manifest.instance_ids != IDS or experiment["sampling"]["n_tasks"] != 3:
        raise SystemExit("This entry point is limited to the three authorized tasks")
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
        runtime = Runtime(ledger, entry.instance_id, cap, "agent")
        token = ACTIVE.set(runtime)
        row = {"instance_id": entry.instance_id, **provenance, "complete": False}
        try:
            ledger.before_task(entry.instance_id, cap)
            repair_path = directory / "repair_record.json"
            repair = RepairRecord.read(repair_path) if repair_path.exists() else run_task(
                entry, backend, run_root, experiment_id="umgpt_probe", run_role=RunRole.SMOKE,
                manifest_hash=manifest.content_hash, limits=limits)
            row.update(agent_termination=repair.termination.value, patch_produced=repair.patch.size_bytes > 0)
            if not runtime.halt:
                runtime.stage = "V4"
                if not (directory / "verification_record.full.json").exists():
                    verifications = verify_task(directory, reproduction=setup,
                                                generator=MiniSweGenerator(setup, ROOT))
                    for record in verifications:
                        updated = record.model_copy(update={"reproduction_generator": {
                            **record.reproduction_generator, "umgpt": {
                                **provenance, "calls": runtime.calls}}})
                        updated.write(directory / f"verification_record.{record.verifier_config}.json")
                    row["V4_outcome"] = verifications[0].reproduction.outcome.value
                row["complete"] = runtime.halt is None
        except Exception as exc:  # noqa: BLE001 - infrastructure stop is persisted
            row["error"] = str(exc)
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
            print(json.dumps(safe_object(row)), flush=True)
        if runtime.halt:
            (ROOT / "reports/umgpt_probe/BLOCKED.md").write_text(
                f"Stopped at {entry.instance_id}: {runtime.halt['termination']}.\n"
                f"Sanitized reason: {safe_object(runtime.halt)}\n"
                "Decision needed: resolve this infrastructure stop before any more paid calls.\n")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
