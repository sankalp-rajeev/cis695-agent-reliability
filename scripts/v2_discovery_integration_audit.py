"""Audit fresh A/B captures and replay unchanged adapters/policies, without test execution."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from reliability.verifier.decision import BaselinePolicy, Evidence, FullPolicy
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
    evidence_from_record,
)
from reliability.verifier.regression import RegressionConfig, run_from_dict, run_regression
from reliability.verifier.run import signal_from_regression
from reliability.verifier.selection import Selection
from v2_discovery_experiment import save, sha


def audit(comparison, out):
    captures = json.loads((comparison / "docker_results.json").read_text())
    offline = json.loads((comparison / "offline.json").read_text())
    selections = {r["instance_id"]: r for r in offline["tasks"]}
    assert len(captures) == 12
    assert len({r["instance_id"] for r in captures}) == 3
    out.mkdir(parents=True, exist_ok=False)
    rows, source_hashes, raw_proofs = [], {}, {}
    for row in captures:
        iid, arm, pair = row["instance_id"], row["arm"], row["pair"]
        selected = selections[iid]
        tests = tuple(selected["before" if arm == "A" else "after"])
        calls = row["calls"][:row["initial_calls"]]

        class Replay:
            def __init__(self, observations):
                self.position = 0
                self.calls = observations

            def run(self, tests, *, patched, timeout_s):
                observed = self.calls[self.position]
                self.position += 1
                assert patched is observed["patched"]
                assert tuple(tests) == tuple(observed["run"]["requested_tests"])
                assert timeout_s == 300
                return run_from_dict(observed["run"])

        replay = Replay(calls)
        report = run_regression(iid, Selection(tests=tests), replay, RegressionConfig())
        assert replay.position == len(calls)
        assert report.signal.value == row["signal"]
        assert report.completeness == row["completeness"] and report.summary == row["summary"]
        assert list(report.regressions) == row["regressions"]
        assert not (row["signal"] == "PASS" and row["completeness"] != "COMPLETE")
        for call in row["calls"]:
            for name, path in call["run"]["evidence_files"].items():
                actual = sha(Path(path).read_bytes())
                assert actual == call["run"]["evidence_sha256"][name]
                raw_proofs[path] = actual
        environment = json.loads((comparison / "docker" / iid / f"pair{pair}_{arm}" / "environment.json").read_text())
        for path, digest in environment["hashes"].items():
            key = iid + ":" + path
            assert key not in source_hashes or source_hashes[key] == digest
            source_hashes[key] = digest
        regression = signal_from_regression(report)
        regression.findings["superseded_shadow"] = row["shadow"]
        evidence = Evidence(regression=regression.outcome)
        decision = FullPolicy().decide(evidence)

        def absent(kind):
            return SignalRecord.absent(kind, SignalAbsence.DISABLED,
                                       "V2-only discovery validation; this stage was not executed")

        patch_hash = environment["patch_sha256"]
        record = VerificationRecord(
            instance_id=iid, experiment_id="v2_discovery_validation", verifier_config="full",
            patch_sha256="sha256:" + patch_hash, integrity=absent(SignalKind.INTEGRITY),
            regression=regression, static=absent(SignalKind.STATIC),
            reproduction=absent(SignalKind.REPRODUCTION),
            reproduction_generator={"generator": {"model_id": "NOT_INVOKED_V2_ONLY_VALIDATION"}},
            selected_tests=tests, selection_runner=selected["runner"]["name"],
            decision=DecisionEntry.from_record(decision), verified_at=datetime.now(UTC).isoformat())
        path = out / "records" / iid / f"pair{pair}_{arm}.json"
        record.write(path)
        restored = VerificationRecord.read(path)
        assert evidence_from_record(restored).regression == regression.outcome
        if row["signal"] == "INCOMPLETE":
            assert restored.regression.absence is SignalAbsence.INCOMPLETE
            assert decision.decision.value == "FLAG"
        predictions = row["shadow"].get("predictions", [row["shadow"]])
        assert all(p["shadow_mode"] is True for p in predictions)
        base, patched = calls[0]["run"], calls[1]["run"]
        raw_base = {r["test_id"]: r["status"] for r in base["raw_results"]}
        raw_patched = {r["test_id"]: r["status"] for r in patched["raw_results"]}
        base_coverage = {t for ids in base["raw_id_map"].values() for t in ids}
        patch_coverage = {t for ids in patched["raw_id_map"].values() for t in ids}
        prior = [r for r in rows if r["instance_id"] == iid]
        assert all(r["raw_base"] == raw_base and r["raw_patched"] == raw_patched for r in prior)
        rows.append({"instance_id": iid, "pair": pair, "arm": arm, "selected": len(tests),
                     "signal": row["signal"], "completeness": row["completeness"],
                     "missing_base_raw_evidence": sorted(set(tests) - base_coverage),
                     "missing_patched_raw_evidence": sorted(set(tests) - patch_coverage),
                     "base_timeouts": sum(r["status"] == "timeout" for r in base["results"]),
                     "patched_timeouts": sum(r["status"] == "timeout" for r in patched["results"]),
                     "raw_base": raw_base, "raw_patched": raw_patched,
                     "initial_runner_errors": base["infrastructure_errors"] + patched["infrastructure_errors"],
                     "regressions": row["regressions"], "regression_wall_s": row["regression_wall_s"],
                     "shadow_predictions": [p["prediction"] for p in predictions],
                     "full_V2_only_decision": decision.decision.value,
                     "baseline_V2_only_decision": BaselinePolicy().decide(evidence).decision.value,
                     "native_verdict_unchanged_by_shadow": True,
                     "neutral_roundtrip_verified": True})
    for iid in {r["instance_id"] for r in rows}:
        group = [r for r in rows if r["instance_id"] == iid]
        assert {(r["pair"], r["arm"]) for r in group} == {(1, "A"), (1, "B"), (2, "B"), (2, "A")}
        assert len({tuple(r["regressions"]) for r in group}) == 1
    save(out / "results.json", rows)
    with (out / "summary.csv").open("x", newline="") as stream:
        fields = [k for k in rows[0] if k not in ("raw_base", "raw_patched")]
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, list) else v
                             for k, v in row.items() if k in fields})
    save(out / "validation.json", {"arms": len(rows), "tasks": 3,
                                    "raw_files_hash_verified": len(raw_proofs), "raw_sha256": raw_proofs,
                                    "executed_test_ids_and_outcomes_unchanged": True,
                                    "regressions_preserved": True, "incomplete_PASS_count": 0,
                                    "shadow_only": True, "policy_and_neutral_roundtrips_verified": True,
                                    "source_sha256": source_hashes,
                                    "limitation": "Same local image IDs as prior audit, selected/changed source verified; original historical full-image equivalence remains unproven."})
    print(json.dumps({"arms": len(rows), "raw_files_verified": len(raw_proofs), "passed": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit(args.comparison, args.out)
