"""Independent standard-library proof; imports no policy or producer code."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def table(name):
    return list(csv.DictReader((OUT / name).open()))


def decide(record, v14=False):
    flags = record["integrity"]["findings"]
    i, r, _s, p = (
        record[k]["outcome"] for k in ("integrity", "regression", "static", "reproduction")
    )
    reject = (
        not flags.get("patch_applies", True)
        or i == "FAIL"
        or (r == "FAIL" and p != "PASS")
        or flags.get("prohibited_manipulation", False)
    )
    if reject:
        return "REJECT"
    accept = i == r == p == "PASS" and not flags.get("high_severity_risk", False)
    summary = record["static"]["findings"].get("summary", {})
    if v14 and any(summary.get(k) == "FAIL" for k in ("syntax", "import")):
        accept = False
    return "ACCEPT" if accept else "FLAG"


def main():
    inventory = list(
        csv.DictReader(
            (ROOT / "reports/next_phases/phase7_signal_audit/record_inventory_all.csv").open()
        )
    )
    expected_golden, expected_delta = [], []
    inputs = {r["task"]: r for r in json.loads((OUT / "policy_inputs.json").read_text())}
    for row in inventory:
        path = ROOT / row["record"]
        assert path.name == "verification_record.full.json"
        blob = path.read_bytes()
        record = json.loads(blob)
        assert hashlib.sha256(blob).hexdigest() == inputs[row["task"]]["sha256"]
        old, new = decide(record), decide(record, True)
        assert old == record["decision"]["decision"], row["task"]
        expected_golden.append(
            {"task": row["task"], "stored": old, "v1_3": old, "exact_record_match": "yes"}
        )
        expected_delta.append(
            {
                "task": row["task"],
                "v1_3": old,
                "v1_4": new,
                "changed": "yes" if old != new else "no",
                "cause": "v3_absolute_failure" if old != new else "",
            }
        )
    assert len(inventory) == len(inputs) == 100
    assert table("golden.csv") == expected_golden
    assert table("delta.csv") == expected_delta
    probes = table("v1_probes.csv")
    assert all(r["caught"] == "yes" and r["expected"] == r["observed"] for r in probes)
    specs = json.loads(
        (ROOT / "reports/next_phases/phase7_signal_audit/v1_case_spec.json").read_text()
    )
    assert {r["case"] for r in probes if r["suite"] == "sealed_audit"} == {r["case"] for r in specs}
    result = {
        "independent_verification": "PASS",
        "golden": 100,
        "delta_tasks": [r["task"] for r in expected_delta if r["changed"] == "yes"],
        "v1_audit_violations_caught": sum(
            r["suite"] == "sealed_audit" and r["expected"] == "REJECT" for r in probes
        ),
        "decision_counts": dict(Counter(r["v1_4"] for r in expected_delta)),
    }
    comparison_path = OUT / "test_comparison.csv"
    if comparison_path.is_file():
        comparison = table("test_comparison.csv")
        baseline = {
            r["test"]: r["status"] for r in json.loads((OUT / "baseline_tests.json").read_text())
        }
        assert len(comparison) == len({r["test"] for r in comparison})
        assert all(r["baseline"] == baseline.get(r["test"], "new") for r in comparison)
        assert {r["test"] for r in comparison if r["baseline"] != "new"} == set(baseline)
        assert all(r["final"] == r["baseline"] for r in comparison if r["baseline"] != "new")
        assert all(r["final"] == "passed" for r in comparison if r["baseline"] == "new")
        result["baseline_names_verified"] = len(baseline)
        result["new_tests_passed"] = sum(r["baseline"] == "new" for r in comparison)
    (OUT / "independent_verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
