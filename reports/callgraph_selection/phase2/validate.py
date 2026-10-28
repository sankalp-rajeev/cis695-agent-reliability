"""Validate frozen selector artifacts; no new graph, selection or benchmark run."""
from __future__ import annotations

import csv
import gzip
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from inputs import HERE, CG, ROOT, DESIGN_COMMIT, sha, dump, Registry, base_test_ids, stored_selections
from callgraph_selector import VARIANTS, DEPTHS, BUDGETS, rank_key
from run import verify_freeze, finalize_outputs
from analysis import read_csv, summarize, criteria


def validate():
    frozen = verify_freeze()
    inputs = json.loads((HERE / "inputs.json").read_text())
    assert frozen["design_commit"] == inputs["design_commit"] == DESIGN_COMMIT
    actual_design = (CG / "design.md").read_bytes()
    committed = subprocess.run(["git", "show", DESIGN_COMMIT + ":reports/callgraph_selection/design.md"],
                               cwd=ROOT, check=True, capture_output=True).stdout
    assert actual_design == committed
    for filename, expected in inputs["code_sha256"].items():
        assert sha((ROOT / filename).read_bytes()) == expected, filename
    for filename, expected in inputs["input_sha256"].items():
        assert sha(Path(filename).read_bytes()) == expected, filename
    eligibility = json.loads((HERE / "eligibility.json").read_text())
    ef = json.loads((HERE / "eligibility_freeze.json").read_text())
    assert ef["frozen_before_selectors"]
    assert ef["sha256"] == sha((HERE / "eligibility.json").read_bytes()) == inputs["eligibility_sha256"]
    eligible = {r["instance_id"]: r for r in eligibility["tasks"]}
    assert len(eligible) == 83 and len(eligibility["historical_19"]) == 19
    assert eligibility["c3_primary_eligible"] == sorted(iid for iid, r in eligible.items()
        if r["v2_outcome"] == "NOT_AVAILABLE" and r["stratum"] == "PRIMARY_COMPLETE")
    before = json.loads((HERE / "resume_state.json").read_text())
    for item in before["initial_entries"]:
        if "/phase2/" not in item["path"] and item["sha256"]:
            assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"], item["path"]
    snapshot = stored_selections((ROOT / "reports/failure_analysis/extracted.json").read_text())
    acquisition = json.loads((CG / "inputs.json").read_text())
    registry = Registry()
    base_ids = {r["instance_id"]: set(base_test_ids(r, registry)[0]) for r in acquisition["tasks"]}
    ranked = {}
    candidate_rows = 0
    with gzip.open(HERE / "ranked_outputs.jsonl.gz", "rt") as stream:
        for line in stream:
            record = json.loads(line)
            iid, strategy, variant, depth = (record[k] for k in ("instance_id", "strategy", "edge_variant", "depth"))
            assert variant in VARIANTS and depth in DEPTHS
            key = (iid, strategy, variant, depth)
            assert key not in ranked
            candidates = record["candidates"]
            ranked[key] = record
            candidate_rows += len(candidates)
            if strategy in {"A", "C"}:
                assert iid in eligibility["historical_19"]
                original = snapshot[iid]["selected_tests"]
                if strategy == "A":
                    assert [c["test_id"] for c in candidates] == original
                else:
                    assert Counter(c["test_id"] for c in candidates) == Counter(original)
            if strategy in {"B", "C"}:
                assert candidates == sorted(candidates, key=lambda c: rank_key(c, strategy))
            for c in candidates:
                assert c["graph_status"] in {"reachable", "mapped_unreachable", "unmappable"}
                if c["graph_status"] == "unmappable":
                    assert c["specificity_score"] is c["score_numerator"] is c["score_denominator"] is c["directly_called_seeds"] is c["minimum_distance"] is None
                elif c["graph_status"] == "mapped_unreachable":
                    assert c["specificity_score"] == c["score_numerator"] == c["directly_called_seeds"] == 0
                    assert c["minimum_distance"] is None
                else:
                    assert c["specificity_score"] > 0 and 1 <= c["minimum_distance"] <= depth
                if strategy == "B":
                    assert c["test_id"] in base_ids[iid]
                    assert c["graph_status"] == "reachable"
    rows = read_csv(HERE / "per_task.csv")
    assert len(rows) == 83 * 2 * 3 * 6 + 19 * 2 * 3 * 6 * 2
    for row in rows:
        key = (row["instance_id"], row["strategy"], row["edge_variant"], int(row["depth"]))
        record = ranked.get(key)
        assert row["stratum"] == eligible[row["instance_id"]]["stratum"]
        if record is None:
            assert row["selected_count"] == "" and row["outcome"] != "EMPTY_REACHABILITY"
            continue
        candidates = record["candidates"]
        chosen = candidates if row["budget"] == "ALL" else candidates[:int(row["budget"])]
        assert len(chosen) == int(row["selected_count"])
        assert len(candidates) == int(row["unbudgeted_count"])
        for status in ("reachable", "mapped_unreachable", "unmappable"):
            assert int(row[status + "_candidate_count"]) == sum(c["graph_status"] == status for c in candidates)
            assert int(row[status + "_selected_count"]) == sum(c["graph_status"] == status for c in chosen)
        for d in DEPTHS:
            assert int(row[f"distance_{d}_selected_count"]) == sum(c["minimum_distance"] == d for c in chosen)
    full_counts, group_counts = Counter(), Counter()
    with (HERE / "per_test_provenance.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            assert row["edge_variant"] in VARIANTS and row["strategy"] in {"B", "C"}
            if row["record_type"] != "FULL_PATH":
                continue
            rank = int(row["rank"])
            assert rank <= 25
            nodes = json.loads(row["path_nodes"])
            calls = json.loads(row["path_calls"])
            assert 1 <= len(calls) <= int(row["depth"]) <= 3
            assert len(nodes) == len(calls) + 1
            assert nodes[-1] == row["changed_seed"]
            positions = []
            for i, call in enumerate(calls):
                assert call["caller"] == nodes[i] and call["chosen_target"] == nodes[i + 1]
                assert nodes[i + 1] in call["candidate_targets"]
                assert call["status"] in {"resolved", "ambiguous"}
                if call["status"] == "ambiguous":
                    positions.append(i + 1)
                if row["edge_variant"] == VARIANTS[0]:
                    assert call["status"] == "resolved"
            assert json.loads(row["ambiguous_hop_positions"]) == positions
            assert int(row["ambiguous_hop_count"]) == len(positions)
            assert (row["uses_ambiguous_edge"] == "True") == bool(positions)
            full_counts[row["edge_variant"]] += 1
            group_counts[(row["instance_id"], row["strategy"], row["edge_variant"], row["depth"], rank)] += 1
    assert all(v <= 3 for v in group_counts.values())
    assert all(v <= 22_950 for v in full_counts.values()) and sum(full_counts.values()) <= 45_900
    counts = json.loads((HERE / "provenance_counts.json").read_text())
    assert dict(full_counts) == counts["full_paths_by_variant"]
    computed = summarize(rows)
    actual = read_csv(HERE / "selector_summary.csv")
    assert len(computed) == len(actual)
    for result, stored in zip(computed, actual):
        for name, value in result.items():
            if value is None:
                assert stored[name] == ""
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                assert abs(float(stored[name]) - value) < 1e-10, name
            else:
                assert str(value) == stored[name], name
    assert criteria(rows, eligibility) == json.loads((HERE / "criteria.json").read_text())
    report = (HERE / "report.md").read_text()
    assert 'Nothing in the primary evaluation confirms that a selected test actually exercises the changed code.' in report
    plain = report.split('## Plain-language answer (seven lines)\n\n')[1].split('\n\n')[0].splitlines()
    assert len(plain) <= 10
    assert '## Deviations and incidents' in report
    incidents = json.loads((HERE / 'incidents.json').read_text())
    assert incidents['eligibility_json_sha256'] == sha((HERE / 'eligibility.json').read_bytes())
    assert incidents['eligibility_freeze_file_sha256'] == sha((HERE / 'eligibility_freeze.json').read_bytes())
    first_failure = json.loads((HERE / 'failed_attempts/archive_root_check/failure.json').read_text())
    assert sha((HERE / 'callgraph_selector.py').read_bytes()) == first_failure['code_sha256']['reports/callgraph_selection/phase2/callgraph_selector.py']
    assert incidents['no_ranking_eligibility_or_frozen_parameter_change']
    assert incidents['no_selector_candidate_output_inspected_before_fixes']
    morning = (HERE / 'MORNING_SUMMARY.md').read_text()
    assert morning.startswith('COMPLETED') and '83 headline tasks' in morning.splitlines()[0]
    assert len([line for line in morning.splitlines() if line]) <= 10
    task_statuses = read_csv(HERE / 'graph_status_by_task.csv')
    assert len(task_statuses) == sum(r['budget'] == 'ALL' for r in rows)
    verify_freeze()
    result = dict(status="passed", tasks=83, historical_tasks=19, ranked_configurations=len(ranked),
        candidate_rows=candidate_rows, task_configuration_rows=len(rows), full_paths_by_variant=dict(full_counts),
        no_phase1_file_changes=True, design_unchanged=True, selector_freeze_verified=True,
        frozen_code_and_all_input_hashes_verified=True, eligibility_before_selection_verified=True,
        shared_tail_missing_not_zero_verified=True, A_exact_and_C_same_union_verified=True,
        B_base_ids_verified=True, budget_prefixes_and_strata_verified=True, summary_and_criteria_verified=True,
        benchmark_execution=False, oracle_data=False)
    dump(HERE / "validation.json", result)
    finalize_outputs()
    manifest = json.loads((HERE / "outputs.sha256.json").read_text())
    for name, expected in manifest["output_sha256"].items():
        assert sha((HERE / name).read_bytes()) == expected
    assert (HERE / "outputs.sha256.json.sha256").read_text().split()[0] == sha((HERE / "outputs.sha256.json").read_bytes())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    validate()
