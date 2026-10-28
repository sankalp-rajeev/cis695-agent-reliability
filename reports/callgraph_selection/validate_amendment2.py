"""Validate stored amendment outputs only; never rebuild or execute source."""
import csv
import json
from collections import Counter

from build_graphs import OUT, digest, write_json
from rebuild_and_resolve import WORK, SYMPY, aggregate, verify_design, verify_original_graphs


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    verify_design()
    hashes = verify_original_graphs()
    manifest = json.loads((WORK / "graph_manifest.json").read_text())
    tasks = read_csv(WORK / "task_resolution.csv")
    names = read_csv(WORK / "changed_symbol_resolution.csv")
    assert len(tasks) == len(manifest) == len({r["instance_id"] for r in tasks}) == 83
    assert {r["instance_id"] for r in tasks} == set(manifest)
    assert len(read_csv(WORK / "verified_patch_manifest.csv")) == 83
    # Per-file verification needs the full (task, file) identity, not the task alone.
    historical_files = {(r["instance_id"], r["path"]): r for r in read_csv(OUT / "draft_sympy_preflight_files.csv")}
    historical_omitted = {(r["instance_id"], r["path"]) for r in read_csv(OUT / "draft_sympy_omissions.csv")
                          if r["rule"] == "largest_first"}
    omitted_keys = set()
    new_diagnostics = []
    for iid, record in manifest.items():
        directory = OUT / record["directory"]
        for filename, sha in record["artifact_sha256"].items():
            assert digest(directory / filename) == sha, (iid, filename)
        if iid not in SYMPY:
            assert record["directory"] == "graphs/" + iid
            continue
        diagnostic = json.loads((directory / "diagnostics.json").read_text())
        row = diagnostic["row"]
        assert row["graph_status"] == "partial"
        assert row["preflight_complete"]
        assert row["preflight_ast_nodes"] <= 10_000_000
        assert row["retained_ast_nodes"] <= 5_000_000
        assert row["graph_runtime_seconds"] < 600
        assert row["ast_parse_passes"] == 1 and row["retained_ast_reuse"] and not row["reparsed_for_indexing"]
        assert 0 < row["indexing_visits"] <= row["retained_ast_nodes"]
        assert row["edge_records"] == row["call_sites"]
        assert row["resolved_edges"] + row["ambiguous_edges"] + row["unresolved_edges"] == row["edge_records"]
        inventory = read_csv(directory / "file_inventory.csv")
        omissions = read_csv(directory / "omitted_files.csv")
        assert len(inventory) == row["python_files"]
        assert row["omitted_files"] == len(omissions)
        assert row["parsed_files"] + len(omissions) == row["python_files"]
        assert row["parse_failures"] == 0
        for item in inventory:
            expected = historical_files[(iid, item["path"])]
            assert int(item["ast_nodes"]) == int(expected["ast_nodes"])
            assert item["source_sha256"] == expected["source_sha256"]
        costs = sorted(inventory, key=lambda r: (-int(r["ast_nodes"]), r["path"]))
        assert [r["path"] for r in omissions] == [r["path"] for r in costs[:len(omissions)]]
        retained = sum(int(r["ast_nodes"]) for r in inventory)
        for item in omissions:
            assert int(item["retained_before"]) == retained
            assert retained > 5_000_000
            retained -= int(item["ast_nodes"])
            assert int(item["retained_after"]) == retained
            omitted_keys.add((iid, item["path"]))
        assert retained == row["retained_ast_nodes"]
        assert all(f["reason"] == "largest_first_retained_ast_quota" for f in diagnostic["parse_and_resource_failures"])
        new_diagnostics.append(row)
    assert omitted_keys == historical_omitted and len(omitted_keys) == 43
    patches = {r["instance_id"]: r for r in read_csv(WORK / "verified_patch_manifest.csv")}
    numerical_keys = ("names_total", "names_resolved", "names_ambiguous", "names_unresolved", "newly_added_names",
                      "excluding_new_total", "excluding_new_resolved", "excluding_new_ambiguous", "excluding_new_unresolved")
    for task in tasks:
        iid = task["instance_id"]
        assert task["resolution_status"].startswith("measured")
        assert task["source_run"] == patches[iid]["source_run"]
        assert task["patch_sha256"] == patches[iid]["patch_sha256"]
        symbols = [r for r in names if r["instance_id"] == iid]
        for symbol in symbols:
            assert symbol["source_run"] == task["source_run"]
        counts = Counter(s["status"] for s in symbols)
        assert len(symbols) == int(task["names_total"])
        assert all(counts[k] == int(task["names_" + k]) for k in ("resolved", "ambiguous", "unresolved"))
        remaining = [s for s in symbols if s["origin"] != "newly_added_name_absent_at_base"]
        counts = Counter(s["status"] for s in remaining)
        assert len(remaining) == int(task["excluding_new_total"])
        assert len(symbols) - len(remaining) == int(task["newly_added_names"])
        assert all(counts[k] == int(task["excluding_new_" + k]) for k in ("resolved", "ambiguous", "unresolved"))
        for key in numerical_keys:
            task[key] = int(task[key])
        for key in ("primary_eligible", "extended_partial_eligible"):
            task[key] = task[key] == "True"
    repositories = [r["repo"] for r in json.loads((OUT / "inputs.json").read_text())["repositories"]]
    expected = aggregate(tasks, repositories)
    summary = json.loads((WORK / "resolution_summary.json").read_text())
    assert expected[:-1] == summary["per_repository"]
    assert expected[-1] == summary["totals"]
    assert summary["selectors_run"] is False and summary["oracle_access"] is False
    assert len(read_csv(WORK / "omission_annotations.csv")) == 43
    assert len(read_csv(WORK / "base_feasibility.csv")) == 83
    inputs = json.loads((WORK / "inputs.json").read_text())
    for path, sha in inputs["output_sha256"].items():
        assert digest(WORK / path) == sha, path
    for filename, sha in inputs["code_sha256"].items():
        assert digest(OUT / filename) == sha, filename
    result = dict(status="passed", tasks=83, symbols=len(names), rebuilt_tasks=sorted(SYMPY),
                  omissions=43, largest_first_matches_committed_preflight=True,
                  original_graphs=hashes, new_graph_statuses=dict(Counter(r["graph_status"] for r in new_diagnostics)),
                  aggregate_rates_verified=True, design_unchanged=True, selectors_run=False)
    write_json(WORK / "validation.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
