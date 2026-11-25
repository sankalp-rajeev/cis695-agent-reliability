"""Independent, standard-library-only reconciliation of committed probe evidence.

Run with python3 scripts/verify_umgpt_probe.py. No model, dataset, or verifier is loaded.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/umgpt_probe'
IDS = ('django__django-14373', 'scikit-learn__scikit-learn-12973', 'django__django-16899')
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'cost_usd')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def equal(actual, expected, message):
    check(isinstance(expected, (int, float)) and math.isfinite(expected), message)
    check(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10),
          f'{message}: computed {actual}, reported {expected}')


def totals(calls):
    return {k: sum(c.get(k, 0) or 0 for c in calls) for k in FIELDS}


def read_prices():
    module = ast.parse((ROOT / 'src/reliability/umgpt.py').read_text())
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'PRICES' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Branch pricing table not found')


def audit():
    evidence = json.loads((REPORT / 'spend_evidence.json').read_text())
    ledger = evidence['ledger']
    baseline = {c['id']: c for c in evidence['ledger_baseline']['calls']}
    check(set(baseline).issubset({c['id'] for c in ledger['calls']}), 'Historical ledger entry missing')
    calls = evidence['per_call_records']
    check(len({c['id'] for c in calls}) == len(calls), 'Duplicate per-call ID')
    by_id = {c['id']: c for c in calls}
    prices = read_prices()
    for c in ledger['calls']:
        check(c['state'] == 'settled', f"Outstanding reservation: {c['id']}")
        if c['id'] in baseline:
            check(c == baseline[c['id']], 'Historical ledger entry changed')
            continue
        check(c['id'] in by_id, 'Ledger entry lacks a per-call record')
        record = by_id.pop(c['id'])
        if c['task'] in IDS:
            check(c['model_id'] == 'openai/gpt-4.1-mini', 'Unauthorized task model')
        check(c['task'] == record['task'] and c['stage'] == record['stage'], 'Call attribution mismatch')
        equal(c['cost_usd'], record.get('cost_usd', 0), 'Ledger / call cost')
        if 'input_tokens' in c:
            for k in FIELDS[:-1]:
                equal(c[k], record[k], 'Ledger / call ' + k)
            inp, cache, out = prices[c['model_id'].split('openai/', 1)[-1]]
            expected = ((c['input_tokens'] - c['cached_input_tokens']) * inp
                        + c['cached_input_tokens'] * cache + c['output_tokens'] * out) / 1e6
            equal(c['cost_usd'], expected, 'Token-repriced ledger cost')
        check('finish_reason' in record and 'protected_material_code_detected' in record
              and 'protected_material_code_filtered' in record and 'any_filtered' in record,
              'Missing finish/filter metadata')
    check(not by_id, 'Per-call record absent from ledger')
    local_ledger = ROOT / 'runs/umgpt_spend_ledger.json'
    if local_ledger.is_file():
        check(json.loads(local_ledger.read_text()) == ledger, 'Local ledger differs from evidence')
    # When local raw records exist, require them to match the committed per-call evidence.
    raw = []
    verification = ROOT / 'runs/umgpt_probe/verification.json'
    if verification.is_file():
        for result in json.loads(verification.read_text()):
            raw.extend({**c, 'task': 'verify:' + result['model_id'].split('openai/', 1)[-1]}
                       for c in result['calls'])
        for instance_id in IDS:
            p = ROOT / 'runs/umgpt_probe/tasks' / instance_id / 'umgpt_record.json'
            if p.is_file():
                raw.extend({**c, 'task': instance_id} for c in json.loads(p.read_text())['calls'])
        check(raw == calls, 'Local per-call records differ from committed evidence')
    report = (REPORT / 'REPORT.md').read_text()
    start, end = '<!-- spend-audit-start -->\n```json\n', '\n```\n<!-- spend-audit-end -->'
    numbers = json.loads(report.split(start, 1)[1].split(end, 1)[0])
    job_calls = [c for c in ledger['calls'] if c['job'] == 'umgpt_probe']
    check(set(numbers['tasks']) == set(IDS), 'Report must identify exactly the three tasks')
    for instance_id in IDS:
        measured = [c for c in job_calls if c['task'] == instance_id]
        for k, value in totals(measured).items():
            equal(value, numbers['tasks'][instance_id]['total'][k], instance_id + ' ' + k)
        for stage in ('agent', 'V4'):
            for k, value in totals([c for c in measured if c['stage'] == stage]).items():
                equal(value, numbers['tasks'][instance_id][stage][k], instance_id + '/' + stage + ' ' + k)
    for name, selected in (
            ('job', job_calls), ('account', ledger['calls']),
            ('verification', [c for c in job_calls if c['stage'] == 'verification'])):
        for k, value in totals(selected).items():
            equal(value, numbers[name][k], name + ' ' + k)
    # Verify the visible tables as well as the report's full-precision audit block.
    if '| Task | Repair steps |' in report:
        for instance_id in IDS:
            rows = [[v.strip() for v in line.split('|')[1:-1]]
                    for line in report.splitlines() if line.startswith('| ' + instance_id + ' |')]
            check(len(rows) >= 4, 'Missing task tables: ' + instance_id)
            for stage, cells, token_col, cost_col in (('agent', rows[0], 2, 3), ('V4', rows[1], 4, 5)):
                n = numbers['tasks'][instance_id][stage]
                token_text = ' / '.join(str(n[k]) for k in FIELDS[:-1])
                check(cells[token_col] == token_text, 'Visible token table mismatch')
                check(cells[cost_col] == f"${n['cost_usd']:.8f}", 'Visible cost table mismatch')
            combined = next((r for r in rows if r[1].startswith('$')), None)
            check(combined is not None and combined[1] ==
                  f"${numbers['tasks'][instance_id]['total']['cost_usd']:.8f}",
                  'Visible combined-cost mismatch')
    if '| Model / basis |' in report:
        for model in ('gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini'):
            ip, cp, op = prices[model]
            repriced = [((n['total']['input_tokens'] - n['total']['cached_input_tokens']) * ip
                         + n['total']['cached_input_tokens'] * cp + n['total']['output_tokens'] * op)
                        / 1e6 for n in numbers['tasks'].values()]
            avg, worst = sum(repriced) / len(IDS), max(repriced)
            expected = [f'${v:.8f}' for v in (avg, worst, avg * 10, worst * 10, avg * 83, worst * 83)]
            line = next((s for s in report.splitlines() if s.startswith('| ' + model + ' (')), None)
            check(line is not None and [v.strip() for v in line.split('|')[2:-1]] == expected,
                  'Visible projection mismatch: ' + model)
    equal(sum(c['cost_usd'] for c in ledger['calls']), numbers['account']['cost_usd'], 'Total spend')
    check(numbers['job']['cost_usd'] <= 3 and numbers['account']['cost_usd'] <= 20, 'Budget exceeded')
    for values in numbers['tasks'].values():
        check(values['total']['cost_usd'] <= .75 and values['agent']['cost_usd'] <= .60,
              'Task/repair cap exceeded')
    frozen = json.loads((REPORT / 'frozen_files.json').read_text())
    for entry in frozen:
        path = entry['path']
        current = (ROOT / path).read_bytes()
        main = subprocess.check_output(['git', 'show', 'origin/main:' + path], cwd=ROOT)
        digest = hashlib.sha256(current).hexdigest()
        check(current == main and digest == entry['sha256'], 'Frozen file mismatch: ' + path)
    print(f"PASS: {len(calls)} per-call records reconcile with {len(ledger['calls'])} ledger entries; no reservations.")
    for instance_id in IDS:
        n = numbers['tasks'][instance_id]
        print(f"PASS: {instance_id}: repair=${n['agent']['cost_usd']:.8f} V4=${n['V4']['cost_usd']:.8f} total=${n['total']['cost_usd']:.8f}")
    print(f"PASS: verification=${numbers['verification']['cost_usd']:.8f}; job=${numbers['job']['cost_usd']:.8f}; account=${numbers['account']['cost_usd']:.8f}; report matches.")
    if '| Model / basis |' in report:
        print('PASS: visible task costs/tokens and all 10/83-task projections match independent calculations.')
    print(f'PASS: all {len(frozen)} frozen-file hashes match origin/main and the recorded manifest.')


if __name__ == '__main__':
    try:
        audit()
    except (ValueError, KeyError, IndexError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit('FAIL: ' + str(exc)) from None
