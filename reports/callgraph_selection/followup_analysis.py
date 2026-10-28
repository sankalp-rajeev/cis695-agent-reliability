"""Read-only phase-1b follow-ups. No graph rebuild, selector, oracle or repo execution.

Existing graphs remain immutable. Base archives supply only AST import metadata
and a deterministic replay of the four stopped AST counters, never call graphs.
"""
from __future__ import annotations

import ast
import builtins
import csv
import dataclasses
import gzip
import hashlib
import json
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from build_graphs import OUT, ROOT, candidate, candidate_projection, digest, write_json
from reliability.verifier.patch import Patch, parse_patch, touched_symbols
from static_graph import Graph, Indexer, LIMITS

AMENDMENT = b"\n<!-- amendment-2026-10-21-draft -->\n"
BUILTINS = frozenset(dir(builtins))
BUCKETS = ("internal_resolved", "internal_ambiguous_unresolved", "external_builtin", "unknown_boundary")


def records(path):
    with gzip.open(path, "rt") as stream:
        yield from (json.loads(line) for line in stream)


def write_csv(path, rows, fields=None):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def side_names(change, side):
    """Use the existing extractor on one diff side; no new definition regex."""
    hunks = tuple(dataclasses.replace(h, added=getattr(h, side), removed=(), context=(), section="")
                  for h in change.hunks)
    return set(touched_symbols(Patch(files=(dataclasses.replace(change, hunks=hunks),), raw="")))


def symbol_origin(symbol, change):
    name = symbol["name"]
    if symbol["targets"]:
        return "base_name_present"
    if symbol["reason"] == "symbol_absent_at_base_or_diff_context_name" and change is not None:
        if name in side_names(change, "added") and name not in side_names(change, "removed"):
            return "newly_added_name_absent_at_base"
    return "not_established"


def first_party(module, modules):
    return module in modules or module.split(".")[0] in modules


def binding_scope(scopes, sid, name):
    while sid:
        scope = scopes[sid]
        if name in scope["redirected"]:
            return None, "global_or_nonlocal"
        if name in scope["bindings"]:
            return sid, "bound"
        if scope["star_import"]:
            return None, "star_import"
        sid = scope["parent"]
        while sid and scopes[sid]["kind"] == "class":
            sid = scopes[sid]["parent"]
    return None, "unbound"


def classify_call(edge, scopes, raw_imports, modules):
    """Classify nominal namespace evidence, never pretend it proves runtime type."""
    if edge["status"] == "resolved":
        return "internal_resolved", "recorded_unique_first_party_target"
    if edge["targets"]:
        return "internal_ambiguous_unresolved", "recorded_first_party_candidate_targets"
    expr = edge["expression"]
    root = expr.split(".", 1)[0]
    if not root.isidentifier() or edge["reason"] == "unsupported_comprehension_lambda_or_annotation_scope":
        return "unknown_boundary", "dynamic_or_unmodeled_scope"
    sid, lookup = binding_scope(scopes, edge["scope"], root)
    if sid is None:
        if lookup == "unbound" and root in BUILTINS:
            return "external_builtin", "unshadowed_builtin_name"
        return "unknown_boundary", "no_namespace_evidence_" + lookup
    refs = scopes[sid]["bindings"][root]
    evidence = set()
    reasons = set()
    for kind, value in refs:
        if kind in {"node", "receiver"}:
            evidence.add("internal")
            reasons.add("first_party_definition_or_receiver")
        elif kind == "module":
            evidence.add("internal" if first_party(value, modules) else "external")
            reasons.add("explicit_module_binding")
        elif kind == "unknown" and value == "external_or_missing_module_attribute":
            imports = raw_imports.get(sid, {}).get(root, [])
            if not imports:
                evidence.add("unknown")
            for import_kind, origin in imports:
                if import_kind not in {"import", "module"}:
                    evidence.add("unknown")
                    continue
                module = origin.rsplit(":", 1)[0] if import_kind == "import" else origin
                evidence.add("internal" if first_party(module, modules) else "external")
                reasons.add("explicit_import_origin")
        else:
            evidence.add("unknown")
    if evidence == {"internal"}:
        return "internal_ambiguous_unresolved", "+".join(sorted(reasons))
    if evidence == {"external"}:
        return "external_builtin", "+".join(sorted(reasons))
    return "unknown_boundary", "unknown_rebound_or_mixed_namespace_binding"


class ImportOrigins(ast.NodeVisitor):
    """Locate import scopes in base AST; delegate import representation to Indexer."""
    def __init__(self, graph, path, module_id):
        self.graph, self.path, self.scope = graph, path, module_id
        self.locations = graph.followup_locations[path]

    def definition(self, node):
        previous = self.scope
        self.scope = self.locations[(node.lineno, node.col_offset)]
        for statement in node.body:
            self.visit(statement)
        self.scope = previous

    visit_FunctionDef = definition
    visit_AsyncFunctionDef = definition
    visit_ClassDef = definition

    def generic_visit(self, node):
        # Imports only occur in statement suites, never inside expressions.
        # Do not walk irrelevant expression trees just to recover import origins.
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                self.visit(child)

    def visit_Import(self, node):
        Indexer(self.graph, self.scope).visit_Import(node)

    def visit_ImportFrom(self, node):
        Indexer(self.graph, self.scope).visit_ImportFrom(node)


def archive_python(archive):
    entries = sorted((e for e in archive.getmembers() if e.isfile() and e.name.endswith(".py")),
                     key=lambda e: e.name)
    modules = set()
    for entry in entries:
        parts = list(PurePosixPath(entry.name).relative_to("testbed").with_suffix("").parts)
        if parts[0] in {"src", "lib"}:
            parts = parts[1:]
        if parts[-1] == "__init__":
            parts.pop()
        for index in range(1, len(parts) + 1):
            modules.add(".".join(parts[:index]))
    return entries, modules


def diagnose_stop(archive, entries, row):
    """Replay AST counting only, matching the original per-file checkpoint order."""
    total, parsed = 0, 0
    for entry in entries:
        if entry.size > LIMITS["source_blob_bytes"]:
            continue
        payload = archive.extractfile(entry).read()
        try:
            tree = ast.parse(payload, filename=entry.name.removeprefix("testbed/"))
        except (SyntaxError, UnicodeError, ValueError, RecursionError):
            continue
        before, crossed = total, None
        file_nodes = 0
        for index, node in enumerate(ast.walk(tree)):
            total += 1
            file_nodes += 1
            if crossed is None and index % 4096 == 0 and total > LIMITS["ast_nodes"]:
                crossed = (total, file_nodes)
        if crossed is None and total > LIMITS["ast_nodes"]:
            crossed = (total, file_nodes)
        if crossed:
            if crossed[0] != int(row["ast_nodes"]) or parsed != int(row["parsed_files"]):
                raise ValueError("counter replay disagrees with stored resource stop")
            return dict(instance_id=row["instance_id"], path=entry.name.removeprefix("testbed/"),
                        limit=LIMITS["ast_nodes"], limit_scope="cumulative_per_task_inspected_ast_nodes",
                        nodes_before_file=before, file_ast_nodes=file_nodes,
                        nodes_inspected_in_stopping_file=crossed[1], observed_stop_counter=crossed[0],
                        file_bytes=entry.size, file_sha256=hashlib.sha256(payload).hexdigest(),
                        evidence_status="inferred_exact_base_archive_ast_counter_replay")
        parsed += 1
    raise ValueError("could not reproduce stored AST limit counter")


def calls_for_task(task, row):
    directory = OUT / "graphs" / task["instance_id"]
    nodes = {n["id"]: n for n in records(directory / "nodes.jsonl.gz")}
    scopes = {s["id"]: s for s in records(directory / "scopes.jsonl.gz")}
    needed = {s["path"] for s in scopes.values() if any(
        kind == "unknown" and value == "external_or_missing_module_attribute"
        for refs in s["bindings"].values() for kind, value in refs)}
    graph = Graph()
    graph.nodes = nodes
    graph.followup_locations = defaultdict(dict)
    for node in nodes.values():
        if node["kind"] != "module":
            graph.followup_locations[node["path"]][(node["line"], node["column"])] = node["id"]
    graph.scopes = {sid: dict(scope, bindings=defaultdict(list)) for sid, scope in scopes.items()}
    raw_imports = {}
    with tarfile.open(task["archive_path"], "r:") as archive:
        if archive.pax_headers.get("comment") != task["base_commit"]:
            raise ValueError("archive base commit mismatch")
        entries, modules = archive_python(archive)
        if row["graph_status"] == "resource_limited":
            return None, diagnose_stop(archive, entries, row)
        module_ids = {n["path"]: n["id"] for n in nodes.values() if n["kind"] == "module"}
        for entry in entries:
            path = entry.name.removeprefix("testbed/")
            if path not in needed or path not in module_ids:
                continue
            tree = ast.parse(archive.extractfile(entry).read(), filename=path)
            ImportOrigins(graph, path, module_ids[path]).visit(tree)
        raw_imports = {sid: scope["bindings"] for sid, scope in graph.scopes.items() if scope["bindings"]}
    counts, reasons = Counter(), Counter()
    for edge in records(directory / "edges.jsonl.gz"):
        bucket, reason = classify_call(edge, scopes, raw_imports, modules)
        counts[bucket] += 1
        reasons[(bucket, reason)] += 1
    if sum(counts.values()) != int(row["edge_records"]):
        raise ValueError("boundary classification does not partition recorded call sites")
    return ({"instance_id": task["instance_id"], "repo": task["repo"], "graph_status": row["graph_status"],
             "classified_call_sites": sum(counts.values()), **{key: counts[key] for key in BUCKETS},
             "reason_counts": {bucket + ":" + reason: count for (bucket, reason), count in reasons.items()}}, None)


def verify_baseline():
    manifest = json.loads((OUT / "graph_inputs.json").read_text())
    for section in ("code_sha256", "input_sha256"):
        for path, expected in manifest[section].items():
            payload = (ROOT / path).read_bytes()
            if path.endswith("/design.md"):
                payload = payload.split(AMENDMENT)[0]
            if hashlib.sha256(payload).hexdigest() != expected:
                raise ValueError("accepted baseline input/code changed: " + path)
    for path, expected in manifest["output_sha256"].items():
        if digest(OUT / path) != expected:
            raise ValueError("accepted graph artifact changed: " + path)
    return manifest


def main():
    verify_baseline()
    acquisition = json.loads((OUT / "inputs.json").read_text())
    with (OUT / "base_feasibility.csv").open(newline="") as stream:
        rows = {r["instance_id"]: r for r in csv.DictReader(stream)}
    with (ROOT / "reports/v2_diagnostic/patches.csv").open(newline="") as stream:
        members = {r["instance_id"]: {k: r[k] for k in ("instance_id", "source_run", "artifact_kind")}
                   for r in csv.DictReader(stream)}
    snapshot = candidate_projection(ROOT / "reports/failure_analysis/extracted.json")
    calls, stops, partials, symbols = [], [], [], []
    archive_hashes = {}
    for task in acquisition["tasks"]:
        iid = task["instance_id"]
        row = rows[iid]
        actual = digest(Path(task["archive_path"]))
        if actual != task["archive_sha256"]:
            raise ValueError("archive SHA-256 mismatch")
        archive_hashes[iid] = actual
        cache_dir = OUT / "followup_cache"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / (iid + ".json")
        cache_key = hashlib.sha256((digest(Path(__file__)) + actual + json.dumps(row, sort_keys=True) +
                                    digest(OUT / "graphs" / iid / "diagnostics.json")).encode()).hexdigest()
        cached = json.loads(cache_path.read_text()) if cache_path.is_file() else {}
        if cached.get("input_key") == cache_key:
            call, stop = cached["call"], cached["stop"]
        else:
            call, stop = calls_for_task(task, row)
            write_json(cache_path, dict(input_key=cache_key, call=call, stop=stop))
        if call:
            calls.append(call)
        if stop:
            stops.append(stop)
        directory = OUT / "graphs" / iid
        diagnostic = json.loads((directory / "diagnostics.json").read_text())
        if row["graph_status"] == "partial":
            for failure in diagnostic["parse_and_resource_failures"]:
                partials.append(dict(instance_id=iid, repo=task["repo"], **failure))
        stored_symbols = json.loads((directory / "changed_symbols.json").read_text())["symbols"]
        if row["patch_status"] == "available" and row["graph_status"] != "resource_limited":
            payload, _ = candidate(task, members[iid], snapshot)
            if hashlib.sha256(payload).hexdigest() != row["patch_sha256"]:
                raise ValueError("candidate differs from accepted diagnostic")
            changes = {c.path: c for c in parse_patch(payload)}
            for symbol in stored_symbols:
                if symbol["name"] is None:
                    continue
                symbols.append(dict(instance_id=iid, repo=task["repo"], provenance=row["patch_provenance"],
                                    path=symbol["path"], name=symbol["name"], status=symbol["status"],
                                    origin=symbol_origin(symbol, changes.get(symbol["path"])),
                                    baseline_reason=symbol["reason"]))
        print(json.dumps(dict(instance_id=iid, call_boundary="classified" if call else "resource_limit_diagnosed")), flush=True)
    if len(stops) != 4 or len({p["instance_id"] for p in partials}) != 23:
        raise ValueError("follow-up population mismatch")
    write_csv(OUT / "call_resolution_by_task.csv", [{k: v for k, v in r.items() if k != "reason_counts"} for r in calls])
    write_csv(OUT / "sympy_limit_stops.csv", stops)
    write_csv(OUT / "partial_graph_files.csv", partials,
              ["instance_id", "repo", "path", "reason", "line", "message"])
    write_csv(OUT / "changed_symbol_origins.csv", symbols)
    repositories = []
    for source in acquisition["repositories"]:
        subset = [r for r in calls if r["repo"] == source["repo"]]
        repositories.append(dict(repo=source["repo"], tasks_with_call_classification=len(subset),
                                 **{key: sum(r[key] for r in subset) for key in BUCKETS}))
    write_csv(OUT / "call_resolution_by_repository.csv", repositories)
    symbol_summaries = []
    for group in ["all", "confirmed_study_snapshot", "local_final_identity_unverified"]:
        subset = [s for s in symbols if group == "all" or s["provenance"] == group]
        for exclude_new in (False, True):
            measured = [s for s in subset if not exclude_new or s["origin"] != "newly_added_name_absent_at_base"]
            counts = Counter(s["status"] for s in measured)
            symbol_summaries.append(dict(provenance=group, exclude_newly_added=exclude_new,
                                         total=len(measured), resolved=counts["resolved"], ambiguous=counts["ambiguous"],
                                         unresolved=counts["unresolved"], resolution_rate=counts["resolved"] / len(measured) if measured else None))
    write_csv(OUT / "changed_symbol_rates.csv", symbol_summaries)
    summary = dict(baseline_commit="f8c610d1db485f7078172627dfc9aa2bdbe22d28", tasks=83,
                   per_repository=repositories, total_calls={key: sum(r[key] for r in calls) for key in BUCKETS},
                   call_boundary_reason_counts=dict(sum((Counter(r["reason_counts"]) for r in calls), Counter())),
                   sympy_stops=stops, changed_symbol_rates=symbol_summaries,
                   partial_graph_count=23, partial_file_rows=len(partials),
                   archive_sha256=archive_hashes, graph_rebuild=False, oracle_access=False,
                   source_handling="AST import metadata and counter replay from verified tar members; never imported/executed")
    write_json(OUT / "followup_summary.json", summary)
    render_report(summary, partials, symbols)
    outputs = ["report.md", "partial_graphs.md", "followup_summary.json", "call_resolution_by_task.csv",
               "call_resolution_by_repository.csv", "sympy_limit_stops.csv", "partial_graph_files.csv",
               "changed_symbol_origins.csv", "changed_symbol_rates.csv"]
    write_json(OUT / "followup_inputs.json", dict(
        command="env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/followup_analysis.py",
        baseline_graph_inputs_sha256=digest(OUT / "graph_inputs.json"),
        code_sha256={p.name: digest(p) for p in (Path(__file__), OUT / "followup_report.py", OUT / "test_static_graph.py")},
        current_design_sha256=digest(OUT / "design.md"), amendment_applied=False,
        output_sha256={p: digest(OUT / p) for p in outputs}))


def render_report(summary, partials, symbols):
    # Defined below; separated from all source/artifact inspection.
    from followup_report import render
    render(summary, partials, symbols)


if __name__ == "__main__":
    main()
