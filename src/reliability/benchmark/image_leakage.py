"""Audit-only image request preparation and safe result serialization."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from reliability.agent.isolation import MASKED_TMPFS_PATHS, docker_bin
from reliability.benchmark.image_probe import apply_hunks, version_from_text
from reliability.benchmark.leakage import import_name_for_instance, probes_from_oracle
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive

ROOT = Path(__file__).resolve().parents[3]
PIN_FILE = ROOT / 'reports/v2_scg_paired/ubuntu_progress_20261105/archive_references.json'
ARCHIVES = Path('/home/sankalp/cg_repos/task_archives')


def archive_for(task, pins=None):
    pins = json.loads(PIN_FILE.read_text())['archives'] if pins is None else pins
    pin = next((p for p in pins if p['instance_id'] == task.instance_id), None)
    path = ARCHIVES / (task.instance_id + '.tar')
    origin = 'audit-initial-inventory'
    if not path.is_file():
        path = ROOT/'runs/leakage_gaps/source_archives'/(task.instance_id + '.tar')
        origin = 'image-pinned-base-git-archive'
    if pin is None:
        # Freeze a new digest for the 17 tasks omitted by the previous preparation.
        # Its origin is explicit in the report, rather than claiming an old pin.
        pin = dict(instance_id=task.instance_id, base_commit=task.base_commit,
                   path=str(path), sha256=hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(),
                   pin_origin=origin)
    else:
        pin = dict(pin, pin_origin='historical-archive-references')
    if pin['base_commit'] != task.base_commit:
        raise ValueError('archive base identity mismatch')
    spec = BaseSourceSpec(task.base_commit, path, pin['sha256'])
    return SourceArchive(spec), pin


def base_version(archive, import_name):
    candidates = [import_name + '/' + name for name in
                  ('__version__.py', '_version.py', 'version.py', '__init__.py',
                   'release.py', '__pkginfo__.py')]
    candidates += ['lib/' + p for p in candidates] + ['src/' + p for p in candidates]
    candidates += ['src/_pytest/_version.py', 'src/_pytest/__init__.py',
                   '_pytest/_version.py', '_pytest/__init__.py'] if import_name == 'pytest' else []
    sources = archive.read_many(candidates + ['setup.py', 'setup.cfg'])
    for name in candidates:
        value = version_from_text(sources.get(name, b'').decode(errors='replace'))
        if value:
            return value
    text = sources.get('setup.py', b'').decode(errors='replace')
    parts = {}
    for key in ['MAJOR', 'MINOR', 'MICRO']:
        match = re.search(r'(?m)^' + key + r'\s*=\s*(\d+)', text)
        if match:
            parts[key] = match.group(1)
    if len(parts) == 3:
        return '.'.join(parts.values())
    match = re.search(r'(?m)^version\s*=\s*([^\s\'"]+)', sources.get('setup.cfg', b'').decode(errors='replace'))
    if match and not match.group(1).startswith(('attr:', 'file:')):
        return match.group(1)
    return version_from_text(text)


def post_images(archive, patch):
    """Reconstruct post-images in memory; never apply the gold patch to disk."""
    from unidiff import PatchSet
    outputs = []
    for file in PatchSet(patch):
        if file.is_removed_file:
            continue
        path = file.path
        original = io.StringIO(archive.read_many([path]).get(path, b'').decode()).readlines()
        try:
            result = apply_hunks(original, [dict(start=h.source_start,
                lines=[(line.line_type, line.value) for line in h]) for h in file])
        except RuntimeError:
            raise ValueError('post-image context mismatch') from None
        outputs.append(base64.b64encode(result).decode())
    return outputs


def gold_hunks(patch):
    from unidiff import PatchSet
    return [dict(path=f.path, added=f.is_added_file,
        hunks=[dict(start=h.source_start, lines=[(line.line_type, line.value)
            for line in h]) for h in f]) for f in PatchSet(patch) if not f.is_removed_file]


def prepare_gold_requests(manifest, directory):
    """Exact Git-base recheck, independent of archive export transformations."""
    from reliability.benchmark.loader import load_instance, load_verified
    dataset = load_verified()
    for row in csv.DictReader(Path(manifest).open()):
        task, oracle = load_instance(row['instance_id'], dataset)
        request = dict(instance_id=task.instance_id, base_commit=task.base_commit,
                       post_image_hunks=gold_hunks(oracle.patch))
        (directory/(task.instance_id+'.json')).write_text(json.dumps(request))


def prepare_requests(manifest, directory):
    from reliability.benchmark.loader import load_instance, load_verified
    dataset = load_verified()
    requests = []
    for row in csv.DictReader(Path(manifest).open()):
        task, oracle = load_instance(row['instance_id'], dataset)
        if task.base_commit != row['base_commit']:
            raise ValueError('cohort base mismatch')
        archive, pin = archive_for(task)
        probes = probes_from_oracle(oracle, task.problem_statement)
        import_name = import_name_for_instance(task.instance_id)
        version = base_version(archive, import_name)
        # Archive exports can transform bytes outside a patch hunk. Always
        # derive exact gold post-images from git show BASE:path in the image.
        post, hunks = [], gold_hunks(oracle.patch)
        request = dict(instance_id=task.instance_id, base_commit=task.base_commit,
            package=task.repo.split('/')[-1], import_name=import_name,
            base_version=version, masked_paths=list(MASKED_TMPFS_PATHS),
            patch_lines=list(probes.patch_lines),
            all_lines=list(probes.patch_lines + probes.test_patch_lines),
            post_images_b64=post, post_image_hunks=hunks, archive=pin)
        path = directory / (task.instance_id + '.json')
        path.write_text(json.dumps(request))
        requests.append(dict(instance_id=task.instance_id, base_version=version, archive=pin))
    return requests


def docker_command(image, probe_path):
    """Only new, anonymous, short-lived containers; no daemon container queries."""
    return [docker_bin(), 'run', '--rm', '--network', 'none', '--read-only',
            '--pull', 'never', '--cpu-shares', '256', '-i',
            '--mount', 'type=bind,src=' + str(probe_path.resolve()) + ',dst=/audit_probe.py,readonly',
            '--entrypoint', '/opt/miniconda3/bin/python', image, '/audit_probe.py']


def public_image_result(raw, request, image):
    # Commit timestamps are hashes and integers, kept for trajectory correlation.
    if raw.get('checks', {}).get('git', {}).get('status') == 'complete':
        result = raw['checks']['git']['result']
        result['commit_timestamps'] = {h: t for h, t in result['commit_timestamps'].items()
                                      if h in result['future_commit_hashes']}
    for name, check in raw.get('checks', {}).items():
        exposed = (name == 'git' and check.get('result', {}).get('future_object_count', 0) > 0
                   or name == 'packages' and any(c.get('different_from_base') for c in check.get('result', {}).get('copies', [])))
        check['severity'] = 'exposed-copy' if exposed else 'review'
        check['rule'] = {'git': 'image-git-object-inventory', 'packages': 'image-package-inventory',
                         'base_probes': 'legacy-base-probe-subtraction'}[name]
    return dict(raw, instance_id=request['instance_id'], image=image, base_commit=request['base_commit'],
                base_version=request['base_version'], archive=request['archive'])


def run_image(image, request, *, runner=subprocess.run):
    process = runner(docker_command(image, Path(__file__).with_name('image_probe.py')),
        input=json.dumps(request), capture_output=True, text=True, timeout=900, check=False)
    if process.returncode:
        return dict(instance_id=request['instance_id'], image=image, status='incomplete',
                    rule='docker-probe-failed', returncode=process.returncode)
    raw = json.loads(process.stdout)
    checks = raw.get('checks', {})
    if all(checks.get(c, {}).get('status') == 'complete' for c in ['git', 'packages']):
        supplement_request = dict(request, copies=checks['packages']['result']['copies'],
                                  future_commit_hashes=checks['git']['result']['future_commit_hashes'])
        extra_process = runner(docker_command(image, Path(__file__).with_name('image_probe.py')) + ['--supplement'],
            input=json.dumps(supplement_request), capture_output=True, text=True, timeout=180, check=False)
        if extra_process.returncode:
            return dict(instance_id=request['instance_id'], image=image, status='incomplete',
                        rule='image-supplement-failed')
        extra = json.loads(extra_process.stdout)
        request = dict(request, base_version=extra['base_version'])
        raw['base_version_origin'] = extra['base_version_origin']
        checks['packages']['result']['copies'] = extra['copies']
        checks['git']['result']['future_commit_details'] = extra['future_commit_details']
    return public_image_result(raw, request, image)
