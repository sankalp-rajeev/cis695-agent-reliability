#!/usr/bin/env python3
"""Recompute v1.5 decisions for every task of a sealed run from its stored evidence.

Offline and label-free: nothing is re-executed, and only the run's seal, header,
completion record and per-task verification records are opened. A run path
naming labels, grading or post-hoc material is refused before anything is
read; every file opened is checked by name too. Writes one CSV row per task
and a JSON summary for the chosen switches:

    scripts/decide_v1_5.py runs/study_test1_gold --frozen --output DIR
    scripts/decide_v1_5.py runs/study_dev_armB --switches r2=0,r3=0,r6=0 --output DIR

--frozen reads the switches from configs/verifier/v1_5.yaml as committed at the
annotated tag v1.5-frozen and records the tag commit and config SHA-256.
Headline results use --frozen only; --switches is for Phase 7 calibration and
Phase 16 ablations.

--no-v2-fallback (amendment A4 (v)) recomputes V2 as if the V2 fallback were off,
from each task's sealed selection.json. The fallback runs only when Tiers 1 and
2 select nothing, so a fallback selection holds only fallback tests, and without
it V2 is NOT_AVAILABLE with nothing to check, which is what the run itself
records for an empty selection. A task whose stored selection does not show
which tests the fallback chose, or mixes fallback and other tests, is refused
rather than guessed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from e2e_input_preflight import FORBIDDEN_NAMES  # noqa: E402

from reliability.verifier.decision import Decision, SignalOutcome  # noqa: E402
from reliability.verifier.policy_v1_5 import (  # noqa: E402
    RULE_DECISIONS, V2_NOTHING_TO_CHECK, FullPolicyV15, evidence_from_signals,
    switches_from_config_text,
)
from reliability.verifier.reproduction_reuse import RECORD  # noqa: E402
from reliability.verifier.run_v1_4_1 import VerificationRecordV141  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FROZEN_TAG = "v1.5-frozen"
FROZEN_CONFIG = "configs/verifier/v1_5.yaml"
#: CLAUDE.md names these too; "grading" does not contain "grade".
LABEL_WORDS = FORBIDDEN_NAMES + ("grading", "per_instance_details", "git_peek",
                                 "decision_by_correctness")
SWITCH_KEYS = {"r2": "r2_v3_reject", "r3": "r3_extended_reject", "r6": "r6_accept_v2_not_available"}
#: Optional switches: off when not named (amendment A8).
OPTIONAL_SWITCH_KEYS = {"r6b": "r6b_accept_one_uncovered"}
EVIDENCE_FIELDS = ("v3_absolute_failure", "v1_analysis_incomplete", "high_severity_risk",
                   "v4_design", "v4_full_pass", "v4_fail_confirmed", "v4_failing_units",
                   "v4_pass_units", "v4_uncovered_units", "v4_no_result_units", "v2_absence", "v2_patched_timeout_or_crash",
                   "v3_pre_existing", "v3_base_unknown")
FIELDS = ("instance_id", "has_patch", "stored_decision", "stored_policy_version",
          "integrity", "v2", "v4", *EVIDENCE_FIELDS, "v2_fallback_removed",
          "decision", "rule_id", "review_label")
SELECTION = "verification/selection.json"


def parse_switches(text: str) -> dict[str, bool]:
    pairs = [item.split("=", 1) for item in text.split(",")]
    if any(len(pair) != 2 for pair in pairs):
        raise ValueError("--switches must look like r2=0,r3=0,r6=0")
    keys = [key for key, _ in pairs]
    required = [key for key in keys if key in SWITCH_KEYS]
    optional = [key for key in keys if key in OPTIONAL_SWITCH_KEYS]
    if (sorted(required) != sorted(SWITCH_KEYS) or len(set(optional)) != len(optional)
            or len(required) + len(optional) != len(keys)
            or any(value not in ("0", "1") for _, value in pairs)):
        raise ValueError("--switches needs r2, r3 and r6 exactly once (r6b optional), each 0 or 1")
    names = {**SWITCH_KEYS, **OPTIONAL_SWITCH_KEYS}
    switches = {name: False for name in OPTIONAL_SWITCH_KEYS.values()}
    switches.update({names[key]: value == "1" for key, value in pairs})
    return switches


def frozen_switches(repo: Path | None = None, tag: str = FROZEN_TAG) -> tuple[dict[str, bool], dict]:
    """Switches from the config as committed at an annotated tag, never the working tree."""
    repo = Path(repo or ROOT)

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True)

    kind = git("cat-file", "-t", f"refs/tags/{tag}")
    if kind.returncode != 0:
        raise ValueError(f"tag {tag} is missing")
    if kind.stdout.decode().strip() != "tag":
        raise ValueError(f"tag {tag} is not an annotated tag")
    commit = git("rev-parse", f"refs/tags/{tag}^{{commit}}")
    raw = git("show", f"refs/tags/{tag}:{FROZEN_CONFIG}")
    if commit.returncode != 0 or raw.returncode != 0:
        raise ValueError(f"cannot read {FROZEN_CONFIG} at tag {tag}")
    switches = switches_from_config_text(raw.stdout.decode("utf-8"))
    return switches, {"tag": tag, "tag_commit": commit.stdout.decode().strip(),
                      "config_path": FROZEN_CONFIG,
                      "config_sha256": hashlib.sha256(raw.stdout).hexdigest()}


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


def tag(switches: dict[str, bool], v2_fallback: bool = True) -> str:
    name = "_".join(f"{key}-{int(switches[name])}" for key, name in SWITCH_KEYS.items())
    name += "".join(f"_{key}-1" for key, option in OPTIONAL_SWITCH_KEYS.items() if switches.get(option))
    return name if v2_fallback else name + "_v2-nofallback"


def added_paths(run: Path, files: dict[str, str], iid: str) -> tuple[str, ...]:
    """Files the task's sealed patch adds or renames to (amendment A6). Contents are never printed."""
    from reliability.verifier.patch import PatchParseError, parse_patch

    name = f"tasks/{iid}/patch.diff"
    if name not in files:
        return ()
    text = _read(run, files, name).decode("utf-8", errors="replace")
    if not text.strip():
        return ()
    try:
        changes = parse_patch(text)
    except PatchParseError:
        # V1 records such a patch as unparseable (integrity FAIL, R1 REJECT).
        return ()
    return tuple(sorted(f.path for f in changes if f.kind.value in ("added", "renamed")))


def without_v2_fallback(run: Path, files: dict[str, str], iid: str, record, evidence):
    """V2 evidence with the fallback off. Returns (evidence, whether the fallback was removed)."""
    name = f"tasks/{iid}/{SELECTION}"
    if name not in files:
        # No selection was made, so no fallback ran; V2 is absent either way.
        if evidence.regression is not SignalOutcome.NOT_AVAILABLE:
            raise ValueError(f"cannot tell which tests the V2 fallback selected: {iid} "
                             "has a V2 result but no stored selection")
        return evidence, False
    raw = _read(run, files, name)
    if record.selection_sha256 != hashlib.sha256(raw).hexdigest():
        raise ValueError(f"stored selection differs from the record's selection_sha256: {iid}")
    selection = json.loads(raw)
    used, fallback = selection.get("fallback_used"), selection.get("fallback_tests")
    tests = selection.get("tests")
    if type(used) is not bool or not isinstance(fallback, list) or not isinstance(tests, list):
        raise ValueError(f"cannot tell which tests the V2 fallback selected: {iid}")
    if used != bool(fallback) or not set(fallback) <= set(tests):
        raise ValueError(f"stored selection mixes fallback and other tests: {iid}")
    if not used:
        return evidence, False
    if set(tests) != set(fallback):
        raise ValueError(f"stored selection mixes fallback and other tests: {iid}; V2 without "
                         "the fallback cannot be recomputed from stored signals")
    return replace(evidence, regression=SignalOutcome.NOT_AVAILABLE,
                   v2_absence=V2_NOTHING_TO_CHECK), True


def decide_run(run: Path, switches: dict[str, bool], output: Path, frozen: dict | None = None,
               *, v2_fallback: bool = True) -> dict:
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
        evidence = evidence_from_signals(record.signals,
                                         added_paths=added_paths(run, files, iid))
        removed = False
        if not v2_fallback:
            evidence, removed = without_v2_fallback(run, files, iid, record, evidence)
        result = policy.decide(evidence)
        rows.append({
            "instance_id": iid, "has_patch": iid not in no_patch,
            "stored_decision": record.decision.decision.value,
            "stored_policy_version": record.decision.policy_version,
            "integrity": evidence.integrity.value, "v2": evidence.regression.value,
            "v4": evidence.reproduction.value,
            **{k: (";".join(v) if isinstance(v := getattr(evidence, k), tuple) else v)
               for k in EVIDENCE_FIELDS},
            "v2_fallback_removed": removed,
            "decision": result.decision.value, "rule_id": result.rule_id,
            "review_label": result.review_label,
        })
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / f"decisions_v1_5_{tag(switches, v2_fallback)}.csv"
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
        "v2_fallback": v2_fallback,
        "v2_fallback_removed_tasks": sorted(r["instance_id"] for r in rows if r["v2_fallback_removed"]),
        "switch_source": "frozen" if frozen else "command line", "frozen": frozen,
        "tasks": len(rows), "patch_tasks": len(patch_rows),
        "counts": {"all": counts(rows), "patch": counts(patch_rows)},
        "csv": str(csv_path),
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "summary_name": f"summary_v1_5_{tag(switches, v2_fallback)}.json",
    }
    (output / summary["summary_name"]).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path, help="sealed run directory")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--frozen", action="store_true",
                        help=f"switches from {FROZEN_CONFIG} at annotated tag {FROZEN_TAG}")
    source.add_argument("--switches", help="r2=0|1,r3=0|1,r6=0|1[,r6b=0|1]")
    parser.add_argument("--no-v2-fallback", action="store_true",
                        help="recompute V2 without fallback-selected tests (amendment A4 (v))")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.frozen:
        switches, frozen = frozen_switches()
    else:
        switches, frozen = parse_switches(args.switches), None
    summary = decide_run(args.run, switches, args.output, frozen,
                         v2_fallback=not args.no_v2_fallback)
    patch = summary["counts"]["patch"]
    if frozen:
        print(f"switches from {frozen['tag']} @ {frozen['tag_commit']}")
    print(f"{summary['policy']['version']} {tag(summary['switches'], summary['v2_fallback'])}: "
          f"{summary['tasks']} tasks, {summary['patch_tasks']} with a patch")
    print("patch decisions: " + ", ".join(f"{k} {v}" for k, v in patch["decision"].items()))
    print("patch rules: " + ", ".join(f"{k} {v}" for k, v in patch["rule"].items() if v))
    print(f"wrote {summary['csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
