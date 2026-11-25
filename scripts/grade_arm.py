#!/usr/bin/env python3
"""Grade one sealed rerun arm serially and retain results for resumption."""

import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tomllib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import monotonic

from verify_grading import (
    OUTCOMES, ROOT, check_patch, check_seal, parse_args, read_json, report_dir,
)

sys.path.insert(0, str(ROOT / "src"))

TIMEOUT_S = 1800
FROZEN_TAG = "e2e-v1.4.3-frozen"
SWEBENCH_VERSION = "5.0.2"
EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()
POLL_S = 5


class GradingPaused(RuntimeError):
    pass


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def utc_now():
    return datetime.now(UTC).isoformat()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def check_environment(arm):
    if Path(sys.prefix) != ROOT / ".venv":
        raise ValueError("Run this script with the worktree's .venv/bin/python")
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked, = (entry["version"] for entry in lock["package"] if entry["name"] == "swebench")
    installed = version("swebench")
    if locked != SWEBENCH_VERSION or installed != locked:
        raise ValueError(f"Main study, lockfile, and installed SWE-bench differ: "
                         f"{SWEBENCH_VERSION}, {locked}, {installed}")
    subprocess.run(
        ["git", "diff", "--exit-code", "--quiet", FROZEN_TAG, "--", "src", "uv.lock"],
        cwd=ROOT, check=True,
    )
    tag = f"rerun-arm{arm}-sealed"
    if git("cat-file", "-t", f"refs/tags/{tag}").strip() != b"tag":
        raise ValueError(f"The seal tag is not annotated: {tag}")
    seal = report_dir(arm) / "seal"
    manifest = seal / "manifest.sha256"
    if git("show", f"{tag}:{manifest.relative_to(ROOT)}") != manifest.read_bytes():
        raise ValueError("Working manifest differs from the annotated seal")
    tagged_message = git("for-each-ref", "--format=%(contents)", f"refs/tags/{tag}").decode()
    checksum = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if f"Manifest SHA-256 {checksum}" not in tagged_message:
        raise ValueError("Annotated tag message does not match the seal manifest")

    os.environ.update(
        HF_HOME=str(ROOT / "runs" / "hf_home"),
        HF_DATASETS_OFFLINE="1",
        HF_HUB_OFFLINE="1",
    )
    # Dedicated offline cache, including in shells with separate HF overrides.
    for key in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "HF_DATASETS_CACHE"):
        os.environ.pop(key, None)
    if not (ROOT / "runs/hf_home/datasets/SWE-bench___swe-bench_verified").is_dir():
        raise ValueError("Missing the offline SWE-bench Verified dataset cache in runs/hf_home")
    if read_json(seal / "header.json")["git_head"] != git("rev-parse", f"{FROZEN_TAG}^{{commit}}").decode().strip():
        raise ValueError("Sealed arm and oracle pipeline commits differ")


def busy_reason(run_id=None):
    tmux = subprocess.run(
        ["tmux", "ls", "-F", "#{session_name}"], text=True, capture_output=True, timeout=10
    )
    if tmux.returncode and not any(
        message in tmux.stderr for message in ("no server running", "No such file or directory")
    ):
        raise GradingPaused(f"Cannot check tmux: {tmux.stderr.strip()}")
    for name in tmux.stdout.splitlines():
        if name in {"armA", "armB"}:
            return f"active tmux session {name}"

    docker = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}"],
        text=True, capture_output=True, timeout=15,
    )
    if docker.returncode:
        raise GradingPaused(f"Cannot check Docker: {docker.stderr.strip()}")
    for row in docker.stdout.splitlines():
        name, image = row.split("\t", 1)
        if run_id and name.startswith("sweb.eval.") and re.search(
            rf"\.{re.escape(run_id)}(?:\.\d+)?$", name
        ):
            continue
        if re.search(r"verify_|agent_|sweb[./-]|swebench", f"{name} {image}", re.I):
            return f"active Docker container {name}"

    processes = subprocess.check_output(["ps", "-eo", "comm=,args="], text=True)
    for line in processes.splitlines():
        command, _, args = line.strip().partition(" ")
        if command.startswith("python") and "swebench.harness.run_evaluation" in args:
            if not run_id or f"--run_id {run_id} " not in f"{args} ":
                return "active SWE-bench harness process"
        if command.startswith("python") and re.search(r"(^|/)run_e2e\.py(?: |$)", args):
            return "active E2E arm process"
        if command == "docker" and re.search(r"\b(build|buildx build|compose build|run|exec)\b", args):
            return "active Docker workload"
    return None


def require_idle():
    if reason := busy_reason():
        raise GradingPaused(f"Docker must be idle before grading: {reason}")


def checked_source(sealed, manifest, name):
    raw = (sealed / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest[name]:
        raise ValueError(f"Sealed input changed: {name}")
    return raw


def stage_task(sealed, manifest, task):
    from reliability.verifier.record import VerificationRecord

    task.mkdir(parents=True, exist_ok=True)
    prefix = f"tasks/{task.name}"
    for name in ("patch.diff", "repair_record.json", "verification_record.full-v1.4.1.json"):
        raw = checked_source(sealed, manifest, f"{prefix}/{name}")
        if name.startswith("verification_record."):
            source = json.loads(raw)
            fields = {key: source[key] for key in VerificationRecord.model_fields if key in source}
            VerificationRecord.validate_dict(fields)
            raw = (json.dumps(fields, indent=2) + "\n").encode()
            name = "verification_record.full.json"
        target = task / name
        if target.exists():
            if target.is_symlink() or target.read_bytes() != raw:
                raise ValueError(f"Existing grading input changed: {target}")
        else:
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_bytes(raw)
            if name == "patch.diff":
                temporary.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            temporary.replace(target)
    check_patch(manifest, task.parent.parent, task.name)


def check_task_location(task):
    if task.resolve() != task:
        raise ValueError(f"Grading task path contains a symlink: {task}")


def harness_root(task):
    experiment = read_json(task / "repair_record.json")["experiment_id"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", experiment):
        raise ValueError(f"Unexpected experiment ID for {task.name}")
    return ROOT / "logs" / "run_evaluation" / f"{experiment}__{task.name}"


def archive_attempt(task, destination):
    destination.mkdir(exist_ok=True)
    harness = harness_root(task)
    if harness.exists():
        harness.rename(destination / "harness")
    # Move the receipt before the oracle record so an interrupted retry remains identifiable.
    for name in ("harness.log", "predictions.jsonl", "attempt.json", "oracle_record.json"):
        path = task / name
        if path.exists():
            path.rename(destination / name)


def archive_interrupted(task):
    number = 1
    while (task / f"interrupted_{number}").exists():
        number += 1
    archive_attempt(task, task / f"interrupted_{number}")


def error_class(oracle, task):
    if oracle.outcome.value == "patch_apply_failed":
        return "patch_apply_failed"
    if not oracle.infrastructure_error:
        return ""
    if oracle.report_file:
        report = read_json(Path(oracle.report_file))[task.name]
        return report.get("infra_failure_reason") or "harness_reported_infrastructure"
    logs = list(harness_root(task).rglob("run_instance.log")) + [task / "harness.log"]
    for log in logs:
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="replace")
            if ">>>>> Patch Apply Failed" in text:
                return "patch_apply_failed"
            if re.search(r"Test timed out after|Timeout error:", text):
                return "harness_timeout"
    return "missing_harness_report"


def run_attempt(run_oracle, task):
    start = monotonic()
    started_at = utc_now()
    write_json(task / "attempt.json", {"started_at": started_at})
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(run_oracle, task, timeout_s=TIMEOUT_S, repo_root=ROOT)
        interference = None
        while True:
            try:
                oracle = pending.result(timeout=POLL_S)
                elapsed = monotonic() - start
                break
            except TimeoutError:
                if pending.done():
                    raise
                try:
                    interference = busy_reason(harness_root(task).name) or interference
                except (GradingPaused, subprocess.SubprocessError) as exc:
                    interference = str(exc)
                if interference:
                    write_json(task / "attempt.json", {
                        "started_at": started_at, "interference": interference,
                    })
        try:
            interference = busy_reason(harness_root(task).name) or interference
        except (GradingPaused, subprocess.SubprocessError) as exc:
            interference = str(exc)
    write_json(task / "attempt.json", {
        "started_at": started_at, "finished_at": utc_now(), "wall_seconds": round(elapsed, 6),
        "error_class": error_class(oracle, task), "interference": interference,
    })
    if interference:
        archive_interrupted(task)
        raise GradingPaused(f"Grading paused after Docker contention: {interference}")
    return oracle


def grade_task(task, expected):
    from pydantic import ValidationError
    from reliability.oracle.records import OracleRecord
    from reliability.oracle.runner import run_oracle

    record = task / "oracle_record.json"
    retry = task / "first_attempt"
    receipt = task / "attempt.json"
    if receipt.exists() and read_json(receipt).get("interference"):
        archive_interrupted(task)
    while True:
        if record.is_file():
            try:
                oracle = OracleRecord.read(record)
            except ValidationError:
                archive_interrupted(task)
        if not record.is_file():
            require_idle()
            if any((task / name).exists() for name in ("harness.log", "attempt.json", "predictions.jsonl")) or harness_root(task).exists():
                archive_interrupted(task)
            print(f"Grading {task.name}{' (infrastructure retry)' if retry.exists() else ''}", flush=True)
            oracle = run_attempt(run_oracle, task)
        if oracle.instance_id != task.name or oracle.patch_sha256 != f"sha256:{expected}":
            raise ValueError(f"Oracle record does not match sealed task: {task.name}")
        if retry.is_dir() and not (retry / record.name).exists() and (retry / receipt.name).is_file():
            # A crash while archiving may leave the first attempt's receipt on its own.
            if not receipt.exists():
                (retry / receipt.name).rename(receipt)
        if not receipt.is_file() or "wall_seconds" not in read_json(receipt):
            write_json(receipt, {
                "started_at": oracle.evaluated_at, "finished_at": None,
                "wall_seconds": oracle.duration_s, "error_class": error_class(oracle, task),
                "timing_recovered_from_oracle": True,
            })
        if oracle.infrastructure_error and not (retry / record.name).is_file():
            archive_attempt(task, retry)
            continue
        attempts = [read_json(retry / receipt.name)] if retry.exists() else []
        attempts.append(read_json(receipt))
        result = {
            "swebench_version": SWEBENCH_VERSION, "timeout_s": TIMEOUT_S,
            "outcome": oracle.outcome.value, "error_class": attempts[-1]["error_class"],
            "attempts": attempts,
        }
        write_json(task / "grading.json", result)
        return result


def write_progress(out, ids, results, status, current=None, error=None):
    counts = Counter(result["outcome"] for result in results.values())
    errors = Counter(
        attempt["error_class"]
        for result in results.values() for attempt in result["attempts"]
        if attempt["error_class"]
    )
    write_json(out / "progress.json", {
        "status": status, "done": len(results), "total": len(ids), "current_task": current,
        "outcome_counts": {outcome: counts[outcome] for outcome in OUTCOMES},
        "errors": dict(sorted(errors.items())), "last_error": error,
        "updated_at": utc_now(),
    })


def grade(args, sealed, out):
    check_environment(args.arm)
    from reliability.oracle.records import OracleRecord

    manifest, ids = check_seal(args.arm, sealed)
    results = {}
    current = None
    try:
        for iid in ids:
            task = out / "tasks" / iid
            check_task_location(task)
            if (task / "grading.json").exists():
                digest = check_patch(manifest, out, iid)
                result = read_json(task / "grading.json")
                oracle = OracleRecord.read(task / "oracle_record.json")
                if (oracle.instance_id != iid or oracle.patch_sha256 != f"sha256:{digest}"
                        or oracle.outcome.value != result["outcome"]
                        or result["swebench_version"] != SWEBENCH_VERSION
                        or result["timeout_s"] != TIMEOUT_S):
                    raise ValueError(f"Completed grading record disagrees with the seal or oracle: {iid}")
                results[iid] = result
        require_idle()
        if args.smoke_test:
            samples = {}
            for iid in ids:
                patch = checked_source(sealed, manifest, f"tasks/{iid}/patch.diff")
                samples.setdefault(bool(patch.decode("utf-8").strip()), iid)
                if len(samples) == 2:
                    break
            selected = [samples[False], samples[True]]
        else:
            selected = ids
        write_progress(out, ids, results, "running")
        for iid in selected:
            if iid in results:
                continue
            current = iid
            write_progress(out, ids, results, "running", current)
            task = out / "tasks" / iid
            stage_task(sealed, manifest, task)
            results[iid] = grade_task(task, manifest[f"tasks/{iid}/patch.diff"])
            check_patch(manifest, out, iid)
            write_progress(out, ids, results, "running")
            current = None
    except (Exception, KeyboardInterrupt) as exc:
        write_progress(out, ids, results, "paused", current, str(exc) or type(exc).__name__)
        raise
    finally:
        try:
            check_seal(args.arm, sealed)
        except Exception as exc:
            write_progress(out, ids, results, "seal_error", current, str(exc))
            raise
    write_progress(out, ids, results, "complete" if len(results) == len(ids) else "incomplete")
    print(f"Grading progress: {len(results)}/{len(ids)} tasks", flush=True)


def main():
    parser = parse_args(__doc__)
    parser.add_argument("--smoke-test", action="store_true",
                        help="Grade only the first empty and first non-empty patch in sealed order")
    args = parser.parse_args()
    sealed = args.sealed.resolve(strict=True)
    out = args.out.resolve()
    if (not out.is_relative_to(ROOT / "runs") or out == ROOT / "runs"
            or out.is_relative_to(sealed) or sealed.is_relative_to(out)):
        raise ValueError("Grading output must be a separate directory below this worktree's runs/")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "grading.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "This grading directory already has an active grader.\n")
        grade(args, sealed, out)


if __name__ == "__main__":
    try:
        main()
    except GradingPaused as exc:
        raise SystemExit(str(exc)) from exc
