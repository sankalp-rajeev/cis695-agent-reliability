"""Read-only post-collection integrity/diagnostic analysis. No Docker/test imports.

python3 -B analyze_completed.py ANALYSIS_DIRECTORY
Outputs are exclusive-create and separate from all original experiment artifacts.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def fingerprint(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def phase_stats(run, requested):
    raw = run.get("raw_results", [])
    mappings = run.get("raw_id_map", {})
    raw_ids = {r["test_id"] for r in raw}
    selected = set(requested)
    mapped = {tid for rid, ids in mappings.items() if rid in raw_ids for tid in ids}
    unique_mapped = [r for r in raw if len(mappings.get(r["test_id"], [])) == 1]
    statuses = Counter(r["status"] for r in run.get("results", []))
    admitted = {r["test_id"] for r in run.get("results", [])
                if r["status"] not in ("not_run", "timeout")}
    not_run = {r["test_id"] for r in run.get("results", []) if r["status"] == "not_run"}
    family = {tid for rid, ids in mappings.items() if rid in raw_ids for tid in ids
              if tid in not_run and rid.startswith(tid + "[")}
    return {"requested": len(selected), "raw_adapter_cases": len(raw),
            "raw_uniquely_mapped_cases": len(unique_mapped),
            "raw_unmapped_or_ambiguous_cases": len(raw) - len(unique_mapped),
            "raw_statuses": dict(Counter(r["status"] for r in raw)),
            "raw_uniquely_mapped_statuses": dict(Counter(r["status"] for r in unique_mapped)),
            "mapped_selected_families": len(mapped & selected),
            "selected_families_without_raw_mapping": sorted(selected - mapped),
            "admitted_selected_results": len(admitted & selected), "selected_statuses": dict(statuses),
            "raw_mapped_but_not_admitted_families": len((mapped & selected) - admitted),
            "bracket_family_admission_gap_ids": sorted(family),
            "timeout": bool(run.get("timed_out")), "capture_complete": run.get("evidence_complete"),
            "runner_errors": run.get("infrastructure_errors", []),
            "unmatched_raw_ids": run.get("unmatched_ids", [])}


def main(out):
    cfg = read(out / "analysis_configuration.json")
    frozen, results, root, review, runroot = (Path(cfg[k]) for k in ("frozen", "results", "root", "review", "run"))
    frozen_before, results_before = fingerprint(frozen), fingerprint(results)
    save(out / "original_artifacts_before.json", {"frozen": frozen_before, "results": results_before})
    complete = read(results / "collection_complete.json")
    provenance = read(results / "run_provenance.json")
    protocol = read(frozen / "protocol.json")
    plan = read(runroot / "full_83_plan.json")
    pairs = read(results / "results.json")
    tasks = read(frozen / "tasks.json")
    by_id = {t["instance_id"]: t for t in tasks}
    labels = read(out / "correctness_sidecar.json")
    witnesses = read(out / "historical_witness_sidecar.json")
    summary = read(out / "labeled_summary.json")
    assert sha(results / "results.json") == complete["results_sha256"] == cfg["results_sha256"]
    assert sha(frozen / "protocol.json") == complete["protocol_sha256"] == cfg["protocol_sha256"]
    assert sha(runroot / "full_83_plan.json") == complete["plan_sha256"] == cfg["plan_sha256"]
    ids = [p["instance_id"] for p in pairs]
    assert ids == [t["instance_id"] for t in tasks] == complete["scope"]
    assert len(ids) == len(set(ids)) == len(labels) == 83
    assert len(list((results / "tasks").glob("*/paired.json"))) == 83
    assert len(list((results / "tasks").glob("*/*/paired_arm.json"))) == 166
    assert provenance["actual_git_revision"] == "b030e508d849926b9a2260c70e1091adebfee993"
    assert provenance["labels_read"] is False and complete["labels_read"] is False
    assert provenance["plan"] == plan and provenance["source_sha256"] == protocol["source_sha256"]
    assert provenance["host_packages"] == read(frozen / "host_packages.json")
    assert read(runroot / "run.exit.json")["returncode"] == 0
    seals = read(frozen / "artifact_hashes.json")
    assert all(frozen_before[p] == digest for p, digest in seals.items())
    assert all(frozen_before[p] == digest for p, digest in protocol["task_artifact_sha256"].items())
    assert all(sha(review / p) == digest for p, digest in protocol["source_sha256"].items())
    assert not subprocess.check_output(["git", "-C", str(review), "status", "--porcelain"], text=True).strip()
    monitor_spec = importlib.util.spec_from_file_location("monitor_analysis_helpers", root / "scripts/monitor_v2_scg_live.py")
    monitor = importlib.util.module_from_spec(monitor_spec)
    monitor_spec.loader.exec_module(monitor)
    inventories, evidence, environments, regression_evidence, witness_evidence = [], [], [], [], []
    reason_groups = {a: Counter() for a in ("v2", "scg")}
    incompletes = {a: [] for a in ("v2", "scg")}
    parser_tasks = {a: set() for a in ("v2", "scg")}
    coverage = {a: defaultdict(Counter) for a in ("v2", "scg")}
    label_signals = {a: defaultdict(Counter) for a in ("v2", "scg")}
    unavailable = []
    for index, pair in enumerate(pairs):
        iid = pair["instance_id"]
        task = by_id[iid]
        folder = results / "tasks" / iid
        assert read(folder / "paired.json") == pair
        expected_order = ["v2", "scg"] if index % 2 == 0 else ["scg", "v2"]
        assert pair["arm_order"] == expected_order == plan["schedule"][index]["arms"]
        assert pair["patch_sha256"] == task["patch_sha256"] == labels[iid]["patch_sha256"]
        assert pair["image_id"] == task["image_binding"]["host_image_id"]
        for key in ("base_commit", "base_archive_sha256", "runner", "image_tag", "image_binding"):
            assert pair[key] == task[key], (iid, key)
        for arm in ("v2", "scg"):
            row = pair["arms"][arm]
            armfolder = folder / arm
            assert read(armfolder / "paired_arm.json") == row
            native = read(armfolder / "result.json")
            for key in ("signal", "execution_status", "completeness", "selected_tests", "patch_sha256"):
                assert native.get(key) == row.get(key), (iid, arm, key)
            selected = read(frozen / task["selections"][arm])
            assert row["selected_tests"] == selected["tests"] == row["selection"]["tests"]
            assert row["patch_sha256"] == task["patch_sha256"]
            assert selected == row["selection"]
            assert row["signal"] != "PASS" or row["completeness"] == "COMPLETE"
            if row["execution_status"] == "EXECUTED":
                environment = read(armfolder / "environment.json")
                assert environment["image_id"] == pair["image_id"]
                assert environment["source_sha256"] == task["base_source_sha256"]
                environments.append({"instance_id": iid, "arm": arm,
                                     "source_file_matches": len(environment["source_sha256"]),
                                     "head_matches_dataset_base": environment["head_matches_dataset_base"],
                                     "image_id": environment["image_id"]})
            elif row["execution_status"] in ("ZERO_SELECTION", "UNAVAILABLE_SELECTION"):
                assert not row["calls"]
            if row["signal"] is None:
                assert arm == "scg" and row["selected_tests"] is None
                assert selected["selection_status"] == "UNAVAILABLE_NO_RESOLVED_SEEDS"
                assert selected["resolved_seeds"] == []
                unavailable.append({"instance_id": iid, "execution_status": row["execution_status"],
                                    "reason": row["reason"], "graph_status": selected["graph_status"],
                                    "graph_failures": selected["graph_failures"],
                                    "mapping": selected["mapping"], "mapping_diagnostics": selected["mapping_diagnostics"],
                                    "expected_preexecution_abstention": True, "execution_calls": 0})
            explain = monitor.explain_arm(row)
            reason_groups[arm].update(explain["reason_groups"])
            label_signals[arm][labels[iid]["correctness"]][row["signal"] or "NO_VERDICT"] += 1
            callstats, missing_ids = [], set()
            for ci, call in enumerate(row.get("calls", [])):
                recorded = call["run"]
                requested = call["requested"]
                assert set(requested) <= set(row["selected_tests"] or [])
                if ci < 2:
                    assert requested == row["selected_tests"], (iid, arm, ci, "initial request drift")
                phase = ("base" if ci == 0 else "patched" if ci == 1 else
                         "production_confirmation" if ci < row["initial_calls"] else "shadow_observation")
                stats = phase_stats(recorded, requested)
                stats.update(phase=phase, patched=call["patched"], wall_s=call["wall_s"])
                for key in ("requested", "raw_adapter_cases", "raw_uniquely_mapped_cases",
                            "raw_unmapped_or_ambiguous_cases", "mapped_selected_families",
                            "admitted_selected_results", "raw_mapped_but_not_admitted_families"):
                    coverage[arm][phase][key] += stats[key]
                for status, count in stats["selected_statuses"].items():
                    coverage[arm][phase]["selected_status_" + status] += count
                for status, count in stats["raw_statuses"].items():
                    coverage[arm][phase]["raw_status_" + status] += count
                coverage[arm][phase]["calls"] += 1
                coverage[arm][phase]["timed_out_calls"] += stats["timeout"]
                if stats["bracket_family_admission_gap_ids"]:
                    parser_tasks[arm].add(iid)
                for name, filename in recorded["evidence_files"].items():
                    path = Path(filename)
                    assert results.resolve() in path.resolve().parents
                    digest = sha(path)
                    assert digest == recorded["evidence_sha256"][name], filename
                    evidence.append({"instance_id": iid, "arm": arm, "call": ci + 1,
                                     "phase": phase, "path": filename, "sha256": digest, "bytes": path.stat().st_size})
                runner = Path(recorded["evidence_files"]["runner.raw"]).read_text(errors="replace")
                explicit_missing = re.findall(r"ERROR: not found: /testbed/([^\r\n]+)", runner)
                stats["explicit_pytest_not_found_ids"] = sorted(set(explicit_missing))
                missing_ids.update(explicit_missing)
                callstats.append(stats)
            record = {"instance_id": iid, "arm": arm, "correctness": labels[iid]["correctness"],
                      "signal": row["signal"], "original_signal": row.get("original_signal"),
                      "execution_status": row["execution_status"], "completeness": row["completeness"],
                      "selected": row["selected"], "selected_tests": row["selected_tests"],
                      "graph_status": selected["graph_status"], "selection_status": selected["selection_status"],
                      "reason_groups": explain["reason_groups"], "incompleteness": row.get("incompleteness", []),
                      "explicit_pytest_not_found_ids": sorted(missing_ids),
                      "outcome_counts": dict(Counter(row.get("outcomes", {}).values())),
                      "native_counted_outcomes": explain["native_counted_outcomes"],
                      "regressions": row.get("regressions", []), "calls": callstats,
                      "costs": row["costs"], "shadow_prediction": row.get("shadow", {}).get("prediction"),
                      "shadow_reason": row.get("shadow", {}).get("reason")}
            inventories.append(record)
            if row["signal"] == "INCOMPLETE":
                incompletes[arm].append(record)
            for tid in row.get("regressions", []):
                observations = []
                for ci, call in enumerate(row["calls"]):
                    selected_result = next((r for r in call["run"]["results"] if r["test_id"] == tid), None)
                    raw = [r for r in call["run"]["raw_results"]
                           if tid in call["run"]["raw_id_map"].get(r["test_id"], [])]
                    if tid in call["requested"]:
                        observations.append({"call": ci + 1, "patched": call["patched"],
                                             "requested": True, "selected_result": selected_result,
                                             "raw_results": raw, "timed_out": call["run"]["timed_out"],
                                             "evidence_complete": call["run"]["evidence_complete"],
                                             "runner_path": call["run"]["evidence_files"]["runner.raw"]})
                regression_evidence.append({"instance_id": iid, "arm": arm, "test_id": tid,
                                            "correctness": labels[iid]["correctness"], "observations": observations})
            for tid in witnesses.get(iid, {}).get("test_ids", []):
                initial = row.get("calls", [])[:2]
                observations = []
                for call in initial:
                    outcome = next((r for r in call["run"]["results"] if r["test_id"] == tid), None)
                    observations.append({"patched": call["patched"], "selected_result": outcome,
                                         "raw_matches": [r for r in call["run"]["raw_results"]
                                                         if tid in call["run"]["raw_id_map"].get(r["test_id"], [])]})
                witness_evidence.append({"instance_id": iid, "arm": arm, "test_id": tid,
                                         "correctness": labels[iid]["correctness"],
                                         "selected": tid in (row["selected_tests"] or []),
                                         "confirmed_detection": tid in row.get("regressions", []),
                                         "initial_observations": observations})
    incomplete_reasons = {}
    for arm, records in incompletes.items():
        counter = Counter(group for record in records for group in record["reason_groups"])
        counter["EXPLICIT_PYTEST_NOT_FOUND"] = sum(bool(r["explicit_pytest_not_found_ids"]) for r in records)
        incomplete_reasons[arm] = {"tasks": len(records), "original_signals": dict(Counter(r["original_signal"] for r in records)),
                                   "overlapping_task_reason_counts": dict(counter),
                                   "task_ids": [r["instance_id"] for r in records]}
    scg_nonempty = [t for t in pairs if t["arms"]["scg"]["selected"] not in (None, 0)]
    useful = [{"instance_id": t["instance_id"], "correctness": labels[t["instance_id"]]["correctness"],
               "v2_selected": t["arms"]["v2"]["selected"], "scg_selected": t["arms"]["scg"]["selected"],
               "graph_status": t["arms"]["scg"]["selection"]["graph_status"]}
              for t in pairs if t["arms"]["scg"]["signal"] == "PASS" and t["arms"]["v2"]["signal"] != "PASS"]
    output = {"label_signals": {a: {k: dict(v) for k, v in x.items()} for a, x in label_signals.items()},
              "coverage": {a: {p: dict(v) for p, v in x.items()} for a, x in coverage.items()},
              "all_task_reason_groups": {a: dict(v) for a, v in reason_groups.items()},
              "incomplete_reasons": incomplete_reasons,
              "runtime_confirmed_bracket_admission_tasks": {a: sorted(v) for a, v in parser_tasks.items()},
              "scg_nonempty_signals": dict(Counter(t["arms"]["scg"]["signal"] for t in scg_nonempty)),
              "scg_nonempty_graph_status": dict(Counter(t["arms"]["scg"]["selection"]["graph_status"] for t in scg_nonempty)),
              "scg_pass_where_v2_does_not_pass": useful,
              "both_binary_task_ids": [t["instance_id"] for t in pairs
                                       if all(t["arms"][a]["signal"] in ("PASS", "FAIL") for a in ("v2", "scg"))],
              "summary_correctness_metrics": {a: x["correctness_metrics"] for a, x in summary["arms"].items()}}
    integrity = {"paired_tasks_verified": 83, "arm_records_verified": 166,
                 "task_order_pairing_inputs_selections_and_images_verified": True,
                 "frozen_artifacts_sealed_verified": len(seals),
                 "raw_capture_hash_entries_verified": len(evidence),
                 "raw_capture_unique_files_verified": len({e["path"] for e in evidence}),
                 "runtime_source_checks_verified": len(environments),
                 "runtime_source_file_entries_verified": sum(e["source_file_matches"] for e in environments),
                 "image_heads_differing_from_dataset_base": sum(not e["head_matches_dataset_base"] for e in environments),
                 "runtime_import_trace_complete": False,
                 "no_verdict_expected_abstentions": unavailable,
                 "execution_error_or_environment_mismatch_records": [r["instance_id"] + ":" + r["arm"] for r in inventories
                                                                        if r["execution_status"] in ("EXECUTION_ERROR", "ENVIRONMENT_MISMATCH")],
                 "protocol_sha256": cfg["protocol_sha256"], "results_sha256": cfg["results_sha256"],
                 "plan_sha256": cfg["plan_sha256"], "labels_read_during_collection": False,
                 "frozen_files_unchanged": fingerprint(frozen) == frozen_before,
                 "result_files_unchanged": fingerprint(results) == results_before}
    assert integrity["frozen_files_unchanged"] and integrity["result_files_unchanged"]
    save(out / "integrity_verification.json", integrity)
    save(out / "capture_hash_inventory.json", evidence)
    save(out / "environment_checks.json", environments)
    save(out / "arm_diagnostics.json", inventories)
    save(out / "regression_evidence.json", regression_evidence)
    save(out / "historical_witness_execution.json", witness_evidence)
    save(out / "analysis_metrics.json", output)
    fields = ("instance_id", "arm", "correctness", "signal", "original_signal", "execution_status",
              "completeness", "selected", "graph_status", "selection_status", "native_counted_outcomes", "reason_groups")
    with (out / "task_arm_inventory.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for record in inventories:
            writer.writerow({k: json.dumps(record[k]) if isinstance(record[k], list) else record[k] for k in fields})
    print(json.dumps({"integrity": {k: v for k, v in integrity.items() if k != "no_verdict_expected_abstentions"},
                      "metrics": output}, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
