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
