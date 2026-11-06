#!/usr/bin/env python3
"""Read saved paired evidence only. Never imports or invokes the experiment.

Examples:
  python3 -B scripts/monitor_v2_scg_live.py --results /path/to/results --latest
  python3 -B scripts/monitor_v2_scg_live.py --results /path/to/results --summary
  python3 -B scripts/monitor_v2_scg_live.py --results /path/to/results --all --all-reasons
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ARMS = ("v2", "scg")
ADMITTED_STATUSES = {"passed", "failed", "skipped", "error"}
VERDICTS = ("PASS", "FAIL", "NOT_AVAILABLE", "INCOMPLETE", "BASELINE_UNRELIABLE", "NO_VERDICT")


def read_json(path):
    return json.loads(path.read_text())


def safe_text(value):
    """Render diagnostics without executing terminal escape/control sequences."""
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(value))
    return "".join(c if c in "\n\t" or ord(c) >= 32 else "?" for c in value)


def phase_evidence(call, number, initial_calls):
    run = call.get("run", {})
    requested = set(run.get("requested_tests", call.get("requested", [])))
    results = run.get("results", [])
    mappings = run.get("raw_id_map", {})
    raw = run.get("raw_results")
    raw_ids = {r.get("test_id") for r in raw or []}
    mapped = {tid for raw_id, ids in mappings.items() if raw_id in raw_ids for tid in ids}
    admitted = {r.get("test_id") for r in results if r.get("status") in ADMITTED_STATUSES}
    statuses = dict(Counter(r.get("status", "unknown") for r in results))
    not_run = [r["test_id"] for r in results if r.get("status") == "not_run"]
    timeout_ids = [r["test_id"] for r in results if r.get("status") == "timeout"]
    absent = sorted(requested - {r.get("test_id") for r in results})
    ends = [e for e in run.get("events", []) if e.get("event") == "end"]
    # This establishes a recorded parameter-family admission gap only when
    # concrete bracketed raw IDs actually map to the bare NOT_RUN family.
    parameter_gaps = sorted({tid for raw_id, ids in mappings.items()
                             if raw_id in raw_ids for tid in ids
                             if tid in not_run and raw_id.startswith(tid + "[")})
    return {
        "phase": "patched" if call.get("patched") else "base",
        "call": number + 1,
        "scope": "initial" if number < initial_calls else "confirmation/shadow",
        "requested_count": len(requested),
        "raw_concrete_cases": len(raw) if raw is not None else None,
        "raw_statuses": dict(Counter(r.get("status", "unknown") for r in raw or [])),
        "mapped_selected_count": len(mapped & requested) if raw is not None else None,
        "admitted_selected_status_count": (len(admitted & requested) if "results" in run else None),
        "selected_statuses": statuses,
        "not_run_ids": not_run,
        "timeout_ids": timeout_ids,
        "absent_selected_result_ids": absent,
        "without_mapped_raw_ids": sorted(requested - mapped) if raw is not None else None,
        "parameter_family_admission_gap_ids": parameter_gaps,
        "unmatched_raw_ids": run.get("unmatched_ids", []),
        "ambiguous_raw_ids": [rid for rid, ids in mappings.items() if len(ids) > 1],
        "timed_out": run.get("timed_out"),
        "evidence_complete": run.get("evidence_complete"),
        "infrastructure_errors": run.get("infrastructure_errors", []),
        "batch_exit_counts": dict(Counter(str(e.get("returncode")) for e in ends)),
        "note": run.get("note", ""),
    }


def explain_arm(row):
    status, signal = row.get("execution_status", "UNKNOWN"), row.get("signal")
    selection = row.get("selection", {})
    calls = row.get("calls", [])
    phases = [phase_evidence(c, i, row.get("initial_calls", len(calls)))
              for i, c in enumerate(calls)]
    counts = dict(Counter(row.get("outcomes", {}).values()))
    # Display the frozen Outcome.executed definition without reclassifying
    # any test or changing a verdict. That definition includes ERROR outcomes.
    native_counted = (sum(n for k, n in counts.items() if k not in ("NOT_RUN", "TIMEOUT"))
                      if "outcomes" in row else None)
    reasons = set()
    if status == "ZERO_SELECTION":
        explanation = "No tests selected; no benchmark container/test calls for this arm."
        reasons.add("ZERO_SELECTION")
    elif status == "UNAVAILABLE_SELECTION":
        explanation = "Selection/shared preparation unavailable; no substitute tests inferred."
        reasons.add("UNAVAILABLE_SELECTION")
    elif status == "EXECUTED" and signal == "NOT_AVAILABLE":
        explanation = "Tests selected, but no executions counted by native scoring; raw cases may still exist."
        reasons.add("NO_NATIVE_COUNTED_EXECUTIONS")
    elif signal == "INCOMPLETE":
        explanation = "Final INCOMPLETE: evidence gaps prevented a complete native PASS."
    elif signal == "PASS":
        explanation = "Native PASS for the selected list; inspect counted outcomes and completeness below."
    elif signal == "FAIL":
        explanation = "Native FAIL; recorded regression evidence is retained even if other gaps exist."
        reasons.add("RECORDED_REGRESSION")
    elif signal == "BASELINE_UNRELIABLE":
        explanation = "Recorded baseline-reliability verdict; no new reliability threshold inferred."
        reasons.add("BASELINE_UNRELIABLE")
    else:
        explanation = "No native verdict available; see recorded execution status and diagnostics."
    incomplete = row.get("incompleteness", [])
    if incomplete or row.get("completeness") not in (None, "COMPLETE") or signal == "INCOMPLETE":
        reasons.add("EVIDENCE_GAPS")
    if status == "EXECUTION_ERROR":
        reasons.add("EXECUTION_ERROR")
    if status == "ENVIRONMENT_MISMATCH":
        reasons.add("ENVIRONMENT_MISMATCH")
    if status == "UNAVAILABLE_ENVIRONMENT":
        reasons.add("UNAVAILABLE_ENVIRONMENT")
    if row.get("cleanup_error"):
        reasons.add("CLEANUP_ERROR")
    for phase in phases:
        if phase["timed_out"] or phase["timeout_ids"]:
            reasons.add("TIMEOUT")
        if phase["infrastructure_errors"]:
            reasons.add("RUNNER_ERROR")
        if phase["evidence_complete"] is False:
            reasons.add("INCOMPLETE_CAPTURE")
        if phase["not_run_ids"]:
            reasons.add("LEGACY_NOT_RUN")
        if phase["absent_selected_result_ids"]:
            reasons.add("ABSENT_SELECTED_RESULT")
        if phase["without_mapped_raw_ids"]:
            reasons.add("SELECTED_IDS_WITHOUT_RAW_MAPPING")
        if phase["unmatched_raw_ids"] or phase["ambiguous_raw_ids"]:
            reasons.add("RAW_ID_MAPPING_ERROR")
        if phase["parameter_family_admission_gap_ids"]:
            reasons.add("RECORDED_PARAMETER_FAMILY_ADMISSION_GAP")
        if phase["raw_statuses"].get("error", 0):
            reasons.add("RAW_TEST_ERROR")
    if selection.get("graph_status") == "partial":
        reasons.add("GRAPH_PARTIAL")
    if selection.get("graph_failures") or selection.get("mapping_diagnostics"):
        reasons.add("GRAPH_OR_MAPPING_DIAGNOSTICS_RECORDED")
    return {
        "signal": signal, "original_signal": row.get("original_signal"),
        "execution_status": status, "explanation": explanation,
        "selected": row.get("selected"), "completeness": row.get("completeness"),
        "selection_status": selection.get("selection_status", "unknown"),
        "graph_status": selection.get("graph_status", "unknown"),
        "graph_failures": selection.get("graph_failures", []),
        "mapping_diagnostics": selection.get("mapping_diagnostics", []),
        "selection_reason": selection.get("reason"),
        "resolved_seed_count": (len(selection["resolved_seeds"])
                                if "resolved_seeds" in selection else None),
        "reason": row.get("reason"), "error_type": row.get("error_type"),
        "cleanup_error": row.get("cleanup_error"), "summary": row.get("summary"),
        "incompleteness": incomplete, "outcome_counts": counts,
        "native_counted_outcomes": native_counted,
        "regressions": row.get("regressions", []), "phases": phases,
        "reason_groups": sorted(reasons),
    }


def snapshot(root):
    pairs = list((root / "tasks").glob("*/paired.json"))
    arms = list((root / "tasks").glob("*/*/paired_arm.json"))
    records, warnings = [], []
    for path in pairs:
        try:
            pair = read_json(path)
            if (not isinstance(pair, dict) or pair.get("instance_id") != path.parent.name
                    or not isinstance(pair.get("arms"), dict) or set(pair["arms"]) != set(ARMS)):
                warnings.append(f"{path}: invalid task identity or missing arm; deferred")
                continue
            record = {"instance_id": pair["instance_id"], "mtime_ns": path.stat().st_mtime_ns,
                      "evidence_path": str(path), "arms": {}, "record_warnings": []}
            for arm in ARMS:
                row = pair["arms"][arm]
                if not isinstance(row, dict):
                    raise TypeError(f"{arm}: arm is not an object")
                armfile = path.parent / arm / "paired_arm.json"
                arm_warning = None
                try:
                    if read_json(armfile) != row:
                        arm_warning = f"{arm}: paired.json/paired_arm.json differ"
                except (OSError, ValueError) as exc:
                    arm_warning = f"{arm}: arm file unavailable/unreadable: {exc}"
                record["arms"][arm] = explain_arm(row)
                if arm_warning:
                    record["record_warnings"].append(arm_warning)
                    record["arms"][arm]["reason_groups"].append("ARM_RECORD_CONSISTENCY_WARNING")
            records.append(record)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            warnings.append(f"{path}: incomplete/unreadable record; deferred ({exc})")
    records.sort(key=lambda r: (r["mtime_ns"], r["instance_id"]))
    return {"paired_files": len(pairs), "percent": len(pairs) * 100 / 83,
            "arm_files": len(arms), "records": records, "warnings": warnings}


def show_items(label, values, limit):
    if not values:
        return
    if not isinstance(values, list):
        values = [values]
    print(f"    {label} ({len(values)}):")
    for value in values if limit == 0 else values[:limit]:
        text = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        print("      " + safe_text(text).replace("\n", "\n      "))
    if limit and len(values) > limit:
        print(f"      ... {len(values) - limit} more; use --all-reasons or --json for every exact record")


def display_task(task, limit):
    print("\nTask: " + task["instance_id"])
    for arm in ARMS:
        row = task["arms"][arm]
        print(f"  {arm.upper()} overview: {row['signal'] or 'NO_VERDICT'}; selected={row['selected']}; "
              + (f"graph={row['graph_status']}; " if arm == "scg" else "") + row["explanation"])
    for arm in ARMS:
        row = task["arms"][arm]
        signal = row["signal"] or "NO_VERDICT"
        print(f"  {arm.upper()}: {signal} | {row['execution_status']} | selected={row['selected']}"
              f" | completeness={row['completeness']}")
        print("    " + row["explanation"])
        if row["original_signal"] is not None:
            print(f"    Original -> final: {row['original_signal']} -> {signal}")
        elif signal == "INCOMPLETE":
            print("    Original verdict: not recorded; not inferred")
        print(f"    Selection status: {safe_text(row['selection_status'])}")
        if arm == "scg":
            print(f"    SCG graph: {safe_text(row['graph_status'])}; resolved seeds={row['resolved_seed_count']}")
            print("    Graph/selection mechanism: use recorded diagnostics below; otherwise unknown.")
            show_items("Recorded graph failures", row["graph_failures"], limit)
            show_items("Recorded mapping diagnostics", row["mapping_diagnostics"], limit)
        for field in ("reason", "selection_reason", "error_type", "cleanup_error", "summary"):
            if row[field]:
                print(f"    {field}: {safe_text(row[field])}")
        if row["native_counted_outcomes"] is not None:
            print(f"    Native counted outcomes: {row['native_counted_outcomes']};"
                  f" outcome counts={row['outcome_counts']} (native count includes ERROR)")
        if not row["phases"]:
            print("    Raw/admitted coverage: no recorded runner calls; not inferred")
        for phase in row["phases"]:
            total = phase["requested_count"]
            print(f"    {phase['phase']} call {phase['call']} ({phase['scope']}):"
                  f" raw concrete={phase['raw_concrete_cases']};"
                  f" mapped selected={phase['mapped_selected_count']}/{total};"
                  f" admitted selected statuses={phase['admitted_selected_status_count']}/{total}")
            print(f"      raw statuses={phase['raw_statuses']}; selected statuses={phase['selected_statuses']}")
            print(f"      timeout={phase['timed_out']}; capture_complete={phase['evidence_complete']};"
                  f" batch exit codes={phase['batch_exit_counts']}")
            show_items("Runner errors", phase["infrastructure_errors"], limit)
            show_items("Selected NOT_RUN IDs (not proof of a missing test)", phase["not_run_ids"], limit)
            show_items("Selected TIMEOUT IDs", phase["timeout_ids"], limit)
            show_items("Absent selected result IDs", phase["absent_selected_result_ids"], limit)
            show_items("Selected IDs without mapped raw evidence (cause unknown)",
                       phase["without_mapped_raw_ids"], limit)
            show_items("Recorded parameter-family admission gaps", phase["parameter_family_admission_gap_ids"], limit)
            show_items("Unmatched raw IDs", phase["unmatched_raw_ids"], limit)
            show_items("Ambiguous raw IDs", phase["ambiguous_raw_ids"], limit)
            if phase["note"]:
                print("      Recorded runner note: " + safe_text(phase["note"]))
        show_items("Exact recorded incompleteness reasons", row["incompleteness"], limit)
        show_items("Recorded regression IDs", row["regressions"], limit)
        print("    Reason groups: " + (", ".join(row["reason_groups"]) or "none recorded"))
    show_items("Record consistency warnings", task["record_warnings"], limit)
    print("  Evidence: " + task["evidence_path"])


def display_summary(records):
    print("\nCompleted-task verdict counts (native final verdicts unchanged):")
    print("  ARM  " + "  ".join(f"{v:>19}" for v in VERDICTS))
    for arm in ARMS:
        counts = Counter(t["arms"][arm]["signal"] or "NO_VERDICT" for t in records)
        print(f"  {arm.upper():<4} " + "  ".join(f"{counts[v]:19d}" for v in VERDICTS))
        other = {k: v for k, v in counts.items() if k not in VERDICTS}
        if other:
            print("    Other recorded verdicts: " + str(other))
        reasons = Counter(reason for t in records for reason in t["arms"][arm]["reason_groups"])
        selections = Counter(t["arms"][arm]["selection_status"] for t in records)
        print(f"    {arm.upper()} selection status counts: {dict(selections)}")
        print(f"    {arm.upper()} reason groups (task-arm counts; groups overlap): {dict(sorted(reasons.items()))}")
    print("\nCompleted tasks:")
    for t in records:
        print("  " + t["instance_id"] + " | " + " | ".join(
            f"{arm.upper()}={t['arms'][arm]['signal'] or 'NO_VERDICT'}"
            f" selected={t['arms'][arm]['selected']}"
            f" [{','.join(t['arms'][arm]['reason_groups']) or 'no recorded gap'}]" for arm in ARMS)
            + f" | SCG graph={t['arms']['scg']['graph_status']}")
    print("  Use --all for detailed coverage/reasons for every completed task, or --task TASK_ID.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--latest", dest="mode", action="store_const", const="latest")
    modes.add_argument("--summary", dest="mode", action="store_const", const="summary")
    modes.add_argument("--all", dest="mode", action="store_const", const="all")
    modes.add_argument("--task", metavar="TASK_ID")
    parser.set_defaults(mode="latest")
    parser.add_argument("--reason-limit", type=int, default=8,
                        help="max entries per diagnostic list; 0 means all (default: 8)")
    parser.add_argument("--all-reasons", action="store_true", help="show all exact diagnostic entries")
    parser.add_argument("--json", action="store_true", help="emit full structured evidence without truncation")
    args = parser.parse_args(argv)
    if args.reason_limit < 0:
        parser.error("--reason-limit must be nonnegative")
    if not args.results.is_dir():
        parser.error("results directory does not exist")
    data = snapshot(args.results)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Tasks: {data['paired_files']}/83 ({data['percent']:.2f}%) | Arms: {data['arm_files']}/166")
    print("Read-only evidence display; no verdict recomputation or container/process actions.")
    print("Coverage: raw cases != mapped families != admitted selected statuses."
          " Admission excludes NOT_RUN/TIMEOUT; native outcome count can include ERROR.")
    limit = 0 if args.all_reasons else args.reason_limit
    if args.mode == "summary":
        display_summary(data["records"])
    else:
        records = data["records"]
        if args.task:
            records = [t for t in records if t["instance_id"] == args.task]
        elif args.mode == "latest":
            records = records[-1:]
        if not records:
            print("No readable completed task in the requested scope yet.")
        for task in records:
            display_task(task, limit)
    show_items("Snapshot warnings (active writes may be deferred until next refresh)", data["warnings"], limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
