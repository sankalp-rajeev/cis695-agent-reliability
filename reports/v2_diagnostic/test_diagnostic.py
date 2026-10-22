"""Offline tests for stored-evidence aggregation and post-hoc identity matching."""

import ast
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import diagnostic as core
import oracle_posthoc as posthoc


def identity():
    return {"instance_id": "x__x-1", "repo": "x/x", "source_run": "main",
            "verifier_decision": "ACCEPT", "v2_outcome": "PASS"}


def collect(evidence=None, patch=None):
    return core.collect(identity(), evidence, patch, source="fixture", patch_source="diff",
                        artifact_kind="fixture", note="test")


def evidence(summary, executed, selected=3):
    return {"decision": "ACCEPT", "selected_tests": [f"t{i}" for i in range(selected)],
            "regression": {"outcome": "PASS", "duration_s": 2.5,
                           "findings": {"signal": "PASS", "summary": summary,
                                        "n_executed": executed}}}


def test_missing_is_blank_not_zero():
    row = collect()
    assert row["number_executed"] is None
    assert row["number_timed_out"] is None
    assert row["number_timed_out_status"] == "missing"
    assert core.encoded(None) == ""
    assert core.encoded(0) == 0


def test_schema_defaults_are_not_misreported_as_recorded_evidence():
    path = REPO / "runs/main_50_a/tasks/pytest-dev__pytest-7432/verification_record.full.json"
    raw = json.loads(path.read_text())
    del raw["selected_tests"]
    del raw["regression"]["duration_s"]

    class StoredJson:
        def read_text(self, **kwargs):
            return json.dumps(raw)

    projected = core.project_local(StoredJson())
    assert "selected_tests" not in projected
    assert "duration_s" not in projected["regression"]


def test_complete_sparse_summary_implies_zero_with_inferred_provenance():
    row = collect(evidence({"PASS": 2, "NOT_RUN": 1}, 2))
    assert row["number_timed_out"] == 0
    assert row["number_timed_out_status"] == "inferred"
    assert row["number_not_run_status"] == "recorded"
    assert row["execution_coverage"] == pytest.approx(2 / 3)


def test_incomplete_histogram_does_not_imply_zero():
    row = collect(evidence({"PASS": 1}, 1))
    assert row["number_pre_existing_failures"] is None
    assert row["number_observed_regressions"] is None


def test_execution_matches_existing_outcome_semantics():
    row = collect(evidence({"PASS": 1, "ERROR": 1, "TIMEOUT": 1}, 2))
    assert row["execution_coverage"] == pytest.approx(2 / 3)
    assert row["timeout_fraction"] == pytest.approx(1 / 3)
    with pytest.raises(ValueError, match="n_executed"):
        collect(evidence({"PASS": 1, "ERROR": 1, "TIMEOUT": 1}, 1))


def test_zero_selection_has_undefined_ratios_and_missing_tiers():
    row = collect(evidence({}, 0, selected=0))
    assert row["total_selected_tests"] == 0
    assert row["execution_coverage"] is None
    assert row["timeout_fraction"] is None
    assert row["tier1_selected_count"] is None
    assert row["tier2_selected_count"] is None


def test_source_files_and_symbols_reuse_candidate_parser():
    patch = """diff --git a/pkg/api.py b/pkg/api.py
--- a/pkg/api.py
+++ b/pkg/api.py
@@ -1 +1 @@ def changed():
-    return 0
+    return 1
diff --git a/tests/test_api.py b/tests/test_api.py
--- a/tests/test_api.py
+++ b/tests/test_api.py
@@ -1 +1 @@ def test_api():
-    assert 0
+    assert 1
"""
    row = collect(patch=patch)
    assert row["changed_source_files"] == ["pkg/api.py"]
    assert row["changed_symbols"] == ["changed", "test_api"]
    assert row["changed_symbols_status"] == "inferred"


def test_disagreement_fails_instead_of_overwriting_committed_decision():
    data = evidence({"PASS": 3}, 3)
    data["decision"] = "FLAG"
    with pytest.raises(ValueError, match="decision disagrees"):
        collect(data)


def test_distribution_keeps_zero_excludes_missing_and_interpolates():
    result = core.distribution([None, 0, 2, 4, 6])
    assert result == {"n": 4, "missing": 1, "min": 0, "p25": 1.5,
                      "median": 3, "p75": 4.5, "p90": 5.4, "max": 6,
                      "mean": 3, "total": 12}
    assert core.distribution([None]) == {"n": 0, "missing": 1}


def test_overlap_denominators_distinguish_unknown_empty_and_unavailable():
    rows = [
        {"official_f2p_count_posthoc": 1, "selected_test_ids": [],
         "f2p_selection_hit_posthoc": False},
        {"official_f2p_count_posthoc": 1, "selected_test_ids": ["test"],
         "f2p_selection_hit_posthoc": True},
        {"official_f2p_count_posthoc": 1, "selected_test_ids": ["test"],
         "f2p_selection_hit_posthoc": None},
        {"official_f2p_count_posthoc": 0, "selected_test_ids": [],
         "f2p_selection_hit_posthoc": False},
        {"official_f2p_count_posthoc": 1, "selected_test_ids": None,
         "f2p_selection_hit_posthoc": None},
    ]
    assert posthoc.overlap_summary(rows, "f2p") == {
        "applicable": 3, "positive": 1, "no_exact_hit": 1, "unresolved": 1, "missing": 1}


@pytest.mark.parametrize("official", [
    "test_x (forms_tests.test_forms.MyTests)",
    "test_x (forms_tests.test_forms.MyTests.test_x)",
    "forms_tests.test_forms.MyTests.test_x",
])
def test_django_exact_normalization_including_redundant_method(official):
    selected = ["tests/forms_tests/test_forms.py::MyTests::test_x"]
    match = posthoc.match_test(official, selected, "django/django", {})
    assert match["selected_ids"] == selected


def test_docstring_names_are_unresolved_not_guessed():
    match = posthoc.match_test("Some behavior description (forms_tests.MyTests)",
                              ["tests/forms_tests.py::MyTests::test_x"], "django/django", {})
    assert match["canonical_id"] is None
    assert match["reason"] == "unresolved_docstring_or_non_test_id"


def test_no_generic_tail_or_substring_matching():
    selected = ["tests/a.py::test_x", "tests/a.py::test_xyz"]
    assert not posthoc.match_test("tests/b.py::test_x", selected, "x/x", {})["selected_ids"]
    assert not posthoc.match_test("test_x", selected, "x/x", {})["selected_ids"]


def test_parameterized_family_is_explicit_and_not_substring_matching():
    selected = ["tests/a.py::test_x"]
    match = posthoc.match_test("tests/a.py::test_x[case-1]", selected, "x/x", {})
    assert match["match_method"] == "explicit_parameterized_family"
    assert not posthoc.match_test("tests/a.py::test_xyz[case-1]", selected, "x/x", {})["selected_ids"]


def test_bare_name_requires_unique_concrete_gold_identity():
    changed = {"tests/a.py::test_x": "added_or_rewritten"}
    match = posthoc.match_test("test_x", ["tests/a.py::test_x"], "x/x", changed)
    assert match["normalization"] == "unique_exact_name_in_gold_diff"
    changed["tests/b.py::test_x"] = "added_or_rewritten"
    assert posthoc.match_test("test_x", [], "x/x", changed)["canonical_id"] is None


def test_gold_added_and_rewritten_tests_distinct_from_selection_failure():
    diff = """diff --git a/tests/test_api.py b/tests/test_api.py
--- a/tests/test_api.py
+++ b/tests/test_api.py
@@ -1,2 +1,4 @@
 def test_old():
-    assert f() == 0
+    assert f() == 1
+def test_new():
+    assert f() == 2
"""
    changed = posthoc.gold_changes(diff, "x/x")
    assert set(changed) == {"tests/test_api.py::test_old", "tests/test_api.py::test_new"}
    match = posthoc.match_test("tests/test_api.py::test_new", [], "x/x", changed)
    category, status = posthoc.relevant_category(
        match, changed, per_test=None, aggregate=None, selected_known=True)
    assert category == posthoc.ADDED
    assert status == "inferred"


def test_gold_nested_class_identity_is_exact():
    diff = """diff --git a/tests/test_api.py b/tests/test_api.py
--- a/tests/test_api.py
+++ b/tests/test_api.py
@@ -1,3 +1,5 @@
 class Outer:
     class Inner:
         pass
+        def test_new(self):
+            assert f()
"""
    changed = posthoc.gold_changes(diff, "x/x")
    assert "tests/test_api.py::Outer::Inner::test_new" in changed


def test_missing_gold_class_scope_is_not_guessed_from_git_header():
    diff = """diff --git a/tests/test_api.py b/tests/test_api.py
--- a/tests/test_api.py
+++ b/tests/test_api.py
@@ -1,2 +1,2 @@ class EarlierNestedClass:
     def test_x(self):
-        assert f() == 0
+        assert f() == 1
"""
    changed = posthoc.gold_changes(diff, "x/x")
    assert changed == {"tests/test_api.py::test_x": "scope_unresolved"}
    match = posthoc.match_test("tests/test_api.py::ActualClass::test_x", [], "x/x", changed)
    category, status = posthoc.relevant_category(
        match, changed, per_test=None, aggregate=None, selected_known=True)
    assert "scope unresolved" in category
    assert status == "missing"


@pytest.mark.parametrize("outcome,category", [
    ("TIMEOUT", "selected but timed out before execution"),
    ("PRE_EXISTING_FAIL", "executed and classified as pre-existing failure"),
    ("REGRESSION", "correctly detected a regression"),
    ("PASS", "executed and missed behavior for another reason"),
])
def test_per_test_categories_require_per_test_evidence(outcome, category):
    match = posthoc.match_test("tests/a.py::test_x", ["tests/a.py::test_x"], "x/x", {})
    assert posthoc.relevant_category(match, {}, per_test={"tests/a.py::test_x": outcome},
                                    aggregate=None, selected_known=True) == (category, "recorded")


def test_aggregate_counts_never_guess_pylint_or_partial_timeout_identity():
    match = posthoc.match_test("tests/a.py::test_x", ["tests/a.py::test_x"], "x/x", {})
    category, status = posthoc.relevant_category(
        match, {}, per_test=None,
        aggregate={"n_selected": 70, "TIMEOUT": 13, "PRE_EXISTING_FAIL": 2}, selected_known=True)
    assert (category, status) == (posthoc.UNKNOWN, "missing")
    category, status = posthoc.relevant_category(
        match, {}, per_test=None, aggregate={"n_selected": 70, "TIMEOUT": 70}, selected_known=True)
    assert (category, status) == ("selected but timed out before execution", "inferred")


def test_never_selected_and_missing_selection_are_different():
    match = posthoc.match_test("tests/a.py::test_x", [], "x/x", {})
    assert posthoc.relevant_category(match, {}, per_test=None, aggregate=None,
                                    selected_known=True)[0] == "never selected the relevant test"
    assert posthoc.relevant_category(match, {}, per_test=None, aggregate=None,
                                    selected_known=False)[0] == "missing stored selection"


def test_study_population_has_no_empty_or_requests_rows_and_keeps_7432():
    rows = posthoc.population((REPO / "docs/results_100.csv").read_text())
    assert len(rows) == 83
    assert all(r["stratum"] == "headline" and r["oracle"] != "empty_patch" for r in rows)
    assert Counter_oracle(rows) == {"resolved": 69, "unresolved": 14}
    assert next(r for r in rows if r["instance_id"] == "pytest-dev__pytest-7432")["oracle"] == "resolved"


def Counter_oracle(rows):
    from collections import Counter
    return dict(Counter(r["oracle"] for r in rows))


def test_actual_preview_is_readonly_and_keeps_authoritative_oracle(monkeypatch):
    import socket
    import subprocess

    def forbidden(*args, **kwargs):
        raise AssertionError("no network or subprocess execution is allowed")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    inputs = posthoc.Inputs()
    all_rows = posthoc.population(inputs.read(REPO / "docs/results_100.csv").decode())
    sample = [next(r for r in all_rows if r["instance_id"] == iid) for iid in posthoc.SAMPLE]
    raw = inputs.json(REPO / "reports/failure_analysis/extracted.json")
    snapshots = {(t["instance_id"], t["source_run"]): t for t in raw["tasks"]}
    rows, _, wrong = posthoc.build(sample, snapshots, {}, inputs)
    assert len(rows) == 3
    discrepancy = rows[-1]
    assert discrepancy["oracle_outcome_posthoc"] == "resolved"
    assert discrepancy["local_oracle_outcome_posthoc"] == "patch_apply_failed"
    assert "committed=resolved; local=patch_apply_failed" in discrepancy["pytest_7432_note_posthoc"]
    django = next(r for r in rows if r["instance_id"] == "django__django-13297")
    assert django["number_timed_out"] == 6890
    assert django["failed_f2p_ids_posthoc"] == []
    assert next(r for r in wrong if r["instance_id"] == django["instance_id"])["category"] == posthoc.NO_F2P
    for path, digest in inputs.files.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    for row in rows:
        fields = [k for k in row if not k.endswith(("_status", "_source"))]
        for field in fields:
            assert row[field + "_status"] in {"recorded", "inferred", "missing"}
            if row[field] is None:
                assert row[field + "_status"] == "missing"


def test_no_src_module_imports_diagnostic_or_oracle_module():
    for path in (REPO / "src").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""] + [a.name for a in node.names]
            else:
                continue
            assert not any("v2_diagnostic" in m or "oracle_posthoc" in m for m in modules), path
        assert "oracle_posthoc" not in path.read_text(), path  # also catches dynamic imports


def test_core_has_no_oracle_dependency_and_no_selection_or_execution_calls():
    source = (HERE / "diagnostic.py").read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert "oracle" not in (node.module or "")
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else ""
            assert name not in {"select_tests", "run_regression", "TaskContainer", "run_oracle"}
    oracle_tree = ast.parse((HERE / "oracle_posthoc.py").read_text())
    forbidden = {"select_tests", "run_regression", "TaskContainer", "run_oracle", "load_instance",
                 "load_dataset", "load_verified", "run_task"}
    for node in ast.walk(oracle_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden


def test_output_path_cannot_escape_diagnostic_directory():
    with pytest.raises(ValueError, match="outputs must remain"):
        posthoc.write_csv(REPO / "forbidden.csv", [{"x": 1}])


def test_published_csv_is_readable_and_retains_all_committed_labels():
    # Also guards against enormous selected-ID cells exceeding csv's default
    # 131072-character field limit. Full unions stay in the hashed inputs.
    with (HERE / "patches.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    authoritative = {r["instance_id"]: r for r in posthoc.population(
        (REPO / "docs/results_100.csv").read_text())}
    assert len(rows) == 83
    assert {r["instance_id"] for r in rows} == set(authoritative)
    for row in rows:
        expected = authoritative[row["instance_id"]]
        assert row["oracle_outcome_posthoc"] == expected["oracle"]
        assert row["verifier_decision"] == expected["verifier_decision"]
        assert row["v2_outcome"] == expected["regression"]
        assert row["tier1_selected_count"] == ""
        assert row["tier2_selected_count"] == ""
        assert row["per_test_outcomes"] == ""
        for field in row:
            if not field.endswith(("_status", "_source")):
                assert row[field + "_status"] in {"recorded", "inferred", "missing"}
