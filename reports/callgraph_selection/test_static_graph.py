"""Resolver checks supplied for later review; not run during no-test phase 1b.

All fixtures are synthetic source text, parsed with ast only. No fixture is
imported or executed. This test module imports only the research implementation
and the project's existing parser; it does not import post-hoc modules.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from build_graphs import candidate_projection, changed_symbols
from static_graph import Graph


class StaticGraphChecks(unittest.TestCase):
    def graph(self, files):
        with tempfile.TemporaryDirectory(prefix="cg-unit-", dir="/tmp") as directory:
            root = Path(directory)
            for path, source in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
            return Graph().build(root)

    def test_explicit_import_alias_resolves_and_constructor_has_no_implicit_edge(self):
        graph = self.graph({"pkg/api.py": "def work(): pass\nclass Item:\n def __init__(self): pass\n",
                            "tests/test_api.py": "from pkg.api import work as run, Item\ndef test_api():\n run()\n Item()\n"})
        self.assertEqual(graph.status, "complete")
        self.assertEqual([e["status"] for e in graph.edges], ["resolved", "resolved"])
        self.assertEqual([graph.nodes[e["targets"][0]]["qualname"] for e in graph.edges], ["work", "Item"])
        self.assertEqual(graph.counts["call_sites"], len(graph.edges))

    def test_rebinding_and_multiple_definitions_never_resolve(self):
        graph = self.graph({"a.py": "def work(): pass\ndef work(): pass\ndef caller():\n work()\ndef shadow(work):\n work()\n"})
        self.assertEqual([e["status"] for e in graph.edges], ["ambiguous", "unresolved"])
        self.assertEqual(len(graph.edges[0]["targets"]), 2)

    def test_inheritance_decorators_and_dynamic_scope_are_uncertain(self):
        graph = self.graph({"a.py": "def deco(f): return f\n@deco\ndef work(): pass\nclass A(object):\n def method(self): pass\n def caller(self):\n  self.method()\ndef caller():\n work()\n [work() for x in []]\n"})
        self.assertEqual([e["status"] for e in graph.edges], ["ambiguous", "ambiguous", "unresolved"])

    def test_class_namespace_is_not_a_function_closure(self):
        graph = self.graph({"a.py": "def target(): pass\nclass C:\n def target(self): pass\n def method(self):\n  target()\n"})
        self.assertEqual(graph.edges[0]["status"], "resolved")
        self.assertEqual(graph.nodes[graph.edges[0]["targets"][0]]["qualname"], "target")

    def test_parse_failure_is_partial_and_calls_are_accounted(self):
        graph = self.graph({"broken.py": "def broken(:\n", "a.py": "def caller(x=build()) -> kind():\n return x()\n"})
        self.assertEqual(graph.status, "partial")
        self.assertEqual(graph.counts["parse_failures"], 1)
        self.assertEqual(graph.counts["call_sites"], len(graph.edges))
        self.assertTrue(all(e["status"] == "unresolved" for e in graph.edges))

    def test_seed_matching_is_file_local_and_duplicates_are_ambiguous(self):
        graph = self.graph({"a.py": "def changed(): pass\nclass C:\n def changed(self): pass\n",
                            "elsewhere.py": "def new_name(): pass\n"})
        patch = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1,2 @@ def changed():\n-def changed(): pass\n+def changed(): return 1\n+def new_name(): pass\n"
        seeds = changed_symbols(patch, graph)
        self.assertEqual({s["name"]: s["status"] for s in seeds},
                         {"changed": "ambiguous", "new_name": "unresolved"})

    def test_snapshot_projection_discards_every_unapproved_value(self):
        source = json.dumps({"tasks": [{"instance_id": "a", "source_run": "r", "agent_patch": "candidate",
                                        "forbidden": {"nested": ['"', {"a": True}]}}]})
        with tempfile.TemporaryDirectory(prefix="cg-unit-", dir="/tmp") as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text(source)
            self.assertEqual(candidate_projection(path),
                             {"a": {"instance_id": "a", "source_run": "r", "agent_patch": "candidate"}})


if __name__ == "__main__":
    unittest.main()
