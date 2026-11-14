#!/usr/bin/env python3
"""Prepare the four-column, label-free provenance projection for Fix 10.

Hash the original Arrow file opaquely; Arrow IPC included_fields prevents other
column values from being decoded. Never load a dataset row through datasets.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow as pa
from pyarrow import ipc

from reliability.verifier.pre_install import WHEEL_SHA256, WHEEL_URL, load_specs

COLUMNS = ('instance_id', 'repo', 'base_commit', 'version')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(arrow, frozen, wheel, output):
    if output.exists():
        raise ValueError('Use a fresh provenance directory')
    if sha(wheel) != WHEEL_SHA256:
        raise ValueError('Wrong snapshot wheel')
    with pa.memory_map(str(arrow), 'r') as stream:
        schema = ipc.open_stream(stream).schema
        indices = [schema.get_field_index(c) for c in COLUMNS]
        if min(indices) < 0:
            raise ValueError('Required metadata column missing')
    with pa.memory_map(str(arrow), 'r') as stream:
        table = ipc.open_stream(stream, options=ipc.IpcReadOptions(included_fields=indices)).read_all()
    if set(table.column_names) != set(COLUMNS):
        raise ValueError('IPC projection returned unapproved columns')
    rows = table.to_pylist()
    tasks = json.loads((frozen/'tasks.json').read_text())
    by_id = {r['instance_id']: r for r in rows}
    selected = []
    for task in tasks:
        row = by_id[task['instance_id']]
        if row['repo'] != task['repo'] or row['base_commit'] != task['base_commit']:
            raise ValueError('Dataset/frozen identity mismatch')
        selected.append(row)
    if len(rows) != 500 or len(selected) != 83 or len({r['instance_id'] for r in selected}) != 83:
        raise ValueError('Unexpected dataset/cohort size')
    output.mkdir(parents=True)
    projection = output/'dataset_projection.json'
    projection.write_text(json.dumps({'dataset': 'SWE-bench/SWE-bench_Verified', 'split': 'test',
        'cache_snapshot': arrow.parent.name, 'arrow_path': str(arrow), 'arrow_sha256': sha(arrow),
        'columns_read': COLUMNS, 'rows_in_snapshot': len(rows),
        'frozen_tasks_sha256': sha(frozen/'tasks.json'), 'tasks': selected}, indent=2)+'\n')
    specs = load_specs(wheel, projection)
    receipt = {'version': '4.0.4', 'project_swebench_version': '5.0.2',
        'wheel_url': WHEEL_URL, 'pypi_url': 'https://pypi.org/project/swebench/4.0.4/',
        'wheel_sha256': WHEEL_SHA256, 'filename': wheel.name,
        'dataset_projection_sha256': sha(projection), 'specs_validated': len(specs),
        'installed_or_imported_snapshot': False}
    (output/'provenance.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('arrow', 'frozen', 'wheel', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    prepare(args.arrow, args.frozen, args.wheel, args.output)
