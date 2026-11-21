#!/usr/bin/env python3
"""Recompute v1.5 decisions for every task of a sealed run from its stored evidence.

Offline and label-free: nothing is re-executed, and only the run's seal, header,
completion record and per-task verification records are opened. A run path
naming labels, grading or post-hoc material is refused before anything is
read; every file opened is checked by name too. Writes one CSV row per task
and a JSON summary for the chosen switches:

    scripts/decide_v1_5.py runs/study_dev_armB --switches r2=0,r3=0,r6=0 --output DIR
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from e2e_input_preflight import FORBIDDEN_NAMES  # noqa: E402

from reliability.verifier.decision import Decision  # noqa: E402
from reliability.verifier.policy_v1_5 import RULE_DECISIONS, FullPolicyV15, evidence_from_signals  # noqa: E402
from reliability.verifier.reproduction_reuse import RECORD  # noqa: E402
from reliability.verifier.run_v1_4_1 import VerificationRecordV141  # noqa: E402

#: CLAUDE.md names these too; "grading" does not contain "grade".
LABEL_WORDS = FORBIDDEN_NAMES + ("grading", "per_instance_details", "git_peek",
                                 "decision_by_correctness")
SWITCH_KEYS = {"r2": "r2_v3_reject", "r3": "r3_extended_reject", "r6": "r6_accept_v2_not_available"}
FIELDS = ("instance_id", "has_patch", "stored_decision", "stored_policy_version",
          "integrity", "v2", "v4", "v3_absolute_failure", "v1_analysis_incomplete",
          "high_severity_risk", "v4_design", "v4_full_pass", "v4_fail_confirmed",
          "v4_failing_units", "v4_pass_units", "decision", "rule_id", "review_label")


def parse_switches(text: str) -> dict[str, bool]:
    pairs = [item.split("=", 1) for item in text.split(",")]
    if any(len(pair) != 2 for pair in pairs):
        raise ValueError("--switches must look like r2=0,r3=0,r6=0")
    keys = [key for key, _ in pairs]
    if sorted(keys) != sorted(SWITCH_KEYS) or any(value not in ("0", "1") for _, value in pairs):
        raise ValueError("--switches needs r2, r3 and r6 exactly once, each 0 or 1")
    return {SWITCH_KEYS[key]: value == "1" for key, value in pairs}


def _label_words(path: Path) -> set[str]:
    text = path.as_posix().casefold()
    return {word for word in LABEL_WORDS if word in text}


def check_label_free(run: Path) -> None:
    """Refuse a label run path. A gold run's own folder may say "gold" only if
    its header records reference-patch mode, the one lift PROTOCOL §4.7 allows."""
    hits = _label_words(run)
    if hits - {"gold"}:
        raise ValueError(f"run path has a forbidden name: {sorted(hits)}")
    if hits:
        header = json.loads((run / "header.json").read_text(encoding="utf-8"))
        if header.get("reference_patches") is not True:
            raise ValueError("run path has a forbidden name (gold) and is not a reference-patch run")


def check_sealed(run: Path) -> tuple[dict[str, str], str]:
    seal = run / "seal.json"
    if not seal.is_file() or seal.is_symlink():
        raise ValueError("run has no seal.json; only sealed runs can be decided")
    raw = seal.read_bytes()
    data = json.loads(raw)
    files = data.get("files_sha256")
    if data.get("status") != "COMPLETE" or not isinstance(files, dict):
        raise ValueError("run seal is not COMPLETE")
    paths = list(run.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("sealed run contains a symlink")
    inventory = {path.relative_to(run).as_posix() for path in paths
                 if path.is_file() and path != seal}
    if inventory != files.keys():
        raise ValueError("run files do not match the seal inventory")
    return files, hashlib.sha256(raw).hexdigest()


def _read(run: Path, files: dict[str, str], name: str) -> bytes:
    hits = _label_words(Path(name))
    if hits:
        raise ValueError(f"refusing to open a forbidden path: {name}")
    if name not in files:
        raise ValueError(f"file is not in the run seal: {name}")
    raw = (run / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != files[name]:
        raise ValueError(f"file differs from the run seal: {name}")
    return raw


def tag(switches: dict[str, bool]) -> str:
    return "_".join(f"{key}-{int(switches[name])}" for key, name in SWITCH_KEYS.items())


def decide_run(run: Path, switches: dict[str, bool], output: Path) -> dict:
    run, output = Path(run).resolve(), Path(output).resolve()
    check_label_free(run)
    if output.is_relative_to(run):
        raise ValueError("output must not be inside the sealed run")
    files, seal_sha256 = check_sealed(run)
    completion = json.loads(_read(run, files, "completion.json"))
    if completion.get("status") != "COMPLETE":
        raise ValueError("run completion is not COMPLETE")
    no_patch = set(completion.get("no_patch_tasks", ()))
    policy = FullPolicyV15(**switches)
    rows = []
    for iid in completion["completed_tasks"]:
        name = f"tasks/{iid}/{RECORD}"
        record = VerificationRecordV141.model_validate_json(_read(run, files, name))
        if record.instance_id != iid:
            raise ValueError(f"record instance differs: {name}")
        evidence = evidence_from_signals(record.signals)
        result = policy.decide(evidence)
        rows.append({
            "instance_id": iid, "has_patch": iid not in no_patch,
            "stored_decision": record.decision.decision.value,
            "stored_policy_version": record.decision.policy_version,
            "integrity": evidence.integrity.value, "v2": evidence.regression.value,
            "v4": evidence.reproduction.value,
            **{k: getattr(evidence, k) for k in FIELDS[7:15]},
            "decision": result.decision.value, "rule_id": result.rule_id,
            "review_label": result.review_label,
        })
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / f"decisions_v1_5_{tag(switches)}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    def counts(subset):
        return {
            "decision": {d.value: sum(r["decision"] == d.value for r in subset) for d in Decision},
            "rule": {rule: sum(r["rule_id"] == rule for r in subset) for rule in RULE_DECISIONS},
            "review_label": dict(sorted(Counter(r["review_label"] for r in subset).items())),
        }

    patch_rows = [row for row in rows if row["has_patch"]]
    summary = {
        "run": str(run), "seal_sha256": seal_sha256,
        "policy": {"name": policy.name, "version": policy.version}, "switches": switches,
        "tasks": len(rows), "patch_tasks": len(patch_rows),
        "counts": {"all": counts(rows), "patch": counts(patch_rows)},
        "csv": str(csv_path),
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "summary_name": f"summary_v1_5_{tag(switches)}.json",
    }
    (output / summary["summary_name"]).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path, help="sealed run directory")
    parser.add_argument("--switches", required=True, help="r2=0|1,r3=0|1,r6=0|1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = decide_run(args.run, parse_switches(args.switches), args.output)
    patch = summary["counts"]["patch"]
    print(f"{summary['policy']['version']} {tag(summary['switches'])}: "
          f"{summary['tasks']} tasks, {summary['patch_tasks']} with a patch")
    print("patch decisions: " + ", ".join(f"{k} {v}" for k, v in patch["decision"].items()))
    print("patch rules: " + ", ".join(f"{k} {v}" for k, v in patch["rule"].items() if v))
    print(f"wrote {summary['csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
