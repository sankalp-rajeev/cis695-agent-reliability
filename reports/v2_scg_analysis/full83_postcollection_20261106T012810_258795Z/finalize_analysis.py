"""Independent aggregate checks, publication tables and protected-file check."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main(out):
    cfg = read(out / "analysis_configuration.json")
    root, results, frozen, run = (Path(cfg[k]) for k in ("root", "results", "frozen", "run"))
    pairs = read(results / "results.json")
    labels = read(out / "correctness_sidecar.json")
    summary = read(out / "labeled_summary.json")
    regressions = read(out / "regression_evidence.json")
    assert len(regressions) == 7
    pair_by_id = {r["instance_id"]: r for r in pairs}
    for regression in regressions:
        assert pair_by_id[regression["instance_id"]]["arms"]["scg"]["selected"] == 0
        observations = regression["observations"]
        assert [o["patched"] for o in observations] == [False, True, True, False]
        assert [o["selected_result"]["status"] for o in observations] == ["passed", "failed", "failed", "passed"]
        assert [[r["status"] for r in o["raw_results"]] for o in observations] == [["passed"], ["failed"], ["failed"], ["passed"]]
    independent = {}
    for arm in ("v2", "scg"):
        tp = sum(t["arms"][arm]["signal"] == "FAIL" and labels[t["instance_id"]]["correctness"] == "wrong" for t in pairs)
        fp = sum(t["arms"][arm]["signal"] == "FAIL" and labels[t["instance_id"]]["correctness"] == "right" for t in pairs)
        fn = sum(t["arms"][arm]["signal"] == "PASS" and labels[t["instance_id"]]["correctness"] == "wrong" for t in pairs)
        covered = sum(t["arms"][arm]["signal"] in ("PASS", "FAIL") for t in pairs)
        metrics = summary["arms"][arm]["correctness_metrics"]
        assert (tp, fp, fn) == (metrics["true_positive"], metrics["false_positive"], metrics["false_negative_binary"])
        assert covered == summary["arms"][arm]["completed_outcomes"]
        independent[arm] = {"wrong_patch_fail": tp, "right_patch_fail": fp, "wrong_patch_pass": fn,
                            "binary_covered": covered, "abstentions": 83 - covered}
    selected_available = [t for t in pairs if t["arms"]["scg"]["selected"] is not None]
    assert len(selected_available) == 81
    selected_v2 = sum(t["arms"]["v2"]["selected"] for t in selected_available)
    selected_scg = sum(t["arms"]["scg"]["selected"] for t in selected_available)
    assert selected_v2 == 57159 and selected_scg == 131
    costs = {a: summary["arms"][a]["costs"] for a in ("v2", "scg")}
    prep_elapsed = read(Path(cfg["base"]) / "prepare.result.json")["elapsed_s"]
    run_elapsed = read(run / "run.exit.json")["elapsed_s"]
    numbers = {"independent_label_metric_check": independent,
               "matched_available_tasks": 81, "v2_selected_matched": selected_v2,
               "scg_selected_matched": selected_scg,
               "matched_selected_reduction_percent": 100 * (1 - selected_scg / selected_v2),
               "combined_arm_time_reduction_percent": 100 * (1 - costs["scg"]["total_wall_s"]["sum"] / costs["v2"]["total_wall_s"]["sum"]),
               "original_prepare_cli_s": prep_elapsed, "full_run_cli_s": run_elapsed,
               "prepare_plus_full_run_cli_s": prep_elapsed + run_elapsed,
               "both_binary": sum(all(t["arms"][a]["signal"] in ("PASS", "FAIL") for a in ("v2", "scg")) for t in pairs),
               "either_binary": sum(any(t["arms"][a]["signal"] in ("PASS", "FAIL") for a in ("v2", "scg")) for t in pairs),
               "unequal_native_dispositions": sum(t["arms"]["v2"]["signal"] != t["arms"]["scg"]["signal"] for t in pairs)}
    write(out / "independent_crosschecks_and_costs.json", numbers)
    fields = ["instance_id", "correctness", "v2_signal", "scg_signal", "v2_selected", "scg_selected", "scg_graph"]
    with (out / "incorrect_patch_outcomes.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for task in pairs:
            if labels[task["instance_id"]]["correctness"] == "wrong":
                writer.writerow({"instance_id": task["instance_id"], "correctness": "wrong",
                    **{a + "_signal": task["arms"][a]["signal"] for a in ("v2", "scg")},
                    **{a + "_selected": task["arms"][a]["selected"] for a in ("v2", "scg")},
                    "scg_graph": task["arms"]["scg"]["selection"]["graph_status"]})
    with (out / "paired_dispositions.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["v2", "scg", "tasks"])
        for (v2, scg), n in sorted(Counter((t["arms"]["v2"]["signal"], t["arms"]["scg"]["signal"] or "NO_VERDICT") for t in pairs).items()):
            writer.writerow([v2, scg, n])
    historical = [root / "reports/callgraph_selection/report.md",
                  root / "reports/callgraph_selection/amendment2_72ad21b/report.md",
                  root / "reports/callgraph_selection/phase2/report.md"]
    scg = Path("/home/sankalp/projects/cis695-callgraph-typeprop")
    historical += [scg / "reports/next_steps/report.md"]
    historical += [scg / "reports/callgraph_selection/typeprop_experiment" / rel for rel in
                   ("report.md", "qualified_mapping/report.md", "regression_validation/report.md", "regression_path_diagnosis/report.md")]
    write(out / "historical_report_inputs.json", {str(p): sha(p) for p in historical})
    write(out / "analysis_incidents.json", {
        "label_preparation_sanity_checks": [
            "Initial exact working-vs-Git CSV byte check rejected CRLF; authoritative pinned LF bytes were then used. Parsed label values are identical.",
            "Initial exact source-run string check rejected four recorded rerun aliases. Final-study CSV provenance and exact candidate hashes matched the verified export manifest; no alternate patch or label value was substituted."],
        "all_sidecar_bindings_verified_before_labeled_summary": True,
        "no_experiments_or_scientific_audits_rerun": True})
    commands = [read(out / "unlabeled_summary.command.json"),
                {"command": ["/usr/bin/python3", "-B", str(out / "prepare_posthoc_evaluation.py"), str(out)],
                 "purpose": "Bind pinned labels and invoke existing labeled summary"},
                read(out / "labeled_summary.command.json"),
                {"command": ["/usr/bin/python3", "-B", str(out / "analyze_completed.py"), str(out)]},
                {"command": [str(Path(cfg["review"]) / ".venv/bin/python"), "-B", str(out / "diagnostic_replays.py"), str(out)],
                 "PYTHONPATH": "unset"},
                {"command": ["/usr/bin/python3", "-B", str(out / "finalize_analysis.py"), str(out)]}]
    write(out / "analysis_commands.json", commands)
    before = read(out / "original_artifacts_before.json")
    protected = {}
    for key, folder in (("frozen", frozen), ("results", results)):
        now = {str(p.relative_to(folder)): sha(p) for p in folder.rglob("*") if p.is_file()}
        assert now == before[key], key + " changed during post-collection analysis"
        protected[key] = {"files": len(now), "unchanged": True}
    write(out / "final_preservation_check.json", protected)
    print(json.dumps(numbers, indent=2))
    print("Preserved", protected)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
