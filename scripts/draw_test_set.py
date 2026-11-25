#!/usr/bin/env python3
"""Draw the preregistered study test set from cached agent-visible tasks."""

import hashlib
import json
import os
import random
from pathlib import Path

from reliability.benchmark.loader import load_agent_tasks

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "reports/study_v1_5/inputs"
SEED = 20261120


def load_dev_ids() -> list[str]:
    ids = []
    for filename, expected_count in (
        ("task_specs_83.json", 83),
        ("task_specs_add9_e2e_v141.json", 9),
    ):
        registry = json.loads((ROOT / "configs/e2e" / filename).read_text())
        tasks = registry["tasks"]
        if len(tasks) != expected_count:
            raise ValueError(f"Expected {expected_count} tasks in {filename}")
        ids.extend(task["instance_id"] for task in tasks)
    if len(set(ids)) != 92:
        raise ValueError("The development registries must contain 92 distinct IDs")
    return ids


def main() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    tasks = load_agent_tasks()
    ids = {task.instance_id for task in tasks}
    if len(tasks) != 500 or len(ids) != 500:
        raise ValueError("Expected 500 distinct SWE-bench Verified tasks")
    dev_ids = set(load_dev_ids())
    if missing := dev_ids - ids:
        raise ValueError(f"Development IDs absent from Verified: {sorted(missing)}")

    candidates = ids - dev_ids
    order = sorted(iid for iid in candidates if not iid.startswith("psf__requests-"))
    if len(order) < 130:
        raise ValueError("Test pool cannot supply the first 130 IDs")
    random.Random(SEED).shuffle(order)
    batch1, batch2, reserve = order[:60], order[60:108], order[108:]
    draw = {
        "seed": SEED,
        "counts": {
            "loaded": len(tasks),
            "development": len(dev_ids),
            "requests_excluded": len(candidates) - len(order),
            "eligible": len(order),
            "batch1": len(batch1),
            "batch2": len(batch2),
            "reserve": len(reserve),
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "order": order,
        "batch1": batch1,
        "batch2": batch2,
        "reserve": reserve,
    }
    INPUTS.mkdir(parents=True, exist_ok=True)
    (INPUTS / "test_order.json").write_text(json.dumps(draw, indent=2) + "\n")
    print(json.dumps(draw["counts"]))


if __name__ == "__main__":
    main()
