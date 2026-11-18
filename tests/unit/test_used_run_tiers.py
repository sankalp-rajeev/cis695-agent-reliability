"""Synthetic provenance and chronology facts for the frozen-run tables."""

import hashlib
import runpy
from pathlib import Path

import pytest

VERIFIER = runpy.run_path(str(Path(__file__).resolve().parents[2] / 'scripts/verify_leakage_gaps.py'))
resolve_repair_run = VERIFIER['resolve_repair_run']
split_t3 = VERIFIER['split_t3']
used_run_tables = VERIFIER['used_run_tables']


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def answer(field, speaker='model_output', *, defined=False):
    return {
        'category': 'answer',
        'field': field,
        'first_seen_in': speaker,
        'nonwhitespace_length': 30,
        'base_occurrences': 0,
        'guard_pass': True,
        'guard_rules': [],
        'defined_at_first_mention': defined,
    }


@pytest.mark.parametrize('hint', [None, 'rerun'])
def test_frozen_patch_hash_selects_unique_run(hint):
    frozen = sha('candidate B\n')
    assert resolve_repair_run(hint, frozen, {
        'original': sha('candidate A\n'), 'rerun_1': frozen,
    }) == ('rerun_1', 'unique-patch-sha256')


def test_explicit_provenance_selects_between_identical_patch_bytes():
    patch = sha('candidate\n')
    assert resolve_repair_run('original', patch, {
        'original': patch, 'rerun_1': patch,
    }) == ('original', 'explicit-run-and-patch-sha256')


def test_patch_hash_mapping_rejects_stale_and_ambiguous_provenance():
    patch = sha('candidate\n')
    with pytest.raises(ValueError, match='conflicts'):
        resolve_repair_run('original', patch, {'original': sha('different'), 'rerun_1': patch})
    with pytest.raises(ValueError, match='unique'):
        resolve_repair_run('rerun', patch, {'original': patch, 'rerun_1': patch})
    with pytest.raises(ValueError, match='unique'):
        resolve_repair_run(None, patch, {'original': sha('different')})


@pytest.mark.parametrize(('facts', 'expected'), [
    ([answer('gold_patch')], 'T3-content'),
    ([answer('test_patch')], 'T3-content'),
    ([answer('hidden_test_name')], 'T3-name'),
    ([answer('gold_patch'), answer('hidden_test_name')], 'T3-name'),
    ([answer('gold_patch'), answer('hidden_test_name', defined=True)], 'T3-content'),
    ([answer('hidden_test_name', defined=True)], 'T0'),
    ([answer('hidden_test_name'), answer('gold_patch', 'tool_output')], 'T4'),
])
def test_t3_split_uses_model_first_predefinition_evidence(facts, expected):
    assert split_t3({'facts': facts}) == expected


def test_used_role_runs_are_independent_of_worst_run():
    task = 'example__repo-1'
    patch, suite = sha('frozen patch'), sha('stored V4 suite')

    def observed(role, run, facts):
        return dict(instance_id=task, role=role, run=run, facts=facts,
                    observed=True, comparable=True, excluded=False)

    records = [
        observed('repair', 'earlier', [answer('gold_patch', 'tool_output')]),
        observed('repair', 'later', [answer('gold_patch')]),
        observed('generator', 'earlier', [answer('hidden_test_name')]),
        observed('generator', 'later', [answer('hidden_test_name', 'tool_output')]),
    ]
    provenance = {task: {
        'source_run': 'rerun', 'patch_sha256': patch,
        'repair_patch_sha256s': {'earlier': sha('superseded patch'), 'later': patch},
        'reproduction_record_provenance': {
            'verification_record.full.json': {'patch_sha256': patch, 'suite_sha256': suite},
        },
        'v4_suite_sha256s': {'earlier': suite, 'later': sha('another suite')},
    }}
    used, superseded, summary = used_run_tables(records, provenance)
    assert (used[0]['repair_run'], used[0]['repair_tier']) == ('later', 'T3-content')
    assert (used[0]['v4_run'], used[0]['v4_tier']) == ('earlier', 'T3-name')
    assert {row['role']: row['tier'] for row in superseded} == {'repair': 'T4', 'generator': 'T4'}
    assert summary['used_comparable']['highest_tier']['T3-name'] == 1
    assert summary['used_comparable']['any_role']['T4'] == []
    assert summary['all_runs_comparable']['any_role']['T4'] == [task]
