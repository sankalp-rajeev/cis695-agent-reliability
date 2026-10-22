"""POST-HOC ANALYSIS ONLY. Re-runs V2 (regression) on frozen Group 4 patches.

Uses the existing verifier code path (TaskContainer, select_tests, run_regression).
Does not write into any run directory, does not run the agent, V4, or the oracle.
Does not modify records, configs, policy, or manifests.

Writes reports/failure_analysis/group4_failing_tests.json.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.agent.records import RepairRecord
from reliability.verifier.container import (
    ContainerRepoTree,
    ContainerTestExecutor,
    TaskContainer,
)
from reliability.verifier.integrity import check_integrity
from reliability.verifier.patch import parse_patch
from reliability.verifier.regression import Outcome, RegressionConfig, run_regression
from reliability.verifier.selection import SelectionConfig, select_tests

NOTICE = (
    "POST-HOC ANALYSIS ONLY. This file names tests that failed the existing "
    "regression suite on oracle-resolved patches. It must never feed back into "
    "any run, policy, manifest, or config."
)

GROUP4 = {
    "django__django-12209": "main_50_b",
    "django__django-14140": "main_50_b",
    "django__django-14631": "main_50_b",
    "pytest-dev__pytest-5809": "main_50_a",
    "sphinx-doc__sphinx-10435": "main_50_b",
}

OUT_DIR = Path(__file__).resolve().parent
OUT = OUT_DIR / "group4_failing_tests.json"
DETAIL = OUT_DIR / "group4_regression_rerun.json"
CACHE = OUT_DIR / "_baseline_cache_copy"


def rerun_one(instance_id: str, run: str) -> dict:
    task_dir = REPO / "runs" / run / "tasks" / instance_id
    record = RepairRecord.read(task_dir / "repair_record.json")
    frozen = FrozenPatch(
        path=task_dir / "patch.diff",
        sha256=record.patch.sha256,
        size_bytes=record.patch.size_bytes,
    )
    patch_text = read_patch(frozen).decode("utf-8")
    src_cache = REPO / "runs" / run / "_baseline_cache" / f"{instance_id}.baseline.json"
    if src_cache.is_file():
        CACHE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_cache, CACHE / src_cache.name)

    integrity = check_integrity(patch_text)
    patch = integrity.patch or (parse_patch(patch_text) if patch_text.strip() else None)
    if patch is None:
        return {
            "instance_id": instance_id,
            "error": "patch empty or unparseable",
            "failing": [],
        }

    with TaskContainer(
        instance_id=instance_id,
        patch_text=patch_text,
        experiment_id="failure_analysis_group4",
    ) as container:
        tree = ContainerRepoTree(container)
        selection = select_tests(patch, tree, SelectionConfig())
        executor = ContainerTestExecutor(container)
        if hasattr(executor, "runner"):
            executor.runner = selection.runner
        report = run_regression(
            instance_id,
            selection,
            executor,
            RegressionConfig(baseline_cache_dir=CACHE),
        )

    failing = [
        test_id
        for test_id, outcome in report.outcomes.items()
        if outcome is Outcome.REGRESSION
    ]
    return {
        "instance_id": instance_id,
        "source_run": run,
        "signal": report.signal.value,
        "n_selected": len(selection.tests),
        "n_executed": report.n_executed,
        "n_regressions": report.n_regressions,
        "notes": list(report.notes),
        "failing": failing,
        "summary": report.summary,
        "baseline_from_cache": report.baseline_from_cache,
    }


def main() -> int:
    print(NOTICE)
    details = []
    mapping: dict[str, list[str]] = {"_notice": [NOTICE]}
    for instance_id, run in GROUP4.items():
        print(f"rerun V2 {instance_id} from {run}", flush=True)
        row = rerun_one(instance_id, run)
        details.append(row)
        mapping[instance_id] = row.get("failing") or []
        print(
            f"  signal={row.get('signal')} failing={len(mapping[instance_id])}",
            flush=True,
        )
    mapping.pop("_notice", None)
    payload = {"_notice": NOTICE, **mapping}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    DETAIL.write_text(
        json.dumps({"notice": NOTICE, "tasks": details}, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    print(f"wrote {DETAIL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
