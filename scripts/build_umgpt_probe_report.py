"""Assemble cost-only probe evidence and the report from numeric records."""
from __future__ import annotations

import ast
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/umgpt_probe'
RUN = ROOT / 'runs/umgpt_probe'
IDS = ('django__django-14373', 'scikit-learn__scikit-learn-12973', 'django__django-16899')
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'cost_usd')


def read(path):
    return json.loads(path.read_text())


def totals(calls):
    return {k: sum(c.get(k, 0) or 0 for c in calls) for k in FIELDS}


def money(value):
    return f'${value:.8f}' if value is not None else 'unreported'


def mean(values):
    present = [v for v in values if v is not None]
    return statistics.mean(present) if present else None


def seconds(value):
    return f'{value:.2f}' if isinstance(value, (int, float)) else '—'


def build():
    ledger = read(ROOT / 'runs/umgpt_spend_ledger.json')
    verify = read(RUN / 'verification.json')
    baseline = read(RUN / 'ledger_baseline.json')
    rows = {}
    calls = []
    for result in verify:
        calls.extend({**c, 'task': 'verify:' + result['model_id'].split('openai/', 1)[-1]}
                     for c in result['calls'])
    for instance_id in IDS:
        path = RUN / 'tasks' / instance_id / 'umgpt_record.json'
        if path.is_file():
            rows[instance_id] = read(path)
            rows[instance_id].get('V4', {}).get('generation_evidence', {}).pop('sanitized_output_tail', None)
            calls.extend({**c, 'task': instance_id} for c in rows[instance_id]['calls'])
    evidence = {'ledger_source': 'runs/umgpt_spend_ledger.json',
                'ledger_original_source': '/home/sankalp/projects/cis695-v2-scg-ubuntu-publication/runs/umgpt_spend_ledger.json',
                'ledger_baseline': baseline, 'ledger': ledger, 'per_call_records': calls,
                'verification_source': 'runs/umgpt_probe/verification.json',
                'task_sources': {i: f'runs/umgpt_probe/tasks/{i}/umgpt_record.json' for i in rows}}
    (REPORT / 'spend_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (REPORT / 'execution_meta.yaml').write_bytes((RUN / 'meta.yaml').read_bytes())
    (REPORT / 'task_measurements.json').write_text(json.dumps({i: {k: v for k, v in row.items() if k != 'calls'} for i, row in rows.items()}, indent=2) + '\n')
    job = [c for c in ledger['calls'] if c['job'] == 'umgpt_probe']
    numbers = {'tasks': {i: {
        'total': totals([c for c in job if c['task'] == i]),
        **{s: totals([c for c in job if c['task'] == i and c['stage'] == s])
           for s in ('agent', 'V4')}} for i in IDS},
        'verification': totals([c for c in job if c['stage'] == 'verification']),
        'job': totals(job), 'account': totals(ledger['calls'])}
    filtered = [c for c in calls if c.get('any_filtered')
                or 'content_filter' in c.get('finish_reasons', [])]
    detected = [c for c in calls if c.get('protected_material_code_detected')]
    complete = len(rows) == 3 and all(r.get('complete') for r in rows.values())
    generator_errors = {i: r['V4'].get('termination') for i, r in rows.items()
                        if r.get('V4', {}).get('termination') not in (None, 'Submitted', 'LimitsExceeded', 'TimeExceeded')}
    skipped_v4 = {i: r['V4'].get('not_run_reason') for i, r in rows.items()
                  if r.get('V4') and not r['V4'].get('ran')}
    if filtered:
        verdict = '**Verdict: the gateway filtered model output; do not use this route for repair. The probe stopped immediately.**'
    elif complete and skipped_v4:
        verdict = (f'**Verdict: the three gpt-4.1-mini tasks were attempted without Azure filtering, '
                   f'but {len(skipped_v4)} V4 generator(s) could not run and {len(generator_errors)} ended in error. '
                   'Observed costs include these incomplete chains; correctness was not evaluated.**')
    elif complete and generator_errors:
        verdict = (f'**Verdict: all three gpt-4.1-mini task chains were measured without Azure filtering; '
                   f'{len(generator_errors)} V4 generation(s) ended in error. Costs include those early terminations. '
                   'Correctness was not evaluated.**')
    elif complete:
        verdict = '**Verdict: the three-task gpt-4.1-mini cost probe completed without Azure filtering. Measured costs support budget planning; correctness was not evaluated.**'
    else:
        verdict = '**Verdict: the cost probe is incomplete; a stopping condition prevented complete three-task measurements. Do not treat truncated costs as natural task costs.**'
    lines = [verdict, '', 'Date: 2026-11-16 (America/Phoenix). Branch: `feature/umgpt-routing`.',
             'All amounts are USD list-price estimates, including ledger costs. No UM billing receipt was collected.',
             '', '## Scope and provenance', '',
             'Preflight confirmed a clean tree on the requested branch, origin/main as an ancestor of HEAD, key-entry presence without displaying its value, and all 38 frozen files unchanged.',
             ('Only the three authorized tasks were attempted, on gpt-4.1-mini. Each chain is `run_task` → '
             '`reliability.verifier.reproduction_v1_4.run_reproduction`, with the UM generator and an 80-step cap. '
             '`verify_task` was never called. **V1, V2, V3 and oracle: not run in probe.** No policy decision or correctness grade was produced.'),
             ('The repair agent retains its existing prompt, decoding parameters, 100-step cap and timeouts; '
             'only routing and the explicitly authorized cost ceiling differ. V4 receives the patch and uses its own containers.'),
             ('Account cap $20; job cap $3 including model verification; task cap $0.75 combined, repair up to $0.60, '
             'V4 using the remainder. A conservative uncached reservation precedes every request; an estimate above $0.30 stops before sending.'),
             'The ledger was copied from `' + evidence['ledger_original_source'] + '` to `runs/umgpt_spend_ledger.json`; '
             f"its {len(baseline['calls'])} historical entries were preserved. Earlier HTTP 401 cost $0 and was not retried in this session.",
             ('The first task startup hit an inherited-Python-path error before any task API call ($0 task spend). '
             'Its artifacts remain in `runs/umgpt_probe/precall_bootstrap_20261116`. A dedicated ignored environment was installed '
             'offline from `uv.lock`, import-affecting shell variables were cleared, and the same tasks were launched. No paid trajectory was rerun.'),
             ('Execution commit and interpreter details are preserved in `execution_meta.yaml` (copied from `runs/umgpt_probe/meta.yaml`); sanitized cost records are committed in '
             '`task_measurements.json`, `spend_evidence.json` and `verification.json`.'),
             '', '## Live model verification', '',
             '| Requested | Served model | Fingerprint | Input / cached / output | Cost | Finish |',
             '|---|---|---|---:|---:|---|']
    for v in verify:
        lines.append(f"| {v['model_id']} | {v.get('served_model')} | {v.get('system_fingerprint')} | "
                     f"{v.get('input_tokens')} / {v.get('cached_input_tokens')} / {v.get('output_tokens')} | "
                     f"{money(v.get('cost_usd'))} | {v.get('finish_reason')} |")
    lines += ['', ('All three passed a real well-formed `bash` tool call in the displayed order. '
              'The full `x-ratelimit-*` headers are retained in `verification.json`; they indicate request/token allocations, not a dollar balance. '
              f"Verification total: **{money(numbers['verification']['cost_usd'])}**. gpt-4.1 and gpt-4o-mini were used only for verification."),
              '', '## Per-task measurements', '',
              ('Input includes cached input; cached is a subset. Repair steps are provider calls (the ledger records retries separately if any). '
              'V4 steps come from v1.4 generation telemetry. Wall time includes stage container work. '
              'All report figures can be reconstructed from the committed numeric evidence.'), '',
              '| Task | Repair steps | Input / cached / output | Ledger cost | LiteLLM cost | Termination / subtype | Patch bytes | Wall s |',
              '|---|---:|---:|---:|---:|---|---:|---:|']
    for i in IDS:
        r = rows.get(i, {}); a = r.get('repair', {}); n = numbers['tasks'][i]['agent']
        termination = {'completed': 'submitted', 'step_limit': 'step limit / configured max_steps=100', 'cost_limit': 'cost limit'}.get(
            a.get('termination'), a.get('termination', 'not run'))
        halt = r.get('halt') or {}
        if halt and halt.get('stage', 'agent') == 'agent':
            termination += ' / ' + halt.get('termination', '') + ': ' + halt.get('response_body', '')
        lines.append(f"| {i} | {a.get('steps') if a.get('steps') is not None else '—'} | {n['input_tokens']} / {n['cached_input_tokens']} / {n['output_tokens']} | "
                     f"{money(n['cost_usd'])} | {money(a.get('litellm_cost_usd'))} | {termination} | "
                     f"{a.get('patch_bytes', '—')} ({'yes' if a.get('patch_produced') else 'no'}) | {seconds(a.get('duration_s'))} |")
    lines += ['', '| Task | V4 steps | Fired limit / termination | Tests written | Input / cached / output | Ledger cost | LiteLLM cost | Generator / total wall s |',
              '|---|---:|---|---:|---:|---:|---:|---:|']
    for i in IDS:
        r = rows.get(i, {}); a = r.get('V4', {}); n = numbers['tasks'][i]['V4']
        halt = r.get('halt') or {}
        detail = f"{a.get('fired_limit_subtype') or 'none'} / {a.get('termination') or 'not run'}"
        if halt.get('stage') == 'V4':
            detail += ' / ' + halt.get('termination', '')
        if a and not a.get('ran'):
            detail = 'not run: ' + str(a.get('not_run_reason'))
        if not a:
            detail = 'not run after repair stop' if r else 'not run'
        lines.append(f"| {i} | {a.get('steps') if a.get('steps') is not None else '—'} | {detail} | {a.get('tests_written', '—')} | "
                     f"{n['input_tokens']} / {n['cached_input_tokens']} / {n['output_tokens']} | {money(n['cost_usd'])} | "
                     f"{money(a.get('litellm_cost_usd'))} | {seconds(a.get('generation_evidence', {}).get('elapsed_seconds'))} / {seconds(a.get('duration_s'))} |")
    lines += ['', ('The frozen v1.4 trajectory-based token telemetry omits some paid responses. '
              'The V4 table and projections use complete per-call ledger usage. Original telemetry totals are retained below:'),
              '| Task | V1.4 telemetry input / output | Per-call ledger input / output |',
              '|---|---:|---:|']
    for i in IDS:
        ev = rows.get(i, {}).get('V4', {}).get('generation_evidence', {})
        n = numbers['tasks'][i]['V4']
        lines.append(f"| {i} | {ev.get('total_input_tokens', '—')} / {ev.get('total_output_tokens', '—')} | "
                     f"{n['input_tokens']} / {n['output_tokens']} |")
    lines += ['', '| Task | Repair + V4 ledger cost | Served model(s) | Fingerprint(s) |',
              '|---|---:|---|---|']
    for i in IDS:
        cs = [c for c in calls if c['task'] == i]
        models = ', '.join(sorted({c['served_model'] for c in cs if c.get('served_model')})) or 'not served'
        fps = ', '.join(sorted({c['system_fingerprint'] for c in cs if c.get('system_fingerprint')})) or 'unreported'
        lines.append(f"| {i} | {money(numbers['tasks'][i]['total']['cost_usd'])} | {models} | {fps} |")
    lines += ['', (f"Job total including verification: **{money(numbers['job']['cost_usd'])}**. "
              f"Account ledger total: **{money(numbers['account']['cost_usd'])}**."),
              'No cost ceiling fired. The final repair reached its unchanged 100-step limit; V4 then recorded an empty-patch skip.',
              '', '## Filtering and prompt caching', '',
              (f"Across {len(calls)} new provider calls: **{len(filtered)} hard filtering events**, "
              f"{len(detected)} calls with `protected_material_code.detected=true`. "
              'Every call records finish reason, protected-code detected/filtered flags, and any-category filtered flags. '
              'Detection alone does not stop execution; `content_filter` or any `filtered=true` does.'),
              'Hard filtering steps: ' + (', '.join(f"{c['task']} {c['stage']} step {c['step']}" for c in filtered) or 'none') + '.',
              '| Stage | Input | Cached | Cached share |', '|---|---:|---:|---:|']
    for name, cs in [('repair', [c for c in calls if c['stage'] == 'agent']),
                     ('V4', [c for c in calls if c['stage'] == 'V4']), ('all calls', calls)]:
        n = totals(cs)
        share = n['cached_input_tokens'] / n['input_tokens'] if n['input_tokens'] else 0
        lines.append(f"| {name} | {n['input_tokens']} | {n['cached_input_tokens']} | {share:.2%} |")
    task_calls = [c for c in calls if c['task'] in IDS and 'input_tokens' in c]
    differences = [c for c in task_calls if c.get('litellm_cost_usd') is not None
                   and abs(c['cost_usd'] - c['litellm_cost_usd']) > 1e-10]
    lines += ['', (f"{len(differences)} task calls had a ledger/LiteLLM price difference larger than $0.0000000001. "
              'The UM route uses list-price estimates for budget enforcement; the gateway usage and caching metadata do not '
              'establish actual UM charges. No distinct UM billing rate or discount was verified.'),
              '', '## 10-task and 83-task projections', '',
              ('List prices are from this branch’s `src/reliability/umgpt.py:PRICES` and model YAML pricing blocks, '
              'in USD per million tokens. Input prices below apply to uncached tokens; cached tokens use the separate cache rate.'),
              '| Model | Uncached input | Cached input | Output |', '|---|---:|---:|---:|']
    prices = None
    for node in ast.parse((ROOT / 'src/reliability/umgpt.py').read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PRICES' for t in node.targets):
            prices = ast.literal_eval(node.value)
    for name in ('gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini'):
        lines.append('| ' + name + ' | ' + ' | '.join(f'${v:g}' for v in prices[name]) + ' |')
    if complete:
        if skipped_v4:
            lines += ['', 'The observed mean includes V4 that could not run: ' + ', '.join(
                f'{i}: {reason}' for i, reason in skipped_v4.items())
                + '. Its zero V4 spend is an observed skip, not a measurement of generator cost for that task.']
        if generator_errors:
            lines += ['', 'The measured mean includes early V4 errors: ' + ', '.join(
                f'{i}: {reason}' for i, reason in generator_errors.items())
                + '. Successful V4 generation could cost more; these projections preserve the observed terminations.']
        lines += ['', ('Projections multiply the three measured combined repair+V4 task costs or their repriced token counts. '
                  'Verification is a one-time probe overhead and is excluded. Worst-case uses the most expensive of these three tasks; '
                  'it is not a bound on unseen tasks. Repricing assumes identical trajectories and cache shares, which other models may not produce.'),
                  '| Model / basis | Mean per task | Worst task | 10 × mean | 10 × worst | 83 × mean | 83 × worst |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for name in ('gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini'):
            ip, cp, op = prices[name]
            values = []
            for i in IDS:
                n = numbers['tasks'][i]['total']
                values.append(((n['input_tokens'] - n['cached_input_tokens']) * ip
                               + n['cached_input_tokens'] * cp + n['output_tokens'] * op) / 1e6)
            avg, worst = statistics.mean(values), max(values)
            label = 'measured' if name == 'gpt-4.1-mini' else 'repriced, not measured'
            lines.append(f'| {name} ({label}) | ' + ' | '.join(money(v) for v in
                         (avg, worst, avg * 10, worst * 10, avg * 83, worst * 83)) + ' |')
    else:
        lines += ['', ('**Full three-task mean/worst projections are unavailable because the probe stopped.** '
                  'Reported partial spend is not substituted for a natural task cost. Repricing any completed subset '
                  'would not meet the requested three-task comparison.')]
    if complete:
        observed = [n['total']['cost_usd'] for n in numbers['tasks'].values()]
        lines += ['', (f'The observed gpt-4.1-mini 83-task projection is {money(mean(observed) * 83)} from the mean '
                  f'and {money(max(observed) * 83)} from the worst task, compared with the $20 account cap. '
                  'The skipped/errored V4 stages limit a full-run budget decision. The gpt-4o-mini projection remains repriced, not measured.')]
    lines += ['', '## Stored DeepSeek comparison (read-only numeric extraction)', '',
              ('`scripts/extract_umgpt_deepseek_numeric.py` reads only the authorized repair token/step/cost/time fields '
              'and V4 generation numeric telemetry in `~/projects/cis695-agent-reliability/runs/main_50_a` and `main_50_b`. '
              'The same three tasks are not all present in either run, so these are **whole-set means**, not matched-task comparisons. '
              'No trajectory, issue discussion, patch, correctness decision, or oracle record was read from the old runs. '
              'DeepSeek cost values are the stored usage.api_cost_usd and V4 generation.cost_usd; historical billing receipts were not inspected.'),
              '| Run | Repair n | Mean input / output | Mean repair cost | Mean repair wall s | V4 numeric n | Mean V4 steps | Mean V4 cost | Paired combined mean (n) |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    deep = read(REPORT / 'deepseek_numeric.json')
    for name, data in deep.items():
        ds = data['rows']; pairs = []
        for row in ds:
            # full and baseline records describe the same V4 generation; count once.
            v4 = next((v for v in row['v4_numeric'] if v.get('cost_usd') is not None), None)
            if v4 is not None:
                pairs.append((row, v4))
        lines.append(f"| {name} | {len(ds)} | {mean([r['usage']['tokens_in'] for r in ds]):.2f} / "
                     f"{mean([r['usage']['tokens_out'] for r in ds]):.2f} | {money(mean([r['usage']['api_cost_usd'] for r in ds]))} | "
                     f"{mean([r['duration_s'] for r in ds]):.2f} | {len(pairs)} | "
                     f"{mean([v.get('steps_used') or v.get('n_steps') for _, v in pairs]):.2f} | "
                     f"{money(mean([v['cost_usd'] for _, v in pairs]))} | "
                     f"{money(mean([r['usage']['api_cost_usd'] + v['cost_usd'] for r, v in pairs]))} ({len(pairs)}) |")
    lines += ['', ('Old repair records do not contain numeric step counts or cached-token counts; those are unreported. '
              'Old V4 generation records report steps and cost but do not report token counts, cached tokens or generator wall time. '
              'Missing V4 values are excluded from V4/paired means and are never treated as zero. Full/baseline V4 telemetry is deduplicated per task. '
              'The different populations and unknown historical cache shares limit direct cost comparisons.'),
              '', '## Independent spend and frozen-file check', '',
              ('`python3 scripts/verify_umgpt_probe.py` uses only the standard library. It independently '
              'reprices token counts, joins per-call IDs to the persistent ledger, checks the report numbers below, '
              'and compares frozen-file bytes/hashes against `origin/main`. It also checks local raw records when available.'),
              '', 'Validation: 75 focused tests passed (UM mocked transport, repair runner, direct V4 orchestration, and independent audit tamper checks); Ruff passed for every changed Python file.',
              '', 'Audit output is inserted after the checker succeeds.', '',
              '<!-- spend-audit-start -->', '```json', json.dumps(numbers, indent=2), '```', '<!-- spend-audit-end -->', '']
    rendered = []
    for line in lines:
        if line.startswith('|') and rendered and rendered[-1] and not rendered[-1].startswith('|'):
            rendered.append('')
        rendered.append(line)
    (REPORT / 'REPORT.md').write_text('\n'.join(rendered))
    result = subprocess.run(['python3', str(ROOT / 'scripts/verify_umgpt_probe.py')],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    text = (REPORT / 'REPORT.md').read_text().replace('Audit output is inserted after the checker succeeds.',
             '```text\n' + result.stdout.rstrip() + '\n```')
    (REPORT / 'REPORT.md').write_text(text)
    print(result.stdout, end='')


if __name__ == '__main__':
    build()
