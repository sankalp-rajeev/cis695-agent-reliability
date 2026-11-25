#!/usr/bin/env python3
"""Independently verify rerun analysis tables using only the standard library."""

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

OPTIONS = ("S_invalid_excluded", "S_invalid_missing", "C_invalid_excluded", "C_invalid_missing")
LIVE = OPTIONS[0]
CHOICES = ("ACCEPT", "FLAG", "REJECT")
LAYERS = ("integrity", "regression", "static", "reproduction")
TASK_TYPES = ("patch", "no_patch", "provider_blocked", "agent_infrastructure")
TYPES = ("R", "U", "X")
UNAVAILABLE = "NOT_AVAILABLE"
TOLERANCE = 1e-9
GRADE_COLUMNS = (
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


def check(ok, failure):
    if not ok:
        raise ValueError(failure)


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def task_id(value):
    return re.fullmatch(r"[a-zA-Z0-9_.-]+__[a-zA-Z0-9_.-]+-[0-9]+", value)


class Run:
    def __init__(self, directory, manifest):
        self.directory = directory.resolve(strict=True)
        manifest_bytes = manifest.read_bytes()
        self.manifest_digest = checksum(manifest_bytes)
        receipt = manifest.parent / (manifest.name + ".sha256")
        check(
            receipt.read_text().split() == [self.manifest_digest, manifest.name],
            "Manifest SHA-256 receipt differs",
        )
        self.paths = {}
        for line in manifest_bytes.decode("utf-8").splitlines():
            sha, relative = line.split("  ", maxsplit=1)
            path = Path(relative)
            check(
                re.fullmatch(r"[a-f0-9]{64}", sha)
                and not path.is_absolute()
                and ".." not in path.parts
                and str(path) == relative
                and relative not in self.paths,
                f"Malformed manifest entry {relative}",
            )
            self.paths[relative] = sha

    def fetch(self, relative, *, optional=False):
        path = self.directory.joinpath(relative)
        if optional and relative not in self.paths:
            check(not path.exists() and not path.is_symlink(), f"Unsealed artifact: {relative}")
            return None
        check(
            relative in self.paths and path.resolve(strict=True) == path and path.is_file(),
            f"Missing or non-regular sealed artifact: {relative}",
        )
        payload = path.read_bytes()
        check(checksum(payload) == self.paths[relative], f"Sealed input changed: {relative}")
        return payload


def get_ledger(path, run):
    ledger = json.loads(path.read_bytes(), parse_float=Decimal)
    check(ledger["version"] == 1, "Ledger version differs")
    provider, task, filtered = Counter(), Counter(), Counter()
    call_ids = set()
    for call in ledger["calls"]:
        if call["job"] != str(run):
            continue
        check(
            call["id"] not in call_ids and call["state"] == "settled", "Duplicate or unsettled call"
        )
        call_ids.add(call["id"])
        usd = Decimal(call["cost_usd"])
        check(
            call["provider"] in ("umgpt", "deepseek") and usd.is_finite() and usd >= 0,
            "Unexpected provider or spend value",
        )
        provider[call["provider"]] += usd
        task[call["task"]] += usd
        if call["stage"] == "agent" and (
            call.get("finish_reason") == "content_filter" or call.get("any_filtered") is True
        ):
            filtered[call["task"]] += 1
    check(
        call_ids
        and not any(
            h["job"] == str(run) and h["state"] == "active" for h in ledger.get("stage_escrows", [])
        ),
        "Missing or unsettled arm accounting",
    )
    return provider, task, filtered


def policy(record, v2=None, forced=None):
    # Frozen e2e-v1.4.3-frozen source: verifier/decision.py, policy_v1_4.py
    # and policy_v1_4_1.py. Duplicate the rule in terms of plain JSON values.
    integrity, regression, _, reproduction = (record[layer]["outcome"] for layer in LAYERS)
    v1 = record["integrity"]["findings"]
    flags = record["static"]["findings"].get("summary", {})
    applies = bool(v1.get("patch_applies", True))
    manipulation = bool(v1.get("prohibited_manipulation"))
    risk = bool(v1.get("high_severity_risk"))
    incomplete = any(row["status"] != "checked" for row in v1.get("ast_analysis", []))
    absolute = flags.get("syntax") == "FAIL" or flags.get("import") == "FAIL"

    if v2 is not None:
        regression = v2
    if forced == "V1":
        integrity, applies = "PASS", True
        manipulation = risk = incomplete = False
    elif forced == "V2":
        regression = "PASS"
    elif forced == "V3":
        absolute = False
    elif forced == "V4":
        reproduction = "PASS"

    conflict = regression == "FAIL" and reproduction == "PASS"
    failure_conditions = [
        (not applies, "patch fails to apply"),
        (integrity == "FAIL", "integrity check failed"),
        (regression == "FAIL" and not conflict, "regression test failed"),
        (manipulation, "prohibited benchmark or test manipulation detected"),
    ]
    failures = [message for active, message in failure_conditions if active]
    if failures:
        return "REJECT", failures
    modifier_conditions = [
        (absolute, "v3_absolute_failure"),
        (incomplete, "v1_analysis_incomplete"),
    ]
    accept_conditions = [
        (integrity != "PASS", f"integrity is {integrity}, not PASS"),
        (conflict, "signals disagree: regression FAIL, reproduction PASS"),
        (regression != "PASS" and not conflict, f"regression is {regression}, not PASS"),
        (
            reproduction != "PASS",
            f"no issue-specific execution signal supports repair (reproduction is {reproduction})",
        ),
        (risk, "high-severity risk flag present"),
    ]
    reasons = [message for active, message in modifier_conditions + accept_conditions if active]
    return ("FLAG", reasons) if reasons else ("ACCEPT", ["all accept conditions met"])


def regression_number(report):
    signal = report["signal"]
    if signal == "PASS":
        return signal
    if signal == "REGRESSION_ERROR" or signal == "FAIL":
        return "FAIL"
    check(
        signal in ("INCOMPLETE", "NOT_AVAILABLE", "BASELINE_UNRELIABLE"),
        f"Unknown V2 status: {signal}",
    )
    return UNAVAILABLE


def read_cohort(run, filtered):
    completion = json.loads(run.fetch("completion.json"))
    ids = completion["completed_tasks"]
    infrastructure = set(completion["agent_infrastructure_tasks"])
    check(
        ids
        and len(set(ids)) == len(ids)
        and all(task_id(i) for i in ids)
        and infrastructure <= set(ids)
        and completion["status"] in ("COMPLETE", "STOPPED_BUDGET"),
        "Malformed completion receipt",
    )
    no_patch = set()
    cohort = {}
    for iid in sorted(ids):
        folder = f"tasks/{iid}"
        payload = run.fetch(f"{folder}/patch.diff")
        sha = checksum(payload)
        nonempty = bool(payload.strip())
        task_record = json.loads(run.fetch(f"{folder}/verification_record.full-v1.4.1.json"))
        done = json.loads(run.fetch(f"{folder}/task_completion.json"))
        check(
            task_record["instance_id"] == iid
            and "sha256:" + sha == task_record["patch_sha256"]
            and done["patch_sha256"] == task_record["patch_sha256"]
            and done["complete"] is True,
            f"Invalid task binding: {iid}",
        )
        check(
            not (nonempty and iid in infrastructure),
            f"Agent infrastructure task has a patch: {iid}",
        )
        if not nonempty and iid not in infrastructure:
            no_patch.add(iid)
        category = (
            "patch"
            if nonempty
            else "provider_blocked"
            if iid in filtered
            else "agent_infrastructure"
            if iid in infrastructure
            else "no_patch"
        )
        raw_report = run.fetch(f"{folder}/verification/v2_policies.json", optional=True)
        if raw_report is None:
            check(
                task_record["regression"]["outcome"] == UNAVAILABLE, f"Missing available V2: {iid}"
            )
            reports = {}
        else:
            v2 = json.loads(raw_report)
            reports = v2["policies"]
            check(v2["instance_id"] == iid and reports.keys() == set(OPTIONS), f"Invalid V2: {iid}")
        original = task_record["decision"]
        check(
            original["policy_version"] == "v1.4.1-full"
            and policy(task_record) == (original["decision"], original["reasons"]),
            f"Recorded decision does not match independently recomputed live decision: {iid}",
        )

        accountings = {}
        for option in OPTIONS:
            outcome = (
                regression_number(reports[option])
                if reports
                else task_record["regression"]["outcome"]
            )
            accountings[option] = policy(task_record, v2=outcome)
            if option == LIVE:
                check(
                    accountings[option][0] == original["decision"]
                    and outcome == task_record["regression"]["outcome"],
                    f"Live accounting disagrees with sealed record: {iid}",
                )
        cohort[iid] = {
            "category": category,
            "record": task_record,
            "reports": reports,
            "accountings": accountings,
            "sha": sha,
        }
    check(
        no_patch == set(completion["no_patch_tasks"]),
        "Frozen patches differ from completion counts",
    )
    return cohort


def case_counts(cases):
    totals = Counter(cases)
    return {decision: totals[decision] for decision in CHOICES}


def independent_self_checks(cohort, provider, filtered, summary, directory):
    live = {iid: task["accountings"][LIVE][0] for iid, task in cohort.items()}
    mix = case_counts(live.values())
    patches = {iid for iid, task in cohort.items() if task["category"] == "patch"}
    empty = set(cohort) - patches
    patch_mix = case_counts(live[iid] for iid in patches)
    blocked = [iid for iid, task in cohort.items() if task["category"] == "provider_blocked"]
    counts = Counter(task["category"] for task in cohort.values())
    check(
        all(live[iid] == "REJECT" for iid in empty)
        and mix == summary["decision_counts"]
        and len(cohort) == summary["completed_tasks"],
        "Label-free decision expectation failed",
    )
    check(
        counts["no_patch"] == summary["no_patch_tasks_after_a1"]
        and counts["agent_infrastructure"] == summary["agent_infrastructure_tasks_after_a1"]
        and blocked == sorted(summary["provider_blocked_instance_ids"])
        and filtered.total() == summary["repair_filtered_calls"],
        "Provider or outcome counts differ from seal",
    )
    total = provider.total()
    check(
        summary["ledger"]["job"] == str(directory)
        and round(Decimal(summary["ledger"]["spend_usd"]), 2) == round(total, 2),
        f"Ledger spend differs from seal: {total}",
    )
    if directory.name == "e2e_v1_4_3_armB_um":
        check(
            len(cohort) == 92
            and list(mix.values()) == [5, 42, 45]
            and list(patch_mix.values()) == [5, 42, 4]
            and blocked == ["django__django-13569"],
            "Arm B seal expectations differ",
        )
    return {
        "completed_tasks": len(cohort),
        "categories": {name: counts[name] for name in TASK_TYPES},
        "live_decisions": mix,
        "patch_decisions": patch_mix,
        "reproduced_live_decisions": len(live),
        "provider_blocked_tasks": blocked,
        "filtered_repair_calls": filtered.total(),
        "v2_reports": sum(bool(item["reports"]) for item in cohort.values()),
        "spend_usd": float(total),
        "spend_by_provider_usd": {name: float(value) for name, value in provider.items()},
    }


def inspect_audit(directory, cohort):
    # The audit is frozen independently. Use eligible facts, including T3 facts
    # in trajectories whose maximum tier is T4.
    kinds = ("T3_name", "T3_content", "T4", "awareness")
    row_count = 0
    facts = Counter()
    audit_keys = set()
    for file in (directory / "tiers" / "artifacts").glob("*/*/*.json"):
        record = read(file)
        iid, role = record["instance_id"], record["role"]
        check(
            role in ("repair", "generator") and (iid, role) not in audit_keys,
            f"Invalid audit artifact identity: {file}",
        )
        audit_keys.add((iid, role))
        row_count += 1
        if record["excluded"]:
            continue
        for entry in record["facts"]:
            category = entry["category"]
            if category in ("awareness", "history") and not entry.get("setup_only", False):
                facts["awareness", iid, role] += 1
                continue
            if (
                category != "answer"
                or not entry["guard_pass"]
                or entry.get("defined_at_first_mention", False)
            ):
                continue
            first = entry["first_seen_in"]
            if first == "model_output":
                kind = "T3_name" if entry["field"] == "hidden_test_name" else "T3_content"
                facts[kind, iid, role] += 1
            elif first == "tool_output":
                facts["T4", iid, role] += 1
    audit = read(directory / "tiers" / "summary.json")
    check(
        row_count
        and row_count == audit["rows"]
        and {iid for tier, iid, _ in facts if tier == "T4"} == set(audit["T4_tasks"]),
        "Audit artifact coverage differs from audit summary",
    )
    rows = []
    by_tier = {}
    for kind in kinds:
        rows.extend(
            (name, iid, role, count)
            for (name, iid, role), count in sorted(facts.items())
            if name == kind and iid in cohort
        )
        by_tier[kind] = {iid for tier, iid, _ in facts if tier == kind and iid in cohort}
    return rows, by_tier


def oracle_labels(path, cohort):
    with path.open(encoding="utf-8", newline="") as stream:
        records = csv.reader(stream)
        check(tuple(next(records, ())) == GRADE_COLUMNS, "Unexpected oracle label header")
        labels = {}
        for row in records:
            iid, sha, outcome, resolved, ftp, ft_total, ptp, pt_total, harness, wrong = row
            check(iid in cohort and iid not in labels, f"Unexpected oracle label identity: {iid}")
            task = cohort[iid]
            check(
                sha == task["sha"] and (task["category"] == "patch") == (outcome != "empty_patch"),
                f"Oracle row does not match patch: {iid}",
            )
            fp, ft, pp, pt = map(int, (ftp, ft_total, ptp, pt_total))
            check(0 <= fp <= ft and 0 <= pp <= pt, f"Invalid oracle arithmetic: {iid}")
            if outcome == "unresolved":
                check(pp != pt or fp != ft, f"Unresolved without failing tests: {iid}")
                label = "R" if pp != pt else "U"
            elif outcome in ("patch_apply_failed", "infra_error"):
                label = "X"
            else:
                check(
                    outcome in ("empty_patch", "resolved") and (fp, pp) == (ft, pt),
                    f"Invalid oracle verdict: {iid}",
                )
                label = ""
            correct = outcome == "resolved"
            check(
                resolved == ("true" if correct else "false")
                and label == wrong
                and bool(harness) == (label == "X"),
                f"Oracle evidence does not support type/verdict: {iid}",
            )
            labels[iid] = ("correct" if correct else "wrong", label)
        check(labels.keys() == cohort.keys(), "Oracle label task set differs from seal")
    return labels


def score_bounds(successes, trials):
    if trials == 0:
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE
    # Algebraically equivalent form in terms of counts.
    z = 1.959964
    center = successes + z**2 / 2
    radius = z * math.sqrt(successes * (trials - successes) / trials + z**2 / 4)
    scale = trials + z**2
    return (
        successes / trials,
        max(0.0, (center - radius) / scale),
        min(1.0, (center + radius) / scale),
    )


def hybrid_score(first, second):
    p1, l1, u1 = score_bounds(*first)
    p2, l2, u2 = score_bounds(*second)
    if p1 == UNAVAILABLE or p2 == UNAVAILABLE:
        return (UNAVAILABLE,) * 3
    low = math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    high = math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return p1 - p2, p1 - p2 - low, p1 - p2 + high


def conditional_p(ca, cn, wa, wn):
    correct = ca + cn
    wrong = wa + wn
    if correct == 0 or wrong == 0:
        return UNAVAILABLE
    total = correct + wrong
    accepted = ca + wa
    denominator = math.comb(total, correct)
    probabilities = {}
    for i in range(max(0, correct - (total - accepted)), min(correct, accepted) + 1):
        probabilities[i] = Fraction(
            math.comb(accepted, i) * math.comb(total - accepted, correct - i), denominator
        )
    return float(sum(p for p in probabilities.values() if p <= probabilities[ca]))


def known_answer_tests():
    # reports/next_phases/phase7_signal_audit/followup/REPORT.md, primary 11/14.
    _, lo, hi = score_bounds(11, 14)
    check((round(lo * 100, 2), round(hi * 100, 2)) == (52.41, 92.43), "Wilson known answer failed")
    # Fagerland, Lydersen and Laake (2015), Recommended Confidence Intervals
    # for Two Independent Binomial Proportions, doi:10.1177/0962280211415469.
    # Their worked example uses 7/34 and 1/34, Newcombe hybrid score bounds 0.019 and 0.34.
    _, lo, hi = hybrid_score((7, 34), (1, 34))
    check(round(lo, 3) == 0.019 and round(hi, 2) == 0.34, "Newcombe known answer failed")
    # Fisher, The Design of Experiments (1935), ch. II, Lady Tasting Tea.
    # Both extreme tables have probability 1/70 under the fixed margins.
    check(
        math.isclose(conditional_p(4, 0, 0, 4), 2 / 70, rel_tol=0, abs_tol=TOLERANCE),
        "Fisher known answer failed",
    )
    check(
        score_bounds(0, 0) == (UNAVAILABLE,) * 3
        and hybrid_score((0, 0), (0, 1)) == (UNAVAILABLE,) * 3
        and conditional_p(0, 0, 1, 1) == UNAVAILABLE,
        "Zero-denominator known answer failed",
    )


CSV_COLUMNS = {
    "decisions": "accounting scope ACCEPT FLAG REJECT",
    "leakage": "kind instance_id role findings",
    "leakage_counts": "kind tasks findings",
    "patch_tasks": "instance_id decision correctness",
    "decision_by_correctness": "accounting cohort decision correct wrong",
    "metrics": "accounting cohort metric k n reference_k reference_n estimate lower upper method",
    "wrong_types": "accounting cohort type wrong ACCEPT FLAG REJECT not_accepted rate lower upper",
    "signal_attribution": (
        "accounting cohort instance_id correctness decision signal outcome absence absence_detail decision_reasons"
    ),
    "signal_counts": "accounting cohort correctness signal outcome absence tasks",
    "reason_counts": "accounting cohort correctness reason tasks",
    "exploratory_ablation": "accounting cohort forced_pass decision correct wrong",
    "exploratory_repositories": "accounting cohort repository decision correct wrong",
    "exploratory_cost": "accounting cohort total_usd correct_ACCEPT cost_per_correct_ACCEPT_usd median_task_usd",
    "paired_decision_by_correctness": "arm decision correct wrong",
    "paired_differences": "shared_patch_tasks different_decision different_correctness either",
}


def analysis_groups(cohort, sets):
    patches, empty, filtered = (set() for _ in range(3))
    for iid, task in cohort.items():
        if task["category"] == "patch":
            patches.add(iid)
        elif task["category"] == "no_patch":
            empty.add(iid)
        elif task["category"] == "provider_blocked":
            filtered.add(iid)
    return {
        "primary": sorted(patches),
        "including_no_patch": sorted(patches | empty),
        "including_no_patch_and_provider_blocked": sorted(patches | empty | filtered),
        "excluding_T4": sorted(patches - sets["T4"]),
        "excluding_T4_and_T3_name": sorted(patches - sets["T4"] - sets["T3_name"]),
    }


def fraction_rows(ca, cn, wa, wn):
    correct = ca + cn
    wrong = wa + wn
    all_tasks = correct + wrong
    rejected_or_flagged = cn + wn
    intervals = [
        ("accept_precision", ca, ca + wa),
        ("base_rate", correct, all_tasks),
        ("wrong_not_accepted", wn, wrong),
        ("all_not_accepted", rejected_or_flagged, all_tasks),
        ("correct_not_accepted", cn, correct),
    ]
    for name, success, total in intervals:
        yield (name, success, total, "", "", *score_bounds(success, total), "Wilson 95%")
    yield (
        "chance_difference",
        wn,
        wrong,
        rejected_or_flagged,
        all_tasks,
        *hybrid_score((wn, wrong), (rejected_or_flagged, all_tasks)),
        "Newcombe 10 95% (approximate, overlapping cohorts)",
    )
    yield (
        "wrong_correct_difference",
        wn,
        wrong,
        cn,
        correct,
        *hybrid_score((wn, wrong), (cn, correct)),
        "Newcombe 10 95%",
    )
    yield (
        "fisher_exact_p",
        "",
        "",
        "",
        "",
        conditional_p(ca, cn, wa, wn),
        UNAVAILABLE,
        UNAVAILABLE,
        "Two-sided Fisher exact",
    )


def layer_rows(option, group, ids, cohort, labels):
    for iid in ids:
        task = cohort[iid]
        record = task["record"]
        decision, reasons = task["accountings"][option]
        if task["category"] != "patch" or decision == "ACCEPT":
            continue
        result = labels[iid][0]
        for index, layer in enumerate(LAYERS, 1):
            layer_record = record[layer]
            outcome = layer_record["outcome"]
            absence = layer_record["absence"] or ""
            details = layer_record["findings"].get("absence_reason") or layer_record["detail"]
            if layer == "regression" and option != LIVE and task["reports"]:
                report = task["reports"][option]
                outcome = regression_number(report)
                signal = report["signal"]
                if signal == "INCOMPLETE":
                    absence = "incomplete"
                elif outcome != UNAVAILABLE:
                    absence = ""
                elif signal == "BASELINE_UNRELIABLE" or (report.get("selection") or {}).get(
                    "tests"
                ):
                    absence = "error"
                else:
                    absence = "nothing_to_check"
                details = signal
            yield (
                option,
                group,
                iid,
                result,
                decision,
                f"V{index}",
                outcome,
                absence,
                details if outcome == UNAVAILABLE else "",
                " | ".join(reasons),
            )


def group_arithmetic(tables, option, name, ids, cohort, labels, cost, median):
    tab = Counter()
    types = Counter()
    repos = Counter()
    ablation = Counter()
    repositories = set()
    for iid in ids:
        task = cohort[iid]
        decision = task["accountings"][option][0]
        classification, wrong_type = labels[iid]
        tab[decision, classification] += 1
        if wrong_type:
            types[wrong_type, decision] += 1
        repo = iid.rpartition("-")[0]
        repositories.add(repo)
        repos[repo, decision, classification] += 1
        v2 = regression_number(task["reports"][option]) if task["reports"] else None
        for layer in ("V1", "V2", "V3", "V4"):
            changed, _ = policy(task["record"], v2=v2, forced=layer)
            ablation[layer, changed, classification] += 1

    prefix = option, name
    for decision in CHOICES:
        tables["decision_by_correctness"].append(
            (*prefix, decision, tab[decision, "correct"], tab[decision, "wrong"])
        )
    ca = tab["ACCEPT", "correct"]
    wa = tab["ACCEPT", "wrong"]
    cn = tab["FLAG", "correct"] + tab["REJECT", "correct"]
    wn = tab["FLAG", "wrong"] + tab["REJECT", "wrong"]
    tables["metrics"].extend((*prefix, *line) for line in fraction_rows(ca, cn, wa, wn))
    for kind in TYPES:
        accepted = types[kind, "ACCEPT"]
        flag = types[kind, "FLAG"]
        reject = types[kind, "REJECT"]
        total = accepted + flag + reject
        withheld = total - accepted
        tables["wrong_types"].append(
            (*prefix, kind, total, accepted, flag, reject, withheld, *score_bounds(withheld, total))
        )

    attributed = list(layer_rows(option, name, ids, cohort, labels))
    tables["signal_attribution"].extend(attributed)
    counts = Counter(
        (correct, layer, outcome, absence)
        for _, _, _, correct, _, layer, outcome, absence, _, _ in attributed
    )
    tables["signal_counts"].extend((*prefix, *key, count) for key, count in sorted(counts.items()))
    counts = Counter(
        (labels[iid][0], reason)
        for iid in ids
        if cohort[iid]["category"] == "patch" and cohort[iid]["accountings"][option][0] != "ACCEPT"
        for reason in cohort[iid]["accountings"][option][1]
    )
    tables["reason_counts"].extend((*prefix, *key, count) for key, count in sorted(counts.items()))

    for layer in ("V1", "V2", "V3", "V4"):
        for decision in CHOICES:
            tables["exploratory_ablation"].append(
                (
                    *prefix,
                    layer,
                    decision,
                    ablation[layer, decision, "correct"],
                    ablation[layer, decision, "wrong"],
                )
            )
    for repo in sorted(repositories):
        for decision in CHOICES:
            tables["exploratory_repositories"].append(
                (
                    *prefix,
                    repo,
                    decision,
                    repos[repo, decision, "correct"],
                    repos[repo, decision, "wrong"],
                )
            )
    tables["exploratory_cost"].append(
        (*prefix, float(cost), ca, float(cost / ca) if ca else UNAVAILABLE, float(median))
    )
    magnitude, lower, _ = hybrid_score((wn, wa + wn), (cn, ca + cn))
    better = magnitude != UNAVAILABLE and magnitude > 0 and lower > 0
    return {"tasks": len(ids), "correct": ca + cn, "better_than_chance": better}


def independent_pair(tables, directory, cohort, labels):
    other = {}
    with (directory / "patch_tasks.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        check(reader.fieldnames == CSV_COLUMNS["patch_tasks"].split(), "Bad paired cohort header")
        for line in reader:
            iid = line["instance_id"]
            decision = line["decision"]
            classification = line["correctness"]
            check(
                iid not in other
                and task_id(iid)
                and decision in CHOICES
                and classification in ("correct", "wrong"),
                f"Invalid paired task {iid}",
            )
            other[iid] = decision, classification
    shared = {iid for iid, item in cohort.items() if item["category"] == "patch" and iid in other}
    this_table = Counter()
    other_table = Counter()
    decision_differences = correct_differences = either = 0
    for iid in shared:
        current = cohort[iid]["accountings"][LIVE][0], labels[iid][0]
        this_table[current] += 1
        other_table[other[iid]] += 1
        decision_differences += current[0] != other[iid][0]
        correct_differences += current[1] != other[iid][1]
        either += current != other[iid]
    tables["paired_decision_by_correctness"] = [
        (name, choice, tab[choice, "correct"], tab[choice, "wrong"])
        for name, tab in (("current", this_table), ("paired_with", other_table))
        for choice in CHOICES
    ]
    values = len(shared), decision_differences, correct_differences, either
    tables["paired_differences"] = [values]
    return dict(zip(CSV_COLUMNS["paired_differences"].split(), values, strict=True))


def verify_table(path, name, expected):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        check(
            next(reader, None) == CSV_COLUMNS[name].split(), f"CSV header mismatch in {path.name}"
        )
        actual = list(reader)
    check(len(actual) == len(expected), f"CSV row count mismatch in {path.name}")
    for row_no, (received, required) in enumerate(zip(actual, expected, strict=True), 2):
        check(len(received) == len(required), f"CSV width mismatch in {path.name} row {row_no}")
        for col, (value, goal) in enumerate(zip(received, required, strict=True), 1):
            if isinstance(goal, float):
                try:
                    same = math.isclose(float(value), goal, rel_tol=0, abs_tol=TOLERANCE)
                except ValueError:
                    same = False
            else:
                same = value == str(goal)
            check(
                same,
                f"CSV mismatch in {path.name} row {row_no}, column {col}: {value!r} vs {goal!r}",
            )


def verify_json(actual, expected, location="counts.json"):
    if isinstance(expected, float):
        check(
            type(actual) in (int, float)
            and math.isclose(actual, expected, abs_tol=TOLERANCE, rel_tol=0),
            f"Float mismatch at {location}: {actual!r} vs {expected!r}",
        )
        return
    check(type(actual) is type(expected), f"JSON type mismatch at {location}")
    if isinstance(expected, dict):
        check(actual.keys() == expected.keys(), f"JSON key mismatch at {location}")
        for key, value in expected.items():
            verify_json(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, list):
        check(len(actual) == len(expected), f"JSON list length mismatch at {location}")
        for index, (given, value) in enumerate(zip(actual, expected, strict=True)):
            verify_json(given, value, f"{location}[{index}]")
    else:
        check(actual == expected, f"JSON mismatch at {location}: {actual!r} vs {expected!r}")


def generate_expected(args):
    raw = Run(args.run, args.manifest)
    provider, task_spend, filtered = get_ledger(args.ledger, raw.directory)
    cohort = read_cohort(raw, filtered)
    checked = independent_self_checks(
        cohort, provider, filtered, read(args.manifest.parent / "summary.json"), raw.directory
    )
    leak_rows, exclusions = inspect_audit(args.leakage, cohort)
    counts = {
        "stage": args.stage,
        "run": raw.directory.name,
        "seal_manifest_sha256": raw.manifest_digest,
        "self_checks": checked,
        "leakage_task_counts": {key: len(ids) for key, ids in exclusions.items()},
    }
    counts_per_kind = Counter()
    for tier, _, _, n in leak_rows:
        counts_per_kind[tier] += n
    tables = {
        "decisions": [],
        "leakage": leak_rows,
        "leakage_counts": [
            (kind, len(tasks), counts_per_kind[kind]) for kind, tasks in exclusions.items()
        ],
    }
    for option in OPTIONS:
        for scope in ("all", *TASK_TYPES):
            totals = case_counts(
                row["accountings"][option][0]
                for row in cohort.values()
                if scope == "all" or row["category"] == scope
            )
            tables["decisions"].append((option, scope, *(totals[key] for key in CHOICES)))
    if args.stage == 1:
        return tables, counts

    labels = oracle_labels(args.labels, cohort)
    groups = analysis_groups(cohort, exclusions)
    tables["patch_tasks"] = [
        (iid, cohort[iid]["accountings"][LIVE][0], labels[iid][0]) for iid in groups["primary"]
    ]
    for name in CSV_COLUMNS:
        if not name.startswith("paired_"):
            tables.setdefault(name, [])
    spend_sorted = sorted(task_spend.get(iid, Decimal(0)) for iid in cohort)
    middle = len(spend_sorted) // 2
    median = (
        spend_sorted[middle]
        if len(spend_sorted) % 2
        else (spend_sorted[middle - 1] + spend_sorted[middle]) / 2
    )
    counts["panels"] = {}
    for option in OPTIONS:
        counts["panels"][option] = {}
        for name, tasks in groups.items():
            counts["panels"][option][name] = group_arithmetic(
                tables, option, name, tasks, cohort, labels, provider.total(), median
            )
    if args.paired_with:
        counts["paired"] = independent_pair(tables, args.paired_with, cohort, labels)
    return tables, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "manifest", "ledger", "leakage", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--stage", required=True, type=int, choices=(1, 2))
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--paired-with", type=Path)
    args = parser.parse_args()
    if bool(args.labels) != (args.stage == 2) or (args.paired_with and args.stage == 1):
        parser.error("--stage 2 and --labels are required together and for pairing")

    known_answer_tests()
    expected_tables, expected_counts = generate_expected(args)
    actual_csvs = {path.stem for path in args.out.glob("*.csv")}
    check(
        actual_csvs == expected_tables.keys(),
        f"Output CSV set mismatch: {sorted(actual_csvs ^ expected_tables.keys())}",
    )
    for name, rows in expected_tables.items():
        verify_table(args.out / (name + ".csv"), name, rows)
    verify_json(read(args.out / "counts.json"), expected_counts)
    print(
        json.dumps(
            {
                "result": "PASS",
                "stage": args.stage,
                "mismatches": 0,
                "tables_checked": len(expected_tables),
                "rows_checked": sum(map(len, expected_tables.values())),
                "counts_json_checked": True,
                "all_live_decisions_checked": expected_counts["self_checks"]["completed_tasks"],
                "known_answer_tests": [
                    "Wilson 11/14",
                    "Newcombe worked example",
                    "Fisher tea tasting",
                    "zero denominators",
                ],
                "paired": expected_counts.get("paired"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError) as exc:
        raise SystemExit(f"Checker hard stop: {exc}") from exc
