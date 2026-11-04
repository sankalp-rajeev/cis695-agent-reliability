"""Freeze/approval and post-hoc accounting checks; never invokes Docker."""
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from reliability.verifier.regression import RegressionConfig
from reliability.verifier.selection import SelectionConfig

SPEC = importlib.util.spec_from_file_location(
    "v2_evaluation", Path(__file__).resolve().parents[2] / "scripts/v2_evaluation.py")
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


def test_runner_rejects_unapproved_execution_before_creating_output(tmp_path):
    frozen = tmp_path / "freeze"
    frozen.mkdir()
    (frozen / "protocol.json").write_text('{}\n')
    out = tmp_path / "must_not_exist"
    with pytest.raises(ValueError, match="reviewed protocol"):
        evaluation.run(frozen, out, "not-approved")
    assert not out.exists()


def test_approval_is_bound_to_protocol_bytes():
    protocol = b'{"budget": 300}\n'
    evaluation.require_approval(protocol, evaluation.sha(protocol))
    with pytest.raises(ValueError):
        evaluation.require_approval(protocol + b" ", evaluation.sha(protocol))


def test_frozen_source_drift_is_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    source = tmp_path / "source.py"
    source.write_text("original\n")
    protocol = {"source_sha256": {"source.py": evaluation.sha(source.read_bytes())},
                "shadow_only": True, "parallelism": 1,
                "selection_config": asdict(SelectionConfig()),
                "regression_config": asdict(RegressionConfig())}
    evaluation.write_json(tmp_path / "tasks.json", [{"instance_id": str(i)} for i in range(83)])
    protocol["task_artifact_sha256"] = {"tasks.json": evaluation.sha((tmp_path / "tasks.json").read_bytes())}
    evaluation.write_json(tmp_path / "protocol.json", protocol)
    evaluation.write_json(tmp_path / "artifact_hashes.json", {
        p.name: evaluation.sha(p.read_bytes()) for p in tmp_path.glob("*.json")})
    assert len(evaluation.verify_frozen(tmp_path)[1]) == 83
    source.write_text("changed\n")
    with pytest.raises(AssertionError, match="source/config drift"):
        evaluation.verify_frozen(tmp_path)


def result(iid, signal, completeness="COMPLETE"):
    return {"instance_id": iid, "signal": signal, "completeness": completeness,
            "execution_status": "EXECUTED", "patch_sha256": iid, "selected": 1}


def test_incomplete_and_unavailable_are_abstentions_in_binary_metrics():
    rows = [result("a", "FAIL"), result("b", "PASS"),
            result("c", "INCOMPLETE", "INCOMPLETE_CONFIRMED"), result("d", None, None)]
    rows[-1]["execution_status"] = "UNAVAILABLE_ENVIRONMENT"
    labels = {iid: {"patch_sha256": iid, "correctness": correctness}
              for iid, correctness in [("a", "wrong"), ("b", "right"), ("c", "wrong"), ("d", "wrong")]}
    m = evaluation.metrics(rows, labels)["correctness_metrics"]
    assert m["precision"] == m["recall_binary"] == m["f1_binary"] == 1
    assert m["recall_all_labeled"] == pytest.approx(1 / 3)
    assert m["binary_coverage"] == 0.5


def test_undefined_metrics_remain_null():
    row = result("x", "INCOMPLETE", "UNVERIFIABLE")
    m = evaluation.metrics([row], {"x": {"patch_sha256": "x", "correctness": "right"}})
    assert m["correctness_metrics"]["precision"] is None
    assert m["correctness_metrics"]["recall_binary"] is None


def test_metric_labels_must_match_candidate_hash():
    with pytest.raises(AssertionError, match="candidate mismatch"):
        evaluation.metrics([result("x", "FAIL")],
                           {"x": {"patch_sha256": "different", "correctness": "wrong"}})


def test_incomplete_pass_is_never_accepted_by_accounting():
    with pytest.raises(AssertionError):
        evaluation.metrics([result("x", "PASS", "INCOMPLETE_CONFIRMED")])


def test_summary_does_not_open_labels_before_collection_complete(tmp_path):
    (tmp_path / "collection_complete.json").write_text(json.dumps({"tasks_accounted": 3}))
    with pytest.raises(AssertionError, match="before collection"):
        evaluation.summarize(tmp_path, tmp_path / "must_not_be_opened.json")


def test_absent_image_is_accounted_without_starting_a_container(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No container or subprocess should start for a frozen unavailable image")

    monkeypatch.setattr(evaluation.subprocess, "run", forbidden)
    evaluation.write_json(tmp_path / "tests.json", {"tests": ["test_x"]})
    row = evaluation.execute_one({"instance_id": "missing", "patch_sha256": "x",
                                  "selected": 1, "image_id": None, "test_manifest": "tests.json"},
                                 tmp_path, tmp_path / "task")
    assert row["execution_status"] == "UNAVAILABLE_ENVIRONMENT"
    assert row["signal"] is None
    assert row["selected_tests"] == ["test_x"]
    assert (tmp_path / "task/result.json").exists()


def test_changed_task_manifest_cannot_reuse_approved_protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    task_path = tmp_path / "tasks.json"
    evaluation.write_json(task_path, [{"instance_id": str(i)} for i in range(83)])
    protocol = {"task_artifact_sha256": {"tasks.json": evaluation.sha(task_path.read_bytes())}}
    evaluation.write_json(tmp_path / "protocol.json", protocol)
    task_path.write_text('[]\n')
    evaluation.write_json(tmp_path / "artifact_hashes.json", {
        p.name: evaluation.sha(p.read_bytes()) for p in tmp_path.glob("*.json")})
    with pytest.raises(AssertionError, match="approved task/input drift"):
        evaluation.verify_frozen(tmp_path)
