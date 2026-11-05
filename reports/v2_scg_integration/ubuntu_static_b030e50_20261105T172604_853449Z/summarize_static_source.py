"""Audit a completed static paired freeze and write new review evidence only."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(sys.argv[1])
REVIEW = Path(sys.argv[2])
FROZEN = OUT / "paired_frozen"
ORIGINAL = REVIEW / "reports/v2_discovery_cleanup/frozen_83"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def write(name, data):
    with (OUT / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def measured(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return dict(sum=sum(values) if values else None, measured_tasks=len(values),
                max=max(values) if values else None)


def main():
    tasks = json.loads((FROZEN / "tasks.json").read_text())
    old = {t["instance_id"]: t for t in json.loads((ORIGINAL / "tasks.json").read_text())}
    protocol = json.loads((FROZEN / "protocol.json").read_text())
    assert len(tasks) == len(old) == len({t["instance_id"] for t in tasks}) == 83
    assert {t["instance_id"] for t in tasks} == set(old)
    seals = json.loads((FROZEN / "artifact_hashes.json").read_text())
    assert all(sha(FROZEN / p) == h for p, h in seals.items())
    assert all(sha(FROZEN / p) == h for p, h in protocol["task_artifact_sha256"].items())
    old_seal = json.loads((ORIGINAL / "artifact_hashes.json").read_text())
    assert all(sha(ORIGINAL / p) == h == sha(FROZEN / "v2" / p) for p, h in old_seal.items())
    sources = protocol["scg_source_sha256"]
    for p, h in sources.items():
        payload = subprocess.check_output(["git", "show", protocol["scg_revision"] + ":" + p], cwd=REVIEW)
        assert hashlib.sha256(payload).hexdigest() == h == sha(FROZEN / "scg_source" / p)
    selections = {a: [] for a in ("v2", "scg")}
    inventory = []
    for t in tasks:
        iid = t["instance_id"]
        previous = old[iid]
        for key in ("repo", "base_commit", "base_archive_sha256", "patch_sha256", "image_tag", "image_id", "image_digest", "runner", "environment_status"):
            assert t[key] == previous[key], (iid, key)
        assert (FROZEN / t["patch_path"]).read_bytes() == (ORIGINAL / previous["patch_path"]).read_bytes()
        assert (FROZEN / t["issue_path"]).read_bytes() == (ORIGINAL / previous["issue_path"]).read_bytes()
        expected = json.loads((ORIGINAL / previous["test_manifest"]).read_text())["tests"]
        row = dict(instance_id=iid, repo=t["repo"], base_commit=t["base_commit"], archive_sha256=t["base_archive_sha256"],
                   patch_sha256=t["patch_sha256"], v2_reproduced=t["v2_reproduced"],
                   image_tag=t["image_tag"], historical_image_id=t["image_id"],
                   ubuntu_host_image_id=t["image_binding"]["host_image_id"],
                   image_availability=t["image_binding"]["availability"],
                   historical_id_comparison=t["image_binding"]["historical_id_comparison"],
                   source_fidelity_status=t["source_fidelity_status"],
                   source_union_files=len(t["base_source_sha256"]),
                   source_union_missing_files=[p for p, h in t["base_source_sha256"].items() if h is None],
                   original_source_subset_matches=all(t["base_source_sha256"][p] == h for p, h in previous["base_source_sha256"].items()),
                   paired_preparation_wall_s=t["paired_preparation_wall_s"])
        for arm in selections:
            r = json.loads((FROZEN / t["selections"][arm]).read_text())
            selections[arm].append(r)
            if arm == "v2":
                assert r["tests"] == expected
            row[arm + "_test_count"] = len(r["tests"]) if r["tests"] is not None else None
            for key in ("selection_status", "graph_status", "graph_build_s", "graph_input_preparation_s", "selection_s", "worker_wall_s", "selection_cpu_s", "selection_process_peak_rss_bytes", "reason"):
                row[arm + "_" + key] = r.get(key)
            row[arm + "_graph_failures"] = r.get("graph_failures", [])
            row[arm + "_graph_counts"] = r.get("graph_counts", {})
            row[arm + "_resolved_seed_count"] = len(r["resolved_seeds"]) if "resolved_seeds" in r else None
        inventory.append(row)
    write("task_preparation_inventory.json", inventory)
    with (OUT / "task_preparation_inventory.csv").open("x", newline="") as stream:
        fields = sorted(set().union(*(r.keys() for r in inventory)))
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for r in inventory:
            writer.writerow({k: "null" if v is None else json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in r.items()})
    arm_counts = {}
    for arm, rows in selections.items():
        arm_counts[arm] = dict(available_including_empty=sum(r["tests"] is not None for r in rows),
            nonempty=sum(bool(r["tests"]) for r in rows), empty=sum(r["tests"] == [] for r in rows),
            unavailable=sum(r["tests"] is None for r in rows),
            selection_status=dict(Counter(r["selection_status"] for r in rows)),
            graph_status=dict(Counter(r["graph_status"] for r in rows)),
            total_selected_ids=sum(len(r["tests"]) for r in rows if r["tests"] is not None),
            costs={k: measured(rows, k) for k in ("graph_build_s", "graph_input_preparation_s", "selection_s", "worker_wall_s", "selection_cpu_s", "selection_process_peak_rss_bytes")})
    preflight = json.loads((OUT / "offline_preflight.json").read_text())
    binding = json.loads((OUT / "ubuntu_image_bindings.json").read_text())
    summary = dict(tasks=83, protocol_sha256=sha(FROZEN / "protocol.json"),
        harness_revision=protocol["harness_revision"], scg_revision=protocol["scg_revision"],
        worktree=str(REVIEW), frozen_directory=str(FROZEN),
        validated=json.loads((OUT / "validate.result.json").read_text())["returncode"] == 0,
        launch_status=protocol["launch_status"], protocol_version=protocol["version"],
        original_frozen_artifacts_verified=len(old_seal), paired_sealed_artifacts_verified=len(seals),
        scg_source_files_verified=len(sources), archives_verified=sum(r["archive_hash_matches"] for r in preflight["rows"]),
        images=dict(Counter(r["availability"] for r in binding["rows"])),
        historical_image_comparisons=dict(Counter(r["historical_id_comparison"] for r in binding["rows"])),
        image_binding_sha256=sha(FROZEN / "image_bindings.json"),
        v2_exactly_reproduced=sum(t["v2_reproduced"] for t in tasks),
        arms=arm_counts, common_source_manifests=dict(Counter(t["source_fidelity_status"] for t in tasks)),
        common_source_files=sum(len(t["base_source_sha256"]) for t in tasks),
        common_source_missing_files=sum(h is None for t in tasks for h in t["base_source_sha256"].values()),
        common_source_missing_by_task={r["instance_id"]: r["source_union_missing_files"] for r in inventory if r["source_union_missing_files"]},
        protocol_preparation_wall_s=protocol["preparation_wall_s"],
        observed_prepare_stage_wall_s=json.loads((OUT / "prepare.result.json").read_text())["elapsed_s"],
        paired_task_preparation_wall_s=sum(t["paired_preparation_wall_s"] for t in tasks),
        static_worker_exceptions={r["instance_id"]: {a:r.get(a+"_reason") for a in selections if r.get(a+"_reason")} for r in inventory if any(r.get(a+"_reason") for a in selections)},
        runtime_import_fidelity="NOT_VERIFIED_BY_STATIC_PREPARATION; requires separately authorized pilot",
        benchmark_containers_started=0, benchmark_tests_executed=0,
        selection_configuration=protocol["scg_configuration"], regression_configuration=protocol["regression_config"])
    write("static_preparation_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
