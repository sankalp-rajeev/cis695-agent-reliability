#!/usr/bin/env python3
"""Exhaustive G1: record all 166 pairs, then evaluate the launch gate."""

import argparse
import csv
import hashlib
import gzip
import json
import time
from pathlib import Path

import phase4_launch as launch
from reliability.verifier.collection import validate_in_container
from reliability.verifier.g1_reference import project_collection
from reliability.verifier.run_health import effective_runner, runner_startup, zero_output
from reliability.verifier.source_integrity import GeneratedInputAudit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        with launch.FrozenContainer(spec.instance_id,spec.patch_path.read_text(),image=spec.image_id,
            experiment_id='phase4_fix15_G1',source_spec=spec.source,
            source_receipt_path=folder/'pristine_source_receipt.json') as container:
            stages.append({'stage':'pristine_source','status':'VERIFIED','input_count':1,'output_count':1})
            audit=GeneratedInputAudit(container.generated_snapshot)
            audit.stage('patch_application',lambda patched=patched:container.set_patched(patched))
            stages.append({'stage':'patch_application','status':'APPLIED' if patched else 'BASE_READY','input_count':1,'output_count':1})
            validation=audit.stage('native_collection',lambda spec=spec,deadline=deadline:validate_in_container(container,spec.tests,spec.runner,timeout_s=max(0.001,deadline-time.monotonic())))
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
    except BaseException as exc:  # noqa: BLE001
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
    # Each persistence error belongs to this pair, even when its folder is unwritable.
    for name, value in [('generated_inputs.json', audit.to_dict() if audit else None), ('health.json', health)]:
        if value is None:
            continue
        try:
            launch.write(folder/name, value)
        except (KeyboardInterrupt,SystemExit):
            raise
        except BaseException as exc:
            stages.append({'stage':'pair_recording','status':'ERROR','input_count':1,'output_count':0,
                           'message':name+': '+repr(exc)})
            health['status']='BLOCKED'
            health['G3']=zero_output(stages)
    return health


def guarded_pair(spec, patched, output, reference=None):
    try:
        return audit_pair(spec, patched, output, reference)
    except (KeyboardInterrupt,SystemExit) as exc:
        health={'task':spec.instance_id,'tree':'patched' if patched else 'base',
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
    except BaseException as exc:
        # Even receipt construction and writes are inside the per-pair boundary.
        stage = {'stage':'pair_error','status':'ERROR','input_count':1,'output_count':0,'message':repr(exc)}
        return {'task':spec.instance_id,'tree':'patched' if patched else 'base','status':'BLOCKED',
                'collector_status':'BLOCKED_UPSTREAM','stages':[stage], 'COLLECTOR_FALLBACK_slots':0,
                'module_skipped_slots':0,'INVALID_ID_slots':None,'native_collected_ids':[],
                'G2':'NOT_EVALUATED_NO_TEST_EXECUTION','G3':zero_output([stage]),
                'tests_executed':0,'zero_body_commands_only':True,'duration_s':0}


def compare_invalid_slots(before, output, rows):
    comparison=[];inputs={}
    for row in rows:
        path=before/'tasks'/row['instance_id']/row['tree']/'collection.json'
        path=path if path.exists() else path.with_suffix('.json.gz')
        raw=path.read_bytes()
        inputs[str(path)]=hashlib.sha256(raw).hexdigest()
        receipt=json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
        previous=sum(r['validation_status']=='INVALID_ID' for r in receipt['records'])
        current=row['INVALID_ID_slots']
        comparison.append({'instance_id':row['instance_id'],'tree':row['tree'],
            'INVALID_ID_before':previous,'INVALID_ID_after':current,
            'delta':current-previous if current is not None else None,
            'after_collection_available':current is not None})
    with (output/'invalid_id_comparison.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(comparison[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(comparison)
    launch.write(output/'comparison_inputs.json',{'before_collection_sha256':inputs,
        'before':str(before),'after':'Fix 15 G1 collection receipts only',
        'attempt2_outcomes_read':False,'tests_executed':0})


def main(output, before=None):
    if output.exists():
        raise ValueError('Use a fresh G1 directory')
    specs=launch.validate_inputs(launch.DEFAULT_FROZEN,Path('/home/sankalp/cg_repos/task_archives'),
        launch.ROOT/'runs/phase4_fix10_provenance/swebench-4.0.4-py3-none-any.whl',launch.PROVENANCE,launch.PREFLIGHT)
    references=launch.load_reference()
    if set(references) != {s.instance_id for s in specs}:
        raise ValueError("G1 requires the frozen reference for every task")
    output.mkdir(parents=True)
    launch.write(output/'plan.json',launch.plan_for(specs))
    rows=[];failures=[];started=time.monotonic()
    for spec in specs:
        for patched in (False,True):
            tree='patched' if patched else 'base';folder=output/'tasks'/spec.instance_id/tree
            health=guarded_pair(spec,patched,output,references[spec.instance_id][tree])
            stages=health['stages'];collector_status=health['collector_status'];g3=health['G3']
            fallback=health['COLLECTOR_FALLBACK_slots']
            for stage in stages:
                failed = stage['status'] in ('COLLECTION_ERROR','RUNNER_UNAVAILABLE','NOT_REACHED','ERROR')
                if failed or zero_output([stage])['halt']:
                    failures.append({'instance_id':spec.instance_id,'tree':tree,'stage':stage['stage'],
                        'module':stage.get('module',''),'inputs':stage['input_count'],'outputs':stage['output_count'],
                        'status':stage['status'],'allowed_exception':json.dumps(stage.get('allowed_exception',[])),
                        'diagnostic':'\n'.join(stage.get('messages',[])) or stage.get('message',''),
                        'proposed_category':proposed_failure_category(stage)})
            row={'instance_id':spec.instance_id,'tree':tree,'runner':effective_runner(spec),
                'repo':spec.source.pre_install.repo,'version':spec.source.pre_install.version,
                'status':health['status'],'collector_status':collector_status,'fallback_slots':fallback,
                'zero_output_halt':g3['halt'],'module_skipped_slots':health['module_skipped_slots'],
                'INVALID_ID_slots':health['INVALID_ID_slots'],
                'G2_projected_halt':health.get('G2_projection',{}).get('halt',True),
                'tests_executed':0,'duration_s':health['duration_s']}
            rows.append(row);print(json.dumps({'event':'G1_end',**row}),flush=True)
    exclusions=[]
    for spec in specs:
        for tree in ('base','patched'):
            health_path=output/'tasks'/spec.instance_id/tree/'health.json'
            if health_path.exists():
                evidence=json.loads(health_path.read_text())
                exclusions.extend(dict(instance_id=spec.instance_id,tree=tree,selected_id=t) for t in evidence.get('G2_projection',{}).get('excluded_spurious_ids',()))
    launch.write(output/'reference_hygiene.json',{'exclusions':exclusions,'tree_id_slots':len(exclusions),'unique_ids':len({r['selected_id'] for r in exclusions})})
    with (output/'tasks.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    with (output/'failures.csv').open('w',newline='') as stream:
        fields=['instance_id','tree','stage','module','inputs','outputs','status','allowed_exception','diagnostic','proposed_category']
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(failures)
    if before is not None:
        compare_invalid_slots(before,output,rows)
    summary={'launch_allowed':len(rows)==len(specs)*2 and all(r['status']=='READY' for r in rows),'task_tree_count':len(rows),
        'exhaustive':True,'gate_evaluated_after_all_pairs':True,
        'projected_halts':[{'task':r['instance_id'],'tree':r['tree']} for r in rows if r['G2_projected_halt']],
        'blocked_task_trees':[{'task':r['instance_id'],'tree':r['tree']} for r in rows if r['status']!='READY'],
        'tests_executed':0,'wall_s':time.monotonic()-started,'correctness_labels_read':False,
        'attempt2_outcomes_read':False}
    launch.write(output/'summary.json',summary)
    paths=[Path(__file__).resolve(),launch.ROOT/'scripts/phase4_launch.py',
        *sorted((launch.ROOT/'src/reliability/verifier').glob('*.py')),
        launch.ROOT/'reports/next_phases/phase4_rerun/fix11_12_scope/run_health_exceptions.json',
        launch.REFERENCE/'manifest.json',launch.REFERENCE/'reference_ids.json.gz']
    launch.write(output/'manifest.json',{'source_sha256':{str(p.relative_to(launch.ROOT)):sha(p) for p in paths},
        'receipt_sha256':{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file()},
        'tests_executed':0,'flags':{'cpu_shares':2048,'network':'none','parallelism':1,'pull':'never'}})
    print(json.dumps(summary,indent=2))
    return 0 if summary['launch_allowed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--before',type=Path,default=launch.ROOT/'reports/next_phases/phase4_rerun/fix14_g1')
    args=parser.parse_args()
    raise SystemExit(main(args.output,args.before))
