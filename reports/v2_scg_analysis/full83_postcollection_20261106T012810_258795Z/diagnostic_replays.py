"""Replay saved strings through unchanged parser; never imports benchmark code."""
from collections import Counter
import json
from pathlib import Path
import re
import sys


def main(out):
    config = json.loads((out / "analysis_configuration.json").read_text())
    sys.path.insert(0, str(Path(config["review"]) / "src"))
    from reliability.verifier.container import _parse_pytest

    pairs = json.loads((Path(config["results"]) / "results.json").read_text())
    ansi = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    replay, missing_pytest, shadow = [], [], []
    for pair in pairs:
        for arm, row in pair["arms"].items():
            if row["signal"] == "NOT_AVAILABLE" and row["selected"]:
                record = {"instance_id": pair["instance_id"], "arm": arm,
                          "preserved_native_signal": row["signal"], "phases": []}
                for call in row["calls"][:2]:
                    run = call["run"]
                    raw_path = Path(run["evidence_files"]["runner.raw"])
                    text = raw_path.read_text()
                    native = _parse_pytest(text, tuple(call["requested"]))
                    decolored = _parse_pytest(ansi.sub("", text), tuple(call["requested"]))
                    record["phases"].append({"patched": call["patched"], "raw_path": str(raw_path),
                        "raw_adapter_cases": len(run["raw_results"]),
                        "unchanged_parser_exact_admissions": {k: v.value for k, v in native.items()},
                        "diagnostic_ansi_removed_exact_admissions": {k: v.value for k, v in decolored.items()},
                        "diagnostic_does_not_change_stored_results_or_verdict": True,
                        "note": run["note"], "runner_errors": run["infrastructure_errors"]})
                    if "No module named pytest" in text:
                        missing_pytest.append({"instance_id": pair["instance_id"], "arm": arm,
                                               "patched": call["patched"], "raw_path": str(raw_path),
                                               "exact_diagnostic": "/opt/miniconda3/envs/testbed/bin/python: No module named pytest"})
                replay.append(record)
            if row["signal"] == "FAIL":
                recorded = row.get("shadow", {})
                shadow.append({"instance_id": pair["instance_id"], "arm": arm,
                               "isolation": recorded.get("isolation"),
                               "predictions": recorded.get("predictions"),
                               "native_signal_unchanged": row["signal"]})
    summary = {"records": replay, "missing_pytest": missing_pytest,
               "missing_pytest_unique_tasks": sorted({r["instance_id"] for r in missing_pytest}),
               "shadow_classifier_unavailable": shadow,
               "shadow_prediction_counts": dict(Counter(p["prediction"] for r in shadow for p in r["predictions"] or [])),
               "benchmark_tests_executed": 0, "stored_verdicts_changed": False}
    with (out / "parser_and_environment_diagnostics.json").open("x") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("missing pytest tasks", summary["missing_pytest_unique_tasks"])
    print("shadow predictions", summary["shadow_prediction_counts"])
    print("ANSI-sensitive native admission records", [r["instance_id"] + ":" + r["arm"] for r in replay
          if any(p["diagnostic_ansi_removed_exact_admissions"] != p["unchanged_parser_exact_admissions"] for p in r["phases"])])


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
