"""Run the SWE-bench harness against a frozen patch and record the verdict.

Reads a task directory written by the runner, verifies the patch still matches
its recorded hash, submits it to the harness, and writes `oracle_verdict.json`
next to the record.

The verdict is deliberately kept out of the repair record. The record is what
the agent produced and claimed; the verdict is what the oracle found. Keeping
them in separate files means nothing downstream can read a resolution status out
of the agent's own account of its work.

Count-agnostic and parallel-safe like the runner: it takes a task directory, not
a manifest or an instance count, and writes only inside that directory.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.agent.records import RepairRecord
from reliability.env import clean_env

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", help="a tasks/<instance_id>/ directory")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    task_dir = pathlib.Path(args.task_dir).resolve()
    record = RepairRecord.read(task_dir / "repair_record.json")
    patch_path = task_dir / "patch.diff"

    # Verify against the hash recorded at freeze time, so a verdict can never be
    # attributed to a patch that changed after the agent produced it.
    frozen = FrozenPatch(
        path=patch_path, sha256=record.patch.sha256, size_bytes=record.patch.size_bytes
    )
    patch_text = read_patch(frozen).decode("utf-8")
    print(f"patch verified: {record.patch.sha256[:23]}... ({record.patch.size_bytes} bytes)")

    if not patch_text.strip():
        verdict = {
            "instance_id": record.instance_id,
            "resolved": False,
            "reason": "empty_patch",
            "note": "agent produced no diff; harness short-circuits empty predictions",
            "patch_sha256": record.patch.sha256,
        }
        (task_dir / "oracle_verdict.json").write_text(json.dumps(verdict, indent=2))
        print("empty patch — recorded as unresolved without invoking the harness")
        return 0

    model_slug = record.model_id.replace("/", "_")
    predictions = task_dir / "predictions.jsonl"
    predictions.write_text(
        json.dumps({
            "instance_id": record.instance_id,
            "model_name_or_path": model_slug,
            "model_patch": patch_text,
        }) + "\n",
        encoding="utf-8",
    )

    run_id = f"{record.experiment_id}__{record.instance_id}"
    cmd = [
        str(REPO_ROOT / ".venv/bin/python"), "-m", "swebench.harness.run_evaluation",
        "--dataset_name", "SWE-bench/SWE-bench_Verified",
        "--split", "test",
        "--predictions_path", str(predictions),
        "--instance_ids", record.instance_id,
        "--max_workers", "1",
        "--run_id", run_id,
        "--report_dir", str(task_dir),
        "--timeout", str(args.timeout),
    ]
    print(f"running harness: {record.instance_id}\n", flush=True)

    log_path = task_dir / "harness.log"
    with log_path.open("w", encoding="utf-8") as log:
        # clean_env strips import-affecting vars: ROS leaks 3.12 site-packages into
        # this 3.11 venv, and a shadowed import inside a verifier run would be
        # near-invisible afterwards. check=False - the returncode is recorded in
        # the verdict, and a harness failure is data rather than a crash.
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=clean_env(), check=False,
        )

    reports = sorted(task_dir.glob(f"*{run_id}.json")) or sorted(
        task_dir.glob("*.json_report.json")
    ) or [p for p in task_dir.glob("*.json")
          if p.name not in {"repair_record.json", "oracle_verdict.json"}]

    if not reports:
        print(f"no harness report found; see {log_path}")
        return 1

    report = json.loads(reports[-1].read_text())
    resolved_ids = report.get("resolved_ids", [])

    verdict = {
        "instance_id": record.instance_id,
        "resolved": record.instance_id in resolved_ids,
        "patch_sha256": record.patch.sha256,
        "harness_exit_code": proc.returncode,
        "report_file": reports[-1].name,
        "totals": {
            k: report.get(k) for k in [
                "total_instances", "submitted_instances", "completed_instances",
                "resolved_instances", "unresolved_instances",
                "empty_patch_instances", "error_instances",
            ]
        },
    }
    (task_dir / "oracle_verdict.json").write_text(json.dumps(verdict, indent=2))

    print(f"\n=== oracle verdict: {record.instance_id} ===")
    print(f"  resolved     : {verdict['resolved']}")
    print(f"  agent claimed: {record.claim.status.value}")
    agreement = (
        "n/a (claim unparseable)" if not record.claim.is_parseable
        else ("AGREE" if (record.claim.status.value == "RESOLVED") == verdict["resolved"]
              else "DISAGREE")
    )
    print(f"  claim vs oracle: {agreement}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
