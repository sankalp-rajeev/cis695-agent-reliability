"""Fix 15: real receipt paths, native collection, and launcher/scoring guards."""
import json
from pathlib import Path

import pytest

from reliability.verifier.g1_reference import clean_reference, read_collection
from reliability.verifier.run_health import health_for_run
from reliability.verifier.regression import RunResult, TestResult, TestStatus
from tests.unit.test_phase4_launcher import launch, task_spec

ROOT = Path(__file__).resolve().parents[2]


def test_pylint_spurious_references_require_real_native_directory_proof():
    reference = launch.load_reference()['pylint-dev__pylint-4970']
    exclusions=[]
    for tree in ('base','patched'):
        collection=read_collection(ROOT/'reports/next_phases/phase4_rerun/fix14_g1/tasks/pylint-dev__pylint-4970'/tree/'collection.json')
        cleaned=clean_reference(reference[tree],collection)
        assert len(cleaned['excluded_spurious_ids'])==16
        assert all('consider_using_with.py::' in t for t in cleaned['excluded_spurious_ids'])
        assert set(reference[tree]['admitted_ids'])-set(cleaned['admitted_ids'])==set(cleaned['excluded_spurious_ids'])
        exclusions.append(cleaned['excluded_spurious_ids'])
    assert exclusions[0]==exclusions[1]


def test_other_invalid_reference_is_never_removed():
    identity='tests/test_real.py::helper'
    reference={'admitted_ids':[identity]}
    collection={'records':[{'selected_id':identity,'stage':'native','reason':'helper',
        'validation_status':'INVALID_ID','native_proven_absent':True}]}
    assert clean_reference(reference,collection)['admitted_ids']==[identity]
