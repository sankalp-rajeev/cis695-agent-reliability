"""G2-G6: execution health uses identity admission, never result verdicts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from reliability.verifier.accounting import ADMITTED_STATUSES


class RunHealthError(RuntimeError):
    def __init__(self, record):
        self.record = record
        super().__init__('Run-health halt: ' + '; '.join(record.get('halt_reasons', [])))


def effective_runner(spec):
    return 'sympy' if spec.source.pre_install.repo == 'sympy/sympy' else spec.runner.name


def covering_order(specs):
    groups = {}
    for spec in specs:
        key = (effective_runner(spec), spec.source.pre_install.repo, spec.source.pre_install.version)
        if key not in groups or spec.instance_id < groups[key].instance_id:
            groups[key] = spec
    first = sorted(groups.values(), key=lambda s: s.instance_id)
    ids = {s.instance_id for s in first}
    return tuple(first + [s for s in specs if s.instance_id not in ids])


def allowed_failure(exceptions, task, module, stage, message):
    return next((r['cause'] for r in exceptions if r['instance_id'] == task
        and r['module'] == module and stage in r['stages'] and r['required_message'] in message), None)


def monotonicity(reference, admitted, invalid):
    reference, admitted, invalid = set(reference), set(admitted), set(invalid)
    lost = sorted(reference - admitted - invalid)
    fraction = len(lost)/len(reference) if reference else 0.0
    return {'reference_ids': len(reference), 'admitted_reference_ids': len(reference & admitted),
            'proven_INVALID_ID_reference_ids': len(reference & invalid), 'lost_ids': lost,
            'lost_count': len(lost), 'lost_fraction': fraction,
            'halt': len(lost) >= 10 or (bool(reference) and len(lost)*100 >= len(reference))}


def zero_output(stages):
    failed = [s['stage'] for s in stages if s['input_count'] > 0 and s['output_count'] == 0
              and not s.get('allowed_exception')]
    return {'halt': bool(failed), 'zero_output_stages': failed}


def health_for_run(task, tree, run, reference):
    admitted = {r.test_id for r in run.results if r.status in ADMITTED_STATUSES}
    # Expansion admission must be unanimous, as in the committed owner rule.
    receipts = {r['selected_id']: r for r in run.validation}
    admitted = {t for t in admitted if not receipts or receipts.get(t, {}).get('admitted', False)}
    invalid = {r['selected_id'] for r in run.validation
               if r.get('validation_status') == 'INVALID_ID' and not r.get('unavailable')}
    g2 = monotonicity(reference, admitted, invalid)
    stages = list(run.stage_health)
    g3 = zero_output(stages)
    reasons = (['G2 ' + tree + ': lost ' + str(g2['lost_count']) + ' reference IDs'] if g2['halt'] else [])
    reasons += ['G3 ' + tree + ': zero output at ' + s for s in g3['zero_output_stages']]
    return {'task': task, 'tree': tree, 'collector_status': run.validation_summary.get('collector_status', 'NOT_REPORTED'),
            'input_ids': len(run.requested_tests), 'admitted_ids': len(admitted),
            'admitted_share': len(admitted)/len(run.requested_tests) if run.requested_tests else None,
            'G2': g2, 'G3': g3, 'stages': stages, 'halt': bool(reasons), 'halt_reasons': reasons}


def append_health(path: Path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        stream.write(json.dumps(record)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def runner_startup(container, runner, *, timeout_s=60):
    command = {'pytest': 'python -m pytest --help', 'django': 'python tests/runtests.py --help',
               'sympy': "PYTHONWARNINGS='ignore::UserWarning,ignore::SyntaxWarning' python bin/test --help"}.get(runner)
    if command is None:
        return {'stage':'runner_startup','status':'RUNNER_UNAVAILABLE','input_count':1,'output_count':0,
                'message':'Unsupported runner: '+runner,'tests_executed':0}
    try:
        rc, output = container.exec(command, timeout_s=timeout_s)
        ok = rc == 0 and bool(output.strip())
        return {'stage':'runner_startup','status':'COMPLETE' if ok else 'RUNNER_UNAVAILABLE',
                'input_count':1,'output_count':int(ok),'returncode':rc,'command':command,
                'message':output[-4000:] if not ok else '', 'tests_executed':0}
    except (RuntimeError, TimeoutError, OSError) as exc:
        return {'stage':'runner_startup','status':'RUNNER_UNAVAILABLE','input_count':1,'output_count':0,
                'command':command,'message':str(exc),'tests_executed':0}
