"""Prepare immutable registry entries without patches, tests, or model access."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from reliability.agent.isolation import MASKED_TMPFS_PATHS, assert_network_none
from reliability.benchmark.leakage import import_name_for_instance
from reliability.env import assert_clean_interpreter, clean_env
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.container import ContainerRepoTree, TaskContainer, _docker_bin, image_for
from reliability.verifier.pre_install import WHEEL_SHA256, load_specs
from reliability.verifier.selection import TestRunner, discover_runner
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive, verify_base_source

ROOT = Path(__file__).resolve().parents[3]
FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')
PROVENANCE = ROOT / 'reports/next_phases/phase4_rerun/fix10_provenance'
WHEEL = ROOT / 'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl'
COLUMNS = ('instance_id', 'repo', 'base_commit', 'version')
RULE = 'INELIGIBLE_UNMASKABLE_COPY'
MIN_FREE = 50_000_000_000
BLOCKED = ('oracle', 'grade', 'label', 'gold', 'posthoc', 'fail_to_pass', 'pass_to_pass')


def safe_path(path):
    path = Path(path).absolute()
    if any(word in str(path).lower() for word in BLOCKED):
        raise ValueError('Forbidden input/output path')
    return path


def sha(path):
    with safe_path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return digest


def write_new(path, value):
    """Atomic publication with no replacement, including under concurrent use."""
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # EEXIST is intentional; never replace a registry.
    finally:
        os.unlink(temporary)


def run(argv, **kwargs):
    return subprocess.run(argv, env=clean_env(), capture_output=True, check=True, **kwargs)


def free_guard(path, needed=0):
    if shutil.disk_usage(path).free - needed < MIN_FREE:
        raise RuntimeError('STOP: projected free disk below 50 GB')


def dataset_rows(arrow=None):
    """Arrow projects columns before decoding any row or unapproved column."""
    import pyarrow as pa
    from pyarrow import ipc
    if arrow is None:
        home = Path(os.environ['HF_HOME']).resolve()
        if not home.is_relative_to(ROOT / 'runs'):
            raise ValueError('HF_HOME must be under this worktree runs/')
        matches = sorted((home / 'datasets').glob('SWE-bench___swe-bench_verified/default/0.0.0/*/swe-bench_verified-test.arrow'))
        if len(matches) != 1:
            raise ValueError('Expected exactly one cached Verified snapshot')
        arrow = matches[0]
    arrow = safe_path(arrow)
    with pa.memory_map(str(arrow), 'r') as stream:
        schema = ipc.open_stream(stream).schema
        indices = [schema.get_field_index(c) for c in COLUMNS]
    if min(indices) < 0:
        raise ValueError('Required public dataset columns missing')
    with pa.memory_map(str(arrow), 'r') as stream:
        table = ipc.open_stream(stream, options=ipc.IpcReadOptions(included_fields=indices)).read_all()
    if set(table.column_names) != set(COLUMNS):
        raise ValueError('Projection contains unapproved fields')
    rows = [{key: row[key] for key in COLUMNS} for row in table.to_pylist()]
    for row in rows:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+', row['instance_id']):
            raise ValueError('Unsafe instance ID')
        if not re.fullmatch(r'[0-9a-f]{40}', row['base_commit']):
            raise ValueError('Invalid base commit')
    if len({r['instance_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate dataset IDs')
    return rows, arrow


def manifest_ids(path):
    path = safe_path(path)
    if path.suffix == '.json':
        payload = json.loads(path.read_text())
        ids = payload if isinstance(payload, list) else payload['instance_ids']
    elif path.suffix == '.csv':
        with path.open(newline='') as stream:
            ids = [r['instance_id'] for r in csv.DictReader(stream)]
    else:
        ids = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not ids or len(set(ids)) != len(ids) or not all(isinstance(i, str) for i in ids):
        raise ValueError('Manifest must contain distinct instance IDs')
    return ids


def frozen_metadata():
    path = FROZEN / 'tasks.json'
    if sha(path) != '532df6e8eebd9afa91592ef39aa28f12d8b905fcf3987c7698e06c8ad02ac625':
        raise ValueError('Frozen task metadata hash mismatch')
    fields = {'instance_id': True, 'repo': True, 'base_commit': True, 'runner': {'name': True, 'evidence': True},
              'base_archive_sha256': True, 'image_tag': True, 'image_binding': {'host_image_id': True}}
    return {t['instance_id']: t for t in JSONProjection(path.read_text()).project({'*': fields})}


class PreparationContainer(TaskContainer):
    def run_args(self):
        args = super().run_args()
        args[2:2] = ['--pull=never', *[part for p in MASKED_TMPFS_PATHS for part in ('--tmpfs', p)]]
        return args

    def start(self):
        try:
            super().start()
            assert_network_none(self.name)
        except BaseException:
            self.stop()
            raise


def inspect_image(tag):
    proc = subprocess.run([_docker_bin(), 'image', 'inspect', tag, '--format', '{{json .}}'],
                          env=clean_env(), capture_output=True, text=True)
    if proc.returncode:
        # A daemon failure must never be mistaken for a missing image and pull.
        if 'No such image' not in proc.stderr and 'No such object' not in proc.stderr:
            raise RuntimeError('Image inspection failed: ' + proc.stderr[:300])
        return None
    info = json.loads(proc.stdout)
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', info['Id']):
        raise ValueError('Image ID is not immutable')
    return info


def ensure_image(iid, allow_pull=False):
    tag = image_for(iid)
    info = inspect_image(tag)
    if info is None:
        if not allow_pull:
            raise ValueError('Image absent; explicit --allow-pull is required')
        # Manifest sizes use the same OCI layer union as manifest_disk_cost.py.
        from reliability.task_prep.projection import layers_for
        compressed = sum(size for _, size in layers_for(tag))
        free_guard(ROOT, compressed * 5)  # conservative temporary + extracted bound
        run([_docker_bin(), 'pull', tag], text=True)
        free_guard(ROOT)
        info = inspect_image(tag)
    return {'tag': tag, 'id': info['Id']}


def eligibility(container, row):
    request = {'import_name': import_name_for_instance(row['instance_id']),
               'base_commit': row['base_commit'], 'masked_paths': MASKED_TMPFS_PATHS}
    probe = Path(__file__).with_name('versions_probe.py').read_text()
    command = 'python -c ' + shlex.quote(probe)
    rc, raw = container.exec_input(command, json.dumps(request), timeout_s=180)
    if rc:
        raise ValueError('Version probe failed: ' + raw[-500:])
    evidence = json.loads(raw)
    base = {v['version'] for v in evidence['base_versions']}
    differences = [c for c in evidence['copies'] if c['version'] is not None and base and c['version'] not in base]
    unknown = [c for c in evidence['copies'] if c['version'] is None or not base]
    status = RULE if differences else ('UNCHECKED' if unknown or evidence['scan_errors'] else 'ELIGIBLE')
    return {'instance_id': row['instance_id'], 'image_id': container.image, 'status': status,
            'import_name': request['import_name'], 'evidence': differences, 'probe': evidence,
            'unresolved_copies': unknown, 'network': 'none'}


def archive_from_container(container, row, directory, expected=None):
    """git archive retains Git's order, commit mtime, prefix and pax comment."""
    directory = safe_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (row['instance_id'] + '.tar')
    free_guard(directory)
    fd, temporary = tempfile.mkstemp(prefix='.' + row['instance_id'], suffix='.tar', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            proc = subprocess.run([_docker_bin(), 'exec', '-w', '/testbed', container.name,
                                   'git', '-c', 'core.attributesFile=/dev/null', 'archive', '--format=tar',
                                   '--prefix=testbed/', row['base_commit']], stdout=stream,
                                  stderr=subprocess.PIPE, env=clean_env(), timeout=180)
        if proc.returncode:
            raise ValueError('git archive failed: ' + proc.stderr.decode(errors='replace')[:300])
        digest = sha(temporary)
        if expected and digest != expected:
            raise ValueError('STOP: rebuilt archive differs from frozen hash')
        if target.exists():
            if sha(target) != digest:
                raise ValueError('Existing archive differs; refusing overwrite')
        else:
            os.link(temporary, target)
        spec = BaseSourceSpec(row['base_commit'], target, digest)
        SourceArchive(spec)
        with tarfile.open(target) as archive:
            if archive.pax_headers.get('comment') != row['base_commit']:
                raise ValueError('Archive pax comment does not match base commit')
        return {'path': str(target.resolve()), 'sha256': digest, 'pax_comment': row['base_commit']}
    finally:
        os.unlink(temporary)


def runner_choice(container, row, frozen):
    discovered = discover_runner(ContainerRepoTree(container))
    # Phase 4 intentionally preserves historical runner metadata; the executor
    # selects SymPy's native adapter from the repo. Do not rewrite frozen fields.
    if frozen:
        runner = TestRunner(**frozen['runner'])
        if discovered.name != runner.name and row['repo'] != 'sympy/sympy':
            raise ValueError('Discovered runner differs from frozen runner')
    else:
        runner = discovered
    result = asdict(runner)
    result['django_parallel_one'] = None
    provenance = {'discovered': asdict(discovered), 'effective_name': 'sympy' if row['repo'] == 'sympy/sympy' else runner.name}
    if runner.name == 'django':
        choices = json.loads((ROOT / 'reports/next_phases/phase4_rerun/fix17_django_commands.json').read_text())['tasks']
        if frozen:
            result['django_parallel_one'] = choices[row['instance_id']]['parallel_one']
            provenance['django_choice'] = 'phase4_freeze'
        else:
            values = [v['parallel_one'] for v in choices.values()]
            default = max(set(values), key=values.count)
            result['django_parallel_one'] = default
            provenance['django_choice'] = 'prepared_default'
    return result, provenance


def prepare(ids, cohort, out, *, archives, wheel=WHEEL, allow_pull=False):
    assert_clean_interpreter()
    if os.environ.get('HF_DATASETS_OFFLINE') != '1' or os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('Both Hugging Face offline flags must be 1')
    out = safe_path(out)
    if out.exists():
        raise FileExistsError('Registry exists; use a new output path')
    if sha(wheel) != WHEEL_SHA256:
        raise ValueError('Pinned wheel hash mismatch')
    rows, arrow = dataset_rows()
    by_id = {r['instance_id']: r for r in rows}
    if not set(ids) <= by_id.keys():
        raise ValueError('Unknown manifest instance')
    frozen = frozen_metadata()
    evidence_dir = out.parent / (out.stem + '_evidence')
    evidence_dir.mkdir(parents=True, exist_ok=False)
    # For frozen tasks reuse the exact, verified four-column projection, so
    # resolve() retains every original provenance field and SHA-256.
    original_path = PROVENANCE / 'dataset_projection.json'
    meta = json.loads((PROVENANCE / 'provenance.json').read_text())
    if sha(original_path) != meta['dataset_projection_sha256']:
        raise ValueError('Frozen projection hash mismatch')
    original_specs = load_specs(wheel, original_path)
    selected = [by_id[i] for i in sorted(ids) if i not in frozen]
    extra_specs = {}
    if selected:
        projection = evidence_dir / 'dataset_projection.json'
        original = json.loads(original_path.read_text())
        write_new(projection, {'dataset': original['dataset'], 'split': 'test', 'cache_snapshot': arrow.parent.name,
                              'arrow_path': str(arrow), 'arrow_sha256': original['arrow_sha256'],
                              'columns_read': list(COLUMNS), 'rows_in_snapshot': len(rows), 'tasks': selected})
        extra_specs = load_specs(wheel, projection)
    entries, failures, eligible, timing = [], [], [], []
    for iid in ids:
        started = time.monotonic()
        row, stage = by_id[iid], 'image'
        try:
            print(json.dumps({'task': iid, 'event': 'start'}), flush=True)
            image = ensure_image(iid, allow_pull)
            frozen_task = frozen.get(iid)
            if frozen_task and image['id'] != frozen_task['image_binding']['host_image_id']:
                raise ValueError('Frozen image identity mismatch')
            with PreparationContainer(iid, '', image=image['id'], experiment_id='task_prep') as container:
                stage = 'eligibility'
                check = eligibility(container, row)
                eligible.append(check)
                if check['status'] != 'ELIGIBLE':
                    if check['status'] == RULE:
                        print(json.dumps({'task': iid, 'status': RULE}), flush=True)
                        continue
                    raise ValueError('Eligibility could not establish package versions')
                stage = 'archive'
                archive = archive_from_container(container, row, archives,
                                                 frozen_task['base_archive_sha256'] if frozen_task else None)
                stage = 'pre_install'
                proof = (original_specs if iid in frozen else extra_specs)[iid]
                if {k: getattr(proof, k) for k in COLUMNS} != row:
                    raise ValueError('Projected dataset/frozen identity mismatch')
                pre_install = proof.resolve()
                stage = 'integrity_preflight'
                source = BaseSourceSpec(row['base_commit'], Path(archive['path']), archive['sha256'], proof)
                receipt = verify_base_source(container, source)
                if receipt['status'] != 'VERIFIED':
                    raise ValueError('Source preflight did not verify')
                receipt_path = evidence_dir / iid / 'source_receipt.json'
                write_new(receipt_path, receipt)
                identity = {'image_id': image['id'], 'base_commit': row['base_commit'], 'archive_sha256': archive['sha256']}
                write_new(evidence_dir / iid / 'identity.json', {**identity, 'network': 'none', 'masked_paths': MASKED_TMPFS_PATHS})
                stage = 'runner'
                runner, runner_evidence = runner_choice(container, row, frozen_task)
                entries.append({**row, 'image': image, 'archive': archive,
                                'pre_install': {'wheel_sha256': WHEEL_SHA256, 'dataset_projection_sha256': proof.dataset_projection_sha256, 'spec': pre_install},
                                'integrity_preflight': {'status': 'VERIFIED', 'receipt_path': str(receipt_path.resolve()), 'receipt_sha256': sha(receipt_path)},
                                'runner': runner, 'origin': 'phase4_freeze' if frozen_task else 'prepared',
                                'dataset_projection_row': row, 'preflight_identity': identity, 'runner_provenance': runner_evidence})
        except Exception as exc:
            failures.append({'instance_id': iid, 'stage': stage, 'reason': str(exc)})
        finally:
            timing.append({'instance_id': iid, 'seconds': round(time.monotonic() - started, 6)})
            print(json.dumps({'task': iid, 'event': 'end', 'seconds': timing[-1]['seconds'],
                              'failure': failures[-1] if failures and failures[-1]['instance_id'] == iid else None}), flush=True)
    write_new(evidence_dir / 'failures.json', failures)
    write_new(evidence_dir / 'eligibility.json', eligible)
    write_new(evidence_dir / 'timing.json', timing)
    commit = run(['git', 'rev-parse', 'HEAD'], text=True).stdout.strip()
    registry = {'schema': 'task_spec_registry/1', 'cohort': cohort, 'built_by_commit': commit, 'tasks': entries}
    write_new(out, registry)
    return registry, failures, eligible
