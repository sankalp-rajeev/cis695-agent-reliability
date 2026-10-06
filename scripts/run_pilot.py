"""Phase 9: 10-task pilot, single pass, no retries, no config changes mid-run.

Full chain per task: agent → freeze → verifier (full + baseline, in-container)
→ oracle. Failures are recorded and the next task is started; a failed task is
never retried.

    .venv/bin/python scripts/run_pilot.py
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import traceback
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import yaml

from reliability.agent.claim_parser import ClaimStatus
from reliability.agent.isolation import probe_agent_network
from reliability.agent.records import RepairRecord, RunRole, load_records, summarise
from reliability.agent.runner import AgentLimits, MiniSweAgentBackend, run_task
from reliability.analysis.overlap import overlap_from_records
from reliability.benchmark.manifest import load_manifest
from reliability.billing import (
    fetch_deepseek_balance_usd,
    projected_cost_usd,
    require_sufficient_balance,
)
from reliability.env import assert_clean_interpreter
from reliability.oracle.records import load_records as load_oracle
from reliability.oracle.runner import run_oracle
from reliability.provenance import (
    RunProvenance,
    git_commit,
    git_dirty,
    require_clean_tree,
    utc_now,
    write_meta,
)
from reliability.verifier.container import image_for
from reliability.verifier.decision import get_policy
from reliability.verifier.record import (
    VerificationRecord,
)
from reliability.verifier.record import (
    load_records as load_verification,
)
from reliability.verifier.run import default_reproduction_setup, verify_task

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Docker Desktop's Linux CLI, which is not on PATH until the engine is up.
_DOCKER_CLI = pathlib.Path("/mnt/wsl/docker-desktop/cli-tools/usr/bin")
if _DOCKER_CLI.is_dir():
    os.environ["PATH"] = f"{_DOCKER_CLI}{os.pathsep}{os.environ.get('PATH', '')}"


def load_env_file(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_docker() -> None:
    import shutil
    import subprocess

    docker = shutil.which("docker")
    if not docker:
        raise SystemExit("docker is not on PATH; start Docker Desktop and retry")
    proc = subprocess.run(
        [docker, "info"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"docker is not ready: {proc.stderr.strip()[:200]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="configs/experiments/pilot.yaml")
    parser.add_argument("--run-root", default=None)
    parser.add_argument(
        "--allow-dirty", action="store_true",
        help="run from uncommitted code; dry_* experiments only")
    parser.add_argument(
        "--max-workers", type=int, default=1,
        help="tasks run concurrently via ThreadPoolExecutor; 1 is serial "
             "(pilot default). Recorded in meta.yaml regardless of value.")
    parser.add_argument(
        "--balance-usd", type=float, default=None,
        help="override the provider balance check (billing guard) instead of "
             "querying DEEPSEEK_API_KEY's account balance")
    args = parser.parse_args()
    if args.max_workers < 1:
        raise SystemExit("--max-workers must be >= 1")

    os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
    load_env_file(REPO_ROOT / ".env")
    assert_clean_interpreter()
    ensure_docker()

    experiment = yaml.safe_load((REPO_ROOT / args.experiment).read_text())
    if experiment.get("execution", {}).get("retries", 0) != 0:
        raise SystemExit("pilot.yaml must have retries: 0; refusing to run a retried pilot")

    model_cfg = yaml.safe_load((REPO_ROOT / experiment["model"]).read_text())
    if model_cfg.get("role") != "primary":
        raise SystemExit(f"{experiment['model']} is not role: primary")
    if not model_cfg.get("model_id"):
        raise SystemExit("primary.yaml has no model_id")
    if (model_cfg.get("verified") or {}).get("status") != "ok":
        raise SystemExit(
            "primary.yaml is not verified; run scripts/verify_model.py --update first")
    key_env = model_cfg["api_key_env"]
    if not os.environ.get(key_env):
        raise SystemExit(f"{key_env} is not set")

    # V4's generator is pinned and verified separately from the repair model.
    reproduction = default_reproduction_setup()
    generator_cfg = yaml.safe_load(
        (REPO_ROOT / "configs/model/generator.yaml").read_text())
    if not os.environ.get(generator_cfg["api_key_env"]):
        raise SystemExit(f"{generator_cfg['api_key_env']} is not set")

    agent_limits_cfg = yaml.safe_load(
        (REPO_ROOT / "configs/agent/mini_swe_agent.yaml").read_text())["limits"]
    # The claim prompt is the Phase 3.2 modified prompt. The experiment yaml
    # names the agent layer; the claim elicitation lives in swebench_claim.yaml
    # and must be used or Phase 9.3 cannot be measured.
    agent_config = REPO_ROOT / "configs/agent/swebench_claim.yaml"

    manifest = load_manifest(REPO_ROOT / experiment["benchmark"]["manifest"])
    experiment_id = experiment["experiment_id"]
    if experiment_id == "pilot_10":
        raise SystemExit(
            "pilot_10 is invalidated and must not be reused; pick a new experiment_id"
        )
    require_clean_tree(
        git_dirty(REPO_ROOT), experiment_id=experiment_id, allow_dirty=args.allow_dirty)
    run_root = REPO_ROOT / (args.run_root or f"runs/{experiment_id}")
    if (run_root / "meta.yaml").exists():
        raise SystemExit(
            f"{run_root} already holds a run; a single-pass experiment is not "
            "resumed or re-run. Pick a new experiment_id")
    run_root.mkdir(parents=True, exist_ok=True)

    # Billing guard: abort before any task starts if the account cannot cover
    # this run's worst-case cost. Checked against the provider's own balance
    # endpoint when the model is deepseek (it has one); otherwise --balance-usd
    # is required, since the guard needs a number from somewhere.
    projected = projected_cost_usd(
        len(manifest.entries),
        max_cost_usd_per_task=float(model_cfg["limits"]["max_cost_usd_per_task"]),
        generator_max_cost_usd=float(reproduction.budget.generator_max_cost_usd),
    )
    if args.balance_usd is not None:
        balance = args.balance_usd
    elif model_cfg.get("provider") == "deepseek":
        balance = fetch_deepseek_balance_usd(os.environ[model_cfg["api_key_env"]])
    else:
        raise SystemExit(
            f"no balance endpoint known for provider {model_cfg.get('provider')!r}; "
            "pass --balance-usd explicitly")
    print(f"billing guard: ${balance:.2f} available, ${projected:.2f} projected "
          f"({len(manifest.entries)} tasks) ... ", end="", flush=True)
    require_sufficient_balance(balance, projected)
    print("OK", flush=True)

    limits = AgentLimits(
        max_steps=model_cfg["limits"]["max_steps"],
        per_command_timeout_s=agent_limits_cfg["per_command_timeout_s"],
        per_task_timeout_s=agent_limits_cfg["per_task_timeout_s"],
        max_cost_usd=float(model_cfg["limits"]["max_cost_usd_per_task"]),
    )
    backend = MiniSweAgentBackend(
        model_id=model_cfg["model_id"],
        agent_config_path=agent_config,
        model_kwargs={
            "model_kwargs": {
                **model_cfg.get("model_kwargs", {}),
                "temperature": model_cfg.get("temperature", 0.0),
                "top_p": model_cfg.get("top_p", 1.0),
                "max_tokens": model_cfg.get("max_output_tokens", 8192),
            },
            "cost_tracking": "ignore_errors",
        },
    )

    if not manifest.entries:
        raise SystemExit("manifest is empty")
    # Inspect a container launched the way the agent launches one, and record
    # that NetworkMode. Writing the configured string here would let a run
    # claim isolation it did not have.
    print(f"probing agent network on {manifest.entries[0].instance_id}...",
          flush=True)
    agent_network_mode = probe_agent_network(
        agent_config, manifest.entries[0].instance_id)
    print(f"agent network mode (inspected): {agent_network_mode}", flush=True)

    if not (run_root / "meta.yaml").exists():
        write_meta(run_root, RunProvenance.capture(
            task_manifest_hash=manifest.content_hash,
            git_commit=git_commit(REPO_ROOT),
            git_dirty=git_dirty(REPO_ROOT),
            agent_scaffold=backend.scaffold,
            agent_version=backend.version,
            model_id=model_cfg["model_id"],
            temperature=float(model_cfg.get("temperature", 0.0)),
            max_steps=limits.max_steps,
            max_input_tokens_per_task=int(
                model_cfg["limits"]["max_input_tokens_per_task"]),
            max_output_tokens=int(model_cfg.get("max_output_tokens", 8192)),
            per_task_timeout_s=limits.per_task_timeout_s,
            verifier_policy_version=(
                f"{get_policy('full').version}+{get_policy('baseline').version}"),
            docker_image="swebench/sweb.eval.x86_64.<instance>:latest (derived)",
            swebench_version="5.0.2",
            timestamp_utc=utc_now(),
            agent_network_mode=agent_network_mode,
            reproduction_generator_model_id=reproduction.model.model_id,
            reproduction_generator_served_model=reproduction.model.served_model,
            reproduction_generator_fingerprint=reproduction.model.system_fingerprint,
            reproduction_generator_verified_on=reproduction.model.verified_on,
            reproduction_generator_prompt_sha256=reproduction.prompt_sha256,
            reproduction_max_tests=reproduction.budget.max_tests,
            reproduction_retries=reproduction.budget.retries,
            reproduction_generator_max_steps=reproduction.budget.generator_max_steps,
            reproduction_generator_max_cost_usd=(
                reproduction.budget.generator_max_cost_usd),
            reproduction_runner_sha256=reproduction.identity()["runner_sha256"],
            max_workers=args.max_workers,
        ))

    (run_root / "manifest.csv").write_bytes(manifest.path.read_bytes())
    (run_root / "manifest.sha256").write_text(
        f"{manifest.content_hash}  {manifest.path.name}\n", encoding="utf-8")

    print(f"experiment : {experiment_id}")
    print(f"model      : {model_cfg['model_id']}")
    print(f"manifest   : {manifest.path.name} @ {manifest.content_hash[:19]}... "
          f"({len(manifest)} tasks)")
    print(f"run root   : {run_root.relative_to(REPO_ROOT)}")
    print(f"step limit : {limits.max_steps}")
    print(f"generator  : {reproduction.model.model_id} "
          f"(served {reproduction.model.served_model}), "
          f"max_tests={reproduction.budget.max_tests} "
          f"retries={reproduction.budget.retries}")
    print(f"single pass, retries=0, max_workers={args.max_workers}.\n", flush=True)

    log_path = run_root / "pilot.log"
    started = time.monotonic()
    per_task: list[dict] = []

    if args.max_workers == 1:
        # Unchanged from before --max-workers existed: serial, print as each
        # task finishes, in manifest order.
        for i, entry in enumerate(manifest, 1):
            print(f"\n===== [{i}/{len(manifest)}] {entry.instance_id}  "
                  f"{image_for(entry.instance_id)} =====", flush=True)
            row = _run_one(
                entry, backend, run_root, experiment_id, manifest.content_hash,
                limits, log_path, reproduction)
            per_task.append(row)
            print(f"  agent={row.get('agent_termination')} "
                  f"claim={row.get('claim')} "
                  f"full={row.get('full_decision')} "
                  f"oracle={row.get('oracle_outcome')} "
                  f"cost=${row.get('cost_usd', 0):.4f} "
                  f"wall={row.get('wall_s', 0):.0f}s",
                  flush=True)
    else:
        # Each task owns `tasks/<instance_id>/` and writes only inside it
        # (agent/runner.py's run_manifest relies on the same property), so
        # concurrent tasks here do not contend. Printed as each completes,
        # which is arrival order, not manifest order; per_task itself is
        # still written out sorted by instance_id below for a deterministic
        # summary.json regardless of how many workers produced it.
        from concurrent.futures import ThreadPoolExecutor, as_completed
        print(f"running {len(manifest)} tasks across {args.max_workers} workers "
              "(completion order, not manifest order):", flush=True)
        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {
                pool.submit(
                    _run_one, entry, backend, run_root, experiment_id,
                    manifest.content_hash, limits, log_path, reproduction,
                ): entry
                for entry in manifest
            }
            for future in as_completed(futures):
                entry = futures[future]
                row = future.result()
                per_task.append(row)
                print(f"  [{len(per_task)}/{len(manifest)}] {entry.instance_id} "
                      f"agent={row.get('agent_termination')} "
                      f"claim={row.get('claim')} "
                      f"full={row.get('full_decision')} "
                      f"oracle={row.get('oracle_outcome')} "
                      f"cost=${row.get('cost_usd', 0):.4f} "
                      f"wall={row.get('wall_s', 0):.0f}s",
                      flush=True)
        per_task.sort(key=lambda r: r["instance_id"])

    elapsed = time.monotonic() - started
    summary = _summarise(run_root, per_task, elapsed, experiment)
    (run_root / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    _print_summary(summary)
    return 0 if summary["gates"]["all_passed"] else 1


def _run_one(entry, backend, run_root, experiment_id, manifest_hash, limits, log_path,
             reproduction) -> dict:
    """Run one task through the chain. Never retries. Catches and records."""
    t0 = time.monotonic()
    task_dir = run_root / "tasks" / entry.instance_id
    row: dict = {
        "instance_id": entry.instance_id,
        "image": image_for(entry.instance_id),
        "started_at": datetime.now(tz=UTC).isoformat(),
    }
    try:
        repair_path = task_dir / "repair_record.json"
        if repair_path.exists():
            repair = RepairRecord.read(repair_path)
            row["agent_skipped"] = True
        else:
            repair = run_task(
                entry, backend, run_root,
                experiment_id=experiment_id,
                run_role=RunRole.PILOT,
                manifest_hash=manifest_hash,
                limits=limits,
            )
        row.update({
            "agent_termination": repair.termination.value,
            "claim": repair.claim.status.value,
            "parseable": repair.claim.is_parseable,
            "cost_usd": repair.usage.api_cost_usd,
            "tokens_in": repair.usage.tokens_in,
            "tokens_out": repair.usage.tokens_out,
            "agent_duration_s": repair.duration_s,
            "patch_bytes": repair.patch.size_bytes,
        })
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        _log(log_path, entry.instance_id, "agent", exc)
        row["agent_error"] = f"{type(exc).__name__}: {exc}"[:400]
        row["wall_s"] = time.monotonic() - t0
        return row

    try:
        if not (task_dir / "verification_record.full.json").exists():
            verify_task(task_dir, configs=("full", "baseline"), use_container=True,
                        reproduction=reproduction)
        full = VerificationRecord.read(task_dir / "verification_record.full.json")
        baseline = VerificationRecord.read(
            task_dir / "verification_record.baseline.json")
        row.update({
            "full_decision": full.decision.decision.value,
            "full_reasons": list(full.decision.reasons),
            "baseline_decision": baseline.decision.decision.value,
            "integrity": full.integrity.outcome.value,
            "regression": full.regression.outcome.value,
            "regression_absence": (
                full.regression.absence.value if full.regression.absence else None),
            "static": full.static.outcome.value,
            "static_absence": (
                full.static.absence.value if full.static.absence else None),
            "reproduction": full.reproduction.outcome.value,
            "reproduction_absence": (
                full.reproduction.absence.value if full.reproduction.absence else None),
            "reproduction_detail": full.reproduction.detail,
            "reproduction_suite_sha256": full.reproduction.findings.get("suite_sha256"),
            "reproduction_generation_cost_usd": (
                full.reproduction.findings.get("generation") or {}).get("cost_usd", 0.0),
            "n_selected": len(full.selected_tests),
        })
    except Exception as exc:  # noqa: BLE001
        _log(log_path, entry.instance_id, "verifier", exc)
        row["verifier_error"] = f"{type(exc).__name__}: {exc}"[:400]
        row["wall_s"] = time.monotonic() - t0
        return row

    try:
        if not (task_dir / "oracle_record.json").exists():
            run_oracle(task_dir, timeout_s=1800, repo_root=REPO_ROOT)
        oracle = load_oracle(run_root)
        this = next(r for r in oracle if r.instance_id == entry.instance_id)
        row.update({
            "oracle_outcome": this.outcome.value,
            "resolved": this.resolved,
            "infrastructure_error": this.infrastructure_error,
            "fail_to_pass_all_passed": this.fail_to_pass.all_passed,
            "n_pass_to_pass": this.pass_to_pass.n_total,
        })
        row["overlap"] = overlap_from_records(full, this)
    except Exception as exc:  # noqa: BLE001
        _log(log_path, entry.instance_id, "oracle", exc)
        row["oracle_error"] = f"{type(exc).__name__}: {exc}"[:400]

    row["wall_s"] = time.monotonic() - t0
    return row


def _log(path: pathlib.Path, instance_id: str, stage: str, exc: BaseException) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n--- {instance_id} {stage} {datetime.now(tz=UTC).isoformat()} ---\n")
        traceback.print_exception(exc, file=fh)


def _summarise(run_root, per_task: list[dict], elapsed: float, experiment: dict) -> dict:
    repairs = load_records(run_root)
    verifications = load_verification(run_root, config="full")
    oracles = load_oracle(run_root)
    agent_sum = summarise(repairs)
    from reliability.oracle.records import summarise as oracle_sum
    o_sum = oracle_sum(oracles)

    n = len(per_task)
    complete = [
        r for r in per_task
        if r.get("oracle_outcome") and not r.get("infrastructure_error")
        and "verifier_error" not in r and "agent_error" not in r
        and "oracle_error" not in r
    ]
    parseable = sum(1 for r in repairs if r.claim.is_parseable)
    resolved_claims = sum(
        1 for r in repairs if r.claim.status is ClaimStatus.RESOLVED)

    gates_cfg = experiment["execution"]["gates"]
    gates = {
        "complete_without_infra": {
            "need": gates_cfg["min_completed_without_infra_failure"],
            "got": len(complete),
            "passed": len(complete) >= gates_cfg["min_completed_without_infra_failure"],
        },
        "parseable_claims": {
            "need": gates_cfg["min_parseable_claims"],
            "got": parseable,
            "passed": parseable >= gates_cfg["min_parseable_claims"],
        },
        "resolved_claims": {
            "need": gates_cfg["min_resolved_claims"],
            "got": resolved_claims,
            "passed": resolved_claims >= gates_cfg["min_resolved_claims"],
        },
    }
    gates["all_passed"] = all(g["passed"] for g in gates.values() if isinstance(g, dict))

    overlaps = [r["overlap"] for r in per_task if "overlap" in r]
    n_sel = sum(o["n_selected"] for o in overlaps)
    n_olap = sum(o["n_overlap_selected"] for o in overlaps)

    static_availability: dict[str, int] = {}
    for v in verifications:
        key = f"{v.static.outcome.value}:{v.static.absence.value if v.static.absence else 'reported'}"
        static_availability[key] = static_availability.get(key, 0) + 1

    return {
        "experiment_id": experiment["experiment_id"],
        "n_tasks": n,
        "elapsed_s": round(elapsed, 1),
        "total_cost_usd": round(sum(r.get("cost_usd") or 0 for r in per_task), 4),
        "gates": gates,
        "agent": agent_sum,
        "oracle": o_sum,
        "reproduction": {
            "outcomes": _count(
                f"{r.get('reproduction')}:{r.get('reproduction_absence') or 'reported'}"
                for r in per_task if r.get("reproduction")),
            "generation_cost_usd": round(sum(
                r.get("reproduction_generation_cost_usd") or 0 for r in per_task), 4),
        },
        "overlap": {
            "n_instances": len(overlaps),
            "n_selected_total": n_sel,
            "n_overlap_total": n_olap,
            "fraction_of_selected": (
                round(n_olap / n_sel, 4) if n_sel else None),
            "per_instance": overlaps,
        },
        "static_availability": static_availability,
        "per_task": per_task,
    }


def _count(keys) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    return counts


def _print_summary(summary: dict) -> None:
    print("\n========== PILOT SUMMARY ==========")
    gates = summary["gates"]
    n = summary["n_tasks"]
    print(f"complete without infra : {gates['complete_without_infra']['got']}/{n}"
          f"  (need ≥{gates['complete_without_infra']['need']})  "
          f"{'PASS' if gates['complete_without_infra']['passed'] else 'FAIL'}")
    print(f"parseable FINAL_STATUS : {gates['parseable_claims']['got']}/{n}"
          f"  (need ≥{gates['parseable_claims']['need']})  "
          f"{'PASS' if gates['parseable_claims']['passed'] else 'FAIL'}")
    ag = summary["agent"]
    print(f"  unparseable, split   : never finished {ag['never_finished']} "
          f"{ag['never_finished_by_termination']}, "
          f"finished but badly stated {ag['unparseable_after_finishing']}")
    print(f"RESOLVED claims        : {gates['resolved_claims']['got']}/{n}"
          f"  (need ≥{gates['resolved_claims']['need']})  "
          f"{'PASS' if gates['resolved_claims']['passed'] else 'FAIL'}")
    print(f"total cost             : ${summary['total_cost_usd']:.4f}")
    print(f"wall clock             : {summary['elapsed_s']:.0f}s")
    rep = summary["reproduction"]
    print(f"V4 reproduction        : {rep['outcomes']}  "
          f"(generation ${rep['generation_cost_usd']:.4f}, not in total cost)")
    olap = summary["overlap"]
    print(f"P2P overlap (5.3)      : {olap['n_overlap_total']}/{olap['n_selected_total']}"
          f" selected tests also in PASS_TO_PASS"
          f" ({olap['fraction_of_selected']})")
    print("per task:")
    for r in summary["per_task"]:
        print(f"  {r['instance_id']:<42} claim={r.get('claim')!s:<12} "
              f"cost=${(r.get('cost_usd') or 0):.4f}  wall={r.get('wall_s', 0):.0f}s  "
              f"oracle={r.get('oracle_outcome')}")


if __name__ == "__main__":
    raise SystemExit(main())
