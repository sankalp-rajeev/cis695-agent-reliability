"""POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold
patch, test_patch). Must never feed back into any run, policy, or config.

Collects issue text, agent patch, gold patch/test_patch, oracle failing tests,
verifier signals, V4 frozen tests, and V2/P2P overlap for the 19 study tasks.
Writes reports/failure_analysis/extracted.json. Does not modify run directories.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from reliability.analysis.overlap import names_match, overlap
from reliability.benchmark.loader import load_instance

NOTICE = (
    "POST-HOC ANALYSIS ONLY. This file uses oracle fields (FAIL_TO_PASS, "
    "PASS_TO_PASS, gold patch, test_patch). It must never feed back into any "
    "run, policy, manifest, or config."
)

TASKS = [
    ("group1_false_accept", "django__django-13212", "main_50_a"),
    ("group1_false_accept", "django__django-16667", "main_50_a"),
    ("group1_false_accept", "pylint-dev__pylint-7277", "main_50_a"),
    ("group1_false_accept", "django__django-13297", "main_50_b"),
    ("group1_false_accept", "matplotlib__matplotlib-23299", "main_50_b"),
    ("group1_false_accept", "matplotlib__matplotlib-23476", "main_50_b"),
    ("group1_false_accept", "pylint-dev__pylint-4661", "main_50_b"),
    ("group2_false_flag", "matplotlib__matplotlib-20676", "main_2_rerun_mpl"),
    ("group2_false_flag", "pylint-dev__pylint-6528", "main_50_a"),
    ("group2_false_flag", "astropy__astropy-13977", "main_50_b"),
    ("group2_false_flag", "django__django-16631", "main_50_b"),
    ("group2_false_flag", "mwaskom__seaborn-3069", "main_50_b"),
    ("group2_false_flag", "sympy__sympy-17318", "main_3_rerun_infra"),
    ("group3_false_reject", "matplotlib__matplotlib-25479", "main_50_b"),
    ("group4_right_old_tests_fail", "django__django-12209", "main_50_b"),
    ("group4_right_old_tests_fail", "django__django-14140", "main_50_b"),
    ("group4_right_old_tests_fail", "django__django-14631", "main_50_b"),
    ("group4_right_old_tests_fail", "pytest-dev__pytest-5809", "main_50_a"),
    ("group4_right_old_tests_fail", "sphinx-doc__sphinx-10435", "main_50_b"),
]

CSV_PATH = REPO / "docs" / "results_100.csv"
OUT = Path(__file__).resolve().parent / "extracted.json"
JSONL_CANDIDATES = [
    REPO / "local_swebench_verified.jsonl",
    REPO / "data" / "local_swebench_verified.jsonl",
    Path.home() / "local_swebench_verified.jsonl",
    Path.home() / "datasets" / "local_swebench_verified.jsonl",
]


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_row(instance_id: str) -> dict | None:
    with CSV_PATH.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["instance_id"] == instance_id:
                return row
    return None


def _v4_sources(run: str, instance_id: str) -> dict[str, str]:
    cache = REPO / "runs" / run / "_reproduction_cache" / instance_id / "tests"
    found: dict[str, str] = {}
    if not cache.is_dir():
        return found
    for path in sorted(cache.glob("test_repro_*.py")):
        found[path.name] = path.read_text(encoding="utf-8", errors="replace")
    return found


def _failing_oracle(ora: dict) -> dict:
    f2p = (ora.get("fail_to_pass") or {})
    p2p = (ora.get("pass_to_pass") or {})
    return {
        "f2p_failure": list(f2p.get("failure") or ()),
        "f2p_success": list(f2p.get("success") or ()),
        "p2p_failure": list(p2p.get("failure") or ()),
        "p2p_success": list(p2p.get("success") or ()),
    }


def _overlap_failing(selected: list[str], failing: list[str]) -> list[str]:
    return [t for t in failing if any(names_match(s, t) for s in selected)]


def collect_one(group: str, instance_id: str, run: str) -> dict:
    task_dir = REPO / "runs" / run / "tasks" / instance_id
    csv_row = _csv_row(instance_id)
    missing: list[str] = []
    for name in ("patch.diff", "oracle_record.json", "verification_record.full.json"):
        if not (task_dir / name).is_file():
            missing.append(str(task_dir / name))

    ora = _read_json(task_dir / "oracle_record.json") or {}
    ver = _read_json(task_dir / "verification_record.full.json") or {}
    patch_path = task_dir / "patch.diff"
    agent_patch = (
        patch_path.read_text(encoding="utf-8", errors="replace")
        if patch_path.is_file() else ""
    )

    disagreements: list[str] = []
    if csv_row:
        mapped = {
            "verifier_decision": ver.get("decision", {}).get("decision"),
            "oracle": ora.get("outcome"),
            "integrity": (ver.get("integrity") or {}).get("outcome"),
            "regression": (ver.get("regression") or {}).get("outcome"),
            "static": (ver.get("static") or {}).get("outcome"),
            "reproduction": (ver.get("reproduction") or {}).get("outcome"),
            "source_run": run,
        }
        for key in ("verifier_decision", "oracle", "integrity", "regression",
                    "static", "reproduction"):
            csv_val = csv_row.get(key)
            rec_val = mapped.get(key)
            if csv_val and rec_val and csv_val != rec_val:
                disagreements.append(
                    f"{key}: csv={csv_val!r} record={rec_val!r}"
                )
        if csv_row.get("source_run") != run:
            disagreements.append(
                f"source_run: csv={csv_row.get('source_run')!r} used={run!r}"
            )

    agent, gold = load_instance(instance_id)
    selected = list(ver.get("selected_tests") or ())
    failing = _failing_oracle(ora)
    all_failing = failing["f2p_failure"] + failing["p2p_failure"]
    p2p_official = list(gold.pass_to_pass)
    f2p_official = list(gold.fail_to_pass)
    ov = overlap(tuple(selected), tuple(p2p_official))

    repro = ver.get("reproduction") or {}
    findings = repro.get("findings") or {}
    frozen = findings.get("frozen") or []
    patched_v4 = findings.get("patched") or []
    v4_src = _v4_sources(run, instance_id)

    report_file = ora.get("report_file") or ""
    report = None
    if report_file:
        rpath = Path(report_file)
        if rpath.is_file():
            report = json.loads(rpath.read_text(encoding="utf-8"))
        else:
            missing.append(report_file)

    return {
        "group": group,
        "instance_id": instance_id,
        "source_run": run,
        "task_dir": str(task_dir),
        "missing_files": missing,
        "csv_disagreements": disagreements,
        "csv_row": csv_row,
        "problem_statement": agent.problem_statement,
        "agent_patch": agent_patch,
        "gold_patch": gold.patch,
        "gold_test_patch": gold.test_patch,
        "official_fail_to_pass": f2p_official,
        "official_pass_to_pass": p2p_official,
        "oracle_record": {
            "outcome": ora.get("outcome"),
            "resolved": ora.get("resolved"),
            "patch_applied": ora.get("patch_applied"),
            "report_file": report_file,
            "experiment_id": ora.get("experiment_id"),
            **failing,
        },
        "harness_report": report,
        "signals": {
            "decision": (ver.get("decision") or {}).get("decision"),
            "reasons": (ver.get("decision") or {}).get("reasons"),
            "policy_version": (ver.get("decision") or {}).get("policy_version"),
            "integrity": ver.get("integrity"),
            "regression": ver.get("regression"),
            "static": ver.get("static"),
            "reproduction": {
                "outcome": repro.get("outcome"),
                "absence": repro.get("absence"),
                "detail": repro.get("detail"),
                "generation": findings.get("generation"),
                "n_frozen": len(frozen),
                "frozen_meta": frozen,
                "patched": patched_v4,
            },
            "n_selected": len(selected),
            "selected_tests": selected,
            "selection_convention": ver.get("selection_convention"),
            "selection_runner": ver.get("selection_runner"),
            "risk_features": ver.get("risk_features"),
        },
        "v4_test_sources": v4_src,
        "coverage": {
            "n_selected": ov["n_selected"],
            "n_official_p2p": ov["n_pass_to_pass"],
            "n_overlap_p2p": ov["n_overlap_pass_to_pass"],
            "n_overlap_selected": ov["n_overlap_selected"],
            "fraction_of_p2p": ov["fraction_of_pass_to_pass"],
            "matched_selected": ov["matched_selected"],
            "failing_oracle_tests": all_failing,
            "failing_in_v2_selection": _overlap_failing(selected, all_failing),
            "failing_f2p_in_v2": _overlap_failing(selected, failing["f2p_failure"]),
            "failing_p2p_in_v2": _overlap_failing(selected, failing["p2p_failure"]),
        },
    }


def find_jsonl() -> str | None:
    for path in JSONL_CANDIDATES:
        if path.is_file():
            return str(path)
    return None


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for group, iid, run in TASKS:
        print(f"extract {iid} from {run}", flush=True)
        rows.append(collect_one(group, iid, run))

    extra_20676 = None
    orig = REPO / "runs" / "main_50_a" / "tasks" / "matplotlib__matplotlib-20676"
    if orig.is_dir():
        extra_20676 = collect_one(
            "group2_false_flag_ORIGINAL_LEAK_OPEN",
            "matplotlib__matplotlib-20676",
            "main_50_a",
        )

    payload = {
        "notice": NOTICE,
        "local_swebench_verified_jsonl": find_jsonl(),
        "dataset_source": (
            "HuggingFace SWE-bench/SWE-bench_Verified via "
            "reliability.benchmark.loader.load_instance; named file "
            "local_swebench_verified.jsonl was "
            + ("found at " + find_jsonl() if find_jsonl() else "NOT FOUND")
        ),
        "tasks": rows,
        "matplotlib_20676_original_leak_open": extra_20676,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
