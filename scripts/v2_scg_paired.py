"""Frozen updated V2 vs corrected SCG comparison, with an explicit launch barrier.

preflight/prepare/validate/plan never start containers. run requires a separately
reviewed plan hash and an explicit task scope; preparation is not authorization.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import v2_evaluation as v2
from reliability.verifier.regression import RegressionConfig, run_regression
from reliability.verifier.selection import Selection, SelectionConfig
from v2_scg_select import CONFIGURATION, SCG_FILES, SCG_REVISION, digest

ROOT = Path(__file__).resolve().parents[1]
V2_FROZEN = ROOT / "reports/v2_discovery_cleanup/frozen_83"
ARMS = ("v2", "scg")
V2_PROTOCOL_SHA256 = "f3c8ef5c802d26985bbe0f70f5bf9f7ac846c73ef496b50e48af606bfead463f"
write_json = v2.write_json
sha = v2.sha


def require(condition, message):
    # Freeze/launch integrity must also hold under python -O.
    if not condition:
        raise ValueError(message)


def git_bytes(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def check_scg_revision():
    actual = subprocess.check_output(
        ["git", "rev-parse", "origin/experiment/callgraph-typeprop"], cwd=ROOT).decode().strip()
    require(actual == SCG_REVISION, "SCG remote moved; review a new pin rather than silently changing algorithms")


def source_hashes():
    paths = [*v2.code_paths(), Path(__file__), ROOT / "scripts/v2_scg_select.py",
             ROOT / "scripts/v2_discovery_experiment.py"]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def copied_v2_selection(frozen, task):
    row = json.loads((frozen / task["test_manifest"]).read_text())
    require(row["instance_id"] == task["instance_id"], "V2 test manifest identity mismatch")
    return row["tests"]


def verify_v2_inputs(frozen):
    """Verify the archived V2 freeze without requiring its original WSL host.

    The V2 protocol, artifacts, source checks and configs remain immutable. A
    new paired freeze records/binds the actual Ubuntu host separately. Calling
    the old run-oriented verifier here would compare Ubuntu's kernel/platform
    string to the historical WSL inventory, preventing even offline preflight.
    """
    require(digest(frozen / "protocol.json") == V2_PROTOCOL_SHA256, "not the frozen 9654fc7 V2 protocol")
    protocol = json.loads((frozen / "protocol.json").read_text())
    seals = json.loads((frozen / "artifact_hashes.json").read_text())
    for hashes in (seals, protocol["task_artifact_sha256"]):
        require(all(digest(frozen / p) == h for p, h in hashes.items()), "V2 input artifact drift")
    for key in ("source_sha256", "validation_evidence_sha256"):
        require(all(digest(ROOT / p) == h for p, h in protocol[key].items()), "frozen V2 source/evidence drift")
    require(protocol["selection_config"] == asdict(SelectionConfig()) and
            protocol["regression_config"] == asdict(RegressionConfig()), "frozen V2 configuration drift")
    require(protocol["shadow_only"] is True and protocol["parallelism"] == 1, "frozen V2 runner drift")
    tasks = json.loads((frozen / "tasks.json").read_text())
    require(len(tasks) == len({t["instance_id"] for t in tasks}) == 83, "frozen V2 cohort drift")
    return protocol, tasks, seals


def preflight(frozen, archives):
    """Offline inventory only: no Docker commands, selectors or benchmark execution."""
    _, tasks, _ = verify_v2_inputs(frozen)
    check_scg_revision()
    rows = []
    for task in tasks:
        archive = archives / (task["instance_id"] + ".tar")
        rows.append({"instance_id": task["instance_id"], "patch_sha256": task["patch_sha256"],
                     "base_commit": task["base_commit"], "image_id": task["image_id"],
                     "image_tag": task["image_tag"], "environment_status": task["environment_status"],
                     "archive_present": archive.is_file(),
                     "archive_hash_matches": digest(archive) == task["base_archive_sha256"] if archive.is_file() else None,
                     "v2_selected": len(copied_v2_selection(frozen, task))})
    old_host = json.loads((frozen / "host_packages.json").read_text())
    current_host = v2.host_packages()
    return {"status": "PREFLIGHT_ONLY_NOT_AUTHORIZED", "tasks": len(rows), "rows": rows,
            "scg_revision": SCG_REVISION, "scg_configuration": CONFIGURATION,
            "containers_started": 0, "benchmark_tests_executed": 0,
            "environment_counts": dict(Counter(r["environment_status"] for r in rows)),
            "frozen_v2_protocol_sha256": digest(frozen / "protocol.json"),
            "host_comparison": {"historical_platform": old_host["platform"],
                "current_platform": current_host["platform"],
                "python_matches": old_host["python"] == current_host["python"],
                "packages_match": old_host["packages"] == current_host["packages"],
                "note": "prepare binds the current host for both arms; original inventory is preserved"}}


def export_scg(snapshot):
    check_scg_revision()
    hashes = {}
    for path in SCG_FILES:
        payload = git_bytes(SCG_REVISION, path)
        target = snapshot / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        hashes[path] = sha(payload)
    return hashes


def worker(task, patch, archive, expected, arm, snapshot, folder):
    with tempfile.TemporaryDirectory(prefix="paired-selection-request-") as temporary:
        request, result = Path(temporary) / "request.json", Path(temporary) / "result.json"
        write_json(request, {"task": task, "patch": str(patch.resolve()),
                             "archive": str(archive.resolve()), "expected_v2": expected})
        # Pin imports to this worktree, even when a shared venv is editable-installed
        # against the user's original checkout. A fresh process isolates each arm.
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts"),
                   PYTHONDONTWRITEBYTECODE="1")
        command = [sys.executable, "-B", str(ROOT / "scripts/v2_scg_select.py"),
                   "--request", str(request), "--arm", arm,
                   "--snapshot", str(snapshot.resolve()), "--out", str(result)]
        started = time.monotonic()
        proc = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
        (folder / f"{arm}_selection.stdout").write_text(proc.stdout)
        (folder / f"{arm}_selection.stderr").write_text(proc.stderr)
        if proc.returncode:
            return {"tests": None, "selection_status": "SELECTION_ERROR",
                    "graph_status": "UNKNOWN", "selection_s": None, "graph_build_s": None,
                    "worker_wall_s": time.monotonic() - started, "worker_returncode": proc.returncode,
                    "reason": proc.stderr[-2000:]}
        data = json.loads(result.read_text())
        data["worker_wall_s"] = time.monotonic() - started
        return data


def source_union(task, selections, archive):
    """One common fidelity manifest for both arms, including SCG-only test files."""
    require(digest(archive) == task["base_archive_sha256"], "base archive hash mismatch")
    paths = set(task["base_source_sha256"])
    for selection in selections.values():
        paths.update(t.split("::", 1)[0] for t in selection["tests"] or [])
    with tarfile.open(archive) as stream:
        require(stream.pax_headers.get("comment") == task["base_commit"], "base commit mismatch")
        members = {m.name: m for m in stream}
        result = {}
        for path in sorted(paths):
            member = members.get("testbed/" + path)
            result[path] = sha(stream.extractfile(member).read()) if member and member.isfile() else None
    require(all(result[p] == h for p, h in task["base_source_sha256"].items()),
            "frozen V2 source hashes disagree with archive")
    return result


def prepare(frozen, archives, out):
    """Static selection of all 83 tasks. No image inspection or test execution."""
    started = time.monotonic()
    _, original, _ = verify_v2_inputs(frozen)
    check_scg_revision()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(frozen, out / "v2")
    write_json(out / "host_packages.json", v2.host_packages())
    scg_hashes = export_scg(out / "scg_source")
    rows = []
    for source in sorted(original, key=lambda t: t["instance_id"]):
        task_started = time.monotonic()
        task = copy.deepcopy(source)
        iid = task["instance_id"]
        folder = out / "selections" / iid
        folder.mkdir(parents=True)
        expected = copied_v2_selection(frozen, task)
        archive = archives / (iid + ".tar")
        selections = {arm: worker(task, frozen / task["patch_path"], archive, expected,
                                  arm, out / "scg_source", folder) for arm in ARMS}
        # The original V2 list is authoritative even if reproduction is unavailable.
        # Such a task cannot execute until the shared source check is available.
        reproduced = selections["v2"]["tests"] == expected
        selections["v2"]["tests"] = expected
        task["v2_reproduced"] = reproduced
        task["source_fidelity_status"] = "UNAVAILABLE"
        if archive.is_file():
            task["base_source_sha256"] = source_union(task, selections, archive)
            task["source_fidelity_status"] = "FROZEN_UNION"
        task["selections"] = {}
        for arm, selection in selections.items():
            path = f"selections/{iid}/{arm}.json"
            selection.update(instance_id=iid, arm=arm)
            write_json(out / path, selection)
            task["selections"][arm] = path
        task["patch_path"] = "v2/" + task["patch_path"]
        task["issue_path"] = "v2/" + task["issue_path"]
        task["paired_preparation_wall_s"] = time.monotonic() - task_started
        rows.append(task)
        print(iid, {a: selections[a]["selection_status"] for a in ARMS}, flush=True)
    write_json(out / "tasks.json", rows)
    protocol = {
        "version": 1, "tasks": 83, "created_utc": datetime.now(UTC).isoformat(),
        "v2_revision": "9654fc7", "scg_revision": SCG_REVISION,
        "harness_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "v2_protocol_sha256": digest(frozen / "protocol.json"), "scg_source_sha256": scg_hashes,
        "scg_configuration": CONFIGURATION, "source_sha256": source_hashes(),
        "selection_config": asdict(SelectionConfig()), "regression_config": asdict(RegressionConfig()),
        "network": "none", "image_pull": "never", "parallelism": 1,
        "arm_order": "Alternating V2/SCG and SCG/V2 by sorted task index; fresh containers per arm",
        "test_id_normalization": "Unchanged ContainerTestExecutor/account_raw_output/django_label for BOTH arms",
        "source_fidelity": "Identical union of both test lists and original changed/selected source files",
        "confirmation": "Unchanged V2 production patched confirmation and shadow-only base observation",
        "budgets": "300s/pass, 600s nominal initial pair, existing confirmations; no new hard total stop",
        "selection_cost": "Measured reproduction for V2; SCG graph build and mapping/ranking separately. No truncation",
        "graph_partial": "Retain graph status/omissions; native verdict describes selected tests only",
        "launch_status": "PREPARED_FOR_REVIEW_NOT_AUTHORIZED", "preparation_wall_s": time.monotonic() - started,
        "task_artifact_sha256": {str(p.relative_to(out)): digest(p) for p in out.rglob("*") if p.is_file()},
    }
    write_json(out / "protocol.json", protocol)
    write_json(out / "artifact_hashes.json", {str(p.relative_to(out)): digest(p)
                                             for p in out.rglob("*") if p.is_file()})
    validate(out)


def validate(frozen):
    protocol = json.loads((frozen / "protocol.json").read_text())
    seals = json.loads((frozen / "artifact_hashes.json").read_text())
    require(all(digest(frozen / p) == h for p, h in seals.items()), "frozen artifact drift")
    require(all(digest(frozen / p) == h for p, h in protocol["task_artifact_sha256"].items()),
            "protocol-bound input drift")
    require(protocol["source_sha256"] == source_hashes(), "execution source/config drift")
    require(json.loads((frozen / "host_packages.json").read_text()) == v2.host_packages(),
            "paired host interpreter/package/platform drift; prepare and review on the execution host")
    require(protocol["regression_config"] == asdict(RegressionConfig()), "regression budget/policy drift")
    require(protocol["selection_config"] == asdict(SelectionConfig()), "V2 selection configuration drift")
    require(protocol["scg_configuration"] == CONFIGURATION and protocol["scg_revision"] == SCG_REVISION,
            "SCG configuration drift")
    require(protocol["network"] == "none" and protocol["image_pull"] == "never" and
            protocol["parallelism"] == 1, "runner setting drift")
    require(protocol["tasks"] == 83, "cohort size drift")
    for path, expected in protocol["scg_source_sha256"].items():
        require(digest(frozen / "scg_source" / path) == expected, "SCG snapshot drift")
        require(expected == sha(git_bytes(SCG_REVISION, path)), "SCG snapshot differs from pinned Git source")
    _, originals, _ = verify_v2_inputs(frozen / "v2")
    original = {t["instance_id"]: t for t in originals}
    tasks = json.loads((frozen / "tasks.json").read_text())
    require(len(tasks) == len({t["instance_id"] for t in tasks}) == 83 and
            {t["instance_id"] for t in tasks} == set(original), "cohort identity drift")
    require([t["instance_id"] for t in tasks] == sorted(original), "frozen task order drift")
    for task in tasks:
        source = original[task["instance_id"]]
        for key in ("repo", "base_commit", "patch_sha256", "base_archive_sha256", "image_tag",
                    "image_id", "image_digest", "runner", "environment_status"):
            require(task[key] == source[key], f"paired input drift: {key}")
        require(set(task["selections"]) == set(ARMS), "exactly two selections required")
        require(digest(frozen / task["patch_path"]) == task["patch_sha256"], "patch drift")
        for arm, path in task["selections"].items():
            require(path == f"selections/{task['instance_id']}/{arm}.json", "selection manifest alias")
            selection = json.loads((frozen / path).read_text())
            require(selection["instance_id"] == task["instance_id"] and selection["arm"] == arm,
                    "selection manifest identity mismatch")
            tests = selection["tests"]
            require(tests is None or (isinstance(tests, list) and all(isinstance(t, str) and
                    t.strip() == t and t and "\n" not in t for t in tests) and len(tests) == len(set(tests))),
                    "invalid or duplicate test IDs; never silently renormalize")
            if arm == "v2":
                require(tests == copied_v2_selection(frozen / "v2", source), "frozen V2 selection drift")
            require(tests is None or all(t.split("::", 1)[0] in task["base_source_sha256"] for t in tests)
                    or task["source_fidelity_status"] == "UNAVAILABLE", "selected file missing from fidelity union")
    return protocol, tasks


def make_plan(frozen, task_ids, out):
    _, tasks = validate(frozen)
    require(task_ids and len(task_ids) == len(set(task_ids)), "explicit unique pilot task scope required")
    require(set(task_ids) <= {t["instance_id"] for t in tasks}, "task outside cohort")
    schedule = [{"instance_id": task["instance_id"], "arms": list(ARMS if index % 2 == 0 else ARMS[::-1])}
                for index, task in enumerate(tasks) if task["instance_id"] in task_ids]
    write_json(out, {"protocol_sha256": digest(frozen / "protocol.json"),
                     "schedule": schedule, "status": "PLAN_FOR_REVIEW_NOT_AUTHORIZED"})


def empty_row(task, selection):
    return {"instance_id": task["instance_id"], "patch_sha256": task["patch_sha256"],
            "execution_status": "UNAVAILABLE_SELECTION", "signal": None, "completeness": None,
            "selected": len(selection["tests"]) if selection["tests"] is not None else None,
            "selected_tests": selection["tests"], "calls": [], "initial_calls": 0, "wall_s": 0,
            "resources": {}}


def execute_arm(task, selection, frozen, folder):
    """One shared executor boundary. The SCG IDs never enter V2 discovery."""
    stored = json.loads((frozen / task["selections"][selection["arm"]]).read_text())
    require(selection["tests"] == stored["tests"], "execution IDs differ from frozen selection")
    if selection["tests"] is None or not task["v2_reproduced"] or task["source_fidelity_status"] != "FROZEN_UNION":
        row = empty_row(task, selection)
        row["reason"] = selection["selection_status"] if selection["tests"] is None else "UNAVAILABLE_SHARED_SOURCE_OR_V2_REPRODUCTION"
        folder.mkdir(parents=True, exist_ok=False)
        write_json(folder / "result.json", row)
        return row
    if not selection["tests"]:
        # Preserve native empty-selection verdict without starting any container.
        report = run_regression(task["instance_id"], Selection(tests=()), None, RegressionConfig())
        row = empty_row(task, selection)
        row.update(execution_status="ZERO_SELECTION", signal=report.signal.value,
                   completeness=report.completeness, reason="Frozen selection is empty")
        folder.mkdir(parents=True, exist_ok=False)
        write_json(folder / "result.json", row)
        return row
    adapted = dict(task, test_manifest=task["selections"][selection["arm"]],
                   selected=len(selection["tests"]))
    started = time.monotonic()
    row = v2.execute_one(adapted, frozen, folder)
    row.setdefault("wall_s", time.monotonic() - started)
    return row


def phase_costs(row, selection):
    calls = row.get("calls", [])
    initial = calls[:row.get("initial_calls", 0)]
    base = next((c for c in initial if not c["patched"]), None)
    patched = next((c for c in initial if c["patched"]), None)
    error = row.get("execution_status") == "EXECUTION_ERROR"
    confirmation = None if error else sum(c["wall_s"] for c in initial[2:])
    shadow = None if error else sum(c["wall_s"] for c in calls[len(initial):])
    selection_s, graph_s = selection.get("selection_s"), selection.get("graph_build_s")
    worker_s = selection.get("worker_wall_s")
    return {"selection_s": selection_s, "graph_build_s": graph_s,
            "graph_input_preparation_s": selection.get("graph_input_preparation_s"),
            "selection_worker_wall_s": worker_s, "base_wall_s": base["wall_s"] if base else None,
            "patched_wall_s": patched["wall_s"] if patched else None,
            "production_confirmation_wall_s": confirmation, "shadow_confirmation_wall_s": shadow,
            "confirmation_wall_s": confirmation + shadow if not error else None, "execution_wall_s": row.get("wall_s"),
            "total_wall_s": worker_s + row["wall_s"] if worker_s is not None and "wall_s" in row else None,
            "selection_cpu_s": selection.get("selection_cpu_s"),
            "selection_process_peak_rss_bytes": selection.get("selection_process_peak_rss_bytes")}


def aggregate(pairs, labels=None, witnesses=None):
    summaries = {}
    for arm in ARMS:
        rows = [p["arms"][arm] for p in pairs]
        native = v2.metrics(rows, labels)
        if witnesses is not None:
            require(set(witnesses) <= {r["instance_id"] for r in rows}, "witness task outside reviewed scope")
            available = [r for r in rows if r["selected_tests"] is not None]
            available_ids = {r["instance_id"] for r in available}
            recorded = v2.metrics(available, witnesses={k: w for k, w in witnesses.items() if k in available_ids})
            observations = recorded["historical_witness_observations"]
            for row in rows:
                witness = witnesses.get(row["instance_id"])
                if witness is None:
                    continue
                require(witness["patch_sha256"] == row["patch_sha256"], "witness candidate mismatch")
                if row["selected_tests"] is None:
                    observations.extend({"instance_id": row["instance_id"], "test_id": tid,
                        "selected": None, "paired_observation": False, "confirmed_detection": False}
                        for tid in witness["test_ids"])
            native["historical_witness_observations"] = observations
            native["historical_witness_metrics"] = {
                "known": len(observations), "selected": sum(o["selected"] is True for o in observations),
                "selection_unknown": sum(o["selected"] is None for o in observations),
                "paired": sum(o["paired_observation"] for o in observations),
                "confirmed": sum(o["confirmed_detection"] for o in observations),
                "detection_rate_all_known": v2.ratio(sum(o["confirmed_detection"] for o in observations), len(observations)),
                "environment_caveat": "Historical targets are not assumed to reproduce in the current environment"}
        completed = [r for r in rows if r["execution_status"] == "EXECUTED" and r["signal"] in ("PASS", "FAIL")]
        costs = {}
        for key in ("selection_s", "graph_build_s", "graph_input_preparation_s", "base_wall_s", "patched_wall_s", "confirmation_wall_s",
                    "execution_wall_s", "total_wall_s", "selection_cpu_s"):
            values = [r["costs"][key] for r in rows if r["costs"][key] is not None]
            costs[key] = {"sum": sum(values) if values else None, "measured_tasks": len(values)}
        summaries[arm] = {**native, "completed_outcomes": len(completed),
            "abstentions": len(rows) - len(completed),
            "selection_status": dict(Counter(r["selection"]["selection_status"] for r in rows)),
            "graph_status": dict(Counter(r["selection"]["graph_status"] for r in rows)),
            "selected_total": sum(r["selected"] for r in rows if r["selected"] is not None),
            "selection_unavailable": sum(r["selected"] is None for r in rows),
            "zero_selections": sum(r["selected"] == 0 for r in rows), "costs": costs,
            "confirmed_regressions": sum(len(r.get("regressions", [])) for r in rows)}
        cpu_values, memory_values = [], []
        for row, detail in zip(rows, native["execution_details"]):
            cpu = detail["container_lifetime_cpu_s"]
            v1_cpu = row.get("resources", {}).get("/sys/fs/cgroup/cpuacct/cpuacct.usage")
            if cpu is None and v1_cpu is not None:
                cpu = int(v1_cpu.strip()) / 1e9
                detail["container_lifetime_cpu_s"] = cpu
            if cpu is not None:
                cpu_values.append(cpu)
            if detail["container_lifetime_peak_memory_bytes"] is not None:
                memory_values.append(detail["container_lifetime_peak_memory_bytes"])
        summaries[arm]["resource_metrics"] = {
            "container_cpu_s_sum": sum(cpu_values) if cpu_values else None,
            "cpu_measured_tasks": len(cpu_values),
            "container_peak_memory_bytes_max": max(memory_values) if memory_values else None,
            "memory_measured_tasks": len(memory_values)}
        summaries[arm]["execution_phases"] = {}
        for name in ("base", "patched"):
            phases = [d[name] for d in native["execution_details"]]
            summaries[arm]["execution_phases"][name] = {
                "tasks_observed": sum(p["observed"] for p in phases),
                "selected_accounted": sum(p["accounted_selected"] for p in phases),
                "raw_concrete_cases": sum(p["raw_concrete_cases"] for p in phases),
                "timeouts": sum(p["timeout"] is True for p in phases),
                "tasks_with_infrastructure_errors": sum(bool(p["infrastructure_errors"]) for p in phases),
                "unaccounted_selected_ids": sum(len(p["unaccounted_raw_selected_ids"]) for p in phases)}
        summaries[arm]["graph_strata"] = {}
        for status in {r["selection"]["graph_status"] for r in rows}:
            stratum = [r for r in rows if r["selection"]["graph_status"] == status]
            summaries[arm]["graph_strata"][status] = {
                "tasks": len(stratum), "signals": dict(Counter(r["signal"] for r in stratum if r["signal"] is not None)),
                "abstentions": sum(r["execution_status"] != "EXECUTED" or r["signal"] not in ("PASS", "FAIL") for r in stratum)}
    paired = Counter()
    deltas = []
    for pair in pairs:
        a, b = (pair["arms"][arm] for arm in ARMS)
        both = all(r["execution_status"] == "EXECUTED" and r["signal"] in ("PASS", "FAIL") for r in (a, b))
        paired[f"{a['signal']}/{b['signal']}"] += 1
        sa, sb = a["selected_tests"], b["selected_tests"]
        deltas.append({"instance_id": pair["instance_id"], "both_completed": both,
            "selection_overlap": len(set(sa) & set(sb)) if sa is not None and sb is not None else None,
            "selected_delta_scg_minus_v2": len(sb) - len(sa) if sa is not None and sb is not None else None,
            "total_wall_delta_scg_minus_v2": b["costs"]["total_wall_s"] - a["costs"]["total_wall_s"]
                if all(r["costs"]["total_wall_s"] is not None for r in (a, b)) else None})
    both_completed = [p for p, d in zip(pairs, deltas) if d["both_completed"]]
    detection = Counter(f"{p['arms']['v2']['signal']}/{p['arms']['scg']['signal']}" for p in both_completed)
    task_times = [p["total_wall_s"] for p in pairs if p.get("total_wall_s") is not None]
    return {"tasks_accounted": len(pairs), "arms": summaries, "paired_signals": dict(paired),
            "both_completed": len(both_completed), "paired_details": deltas,
            "regression_detection_both_completed": dict(detection),
            "paired_total_task_wall_s": sum(task_times) if task_times else None,
            "paired_wall_measured_tasks": len(task_times)}


def run(frozen, plan_path, out, approved_hash):
    plan_bytes = plan_path.read_bytes()
    v2.require_approval(plan_bytes, approved_hash)
    protocol, tasks = validate(frozen)
    plan = json.loads(plan_bytes)
    require(plan["protocol_sha256"] == digest(frozen / "protocol.json"), "plan protocol mismatch")
    scope = [r["instance_id"] for r in plan["schedule"]]
    require(scope and len(scope) == len(set(scope)) and set(scope) <= {t["instance_id"] for t in tasks},
            "invalid launch scope")
    expected = [{"instance_id": t["instance_id"], "arms": list(ARMS if i % 2 == 0 else ARMS[::-1])}
                for i, t in enumerate(tasks) if t["instance_id"] in scope]
    require(plan["schedule"] == expected, "schedule differs from frozen alternating order")
    require(not (out.resolve() == frozen.resolve() or frozen.resolve() in out.resolve().parents),
            "execution output must be separate from frozen inputs")
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    write_json(out / "run_provenance.json", {"plan_sha256": sha(plan_bytes), "plan": plan,
        "protocol_sha256": plan["protocol_sha256"], "started_utc": datetime.now(UTC).isoformat(),
        "host_packages": v2.host_packages(), "source_sha256": protocol["source_sha256"],
        "actual_git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "disk_before": v2.asdict_disk(out), "labels_read": False})
    by_id = {t["instance_id"]: t for t in tasks}
    pairs = []
    for entry in plan["schedule"]:
        task = by_id[entry["instance_id"]]
        task_started = time.monotonic()
        pair = {"instance_id": task["instance_id"], "patch_sha256": task["patch_sha256"],
                "base_commit": task["base_commit"], "image_id": task["image_id"],
                "image_tag": task["image_tag"], "image_digest": task["image_digest"],
                "environment_status": task["environment_status"],
                "base_archive_sha256": task["base_archive_sha256"],
                "runner": task["runner"], "arm_order": entry["arms"], "arms": {}}
        for arm in entry["arms"]:
            selection = json.loads((frozen / task["selections"][arm]).read_text())
            selection["arm"] = arm
            folder = out / "tasks" / task["instance_id"] / arm
            row = execute_arm(task, selection, frozen, folder)
            # Environment/evidence failures never become completed outcomes.
            if row["execution_status"] != "EXECUTED" and row["execution_status"] != "ZERO_SELECTION":
                row["signal"] = None
            require(not (row["signal"] == "PASS" and row["completeness"] != "COMPLETE"),
                    "incomplete PASS forbidden")
            row["selection"] = selection
            row["costs"] = phase_costs(row, selection)
            pair["arms"][arm] = row
            write_json(folder / "paired_arm.json", row)
        pair["execution_wall_s"] = time.monotonic() - task_started
        pair["preparation_wall_s"] = task["paired_preparation_wall_s"]
        pair["total_wall_s"] = pair["preparation_wall_s"] + pair["execution_wall_s"]
        write_json(out / "tasks" / task["instance_id"] / "paired.json", pair)
        pairs.append(pair)
    write_json(out / "results.json", pairs)
    write_json(out / "metrics.json", aggregate(pairs))
    write_json(out / "collection_complete.json", {"tasks_accounted": len(pairs), "scope": scope,
        "plan_sha256": sha(plan_bytes), "protocol_sha256": digest(frozen / "protocol.json"),
        "total_collection_wall_s": time.monotonic() - started, "labels_read": False,
        "disk_after": v2.asdict_disk(out),
        "results_sha256": digest(out / "results.json")})


def summarize(out, target, labels_path=None, witnesses_path=None):
    complete = json.loads((out / "collection_complete.json").read_text())
    rows = json.loads((out / "results.json").read_text())
    require(complete["tasks_accounted"] == len(rows) == len(set(complete["scope"])) and
            {r["instance_id"] for r in rows} == set(complete["scope"]), "collection incomplete")
    require(digest(out / "results.json") == complete["results_sha256"], "collected evidence drift")
    # Labels/witnesses are first read here, after the whole reviewed scope finishes.
    labels = json.loads(labels_path.read_text()) if labels_path else None
    witnesses = json.loads(witnesses_path.read_text()) if witnesses_path else None
    write_json(target, aggregate(rows, labels, witnesses))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "prepare"):
        sub = commands.add_parser(command)
        sub.add_argument("--v2-frozen", type=Path, default=V2_FROZEN)
        sub.add_argument("--archives", type=Path, default=Path.home() / "cg_repos/task_archives")
        sub.add_argument("--out", type=Path, required=True)
    for command in ("validate", "plan", "run"):
        sub = commands.add_parser(command)
        sub.add_argument("--frozen", type=Path, required=True)
        if command != "validate":
            sub.add_argument("--out", type=Path, required=True)
        if command == "plan":
            sub.add_argument("--task", action="append", required=True)
        if command == "run":
            sub.add_argument("--plan", type=Path, required=True)
            sub.add_argument("--approved-plan-sha256", required=True)
    sub = commands.add_parser("summarize")
    sub.add_argument("--results", type=Path, required=True)
    sub.add_argument("--out", type=Path, required=True)
    sub.add_argument("--labels", type=Path)
    sub.add_argument("--witnesses", type=Path)
    args = parser.parse_args()
    if args.command == "preflight":
        write_json(args.out, preflight(args.v2_frozen, args.archives))
    elif args.command == "prepare":
        prepare(args.v2_frozen, args.archives, args.out)
    elif args.command == "validate":
        _, tasks = validate(args.frozen)
        print(json.dumps({"verified": True, "tasks": len(tasks), "containers_started": 0}))
    elif args.command == "plan":
        make_plan(args.frozen, args.task, args.out)
    elif args.command == "run":
        run(args.frozen, args.plan, args.out, args.approved_plan_sha256)
    else:
        summarize(args.results, args.out, args.labels, args.witnesses)


if __name__ == "__main__":
    main()
