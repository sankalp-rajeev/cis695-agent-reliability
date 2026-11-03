"""Evidence safeguards and integrity of every frozen selection configuration."""
import csv
import gzip
import json
from pathlib import Path

import pytest
from analyze import matches

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize('target,selected,expected', [
    ('tests/a.py::A::test_x', {'tests/a.py::B::test_x'}, False),
    ('tests/a.py::A::test_x', {'tests/b.py::A::test_x'}, False),
    ('tests/a.py::test_x[1]', {'tests/a.py::test_x'}, True),
    ('tests/a.py::test_x[1]', {'tests/a.py::test_x[2]'}, False),
    ('tests/a.py::test_x', {'tests/a.py::test_x[1]'}, False),
    ('tests/a.py::test_x', set(), False),
    ('tests/a.py::test_x', None, None),
    ('test_x', {'tests/a.py::test_x'}, None),
    ('a prose description of a test', set(), None),
])
def test_identity_never_guesses_or_turns_unknown_into_negative(target, selected, expected):
    assert matches(target, selected, 'pytest-dev/pytest') is expected


def test_django_exact_scope_normalization():
    target = 'test_deconstruct (queries.test_q.QTests)'
    assert matches(target, {'tests/queries/test_q.py::QTests::test_deconstruct'}, 'django/django')
    assert not matches(target, {'tests/queries/test_q.py::OtherTests::test_deconstruct'}, 'django/django')


def test_all_configurations_preserve_availability_counts_and_budget_membership():
    frozen = HERE.parent / 'qualified_mapping/selection_summary.csv'
    with frozen.open() as f:
        counts = {(r['instance_id'], r['strategy'], r['edge_variant'], r['depth'], r['budget']): r for r in csv.DictReader(f)}
    with gzip.open(HERE / 'selection_memberships.jsonl.gz', 'rt') as f:
        selections = [json.loads(line) for line in f]
    assert len(selections) == len(counts) == 3672
    index = {(r['instance_id'], r['strategy'], r['edge_variant'], r['depth'], r['budget']): r for r in selections}
    assert len(index) == len(selections)
    for key, r in index.items():
        for stage in ('before', 'after'):
            ids = r[stage + '_selected']
            assert (ids is not None) == (counts[key][stage + '_available'] == 'True')
            if ids is None: continue
            assert len(ids) == len(set(ids)) == int(counts[key][stage + '_count'])
            assert set(ids) <= set(index[key[:4] + ('ALL',)][stage + '_selected'])
            if key[4] != 'ALL': assert len(ids) <= int(key[4])


def test_all_known_witness_denominators_are_explicit_and_distinct():
    with (HERE / 'witnesses.csv').open() as f: rows = list(csv.DictReader(f))
    usable = [r for r in rows if r['usable_for_existing_test_recall'] == 'True']
    assert len({r['instance_id'] for r in usable}) == 9
    assert sum(r['evidence_tier'] == 'reported_existing_regression' for r in usable) == 6
    assert sum(r['evidence_tier'] == 'official_existing_base_witness' for r in usable) == 7
    assert len(rows) == 34  # 28 oracle failures plus six independently named regressions.


def test_removed_official_witness_is_not_reclassified_as_irrelevant_by_later_pass():
    with (HERE / 'removed_tests.csv').open() as f: rows = list(csv.DictReader(f))
    assert len(rows) == 584
    witness = next(r for r in rows if r['selected_test_id'] == 'tests/lint/unittest_lint.py::test_multiprocessing')
    assert witness['classification'] == 'known_detecting_witness'
    assert len(json.loads(witness['known_witness_ids'])) == 2
    assert json.loads(witness['concrete_outcome_classes']) == {'observed_non_detecting_pass': 2}
    assert sum(r['classification'] == 'UNKNOWN_NO_PER_TEST_OUTCOME' for r in rows) == 555


def test_new_misses_and_preexisting_misses_are_distinguished():
    with (HERE / 'witness_selection.csv').open() as f: rows = list(csv.DictReader(f))
    rows = [r for r in rows if r['strategy'] == 'B' and r['depth'] == '3' and r['budget'] == 'ALL']
    primary = [r for r in rows if r['edge_variant'] == 'PRIMARY_RESOLVED_ONLY']
    secondary = [r for r in rows if r['edge_variant'] == 'SECONDARY_RESOLVED_PLUS_AMBIGUOUS']
    assert sum(r['transition'] == 'LOST' for r in primary) == 2
    lost_regressions = [r for r in secondary if r['transition'] == 'LOST' and r['evidence_tier'] == 'reported_existing_regression']
    assert {r['test_id'] for r in lost_regressions} == {
        'tests/queries/test_q.py::QTests::test_deconstruct',
        'tests/queries/test_q.py::QTests::test_deconstruct_negated'}
    assert all(r['instance_id'] == 'django__django-14140' for r in lost_regressions)


def test_no_historical_equivalence_claim_for_supplemental_raw_pairs():
    with (HERE / 'paired_outcomes.csv').open() as f: rows = list(csv.DictReader(f))
    assert len(rows) == 689
    assert all(r['base_commit_identity_matches'] == 'False' for r in rows)
    assert sum(r['outcome_class'] == 'observed_regression' for r in rows) == 1
    with (HERE / 'additional_local_record_evidence.csv').open() as f:
        local = {r['instance_id']: r for r in csv.DictReader(f)}
    assert local['pydata__xarray-6744']['accepted'] == 'False'
