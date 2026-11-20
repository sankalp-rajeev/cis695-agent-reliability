"""Join committed Arm B correctness labels after the label-free checks pass."""

from collections import Counter

from analyze_rerun_arm import wilson
from replay_paired_skip_arm_b import (
    ACCOUNTINGS,
    DECISIONS,
    HANDLINGS,
    OUT,
    check_decisions,
    committed_csv,
    read_csv,
    require,
    write_csv,
)


def correctness_labels(decisions):
    labels = {}
    for row in committed_csv("patch_tasks.csv"):
        instance_id, correctness = row["instance_id"], row["correctness"]
        require(
            instance_id in decisions and instance_id not in labels,
            f"Unexpected or duplicate correctness row: {instance_id}",
        )
        require(correctness in ("correct", "wrong"), f"Invalid correctness label: {instance_id}")
        require(
            row["decision"] == decisions[instance_id]["decision_S_invalid_excluded"],
            f"Stored primary decision differs from the label-free replay: {instance_id}",
        )
        labels[instance_id] = correctness
    require(labels.keys() == decisions.keys(), "Correctness labels do not cover the Arm B replay")
    return labels


def write_summary(cells, labels):
    totals = Counter(labels.values())
    correct, wrong = totals["correct"], totals["wrong"]
    lines = [
        "# Arm B paired-skip replay",
        "",
        (
            "The replay covers 51 gpt-4.1-mini Arm B patches. V2 was recomputed from "
            "stored evidence for 40 patches. For the 11 tasks with no executed tests, "
            "the four stored S and C variants agreed on V2 `NOT_AVAILABLE` and on "
            "the decision. Both P variants carry those results forward. The frozen "
            "v1.4.1 decision rule used the stored V1, V3, and V4 values."
        ),
        "",
        (
            "Before joining correctness labels, the replay reproduced 5 ACCEPT, "
            "42 FLAG, and 4 REJECT under S with `INVALID_ID` excluded, and "
            "20 ACCEPT, 27 FLAG, and 4 REJECT under C. The ACCEPT sets satisfied "
            "S ⊆ P ⊆ C under both `INVALID_ID` variants. P and C agreed on every "
            "task in both variants. [Label-free decisions](decisions_label_free.csv) "
            "· [Decision counts](counts_label_free.csv) · "
            "[P/C decision differences](p_vs_c_differences.csv)"
        ),
        "",
        (
            f"The committed labels identify {correct} correct patches and {wrong} wrong "
            "patches. Held back means FLAG or REJECT. The last column subtracts "
            "the correct-patch held-back rate from the wrong-patch held-back rate."
        ),
    ]
    for handling in HANDLINGS:
        lines.extend(
            (
                "",
                f"## INVALID_ID {handling}",
                "",
                (
                    "| Policy | ACCEPT (correct + wrong) | Precision (95% Wilson CI) | Coverage | "
                    "Correct patches accepted | Wrong held back | Correct held back | Difference |"
                ),
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for policy in "SCP":
            counts = cells[f"{policy}_invalid_{handling}"]
            accepted_correct = counts["ACCEPT", "correct"]
            accepted_wrong = counts["ACCEPT", "wrong"]
            accepted = accepted_correct + accepted_wrong
            coverage = accepted / len(labels)
            precision, lower, upper = wilson(accepted_correct, accepted)
            held_correct = (correct - accepted_correct) / correct
            held_wrong = (wrong - accepted_wrong) / wrong
            lines.append(
                f"| {policy} | {accepted} ({accepted_correct} + {accepted_wrong}) | "
                f"{precision:.1%} [{lower:.1%}, {upper:.1%}] | "
                f"{accepted}/{len(labels)} ({coverage:.1%}) | "
                f"{accepted_correct}/{correct} ({accepted_correct / correct:.1%}) | "
                f"{held_wrong:.1%} | {held_correct:.1%} | "
                f"{100 * (held_wrong - held_correct):+.1f} pp |"
            )
    lines.extend(
        (
            "",
            (
                "Policy P was designed after the Arm B and DeepSeek correctness labels "
                "were seen, so the replay is exploratory. Policy S remains primary. "
                "Adopting P as primary requires a protocol amendment frozen before Arm A "
                "and the 200-task run."
            ),
            "",
            (
                "The DeepSeek Phase 4 V2 run directory was not found on this machine. "
                "The DeepSeek replay is pending."
            ),
            "",
        )
    )
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    check_decisions()
    rows = {row["instance_id"]: row for row in read_csv("decisions_label_free.csv")}
    labels = correctness_labels(rows)
    cells = {
        name: Counter(
            (row[f"decision_{name}"], labels[instance_id]) for instance_id, row in rows.items()
        )
        for name in ACCOUNTINGS
    }
    write_csv(
        "decision_by_correctness.csv",
        ("accounting", "decision", "correct", "wrong"),
        [
            {
                "accounting": name,
                "decision": decision,
                "correct": counts[decision, "correct"],
                "wrong": counts[decision, "wrong"],
            }
            for name, counts in cells.items()
            for decision in DECISIONS
        ],
    )
    write_summary(cells, labels)


if __name__ == "__main__":
    main()
