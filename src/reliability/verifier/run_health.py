"""G2-G6: execution health uses identity admission, never result verdicts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from reliability.verifier.accounting import ADMITTED_STATUSES
from reliability.verifier.regression import TestStatus


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
    lost = sorted(reference - admitted)
    fraction = len(lost)/len(reference) if reference else 0.0
    return {'reference_ids': len(reference), 'admitted_reference_ids': len(reference & admitted),
            'proven_INVALID_ID_reference_ids': len(reference & invalid), 'lost_ids': lost,
            'lost_count': len(lost), 'lost_fraction': fraction,
            'halt': len(lost) >= 10 or (bool(reference) and len(lost)*100 >= len(reference))}


IDENTITY_LOSS_STATUSES = frozenset({TestStatus.COLLECTION_ERROR, TestStatus.INVALID_ID,
    TestStatus.NOT_RUN, TestStatus.RUNNER_UNAVAILABLE})
BUDGET_STATUSES = frozenset({TestStatus.NOT_REACHED, TestStatus.TIMEOUT})


def identity_monotonicity(reference, run):
    """Preserve identity independently of terminal outcome/admission."""
    reference=set(reference)
    results=run.by_id()
    execution={r.test_id:r for r in run.execution_results}
    receipts={r['selected_id']:r for r in run.validation}
    unmatched=set(run.unmatched_ids)
    preserved=set();invalid=set()
    for identity in reference:
        result=results.get(identity);receipt=receipts.get(identity,{})
        if receipt.get('validation_status')=='INVALID_ID':invalid.add(identity)
        lost=(result is None or result.status in IDENTITY_LOSS_STATUSES
              or identity in unmatched or receipt.get('collector_fallback')
              or receipt.get('validation_status') in ('INVALID_ID','COLLECTION_ERROR','RUNNER_UNAVAILABLE'))
        if not lost and execution and receipt.get('runnable_ids'):
            skipped={p[0] for p in receipt.get('module_skip_instances',())}
            lost=any(t not in skipped and ((t not in execution and result.status not in BUDGET_STATUSES) or
                     (t in execution and execution[t].status in IDENTITY_LOSS_STATUSES)
                     or t in unmatched) for t in receipt['runnable_ids'])
        if not lost:preserved.add(identity)
    result=monotonicity(reference,preserved,invalid)
    result['mode']='IDENTITY_ONLY'
    result['budget_ids']=sorted(t for t in reference if t in results and results[t].status in BUDGET_STATUSES)
    result['error_ids']=sorted(t for t in reference if t in results and results[t].status is TestStatus.ERROR)
    result['unmatched_reference_ids']=sorted(reference & unmatched)
    return result


def identity_stage_health(run, *, confirmation=False):
    """Budget gaps, and unstable confirmations, are not zero identity output."""
    protected=BUDGET_STATUSES | ({TestStatus.ERROR} if confirmation else set())
    stages=[]
    for original in run.stage_health:
        stage=dict(original)
        if stage['stage'] in ('execution','admission'):
            cases=(run.execution_results or run.results) if stage['stage']=='execution' else run.results
            count=sum(r.status in protected for r in cases)
            if count:
                stage['identity_input_original_count']=stage['input_count']
                stage['non_identity_gap_count']=count
                stage['input_count']=max(0,stage['input_count']-count)
        stages.append(stage)
    return stages


def zero_output(stages):
    failed = [s['stage'] for s in stages if s['input_count'] > 0 and s['output_count'] == 0
              and s.get('status') not in ('NOT_REACHED','TIMEOUT')
              and not s.get('allowed_exception') and not (
                  s.get('status')=='MODULE_SKIPPED' and s.get('module_skip_reason','').strip()
                  and s.get('native_skip_recorded'))]
    return {'halt': bool(failed), 'zero_output_stages': failed}


def health_for_run(task, tree, run, reference, *, confirmation=False):
    admitted = {r.test_id for r in run.results if r.status in ADMITTED_STATUSES}
    # Expansion admission must be unanimous, as in the committed owner rule.
    receipts = {r['selected_id']: r for r in run.validation}
    fallback = {r['selected_id'] for r in run.validation if r.get('collector_fallback')}
    admitted = {t for t in admitted if t not in fallback
                and (not receipts or receipts.get(t, {}).get('admitted', False))}
    invalid = {r['selected_id'] for r in run.validation
               if r.get('validation_status') == 'INVALID_ID' and not r.get('unavailable')}
    reference_ids = set(reference['admitted_ids']) if isinstance(reference,dict) else set(reference)
    empty_original = not reference_ids and (bool(run.requested_tests) or
        (isinstance(reference, dict) and bool(reference.get('g1_collected_ids'))))
    missing_g1 = empty_original and (not isinstance(reference, dict) or 'g1_collected_ids' not in reference)
    if empty_original and not missing_g1:
        reference_ids = set(reference['g1_collected_ids'])
    blocked_skip = set(reference.get('module_skip_blocked_ids',())) if isinstance(reference,dict) else reference_ids
    if empty_original:
        blocked_skip |= reference_ids
    skipped = {r.test_id for r in run.results if r.status is TestStatus.SKIPPED}
    skipped_instances = {r.test_id for r in run.execution_results if r.status is TestStatus.SKIPPED}
    skipped |= {r['selected_id'] for r in run.validation if r.get('module_skip_reason')
                or skipped_instances.intersection(r.get('runnable_ids', ()))}
    lost_to_skip = skipped & blocked_skip
    # ERROR reference evidence also cannot be replaced by a module-level skip.
    g2 = monotonicity(reference_ids | lost_to_skip, admitted-lost_to_skip, invalid)
    if confirmation or empty_original:
        lost_to_skip=set()
        g2=identity_monotonicity(reference_ids,run)
    g2['reference_source'] = reference.get('reference_source', 'G1_NATIVE_COLLECTION' if empty_original else 'FROZEN_ORIGINAL') if isinstance(reference, dict) else 'FROZEN_ORIGINAL'
    g2['missing_G1_reference'] = missing_g1
    g2['halt'] |= missing_g1
    g2['module_skip_incompatible_reference_ids'] = sorted(lost_to_skip)
    g1_ids=set(reference.get('g1_collected_ids',())) if isinstance(reference,dict) else set()
    g1_guard=identity_monotonicity(g1_ids,run)
    g1_guard['reference_source']='G1_NATIVE_COLLECTION'
    if isinstance(reference,dict) and reference.get('g1_reference_required') and 'g1_collected_ids' not in reference:
        g1_guard.update(halt=True,missing_G1_reference=True)
    stages = identity_stage_health(run,confirmation=confirmation)
    g3 = zero_output(stages)
    reasons = (['G2 ' + tree + ': lost ' + str(g2['lost_count']) + ' reference IDs'] if g2['halt'] else [])
    if g1_guard['halt']:
        reasons.append('G1-collected ' + tree + ': lost ' + str(g1_guard['lost_count']) + ' native identities')
    if missing_g1:
        reasons.append('G2 ' + tree + ': non-empty selection requires G1 native reference')
    reasons += ['G3 ' + tree + ': zero output at ' + s for s in g3['zero_output_stages']]
    return {'task': task, 'tree': tree, 'collector_status': run.validation_summary.get('collector_status', 'NOT_REPORTED'),
            'input_ids': len(run.requested_tests), 'COLLECTOR_FALLBACK_slots': len(fallback),
            'collector_fallback_ids': sorted(fallback), 'admitted_ids': len(admitted-lost_to_skip),
            'admitted_share': len(admitted-lost_to_skip)/len(run.requested_tests) if run.requested_tests else None,
            'G2': g2, 'G1_collected_guard':g1_guard, 'G3': g3,
            'unstable_confirmation_ids':sorted({r.test_id for r in (*run.results,*run.execution_results) if confirmation and r.status in (TestStatus.ERROR,TestStatus.TIMEOUT)}), 'stages': stages, 'halt': bool(reasons), 'halt_reasons': reasons}


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
