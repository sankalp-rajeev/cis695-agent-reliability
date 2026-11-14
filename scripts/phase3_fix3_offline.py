#!/usr/bin/env python3
"""AST-only acceptance against frozen selections and recorded load-abort labels."""

import argparse
import csv
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

from unidiff import PatchSet

from reliability.verifier.id_validation import SourceTree, StaticIndex

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path(
    "/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen"
)
CONFIGS = {"setup.cfg", "tox.ini", "pytest.ini", ".pytest.ini", "pyproject.toml"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sources_from_archive(path):
    sources = {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith("testbed/"):
                name = member.name[8:]
                if name.endswith(".py") or Path(name).name in CONFIGS:
                    sources[name] = archive.extractfile(member).read().decode("utf-8", "replace")
    return SourceTree(sources)


def patched_sources(tree, patch_text):
    """Apply candidate text hunks in memory; never import or execute tree source."""
    sources = dict(tree.sources)
    for patch in PatchSet(patch_text):
        source = patch.source_file.removeprefix("a/")
        target = patch.target_file.removeprefix("b/")
        if not (
            source.endswith(".py")
            or target.endswith(".py")
            or Path(source).name in CONFIGS
            or Path(target).name in CONFIGS
        ):
            continue
        original = sources.get(source, "").splitlines(keepends=True)
        result, cursor = [], 0
        for hunk in patch:
            start = max(0, hunk.source_start - 1)
            result.extend(original[cursor:start])
            cursor = start
            for line in hunk:
                if line.line_type == "\\":
                    if result:
                        result[-1] = result[-1].rstrip("\r\n")
                    continue
                if line.is_context or line.is_removed:
                    assert cursor < len(original), (source, cursor)
                    assert original[cursor].rstrip("\r\n") == line.value.rstrip("\r\n"), (
                        source,
                        cursor,
                    )
                    cursor += 1
                if line.is_context or line.is_added:
                    result.append(line.value)
        result.extend(original[cursor:])
        if source != target:
            sources.pop(source, None)
        if target != "/dev/null":
            sources[target] = "".join(result)
        else:
            sources.pop(source, None)
    return SourceTree(sources)


def main(args):
    assert not args.output.exists()
    hashes = {}

    def read(path):
        raw = path.read_bytes()
        hashes[str(path)] = sha(raw)
        return raw

    report = ROOT / "reports/next_phases/phase2_incomplete_causes"
    batches = list(
        csv.DictReader(read(report / "batch_offending_label_classes.csv").decode().splitlines())
    )
    assert len(batches) == 942
    prior = list(
        csv.DictReader(
            read(ROOT / "reports/next_phases/phase4_baselines/fix0_owner_check.csv")
            .decode()
            .splitlines()
        )
    )
    collateral = {
        (r["instance_id"], r["selected_test_id"]) for r in prior if r["owner_is_TestCase"] == "True"
    }
    assert len(collateral) == 796
    tasks = json.loads(read(FROZEN / "tasks.json"))
    all_rows, tree_rows, offender_rows, collateral_rows = [], [], [], []
    for meta in tasks:
        task, runner = meta["instance_id"], meta["runner"]["name"]
        selected = json.loads(read(FROZEN / meta["selections"]["v2"]))["tests"]
        archive = Path("/home/sankalp/cg_repos/task_archives") / (task + ".tar")
        assert sha(read(archive)) == meta["base_archive_sha256"]
        base = sources_from_archive(archive)
        for path, expected in meta["base_source_sha256"].items():
            if path in base.sources:
                assert sha(base.sources[path].encode()) == expected, (task, path)
        patch = Path(meta["patch_path"])
        if not patch.is_absolute():
            patch = FROZEN / patch
        patch_raw = read(patch)
        assert sha(patch_raw) == meta["patch_sha256"]
        patched = patched_sources(base, patch_raw.decode("utf-8"))
        parse_cache = {}
        for tree, sources in (("base", base), ("patched", patched)):
            index = StaticIndex(sources, runner, parse_cache=parse_cache)
            records = {r.selected_id: r for r in index.validate(selected)}
            for record in records.values():
                row = {"instance_id": task, "tree": tree, "runner": runner, **record.to_dict()}
                for field in ("runnable_ids", "decorators", "invalid_instances", "owner_instances"):
                    row[field] = json.dumps(row[field])
                all_rows.append(row)
            counts = Counter(r.category for r in records.values())
            tree_rows.append(
                {
                    "instance_id": task,
                    "tree": tree,
                    "runner": runner,
                    "selected_slots": len(selected),
                    "static_INVALID_ID": sum(not r.valid for r in records.values()),
                    "expanded_slots": sum(r.expanded for r in records.values()),
                    "owner_expanded_instances": sum(
                        len(r.runnable_ids) for r in records.values() if r.expanded
                    ),
                    "runnable_instances": len(
                        {tid for r in records.values() if r.valid for tid in r.runnable_ids}
                    ),
                    "categories": json.dumps(counts, sort_keys=True),
                }
            )
            for batch in batches:
                if batch["instance_id"] != task or batch["tree"] != tree:
                    continue
                offenders = json.loads(batch["offending_selected_ids"])
                findings = [records[t] for t in offenders]
                offender_rows.append(
                    {
                        "instance_id": task,
                        "tree": tree,
                        "batch": batch["batch"],
                        "recorded_class": batch["offending_label_class"],
                        "identification": batch["label_identification"],
                        "offending_labels": json.dumps(offenders),
                        "categories": json.dumps([r.category for r in findings]),
                        "reasons": json.dumps([r.reason for r in findings]),
                        "identified_labels": len(findings),
                        "flagged_labels": sum(not r.valid or r.expanded for r in findings),
                        "any_offender_flagged": any(not r.valid or r.expanded for r in findings),
                        "all_offenders_flagged": bool(findings)
                        and all(not r.valid or r.expanded for r in findings),
                        "static_not_found_labels": sum(r.category == "not_found" for r in findings),
                        "capture_path": batch["evidence_path"],
                        "line_start": batch["line_start"],
                    }
                )
            if tree == "base":
                for _, tid in sorted(k for k in collateral if k[0] == task):
                    r = records[tid]
                    collateral_rows.append(
                        {
                            "instance_id": task,
                            "selected_id": tid,
                            "category": r.category,
                            "runnable": r.valid and not r.expanded,
                            "owner_is_TestCase": r.owner_is_testcase,
                            "reason": r.reason,
                        }
                    )
            del index
        print(task, len(selected), flush=True)
    by_class = []
    for kind in sorted({r["recorded_class"] for r in offender_rows}):
        relevant = [r for r in offender_rows if r["recorded_class"] == kind]
        by_class.append(
            {
                "recorded_class": kind,
                "abort_batches": len(relevant),
                "batches_with_identified_labels": sum(
                    bool(r["identified_labels"]) for r in relevant
                ),
                "any_offender_flagged": sum(r["any_offender_flagged"] for r in relevant),
                "all_offenders_flagged": sum(r["all_offenders_flagged"] for r in relevant),
                "identified_labels": sum(r["identified_labels"] for r in relevant),
                "flagged_labels": sum(r["flagged_labels"] for r in relevant),
                "static_not_found_labels": sum(r["static_not_found_labels"] for r in relevant),
            }
        )
    summary = {
        "scope": "OFFLINE STATIC ONLY; no repository source execution, Docker or outcomes",
        "tasks": len(tasks),
        "selected_tree_slots": len(all_rows),
        "load_abort_batches": len(offender_rows),
        "flagged_abort_batches": sum(r["any_offender_flagged"] for r in offender_rows),
        "identified_offender_labels": sum(r["identified_labels"] for r in offender_rows),
        "flagged_offender_labels": sum(r["flagged_labels"] for r in offender_rows),
        "collateral_TestCase_labels": len(collateral_rows),
        "collateral_correctly_left_runnable": sum(r["runnable"] for r in collateral_rows),
        "not_found_coverage": "Separated in abort_classes.csv and abort_acceptance.csv; AST cannot predict missing dependencies, GIS guards or module import exceptions.",
        "Docker_calls": 0,
        "correctness_labels_read": False,
    }
    assert len(offender_rows) == 942 and len(collateral_rows) == 796
    args.output.mkdir(parents=True)
    for name, rows in [
        ("static_ids.csv", all_rows),
        ("task_tree_counts.csv", tree_rows),
        ("abort_acceptance.csv", offender_rows),
        ("abort_classes.csv", by_class),
        ("collateral_acceptance.csv", collateral_rows),
    ]:
        write_csv(args.output / name, rows)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for path in (
        Path(__file__),
        ROOT / "src/reliability/verifier/id_validation.py",
        ROOT / "reports/next_phases/phase4_plan.md",
    ):
        read(path)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {"input_sha256": hashes, "rule_commit": "55a5fd6", "correctness_labels_read": False},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))
    print(json.dumps(by_class, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
