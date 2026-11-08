"""Collection-only reference hygiene and selected-slot G1 evidence."""

import gzip
import json
from pathlib import PurePosixPath


def read_collection(path):
    raw = path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.json.gz').read_bytes())
    return json.loads(raw)


def native_collected_ids(collection):
    return [r['selected_id'] for r in collection['records']
            if r.get('stage') == 'native' and r.get('valid') and r.get('runnable_ids')
            and not r.get('collector_fallback') and not r.get('module_skip_reason')]


def spurious_reference_ids(collection, reference):
    """Only completed, error-free native directory exclusion permits removal."""
    groups = {g['module']: g for g in collection.get('groups', ())}
    proven = set()
    for record in collection['records']:
        identity = record['selected_id']
        module = identity.split('::', 1)[0]
        group = groups.get(module, {})
        directory = group.get('directory_collection', {})
        command = directory.get('command', ())
        if (record.get('stage') == 'native' and record.get('reason') == 'not_a_test_module'
            and record.get('validation_status') == 'INVALID_ID' and record.get('native_proven_absent')
            and not record.get('unavailable') and not record.get('collector_fallback')
            and directory.get('file_collected') is False and directory.get('returncode') in (0, 5)
            and group.get('returncode') in (0, 5) and not directory.get('collection_errors')
            and '--collect-only' in command and command[-1] == str(PurePosixPath(module).parent)
            and directory.get('directory') == str(PurePosixPath(module).parent)):
            proven.add(identity)
    return sorted(set(reference) & proven)


def clean_reference(original, collection):
    evidence = dict(original) if isinstance(original, dict) else {'admitted_ids': list(original)}
    removed = set(spurious_reference_ids(collection, evidence['admitted_ids']))
    for field in ('admitted_ids', 'skipped_reference_ids', 'module_skip_blocked_ids'):
        if field in evidence:
            evidence[field] = sorted(set(evidence[field]) - removed)
    evidence['excluded_spurious_ids'] = sorted(removed)
    return evidence


def project_collection(task, tree, collection, original):
    """Project admission potential only; no test outcomes are produced or scored."""
    from reliability.verifier.regression import RunResult, TestResult, TestStatus
    from reliability.verifier.run_health import health_for_run

    reference = clean_reference(original, collection)
    reference['g1_collected_ids'] = native_collected_ids(collection)
    results=[]; receipts=[]
    for raw in collection['records']:
        row=dict(raw)
        potential = bool(row.get('valid')) and not row.get('collector_fallback')
        row['admitted'] = potential
        receipts.append(row)
        status = (TestStatus.SKIPPED if row.get('module_skip_reason') else TestStatus.PASSED) if potential else (
            TestStatus.INVALID_ID if row.get('validation_status') == 'INVALID_ID' else
            TestStatus.NOT_REACHED if row.get('failure_status') == 'NOT_REACHED' else
            TestStatus.RUNNER_UNAVAILABLE if row.get('failure_status') == 'RUNNER_UNAVAILABLE' else
            TestStatus.COLLECTION_ERROR)
        results.append(TestResult(row['selected_id'],status))
    run=RunResult(results=tuple(results),validation=tuple(receipts),
        requested_tests=tuple(r['selected_id'] for r in receipts),
        stage_health=tuple(collection.get('stage_health', ())))
    health=health_for_run(task,tree,run,reference)
    guard=health.get('G1_collected_guard',{'halt':False})
    return {'G2':health['G2'],'G1_collected_guard':guard,
            'environment_drift':health['environment_drift'],
            'halt':health['G2']['halt'] or guard['halt'] or health['environment_drift']['halt'],
            'excluded_spurious_ids':reference['excluded_spurious_ids'],
            'natively_collected_slots':len(reference['g1_collected_ids']),
            'collection_only':True,'tests_executed':0}
