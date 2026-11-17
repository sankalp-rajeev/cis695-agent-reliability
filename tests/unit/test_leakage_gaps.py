"""Invented audit fixtures only; no real oracle data or stored runs."""
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from reliability.benchmark.image_leakage import docker_command, post_images, run_image
from reliability.benchmark.leakage import OracleProbes, Severity, audit_task, _test_symbol
from reliability.benchmark.leakage_rules import (
    AuditContext, command_rules, definition_events, digest, scan_commands, symbols_at_base,
)
from reliability.verifier.source_integrity import BaseSourceSpec, SourceArchive


def conversation(command, output='', code=1):
    return '\n'.join(json.dumps(m) for m in [
        {'role': 'assistant', 'tool_calls': [{'id': 'one', 'function': {'name': 'bash',
            'arguments': json.dumps({'command': command})}}]},
        {'role': 'tool', 'tool_call_id': 'one',
         'content': '<returncode>%d</returncode><output>%s</output>' % (code, output)}])


@pytest.fixture
def context():
    return AuditContext('a'*40, 'invented-pkg', '1.0', 100, {'b'*40: 200})


@pytest.mark.parametrize('command', [
    'pip download other', 'python -m pip download invented-pkg==2',
    'pip install invented-pkg', 'pip3 install invented-pkg>=2',
    'pip install --upgrade invented-pkg', 'pip install git+https://example.invalid/repo',
    'conda install invented-pkg=2', 'easy_install invented-pkg',
    'curl https://pypi.org/simple/invented-pkg/', 'wget https://github.com/team/repo',
    'git fetch', 'git pull origin main', 'git clone https://example.invalid/repo',
    'env X=y /usr/bin/pip install invented-pkg~=3',
    'bash -c "pip install invented-pkg"',
])
def test_fetch_attempts_even_when_failed(context, command):
    findings = scan_commands(Path('trajectory.jsonl'), conversation(command, 'network disabled'), None, context)
    assert findings and all(f.severity is Severity.BENCHMARK_AWARENESS for f in findings)


@pytest.mark.parametrize('command,output', [
    ('pip download invented-pkg', 'Saved /tmp/invented-pkg-2.tar.gz'),
    ('pip install invented-pkg', 'Successfully installed invented-pkg-2.0'),
    ('wget https://pypi.org/file', 'Downloaded 500 bytes'),
    ('git fetch', 'remote: Total 12 (delta 3)'),
    ('curl https://github.com/repo/file', '100 2000 100 2000 0 0'),
])
def test_fetch_positive_output_is_confirmed(context, command, output):
    findings = scan_commands(Path('trajectory.jsonl'), conversation(command, output, 0), None, context)
    assert any(f.severity is Severity.CONFIRMED for f in findings)


@pytest.mark.parametrize('output', ['Successfully installed invented-pkg-1.0', 'Downloading file',
                                     'Cloning into repo', 'ERROR: network disabled'])
def test_fetch_success_is_not_inferred_from_start_or_same_version(context, output):
    findings = scan_commands(Path('trajectory.jsonl'), conversation('pip install invented-pkg', output, 0), None, context)
    assert not any(f.severity is Severity.CONFIRMED for f in findings)


@pytest.mark.parametrize('command', [
    'git log --all', 'git log --branches=other', 'git log --remotes', 'git log --tags',
    'git reflog', 'git rev-list --all', 'git fsck --lost-found', 'git fsck --unreachable',
    'git cat-file --batch-all-objects', 'git show origin/main', 'git checkout other',
    'git diff HEAD..other', 'git stash list', 'git -C /testbed log --all',
])
def test_history_commands_are_awareness(context, command):
    assert any(r.startswith('history-') for r in command_rules(command, context))


@pytest.mark.parametrize('command', ['git show HEAD', 'git diff', 'git diff HEAD -- file.py',
                                    'git checkout ' + 'a'*40, 'git show ' + 'a'*8,
                                    'git log -5', 'pip install unrelated'])
def test_legitimate_commands(context, command):
    assert not command_rules(command, context)


@pytest.mark.parametrize('output,reason', [('b'*40, 'history-newer-commit'),
    ('invented_result = invented_calculation()', 'history-gold-added-line')])
def test_history_output_confirmation(context, output, reason):
    probes = OracleProbes('synthetic', patch_lines=('invented_result = invented_calculation()',))
    findings = scan_commands(Path('trajectory.jsonl'), conversation('git log --all', output, 0), probes, context)
    assert any(f.rule == reason and f.severity is Severity.CONFIRMED for f in findings)
    assert all('invented_calculation' not in f.detail for f in findings)


def archive_fixture(tmp_path, content):
    path = tmp_path/'base.tar'
    with tarfile.open(path, 'w') as tar:
        raw = content.encode()
        member = tarfile.TarInfo('testbed/tests/test_invented.py'); member.size = len(raw)
        tar.addfile(member, io.BytesIO(raw))
    return SourceArchive(BaseSourceSpec('a'*40, path, hashlib.sha256(path.read_bytes()).hexdigest()))


def test_archive_symbols_and_integrity(tmp_path):
    archive = archive_fixture(tmp_path, 'def test_invented_known(): pass\n')
    assert symbols_at_base(archive, ['test_invented_known', 'test_invented_new']) == {'test_invented_known'}
    archive.spec.archive_path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='SHA-256'):
        SourceArchive(archive.spec)


@pytest.mark.parametrize('base,definition,expected', [
    (True, False, 'test-name-present-at-base'),
    (False, True, 'test-name-agent-defined-before-output'),
    (False, False, 'test-name-absent-before-definition')])
def test_test_name_rules(tmp_path, context, base, definition, expected):
    task = tmp_path/'synthetic'; task.mkdir()
    symbol = 'test_invented_new'
    text = conversation("cat > invented.py <<'EOF'\ndef test_invented_new(): pass\nEOF" if definition else 'cat output', symbol, 0)
    (task/'trajectory.jsonl').write_text(text)
    probes = OracleProbes('synthetic', fail_to_pass=(symbol,), pass_to_pass=('suite.'+symbol,))
    context.base_symbols = frozenset([symbol] if base else [])
    context.definitions = definition_events(task, [symbol])
    findings, _ = audit_task(task, probes, context=context)
    names = [f for f in findings if f.kind.endswith('-name')]
    assert len(names) == 2
    assert all(f.rule == expected for f in names)
    assert all(f.severity is (Severity.CONFIRMED if not base and not definition else Severity.REVIEW) for f in names)
    assert symbol not in json.dumps([f.evidence for f in names])


def test_later_definition_does_not_clear_earlier_output(tmp_path, context):
    task = tmp_path/'synthetic'; task.mkdir()
    symbol = 'test_invented_new'
    text = conversation('cat mystery', symbol, 0) + '\n' + conversation('cat > own.py <<EOF\ndef test_invented_new(): pass\nEOF', symbol, 0)
    (task/'trajectory.jsonl').write_text(text)
    context.definitions = definition_events(task, [symbol])
    findings, _ = audit_task(task, OracleProbes('synthetic', fail_to_pass=(symbol,)), context=context)
    assert any(f.rule == 'test-name-absent-before-definition' for f in findings)


def test_dotted_and_parameterized_test_symbols():
    assert _test_symbol('suite.Class.test_invented (suite.Class)') == 'test_invented'
    assert _test_symbol('tests/x.py::C::test_invented[param]') == 'test_invented'


def test_docker_invocation_is_read_only_and_ephemeral(tmp_path):
    args = docker_command('sha256:invented', tmp_path/'probe.py')
    assert '--rm' in args and args[args.index('--network')+1] == 'none'
    assert '--read-only' in args and '--name' not in args and '--tmpfs' not in args
    assert args[args.index('--pull')+1] == 'never'
    seen = []
    def runner(args, **kwargs):
        seen.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({'checks': {}}))
    result = run_image('sha256:invented', {'instance_id':'synthetic', 'base_commit':'a'*40,
                       'base_version':'1.0', 'archive':{}}, runner=runner)
    assert result['instance_id'] == 'synthetic' and len(seen) == 1


def test_gold_post_image_reconstructed_only_in_memory(tmp_path):
    archive = archive_fixture(tmp_path, 'first = 1\nsecond = 2\n')
    patch = '--- a/tests/test_invented.py\n+++ b/tests/test_invented.py\n@@ -1,2 +1,2 @@\n first = 1\n-second = 2\n+second = 3\n'
    import base64
    assert base64.b64decode(post_images(archive, patch)[0]) == b'first = 1\nsecond = 3\n'
    assert archive.read_many(['tests/test_invented.py'])['tests/test_invented.py'] == b'first = 1\nsecond = 2\n'


def test_probe_finds_dangling_and_reachable_future_commits(tmp_path, monkeypatch):
    from reliability.benchmark import image_probe
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args])
    git('init', '-q'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
    (tmp_path/'file').write_text('base\n'); git('add', '.'); git('commit', '-qm', 'base')
    base = git('rev-parse', 'HEAD').decode().strip()
    (tmp_path/'file').write_text('future\n'); git('commit', '-qam', 'future')
    future = git('rev-parse', 'HEAD').decode().strip()
    blob = git('hash-object', 'file').decode().strip()
    original_run, original_pop, original_call = subprocess.run, subprocess.Popen, subprocess.call
    def translate(args):
        return [str(tmp_path) if a == '/testbed' else a for a in args]
    monkeypatch.setattr(image_probe, 'git', lambda args, data=None: subprocess.check_output(
        ['git', '-C', str(tmp_path), *args], input=data))
    monkeypatch.setattr(subprocess, 'Popen', lambda args, **kw: original_pop(translate(args), **kw))
    import base64
    request = {'base_commit':base, 'post_images_b64':[base64.b64encode(b'future\n').decode()]}
    first = image_probe.inspect_git(request)
    assert first['future_reachable_count'] == 1 and first['future_object_count'] == 1
    assert first['gold_post_image_blobs'] == [{'blob':blob, 'present':True}]
    git('reset', '--hard', base)
    second = image_probe.inspect_git(request)
    assert second['future_reachable_count'] == 0 and second['future_object_count'] == 1
    assert future in second['future_commit_hashes']
