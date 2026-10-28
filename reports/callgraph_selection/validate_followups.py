"""Stored-output checks for follow-ups; no tests, graph rebuilds or repo execution."""
import csv
import json
from collections import Counter
from pathlib import Path

from followup_analysis import OUT, BUCKETS, verify_baseline
from build_graphs import digest, write_json


def read_csv(name):
    with (OUT / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def require(value, reason):
    if not value:
        raise ValueError(reason)


def main():
    verify_baseline()
    manifest = json.loads((OUT / "followup_inputs.json").read_text())
    for name, expected in manifest["code_sha256"].items():
        require(digest(OUT / name) == expected, "follow-up code hash mismatch")
    for name, expected in manifest["output_sha256"].items():
        require(digest(OUT / name) == expected, "follow-up output hash mismatch")
    require(digest(OUT / "design.md") == manifest["current_design_sha256"], "draft design changed")
    baseline = {r["instance_id"]: r for r in read_csv("base_feasibility.csv")}
    calls = read_csv("call_resolution_by_task.csv")
    stops = read_csv("sympy_limit_stops.csv")
    require(len(calls) == 79 and len(stops) == 4, "wrong completed/limited denominators")
    require({r["instance_id"] for r in calls + stops} == set(baseline), "missing/duplicate task")
    counts = Counter()
    for row in calls:
        original = baseline[row["instance_id"]]
        require(original["graph_status"] != "resource_limited", "resource stop classified as zero")
        require(sum(int(row[key]) for key in BUCKETS) == int(row["classified_call_sites"]) == int(original["edge_records"]),
                "boundary buckets do not partition original call sites")
        require(row["internal_resolved"] == original["resolved_edges"], "resolved baseline changed")
        counts.update({key: int(row[key]) for key in BUCKETS})
    summary = json.loads((OUT / "followup_summary.json").read_text())
    require(dict(counts) == summary["total_calls"], "call summary mismatch")
    for stop in stops:
        original = baseline[stop["instance_id"]]
        require(int(stop["limit"]) == 5_000_000, "limit changed")
        require(stop["observed_stop_counter"] == original["ast_nodes"], "replay mismatch")
        require(int(stop["nodes_before_file"]) + int(stop["nodes_inspected_in_stopping_file"]) == int(stop["observed_stop_counter"]),
                "counter decomposition mismatch")
        require(int(stop["file_ast_nodes"]) >= int(stop["nodes_inspected_in_stopping_file"]), "invalid full-file count")
    partials = read_csv("partial_graph_files.csv")
    partial_ids = {r["instance_id"] for r in partials}
    require(len(partials) == 77 and len(partial_ids) == 23, "partial file list incomplete")
    require(partial_ids == {iid for iid, r in baseline.items() if r["graph_status"] == "partial"}, "wrong partial tasks")
    for iid in partial_ids:
        expected = json.loads((OUT / "graphs" / iid / "diagnostics.json").read_text())["parse_and_resource_failures"]
        listed = [r for r in partials if r["instance_id"] == iid]
        require(Counter((r["path"], r["reason"]) for r in listed) == Counter((r["path"], r["reason"]) for r in expected),
                "partial reasons differ from stored diagnostics")
    symbols = read_csv("changed_symbol_origins.csv")
    require(len(symbols) == 64, "changed-symbol inventory changed")
    require(sum(r["origin"] == "newly_added_name_absent_at_base" for r in symbols) == 5, "new-name count mismatch")
    for rate in read_csv("changed_symbol_rates.csv"):
        subset = [s for s in symbols if (rate["provenance"] == "all" or s["provenance"] == rate["provenance"])
                  and (rate["exclude_newly_added"] != "True" or s["origin"] != "newly_added_name_absent_at_base")]
        grouped = Counter(s["status"] for s in subset)
        require(len(subset) == int(rate["total"]), "symbol denominator mismatch")
        for status in ("resolved", "ambiguous", "unresolved"):
            require(grouped[status] == int(rate[status]), "symbol rate count mismatch")
        require(abs(grouped["resolved"] / len(subset) - float(rate["resolution_rate"])) < 1e-10, "symbol rate mismatch")
    result = dict(status="passed", original_graph_artifacts_unchanged=True,
                  tasks=83, classified_tasks=79, resource_stops=4, partial_graphs=23, partial_files=77,
                  changed_names=64, newly_added_names=5, call_counts=dict(counts),
                  graph_rebuild=False, benchmark_execution=False, oracle_analysis=False,
                  validator_sha256=digest(Path(__file__)),
                  followup_inputs_sha256=digest(OUT / "followup_inputs.json"))
    write_json(OUT / "followup_validation.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
