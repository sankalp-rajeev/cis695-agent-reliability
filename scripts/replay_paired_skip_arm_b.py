"""Replay and check Arm B against frozen captures and committed decisions."""

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from dataclasses import replace
from pathlib import Path

from reliability.verifier.evidence import regression_outcome
from reliability.verifier.guarded_v2 import Replay
from reliability.verifier.policy_v1_4 import evidence_from_signals
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.regression import RegressionConfig, run_from_dict, run_regression
from reliability.verifier.run_v1_4_1 import VerificationRecordV141
from reliability.verifier.selection import Selection

ROOT = Path(__file__).resolve().parents[1]
RUN = Path("/home/sankalp/projects/wt-e2e/runs/e2e_v1_4_3_armB_um")
OUT = ROOT / "reports/paired_skip/armB"
INPUT_COMMIT = "4cb6ab54958a57c38b332662baefed2cd95b2271"
INPUT_DIR = "reports/rerun_v1/arm_B/analysis"
HANDLINGS = ("excluded", "missing")
ACCOUNTINGS = tuple(f"{p}_invalid_{h}" for h in HANDLINGS for p in "SCP")
DECISIONS = ("ACCEPT", "FLAG", "REJECT")
CARRY = "carried: no executed tests"
CARRY_IDS = {
    "astropy__astropy-13398", "astropy__astropy-14508", "django__django-13023",
    "django__django-13158", "django__django-14140", "django__django-15103",
    "django__django-16667", "matplotlib__matplotlib-24627", "pylint-dev__pylint-6903",
    "pytest-dev__pytest-7236", "sphinx-doc__sphinx-10323",
}
SKIP_GAP = re.compile(r"(confirmation: )?(base|patched): (?:raw SKIPPED: (.+)|(.+): skipped)")


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def committed_csv(name, *, columns=None):
    command = ["git", "show", f"{INPUT_COMMIT}:{INPUT_DIR}/{name}"]
    if columns:
        # The selected fields precede the quoted free-text fields. Project away
        # correctness before parsing the CSV or inspecting any row.
        with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE) as blob:
            data = subprocess.check_output(["cut", "-d,", "-f", columns], stdin=blob.stdout)
            require(blob.wait() == 0, f"Could not read committed {name}")
    else:
        data = subprocess.check_output(command, cwd=ROOT)
    return csv.DictReader(data.decode("utf-8").splitlines())


def read_csv(name):
    with (OUT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(name, fields, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def carry_decisions():
    outcomes = {instance_id: {} for instance_id in CARRY_IDS}
    stored_options = {name for name in ACCOUNTINGS if not name.startswith("P")}
    for row in committed_csv("signal_attribution.csv", columns="1-3,5-7"):
        instance_id, accounting = row["instance_id"], row["accounting"]
        if (instance_id not in outcomes or row["cohort"] != "primary"
                or row["signal"] != "V2" or accounting not in stored_options):
            continue
        options = outcomes[instance_id]
        require(accounting not in options, f"Duplicate carry-forward row for {instance_id}: {accounting}")
        options[accounting] = (row["outcome"], row["decision"])
    carried = {}
    for instance_id, options in sorted(outcomes.items()):
        require(options.keys() == stored_options and len(set(options.values())) == 1,
                f"Carry-forward decision mismatch for {instance_id}: {options}")
        outcome, decision = next(iter(options.values()))
        require(outcome == "NOT_AVAILABLE" and decision in DECISIONS,
                f"Unexpected carry-forward outcome for {instance_id}: {options}")
        carried[instance_id] = (outcome, decision)
    return carried


def read_record(instance_id):
    path = RUN / "tasks" / instance_id / "verification_record.full-v1.4.1.json"
    record = VerificationRecordV141.model_validate_json(path.read_bytes())
    require(record.instance_id == instance_id and record.decision.policy_version == "v1.4.1-full",
            f"Stored record does not match the instance or frozen policy: {instance_id}")
    return record


def captured_calls(record):
    folder = RUN / "tasks" / record.instance_id / "verification"
    tests = tuple(record.selected_tests)
    findings = record.regression.findings
    calls = []
    for is_patched, tree in enumerate(("base", "patched")):
        path = folder / f"{tree}.json"
        require(path.is_file(), f"Missing captured pass: {path}")
        capture = json.loads(path.read_text(encoding="utf-8"))
        require(capture.get("requested_tests") == list(tests),
                f"Captured initial selection differs from the stored record: {path}")
        require(findings.get(tree) is None or findings[tree] == capture,
                f"Captured pass differs from the stored record: {path}")
        calls.append((tests, bool(is_patched), 1800, run_from_dict(capture)))
    for capture in findings.get("confirmations", ()):
        confirmation = run_from_dict(capture)
        tree = confirmation.confirmation["tree"]
        require(tree in ("base", "patched") and confirmation.requested_tests,
                f"Invalid confirmation metadata: {record.instance_id}")
        calls.append((confirmation.requested_tests, tree == "patched", 1800, confirmation))
    return calls


def replay_v2(record, calls, accounting):
    policy, handling = accounting.split("_invalid_")
    return run_regression(
        record.instance_id, Selection(tests=tuple(record.selected_tests)), Replay(calls),
        RegressionConfig(skip_compatible=policy == "C", skip_paired=policy == "P",
                         invalid_as_missing=handling == "missing"),
    )


def decision_counts(rows):
    return {
        name: Counter(row[f"decision_{name}"] for row in rows)
        for name in ACCOUNTINGS
    }


def generate_decisions():
    completion = json.loads((RUN / "completion.json").read_text(encoding="utf-8"))
    patch_ids = set(completion["completed_tasks"]) - set(completion["no_patch_tasks"])
    require(completion["status"] == "COMPLETE" and len(patch_ids) == 51 and CARRY_IDS <= patch_ids,
            "Stored completion does not identify the expected 51 Arm B patch tasks")
    carried = carry_decisions()
    rows = []
    for instance_id in sorted(patch_ids):
        record = read_record(instance_id)
        row = {"instance_id": instance_id, "provenance": "replayed"}
        live = evidence_from_signals(record.signals)
        if instance_id in carried:
            row["provenance"] = CARRY
        else:
            calls = captured_calls(record)
        for name in ACCOUNTINGS:
            if instance_id in carried:
                outcome, decision = carried[instance_id]
            else:
                report = replay_v2(record, calls, name)
                v2 = regression_outcome(report)
                outcome = v2.value
                evidence = replace(live, regression=v2)
                decision = FullPolicyV141().decide(evidence).decision.value
            if name == "S_invalid_excluded":
                require((outcome, decision) == (record.regression.outcome.value, record.decision.decision.value),
                        f"Replayed S does not match the frozen V2 outcome and decision: {instance_id}")
            row[f"v2_{name}"] = outcome
            row[f"decision_{name}"] = decision
        rows.append(row)
    write_csv("decisions_label_free.csv", list(rows[0]), rows)
    write_csv("counts_label_free.csv", ("accounting", *DECISIONS), [
        {"accounting": name, **{decision: counts[decision] for decision in DECISIONS}}
        for name, counts in decision_counts(rows).items()
    ])


def check_decisions():
    rows = read_csv("decisions_label_free.csv")
    counts = decision_counts(rows)
    require(len(rows) == 51 and len({row["instance_id"] for row in rows}) == 51,
            "Expected 51 unique Arm B patch rows")
    violations = []
    for row in rows:
        for handling in HANDLINGS:
            s, p, c = (row[f"decision_{policy}_invalid_{handling}"] for policy in "SPC")
            if not ((s == "ACCEPT") <= (p == "ACCEPT") <= (c == "ACCEPT")):
                violations.append(f'{row["instance_id"]} ({handling}): S={s}, P={p}, C={c}')
    require(not violations, "ACCEPT set invariant failed:\n" + "\n".join(violations))

    expected = {
        row["accounting"]: tuple(int(row[decision]) for decision in DECISIONS)
        for row in committed_csv("decisions.csv") if row["scope"] == "patch"
    }
    require(expected.get("S_invalid_excluded") == (5, 42, 4)
            and expected.get("C_invalid_excluded") == (20, 27, 4),
            "Committed S/C counts do not match the requested benchmarks")
    mismatches = []
    for name, total in expected.items():
        actual = tuple(counts[name][decision] for decision in DECISIONS)
        if actual != total:
            mismatches.append(f"{name}: replay {actual}, committed {total}")
    require(not mismatches, "S/C decision counts differ:\n" + "\n".join(mismatches))

    fields = ("instance_id", "invalid_handling", "decision_P", "decision_C",
              "evidence", "skipped_tree", "test_id")
    differences = []
    for row in rows:
        for handling in HANDLINGS:
            accounting = f"P_invalid_{handling}"
            p, c = row[f"decision_{accounting}"], row[f"decision_C_invalid_{handling}"]
            if p == c:
                continue
            record = read_record(row["instance_id"])
            report = replay_v2(record, captured_calls(record), accounting)
            gaps = set()
            for gap in report.incompleteness:
                match = SKIP_GAP.fullmatch(gap)
                if match:
                    confirmation, tree, raw_id, selected_id = match.groups()
                    evidence = "raw" if raw_id else "selected"
                    if confirmation:
                        evidence = f"confirmation {evidence}"
                        tree = "confirmation"
                    gaps.add((evidence, tree, raw_id or selected_id))
            require(gaps, f"P/C decision for {record.instance_id} ({handling}) differs without a skip gap")
            differences.extend(
                dict(zip(fields, (record.instance_id, handling, p, c, *gap)))
                for gap in sorted(gaps)
            )
    write_csv("p_vs_c_differences.csv", fields, differences)
    print("PASS: ACCEPT set S ⊆ P ⊆ C under both INVALID_ID variants")
    for name, total in expected.items():
        print(f"PASS: {name} ACCEPT/FLAG/REJECT = {'/'.join(map(str, total))}")
    for handling in HANDLINGS:
        tasks = {row["instance_id"] for row in differences if row["invalid_handling"] == handling}
        print(f"P/C decision differences with INVALID_ID {handling}: {len(tasks)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("decisions", "check"))
    args = parser.parse_args()
    if args.step == "decisions":
        generate_decisions()
    else:
        check_decisions()
