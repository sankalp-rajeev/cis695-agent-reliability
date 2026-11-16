"""Offline golden and delta producer. Read only verification records, never labels."""

import csv
import hashlib
import json
from pathlib import Path

from reliability.verifier.decision import Evidence, FullPolicy, SignalOutcome
from reliability.verifier.policy_v1_4 import EvidenceV14, FullPolicyV14

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
AUDIT = ROOT / "reports/next_phases/phase7_signal_audit"


def write_csv(name, rows, fields):
    with (OUT / name).open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    golden, delta, inputs = [], [], []
    for row in csv.DictReader((AUDIT / "record_inventory_all.csv").open()):
        path = ROOT / row["record"]
        assert path.name == "verification_record.full.json"
        blob = path.read_bytes()
        record = json.loads(blob)
        flags = record["integrity"]["findings"]
        values = {
            k: SignalOutcome(record[k]["outcome"])
            for k in ("integrity", "regression", "static", "reproduction")
        }
        values.update(
            {
                k: flags.get(k, default)
                for k, default in (
                    ("patch_applies", True),
                    ("high_severity_risk", False),
                    ("prohibited_manipulation", False),
                )
            }
        )
        old = FullPolicy().decide(Evidence(**values))
        stored = record["decision"]
        entry = {k: old.as_dict()[k] for k in stored}
        assert entry == stored, (row["task"], entry, stored)
        summary = record["static"]["findings"].get("summary", {})
        absolute = any(summary.get(k) == "FAIL" for k in ("syntax", "import"))
        new = FullPolicyV14().decide(EvidenceV14(**values, v3_absolute_failure=absolute))
        cause = "v3_absolute_failure" if old.decision != new.decision else ""
        golden.append(
            {
                "task": row["task"],
                "stored": stored["decision"],
                "v1_3": old.decision.value,
                "exact_record_match": "yes",
            }
        )
        delta.append(
            {
                "task": row["task"],
                "v1_3": old.decision.value,
                "v1_4": new.decision.value,
                "changed": "yes" if cause else "no",
                "cause": cause,
            }
        )
        # Snapshot only policy inputs, no outcomes about repair correctness.
        inputs.append(
            {
                "task": row["task"],
                "record": row["record"],
                "sha256": hashlib.sha256(blob).hexdigest(),
                "signals": {
                    k: v.value if isinstance(v, SignalOutcome) else v for k, v in values.items()
                },
                "summary": summary,
                "stored_decision": stored,
            }
        )
    assert len(golden) == 100
    write_csv("golden.csv", golden, ["task", "stored", "v1_3", "exact_record_match"])
    write_csv("delta.csv", delta, ["task", "v1_3", "v1_4", "changed", "cause"])
    (OUT / "policy_inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    print(
        json.dumps({"golden": len(golden), "changes": [r for r in delta if r["changed"] == "yes"]})
    )


if __name__ == "__main__":
    main()
