"""G2-G6: execution health uses identity admission, never result verdicts."""

from __future__ import annotations

import json
import base64
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


def exception_rules():
    path=Path(__file__).resolve().parents[3]/'reports/next_phases/phase4_rerun/fix11_12_scope/run_health_exceptions.json'
    return json.loads(path.read_text())['exceptions']


def allowed_failure(exceptions, task, module, stage, message, *, tree=None):
    return next((r['cause'] for r in exceptions if r['instance_id'] == task
        and r['module'] == module and tree in r.get('trees',()) and stage in r['stages'] and r['required_message'] in message), None)


def monotonicity(reference, admitted, invalid):
    reference, admitted, invalid = set(reference), set(admitted), set(invalid)
    lost = sorted(reference - admitted)
    fraction = len(lost)/len(reference) if reference else 0.0
    return {'reference_ids': len(reference), 'admitted_reference_ids': len(reference & admitted),
            'proven_INVALID_ID_reference_ids': len(reference & invalid), 'lost_ids': lost,
            'lost_count': len(lost), 'lost_fraction': fraction,
            'halt': len(lost) >= 10 and bool(reference) and len(lost)*100 >= len(reference)}


IDENTITY_LOSS_STATUSES = frozenset({TestStatus.COLLECTION_ERROR, TestStatus.INVALID_ID,
    TestStatus.NOT_RUN, TestStatus.RUNNER_UNAVAILABLE})
BUDGET_STATUSES = frozenset({TestStatus.NOT_REACHED, TestStatus.TIMEOUT})


def identity_failure(result, receipt, run):
    """Test outcomes never turn into executor identity failures."""
    if result is None:
        return True
    if result.status in (TestStatus.INVALID_ID, TestStatus.RUNNER_UNAVAILABLE, TestStatus.NOT_RUN):
        return True
    if result.status is TestStatus.COLLECTION_ERROR:
        # Execution load failures need their own first-attempt/retry proof.
        if any(e.get('event') == 'start' for e in run.events):
            return receipt.get('failure_status') in ('COLLECTION_ERROR', 'RUNNER_UNAVAILABLE')
        return True  # collection-only captures have no execution events
    return False


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
        lost=(identity_failure(result,receipt,run)
              or identity in unmatched or receipt.get('collector_fallback')
              or receipt.get('validation_status') in ('INVALID_ID','COLLECTION_ERROR','RUNNER_UNAVAILABLE'))
        if not lost and execution and receipt.get('runnable_ids'):
            skipped={p[0] for p in receipt.get('module_skip_instances',())}
            lost=any(t not in skipped and ((t not in execution and result.status not in BUDGET_STATUSES) or
                     (t in execution and identity_failure(execution[t],receipt,run))
                     or t in unmatched) for t in receipt['runnable_ids'])
        if not lost:preserved.add(identity)
    result=monotonicity(reference,preserved,invalid)
    result['mode']='IDENTITY_ONLY'
    result['preserved_reference_ids']=result['admitted_reference_ids']
    result['budget_ids']=sorted(t for t in reference if t in results and results[t].status in BUDGET_STATUSES)
    result['error_ids']=sorted(t for t in reference if t in results and results[t].status.value in ('error','crash'))
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
                # Raw stage counts remain unchanged; G3 only checks collection.
        stages.append(stage)
    return stages


def zero_output(stages):
    failed = [s['stage'] for s in stages if s['stage'] in ('native_collection','static_collection','static_validation','collection') and s['input_count'] > 0 and s['output_count'] == 0
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
    blocked_skip = set(reference.get('drift_reference_ids',reference.get('module_skip_blocked_ids',()))) if isinstance(reference,dict) else reference_ids
    skipped = {r.test_id for r in run.results if r.status is TestStatus.SKIPPED}
    skipped_instances = {r.test_id for r in run.execution_results if r.status is TestStatus.SKIPPED}
    skipped |= {r['selected_id'] for r in run.validation if r.get('module_skip_reason')
                or skipped_instances.intersection(r.get('runnable_ids', ()))}
    drift_ids = skipped & blocked_skip
    # Outcome admission and identity preservation are separate measurements.
    g2 = identity_monotonicity(reference_ids,run)
    drift_reference = reference_ids | blocked_skip
    drift = monotonicity(drift_reference,drift_reference-drift_ids,())
    drift['mode']='ENVIRONMENT_DRIFT'
    drift['skipped_reference_ids']=sorted(drift_ids)
    g2['reference_source'] = reference.get('reference_source', 'G1_NATIVE_COLLECTION' if empty_original else 'FROZEN_ORIGINAL') if isinstance(reference, dict) else 'FROZEN_ORIGINAL'
    g2['missing_G1_reference'] = missing_g1
    g2['halt'] |= missing_g1
    g2['module_skip_incompatible_reference_ids'] = sorted(drift_ids)
    g1_ids=set(reference.get('g1_collected_ids',())) if isinstance(reference,dict) else set()
    g1_guard=identity_monotonicity(g1_ids,run)
    g1_guard['reference_source']='G1_NATIVE_COLLECTION'
    if isinstance(reference,dict) and reference.get('g1_reference_required') and 'g1_collected_ids' not in reference:
        g1_guard.update(halt=True,missing_G1_reference=True)
    stages = identity_stage_health(run,confirmation=confirmation)
    g3 = zero_output(stages)
    reasons = (['G2 ' + tree + ': lost ' + str(g2['lost_count']) + ' reference IDs'] if g2['halt'] else [])
    if drift['halt']:
        reasons.append('Environment drift ' + tree + ': ' + str(len(drift_ids)) + ' reference IDs now SKIPPED')
    if g1_guard['halt']:
        reasons.append('G1-collected ' + tree + ': lost ' + str(g1_guard['lost_count']) + ' native identities')
    if missing_g1:
        reasons.append('G2 ' + tree + ': non-empty selection requires G1 native reference')
    reasons += ['G3 ' + tree + ': zero output at ' + s for s in g3['zero_output_stages']]
    return {'task': task, 'tree': tree, 'collector_status': run.validation_summary.get('collector_status', 'NOT_REPORTED'),
            'input_ids': len(run.requested_tests), 'COLLECTOR_FALLBACK_slots': len(fallback),
            'collector_fallback_ids': sorted(fallback), 'admitted_ids': len(admitted),
            'admitted_share': len(admitted)/len(run.requested_tests) if run.requested_tests else None,
            'G2': g2, 'G1_collected_guard':g1_guard, 'environment_drift':drift, 'G3': g3,
            'outcome_counts':{status.value:sum(r.status is status for r in run.results) for status in TestStatus},
            'reference_current_outcomes':{r.test_id:r.status.value for r in run.results if r.test_id in reference_ids},
            'unstable_confirmation_ids':sorted({r.test_id for r in (*run.results,*run.execution_results) if confirmation and r.status is TestStatus.TIMEOUT}), 'stages': stages, 'halt': bool(reasons), 'halt_reasons': reasons}


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


def module_execution_stages(task, tree, runner, run, exceptions):
    """Independently match pre-registered load failures in actual execution events."""
    from reliability.verifier.result_parser import mapping_for
    data=base64.b64decode(run.runner_log_b64 or '')
    mapper=mapping_for(tuple(r.test_id for r in run.results),runner)
    stages=[]
    for event in run.events:
        if event.get('event')!='end' or not event.get('load_failure') or event.get('split'):
            continue
        start=next((e for e in run.events if e.get('event')=='start' and e.get('batch')==event.get('batch')),{})
        message=data[start.get('offset',0):event.get('offset',len(data))].decode('utf-8','replace')
        module=event.get('module',start.get('module',''))
        ids=sorted({t for native in event.get('missing_ids',start.get('ids',())) for t in mapper(native)})
        cause=allowed_failure(exceptions,task,module,'module_execution',message,tree=tree)
        stages.append(dict(stage='module_execution',module=module,tree=tree,
            status='COLLECTION_ERROR',input_count=len(ids),input_ids=ids,output_count=0,
            allowed_exception=[cause] if cause else [],message=message))
    return stages
