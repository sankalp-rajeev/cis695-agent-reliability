#!/usr/bin/env python3
"""Run native Fix 1 scoring over immutable V2 captures, with no executor I/O."""

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from reliability.verifier.container import run_from_capture
from reliability.verifier.regression import (
    RegressionConfig,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    completeness_of,
    concrete_comparison,
    run_regression,
)
from reliability.verifier.result_parser import parse_capture
from reliability.verifier.selection import Selection, TestRunner


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_csv(path, rows, fields=None):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class StoredExecutor:
    """Use recorded initial calls and identity-compatible confirmations only."""

    def __init__(self, calls):
        self.calls = calls
        self.patch_calls = 0
        self.unavailable_confirmations = []

    def run(self, tests, *, patched, timeout_s):
        if not patched:
            return self.calls[0][1]
        self.patch_calls += 1
        if self.patch_calls == 1:
            return self.calls[1][1]
        wanted = set(tests)
        for metadata, result in self.calls[2:]:
            covered = set(result.by_id()) | {
                r.test_id
                for r in result.raw_results
                if len(result.raw_id_map.get(r.test_id, ())) == 1
            }
            if wanted <= covered:
                # Keep the true recorded requested_tests and full raw scope.
                # No new confirmation run or narrower capture is invented.
                return result
        self.unavailable_confirmations.append(list(tests))
        return RunResult(
            results=tuple(TestResult(t, TestStatus.NOT_RUN) for t in tests),
            requested_tests=tuple(tests),
            note="stored confirmation unavailable; no execution attempted",
            infrastructure_errors=("stored confirmation unavailable",),
        )


def main(args):
    assert not args.output.exists()
    hashes = {}

    def read(path):
        raw = path.read_bytes()
        hashes[str(path)] = sha(raw)
        return raw

    expected = json.loads(read(args.phase2 / "input_manifest.json"))["input_sha256"]
    with (args.phase2 / "parser_replay.csv").open() as stream:
        reference = {r["instance_id"]: r for r in csv.DictReader(stream)}
    read(args.phase2 / "parser_replay.csv")
    spec = importlib.util.spec_from_file_location("phase2_reference", args.reference_parser)
    phase2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(phase2)
    read(args.reference_parser)
    metas = json.loads(read(args.frozen / "tasks.json"))
    task_rows, call_rows, fail_rows = [], [], []
    capture_count = 0
    recovered, recovered_na, retained = [], [], []
    for meta in metas:
        task = meta["instance_id"]
        runner = TestRunner(meta["runner"]["name"], "frozen stored runner")
        path = args.results / "tasks" / task / "v2/result.json"
        data = read(path)
        assert sha(data) == expected[str(path)]
        native = json.loads(data)
        tests = tuple(native.get("selected_tests") or ())
        assert list(tests) == json.loads(read(args.frozen / meta["selections"]["v2"]))["tests"]
        calls = []
        for index, call in enumerate(native.get("calls", [])):
            run = call["run"]
            files = {}
            for name, filename in run["evidence_files"].items():
                raw = read(Path(filename))
                assert sha(raw) == run["evidence_sha256"][name]
                files[name] = raw
                capture_count += 1
            raw = files["runner.raw"]
            # Compare every observed identity/status/flavor/kind with Phase 2,
            # independently of the native scorer's final task disposition.
            assert parse_capture(
                raw.decode("utf-8", "replace"), runner.name
            ) == phase2.parse_capture(raw.decode("utf-8", "replace"), runner.name), (task, index)
            selected = tuple(call.get("requested", run.get("requested_tests", tests)))
            assert set(selected) <= set(tests)
            # These legacy errors were parser/event-derived, so re-evaluate
            # them from immutable raw bytes and events with the native parser.
            preserved = tuple(
                e
                for e in run.get("infrastructure_errors", [])
                if not (
                    e.startswith("runner batch ")
                    or e in ("unexplained nonzero runner exit", "unfinished runner batch")
                )
            )
            result = run_from_capture(
                runner,
                selected,
                runner_log=raw,
                raw_stderr=files.get("stderr.raw", b""),
                raw_stdout=files.get("stdout.raw", b""),
                events=tuple(run.get("events", [])),
                timed_out=run.get("timed_out", False),
                infrastructure_errors=preserved,
                evidence_files=run["evidence_files"],
                evidence_sha256=run["evidence_sha256"],
            )
            calls.append((call, result))
            call_rows.append(
                {
                    "instance_id": task,
                    "tree": "patched" if call["patched"] else "base",
                    "call_index": index,
                    "scope": "initial" if index < 2 else "confirmation",
                    "requested_families": len(selected),
                    "admitted_families": sum(
                        r.status not in (TestStatus.NOT_RUN, TestStatus.TIMEOUT)
                        for r in result.results
                    ),
                    "raw_concrete_and_error_ids": len(result.raw_results),
                    "evidence_complete": result.evidence_complete,
                    "infrastructure_errors": ";".join(result.infrastructure_errors),
                    "evidence_path": run["evidence_files"]["runner.raw"],
                }
            )
        executor = StoredExecutor(calls)
        report = run_regression(task, Selection(tests=tests), executor, RegressionConfig())
        initial_complete = (
            completeness_of(tests, calls[0][1], calls[1][1])[0] == "COMPLETE" if calls else False
        )
        assert initial_complete == (
            reference[task]["parser_only_complete_skip_compatible"] == "True"
        ), (task, "initial completeness differs from Phase 2")
        if native["signal"] == "INCOMPLETE" and report.completeness == "COMPLETE":
            recovered.append(task)
        if native["signal"] == "NOT_AVAILABLE" and report.signal in (Signal.PASS, Signal.FAIL):
            recovered_na.append(task)
        if native["signal"] == "FAIL":
            assert report.signal is Signal.FAIL, ("native FAIL disappeared", task, report.signal)
            retained.append(task)
            base, patched = concrete_comparison(tests, calls[0][1], calls[1][1])
            observed = []
            for test in report.regressions:
                b, p = base.get(test), patched.get(test)
                if b and p and b.status is TestStatus.PASSED and p.status is TestStatus.FAILED:
                    observed.append(test)
                    evidence = []
                    for _, run in calls[:2]:
                        filename = run.evidence_files["runner.raw"]
                        parsed = parse_capture(
                            read(Path(filename)).decode("utf-8", "replace"), runner.name
                        )
                        raw_id = next(
                            r.test_id
                            for r in run.raw_results
                            if r.test_id == test or run.raw_id_map.get(r.test_id) == (test,)
                        )
                        evidence.append(filename + ":" + str(parsed[raw_id]["line"]))
                    fail_rows.append(
                        {
                            "instance_id": task,
                            "concrete_test_id": test,
                            "base_outcome": b.status.value,
                            "patched_outcome": p.status.value,
                            "native_FAIL_retained": True,
                            "stored_confirmation_calls": len(calls[2:]),
                            "base_evidence": evidence[0],
                            "patched_evidence": evidence[1],
                        }
                    )
            assert observed, (task, "lost concrete base-PASS patched-FAIL evidence")
        task_rows.append(
            {
                "instance_id": task,
                "frozen_native_signal": native["signal"],
                "Fix1_native_rescore_signal": report.signal.value,
                "Fix1_completeness": report.completeness,
                "initial_pair_complete_matches_phase2": True,
                "concrete_outcomes": len(report.outcomes),
                "regressions": len(report.regressions),
                "stored_confirmations_used": len(report.confirmations)
                - len(executor.unavailable_confirmations),
                "unavailable_confirmation_requests": json.dumps(executor.unavailable_confirmations),
                "recovered_INCOMPLETE": task in recovered,
                "binary_from_NOT_AVAILABLE": task in recovered_na,
                "retained_frozen_FAIL": task in retained,
                "native_record": str(path),
            }
        )
        print(task, report.signal.value, report.completeness, flush=True)
    assert len(recovered) == 9, (len(recovered), recovered)
    assert len(recovered_na) == 2, (len(recovered_na), recovered_na)
    assert len(retained) == 6
    assert capture_count == 676
    expected_recovered = {
        r["instance_id"]
        for r in reference.values()
        if r["parser_only_recovered_INCOMPLETE"] == "True"
    }
    expected_na = {
        r["instance_id"]
        for r in reference.values()
        if r["parser_only_binary_evidence_from_NOT_AVAILABLE"] == "True"
    }
    assert set(recovered) == expected_recovered and set(recovered_na) == expected_na
    args.output.mkdir(parents=True)
    write_csv(args.output / "task_rescore.csv", task_rows)
    write_csv(args.output / "call_rescore.csv", call_rows)
    write_csv(args.output / "native_FAIL_evidence.csv", fail_rows)
    write_csv(
        args.output / "recovery_chart.csv",
        [
            {"metric": "recovered_INCOMPLETE", "tasks": len(recovered), "frozen_denominator": 39},
            {
                "metric": "binary_evidence_from_NOT_AVAILABLE",
                "tasks": len(recovered_na),
                "frozen_denominator": 13,
            },
            {"metric": "native_FAIL_retained", "tasks": len(retained), "frozen_denominator": 6},
        ],
    )
    summary = {
        "scope": "OFFLINE NATIVE FIX 1 RESCORE ONLY",
        "recovered_INCOMPLETE": recovered,
        "binary_from_NOT_AVAILABLE": recovered_na,
        "native_FAIL_retained": retained,
        "all_initial_pair_completeness_matches_phase2": True,
        "all_169_call_parsers_match_phase2": True,
        "verified_V2_capture_files": capture_count,
        "native_rescore_signal_counts": dict(
            Counter(r["Fix1_native_rescore_signal"] for r in task_rows)
        ),
        "new_regression_candidates_without_stored_confirmation": [
            r["instance_id"] for r in task_rows if r["unavailable_confirmation_requests"] != "[]"
        ],
        "native_verdict_files_modified": False,
        "Docker_calls": 0,
        "benchmark_runs": 0,
        "policy": "historical skip-compatible; XFAIL/XPASS policy separation remains Fix 2",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for path in [
        Path(__file__),
        *(
            args.repo / "src/reliability/verifier" / n
            for n in ("result_parser.py", "container.py", "regression.py")
        ),
        args.repo / "reports/next_phases/phase4_plan.md",
    ]:
        read(path)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "input_sha256": hashes,
                "plan_commit": "c4d17c8",
                "labels_read": False,
                "source_execution": "native parser/scorer only; no benchmark source or executor I/O",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--phase2", type=Path, required=True)
    ap.add_argument("--frozen", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--reference-parser", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    main(ap.parse_args())
