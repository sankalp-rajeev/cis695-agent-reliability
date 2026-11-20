#!/usr/bin/env python3
"""Fetch the preregistered public trajectory predictions and cached reference patches."""

import csv
import fcntl
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

from reliability.benchmark.loader import load_instance
from reliability.verifier.admission_reference import JSONProjection

if __package__:
    from .draw_test_set import INPUTS, ROOT, load_dev_ids
else:
    from draw_test_set import INPUTS, ROOT, load_dev_ids

PATCHES = Path("runs/study_v1_5/patches")
TRAJS_PREFIX = re.compile(r"s3://swe-bench-submissions/bash-only/[A-Za-z0-9._-]+/trajs")
INSTANCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*__[A-Za-z0-9][A-Za-z0-9_.-]*-[0-9]+")
SUFFIXES = {"pred_v0": ".pred", "traj_json_v1": ".traj.json"}
SONNET_FOLDER = "20250726_mini-v1.0.0_claude-sonnet-4-20250514"
SONNET_ALL_PREDS = f"s3://swe-bench-submissions/bash-only/{SONNET_FOLDER}/all_preds.jsonl"


def validate_pred_key(prefix: str, instance_id: str, key: str, format_name="pred_v0") -> None:
    if not TRAJS_PREFIX.fullmatch(prefix) or not INSTANCE_ID.fullmatch(instance_id):
        raise ValueError("Invalid trajectory prefix or instance ID")
    suffix = SUFFIXES.get(format_name)
    if suffix is None or key != f"{prefix}/{instance_id}/{instance_id}{suffix}":
        raise ValueError("Key must match the specified instance and system format under its prefix")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_atomic(path: Path, data: bytes, mode: int) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    # A killed process may leave a read-only temporary file behind.
    temporary.unlink(missing_ok=True)
    temporary.write_bytes(data)
    temporary.chmod(mode)
    temporary.replace(path)


def store_patch(folder: str, instance_id: str, patch: str | None, **source) -> dict:
    if not INSTANCE_ID.fullmatch(instance_id):
        raise ValueError("Invalid instance ID")
    path = PATCHES / folder / f"{instance_id}.patch"
    empty = patch is None or patch.strip() == ""
    raw = b"" if empty else patch.encode("utf-8")
    write_atomic(ROOT / path, raw, 0o444)
    record = {
        "instance_id": instance_id,
        "patch_path": path.as_posix(),
        "patch_sha256": sha256(raw),
        "empty": empty,
        **source,
    }
    if empty:
        record["empty_reason"] = "null" if patch is None else "blank"
    return record


def copy_s3_object(key: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["aws", "s3", "cp", key, "-", "--no-sign-request", "--only-show-errors", "--no-progress"],
        capture_output=True,
        timeout=120,
        check=False,
    )


class ObservedFields(dict):
    """Collect object key names while the projection skips unrelated values."""

    def __init__(self, fields):
        super().__init__(fields)
        self.names = []

    def __contains__(self, key):
        self.names.append(key)
        return super().__contains__(key)


class ObjectProjection(JSONProjection):
    def project(self, schema, *, calls=False):
        self.whitespace()
        if schema is not True and self.text[self.position] != "{":
            self.skip()
            return {}
        return super().project(schema, calls=calls)


def submission_fingerprint(patch) -> str:
    if isinstance(patch, str):
        return sha256(patch.encode("utf-8"))
    encoded = json.dumps(patch, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8"))


def fetch_pred(
    prefix: str, instance_id: str, key: str, format_name="pred_v0", *, first_file=False
) -> tuple[str | None, dict] | dict:
    validate_pred_key(prefix, instance_id, key, format_name)
    result = copy_s3_object(key)
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        if re.search(r"\((?:404|NoSuchKey|NotFound)\)", error):
            return {"instance_id": instance_id, "s3_key": key, "missing": True, "error": error}
        raise RuntimeError(f"AWS CLI failed for {key}: {error}")

    source = {"s3_key": key, "pred_sha256": sha256(result.stdout)}
    try:
        if format_name == "pred_v0":
            prediction = json.loads(result.stdout)
        else:
            info_fields = ObservedFields({"submission": True, "exit_status": True})
            trajectory_fields = ObservedFields({"info": info_fields})
            prediction = ObjectProjection(result.stdout.decode("utf-8")).project(trajectory_fields)
    except (ValueError, IndexError, KeyError):
        raise ValueError(f"Invalid prediction JSON for {key}") from None

    if format_name == "pred_v0":
        if not isinstance(prediction, dict) or prediction.get("instance_id") != instance_id:
            raise ValueError(f"Prediction instance ID mismatch for {key}")
        patch_field = "model_patch"
    else:
        prediction = prediction.get("info", {})
        patch_field = "submission"
        if first_file and patch_field not in prediction:
            raise SystemExit(
                f"{instance_id}: top-level keys {trajectory_fields.names!r}; "
                f"info keys {info_fields.names!r}"
            )
        exit_status = prediction.get("exit_status")
        if exit_status is not None and not isinstance(exit_status, str):
            raise ValueError(f"Invalid exit_status type for {instance_id}")
        source["exit_status"] = exit_status
        if patch_field in prediction:
            source["submission_sha256"] = submission_fingerprint(prediction[patch_field])

    patch = prediction.get(patch_field)
    if patch_field not in prediction or (patch is not None and not isinstance(patch, str)):
        return {
            "instance_id": instance_id,
            **source,
            "malformed": True,
            "model_patch_type": type(patch).__name__ if patch_field in prediction else "absent",
        }
    return patch, source


def check_gate(folder: str, tasks: list[dict]) -> None:
    for name, group in (("development", tasks[:92]), ("test", tasks[92:200])):
        issues = sum(bool(task.get("missing") or task.get("malformed")) for task in group)
        if issues > 5:
            raise SystemExit(f"Phase 2 gate failed for {folder}: {issues} {name} issues")


def fetch_public(system: dict, ids: list[str]) -> list[dict]:
    folder = system["folder"]
    prefix = system["trajs_prefix"]
    format_name = system["format"]
    suffix = SUFFIXES[format_name]
    if not TRAJS_PREFIX.fullmatch(prefix) or folder.casefold() != prefix.split("/")[-2].casefold():
        raise ValueError("Trajectory prefix and system folder must correspond")
    manifest = ROOT / PATCHES / folder / "tasks.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    tasks = json.loads(manifest.read_text())["tasks"] if manifest.exists() else []
    if [task["instance_id"] for task in tasks] != ids[: len(tasks)]:
        raise ValueError(f"Cannot resume {folder}: manifest IDs differ from the requested order")
    print(f"{folder}: {len(tasks)}/{len(ids)} already recorded", flush=True)
    check_gate(folder, tasks)
    seen_prediction = any(not task.get("missing") for task in tasks)

    for index, instance_id in enumerate(ids, start=1):
        key = f"{prefix}/{instance_id}/{instance_id}{suffix}"
        if index <= len(tasks):
            prior = tasks[index - 1]
            validate_pred_key(prefix, instance_id, prior["s3_key"], format_name)
            if not prior.get("missing") and not prior.get("malformed"):
                path = PATCHES / folder / f"{instance_id}.patch"
                patch_file = ROOT / path
                if (
                    prior["patch_path"] != path.as_posix()
                    or sha256(patch_file.read_bytes()) != prior["patch_sha256"]
                    or patch_file.stat().st_mode & 0o222
                ):
                    raise ValueError(
                        f"Cannot resume {folder}: stored patch differs for {instance_id}"
                    )
            continue

        result = fetch_pred(prefix, instance_id, key, format_name, first_file=not seen_prediction)
        if isinstance(result, dict):
            task = result
        else:
            patch, source = result
            task = store_patch(folder, instance_id, patch, **source)
        seen_prediction = seen_prediction or not task.get("missing")
        tasks.append(task)
        write_atomic(manifest, (json.dumps({"tasks": tasks}, indent=2) + "\n").encode(), 0o644)
        check_gate(folder, tasks)
        if index % 50 == 0 or index == len(ids):
            print(f"{folder}: {index}/{len(ids)} recorded", flush=True)
    return tasks


def cross_check_sonnet(key: str, tasks: list[dict]) -> None:
    if key != SONNET_ALL_PREDS:
        raise ValueError("Cross-check requires the exact allowlisted Sonnet all_preds.jsonl key")
    result = copy_s3_object(key)
    if result.returncode:
        raise SystemExit("Download failed for the exact Sonnet all_preds.jsonl key")
    fetched = {task["instance_id"]: task for task in tasks if not task.get("missing")}
    predictions = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            row = JSONProjection(line.decode("utf-8")).project(
                {"instance_id": True, "model_patch": True}
            )
        except (ValueError, IndexError, KeyError):
            raise SystemExit("Invalid Sonnet all_preds.jsonl record") from None
        iid = row.get("instance_id")
        if iid in fetched:
            if iid in predictions:
                raise SystemExit(f"Duplicate Sonnet cross-check ID: {iid}")
            if "model_patch" in row:
                patch = row["model_patch"]
                predictions[iid] = (submission_fingerprint(patch), type(patch).__name__)
            else:
                predictions[iid] = None

    mismatches = []
    for iid, task in fetched.items():
        patch_type = task.get(
            "model_patch_type", "NoneType" if task.get("empty_reason") == "null" else "str"
        )
        signature = (task.get("submission_sha256"), patch_type)
        if predictions.get(iid) != signature:
            mismatches.append(iid)
    matched = len(fetched) - len(mismatches)
    summary = {
        "fetched": len(fetched),
        "matched": matched,
        "mismatch_ids": mismatches,
        "s3_key": key,
        "all_preds_sha256": sha256(result.stdout),
    }
    write_atomic(
        ROOT / PATCHES / SONNET_FOLDER / "cross_check.json",
        (json.dumps(summary, indent=2) + "\n").encode(),
        0o644,
    )
    print(f"Sonnet cross-check: {matched}/{len(fetched)} match", flush=True)
    if mismatches:
        raise SystemExit(f"Sonnet cross-check mismatch IDs: {', '.join(mismatches)}")


def fetch_reference(dev_ids: list[str], test_ids: list[str]) -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    with (ROOT / "reports/rerun_v1/arm_B/analysis/patch_tasks.csv").open(newline="") as stream:
        rows = csv.reader(stream)
        instance_id_column = next(rows).index("instance_id")
        gold_dev_ids = [row[instance_id_column] for row in rows]
    if len(gold_dev_ids) != 51 or len(set(gold_dev_ids)) != 51 or set(gold_dev_ids) - set(dev_ids):
        raise ValueError("Expected 51 distinct Arm B patch task IDs from the development set")

    manifest = ROOT / PATCHES / "reference" / "tasks.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    tasks = []
    for instance_id in gold_dev_ids + test_ids:
        patch = load_instance(instance_id)[1].patch
        tasks.append(store_patch("reference", instance_id, patch, s3_key=None, pred_sha256=None))
    write_atomic(manifest, (json.dumps({"tasks": tasks}, indent=2) + "\n").encode(), 0o644)
    print(f"reference: {len(tasks)} recorded", flush=True)


def main() -> None:
    systems = yaml.safe_load((ROOT / "configs/study_v1_5/systems.yaml").read_text())["systems"]
    order = json.loads((INPUTS / "test_order.json").read_text())["order"]
    dev_ids = load_dev_ids()
    test_ids = order[:130]
    ids = dev_ids + test_ids
    if (
        len(test_ids) != 130
        or len(set(ids)) != 222
        or any(not INSTANCE_ID.fullmatch(iid) for iid in ids)
    ):
        raise ValueError("Expected 92 development and 130 disjoint test IDs")
    if [system["priority"] for system in systems] != list(range(1, 7)):
        raise ValueError("Expected six systems in priority order")
    if any(system.get("format") not in SUFFIXES for system in systems):
        raise ValueError("Expected a confirmed format for each system")

    (ROOT / PATCHES).mkdir(parents=True, exist_ok=True)
    with (ROOT / PATCHES / ".fetch.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for system in systems:
            tasks = fetch_public(system, ids)
            if system["folder"] == SONNET_FOLDER:
                cross_check_sonnet(SONNET_ALL_PREDS, tasks)
        fetch_reference(dev_ids, test_ids)


if __name__ == "__main__":
    main()
