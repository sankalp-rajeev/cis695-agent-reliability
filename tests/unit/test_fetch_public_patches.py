"""The downloader must reject every key outside the exact prediction path."""

import json
from subprocess import CompletedProcess

import pytest
from scripts import fetch_public_patches

PREFIX = "s3://swe-bench-submissions/bash-only/example/trajs"
INSTANCE_ID = "django__django-1234"
PREDICTION = f"{PREFIX}/{INSTANCE_ID}/{INSTANCE_ID}.pred"


def test_allow_exact_prediction_key():
    fetch_public_patches.validate_pred_key(PREFIX, INSTANCE_ID, PREDICTION)


@pytest.mark.parametrize(
    "key",
    [
        PREDICTION.replace("/trajs/", "/logs/"),
        PREDICTION.replace("/trajs/", "/results/"),
        f"{PREFIX}/{INSTANCE_ID}/per_instance_details.json",
        f"{PREFIX}/{INSTANCE_ID}/git_peek_suspicious_commits.md",
        f"{PREFIX}/{INSTANCE_ID}/other__repo-1.pred",
        f"{PREFIX}/other__repo-1/{INSTANCE_ID}.pred",
        f"{PREFIX}/{INSTANCE_ID}/../{INSTANCE_ID}.pred",
        f"{PREDICTION}\n",
    ],
)
def test_reject_non_prediction_keys_before_aws_call(key, monkeypatch):
    def unexpected_aws_call(*args, **kwargs):
        pytest.fail("An invalid S3 key reached the AWS CLI")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", unexpected_aws_call)
    with pytest.raises(ValueError, match="specified instance's .pred"):
        fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, key)


def test_reject_logs_as_the_configured_prefix():
    prefix = PREFIX.replace("/trajs", "/logs")
    key = f"{prefix}/{INSTANCE_ID}/{INSTANCE_ID}.pred"
    with pytest.raises(ValueError, match="Invalid trajectory prefix"):
        fetch_public_patches.validate_pred_key(prefix, INSTANCE_ID, key)


def test_preserve_prediction_patch_string(monkeypatch):
    patch = "first line\r\nsecond line\n\n"
    raw = json.dumps({"instance_id": INSTANCE_ID, "model_patch": patch}).encode()

    def aws_call(args, **kwargs):
        assert args[:6] == ["aws", "s3", "cp", PREDICTION, "-", "--no-sign-request"]
        return CompletedProcess(args, 0, raw, b"")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", aws_call)
    assert fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, PREDICTION) == (
        patch,
        fetch_public_patches.sha256(raw),
    )


def test_missing_prediction_has_no_empty_flag(monkeypatch):
    error = b"fatal error: An error occurred (404) when calling the HeadObject operation"

    def aws_call(args, **kwargs):
        return CompletedProcess(args, 1, b"", error)

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", aws_call)
    assert fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, PREDICTION) == {
        "instance_id": INSTANCE_ID,
        "s3_key": PREDICTION,
        "missing": True,
        "error": error.decode(),
    }


@pytest.mark.parametrize(("patch", "reason"), [(" \r\n\t", "blank"), (None, "null")])
def test_blank_and_null_write_read_only_zero_byte_files(patch, reason, tmp_path, monkeypatch):
    raw = json.dumps({"instance_id": INSTANCE_ID, "model_patch": patch}).encode()

    def aws_call(args, **kwargs):
        return CompletedProcess(args, 0, raw, b"")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", aws_call)
    monkeypatch.setattr(fetch_public_patches, "ROOT", tmp_path)
    (tmp_path / fetch_public_patches.PATCHES / "example").mkdir(parents=True)

    fetched_patch, pred_sha = fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, PREDICTION)
    record = fetch_public_patches.store_patch(
        "example", INSTANCE_ID, fetched_patch, s3_key=PREDICTION, pred_sha256=pred_sha
    )
    path = tmp_path / record["patch_path"]
    assert path.read_bytes() == b""
    assert path.stat().st_mode & 0o222 == 0
    assert record["patch_sha256"] == fetch_public_patches.sha256(b"")
    assert record["empty"] is True
    assert record["empty_reason"] == reason


@pytest.mark.parametrize(
    ("fields", "patch_type"),
    [
        ({}, "absent"),
        ({"model_patch": 3}, "int"),
        ({"model_patch": []}, "list"),
        ({"model_patch": {}}, "dict"),
        ({"model_patch": True}, "bool"),
    ],
)
def test_malformed_prediction_is_neither_missing_nor_empty(fields, patch_type, monkeypatch):
    raw = json.dumps({"instance_id": INSTANCE_ID, **fields}).encode()

    def aws_call(args, **kwargs):
        return CompletedProcess(args, 0, raw, b"")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", aws_call)
    assert fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, PREDICTION) == {
        "instance_id": INSTANCE_ID,
        "s3_key": PREDICTION,
        "pred_sha256": fetch_public_patches.sha256(raw),
        "malformed": True,
        "model_patch_type": patch_type,
    }


def test_fetch_stops_after_combined_gate_breach(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_public_patches, "ROOT", tmp_path)
    calls = []

    def unavailable(prefix, instance_id, key):
        calls.append(instance_id)
        outcome = "missing" if len(calls) % 2 else "malformed"
        return {"instance_id": instance_id, "s3_key": key, outcome: True}

    monkeypatch.setattr(fetch_public_patches, "fetch_pred", unavailable)
    system = {"folder": "example", "trajs_prefix": PREFIX}
    ids = [f"django__django-{number}" for number in range(1, 223)]
    with pytest.raises(SystemExit, match="6 development issues"):
        fetch_public_patches.fetch_public(system, ids)

    assert calls == ids[:6]
    manifest = tmp_path / fetch_public_patches.PATCHES / "example/tasks.json"
    assert [record["instance_id"] for record in json.loads(manifest.read_text())["tasks"]] == calls


def test_gate_checks_test_set_and_excludes_reserves():
    tasks = [{}] * 195 + [{"malformed": True}] * 27
    fetch_public_patches.check_gate("example", tasks)
    tasks[194] = {"missing": True}
    with pytest.raises(SystemExit, match="6 test issues"):
        fetch_public_patches.check_gate("example", tasks)
