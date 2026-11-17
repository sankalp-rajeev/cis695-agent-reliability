#!/usr/bin/env python3
"""Independent task-preparation verifier. Python standard library only."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

WHEEL_SHA256 = "4e315ac60ff7b5b7186592b84d22df9befd898bba296a6b9665fdb3487fcd8f7"
SHA = r"[0-9a-f]{64}"
REQUIRED = {
    "instance_id",
    "repo",
    "version",
    "base_commit",
    "image",
    "archive",
    "pre_install",
    "integrity_preflight",
    "runner",
    "origin",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    path = Path(path)
    if path.suffix == ".gz":
        return json.loads(gzip.decompress(path.read_bytes()))
    return json.loads(path.read_text())


def validate_schema(registry):
    require(registry["schema"] == "task_spec_registry/1", "registry schema")
    require(isinstance(registry["cohort"], str) and registry["cohort"], "cohort")
    require(re.fullmatch(r"[0-9a-f]{40}", registry["built_by_commit"]), "built_by_commit")
    require(isinstance(registry["tasks"], list), "tasks must be a list")
    ids = []
    for task in registry["tasks"]:
        require(REQUIRED <= task.keys(), "missing required task field")
        iid = task["instance_id"]
        require(
            isinstance(iid, str) and re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+", iid),
            "instance ID",
        )
        ids.append(iid)
        require(
            isinstance(task["repo"], str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", task["repo"]),
            "repo",
        )
        require(isinstance(task["version"], str) and task["version"], "version")
        require(re.fullmatch(r"[0-9a-f]{40}", task["base_commit"]), "base_commit")
        require(isinstance(task["image"]["tag"], str) and task["image"]["tag"], "image tag")
        require(re.fullmatch("sha256:" + SHA, task["image"]["id"]), "image ID")
        require(Path(task["archive"]["path"]).is_absolute(), "archive absolute path")
        require(re.fullmatch(SHA, task["archive"]["sha256"]), "archive SHA")
        require(task["archive"]["pax_comment"] == task["base_commit"], "archive pax identity")
        proof = task["pre_install"]
        require(proof["wheel_sha256"] == WHEEL_SHA256, "wrong pinned wheel")
        require(re.fullmatch(SHA, proof["dataset_projection_sha256"]), "dataset projection SHA")
        require(isinstance(proof["spec"], dict), "pre_install spec")
        require(proof["spec"]["wheel_sha256"] == WHEEL_SHA256, "resolved wheel SHA")
        require(
            proof["spec"]["dataset_projection_sha256"] == proof["dataset_projection_sha256"],
            "resolved projection SHA",
        )
        require(proof["spec"]["swebench_version"] == "4.0.4", "resolved version")
        require(
            isinstance(proof["spec"]["commands"], list)
            and all(isinstance(c, str) for c in proof["spec"]["commands"]),
            "commands",
        )
        row = {k: task[k] for k in ("instance_id", "repo", "base_commit", "version")}
        require(proof["spec"]["dataset_row"] == row, "resolved dataset row")
        preflight = task["integrity_preflight"]
        require(preflight["status"] == "VERIFIED", "unverified task in registry")
        require(Path(preflight["receipt_path"]).is_absolute(), "receipt absolute path")
        require(re.fullmatch(SHA, preflight["receipt_sha256"]), "receipt SHA")
        runner = task["runner"]
        require(runner["name"] in ("django", "sympy", "pytest"), "runner name")
        require(isinstance(runner["evidence"], str) and runner["evidence"], "runner evidence")
        require(
            type(runner["django_parallel_one"]) is bool
            if runner["name"] == "django"
            else runner["django_parallel_one"] is None,
            "Django choice",
        )
        require(task["origin"] in ("prepared", "phase4_freeze"), "origin")
    require(len(ids) == len(set(ids)), "duplicate registry IDs")


def verify_registries(paths):
    tasks, verified = {}, 0
    for path in paths:
        registry = read(path)
        validate_schema(registry)
        for task in registry["tasks"]:
            iid = task["instance_id"]
            archive = task["archive"]
            require(digest(archive["path"]) == archive["sha256"], iid + " archive hash")
            with tarfile.open(archive["path"]) as tar:
                require(
                    tar.pax_headers.get("comment") == task["base_commit"],
                    iid + " archive pax comment",
                )
                for entry in tar:
                    require(
                        not entry.name.startswith("/") and ".." not in Path(entry.name).parts,
                        iid + " unsafe tar path",
                    )
            image = task["image"]["id"]
            proc = subprocess.run(
                ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            require(proc.stdout.strip() == image, iid + " image not local")
            receipt = task["integrity_preflight"]
            require(
                digest(receipt["receipt_path"]) == receipt["receipt_sha256"], iid + " receipt hash"
            )
            source = read(receipt["receipt_path"])
            require(
                source["status"] == "VERIFIED" and not source["mismatches"], iid + " source receipt"
            )
            require(
                source["base_commit"] == task["base_commit"]
                and source["archive_sha256"] == archive["sha256"],
                iid + " receipt identity",
            )
            require(
                source["tests_executed"] == 0 and source["collection_performed"] is False,
                iid + " task execution in preparation",
            )
            spec = dict(source["pre_install"])
            spec.pop("image_corroboration", None)
            spec.pop("replay", None)
            require(spec == task["pre_install"]["spec"], iid + " receipt spec differs")
            tasks.setdefault(iid, []).append(task)
            verified += 1
        print(
            f"REGISTRY {path}: {len(registry['tasks'])} tasks OK (schema, archive hash/pax, local image, receipt)"
        )
    return tasks, verified


def verify_parity(path, tasks, frozen_preflight):
    parity = read(path)
    require(
        parity["passed"] is True and parity["authority"] == "phase4_launch.validate_inputs",
        "golden authority/failure",
    )
    require(len(parity["tasks"]) == 3, "golden task count")
    for row in parity["tasks"]:
        iid = row["instance_id"]
        require(iid in tasks, "missing golden task")
        require(all(row["checks"].values()), "reported golden mismatch")
        frozen_receipt = frozen_preflight / "tasks" / iid / "source_receipt.json.gz"
        manifest = read(frozen_preflight / "manifest.json")
        relative = str(frozen_receipt.relative_to(frozen_preflight))
        require(
            digest(frozen_receipt) == manifest["receipt_sha256"][relative],
            iid + " frozen receipt hash",
        )
        for task in tasks[iid]:
            require(
                read(task["integrity_preflight"]["receipt_path"]) == read(frozen_receipt),
                iid + " golden full source receipt",
            )
            observed = {
                "archive_sha256": task["archive"]["sha256"],
                "image_id": task["image"]["id"],
                "pre_install_spec": task["pre_install"]["spec"],
                "preflight_identity": task["preflight_identity"],
                "runner": task["runner"],
            }
            require(observed == row["expected"], iid + " independent golden mismatch")
    print("GOLDEN: 3/3 task fields equal phase4_launch.validate_inputs expectations")


def verify_cohorts(directory, tasks=None):
    cohorts = {
        name: read(directory / (name + ".json"))
        for name in ("main100", "verified200", "verified500")
    }
    sets = {}
    for name, value in cohorts.items():
        ids = value["instance_ids"]
        require(len(ids) == len(set(ids)), "duplicate cohort IDs: " + name)
        require(ids == sorted(ids), "non-deterministic order: " + name)
        require(not any(i.startswith("psf__requests-") for i in ids), "requests in cohort")
        require(set(value["eligibility"]) == set(ids), "missing eligibility")
        require(
            all(s in ("ELIGIBLE", "UNCHECKED") for s in value["eligibility"].values()),
            "ineligible cohort member",
        )
        require(
            not set(ids) & {r["instance_id"] for r in value["excluded"]},
            "included/excluded overlap",
        )
        expected_counts = dict(
            Counter(i.split("__")[0] + "/" + i.split("__")[1].rsplit("-", 1)[0] for i in ids)
        )
        require(value["repo_counts"] == expected_counts, "repo counts")
        require(set(value["pilot_instances"]) <= set(ids), "pilot membership")
        sets[name] = set(ids)
    require(
        len(sets["verified500"]) + len(cohorts["verified500"]["excluded"]) == 500,
        "population/exclusions",
    )
    require(len(sets["main100"]) == 93 and len(sets["verified200"]) == 200, "cohort sizes")
    require(sets["main100"] < sets["verified200"] <= sets["verified500"], "non-nested cohorts")
    with (directory.parents[2] / "manifests/pilot.csv").open(newline="") as stream:
        import csv

        pilot = {r["instance_id"] for r in csv.DictReader(stream)}
    require(not sets["verified200"] & pilot, "pilot in 200")
    require(
        set(cohorts["verified500"]["pilot_instances"]) == sets["verified500"] & pilot,
        "500 pilot list",
    )
    print(
        f"COHORTS: 93 < 200 <= {len(sets['verified500'])}; nested, duplicate-free, requests excluded, pilot rules OK"
    )
    if tasks is not None:
        missing = sorted(sets["main100"] - set(tasks))
        print(
            f"MAIN COVERAGE: {93 - len(missing)}/93 have VERIFIED registry entries; {len(missing)} preparation failures"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registries", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--parity", type=Path, default=Path("reports/next_phases/task_prep/parity.json")
    )
    parser.add_argument("--cohort-dir", type=Path, default=Path("configs/e2e/cohorts"))
    parser.add_argument(
        "--frozen-preflight",
        type=Path,
        default=Path("reports/next_phases/phase4_rerun/fix10_integrity_preflight"),
    )
    args = parser.parse_args()
    try:
        tasks, count = verify_registries(args.registries)
        verify_parity(args.parity, tasks, args.frozen_preflight)
        verify_cohorts(args.cohort_dir, tasks)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print("FAIL: " + str(exc))
        return 1
    print(f"PASS: {count} registry entries independently verified; no reliability imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
