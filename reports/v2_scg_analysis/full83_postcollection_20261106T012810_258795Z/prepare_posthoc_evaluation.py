"""Bind committed post-hoc labels/witnesses, then invoke the existing summary.

Usage: python3 -B prepare_posthoc_evaluation.py NEW_ANALYSIS_DIRECTORY
Requires a successful unlabeled summary in that directory. Never runs tests.
"""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PIN = "b030e508d849926b9a2260c70e1091adebfee993"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main(out):
    config = json.loads((out / "analysis_configuration.json").read_text())
    assert json.loads((out / "unlabeled_summary.command.json").read_text())["returncode"] == 0
    root, review, frozen = (Path(config[k]) for k in ("root", "review", "frozen"))
    complete = json.loads((Path(config["results"]) / "collection_complete.json").read_text())
    assert complete["tasks_accounted"] == 83 and complete["labels_read"] is False
    source = root / "docs/results_100.csv"
    pinned = subprocess.check_output(["git", "-C", str(review), "show", PIN + ":docs/results_100.csv"])
    working = source.read_bytes()
    assert working.replace(b"\r\n", b"\n") == pinned, "label changes beyond CRLF refused"
    assert sha(pinned) == "89192cb27935c33b62204dbbc5ac9090e8577407e367ec347542ca7c9155cb66"
    pinned_copy = out / "correctness_source_pinned.csv"
    if pinned_copy.exists():
        assert pinned_copy.read_bytes() == pinned
    else:
        with pinned_copy.open("xb") as stream:
            stream.write(pinned)
    rows = {r["instance_id"]: r for r in csv.DictReader(pinned.decode().splitlines())}
    manifest_path = root / "reports/callgraph_selection/amendment2_72ad21b/verified_patch_manifest.csv"
    manifest = {r["instance_id"]: r for r in csv.DictReader(manifest_path.open())}
    tasks = json.loads((frozen / "tasks.json").read_text())
    cohort = {t["instance_id"]: t for t in tasks}
    labels, bindings = {}, []
    for iid, task in cohort.items():
        row, exported = rows[iid], manifest[iid]
        assert row["source_run"] == exported["source_run"]
        assert task["source_run"] in (exported["source_run"], exported["export_source_run_raw"])
        assert exported["patch_sha256"].replace("sha256:", "") == task["patch_sha256"]
        assert sha((frozen / task["patch_path"]).read_bytes()) == task["patch_sha256"]
        assert row["oracle"] in ("resolved", "unresolved")
        labels[iid] = {"patch_sha256": task["patch_sha256"],
                       "correctness": "right" if row["oracle"] == "resolved" else "wrong"}
        bindings.append({"instance_id": iid, "source_run_frozen": task["source_run"],
                         "source_run_final_csv": row["source_run"],
                         "export_source_run_raw": exported["export_source_run_raw"],
                         "export_manifest_notes": exported["manifest_notes"],
                         "oracle": row["oracle"], "patch_sha256": task["patch_sha256"]})
    counts = collections.Counter(r["correctness"] for r in labels.values())
    assert counts == {"right": 69, "wrong": 14}
    witness_path = root / "reports/v2_discovery_cleanup/audit/known_witnesses_retained.json"
    witnesses = {}
    for row in json.loads(witness_path.read_text()):
        iid = row["instance_id"]
        entry = witnesses.setdefault(iid, {"patch_sha256": cohort[iid]["patch_sha256"], "test_ids": []})
        entry["test_ids"].append(row["test_id"])
    assert len(witnesses) == 5 and sum(len(r["test_ids"]) for r in witnesses.values()) == 6
    save(out / "correctness_sidecar.json", labels)
    save(out / "historical_witness_sidecar.json", witnesses)
    save(out / "label_candidate_bindings.json", bindings)
    save(out / "sidecar_provenance.json", {
        "unlabeled_summary_completed_first": True,
        "label_source": str(source), "label_source_working_sha256": sha(working),
        "label_source_pinned_sha256": sha(pinned), "source_pinned_git_revision": PIN,
        "working_vs_git_difference": "CRLF only; pinned LF bytes are authoritative",
        "source_run_aliases": [r for r in bindings if r["source_run_frozen"] != r["source_run_final_csv"]],
        "label_mapping": {"resolved": "right", "unresolved": "wrong"}, "counts": dict(counts),
        "patch_binding_manifest": str(manifest_path),
        "patch_binding_manifest_sha256": sha(manifest_path.read_bytes()),
        "witness_source": str(witness_path), "witness_source_sha256": sha(witness_path.read_bytes()),
        "witnesses": 6, "witness_tasks": 5,
        "official_gold_test_lists_read_for_sidecars": False})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(review / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONSTARTUP", None)
    command = [str(review / ".venv/bin/python"), "-B", "scripts/v2_scg_paired.py", "summarize",
               "--results", config["results"], "--out", str(out / "labeled_summary.json"),
               "--labels", str(out / "correctness_sidecar.json"),
               "--witnesses", str(out / "historical_witness_sidecar.json")]
    started = time.monotonic()
    result = subprocess.run(command, cwd=review, env=env, capture_output=True, text=True)
    for kind in ("stdout", "stderr"):
        with (out / ("labeled_summary." + kind)).open("x") as stream:
            stream.write(getattr(result, kind))
    save(out / "labeled_summary.command.json", {"command": command, "cwd": str(review),
         "PYTHONPATH": env["PYTHONPATH"], "returncode": result.returncode,
         "elapsed_s": time.monotonic() - started})
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "labeled_summary.json").read_text())
    for arm, data in summary["arms"].items():
        print(arm, data["correctness_metrics"], data["historical_witness_metrics"])
    print("paired", summary["paired_signals"], "both_completed", summary["both_completed"])


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
