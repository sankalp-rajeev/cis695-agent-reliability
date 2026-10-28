"""Largest-first AST inputs under committed Amendment 2; no patch/oracle inputs."""
from __future__ import annotations

import ast
import hashlib
import time
from collections import Counter, deque
from pathlib import Path

from static_graph import Graph, Indexer, LIMITS, ResourceLimit

PREFLIGHT_LIMIT = 10_000_000
RETAINED_LIMIT = 5_000_000


class CountingIndexer(Indexer):
    def visit(self, node):
        self.g.indexing_visits += 1
        if self.g.indexing_visits % 4096 == 0:
            self.g.check()
        return super().visit(node)


def largest_first_omissions(records, limit=RETAINED_LIMIT):
    eligible = [r for r in records if r["preflight_status"] == "parsed"]
    remaining = sum(r["ast_nodes"] for r in eligible)
    omitted = []
    for row in sorted(eligible, key=lambda r: (-r["ast_nodes"], r["path"])):
        if remaining <= limit:
            break
        before = remaining
        remaining -= row["ast_nodes"]
        omitted.append(dict(row, removal_rank=len(omitted) + 1,
                            retained_before=before, retained_after=remaining,
                            reason="largest_first_retained_ast_quota"))
    return omitted, remaining


class AmendedGraph(Graph):
    def __init__(self, *, started=None, preflight_limit=PREFLIGHT_LIMIT, retained_limit=RETAINED_LIMIT):
        super().__init__()
        if started is not None:
            self.started = started
        self.preflight_limit = preflight_limit
        self.retained_limit = retained_limit
        self.indexing_visits = 0
        self.preflight_records = []
        self.omissions = []
        self.stage_seconds = {}
        self.preflight_complete = False

    def check(self):
        for name in ("python_files", "source_bytes", "definitions", "call_sites"):
            if self.counts[name] > LIMITS[name]:
                raise ResourceLimit(name)
        if self.counts["ast_nodes"] > self.preflight_limit:
            raise ResourceLimit("preflight_ast_nodes")
        if self.counts["retained_ast_nodes"] > self.retained_limit:
            raise ResourceLimit("retained_ast_nodes")
        if time.monotonic() - self.started > LIMITS["seconds"]:
            raise ResourceLimit("seconds")

    def build(self, root: Path):
        trees = {}
        paths = sorted(p for p in root.rglob("*.py") if p.is_file() and not p.is_symlink())
        self.counts["python_files"] = len(paths)
        self.counts["source_bytes"] = sum(p.stat().st_size for p in paths)
        stage_start = time.monotonic()
        current_path = None
        try:
            self.check()
            for source in paths:
                self.check()
                current_path = source.relative_to(root).as_posix()
                payload = source.read_bytes()
                self.base_digest.update(current_path.encode() + b"\0" + payload + b"\0")
                row = dict(path=current_path, source_bytes=len(payload),
                           source_sha256=hashlib.sha256(payload).hexdigest(),
                           ast_nodes=0, definitions=0, call_sites=0, preflight_status="pending")
                self.preflight_records.append(row)
                if len(payload) > LIMITS["source_blob_bytes"]:
                    row["preflight_status"] = "source_blob_over_2_MiB"
                    self.files[current_path] = "omitted"
                    self.counts["omitted_files"] += 1
                    self.failures.append(dict(path=current_path, reason=row["preflight_status"]))
                    continue
                try:
                    tree = ast.parse(payload, filename=current_path)
                except (SyntaxError, UnicodeError, ValueError, RecursionError) as exc:
                    row["preflight_status"] = "parse_failure"
                    self.files[current_path] = "parse_failure"
                    self.counts["parse_failures"] += 1
                    self.failures.append(dict(path=current_path, reason=type(exc).__name__,
                                              line=getattr(exc, "lineno", None), message=str(exc)[:200]))
                    continue
                queue = deque([tree])
                while queue:
                    if self.counts["ast_nodes"] == self.preflight_limit:
                        row["preflight_status"] = "incomplete_resource_limit"
                        raise ResourceLimit("preflight_ast_nodes")
                    node = queue.popleft()
                    self.counts["ast_nodes"] += 1
                    row["ast_nodes"] += 1
                    row["definitions"] += isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    row["call_sites"] += isinstance(node, ast.Call)
                    queue.extend(ast.iter_child_nodes(node))
                    if row["ast_nodes"] % 4096 == 0:
                        self.check()
                row["preflight_status"] = "parsed"
                self.files[current_path] = "preflighted"
                trees[current_path] = tree
            self.preflight_complete = True
            self.stage_seconds["preflight"] = time.monotonic() - stage_start
            self.omissions, retained = largest_first_omissions(self.preflight_records, self.retained_limit)
            self.counts["retained_ast_nodes"] = retained
            for omitted in self.omissions:
                path = omitted["path"]
                del trees[path]
                self.files[path] = "omitted_largest_first"
                self.counts["omitted_files"] += 1
                self.failures.append(dict(path=path, reason=omitted["reason"],
                                          ast_nodes=omitted["ast_nodes"], removal_rank=omitted["removal_rank"]))
            retained_records = [r for r in self.preflight_records if r["path"] in trees]
            self.counts["definitions"] = sum(r["definitions"] for r in retained_records)
            self.counts["call_sites"] = sum(r["call_sites"] for r in retained_records)
            self.check()
            stage_start = time.monotonic()
            for path in sorted(trees):
                current_path = path
                self.check()
                tree = trees.pop(path)
                self.index_tree(path, tree, CountingIndexer)
                self.files[path] = "parsed"
                self.counts["parsed_files"] += 1
            self.stage_seconds["indexing"] = time.monotonic() - stage_start
            stage_start = time.monotonic()
            self.resolve_calls()
            self.stage_seconds["call_resolution"] = time.monotonic() - stage_start
        except ResourceLimit as exc:
            self.status = "resource_limited"
            self.failures.append(dict(reason="fixed_resource_limit", limit=str(exc), path=current_path))
        if self.status == "complete" and self.failures:
            self.status = "partial"
        self.counts.update(Counter(edge["status"] + "_edges" for edge in self.edges))
        self.counts["nodes"] = len(self.nodes)
        self.counts["edge_records"] = len(self.edges)
        self.runtime = time.monotonic() - self.started
        return self
