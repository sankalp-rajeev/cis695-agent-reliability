"""Patch-dependent native G1 references, with the frozen hygiene and thresholds."""

import gzip
import json
from pathlib import Path

from reliability.verifier.g1_reference import (
    native_collected_ids,
    published_spurious_ids,
    spurious_reference_ids,
)
from reliability.verifier.task_specs import ROOT, require_hash


def clean_reference(original, collection, *, task, tree):
    """Clean an empty original using only the current selected-slot evidence.

    The published exclusions concern the old pylint-4970 reference. A new
    patch may select fewer of those IDs; only the selected intersection needs
    removal, and every removed ID still needs the unchanged native proof.
    """
    if original.get('admitted_ids'):
        raise ValueError('Native G1 construction requires an empty original reference')
    selected = {r['selected_id'] for r in collection['records']}
    expected = published_spurious_ids() & selected if task == 'pylint-dev__pylint-4970' else set()
    removed = set(spurious_reference_ids(collection, expected))
    if removed != expected:
        raise ValueError('Reference hygiene removal mismatch: ' + task + '/' + tree)
    evidence = dict(original)
    for field in ('admitted_ids', 'skipped_reference_ids', 'module_skip_blocked_ids', 'drift_reference_ids'):
        if field in evidence:
            evidence[field] = sorted(set(evidence[field]) - removed)
    evidence['excluded_spurious_ids'] = sorted(removed)
    return evidence


def project_collection(task, tree, collection, original):
    # Same projection and guard thresholds as the frozen helper, with the
    # selected-slot cleaner above instead of its old fixed-cohort assertion.
    from reliability.verifier.regression import RunResult, TestResult, TestStatus
    from reliability.verifier.run_health import health_for_run
    reference = clean_reference(original, collection, task=task, tree=tree)
    reference['g1_collected_ids'] = native_collected_ids(collection)
    results, receipts = [], []
    for raw in collection['records']:
        row = dict(raw)
        potential = bool(row.get('valid')) and not row.get('collector_fallback')
        row['admitted'] = potential
        receipts.append(row)
        status = (TestStatus.SKIPPED if row.get('module_skip_reason') else TestStatus.PASSED) if potential else (
            TestStatus.INVALID_ID if row.get('validation_status') == 'INVALID_ID' else
            TestStatus.NOT_REACHED if row.get('failure_status') == 'NOT_REACHED' else
            TestStatus.RUNNER_UNAVAILABLE if row.get('failure_status') == 'RUNNER_UNAVAILABLE' else
            TestStatus.COLLECTION_ERROR)
        results.append(TestResult(row['selected_id'], status))
    run = RunResult(results=tuple(results), validation=tuple(receipts),
                    requested_tests=tuple(r['selected_id'] for r in receipts),
                    stage_health=tuple(collection.get('stage_health', ())))
    health = health_for_run(task, tree, run, reference)
    guard = health.get('G1_collected_guard', {'halt': False})
    return {'G2': health['G2'], 'G1_collected_guard': guard, 'environment_drift': health['environment_drift'],
            'halt': health['G2']['halt'] or guard['halt'] or health['environment_drift']['halt'],
            'excluded_spurious_ids': reference['excluded_spurious_ids'],
            'natively_collected_slots': len(reference['g1_collected_ids']), 'collection_only': True, 'tests_executed': 0}


def load_drift(path=None):
    path = Path(path or ROOT / 'reports/next_phases/phase4_rerun/fix16_reference')
    manifest = json.loads((path / 'manifest.json').read_bytes())
    require_hash(path / 'drift_ids.json.gz', manifest['data_sha256'])
    return json.loads(gzip.decompress((path / 'drift_ids.json.gz').read_bytes()))


def empty_reference(instance_id, tree, tests, drift):
    return {'admitted_ids': [], 'drift_reference_ids': sorted(
        set(drift.get(instance_id, {}).get('base', ())) & set(tests)) if tree == 'base' else [],
        'reference_source': 'G1_NATIVE_COLLECTION', 'g1_reference_required': True}


def collection_reference(instance_id, tree, tests, collection, drift):
    if {r['selected_id'] for r in collection['records']} != set(tests):
        raise ValueError('G1 collection/selection identity mismatch: ' + instance_id)
    original = empty_reference(instance_id, tree, tests, drift)
    reference = clean_reference(original, collection, task=instance_id, tree=tree)
    reference.update(g1_collected_ids=native_collected_ids(collection),
                     g1_reference_required=True, reference_source='G1_NATIVE_COLLECTION')
    return reference
