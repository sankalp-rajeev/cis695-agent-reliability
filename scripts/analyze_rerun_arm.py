#!/usr/bin/env python3
"""Recompute sealed rerun decisions and analyze an arm under amendment A3."""

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path

from reliability.verifier.decision import SignalOutcome
from reliability.verifier.policy_v1_4 import evidence_from_signals
from reliability.verifier.policy_v1_4_1 import FullPolicyV141
from reliability.verifier.record import SignalKind
from reliability.verifier.run_v1_4_1 import VerificationRecordV141

PRIMARY = "S_invalid_excluded"
ACCOUNTINGS = (PRIMARY, "S_invalid_missing", "C_invalid_excluded", "C_invalid_missing")
DECISIONS = ("ACCEPT", "FLAG", "REJECT")
SIGNALS = tuple(SignalKind)
KINDS = ("R", "U", "X")
CATEGORIES = ("patch", "no_patch", "provider_blocked", "agent_infrastructure")
NA = "NOT_AVAILABLE"
Z = 1.959964
V2_MAP = {
    "PASS": "PASS",
    "FAIL": "FAIL",
    "REGRESSION_ERROR": "FAIL",
    "INCOMPLETE": NA,
    "NOT_AVAILABLE": NA,
    "BASELINE_UNRELIABLE": NA,
}
LABEL_FIELDS = (
    "instance_id",
    "patch_sha256",
    "oracle_outcome",
    "resolved",
    "fail_to_pass_passed",
    "fail_to_pass_total",
    "pass_to_pass_passed",
    "pass_to_pass_total",
    "harness_error_class",
    "wrong_patch_type",
)
ARM_B = "e2e_v1_4_3_armB_um"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json(path):
    return json.loads(path.read_bytes())


def unique_ids(ids):
    return len(ids) == len(set(ids)) and all(
        re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+", iid) for iid in ids
    )


class SealedInputs:
    def __init__(self, root, manifest):
        self.root = root.resolve(strict=True)
        raw = manifest.read_bytes()
        self.sha256 = digest(raw)
        checksum = manifest.with_name(manifest.name + ".sha256")
        require(
            checksum.read_text().split() == [self.sha256, manifest.name],
            "Seal manifest digest does not match its recorded SHA-256",
        )
        self.files = {}
        for line in raw.decode().splitlines():
            expected, name = line.split("  ", 1)
            path = Path(name)
            require(
                re.fullmatch(r"[0-9a-f]{64}", expected)
                and not path.is_absolute()
                and ".." not in path.parts
                and path.as_posix() == name
                and name not in self.files,
                f"Invalid manifest entry {name!r}",
            )
            self.files[name] = expected

    def read(self, name):
        require(name in self.files, f"Input is absent from the seal: {name}")
        path = self.root / name
        require(
            path.resolve(strict=True) == path and path.is_file(),
            f"Unexpected sealed input type: {name}",
        )
        raw = path.read_bytes()
        require(digest(raw) == self.files[name], f"Seal checksum mismatch: {name}")
        return raw

    def optional_json(self, name):
        path = self.root / name
        if name not in self.files:
            require(not path.exists() and not path.is_symlink(), f"Unsealed input: {name}")
            return None
        return json.loads(self.read(name))


@dataclass(frozen=True)
class Task:
    iid: str
    patch_sha256: str
    category: str
    record: VerificationRecordV141
    reports: dict

    @property
    def repo(self):
        return self.iid.rsplit("-", 1)[0]


def ledger_for_arm(path, run):
    data = json.loads(path.read_bytes(), parse_float=Decimal)
    require(data["version"] == 1, "Unexpected spend ledger version")
    job = str(run)
    rows = [row for row in data["calls"] if row["job"] == job]
    require(
        rows and all(row["state"] == "settled" for row in rows),
        "The arm ledger must have calls, all settled",
    )
    require(len({row["id"] for row in rows}) == len(rows), "Duplicate arm ledger call")
    require(
        not any(
            row["job"] == job and row["state"] == "active" for row in data.get("stage_escrows", [])
        ),
        "Active arm ledger escrow",
    )
    by_provider = defaultdict(Decimal)
    by_task = defaultdict(Decimal)
    filtered = Counter()
    for row in rows:
        require(row["provider"] in {"deepseek", "umgpt"}, "Unknown arm ledger provider")
        cost = Decimal(row["cost_usd"])
        require(cost.is_finite() and cost >= 0, "Invalid arm ledger cost")
        by_provider[row["provider"]] += cost
        by_task[row["task"]] += cost
        if row["stage"] == "agent" and (
            row.get("finish_reason") == "content_filter" or row.get("any_filtered") is True
        ):
            filtered[row["task"]] += 1
    return by_provider, by_task, filtered


def read_tasks(seal, filtered):
    completion = json.loads(seal.read("completion.json"))
    ids = completion["completed_tasks"]
    require(
        completion["status"] in {"COMPLETE", "STOPPED_BUDGET"} and ids and unique_ids(ids),
        "Unexpected completion status or completed task list",
    )
    agent_infra = set(completion["agent_infrastructure_tasks"])
    require(agent_infra <= set(ids), "Agent infrastructure task outside completed cohort")
    tasks = []
    raw_no_patch = set()
    for iid in sorted(ids):
        base = f"tasks/{iid}/"
        patch = seal.read(base + "patch.diff")
        has_patch = bool(patch.strip())
        patch_hash = seal.files[base + "patch.diff"]
        record = VerificationRecordV141.model_validate_json(
            seal.read(base + "verification_record.full-v1.4.1.json")
        )
        receipt = json.loads(seal.read(base + "task_completion.json"))
        require(
            record.instance_id == iid
            and record.patch_sha256 == f"sha256:{patch_hash}"
            and receipt["complete"] is True
            and receipt["patch_sha256"] == record.patch_sha256
            and record.decision.policy_version == "v1.4.1-full",
            f"Completion and verifier record identity mismatch: {iid}",
        )
        require(
            not has_patch or iid not in agent_infra,
            f"Task has a patch and is marked as agent infrastructure: {iid}",
        )
        if has_patch:
            category = "patch"
        elif iid in filtered:
            category = "provider_blocked"
        elif iid in agent_infra:
            category = "agent_infrastructure"
        else:
            category = "no_patch"
        if not has_patch and iid not in agent_infra:
            raw_no_patch.add(iid)
        v2 = seal.optional_json(base + "verification/v2_policies.json")
        if v2 is not None:
            require(
                v2["instance_id"] == iid and set(v2["policies"]) == set(ACCOUNTINGS),
                f"Unexpected V2 report identity or accountings: {iid}",
            )
        else:
            require(
                record.regression.outcome is SignalOutcome.NOT_AVAILABLE,
                f"Missing V2 report for available recorded V2: {iid}",
            )
        tasks.append(Task(iid, patch_hash, category, record, v2["policies"] if v2 else {}))
    require(
        raw_no_patch == set(completion["no_patch_tasks"]),
        "Frozen patches disagree with runner no-patch counts",
    )
    return tasks


def report_absence(report):
    if report["signal"] == "INCOMPLETE":
        return "incomplete"
    if report["signal"] == "BASELINE_UNRELIABLE" or (report.get("selection") or {}).get("tests"):
        return "error"
    return "nothing_to_check"


def evaluate(tasks):
    policy = FullPolicyV141()
    evaluations = {}
    for task in tasks:
        record = task.record
        live = evidence_from_signals(record.signals)
        original = policy.decide(live)
        require(
            original.decision == record.decision.decision
            and original.reasons == record.decision.reasons,
            f"Recomputed live decision or reasons disagree with record: {task.iid}",
        )
        per_accounting = {}
        for accounting in ACCOUNTINGS:
            evidence = live
            regression_absence = record.regression.absence
            if task.reports:
                report = task.reports[accounting]
                outcome = SignalOutcome(V2_MAP[report["signal"]])
                evidence = replace(live, regression=outcome)
                regression_absence = report_absence(report) if outcome.value == NA else ""
            verdict = policy.decide(evidence)
            if accounting == PRIMARY:
                require(
                    verdict.decision == record.decision.decision,
                    f"Policy S with INVALID_ID excluded disagrees with live decision: {task.iid}",
                )
                require(
                    evidence.regression == live.regression,
                    f"Policy S with INVALID_ID excluded disagrees with live V2: {task.iid}",
                )
                regression_absence = record.regression.absence
            outcomes = {
                kind: (
                    getattr(evidence, kind.value).value,
                    regression_absence
                    if kind == SignalKind.REGRESSION
                    else record.signals[kind].absence,
                )
                for kind in SIGNALS
            }
            reasons = record.decision.reasons if accounting == PRIMARY else verdict.reasons
            per_accounting[accounting] = (verdict.decision.value, reasons, outcomes, evidence)
        evaluations[task.iid] = per_accounting
    return evaluations


def counts_by_decision(decisions):
    counts = Counter(decisions)
    return {decision: counts[decision] for decision in DECISIONS}


def check_seal_summary(tasks, decisions, summary, by_provider, filtered, run):
    primary = {iid: accountings[PRIMARY][0] for iid, accountings in decisions.items()}
    counts = counts_by_decision(primary.values())
    patch_counts = counts_by_decision(primary[t.iid] for t in tasks if t.category == "patch")
    categories = {category: sum(t.category == category for t in tasks) for category in CATEGORIES}
    blocked = sorted(t.iid for t in tasks if t.category == "provider_blocked")
    require(
        all(primary[t.iid] == "REJECT" for t in tasks if t.category != "patch"),
        "An empty-patch task was not REJECT",
    )
    require(
        counts == summary["decision_counts"] and len(tasks) == summary["completed_tasks"],
        f"Live decision or task count differs from seal: {counts}, {len(tasks)} tasks",
    )
    require(
        categories["no_patch"] == summary["no_patch_tasks_after_a1"]
        and categories["agent_infrastructure"] == summary["agent_infrastructure_tasks_after_a1"]
        and blocked == sorted(summary["provider_blocked_instance_ids"]),
        f"Task categories differ from seal: {categories}, blocked {blocked}",
    )
    require(
        sum(filtered.values()) == summary["repair_filtered_calls"],
        "Number of filtered repair calls differs from seal",
    )
    total = sum(by_provider.values(), Decimal(0))
    cent = Decimal("0.01")
    require(
        str(run) == summary["ledger"]["job"]
        and total.quantize(cent) == Decimal(summary["ledger"]["spend_usd"]).quantize(cent),
        f"Total arm spend differs from seal: {total}",
    )
    if run.name == ARM_B:
        require(
            len(tasks) == 92
            and counts == dict(zip(DECISIONS, (5, 42, 45), strict=True))
            and patch_counts == dict(zip(DECISIONS, (5, 42, 4), strict=True))
            and blocked == ["django__django-13569"],
            f"Arm B label-free expectations failed: {counts}, patch decisions {patch_counts}, "
            f"provider-blocked {blocked}",
        )
    return {
        "completed_tasks": len(tasks),
        "categories": categories,
        "live_decisions": counts,
        "patch_decisions": patch_counts,
        "reproduced_live_decisions": len(tasks),
        "provider_blocked_tasks": blocked,
        "filtered_repair_calls": sum(filtered.values()),
        "v2_reports": sum(bool(t.reports) for t in tasks),
        "spend_usd": float(total),
        "spend_by_provider_usd": {key: float(value) for key, value in sorted(by_provider.items())},
    }


def leakage_findings(directory, ids):
    findings = {kind: Counter() for kind in ("T3_name", "T3_content", "T4", "awareness")}
    summary = load_json(directory / "tiers/summary.json")
    roles = set()
    for path in sorted((directory / "tiers/artifacts").glob("*/*/*.json")):
        record = load_json(path)
        iid, role = record["instance_id"], record["role"]
        require(
            role in {"repair", "generator"} and (iid, role) not in roles,
            f"Unexpected or duplicate audit row: {iid}, {role}",
        )
        roles.add((iid, role))
        if record["excluded"]:
            continue
        for fact in record["facts"]:
            if (
                fact["category"] == "answer"
                and fact["guard_pass"]
                and not fact.get("defined_at_first_mention")
            ):
                if fact["first_seen_in"] == "tool_output":
                    findings["T4"][iid, role] += 1
                elif fact["first_seen_in"] == "model_output":
                    kind = "T3_name" if fact["field"] == "hidden_test_name" else "T3_content"
                    findings[kind][iid, role] += 1
            elif fact["category"] == "awareness" or (
                fact["category"] == "history" and not fact["setup_only"]
            ):
                findings["awareness"][iid, role] += 1
    require(len(roles) == summary["rows"] and roles, "Missing audit artifacts")
    require(
        {iid for iid, _ in findings["T4"]} == set(summary["T4_tasks"]),
        "Task-level T4 findings disagree with audit summary",
    )
    rows = []
    sets = {}
    for kind, counts in findings.items():
        valid = [(iid, role, count) for (iid, role), count in sorted(counts.items()) if iid in ids]
        sets[kind] = {iid for iid, _, _ in valid}
        rows.extend((kind, iid, role, count) for iid, role, count in valid)
    return rows, sets


def labels_for_tasks(path, tasks):
    by_id = {task.iid: task for task in tasks}
    labels = {}
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == LABEL_FIELDS, "Unexpected label columns")
        for row in reader:
            iid = row["instance_id"]
            require(
                iid in by_id and iid not in labels and None not in row and None not in row.values(),
                f"Unexpected, duplicate, or malformed label row: {iid}",
            )
            task = by_id[iid]
            outcome = row["oracle_outcome"]
            require(
                row["patch_sha256"] == task.patch_sha256
                and (outcome == "empty_patch") == (task.category != "patch"),
                f"Label does not match frozen patch: {iid}",
            )
            fail_pass, fail_total, pass_pass, pass_total = (
                int(row[key]) for key in LABEL_FIELDS[4:8]
            )
            require(
                0 <= fail_pass <= fail_total and 0 <= pass_pass <= pass_total,
                f"Bad label test counts: {iid}",
            )
            if outcome in {"patch_apply_failed", "infra_error"}:
                wrong_type = "X"
            elif outcome == "unresolved" and (pass_pass < pass_total or fail_pass < fail_total):
                wrong_type = "R" if pass_pass < pass_total else "U"
            elif outcome in {"empty_patch", "resolved"} and (fail_pass, pass_pass) == (
                fail_total,
                pass_total,
            ):
                wrong_type = ""
            else:
                raise ValueError(f"Label outcome differs from its test counts: {iid}")
            correct = outcome == "resolved"
            require(
                row["resolved"] == str(correct).lower()
                and row["wrong_patch_type"] == wrong_type
                and bool(row["harness_error_class"]) == (wrong_type == "X"),
                f"Label classification disagrees with grader evidence: {iid}",
            )
            labels[iid] = correct, wrong_type
    require(labels.keys() == by_id.keys(), "Labels and completion task sets differ")
    return labels


def wilson(k, n):
    if not n:
        return NA, NA, NA
    probability = k / n
    z2 = Z * Z
    divisor = 1 + z2 / n
    center = probability + z2 / (2 * n)
    spread = Z * math.sqrt((probability * (1 - probability) + z2 / (4 * n)) / n)
    return probability, max(0.0, (center - spread) / divisor), min(1.0, (center + spread) / divisor)


def newcombe(k1, n1, k2, n2):
    if not n1 or not n2:
        return NA, NA, NA
    p, lower_p, upper_p = wilson(k1, n1)
    q, lower_q, upper_q = wilson(k2, n2)
    difference = p - q
    return (
        difference,
        difference - math.hypot(p - lower_p, upper_q - q),
        (difference + math.hypot(upper_p - p, q - lower_q)),
    )


def fisher(a, b, c, d):
    n1, n2 = a + b, c + d
    if not n1 or not n2:
        return NA
    accepts = a + c

    def weight(k):
        return math.comb(n1, k) * math.comb(n2, accepts - k)

    observed = weight(a)
    support = range(max(0, accepts - n2), min(accepts, n1) + 1)
    return sum(w for k in support if (w := weight(k)) <= observed) / math.comb(n1 + n2, accepts)


def table_cells(tasks, labels, verdicts):
    return Counter((verdicts[t.iid], labels[t.iid][0]) for t in tasks)


def rates(cells):
    correct = sum(cells[decision, True] for decision in DECISIONS)
    wrong = sum(cells[decision, False] for decision in DECISIONS)
    a, c = cells["ACCEPT", True], cells["ACCEPT", False]
    b, d = correct - a, wrong - c
    amounts = (
        ("accept_precision", a, a + c),
        ("base_rate", correct, correct + wrong),
        ("wrong_not_accepted", d, wrong),
        ("all_not_accepted", b + d, correct + wrong),
        ("correct_not_accepted", b, correct),
    )
    rows = [(name, k, n, "", "", *wilson(k, n), "Wilson 95%") for name, k, n in amounts]
    overlapping = newcombe(d, wrong, b + d, correct + wrong)
    supplemental = newcombe(d, wrong, b, correct)
    rows.extend(
        (
            (
                "chance_difference",
                d,
                wrong,
                b + d,
                correct + wrong,
                *overlapping,
                "Newcombe 10 95% (approximate, overlapping cohorts)",
            ),
            ("wrong_correct_difference", d, wrong, b, correct, *supplemental, "Newcombe 10 95%"),
            (
                "fisher_exact_p",
                "",
                "",
                "",
                "",
                fisher(a, b, c, d),
                NA,
                NA,
                "Two-sided Fisher exact",
            ),
        )
    )
    qualifies = supplemental[0] != NA and supplemental[0] > 0 and supplemental[1] > 0
    return rows, qualifies


def ablate(evidence, kind):
    replacements = {kind.value: SignalOutcome.PASS}
    if kind == SignalKind.INTEGRITY:
        replacements.update(
            patch_applies=True,
            prohibited_manipulation=False,
            high_severity_risk=False,
            v1_analysis_incomplete=False,
        )
    if kind == SignalKind.STATIC:
        replacements["v3_absolute_failure"] = False
    return FullPolicyV141().decide(replace(evidence, **replacements)).decision.value


TABLE_FIELDS = {
    "decisions": ("accounting", "scope", "ACCEPT", "FLAG", "REJECT"),
    "leakage": ("kind", "instance_id", "role", "findings"),
    "leakage_counts": ("kind", "tasks", "findings"),
    "patch_tasks": ("instance_id", "decision", "correctness"),
    "decision_by_correctness": ("accounting", "cohort", "decision", "correct", "wrong"),
    "metrics": (
        "accounting",
        "cohort",
        "metric",
        "k",
        "n",
        "reference_k",
        "reference_n",
        "estimate",
        "lower",
        "upper",
        "method",
    ),
    "wrong_types": (
        "accounting",
        "cohort",
        "type",
        "wrong",
        "ACCEPT",
        "FLAG",
        "REJECT",
        "not_accepted",
        "rate",
        "lower",
        "upper",
    ),
    "signal_attribution": (
        "accounting",
        "cohort",
        "instance_id",
        "correctness",
        "decision",
        "signal",
        "outcome",
        "absence",
        "absence_detail",
        "decision_reasons",
    ),
    "signal_counts": (
        "accounting",
        "cohort",
        "correctness",
        "signal",
        "outcome",
        "absence",
        "tasks",
    ),
    "reason_counts": ("accounting", "cohort", "correctness", "reason", "tasks"),
    "exploratory_ablation": ("accounting", "cohort", "forced_pass", "decision", "correct", "wrong"),
    "exploratory_repositories": (
        "accounting",
        "cohort",
        "repository",
        "decision",
        "correct",
        "wrong",
    ),
    "exploratory_cost": (
        "accounting",
        "cohort",
        "total_usd",
        "correct_ACCEPT",
        "cost_per_correct_ACCEPT_usd",
        "median_task_usd",
    ),
    "paired_decision_by_correctness": ("arm", "decision", "correct", "wrong"),
    "paired_differences": (
        "shared_patch_tasks",
        "different_decision",
        "different_correctness",
        "either",
    ),
}


def class_name(is_correct):
    return "correct" if is_correct else "wrong"


def panel_tables(tables, accounting, cohort, group, labels, decisions, spend, median_spend):
    prefix = accounting, cohort
    verdicts = {task.iid: decisions[task.iid][accounting][0] for task in group}
    cells = table_cells(group, labels, verdicts)
    tables["decision_by_correctness"].extend(
        (*prefix, decision, cells[decision, True], cells[decision, False]) for decision in DECISIONS
    )
    metrics, qualifies = rates(cells)
    tables["metrics"].extend((*prefix, *metric) for metric in metrics)
    type_decisions = Counter((labels[iid][1], verdict) for iid, verdict in verdicts.items())
    for wrong_type in KINDS:
        a, f, r = (type_decisions[wrong_type, decision] for decision in DECISIONS)
        tables["wrong_types"].append(
            (*prefix, wrong_type, a + f + r, a, f, r, f + r, *wilson(f + r, a + f + r))
        )

    count_signals, count_reasons = Counter(), Counter()
    for task in group:
        decision, reasons, outcomes, _ = decisions[task.iid][accounting]
        if task.category != "patch" or decision == "ACCEPT":
            continue
        correctness = class_name(labels[task.iid][0])
        count_reasons.update((correctness, reason) for reason in reasons)
        for index, kind in enumerate(SIGNALS, 1):
            outcome, absence = outcomes[kind]
            signal = f"V{index}"
            absence = str(absence.value if hasattr(absence, "value") else absence or "")
            detail = ""
            if outcome == NA:
                raw = task.record.signals[kind]
                if kind == SignalKind.REGRESSION and task.reports and accounting != PRIMARY:
                    detail = task.reports[accounting]["signal"]
                else:
                    detail = raw.findings.get("absence_reason") or raw.detail
            tables["signal_attribution"].append(
                (
                    *prefix,
                    task.iid,
                    correctness,
                    decision,
                    signal,
                    outcome,
                    absence,
                    detail,
                    " | ".join(reasons),
                )
            )
            count_signals[correctness, signal, outcome, absence] += 1
    for name, counts in (("signal_counts", count_signals), ("reason_counts", count_reasons)):
        tables[name].extend((*prefix, *key, count) for key, count in sorted(counts.items()))

    for index, kind in enumerate(SIGNALS, 1):
        alternative = {t.iid: ablate(decisions[t.iid][accounting][3], kind) for t in group}
        cross = table_cells(group, labels, alternative)
        tables["exploratory_ablation"].extend(
            (*prefix, f"V{index}", decision, cross[decision, True], cross[decision, False])
            for decision in DECISIONS
        )
    by_repo = defaultdict(list)
    for task in group:
        by_repo[task.repo].append(task)
    for repo, repo_tasks in sorted(by_repo.items()):
        cross = table_cells(repo_tasks, labels, verdicts)
        tables["exploratory_repositories"].extend(
            (*prefix, repo, d, cross[d, True], cross[d, False]) for d in DECISIONS
        )
    accepted_correct = cells["ACCEPT", True]
    tables["exploratory_cost"].append(
        (
            *prefix,
            float(spend),
            accepted_correct,
            float(spend / accepted_correct) if accepted_correct else NA,
            float(median_spend),
        )
    )
    return {
        "tasks": len(group),
        "correct": sum(labels[task.iid][0] for task in group),
        "better_than_chance": qualifies,
    }


def pairing(tables, other):
    comparison = {}
    with (other / "patch_tasks.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        require(
            tuple(next(reader, ())) == TABLE_FIELDS["patch_tasks"], "Unexpected paired task schema"
        )
        for iid, decision, correctness in reader:
            require(
                iid not in comparison
                and unique_ids([iid])
                and decision in DECISIONS
                and correctness in {"correct", "wrong"},
                f"Invalid paired task row: {iid}",
            )
            comparison[iid] = decision, correctness
    current = {iid: (decision, correctness) for iid, decision, correctness in tables["patch_tasks"]}
    shared = sorted(current.keys() & comparison.keys())
    for name, arm in (("current", current), ("paired_with", comparison)):
        counts = Counter(arm[iid] for iid in shared)
        tables["paired_decision_by_correctness"].extend(
            (name, d, counts[d, "correct"], counts[d, "wrong"]) for d in DECISIONS
        )
    result = (
        len(shared),
        sum(current[iid][0] != comparison[iid][0] for iid in shared),
        sum(current[iid][1] != comparison[iid][1] for iid in shared),
        sum(current[iid] != comparison[iid] for iid in shared),
    )
    tables["paired_differences"].append(result)
    return dict(zip(TABLE_FIELDS["paired_differences"], result, strict=True))


def markdown_cell(value):
    if isinstance(value, float):
        return f"{value:.9g}"
    return str(value).replace("|", r"\|").replace("\n", "<br>")


def publish(out, tables, counts):
    files = [out / "counts.json", out / "results.md", *(out / f"{name}.csv" for name in tables)]
    require(
        not any(path.exists() or path.is_symlink() for path in files),
        "Output files already exist, aborting to keep the original results",
    )
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# Rerun arm results", ""]
    for name, rows in tables.items():
        fields = TABLE_FIELDS[name]
        with (out / f"{name}.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fields)
            writer.writerows(rows)
        lines.extend(
            (
                f"## {name.replace('_', ' ').capitalize()}",
                "",
                "| " + " | ".join(fields) + " |",
                "| " + " | ".join("---" for _ in fields) + " |",
            )
        )
        for row in rows:
            lines.append("| " + " | ".join(map(markdown_cell, row)) + " |")
        lines.append("")
    with (out / "counts.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(counts, sort_keys=True, indent=2, allow_nan=False) + "\n")
    with (out / "results.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("run", "manifest", "ledger", "leakage", "out"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--stage", type=int, choices=(1, 2), required=True)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--paired-with", type=Path)
    args = parser.parse_args()
    if (args.labels is not None) != (args.stage == 2) or (args.paired_with and args.stage != 2):
        parser.error("--stage 2 and --labels are required together and for pairing")

    seal = SealedInputs(args.run, args.manifest)
    out = args.out.resolve()
    require(
        not out.is_relative_to(seal.root)
        and not out.is_relative_to(args.leakage.resolve())
        and (not args.paired_with or out != args.paired_with.resolve()),
        "Output overlaps a protected input location",
    )
    provider, task_spend, filtered = ledger_for_arm(args.ledger, seal.root)
    tasks = read_tasks(seal, filtered)
    decisions = evaluate(tasks)
    summary = load_json(args.manifest.with_name("summary.json"))
    checked = check_seal_summary(tasks, decisions, summary, provider, filtered, seal.root)
    print(json.dumps(checked, sort_keys=True), flush=True)
    ids = {task.iid for task in tasks}
    leakage, leakage_sets = leakage_findings(args.leakage, ids)
    leakage_counts = Counter()
    for kind, _, _, count in leakage:
        leakage_counts[kind] += count
    tables = {
        "decisions": [],
        "leakage": leakage,
        "leakage_counts": [
            (kind, len(leakage_sets[kind]), leakage_counts[kind]) for kind in leakage_sets
        ],
    }
    counts = {
        "stage": args.stage,
        "run": seal.root.name,
        "seal_manifest_sha256": seal.sha256,
        "self_checks": checked,
        "leakage_task_counts": {kind: len(ids) for kind, ids in leakage_sets.items()},
    }
    for accounting in ACCOUNTINGS:
        for category in ("all", *CATEGORIES):
            totals = counts_by_decision(
                decisions[t.iid][accounting][0] for t in tasks if category in ("all", t.category)
            )
            tables["decisions"].append((accounting, category, *totals.values()))

    if args.stage == 2:
        labels = labels_for_tasks(args.labels, tasks)
        patches = [task for task in tasks if task.category == "patch"]
        tables["patch_tasks"] = [
            (t.iid, decisions[t.iid][PRIMARY][0], class_name(labels[t.iid][0])) for t in patches
        ]
        for name in TABLE_FIELDS:
            if name not in tables and not name.startswith("paired_"):
                tables[name] = []
        t4 = leakage_sets["T4"]
        t3_name = leakage_sets["T3_name"]
        groups = {
            "primary": patches,
            "including_no_patch": [t for t in tasks if t.category in {"patch", "no_patch"}],
            "including_no_patch_and_provider_blocked": [
                t for t in tasks if t.category != "agent_infrastructure"
            ],
            "excluding_T4": [t for t in patches if t.iid not in t4],
            "excluding_T4_and_T3_name": [t for t in patches if t.iid not in t4 | t3_name],
        }
        median = statistics.median(task_spend.get(t.iid, Decimal(0)) for t in tasks)
        spend = sum(provider.values(), Decimal(0))
        counts["panels"] = {
            accounting: {
                name: panel_tables(
                    tables, accounting, name, group, labels, decisions, spend, median
                )
                for name, group in groups.items()
            }
            for accounting in ACCOUNTINGS
        }
        if args.paired_with:
            tables.update(paired_decision_by_correctness=[], paired_differences=[])
            counts["paired"] = pairing(tables, args.paired_with)
    publish(out, tables, counts)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError) as exc:
        raise SystemExit(f"Analysis hard stop: {exc}") from exc
