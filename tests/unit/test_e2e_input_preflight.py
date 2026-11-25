"""The access preflight must never decode unrequested metadata values."""

import importlib.util
from pathlib import Path


def load_preflight():
    path = Path(__file__).resolve().parents[2] / 'scripts/e2e_input_preflight.py'
    spec = importlib.util.spec_from_file_location('e2e_input_preflight', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projection_skips_unknown_values_without_decoding():
    module = load_preflight()
    parser = module.Projection('[{"instance_id":"a","hidden":{"nested":["secret",null]},"runner":{"name":"django","extra":false}}]')
    decoder = parser.decoder

    class GuardedDecoder:
        def raw_decode(self, text, position):
            assert not text[position:].startswith(('"secret"', 'null', 'false', '{', '['))
            return decoder.raw_decode(text, position)

    parser.decoder = GuardedDecoder()
    assert parser.project({'*': {'instance_id': True, 'runner': {'name': True}}}) == [
        {'instance_id': 'a', 'runner': {'name': 'django'}}]


def test_django_source_outside_paired_freeze_is_not_opened(tmp_path, monkeypatch):
    module = load_preflight()
    frozen = tmp_path / 'paired_frozen'
    frozen.mkdir()
    tasks = b'[{"instance_id":"django__django-1","runner":{"name":"django"}}]'
    (frozen / 'tasks.json').write_bytes(tasks)
    (frozen / 'protocol.json').write_bytes(b'{}')
    monkeypatch.setattr(module, 'TASKS_SHA256', module.digest(tasks))
    monkeypatch.setattr(module, 'PROTOCOL_SHA256', module.digest(b'{}'))
    reference = tmp_path / 'reference'
    reference.mkdir()
    source = tmp_path / 'outside/tasks/django__django-1/v2/result.json'
    # The source deliberately does not exist: opening or statting it is unnecessary.
    import json
    (reference / 'manifest.json').write_text(json.dumps({'input_sha256': {str(source): 'a' * 64}}))
    report = module.audit(frozen, reference)
    assert report['status'] == 'BLOCKED_INPUT_ACCESS'
    assert report['command_projection_sources_opened'] == 0
    assert report['blocked_sources'][0]['path'] == str(source)


def test_frozen_hash_check_does_not_open_forbidden_path(tmp_path):
    module = load_preflight()
    policy = tmp_path / 'reports/policy_v1_4'
    policy.mkdir(parents=True)
    (policy / 'artifact_manifest.sha256').write_text(
        'a' * 64 + '  reports/policy_v1_4/golden.csv\n')
    probe = tmp_path / 'reports/umgpt_probe'
    probe.mkdir()
    (probe / 'frozen_files.json').write_text('[]')
    assert module.audit_frozen_files(tmp_path) == [{
        'manifest': 'reports/policy_v1_4/artifact_manifest.sha256',
        'path': 'reports/policy_v1_4/golden.csv', 'expected_sha256': 'a' * 64,
        'status': 'BLOCKED_FORBIDDEN_NAME', 'opened': False}]
