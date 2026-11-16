"""Compare every baseline test by name; fail on any new failure or missing test."""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("junit", type=Path)
    args = parser.parse_args()
    baseline = {
        r["test"]: r["status"] for r in json.loads((OUT / "baseline_tests.json").read_text())
    }
    final = {}
    for case in ET.parse(args.junit).iter("testcase"):
        bad = next((n for n in case if n.tag in ("error", "failure", "skipped")), None)
        name = case.attrib["classname"] + "::" + case.attrib["name"]
        assert name not in final, name
        final[name] = bad.tag if bad is not None else "passed"
    rows = [
        {"test": name, "baseline": baseline.get(name, "new"), "final": final.get(name, "missing")}
        for name in sorted(set(baseline) | set(final))
    ]
    regressions = [
        r
        for r in rows
        if r["final"] == "missing"
        or (r["final"] in ("error", "failure") and r["baseline"] != r["final"])
    ]
    with (OUT / "test_comparison.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, ["test", "baseline", "final"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "baseline": dict(Counter(baseline.values())),
        "final": dict(Counter(final.values())),
        "new_tests": sum(r["baseline"] == "new" for r in rows),
        "new_failures": regressions,
        "baseline_status_changes": [
            r for r in rows if r["baseline"] != "new" and r["baseline"] != r["final"]
        ],
    }
    (OUT / "test_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not regressions, regressions
    print(json.dumps(result))


if __name__ == "__main__":
    main()
