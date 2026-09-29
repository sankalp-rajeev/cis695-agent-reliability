"""Phase 5.3: overlap between selected tests and PASS_TO_PASS."""

from __future__ import annotations

from reliability.analysis.overlap import names_match, overlap


def test_exact_names_overlap():
    result = overlap(("tests/a.py::test_x", "tests/a.py::test_y"),
                     ("tests/a.py::test_x",))
    assert result["n_overlap_selected"] == 1
    assert result["fraction_of_selected"] == 0.5
    assert result["fraction_of_pass_to_pass"] == 1.0


def test_short_oracle_name_matches_a_nodeid():
    """SWE-bench sometimes stores `test_foo` where selection produces a node id."""
    result = overlap(("tests/mod.py::test_foo",), ("test_foo",))
    assert result["n_overlap_selected"] == 1
    assert result["n_overlap_pass_to_pass"] == 1


def test_similar_prefixes_do_not_match():
    assert not names_match("tests/a.py::test_foo", "test_foobar")
    result = overlap(("tests/a.py::test_foo",), ("test_foobar",))
    assert result["n_overlap_selected"] == 0


def test_empty_selection_is_zero_not_a_rate():
    result = overlap((), ("test_a",))
    assert result["n_selected"] == 0
    assert result["fraction_of_selected"] is None
    assert result["fraction_of_pass_to_pass"] == 0.0


def test_disjoint_sets_report_zero():
    result = overlap(("tests/a.py::test_x",), ("test_y",))
    assert result["n_overlap_selected"] == 0
    assert result["unmatched_selected"] == ["tests/a.py::test_x"]
