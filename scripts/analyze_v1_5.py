#!/usr/bin/env python3
"""Study v1.5 analysis (Phase 14): per-system and pooled verifier metrics, H1-H3, baselines, S1-S3.

Frozen at tag study-analysis-frozen. Reads sealed runs and label files only; never prints
patch content. Decisions: v1.5 with the switches committed at tag v1.5-frozen-2 (read with
decide_v1_5.frozen_switches), recomputed from each sealed record exactly as decide_v1_5.py
does. Pure Python statistics (no numpy).

    scripts/analyze_v1_5.py \\
      --system gpt-4.1-mini=runs/study_test_gpt-4.1-mini_b1 --labels gpt-4.1-mini=LABELS.json \\
      --system claude-sonnet-4=runs/study_test_claude-sonnet-4_b1 --labels claude-sonnet-4=LABELS.json \\
      --gold runs/study_test_gold_b1 --recall reports/study_v1_5/test_gold_b1/test_gold_b1_recall.json \\
      --out-md OUT.md --out-json OUT.json

A --system value is RUN[:IDS.json] and may repeat (comma-separated); a later run overrides an
earlier one for the same task. Label files: {"system": NAME, "labels": {iid: {"resolved":
bool|null, "official_patch_sha256": hex|null}}}. A label is used only if its official patch
sha256 (when given) equals our sealed input bytes before newline normalization.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import decide_v1_5 as dv  # noqa: E402

from reliability.verifier.decision import Evidence, FullPolicy, SignalOutcome  # noqa: E402
from reliability.verifier.policy_v1_4 import evidence_from_signals as v14_evidence  # noqa: E402
from reliability.verifier.policy_v1_4_1 import FullPolicyV141  # noqa: E402
from reliability.verifier.policy_v1_5 import FullPolicyV15, evidence_from_signals  # noqa: E402
from reliability.verifier.record import SignalKind  # noqa: E402
from reliability.verifier.reproduction_reuse import RECORD  # noqa: E402
from reliability.verifier.run_v1_4_1 import VerificationRecordV141  # noqa: E402

FROZEN_TAG = "v1.5-frozen-2"
SEED, RESAMPLES = 20261126, 10_000
MINIMUM_SET = ("gpt-4.1-mini", "claude-sonnet-4", "gemini-2.5-flash")
NEVER_POOLED = ("o4-mini",)
POLICIES = ("frozen", "v141", "v1v2", "s1", "s2", "s3")
POLICY_NAMES = {
    "frozen": "v1.5 frozen (headline)", "v141": "v1.4.1, same signals", "v1v2": "V1+V2 only",
    "s1": "S1: risk flags informational", "s2": "S2: V1 manipulation findings informational",
    "s3": "S3: S1 and S2",
}
#: S2: these V1 findings no longer fail V1; does_not_apply, unparseable and the rest still do.
S2_INFORMATIONAL = frozenset({"unexpected_config_edit", "harness_file_edit", "conflict_markers", "binary_blob"})
MANIPULATION = frozenset({"harness_file_edit", "test_deleted", "test_weakened", "unexpected_config_edit"})
#: Used by the unit tests only: the switches committed at v1.5-frozen-2 (r2, r6, r6b on).
FROZEN_FOR_TESTS = {"r2_v3_reject": True, "r3_extended_reject": False,
                    "r6_accept_v2_not_available": True, "r6b_accept_one_uncovered": True}
Z = 1.959963984540054


# ---------------------------------------------------------------- statistics

def wilson(k, n, z=Z):
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe(k1, n1, k2, n2):
    """Newcombe (1998) method 10 CI for p1 - p2."""
    if n1 == 0 or n2 == 0:
        return (None, None)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]] (sum of tables no more likely than observed)."""
    n, r1, c1 = a + b + c + d, a + b, a + c
    if n == 0:
        return 1.0
    def prob(x):
        return math.comb(c1, x) * math.comb(n - c1, r1 - x) / math.comb(n, r1)
    observed = prob(a)
    lo, hi = max(0, r1 + c1 - n), min(r1, c1)
    return min(1.0, sum(p for x in range(lo, hi + 1) if (p := prob(x)) <= observed * (1 + 1e-7)))


def rate(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "value": k / n if n else None, "ci": [lo, hi]}


# ---------------------------------------------------------------- rows and metrics

@dataclass
class Row:
    system: str
    instance_id: str
    empty: bool
    labelled: bool
    correct: bool | None
    decisions: dict
    v4_full_pass: bool
    recall: bool
    extra: dict = field(default_factory=dict)


def scored(rows):
    """Rows that enter verifier metrics: non-empty and labelled."""
    return [r for r in rows if not r.empty and r.labelled]


def metrics(rows, policy, systems=None):
    if systems is not None:
        rows = [r for r in rows if r.system in systems]
    s = scored(rows)
    cells = Counter((r.decisions[policy], r.correct) for r in s)
    correct, wrong = sum(r.correct for r in s), sum(not r.correct for r in s)
    acc_c, acc_w = cells["ACCEPT", True], cells["ACCEPT", False]
    rej_c, rej_w = cells["REJECT", True], cells["REJECT", False]
    flags = cells["FLAG", True] + cells["FLAG", False]
    base = correct / len(s) if s else None
    precision = acc_c / (acc_c + acc_w) if acc_c + acc_w else None
    by_system = defaultdict(list)
    for r in s:
        by_system[r.system].append(r)
    accepts = {sy: sum(r.decisions[policy] == "ACCEPT" for r in rs) for sy, rs in by_system.items()}
    total_accepts = sum(accepts.values())
    weighted = (sum(accepts[sy] * (sum(r.correct for r in rs) / len(rs)) for sy, rs in by_system.items())
                / total_accepts) if total_accepts else None
    held_w, held_c = wrong - acc_w, correct - acc_c
    return {
        "n": len(s), "correct": correct, "wrong": wrong,
        "empty": sum(r.empty for r in rows), "unlabelled": sum((not r.empty) and not r.labelled for r in rows),
        "decisions": {f"{d}_{'correct' if c else 'wrong'}": cells[d, c]
                      for d in ("ACCEPT", "FLAG", "REJECT") for c in (True, False)},
        "base_rate": rate(correct, len(s)),
        "accept_precision": rate(acc_c, acc_c + acc_w),
        "lift": precision / base if precision is not None and base else None,
        "accept_weighted_base_rate": weighted,
        "lift_accept_weighted": precision / weighted if precision is not None and weighted else None,
        "coverage": rate(acc_c, correct), "false_accept_rate": rate(acc_w, wrong),
        "wrong_rejected": rate(rej_w, wrong), "correct_rejected": rate(rej_c, correct),
        "flag_rate": rate(flags, len(s)),
        "held_back_wrong": rate(held_w, wrong), "held_back_correct": rate(held_c, correct),
        "held_back_difference": {"value": (held_w / wrong - held_c / correct) if wrong and correct else None,
                                 "ci_newcombe": list(newcombe(held_w, wrong, held_c, correct))},
        "fisher_p": fisher_two_sided(held_w, acc_w, held_c, acc_c),
    }


def bootstrap(rows, policy, resamples=RESAMPLES, seed=SEED, systems=None):
    """Task-clustered bootstrap: resample whole tasks with replacement (PROTOCOL §6)."""
    s = scored([r for r in rows if systems is None or r.system in systems])
    by_task = defaultdict(list)
    for r in s:
        by_task[r.instance_id].append(r)
    tasks = sorted(by_task)
    rng = random.Random(seed)
    h1, h2, prec = [], [], []
    for _ in range(resamples):
        sample = [r for t in (rng.choice(tasks) for _ in tasks) for r in by_task[t]]
        acc = [r for r in sample if r.decisions[policy] == "ACCEPT"]
        correct = [r for r in sample if r.correct]
        wrong = [r for r in sample if not r.correct]
        if not acc or not correct or not wrong:
            continue
        p = sum(r.correct for r in acc) / len(acc)
        prec.append(p)
        h1.append(p - len(correct) / len(sample))
        h2.append(sum(r.decisions[policy] != "ACCEPT" for r in wrong) / len(wrong)
                  - sum(r.decisions[policy] != "ACCEPT" for r in correct) / len(correct))

    def ci(values):
        if not values:
            return [None, None]
        values = sorted(values)
        return [values[int(0.025 * (len(values) - 1))], values[int(math.ceil(0.975 * (len(values) - 1)))]]

    return {"tasks": len(tasks), "resamples": resamples, "resamples_used": len(h1), "seed": seed,
            "precision_ci": ci(prec), "h1_ci": ci(h1), "h2_ci": ci(h2),
            "h1_supported": bool(h1) and ci(h1)[0] > 0, "h2_supported": bool(h2) and ci(h2)[0] > 0}


# ---------------------------------------------------------------- policies

def decide_variant(evidence, violations, policy, switches):
    """Decision (decision, rule) for one task under one analysis policy."""
    if policy in ("s2", "s3"):
        remaining = [v for v in violations if v not in S2_INFORMATIONAL]
        if evidence.integrity is SignalOutcome.FAIL and not remaining:
            evidence = replace(evidence, integrity=SignalOutcome.PASS)
        evidence = replace(evidence, prohibited_manipulation=bool(set(remaining) & MANIPULATION))
    if policy in ("s1", "s3"):
        evidence = replace(evidence, high_severity_risk=False)
    if policy == "v141":
        r = FullPolicyV141().decide(evidence)
        return (r.decision.value, "v1.4.1")
    if policy == "v1v2":
        base = Evidence(integrity=evidence.integrity, regression=evidence.regression,
                        static=SignalOutcome.NOT_AVAILABLE, reproduction=SignalOutcome.NOT_AVAILABLE,
                        high_severity_risk=evidence.high_severity_risk,
                        prohibited_manipulation=evidence.prohibited_manipulation,
                        patch_applies=evidence.patch_applies)
        r = FullPolicy(require_reproduction=False).decide(base)
        return (r.decision.value, "V1+V2")
    r = FullPolicyV15(**switches).decide(evidence)
    return (r.decision.value, r.rule_id)


_MARKER = re.compile(r"unresolved merge marker: '(.{0,7})")


def only_equals_markers(detail):
    """True when every recorded conflict-marker finding is a line starting '=======' (no line text kept)."""
    found = _MARKER.findall(detail or "")
    return bool(found) and all(m == "=======" for m in found)


# ---------------------------------------------------------------- inputs

def input_sha_before_normalization(run):
    """Per task: sha256 of our input bytes before any newline normalization (B12 inputs)."""
    header = json.loads((run / "header.json").read_text())
    folder = header.get("verify_only_input_folder")
    out = {iid: v["sha256"] for iid, v in (header.get("verify_only_inputs") or {}).items()}
    if folder and (Path(folder) / "source.json").is_file():
        source = json.loads((Path(folder) / "source.json").read_text())
        manifest = ROOT / source["source_manifest"]
        if not manifest.is_file():
            manifest = Path("/home/sankalp/projects/wt-study") / source["source_manifest"]
        rows = json.loads(manifest.read_text())
        rows = rows["tasks"] if isinstance(rows, dict) else rows
        for r in rows:
            if r["instance_id"] in out:
                out[r["instance_id"]] = r.get("source_sha256") or r["patch_sha256"]
    return out


def load_run_rows(spec, switches):
    """{iid: (evidence, v14 evidence, violations, detail, empty, input_sha)} from RUN[:IDS] specs."""
    out = {}
    for part in spec.split(","):
        path, _, ids_file = part.partition(":")
        run = Path(path).resolve()
        files, _ = dv.check_sealed(run, require_complete=False)
        completion = json.loads(dv._read(run, files, "completion.json"))
        ids = json.loads(Path(ids_file).read_text()) if ids_file else completion["completed_tasks"]
        ids = [i if isinstance(i, str) else i["instance_id"] for i in ids]
        missing = [i for i in ids if i not in completion["completed_tasks"]]
        if missing:
            raise ValueError(f"{run.name}: tasks not completed: {missing}")
        empty = set(completion.get("no_patch_tasks", ()))
        shas = input_sha_before_normalization(run)
        for iid in ids:
            record = VerificationRecordV141.model_validate_json(dv._read(run, files, f"tasks/{iid}/{RECORD}"))
            integrity = record.signals[SignalKind.INTEGRITY]
            out[iid] = {
                "evidence": evidence_from_signals(record.signals, added_paths=dv.added_paths(run, files, iid)),
                "v14": v14_evidence(record.signals),
                "violations": tuple(integrity.findings.get("violations", ())),
                "detail": integrity.detail, "empty": iid in empty, "input_sha": shas.get(iid),
                "run": run.name,
            }
    return out


def load_labels(path, input_sha):
    data = json.loads(Path(path).read_text())
    labels, problems = {}, {"patch_sha256_mismatch": [], "no_label": []}
    for iid in sorted(input_sha):
        entry = (data.get("labels") or {}).get(iid)
        if not entry or entry.get("resolved") is None:
            problems["no_label"].append(iid)
            continue
        official = entry.get("official_patch_sha256")
        if official and official != input_sha[iid]:
            problems["patch_sha256_mismatch"].append(iid)
            continue
        labels[iid] = bool(entry["resolved"])
    return labels, problems


@dataclass
class Scope:
    ids: tuple
    task_excluded: frozenset
    pair_excluded: frozenset

    @classmethod
    def load(cls, ids, task_exclusions, pair_exclusion_files):
        tasks = set()
        pairs = set()
        if task_exclusions:
            data = json.loads(Path(task_exclusions).read_text())
            tasks = {r["instance_id"] for r in data.get("excluded", ()) if "system" not in r}
            pairs |= {(r["system"], r["instance_id"]) for r in data.get("excluded", ()) if "system" in r}
            pairs |= {(r["system"], r["instance_id"]) for r in data.get("pair_excluded", ())}
        for f in pair_exclusion_files:
            data = json.loads(Path(f).read_text())
            pairs |= {(r["system"], r["instance_id"]) for r in data.get("excluded", ())}
        return cls(tuple(ids), frozenset(tasks), frozenset(pairs))

    def keeps(self, system, iid):
        return iid in self.ids and iid not in self.task_excluded and (system, iid) not in self.pair_excluded


def build_rows(systems, labels, switches, scope, recall_tasks):
    rows, problems = [], {}
    for system, runs in systems.items():
        task_rows = {}
        for spec in runs:
            task_rows.update(load_run_rows(spec, switches))
        shas = {iid: t["input_sha"] for iid, t in task_rows.items() if scope.keeps(system, iid)}
        lab, prob = load_labels(labels[system], shas) if system in labels else ({}, {"no_label": sorted(shas), "patch_sha256_mismatch": []})
        problems[system] = prob
        for iid, t in sorted(task_rows.items()):
            if not scope.keeps(system, iid):
                continue
            decisions = {p: decide_variant(t["v14"] if p == "v141" else t["evidence"], t["violations"], p, switches)[0]
                         for p in POLICIES}
            rows.append(Row(system=system, instance_id=iid, empty=t["empty"], labelled=iid in lab,
                            correct=lab.get(iid), decisions=decisions, v4_full_pass=bool(t["evidence"].v4_full_pass),
                            recall=iid in recall_tasks,
                            extra={"equals_only_conflict": "conflict_markers" in t["violations"]
                                   and only_equals_markers(t["detail"]), "run": t["run"]}))
    return rows, problems


# ---------------------------------------------------------------- analyses

def within_task(rows, policy, systems):
    s = [r for r in scored(rows) if r.system in systems]
    by_task = defaultdict(list)
    for r in s:
        by_task[r.instance_id].append(r)
    mixed = {t: rs for t, rs in by_task.items() if len({r.correct for r in rs}) == 2}
    concordant = discordant = ties = 0
    for rs in mixed.values():
        for c in (r for r in rs if r.correct):
            for w in (r for r in rs if not r.correct):
                ca, wa = c.decisions[policy] == "ACCEPT", w.decisions[policy] == "ACCEPT"
                concordant += ca and not wa
                discordant += wa and not ca
                ties += ca == wa
    flat = [r for rs in mixed.values() for r in rs]
    return {"tasks": len(mixed), "patches": len(flat),
            "accept_correct": rate(sum(r.correct and r.decisions[policy] == "ACCEPT" for r in flat), sum(r.correct for r in flat)),
            "accept_wrong": rate(sum((not r.correct) and r.decisions[policy] == "ACCEPT" for r in flat), sum(not r.correct for r in flat)),
            "pairs": {"concordant": concordant, "discordant": discordant, "ties": ties}}


def v4_correct_vs_gold(rows, gold, systems):
    pub = [r for r in scored(rows) if r.system in systems and r.correct and r.instance_id in gold]
    cells = Counter((r.v4_full_pass, gold[r.instance_id]) for r in pub)
    return {"correct_public_patches": len(pub),
            "public_full_pass": rate(sum(r.v4_full_pass for r in pub), len(pub)),
            "gold_full_pass_same_tasks": rate(sum(gold[r.instance_id] for r in pub), len(pub)),
            "cells": {f"public_{'pass' if a else 'not'}__gold_{'pass' if b else 'not'}": cells[a, b]
                      for a in (True, False) for b in (True, False)}}


def gold_h3(gold_rows, scope):
    kept = {iid: d for iid, d in gold_rows.items() if scope is None or scope.keeps("gold", iid)}
    rejects = sorted(iid for iid, d in kept.items() if d == "REJECT")
    lo, hi = wilson(len(rejects), len(kept))
    return {"gold_patches": len(kept), "rejects": len(rejects), "reject_ids": rejects,
            "point": len(rejects) / len(kept) if kept else None, "wilson_upper": hi}


def analyse(rows, gold_decisions, gold_v4, minimum, systems, scope, resamples, seed):
    pooled_systems = tuple(s for s in minimum if s in systems and s not in NEVER_POOLED)
    out = {"pooled_systems": pooled_systems, "policies": {}}
    for p in POLICIES:
        out["policies"][p] = {
            "per_system": {s: metrics(rows, p, systems=(s,)) for s in systems},
            "pooled": metrics(rows, p, systems=pooled_systems),
            "bootstrap": bootstrap(rows, p, resamples, seed, systems=pooled_systems),
        }
    out["within_task"] = within_task(rows, "frozen", pooled_systems)
    out["v4_correct_vs_gold"] = v4_correct_vs_gold(rows, gold_v4, pooled_systems) if gold_v4 else None
    out["h3"] = {"all": gold_h3(gold_decisions, None), "headline_scope": gold_h3(gold_decisions, scope)} if gold_decisions else None
    out["rq1"] = {s: {"patches": sum(r.system == s for r in rows), "empty": sum(r.system == s and r.empty for r in rows),
                      "non_empty_labelled": sum(r.system == s and not r.empty and r.labelled for r in rows),
                      "resolved": sum(r.system == s and not r.empty and r.labelled and r.correct for r in rows)}
                  for s in systems}
    out["equals_only_conflict_markers"] = sorted({(r.system, r.instance_id) for r in rows if r.extra.get("equals_only_conflict")})
    return out


# ---------------------------------------------------------------- report

def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def ci_text(r):
    lo, hi = r["ci"]
    return "n/a" if r["value"] is None else f"{pct(r['value'])} [{pct(lo)}, {pct(hi)}]"


def render(results, title):
    L = [f"# {title}", ""]
    for scope_name, res in results["scopes"].items():
        L += [f"## Scope: {scope_name}", ""]
        for p in POLICIES:
            block = res["policies"][p]
            L += [f"### {POLICY_NAMES[p]}", "",
                  "| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |",
                  "|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|"]
            for name, m in [*block["per_system"].items(), ("pooled (" + ", ".join(res["pooled_systems"]) + ")", block["pooled"])]:
                hb = m["held_back_difference"]
                hb_text = "n/a" if hb["value"] is None else f"{pct(hb['value'])} [{pct(hb['ci_newcombe'][0])}, {pct(hb['ci_newcombe'][1])}]"
                lift = "n/a" if m["lift"] is None else f"{m['lift']:.2f}"
                lift_w = "n/a" if m["lift_accept_weighted"] is None else f"{m['lift_accept_weighted']:.2f}"
                L.append(f"| {name} | {m['n']} | {ci_text(m['base_rate'])} | {ci_text(m['accept_precision'])} | "
                         f"{lift} | {lift_w} | "
                         f"{ci_text(m['coverage'])} | {ci_text(m['false_accept_rate'])} | {ci_text(m['wrong_rejected'])} | "
                         f"{ci_text(m['correct_rejected'])} | {ci_text(m['flag_rate'])} | {hb_text} | {m['fisher_p']:.3g} |")
            b = block["bootstrap"]
            L += ["", f"Bootstrap (task-clustered, {b['resamples']} resamples, seed {b['seed']}, {b['tasks']} tasks, "
                      f"{b['resamples_used']} usable): H1 precision − base rate 95% CI [{pct(b['h1_ci'][0])}, {pct(b['h1_ci'][1])}] → "
                      f"{'supported' if b['h1_supported'] else 'not supported'}; H2 held-back difference 95% CI "
                      f"[{pct(b['h2_ci'][0])}, {pct(b['h2_ci'][1])}] → {'supported' if b['h2_supported'] else 'not supported'}.", ""]
        w = res["within_task"]
        L += ["### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)", "",
              f"{w['tasks']} tasks, {w['patches']} patches. ACCEPT rate correct {ci_text(w['accept_correct'])}, wrong "
              f"{ci_text(w['accept_wrong'])}. Correct/wrong pairs in the same task: concordant {w['pairs']['concordant']}, "
              f"discordant {w['pairs']['discordant']}, ties {w['pairs']['ties']}.", ""]
        v = res["v4_correct_vs_gold"]
        if v:
            L += ["### V4 on correct public patches vs gold on the same tasks", "",
                  f"{v['correct_public_patches']} correct public patches: V4 full pass {ci_text(v['public_full_pass'])}; "
                  f"gold on the same tasks {ci_text(v['gold_full_pass_same_tasks'])}. Cells: {v['cells']}.", ""]
        if res["h3"]:
            for k, h in res["h3"].items():
                L.append(f"- H3 ({k}): {h['rejects']} of {h['gold_patches']} gold patches REJECTed, point {pct(h['point'])}, "
                         f"Wilson 95% upper {pct(h['wilson_upper'])} ({', '.join(h['reject_ids']) or 'none'}).")
            L.append("")
        L += ["### RQ1 and data", "", "| system | patches in scope | empty | non-empty labelled | resolved |", "|---|---:|---:|---:|---:|"]
        for s, q in res["rq1"].items():
            L.append(f"| {s} | {q['patches']} | {q['empty']} | {q['non_empty_labelled']} | {q['resolved']} |")
        L += ["", "Conflict markers fired only on lines starting `=======`: "
              + (", ".join(f"{s}/{i}" for s, i in res["equals_only_conflict_markers"]) or "none") + ".", ""]
    L += ["## Label checks", ""]
    for s, prob in results["label_problems"].items():
        L.append(f"- {s}: no label {len(prob['no_label'])} ({', '.join(prob['no_label']) or 'none'}); official patch sha256 "
                 f"mismatch {len(prob['patch_sha256_mismatch'])} ({', '.join(prob['patch_sha256_mismatch']) or 'none'}).")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", action="append", default=[], help="NAME=RUN[:IDS][,RUN[:IDS]...]")
    parser.add_argument("--labels", action="append", default=[], help="NAME=LABELS.json")
    parser.add_argument("--gold", help="sealed gold run(s) for H3 and V4-vs-gold, RUN[:IDS][,...]")
    parser.add_argument("--recall", help="reference-audit summary JSON; tasks with recall lines form the no-recall sensitivity")
    parser.add_argument("--batch-ids", default=str(ROOT / "configs/study_v1_5/test_batch1_final_ids.json"))
    parser.add_argument("--exclusions", default=str(ROOT / "configs/study_v1_5/headline_exclusions.json"))
    parser.add_argument("--pair-exclusions", action="append",
                        default=["/home/sankalp/projects/wt-study/runs/study_v1_5/headline_exclusions_pending.json"])
    parser.add_argument("--frozen-tag", default=FROZEN_TAG)
    parser.add_argument("--minimum-set", default=",".join(MINIMUM_SET))
    parser.add_argument("--resamples", type=int, default=RESAMPLES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--title", default="Study v1.5 results")
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    switches, frozen = dv.frozen_switches(ROOT, args.frozen_tag)
    systems = {}
    for spec in args.system:
        name, _, runs = spec.partition("=")
        systems.setdefault(name, []).append(runs)
    labels = dict(spec.split("=", 1) for spec in args.labels)
    raw_ids = json.loads(Path(args.batch_ids).read_text())
    ids = [i if isinstance(i, str) else i["instance_id"] for i in raw_ids]
    recall_tasks = set()
    if args.recall:
        recall_tasks = {t["instance_id"] for t in json.loads(Path(args.recall).read_text())["tasks"] if t["recall_lines"]}

    gold_decisions, gold_v4 = {}, {}
    if args.gold:
        gold_tasks = {}
        for spec in args.gold.split(","):
            gold_tasks.update(load_run_rows(spec, switches))
        gold_decisions = {iid: decide_variant(t["evidence"], t["violations"], "frozen", switches)[0]
                          for iid, t in gold_tasks.items() if iid in ids and not t["empty"]}
        gold_v4 = {iid: bool(t["evidence"].v4_full_pass) for iid, t in gold_tasks.items()}

    headline = Scope.load(ids, args.exclusions, [f for f in args.pair_exclusions if Path(f).is_file()])
    everything = Scope.load(ids, None, [])
    scopes, label_problems = {}, {}
    rows, label_problems = build_rows(systems, labels, switches, headline, recall_tasks)
    scopes["headline (batch, minus headline exclusions)"] = analyse(
        rows, gold_decisions, gold_v4, args.minimum_set.split(","), list(systems), headline, args.resamples, args.seed)
    all_rows, _ = build_rows(systems, labels, switches, everything, recall_tasks)
    scopes["sensitivity: all tasks (no exclusions)"] = analyse(
        all_rows, gold_decisions, gold_v4, args.minimum_set.split(","), list(systems), everything, args.resamples, args.seed)
    if recall_tasks:
        no_recall = Scope(headline.ids, headline.task_excluded | frozenset(recall_tasks), headline.pair_excluded)
        nr_rows, _ = build_rows(systems, labels, switches, no_recall, recall_tasks)
        scopes["sensitivity: headline minus tasks with generator recall"] = analyse(
            nr_rows, gold_decisions, gold_v4, args.minimum_set.split(","), list(systems), no_recall, args.resamples, args.seed)
    results = {"frozen": frozen, "switches": switches, "seed": args.seed, "resamples": args.resamples,
               "systems": systems, "labels": labels, "scopes": scopes, "label_problems": label_problems,
               "rows": [{"system": r.system, "instance_id": r.instance_id, "empty": r.empty, "labelled": r.labelled,
                         "correct": r.correct, "decisions": r.decisions, "v4_full_pass": r.v4_full_pass,
                         "recall": r.recall, **r.extra} for r in rows]}
    Path(args.out_json).write_text(json.dumps(results, indent=1, sort_keys=True, default=list) + "\n", encoding="utf-8")
    Path(args.out_md).write_text(render(results, args.title), encoding="utf-8")
    print(f"wrote {args.out_md} and {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
