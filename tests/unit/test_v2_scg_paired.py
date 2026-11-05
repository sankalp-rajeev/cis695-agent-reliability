"""Paired harness invariants. Synthetic archives/executors only; no Docker."""
from __future__ import annotations

import importlib
import io
import json
import subprocess
import sys
import tarfile
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
h = importlib.import_module("v2_scg_paired")
s = importlib.import_module("v2_scg_select")
from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    TestResult,
    TestStatus,
)
from reliability.verifier.selection import SelectionConfig, TestRunner

IID = "pytest-dev__pytest-5809"
LOCAL_ID = "sha256:" + "a" * 64
TESTS = ["tests/test_api.py::test_compute", "tests/test_api.py::test_other"]
PATCH = """diff --git a/api.py b/api.py
--- a/api.py
+++ b/api.py
@@ -1,2 +1,2 @@
 def compute(x):
-    return x + 1
+    return x + 2
"""


@pytest.fixture(autouse=True)
def no_docker(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No live container is permitted in harness validation")
    monkeypatch.setattr(h.v2.LocalOnlyContainer, "start", forbidden)
    monkeypatch.setattr(h.images, "daemon_id", lambda: "synthetic-daemon")
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: {
        "availability": "MISSING", "host_image_id": None, "repo_digests": [], "reason": "Synthetic missing image"})


def task_and_archive(tmp_path):
    archive = tmp_path / "base.tar"
    contents = {"api.py": b"def compute(x):\n    return x + 1\n",
                "tests/test_api.py": b"from api import compute\ndef test_compute():\n    assert compute(2) == 3\ndef test_other():\n    assert True\n"}
    with tarfile.open(archive, "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": "base"}) as stream:
        for path, payload in contents.items():
            member = tarfile.TarInfo("testbed/" + path)
            member.size = len(payload)
            stream.addfile(member, io.BytesIO(payload))
    patch = tmp_path / "candidate.patch"
    patch.write_text(PATCH)
    task = {"instance_id": IID, "repo": "pytest-dev/pytest", "base_commit": "base",
            "base_archive_sha256": s.digest(archive), "patch_sha256": s.digest(patch),
            "runner": asdict(TestRunner("pytest", "pytest.ini")), "patch_path": patch.name,
            "issue_path": "issue.txt", "image_id": None, "image_tag": "frozen:exact",
            "image_digest": None, "environment_status": "UNAVAILABLE_LOCAL_IMAGE",
            "base_source_sha256": {"api.py": h.sha(contents["api.py"])} }
    return task, archive, patch


@pytest.fixture(scope="module")
def scg_snapshot(tmp_path_factory):
    snapshot = tmp_path_factory.mktemp("scg-snapshot")
    hashes = h.export_scg(snapshot)
    assert set(hashes) == set(s.SCG_FILES)
    return snapshot


def test_scg_uses_pinned_corrected_mapping_and_own_ids(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    # Supplying impossible V2 IDs cannot influence B selection.
    row = h.worker(task, patch, archive, ["never_discover_v2"], "scg", scg_snapshot, tmp_path)
    assert row["selection_status"] == "SELECTED", row
    assert row["tests"] == [TESTS[0]]
    assert row["graph_status"] == "complete"
    assert row["graph_build_s"] > 0 and row["selection_s"] > 0
    assert row["selection_process_peak_rss_bytes"] > 0
    assert row["mapping"][0]["status"] == "resolved"


def test_scg_never_calls_v2_selector(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    request = tmp_path / "request.json"
    h.write_json(request, {"task": task, "patch": str(patch), "archive": str(archive), "expected_v2": []})
    # A separate process is also how production isolates diagnostic module imports.
    code = """
import json, pathlib, sys
import v2_scg_select as s
def forbidden(*a, **k):
    raise RuntimeError('V2 discovery called from SCG')
s.select_tests = forbidden
result = s.select(json.loads(pathlib.Path(sys.argv[1]).read_text()), 'scg', pathlib.Path(sys.argv[2]))
assert result['tests'] == ['tests/test_api.py::test_compute'], result
"""
    proc = subprocess.run([sys.executable, "-c", code, str(request), str(scg_snapshot)],
                          env={**h.os.environ, "PYTHONPATH": str(ROOT / "scripts") + ":" + str(ROOT / "src")},
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


def test_scg_mapping_failure_has_no_fallback(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    # Change the named but uncalled test-independent function instead.
    patch.write_text(PATCH.replace("compute", "absent"))
    # Exact mapping must fail rather than inventing the mismatched function.
    task["patch_sha256"] = s.digest(patch)
    row = h.worker(task, patch, archive, TESTS, "scg", scg_snapshot, tmp_path)
    assert row["tests"] is None
    assert row["selection_status"] == "UNAVAILABLE_NO_RESOLVED_SEEDS"
    assert row["mapping_diagnostics"]


def selection(tests, arm="scg", status=None):
    return {"tests": tests, "arm": arm, "selection_status": status or (
        "SELECTED" if tests else "ZERO_SELECTION" if tests == [] else "UNAVAILABLE"),
        "graph_status": "complete", "selection_s": 1, "graph_build_s": 2 if arm == "scg" else None,
        "worker_wall_s": 4, "selection_cpu_s": 0.5}


def task_ready(tmp_path):
    task, _, _ = task_and_archive(tmp_path)
    task.update(v2_reproduced=True, source_fidelity_status="FROZEN_UNION",
                selections={a: a + ".json" for a in h.ARMS}, docker_daemon_id="synthetic-daemon")
    task["image_binding"] = h.images.binding_record(task, h.images.inspect_image(task["image_tag"]))
    for arm in h.ARMS:
        h.write_json(tmp_path / (arm + ".json"), selection(TESTS if arm == "v2" else TESTS[:1], arm))
    (tmp_path / "issue.txt").write_text("Candidate issue")
    return task


@pytest.mark.parametrize("tests,signal,status", [(None, None, "UNAVAILABLE_SELECTION"),
                                                ([], "NOT_AVAILABLE", "ZERO_SELECTION")])
def test_empty_and_unavailable_never_execute_or_pass(tmp_path, tests, signal, status):
    task = task_ready(tmp_path)
    (tmp_path / "scg.json").write_text(json.dumps(selection(tests)))
    row = h.execute_arm(task, selection(tests), tmp_path, tmp_path / "arm")
    assert row["signal"] == signal and row["execution_status"] == status
    assert row["selected_tests"] == tests and not row["calls"]


def test_union_fidelity_contains_scg_only_and_missing_files(tmp_path):
    task, archive, _ = task_and_archive(tmp_path)
    selected = {"v2": selection([]), "scg": selection([TESTS[0], "tests/test_missing.py::test_x"])}
    union = h.source_union(task, selected, archive)
    assert union["tests/test_api.py"] is not None
    assert union["tests/test_missing.py"] is None
    assert union["api.py"] == task["base_source_sha256"]["api.py"]


@pytest.mark.parametrize("bad", ["archive", "commit", "source"])
def test_union_refuses_fidelity_drift(tmp_path, bad):
    task, archive, _ = task_and_archive(tmp_path)
    task[{"archive": "base_archive_sha256", "commit": "base_commit"}.get(bad, "base_commit")] = "wrong"
    if bad == "source":
        task["base_commit"] = "base"
        task["base_source_sha256"]["api.py"] = "wrong"
    with pytest.raises(ValueError):
        h.source_union(task, {"v2": selection(TESTS), "scg": selection(TESTS)}, archive)


def raw_run(tests, statuses, *, timed_out=False):
    results = tuple(TestResult(t, TestStatus(status)) for t, status in zip(tests, statuses))
    return RunResult(results=results, raw_results=results, raw_id_map={t: (t,) for t in tests},
                     evidence_complete=True, requested_tests=tuple(tests), timed_out=timed_out)


@pytest.mark.parametrize("arm", h.ARMS)
@pytest.mark.parametrize("scenario,signal", [("pass", "PASS"), ("regression", "FAIL"),
    ("flaky", "PASS"), ("missing", "INCOMPLETE"), ("timeout", "NOT_AVAILABLE"),
    ("baseline", "BASELINE_UNRELIABLE"), ("bad_evidence", None)])
def test_shared_executor_budgets_ids_policy_and_isolation(tmp_path, monkeypatch, arm, scenario, signal):
    task = task_ready(tmp_path)
    # Historical null must not cause a skip when Ubuntu has the exact frozen tag.
    assert task["image_id"] is None
    observed = {"availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None}
    task["image_binding"] = h.images.binding_record(task, observed)
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: observed)
    selected = selection(TESTS, arm)
    (tmp_path / (arm + ".json")).write_text(json.dumps(selected))
    instances, requests, fidelity = [], [], []

    class Container:
        def __init__(self, iid, patch, **kwargs):
            self.name = f"isolated-{len(instances)}"
            self.image = kwargs["image"]
            assert self.image == LOCAL_ID
            instances.append(self)
        def start(self):
            pass
        def stop(self):
            self.stopped = True

    class Executor:
        def __init__(self, container, runner, evidence_dir):
            self.container = container
            assert runner == TestRunner(**task["runner"])
            assert evidence_dir == tmp_path / arm / "raw"
        def run(self, tests, *, patched, timeout_s):
            requests.append((tests, patched, timeout_s))
            statuses = ["passed"] * len(tests)
            if scenario == "baseline":
                statuses = ["failed"] * len(tests)
            elif scenario == "timeout":
                statuses = ["timeout"] * len(tests)
            elif patched and scenario == "missing":
                statuses[-1] = "not_run"
            elif patched and scenario in ("regression", "flaky") and (len(requests) == 2 or scenario == "regression"):
                statuses[0] = "failed"
            run = raw_run(tests, statuses, timed_out=scenario == "timeout")
            if scenario == "bad_evidence":
                path = tmp_path / arm / "tampered.raw"
                path.write_text("tampered")
                run = replace(run, evidence_files={"stdout": str(path)}, evidence_sha256={"stdout": "wrong"})
            return run

    monkeypatch.setattr(h.v2, "LocalOnlyContainer", Container)
    monkeypatch.setattr(h.v2, "ContainerTestExecutor", Executor)
    monkeypatch.setattr(h.v2.subprocess, "run", lambda *a, **k: type("Inspect", (), {
        "returncode": 0, "stdout": LOCAL_ID + "\n"})())
    monkeypatch.setattr(h.v2, "preflight", lambda c, t: fidelity.append(t["base_source_sha256"]) or {})
    monkeypatch.setattr(h.v2, "resource_snapshot", lambda c: {})
    monkeypatch.setattr(h.v2, "shadow_from_report", lambda *a, **k: {})
    row = h.execute_arm(task, selected, tmp_path, tmp_path / arm)
    assert row["signal"] == signal, row
    assert requests[0] == (tuple(TESTS), False, 300)
    if scenario != "baseline":
        assert requests[1] == (tuple(TESTS), True, 300)
    else:
        assert len(requests) == 1 and row["completeness"] != "COMPLETE"
    if scenario in ("regression", "flaky"):
        assert requests[2] == ((TESTS[0],), True, 300)
    assert instances[0].stopped and fidelity == [task["base_source_sha256"]]
    assert row["execution_status"] == ("EXECUTION_ERROR" if scenario == "bad_evidence" else "EXECUTED")


def test_two_arms_have_independent_container_and_evidence_folders(tmp_path, monkeypatch):
    task = task_ready(tmp_path)
    calls = []
    def execute(adapted, frozen, folder):
        calls.append((adapted, folder))
        return {}
    monkeypatch.setattr(h.v2, "execute_one", execute)
    for arm in h.ARMS:
        selected = json.loads((tmp_path / (arm + ".json")).read_text())
        h.execute_arm(task, selected, tmp_path, tmp_path / arm)
    assert calls[0][0] is not calls[1][0]
    assert calls[0][0]["base_source_sha256"] == calls[1][0]["base_source_sha256"]
    assert calls[0][0]["test_manifest"] != calls[1][0]["test_manifest"]
    assert calls[0][1] != calls[1][1]
    assert RegressionConfig().baseline_cache_dir is None
    first = h.v2.LocalOnlyContainer(IID, PATCH, image="sha256:pinned")
    second = h.v2.LocalOnlyContainer(IID, PATCH, image="sha256:pinned")
    assert first.name != second.name
    assert first.run_args()[1:3] == ["run", "--pull=never"]
    assert first.run_args() == [first.name if x == second.name else x for x in second.run_args()]


def test_missing_environment_never_publishes_pass(tmp_path):
    task = task_ready(tmp_path)
    task["image_id"] = None
    row = h.execute_arm(task, selection(TESTS, "v2"), tmp_path, tmp_path / "missing")
    assert row["execution_status"] == "UNAVAILABLE_ENVIRONMENT" and row["signal"] is None


def test_confirmation_costs_and_missing_phase_are_explicit():
    calls = [{"patched": p, "wall_s": wall} for p, wall in [(False, 10), (True, 20), (True, 4), (False, 3)]]
    costs = h.phase_costs({"calls": calls, "initial_calls": 3, "wall_s": 40}, selection(TESTS))
    assert costs["base_wall_s"] == 10 and costs["patched_wall_s"] == 20
    assert costs["confirmation_wall_s"] == 7 and costs["total_wall_s"] == 44
    costs = h.phase_costs({"calls": calls[:1], "initial_calls": 1, "wall_s": 12}, selection(TESTS))
    assert costs["patched_wall_s"] is None and costs["confirmation_wall_s"] == 0


def pair(signal, completeness="COMPLETE", execution_status="EXECUTED"):
    arms = {}
    for arm in h.ARMS:
        selected = selection(TESTS, arm)
        row = {**h.empty_row({"instance_id": "a", "patch_sha256": "hash"}, selected),
               "signal": signal, "completeness": completeness, "execution_status": execution_status,
               "selection": selected}
        row["costs"] = h.phase_costs(row, selected)
        arms[arm] = row
    return {"instance_id": "a", "arms": arms}


def test_abstentions_metrics_and_null_costs():
    p = pair("INCOMPLETE", "INCOMPLETE_CONFIRMED")
    p["arms"]["scg"]["selection"]["graph_status"] = "partial"
    p["arms"]["v2"]["costs"]["selection_s"] = None
    result = h.aggregate([p])
    assert result["both_completed"] == 0
    assert result["arms"]["scg"]["abstentions"] == 1
    assert result["arms"]["scg"]["graph_status"] == {"partial": 1}
    assert result["arms"]["v2"]["costs"]["selection_s"] == {"sum": None, "measured_tasks": 0}
    with pytest.raises(AssertionError):
        h.aggregate([pair("PASS", "UNVERIFIABLE")])


def test_posthoc_labels_bound_to_patch_and_never_read_early(tmp_path):
    with pytest.raises(AssertionError, match="candidate mismatch"):
        h.aggregate([pair("FAIL")], {"a": {"patch_sha256": "wrong", "correctness": "wrong"}})
    h.write_json(tmp_path / "collection_complete.json", {"tasks_accounted": 2, "scope": ["a", "b"]})
    h.write_json(tmp_path / "results.json", [pair("PASS")])
    with pytest.raises(ValueError, match="incomplete"):
        h.summarize(tmp_path, tmp_path / "summary.json", tmp_path / "never-open-labels.json")


def test_run_requires_review_hash_before_any_output(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    plan.write_text('{}\n')
    monkeypatch.setattr(h, "validate", lambda *a: pytest.fail("approval must be first"))
    with pytest.raises(ValueError, match="reviewed protocol"):
        h.run(tmp_path, plan, tmp_path / "output", "unapproved")
    assert not (tmp_path / "output").exists()


def test_plan_scope_order_and_no_default_execution(tmp_path, monkeypatch):
    tasks = [{"instance_id": "a"}, {"instance_id": "b"}, {"instance_id": "c"}]
    monkeypatch.setattr(h, "validate", lambda *a: ({}, tasks))
    (tmp_path / "protocol.json").write_text('{}')
    h.make_plan(tmp_path, ["b", "a"], tmp_path / "plan.json")
    plan = json.loads((tmp_path / "plan.json").read_text())
    assert plan["schedule"] == [{"instance_id": "a", "arms": ["v2", "scg"]},
                                 {"instance_id": "b", "arms": ["scg", "v2"]}]
    for ids in ([], ["a", "a"], ["unknown"]):
        with pytest.raises(ValueError):
            h.make_plan(tmp_path, ids, tmp_path / "bad.json")


def test_new_output_only(tmp_path):
    target = tmp_path / "historical.json"
    target.write_text("preserve")
    with pytest.raises(FileExistsError):
        h.write_json(target, {})
    assert target.read_text() == "preserve"


def test_frozen_configuration_defaults_are_unchanged():
    assert asdict(RegressionConfig()) == {"baseline_cache_dir": None, "per_pass_timeout_s": 300,
        "per_instance_timeout_s": 600, "rerun_flaky": True}
    assert s.CONFIGURATION == {"strategy": "B", "depth": 3, "budget": "ALL",
                               "edge_variant": "PRIMARY_RESOLVED_ONLY"}
    assert SelectionConfig().max_tier == 2


@pytest.fixture
def dry_frozen(tmp_path, monkeypatch, request):
    """Exercise real 83-cohort freezing with deliberately unavailable test inputs.

    This is a synthetic dry run, not a real SCG experiment or a performance result.
    No real task selectors or tests run in this fixture.
    """
    def synthetic_worker(task, patch, archive, expected, arm, snapshot, folder):
        result = selection(expected if arm == "v2" else None, arm)
        result["selection_status"] = "SYNTHETIC_DRY_RUN" if arm == "v2" else "UNAVAILABLE_BASE_ARCHIVE"
        return result
    monkeypatch.setattr(h, "worker", synthetic_worker)
    if getattr(request, "param", None) == "host-images":
        monkeypatch.setattr(h.images, "inspect_image", lambda tag: {
            "availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None})
    frozen = tmp_path / "frozen"
    binding_path = tmp_path / "bindings.json"
    h.bind_images(h.V2_FROZEN, binding_path)
    h.prepare(h.V2_FROZEN, tmp_path / "intentionally-missing-archives", frozen, binding_path)
    return frozen


def test_all_83_have_one_manifest_per_arm_and_original_identity(dry_frozen):
    protocol, tasks = h.validate(dry_frozen)
    originals = json.loads((h.V2_FROZEN / "tasks.json").read_text())
    assert len(tasks) == 83 and protocol["launch_status"] == "PREPARED_FOR_REVIEW_NOT_AUTHORIZED"
    for task, original in zip(tasks, originals):
        assert task["instance_id"] == original["instance_id"]
        for key in ("base_commit", "image_id", "image_tag", "runner", "patch_sha256"):
            assert task[key] == original[key]
        assert len(task["selections"]) == 2
        v2 = json.loads((dry_frozen / task["selections"]["v2"]).read_text())
        scg = json.loads((dry_frozen / task["selections"]["scg"]).read_text())
        assert v2["tests"] == h.copied_v2_selection(h.V2_FROZEN, original)
        assert scg["tests"] is None


@pytest.mark.parametrize("target", ["selection", "source", "protocol", "snapshot", "image_binding"])
def test_seal_catches_all_input_classes(dry_frozen, target):
    _, tasks = h.validate(dry_frozen)
    paths = {"selection": dry_frozen / tasks[0]["selections"]["scg"],
             "source": dry_frozen / "tasks.json", "protocol": dry_frozen / "protocol.json",
             "snapshot": dry_frozen / "scg_source" / s.SCG_FILES[0],
             "image_binding": dry_frozen / "image_bindings.json"}
    with paths[target].open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="drift"):
        h.validate(dry_frozen)


def test_resealed_selection_cannot_bypass_protocol_bound_inputs(dry_frozen):
    _, tasks = h.validate(dry_frozen)
    target = dry_frozen / tasks[0]["selections"]["scg"]
    target.write_text(json.dumps(selection(TESTS)))
    seals = json.loads((dry_frozen / "artifact_hashes.json").read_text())
    seals[str(target.relative_to(dry_frozen))] = s.digest(target)
    (dry_frozen / "artifact_hashes.json").write_text(json.dumps(seals))
    with pytest.raises(ValueError, match="protocol-bound input drift"):
        h.validate(dry_frozen)


def test_source_drift_detected_without_container(dry_frozen, monkeypatch):
    monkeypatch.setattr(h, "source_hashes", lambda: {"changed": "changed"})
    with pytest.raises(ValueError, match="source/config drift"):
        h.validate(dry_frozen)


def test_end_to_end_scoped_dry_run_accounts_for_both_abstentions(dry_frozen, tmp_path):
    _, tasks = h.validate(dry_frozen)
    iid = tasks[0]["instance_id"]
    plan, out = tmp_path / "plan.json", tmp_path / "dry_results"
    h.make_plan(dry_frozen, [iid], plan)
    h.run(dry_frozen, plan, out, s.digest(plan))
    pairs = json.loads((out / "results.json").read_text())
    assert len(pairs) == 1 and set(pairs[0]["arms"]) == set(h.ARMS)
    assert all(r["signal"] is None for r in pairs[0]["arms"].values())
    summary = json.loads((out / "metrics.json").read_text())
    assert summary["both_completed"] == 0
    assert all(arm["abstentions"] == 1 for arm in summary["arms"].values())
    assert json.loads((out / "collection_complete.json").read_text())["scope"] == [iid]
    assert json.loads((out / "run_provenance.json").read_text())["image_bindings_sha256"] == s.digest(dry_frozen / "image_bindings.json")
    h.summarize(out, tmp_path / "posthoc.json")
    with pytest.raises(FileExistsError):
        h.run(dry_frozen, plan, out, s.digest(plan))


def test_selection_missing_base_is_explicit(tmp_path):
    result = s.select({"task": {}, "archive": str(tmp_path / "missing")}, "scg")
    assert result["tests"] is None and result["selection_status"] == "UNAVAILABLE_BASE_ARCHIVE"


def test_scg_zero_reachability_preserved(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    # Recreate the same base with a named function that has no test callers.
    with tarfile.open(archive) as original:
        blobs = {m.name: original.extractfile(m).read() for m in original if m.isfile()}
    blobs["testbed/tests/test_api.py"] = b"def test_other():\n    assert True\n"
    with tarfile.open(archive, "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": "base"}) as stream:
        for name, payload in blobs.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            stream.addfile(member, io.BytesIO(payload))
    task["base_archive_sha256"] = s.digest(archive)
    row = h.worker(task, patch, archive, TESTS, "scg", scg_snapshot, tmp_path)
    assert row["tests"] == [] and row["selection_status"] == "ZERO_SELECTION"
    assert row["resolved_seeds"]


def test_worker_error_is_explicit_not_a_v2_fallback(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    task["base_archive_sha256"] = "wrong"
    result = h.worker(task, patch, archive, TESTS, "scg", scg_snapshot, tmp_path)
    assert result["tests"] is None and result["selection_status"] == "SELECTION_ERROR"
    assert "hash mismatch" in result["reason"]


def test_scg_partial_graph_remains_explicit(tmp_path, scg_snapshot):
    task, archive, patch = task_and_archive(tmp_path)
    with tarfile.open(archive) as original:
        blobs = {m.name: original.extractfile(m).read() for m in original if m.isfile()}
    blobs["testbed/invalid.py"] = b"def invalid syntax\n"
    with tarfile.open(archive, "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": "base"}) as stream:
        for name, payload in blobs.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            stream.addfile(member, io.BytesIO(payload))
    task["base_archive_sha256"] = s.digest(archive)
    row = h.worker(task, patch, archive, TESTS, "scg", scg_snapshot, tmp_path)
    assert row["tests"] == [TESTS[0]] and row["graph_status"] == "partial"
    assert row["graph_failures"][0]["reason"] == "SyntaxError"


def test_resource_limited_graph_has_no_selection_fallback(tmp_path, scg_snapshot, monkeypatch):
    task, archive, patch = task_and_archive(tmp_path)
    class LimitedGraph:
        def __init__(self):
            self.status = "resource_limited"
            self.failures = [{"reason": "fixed_resource_limit", "limit": "seconds"}]
            self.files, self.counts = {}, {}
        def build(self, root):
            return self
    graph_types = SimpleNamespace(TypeGraph=LimitedGraph, TypeAmendedGraph=LimitedGraph)
    builders = SimpleNamespace(extract=lambda *a: (task["base_archive_sha256"], []))
    monkeypatch.setattr(s, "load_scg", lambda *a: (graph_types, None, None, None, builders))
    monkeypatch.setattr(s, "select_tests", lambda *a: pytest.fail("No V2 fallback is allowed"))
    row = s.select({"task": task, "archive": str(archive), "patch": str(patch)}, "scg", scg_snapshot)
    assert row["tests"] is None and row["graph_status"] == "resource_limited"
    assert row["selection_status"] == "UNAVAILABLE_RESOURCE_LIMITED_GRAPH"
    assert row["graph_build_s"] is not None and row["selection_s"] is None


def test_host_drift_blocks_launch_after_freeze(dry_frozen, monkeypatch):
    inventory = h.v2.host_packages()
    inventory["platform"] = "different Ubuntu host"
    monkeypatch.setattr(h.v2, "host_packages", lambda: inventory)
    with pytest.raises(ValueError, match="host interpreter/package/platform drift"):
        h.validate(dry_frozen)


def test_archived_v2_inputs_are_portable_without_changing_frozen_policy(monkeypatch):
    monkeypatch.setattr(h.v2, "host_packages", lambda: pytest.fail("Historical host equality is not input integrity"))
    protocol, tasks, _ = h.verify_v2_inputs(h.V2_FROZEN)
    assert len(tasks) == 83 and protocol["regression_config"] == asdict(RegressionConfig())


def test_unavailable_witness_selection_remains_unknown():
    p = pair(None, None, "UNAVAILABLE_SELECTION")
    p["arms"]["scg"]["selected_tests"] = None
    p["arms"]["scg"]["selected"] = None
    p["arms"]["scg"]["selection"]["tests"] = None
    result = h.aggregate([p], witnesses={"a": {"patch_sha256": "hash", "test_ids": [TESTS[0]]}})
    observations = result["arms"]["scg"]["historical_witness_observations"]
    assert observations[0]["selected"] is None
    metrics = result["arms"]["scg"]["historical_witness_metrics"]
    assert metrics["selection_unknown"] == 1 and metrics["confirmed"] == 0


def test_resource_metrics_preserve_missing_and_v1_cpu():
    p = pair("PASS")
    p["arms"]["scg"]["resources"] = {"/sys/fs/cgroup/cpuacct/cpuacct.usage": "2000000000",
        "/sys/fs/cgroup/memory/memory.max_usage_in_bytes": "1024"}
    result = h.aggregate([p])
    assert result["arms"]["scg"]["resource_metrics"] == {
        "container_cpu_s_sum": 2, "cpu_measured_tasks": 1,
        "container_peak_memory_bytes_max": 1024, "memory_measured_tasks": 1}
    assert result["arms"]["v2"]["resource_metrics"]["container_cpu_s_sum"] is None


def test_unsealed_execution_selection_is_refused(tmp_path):
    task = task_ready(tmp_path)
    with pytest.raises(ValueError, match="IDs differ"):
        h.execute_arm(task, selection(["changed_selection"]), tmp_path, tmp_path / "must-not-exist")
    assert not (tmp_path / "must-not-exist").exists()


def test_binding_inventory_has_all_83_historical_records_unchanged(dry_frozen):
    originals = json.loads((h.V2_FROZEN / "tasks.json").read_text())
    bindings = json.loads((dry_frozen / "image_bindings.json").read_text())
    assert len(bindings["rows"]) == 83
    assert sum(r["historical_image_id"] is None for r in bindings["rows"]) == 44
    assert sum(r["historical_image_id"] is not None for r in bindings["rows"]) == 39
    for original, binding in zip(originals, bindings["rows"]):
        assert original["image_id"] == binding["historical_image_id"]
        assert binding["host_image_id"] is None and binding["availability"] == "MISSING"
    for source in h.V2_FROZEN.rglob("*"):
        if source.is_file():
            assert source.read_bytes() == (dry_frozen / "v2" / source.relative_to(h.V2_FROZEN)).read_bytes()


def test_validation_detects_image_drift_before_plan_creation(dry_frozen, tmp_path, monkeypatch):
    _, tasks = h.validate(dry_frozen)
    iid = tasks[0]["instance_id"]
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: {
        "availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None})
    with pytest.raises(h.images.ImageBindingError, match="Host image drift"):
        h.make_plan(dry_frozen, [iid], tmp_path / "must-not-exist.json")
    assert not (tmp_path / "must-not-exist.json").exists()


def test_validation_detects_docker_daemon_drift(dry_frozen, monkeypatch):
    monkeypatch.setattr(h.images, "daemon_id", lambda: "another-daemon")
    with pytest.raises(ValueError, match="Docker daemon binding drift"):
        h.validate(dry_frozen)


def test_resealed_binding_still_bound_to_protocol(dry_frozen):
    target = dry_frozen / "image_bindings.json"
    with target.open("a") as stream:
        stream.write(" ")
    seals = json.loads((dry_frozen / "artifact_hashes.json").read_text())
    seals["image_bindings.json"] = s.digest(target)
    (dry_frozen / "artifact_hashes.json").write_text(json.dumps(seals))
    with pytest.raises(ValueError, match="protocol-bound input drift"):
        h.validate(dry_frozen)


def test_each_arm_rechecks_binding_before_executor(tmp_path, monkeypatch):
    task = task_ready(tmp_path)
    observed = {"availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None}
    task["image_binding"] = h.images.binding_record(task, observed)
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: observed)
    calls = []
    monkeypatch.setattr(h.v2, "execute_one", lambda adapted, *a: calls.append(adapted["image_id"]) or {})
    h.execute_arm(task, selection(TESTS, "v2"), tmp_path, tmp_path / "v2")
    observed = dict(observed, host_image_id="sha256:" + "b" * 64)
    with pytest.raises(h.images.ImageBindingError, match="Host image drift"):
        h.execute_arm(task, selection(TESTS[:1], "scg"), tmp_path, tmp_path / "scg")
    assert calls == [LOCAL_ID] and not (tmp_path / "scg").exists()


@pytest.mark.parametrize("arm", h.ARMS)
def test_available_bound_image_still_requires_source_fidelity(tmp_path, monkeypatch, arm):
    task = task_ready(tmp_path)
    observed = {"availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None}
    task["image_binding"] = h.images.binding_record(task, observed)
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: observed)
    class Container:
        def __init__(self, *args, **kwargs):
            assert kwargs["image"] == LOCAL_ID
        def start(self):
            pass
        def stop(self):
            pass
    def mismatch(container, adapted):
        assert adapted["base_source_sha256"] == task["base_source_sha256"]
        raise h.v2.EnvironmentMismatch("synthetic archive/source mismatch")
    monkeypatch.setattr(h.v2, "LocalOnlyContainer", Container)
    monkeypatch.setattr(h.v2, "preflight", mismatch)
    monkeypatch.setattr(h.v2, "ContainerTestExecutor", lambda *a, **k: pytest.fail("Source mismatch must precede tests"))
    monkeypatch.setattr(h.v2.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=LOCAL_ID))
    selected = json.loads((tmp_path / (arm + ".json")).read_text())
    row = h.execute_arm(task, selected, tmp_path, tmp_path / arm)
    assert row["execution_status"] == "ENVIRONMENT_MISMATCH" and row["signal"] is None


@pytest.mark.parametrize("dry_frozen", ["host-images"], indirect=True)
def test_new_freeze_binds_host_images_for_all_83_without_rewriting_history(dry_frozen):
    _, tasks = h.validate(dry_frozen)
    assert sum(t["image_id"] is None for t in tasks) == 44
    assert all(t["image_binding"]["host_image_id"] == LOCAL_ID for t in tasks)
    assert all(t["image_binding"]["historical_image_id"] == t["image_id"] for t in tasks)
    assert all(t["image_binding"]["source_fidelity"] == "NOT_VERIFIED" for t in tasks)


@pytest.mark.parametrize("historical", [None, LOCAL_ID, "sha256:" + "b" * 64])
def test_both_arms_receive_same_host_id_with_history_intact(tmp_path, monkeypatch, historical):
    task = task_ready(tmp_path)
    task["image_id"] = historical
    observed = {"availability": "AVAILABLE", "host_image_id": LOCAL_ID, "repo_digests": [], "reason": None}
    task["image_binding"] = h.images.binding_record(task, observed)
    monkeypatch.setattr(h.images, "inspect_image", lambda tag: observed)
    calls = []
    monkeypatch.setattr(h.v2, "execute_one", lambda adapted, *a: calls.append(adapted) or {})
    for arm in h.ARMS:
        selected = json.loads((tmp_path / (arm + ".json")).read_text())
        h.execute_arm(task, selected, tmp_path, tmp_path / arm)
    assert [c["image_id"] for c in calls] == [LOCAL_ID, LOCAL_ID]
    assert task["image_id"] == historical
    assert calls[0]["base_source_sha256"] == calls[1]["base_source_sha256"] == task["base_source_sha256"]


def test_image_inspection_error_blocks_preparation(dry_frozen, tmp_path, monkeypatch):
    bindings = json.loads((dry_frozen / "image_bindings.json").read_text())
    bindings["ready"] = False
    target = tmp_path / "unverified.json"
    h.write_json(target, bindings)
    monkeypatch.setattr(h, "worker", lambda *a: pytest.fail("Unverified images must block before selection"))
    with pytest.raises(ValueError, match="image inspection errors"):
        h.prepare(h.V2_FROZEN, tmp_path, tmp_path / "must-not-exist", target)
    assert not (tmp_path / "must-not-exist").exists()


def test_image_binding_cannot_change_task_cohort(dry_frozen):
    bindings = json.loads((dry_frozen / "image_bindings.json").read_text())
    bindings["rows"].pop()
    _, originals, _ = h.verify_v2_inputs(h.V2_FROZEN)
    with pytest.raises(ValueError, match="cohort mismatch"):
        h.verify_image_bindings(bindings, originals)


@pytest.mark.parametrize("arm", h.ARMS)
def test_missing_bound_tag_never_falls_back_to_historical_id(tmp_path, monkeypatch, arm):
    task = task_ready(tmp_path)
    task["image_id"] = LOCAL_ID
    task["image_binding"] = h.images.binding_record(task, h.images.inspect_image(task["image_tag"]))
    monkeypatch.setattr(h.v2, "LocalOnlyContainer", lambda *a, **k: pytest.fail("No historical ID fallback"))
    selected = json.loads((tmp_path / (arm + ".json")).read_text())
    row = h.execute_arm(task, selected, tmp_path, tmp_path / arm)
    assert row["execution_status"] == "UNAVAILABLE_ENVIRONMENT" and row["signal"] is None
    assert task["image_id"] == LOCAL_ID
