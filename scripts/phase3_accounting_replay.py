#!/usr/bin/env python3
"""Stored-data policy and H1 sensitivity; no Docker, source execution or labels."""

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from dataclasses import fields
from pathlib import Path

from phase3_fix1_rescore import StoredExecutor
from phase3_fix2_rescore import DATA
from reliability.verifier.accounting import ADMITTED_STATUSES, h1_accounting
from reliability.verifier.collection import ValidationPass
from reliability.verifier.container import run_from_capture
from reliability.verifier.id_validation import STATIC_INVALID_REASONS, IDValidation
from reliability.verifier.regression import RegressionConfig, Signal, run_regression
from reliability.verifier.selection import Selection, TestRunner
from reliability.verifier.validated_run import apply_validation

ROOT = Path(__file__).resolve().parents[1]


def main(args):
    assert not args.output.exists()
    hashes = {}

    def read(path):
        raw = path.read_bytes()
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        return raw

    static_path = ROOT / "reports/next_phases/phase3_fix3/static_ids.csv.gz"
    static = {}
    allowed = {f.name for f in fields(IDValidation)}
    for row in csv.DictReader(gzip.decompress(read(static_path)).decode().splitlines()):
        payload = {k: v for k, v in row.items() if k in allowed}
        for name in ("runnable_ids", "decorators", "owner_instances", "invalid_instances"):
            payload[name] = tuple(json.loads(payload[name]))
        for name in ("owner_is_testcase", "expanded", "native_disagrees", "unavailable"):
            payload[name] = payload.get(name) == "True"
        if payload["reason"] and payload["reason"] not in STATIC_INVALID_REASONS:
            payload.update(unavailable=True, failure_status="COLLECTION_ERROR")
        static.setdefault((row["instance_id"], row["tree"]), {})[row["selected_id"]] = IDValidation(
            **payload
        )
    gap_path = ROOT / "reports/next_phases/phase2_incomplete_causes/selected_gap_attribution.csv"
    gaps = list(csv.DictReader(read(gap_path).decode().splitlines()))
    b1 = {
        (r["instance_id"], r["tree"], r["test_id"])
        for r in gaps
        if r["scope"] == "initial" and r["cause"] != "environment_guard_abort"
    }
    assert len(b1) == 37614
    expected = json.loads(
        read(ROOT / "reports/next_phases/phase2_incomplete_causes/input_manifest.json")
    )["input_sha256"]
    frozen = DATA / "paired_frozen"
    results = DATA / "full_83_20261105T231219_643682Z/results"
    rows = []
    admitted = set()
    invalid = set()
    retained = set()
    for meta in json.loads(read(frozen / "tasks.json")):
        task = meta["instance_id"]
        runner = TestRunner(**meta["runner"])
        path = results / "tasks" / task / "v2/result.json"
        raw = read(path)
        assert hashlib.sha256(raw).hexdigest() == expected[str(path)]
        native = json.loads(raw)
        tests = tuple(native.get("selected_tests") or ())
        assert list(tests) == json.loads(read(frozen / meta["selections"]["v2"]))["tests"]
        calls = []
        for index, call in enumerate(native.get("calls", [])):
            tree = "patched" if call["patched"] else "base"
            run = call["run"]
            requested = tuple(call.get("requested", run.get("requested_tests", tests)))
            # Historical confirmation IDs may already be concrete; use their
            # frozen selected-family record when available, otherwise preserve
            # only the identity explicitly requested by that recorded call.
            records = tuple(
                static[task, tree].get(t, IDValidation(t, "historical_concrete", (t,)))
                for t in requested
            )
            validation = ValidationPass(
                records, context={"scope": "offline static overlay; no new native collection"}
            )
            files = {n: read(Path(p)) for n, p in run["evidence_files"].items()}
            assert all(
                hashlib.sha256(raw).hexdigest() == run["evidence_sha256"][n]
                for n, raw in files.items()
            )
            preserved = tuple(
                e
                for e in run.get("infrastructure_errors", [])
                if not (
                    e.startswith("runner batch ")
                    or e in ("unexplained nonzero runner exit", "unfinished runner batch")
                )
            )
            parsed = run_from_capture(
                runner,
                validation.runnable_ids,
                runner_log=files["runner.raw"],
                raw_stderr=files.get("stderr.raw", b""),
                raw_stdout=files.get("stdout.raw", b""),
                events=tuple(run.get("events", ())),
                timed_out=run.get("timed_out", False),
                infrastructure_errors=preserved,
                evidence_files=run["evidence_files"],
                evidence_sha256=run["evidence_sha256"],
            )
            mapped = apply_validation(parsed, validation)
            calls.append((call, mapped))
            if index < 2:
                for item in mapped.results:
                    key = (task, tree, item.test_id)
                    if item.status.value == "invalid_id":
                        invalid.add(key)
                    if item.status in ADMITTED_STATUSES:
                        receipt = next(
                            r for r in mapped.validation if r["selected_id"] == item.test_id
                        )
                        if receipt["admitted"]:
                            admitted.add(key)
        row = {"instance_id": task}
        for policy in ("C", "S"):
            for missing in (False, True):
                report = run_regression(
                    task,
                    Selection(tests=tests),
                    StoredExecutor(calls),
                    RegressionConfig(skip_compatible=policy == "C", invalid_as_missing=missing),
                )
                key = f"{policy}_" + ("INVALID_missing" if missing else "INVALID_excluded")
                row[key] = report.signal.value
                if native["signal"] == "FAIL":
                    assert report.signal is Signal.FAIL, (task, key, "native FAIL lost")
                    retained.add(task)
            row[policy + "_differs"] = (
                row[policy + "_INVALID_missing"] != row[policy + "_INVALID_excluded"]
            )
        rows.append(row)
        print(task, row["C_INVALID_excluded"], row["C_INVALID_missing"], flush=True)
    assert len(rows) == 83 and len(retained) == 6
    policy_rows = []
    for policy in ("C", "S"):
        for mode in ("excluded", "missing"):
            counts = Counter(r[policy + "_INVALID_" + mode] for r in rows)
            policy_rows.append(
                {
                    "policy": policy,
                    "INVALID_ID_completeness": mode,
                    **{
                        k: counts[k]
                        for k in (
                            "PASS",
                            "FAIL",
                            "REGRESSION_ERROR",
                            "INCOMPLETE",
                            "NOT_AVAILABLE",
                            "BASELINE_UNRELIABLE",
                        )
                    },
                    "yes_no_PASS_plus_FAIL": counts["PASS"] + counts["FAIL"],
                    "decisive_including_REGRESSION_ERROR": counts["PASS"]
                    + counts["FAIL"]
                    + counts["REGRESSION_ERROR"],
                    "tasks": 83,
                }
            )
    h1 = h1_accounting(b1, admitted, invalid)
    h1["scope"] = (
        "OFFLINE PROJECTION from stored captures plus frozen source validation; not the Phase 4 H1 run result"
    )
    args.output.mkdir(parents=True)

    def write(name, records):
        with (args.output / name).open("w", newline="") as stream:
            w = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(records)

    write("task_policy_sensitivity.csv", rows)
    write("policy_counts.csv", policy_rows)
    (args.output / "H1_projection.json").write_text(json.dumps(h1, indent=2) + "\n")
    summary = {
        "scope": h1["scope"],
        "policy_differing_tasks": {
            p: [r["instance_id"] for r in rows if r[p + "_differs"]] for p in ("C", "S")
        },
        "native_FAIL_retained": len(retained),
        "correctness_labels_read": False,
        "Docker_calls": 0,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for path in (
        Path(__file__),
        *[
            ROOT / "src/reliability/verifier" / n
            for n in (
                "regression.py",
                "accounting.py",
                "validated_run.py",
                "result_parser.py",
                "container.py",
            )
        ],
    ):
        read(path)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "input_sha256": hashes,
                "accounting_guard_commit": "ec918ba",
                "native_records_modified": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))
    print(json.dumps(policy_rows, indent=2))
    print(json.dumps(h1, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
