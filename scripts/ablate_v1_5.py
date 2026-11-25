#!/usr/bin/env python3
"""Study v1.5 Phase 16: ablations (RQ3, RQ4) and failure modes (RQ5).

Pre-specified in PLAN §6; computed after labels were joined; not used to choose any rule.
The headline stays v1.5 frozen. Imports analyze_v1_5 and decide_v1_5 and changes neither.
Reads sealed runs, committed labels and stored signals only; no model calls, no Docker.
Never prints patch or test-file contents (test names only).

    env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/ablate_v1_5.py \\
      --out-dir reports/study_v1_5/results

Run specs, label files, switches and the frozen tag come from results_final.json (keys systems,
labels, switches, frozen). Scope = analyze_v1_5's headline scope from the same batch-id and
exclusion files. Gate G1 (frozen and V1+V2 decision counts equal results_final.json, per system
and pooled) runs first; if it fails the script writes nothing and exits 2.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import analyze_v1_5 as AN  # noqa: E402
import decide_v1_5 as dv  # noqa: E402

from reliability.verifier.decision import SignalOutcome  # noqa: E402
from reliability.verifier.policy_v1_5 import FullPolicyV15, patched_timeout_or_crash  # noqa: E402
from reliability.verifier.record import SignalKind  # noqa: E402
from reliability.verifier.reproduction_reuse import RECORD  # noqa: E402
from reliability.verifier.run_v1_4_1 import VerificationRecordV141  # noqa: E402

P, F, NA = SignalOutcome.PASS, SignalOutcome.FAIL, SignalOutcome.NOT_AVAILABLE
HEADER = "Pre-specified in PLAN §6; computed after labels were joined; not used to choose any rule."
HEADLINE = "headline (batch, minus headline exclusions)"
V2_ACCOUNTINGS = ("S_invalid_excluded", "S_invalid_missing", "C_invalid_excluded", "C_invalid_missing",
                  "P_invalid_excluded", "P_invalid_missing")
FAILING_V2 = ("REGRESSION", "REGRESSION_ERROR")
LABELS_DIR = ROOT / "runs/study_v1_5/labels"
GIT_PEEK_DIR = ROOT / "reports/study_v1_5/results/git_peek"
GIT_PEEK_SOURCE = ("https://raw.githubusercontent.com/SWE-bench/experiments/main/evaluation/verified/"
                   "{folder}/git_peek_suspicious_commits.md")
SUBMISSION = {"gpt-4.1-mini": "20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14",
              "claude-sonnet-4": "20250726_mini-v1.0.0_claude-sonnet-4-20250514",
              "gemini-2.5-flash": "20250726_mini-v1.0.0_gemini-2.5-flash"}


# ---------------------------------------------------------------- pure helpers (unit-tested)

def force_pass(evidence, signal):
    """Evidence with one signal forced to PASS (same replacements as analyze_rerun_arm.ablate;
    V4 forced to a full pass)."""
    if signal == "V1":
        return replace(evidence, integrity=P, patch_applies=True, prohibited_manipulation=False,
                       high_severity_risk=False, v1_analysis_incomplete=False)
    if signal == "V2":
        return replace(evidence, regression=P)
    if signal == "V3":
        return replace(evidence, static=P, v3_absolute_failure=False)
    if signal == "V4":
        return replace(evidence, reproduction=P, v4_full_pass=True, v4_failing_units=0,
                       v4_uncovered_units=0, v4_no_result_units=0)
    raise ValueError(f"unknown signal {signal!r}")


def v2_from_report(report):
    """(outcome, absence, patched timeout/crash) from one stored per-accounting V2 report, mapped
    exactly as run.signal_from_regression and policy_v1_5.evidence_from_signals do."""
    signal = report.get("signal")
    if signal == "PASS":
        outcome, absence = P, None
    elif signal in ("FAIL", "REGRESSION_ERROR"):
        outcome, absence = F, None
    else:
        outcome = NA
        if signal == "INCOMPLETE":
            absence = "incomplete"
        elif signal == "BASELINE_UNRELIABLE":
            absence = "error"
        elif (report.get("selection") or {}).get("tests"):
            absence = "error"
        else:
            absence = "nothing_to_check"
    return outcome, absence, patched_timeout_or_crash(report)


def with_v2(evidence, v2):
    outcome, absence, timeout = v2
    return replace(evidence, regression=outcome, v2_absence=absence, v2_patched_timeout_or_crash=timeout)


def tests_status(report, iid):
    """Per-test status from a swebench report.json, nested {iid: {...}} or flat."""
    node = report.get(iid) if isinstance(report.get(iid), dict) else report
    status = node.get("tests_status")
    return status if isinstance(status, dict) and status else None


def applied_flag(report, iid):
    node = report.get(iid) if isinstance(report.get(iid), dict) else report
    return node.get("patch_successfully_applied")


def failed(status, key):
    return list(((status or {}).get(key) or {}).get("failure") or ())


def wrong_type(status):
    """U: a FAIL_TO_PASS test does not pass and no PASS_TO_PASS fails; R: all FAIL_TO_PASS pass and a
    PASS_TO_PASS fails; X: both; unknown: no per-test status."""
    if not status:
        return "unknown"
    f2p, p2p = bool(failed(status, "FAIL_TO_PASS")), bool(failed(status, "PASS_TO_PASS"))
    if f2p and p2p:
        return "X"
    if f2p:
        return "U"
    if p2p:
        return "R"
    return "no failing test"


def failing_v2_files(outcomes):
    return {tid.split("::", 1)[0] for tid, o in (outcomes or {}).items() if o in FAILING_V2}


def patch_files(patch_text):
    """Paths a unified diff touches, from its 'diff --git a/X b/X' lines (contents never kept)."""
    out = set()
    for line in (patch_text or "").splitlines():
        m = re.match(r"diff --git a/(\S+) b/(\S+)", line)
        if m:
            out.add(m.group(2))
    return out


def gold_cause(rule, reason, evidence, v2_files, test_patch_files):
    """Cause of a gold FLAG/REJECT by first matching rule (fixed before computing)."""
    second = "no covering test" if evidence.v2_absence == "nothing_to_check" else None
    out = {"cause": None, "second_cause": second, "confirmed": None}
    if rule in ("R5", "R3", "R3b") and evidence.regression is F:
        in_patch = sorted(f for f in v2_files if f in test_patch_files)
        out.update(cause="superseded assertion", confirmed=bool(v2_files) and len(in_patch) == len(v2_files),
                   v2_failing_files=sorted(v2_files), in_test_patch=in_patch)
    elif rule == "R4":
        out["cause"] = "verifier fault (V4 test asserts the wrong thing)"
    elif (rule == "R7" and (evidence.v4_uncovered_units or evidence.v4_no_result_units)) or evidence.reproduction is NA:
        out["cause"] = "issue not reproducible as a test"
    else:
        out["cause"] = f"verifier fault ({rule}: {reason})"
    return out


def git_peek_ids(text):
    m = re.search(r"All iids:\s*\n\s*```\n(.*?)```", text, re.S)
    if not m:
        raise ValueError("no 'All iids' block in git_peek file")
    return m.group(1).split()


def empty_as_wrong_reject(rows, policy):
    """Empty patches counted as wrong patches held back: labelled wrong, decision REJECT."""
    return [replace(r, empty=False, labelled=True, correct=False, decisions={**r.decisions, policy: "REJECT"})
            if r.empty else r for r in rows]


def repo_of(iid):
    owner, rest = iid.split("__", 1)
    return f"{owner}/{rest.rsplit('-', 1)[0]}"


def with_decisions(rows, key, decisions):
    return [replace(r, decisions={**r.decisions, key: decisions[(r.system, r.instance_id)]}) for r in rows]


def bare_test_name(name):
    name = name.split(" (", 1)[0]
    name = name.split("::")[-1]
    return name.split("[", 1)[0].strip()


# ---------------------------------------------------------------- loading

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_tasks(specs, switches):
    """{iid: {evidence, record, run, files, empty}}; a later run overrides an earlier one (as analyze_v1_5)."""
    out = {}
    for spec in specs:
        rows = AN.load_run_rows(spec, switches)
        run = Path(spec.split(":", 1)[0]).resolve()
        files, _ = dv.check_sealed(run, require_complete=False)
        for iid, t in rows.items():
            record = VerificationRecordV141.model_validate_json(dv._read(run, files, f"tasks/{iid}/{RECORD}"))
            out[iid] = {**t, "record": record, "run_path": run, "files": files}
    return out


def decide(evidence, switches):
    r = FullPolicyV15(**switches).decide(evidence)
    return r.decision.value, r.rule_id, "; ".join(r.reasons)


def block(rows, key, pooled, seed, resamples, per_system_bootstrap=False):
    systems = sorted({r.system for r in rows})
    out = {"per_system": {s: AN.metrics(rows, key, systems=(s,)) for s in systems},
           "pooled": AN.metrics(rows, key, systems=pooled),
           "bootstrap": AN.bootstrap(rows, key, resamples, seed, systems=pooled)}
    if per_system_bootstrap:
        out["bootstrap_per_system"] = {s: AN.bootstrap(rows, key, resamples, seed, systems=(s,)) for s in systems}
    return out


# ---------------------------------------------------------------- report text

def fmt_row(name, m):
    hb = m["held_back_difference"]
    hb_text = "n/a" if hb["value"] is None else f"{AN.pct(hb['value'])} [{AN.pct(hb['ci_newcombe'][0])}, {AN.pct(hb['ci_newcombe'][1])}]"
    lift = "n/a" if m["lift"] is None else f"{m['lift']:.2f}"
    lift_w = "n/a" if m["lift_accept_weighted"] is None else f"{m['lift_accept_weighted']:.2f}"
    return (f"| {name} | {m['n']} | {AN.ci_text(m['base_rate'])} | {AN.ci_text(m['accept_precision'])} | {lift} | {lift_w} | "
            f"{AN.ci_text(m['coverage'])} | {AN.ci_text(m['false_accept_rate'])} | {AN.ci_text(m['wrong_rejected'])} | "
            f"{AN.ci_text(m['correct_rejected'])} | {AN.ci_text(m['flag_rate'])} | {hb_text} | {m['fisher_p']:.3g} |")


def h_text(b):
    if b is None:
        return "n/a"
    return (f"H1 [{AN.pct(b['h1_ci'][0])}, {AN.pct(b['h1_ci'][1])}] {'✓' if b['h1_supported'] else '✗'}; "
            f"H2 [{AN.pct(b['h2_ci'][0])}, {AN.pct(b['h2_ci'][1])}] {'✓' if b['h2_supported'] else '✗'}")


TABLE_HEAD = ["| variant | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | "
              "false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p | "
              "bootstrap H1 / H2 (95% CI, supported) |",
              "|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|---|"]


def variant_table(variants, *, per_system=False):
    """variants: [(label, block)]; pooled rows first, then per-system rows when asked."""
    L = list(TABLE_HEAD)
    for label, b in variants:
        L.append(fmt_row(f"{label} (pooled)", b["pooled"])[:-1] + f" {h_text(b['bootstrap'])} |")
    if per_system:
        for label, b in variants:
            for s, m in b["per_system"].items():
                bs = (b.get("bootstrap_per_system") or {}).get(s)
                L.append(fmt_row(f"{label}: {s}", m)[:-1] + f" {h_text(bs)} |")
    return L


# ---------------------------------------------------------------- main analysis

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(ROOT / "reports/study_v1_5/results/results_final.json"))
    ap.add_argument("--batch-ids", default=str(ROOT / "runs/study_v1_5/final_ids_b1b2.json"))
    ap.add_argument("--recall", default=str(ROOT / "runs/study_v1_5/recall_b1b2.json"))
    ap.add_argument("--exclusions", default=str(ROOT / "configs/study_v1_5/headline_exclusions.json"))
    ap.add_argument("--pair-exclusions", action="append",
                    default=[str(ROOT / "runs/study_v1_5/headline_exclusions_pending.json")])
    ap.add_argument("--gold", default="runs/study_test_gold_b1,runs/study_test_gold_b2")
    ap.add_argument("--resamples", type=int, default=AN.RESAMPLES)
    ap.add_argument("--seed", type=int, default=AN.SEED)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    out_dir = Path(args.out_dir)

    final = json.loads(Path(args.results).read_text())
    switches = final["switches"]
    tag_switches, frozen = dv.frozen_switches(ROOT, final["frozen"]["tag"])
    if tag_switches != switches or frozen.get("tag_commit") != final["frozen"]["tag_commit"]:
        print("STOP: switches at the frozen tag differ from results_final.json", file=sys.stderr)
        return 2
    systems = final["systems"]
    labels = final["labels"]
    ids = [i if isinstance(i, str) else i["instance_id"] for i in json.loads(Path(args.batch_ids).read_text())]
    recall_tasks = {t["instance_id"] for t in json.loads(Path(args.recall).read_text())["tasks"] if t["recall_lines"]}
    scope = AN.Scope.load(ids, args.exclusions, [f for f in args.pair_exclusions if Path(f).is_file()])
    rows, _ = AN.build_rows(systems, labels, switches, scope, recall_tasks)
    pooled = tuple(s for s in AN.MINIMUM_SET if s in systems)
    tasks = {s: load_tasks(specs, switches) for s, specs in systems.items()}
    key = lambda r: (r.system, r.instance_id)  # noqa: E731
    ev_of = {key(r): tasks[r.system][r.instance_id]["evidence"] for r in rows}

    # ---- G1: frozen and V1+V2 counts reproduce results_final.json; own decide() equals frozen.
    ref = final["scopes"][HEADLINE]["policies"]
    g1 = {"pass": True, "checks": []}
    mine = {k: decide(e, switches) for k, e in ev_of.items()}
    own_differs = [f"{s}/{i}" for r in rows for s, i in [key(r)] if mine[key(r)][0] != r.decisions["frozen"]]
    rows = with_decisions(rows, "frozen_recomputed", {k: v[0] for k, v in mine.items()})
    for policy, col in (("frozen", "frozen_recomputed"), ("v1v2", "v1v2")):
        for name in [*pooled, "pooled"]:
            got = AN.metrics(rows, col, systems=pooled if name == "pooled" else (name,))["decisions"]
            want = (ref[policy]["pooled"] if name == "pooled" else ref[policy]["per_system"][name])["decisions"]
            ok = got == want
            g1["checks"].append({"policy": policy, "system": name, "match": ok, "counts": got})
            g1["pass"] &= ok
    g1["own_decide_differs"] = own_differs
    g1["pass"] &= not own_differs
    if not g1["pass"]:
        print("STOP: G1 failed: " + json.dumps(g1), file=sys.stderr)
        return 2
    print("G1 pass: " + "; ".join(f"{c['policy']} {c['system']} {c['counts']}" for c in g1["checks"]))

    run_args = (pooled, args.seed, args.resamples)
    frozen_block = block(rows, "frozen", *run_args)
    abl = {"header": HEADER, "g1": g1, "frozen": final["frozen"], "switches": switches,
           "seed": args.seed, "resamples": args.resamples, "pooled_systems": pooled}

    # ---- 2. Signal drop-outs (RQ3).
    drops = {}
    for sig in ("V1", "V2", "V3", "V4"):
        d = {k: decide(force_pass(e, sig), switches)[0] for k, e in ev_of.items()}
        rows = with_decisions(rows, f"drop_{sig}", d)
        drops[sig] = block(rows, f"drop_{sig}", *run_args)
        drops[sig]["changed"] = sum(d[key(r)] != r.decisions["frozen"] for r in AN.scored(rows))
    abl["signal_dropouts"] = drops

    # ---- 3. V2 fallback (RQ3).
    nofb, fb_changed, fb_removed, fb_errors = {}, [], [], []
    for r in rows:
        t = tasks[r.system][r.instance_id]
        try:
            e2, removed = dv.without_v2_fallback(t["run_path"], t["files"], r.instance_id, t["record"], t["evidence"])
        except ValueError as exc:
            fb_errors.append({"system": r.system, "instance_id": r.instance_id, "error": str(exc)})
            e2, removed = t["evidence"], False
        if removed:
            fb_removed.append(f"{r.system}/{r.instance_id}")
        if e2.regression is not t["evidence"].regression:
            fb_changed.append({"system": r.system, "instance_id": r.instance_id,
                               "v2_with": t["evidence"].regression.value, "v2_without": e2.regression.value})
        nofb[key(r)] = decide(e2, switches)[0]
    rows = with_decisions(rows, "no_v2_fallback", nofb)
    abl["v2_fallback"] = {**block(rows, "no_v2_fallback", *run_args), "fallback_removed": fb_removed,
                          "v2_outcome_changed": fb_changed, "not_recomputable": fb_errors,
                          "decision_changed": sum(nofb[key(r)] != r.decisions["frozen"] for r in AN.scored(rows))}

    # ---- 5. V2 accountings S/C/P (RQ4).
    acc_dec = {a: {} for a in V2_ACCOUNTINGS}
    acc_mismatch, acc_missing, stored_primary = [], [], Counter()
    for r in rows:
        t = tasks[r.system][r.instance_id]
        name = f"tasks/{r.instance_id}/verification/v2_policies.json"
        e = t["evidence"]
        if name not in t["files"]:
            acc_missing.append(f"{r.system}/{r.instance_id}")
            for a in V2_ACCOUNTINGS:
                acc_dec[a][key(r)] = r.decisions["frozen"]
            continue
        payload = json.loads(dv._read(t["run_path"], t["files"], name))
        primary = payload.get("primary_accounting")
        stored_primary[primary] += 1
        stored = (e.regression, e.v2_absence, e.v2_patched_timeout_or_crash)
        if v2_from_report(payload["policies"][primary]) != stored:
            acc_mismatch.append(f"{r.system}/{r.instance_id}")
        for a in V2_ACCOUNTINGS:
            ok = f"{r.system}/{r.instance_id}" not in acc_mismatch
            acc_dec[a][key(r)] = decide(with_v2(e, v2_from_report(payload["policies"][a])), switches)[0] if ok \
                else r.decisions["frozen"]
    accounts = {}
    for a in V2_ACCOUNTINGS:
        rows = with_decisions(rows, f"acc_{a}", acc_dec[a])
        accounts[a] = block(rows, f"acc_{a}", *run_args)
        changed = [r for r in AN.scored(rows) if acc_dec[a][key(r)] != r.decisions["frozen"]]
        accounts[a]["changed_vs_frozen"] = len(changed)
        accounts[a]["changed_tasks"] = [f"{r.system}/{r.instance_id} {r.decisions['frozen']} → {acc_dec[a][key(r)]} "
                                        f"({'correct' if r.correct else 'wrong'})" for r in changed]
    abl["v2_accountings"] = {"stored_primary": dict(stored_primary), "replay_mismatch": acc_mismatch,
                             "no_stored_v2_reports": len(acc_missing), "accountings": accounts}

    # ---- 4. Old vs per-requirement V4 on arm B (RQ3).
    abl["old_vs_new_v4"] = arm_b(args)

    # ---- 6. Gold coverage ceiling (RQ4).
    abl["gold"] = gold(args, switches)

    # ---- 7. Failure modes (RQ5).
    fm = {"header": HEADER, "frozen": final["frozen"], "pooled_systems": pooled}
    reports = {r_key: official_status(*r_key) for r_key in (key(r) for r in AN.scored(rows))}
    fm["false_accepts"] = false_accepts(rows, tasks, reports, switches)
    fm["wrong_type_by_decision"] = wrong_types(rows, reports)
    fm["per_repository"] = per_repo(rows)
    fm["git_peek"] = git_peek(rows, scope, *run_args)
    fm["v4_generator_audit"] = recall_audit(final)
    fm["empty_patch_sensitivity"] = empty_sensitivity(rows, *run_args)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ablations.json").write_text(json.dumps({**abl, "frozen_block": frozen_block}, indent=1, sort_keys=True,
                                                       default=list) + "\n")
    (out_dir / "failure_modes.json").write_text(json.dumps({**fm, "frozen_block": frozen_block}, indent=1,
                                                           sort_keys=True, default=list) + "\n")
    (out_dir / "ablations.md").write_text(render_ablations(abl, frozen_block))
    (out_dir / "failure_modes.md").write_text(render_failure_modes(fm, frozen_block))
    print(f"wrote {out_dir}/ablations.md, ablations.json, failure_modes.md, failure_modes.json")
    return 0


# ---------------------------------------------------------------- item 4: arm B

def arm_b(args):
    """v1.5 switches off on arm B's 51 dev patches, old (stored legacy) vs per-requirement V4, plus
    v1.5 frozen with the new V4. Evidence and labels from runs/study_v1_5/phase7_adoption.py, the
    script that wrote ADOPTION.md; task sources as in adoption_b12.json (amendment B12)."""
    sys.path.insert(0, str(ROOT / "runs/study_v1_5"))
    import phase7_adoption as pa  # noqa: E402
    adoption = json.loads((ROOT / "reports/study_v1_5/adoption_b12.json").read_text())
    ids = json.loads((ROOT / "reports/study_v1_5/pilot/dev_reference_ids.json").read_text())
    inputs = {r["instance_id"]: r["patch_sha256"] for r in json.loads((pa.ARMB_INPUTS / "tasks.json").read_text())}
    labels = pa.read_labels(pa.LABELS, inputs)
    by_run = defaultdict(list)
    for iid in ids:
        by_run[adoption["task_sources"][iid]].append(iid)
    new = {}
    for run, run_ids in by_run.items():
        e, _ = pa.sealed_evidence(ROOT / run, run_ids, require_complete=False)
        new.update(e)
    old, _ = pa.armb_old_evidence(ids)
    off = {k: False for k in AN.FROZEN_FOR_TESTS}
    frozen_sw, _ = dv.frozen_switches(ROOT, AN.FROZEN_TAG)
    dec = {"frozen_new_v4": {i: decide(new[i], frozen_sw)[0] for i in ids},
           "off_old_v4": {i: decide(old[i], off)[0] for i in ids},
           "off_new_v4": {i: decide(new[i], off)[0] for i in ids}}
    rows = [AN.Row(system="gpt-4.1-mini (arm B dev)", instance_id=i, empty=False, labelled=True, correct=labels[i],
                   decisions={k: v[i] for k, v in dec.items()}, v4_full_pass=bool(new[i].v4_full_pass), recall=False)
            for i in ids]
    sysname = ("gpt-4.1-mini (arm B dev)",)
    out = {k: block(rows, k, sysname, args.seed, args.resamples) for k in dec}
    cells = lambda k: out[k]["pooled"]["decisions"]  # noqa: E731
    step_a = adoption["step_a"]
    out["crosscheck_adoption_b12"] = {
        "off_new_v4": cells("off_new_v4") == step_a["new_v4_off"]["cells"],
        "off_old_v4": cells("off_old_v4") == step_a["old_v4_off"]["cells"],
        "frozen_new_v4_vs_adopted": cells("frozen_new_v4") == adoption["armb_summary"].get(
            "v1.5 adopted (r2, r6, r6b)", {}).get("cells")}
    out["changed_old_to_new"] = sorted(i for i in ids if dec["off_old_v4"][i] != dec["off_new_v4"][i])
    out["task_sources"] = {k: len(v) for k, v in by_run.items()}
    return out


# ---------------------------------------------------------------- item 6: gold

def dataset_test_patch_files():
    from reliability.benchmark.loader import load_verified
    return {row["instance_id"]: patch_files(row["test_patch"]) for row in load_verified()}


def gold(args, switches):
    gold_tasks = load_tasks(args.gold.split(","), switches)
    csv_rows = {}
    for b in ("b1", "b2"):
        for f in (ROOT / f"reports/study_v1_5/test_gold_{b}/decisions_frozen").glob("decisions_*.csv"):
            for row in csv.DictReader(f.open()):
                csv_rows[row["instance_id"]] = row
    tp = dataset_test_patch_files()
    per_task, csv_differs = [], []
    for iid, t in sorted(gold_tasks.items()):
        decision, rule, reason = decide(t["evidence"], switches)
        c = csv_rows.get(iid)
        if c is None or (c["decision"], c["rule_id"]) != (decision, rule):
            csv_differs.append(iid)
        if decision == "ACCEPT":
            continue
        outcomes = t["record"].signals[SignalKind.REGRESSION].findings.get("outcomes")
        cause = gold_cause(rule, reason, t["evidence"], failing_v2_files(outcomes), tp.get(iid, set()))
        per_task.append({"instance_id": iid, "decision": decision, "rule": rule, "reason": reason, **cause})
    n = len(gold_tasks)
    accepted = n - len(per_task)
    counts = Counter(p["cause"] for p in per_task)
    second = Counter(p["second_cause"] for p in per_task if p["second_cause"])
    return {"gold_patches": n, "accepted": AN.rate(accepted, n), "flag": sum(p["decision"] == "FLAG" for p in per_task),
            "reject": sum(p["decision"] == "REJECT" for p in per_task), "cause_counts": dict(counts),
            "second_cause_counts": dict(second), "per_task": per_task, "csv_differs": csv_differs}


# ---------------------------------------------------------------- item 7: failure modes

def official_status(system, iid):
    """(per-test status, source, report sha256, patch applied by the grader) from the label source used
    for this (system, task)."""
    if system == "gpt-4.1-mini":
        for folder in ("gpt-4.1-mini_ours", "gpt-4.1-mini_b2"):
            res = LABELS_DIR / folder / "gpt-4.1-mini" / iid / "result.json"
            if res.is_file():
                r = json.loads(res.read_text())
                rep = Path(r["report_file"])
                if rep.is_file() and sha(rep) == r["report_sha256"]:
                    data = json.loads(rep.read_text())
                    return (tests_status(data, iid), f"our grader ({folder})", r["report_sha256"],
                            applied_flag(data, iid))
                return None, f"our grader ({folder}): report missing or sha256 differs", None, None
        return None, "our grader: no result", None, None
    for folder in (system, f"{system}_b2"):
        rep = LABELS_DIR / folder / "logs" / iid / "report.json"
        if rep.is_file():
            data = json.loads(rep.read_text())
            return tests_status(data, iid), f"official report.json ({folder})", sha(rep), applied_flag(data, iid)
    return None, "no official report.json", None, None


def false_accepts(rows, tasks, reports, switches):
    out = []
    for r in AN.scored(rows):
        if r.correct or r.decisions["frozen"] != "ACCEPT":
            continue
        t = tasks[r.system][r.instance_id]
        e = t["evidence"]
        _, rule, reason = decide(e, switches)
        status, source, rep_sha, applied = reports[(r.system, r.instance_id)]
        f2p, p2p = failed(status, "FAIL_TO_PASS"), failed(status, "PASS_TO_PASS")
        outcomes = t["record"].signals[SignalKind.REGRESSION].findings.get("outcomes") or {}
        v2_names = {bare_test_name(k) for k in outcomes}
        p2p_run = sorted(n for n in p2p if bare_test_name(n) in v2_names)
        f2p_run = sorted(n for n in f2p if bare_test_name(n) in v2_names)
        v2_text = e.regression.value + (f" ({e.v2_absence})" if e.v2_absence else "")
        v2_ran = ("V2 had nothing to check (no test selected)" if not outcomes
                  else f"V2 {v2_text} on the {len(outcomes)} tests it ran")
        if status is None:
            why = (("the grader could not apply the patch (patch_successfully_applied false), so there is no per-test "
                    "status; our verifier applied it" if applied is False else "the grader report has no per-test status")
                   + f"; {v2_ran}; V4 passed {e.v4_pass_units} requirement(s)")
        elif p2p and not p2p_run:
            why = (f"{v2_ran}, none of them a PASS_TO_PASS test the grader saw fail (matched by test name); "
                   f"V4 passed {e.v4_pass_units} requirement(s)")
        elif p2p_run:
            why = (f"V2 ran {len(p2p_run)} of the PASS_TO_PASS tests that failed officially (by test name) but did not "
                   f"report them as regressions; V4 passed {e.v4_pass_units} requirement(s)")
        else:
            why = (f"the official failures are FAIL_TO_PASS only; V4 passed {e.v4_pass_units} requirement(s) "
                   f"({e.v4_uncovered_units} uncovered) without catching the missing behaviour; {v2_ran}")
        out.append({"system": r.system, "instance_id": r.instance_id, "repo": repo_of(r.instance_id), "rule": rule,
                    "reason": reason, "v2": v2_text, "v4_pass_units": e.v4_pass_units,
                    "v4_uncovered_units": e.v4_uncovered_units, "v4_full_pass": e.v4_full_pass,
                    "wrong_type": wrong_type(status), "fail_to_pass_failed": f2p, "pass_to_pass_failed": p2p,
                    "official_failures_run_by_v2": {"FAIL_TO_PASS": f2p_run, "PASS_TO_PASS": p2p_run},
                    "status_source": source, "report_sha256": rep_sha, "grader_applied_patch": applied,
                    "why_missed": why})
    return out


def wrong_types(rows, reports):
    def table(rs):
        c = Counter((wrong_type(reports[(r.system, r.instance_id)][0]), r.decisions["frozen"])
                    for r in AN.scored(rs) if not r.correct)
        types = sorted({t for t, _ in c})
        return {t: {d: c[t, d] for d in ("ACCEPT", "FLAG", "REJECT")} for t in types}
    systems = sorted({r.system for r in rows})
    return {"pooled": table(rows), "per_system": {s: table([r for r in rows if r.system == s]) for s in systems},
            "sources": dict(Counter(reports[(r.system, r.instance_id)][1] for r in AN.scored(rows))),
            "unknown_grader_could_not_apply": sorted(
                f"{r.system}/{r.instance_id}" for r in AN.scored(rows) if not r.correct
                and reports[(r.system, r.instance_id)][0] is None and reports[(r.system, r.instance_id)][3] is False)}


def short(names, n=4):
    names = list(names)
    return "—" if not names else ", ".join(names[:n]) + (f" and {len(names) - n} more" if len(names) > n else "")


def per_repo(rows):
    c = defaultdict(Counter)
    for r in AN.scored(rows):
        c[repo_of(r.instance_id)][f"{r.decisions['frozen']}_{'correct' if r.correct else 'wrong'}"] += 1
    return {repo: {k: c[repo][k] for d in ("ACCEPT", "FLAG", "REJECT") for k in (f"{d}_correct", f"{d}_wrong")}
            for repo in sorted(c)}


def git_peek(rows, scope, pooled, seed, resamples):
    listed, files = set(), {}
    for s in pooled:
        f = GIT_PEEK_DIR / s / "git_peek_suspicious_commits.md"
        if not f.is_file():
            files[s] = {"file": None, "note": "no git_peek_suspicious_commits.md for this system"}
            continue
        iids = git_peek_ids(f.read_text(encoding="utf-8"))
        in_scope = sorted(i for i in iids if scope.keeps(s, i))
        files[s] = {"file": str(f.relative_to(ROOT)), "sha256": sha(f), "source": GIT_PEEK_SOURCE.format(folder=SUBMISSION[s]),
                    "listed": len(iids), "in_headline_scope": in_scope,
                    "scored_in_headline": sorted(r.instance_id for r in AN.scored(rows) if r.system == s and r.instance_id in iids)}
        listed |= {(s, i) for i in iids}
    kept = [r for r in rows if (r.system, r.instance_id) not in listed]
    return {"files": files, "pairs_removed": sum((r.system, r.instance_id) in listed for r in AN.scored(rows)),
            "block": block(kept, "frozen", pooled, seed, resamples)}


def recall_audit(final):
    out = {}
    for b in ("b1", "b2"):
        f = ROOT / f"reports/study_v1_5/test_gold_{b}/test_gold_{b}_recall.json"
        d = json.loads(f.read_text())
        with_recall = {t["instance_id"]: t["recall_lines"] for t in d["tasks"] if t["recall_lines"]}
        out[b] = {"file": str(f.relative_to(ROOT)), "tasks": len(d["tasks"]), "tasks_with_recall": len(with_recall),
                  "recall_lines": sum(with_recall.values()) if all(isinstance(v, int) for v in with_recall.values())
                  else None, "ids": sorted(with_recall)}
    nr = final["scopes"].get("sensitivity: headline minus tasks with generator recall")
    out["no_recall_sensitivity"] = ({"where": "results_final.md, scope 'sensitivity: headline minus tasks with generator recall'",
                                     "pooled": {k: nr["policies"]["frozen"]["pooled"][k] for k in
                                                ("n", "accept_precision", "coverage", "false_accept_rate")},
                                     "bootstrap": nr["policies"]["frozen"]["bootstrap"]} if nr else None)
    return out


def empty_sensitivity(rows, pooled, seed, resamples):
    counts = {s: sum(r.empty for r in rows if r.system == s) for s in pooled}
    ids = {s: sorted(r.instance_id for r in rows if r.system == s and r.empty) for s in pooled}
    er = empty_as_wrong_reject(rows, "frozen")
    return {"empty_counts": counts, "empty_ids": ids,
            "block": block(er, "frozen", pooled, seed, resamples, per_system_bootstrap=True)}


# ---------------------------------------------------------------- rendering

def render_ablations(a, fb):
    L = ["# Study v1.5 Phase 16: ablations (RQ3, RQ4)", "", f"*{HEADER}*", "",
         f"Headline scope throughout (results_final.md). Decisions: v1.5 with the switches at tag `{a['frozen']['tag']}` "
         f"(`{a['frozen']['tag_commit'][:12]}`) unless a row says otherwise. Pooled = {', '.join(a['pooled_systems'])}. "
         f"Bootstrap: task-clustered, {a['resamples']} resamples, seed {a['seed']}. Each table starts with the v1.5 frozen row.", ""]
    g = a["g1"]
    L += ["## Gate G1", "", f"Frozen and V1+V2 decision counts recomputed here equal results_final.json per system and pooled: "
          f"**{'pass' if g['pass'] else 'FAIL'}** ({sum(c['match'] for c in g['checks'])}/{len(g['checks'])} checks; "
          f"own decide() differs on {len(g['own_decide_differs'])} patches).", ""]
    for c in g["checks"]:
        d = c["counts"]
        L.append(f"- {c['policy']} {c['system']}: A {d['ACCEPT_correct']}/{d['ACCEPT_wrong']}, F {d['FLAG_correct']}/"
                 f"{d['FLAG_wrong']}, R {d['REJECT_correct']}/{d['REJECT_wrong']} (correct/wrong) — {'match' if c['match'] else 'DIFFERS'}")
    L.append("")

    L += ["## 1. Signal drop-outs (RQ3)", "",
          "Each signal forced to PASS in turn (V1 also clears apply, manipulation, risk and incomplete-analysis flags; "
          "V3 also clears the absolute-failure flag; V4 becomes a full pass), decided with the frozen rules. "
          "This shows how much each signal contributes: a row close to the frozen row means that signal changes little.", ""]
    L += variant_table([("v1.5 frozen", fb)] + [(f"{s} forced PASS ({b['changed']} decisions change)", b)
                                                for s, b in a["signal_dropouts"].items()])
    L.append("")

    v = a["v2_fallback"]
    L += ["## 2. With vs without the V2 fallback (RQ3)", "",
          f"Frozen rules with the fallback-selected V2 tests removed (decide_v1_5.without_v2_fallback). The fallback ran on "
          f"{len(v['fallback_removed'])} headline patches; removing it changes the V2 outcome on {len(v['v2_outcome_changed'])} "
          f"and the decision on {v['decision_changed']} scored patches; {len(v['not_recomputable'])} could not be recomputed.", ""]
    L += variant_table([("v1.5 frozen", fb), ("without V2 fallback", v)])
    if v["v2_outcome_changed"]:
        L += ["", "V2 outcome changes: " + ", ".join(f"{c['system']}/{c['instance_id']} {c['v2_with']} → {c['v2_without']}"
                                                   for c in v["v2_outcome_changed"]) + "."]
    if v["not_recomputable"]:
        L += ["", "Not recomputable (kept at the frozen evidence): " + "; ".join(
            f"{c['system']}/{c['instance_id']}: {c['error']}" for c in v["not_recomputable"]) + "."]
    L.append("")

    o = a["old_vs_new_v4"]
    L += ["## 3. Old vs per-requirement V4 on arm B (RQ3)", "",
          "Arm B's 51 gpt-4.1-mini dev patches with arm B's dev labels (25 correct, 26 wrong), as in ADOPTION.md. v1.5 with "
          "switches off, once with the stored old (legacy) V4 signals and once with the new per-requirement V4; the first row is "
          "v1.5 frozen with the new V4. Task sources follow amendment B12 (adoption_b12.json): "
          + ", ".join(f"{k} {n}" for k, n in o["task_sources"].items()) + ". Dev data, so one patch per task.", ""]
    L += variant_table([("v1.5 frozen, new V4", o["frozen_new_v4"]), ("switches off, old V4", o["off_old_v4"]),
                        ("switches off, new V4", o["off_new_v4"])])
    cc = o["crosscheck_adoption_b12"]
    L += ["", f"Cross-check against adoption_b12.json: switches off new V4 {'equal' if cc['off_new_v4'] else 'DIFFERS'}, "
          f"old V4 {'equal' if cc['off_old_v4'] else 'DIFFERS'}, frozen new V4 vs adopted {'equal' if cc['frozen_new_v4_vs_adopted'] else 'DIFFERS'}. "
          f"Decisions that change from old to new V4: {len(o['changed_old_to_new'])} ({', '.join(o['changed_old_to_new']) or 'none'}).", ""]

    s = a["v2_accountings"]
    L += ["## 4. V2 accountings S/C/P (RQ4)", "",
          "V2 recomputed from each task's stored per-accounting reports (verification/v2_policies.json, sealed), then decided "
          f"with the frozen rules. The frozen v1.5 runs used {', '.join(f'{k} ({n} tasks)' for k, n in s['stored_primary'].items())} "
          "as primary (PROTOCOL change 1, configs/verifier/v1_5.yaml `v2_primary_accounting`); the Phase 16 prompt names "
          "S_invalid_excluded as primary, so both are marked. Replaying the stored primary reproduces the stored V2 evidence on "
          f"every task except {len(s['replay_mismatch'])} ({', '.join(s['replay_mismatch']) or 'none'}), which keep the frozen decision. "
          f"{s['no_stored_v2_reports']} headline patches have no V2 reports (V2 never ran), so they are the same under every accounting.", ""]
    rowsv = [("v1.5 frozen", fb)]
    for name, b in s["accountings"].items():
        mark = " [frozen primary]" if name in s["stored_primary"] else ""
        mark += " [prompt primary]" if name == "S_invalid_excluded" else ""
        rowsv.append((f"{name}{mark} ({b['changed_vs_frozen']} decisions change)", b))
    L += variant_table(rowsv)
    for name, b in s["accountings"].items():
        if b["changed_tasks"]:
            L += ["", f"{name} changes: " + "; ".join(b["changed_tasks"]) + "."]
    L.append("")

    gd = a["gold"]
    acc = gd["accepted"]
    L += ["## 5. Gold coverage ceiling (RQ4)", "",
          f"All {gd['gold_patches']} test-set gold patches (batches 1 and 2), frozen rules. Gold ACCEPTed: {acc['k']}/{acc['n']} = "
          f"{AN.ci_text(acc)} (Wilson). FLAG {gd['flag']}, REJECT {gd['reject']}. Recomputed decisions and rules differ from "
          f"decisions_frozen on {len(gd['csv_differs'])} tasks ({', '.join(gd['csv_differs']) or 'none'}). "
          "This is the ceiling on coverage: a correct patch that looks like gold is held back at least this often.", "",
          "| cause (first matching rule) | count |", "|---|---:|"]
    for c, n in sorted(gd["cause_counts"].items(), key=lambda x: -x[1]):
        L.append(f"| {c} | {n} |")
    for c, n in gd["second_cause_counts"].items():
        L.append(f"| second cause: {c} | {n} |")
    sup = [p for p in gd["per_task"] if p["cause"] == "superseded assertion"]
    L += ["", f"Superseded assertions confirmed (every failing V2 test file is modified by the task's test_patch): "
          f"{sum(bool(p['confirmed']) for p in sup)} of {len(sup)}.", "",
          "The per-task list gives each gold FLAG or REJECT with its rule and cause.", "",
          "| task | decision | rule | cause | second cause | confirmed |", "|---|---|---|---|---|---|"]
    for p in gd["per_task"]:
        conf = "" if p["confirmed"] is None else ("yes" if p["confirmed"] else "no")
        L.append(f"| {p['instance_id']} | {p['decision']} | {p['rule']} | {p['cause']} | {p['second_cause'] or ''} | {conf} |")
    L.append("")
    return "\n".join(L)


def render_failure_modes(fm, fb):
    L = ["# Study v1.5 Phase 16: failure modes (RQ5)", "", f"*{HEADER}*", "",
         f"Headline scope, frozen rules (tag `{fm['frozen']['tag']}`). Pooled = {', '.join(fm['pooled_systems'])}. "
         "Test names only; no patch or test-file contents.", ""]
    fa = fm["false_accepts"]
    L += ["## a. Every false ACCEPT", "",
          f"{len(fa)} wrong patches were ACCEPTed. For each: the rule, the signals, the wrong-patch type, the tests the official "
          "grader saw fail, and why the verifier's signals did not catch it.", "",
          "| system | task | repo | rule | V2 | V4 pass / uncovered | type | FAIL_TO_PASS failed | PASS_TO_PASS failed | why not caught |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for f in fa:
        L.append(f"| {f['system']} | {f['instance_id']} | {f['repo']} | {f['rule']} | {f['v2']} | {f['v4_pass_units']} / "
                 f"{f['v4_uncovered_units']} | {f['wrong_type']} | {short(f['fail_to_pass_failed'])} | "
                 f"{short(f['pass_to_pass_failed'])} | {f['why_missed']} |")
    wt = fm["wrong_type_by_decision"]
    L += ["", "## b. Wrong-patch type × decision", "",
          "Wrong patches by type (U: a FAIL_TO_PASS test does not pass, no PASS_TO_PASS fails; R: all FAIL_TO_PASS pass, a "
          "PASS_TO_PASS fails; X: both; unknown: no per-test status). It shows which kinds of wrong patch the verifier holds back. "
          "Sources: " + ", ".join(f"{k} {n}" for k, n in wt["sources"].items()) + ". Unknown includes "
          f"{len(wt['unknown_grader_could_not_apply'])} wrong patches the grader could not apply "
          f"({', '.join(wt['unknown_grader_could_not_apply']) or 'none'}).", "",
          "| scope | type | ACCEPT | FLAG | REJECT |", "|---|---|---:|---:|---:|"]
    for name, tbl in [("pooled", wt["pooled"]), *wt["per_system"].items()]:
        for t, d in tbl.items():
            L.append(f"| {name} | {t} | {d['ACCEPT']} | {d['FLAG']} | {d['REJECT']} |")
    pr = fm["per_repository"]
    L += ["", "## c. Per repository (pooled)", "", "Decisions on correct and wrong patches per repository; it shows where "
          "the verifier is accurate and where it holds back or lets through most.", "",
          "| repo | ACCEPT c/w | FLAG c/w | REJECT c/w |", "|---|---|---|---|"]
    for repo, d in pr.items():
        L.append(f"| {repo} | {d['ACCEPT_correct']}/{d['ACCEPT_wrong']} | {d['FLAG_correct']}/{d['FLAG_wrong']} | "
                 f"{d['REJECT_correct']}/{d['REJECT_wrong']} |")
    gp = fm["git_peek"]
    L += ["", "## d. git_peek sensitivity", "",
          f"The headline minus the (system, task) pairs listed in each system's git_peek_suspicious_commits.md "
          f"({gp['pairs_removed']} scored pairs removed). It shows whether trajectories that peeked at git history drive the result.", ""]
    for s, f in gp["files"].items():
        if f["file"] is None:
            L.append(f"- {s}: {f['note']}.")
        else:
            L.append(f"- {s}: {f['listed']} listed; in headline scope: {', '.join(f['in_headline_scope']) or 'none'}; "
                     f"`{f['file']}` sha256 `{f['sha256']}` (from {f['source']}).")
    L += [""] + variant_table([("v1.5 frozen", fb), ("minus git_peek pairs", gp["block"])], per_system=True) + [""]
    ra = fm["v4_generator_audit"]
    L += ["## e. V4 generator audit (A3 recall)", "",
          "Gold tasks where the V4 generator wrote a gold-patch line itself (recall, recorded under A3; not a leak).", ""]
    for b in ("b1", "b2"):
        r = ra[b]
        L.append(f"- batch {b[1]}: {r['tasks_with_recall']} of {r['tasks']} tasks with recall"
                 + (f", {r['recall_lines']} lines" if r["recall_lines"] is not None else "") + f" (`{r['file']}`): "
                 + ", ".join(r["ids"]) + ".")
    nr = ra["no_recall_sensitivity"]
    if nr:
        p = nr["pooled"]
        L += ["", f"No-recall sensitivity is in {nr['where']}: pooled n {p['n']}, ACCEPT precision {AN.ci_text(p['accept_precision'])}, "
              f"coverage {AN.ci_text(p['coverage'])}, false-accept rate {AN.ci_text(p['false_accept_rate'])}; {h_text(nr['bootstrap'])}."]
    es = fm["empty_patch_sensitivity"]
    L += ["", "## f. Empty-patch sensitivity (PLAN §6)", "",
          "Every empty patch counted as a wrong patch held back (decision REJECT). It shows how much leaving empty patches out "
          "flatters the headline. Empty patches in the headline scope: "
          + ", ".join(f"{s} {n}" for s, n in es["empty_counts"].items()) + ".", ""]
    L += variant_table([("v1.5 frozen", fb), ("empty = wrong, REJECT", es["block"])], per_system=True)
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
