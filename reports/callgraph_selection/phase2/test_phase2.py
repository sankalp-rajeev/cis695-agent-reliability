"""Synthetic-only tests. No fixture source or benchmark test is executed."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inputs import stored_selections, eligibility
from callgraph_selector import (Identities, Traversal, VARIANTS, features, rank_candidates,
                               membership, BUDGETS)
from run import prefix_rows, Provenance


def node(name, path="pkg/a.py", kind="function", module="pkg.a"):
    return dict(id=name, path=path, qualname=name, kind=kind, module=module)


def make_test_node(name):
    return node(name, path="tests/test_a.py", kind="test_function", module="tests.test_a")


def edge(caller, target, status="resolved", ordinal=1):
    return dict(caller=caller, targets=[target], status=status, path="tests/test_a.py",
                line=ordinal, column=0, scope=caller, reason="synthetic")


def test_projection_never_exposes_oracle_or_other_signal_values():
    text = json.dumps(dict(tasks=[dict(instance_id="i", source_run="s", oracle={"hidden": [1, 2]},
        gold_test_patch="forbidden", signals=dict(selected_tests=["tests/a.py::test_a"], regression={"secret": True}))]))
    assert stored_selections(text) == {"i": dict(instance_id="i", source_run="s", selected_tests=["tests/a.py::test_a"])}


def test_base_archive_root_directory_and_existing_node_id_extractor(tmp_path):
    import io
    import tarfile
    from inputs import Registry, base_test_ids, sha
    path = tmp_path / 'base.tar'
    with tarfile.open(path, 'w', format=tarfile.PAX_FORMAT, pax_headers={'comment': 'base_sha'}) as archive:
        root = tarfile.TarInfo('testbed')
        root.type = tarfile.DIRTYPE
        archive.addfile(root)
        payload = b'def test_a():\n    assert False  # never executed\n'
        entry = tarfile.TarInfo('testbed/tests/test_a.py')
        entry.size = len(payload)
        archive.addfile(entry, io.BytesIO(payload))
    ids, files = base_test_ids(dict(archive_path=str(path), archive_sha256=sha(path.read_bytes()), base_commit='base_sha'), Registry())
    assert ids == ('tests/test_a.py::test_a',)
    assert files == {'tests/test_a.py': 'unindexed'}


def test_identity_reuses_exact_normalizer_and_explicit_parameter_family():
    nodes = {"test_a": make_test_node("test_a")}
    index = Identities(nodes, ["tests/test_a.py::test_a"], "pkg/pkg")
    assert index.lookup("./tests/test_a.py::test_a")['node_id'] == "test_a"
    matched = index.lookup("tests/test_a.py::test_a[value]")
    assert matched['node_id'] == "test_a"
    assert matched['match_method'] == "explicit_parameterized_family"
    assert index.lookup("test_a")['node_id'] is None
    assert index.lookup("other/test_a.py::test_a")['node_id'] is None
    assert len(index.test_definitions) == 1


def test_django_unittest_identity_and_docstring_uncertainty():
    n = node("C.test_a", "tests/basic/tests.py", "test_method", "tests.basic.tests")
    index = Identities({n['id']: n}, ["tests/basic/tests.py::C::test_a"], "django/django")
    assert index.lookup("test_a (basic.tests.C)")['node_id'] == "C.test_a"
    assert index.lookup("A description of behavior")['node_id'] is None


def test_duplicate_definitions_are_unmappable_and_not_collapsed_into_one_definition():
    a = make_test_node("test_a"); b = dict(a, id="second definition")
    index = Identities({a['id']: a, b['id']: b}, ["tests/test_a.py::test_a"], "pkg/pkg")
    assert index.lookup("tests/test_a.py::test_a")['mapping_reason'] == "multiple_base_definitions"
    assert len(index.test_definitions) == 2
    assert not index.emittable


def test_shortest_paths_are_cycle_safe_depth_bounded_and_lexical():
    nodes = {n: node(n) for n in ("seed", "a", "b", "test", "far", "too_far")}
    edges = [edge("b", "seed"), edge("a", "seed"), edge("test", "b"), edge("test", "a"),
             edge("seed", "test"), edge("far", "test"), edge("too_far", "far")]
    graph = Traversal(nodes, edges, VARIANTS[0])
    paths = graph.from_seed("seed")
    assert paths["test"].nodes == ("test", "a", "seed")
    assert len(paths["far"].edges) == 3
    assert "too_far" not in paths


def test_secondary_traverses_candidates_but_never_unresolved_sites():
    nodes = {n: node(n) for n in ("seed", "test", "bad")}
    edges = [edge("test", "seed", "ambiguous"), edge("bad", "seed", "unresolved")]
    assert "test" not in Traversal(nodes, edges, VARIANTS[0]).from_seed("seed")
    secondary = Traversal(nodes, edges, VARIANTS[1])
    paths = secondary.from_seed("seed")
    assert "test" in paths and "bad" not in paths
    detail = secondary.provenance(paths["test"])
    assert detail['uses_ambiguous_edge'] and detail['ambiguous_hop_positions'] == [1]
    assert detail['path_calls'][0]['candidate_targets'] == ["seed"]


def test_secondary_shortest_ambiguity_does_not_imply_resolved_path_is_absent():
    nodes = {n: node(n) for n in ("seed", "mid", "test")}
    edges = [edge("test", "seed", "ambiguous"), edge("test", "mid"), edge("mid", "seed")]
    primary = Traversal(nodes, edges, VARIANTS[0])
    secondary = Traversal(nodes, edges, VARIANTS[1])
    p, _ = primary.test_paths({"seed"}, {"test"})
    s, fan = secondary.test_paths({"seed"}, {"test"})
    row, _, _ = features("tests/a.py::test_a", "test", nodes, {"pkg.a"}, s, fan, 2, p)
    assert row['reachable_resolved_only_same_depth'] is True
    assert secondary.provenance(s['test']['seed'])['uses_ambiguous_edge'] is True


def test_fanin_is_all_definitions_at_depth3_and_does_not_change_with_depth():
    nodes = {n: node(n) for n in ("seed", "mid", "near", "far")}
    graph = Traversal(nodes, [edge("near", "seed"), edge("far", "mid"), edge("mid", "seed")], VARIANTS[0])
    paths, fan = graph.test_paths({"seed"}, {"near", "far"})
    assert fan == {"seed": 2}
    row1, _, _ = features("tests/a.py::test_a", "near", nodes, {"pkg.a"}, paths, fan, 1, paths)
    row3, _, _ = features("tests/a.py::test_a", "near", nodes, {"pkg.a"}, paths, fan, 3, paths)
    assert row1['score_denominator'] == row3['score_denominator'] == 3


def test_shared_tail_does_not_prefer_mapping_status_or_impute_missing_zero():
    nodes = {"mapped": node("mapped", module="tests.a")}
    args = (nodes, {"pkg.a"}, {}, {}, 2, {})
    mapped, _, _ = features("tests/a.py::test_a", "mapped", *args, position=2)
    missing, _, _ = features("tests/a.py::test_missing", None, *args, position=1)
    assert mapped['specificity_score'] == 0 and missing['specificity_score'] is None
    assert missing['directly_called_seeds'] is None and missing['minimum_distance'] is None
    assert [r['test_id'] for r in rank_candidates("C", [mapped, missing])] == [missing['test_id'], mapped['test_id']]
    assert missing['specificity_score'] is None


def test_shared_tail_uses_computable_package_feature_before_v2_position():
    nodes = {"mapped": node("mapped", module="tests.a")}
    mapped, _, _ = features("tests/a.py::test_a", "mapped", nodes, {"pkg.a"}, {}, {}, 1, {}, 1)
    missing, _, _ = features("pkg/test_a.py::test_missing", None, nodes, {"pkg.a"}, {}, {}, 1, {}, 2)
    assert rank_candidates("C", [mapped, missing])[0]['test_id'] == missing['test_id']


def test_exact_ranking_prefers_specificity_before_direct_count_and_uses_final_ties():
    base = dict(graph_status="reachable", score_numerator=1, score_denominator=2, directly_called_seeds=1,
                minimum_distance=1, same_module=False, same_package=False, original_v2_position=None)
    hub = dict(base, test_id="a", score_denominator=100, directly_called_seeds=3)
    focused = dict(base, test_id="b", directly_called_seeds=1)
    tied = dict(focused, test_id="c")
    assert [r['test_id'] for r in rank_candidates("B", [tied, hub, focused])] == ["b", "c", "a"]


def test_budgets_are_prefixes_without_padding_and_A_preserves_order():
    candidates = [dict(test_id="b"), dict(test_id="a")]
    assert rank_candidates("A", candidates) == candidates
    assert all(len(candidates[:k]) == 2 for k in BUDGETS)
    assert membership(26) == [50, 100, 250, 500, "ALL"]


def test_eligibility_separates_seed_failure_and_partial_reasons():
    task = dict(patch_confirmed="True", names_resolved="0", names_ambiguous="1", names_total="1", newly_added_names="0")
    diagnostic = dict(row=dict(graph_status="complete"), parse_and_resource_failures=[])
    assert eligibility({}, task, diagnostic, True) == ("EXCLUDED", "AMBIGUOUS_ONLY_SEEDS")
    assert eligibility({}, task, diagnostic, False) == ("EXCLUDED", "MISSING_GRAPH")
    task['names_resolved'] = "1"
    diagnostic['row']['graph_status'] = "partial"
    diagnostic['parse_and_resource_failures'] = [dict(reason="SyntaxError")]
    assert eligibility({}, task, diagnostic, True)[0] == "EXTENDED_PARTIAL"
    diagnostic['parse_and_resource_failures'].append(dict(reason="archive_link_or_special_file_not_followed"))
    assert eligibility({}, task, diagnostic, True)[1] == "PARTIAL_GRAPH_OTHER_REASONS"


def test_provenance_caps_paths_and_aggregates_the_rest(tmp_path):
    nodes = {n: node(n) for n in ("s1", "s2", "s3", "s4", "t")}
    traversal = Traversal(nodes, [edge("t", seed, ordinal=i) for i, seed in enumerate(("s1", "s2", "s3", "s4"))], VARIANTS[0])
    paths, fan = traversal.test_paths({"s1", "s2", "s3", "s4"}, {"t"})
    feature, _, _ = features("tests/a.py::test_a", "t", nodes, {"pkg.a"}, paths, fan, 1, paths)
    candidates = [dict(feature, test_id=f"tests/a.py::test_{i}") for i in range(30)]
    p = Provenance(tmp_path / "provenance.csv")
    p.emit(dict(instance_id="i", strategy="B", edge_variant=VARIANTS[0], depth=1), candidates, paths, traversal, paths)
    p.close()
    rows = list(csv.DictReader((tmp_path / "provenance.csv").open()))
    full = [r for r in rows if r['record_type'] == 'FULL_PATH']
    aggregate = [r for r in rows if r['record_type'] == 'AGGREGATE_AFTER_TOP25']
    assert len(full) == 25 * 3
    assert sum(int(r['omitted_seed_paths']) for r in full) == 25
    assert sum(int(r['test_count']) for r in aggregate) == 5
    assert sum(int(r['omitted_seed_paths']) for r in aggregate) == 20


def test_missing_selection_is_not_an_empty_reachability():
    identity = dict(repo="p/p", strategy="B")
    missing = prefix_rows(identity, None, None, "AMBIGUOUS_ONLY_SEEDS")
    empty = prefix_rows(identity, [], None, "EMPTY_REACHABILITY")
    assert all(r['selected_count'] is None for r in missing)
    assert all(r['selected_count'] == 0 for r in empty)


def test_src_does_not_import_phase2_research():
    import ast
    from inputs import ROOT
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_bytes())
        for statement in ast.walk(tree):
            if isinstance(statement, ast.ImportFrom):
                assert not (statement.module or "").startswith("reports.callgraph_selection")
            elif isinstance(statement, ast.Import):
                assert all(not n.name.startswith("reports.callgraph_selection") for n in statement.names)


def test_summary_preserves_missing_zero_and_stratum_denominators():
    from analysis import summarize
    base = dict(instance_id="a", repo="r", strategy="B", historical_19="False", stratum="PRIMARY_COMPLETE",
                edge_variant=VARIANTS[0], depth="1", budget="ALL", selected_count="0")
    rows = [base, dict(base, instance_id="b", selected_count=""),
            dict(base, instance_id="c", stratum="EXTENDED_PARTIAL", selected_count="14")]
    summaries = [r for r in summarize(rows) if r['repo'] == 'ALL']
    primary = next(r for r in summaries if r['stratum'] == 'PRIMARY_COMPLETE')
    extended = next(r for r in summaries if r['stratum'] == 'EXTENDED_PARTIAL')
    assert primary['mean'] == 0 and primary['available_tasks'] == 1 and primary['missing_tasks'] == 1
    assert extended['mean'] == 14 and extended['cohort_tasks'] == 1


def test_criteria_fixed_six_and_half_eligible_do_not_pool_extended():
    from analysis import LARGE, criteria
    eligibility_rows = [dict(instance_id=i, stratum='PRIMARY_COMPLETE' if j < 5 else 'EXTENDED_PARTIAL', v2_outcome='PASS')
                        for j, i in enumerate(LARGE)]
    ids = ['na' + str(j) for j in range(7)]
    eligibility_rows += [dict(instance_id=i, stratum='PRIMARY_COMPLETE', v2_outcome='NOT_AVAILABLE') for i in ids]
    data = []
    for variant in VARIANTS:
        for i in LARGE:
            data += [dict(instance_id=i, strategy='B', edge_variant=variant, depth='2', budget='ALL', selected_count='10'),
                     dict(instance_id=i, strategy='C', edge_variant=variant, depth='2', budget='100', selected_count='100', reachable_selected_count='1')]
        for j, i in enumerate(ids):
            data.append(dict(instance_id=i, strategy='B', edge_variant=variant, depth='3', budget='ALL', selected_count='1' if j < 4 else '0'))
    result = criteria(data, dict(tasks=eligibility_rows, c3_primary_eligible=ids, c3_extended_eligible=[]))
    deciding = {r['criterion']: r for r in result['results'] if r['decides']}
    assert deciding['C1']['successes'] == 5 and deciding['C1']['denominator'] == 6
    assert deciding['C2']['successes'] == 5 and deciding['C2']['denominator'] == 6
    assert deciding['C3']['successes'] == 4 and deciding['C3']['denominator'] == 7 and deciding['C3']['threshold'] == 4
    assert all(r['passed'] for r in deciding.values())
    assert result['decision_map_outcome'] == 'Both rank/filter layer over Tier 2 and fallback'
