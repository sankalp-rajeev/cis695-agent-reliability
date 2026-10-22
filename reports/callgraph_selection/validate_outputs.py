"""Read stored graph artifacts and verify provenance/accounting; executes no tests."""
from __future__ import annotations

import ast
import csv
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def records(path):
    with gzip.open(path, "rt") as stream:
        for line in stream:
            yield json.loads(line)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    inputs = json.loads((OUT / "graph_inputs.json").read_text())
    for section in ("code_sha256", "input_sha256"):
        for path, expected in inputs[section].items():
            require(digest(ROOT / path) == expected, "changed input/code: " + path)
    for path, expected in inputs["output_sha256"].items():
        require(digest(OUT / path) == expected, "changed graph artifact: " + path)
    with (OUT / "base_feasibility.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == len({r["instance_id"] for r in rows}) == 83, "wrong population")
    totals = Counter()
    failures = Counter()
    provenance = {}
    for row in rows:
        directory = OUT / "graphs" / row["instance_id"]
        diagnostic = json.loads((directory / "diagnostics.json").read_text())
        require(all(str(v) == row[k] for k, v in diagnostic["row"].items()), "CSV/diagnostics disagree")
        nodes = {n["id"]: n for n in records(directory / "nodes.jsonl.gz")}
        require(len(nodes) == int(row["nodes"]), "node count mismatch")
        indexed_definitions = sum(n["kind"] != "module" for n in nodes.values())
        if row["graph_status"] == "resource_limited":
            require(indexed_definitions <= int(row["definitions"]), "resource prefix exceeds inspected definitions")
        else:
            require(indexed_definitions == int(row["definitions"]), "definition count mismatch")
        counts = Counter()
        for edge in records(directory / "edges.jsonl.gz"):
            require(edge["caller"] in nodes, "missing edge caller")
            require(all(t in nodes for t in edge["targets"]), "missing edge target")
            require(edge["status"] in {"resolved", "ambiguous", "unresolved"}, "invalid edge status")
            if edge["status"] == "resolved":
                require(len(edge["targets"]) == 1 and edge["reason"] == "unique_static_binding",
                        "resolved edge without unique binding")
            counts[edge["status"]] += 1
        require(sum(counts.values()) == int(row["edge_records"]), "edge total mismatch")
        if row["graph_status"] != "resource_limited":
            require(sum(counts.values()) == int(row["call_sites"]), "unaccounted AST call sites")
        for status in ("resolved", "ambiguous", "unresolved"):
            if row["graph_status"] == "resource_limited":
                require(row[status + "_edges"] == "", "resource stop became zero-valued edge evidence")
            else:
                require(counts[status] == int(row[status + "_edges"]), "edge status count mismatch")
        symbols = json.loads((directory / "changed_symbols.json").read_text())["symbols"]
        if row["patch_status"] == "patch missing" or row["graph_status"] == "resource_limited":
            require(not symbols, "missing candidate has symbols")
            require(all(row[key] == "" for key in ("changed_symbols_total", "changed_symbols_resolved",
                        "changed_symbols_ambiguous", "changed_symbols_unresolved", "changed_symbol_resolution_rate")),
                    "missing candidate became zero-valued evidence")
        elif row["patch_status"] == "available":
            named = [s for s in symbols if s["name"] is not None]
            require(len(named) == int(row["changed_symbols_total"]), "changed-symbol count mismatch")
            counts_symbols = Counter(s["status"] for s in named)
            for status in ("resolved", "ambiguous", "unresolved"):
                require(counts_symbols[status] == int(row["changed_symbols_" + status]), "symbol status mismatch")
            if named:
                require(abs(float(row["changed_symbol_resolution_rate"]) - counts_symbols["resolved"] / len(named)) < 0.000001,
                        "symbol rate mismatch")
        for failure in diagnostic["parse_and_resource_failures"]:
            failures[(row["repo"], failure.get("path", ""), failure["reason"])] += 1
        key = (row["repo"], row["patch_provenance"])
        group = provenance.setdefault(key, Counter())
        group["tasks"] += 1
        group["measured_symbol_tasks"] += row["changed_symbol_resolution_status"].startswith("measured")
        group[row["graph_status"] + "_graphs"] += 1
        for name in ("total", "resolved", "ambiguous", "unresolved"):
            group["symbols_" + name] += int(row["changed_symbols_" + name] or 0)
        totals.update(counts)
    require(not list(Path("/tmp").glob("cis695-cg-*")), "temporary extraction tree remains")
    checked_python = []
    # Static import inspection only: no test collection or execution.
    for path in sorted((ROOT / "src").rglob("*.py")) + sorted(OUT.glob("*.py")):
        tree = ast.parse(path.read_bytes(), filename=str(path))
        for node in ast.walk(tree):
            modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            require(not any("oracle_posthoc" in module or "failure_analysis" in module for module in modules),
                    "post-hoc import crosses boundary: " + str(path))
        checked_python.append(str(path.relative_to(ROOT)))
    provenance_rows = []
    for (repo, origin), group in sorted(provenance.items()):
        provenance_rows.append(dict(repo=repo, patch_provenance=origin, tasks=group["tasks"],
                                   measured_symbol_tasks=group["measured_symbol_tasks"],
                                   complete_graphs=group["complete_graphs"], partial_graphs=group["partial_graphs"],
                                   resource_limited_graphs=group["resource_limited_graphs"],
                                   **{k: group[k] if origin != "missing" else "" for k in
                                      ("symbols_total", "symbols_resolved", "symbols_ambiguous", "symbols_unresolved")},
                                   resolution_rate=group["symbols_resolved"] / group["symbols_total"]
                                   if group["symbols_total"] else ""))
    with (OUT / "changed_symbol_by_provenance.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, list(provenance_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(provenance_rows)
    with (OUT / "parse_failure_summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("repo", "path", "reason", "affected_task_snapshots"))
        writer.writerows((*key, count) for key, count in sorted(failures.items()))
    report_path = OUT / "report.md"
    marker = "\n<!-- stored-validation-supplement -->\n"
    original = report_path.read_text().split(marker)[0].rstrip()
    extra = ["", "## Stored-output checks and provenance strata", "",
             "All 83 task artifacts passed hash and accounting checks. Every completed graph's call-site total and all "
             "retained edge target IDs were checked; resource-limit prefixes were checked as incomplete diagnostics. "
             "All extraction trees were removed. AST-only import inspection found no post-hoc module import under `src/` "
             "or this graph implementation. Synthetic unit checks are supplied in `test_static_graph.py` but were not run.", "",
             f"Interpreter: `{sys.version.splitlines()[0]}`. No benchmark source was imported or executed.", "",
             "| Candidate provenance | Tasks / symbol-measured tasks | Complete / partial / limited graphs | Resolved / ambiguous / unresolved symbols | Rate |",
             "|---|---|---|---|---|"]
    for origin in sorted({origin for _, origin in provenance}):
        group = sum((counts for (_, p), counts in provenance.items() if p == origin), Counter())
        rate = group["symbols_resolved"] / group["symbols_total"] if group["symbols_total"] else None
        symbol_text = (f"{group['symbols_resolved']} / {group['symbols_ambiguous']} / {group['symbols_unresolved']}"
                       if origin != "missing" else "—")
        extra.append(f"| {origin} | {group['tasks']} / {group['measured_symbol_tasks']} | {group['complete_graphs']} / {group['partial_graphs']} / {group['resource_limited_graphs']} "
                     f"| {symbol_text} | " + (f"{rate:.1%}" if rate is not None else "—") + " |")
    extra += ["", "Per-repository strata are in `changed_symbol_by_provenance.csv`. Local candidates remain exploratory; "
              "their hashes do not establish final-run identity. Historical and broader offline comparisons have not run.", "",
              "The exact source-run directory also contains a hash-verified local candidate for `pytest-dev__pytest-6202`, "
              "in addition to the five previously inventoried local candidates. It remains in the same unverified-local "
              "stratum; no alternate run was substituted. The confirmed historical cohort remains 19 tasks.", "",
              "Graph definition IDs encode file, lexical name, kind and location; they are not normalized runner test IDs. "
              "No test-ID adapter, Django docstring-name mapping, or second normalizer was introduced in this phase.", "",
              "Failure paths/reasons and their task-snapshot frequencies are in `parse_failure_summary.csv`. "
              "There are 71 syntax/encoding parse failures across task snapshots and six Python symlink members "
              "omitted without following their targets. Four SymPy snapshots hit the unchanged 5,000,000 AST-node limit. "
              "The most frequent stored failures are:", "",
              "| Repository | Path | Reason | Snapshots |", "|---|---|---|---:|"]
    for (repo, path, reason), count in failures.most_common(6):
        extra.append(f"| {repo} | `{path}` | {reason} | {count} |")
    extra += ["", "No syntax fixture or source directory was silently excluded to obtain a complete graph. "
              "Partial graphs remain in feasibility denominators and are ineligible for the later primary comparison.", "",
              "Validate these stored artifacts without rebuilding graphs:", "", "```bash",
              "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_outputs.py", "```", ""]
    if "accounting_refresh" in inputs:
        refresh = inputs["accounting_refresh"]
        extra += ["## Accounting correction", "",
                  "Initial output validation found one omitted call per graph in five tasks: a call appearing directly as "
                  "an annotation root. The AST visitor was corrected to retain these as unresolved calls. Only those "
                  "five graphs were rebuilt; all four AST-node-limit stops were preserved without retry. Reused graph "
                  "provenance and initial implementation hashes/source snapshots are recorded in `graph_inputs.json`. "
                  "Resource-limited symbol and edge-resolution measurements are blank, never failed/zero scores.", "",
                  "Rebuilt tasks: " + ", ".join(f"`{iid}`" for iid in refresh["rebuilt_tasks"]) + ".", "",
                  "Commands used during this diagnostic (a fresh build with the corrected code needs only the first and last):", "",
                  "```bash", inputs["command"], refresh["command"],
                  "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_outputs.py", "```", ""]
    report_path.write_text(original + marker + "\n".join(extra))
    sample_inputs = OUT / "sample_graph_inputs.json"
    if sample_inputs.is_file():
        sample = json.loads(sample_inputs.read_text())
        sample["output_sha256"] = {}
        sample["note"] = "Sample CSV and aggregate measurements retained; graph directories superseded by full build."
        sample_inputs.write_text(json.dumps(sample, sort_keys=True, indent=2) + "\n")
    result = dict(status="passed", tasks=len(rows), edge_status_counts=dict(totals),
                  checks=["code/input/output SHA-256", "83 unique tasks", "CSV/diagnostic agreement",
                          "node and definition counts", "call-site accounting", "edge endpoints and classifications",
                          "changed-symbol accounting", "blank fields for missing candidates", "temporary tree cleanup",
                          "AST syntax and post-hoc import boundary inspection"],
                  test_execution=False, oracle_analysis=False,
                  validator_sha256=digest(Path(__file__)), python_version=sys.version,
                  inspected_python_files=checked_python,
                  derived_output_sha256={p.name: digest(p) for p in (
                      report_path, OUT / "changed_symbol_by_provenance.csv", OUT / "parse_failure_summary.csv")})
    (OUT / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
