"""Status of a run that may still be in progress. No model calls.

    .venv/bin/python scripts/interim_report.py pilot_15
    .venv/bin/python scripts/interim_report.py main_50_a --notify-line --event progress

A task is completed when its repair, full-verification, and oracle records are
all on disk. Infrastructure exclusions are oracle infrastructure errors, plus
a repair that ended in error or timeout and never received an oracle record.
Billing and rate-limit stops are not counted as infrastructure. Cost is the
agent API cost plus the V4 generation cost stored on the full verification
record. The leakage audit is re-run and only its pass/fail status is printed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from reliability.agent.records import RepairRecord, load_records
from reliability.oracle.records import OracleOutcome, load_records as load_oracle
from reliability.verifier.record import load_records as load_verification

_INFRA_TERMINATIONS = frozenset({"error", "timeout"})
_NOT_INFRA_TERMINATIONS = frozenset({"insufficient_balance", "rate_limited"})


def _index(records):
    return {record.instance_id: record for record in records}


def _generation_cost(verification) -> float:
    if verification is None:
        return 0.0
    generation = verification.reproduction.findings.get("generation") or {}
    try:
        return float(generation.get("cost_usd") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _expected(run_root: Path, experiment: str) -> int:
    copied = run_root / "manifest.csv"
    if copied.is_file():
        return max(sum(1 for line in copied.read_text().splitlines() if line.strip()) - 1, 0)
    config = REPO / "configs" / "experiments" / f"{experiment}.yaml"
    if config.is_file():
        for line in config.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("manifest:"):
                path = REPO / stripped.split(":", 1)[1].strip()
                if path.is_file():
                    rows = [
                        line for line in path.read_text().splitlines() if line.strip()
                    ]
                    return max(len(rows) - 1, 0)
    return 50


def _audit_status(run_root: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit_leakage.py"),
         "--runs", str(run_root)],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    status = "pass" if proc.returncode == 0 else "fail"
    scanned = ""
    for line in (proc.stdout or "").splitlines():
        if line.startswith("scanned:") or line.startswith("scope:"):
            scanned = line
    detail = scanned or "no scan line"
    return f"{status} (exit {proc.returncode}; {detail})"


def collect(run_root: Path, experiment: str, *, audit: bool = True) -> dict:
    run_root = Path(run_root)
    repairs = _index(load_records(run_root)) if (run_root / "tasks").is_dir() else {}
    verifications = (
        _index(load_verification(run_root, config="full"))
        if (run_root / "tasks").is_dir() else {}
    )
    oracles = _index(load_oracle(run_root)) if (run_root / "tasks").is_dir() else {}
    ids = sorted(set(repairs) | set(verifications) | set(oracles))

    rows = []
    infra = []
    for instance_id in ids:
        repair = repairs.get(instance_id)
        verification = verifications.get(instance_id)
        oracle = oracles.get(instance_id)
        completed = repair is not None and verification is not None and oracle is not None
        oracle_infra = oracle is not None and (
            oracle.infrastructure_error or oracle.outcome is OracleOutcome.INFRA_ERROR
        )
        termination = repair.termination.value if repair is not None else None
        stranded = (
            oracle is None
            and termination in _INFRA_TERMINATIONS
            and termination not in _NOT_INFRA_TERMINATIONS
        )
        is_infra = oracle_infra or stranded
        if is_infra:
            infra.append(instance_id)
        agent_cost = repair.usage.api_cost_usd if repair is not None else 0.0
        cost = agent_cost + _generation_cost(verification)
        rows.append({
            "instance_id": instance_id,
            "claim": repair.claim.status.value if repair is not None else None,
            "parseable": repair.claim.is_parseable if repair is not None else False,
            "decision": (
                verification.decision.decision.value if verification is not None else None
            ),
            "oracle": oracle.outcome.value if oracle is not None else None,
            "completed": completed,
            "infra": is_infra,
            "cost_usd": cost,
        })

    decisions = {"ACCEPT": 0, "FLAG": 0, "REJECT": 0}
    for row in rows:
        if row["decision"] in decisions:
            decisions[row["decision"]] += 1
    n_repairs = sum(1 for row in rows if row["claim"] is not None)
    n_parseable = sum(1 for row in rows if row["parseable"])
    total_cost = sum(row["cost_usd"] for row in rows)
    return {
        "experiment": experiment,
        "expected": _expected(run_root, experiment),
        "completed": sum(1 for row in rows if row["completed"]),
        "with_any_record": len(rows),
        "infrastructure_exclusions": infra,
        "parseable_claims": n_parseable,
        "repair_records": n_repairs,
        "cost_total_usd": total_cost,
        "cost_per_task_usd": (total_cost / len(rows)) if rows else 0.0,
        "decisions": decisions,
        "rows": rows,
        "audit": _audit_status(run_root) if audit else "not run",
    }


def notify_line(report: dict, event: str) -> str:
    return (
        f"tasks {report['completed']}/{report['expected']} | "
        f"infra {len(report['infrastructure_exclusions'])} | "
        f"cost ${report['cost_total_usd']:.4f} | "
        f"last {event}"
    )


def render(report: dict) -> str:
    lines = [
        f"experiment {report['experiment']}",
        f"completed tasks: {report['completed']}/{report['expected']}",
        f"tasks with any record: {report['with_any_record']}",
        f"infrastructure exclusions: {len(report['infrastructure_exclusions'])}",
        (
            f"parseable claims: {report['parseable_claims']}"
            f"/{report['repair_records']}"
        ),
        f"cost total: ${report['cost_total_usd']:.4f}",
        f"cost per task: ${report['cost_per_task_usd']:.4f}",
        (
            "decisions: "
            f"ACCEPT {report['decisions']['ACCEPT']}  "
            f"FLAG {report['decisions']['FLAG']}  "
            f"REJECT {report['decisions']['REJECT']}"
        ),
        f"audit: {report['audit']}",
        "",
        f"{'instance':42} {'claim':12} {'decision':8} {'oracle':14}",
    ]
    for row in report["rows"]:
        lines.append(
            f"{row['instance_id']:42} {str(row['claim']):12} "
            f"{str(row['decision']):8} {str(row['oracle']):14}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment")
    parser.add_argument("--notify-line", action="store_true")
    parser.add_argument("--event", default="progress")
    args = parser.parse_args()
    if args.event not in {"progress", "halt", "error", "finish"}:
        raise SystemExit("--event must be progress, halt, error, or finish")
    run_root = REPO / "runs" / args.experiment
    if not run_root.is_dir():
        raise SystemExit(f"no run directory at {run_root}")
    report = collect(run_root, args.experiment, audit=not args.notify_line)
    if args.notify_line:
        print(notify_line(report, args.event))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
