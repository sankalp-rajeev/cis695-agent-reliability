"""Fix 9: base-commit source identity and generated-input stage evidence.

These probes use only stdlib/Git and never import task packages or collect tests.
"""

from __future__ import annotations

import base64
import contextvars
import hashlib
import json
import re
import shlex
import tarfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from reliability.verifier.pre_install import (
    PreInstallProofError,
    PreInstallSpec,
    corroborate,
    replay_source_edits,
    source_edit_commands,
)

CONFIG_NAMES = {'setup.cfg', 'tox.ini', 'pytest.ini', '.pytest.ini', 'pyproject.toml'}
GENERATED_INPUT_CHANGED = 'GENERATED_INPUT_CHANGED'
runtime_stage_var: contextvars.ContextVar[str] = contextvars.ContextVar('verifier_runtime_stage', default='initial')


class SourceIntegrityError(RuntimeError):
    """A pristine source mismatch aborts this executor version's attempt."""

    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__('Source integrity mismatch: ' + ', '.join(
            row['path'] + ' (' + row['reason'] + ')' for row in receipt['mismatches']))


@dataclass(frozen=True)
class BaseSourceSpec:
    base_commit: str
    archive_path: Path
    archive_sha256: str
    pre_install: PreInstallSpec | None = None


class SourceArchive:
    def __init__(self, spec):
        self.spec = spec
        digest = hashlib.sha256()
        with spec.archive_path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != spec.archive_sha256:
            raise ValueError('Frozen archive SHA-256 mismatch')
        with tarfile.open(spec.archive_path) as archive:
            self.members = {}
            for member in archive:
                if member.isfile() and member.name.startswith('testbed/'):
                    name = member.name[8:]
                    if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                        raise ValueError('Unsafe archive source path')
                    self.members[name] = member.name
        self.paths = tuple(name for name in self.members if name.endswith('.py')
                           or name == 'bin/test' or PurePosixPath(name).name in CONFIG_NAMES)

    def read_many(self, paths):
        with tarfile.open(self.spec.archive_path) as archive:
            return {path: archive.extractfile(self.members[path]).read()
                    for path in paths if path in self.members}


# Python 3.6 compatible: runs in the unchanged historical task interpreter.
_SOURCE_PROBE = r'''
import base64, hashlib, io, json, os, pathlib, re, subprocess, tarfile, tempfile
request = json.load(open('/tmp/verifier_source_request.json'))
root = os.getcwd()
def git(args, environment=None, data=None):
    return subprocess.check_output(['git'] + args, env=environment, input=data, stderr=subprocess.PIPE)
base = git(['rev-parse', '--verify', request['base_commit'] + '^{commit}']).decode().strip()
entries = {}
for line in git(['ls-tree', '-r', '-z', base]).split(b'\0'):
    if line:
        metadata, name = line.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        if kind == 'blob' and mode in ('100644', '100755'):
            entries[name.decode()] = oid
objects = os.path.abspath(git(['rev-parse', '--git-path', 'objects']).decode().strip())
with tempfile.TemporaryDirectory(prefix='verifier-base-attributes-') as temporary:
    isolated = os.path.join(temporary, 'source.git')
    git(['init', '--bare', '--template=', isolated])
    environment = dict(os.environ)
    for key in list(environment):
        if key.startswith('GIT_CONFIG_KEY_') or key.startswith('GIT_CONFIG_VALUE_'):
            del environment[key]
    environment.update(GIT_DIR=isolated, GIT_WORK_TREE=root, GIT_OBJECT_DIRECTORY=objects,
        GIT_INDEX_FILE=os.path.join(temporary, 'index'), GIT_CONFIG_GLOBAL='/dev/null',
        GIT_CONFIG_SYSTEM='/dev/null', GIT_CONFIG_NOSYSTEM='1', GIT_ATTR_NOSYSTEM='1',
        GIT_CONFIG_COUNT='0')
    # A new Git directory excludes .git/info/attributes. The index is exactly
    # the base tree, so patched/worktree .gitattributes cannot grant exceptions.
    git(['-c', 'core.bare=false', 'read-tree', base], environment)
    refs = git(['for-each-ref', '--format=%(objectname) %(refname)']).decode().splitlines()
    if refs:
        updates = ''.join('update ' + line.split(' ', 1)[1] + ' ' + line.split(' ', 1)[0] + '\n' for line in refs)
        git(['update-ref', '--stdin'], environment, updates.encode())
    head = git(['rev-parse', 'HEAD']).decode().strip()
    try:
        symbolic = git(['symbolic-ref', '-q', 'HEAD']).decode().strip()
    except subprocess.CalledProcessError:
        symbolic = ''
    if symbolic:
        git(['symbolic-ref', 'HEAD', symbolic], environment)
    else:
        git(['update-ref', '--no-deref', 'HEAD', head], environment)
    paths = sorted(entries)
    values = git(['-c', 'core.bare=false', '-c', 'core.attributesFile=/dev/null',
                  'check-attr', '--cached', '-z', '--stdin', 'export-subst'], environment,
                 ('\0'.join(paths) + '\0').encode()).decode().split('\0')
    exported = sorted(values[i] for i in range(0, len(values)-2, 3) if values[i+2] == 'set')
    expansion = {}
    if exported:
        raw = git(['-c', 'core.bare=false', '-c', 'core.attributesFile=/dev/null',
                   'archive', '--format=tar', base, '--'] + exported, environment)
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            expansion = dict((m.name, archive.extractfile(m).read()) for m in archive if m.isfile())
    def describe_expansion(fmt, override=None):
        match = re.fullmatch(br'%\(describe(?::([^)]*))?\)', fmt)
        if not match:
            return None
        command = ['describe']
        for option in (match.group(1) or b'').decode().split(','):
            if not option:
                continue
            key, value = option.split('=', 1)
            if key == 'tags' and value in ('true', 'false'):
                if value == 'true':
                    command.append('--tags')
            elif key == 'abbrev' and value.isdigit():
                command.append('--abbrev=' + value)
            elif key in ('match', 'exclude'):
                command.append('--' + key + '=' + value)
            else:
                raise ValueError('Unsupported describe format option: ' + option)
        if override is not None:
            if any(arg.startswith('--abbrev=') for arg in command):
                raise ValueError('Cannot override an explicit describe abbreviation')
            command.append('--abbrev=' + str(override))
        command.append(base)
        try:
            value = git(command, environment).rstrip(b'\n')
        except subprocess.CalledProcessError as exc:
            if b'No names found' in exc.stderr or b'No tags can describe' in exc.stderr:
                value = b''
            else:
                raise
        return value, command

    def supported_export(blob, native, path):
        # Older image Git releases cannot expand %(describe:...). Do not
        # accept arbitrary text: resolve exactly that pretty-format expression
        # through its equivalent read-only Git describe command and preserve
        # all literal bytes. Other formats still use native Git pretty output.
        parts, offset, fallbacks = [], 0, []
        for match in re.finditer(br'\$Format:([^$\r\n]*)\$', blob):
            parts.append(blob[offset:match.start()])
            fmt = match.group(1)
            value = git(['show', '-s', '--format=format:' + fmt.decode(), base], environment)
            if value == fmt:
                fallback = describe_expansion(fmt, request.get('describe_abbrev_overrides', {}).get(path, {}).get(fmt.decode()))
                if fallback is not None:
                    value, command = fallback
                    fallbacks.append(dict(format=fmt.decode(), command=command,
                                          value_b64=base64.b64encode(value).decode()))
            parts.append(value)
            offset = match.end()
        parts.append(blob[offset:])
        return (b''.join(parts) if fallbacks else native), fallbacks

    records = {}
    proof_paths = set(request.get('pre_install_paths', []))
    for name in sorted(set(request['files']) | set(exported) | proof_paths):
        absolute = os.path.realpath(name)
        error = ''
        try:
            if os.path.commonpath([root, absolute]) != root:
                raise ValueError('source symlink outside repository')
            data = pathlib.Path(name).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
        except (OSError, ValueError) as exc:
            data, digest, error = None, None, str(exc)
        row = dict(observed_sha256=digest, error=error, export_subst=name in exported)
        if name in exported or name in proof_paths or digest != request['files'].get(name):
            row['observed_b64'] = base64.b64encode(data).decode() if data is not None else None
        if (name in exported or name in proof_paths or digest != request['files'].get(name)) and name in entries:
            blob = git(['cat-file', 'blob', entries[name]])
            row['base_blob_b64'] = base64.b64encode(blob).decode()
            row['base_blob_sha256'] = hashlib.sha256(blob).hexdigest()
        if name in exported:
            expected, fallbacks = supported_export(blob, expansion[name], name) if name in expansion else (None, [])
            row['git_archive_b64'] = base64.b64encode(expected).decode() if expected is not None else None
            row['expansion_method'] = 'native git archive plus equivalent git describe for unsupported pretty format' if fallbacks else 'native git archive'
            row['describe_fallback_proofs'] = fallbacks
            if fallbacks:
                row['native_git_archive_b64'] = base64.b64encode(expansion[name]).decode()
        records[name] = row
print(json.dumps(dict(base_commit=base, export_subst_files=exported, records=records,
    attribute_authority='base tree .gitattributes only; isolated index/Git directory; no global/system/info attributes',
    tests_executed=0, collection_performed=False)))
'''


def only_format_expansions(blob: bytes, expanded: bytes) -> bool:
    """All literal bytes must survive; Git independently supplies exact expansions."""
    pattern = rb'\$Format:[^$\r\n]*\$'
    parts, position = [], 0
    for match in re.finditer(pattern, blob):
        parts.extend((re.escape(blob[position:match.start()]), rb'.*?'))
        position = match.end()
    parts.append(re.escape(blob[position:]))
    return re.fullmatch(b''.join(parts), expanded, flags=re.DOTALL) is not None


def compare_source(archive_files: dict[str, bytes], probe: dict, pre_install_expected=None) -> dict:
    receipts, mismatches = [], []
    for path, row in probe['records'].items():
        archived = archive_files.get(path)
        archive_sha = hashlib.sha256(archived).hexdigest() if archived is not None else None
        reason, accepted, pre_accepted = '', False, False
        if row['export_subst']:
            blob = base64.b64decode(row['base_blob_b64'])
            expanded = base64.b64decode(row['git_archive_b64']) if row.get('git_archive_b64') is not None else None
            if row['observed_sha256'] != row['base_blob_sha256']:
                reason = 'image_differs_from_base_blob'
            elif archived is None or expanded is None:
                reason = 'export_subst_archive_entry_missing'
            elif not only_format_expansions(blob, expanded):
                reason = 'archive_transform_exceeds_format_placeholders'
            elif archived != expanded:
                reason = 'archive_differs_from_base_git_archive'
            else:
                accepted = archive_sha != row['observed_sha256']
        elif path in (pre_install_expected or {}):
            expected = pre_install_expected[path]
            if archive_sha != row.get('base_blob_sha256'):
                reason = 'pre_install_archive_differs_from_base_blob'
            elif row['observed_sha256'] != expected['expected_sha256']:
                reason = 'pre_install_image_differs_from_exact_command_effects'
            else:
                pre_accepted = archive_sha != row['observed_sha256']
        elif archived is None or row['observed_sha256'] != archive_sha:
            reason = 'non_export_subst_source_mismatch'
        receipt = {'path': path, 'archive_sha256': archive_sha, **row,
                   'accepted_export_subst_difference': accepted,
                   'accepted_pre_install_difference': pre_accepted, 'reason': reason}
        if path in (pre_install_expected or {}):
            receipt['pre_install_replay'] = pre_install_expected[path]
        if reason or archive_sha != row['observed_sha256']:
            receipt['archive_b64'] = base64.b64encode(archived).decode() if archived is not None else None
        if reason:
            mismatches.append(receipt)
        receipts.append(receipt)
    return {'status': 'MISMATCH' if mismatches else 'VERIFIED', 'base_commit': probe['base_commit'],
            'attribute_authority': probe['attribute_authority'], 'export_subst_files': probe['export_subst_files'],
            'checked_files': len(receipts), 'accepted_export_subst_differences': [r['path'] for r in receipts if r['accepted_export_subst_difference']],
            'accepted_pre_install_differences': [r['path'] for r in receipts if r['accepted_pre_install_difference']],
            'mismatches': mismatches, 'files': receipts, 'tests_executed': 0, 'collection_performed': False}


def describe_abbreviation_queries(archive_files, probe):
    """Infer a default abbreviation length; Git must independently prove its value.

    Git's automatic describe abbreviation varies with object-database size.
    An explicit format abbreviation cannot be overridden.
    """
    queries = {}
    for path, row in probe['records'].items():
        archived = archive_files.get(path)
        if archived is None or not row.get('describe_fallback_proofs'):
            continue
        if archived == base64.b64decode(row['git_archive_b64']):
            continue
        blob = base64.b64decode(row['base_blob_b64'])
        matches = list(re.finditer(rb'\$Format:([^$\r\n]*)\$', blob))
        pieces, offset = [], 0
        for match in matches:
            pieces.extend((re.escape(blob[offset:match.start()]), rb'(.*?)'))
            offset = match.end()
        pieces.append(re.escape(blob[offset:]))
        values = re.fullmatch(b''.join(pieces), archived, flags=re.DOTALL)
        if values is None:
            continue
        allowed = {item['format'] for item in row['describe_fallback_proofs']}
        for token, value in zip(matches, values.groups()):
            fmt = token.group(1).decode()
            suffix = re.search(rb'-[0-9]+-g([0-9a-f]{4,40})$', value)
            if fmt in allowed and 'abbrev=' not in fmt and suffix:
                abbreviated = suffix.group(1).decode()
                if probe['base_commit'].startswith(abbreviated):
                    queries.setdefault(path, {})[fmt] = len(abbreviated)
    return queries


def verify_base_source(container, spec: BaseSourceSpec, *, halt=True):
    archive = SourceArchive(spec)
    sources = archive.read_many(archive.paths)
    provenance, edits = None, None
    if spec.pre_install is not None:
        try:
            provenance = spec.pre_install.resolve()
            if spec.pre_install.base_commit != spec.base_commit or (
                hasattr(container, 'instance_id') and container.instance_id != spec.pre_install.instance_id
            ):
                raise ValueError('pre_install task/base identity mismatch')
            edits = source_edit_commands(spec.pre_install.commands)
        except (ValueError, OSError, StopIteration) as exc:
            receipt = {'status': 'MISMATCH', 'base_commit': spec.base_commit,
                       'mismatches': [{'path': '<pre_install_provenance>', 'reason': str(exc)}],
                       'pre_install': provenance, 'tests_executed': 0, 'collection_performed': False}
            raise SourceIntegrityError(receipt) from exc
    proof_paths = [p for _, _, p in edits] if edits else []
    sources.update(archive.read_many(proof_paths))
    request = {'base_commit': spec.base_commit,
               'pre_install_paths': proof_paths,
               'files': {p: hashlib.sha256(raw).hexdigest() for p, raw in sources.items()}}
    rc, message = container.exec_input('cat > /tmp/verifier_source_request.json', json.dumps(request))
    if rc:
        raise RuntimeError('Source-probe request upload failed: ' + message)
    rc, raw = container.exec('python -c ' + shlex.quote(_SOURCE_PROBE), timeout_s=180)
    if rc:
        raise RuntimeError('Base-only source probe failed: ' + raw[-4000:])
    probe = json.loads(raw)
    sources.update(archive.read_many(probe['export_subst_files']))
    overrides = describe_abbreviation_queries(sources, probe)
    if overrides:
        request['describe_abbrev_overrides'] = overrides
        rc, message = container.exec_input('cat > /tmp/verifier_source_request.json', json.dumps(request))
        if rc:
            raise RuntimeError('Describe proof upload failed: ' + message)
        rc, raw = container.exec('python -c ' + shlex.quote(_SOURCE_PROBE), timeout_s=180)
        if rc:
            raise RuntimeError('Explicit Git describe proof failed: ' + raw[-4000:])
        probe = json.loads(raw)
    expected, proof_error = {}, None
    if provenance is not None:
        provenance['image_corroboration'] = {'status': 'not required: no source-edit proof'}
        provenance['replay'] = 'not needed; unsupported commands cannot justify differences' if edits is None else 'no commands'
        if edits:
            try:
                expected = replay_source_edits(edits, probe)
                provenance['replay'] = 'exact ordered commands in isolated host temporary directory; image unmodified'
                if any(v['expected_sha256'] != v['base_blob_sha256'] for v in expected.values()):
                    provenance['image_corroboration'] = corroborate(container, spec.pre_install.commands)
            except (ValueError, OSError) as exc:
                proof_error = str(exc)
                if isinstance(exc, PreInstallProofError):
                    provenance['image_corroboration'] = exc.evidence
    receipt = compare_source(sources, probe, expected)
    receipt['pre_install'] = provenance
    if proof_error:
        receipt['mismatches'].append({'path': '<pre_install_proof>', 'reason': proof_error})
        receipt['status'] = 'MISMATCH'
    receipt['explicit_describe_abbreviation_queries'] = overrides
    receipt['archive_sha256'] = spec.archive_sha256
    if halt and receipt['mismatches']:
        raise SourceIntegrityError(receipt)
    return receipt


_GENERATED_PROBE = r'''
import hashlib, json, os, pathlib, re, subprocess
root = os.path.realpath(os.getcwd())
tracked = set(subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0'))
paths = set(json.loads(open('/tmp/verifier_generated_request.json').read()))
for directory, folders, files in os.walk('.'):
    folders[:] = [name for name in folders if name not in ('.git', '__pycache__')]
    for name in files:
        if re.search(r'(?i)version.*\.py$', name):
            relative = os.path.normpath(os.path.join(directory, name))
            if relative not in tracked:
                paths.add(relative)
result, errors = {}, {}
for path in sorted(paths):
    try:
        if os.path.commonpath([root, os.path.realpath(path)]) != root:
            raise ValueError('version source symlink outside repository')
        result[path] = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() if pathlib.Path(path).is_file() else None
    except (OSError, ValueError) as exc:
        result[path] = None
        errors[path] = str(exc)
print(json.dumps(dict(files=result, errors=errors, scope='all untracked version-named Python modules, including ignored files', tests_executed=0, collection_performed=False)))
'''


def generated_inventory(container, previous=(), *, timeout_s=60):
    rc, message = container.exec_input('cat > /tmp/verifier_generated_request.json', json.dumps(list(previous)), timeout_s=timeout_s)
    if rc:
        raise RuntimeError('Generated inventory upload failed: ' + message)
    rc, raw = container.exec('python -c ' + shlex.quote(_GENERATED_PROBE), timeout_s=timeout_s)
    if rc:
        raise RuntimeError('Generated inventory failed: ' + raw[-2000:])
    return json.loads(raw)


@dataclass
class GeneratedInputAudit:
    snapshot: object | None
    snapshots: list = field(default_factory=list)
    changes: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def capture(self, stage, boundary):
        if self.snapshot is None:
            return
        previous = self.snapshots[-1]['files'] if self.snapshots else {}
        try:
            value = self.snapshot(tuple(previous))
            current = value['files']
            self.errors.extend({'stage': stage, 'boundary': boundary, 'path': p, 'message': m}
                               for p, m in value.get('errors', {}).items())
            pinned = value.get('pinned_files')
            if not self.snapshots and pinned is not None:
                previous = pinned
            if self.snapshots or pinned is not None:
                for path in sorted(previous.keys() | current.keys()):
                    if previous.get(path) != current.get(path):
                        self.changes.append({'stage': stage, 'boundary': boundary, 'path': path,
                                             'before': previous.get(path), 'after': current.get(path)})
            self.snapshots.append({'stage': stage, 'boundary': boundary, 'files': current})
        except (RuntimeError, TimeoutError, ValueError, OSError) as exc:
            self.errors.append({'stage': stage, 'boundary': boundary, 'message': str(exc)})

    def stage(self, name, action):
        self.capture(name, 'before')
        try:
            return action()
        finally:
            self.capture(name, 'after')

    @property
    def flags(self):
        return ((GENERATED_INPUT_CHANGED,) if self.changes else ()) + (
            ('GENERATED_INPUT_AUDIT_ERROR',) if self.errors else ())

    def to_dict(self):
        return {'snapshots': self.snapshots, 'changes': self.changes, 'errors': self.errors,
                'flags': list(self.flags), 'halting': False,
                'availability': 'AUDITED' if self.snapshot is not None else 'STRUCTURED_EXECUTOR_NO_CONTAINER'}
