"""Independent source audit of frozen discovery results; no selection tuning."""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import subprocess
import tarfile
import tokenize
from collections import Counter
from pathlib import Path

from v2_discovery_experiment import ARCHIVES, ROOT, original_selector, save, sha


def source_definitions(text):
    tree = ast.parse(text)
    nodes = list(ast.walk(tree))
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    definitions = {}
    for node in nodes:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        ancestors = []
        parent = parents.get(node)
        while parent is not None:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ancestors.append(parent)
            parent = parents.get(parent)
        definitions[node.lineno] = (node, ancestors)
    strings = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.STRING:
            strings.update(range(token.start[0], token.end[0] + 1))
    return tree, definitions, strings


def audit(comparison, out):
    data = json.loads(comparison.read_text())
    out.mkdir(parents=True, exist_ok=False)
    assert len(data["tasks"]) == 83 and not data["unavailable"]
    old, _ = original_selector()
    removed_rows, valid_rows, uncertain, task_rows = [], [], [], []
    for task in data["tasks"]:
        iid = task["instance_id"]
        assert len(task["before"]) - len(task["after"]) == task["removed"]
        retained, before = set(task["after"]), set(task["before"])
        assert retained <= before
        assert task["after"] == [t for t in task["before"] if t in retained]
        by_file = {}
        for tid in before:
            by_file.setdefault(tid.split("::", 1)[0], []).append(tid)
        with tarfile.open(ARCHIVES / f"{iid}.tar") as archive:
            for path, ids in by_file.items():
                payload = archive.extractfile("testbed/" + path).read()
                text = payload.decode("utf-8", errors="replace")
                legacy_ids = old.node_ids(path, text)
                # Pair the original scanner's output with physical candidate lines,
                # independently of the improved filter or its reasons.
                lines = [i for i, line in enumerate(text.splitlines(), 1)
                         if re.match(r"^[ \t]*def\s+test_\w+\s*\(", line)]
                assert len(lines) == len(legacy_ids), (iid, path)
                occurrence = {}
                for line, tid in zip(lines, legacy_ids):
                    occurrence.setdefault(tid, []).append(line)
                try:
                    _, defs, strings = source_definitions(text)
                except (SyntaxError, ValueError, RecursionError, tokenize.TokenError):
                    assert set(ids) <= retained, (iid, path, "parse-uncertain ID removed")
                    uncertain.append({"instance_id": iid, "path": path,
                                      "reason": "parse uncertainty retained", "ids": ids})
                    continue
                for line, tid in zip(lines, legacy_ids):
                    if tid not in before or line not in defs:
                        continue
                    node, ancestors = defs[line]
                    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                           for n in ancestors):
                        continue
                    assert tid in retained, (iid, tid, "real outer definition removed")
                    valid_rows.append({"instance_id": iid, "test_id": tid, "line": line,
                                       "parametrized": any("parametrize" in ast.unparse(d)
                                                           for d in node.decorator_list)})
                for tid in set(ids) - retained:
                    proofs = []
                    for line in occurrence[tid]:
                        if line in strings and line not in defs:
                            proof = "tokenizer string token; no function at this source location"
                            assert line not in defs
                        else:
                            assert line in defs, (iid, tid, line, "no independent exclusion proof")
                            node, ancestors = defs[line]
                            assert any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                                       for n in ancestors), (iid, tid, "outer definition")
                            proof = "function ancestor; local helper or method on a local class"
                        proofs.append({"line": line, "proof": proof,
                                       "context": "\n".join(f"{i + 1}: {text.splitlines()[i]}"
                                                           for i in range(max(0, line - 5),
                                                                          min(len(text.splitlines()), line + 5))),
                                       "ancestors": [n.name for n in defs[line][1]] if line in defs else []})
                    removed_rows.append({"instance_id": iid, "test_id": tid,
                                         "source_sha256": sha(payload), "proofs": proofs})
        uncertain.extend({"instance_id": iid, **r} for r in task["uncertain_retained"])
        task_rows.append({"instance_id": iid, "before": task["original"],
                          "after": task["retained"], "removed": task["removed"],
                          "runner": task["runner"]["name"]})

    # The comparison is already immutable and hashed before post-hoc retention
    # evidence is read. These witnesses never enter discovery or its configuration.
    comparison_hash = sha(comparison.read_bytes())
    known = json.loads((ROOT / "reports/failure_analysis/group4_failing_tests.json").read_text())
    selections = {r["instance_id"]: r for r in data["tasks"]}
    witness_rows = []
    for iid, tests in known.items():
        if iid.startswith("_"):
            continue
        for tid in tests:
            task = selections[iid]
            assert tid in task["before"] and tid in task["after"]
            witness_rows.append({"instance_id": iid, "test_id": tid,
                                 "tier": "historical reported regression", "retained": True})
    raw_rows = []
    raw_path = ROOT / "reports/v2_scoring_audit/resume_20261026/raw_test_outcomes.csv"
    with raw_path.open() as stream:
        for row in csv.DictReader(stream):
            iid, tid = row["instance_id"], row["raw_test_id"]
            family = tid.split("[", 1)[0]
            task = selections[iid]
            if tid in task["before"] or family in task["before"]:
                assert tid in task["after"] or family in task["after"]
                raw_rows.append({"instance_id": iid, "raw_test_id": tid,
                                 "retained_family": tid if tid in task["after"] else family})
    assert sha(comparison.read_bytes()) == comparison_hash

    # AST comparison covers all pre-existing selection/ranking functions except
    # the deliberately replaced node_ids; protected files must retain their bytes.
    original = subprocess.check_output(["git", "show", "0c0c87f:src/reliability/verifier/selection.py"], cwd=ROOT)
    current = (ROOT / "src/reliability/verifier/selection.py").read_bytes()
    def defs(code):
        return {n.name: ast.dump(n, include_attributes=False)
                for n in ast.parse(code).body
                if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    before_defs, after_defs = defs(original), defs(current)
    unchanged = [name for name in before_defs if name != "node_ids"]
    assert all(before_defs[n] == after_defs[n] for n in unchanged)
    initial = json.loads((out.parent / "initial_state.json").read_text())
    protected = {p: h for p, h in initial["tracked"].items()
                 if p.startswith(("src/reliability/verifier/", "configs/verifier/"))
                 and not p.endswith("/selection.py")}
    assert all(sha((ROOT / p).read_bytes()) == h for p, h in protected.items())
    save(out / "removed_ids.json", sorted(removed_rows, key=lambda r: (r["instance_id"], r["test_id"])))
    save(out / "valid_outer_definitions.json", valid_rows)
    save(out / "uncertain_retained.json", uncertain)
    save(out / "known_witnesses_retained.json", witness_rows)
    save(out / "observed_raw_tests_retained.json", raw_rows)
    save(out / "task_counts.json", task_rows)
    summary = {"tasks": len(task_rows), "affected_tasks": sum(t["removed"] > 0 for t in task_rows),
               "removed": len(removed_rows), "retained": sum(t["after"] for t in task_rows),
               "original": sum(t["before"] for t in task_rows),
               "independently_proved_invalid": len(removed_rows),
               "proof_occurrences": dict(Counter(p["proof"] for r in removed_rows for p in r["proofs"])),
               "valid_outer_occurrences_retained": len(valid_rows),
               "parametrized_outer_occurrences_retained": sum(r["parametrized"] for r in valid_rows),
               "uncertain_records_retained": len(uncertain), "known_regression_tests_retained": len(witness_rows),
               "observed_raw_tests_retained": len(raw_rows), "comparison_sha256": comparison_hash,
               "protected_code_sha256": protected, "unchanged_selection_definitions": unchanged,
               "source_only_proof_limit": "Module/class collection still depends on runner configuration; this audit proves the removed locations are strings or local scopes, not that every retained ID is runnable.",
               "oracle_labels_used_for_selection": False, "SCG_inputs_used": False}
    save(out / "summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("protected_code_sha256", "unchanged_selection_definitions")}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit(args.comparison, args.out)
