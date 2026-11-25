"""Phase 18 Part A: what B14's patch_apply_failed means for the gpt-4.1-mini pairs.

    phase18_b14_no_results.py OUT_JSON

For every gpt-4.1-mini pair whose B14 outcome is patch_apply_failed, reads the grading run's
test_output.txt and run_instance.log as text and records only: the apply command the grader
logged, whether the START/END test markers are present, which swebench bad codes are present,
and the Python exception type names between the markers. Never records or prints log lines.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "runs/study_v1_5/labels"
START, END = ">>>>> Start Test Output", ">>>>> End Test Output"
BAD = {"Patch Apply Failed": ">>>>> Patch Apply Failed", "Reset Failed": ">>>>> Reset Failed",
       "Tests Errored": ">>>>> Tests Errored", "Tests Timed Out": ">>>>> Tests Timed Out"}
CMDS = ["git apply --verbose", "git apply --verbose --3way", "git apply --verbose --reject",
        "patch --batch --forward --fuzz=5 -p1 -i"]  # swebench 5.0.2 GIT_APPLY_CMDS, in order
NAMED = ("ImportError", "ModuleNotFoundError", "SyntaxError", "IndentationError", "AttributeError", "NameError")
EXC = re.compile(r"(?m)^(?:E\s+)?(?:[A-Za-z_][\w]*\.)*([A-Za-z_]\w*(?:Error|Exception))(?::|\s*$)")


def runner_summary(between):
    """The test runner's own summary between the markers, as counts only (never the line itself)."""
    ran = re.findall(r"(?m)^Ran (\d+) tests? in ", between)
    status = re.findall(r"(?m)^(OK|FAILED \(([^)]*)\))\s*$", between)
    if ran and status:
        counts = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", status[-1][1])}
        return {"runner": "django", "ran": int(ran[-1]), "status": "OK" if status[-1][0] == "OK" else "FAILED", **counts}
    sym = re.findall(r"tests finished: ([^\n]*?)(?:, in [\d.]+ seconds)?\s*=*\s*$", between, re.M)
    if sym:
        counts = {k.replace(" ", "_"): int(n) for n, k in re.findall(r"(\d+) ([a-z][a-z ]*?)(?=,|$)", sym[-1])}
        return {"runner": "sympy", **counts}
    py = re.findall(r"(?m)^=+ (.*?) in [\d.]+s.*=+\s*$", between)
    if py and re.search(r"\b(passed|failed|error|errors|skipped|no tests ran)\b", py[-1]):
        counts = {k: int(n) for n, k in re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed|warnings?)", py[-1])}
        return {"runner": "pytest", **counts}
    return {"runner": "no summary line"}


def summary_kind(rs):
    if rs["runner"] == "no summary line":
        return "no summary line"
    bad = sum(rs.get(k, 0) for k in ("failed", "failures", "errors", "error", "exceptions"))
    return "all passed" if bad == 0 and rs.get("status", "OK") == "OK" else "failures or errors"


def apply_command(log):
    failed = re.findall(r"Failed to apply patch to container: (.+)", log)
    if ">>>>> Applied Patch: verified already applied" in log:
        return "already applied (git apply --check --reverse)"
    if ">>>>> Applied Patch" in log:
        return CMDS[len(failed)] if len(failed) < len(CMDS) else "unknown"
    return "none (all failed)" if failed else "not logged"


def decisions():
    out = {}
    for b in ("b1", "b2"):
        f = next((ROOT / f"reports/study_v1_5/test_{b}/decisions_gpt-4.1-mini").glob("decisions_*.csv"))
        for row in csv.DictReader(f.open()):
            out[row["instance_id"]] = {"decision": row["decision"], "rule": row["rule_id"], "batch": b}
    return out


def our_v1(iid, batch):
    """Our V1 apply check and V1 finding names from the sealed record (names only)."""
    rec = json.loads((ROOT / f"runs/study_test_gpt-4.1-mini_{batch}/tasks/{iid}/verification_record.full-v1.4.1.json").read_text())
    f = rec["integrity"]["findings"]
    return {"our_v1_outcome": rec["integrity"]["outcome"], "our_v1_apply_check": f.get("apply_check"),
            "our_v1_apply_command": f.get("apply_command"), "our_v1_violations": list(f.get("violations") or ())}


def main(out_path):
    dec = decisions()
    rows = []
    for folder in ("gpt-4.1-mini_ours", "gpt-4.1-mini_b2"):
        labels = json.loads((LABELS / folder / "labels.json").read_text())["labels"]
        for iid in sorted(i for i, v in labels.items() if v.get("outcome") == "patch_apply_failed"):
            res = json.loads((LABELS / folder / "gpt-4.1-mini" / iid / "result.json").read_text())
            run_dir = Path(res["report_file"]).parent
            test_out = (run_dir / "test_output.txt").read_text(encoding="utf-8", errors="replace") \
                if (run_dir / "test_output.txt").is_file() else ""
            log = (run_dir / "run_instance.log").read_text(encoding="utf-8", errors="replace") \
                if (run_dir / "run_instance.log").is_file() else ""
            report = json.loads(Path(res["report_file"]).read_text())
            node = report.get(iid, report)
            both = START in test_out and END in test_out
            between = test_out.split(START, 1)[1].split(END, 1)[0] if both else ""
            names = sorted(set(EXC.findall(between)))
            rs = runner_summary(between)
            rows.append({
                "instance_id": iid, "label_folder": folder, "batch": dec[iid]["batch"],
                "apply_command": apply_command(log),
                "test_output_present": bool(test_out), "start_marker": START in test_out, "end_marker": END in test_out,
                "bad_codes": [k for k, v in BAD.items() if v in test_out or v in log],
                "exception_types": {**{n: n in names for n in NAMED},
                                    "other": sorted(n for n in names if n not in NAMED)},
                "report_patch_successfully_applied": node.get("patch_successfully_applied"),
                "report_infra_failure_reason": node.get("infra_failure_reason"),
                "runner_summary": {**rs, "kind": summary_kind(rs)},
                "frozen_decision": dec[iid]["decision"], "frozen_rule": dec[iid]["rule"],
                **our_v1(iid, dec[iid]["batch"]),
                "report_sha256": res["report_sha256"],
            })
    applied_ok = [r for r in rows if r["start_marker"] and r["end_marker"] and not r["bad_codes"]]
    neither = [r for r in rows if "Patch Apply Failed" in r["bad_codes"] and r["our_v1_apply_check"] != "PASS"]
    summary = {
        "pairs": len(rows),
        "applied_both_markers_no_bad_code": len(applied_ok),
        "apply_failed_on_both_sides": len(neither),
        "other": len(rows) - len(applied_ok) - len(neither),
        "apply_commands": {c: sum(r["apply_command"] == c for r in rows) for c in sorted({r["apply_command"] for r in rows})},
        "exception_types_in_applied": {n: sum(r["exception_types"][n] for r in applied_ok) for n in NAMED},
        "applied_with_any_named_exception": sum(any(r["exception_types"][n] for n in NAMED) for r in applied_ok),
        "runner_summary_kinds": {k: sum(r["runner_summary"]["kind"] == k for r in rows)
                                 for k in ("all passed", "failures or errors", "no summary line")},
        "runner_summary_by_runner": {k: sum(r["runner_summary"]["runner"] == k for r in rows)
                                     for k in sorted({r["runner_summary"]["runner"] for r in rows})},
        "frozen_decisions": {d: sum(r["frozen_decision"] == d for r in rows) for d in ("ACCEPT", "FLAG", "REJECT")},
        "frozen_rules": {k: sum(r["frozen_rule"] == k for r in rows) for k in sorted({r["frozen_rule"] for r in rows})},
        "r1_applied_on_both_sides": sorted(f"{r['instance_id']} ({', '.join(r['our_v1_violations'])})" for r in rows
                                          if r["frozen_rule"] == "R1" and r["our_v1_apply_check"] == "PASS"
                                          and r["start_marker"] and r["end_marker"]),
        "our_v1_apply_check": {k: sum(r["our_v1_apply_check"] == k for r in rows) for k in sorted({str(r["our_v1_apply_check"]) for r in rows})},
    }
    out = {"meaning": "swebench 5.0.2 sets patch_successfully_applied false whenever get_logs_eval finds no usable "
                      "result: a bad code (Patch Apply Failed, Reset Failed, Tests Errored, Tests Timed Out), a "
                      "missing START/END marker, or no parsable test status and no sign the suite ran. Such patches "
                      "are unresolved, as in official grading.",
           "script": "scripts/phase18_b14_no_results.py",
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "summary": summary, "pairs": rows}
    Path(out_path).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main(sys.argv[1])
