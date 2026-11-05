"""Selection worker: trusted selector code, base source and candidate bytes only.

Each invocation is a new process. Benchmark code is never imported or executed.
SCG sources are byte-for-byte exports of the pinned remote revision, not a merge.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import json
import re
import resource
import sys
import tarfile
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from reliability.verifier.integrity import is_test_file
from reliability.verifier.patch import ChangeKind, parse_patch
from reliability.verifier.selection import SelectionConfig, select_tests
from v2_discovery_experiment import ArchiveTree

SCG_REVISION = "e1a3ed1c74fd304493c3fe3811de755af77e306c"
CG = "reports/callgraph_selection/"
SCG_FILES = (
    CG + "static_graph.py", CG + "amended_graph.py", CG + "build_graphs.py",
    CG + "phase2/inputs.py", CG + "phase2/callgraph_selector.py",
    CG + "typeprop_experiment/typeprop_graph.py",
    CG + "typeprop_experiment/qualified_mapping/mapper.py",
    "reports/v2_diagnostic/oracle_posthoc.py", "reports/v2_diagnostic/diagnostic.py",
    CG + "amendment2_72ad21b/graph_manifest.json",
)
CONFIGURATION = {"strategy": "B", "depth": 3, "budget": "ALL",
                 "edge_variant": "PRIMARY_RESOLVED_ONLY"}


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def load_scg(snapshot):
    """Only the selection subprocess imports the historical diagnostic modules.

    oracle_posthoc supplies the frozen canonical/family/match_test functions.
    No data-loading, gold mapping or analysis entry point is called; identities
    always pass changed={} to that matcher, as in the corrected implementation.
    """
    cg = snapshot / CG
    sys.path[:0] = [str(cg / "typeprop_experiment/qualified_mapping"),
                    str(cg / "typeprop_experiment"), str(cg / "phase2"), str(cg),
                    str(snapshot / "reports/v2_diagnostic")]
    return tuple(importlib.import_module(name) for name in (
        "typeprop_graph", "mapper", "callgraph_selector", "inputs", "build_graphs"))


def sections(text):
    # Same exact diff-section partition as qualified_mapping/run_mapping.py.
    starts = [m.start() for m in re.finditer(r"(?m)^diff --git ", text)]
    result = {}
    for start, end in zip(starts, [*starts[1:], len(text)]):
        block = text[start:end]
        header = re.fullmatch(r"diff --git a/(.+?) b/(.+)", block.split("\n")[0].rstrip("\r"))
        if not header:
            raise ValueError("unsupported_diff_header")
        path = header.group(2)
        if path in result:
            raise ValueError("duplicate_diff_section")
        result[path] = block
    return result


def corrected_selection(graph, base_ids, repo, patch_text, root, mapper, selector):
    """Apply the unchanged qualified mapper, B features and ranking at depth 3."""
    blocks = sections(patch_text)
    mapping, diagnostics = [], []
    for change in parse_patch(patch_text):
        if not change.path.endswith(".py") or is_test_file(change.path) or change.is_binary:
            continue
        base_path = change.old_path or change.path
        source = root / base_path
        base = source.read_bytes() if source.is_file() and change.kind != ChangeKind.ADDED else None
        output = mapper.map_file(base_path, change.path, base, blocks[change.path],
                                 list(graph.nodes.values()),
                                 added_file=change.kind == ChangeKind.ADDED,
                                 deleted_file=change.kind == ChangeKind.DELETED)
        mapping.extend(output["records"])
        diagnostics.extend(output["diagnostics"])
    seeds = {t for row in mapping if row["status"] == "resolved" for t in row["targets"]}
    detail = {"mapping": mapping, "mapping_diagnostics": diagnostics,
              "resolved_seeds": sorted(seeds)}
    # The existing selections() returns no ranking when there are no seeds.
    if not seeds:
        return None, {**detail, "selection_status": "UNAVAILABLE_NO_RESOLVED_SEEDS"}
    identities = selector.Identities(graph.nodes, base_ids, repo)
    traversal = selector.Traversal(graph.nodes, graph.edges, CONFIGURATION["edge_variant"])
    paths, fan = traversal.test_paths(seeds, identities.test_definitions)
    modules = {graph.nodes[s]["module"] for s in seeds}
    candidates = []
    for node, raw in identities.emittable.items():
        row, reachable, _ = selector.features(raw, node, graph.nodes, modules, paths, fan,
                                               3, paths, None, identities.lookup(raw))
        if reachable:
            candidates.append(row)
    tests = [r["test_id"] for r in selector.rank_candidates("B", candidates)]
    return tests, {**detail, "selection_status": "SELECTED" if tests else "ZERO_SELECTION"}


def select(request, arm, snapshot=None):
    started = time.monotonic()
    cpu_started = time.process_time()
    task, archive = request["task"], Path(request["archive"])
    result = {"tests": None, "selection_status": "UNAVAILABLE_BASE_ARCHIVE",
              "graph_status": "NOT_APPLICABLE" if arm == "v2" else "UNAVAILABLE",
              "graph_build_s": None, "selection_s": None}
    if not archive.is_file():
        return result
    if digest(archive) != task["base_archive_sha256"]:
        raise ValueError("base archive hash mismatch")
    with tarfile.open(archive) as stream:
        if stream.pax_headers.get("comment") != task["base_commit"]:
            raise ValueError("base commit mismatch")
    patch = Path(request["patch"]).read_text()
    if digest(request["patch"]) != task["patch_sha256"]:
        raise ValueError("candidate patch hash mismatch")
    if arm == "v2":
        tree = ArchiveTree(archive)
        try:
            selection_started = time.monotonic()
            selected = select_tests(parse_patch(patch), tree, SelectionConfig())
            result["selection_s"] = time.monotonic() - selection_started
            if list(selected.tests) != request["expected_v2"]:
                raise ValueError("V2 selection differs from frozen updated V2 list")
            if asdict(selected.runner) != task["runner"]:
                raise ValueError("V2 runner differs from frozen runner")
            result.update(tests=list(selected.tests), selection_status=(
                "SELECTED" if selected.tests else "ZERO_SELECTION"))
        finally:
            tree.archive.close()
    else:
        typeprop, mapper, selector, inputs, builders = load_scg(snapshot)
        manifest = json.loads((snapshot / SCG_FILES[-1]).read_text())
        entry = manifest[task["instance_id"]]
        graph_class = (typeprop.TypeAmendedGraph if entry["directory"].startswith("amendment2_")
                       else typeprop.TypeGraph)
        with tempfile.TemporaryDirectory(prefix="paired-scg-base-") as temporary:
            root = Path(temporary) / "testbed"
            build_started = time.monotonic()
            _, skipped = builders.extract({"archive_path": str(archive),
                "archive_sha256": task["base_archive_sha256"], "base_commit": task["base_commit"]},
                Path(temporary))
            result["graph_input_preparation_s"] = time.monotonic() - build_started
            build_started = time.monotonic()
            graph = graph_class().build(root)
            for item in skipped:
                if item["path"].endswith(".py"):
                    graph.files[item["path"]] = "omitted_archive_link"
                    graph.failures.append(item)
                    graph.counts["omitted_files"] += 1
            if graph.status == "complete" and graph.failures:
                graph.status = "partial"
            result.update(graph_build_s=time.monotonic() - build_started,
                          graph_status=graph.status, graph_failures=graph.failures,
                          graph_counts=dict(graph.counts))
            if graph.status == "resource_limited":
                result["selection_status"] = "UNAVAILABLE_RESOURCE_LIMITED_GRAPH"
            else:
                selection_started = time.monotonic()
                # This inventories base test IDs; it never calls select_tests or
                # V2 discovery/ranking. The extractor and normalizer are shared.
                base_ids, _ = inputs.base_test_ids({"archive_path": str(archive),
                    "archive_sha256": task["base_archive_sha256"], "base_commit": task["base_commit"]},
                    inputs.Registry())
                tests, detail = corrected_selection(graph, base_ids, task["repo"], patch,
                                                     root, mapper, selector)
                result.update(tests=tests, **detail, selection_s=time.monotonic() - selection_started)
            del graph
            gc.collect()
    result.update(preparation_wall_s=time.monotonic() - started,
                  selection_cpu_s=time.process_time() - cpu_started,
                  selection_process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--arm", choices=("v2", "scg"), required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = select(json.loads(args.request.read_text()), args.arm, args.snapshot)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
