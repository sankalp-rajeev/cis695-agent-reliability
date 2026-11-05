"""Read saved pilot evidence only. Never executes tests or changes verdicts."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

OUT = Path(sys.argv[1])
FROZEN = OUT.parent / "paired_frozen"
RESULTS = OUT / "results"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
    with (OUT / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    from reliability.verifier.selection import django_label
    authorization = json.loads((OUT / "authorization_scope.json").read_text())
    complete = json.loads((RESULTS / "collection_complete.json").read_text())
    pairs = json.loads((RESULTS / "results.json").read_text())
    frozen_tasks = {r["instance_id"]: r for r in json.loads((FROZEN / "tasks.json").read_text())}
    plan = json.loads(Path(authorization["plan_path"]).read_text())
    assert sha(Path(authorization["plan_path"])) == authorization["approved_plan_sha256"]
    assert complete["results_sha256"] == sha(RESULTS / "results.json")
    assert complete["plan_sha256"] == authorization["approved_plan_sha256"]
    assert complete["protocol_sha256"] == authorization["protocol_sha256"]
    assert complete["labels_read"] is False and complete["tasks_accounted"] == len(pairs) == 3
    assert complete["scope"] == [r["instance_id"] for r in plan["schedule"]]
    assert [p["instance_id"] for p in pairs] == complete["scope"]
    assert json.loads((OUT / "unlabeled_summary.json").read_text()) == json.loads((RESULTS / "metrics.json").read_text())
    inventory, captures, fidelity, calls = [], [], [], []
    for pair in pairs:
        task = frozen_tasks[pair["instance_id"]]
        schedule = next(r for r in plan["schedule"] if r["instance_id"] == pair["instance_id"])
        assert pair["arm_order"] == schedule["arms"]
        assert set(pair["arms"]) == {"v2", "scg"}
        for arm in pair["arm_order"]:
            row = pair["arms"][arm]
            expected = json.loads((FROZEN / task["selections"][arm]).read_text())
            assert row["selected_tests"] == expected["tests"] == row["selection"]["tests"]
            folder = RESULTS / "tasks" / pair["instance_id"] / arm
            assert json.loads((folder / "paired_arm.json").read_text()) == row
            observation = dict(instance_id=pair["instance_id"], arm=arm, execution_status=row["execution_status"],
                native_signal=row["signal"], original_signal=row.get("original_signal"), completeness=row["completeness"],
                selected_ids=row["selected"], selected_test_ids=row["selected_tests"], execution_wall_s=row["wall_s"],
                initial_calls=row["initial_calls"], total_calls=len(row["calls"]),
                incompleteness=row.get("incompleteness", []), regressions=row.get("regressions", []),
                resources=row.get("resources", {}), phases=[], empty_selection=row["selected"] == 0)
            envpath = folder / "environment.json"
            if expected["tests"]:
                env = json.loads(envpath.read_text())
                assert env["source_sha256"] == task["base_source_sha256"]
                assert env["image_id"] == task["image_binding"]["host_image_id"]
                evidence = dict(instance_id=pair["instance_id"], arm=arm, environment_path=str(envpath),
                    environment_sha256=sha(envpath), required_source_files_verified=len(env["source_sha256"]),
                    image_id=env["image_id"], python=env["python"], observed_head=env["head"],
                    dataset_base_commit=task["base_commit"], head_matches_dataset_base=env["head_matches_dataset_base"],
                    source_equivalence_verified=True, source_scope="Frozen common selected/changed-file union, before patch execution; not full repository identity.",
                    import_path_evidence=[], runtime_sys_path_or_module_origin_inventory_recorded=False)
            else:
                assert row["execution_status"] == "ZERO_SELECTION" and row["signal"] == "NOT_AVAILABLE"
                assert not envpath.exists() and not (folder / "raw").exists() and row["calls"] == []
                evidence = dict(instance_id=pair["instance_id"], arm=arm, source_equivalence_verified=None,
                                reason="Zero selection: no benchmark container, no runtime source/import probe.")
            for index, call in enumerate(row["calls"]):
                run = call["run"]
                phase = "base" if not call["patched"] else "patched"
                requested = run["requested_tests"]
                if index < 2:
                    assert requested == row["selected_tests"]
                accounted = {value for mapped in run["raw_id_map"].values() for value in mapped}
                native_outcomes = {}
                raw_paths = []
                native_python_headers = []
                django_origins = []
                native_batch_exits = [e["returncode"] for e in run["events"] if e["event"] == "end"]
                started_ids = [v for e in run["events"] if e["event"] == "start" for v in e["ids"]]
                native_requested = [django_label(t) for t in requested] if task["runner"]["name"] == "django" else requested
                assert started_ids == native_requested
                for name, path in run["evidence_files"].items():
                    actual = sha(Path(path))
                    expected_sha = run["evidence_sha256"][name]
                    assert actual == expected_sha
                    captures.append(dict(instance_id=pair["instance_id"], arm=arm, call_index=index, phase=phase,
                                         artifact=name, path=path, expected_sha256=expected_sha, actual_sha256=actual, verified=True))
                text = Path(run["evidence_files"]["runner.raw"]).read_text(errors="replace")
                for line in text.splitlines():
                    match = re.match(r"^(.+?::.+?)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", line.strip())
                    if match:
                        native_outcomes[match[1]] = match[2]
                    if line.startswith("platform "):
                        native_python_headers.append(line)
                    if "Testing against Django installed in" in line:
                        django_origins.append(line)
                full_paths = re.findall(r"(?<![A-Za-z0-9_./-])(/[^\s:'\"()]+\.py)", text)
                raw_paths = sorted({p for p in full_paths if p.startswith("/testbed/")})
                p = dict(phase=phase, call_index=index, requested_id_count=len(requested), requested_test_ids=requested,
                    accounted_selected_id_count=len(accounted), accounted_selected_ids=sorted(accounted),
                    unaccounted_selected_ids=sorted(set(requested) - accounted),
                    raw_concrete_case_count=len(run["raw_results"]), raw_status_counts=dict(Counter(r["status"] for r in run["raw_results"])),
                    raw_concrete_results=run["raw_results"], raw_id_map=run["raw_id_map"], unmatched_raw_ids=run["unmatched_ids"],
                    legacy_selected_status_counts=dict(Counter(r["status"] for r in run["results"])),
                    legacy_not_run_selected_ids=[r["test_id"] for r in run["results"] if r["status"] == "not_run"],
                    native_pytest_outcome_counts=dict(Counter(native_outcomes.values())),
                    native_pytest_outcomes=native_outcomes, native_batch_returncodes=native_batch_exits,
                    runner_batch_count=len(native_batch_exits), runner_events=run["events"],
                    timed_out=run["timed_out"], infrastructure_errors=run["infrastructure_errors"], evidence_complete=run["evidence_complete"],
                    wall_s=call["wall_s"], runner_s=call["runner_s"], evidence_files=run["evidence_files"], evidence_sha256=run["evidence_sha256"])
                observation["phases"].append(p)
                calls.append(dict(instance_id=pair["instance_id"], arm=arm, **p))
                evidence.setdefault("import_path_evidence", []).append(dict(phase=phase, runner_log_path=run["evidence_files"]["runner.raw"],
                    native_interpreter_headers=native_python_headers, explicit_django_install_location=django_origins,
                    absolute_python_paths_reported_in_warnings_or_tracebacks=raw_paths,
                    caveat="Django install banner is explicit package-location evidence; warning paths locate specific modules. Pytest rootdir/test IDs do not prove every imported library resolves to the frozen source. XFAIL maps to SKIPPED in the unchanged adapter."))
            inventory.append(observation)
            fidelity.append(evidence)
    assert len(inventory) == 6 and len(calls) == 10 and len(captures) == 40
    summary = dict(tasks_accounted=3, arm_records=6, native_signals=dict(Counter(r["native_signal"] for r in inventory)),
        execution_statuses=dict(Counter(r["execution_status"] for r in inventory)), completeness=dict(Counter(r["completeness"] for r in inventory)),
        collection_wall_s=complete["total_collection_wall_s"], command_wall_s=json.loads((OUT / "pilot_run.result.json").read_text())["elapsed_s"],
        summed_arm_execution_wall_s=sum(r["execution_wall_s"] for r in inventory), summed_task_execution_wall_s=sum(p["execution_wall_s"] for p in pairs),
        selected_id_slots_one_list_per_arm=sum(r["selected_ids"] for r in inventory), requested_id_slots_across_passes=sum(r["requested_id_count"] for r in calls),
        accounted_selected_id_slots_across_passes=sum(r["accounted_selected_id_count"] for r in calls),
        concrete_outcomes_across_passes=sum(r["raw_concrete_case_count"] for r in calls),
        concrete_adapter_statuses=dict(sum((Counter(r["raw_status_counts"]) for r in calls), Counter())),
        native_pytest_outcomes=dict(sum((Counter(r["native_pytest_outcome_counts"]) for r in calls), Counter())),
        native_runner_batches=sum(r["runner_batch_count"] for r in calls), native_runner_batch_exit_codes=dict(Counter(code for r in calls for code in r["native_batch_returncodes"])),
        pass_timeouts=sum(r["timed_out"] for r in calls), infrastructure_errors=[e for r in calls for e in r["infrastructure_errors"]],
        unaccounted_selected_ids=[r for r in calls if r["unaccounted_selected_ids"]], unmatched_raw_ids=[r for r in calls if r["unmatched_raw_ids"]],
        raw_capture_files_verified=len(captures), raw_capture_integrity_failures=0,
        runtime_source_checks_verified=sum(r["source_equivalence_verified"] is True for r in fidelity),
        runtime_source_files_checked_across_arms=sum(r.get("required_source_files_verified",0) for r in fidelity),
        source_mismatch_arms=[r for r in inventory if r["execution_status"]=="ENVIRONMENT_MISMATCH"],
        runtime_error_arms=[r for r in inventory if r["execution_status"]=="EXECUTION_ERROR"],
        full_runtime_import_inventory_captured=False, confirmation_or_shadow_passes=sum(max(0,r["total_calls"]-2) for r in inventory),
        labels_or_witnesses_read=False, results_sha256=sha(RESULTS/"results.json"), unlabeled_summary_sha256=sha(OUT/"unlabeled_summary.json"))
    write("execution_inventory.json", inventory)
    write("runtime_source_and_import_evidence.json", fidelity)
    write("raw_capture_integrity.json", captures)
    write("execution_diagnostic_summary.json", summary)
    flat = []
    for row in inventory:
        phases={p["phase"]:p for p in row["phases"][:2]}
        r={k:row[k] for k in ("instance_id","arm","execution_status","native_signal","completeness","selected_ids","execution_wall_s")}
        for phase in ("base","patched"):
            p=phases.get(phase)
            r[phase+"_accounted_selected"]=p["accounted_selected_id_count"] if p else None
            r[phase+"_raw_concrete"]=p["raw_concrete_case_count"] if p else None
            r[phase+"_native_outcomes"]=json.dumps(p["native_pytest_outcome_counts"],sort_keys=True) if p else None
        flat.append(r)
    with (OUT/"execution_inventory.csv").open("x",newline="") as stream:
        writer=csv.DictWriter(stream,list(flat[0]));writer.writeheader()
        for r in flat:writer.writerow({k:"null" if v is None else v for k,v in r.items()})
    print(json.dumps(summary,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
