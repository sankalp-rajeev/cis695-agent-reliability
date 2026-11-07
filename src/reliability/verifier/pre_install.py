"""Label-free, AST-only SWE-bench 4.0.4 pre_install provenance and byte proofs.

The snapshot is never installed/imported. Only pre_install fields are evaluated;
the small interpreter below cannot execute Python calls from the wheel.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import shlex
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

WHEEL_SHA256 = '4e315ac60ff7b5b7186592b84d22df9befd898bba296a6b9665fdb3487fcd8f7'
WHEEL_URL = 'https://files.pythonhosted.org/packages/e4/65/bf9f45764317150c92fe9a0c37a0c4556c13eecc8878d4f92ffb3d31c861/swebench-4.0.4-py3-none-any.whl'
CONSTANTS_PATH = 'swebench/harness/constants/python.py'
SCRIPT_PATHS = ('/root/setup_repo.sh', '/root/setup_env.sh', '/setup_repo.sh', '/setup_env.sh',
                '/tmp/setup_repo.sh', '/tmp/setup_env.sh')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class _PreInstallAST:
    def __init__(self, source, repo):
        self.tree = ast.parse(source)
        mapping = next(n.value for n in self.tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id in ('MAP_REPO_VERSION_TO_SPECS', 'MAP_REPO_VERSION_TO_SPECS_PY') for t in n.targets))
        self.name = next(v.id for k, v in zip(mapping.keys, mapping.values)
                         if isinstance(k, ast.Constant) and k.value == repo and isinstance(v, ast.Name))
        self.env = {}

    def value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.env[node.id]
        if isinstance(node, (ast.List, ast.Tuple)):
            return [self.value(n) for n in node.elts]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.value(node.left) + self.value(node.right)
        if isinstance(node, ast.Subscript):
            return self.value(node.value)[self.value(node.slice)]
        if isinstance(node, ast.Dict):
            # Spec dictionaries: never evaluate install/test_cmd/packages or any
            # other fields. Version dictionaries/comprehensions contain specs.
            result = {}
            for key, value in zip(node.keys, node.values):
                if key is None:
                    result.update(self.value(value))
                    continue
                name = self.value(key)
                if name == 'pre_install' or isinstance(value, (ast.Dict, ast.DictComp)):
                    result[name] = self.value(value)
            return result
        if isinstance(node, ast.DictComp):
            assert len(node.generators) == 1
            gen = node.generators[0]
            assert isinstance(gen.target, ast.Name) and not gen.ifs and not gen.is_async
            result = {}
            for item in self.value(gen.iter):
                self.env[gen.target.id] = item
                result[self.value(node.key)] = self.value(node.value)
            return result
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = self.value(node.left), self.value(node.comparators[0])
            if isinstance(node.ops[0], ast.In):
                return left in right
            if isinstance(node.ops[0], ast.Eq):
                return left == right
        raise ValueError('Unsupported pre_install AST: ' + ast.dump(node)[:150])

    def relevant(self, node):
        if not any(isinstance(n, ast.Name) and n.id == self.name for n in ast.walk(node)):
            return False
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            return (isinstance(target, ast.Name) and target.id == self.name) or (
                isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                and target.slice.value == 'pre_install')
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            return isinstance(call.func, ast.Attribute) and (
                (isinstance(call.func.value, ast.Name) and call.func.value.id == self.name and call.func.attr == 'update')
                or (call.func.attr == 'extend' and isinstance(call.func.value, ast.Subscript)
                    and isinstance(call.func.value.slice, ast.Constant) and call.func.value.slice.value == 'pre_install'))
        if isinstance(node, ast.AugAssign):
            return isinstance(node.target, ast.Subscript) and isinstance(node.target.slice, ast.Constant) and node.target.slice.value == 'pre_install'
        return isinstance(node, (ast.For, ast.If)) and any(self.relevant(n) for n in node.body + node.orelse)

    def statements(self, nodes):
        for node in nodes:
            if not self.relevant(node):
                continue
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                value = self.value(node.value)
                if isinstance(target, ast.Name):
                    self.env[target.id] = value
                else:
                    self.value(target.value)[self.value(target.slice)] = value
            elif isinstance(node, ast.For):
                assert isinstance(node.target, ast.Name) and not node.orelse
                for item in self.value(node.iter):
                    self.env[node.target.id] = item
                    self.statements(node.body)
            elif isinstance(node, ast.If):
                self.statements(node.body if self.value(node.test) else node.orelse)
            elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
                self.value(node.target.value)[self.value(node.target.slice)] += self.value(node.value)
            elif isinstance(node, ast.Expr):
                call = node.value
                assert not call.keywords and len(call.args) == 1
                receiver, value = self.value(call.func.value), self.value(call.args[0])
                if call.func.attr == 'update':
                    receiver.update(value)
                elif call.func.attr == 'extend':
                    receiver.extend(value)
                else:
                    raise ValueError('Unsupported pre_install mutation')
            else:
                raise ValueError('Unsupported pre_install statement')  # noqa: TRY004


def parse_pre_install(source, repo, version):
    try:
        reader = _PreInstallAST(source, repo)
        reader.statements(reader.tree.body)
        spec = reader.env[reader.name][version]
        commands = spec.get('pre_install', [])
        if not isinstance(commands, list) or not all(isinstance(c, str) for c in commands):
            raise ValueError('pre_install must be an ordered string list')
        return tuple(commands)
    except (KeyError, StopIteration, AssertionError) as exc:
        raise ValueError('Missing or unsupported pre_install spec: ' + repo + '@' + version) from exc


@dataclass(frozen=True)
class PreInstallSpec:
    instance_id: str
    repo: str
    version: str
    base_commit: str
    commands: tuple[str, ...]
    wheel_path: Path
    dataset_projection: Path
    dataset_projection_sha256: str

    def resolve(self):
        raw = self.dataset_projection.read_bytes()
        if digest(raw) != self.dataset_projection_sha256:
            raise ValueError('Dataset projection hash mismatch')
        dataset = json.loads(raw)
        if set(dataset['columns_read']) != {'instance_id', 'repo', 'base_commit', 'version'}:
            raise ValueError('Dataset projection contains unapproved columns')
        row = next(r for r in dataset['tasks'] if r['instance_id'] == self.instance_id)
        if row != {'instance_id': self.instance_id, 'repo': self.repo, 'base_commit': self.base_commit, 'version': self.version}:
            raise ValueError('Wrong task/version for pre_install proof')
        wheel = self.wheel_path.read_bytes()
        if digest(wheel) != WHEEL_SHA256:
            raise ValueError('SWE-bench snapshot wheel SHA-256 mismatch')
        with zipfile.ZipFile(self.wheel_path) as archive:
            source = archive.read(CONSTANTS_PATH)
        commands = parse_pre_install(source, self.repo, self.version)
        if commands != self.commands:
            raise ValueError('Command list differs from pinned task/version spec')
        return {'swebench_version': '4.0.4', 'project_swebench_version': '5.0.2',
                'wheel_url': WHEEL_URL, 'pypi_url': 'https://pypi.org/project/swebench/4.0.4/',
                'wheel_sha256': WHEEL_SHA256, 'constants_path': CONSTANTS_PATH,
                'constants_sha256': digest(source), 'spec_key': [self.repo, self.version, 'pre_install'],
                'constants_mapping': 'MAP_REPO_VERSION_TO_SPECS_PY (Python constituent of MAP_REPO_VERSION_TO_SPECS)',
                'commands': list(commands), 'dataset_arrow_sha256': dataset['arrow_sha256'],
                'dataset_snapshot': dataset['cache_snapshot'], 'dataset_projection_sha256': digest(raw),
                'dataset_row': row}


def load_specs(wheel_path, projection_path):
    if digest(wheel_path.read_bytes()) != WHEEL_SHA256:
        raise ValueError('SWE-bench snapshot wheel SHA-256 mismatch')
    raw = projection_path.read_bytes()
    dataset = json.loads(raw)
    with zipfile.ZipFile(wheel_path) as archive:
        source = archive.read(CONSTANTS_PATH)
    specs = {}
    for row in dataset['tasks']:
        spec = PreInstallSpec(**row, commands=parse_pre_install(source, row['repo'], row['version']),
                              wheel_path=wheel_path, dataset_projection=projection_path,
                              dataset_projection_sha256=digest(raw))
        spec.resolve()  # A missing spec or wrong provenance is fatal, never [] by default.
        specs[spec.instance_id] = spec
    return specs


def source_edit_commands(commands):
    """Only literal, relative-file sed edits can be safely replayed on host.

    System/package/network commands are never run; they cannot justify a byte
    exemption. An unexplained difference with such a spec still halts.
    """
    result = []
    for command in commands:
        argv = shlex.split(command)
        if len(argv) != 4 or argv[:2] != ['sed', '-i']:
            return None
        path = PurePosixPath(argv[3])
        if path.is_absolute() or '..' in path.parts or str(path).startswith('-'):
            raise ValueError('Unsafe pre_install source path')
        result.append((command, argv, str(path)))
    return result


def corroborate(container, commands):
    code = "import pathlib,json; print(json.dumps({str(p):p.read_text() for p in map(pathlib.Path," + repr(SCRIPT_PATHS) + ") if p.is_file()}))"
    rc, raw = container.exec('python -c ' + shlex.quote(code))
    if rc:
        raise ValueError('Cannot read image build scripts: ' + raw[-1000:])
    scripts = json.loads(raw)
    if not scripts:
        return {'status': 'no image script', 'paths_checked': list(SCRIPT_PATHS), 'scripts': {}}
    # Harness repo setup scripts place pre_install between git cleanup and
    # installation. Compare the complete sed source-edit subsequence, not just
    # searching for the expected commands (which could conceal extra edits).
    found = [line.strip() for text in scripts.values() for line in text.splitlines()
             if line.strip().startswith('sed ')]
    result = {'status': 'MATCH' if found == list(commands) else 'MISMATCH',
              'paths_checked': list(SCRIPT_PATHS), 'extracted_commands': found,
              'scripts': {p: {'sha256': digest(text.encode()), 'content': text} for p, text in scripts.items()}}
    if result['status'] != 'MATCH':
        raise PreInstallProofError('Image pre_install command list disagrees with snapshot', result)
    return result


class PreInstallProofError(ValueError):
    def __init__(self, message, evidence):
        self.evidence = evidence
        super().__init__(message)


def replay_source_edits(edits, probe):
    paths = {p for _, _, p in edits}
    with tempfile.TemporaryDirectory(prefix='verifier-pre-install-') as temporary:
        root = Path(temporary)
        before = {}
        for path in paths:
            row = probe['records'].get(path, {})
            if not row.get('base_blob_b64'):
                raise ValueError('pre_install target not in base tree: ' + path)
            raw = base64.b64decode(row['base_blob_b64'])
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            before[path] = digest(raw)
        for _, argv, _ in edits:
            try:
                subprocess.run(argv, cwd=root, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'},
                               check=True, capture_output=True, timeout=30)
            except subprocess.SubprocessError as exc:
                raise ValueError('Exact pre_install replay failed: ' + str(exc)) from exc
        return {path: {'base_blob_sha256': before[path],
                       'expected_sha256': digest((root/path).read_bytes()),
                       'expected_b64': base64.b64encode((root/path).read_bytes()).decode()}
                for path in sorted(paths)}
