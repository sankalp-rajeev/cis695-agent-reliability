#!/usr/bin/env python3
"""Offline Fix 2 replay of all frozen V2 captures under policies C and S."""

import argparse
import csv
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from phase3_fix1_rescore import StoredExecutor, sha, write_csv
from reliability.verifier.container import run_from_capture
from reliability.verifier.regression import (
    RegressionConfig,
    Signal,
    TestStatus,
    concrete_comparison,
    run_regression,
)
from reliability.verifier.result_parser import parse_capture
from reliability.verifier.selection import Selection, TestRunner

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(
    "/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z"
)


def main(args):
    assert not args.output.exists()
    hashes = {}

    def read(path):
        data = path.read_bytes()
        hashes[str(path)] = sha(data)
        return data

    phase2 = ROOT / "reports/next_phases/phase2_incomplete_causes/input_manifest.json"
    expected = json.loads(read(phase2))["input_sha256"]
    frozen = DATA / "paired_frozen"
    results = DATA / "full_83_20261105T231219_643682Z/results"
    tasks, transitions, special, fails = [], [], [], []
    captures = 0
    for meta in json.loads(read(frozen / "tasks.json")):
        task = meta["instance_id"]
        native_path = results / "tasks" / task / "v2/result.json"
        raw = read(native_path)
        assert sha(raw) == expected[str(native_path)]
        native = json.loads(raw)
        tests = tuple(native.get("selected_tests") or ())
        assert list(tests) == json.loads(read(frozen / meta["selections"]["v2"]))["tests"]
        runner = TestRunner(meta["runner"]["name"], "immutable stored capture")
        calls, parsed_calls = [], []
        for call in native.get("calls", []):
            run = call["run"]
            files = {name: read(Path(path)) for name, path in run["evidence_files"].items()}
            captures += len(files)
            assert all(sha(data) == run["evidence_sha256"][name] for name, data in files.items())
            preserved = tuple(
                e
                for e in run.get("infrastructure_errors", [])
                if not (
                    e.startswith("runner batch ")
                    or e in ("unexplained nonzero runner exit", "unfinished runner batch")
                )
            )
            requested = tuple(call.get("requested", run.get("requested_tests", tests)))
            result = run_from_capture(
                runner,
                requested,
                runner_log=files["runner.raw"],
                raw_stdout=files.get("stdout.raw", b""),
                raw_stderr=files.get("stderr.raw", b""),
                events=tuple(run.get("events", [])),
                timed_out=run.get("timed_out", False),
                infrastructure_errors=preserved,
                evidence_files=run["evidence_files"],
                evidence_sha256=run["evidence_sha256"],
            )
            calls.append((call, result))
            parsed_calls.append(
                parse_capture(
                    (files["runner.raw"] + files.get("stderr.raw", b"")).decode("utf-8", "replace"),
                    runner.name,
                )
            )
        row = {"instance_id": task, "frozen_native_signal": native["signal"]}
        for policy in ("C", "S"):
            config = RegressionConfig()
            if "skip_compatible" in RegressionConfig.__dataclass_fields__:
                config = replace(config, skip_compatible=policy == "C")
            executor = StoredExecutor(calls)
            report = run_regression(task, Selection(tests=tests), executor, config)
            signal = report.signal.value
            completeness = report.completeness
            # Fix 1 has no strict-policy configuration. Its strict counterpart
            # blocks any normalized SKIPPED evidence, including old XFAIL.
            if args.legacy and policy == "S" and signal == "PASS":
                runs = [r for _, r in calls[:2]] + list(report.confirmations)
                if any(
                    r.status is TestStatus.SKIPPED
                    for run in runs
                    for r in (*run.results, *run.raw_results)
                ):
                    signal = "INCOMPLETE"
                    completeness = "INCOMPLETE_CONFIRMED"
            row[f"Policy_{policy}"] = signal
            row[f"Policy_{policy}_completeness"] = completeness
            row[f"Policy_{policy}_outcomes"] = json.dumps(report.summary, sort_keys=True)
            row[f"Policy_{policy}_unavailable_confirmations"] = json.dumps(
                executor.unavailable_confirmations
            )
            if native["signal"] == "FAIL":
                assert report.signal is Signal.FAIL, (task, policy, "native FAIL lost")
            if policy == "C" and calls:
                base, patch = concrete_comparison(tests, calls[0][1], calls[1][1])
                for tid, b in base.items():
                    p = patch.get(tid)
                    if not b or not p:
                        continue
                    evidence = []
                    for index, run in enumerate([calls[0][1], calls[1][1]]):
                        rid = next(
                            (
                                r.test_id
                                for r in run.raw_results
                                if r.test_id == tid or run.raw_id_map.get(r.test_id) == (tid,)
                            ),
                            None,
                        )
                        observation = parsed_calls[index].get(rid, {})
                        evidence.append(
                            run.evidence_files["runner.raw"] + ":" + str(observation.get("line", 0))
                        )
                    item = {
                        "instance_id": task,
                        "concrete_test_id": tid,
                        "base": b.status.value,
                        "patched": p.status.value,
                        "outcome": report.outcomes[tid].value,
                        "base_evidence": evidence[0],
                        "patched_evidence": evidence[1],
                    }
                    if b.status is TestStatus.PASSED and p.status is TestStatus.ERROR:
                        transitions.append(item)
                    if (
                        native["signal"] == "FAIL"
                        and b.status is TestStatus.PASSED
                        and p.status is TestStatus.FAILED
                    ):
                        fails.append(item)
                for index, (_, run) in enumerate(calls[:2]):
                    for r in run.raw_results:
                        if r.status.value in ("xfail", "xpass"):
                            special.append(
                                {
                                    "instance_id": task,
                                    "tree": "base" if index == 0 else "patched",
                                    "raw_id": r.test_id,
                                    "status": r.status.value,
                                    "selected_ids": json.dumps(run.raw_id_map.get(r.test_id, ())),
                                    "evidence": run.evidence_files["runner.raw"]
                                    + ":"
                                    + str(parsed_calls[index][r.test_id]["line"]),
                                }
                            )
        tasks.append(row)
    assert len(tasks) == 83 and captures == 676
    assert len({r["instance_id"] for r in fails}) == 6
    assert len(transitions) == 5 and len({r["instance_id"] for r in transitions}) == 1
    summary = {
        "scope": "offline stored-capture rescore; no benchmark execution",
        "policies": {p: dict(Counter(r[f"Policy_{p}"] for r in tasks)) for p in ("C", "S")},
        "native_FAIL_retained": 6,
        "PASS_to_ERROR_transitions": len(transitions),
        "PASS_to_ERROR_tasks": sorted({r["instance_id"] for r in transitions}),
        "verified_capture_files": captures,
        "Docker_calls": 0,
        "benchmark_runs": 0,
        "labels_read": False,
        "legacy": args.legacy,
    }
    if args.before:
        before = {r["instance_id"]: r for r in csv.DictReader(args.before.open())}
        for row in tasks:
            for policy in ("C", "S"):
                old = before[row["instance_id"]][f"Policy_{policy}"]
                row[f"Policy_{policy}_before"] = old
                row[f"Policy_{policy}_changed"] = old != row[f"Policy_{policy}"]
        summary["changed_verdict_tasks"] = {
            p: [r["instance_id"] for r in tasks if r[f"Policy_{p}_changed"]] for p in ("C", "S")
        }
        summary["changed_verdict_counts"] = {
            p: len(summary["changed_verdict_tasks"][p]) for p in ("C", "S")
        }
        read(args.before)
        assert all(r["outcome"] == "REGRESSION_ERROR" for r in transitions)
    args.output.mkdir(parents=True)
    write_csv(args.output / "task_rescore.csv", tasks)
    write_csv(args.output / "regression_error_evidence.csv", transitions)
    write_csv(args.output / "native_FAIL_evidence.csv", fails)
    if special:
        write_csv(args.output / "XFAIL_XPASS_evidence.csv", special)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for path in [
        Path(__file__),
        ROOT / "scripts/phase3_fix1_rescore.py",
        *[
            Path(__import__("reliability.verifier." + module, fromlist=[""]).__file__)
            for module in ("regression", "result_parser", "container")
        ],
    ]:
        read(path)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "input_sha256": hashes,
                "native_records_modified": False,
                "plan_rule": "ff53e21, committed and pushed before Fix 2; no Fix 3 implementation",
                "comparison_source_commit": "f53d67a38c7b7dae26be0e73c6f06fc793afd84f",
                "confirmation_rule": "Only stored identity-compatible assertion-regression confirmations; REGRESSION_ERROR observations have no new confirmation. Fix 8 is pending.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--legacy", action="store_true")
    main(parser.parse_args())
