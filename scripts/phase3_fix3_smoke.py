#!/usr/bin/env python3
"""Base-only, collection-only smoke. Never constructs a test executor or scorer."""

import argparse
import hashlib
import json
import tarfile
import time
from collections import Counter
from pathlib import Path

from reliability.verifier.collection import validate_in_container
from reliability.verifier.container import TaskContainer
from reliability.verifier.selection import TestRunner

FROZEN = Path(
    "/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen"
)
ALLOWED = ("django__django-11820", "astropy__astropy-13977", "sympy__sympy-13480")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(args):
    assert args.task in ALLOWED and not args.output.exists()
    implementation = {}
    for name in ("collection.py", "id_validation.py"):
        path = Path(__file__).resolve().parents[1] / "src/reliability/verifier" / name
        implementation[str(path)] = sha(path.read_bytes())
    implementation[str(Path(__file__).resolve())] = sha(Path(__file__).read_bytes())
    tasks_raw = (FROZEN / "tasks.json").read_bytes()
    meta = next(t for t in json.loads(tasks_raw) if t["instance_id"] == args.task)
    selected_path = FROZEN / meta["selections"]["v2"]
    selected_raw = selected_path.read_bytes()
    tests = tuple(json.loads(selected_raw)["tests"])
    archive_path = Path("/home/sankalp/cg_repos/task_archives") / (args.task + ".tar")
    assert sha(archive_path.read_bytes()) == meta["base_archive_sha256"]
    expected, archived_configs = {}, {}
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith("testbed/"):
                name = member.name[8:]
                if name.endswith(".py") or Path(name).name in (
                    "setup.cfg",
                    "tox.ini",
                    "pytest.ini",
                    ".pytest.ini",
                    "pyproject.toml",
                ):
                    raw = archive.extractfile(member).read()
                    expected[name] = sha(raw)
                    if not name.endswith(".py"):
                        archived_configs[name] = raw.decode()
    started = time.monotonic()
    print("collection only:", args.task, meta["runner"]["name"], len(tests), flush=True)
    with TaskContainer(
        args.task, "", image=meta["image_tag"], experiment_id="phase3_fix3_collect_only"
    ) as container:
        rc, base = container.exec("git rev-parse HEAD")
        assert rc == 0, base
        rc, message = container.exec_input(
            "cat > /tmp/verifier_base_sources.json", json.dumps(expected)
        )
        assert rc == 0, message
        check = "import hashlib,json,pathlib; expected=json.load(open('/tmp/verifier_base_sources.json')); print(json.dumps({p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).is_file() else None for p in expected}))"
        import shlex

        rc, raw = container.exec("python -c " + shlex.quote(check), timeout_s=120)
        assert rc == 0, raw
        observed = json.loads(raw)
        mismatches = [p for p in expected if expected[p] != observed[p]]
        restored_configs = []
        for name in mismatches:
            assert name in archived_configs, "Image base Python source mismatch: " + name
            rc, message = container.exec_input("cat > " + shlex.quote(name), archived_configs[name])
            assert rc == 0, message
            restored_configs.append(name)
        if mismatches:
            rc, raw = container.exec("python -c " + shlex.quote(check), timeout_s=120)
            assert rc == 0 and json.loads(raw) == expected, "Base configuration restoration failed"
        validation = validate_in_container(
            container, tests, TestRunner(meta["runner"]["name"], "frozen runner"), timeout_s=1800
        )
        assert not validation.errors, validation.errors
        data = validation.to_dict()
        messages = {}
        for row in data["records"]:
            message = row.pop("message")
            if message:
                digest = sha(message.encode())
                messages[digest] = message
                row["message_sha256"] = digest
            else:
                row["message_sha256"] = ""
        summary = {
            "instance_id": args.task,
            "runner": meta["runner"]["name"],
            "image_head": base.strip(),
            "frozen_base_commit": meta["base_commit"],
            "image_HEAD_matches_frozen_base": base.strip() == meta["base_commit"],
            "archive_base_sources_verified": len(expected),
            "base_configs_restored": restored_configs,
            "base_tree_only": True,
            "collection_time_s": validation.duration_s,
            "native_collection_time_s": sum(g["duration_s"] for g in validation.groups),
            "selected_slots": len(tests),
            "INVALID_ID": sum(bool(r.reason) and not r.unavailable for r in validation.records),
            "reasons": dict(Counter(r.reason for r in validation.records if r.reason)),
            "unavailable_slots": data["unavailable_slots"],
            "expanded_slots": data["expanded_slots"],
            "expanded_instances": data["expanded_instances"],
            "native_runnable_instances": len(validation.runnable_ids),
            "native_disagreements": sum(r.native_disagrees for r in validation.records),
            "native_groups": len(validation.groups),
            "tests_executed": 0,
            "test_outcomes_recorded": False,
            "correctness_labels_read": False,
            "task_choice": "Django and Astropy supplied by user; SymPy is first sorted frozen task ID in that repository",
            "container_run_args": container.run_args(),
            "implementation_sha256": implementation,
            "input_sha256": {
                str(FROZEN / "tasks.json"): sha(tasks_raw),
                str(selected_path): sha(selected_raw),
            },
        }
    summary["total_wall_s"] = time.monotonic() - started
    args.output.mkdir(parents=True)
    (args.output / "collection.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.output / "messages.json").write_text(json.dumps(messages, indent=2) + "\n")
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=ALLOWED, required=True)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
