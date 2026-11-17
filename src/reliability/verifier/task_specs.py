"""Patch-independent task registry v1; all artifact hashes are checked on load."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.pre_install import PreInstallSpec, WHEEL_SHA256
from reliability.verifier.selection import TestRunner
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WHEEL = ROOT / 'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl'
DEFAULT_PROJECTION = ROOT / 'reports/next_phases/phase4_rerun/fix10_provenance/dataset_projection.json'


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def require_hash(path, expected):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Invalid SHA-256: ' + str(path))
    if sha(path) != expected:
        raise ValueError('SHA-256 mismatch: ' + str(path))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Missing or unsupported registry field; expected ' + ', '.join(required))


def absolute(value):
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError('Artifact path must be absolute')
    return Path(value)


@dataclass(frozen=True)
class TaskSpec:
    instance_id: str
    repo: str
    version: str
    base_commit: str
    image_tag: str
    image_id: str
    source: BaseSourceSpec
    runner: TestRunner
    integrity_receipt: Path
    integrity_receipt_sha256: str
    origin: str = field(compare=False)


def validate_task(row):
    fields(row, ('instance_id', 'repo', 'version', 'base_commit', 'image', 'archive',
                 'pre_install', 'integrity_preflight', 'runner', 'origin'))
    iid = row['instance_id']
    if not isinstance(iid, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+', iid):
        raise ValueError('Unsafe instance ID')
    if not re.fullmatch('[0-9a-f]{40}', row['base_commit']):
        raise ValueError('Invalid base commit')
    if not all(isinstance(row[k], str) and row[k] for k in ('repo', 'version')):
        raise ValueError('Missing repo/version')
    if row['origin'] not in ('phase4_freeze', 'prepared'):
        raise ValueError('Unsupported task origin')
    image, archive, pre, proof, runner = (row[k] for k in
                                        ('image', 'archive', 'pre_install', 'integrity_preflight', 'runner'))
    fields(image, ('tag', 'id'))
    if not isinstance(image['tag'], str) or not image['tag'] or not re.fullmatch('sha256:[0-9a-f]{64}', image['id']):
        raise ValueError('Image must be pinned to a SHA-256 ID')
    fields(archive, ('path', 'sha256', 'pax_comment'))
    if archive['pax_comment'] != row['base_commit']:
        raise ValueError('Archive commit mismatch')
    archive_path = absolute(archive['path'])
    fields(pre, ('wheel_sha256', 'dataset_projection_sha256', 'spec'),
           ('wheel_path', 'dataset_projection_path'))
    if pre['wheel_sha256'] != WHEEL_SHA256:
        raise ValueError('Pre_install requires the pinned SWE-bench 4.0.4 wheel')
    wheel = absolute(pre.get('wheel_path', str(DEFAULT_WHEEL)))
    projection = absolute(pre.get('dataset_projection_path', str(DEFAULT_PROJECTION)))
    require_hash(wheel, pre['wheel_sha256'])
    require_hash(projection, pre['dataset_projection_sha256'])
    spec = PreInstallSpec(iid, row['repo'], row['version'], row['base_commit'],
                          tuple(pre['spec']['commands']), wheel, projection, pre['dataset_projection_sha256'])
    if spec.resolve() != pre['spec']:
        raise ValueError('Resolved pre_install spec mismatch')
    source = BaseSourceSpec(row['base_commit'], archive_path, archive['sha256'], spec)
    SourceArchive(source)
    with tarfile.open(archive_path) as stream:
        if stream.pax_headers.get('comment') != archive['pax_comment']:
            raise ValueError('Archive PAX comment mismatch')
    fields(proof, ('status', 'receipt_path', 'receipt_sha256'))
    if proof['status'] != 'VERIFIED':
        raise ValueError('Integrity preflight must be VERIFIED')
    receipt = absolute(proof['receipt_path'])
    require_hash(receipt, proof['receipt_sha256'])
    raw = receipt.read_bytes()
    contents = JSONProjection((gzip.decompress(raw) if receipt.suffix == '.gz' else raw).decode()).project(
        {'status': True, 'base_commit': True, 'archive_sha256': True})
    if contents != {'status': 'VERIFIED', 'base_commit': row['base_commit'], 'archive_sha256': archive['sha256']}:
        raise ValueError('Integrity receipt identity mismatch')
    fields(runner, ('name', 'evidence', 'django_parallel_one'))
    if runner['name'] not in ('pytest', 'django', 'sympy', 'unknown') or not isinstance(runner['evidence'], str):
        raise ValueError('Invalid runner')
    if runner['django_parallel_one'] is not None and type(runner['django_parallel_one']) is not bool:
        raise ValueError('Invalid Django parallel choice')
    if runner['name'] == 'django' and type(runner['django_parallel_one']) is not bool:
        raise ValueError('Django runner needs an explicit parallel choice')
    return TaskSpec(iid, row['repo'], row['version'], row['base_commit'], image['tag'], image['id'],
                    source, TestRunner(**runner), receipt, proof['receipt_sha256'], row['origin'])


def load_registries(paths):
    """Any validated cohort/origin is accepted; duplicate IDs always fail closed."""
    tasks, hashes = {}, {}
    for path in paths:
        path = Path(path).resolve()
        raw = path.read_bytes()
        registry = json.loads(raw)
        fields(registry, ('schema', 'cohort', 'built_by_commit', 'tasks'))
        if registry['schema'] != 'task_spec_registry/1' or not isinstance(registry['cohort'], str) or not registry['cohort']:
            raise ValueError('Unsupported task registry schema/cohort')
        if not re.fullmatch('[0-9a-f]{40}', registry['built_by_commit']):
            raise ValueError('Invalid registry build commit')
        if not isinstance(registry['tasks'], list):
            raise ValueError('Registry tasks must be a list')
        for row in registry['tasks']:
            if row.get('instance_id') in tasks:
                raise ValueError('Duplicate instance ID: ' + row['instance_id'])
            task = validate_task(row)
            tasks[task.instance_id] = task
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
    return tasks, hashes
