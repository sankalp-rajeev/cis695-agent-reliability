"""Exact source transforms from an AST-only snapshot, never task execution."""

import base64
import hashlib
import json
import zipfile
from dataclasses import replace

import pytest
from tests.unit.test_fix9_source_integrity import (  # noqa: F401
    LocalContainer,
    git,
    source_repo,
    spec_for,
)

from reliability.verifier import pre_install as module
from reliability.verifier.pre_install import (
    load_specs,
    parse_pre_install,
    replay_source_edits,
    source_edit_commands,
)
from reliability.verifier.source_integrity import SourceIntegrityError, verify_base_source

SOURCE = '''
raise RuntimeError("This must never execute")
SPECS = {k: {"pre_install": ["sed -i 's/value = 9/value = 10/' plain.py"],
             "test_cmd": forbidden_call(), "install": forbidden_call()}
         for k in ["1", "2"]}
for k in ["1"]:
    SPECS[k]["pre_install"].extend(["sed -i 's/old/new/' tox.ini"])
if "2" in ["2"]:
    SPECS["2"]["pre_install"] = ["sed -i 's/value = 9/value = 11/' plain.py"]
MAP_REPO_VERSION_TO_SPECS_PY = {"example/project": SPECS}
'''


@pytest.fixture
def prepared(source_repo, tmp_path, monkeypatch):  # noqa: F811
    root, _, _ = source_repo
    (root/'tox.ini').write_text('old\n')
    git(root, 'add', 'tox.ini')
    git(root, 'commit', '-qm', 'config')
    archive = root/'base.tar'
    archive.write_bytes(git(root, 'archive', '--format=tar', '--prefix=testbed/', 'HEAD'))
    wheel = root/'snapshot.whl'
    with zipfile.ZipFile(wheel, 'w') as z:
        z.writestr(module.CONSTANTS_PATH, SOURCE)
    monkeypatch.setattr(module, 'WHEEL_SHA256', hashlib.sha256(wheel.read_bytes()).hexdigest())
    projection = root/'metadata.json'
    projection.write_text(json.dumps({'columns_read':['instance_id','repo','base_commit','version'],
        'arrow_sha256':'opaque-snapshot-hash','cache_snapshot':'pinned-snapshot',
        'tasks':[{'instance_id':'task','repo':'example/project','base_commit':git(root,'rev-parse','HEAD').decode().strip(),'version':'1'}]}))
    spec = load_specs(wheel, projection)['task']

    class Container(LocalContainer):
        instance_id = 'task'
        def __init__(self, root):
            super().__init__(root)
            self.scripts = {}
        def exec(self, command, timeout_s=180):
            if '/root/setup_repo.sh' in command:
                return 0, json.dumps(self.scripts)
            return super().exec(command, timeout_s)

    return root, replace(spec_for(root, archive), pre_install=spec), Container(root)


def apply_image_edits(root):
    (root/'plain.py').write_text('value = 10\n')
    (root/'tox.ini').write_text('new\n')


def test_exact_ordered_effects_and_no_script_proof(prepared):
    root, spec, container = prepared
    apply_image_edits(root)
    receipt = verify_base_source(container, spec)
    assert receipt['status'] == 'VERIFIED'
    assert set(receipt['accepted_pre_install_differences']) == {'plain.py', 'tox.ini'}
    proof = receipt['pre_install']
    assert proof['swebench_version'] == '4.0.4'
    assert proof['spec_key'] == ['example/project','1','pre_install']
    assert proof['commands'] == list(spec.pre_install.commands)
    assert proof['image_corroboration']['status'] == 'no image script'
    assert proof['wheel_sha256'] == module.WHEEL_SHA256
    assert proof['dataset_arrow_sha256'] == 'opaque-snapshot-hash'
    assert (root/'plain.py').read_text() == 'value = 10\n'  # Proof never rewrites image.


@pytest.mark.parametrize('missing', ['all', 'one'])
def test_missing_command_effect_halts_even_when_no_raw_mismatch(prepared, missing):
    root, spec, container = prepared
    if missing == 'one':
        (root/'plain.py').write_text('value = 10\n')
    with pytest.raises(SourceIntegrityError, match='exact_command_effects'):
        verify_base_source(container, spec)


def test_extra_image_edit_beyond_commands_halts(prepared):
    root, spec, container = prepared
    apply_image_edits(root)
    with (root/'plain.py').open('a') as stream:
        stream.write('extra = True\n')
    with pytest.raises(SourceIntegrityError, match='exact_command_effects'):
        verify_base_source(container, spec)


@pytest.mark.parametrize('change', ['commands', 'version', 'base', 'dataset', 'wheel'])
def test_wrong_provenance_or_version_command_list_halts(prepared, change):
    root, spec, container = prepared
    apply_image_edits(root)
    proof = spec.pre_install
    if change == 'commands':
        proof = replace(proof, commands=parse_pre_install(SOURCE, 'example/project', '2'))
    elif change == 'version':
        proof = replace(proof, version='2')
    elif change == 'base':
        spec = replace(spec, base_commit='0'*40)
    elif change == 'dataset':
        proof.dataset_projection.write_text(proof.dataset_projection.read_text()+' ')
    else:
        with proof.wheel_path.open('ab') as stream:
            stream.write(b'changed')
    with pytest.raises(SourceIntegrityError):
        verify_base_source(container, replace(spec, pre_install=proof))


def test_archive_must_equal_base_blob_not_image_build_effect(prepared):
    root, spec, container = prepared
    apply_image_edits(root)
    git(root, 'add', 'plain.py')
    git(root, 'commit', '-qm', 'unapproved archive edit')
    spec.archive_path.write_bytes(git(root, 'archive', '--format=tar', '--prefix=testbed/', 'HEAD'))
    spec = replace(spec, archive_sha256=hashlib.sha256(spec.archive_path.read_bytes()).hexdigest())
    with pytest.raises(SourceIntegrityError, match='archive_differs_from_base_blob'):
        verify_base_source(container, spec)


@pytest.mark.parametrize('script_kind', ['exact', 'extra', 'reordered', 'missing'])
def test_image_script_requires_exact_complete_list(prepared, script_kind):
    root, spec, container = prepared
    apply_image_edits(root)
    commands = list(spec.pre_install.commands)
    if script_kind == 'extra':
        commands.append("sed -i 's/unrelated/edit/' other.py")
    elif script_kind == 'reordered':
        commands.reverse()
    elif script_kind == 'missing':
        commands.pop()
    container.scripts = {'/root/setup_repo.sh': '#!/bin/bash\ngit reset --hard\n'+'\n'.join(commands)+'\npython -m pip install -e .\n'}
    if script_kind == 'exact':
        assert verify_base_source(container, spec)['pre_install']['image_corroboration']['status'] == 'MATCH'
    else:
        with pytest.raises(SourceIntegrityError, match='disagrees') as error:
            verify_base_source(container, spec)
        assert error.value.receipt['pre_install']['image_corroboration']['status'] == 'MISMATCH'


def test_ast_reads_only_pre_install_never_imports_or_executes_other_fields():
    assert parse_pre_install(SOURCE, 'example/project','1') == (
        "sed -i 's/value = 9/value = 10/' plain.py", "sed -i 's/old/new/' tox.ini")
    with pytest.raises(ValueError, match='Missing'):
        parse_pre_install(SOURCE, 'example/project', 'unknown')
    malicious = SOURCE.replace('["sed -i \'s/value = 9/value = 10/\' plain.py"]', 'forbidden_call()')
    with pytest.raises(ValueError, match='Unsupported'):
        parse_pre_install(malicious, 'example/project','1')


def test_system_commands_and_escaping_cannot_justify_source_exemptions():
    assert source_edit_commands(['apt-get update']) is None
    with pytest.raises(ValueError, match='Unsafe'):
        source_edit_commands(["sed -i 's/a/b/' /outside"])


def test_replay_preserves_noncommuting_command_order():
    probe = {'records': {'plain.py': {'base_blob_b64': base64.b64encode(b'a\n').decode()}}}
    edits = source_edit_commands(["sed -i 's/a/b/' plain.py", "sed -i 's/b/c/' plain.py"])
    assert base64.b64decode(replay_source_edits(edits, probe)['plain.py']['expected_b64']) == b'c\n'
