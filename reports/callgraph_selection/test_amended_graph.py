"""Synthetic-only tests for amended AST accounting and frozen-patch aggregation."""
import ast
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from amended_graph import AmendedGraph, largest_first_omissions
from static_graph import Graph
from rebuild_and_resolve import aggregate, name_origin
from reliability.verifier.patch import parse_patch


def sources(tmp_path, files):
    for path, source in files.items():
        file = tmp_path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(source)
    return tmp_path


def test_largest_first_ties_and_whole_file_threshold():
    rows = [dict(path=p, ast_nodes=n, preflight_status="parsed")
            for p, n in [("z.py", 4), ("b.py", 8), ("a.py", 8), ("c.py", 2)]]
    omitted, retained = largest_first_omissions(rows, 15)
    assert [r["path"] for r in omitted] == ["a.py"]
    assert retained == 14
    assert omitted[0]["retained_before"] == 22
    assert largest_first_omissions(rows, 22) == ([], 22)


def test_cached_ast_parse_once_and_same_resolution_as_original(tmp_path):
    root = sources(tmp_path, {"pkg/a.py": "def work(): pass\nclass C:\n def m(self): work()\n",
                              "tests/test_a.py": "from pkg.a import work\ndef test_a(): work()\n"})
    original = Graph().build(root)
    actual_parse = ast.parse
    with patch("amended_graph.ast.parse", wraps=actual_parse) as parse:
        amended = AmendedGraph().build(root)
    assert parse.call_count == 2
    assert amended.nodes == original.nodes
    assert amended.edges == original.edges
    assert amended.scopes == original.scopes
    assert amended.status == "complete"
    assert amended.counts["ast_nodes"] == sum(r["ast_nodes"] for r in amended.preflight_records)
    assert amended.counts["retained_ast_nodes"] == amended.counts["ast_nodes"]
    assert 0 < amended.indexing_visits <= amended.counts["retained_ast_nodes"]


def test_preflight_ceiling_is_strict_and_no_omission_without_full_scan(tmp_path):
    root = sources(tmp_path, {"a.py": "x = 1\ny = 2\n", "z.py": "def z(): pass\n"})
    graph = AmendedGraph(preflight_limit=3, retained_limit=1).build(root)
    assert graph.status == "resource_limited"
    assert graph.counts["ast_nodes"] == 3
    assert not graph.preflight_complete
    assert graph.omissions == []
    assert graph.indexing_visits == 0
    assert graph.failures[-1]["limit"] == "preflight_ast_nodes"


def test_largest_file_is_partial_and_retained_tree_is_indexed(tmp_path):
    root = sources(tmp_path, {"a.py": "def a(): pass\n", "z.py": "x = 1\ny = 2\nz = 3\n"})
    count_a = sum(1 for _ in ast.walk(ast.parse((root / "a.py").read_bytes())))
    graph = AmendedGraph(retained_limit=count_a).build(root)
    assert graph.status == "partial"
    assert graph.files == {"a.py": "parsed", "z.py": "omitted_largest_first"}
    assert graph.counts["retained_ast_nodes"] == count_a
    assert graph.counts["parsed_files"] == 1
    assert graph.omissions[0]["path"] == "z.py"


def test_parse_failure_stays_partial_and_does_not_enter_omission_ranking(tmp_path):
    root = sources(tmp_path, {"a.py": "def a(): pass\n", "broken.py": "def invalid(:\n"})
    graph = AmendedGraph().build(root)
    assert graph.status == "partial"
    assert graph.counts["parse_failures"] == 1
    assert graph.omissions == []
    assert graph.files["broken.py"] == "parse_failure"


def test_new_name_in_absent_base_file_but_not_unindexed_file():
    diff = "diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+def new(): pass\n"
    change = parse_patch(diff).files[0]
    symbol = dict(name="new", targets=[], reason="base_file_absent")
    assert name_origin(symbol, change) == "newly_added_name_absent_at_base"
    symbol["reason"] = "base_file_omitted_or_unparsed"
    assert name_origin(symbol, change) == "not_established"
    symbol["targets"] = ["definition"]
    assert name_origin(symbol, change) == "base_name_present"


def test_aggregation_pools_counts_and_excludes_added_names():
    rows = [dict(repo="r", resolution_status="measured", graph_status="complete", names_total=2,
                 names_resolved=1, names_ambiguous=0, names_unresolved=1, newly_added_names=1,
                 excluding_new_total=1, excluding_new_resolved=1, excluding_new_ambiguous=0,
                 excluding_new_unresolved=0),
            dict(repo="r", resolution_status="measured_on_partial_graph", graph_status="partial", names_total=1,
                 names_resolved=0, names_ambiguous=1, names_unresolved=0, newly_added_names=0,
                 excluding_new_total=1, excluding_new_resolved=0, excluding_new_ambiguous=1,
                 excluding_new_unresolved=0)]
    repo, empty, total = aggregate(rows, ["r", "empty"])
    assert repo["resolution_rate"] == 1 / 3
    assert repo["excluding_new_resolution_rate"] == 1 / 2
    assert repo["names_resolved"] + repo["names_ambiguous"] + repo["names_unresolved"] == 3
    assert empty["resolution_rate"] == ""
    assert total["tasks"] == 2
