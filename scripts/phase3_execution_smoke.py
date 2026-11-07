#!/usr/bin/env python3
"""Base-only module smoke: collection and execution, without correctness joins."""

import argparse
import csv
import hashlib
import json
import shlex
import tarfile
import time
from collections import Counter
from pathlib import Path

from phase3_fix3_smoke import FROZEN
from reliability.verifier.container import ContainerTestExecutor, TaskContainer
from reliability.verifier.regression import TestStatus, run_to_dict
from reliability.verifier.selection import TestRunner


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(args):
    assert not args.output.exists()
    meta = next(
        t for t in json.loads((FROZEN / "tasks.json").read_text()) if t["instance_id"] == args.task
    )
    selected_path = FROZEN / meta["selections"]["v2"]
    tests = tuple(json.loads(selected_path.read_text())["tests"])
    archive_path = Path("/home/sankalp/cg_repos/task_archives") / (args.task + ".tar")
    assert sha(archive_path.read_bytes()) == meta["base_archive_sha256"]
    expected, configs = {}, {}
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith("testbed/"):
                name = member.name[8:]
                if (
                    name.endswith(".py")
                    or name == "bin/test"
                    or Path(name).name
                    in ("setup.cfg", "tox.ini", "pytest.ini", ".pytest.ini", "pyproject.toml")
                ):
                    raw = archive.extractfile(member).read()
                    expected[name] = sha(raw)
                    if not name.endswith(".py"):
                        configs[name] = raw.decode()
    args.output.mkdir(parents=True)
    started = time.monotonic()
    with TaskContainer(
        args.task, "", image=meta["image_tag"], experiment_id="phase3_module_smoke"
    ) as container:
        rc, head = container.exec("git rev-parse HEAD")
        assert rc == 0, head
        rc, _ = container.exec_input("cat > /tmp/verifier_expected.json", json.dumps(expected))
        assert rc == 0
        check = "import hashlib,json,pathlib; e=json.load(open('/tmp/verifier_expected.json')); print(json.dumps({p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).is_file() else None for p in e}))"
        rc, raw = container.exec("python -c " + shlex.quote(check))
        assert rc == 0, raw
        restored = []
        for name, digest in json.loads(raw).items():
            if digest != expected[name]:
                assert name in configs, "Base source differs: " + name
                rc, message = container.exec_input("cat > " + shlex.quote(name), configs[name])
                assert rc == 0, message
                restored.append(name)
        rc, raw = container.exec("python -c " + shlex.quote(check))
        assert rc == 0 and json.loads(raw) == expected
        executor = ContainerTestExecutor(
            container, runner=TestRunner(**meta["runner"]), evidence_dir=args.output / "raw"
        )
        result = executor.run(tests, patched=False, timeout_s=args.timeout_s)
        elapsed = time.monotonic() - started
        records = {r["selected_id"]: r for r in result.validation}
        invalid = {r.test_id for r in result.results if r.status is TestStatus.INVALID_ID}
        admitted = {tid for tid, r in records.items() if r.get("admitted")}
        skipped = set()
        for case in result.raw_results:
            if case.status is TestStatus.SKIPPED:
                skipped.update(result.raw_id_map.get(case.test_id, ()))
        strict = admitted - skipped
        starts = [e for e in result.events if e["event"] == "start"]
        ends = [e for e in result.events if e["event"] == "end"]
        collections = result.validation_summary.get("groups", [])
        modules = sorted(
            {t.split("::")[0] for t in tests}
            | {e["module"] for e in starts}
            | {e["module"] for e in collections}
        )
        rows = []
        for module in modules:
            originals = [t for t in tests if t.split("::")[0] == module]
            calls = [e for e in starts if e["module"] == module]
            rows.append(
                {
                    "module": module,
                    "collection_processes": sum(g["module"] == module for g in collections),
                    "execution_processes": len(calls),
                    "initial_module_processes": sum(not c["retry"] for c in calls),
                    "individual_retry_processes": sum(c["retry"] for c in calls),
                    "completed_processes": sum(e["module"] == module for e in ends),
                    "original_selected_slots": len(originals),
                    "admitted_original_slots_C": sum(t in admitted for t in originals),
                    "missing_original_slots_C": sum(
                        t not in admitted and t not in invalid for t in originals
                    ),
                    "INVALID_ID_original_slots": sum(t in invalid for t in originals),
                    "completed_runner_wall_s": sum(
                        e["duration_s"] for e in ends if e["module"] == module
                    ),
                }
            )
        summary = {
            "instance_id": args.task,
            "base_tree_only": True,
            "frozen_runner": meta["runner"]["name"],
            "actual_runner": result.validation_summary.get("context", {}).get(
                "runner", meta["runner"]["name"]
            ),
            "selected_original_slots": len(tests),
            "admitted_original_slots_C": len(admitted),
            "missing_original_slots_C": len(tests) - len(invalid) - len(admitted),
            "admitted_original_slots_S": len(strict),
            "missing_original_slots_S": len(tests) - len(invalid) - len(strict),
            "INVALID_ID": len(invalid),
            "COLLECTION_ERROR": sum(
                r.status is TestStatus.COLLECTION_ERROR for r in result.results
            ),
            "RUNNER_UNAVAILABLE": sum(
                r.status is TestStatus.RUNNER_UNAVAILABLE for r in result.results
            ),
            "base_outcome_counts": dict(Counter(r.status.value for r in result.results)),
            "execution_processes": len(starts),
            "initial_module_processes": sum(not c["retry"] for c in starts),
            "individual_retry_processes": sum(c["retry"] for c in starts),
            "validation_wall_s": result.validation_summary.get("duration_s"),
            "runner_wall_s_completed_processes": sum(e["duration_s"] for e in ends),
            "wall_s": elapsed,
            "timeout_s": args.timeout_s,
            "timed_out": result.timed_out,
            "base_source_files_verified": len(expected),
            "base_configs_restored": restored,
            "image_head": head.strip(),
            "correctness_labels_read": False,
            "patched_tree_executed": False,
            "outcomes_compared_to_labels": False,
            "policy_sensitivity_note": "Base-only slot accounting; task yes/no verdicts require paired captures and are not inferred here.",
        }
        (args.output / "base_run.json").write_text(
            json.dumps(run_to_dict(result, inline_raw=False), indent=2) + "\n"
        )
    with (args.output / "module_processes.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    source_files = [
        Path(__file__),
        *[
            Path(__file__).resolve().parents[1] / "src/reliability/verifier" / n
            for n in (
                "container.py",
                "collection.py",
                "id_validation.py",
                "validated_run.py",
                "regression.py",
                "result_parser.py",
                "selection.py",
            )
        ],
    ]
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "source_sha256": {str(p): sha(p.read_bytes()) for p in source_files},
                "input_sha256": {
                    str(FROZEN / "tasks.json"): sha((FROZEN / "tasks.json").read_bytes()),
                    str(selected_path): sha(selected_path.read_bytes()),
                    str(archive_path): meta["base_archive_sha256"],
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", choices=("django__django-11820", "sympy__sympy-13480"), required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-s", type=int, default=300)
    main(parser.parse_args())
