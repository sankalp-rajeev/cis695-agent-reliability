"""Steps 1–3 only: four amended graphs, then 83 frozen-candidate seed inventories.

Never select tests, import benchmark code, use Docker/network, or read oracle
fields. Original graph directories remain byte-for-byte unchanged. A versioned
graph manifest overlays the four new SymPy graphs on the original 79.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter
from pathlib import Path

from build_graphs import OUT, ROOT, changed_symbols, digest, extract, jsonlines, write_json
from amended_graph import AmendedGraph, PREFLIGHT_LIMIT, RETAINED_LIMIT
from static_graph import Graph
from followup_analysis import records, side_names
from reliability.verifier.patch import parse_patch
from reliability.verifier.integrity import is_test_file

WORK = OUT / "amendment2_72ad21b"
SYMPY = {"sympy__sympy-13480", "sympy__sympy-14711", "sympy__sympy-17318", "sympy__sympy-19783"}


def write_csv(path, rows, fields=None):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields or list(dict.fromkeys(k for r in rows for k in r)), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cohort():
    with (ROOT / "reports/v2_diagnostic/patches.csv").open(newline="") as stream:
        result = {r["instance_id"]: {k: r[k] for k in
                  ("instance_id", "repo", "source_run", "artifact_kind", "v2_outcome")}
                  for r in csv.DictReader(stream)}
    if len(result) != 83:
        raise ValueError("expected frozen 83-task cohort")
    return result


def verify_design():
    verification = json.loads((WORK / "design_verification.json").read_text())
    actual = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if actual != verification["commit"] or digest(OUT / "design.md") != verification["design_sha256"]:
        raise ValueError("committed design changed during this run")
    return verification


def verify_original_graphs():
    expected = json.loads((WORK / "original_graph_hashes.json").read_text())
    for iid, paths in expected.items():
        actual_paths = {str(p.relative_to(OUT)) for p in (OUT / "graphs" / iid).iterdir() if p.is_file()}
        if actual_paths != set(paths):
            raise ValueError("original graph directory membership changed: " + iid)
        for path, sha in paths.items():
            if digest(OUT / path) != sha:
                raise ValueError("original graph artifact changed: " + path)
    return dict(status="passed", unchanged_other_tasks=79, unchanged_original_tasks_including_old_sympy=83,
                compared_files=sum(len(r) for r in expected.values()))


def verified_patches(members, export=None):
    if export is None:
        directory = Path.home() / "frozen_patches_export"
        export = directory if directory.is_dir() else ROOT / "frozen_patches_export.tgz"
    if export.is_dir():
        manifest_bytes = (export / "manifest.csv").read_bytes()
        def payload(iid):
            return (export / (iid + ".patch")).read_bytes()
        container_sha = None
        archive = None
    else:
        archive = tarfile.open(export, "r:gz")
        names = archive.getnames()
        if len(names) != len(set(names)):
            raise ValueError("duplicate export archive members")
        manifest_bytes = archive.extractfile("frozen_patches_export/manifest.csv").read()
        def payload(iid):
            member = archive.getmember("frozen_patches_export/" + iid + ".patch")
            if not member.isfile():
                raise ValueError("candidate archive member is not regular")
            return archive.extractfile(member).read()
        container_sha = digest(export)
    manifest = list(csv.DictReader(io.StringIO(manifest_bytes.decode())))
    if len(manifest) != 83 or {r["instance_id"] for r in manifest} != set(members):
        raise ValueError("patch export differs from frozen population")
    patches, metadata = {}, []
    previous = {r["instance_id"]: r["actual_sha256"] for r in
                json.loads((OUT / "patch_export_verification_83.json").read_text())["tasks"]}
    try:
        for row in manifest:
            iid = row["instance_id"]
            if row["csv_source_run"] != members[iid]["source_run"] or row["is_final_study_patch"] != "yes":
                raise ValueError("export final-study source run mismatch: " + iid)
            candidate = payload(iid)
            sha = "sha256:" + hashlib.sha256(candidate).hexdigest()
            if sha != row["sha256"] or sha != previous[iid]:
                raise ValueError("frozen candidate hash mismatch: " + iid)
            patches[iid] = candidate
            metadata.append(dict(instance_id=iid, repo=members[iid]["repo"], source_run=row["csv_source_run"],
                                 export_source_run_raw=row["source_run"], patch_sha256=sha,
                                 size_bytes=len(candidate), hash_verified=True, confirmed_final_study_patch=True,
                                 manifest_status=row["status"], manifest_notes=row["notes"]))
    finally:
        if archive is not None:
            archive.close()
    write_csv(WORK / "verified_patch_manifest.csv", metadata)
    write_json(WORK / "patch_verification.json", dict(status="passed", tasks=83, export_path=str(export.resolve()),
        export_sha256=container_sha, manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        source_run_rule="csv_source_run matched to committed 83-task cohort; raw rerun aliases retained separately",
        manifest_status_counts=dict(Counter(r["manifest_status"] for r in metadata))))
    return patches, {r["instance_id"]: r for r in metadata}


def rebuild(task):
    iid = task["instance_id"]
    if iid not in SYMPY:
        raise ValueError("only four requested SymPy graphs may be rebuilt")
    directory = WORK / "graphs" / iid
    if (directory / "diagnostics.json").exists():
        raise ValueError("versioned graph already exists; no automatic rebuild/retry: " + iid)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="cis695-cg-amend2-", dir="/tmp") as temporary:
        archive_sha, skipped = extract(task, Path(temporary))
        extraction_seconds = time.monotonic() - started
        graph = AmendedGraph(started=started).build(Path(temporary) / "testbed")
    if skipped:
        for item in skipped:
            if item["path"].endswith(".py"):
                graph.failures.append(item)
                graph.files[item["path"]] = "omitted_archive_link"
                graph.counts["omitted_files"] += 1
        if graph.failures and graph.status == "complete":
            graph.status = "partial"
    directory.mkdir(parents=True, exist_ok=False)
    jsonlines(directory / "nodes.jsonl.gz", graph.nodes.values())
    jsonlines(directory / "edges.jsonl.gz", graph.edges)
    jsonlines(directory / "scopes.jsonl.gz", (dict(id=sid, **{k: sorted(v) if isinstance(v, set) else v
                                                            for k, v in scope.items()})
                                              for sid, scope in graph.scopes.items()))
    inventory = [dict(r, graph_file_status=graph.files.get(r["path"], "not_indexed")) for r in graph.preflight_records]
    write_csv(directory / "file_inventory.csv", inventory)
    omissions = [dict(r, is_test_file=is_test_file(r["path"])) for r in graph.omissions]
    write_csv(directory / "omitted_files.csv", omissions)
    if graph.status != "resource_limited" and graph.counts["call_sites"] != len(graph.edges):
        raise ValueError("unaccounted AST call sites in amended graph")
    row = dict(instance_id=iid, repo=task["repo"], source_run=task["source_run"], base_commit=task["base_commit"],
               graph_status=graph.status, archive_sha256=archive_sha, base_python_sha256=graph.base_digest.hexdigest(),
               **{k: graph.counts[k] for k in ("python_files", "source_bytes", "parsed_files", "parse_failures", "omitted_files",
                                              "ast_nodes", "retained_ast_nodes", "definitions", "call_sites", "nodes", "edge_records",
                                              "resolved_edges", "ambiguous_edges", "unresolved_edges")},
               preflight_complete=graph.preflight_complete, preflight_ast_nodes=graph.counts["ast_nodes"],
               indexing_visits=graph.indexing_visits, indexing_visit_metric="calls to ast.NodeVisitor.visit over retained trees",
               ast_parse_passes=1, retained_ast_reuse=True, reparsed_for_indexing=False,
               hash_extraction_seconds=round(extraction_seconds, 6),
               graph_runtime_seconds=round(graph.runtime, 6), stage_seconds=graph.stage_seconds,
               wall_limit_seconds=600, preflight_limit=PREFLIGHT_LIMIT, retained_limit=RETAINED_LIMIT)
    diagnostic = dict(row=row, parse_and_resource_failures=graph.failures, skipped_archive_members=skipped,
                      node_kind_counts=dict(Counter(n["kind"] for n in graph.nodes.values())),
                      edge_reason_counts=dict(Counter(e["reason"] for e in graph.edges)),
                      artifact_sha256={p.name: digest(p) for p in sorted(directory.iterdir())})
    write_json(directory / "diagnostics.json", diagnostic)
    print(json.dumps(row, sort_keys=True), flush=True)
    return diagnostic


def graph_files(directory, task):
    """Exact base-file existence plus stored parse/omission states, no source execution."""
    if digest(Path(task["archive_path"])) != task["archive_sha256"]:
        raise ValueError("base archive hash mismatch")
    with tarfile.open(task["archive_path"], "r:") as archive:
        if archive.pax_headers.get("comment") != task["base_commit"]:
            raise ValueError("base archive commit mismatch")
        states = {m.name.removeprefix("testbed/"): "unindexed" for m in archive.getmembers()
                  if m.name.endswith(".py") and m.name.startswith("testbed/")}
    inventory = directory / "file_inventory.csv"
    if inventory.exists():
        with inventory.open(newline="") as stream:
            states.update({r["path"]: r["graph_file_status"] for r in csv.DictReader(stream)})
    diagnostic = json.loads((directory / "diagnostics.json").read_text())
    for failure in diagnostic["parse_and_resource_failures"]:
        if not failure.get("path"):
            continue
        reason = failure["reason"]
        state = "omitted_largest_first" if reason == "largest_first_retained_ast_quota" else (
            "parse_failure" if reason in {"SyntaxError", "UnicodeError", "ValueError", "RecursionError"} else "omitted_" + reason)
        states[failure["path"]] = state
    return states, diagnostic


def name_origin(symbol, change):
    if symbol["targets"]:
        return "base_name_present"
    absent = symbol["reason"] in {"symbol_absent_at_base_or_diff_context_name", "base_file_absent"}
    if absent and symbol["name"] in side_names(change, "added") and symbol["name"] not in side_names(change, "removed"):
        return "newly_added_name_absent_at_base"
    return "not_established"


def resolve_task(task, member, patch, provenance, directory):
    graph = Graph()
    graph.files, diagnostic = graph_files(directory, task)
    graph.nodes = {n["id"]: n for n in records(directory / "nodes.jsonl.gz")}
    for node in graph.nodes.values():
        if node["kind"] == "module":
            graph.files[node["path"]] = "parsed"
    graph.status = diagnostic["row"]["graph_status"]
    row = dict(instance_id=task["instance_id"], repo=task["repo"], source_run=member["source_run"],
               patch_sha256=provenance["patch_sha256"], patch_confirmed=True,
               manifest_status=provenance["manifest_status"], manifest_notes=provenance["manifest_notes"],
               historical_cohort=member["artifact_kind"], v2_outcome=member["v2_outcome"],
               graph_directory=str(directory.relative_to(OUT)), graph_status=graph.status,
               resolution_status="measured" if graph.status == "complete" else "measured_on_partial_graph")
    if graph.status == "resource_limited":
        row["resolution_status"] = "not_available_resource_limited"
        return row, []
    try:
        parsed = parse_patch(patch)
        changes = {c.path: c for c in parsed}
        symbols = changed_symbols(patch, graph)
    except ValueError as exc:
        row.update(resolution_status="patch_parse_failure", error=str(exc)[:240])
        return row, []
    named = []
    for item in symbols:
        if item["name"] is None:
            continue
        named.append(dict(instance_id=task["instance_id"], repo=task["repo"], source_run=member["source_run"],
                          **item, origin=name_origin(item, changes[item["path"]]),
                          origin_evidence="inferred_from_base_graph/file_existence_and_frozen_candidate_diff"))
    counts = Counter(s["status"] for s in named)
    remaining = [s for s in named if s["origin"] != "newly_added_name_absent_at_base"]
    excluded_counts = Counter(s["status"] for s in remaining)
    row.update(names_total=len(named), names_resolved=counts["resolved"], names_ambiguous=counts["ambiguous"],
               names_unresolved=counts["unresolved"], newly_added_names=len(named) - len(remaining),
               resolution_rate=counts["resolved"] / len(named) if named else "",
               excluding_new_total=len(remaining), excluding_new_resolved=excluded_counts["resolved"],
               excluding_new_ambiguous=excluded_counts["ambiguous"], excluding_new_unresolved=excluded_counts["unresolved"],
               excluding_new_resolution_rate=excluded_counts["resolved"] / len(remaining) if remaining else "",
               unresolved_reasons=json.dumps(dict(Counter(s["reason"] for s in named if s["status"] != "resolved")), sort_keys=True),
               no_name_production_files=json.dumps([s["path"] for s in symbols if s["name"] is None]))
    allowed_reasons = {"SyntaxError", "UnicodeError", "ValueError", "RecursionError", "largest_first_retained_ast_quota"}
    reasons = diagnostic["parse_and_resource_failures"]
    row["primary_eligible"] = graph.status == "complete" and counts["resolved"] > 0
    row["extended_partial_eligible"] = (graph.status == "partial" and bool(reasons) and
        all(f["reason"] in allowed_reasons for f in reasons) and counts["resolved"] > 0)
    return row, named


def aggregate(task_rows, repositories):
    totals = []
    for repo in [*repositories, "ALL"]:
        rows = [r for r in task_rows if repo == "ALL" or r["repo"] == repo]
        row = dict(repo=repo, tasks=len(rows), measured_tasks=sum(r["resolution_status"].startswith("measured") for r in rows),
                   complete_graphs=sum(r["graph_status"] == "complete" for r in rows),
                   partial_graphs=sum(r["graph_status"] == "partial" for r in rows),
                   primary_eligible_tasks=sum(r.get("primary_eligible", False) for r in rows),
                   extended_partial_eligible_tasks=sum(r.get("extended_partial_eligible", False) for r in rows))
        for key in ("names_total", "names_resolved", "names_ambiguous", "names_unresolved", "newly_added_names",
                    "excluding_new_total", "excluding_new_resolved", "excluding_new_ambiguous", "excluding_new_unresolved"):
            row[key] = sum(r.get(key, 0) for r in rows)
        row["resolution_rate"] = row["names_resolved"] / row["names_total"] if row["names_total"] else ""
        row["excluding_new_resolution_rate"] = row["excluding_new_resolved"] / row["excluding_new_total"] if row["excluding_new_total"] else ""
        totals.append(row)
    return totals


def package(path):
    """Immediate dotted module parent using the graph's existing src/lib convention."""
    parts = list(Path(path).with_suffix("").parts)
    if parts[0] in {"src", "lib"}:
        parts = parts[1:]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts[:-1])


def omission_annotations(mapping, symbols):
    rows = []
    for iid in sorted(SYMPY):
        changed_paths = sorted({s["path"] for s in symbols if s["instance_id"] == iid})
        changed_packages = {package(p) for p in changed_paths}
        with (mapping[iid] / "omitted_files.csv").open(newline="") as stream:
            for row in csv.DictReader(stream):
                parent = package(row["path"])
                rows.append(dict(instance_id=iid, **row, package=parent,
                    changed_packages=json.dumps(sorted(changed_packages)),
                    same_package_as_changed_symbol=parent in changed_packages,
                    matching_changed_paths=json.dumps([p for p in changed_paths if package(p) == parent]),
                    is_changed_source_file=row["path"] in changed_paths,
                    descendant_of_changed_package=any(parent.startswith(p + ".") for p in changed_packages),
                    annotation_provenance="post-ranking verified frozen candidate; existing symbol extractor"))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("verify", "rebuild", "resolve", "all"), default="all")
    parser.add_argument("--patch-export", type=Path)
    args = parser.parse_args()
    design = verify_design()
    verify_original_graphs()
    members = cohort()
    acquisition = json.loads((OUT / "inputs.json").read_text())
    tasks = {t["instance_id"]: t for t in acquisition["tasks"]}
    if set(tasks) != set(members):
        raise ValueError("acquisition/cohort identity mismatch")
    patches, provenance = verified_patches(members, args.patch_export)
    if args.stage == "verify":
        print("Verified all 83 frozen final-study patches.")
        return
    if args.stage in {"rebuild", "all"}:
        for iid in sorted(SYMPY):
            rebuild(tasks[iid])
        write_json(WORK / "graph_hash_verification.json", verify_original_graphs())
    mapping = {iid: WORK / "graphs" / iid if iid in SYMPY else OUT / "graphs" / iid for iid in members}
    if not all((p / "diagnostics.json").exists() for p in mapping.values()):
        raise ValueError("four amended graphs must exist before resolution")
    graph_manifest = {iid: dict(directory=str(p.relative_to(OUT)),
        graph_status=json.loads((p / "diagnostics.json").read_text())["row"]["graph_status"],
        artifact_sha256={f.name: digest(f) for f in sorted(p.iterdir()) if f.is_file()}) for iid, p in mapping.items()}
    write_json(WORK / "graph_manifest.json", graph_manifest)
    if args.stage == "rebuild":
        return
    task_rows, names = [], []
    for iid, member in members.items():
        row, symbols = resolve_task(tasks[iid], member, patches[iid], provenance[iid], mapping[iid])
        task_rows.append(row)
        names.extend(symbols)
        print(json.dumps(dict(instance_id=iid, graph_status=row["graph_status"],
                              resolution_status=row["resolution_status"], names_total=row.get("names_total"))), flush=True)
    repositories = [r["repo"] for r in acquisition["repositories"]]
    per_repo = aggregate(task_rows, repositories)
    write_csv(WORK / "task_resolution.csv", task_rows)
    write_csv(WORK / "changed_symbol_resolution.csv", [dict(s, targets=json.dumps(s["targets"])) for s in names])
    write_csv(WORK / "repository_resolution.csv", per_repo)
    write_csv(WORK / "omission_annotations.csv", omission_annotations(mapping, names))
    feasibility = []
    for row in task_rows:
        diagnostic = json.loads((mapping[row["instance_id"]] / "diagnostics.json").read_text())["row"]
        feasibility.append({**diagnostic, **row})
    write_csv(WORK / "base_feasibility.csv", feasibility)
    summary = dict(design_commit=design["commit"], tasks=83, confirmed_export_patches=83,
                   graph_status_counts=dict(Counter(r["graph_status"] for r in task_rows)),
                   resolution_status_counts=dict(Counter(r["resolution_status"] for r in task_rows)),
                   totals=per_repo[-1], per_repository=per_repo[:-1],
                   original_graph_hash_verification=verify_original_graphs(), selectors_run=False, oracle_access=False)
    write_json(WORK / "resolution_summary.json", summary)
    from rebuild_report import render
    render(WORK, summary, graph_manifest, task_rows)
    verify_design()
    inputs = dict(command=shlex.join(["env", "-u", "PYTHONPATH", ".venv/bin/python", "-B",
                                     "reports/callgraph_selection/rebuild_and_resolve.py", *sys.argv[1:]]),
                  design_commit=design["commit"], design_sha256=design["design_sha256"], python_version=sys.version,
                  code_sha256={p.name: digest(p) for p in (Path(__file__), OUT / "amended_graph.py", OUT / "static_graph.py",
                                                        OUT / "build_graphs.py", OUT / "followup_analysis.py", OUT / "rebuild_report.py",
                                                        OUT / "test_amended_graph.py", OUT / "test_static_graph.py",
                                                        OUT / "validate_amendment2.py")},
                  acquisition_manifest_sha256=digest(OUT / "inputs.json"),
                  graph_manifest_sha256=digest(WORK / "graph_manifest.json"),
                  frozen_patch_verification_sha256=digest(WORK / "patch_verification.json"),
                  output_sha256={str(p.relative_to(WORK)): digest(p) for p in sorted(WORK.rglob("*"))
                                 if p.is_file() and p.name not in {"inputs.json", "run.log", "tests.txt"}})
    write_json(WORK / "inputs.json", inputs)
    print(json.dumps(summary["totals"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
