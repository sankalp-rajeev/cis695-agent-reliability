"""Inline G1 pair audit moved from the Phase 4 exhaustive preflight."""
import json
import time
from reliability.verifier import guarded_v2 as launch
from reliability.verifier.collection import validate_in_container
from reliability.verifier.native_reference import project_collection
from reliability.verifier.run_health import effective_runner, runner_startup, zero_output
from reliability.verifier.container import PatchApplyError
from reliability.verifier.source_integrity import GeneratedInputAudit, SourceIntegrityError
from reliability.verifier.generic_health import check_generic_pair, rules_stamp

def proposed_failure_category(stage):
    if stage.get('allowed_exception'):
        return 'prelisted_missing_evidence'
    message='\n'.join(stage.get('messages',[]))+'\n'+stage.get('message','')
    if stage['status']=='RUNNER_UNAVAILABLE':return 'runner_startup_or_interpreter_unavailable'
    if stage['status']=='NOT_REACHED':return 'stage_budget_exhausted'
    if 'SourceIntegrityError' in message:return 'source_integrity_mismatch'
    if 'No module named' in message:return 'module_import_dependency_failure'
    if 'AttributeError' in message or 'FileNotFoundError' in message:return 'module_import_failure'
    if stage['stage']=='native_collection' and stage['output_count']==0:return 'zero_collection_without_recorded_module_skip'
    return 'stage_error_requires_review'

def audit_pair(spec, patched, output, reference=None):
    tree='patched' if patched else 'base'
    folder=output/'tasks'/spec.instance_id/tree
    stages=[];audit=None;validation=None;start=time.monotonic()
    deadline=start+1800
    print(json.dumps({'event':'G1_start','task':spec.instance_id,'tree':tree}),flush=True)
    try:
        folder.mkdir(parents=True)
        with launch.FrozenContainer(spec.instance_id,spec.patch_path.read_bytes().decode('utf-8'),image=spec.image_id,
            experiment_id=getattr(spec,'experiment_id','e2e_v1_4_1_G1'),source_spec=spec.source,
            source_receipt_path=folder/'pristine_source_receipt.json') as container:
            if container.source_integrity.get('status') != 'VERIFIED':
                raise ValueError('A fresh VERIFIED pristine receipt is required')
            launch.write(folder/'pristine_generated_inputs.json', container.generated_snapshot())
            stages.append({'stage':'pristine_source','status':'VERIFIED','input_count':1,'output_count':1})
            audit=GeneratedInputAudit(container.generated_snapshot)
            audit.stage('patch_application',lambda patched=patched:container.set_patched(patched))
            stages.append({'stage':'patch_application','status':'APPLIED' if patched else 'BASE_READY','input_count':1,'output_count':1})
            validation=audit.stage('native_collection',lambda spec=spec,deadline=deadline:validate_in_container(container,spec.tests,spec.runner,timeout_s=max(0.001,deadline-time.monotonic()),tree=tree))
            stages.extend(validation.stage_health)
            launch.write(folder/'collection.json',validation.to_dict())
            if time.monotonic() >= deadline:
                stages.append({'stage':'runner_startup','status':'NOT_REACHED','input_count':1,'output_count':0,'tests_executed':0})
            else:
                stages.append(audit.stage('runner_startup',lambda spec=spec,deadline=deadline:runner_startup(container,effective_runner(spec),timeout_s=min(60,deadline-time.monotonic()))))
            fallback=sum(r.collector_fallback for r in validation.records)
            collector_status=validation.to_dict()['collector_status']
            unexpected=[s for s in stages if s['status'] in ('COLLECTION_ERROR','RUNNER_UNAVAILABLE','NOT_REACHED') and not s.get('allowed_exception')]
            g3=zero_output(stages)
            ok=not unexpected and not g3['halt']
    except (KeyboardInterrupt,SystemExit):
        raise
    except (SourceIntegrityError, PatchApplyError):
        # A patch git rejects fails V1 (amendment B9), never a run-health block.
        raise
    except Exception as exc:  # noqa: BLE001
        stages.append({'stage':'stage_error','status':'ERROR','input_count':1,'output_count':0,'message':repr(exc)})
        fallback=0;collector_status='BLOCKED_UPSTREAM';g3=zero_output(stages);ok=False
    for name in ('pristine_source','patch_application','native_collection','runner_startup'):
        if not any(s['stage']==name for s in stages):
            stages.append({'stage':name,'status':'BLOCKED_UPSTREAM','input_count':0,'output_count':0})
    health={'task':spec.instance_id,'tree':tree,'status':'READY' if ok else 'BLOCKED',
        'collector_status':collector_status,'stages':stages,'COLLECTOR_FALLBACK_slots':fallback,
        'G2':'NOT_EVALUATED_NO_TEST_EXECUTION','G3':g3,'tests_executed':0,
        'module_skipped_slots':validation.to_dict()['module_skipped_slots'] if validation else 0,
        'INVALID_ID_slots':sum(r.to_dict()['validation_status']=='INVALID_ID' for r in validation.records) if validation else None,
        'native_collected_ids':[r.selected_id for r in validation.records if r.valid and not r.collector_fallback and not r.module_skip_reason] if validation else [],
        'zero_body_commands_only':True,'duration_s':time.monotonic()-start}
    if reference is not None:
        projection = project_collection(spec.instance_id,tree,validation.to_dict(),reference) if validation else {'halt':True,'G2':{'halt':True,'reason':'native receipt unavailable'},'excluded_spurious_ids':[]}
        health['G2_projection']=projection
        health['G2']=projection['G2']
        if projection['halt']:
            health['status']='BLOCKED'
    health['generic_exception_rules'] = rules_stamp()
    if health['status'] == 'READY' and any(s.get('exception_source') == 'generic_rule' for s in stages):
        health['status'] = 'PENDING_BOTH_TREES'
    # Each persistence error belongs to this pair, even when its folder is unwritable.
    for name, value in [('generated_inputs.json', audit.to_dict() if audit else None), ('health.json', health)]:
        if value is None:
            continue
        try:
            launch.write(folder/name, value)
        except (KeyboardInterrupt,SystemExit):
            raise
        except Exception as exc:
            stages.append({'stage':'pair_recording','status':'ERROR','input_count':1,'output_count':0,
                           'message':name+': '+repr(exc)})
            health['status']='BLOCKED'
            health['G3']=zero_output(stages)
    return health


def finalize_generic_pair(spec, output, healths):
    """Resolve provisional records before G1 opens; persist the paired proof."""
    reasons = check_generic_pair({h['tree']: h['stages'] for h in healths})
    for health in healths:
        generic = any(s.get('exception_source') == 'generic_rule' or s.get('generic_rule_rejected')
                      for s in health['stages'])
        if not generic:
            continue
        health['generic_pair_halt_reasons'] = reasons
        health['G3'] = zero_output(health['stages'])
        if reasons:
            health['status'] = 'BLOCKED'
            health['collector_status'] = 'COLLECTION_ERROR'
        elif health['status'] == 'PENDING_BOTH_TREES':
            health['status'] = 'READY'
        folder = output / 'tasks' / spec.instance_id / health['tree']
        collection = json.loads((folder / 'collection.json').read_text())
        collection['stage_health'] = [s for s in health['stages'] if s['stage'] == 'native_collection']
        collection['collector_status'] = health['collector_status']
        collection['generic_exception_rules'] = rules_stamp()
        launch.write(folder / 'collection.json', collection)
        launch.write(folder / 'health.json', health)
    return reasons

def guarded_pair(spec, patched, output, reference=None):
    try:
        return audit_pair(spec, patched, output, reference)
    except (KeyboardInterrupt,SystemExit) as exc:
        health={'task':spec.instance_id,'tree':'patched' if patched else 'base',
                'generic_exception_rules':rules_stamp(),
                'status':'INTERRUPTED','interruption':type(exc).__name__,'message':repr(exc),
                'tests_executed':0,'gate_evaluated':False}
        try:
            launch.write(output/'tasks'/spec.instance_id/health['tree']/'health.json',health)
        except BaseException as write_error:
            health['recording_error']=repr(write_error)
            try:
                launch.write(output/'interruption.json',health)
            except BaseException as fallback_error:
                health['fallback_recording_error']=repr(fallback_error)
        exc.g1_record=health
        raise
    except (SourceIntegrityError, PatchApplyError):
        # A patch git rejects fails V1 (amendment B9), never a run-health block.
        raise
    except Exception as exc:
        # Even receipt construction and writes are inside the per-pair boundary.
        stage = {'stage':'pair_error','status':'ERROR','input_count':1,'output_count':0,'message':repr(exc)}
        return {'task':spec.instance_id,'tree':'patched' if patched else 'base','status':'BLOCKED',
                'generic_exception_rules':rules_stamp(),
                'collector_status':'BLOCKED_UPSTREAM','stages':[stage], 'COLLECTOR_FALLBACK_slots':0,
                'module_skipped_slots':0,'INVALID_ID_slots':None,'native_collected_ids':[],
                'G2':'NOT_EVALUATED_NO_TEST_EXECUTION','G3':zero_output([stage]),
                'tests_executed':0,'zero_body_commands_only':True,'duration_s':0}
