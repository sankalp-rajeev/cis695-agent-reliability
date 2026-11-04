"""Prepare/review a frozen V2 evaluation; execution requires explicit protocol approval.

Selection inputs are candidate patches and base source only. Labels and historical
witnesses are accepted only by the post-execution summary command, with patch hashes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from reliability.verifier.container import (
    ContainerRepoTree,
    ContainerTestExecutor,
    TaskContainer,
    _docker_bin,
    image_for,
)
from reliability.verifier.patch import parse_patch
from reliability.verifier.regression import RegressionConfig, run_regression, run_to_dict
from reliability.verifier.selection import Selection, SelectionConfig, TestRunner
from reliability.verifier.superseded_shadow_v2 import shadow_from_report

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TASKS = 83


class EnvironmentMismatch(RuntimeError):
    """The pinned image does not expose the frozen base-source files."""


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def code_paths():
    return sorted([*ROOT.glob("src/reliability/verifier/*.py"),
                   ROOT / "src/reliability/env.py", Path(__file__).resolve(),
                   ROOT / "configs/verifier/full.yaml", ROOT / "configs/verifier/baseline.yaml",
                   ROOT / "docs/VERIFIER_POLICY.md", ROOT / "pyproject.toml", ROOT / "uv.lock"])


def host_packages():
    return {"python": sys.version, "platform": platform.platform(),
            "packages": [list(pair) for pair in sorted((d.metadata["Name"], d.version)
                                                       for d in importlib.metadata.distributions())]}


def prepare(comparison, metadata, image_inventory, out):
    """Freeze source/config/manifests without starting a container or evaluating a test."""
    compared = json.loads(comparison.read_text())
    safe = json.loads(metadata.read_text())
    tasks = safe["tasks"]
    assert len(tasks) == EXPECTED_TASKS and not compared["unavailable"]
    assert {r["instance_id"] for r in compared["tasks"]} == set(tasks)
    assert compared["selection_config"] == asdict(SelectionConfig())
    assert sha(metadata.read_bytes()) == compared["metadata_sha256"]
    validation_root = comparison.parent.parent
    audit = json.loads((validation_root / "audit/summary.json").read_text())
    integration = json.loads((validation_root / "integration_audit/validation.json").read_text())
    assert audit["comparison_sha256"] == sha(comparison.read_bytes())
    assert audit["independently_proved_invalid"] == sum(r["removed"] for r in compared["tasks"])
    assert integration["tasks"] == 3 and integration["arms"] == 12
    assert integration["incomplete_PASS_count"] == 0 and integration["shadow_only"] is True
    evidence_paths = [validation_root / p for p in ("audit/summary.json", "integration_audit/validation.json",
                                                   "unit_final_complete.txt", "test_results.json", "lint.txt")]
    validation_hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in evidence_paths}
    for path, digest in compared["source_sha256"].items():
        assert sha((ROOT / path).read_bytes()) == digest, f"source drift: {path}"
    images = {}
    for line in image_inventory.read_text().splitlines():
        row = json.loads(line)
        images[row["Repository"] + ":" + row["Tag"]] = row
    out.mkdir(parents=True, exist_ok=False)
    export = ROOT / "frozen_patches_export.tgz"
    assert sha(export.read_bytes()) == compared["candidate_export_sha256"]
    manifest = []
    with tarfile.open(export) as patches:
        patch_manifest = {r["instance_id"]: r for r in csv.DictReader(io.StringIO(
            patches.extractfile("frozen_patches_export/manifest.csv").read().decode()))}
        assert set(patch_manifest) == set(tasks)
        for row in sorted(compared["tasks"], key=lambda t: t["instance_id"]):
            iid = row["instance_id"]
            patch = patches.extractfile(f"frozen_patches_export/{iid}.patch").read()
            assert sha(patch) == row["candidate_sha256"]
            archive_path = Path.home() / "cg_repos/task_archives" / f"{iid}.tar"
            assert sha(archive_path.read_bytes()) == row["archive_sha256"]
            paths = {tid.split("::", 1)[0] for tid in row["after"]}
            paths.update(f.path for f in parse_patch(patch.decode()) if f.path.endswith(".py"))
            with tarfile.open(archive_path) as archive:
                assert archive.pax_headers.get("comment") == tasks[iid]["base_commit"]
                members = {m.name: m for m in archive}
                source_hashes = {}
                for path in sorted(paths):
                    member = members.get("testbed/" + path)
                    source_hashes[path] = sha(archive.extractfile(member).read()) if member and member.isfile() else None
            tag = image_for(iid)
            image = images.get(tag)
            available = image is not None and image["ID"].startswith("sha256:")
            record = {"instance_id": iid, "repo": tasks[iid]["repo"],
                      "source_run": patch_manifest[iid]["source_run"],
                      "base_commit": tasks[iid]["base_commit"],
                      "patch_path": f"patches/{iid}.patch", "patch_sha256": sha(patch),
                      "test_manifest": f"tests/{iid}.json", "issue_path": f"issues/{iid}.txt",
                      "base_archive_sha256": row["archive_sha256"],
                      "base_source_sha256": source_hashes, "runner": row["runner"],
                      "selected": len(row["after"]), "original_selected": row["original"],
                      "image_tag": tag, "image_id": image["ID"] if available else None,
                      "image_digest": image["Digest"] if available else None,
                      "environment_status": "LOCAL_IMAGE_PRESENT_NOT_YET_SOURCE_VERIFIED" if available else "UNAVAILABLE_LOCAL_IMAGE"}
            (out / "patches").mkdir(exist_ok=True)
            (out / record["patch_path"]).write_bytes(patch)
            (out / "issues").mkdir(exist_ok=True)
            (out / record["issue_path"]).write_text(tasks[iid]["problem_statement"])
            write_json(out / record["test_manifest"], {"instance_id": iid, "tests": row["after"],
                                                     "by_tier": row["after_by_tier"],
                                                     "convention": row["convention"]})
            manifest.append(record)
    write_json(out / "tasks.json", manifest)
    write_json(out / "host_packages.json", host_packages())
    task_artifacts = {str(p.relative_to(out)): sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file()}
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in code_paths()}
    protocol = {
        "version": 1, "created_utc": datetime.now(UTC).isoformat(),
        "code_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "source_sha256": sources, "tasks": EXPECTED_TASKS,
        "task_artifact_sha256": task_artifacts,
        "validation_evidence_sha256": validation_hashes,
        "scope": "V2-only fresh paired base/patched evaluation, not a full V1-V4 study",
        "selection_config": asdict(SelectionConfig()), "regression_config": asdict(RegressionConfig()),
        "shadow_only": True, "network": "none", "image_pull": "never", "parallelism": 1,
        "task_order": "lexicographic instance_id, fixed before execution",
        "baseline_cache": "disabled; always fresh",
        "ranking_and_verdict_policy": "unchanged; no SCG filtering, labels or historical witnesses in execution",
        "budgets": "Production 300 seconds per pass, 600-second nominal initial pair. Production permits one 300-second patched confirmation. Shadow may add one base observation per FAIL candidate; costs recorded separately. per_instance_timeout_s is existing metadata, not a newly introduced hard stop.",
        "baseline_guard": "Existing BASELINE_UNRELIABLE behavior may stop before the patched pass; preserve it and record the missing pair.",
        "resources": "Sequential containers with unchanged TaskContainer defaults; no new CPU/memory limits. Record lifetime cgroup CPU and peak memory where available, wall/runner time and evidence bytes.",
        "fidelity": "Pin local image ID and compare selected-test plus candidate-changed Python files to the verified base archive before execution. Record image HEAD separately; relevant-source equivalence is not proof of full historical image identity.",
        "unavailable": "Account for every task; absent image, source mismatch or execution error has no invented V2 verdict. Never pull, replace an image, fabricate PASS, or overwrite a previous run.",
        "metrics": {"signals": ["PASS", "FAIL", "INCOMPLETE", "NOT_AVAILABLE", "BASELINE_UNRELIABLE"],
                    "completeness": "COMPLETE / INCOMPLETE_CONFIRMED / UNVERIFIABLE; include selected/paired/missing/raw concrete counts, timeouts and runner errors",
                    "known_regression_detection": "After collection, report witness selection, paired observation and confirmed detection, preserving historical-vs-current environment caveats.",
                    "classification": "Post-hoc patch-hash-matched correctness sidecar only: positive prediction=FAIL, target=wrong patch. Report precision, binary-only recall/F1, and all-labeled-task recall/F1 with abstentions explicitly counted as not detected; undefined ratios are null.",
                    "costs": "Runtime, runner time, confirmation/shadow cost, cgroup lifetime CPU/peak memory, output bytes; unavailable resource measurements remain null."},
        "inputs": {"comparison_sha256": sha(comparison.read_bytes()), "safe_metadata_sha256": sha(metadata.read_bytes()),
                   "candidate_export_sha256": sha(export.read_bytes()), "image_inventory_sha256": sha(image_inventory.read_bytes())},
        "launch_status": "PREPARED_FOR_REVIEW_NOT_AUTHORIZED",
    }
    write_json(out / "protocol.json", protocol)
    seal = {str(p.relative_to(out)): sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file()}
    write_json(out / "artifact_hashes.json", seal)
    print(json.dumps({"tasks": len(manifest), "environments": dict(Counter(t["environment_status"] for t in manifest)),
                      "protocol_sha256": seal["protocol.json"], "containers_started": 0}))


def verify_frozen(frozen):
    seals = json.loads((frozen / "artifact_hashes.json").read_text())
    assert all(sha((frozen / p).read_bytes()) == h for p, h in seals.items()), "frozen artifact drift"
    protocol = json.loads((frozen / "protocol.json").read_text())
    assert all(sha((frozen / p).read_bytes()) == h for p, h in protocol["task_artifact_sha256"].items()), "approved task/input drift"
    tasks = json.loads((frozen / "tasks.json").read_text())
    assert len(tasks) == len({t["instance_id"] for t in tasks}) == EXPECTED_TASKS
    assert protocol.get("tasks", EXPECTED_TASKS) == EXPECTED_TASKS
    assert all(sha((ROOT / p).read_bytes()) == h for p, h in protocol["source_sha256"].items()), "execution source/config drift"
    assert all(sha((ROOT / p).read_bytes()) == h for p, h in protocol.get("validation_evidence_sha256", {}).items()), "validation evidence drift"
    assert protocol["shadow_only"] is True and protocol["parallelism"] == 1
    assert protocol["selection_config"] == asdict(SelectionConfig())
    assert protocol["regression_config"] == asdict(RegressionConfig())
    if "host_packages.json" in protocol["task_artifact_sha256"]:
        assert json.loads((frozen / "host_packages.json").read_text()) == host_packages(), "host interpreter/package drift"
    return protocol, tasks, seals


def require_approval(protocol_bytes, approved_hash):
    if approved_hash != sha(protocol_bytes):
        raise ValueError("Execution requires the exact reviewed protocol SHA-256; preparation is not launch approval")


class LocalOnlyContainer(TaskContainer):
    def run_args(self):
        args = super().run_args()
        args.insert(2, "--pull=never")
        return args


class MeasuredExecutor:
    def __init__(self, executor):
        self.executor, self.container, self.calls = executor, executor.container, []

    def run(self, tests, *, patched, timeout_s):
        started = time.monotonic()
        result = self.executor.run(tests, patched=patched, timeout_s=timeout_s)
        self.calls.append({"patched": patched, "requested": list(tests),
                           "wall_s": time.monotonic() - started,
                           "runner_s": sum(e.get("duration_s", 0) for e in result.events if e.get("event") == "end"),
                           "run": run_to_dict(result, inline_raw=False)})
        return result


def preflight(container, task):
    expected = task["base_source_sha256"]
    code = ("import hashlib,json,pathlib,subprocess,sys; "
            "paths=" + repr(list(expected)) + "; "
            "print(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),"
            "'python':sys.version,'source_sha256':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() "
            "if pathlib.Path(p).is_file() else None for p in paths}}))")
    rc, raw = container.exec(shlex.join(["python", "-c", code]), timeout_s=120)
    assert rc == 0, raw[-1000:]
    observed = json.loads(raw)
    if observed["source_sha256"] != expected:
        raise EnvironmentMismatch("image selected/changed source differs from base archive")
    observed["head_matches_dataset_base"] = observed["head"] == task["base_commit"]
    observed["image_id"] = task["image_id"]
    return observed


def resource_snapshot(container):
    paths = ["/sys/fs/cgroup/cpu.stat", "/sys/fs/cgroup/memory.peak",
             "/sys/fs/cgroup/cpuacct/cpuacct.usage", "/sys/fs/cgroup/memory/memory.max_usage_in_bytes"]
    code = ("import pathlib,json; paths=" + repr(paths) + "; "
            "print(json.dumps({p:pathlib.Path(p).read_text() if pathlib.Path(p).is_file() else None for p in paths}))")
    try:
        rc, raw = container.exec(shlex.join(["python", "-c", code]), timeout_s=20)
        return json.loads(raw) if rc == 0 else {"unavailable": raw[-500:]}
    except (OSError, ValueError, TimeoutError) as exc:
        return {"unavailable": str(exc)}


def execute_one(task, frozen, folder):
    iid = task["instance_id"]
    tests = tuple(json.loads((frozen / task["test_manifest"]).read_text())["tests"])
    row = {"instance_id": iid, "patch_sha256": task["patch_sha256"], "signal": None,
           "completeness": None, "execution_status": "UNAVAILABLE_ENVIRONMENT", "selected": task["selected"],
           "selected_tests": list(tests)}
    folder.mkdir(parents=True, exist_ok=False)
    if task["image_id"] is None:
        row["reason"] = "No local image was available at freeze; no substitution or pull"
        write_json(folder / "result.json", row)
        return row
    patch = (frozen / task["patch_path"]).read_bytes()
    assert sha(patch) == task["patch_sha256"]
    container = LocalOnlyContainer(iid, patch.decode(), image=task["image_id"],
                                   experiment_id="v2_83_frozen")
    started = time.monotonic()
    try:
        inspect = subprocess.run([_docker_bin(), "image", "inspect", task["image_id"], "--format", "{{.Id}}"],
                                 capture_output=True, text=True, check=False)
        if inspect.returncode or inspect.stdout.strip() != task["image_id"]:
            row["reason"] = "Frozen local image is no longer available"
            return row
        container.start()
        observed = preflight(container, task)
        write_json(folder / "environment.json", observed)
        executor = MeasuredExecutor(ContainerTestExecutor(
            container, runner=TestRunner(**task["runner"]), evidence_dir=folder / "raw"))
        report = run_regression(iid, Selection(tests=tests), executor, RegressionConfig())
        initial_calls = len(executor.calls)
        native = report.signal
        shadow = shadow_from_report(report, (frozen / task["issue_path"]).read_text(), patch.decode(),
                                    ContainerRepoTree(container), executor)
        assert report.signal is native, "shadow altered native V2 signal"
        assert not (report.signal.value == "PASS" and report.completeness != "COMPLETE")
        for call in executor.calls:
            for name, path in call["run"]["evidence_files"].items():
                assert sha(Path(path).read_bytes()) == call["run"]["evidence_sha256"][name]
        row.update(execution_status="EXECUTED", signal=report.signal.value,
                   original_signal=report.original_signal.value, completeness=report.completeness,
                   incompleteness=list(report.incompleteness), regressions=list(report.regressions),
                   summary=report.summary, outcomes={t: o.value for t, o in report.outcomes.items()},
                   initial_calls=initial_calls, calls=executor.calls, shadow=shadow,
                   regression_wall_s=report.duration_s, resources=resource_snapshot(container))
    except EnvironmentMismatch as exc:
        row.update(execution_status="ENVIRONMENT_MISMATCH", reason=str(exc))
    except Exception as exc:  # noqa: BLE001 -- preserve errors for every fixed-cohort task
        row.update(execution_status="EXECUTION_ERROR", error_type=type(exc).__name__, reason=str(exc))
    finally:
        try:
            container.stop()
        except OSError as exc:
            row["cleanup_error"] = str(exc)
        row["wall_s"] = time.monotonic() - started
        row["evidence_bytes"] = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        if not (folder / "result.json").exists():
            write_json(folder / "result.json", row)
    return row


def run(frozen, out, approved_hash):
    require_approval((frozen / "protocol.json").read_bytes(), approved_hash)
    protocol, tasks, seal = verify_frozen(frozen)
    if frozen.resolve() == out.resolve() or frozen.resolve() in out.resolve().parents:
        raise ValueError("Execution output must be separate from the frozen inputs")
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "run_provenance.json", {"protocol_sha256": seal["protocol.json"],
                                            "frozen_artifacts_sha256": sha((frozen / "artifact_hashes.json").read_bytes()),
                                            "started_utc": datetime.now(UTC).isoformat(),
                                            "actual_git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
                                            "code_revision": protocol["code_revision"], "disk_before": asdict_disk(out)})
    rows = []
    for task in tasks:
        row = execute_one(task, frozen, out / "tasks" / task["instance_id"])
        rows.append(row)
        with (out / "ledger.jsonl").open("a") as stream:
            stream.write(json.dumps({k: row.get(k) for k in ("instance_id", "execution_status", "signal", "completeness", "wall_s")}) + "\n")
        print(task["instance_id"], row["execution_status"], row["signal"], flush=True)
    write_json(out / "results.json", rows)
    write_json(out / "collection_complete.json", {"tasks_accounted": len(rows), "finished_utc": datetime.now(UTC).isoformat(),
                                                  "disk_after": asdict_disk(out), "labels_read": False})


def asdict_disk(path):
    return dict(zip(("total", "used", "free"), shutil.disk_usage(path)))


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def metrics(rows, labels=None, witnesses=None):
    result = {"tasks_accounted": len(rows), "execution_status": dict(Counter(r["execution_status"] for r in rows)),
              "signals": dict(Counter(r["signal"] for r in rows if r["signal"] is not None)),
              "completeness": dict(Counter(r["completeness"] for r in rows if r["completeness"] is not None)),
              "wall_s": sum(r.get("wall_s", 0) for r in rows),
              "runner_s": sum(c["runner_s"] for r in rows for c in r.get("calls", [])),
              "evidence_bytes": sum(r.get("evidence_bytes", 0) for r in rows),
              "incomplete_PASS_count": sum(r["signal"] == "PASS" and r["completeness"] != "COMPLETE" for r in rows)}
    assert result["incomplete_PASS_count"] == 0
    execution = []
    for row in rows:
        initial = row.get("calls", [])[:row.get("initial_calls", 0)]
        phases = {}
        for name, patched in (("base", False), ("patched", True)):
            call = next((c for c in initial if c["patched"] is patched), None)
            run = call["run"] if call else {}
            accounted = {tid for ids in run.get("raw_id_map", {}).values() for tid in ids}
            phases[name] = {"observed": call is not None, "accounted_selected": len(accounted),
                            "raw_concrete_cases": len(run.get("raw_results", [])),
                            "statuses": dict(Counter(r["status"] for r in run.get("results", []))),
                            "timeout": run.get("timed_out"), "infrastructure_errors": run.get("infrastructure_errors", []),
                            "wall_s": call["wall_s"] if call else None,
                            "legacy_missing_or_timeout_ids": [r["test_id"] for r in run.get("results", [])
                                                              if r["status"] in ("not_run", "timeout")],
                            "unaccounted_raw_selected_ids": sorted(set(run.get("requested_tests", [])) - accounted)}
        resources = row.get("resources", {})
        cpu_stat = resources.get("/sys/fs/cgroup/cpu.stat") or ""
        cpu = next((int(line.split()[1]) / 1e6 for line in cpu_stat.splitlines()
                    if line.startswith("usage_usec ")), None)
        peak = resources.get("/sys/fs/cgroup/memory.peak") or resources.get("/sys/fs/cgroup/memory/memory.max_usage_in_bytes")
        execution.append({"instance_id": row["instance_id"], "selected": row["selected"], **phases,
                          "container_lifetime_cpu_s": cpu,
                          "container_lifetime_peak_memory_bytes": int(peak.strip()) if peak else None,
                          "confirmation_wall_s": sum(c["wall_s"] for c in initial[2:]),
                          "shadow_wall_s": row.get("shadow", {}).get("costs", {}).get("additional_wall_s", 0)})
    result["execution_details"] = execution
    if labels is not None:
        assert set(labels) == {r["instance_id"] for r in rows}, "labels must cover the exact frozen cohort"
        for r in rows:
            assert labels[r["instance_id"]]["patch_sha256"] == r["patch_sha256"], "label candidate mismatch"
            assert labels[r["instance_id"]]["correctness"] in ("right", "wrong")
        wrong = lambda r: labels[r["instance_id"]]["correctness"] == "wrong"
        tp = sum(r["signal"] == "FAIL" and wrong(r) for r in rows)
        fp = sum(r["signal"] == "FAIL" and not wrong(r) for r in rows)
        fn_binary = sum(r["signal"] == "PASS" and wrong(r) for r in rows)
        wrong_all = sum(wrong(r) for r in rows)
        result["correctness_metrics"] = {"positive_prediction": "FAIL", "target": "wrong patch", "true_positive": tp,
                                         "false_positive": fp, "false_negative_binary": fn_binary,
                                         "wrong_all": wrong_all, "precision": ratio(tp, tp + fp),
                                         "recall_binary": ratio(tp, tp + fn_binary), "recall_all_labeled": ratio(tp, wrong_all),
                                         "f1_binary": ratio(2 * tp, 2 * tp + fp + fn_binary),
                                         "f1_all_labeled": ratio(2 * tp, tp + fp + wrong_all),
                                         "binary_coverage": ratio(sum(r["signal"] in ("PASS", "FAIL") for r in rows), len(rows))}
    if witnesses is not None:
        assert set(witnesses) <= {r["instance_id"] for r in rows}, "witness task outside frozen cohort"
        observed = []
        for row in rows:
            witness = witnesses.get(row["instance_id"])
            if witness is None:
                continue
            assert witness["patch_sha256"] == row["patch_sha256"]
            for tid in witness["test_ids"]:
                initial = row.get("calls", [])[:row.get("initial_calls", 0)]
                paired = len(initial) >= 2 and all(tid in c["run"]["requested_tests"] and any(
                    r["test_id"] == tid and r["status"] not in ("not_run", "timeout") for r in c["run"]["results"])
                    for c in initial[:2])
                selected = tid in row.get("selected_tests", [])
                observed.append({"instance_id": row["instance_id"], "test_id": tid, "selected": selected,
                                 "paired_observation": paired,
                                 "confirmed_detection": tid in row.get("regressions", [])})
        result["historical_witness_observations"] = observed
        result["historical_witness_metrics"] = {
            "known": len(observed), "selected": sum(r["selected"] for r in observed),
            "paired": sum(r["paired_observation"] for r in observed),
            "confirmed": sum(r["confirmed_detection"] for r in observed),
            "detection_rate_all_known": ratio(sum(r["confirmed_detection"] for r in observed), len(observed)),
            "environment_caveat": "Historical witnesses are retention/execution targets, not assumed fresh-environment regressions."}
    return result


def summarize(out, labels_path=None, witnesses_path=None):
    complete = json.loads((out / "collection_complete.json").read_text())
    assert complete["tasks_accounted"] == EXPECTED_TASKS, "No labels/witnesses may be opened before collection is complete"
    rows = json.loads((out / "results.json").read_text())
    labels = json.loads(labels_path.read_text()) if labels_path else None
    witnesses = json.loads(witnesses_path.read_text()) if witnesses_path else None
    write_json(out / "metrics.json", metrics(rows, labels, witnesses))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--comparison", type=Path, required=True)
    prep.add_argument("--metadata", type=Path, required=True)
    prep.add_argument("--images", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--frozen", type=Path, required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--frozen", type=Path, required=True)
    execute.add_argument("--out", type=Path, required=True)
    execute.add_argument("--approved-protocol-sha256", required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--out", type=Path, required=True)
    summary.add_argument("--labels", type=Path)
    summary.add_argument("--witnesses", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.comparison, args.metadata, args.images, args.out)
    elif args.command == "validate":
        _, tasks, _ = verify_frozen(args.frozen)
        print(json.dumps({"verified": True, "tasks": len(tasks), "containers_started": 0}))
    elif args.command == "run":
        run(args.frozen, args.out, args.approved_protocol_sha256)
    else:
        summarize(args.out, args.labels, args.witnesses)


if __name__ == "__main__":
    main()
