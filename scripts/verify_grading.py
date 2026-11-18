#!/usr/bin/env python3
"""Verify the frozen source, grading copies, and label arithmetic."""

import argparse
import csv
import fcntl
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "instance_id", "patch_sha256", "oracle_outcome", "resolved",
    "fail_to_pass_passed", "fail_to_pass_total", "pass_to_pass_passed",
    "pass_to_pass_total", "harness_error_class", "wrong_patch_type",
)
OUTCOMES = ("empty_patch", "resolved", "unresolved", "patch_apply_failed", "infra_error")
SHA256 = re.compile("[0-9a-f]{64}")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def report_dir(arm):
    return ROOT / "reports" / "rerun_v1" / f"arm_{arm}"


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--arm", choices=("A", "B"), required=True)
    parser.add_argument("--sealed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def check_seal(arm, sealed):
    seal = report_dir(arm) / "seal"
    manifest_path = seal / "manifest.sha256"
    digest = sha(manifest_path)
    if (seal / "manifest.sha256.sha256").read_text().split() != [digest, manifest_path.name]:
        raise ValueError("Manifest digest does not match its recorded SHA-256")

    manifest = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        checksum, name = line.split("  ", 1)
        path = Path(name)
        if (not SHA256.fullmatch(checksum) or path.is_absolute()
                or ".." in path.parts or path.as_posix() != name or name in manifest):
            raise ValueError(f"Invalid manifest entry: {name!r}")
        manifest[name] = checksum
    if list(manifest) != sorted(manifest):
        raise ValueError("Manifest paths are out of order")

    if not sealed.is_dir():
        raise ValueError(f"Sealed arm directory is missing: {sealed}")
    seen = set()
    for path in sealed.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError(f"Unexpected file type in sealed arm: {path}")
        if path.is_dir():
            continue
        name = path.relative_to(sealed).as_posix()
        if name not in manifest or sha(path) != manifest[name]:
            raise ValueError(f"Sealed file added or changed: {name}")
        seen.add(name)
    if missing := manifest.keys() - seen:
        raise ValueError(f"Sealed files missing: {sorted(missing)[:5]}")

    for name in ("completion.json", "attempt.json", "header.json", "seal.json"):
        if sha(seal / name) != manifest[name]:
            raise ValueError(f"Sealed report copy changed: {name}")
    completion = read_json(seal / "completion.json")
    if completion["status"] not in ("COMPLETE", "STOPPED_BUDGET"):
        raise ValueError(f"Arm did not reach a gradeable stop: {completion['status']}")
    ids = completion["completed_tasks"]
    if len(ids) != len(set(ids)) or any(
        not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+", iid) for iid in ids
    ):
        raise ValueError("Invalid completed instance IDs")
    return manifest, ids


def check_patch(manifest, out, iid):
    name = f"tasks/{iid}/patch.diff"
    path = out / name
    expected = manifest[name]
    if path.is_symlink() or sha(path) != expected:
        raise ValueError(f"Grading copy differs from the seal: {name}")
    return expected


def wrong_type(outcome, ftp_passed, ftp_total, ptp_passed, ptp_total):
    if not (0 <= ftp_passed <= ftp_total and 0 <= ptp_passed <= ptp_total):
        raise ValueError("Invalid oracle test counts")
    if outcome in ("patch_apply_failed", "infra_error"):
        return "X"
    if outcome == "unresolved":
        if ptp_passed < ptp_total:
            return "R"
        if ftp_passed < ftp_total:
            return "U"
        raise ValueError("Oracle reports unresolved without a failing test")
    if outcome in ("resolved", "empty_patch") and (
        ftp_passed == ftp_total and ptp_passed == ptp_total
    ):
        return ""
    raise ValueError(f"Unexpected oracle outcome or counts: {outcome}")


def label_row(iid, digest, oracle, error_class):
    outcome = oracle["outcome"]
    if oracle["instance_id"] != iid or oracle["patch_sha256"] != f"sha256:{digest}":
        raise ValueError(f"Oracle record identity differs from the seal: {iid}")
    resolved = {"resolved": True, "unresolved": False, "patch_apply_failed": False}
    if outcome not in OUTCOMES or oracle["resolved"] is not resolved.get(outcome):
        raise ValueError(f"Invalid oracle verdict: {iid}")
    ftp = oracle["fail_to_pass"]
    ptp = oracle["pass_to_pass"]
    ftp_passed = len(ftp["success"])
    ftp_total = ftp_passed + len(ftp["failure"])
    ptp_passed = len(ptp["success"])
    ptp_total = ptp_passed + len(ptp["failure"])
    if outcome in ("infra_error", "patch_apply_failed") and not error_class:
        raise ValueError(f"Missing harness error class: {iid}")
    if outcome not in ("infra_error", "patch_apply_failed") and error_class:
        raise ValueError(f"Unexpected harness error class: {iid}")
    kind = wrong_type(outcome, ftp_passed, ftp_total, ptp_passed, ptp_total)
    return dict(zip(FIELDS, (
        iid, digest, outcome, str(outcome == "resolved").lower(),
        str(ftp_passed), str(ftp_total), str(ptp_passed), str(ptp_total),
        error_class, kind,
    ), strict=True))


def load_labels(manifest, ids, out):
    rows = []
    for iid in ids:
        task = out / "tasks" / iid
        digest = check_patch(manifest, out, iid)
        grading = read_json(task / "grading.json")
        oracle = read_json(task / "oracle_record.json")
        if grading["outcome"] != oracle["outcome"]:
            raise ValueError(f"Grading and oracle records disagree: {iid}")
        first_attempt = task / "first_attempt" / "oracle_record.json"
        expected_attempts = 2 if first_attempt.is_file() else 1
        if len(grading["attempts"]) != expected_attempts:
            raise ValueError(f"Inconsistent attempt records: {iid}")
        if first_attempt.is_file():
            first = read_json(first_attempt)
            if (first["instance_id"], first["patch_sha256"], first["outcome"]) != (
                iid, f"sha256:{digest}", "infra_error",
            ):
                raise ValueError(f"Invalid infrastructure retry evidence: {iid}")
        if oracle["outcome"] == "infra_error" and expected_attempts != 2:
            raise ValueError(f"Infrastructure error was not retried: {iid}")
        if (not (task / "patch.diff").read_text(encoding="utf-8").strip()) != (
            oracle["outcome"] == "empty_patch"
        ):
            raise ValueError(f"Empty-patch result disagrees with the sealed patch: {iid}")
        rows.append(label_row(iid, digest, oracle, grading["error_class"]))
    return rows


def label_summary(rows):
    outcomes = Counter(row["oracle_outcome"] for row in rows)
    kinds = Counter(row["wrong_patch_type"] for row in rows)
    return {
        "total": len(rows),
        "outcomes": {name: outcomes[name] for name in OUTCOMES},
        "wrong_patch_types": {kind: kinds[kind] for kind in ("R", "U", "X")},
    }


def verify_files(directory, expected):
    with (directory / "labels.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Unexpected labels.csv columns")
        rows = list(reader)
    if rows != expected:
        raise ValueError("Labels differ from the sealed patch identities or oracle records")
    for row in rows:
        counts = (int(row[field]) for field in FIELDS[4:8])
        if row["wrong_patch_type"] != wrong_type(row["oracle_outcome"], *counts):
            raise ValueError(f"Wrong-patch classification disagrees: {row['instance_id']}")
    if label_summary(rows) != read_json(directory / "labels_summary.json"):
        raise ValueError("Label counts do not match labels_summary.json")


def grading_report(arm, directory, out, rows, summary):
    manifest_digest = sha(directory / "seal" / "manifest.sha256")
    records = [read_json(out / "tasks" / row["instance_id"] / "grading.json") for row in rows]
    versions = {(item["swebench_version"], item["timeout_s"]) for item in records}
    if versions != {("5.0.2", 1800)}:
        raise ValueError(f"Unexpected harness versions or timeouts: {versions}")
    attempts = [attempt for record in records for attempt in record["attempts"]]
    started = min(datetime.fromisoformat(attempt["started_at"]) for attempt in attempts)
    finishes = [attempt["finished_at"] for attempt in attempts if attempt["finished_at"]]
    finished = max(datetime.fromisoformat(value) for value in finishes) if finishes else None
    empty_time = sum(attempt["wall_seconds"]
                     for record in records if record["outcome"] == "empty_patch"
                     for attempt in record["attempts"])
    oracle_time = sum(attempt["wall_seconds"] for attempt in attempts)
    retries = sum(len(record["attempts"]) - 1 for record in records)
    lines = [
        f"# Rerun v1 Arm {arm} grading",
        "",
        f"The annotated tag `rerun-arm{arm}-sealed` binds {len(rows)} completed tasks to manifest SHA-256 `{manifest_digest}`.",
        "The source was re-hashed before and after grading and at finalization. See [the seal](seal/) for the pre-grading accounting.",
        "",
        "The frozen `run_oracle` used SWE-bench 5.0.2 from the lockfile and a 1,800-second task timeout.",
        "Non-empty patches used the oracle's existing harness network configuration. Verified dataset access was offline.",
        "",
        "## Timing",
        "",
        f"The first recorded attempt started at {started.isoformat()}.",
    ]
    if finished:
        lines.append(f"The latest recorded attempt ended at {finished.isoformat()}.")
    lines += [
        f"The {len(attempts)} oracle attempts took {oracle_time:.3f} seconds in total, "
        f"including {empty_time:.3f} seconds on empty patches. These are summed attempt times.",
        f"Mean wall time including retries was {oracle_time / len(rows):.3f} seconds per completed task.",
        "",
        "## Harness errors and re-runs",
        "",
        f"{retries} infrastructure re-runs. {summary['outcomes']['infra_error']} final infrastructure errors.",
    ]
    recovered = sum(attempt.get("timing_recovered_from_oracle", False) for attempt in attempts)
    if recovered:
        lines.insert(-4, f"For {recovered} interrupted receipts, timing comes from the oracle record.")
    for row, record in zip(rows, records, strict=True):
        failures = [attempt["error_class"] or "none" for attempt in record["attempts"]]
        interrupted = sorted((out / "tasks" / row["instance_id"]).glob("interrupted_*"))
        if any(attempt != "none" for attempt in failures):
            final = (
                f"X:{row['harness_error_class']}" if row["wrong_patch_type"] == "X"
                else row["oracle_outcome"]
            )
            lines.append(f"- `{row['instance_id']}` had attempt classes "
                         f"`{' → '.join(failures)}` and finished `{final}`.")
        if interrupted:
            lines.append(f"- `{row['instance_id']}` has {len(interrupted)} archived interrupted attempts.")
    lines += [
        "",
        "## Label counts",
        "",
        "| Oracle outcome | Tasks |",
        "| --- | ---: |",
        *(f"| {outcome} | {count} |" for outcome, count in summary["outcomes"].items()),
        "",
        "| Wrong-patch type | Tasks |",
        "| --- | ---: |",
        *(f"| {kind} | {count} |" for kind, count in summary["wrong_patch_types"].items()),
        "",
    ]
    return "\n".join(lines)


def finalize(arm, sealed, out, directory):
    if not (out / "progress.json").is_file():
        raise ValueError("Grading is incomplete. No progress file exists.")
    with (out / "grading.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Grading is still running.") from exc
        progress = read_json(out / "progress.json")
        if progress["status"] != "complete" or progress["done"] != progress["total"]:
            raise ValueError(f"Grading is incomplete ({progress['done']}/{progress['total']}).")
        manifest, ids = check_seal(arm, sealed)
        if len(ids) != progress["total"]:
            raise ValueError("Progress total differs from the sealed completion record")
        rows = load_labels(manifest, ids, out)
        summary = label_summary(rows)
        if summary["outcomes"] != progress["outcome_counts"]:
            raise ValueError("Grading records disagree with progress counts")
        with TemporaryDirectory(dir=directory) as temporary:
            staging = Path(temporary)
            with (staging / "labels.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            (staging / "labels_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            (staging / "REPORT.md").write_text(grading_report(arm, directory, out, rows, summary))
            verify_files(staging, rows)
            for path in staging.iterdir():
                path.replace(directory / path.name)
        decisions = directory / "DECISIONS.md"
        base = decisions.read_text().split("\n## After grading\n", 1)[0].rstrip()
        decisions.write_text(base + "\n\n## After grading\n\n"
                             + f"Finalized and verified {len(rows)} labels. "
                             "See [the report](REPORT.md) for timing and re-runs.\n")
        status = ROOT / "STATUS.md"
        status_text = status.read_text()
        completion = f"Arm {arm} grading complete and all {len(rows)} labels verified."
        if completion not in status_text:
            heading, remainder = status_text.split("\n\n", 1)
            status.write_text(
                f"{heading}\n\n{completion} "
                f"See [the grading report](reports/rerun_v1/arm_{arm}/REPORT.md).\n\n{remainder}"
            )
    print(f"Wrote and verified {len(rows)} labels")


def main():
    parser = parse_args(__doc__)
    parser.add_argument("--finalize", action="store_true", help="Publish labels after all tasks finish")
    args = parser.parse_args()
    directory = report_dir(args.arm)
    try:
        if args.finalize:
            finalize(args.arm, args.sealed, args.out, directory)
        else:
            manifest, ids = check_seal(args.arm, args.sealed)
            rows = load_labels(manifest, ids, args.out)
            verify_files(directory, rows)
            print(f"Seal, grading copies and counts verified for {len(ids)} tasks")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
