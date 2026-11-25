import copy
import json
from pathlib import Path

import pytest

from reliability.verifier.task_specs import REGISTRY_SCHEMA, RegistryProjection, load_registries, validate_task


@pytest.fixture
def task():
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / 'configs/e2e/task_specs_83.json').read_text())['tasks'][0]


def test_prepared_origin_preserves_operational_task_identity(task):
    prepared = copy.deepcopy(task)
    prepared['origin'] = 'prepared'
    assert validate_task(prepared) == validate_task(task)


@pytest.mark.parametrize('field', ['base_commit', 'pre_install', 'integrity_preflight', 'runner'])
def test_missing_required_task_fields_are_refused(task, field):
    del task[field]
    with pytest.raises(ValueError, match='Missing or unsupported'):
        validate_task(task)


def test_duplicate_ids_across_registries_are_refused(task, tmp_path):
    registry = {'schema': 'task_spec_registry/1', 'cohort': 'another_cohort',
                'built_by_commit': 'a' * 40, 'tasks': [task]}
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(registry))
    with pytest.raises(ValueError, match='Duplicate instance ID'):
        load_registries([path, path])


def test_wrong_archive_hash_is_refused(task):
    task['archive']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='archive SHA-256 mismatch'):
        validate_task(task)


def test_patch_dependent_fields_are_refused(task):
    task['selection'] = ['x']
    with pytest.raises(ValueError, match='Missing or unsupported'):
        validate_task(task)


def test_unknown_registry_values_are_never_decoded():
    parser = RegistryProjection('{"schema":"task_spec_registry/1","unexpected":{"outcome":"SECRET_VALUE"}}')
    decoder = parser.decoder
    class GuardedDecoder:
        def raw_decode(self, text, position):
            assert not text[position:].startswith(('{', '[', '"outcome"', '"SECRET_VALUE"'))
            return decoder.raw_decode(text, position)
    parser.decoder = GuardedDecoder()
    with pytest.raises(ValueError, match='Unsupported registry field'):
        parser.project(REGISTRY_SCHEMA)
