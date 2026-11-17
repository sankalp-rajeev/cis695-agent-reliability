from pathlib import PurePosixPath

import pytest

from reliability.verifier.g1_reference import published_spurious_ids
from reliability.verifier.native_reference import clean_reference, collection_reference


def collection(identity):
    module = identity.split('::', 1)[0]
    directory = str(PurePosixPath(module).parent)
    return {'records': [{'selected_id': identity, 'stage': 'native', 'reason': 'not_a_test_module',
        'validation_status': 'INVALID_ID', 'native_proven_absent': True, 'valid': False,
        'runnable_ids': [], 'unavailable': False, 'collector_fallback': False}],
        'groups': [{'module': module, 'returncode': 5, 'directory_collection': {
            'file_collected': False, 'returncode': 5, 'collection_errors': [], 'directory': directory,
            'command': ['python', '-m', 'pytest', '--collect-only', directory]}}]}


def test_new_selection_need_not_include_the_old_sixteen_hygiene_ids():
    result = collection_reference('pylint-dev__pylint-4970', 'base', (), {'records': [], 'groups': []}, {})
    assert result['admitted_ids'] == result['g1_collected_ids'] == result['excluded_spurious_ids'] == []
    assert result['g1_reference_required']


def test_selected_subset_uses_the_same_native_absence_proof():
    identity = sorted(published_spurious_ids())[0]
    result = clean_reference({'admitted_ids': []}, collection(identity), task='pylint-dev__pylint-4970', tree='base')
    assert result['excluded_spurious_ids'] == [identity]
    assert result['admitted_ids'] == []


def test_selected_published_exclusion_cannot_be_removed_without_native_proof():
    identity = sorted(published_spurious_ids())[0]
    receipt = collection(identity)
    receipt['records'][0]['native_proven_absent'] = False
    with pytest.raises(ValueError, match='Reference hygiene removal mismatch'):
        clean_reference({'admitted_ids': []}, receipt, task='pylint-dev__pylint-4970', tree='patched')


def test_published_old_reference_exclusions_do_not_create_positive_reference_for_new_instance():
    identity = sorted(published_spurious_ids())[0]
    result = clean_reference({'admitted_ids': []}, collection(identity), task='pylint-dev__pylint-99999', tree='base')
    assert result == {'admitted_ids': [], 'excluded_spurious_ids': []}
