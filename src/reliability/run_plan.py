"""Decisions the runner makes before it starts a container.

Serial execution follows the manifest file from top to bottom. A resume runs
only the stages whose record file is absent.
"""

from __future__ import annotations

from pathlib import Path


def resolve_max_workers(cli_value: int | None, experiment: dict) -> int:
    """CLI override, otherwise the experiment file, otherwise serial.

    `main_50_*` is pinned to 1. A flag that asks for more is refused rather
    than quietly ignored.
    """
    if cli_value is None:
        value = int(experiment.get("execution", {}).get("max_workers", 1))
    else:
        value = cli_value
    if value < 1:
        raise SystemExit("--max-workers must be >= 1")
    experiment_id = str(experiment.get("experiment_id", ""))
    if experiment_id.startswith("main_50") and value != 1:
        raise SystemExit(f"{experiment_id} is pinned to max_workers=1")
    return value


def serial_ids(entries) -> list[str]:
    """File order. The serial runner does not sort this."""
    return [entry.instance_id for entry in entries]


def pending_stages(task_dir: Path) -> tuple[str, ...]:
    """Stages that still have no record. Present files are skipped."""
    missing = []
    if not (task_dir / "repair_record.json").is_file():
        missing.append("agent")
    if not (task_dir / "verification_record.full.json").is_file():
        missing.append("verifier")
    if not (task_dir / "oracle_record.json").is_file():
        missing.append("oracle")
    return tuple(missing)
