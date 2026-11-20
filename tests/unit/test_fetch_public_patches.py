"""The downloader must reject every key outside the exact prediction path."""

import json
from subprocess import CompletedProcess

import pytest
from scripts import fetch_public_patches

PREFIX = "s3://swe-bench-submissions/bash-only/example/trajs"
INSTANCE_ID = "django__django-1234"
PREDICTION = f"{PREFIX}/{INSTANCE_ID}/{INSTANCE_ID}.pred"
TRAJECTORY = f"{PREFIX}/{INSTANCE_ID}/{INSTANCE_ID}.traj.json"


def test_allow_exact_prediction_key():
    fetch_public_patches.validate_pred_key(PREFIX, INSTANCE_ID, PREDICTION)
    fetch_public_patches.validate_pred_key(PREFIX, INSTANCE_ID, TRAJECTORY, "traj_json_v1")


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
    with pytest.raises(ValueError, match="system format"):
        fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, key)


@pytest.mark.parametrize(
    ("key", "format_name"),
    [
        (TRAJECTORY, "pred_v0"),
        (PREDICTION, "traj_json_v1"),
        (TRAJECTORY.replace("/trajs/", "/logs/"), "traj_json_v1"),
    ],
)
def test_reject_keys_outside_each_system_format(key, format_name, monkeypatch):
    def unexpected_aws_call(*args, **kwargs):
        pytest.fail("An invalid S3 key reached the AWS CLI")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", unexpected_aws_call)
    with pytest.raises(ValueError, match="system format"):
        fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, key, format_name)


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
        {"s3_key": PREDICTION, "pred_sha256": fetch_public_patches.sha256(raw)},
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

    fetched_patch, source = fetch_public_patches.fetch_pred(PREFIX, INSTANCE_ID, PREDICTION)
    record = fetch_public_patches.store_patch("example", INSTANCE_ID, fetched_patch, **source)
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


def test_parse_only_trajectory_submission_and_exit_status(monkeypatch):
    raw = json.dumps(
        {
            "messages": [{"content": "discarded"}],
            "info": {"other": ["discarded"], "submission": "patch\n", "exit_status": "Submitted"},
        }
    ).encode()
    monkeypatch.setattr(
        fetch_public_patches, "copy_s3_object", lambda key: CompletedProcess([], 0, raw, b"")
    )
    patch, source = fetch_public_patches.fetch_pred(
        PREFIX, INSTANCE_ID, TRAJECTORY, "traj_json_v1", first_file=True
    )
    assert patch == "patch\n"
    assert source == {
        "s3_key": TRAJECTORY,
        "exit_status": "Submitted",
        "pred_sha256": fetch_public_patches.sha256(raw),
        "submission_sha256": fetch_public_patches.sha256(b"patch\n"),
    }


def test_first_trajectory_missing_submission_reports_only_key_names(monkeypatch):
    raw = b'{"messages":["discard this"],"info":{"exit_status":"discard status"}}'
    monkeypatch.setattr(
        fetch_public_patches, "copy_s3_object", lambda key: CompletedProcess([], 0, raw, b"")
    )
    with pytest.raises(SystemExit) as exc:
        fetch_public_patches.fetch_pred(
            PREFIX, INSTANCE_ID, TRAJECTORY, "traj_json_v1", first_file=True
        )
    assert (
        str(exc.value)
        == f"{INSTANCE_ID}: top-level keys ['messages', 'info']; info keys ['exit_status']"
    )


def test_cross_check_refuses_other_top_level_keys(monkeypatch):
    def unexpected_aws_call(*args, **kwargs):
        pytest.fail("An invalid cross-check key reached the AWS CLI")

    monkeypatch.setattr(fetch_public_patches.subprocess, "run", unexpected_aws_call)
    with pytest.raises(ValueError, match="exact allowlisted"):
        fetch_public_patches.cross_check_sonnet(PREFIX + "/all_preds.jsonl", [])


@pytest.mark.parametrize("upstream", [" \r\n", ""])
def test_sonnet_cross_check_uses_raw_submission_before_empty_normalization(
    upstream, tmp_path, monkeypatch
):
    script = fetch_public_patches
    monkeypatch.setattr(script, "ROOT", tmp_path)
    folder = tmp_path / script.PATCHES / script.SONNET_FOLDER
    folder.mkdir(parents=True)
    raw = json.dumps({"instance_id": INSTANCE_ID, "model_patch": upstream}).encode() + b"\n"
    monkeypatch.setattr(script, "copy_s3_object", lambda key: CompletedProcess([], 0, raw, b""))
    tasks = [
        {
            "instance_id": INSTANCE_ID,
            "empty": True,
            "empty_reason": "blank",
            "patch_sha256": script.sha256(b""),
            "submission_sha256": script.sha256(b" \r\n"),
        }
    ]
    if upstream:
        script.cross_check_sonnet(script.SONNET_ALL_PREDS, tasks)
    else:
        with pytest.raises(SystemExit, match=INSTANCE_ID):
            script.cross_check_sonnet(script.SONNET_ALL_PREDS, tasks)
    summary = json.loads((folder / "cross_check.json").read_text())
    assert summary["matched"] == bool(upstream)
    assert summary["mismatch_ids"] == ([] if upstream else [INSTANCE_ID])


def test_fetch_stops_after_combined_gate_breach(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_public_patches, "ROOT", tmp_path)
    calls = []

    def unavailable(prefix, instance_id, key, format_name, *, first_file):
        calls.append(instance_id)
        outcome = "missing" if len(calls) % 2 else "malformed"
        return {"instance_id": instance_id, "s3_key": key, outcome: True}

    monkeypatch.setattr(fetch_public_patches, "fetch_pred", unavailable)
    system = {"folder": "example", "trajs_prefix": PREFIX, "format": "pred_v0"}
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
