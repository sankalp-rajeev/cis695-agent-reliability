"""Reuse sealed audit patches/specification and run_v1.py's three-file base recipe."""

import csv
import difflib
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from reliability.verifier.integrity_v1_4 import check_integrity

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
AUDIT = ROOT / "reports/next_phases/phase7_signal_audit"


def diff(path, before, after):
    return f"diff --git a/{path} b/{path}\n" + "".join(
        difflib.unified_diff(
            before.splitlines(True),
            after.splitlines(True),
            fromfile="a/" + path,
            tofile="b/" + path,
        )
    )


def main():
    prep = json.loads((AUDIT / "stage1_preparation.json").read_text())
    rows = []
    with tempfile.TemporaryDirectory(prefix="v14-audit-") as tmp:
        base = Path(tmp)
        with tarfile.open(prep["archive_path"]) as archive:
            for member in prep["archive_members"]:
                target = base / member.removeprefix("testbed/")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
        subprocess.run(["git", "init", "--template=", str(base)], check=True, capture_output=True)
        specs = json.loads((AUDIT / "v1_case_spec.json").read_text())
        for case in specs:
            patch = (AUDIT / "v1_fixtures" / (case["case"] + ".patch")).read_bytes()
            assert hashlib.sha256(patch).hexdigest() == case["fixture_sha256"]
            report = check_integrity(patch, base, **case["kwargs"])
            caught = report.decision.value == case["expected"] and (
                not case["required_violation"]
                or case["required_violation"] in [v.value for v in report.violations]
            )
            rows.append(
                {
                    "suite": "sealed_audit",
                    "case": case["case"],
                    "expected": case["expected"],
                    "observed": report.decision.value,
                    "caught": "yes" if caught else "no",
                    "reason": "; ".join(map(str, report.findings)),
                }
            )
        path = "tests/test_existing.py"
        before = "def test_existing():\n    x = 2\n    assert x == 2\n    assert x > 0\n"
        target = base / path
        target.parent.mkdir(parents=True)
        target.write_text(before)
        afters = {
            "assertion_removed": before.replace("    assert x > 0\n", ""),
            "constant_true": before.replace("assert x == 2", "assert True"),
            "equality_tautology": before.replace("assert x == 2", "assert x == x"),
            "body_pass": "def test_existing():\n    pass\n",
            "skip_decorator": "import pytest\n@pytest.mark.skip\n" + before,
            "skip_marker": before.replace("    x = 2", '    pytest.skip("skip")\n    x = 2'),
            "add_assertion_control": before + "    assert x < 3\n",
            "add_test_control": before + "\ndef test_new():\n    assert True\n",
        }
        fixtures = OUT / "v1_fixtures"
        fixtures.mkdir(exist_ok=True)
        for name, after in afters.items():
            patch = diff(path, before, after)
            (fixtures / (name + ".patch")).write_text(patch)
            expected = "PASS" if name.endswith("_control") else "REJECT"
            report = check_integrity(patch, base)
            rows.append(
                {
                    "suite": "v1_4",
                    "case": name,
                    "expected": expected,
                    "observed": report.decision.value,
                    "caught": "yes" if expected == report.decision.value else "no",
                    "reason": "; ".join(map(str, report.findings)),
                }
            )
    with (OUT / "v1_probes.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    assert all(r["caught"] == "yes" for r in rows), [r for r in rows if r["caught"] != "yes"]
    print(
        json.dumps(
            {
                "cases": len(rows),
                "caught": len(rows),
                "sealed_violations": sum(
                    r["suite"] == "sealed_audit" and r["expected"] == "REJECT" for r in rows
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
