"""Host image inventory and drift checks. Docker commands are always mocked."""
import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
images = importlib.import_module("v2_scg_images")
NEW_ID, OLD_ID = ("sha256:" + c * 64 for c in ("a", "b"))
TAG = "swebench/frozen:exact"


def task(historical=None):
    return {"instance_id": "task", "image_id": historical, "image_tag": TAG,
            "image_digest": "historical-digest", "environment_status": "historical-status"}


def observed(ident=NEW_ID):
    return {"availability": "AVAILABLE" if ident else "MISSING", "host_image_id": ident,
            "repo_digests": [], "reason": None}


@pytest.mark.parametrize("historical,comparison,mismatch", [
    (None, "HISTORICAL_ID_UNAVAILABLE", None), (NEW_ID, "MATCH", False), (OLD_ID, "DIFFERENT", True)])
def test_host_binding_preserves_historical_null_matching_and_different_ids(monkeypatch, historical, comparison, mismatch):
    original = task(historical)
    before = copy.deepcopy(original)
    monkeypatch.setattr(images, "daemon_id", lambda: "daemon")
    calls = []
    monkeypatch.setattr(images, "inspect_image", lambda tag: calls.append(tag) or observed())
    result = images.capture([original])
    row = result["rows"][0]
    assert original == before and calls == [TAG]
    assert result["ready"] is True and row["host_image_id"] == NEW_ID
    assert row["historical_image_id"] == historical
    assert row["historical_id_comparison"] == comparison and row["historical_id_mismatch"] is mismatch
    assert row["source_fidelity"] == "NOT_VERIFIED"
    images.validate_record(original, row)


def test_inspection_uses_only_exact_tag_and_read_only_commands(monkeypatch):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        assert kwargs["check"] is False and kwargs["timeout"] == 30
        value = "daemon" if args[1] == "info" else {"Id": NEW_ID, "RepoTags": [TAG], "RepoDigests": []}
        return SimpleNamespace(returncode=0, stdout=json.dumps(value), stderr="")
    monkeypatch.setattr(images, "_docker_bin", lambda: "docker")
    monkeypatch.setattr(images.subprocess, "run", run)
    assert images.daemon_id() == "daemon"
    assert images.inspect_image(TAG) == observed()
    assert calls == [["docker", "info", "--format", "{{json .ID}}"],
                     ["docker", "image", "inspect", "--format", "{{json .}}", TAG]]


@pytest.mark.parametrize("error,status", [("Error response from daemon: No such image: " + TAG, "MISSING"),
    ("Cannot connect to the Docker daemon", "INSPECTION_ERROR"), ("permission denied", "INSPECTION_ERROR")])
def test_missing_image_is_distinct_from_docker_errors(monkeypatch, error, status):
    monkeypatch.setattr(images, "docker_read", lambda args: SimpleNamespace(returncode=1, stdout="", stderr=error))
    result = images.inspect_image(TAG)
    assert result["availability"] == status and result["host_image_id"] is None


@pytest.mark.parametrize("payload", ["bad json", json.dumps({"Id": "not-a-full-id", "RepoTags": [TAG]}),
    json.dumps({"Id": NEW_ID, "RepoTags": ["different:tag"]})])
def test_malformed_or_nonmatching_tag_metadata_fails_closed(monkeypatch, payload):
    monkeypatch.setattr(images, "docker_read", lambda args: SimpleNamespace(returncode=0, stdout=payload, stderr=""))
    assert images.inspect_image(TAG)["availability"] == "INSPECTION_ERROR"


@pytest.mark.parametrize("exception", [FileNotFoundError("docker"), subprocess.TimeoutExpired("docker", 30)])
def test_cli_and_timeout_errors_are_unverifiable(monkeypatch, exception):
    def failure(*args):
        raise exception
    monkeypatch.setattr(images, "docker_read", failure)
    assert images.inspect_image(TAG)["availability"] == "INSPECTION_ERROR"
    with pytest.raises(images.ImageBindingError, match="daemon inspection failed"):
        images.daemon_id()


def test_unavailable_daemon_accounts_for_entire_cohort(monkeypatch):
    def failure():
        raise images.ImageBindingError("daemon unavailable")
    monkeypatch.setattr(images, "daemon_id", failure)
    monkeypatch.setattr(images, "inspect_image", lambda *a: pytest.fail("Daemon unavailable"))
    tasks = [dict(task(), instance_id=str(i)) for i in range(83)]
    result = images.capture(tasks)
    assert result["ready"] is False and len(result["rows"]) == 83
    assert all(r["availability"] == "INSPECTION_ERROR" for r in result["rows"])


@pytest.mark.parametrize("frozen_id,current_id", [(NEW_ID, OLD_ID), (NEW_ID, None), (None, NEW_ID)])
def test_retag_removal_or_newly_present_missing_image_is_drift(monkeypatch, frozen_id, current_id):
    original = task(OLD_ID)
    binding = images.binding_record(original, observed(frozen_id))
    monkeypatch.setattr(images, "inspect_image", lambda tag: observed(current_id))
    with pytest.raises(images.ImageBindingError, match="Host image drift"):
        images.verify_current(original, binding)


@pytest.mark.parametrize("ident", [NEW_ID, None])
def test_unchanged_available_or_missing_binding_validates(monkeypatch, ident):
    original = task()
    binding = images.binding_record(original, observed(ident))
    monkeypatch.setattr(images, "inspect_image", lambda tag: observed(ident))
    images.verify_current(original, binding)


def test_tampered_historical_metadata_refused():
    original = task()
    binding = images.binding_record(original, observed())
    binding["historical_image_id"] = OLD_ID
    with pytest.raises(images.ImageBindingError, match="historical metadata"):
        images.validate_record(original, binding)
