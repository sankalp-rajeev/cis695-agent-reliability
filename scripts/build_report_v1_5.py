#!/usr/bin/env python3
"""Build reports/study_v1_5/REPORT.md, the README results block and two figures (Phase 18).

    env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/build_report_v1_5.py

Fills reports/study_v1_5/report_template.md ({{name}} placeholders) from the committed result
files and writes REPORT.md; fills the block between <!-- results:start --> and
<!-- results:end --> in README.md; draws figures/fig1_precision_vs_base.svg and
figures/fig2_ablations.svg. Every statistic comes from a file:

    reports/study_v1_5/results/{results_final,results_b2,ablations,failure_modes,b14_no_results}.json
    reports/study_v1_5/test_gold_b{1,2}/decisions_frozen/decisions_*.csv
    and, for context: adoption_b12.json, results/labels/agreement_ours/agreement.json,
    results/b3_cutoff.json, configs/study_v1_5/headline_exclusions.json, docs/results_100.md,
    PLAN.md §11, STATUS.md (phase table), runs/provider_spend_ledger.json, git tags.

Each message the report states in words is checked against the numbers first; if one no longer
holds, the build stops instead of writing a false sentence. Output is deterministic: running the
script twice gives byte-identical files. Never reads or prints patch content.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "reports/study_v1_5"
RES = S / "results"
HL = "headline (batch, minus headline exclusions)"
ALL = "sensitivity: all tasks (no exclusions)"
NR = "sensitivity: headline minus tasks with generator recall"
SYSTEMS = ("gpt-4.1-mini", "claude-sonnet-4", "gemini-2.5-flash")
NAMES = {"gpt-4.1-mini": "gpt-4.1-mini", "claude-sonnet-4": "Claude Sonnet 4", "gemini-2.5-flash": "Gemini 2.5 Flash"}
START, END = "<!-- results:start -->", "<!-- results:end -->"
BLUE, ORANGE, INK, INK2, GRID, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"


# ---------------------------------------------------------------- formatting

def pct(x, d=1):
    return "n/a" if x is None else f"{100 * x:.{d}f}%"


def ci(r):
    if r.get("value") is None:
        return "n/a"
    lo, hi = r["ci"]
    return f"{pct(r['value'])} [{pct(lo)}, {pct(hi)}]"


def kn(r):
    return f"{r['k']}/{r['n']}"


def pp(x):
    return f"{100 * x:+.1f} pp"


def num(x, d=2):
    return "n/a" if x is None else f"{x:.{d}f}"


def pval(p):
    return f"{p:.3g}"


def render(template, values):
    def sub(m):
        return values[m.group(1)]  # KeyError on a missing placeholder
    return re.sub(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", sub, template)


def fill_block(text, block):
    if START not in text or END not in text:
        raise ValueError("README has no results block markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{block}\n{END}{tail}" if block else f"{head}{START}\n{END}{tail}"


# ---------------------------------------------------------------- typed-number scanner

ALLOWED = {"20261126", "20261120", "10,000", "10000", "200", "92", "108", "60", "48", "500", "695", "2026", "2025"}
MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"


def typed_numbers(text):
    """Numbers typed into prose or tables that are not placeholders or protocol constants."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"`[^`\n]*`", " ", t)
    t = re.sub(r"\{\{[^}]*\}\}", " ", t)
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"Claude Sonnet 4|Gemini 2\.5 Flash|\b95% (?:CI|CIs|upper)\b", " ", t)  # model names, CI level
    t = re.sub(r"\b\d{1,2}:\d{2}\b", " ", t)
    t = re.sub(r"\b(?:[Bb]atch(?:es)?|[Pp]hases?|[Ss]ections?|[Ff]igures?|[Cc]hanges?|[Ss]teps?|[Ii]tems?|[Rr]ows?|"
               r"[Cc]ut rules?|[Pp]arts?)\s+\d+(?:\s*(?:,|and|–|-|to|\+)\s*\d+)*", " ", t)
    t = re.sub(rf"\b\d{{1,2}}\s+{MONTHS}\b", " ", t)
    t = re.sub(rf"\b{MONTHS}\s+\d{{1,2}}\b", " ", t)
    lines = []
    for line in t.splitlines():
        line = re.sub(r"^\s*#+\s+\d+(\.\d+)*\.?\s", " ", line)
        line = re.sub(r"^\s*\d+\.\s", " ", line)
        lines.append(line)
    t = "\n".join(lines)
    out = []
    for m in re.finditer(r"(?<![\w.\-/§$])(\d[\d,]*(?:\.\d+)?)(?![\w\-/]|\.\d)(\s*%)?", t):
        token, percent = m.group(1).rstrip(","), m.group(2)
        if percent or token not in ALLOWED:
            out.append(m.group(0).strip())
    return out


# ---------------------------------------------------------------- figures (plain SVG, deterministic)

def _svg_head(w, h, title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="Helvetica, Arial, sans-serif" role="img" aria-label="{title}">',
            f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>',
            f'<text x="16" y="24" font-size="15" fill="{INK}" font-weight="bold">{title}</text>']


def _legend(x, y, items):
    out = []
    for i, (label, color) in enumerate(items):
        xx = x + i * 190
        out += [f'<circle cx="{xx}" cy="{y}" r="5" fill="{color}"/>',
                f'<text x="{xx + 10}" y="{y + 4}" font-size="12" fill="{INK2}">{label}</text>']
    return out


def svg_points(points, title):
    """points: [(label, base, (lo, hi), precision, (lo, hi))] -> dot-and-whisker, 0-100% axis."""
    w, left, right, row = 760, 190, 40, 46
    h = 70 + row * len(points) + 40
    sx = lambda v: left + v * (w - left - right)  # noqa: E731
    L = _svg_head(w, h, title) + _legend(left, 46, [("base rate (Wilson 95% CI)", BLUE),
                                                     ("ACCEPT precision (Wilson 95% CI)", ORANGE)])
    top = 70
    for t in range(0, 11, 2):
        x = sx(t / 10)
        L += [f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{h - 34}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{x:.1f}" y="{h - 18}" font-size="11" fill="{INK2}" text-anchor="middle">{t * 10}%</text>']
    for i, (label, base, bci, prec, pci) in enumerate(points):
        y = top + row * i + row / 2
        L.append(f'<text x="{left - 12}" y="{y + 4:.1f}" font-size="12" fill="{INK}" text-anchor="end">{label}</text>')
        for v, (lo, hi), color, dy in ((base, bci, BLUE, -8), (prec, pci, ORANGE, 8)):
            if v is None:
                continue
            L += [f'<line x1="{sx(lo):.1f}" y1="{y + dy:.1f}" x2="{sx(hi):.1f}" y2="{y + dy:.1f}" stroke="{color}" stroke-width="2"/>',
                  f'<circle cx="{sx(v):.1f}" cy="{y + dy:.1f}" r="5" fill="{color}" stroke="{SURFACE}" stroke-width="2"/>',
                  f'<text x="{sx(hi) + 6:.1f}" y="{y + dy + 4:.1f}" font-size="11" fill="{INK2}">{pct(v)}</text>']
    L.append("</svg>")
    return "\n".join(L) + "\n"


def svg_bars(rows, title):
    """rows: [(label, precision, false-accept rate)] -> paired horizontal bars, 0-100% axis."""
    w, left, right, row, bar = 760, 230, 50, 40, 12
    h = 70 + row * len(rows) + 40
    sx = lambda v: left + v * (w - left - right)  # noqa: E731
    L = _svg_head(w, h, title) + _legend(left, 46, [("pooled ACCEPT precision", BLUE), ("pooled false-accept rate", ORANGE)])
    top = 70
    for t in range(0, 11, 2):
        x = sx(t / 10)
        L += [f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{h - 34}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{x:.1f}" y="{h - 18}" font-size="11" fill="{INK2}" text-anchor="middle">{t * 10}%</text>']
    for i, (label, prec, far) in enumerate(rows):
        y = top + row * i + 6
        L.append(f'<text x="{left - 12}" y="{y + bar + 2:.1f}" font-size="12" fill="{INK}" text-anchor="end">{label}</text>')
        for j, (v, color) in enumerate(((prec, BLUE), (far, ORANGE))):
            yy = y + j * (bar + 2)
            wv = max(sx(v) - left, 1)
            L += [f'<rect x="{left}" y="{yy:.1f}" width="{wv:.1f}" height="{bar}" rx="2" fill="{color}"/>',
                  f'<text x="{left + wv + 6:.1f}" y="{yy + bar - 2:.1f}" font-size="11" fill="{INK2}">{pct(v)}</text>']
    L.append("</svg>")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- tables

COLS = ("| | n | base rate | ACCEPT precision [95% CI] | lift | coverage | false-accept rate | wrong rejected | "
        "correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |\n"
        "|---|---:|---|---|---:|---|---|---|---|---|---|---:|")


def mrow(label, m):
    hb = m["held_back_difference"]
    hbt = "n/a" if hb["value"] is None else f"{pct(hb['value'])} [{pct(hb['ci_newcombe'][0])}, {pct(hb['ci_newcombe'][1])}]"
    return (f"| {label} | {m['n']} | {ci(m['base_rate'])} | {ci(m['accept_precision'])} | {num(m['lift'])} | "
            f"{ci(m['coverage'])} | {ci(m['false_accept_rate'])} | {ci(m['wrong_rejected'])} | "
            f"{ci(m['correct_rejected'])} | {ci(m['flag_rate'])} | {hbt} | {pval(m['fisher_p'])} |")


def full_table(block):
    rows = [mrow(NAMES[s], block["per_system"][s]) for s in SYSTEMS if s in block["per_system"]]
    return "\n".join([COLS, *rows, mrow("**pooled**", block["pooled"])])


def htext(b):
    return (f"H1 (precision − base rate) 95% CI [{pct(b['h1_ci'][0])}, {pct(b['h1_ci'][1])}], "
            f"{'supported' if b['h1_supported'] else 'not supported'}; H2 (held-back difference) 95% CI "
            f"[{pct(b['h2_ci'][0])}, {pct(b['h2_ci'][1])}], {'supported' if b['h2_supported'] else 'not supported'}")


def hshort(b):
    return (f"[{pct(b['h1_ci'][0])}, {pct(b['h1_ci'][1])}] / [{pct(b['h2_ci'][0])}, {pct(b['h2_ci'][1])}] "
            f"{'✓' if b['h1_supported'] and b['h2_supported'] else '✗'}")


SHORT = ("| variant | n | ACCEPT precision [95% CI] | coverage | false-accept rate | ACCEPT correct/wrong | "
         "bootstrap H1 / H2 95% CI |\n|---|---:|---|---|---|---|---|")


def srow(label, m, b):
    d = m["decisions"]
    return (f"| {label} | {m['n']} | {ci(m['accept_precision'])} | {ci(m['coverage'])} | {ci(m['false_accept_rate'])} | "
            f"{d['ACCEPT_correct']}/{d['ACCEPT_wrong']} | {hshort(b) if b else 'n/a'} |")


# ---------------------------------------------------------------- inputs

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def gold_csv():
    out = {}
    for b in ("b1", "b2"):
        f = next((S / f"test_gold_{b}/decisions_frozen").glob("decisions_*.csv"))
        out[b] = Counter(r["decision"] for r in csv.DictReader(f.open(encoding="utf-8")))
    return out


def results_100():
    text = (ROOT / "docs/results_100.md").read_text(encoding="utf-8")
    halves = re.findall(r"### Half ([AB]).*?RESOLVED-claim precision \(patch-level\): \*\*(\d+)/(\d+)\*\*", text, re.S)
    allm = re.search(r"### All 100.*?RESOLVED-claim precision \(patch-level\): \*\*(\d+)/(\d+)\*\*", text, re.S)
    return {h: (int(k), int(n)) for h, k, n in halves}, (int(allm.group(1)), int(allm.group(2)))


def plan_500():
    text = (S / "PLAN.md").read_text(encoding="utf-8")
    sec = text.split("## 11. Scaling to 500", 1)[1].split("\n## ", 1)[0]
    return " ".join(sec.split(")", 1)[1].split()) if sec.startswith(" (") else " ".join(sec.split())


def phase_table():
    text = (S / "STATUS.md").read_text(encoding="utf-8")
    rows = ["| # | Phase | What it does | Status |", "|---|---|---|---|"]
    for line in text.split("## Phases", 1)[1].split("\n## ", 1)[0].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0] not in ("#", "---") and not set(cells[0]) <= {"-"}:
            what = re.split(r"(?<=\.)\s", cells[2])[0]
            if len(what) > 110:
                what = what[:107].rsplit(" ", 1)[0]
                if what.count("(") > what.count(")"):
                    what = what[:what.rfind("(")].rstrip()
                what = what.rstrip(";:,") + " …"
            rows.append(f"| {cells[0]} | {cells[1]} | {what} | {cells[4]} |")
    return "\n".join(rows)


def spend():
    ledger = ROOT / "runs/provider_spend_ledger.json"
    calls = [c for c in load(ledger)["calls"] if c.get("provider") == "deepseek"]
    by_job = Counter()
    for c in calls:
        by_job[Path(str(c.get("job"))).name] += float(c["cost_usd"])
    total = sum(by_job.values())
    return total, by_job


def earlier_work():
    lines = []
    for d in sorted(p for p in (ROOT / "reports").iterdir() if p.is_dir() and p.name not in ("study_v1_5", "history")):
        main = next((d / n for n in ("REPORT.md", "README.md", "report.md", "analysis.md") if (d / n).is_file()), None)
        if main is None:
            mds = sorted(d.rglob("*.md"))
            main = mds[0] if mds else None
        title = "(no markdown document)"
        if main is not None:
            m = re.search(r"^#\s+(.+)$", main.read_text(encoding="utf-8", errors="replace"), re.M)
            title = m.group(1).strip() if m else main.stem
        link = f"[{main.relative_to(d).as_posix()}](../{d.name}/{main.relative_to(d).as_posix()})" if main else ""
        lines.append(f"- `reports/{d.name}/` (before v1.5): {title} {link}".rstrip())
    return "\n".join(lines)


def need(cond, message):
    if not cond:
        raise SystemExit(f"STOP: the report's message no longer holds: {message}")


# ---------------------------------------------------------------- values

def values():
    F, B = load(RES / "results_final.json"), load(RES / "results_b2.json")
    A, FM, NB = load(RES / "ablations.json"), load(RES / "failure_modes.json"), load(RES / "b14_no_results.json")
    adopt, agree = load(S / "adoption_b12.json"), load(RES / "labels/agreement_ours/agreement.json")
    excl, cut = load(ROOT / "configs/study_v1_5/headline_exclusions.json"), load(RES / "b3_cutoff.json")
    h, hb2 = F["scopes"][HL], B["scopes"][HL]
    fr, frb = h["policies"]["frozen"], hb2["policies"]["frozen"]
    P, Pb = fr["pooled"], frb["pooled"]
    V = {}
    V["commit"] = git("rev-parse", "--short=12", "HEAD")
    V["tag_v15_commit"] = F["frozen"]["tag_commit"][:12]
    for tag, key in (("study-v1.5-prereg", "tag_prereg"), ("study-v4-frozen", "tag_v4"), ("v1.5-frozen", "tag_v15a"),
                     ("v1.5-frozen-2", "tag_v15"), ("study-analysis-frozen", "tag_analysis")):
        V[key] = git("rev-parse", "--short=12", f"{tag}^{{commit}}")

    # headline
    bs = fr["bootstrap"]
    V.update(n=str(P["n"]), prec=ci(P["accept_precision"]), prec_kn=kn(P["accept_precision"]), base=ci(P["base_rate"]),
             cov=ci(P["coverage"]), far=ci(P["false_accept_rate"]), far_kn=kn(P["false_accept_rate"]),
             lift=num(P["lift"]), lift_w=num(P["lift_accept_weighted"]), fisher=pval(P["fisher_p"]),
             wrong_rej=ci(P["wrong_rejected"]), corr_rej=ci(P["correct_rejected"]), flag=ci(P["flag_rate"]),
             h1h2=htext(bs), boot_tasks=str(bs["tasks"]), boot_used=str(bs["resamples_used"]),
             h1_ci=f"[{pct(bs['h1_ci'][0])}, {pct(bs['h1_ci'][1])}]", h2_ci=f"[{pct(bs['h2_ci'][0])}, {pct(bs['h2_ci'][1])}]",
             h1_word="supported" if bs["h1_supported"] else "not supported",
             h2_word="supported" if bs["h2_supported"] else "not supported")
    V["prec_value"], V["base_value"] = pct(P["accept_precision"]["value"]), pct(P["base_rate"]["value"])
    h3, h3h = h["h3"]["all"], h["h3"]["headline_scope"]
    V["h3"] = (f"{h3['rejects']} of {h3['gold_patches']} test-set gold patches REJECTed ({pct(h3['point'])}, Wilson 95% upper "
               f"bound {pct(h3['wilson_upper'])}: {', '.join(h3['reject_ids']) or 'none'}); in the headline scope "
               f"{h3h['rejects']} of {h3h['gold_patches']} ({pct(h3h['point'])}, upper {pct(h3h['wilson_upper'])})")
    V["h3_short"] = f"{h3['rejects']} of {h3['gold_patches']} gold REJECTed, Wilson upper bound {pct(h3['wilson_upper'])}"
    V["table_headline"] = full_table(fr)
    bsb = frb["bootstrap"]
    V.update(b2_n=str(Pb["n"]), b2_prec=ci(Pb["accept_precision"]), b2_base=ci(Pb["base_rate"]), b2_far=ci(Pb["false_accept_rate"]),
             b2_cov=ci(Pb["coverage"]), b2_h1h2=htext(bsb), table_b2=full_table(frb))
    h3b = hb2["h3"]["all"]
    V["b2_h3"] = f"{h3b['rejects']} of {h3b['gold_patches']} batch 2 gold patches REJECTed (Wilson upper {pct(h3b['wilson_upper'])})"
    need(bs["h1_supported"] and bs["h2_supported"] and bsb["h1_supported"] and bsb["h2_supported"],
         "H1 and H2 hold on the headline and on batch 2 alone")

    # RQ1
    r1 = ["| system | patches in scope | empty | non-empty labelled | resolved | base rate (correct ÷ labelled non-empty) |",
          "|---|---:|---:|---:|---:|---|"]
    for s in SYSTEMS:
        q, m = h["rq1"][s], fr["per_system"][s]
        r1.append(f"| {NAMES[s]} | {q['patches']} | {q['empty']} | {q['non_empty_labelled']} | {q['resolved']} | {ci(m['base_rate'])} |")
    V["table_rq1"] = "\n".join(r1)
    need(fr["per_system"]["claude-sonnet-4"]["base_rate"]["value"] > 0.5 > fr["per_system"]["gpt-4.1-mini"]["base_rate"]["value"],
         "Claude is right on most of its patches, gpt-4.1-mini on a minority")
    need(all(fr["per_system"][s]["accept_precision"]["value"] > fr["per_system"][s]["base_rate"]["value"] for s in SYSTEMS),
         "every system's ACCEPT precision is above its base rate")
    halves, allc = results_100()
    V["earlier_half_a"] = f"{halves['A'][0]}/{halves['A'][1]} ({pct(halves['A'][0] / halves['A'][1])})"
    V["earlier_half_b"] = f"{halves['B'][0]}/{halves['B'][1]} ({pct(halves['B'][0] / halves['B'][1])})"
    V["earlier_all"] = f"{allc[0]}/{allc[1]} ({pct(allc[0] / allc[1])})"
    lab = adopt["gates"]["labels"]
    V["armb_correct"], V["armb_wrong"] = str(lab["correct"]), str(lab["wrong"])
    V["armb_n"] = str(lab["correct"] + lab["wrong"])

    # RQ2 extras
    w = h["within_task"]
    V["within"] = (f"{w['tasks']} tasks where systems disagree on correctness ({w['patches']} patches): ACCEPT rate on correct "
                   f"patches {ci(w['accept_correct'])} against {ci(w['accept_wrong'])} on wrong ones; of the correct/wrong "
                   f"pairs within a task, {w['pairs']['concordant']} favour the correct patch, {w['pairs']['discordant']} the "
                   f"wrong one and {w['pairs']['ties']} are ties")
    v = h["v4_correct_vs_gold"]
    V["v4gold"] = (f"V4 fully passes {ci(v['public_full_pass'])} of the {v['correct_public_patches']} correct public patches, "
                   f"against {ci(v['gold_full_pass_same_tasks'])} for the gold patch of the same task")
    need(abs(v["public_full_pass"]["value"] - v["gold_full_pass_same_tasks"]["value"]) < 0.05,
         "V4 treats correct agent patches about as it treats gold")
    sens = [srow("headline (v1.5 frozen)", P, bs)]
    for scope, label in ((ALL, "all tasks (no exclusions)"), (NR, "minus tasks with generator recall")):
        b = F["scopes"][scope]["policies"]["frozen"]
        sens.append(srow(label, b["pooled"], b["bootstrap"]))
    gp, es = FM["git_peek"], FM["empty_patch_sensitivity"]
    sens.append(srow("minus git_peek pairs", gp["block"]["pooled"], gp["block"]["bootstrap"]))
    sens.append(srow("empty patches counted as wrong, REJECT", es["block"]["pooled"], es["block"]["bootstrap"]))
    V["table_sens"] = "\n".join([SHORT, *sens])
    V["gp_removed"] = str(gp["pairs_removed"])
    V["gp_files"] = "; ".join(f"{NAMES[s]} {f['listed']} listed, {len(f['scored_in_headline'])} scored in the headline"
                              for s, f in gp["files"].items() if f.get("file"))
    V["empty_counts"] = ", ".join(f"{NAMES[s]} {n}" for s, n in es["empty_counts"].items())
    labels_per = {s: h["rq1"][s]["non_empty_labelled"] for s in SYSTEMS}

    # RQ3
    dr, v1v2 = A["signal_dropouts"], h["policies"]["v1v2"]
    rows3 = [srow("v1.5 frozen", P, bs)]
    for sig in ("V1", "V2", "V3", "V4"):
        rows3.append(srow(f"{sig} forced to PASS", dr[sig]["pooled"], dr[sig]["bootstrap"]))
    rows3.append(srow("V1+V2 only (Phase 15 baseline)", v1v2["pooled"], v1v2["bootstrap"]))
    fb = A["v2_fallback"]
    rows3.append(srow("without the V2 fallback", fb["pooled"], fb["bootstrap"]))
    V["table_ablations"] = "\n".join([SHORT, *rows3])
    farv = lambda m: m["false_accept_rate"]["value"]  # noqa: E731
    covv = lambda m: m["coverage"]["value"]  # noqa: E731
    r_v4, r_v2 = farv(dr["V4"]["pooled"]) / farv(P), farv(dr["V2"]["pooled"]) / farv(P)
    need(2.5 <= r_v4 <= 3.6 and 2.5 <= r_v2 <= 3.6, "forcing V4 or V2 to PASS roughly triples false accepts")
    V.update(v4_far=pct(farv(dr["V4"]["pooled"])), v2_far=pct(farv(dr["V2"]["pooled"])), far_value=pct(farv(P)),
             v4_ratio=num(r_v4, 1), v2_ratio=num(r_v2, 1),
             v4_prec=pct(dr["V4"]["pooled"]["accept_precision"]["value"]),
             v2_prec=pct(dr["V2"]["pooled"]["accept_precision"]["value"]))
    d3c, d3f = covv(dr["V3"]["pooled"]) - covv(P), farv(dr["V3"]["pooled"]) - farv(P)
    need(abs(d3f) < 0.01 and abs(d3c) < 0.05, "V3 adds nothing measurable")
    d3a = (dr["V3"]["pooled"]["decisions"]["ACCEPT_correct"] + dr["V3"]["pooled"]["decisions"]["ACCEPT_wrong"]
           - P["decisions"]["ACCEPT_correct"] - P["decisions"]["ACCEPT_wrong"])
    need(abs(d3a) <= 5, "V3 moves few patches into or out of ACCEPT")
    V.update(v3_cov_delta=pp(d3c), v3_far_delta=pp(d3f), v3_changed=str(dr["V3"]["changed"]), v3_acc_delta=f"{d3a:+d}")
    d1c, d1f = covv(dr["V1"]["pooled"]) - covv(P), farv(dr["V1"]["pooled"]) - farv(P)
    need(d1c >= 0.1 and d1f <= 0.03 and d1c == max(covv(dr[s]["pooled"]) - covv(P) for s in dr),
         "V1 is the costliest signal: largest coverage gain for a small false-accept cost")
    V.update(v1_cov=pct(covv(dr["V1"]["pooled"])), v1_cov_delta=pp(d1c), v1_far=pct(farv(dr["V1"]["pooled"])), v1_far_delta=pp(d1f),
             cov_value=pct(covv(P)),
             v1_extra_c=str(dr["V1"]["pooled"]["decisions"]["ACCEPT_correct"] - P["decisions"]["ACCEPT_correct"]),
             v1_extra_w=str(dr["V1"]["pooled"]["decisions"]["ACCEPT_wrong"] - P["decisions"]["ACCEPT_wrong"]))
    r12 = farv(v1v2["pooled"]) / farv(P)
    need(v1v2["bootstrap"]["h1_supported"] and 1.6 <= r12 <= 2.4, "V1+V2 alone beats the base rate with about twice the false-accept rate")
    V.update(v1v2_prec=ci(v1v2["pooled"]["accept_precision"]), v1v2_far=pct(farv(v1v2["pooled"])), v1v2_ratio=num(r12, 1))
    need(not fb["fallback_removed"] and not fb["v2_outcome_changed"], "the V2 fallback was never used on the test set")
    V["fb_used"] = str(len(fb["fallback_removed"]))
    o = A["old_vs_new_v4"]
    V["table_armb"] = "\n".join([SHORT, srow("v1.5 frozen switches, new V4", o["frozen_new_v4"]["pooled"], o["frozen_new_v4"]["bootstrap"]),
                                 srow("switches off, old (legacy) V4", o["off_old_v4"]["pooled"], o["off_old_v4"]["bootstrap"]),
                                 srow("switches off, new (per-requirement) V4", o["off_new_v4"]["pooled"], o["off_new_v4"]["bootstrap"])])
    on, oo = o["off_new_v4"]["pooled"], o["off_old_v4"]["pooled"]
    need(on["decisions"]["ACCEPT_correct"] < oo["decisions"]["ACCEPT_correct"]
         and on["accept_precision"]["value"] >= oo["accept_precision"]["value"], "new V4 trades coverage for precision on arm B")
    V.update(armb_new_prec=ci(on["accept_precision"]), armb_old_prec=ci(oo["accept_precision"]),
             armb_new_acc=str(on["decisions"]["ACCEPT_correct"]), armb_old_acc=str(oo["decisions"]["ACCEPT_correct"]),
             armb_changed=str(len(o["changed_old_to_new"])),
             armb_cross="equal" if all(o["crosscheck_adoption_b12"].values()) else "NOT equal")

    # RQ4
    v141 = h["policies"]["v141"]
    t4 = ["| system | v1.4.1 coverage | v1.5 coverage | v1.4.1 false-accept | v1.5 false-accept | v1.4.1 ACCEPT c/w | v1.5 ACCEPT c/w | correct held back (v1.5) |",
          "|---|---|---|---|---|---|---|---|"]
    for s in [*SYSTEMS, "pooled"]:
        a = v141["pooled"] if s == "pooled" else v141["per_system"][s]
        b = P if s == "pooled" else fr["per_system"][s]
        t4.append(f"| {NAMES.get(s, '**pooled**')} | {ci(a['coverage'])} | {ci(b['coverage'])} | {ci(a['false_accept_rate'])} | "
                  f"{ci(b['false_accept_rate'])} | {a['decisions']['ACCEPT_correct']}/{a['decisions']['ACCEPT_wrong']} | "
                  f"{b['decisions']['ACCEPT_correct']}/{b['decisions']['ACCEPT_wrong']} | {ci(b['held_back_correct'])} |")
    V["table_v141"] = "\n".join(t4)
    V.update(v141_cov=pct(covv(v141["pooled"])), v141_far=pct(farv(v141["pooled"])),
             cov_gain=pp(covv(P) - covv(v141["pooled"])),
             extra_correct=str(P["decisions"]["ACCEPT_correct"] - v141["pooled"]["decisions"]["ACCEPT_correct"]),
             extra_wrong=str(P["decisions"]["ACCEPT_wrong"] - v141["pooled"]["decisions"]["ACCEPT_wrong"]),
             v141_prec=ci(v141["pooled"]["accept_precision"]))
    acc = A["v2_accountings"]["accountings"]
    rows_acc = [srow("v1.5 frozen (P_invalid_excluded)", P, bs)]
    for name in ("S_invalid_excluded", "S_invalid_missing", "C_invalid_excluded", "C_invalid_missing", "P_invalid_missing"):
        rows_acc.append(srow(name, acc[name]["pooled"], acc[name]["bootstrap"]))
    V["table_acc"] = "\n".join([SHORT, *rows_acc])
    maxchg = max(b["changed_vs_frozen"] for b in acc.values())
    need(maxchg <= 5 and all(abs(farv(b["pooled"]) - farv(P)) < 0.01 for b in acc.values()), "S/C/P make no material difference")
    V["acc_max_changed"] = str(maxchg)
    V["acc_s_changes"] = "; ".join(acc["S_invalid_excluded"]["changed_tasks"]) or "none"
    V["acc_replayed"] = str(sum(A["v2_accountings"]["stored_primary"].values()))
    # S1-S3
    t5 = ["| scope | variant | n | ACCEPT precision [95% CI] | coverage | false-accept rate | wrong ACCEPTs per system |",
          "|---|---|---:|---|---|---|---|"]
    for scope_name, hh in (("batch 1 + 2 (headline)", h), ("batch 2 alone (held out)", hb2)):
        for pol, label in (("frozen", "v1.5 frozen"), ("s1", "S1 risk flags informational"),
                           ("s2", "S2 V1 manipulation findings informational"), ("s3", "S3 = S1 and S2")):
            bb = hh["policies"][pol]
            m = bb["pooled"]
            wa = ", ".join(f"{NAMES[s]} {bb['per_system'][s]['decisions']['ACCEPT_wrong']}" for s in SYSTEMS)
            t5.append(f"| {scope_name} | {label} | {m['n']} | {ci(m['accept_precision'])} | {ci(m['coverage'])} | "
                      f"{ci(m['false_accept_rate'])} | {wa} |")
    V["table_s"] = "\n".join(t5)
    bp = hb2["policies"]
    need(covv(bp["s1"]["pooled"]) > covv(Pb) and covv(bp["s3"]["pooled"]) > covv(Pb), "S1/S3 coverage gains carry over to batch 2")
    need(bp["s1"]["pooled"]["accept_precision"]["value"] <= Pb["accept_precision"]["value"]
         and bp["s3"]["pooled"]["accept_precision"]["value"] <= Pb["accept_precision"]["value"],
         "the S1/S3 precision gain does not carry over to batch 2")

    def extra_wrong(hh, s):
        return hh["policies"]["s1"]["per_system"][s]["decisions"]["ACCEPT_wrong"] - hh["policies"]["frozen"]["per_system"][s]["decisions"]["ACCEPT_wrong"]
    for hh in (h, hb2):
        tot = sum(extra_wrong(hh, s) for s in SYSTEMS)
        need(tot > 0 and extra_wrong(hh, "claude-sonnet-4") * 2 > tot, "S1's extra risk is mostly Claude's")
    V.update(b2_s1_cov=pct(covv(bp["s1"]["pooled"])), b2_s3_cov=pct(covv(bp["s3"]["pooled"])), b2_cov_value=pct(covv(Pb)),
             b2_s1_prec=pct(bp["s1"]["pooled"]["accept_precision"]["value"]), b2_prec_value=pct(Pb["accept_precision"]["value"]),
             s1_prec=pct(h["policies"]["s1"]["pooled"]["accept_precision"]["value"]),
             s1_extra_claude=str(extra_wrong(h, "claude-sonnet-4")), s1_extra_all=str(sum(extra_wrong(h, s) for s in SYSTEMS)),
             b2_s1_extra_claude=str(extra_wrong(hb2, "claude-sonnet-4")), b2_s1_extra_all=str(sum(extra_wrong(hb2, s) for s in SYSTEMS)))
    # gold ceiling
    g = A["gold"]
    gc = g["cause_counts"]
    r8 = sum(n for c, n in gc.items() if c.startswith("verifier fault (R8") and "NOT_AVAILABLE" in c)
    v4w = gc.get("verifier fault (V4 test asserts the wrong thing)", 0)
    sup, irr = gc.get("superseded assertion", 0), gc.get("issue not reproducible as a test", 0)
    other = sum(gc.values()) - r8 - v4w - sup - irr
    need(other == 0, "every gold FLAG/REJECT falls in the four causes the message names")
    n = g["gold_patches"]
    tg = ["| cause of a gold FLAG or REJECT (first matching rule) | count | share of all gold patches |", "|---|---:|---|"]
    for label, k in (("superseded assertion (V2 FAIL on a test the task's test_patch changes)", sup),
                     ("issue not reproducible as a test (V4 uncovered, no result, or none)", irr),
                     ("verifier fault: V4 test asserts the wrong thing (R4)", v4w),
                     ("verifier fault: V2 produced no result (R8)", r8)):
        tg.append(f"| {label} | {k} | {pct(k / n)} |")
    for c, k in g["second_cause_counts"].items():
        tg.append(f"| also: {c} (second cause) | {k} | {pct(k / n)} |")
    V["table_gold"] = "\n".join(tg)
    gcsv = gold_csv()
    V.update(gold_n=str(n), gold_acc=f"{kn(g['accepted'])} = {ci(g['accepted'])}", gold_flag=str(g["flag"]), gold_reject=str(g["reject"]),
             gold_limit=pct((sup + irr) / n), gold_fixable=pct((v4w + r8) / n),
             gold_limit_k=str(sup + irr), gold_fixable_k=str(v4w + r8),
             gold_sup_confirmed=str(sum(bool(p["confirmed"]) for p in g["per_task"] if p["cause"] == "superseded assertion")),
             gold_sup=str(sup),
             gold_b1=", ".join(f"{d} {gcsv['b1'][d]}" for d in ("ACCEPT", "FLAG", "REJECT")),
             gold_b2=", ".join(f"{d} {gcsv['b2'][d]}" for d in ("ACCEPT", "FLAG", "REJECT")))

    # RQ5
    fa = FM["false_accepts"]
    tf = ["| system | task | rule | V2 | V4 pass / uncovered | type | FAIL_TO_PASS failed | PASS_TO_PASS failed |",
          "|---|---|---|---|---|---|---|---|"]
    short = lambda xs: "—" if not xs else ", ".join(f"`{x}`" for x in xs[:3]) + (f" and {len(xs) - 3} more" if len(xs) > 3 else "")  # noqa: E731
    for f in fa:
        tf.append(f"| {NAMES[f['system']]} | {f['instance_id']} | {f['rule']} | {f['v2']} | {f['v4_pass_units']} / "
                  f"{f['v4_uncovered_units']} | {f['wrong_type']} | {short(f['fail_to_pass_failed'])} | {short(f['pass_to_pass_failed'])} |")
    V["table_fa"] = "\n".join(tf)
    def why(text):
        text = text.replace("V2 had nothing to check (no test selected), none of them a PASS_TO_PASS test the grader saw fail "
                            "(matched by test name)", "V2 had nothing to check (no test selected), so no PASS_TO_PASS test ran")
        return text.replace("requirement(s)", "requirements").replace("passed 1 requirements", "passed 1 requirement")
    V["fa_why"] = "\n".join(f"- {NAMES[f['system']]} {f['instance_id']}: {why(f['why_missed'])}." for f in fa)
    V["fa_n"] = str(len(fa))
    repos_fa = Counter(f["repo"] for f in fa)
    V["fa_repos"] = ", ".join(f"{r} {k}" for r, k in repos_fa.most_common())
    V["fa_rules"] = ", ".join(f"{r} {k}" for r, k in sorted(Counter(f["rule"] for f in fa).items()))
    wt = FM["wrong_type_by_decision"]
    tw = ["| scope | type | ACCEPT | FLAG | REJECT |", "|---|---|---:|---:|---:|"]
    for name, tbl in [("pooled", wt["pooled"]), *[(NAMES[s], wt["per_system"][s]) for s in SYSTEMS]]:
        for t, d in tbl.items():
            tw.append(f"| {name} | {t} | {d['ACCEPT']} | {d['FLAG']} | {d['REJECT']} |")
    V["table_wt"] = "\n".join(tw)
    V["wt_unknown_apply"] = str(len(wt["unknown_grader_could_not_apply"]))
    pr = FM["per_repository"]
    trr = ["| repository | ACCEPT correct/wrong | FLAG correct/wrong | REJECT correct/wrong |", "|---|---|---|---|"]
    for repo, d in pr.items():
        trr.append(f"| {repo} | {d['ACCEPT_correct']}/{d['ACCEPT_wrong']} | {d['FLAG_correct']}/{d['FLAG_wrong']} | "
                   f"{d['REJECT_correct']}/{d['REJECT_wrong']} |")
    V["table_repo"] = "\n".join(trr)
    V["n_repos"] = str(len(pr))
    test_ids = set()
    for b in ("b1", "b2"):
        f = next((S / f"test_gold_{b}/decisions_frozen").glob("decisions_*.csv"))
        test_ids |= {r["instance_id"] for r in csv.DictReader(f.open(encoding="utf-8"))}
    V["n_repos_test"] = str(len({i.split("__")[0] for i in test_ids}))
    ra = FM["v4_generator_audit"]
    V["recall_b1"] = f"{ra['b1']['tasks_with_recall']} of {ra['b1']['tasks']}"
    V["recall_b2"] = f"{ra['b2']['tasks_with_recall']} of {ra['b2']['tasks']}"
    nr = F["scopes"][NR]["policies"]["frozen"]
    V["nr_prec"], V["nr_n"] = ci(nr["pooled"]["accept_precision"]), str(nr["pooled"]["n"])
    need(abs(nr["pooled"]["accept_precision"]["value"] - P["accept_precision"]["value"]) < 0.05 and nr["bootstrap"]["h1_supported"],
         "generator recall does not drive the headline")

    # threats, labels, exclusions, data
    lp = F["label_problems"]
    V["gem_no_label"] = str(len(lp["gemini-2.5-flash"]["no_label"]))
    V["sha_mismatch"] = ", ".join(f"{NAMES[s]} {len(lp[s]['patch_sha256_mismatch'])}" for s in SYSTEMS)
    V["gem_accepts"] = str(fr["per_system"]["gemini-2.5-flash"]["decisions"]["ACCEPT_correct"]
                           + fr["per_system"]["gemini-2.5-flash"]["decisions"]["ACCEPT_wrong"])
    V["gem_prec"] = ci(fr["per_system"]["gemini-2.5-flash"]["accept_precision"])
    V["labelled"] = ", ".join(f"{NAMES[s]} {labels_per[s]}" for s in SYSTEMS)
    V.update(agree_pairs=str(agree["pairs"]), agree_comp=str(agree["comparable"]), agree_ok=str(agree["agree"]),
             agree_gpt_none=str(agree["per_system"].get("gpt-4.1-mini", {}).get("no_official_label", 0)))
    sm = NB["summary"]
    V.update(b14_pairs=str(sm["pairs"]), b14_ok=str(sm["applied_both_markers_no_bad_code"]),
             b14_both_fail=str(sm["apply_failed_on_both_sides"]), b14_named=str(sm["applied_with_any_named_exception"]),
             b14_exc=", ".join(f"{k} {v}" for k, v in sm["exception_types_in_applied"].items() if v),
             b14_cmds=", ".join(f"`{k}` {v}" for k, v in sm["apply_commands"].items()),
             b14_dec=", ".join(f"{k} {v}" for k, v in sm["frozen_decisions"].items()),
             b14_r1=", ".join(sm["r1_applied_on_both_sides"]) or "none")
    cnt = excl["counts"]
    b2ids = [r for r in excl["excluded"] if "system" not in r and not r.get("amendment")]
    b11 = [r for r in excl["excluded"] if "system" not in r and str(r.get("amendment", "")).startswith("B11")]
    V.update(ex_b2=str(len(b2ids)), ex_b11=", ".join(r["instance_id"] for r in b11), ex_pairs=str(cnt["pairs_total"]),
             ex_pairs_b1=str(cnt["pairs_batch1"]), ex_pairs_b2=str(cnt["pairs_batch2"]))
    V["b3"] = "; ".join(f"{NAMES[s]} sealed and reported {d['report_commit_date'][:16].replace('T', ' ')}"
                        for s, d in cut["systems"].items())
    total, by_job = spend()
    V["spend_total"] = f"${total:.2f}"
    V["spend_runs"] = ", ".join(f"`{j}` ${c:.2f}" for j, c in by_job.most_common())
    V["plan_500"] = plan_500()
    V["phase_table"] = phase_table()
    V["earlier_work"] = earlier_work()
    V["g1"] = "pass" if A["g1"]["pass"] else "FAIL"

    # figures and README block
    V["fig1"], V["fig2"] = "figures/fig1_precision_vs_base.svg", "figures/fig2_ablations.svg"
    V["readme_block"] = readme_block(V, fr, P)
    return V, fr, P, dr, v1v2, fb


def readme_block(V, fr, P):
    t = ["| | n | base rate | ACCEPT precision [95% CI] | coverage | false-accept rate |", "|---|---:|---|---|---|---|"]
    for s in SYSTEMS:
        m = fr["per_system"][s]
        t.append(f"| {NAMES[s]} | {m['n']} | {ci(m['base_rate'])} | {ci(m['accept_precision'])} | {ci(m['coverage'])} | {ci(m['false_accept_rate'])} |")
    t.append(f"| **pooled** | {P['n']} | {ci(P['base_rate'])} | {ci(P['accept_precision'])} | {ci(P['coverage'])} | {ci(P['false_accept_rate'])} |")
    return "\n".join([
        "*Generated by `scripts/build_report_v1_5.py` from `reports/study_v1_5/results/`; do not edit by hand.*", "",
        "Headline (test set, batches 1 and 2, v1.5 frozen):", "", *t, "",
        f"1. **An ACCEPT is worth believing.** Pooled ACCEPT precision is {V['prec']} against a base rate of {V['base']}; "
        f"the task-clustered bootstrap supports H1 and H2, and batch 2 alone replicates it ({V['b2_prec']} against {V['b2_base']}).",
        f"2. **V2 and V4 carry the verifier.** Forcing V4 or V2 to PASS raises the false-accept rate from {V['far_value']} to "
        f"{V['v4_far']} and {V['v2_far']}; V3 adds nothing measurable, and V1 costs the most coverage.",
        f"3. **The gold ceiling.** The verifier ACCEPTs {V['gold_acc']} of gold patches. {V['gold_limit']} of all gold patches are "
        f"held back for reasons oracle-blind verification cannot fix; {V['gold_fixable']} by fixable verifier weaknesses.",
        "", "Full report: [reports/study_v1_5/REPORT.md](reports/study_v1_5/REPORT.md)."])


def build(report_out=S / "REPORT.md", readme=ROOT / "README.md", figures=S / "figures"):
    V, fr, P, dr, v1v2, fb = values()
    template = re.sub(r"\A<!--.*?-->\n", "", (S / "report_template.md").read_text(encoding="utf-8"), flags=re.S)
    Path(report_out).write_text(render(template, V), encoding="utf-8")
    Path(readme).write_text(fill_block(Path(readme).read_text(encoding="utf-8"), V["readme_block"]), encoding="utf-8")
    figures = Path(figures)
    figures.mkdir(parents=True, exist_ok=True)
    pts = []
    for s in [*SYSTEMS, "pooled"]:
        m = P if s == "pooled" else fr["per_system"][s]
        pts.append((NAMES.get(s, "pooled"), m["base_rate"]["value"], tuple(m["base_rate"]["ci"]),
                    m["accept_precision"]["value"], tuple(m["accept_precision"]["ci"])))
    (figures / "fig1_precision_vs_base.svg").write_text(
        svg_points(pts, "Figure 1. Base rate vs ACCEPT precision (test set, v1.5 frozen)"), encoding="utf-8")
    bars = [("v1.5 frozen", P["accept_precision"]["value"], P["false_accept_rate"]["value"])]
    for sig in ("V1", "V2", "V3", "V4"):
        m = dr[sig]["pooled"]
        bars.append((f"{sig} forced to PASS", m["accept_precision"]["value"], m["false_accept_rate"]["value"]))
    bars.append(("V1+V2 only", v1v2["pooled"]["accept_precision"]["value"], v1v2["pooled"]["false_accept_rate"]["value"]))
    bars.append(("without V2 fallback", fb["pooled"]["accept_precision"]["value"], fb["pooled"]["false_accept_rate"]["value"]))
    (figures / "fig2_ablations.svg").write_text(svg_bars(bars, "Figure 2. Ablations: pooled precision and false-accept rate"),
                                                encoding="utf-8")
    return V


def main():
    build()
    print(f"wrote {S / 'REPORT.md'}, README.md results block, {S / 'figures'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
