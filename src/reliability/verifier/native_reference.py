"""Patch-dependent native G1 references, with the frozen hygiene and thresholds."""

import gzip
import json
from pathlib import Path

from reliability.verifier.g1_reference import (
    clean_reference as frozen_clean_reference,
    native_collected_ids,
    project_collection as frozen_project_collection,
    published_spurious_ids,
    spurious_reference_ids,
)
from reliability.verifier.task_specs import ROOT, require_hash


def _hygiene_seed(original, collection):
    """Seed only proven INVALID_ID exclusions; never historical positive evidence.

    The frozen hygiene checker requires its published exclusions to be present
    before removal. These negative identities disappear during cleaning and
    cannot become an admission or drift reference.
    """
    if original.get('admitted_ids'):
        raise ValueError('Native G1 construction requires an empty original reference')
    evidence = dict(original)
    evidence['admitted_ids'] = spurious_reference_ids(collection, published_spurious_ids())
    return evidence


def clean_reference(original, collection, *, task, tree):
    return frozen_clean_reference(_hygiene_seed(original, collection), collection, task=task, tree=tree)


def project_collection(task, tree, collection, original):
    return frozen_project_collection(task, tree, collection, _hygiene_seed(original, collection))


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
