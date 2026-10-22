"""Phase 1b: verified archives -> AST graphs and diagnostics, never selectors.

Run from the project root with .venv/bin/python -B. Only our own verifier's
existing patch parser/symbol extractor is imported; benchmark code is AST data.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shlex
import sys
import tarfile
import tempfile
import time
from collections import Counter
from pathlib import Path, PurePosixPath

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reliability.agent.freeze import FrozenPatch, read_patch
from reliability.verifier.patch import Patch, parse_patch, touched_symbols
from reliability.verifier.integrity import is_test_file
from static_graph import Graph, LIMITS


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def skip_json(text, offset):
    """Skip unwanted JSON values without decoding/materializing their contents."""
    offset = whitespace(text, offset)
    if text[offset] == '"':
        offset += 1
        while text[offset] != '"':
            offset += 2 if text[offset] == "\\" else 1
        return offset + 1
    if text[offset] in "[{":
        end = "]" if text[offset] == "[" else "}"
        offset += 1
        while True:
            offset = whitespace(text, offset)
            if text[offset] == end:
                return offset + 1
            if text[offset] in ",:":
                offset += 1
            else:
                offset = skip_json(text, offset)
    while offset < len(text) and text[offset] not in ",]} \r\n\t":
        offset += 1
    return offset


def whitespace(text, offset):
    while offset < len(text) and text[offset].isspace():
        offset += 1
    return offset


def object_items(text, offset):
    decoder = json.JSONDecoder()
    offset = whitespace(text, offset)
    if text[offset] != "{":
        raise ValueError("expected JSON object")
    offset += 1
    while True:
        offset = whitespace(text, offset)
        if text[offset] == "}":
            return
        if text[offset] == ",":
            offset = whitespace(text, offset + 1)
        key, offset = decoder.raw_decode(text, offset)
        offset = whitespace(text, offset)
        if text[offset] != ":":
            raise ValueError("expected JSON key separator")
        offset = whitespace(text, offset + 1)
        yield key, offset
        offset = skip_json(text, offset)


def candidate_projection(path):
    """Mixed historical snapshot -> identity and agent_patch ONLY.

    Gold/test/oracle/issue/label values are lexically skipped, never JSON-decoded.
    No mixed-artifact record is passed to graph or changed-symbol functions.
    """
    text = path.read_text()
    decoder = json.JSONDecoder()
    result = {}
    for key, offset in object_items(text, 0):
        if key != "tasks":
            continue
        if text[offset] != "[":
            raise ValueError("expected snapshot tasks array")
        offset += 1
        while True:
            offset = whitespace(text, offset)
            if text[offset] == "]":
                break
            if text[offset] == ",":
                offset = whitespace(text, offset + 1)
            record = {name: decoder.raw_decode(text, start)[0]
                      for name, start in object_items(text, offset)
                      if name in {"instance_id", "source_run", "agent_patch"}}
            if set(record) != {"instance_id", "source_run", "agent_patch"}:
                raise ValueError("snapshot lacks whitelisted candidate identity")
            if record["instance_id"] in result:
                raise ValueError("duplicate snapshot candidate")
            result[record["instance_id"]] = record
            offset = skip_json(text, offset)
    return result


def candidate(task, member, snapshot):
    iid, run = task["instance_id"], task["source_run"]
    if member["artifact_kind"] == "study_snapshot":
        record = snapshot.get(iid)
        if record is None or record["source_run"] != run:
            raise ValueError("confirmed snapshot missing or run identity mismatch")
        return record["agent_patch"].encode(), dict(
            patch_status="available", patch_provenance="confirmed_study_snapshot",
            patch_artifact="reports/failure_analysis/extracted.json#tasks.agent_patch",
            original_frozen_hash_status="not_available_in_snapshot")
    directory = ROOT / "runs" / run / "tasks" / iid
    patch, record = directory / "patch.diff", directory / "repair_record.json"
    if not patch.is_file() or not record.is_file():
        return None, dict(patch_status="patch missing", patch_provenance="missing",
                          patch_artifact="", original_frozen_hash_status="missing")
    metadata = json.loads(record.read_text())
    if metadata["instance_id"] != iid or metadata["experiment_id"] != run:
        raise ValueError("local frozen candidate identity mismatch")
    frozen = metadata["patch"]
    if frozen["path"] != f"tasks/{iid}/patch.diff":
        raise ValueError("unexpected frozen patch path")
    payload = read_patch(FrozenPatch(patch, frozen["sha256"], frozen["size_bytes"]))
    if len(payload) != frozen["size_bytes"]:
        raise ValueError("frozen patch size mismatch")
    return payload, dict(patch_status="available", patch_provenance="local_final_identity_unverified",
                         patch_artifact=str(patch.relative_to(ROOT)),
                         original_frozen_hash_status="verified_local_hash_not_final_run_identity",
                         repair_record_sha256=digest(record))


def extract(task, destination):
    archive = Path(task["archive_path"])
    actual = digest(archive)
    if actual != task["archive_sha256"]:
        raise ValueError("archive SHA-256 differs from acquisition")
    skipped, seen = [], set()
    with tarfile.open(archive, "r:") as stream:
        if stream.pax_headers.get("comment") != task["base_commit"]:
            raise ValueError("archive PAX commit differs from verified base")
        for entry in stream:
            path = PurePosixPath(entry.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "testbed":
                raise ValueError("unsafe or unexpected archive member path")
            target = destination.joinpath(*path.parts)
            if entry.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif entry.isfile():
                if entry.name in seen:
                    raise ValueError("duplicate archive file")
                seen.add(entry.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                # Never restore executable bits, ownership, timestamps or links.
                with stream.extractfile(entry) as source, target.open("wb") as sink:
                    while chunk := source.read(1024 * 1024):
                        sink.write(chunk)
            else:
                skipped.append(dict(path=str(path.relative_to("testbed")),
                                    reason="archive_link_or_special_file_not_followed"))
    return actual, skipped


def changed_symbols(payload, graph):
    """Reuse production parsing/extraction, exact file + simple-name matching."""
    patch = parse_patch(payload)
    index = {}
    for node in graph.nodes.values():
        if node["kind"] != "module":
            key = (node["path"], node["qualname"].rsplit(".", 1)[-1])
            index.setdefault(key, []).append(node["id"])
    result = []
    for change in patch:
        if not change.path.endswith(".py") or is_test_file(change.path) or change.is_binary:
            continue
        base_path = change.old_path or change.path
        names = touched_symbols(Patch(files=(change,), raw=""))
        for name in names:
            targets = index.get((base_path, name), [])
            file_status = graph.files.get(base_path, "absent")
            if file_status != "parsed":
                status, reason = "unresolved", "base_file_" + file_status
            elif len(targets) == 1:
                status, reason = "resolved", "unique_file_and_simple_name"
            elif targets:
                status, reason = "ambiguous", "multiple_same_name_definitions_in_file"
            else:
                status, reason = "unresolved", "symbol_absent_at_base_or_diff_context_name"
            result.append(dict(path=change.path, base_path=base_path, name=name,
                               status=status, reason=reason, targets=targets))
        if not names:
            # A file without extractor names is not an invented module seed.
            result.append(dict(path=change.path, base_path=base_path, name=None,
                               status="no_extracted_symbol", reason="existing_extractor_returned_no_names", targets=[]))
    return result


def jsonlines(path, records):
    with path.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
        for record in records:
            zipped.write((json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())


def build_task(task, member, snapshot):
    started = time.monotonic()
    directory = OUT / "graphs" / task["instance_id"]
    directory.mkdir(parents=True, exist_ok=True)
    payload, provenance = candidate(task, member, snapshot)
    row = {key: task[key] for key in ("instance_id", "repo", "source_run", "base_commit")}
    row.update(source_kind="local_clone_git_archive", source_path=task["archive_path"],
               source_status="verified_archive", historical_cohort=member["artifact_kind"], **provenance)
    if payload is not None:
        row["patch_sha256"] = hashlib.sha256(payload).hexdigest()
    with tempfile.TemporaryDirectory(prefix="cis695-cg-", dir="/tmp") as temporary:
        archive_sha, skipped = extract(task, Path(temporary))
        extraction_seconds = time.monotonic() - started
        graph = Graph().build(Path(temporary) / "testbed")
        # Tree is deleted on success and exceptions before graph artifacts persist.
    skipped_python = [entry for entry in skipped if entry["path"].endswith(".py")]
    if skipped_python:
        graph.failures.extend(skipped_python)
        graph.counts["omitted_files"] += len(skipped_python)
        if graph.status == "complete":
            graph.status = "partial"
    symbols, patch_error = [], None
    if payload is not None and graph.status != "resource_limited":
        try:
            symbols = changed_symbols(payload, graph)
        except ValueError as exc:
            patch_error = type(exc).__name__ + ": " + str(exc)[:200]
            row["patch_status"] = "patch parse failure"
    counts = Counter(item["status"] for item in symbols if item["name"] is not None)
    total = sum(counts.values())
    row.update({key: graph.counts[key] for key in (
        "python_files", "parsed_files", "parse_failures", "omitted_files", "source_bytes",
        "ast_nodes", "definitions", "call_sites", "nodes", "edge_records", "resolved_edges",
        "ambiguous_edges", "unresolved_edges")})
    row.update(graph_status=graph.status, archive_sha256=archive_sha,
               base_python_sha256=graph.base_digest.hexdigest(),
               graph_runtime_seconds=round(graph.runtime, 6),
               hash_and_extraction_seconds=round(extraction_seconds, 6),
               changed_symbol_resolution_status="skipped_patch_missing" if payload is None else
               "skipped_resource_limit" if graph.status == "resource_limited" else
               "patch_parse_failure" if patch_error else "measured_on_partial_graph" if graph.status != "complete" else "measured",
               changed_symbols_total=total if payload is not None and not patch_error and graph.status != "resource_limited" else "",
               changed_symbols_resolved=counts["resolved"] if payload is not None and not patch_error and graph.status != "resource_limited" else "",
               changed_symbols_ambiguous=counts["ambiguous"] if payload is not None and not patch_error and graph.status != "resource_limited" else "",
               changed_symbols_unresolved=counts["unresolved"] if payload is not None and not patch_error and graph.status != "resource_limited" else "",
               changed_symbol_resolution_rate=round(counts["resolved"] / total, 6) if total else "",
               changed_symbol_reasons=json.dumps(dict(Counter(s["reason"] for s in symbols if s["status"] != "resolved")), sort_keys=True))
    row["edge_resolution_status"] = "not_completed_resource_limit" if graph.status == "resource_limited" else "completed"
    if graph.status == "resource_limited":
        for key in ("resolved_edges", "ambiguous_edges", "unresolved_edges"):
            row[key] = ""
    jsonlines(directory / "nodes.jsonl.gz", graph.nodes.values())
    jsonlines(directory / "edges.jsonl.gz", graph.edges)
    scopes = (dict(id=sid, **{key: sorted(value) if isinstance(value, set) else value
                              for key, value in scope.items()}) for sid, scope in graph.scopes.items())
    jsonlines(directory / "scopes.jsonl.gz", scopes)
    write_json(directory / "changed_symbols.json", dict(patch_status=row["patch_status"],
                provenance=provenance, patch_sha256=row.get("patch_sha256"), error=patch_error, symbols=symbols))
    row["task_runtime_seconds"] = round(time.monotonic() - started, 6)
    diagnostic = dict(row=row, parse_and_resource_failures=graph.failures,
                      skipped_archive_members=skipped,
                      edge_reason_counts=dict(Counter(e["reason"] for e in graph.edges)),
                      node_kind_counts=dict(Counter(n["kind"] for n in graph.nodes.values())),
                      artifact_sha256={p.name: digest(p) for p in sorted(directory.iterdir())
                                       if p.name != "diagnostics.json"})
    write_json(directory / "diagnostics.json", diagnostic)
    return diagnostic


def summarize(diagnostics, acquisition):
    summary = []
    sums = ("python_files", "parsed_files", "parse_failures", "omitted_files", "nodes", "definitions",
            "call_sites", "edge_records", "resolved_edges", "ambiguous_edges", "unresolved_edges",
            "graph_runtime_seconds", "task_runtime_seconds", "changed_symbols_total", "changed_symbols_resolved",
            "changed_symbols_ambiguous", "changed_symbols_unresolved")
    for source in acquisition["repositories"]:
        tasks = [d for d in diagnostics if d["row"]["repo"] == source["repo"]]
        rows = [d["row"] for d in tasks]
        result = dict(repo=source["repo"], head=source["head"], tasks=len(rows),
                      graph_status_counts=dict(Counter(r["graph_status"] for r in rows)),
                      patch_status_counts=dict(Counter(r["patch_status"] for r in rows)),
                      patch_provenance_counts=dict(Counter(r["patch_provenance"] for r in rows)),
                      symbol_reason_counts=dict(sum((Counter(json.loads(r["changed_symbol_reasons"])) for r in rows), Counter())))
        result.update({key: sum(r.get(key, 0) or 0 for r in rows) for key in sums})
        result["changed_symbol_resolution_rate"] = (result["changed_symbols_resolved"] / result["changed_symbols_total"]
                                                     if result["changed_symbols_total"] else None)
        summary.append(result)
    return summary


def outputs(diagnostics, acquisition, command, sample):
    rows = [d["row"] for d in diagnostics]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    csvpath = OUT / ("sample_base_feasibility.csv" if sample else "base_feasibility.csv")
    with csvpath.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(diagnostics, acquisition)
    result = dict(phase="1b_AST_graph_only", command=command, sample=sample,
                  population=len(rows), graphs_constructed=len(rows),
                  graph_status_counts=dict(Counter(r["graph_status"] for r in rows)),
                  patch_status_counts=dict(Counter(r["patch_status"] for r in rows)),
                  patch_provenance_counts=dict(Counter(r["patch_provenance"] for r in rows)),
                  limits=LIMITS, per_repository=summary,
                  edge_reason_counts=dict(sum((Counter(d["edge_reason_counts"]) for d in diagnostics), Counter())),
                  benchmark_code_execution=False, test_execution=False, network_access=False,
                  oracle_analysis=False, selection=False)
    write_json(OUT / ("sample_feasibility.json" if sample else "feasibility.json"), result)
    code = [Path(__file__), OUT / "static_graph.py", OUT / "design.md",
            ROOT / "src/reliability/verifier/patch.py", ROOT / "src/reliability/verifier/integrity.py",
            ROOT / "src/reliability/agent/freeze.py"]
    inputs = [OUT / "inputs.json", ROOT / "reports/v2_diagnostic/patches.csv",
              ROOT / "reports/failure_analysis/extracted.json"]
    write_json(OUT / ("sample_graph_inputs.json" if sample else "graph_inputs.json"), dict(
        command=command, design_commit=acquisition["design_commit"],
        code_sha256={str(p.relative_to(ROOT)): digest(p) for p in code},
        input_sha256={str(p.relative_to(ROOT)): digest(p) for p in inputs},
        acquisition_metadata_preserved=True,
        snapshot_projection=["instance_id", "source_run", "agent_patch"],
        cohort_projection=["instance_id", "repo", "source_run", "artifact_kind"],
        tasks=[{k: r[k] for k in ("instance_id", "base_commit", "archive_sha256", "base_python_sha256", "patch_status", "patch_artifact")}
               | {"patch_sha256": r.get("patch_sha256"), "repair_record_sha256": r.get("repair_record_sha256")}
               for r in rows],
        output_sha256={str(p.relative_to(OUT)): digest(p) for r in rows for p in
                       sorted((OUT / "graphs" / r["instance_id"]).iterdir())}))
    if not sample:
        report(result, acquisition)
    return result


def report(result, acquisition):
    lines = ["# Phase 1b: base-only AST graph feasibility", "",
             f"Attempted graphs for **{result['population']}/83** frozen non-empty headline tasks. "
             f"Status counts: `{json.dumps(result['graph_status_counts'], sort_keys=True)}`.", "",
             "Sources are the user's already-acquired, exact-base-commit Git archives under "
             "`~/cg_repos/task_archives/`, rooted at `testbed/`. No clone/worktree is modified or read for code. "
             "Every archive SHA-256 and PAX commit was checked against the preserved acquisition `inputs.json`. "
             "Each tree was extracted into `/tmp/cis695-cg-*`, parsed only with Python 3.11 `ast`, and deleted "
             "before retaining graph outputs. Links and special files are never followed; omitted Python links make a graph partial.", "",
             f"Design pre-registration: `{acquisition['design_commit']}`. The committed `design.md` is unchanged. "
             "The later explicit acquisition/phase-1b instructions authorize archives and graph construction in phase 1. "
             "No selectors, reachability/ranking calculations, oracle analysis, benchmark imports/installations, network, Docker, "
             "or tests were run. All changes in this phase remain uncommitted; Git index/history were untouched.", "",
             "## Per repository", "",
             "Counts sum task snapshots, including repeated files/definitions across different bases; they are not unique-repo counts. "
             "Complete/partial/resource-limited counts retain all task denominators. Graph seconds exclude archive hashing/extraction "
             "and output serialization; total task seconds include them. Resource-limited tasks have blank edge-resolution and "
             "changed-symbol measurements, and contribute no such measurements to repository totals. Their inspected AST counts "
             "and retained prefix nodes remain diagnostic lower bounds. Definitions counted during AST inspection can exceed "
             "definitions actually indexed before a resource stop.", "",
             "| Repository | Tasks | Complete / partial / limited | Python files / parsed | Parse failures / omitted | Nodes | Resolved / ambiguous / unresolved edges | Changed symbols R / A / U | Resolution rate | Graph / total seconds |",
             "|---|---:|---|---|---|---:|---|---|---|---|"]
    for r in result["per_repository"]:
        if not r["tasks"]:
            lines.append(f"| {r['repo']} | 0 | — | — | — | — | — | — | — | — |")
            continue
        c = r["graph_status_counts"]
        rate = r["changed_symbol_resolution_rate"]
        lines.append(f"| {r['repo']} | {r['tasks']} | {c.get('complete',0)} / {c.get('partial',0)} / {c.get('resource_limited',0)} "
                     f"| {r['python_files']:,} / {r['parsed_files']:,} | {r['parse_failures']} / {r['omitted_files']} "
                     f"| {r['nodes']:,} | {r['resolved_edges']:,} / {r['ambiguous_edges']:,} / {r['unresolved_edges']:,} "
                     f"| {r['changed_symbols_resolved']} / {r['changed_symbols_ambiguous']} / {r['changed_symbols_unresolved']} "
                     f"| {rate:.1%}" if rate is not None else
                     f"| {r['repo']} | {r['tasks']} | {c.get('complete',0)} / {c.get('partial',0)} / {c.get('resource_limited',0)} "
                     f"| {r['python_files']:,} / {r['parsed_files']:,} | {r['parse_failures']} / {r['omitted_files']} "
                     f"| {r['nodes']:,} | {r['resolved_edges']:,} / {r['ambiguous_edges']:,} / {r['unresolved_edges']:,} "
                     "| — | —")
        lines[-1] += f" | {r['graph_runtime_seconds']:.2f} / {r['task_runtime_seconds']:.2f} |"
    lines += ["", "## Candidate provenance and changed symbols", "",
              f"Patch availability: `{json.dumps(result['patch_status_counts'], sort_keys=True)}`. "
              f"Provenance: `{json.dumps(result['patch_provenance_counts'], sort_keys=True)}`.", "",
              "Confirmed candidates are projected from the hash-pinned committed mixed failure-analysis snapshot using only "
              "`instance_id`, `source_run`, and `agent_patch`. All other JSON values are lexically skipped without decoding. "
              "No gold/official-test/oracle/issue values reach the graph or symbol functions. Snapshot candidate hashes are derived "
              "from the stored strings; original frozen repair hashes are unavailable there. Local candidates are read only from "
              "the exact cohort source-run path and verified using the existing frozen-patch reader, recorded SHA-256 and byte size. "
              "Their final-run identity remains unverified and exploratory. Missing patches do not prevent base graph builds, "
              "are explicitly `patch missing`, and have blank symbol totals/rates; no alternate run is substituted.", "",
              "Changed production Python paths use the existing `is_test_file`, `parse_patch`, and `touched_symbols`. "
              "Names are matched exactly within the changed base file (old path for renames). Duplicate simple names are ambiguous; "
              "no global matching or invented module seed is used. The extractor includes diff context/hunk names, so this is a "
              "diff-based inventory, not proof of semantic changes. New/absent symbols cannot be distinguished from unmatched "
              "context names without more evidence and are explicitly grouped. Rates are resolved/extracted names on available "
              "patches only, not on all 83 tasks; zero extracted names have a blank rate. Partial graph rates are marked as such.", "",
              "| Repository | Unresolved/ambiguous/no-name reasons |", "|---|---|"]
    for r in result["per_repository"]:
        lines.append(f"| {r['repo']} | `{json.dumps(r['symbol_reason_counts'], sort_keys=True)}` |")
    lines += ["", "## Graph interpretation and limits", "",
              "Each recorded edge is an AST call site with caller, path, line/column, expression, target candidates and reason. "
              "Only a single, unqualified static binding is resolved. Lexical names and explicit first-party imports/aliases are "
              "indexed; import cycles, rebinding, conditional definitions/imports, module collisions, custom decorators, "
              "inheritance and dynamic receiver dispatch retain uncertainty. All decorated targets (including possibly shadowed "
              "builtin decorators) are conservatively ambiguous. Calls inside comprehensions/lambdas/annotations are unresolved "
              "because their scope/evaluation is not modeled. Assignment-based aliases, instance types, inherited lookup, "
              "external libraries, star-import expansion, fixtures, reflection and monkey-patching are not inferred. "
              "Constructor calls may point to a class; there is no fabricated class-to-`__init__` edge. Module containment and "
              "imports are metadata, not call edges. Static resolution does not guarantee a runtime target.", "",
              "Syntax/encoding failures or omitted Python files make a graph **partial**, even if all remaining files build. "
              "The committed resource caps are unchanged, with exhausted builds marked resource-limited. Only complete graphs "
              "are eligible for a later primary comparison. Parse details and edge uncertainty histograms are retained per task.", "",
              "**Nothing in the primary evaluation confirms that a selected test exercises the changed code.** "
              "This phase provides no dynamic coverage, runtime-test behavior, correctness measurement or selector recommendation. "
              "A/B/C remains restricted to the 19 confirmed historical selections; any broader B analysis is a separate future phase.", "",
              "## Outputs and reproduction", "",
              "`base_feasibility.csv`: one row per task. `feasibility.json`: aggregate/per-repository metrics. "
              "`graphs/<instance_id>/`: compressed nodes, call edges, scope/import binding metadata, changed-symbol diagnostics, "
              "and parse/resource/provenance diagnostics. `graph_inputs.json`: code, inputs, archive, candidate, base-source and "
              "output SHA-256 hashes, plus the committed design revision. Acquisition `inputs.json` is preserved unchanged.", "",
              "```bash", result["command"], "```", "",
              "No test suite was executed under the no-test-execution constraint. Verification consists of archive/source hashes, "
              "PAX commit checks, AST-only parsing, and stored-output consistency checks. These establish provenance and internal "
              "accounting, not the semantic soundness/completeness of the static resolver.", "",
              "**Stopped after phase 1b. No selectors or post-hoc evaluation have run.**", ""]
    (OUT / "report.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", help="small explicit diagnostic sample; writes sample summaries")
    parser.add_argument("--refresh-accounting", action="store_true",
                        help="repair stored call-accounting failures only; never retry resource-limited tasks")
    args = parser.parse_args()
    command = shlex.join(["env", "-u", "PYTHONPATH", ".venv/bin/python", "-B",
                          "reports/callgraph_selection/build_graphs.py", *sys.argv[1:]])
    acquisition = json.loads((OUT / "inputs.json").read_text())
    for section in ("code_sha256", "input_sha256"):
        for path, expected in acquisition[section].items():
            if digest(path) != expected:
                raise ValueError(f"acquisition input changed: {path}")
    snapshot_path = ROOT / "reports/failure_analysis/extracted.json"
    pinned = json.loads((ROOT / "reports/v2_diagnostic/inputs.json").read_text())["sha256"]
    if digest(snapshot_path) != pinned[str(snapshot_path)]:
        raise ValueError("committed candidate snapshot hash mismatch")
    snapshot = candidate_projection(snapshot_path)
    with (ROOT / "reports/v2_diagnostic/patches.csv").open(newline="") as stream:
        members = {r["instance_id"]: {k: r[k] for k in ("instance_id", "repo", "source_run", "artifact_kind")}
                   for r in csv.DictReader(stream)}
    tasks = acquisition["tasks"]
    if len(tasks) != 83 or set(members) != {t["instance_id"] for t in tasks}:
        raise ValueError("population identity differs from frozen 83-task cohort")
    if args.tasks:
        if set(args.tasks) - set(members):
            raise ValueError("unknown sample task")
        tasks = [t for t in tasks if t["instance_id"] in args.tasks]
    previous = json.loads((OUT / "graph_inputs.json").read_text()) if args.refresh_accounting else None
    diagnostics = []
    rebuilt, reused, stopped = [], [], []
    for task in tasks:
        member = members[task["instance_id"]]
        if task["source_run"] != member["source_run"] or task["repo"] != member["repo"]:
            raise ValueError("acquisition task identity differs from cohort")
        if not task["base_commit_exists"] or task["commit_verification_status"] != "verified":
            raise ValueError("unverified base commit")
        existing = OUT / "graphs" / task["instance_id"] / "diagnostics.json"
        if args.refresh_accounting:
            diagnostic = json.loads(existing.read_text())
            row = diagnostic["row"]
            needs_rebuild = row["graph_status"] != "resource_limited" and row["call_sites"] != row["edge_records"]
            if needs_rebuild:
                diagnostic = build_task(task, member, snapshot)
                rebuilt.append(task["instance_id"])
            else:
                reused.append(task["instance_id"])
                row["edge_resolution_status"] = "completed"
                if row["graph_status"] == "resource_limited":
                    stopped.append(task["instance_id"])
                    row["edge_resolution_status"] = "not_completed_resource_limit"
                    for key in ("resolved_edges", "ambiguous_edges", "unresolved_edges"):
                        row[key] = ""
                    if row["patch_status"] == "available":
                        row["changed_symbol_resolution_status"] = "skipped_resource_limit"
                        for key in ("changed_symbols_total", "changed_symbols_resolved", "changed_symbols_ambiguous",
                                    "changed_symbols_unresolved", "changed_symbol_resolution_rate"):
                            row[key] = ""
                        row["changed_symbol_reasons"] = "{}"
                        symbols_path = existing.parent / "changed_symbols.json"
                        symbol_data = json.loads(symbols_path.read_text())
                        symbol_data["symbols"] = []
                        symbol_data["resolution_status"] = "skipped_resource_limit"
                        write_json(symbols_path, symbol_data)
                        diagnostic["artifact_sha256"][symbols_path.name] = digest(symbols_path)
                write_json(existing, diagnostic)
        else:
            diagnostic = build_task(task, member, snapshot)
        diagnostics.append(diagnostic)
        print(json.dumps(diagnostic["row"], sort_keys=True), flush=True)
    result = outputs(diagnostics, acquisition, command, bool(args.tasks))
    if previous:
        path = OUT / "graph_inputs.json"
        metadata = json.loads(path.read_text())
        metadata["accounting_refresh"] = dict(
            command=command, initial_execution_code_sha256=previous["code_sha256"],
            initial_code_snapshots={str(p.relative_to(ROOT)): digest(p) for p in sorted((OUT / "provenance").iterdir())},
            rebuilt_tasks=rebuilt, reused_tasks=reused, resource_limited_tasks_not_retried=stopped,
            reason="Root ast.Call annotation accounting corrected; resource-limited measurements made unavailable.")
        metadata["command"] = "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/build_graphs.py"
        write_json(path, metadata)
    print(json.dumps({key: result[key] for key in ("population", "graph_status_counts", "patch_status_counts")}), flush=True)


if __name__ == "__main__":
    main()
