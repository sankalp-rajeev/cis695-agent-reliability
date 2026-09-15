"""Aggregate SWE-bench harness reports for a run directory.

One report is written per single-instance run, so the denominator is
`total_instances` (what the harness actually evaluated), not
`submitted_instances` (every row in the predictions file).
"""

import glob
import json
import sys

run_dir = sys.argv[1]
expected_resolved = int(sys.argv[2])

evaluated = 0
resolved = 0
infra = 0
empty = 0
rows = []

for path in sorted(glob.glob(f"{run_dir}/*.json")):
    with open(path) as fh:
        d = json.load(fh)
    evaluated += d["total_instances"]
    resolved += d["resolved_instances"]
    infra += d["infra_failure_instances"]
    empty += d["empty_patch_instances"]
    inst = (d["submitted_ids"] and d["completed_ids"] or d["submitted_ids"])[:1]
    rows.append(
        {
            "instance": (d["resolved_ids"] or d["unresolved_ids"] or d["empty_patch_ids"] or inst or ["?"])[0],
            "evaluated": d["total_instances"],
            "resolved": d["resolved_instances"],
            "unresolved": d["unresolved_instances"],
            "empty_patch": d["empty_patch_instances"],
            "infra_failure": d["infra_failure_instances"],
            "failure_reasons": d["failure_reasons"],
        }
    )

for r in rows:
    print(
        f"{r['instance']:35s} evaluated={r['evaluated']} resolved={r['resolved']} "
        f"unresolved={r['unresolved']} empty_patch={r['empty_patch']} infra={r['infra_failure']}"
    )
    if r["failure_reasons"]:
        print(f"{'':35s} failure_reasons={r['failure_reasons']}")

print()
print(f"evaluated={evaluated}  resolved={resolved}  infra_failures={infra}  empty_patches={empty}")
ok = evaluated == 3 and resolved == expected_resolved and infra == 0
print(f"expected resolved={expected_resolved}/3 -> {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
