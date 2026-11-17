"""The independent audit must reject altered costs, reports and frozen files."""
import hashlib
import json

import pytest
from scripts import verify_umgpt_probe as audit


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    root = tmp_path
    report = root / 'reports/umgpt_probe'
    report.mkdir(parents=True)
    monkeypatch.setattr(audit, 'ROOT', root)
    monkeypatch.setattr(audit, 'REPORT', report)
    (root / 'src/reliability').mkdir(parents=True)
    (root / 'src/reliability/umgpt.py').write_text("PRICES = {'gpt-4.1-mini': (.4, .1, 1.6)}\n")
    call = {'id': 'unit', 'job': 'umgpt_probe', 'task': audit.IDS[0], 'stage': 'agent',
            'model_id': 'openai/gpt-4.1-mini', 'state': 'settled',
            'input_tokens': 100, 'cached_input_tokens': 50, 'output_tokens': 10,
            'cost_usd': .000041, 'finish_reason': 'tool_calls',
            'protected_material_code_detected': False,
            'protected_material_code_filtered': False, 'any_filtered': False}
    data = {'ledger': {'version': 1, 'calls': [call]},
            'ledger_baseline': {'version': 1, 'calls': []},
            'per_call_records': [dict(call)]}
    path = report / 'spend_evidence.json'
    path.write_text(json.dumps(data))
    numbers = {'tasks': {i: {'total': audit.totals([call] if i == audit.IDS[0] else []),
                            'agent': audit.totals([call] if i == audit.IDS[0] else []),
                            'V4': audit.totals([])} for i in audit.IDS},
               'account': audit.totals([call]), 'job': audit.totals([call]),
               'verification': audit.totals([])}
    (report / 'REPORT.md').write_text('<!-- spend-audit-start -->\n```json\n' + json.dumps(numbers)
                                    + '\n```\n<!-- spend-audit-end -->')
    visible = ['| Task | Repair steps |']
    for instance_id in audit.IDS:
        n = numbers['tasks'][instance_id]['agent']
        tokens = ' / '.join(str(n[k]) for k in audit.FIELDS[:-1])
        visible.append(f"| {instance_id} | 1 | {tokens} | ${n['cost_usd']:.8f} |")
    for instance_id in audit.IDS:
        visible.append(f'| {instance_id} | 0 | none | 0 | 0 / 0 / 0 | $0.00000000 |')
    for instance_id in audit.IDS:
        visible.append(f'| {instance_id} | 0 / 0 | 0 / 0 |')
    for instance_id in audit.IDS:
        cost = numbers['tasks'][instance_id]['total']['cost_usd']
        visible.append(f'| {instance_id} | ${cost:.8f} |')
    with (report / 'REPORT.md').open('a') as output:
        output.write('\n' + '\n'.join(visible))
    frozen = root / 'frozen.py'
    frozen.write_text('original\n')
    (report / 'frozen_files.json').write_text(json.dumps([{
        'path': 'frozen.py', 'sha256': hashlib.sha256(frozen.read_bytes()).hexdigest()}]))
    monkeypatch.setattr(audit.subprocess, 'check_output', lambda *a, **k: b'original\n')
    return root, report, data


def test_independent_audit_accepts_consistent_evidence(evidence, capsys):
    audit.audit()
    assert 'report matches' in capsys.readouterr().out


@pytest.mark.parametrize('change', ['call_cost', 'ledger_cost', 'report_cost', 'visible_cost', 'frozen'])
def test_independent_audit_detects_tampering(evidence, change):
    root, report, data = evidence
    if change == 'call_cost':
        data['per_call_records'][0]['cost_usd'] = .001
    elif change == 'ledger_cost':
        data['ledger']['calls'][0]['cost_usd'] = .001
        data['per_call_records'][0]['cost_usd'] = .001
    elif change == 'report_cost':
        path = report / 'REPORT.md'
        path.write_text(path.read_text().replace('4.1e-05', '0.001'))
    elif change == 'visible_cost':
        path = report / 'REPORT.md'
        path.write_text(path.read_text().replace('$0.00004100', '$0.00004200'))
    else:
        (root / 'frozen.py').write_text('changed\n')
    (report / 'spend_evidence.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):
        audit.audit()
