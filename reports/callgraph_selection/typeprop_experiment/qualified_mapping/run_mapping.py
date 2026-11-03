"""All-83 mapping and selection-input comparison using immutable graph artifacts."""
from __future__ import annotations
import argparse
import csv
import gc
import hashlib
import json
import re
import sys
import tarfile
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXP=HERE.parent;CG=EXP.parent;ROOT=CG.parents[1]
sys.path[:0]=[str(HERE),str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from mapper import map_file
from evaluate import (patch_inputs,records,digest,csv_write,dump,verify_manifest,original_state,selections)
from callgraph_selector import Identities,VARIANTS,DEPTHS,BUDGETS
from inputs import Registry,base_test_ids,eligibility,stored_selections
from reliability.verifier.patch import parse_patch,ChangeKind
from reliability.verifier.integrity import is_test_file


def read_csv(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))


def sections(payload):
    text=payload.decode('utf-8')
    starts=[m.start() for m in re.finditer(r'(?m)^diff --git ',text)]
    result={}
    for start,end in zip(starts,[*starts[1:],len(text)]):
        block=text[start:end]
        header=re.fullmatch(r'diff --git a/(.+?) b/(.+)',block.split('\n')[0].rstrip('\r'))
        if not header:raise ValueError('unsupported_diff_header')
        path=header.group(2)
        if path in result:raise ValueError('duplicate_patch_file_section')
        result[path]=block
    return result


def inputs():
    acquisition=json.loads((CG/'inputs.json').read_text())
    manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    original=Path(json.loads((EXP/'protocol.json').read_text())['original_worktree'])
    old=read_csv(CG/'amendment2_72ad21b/changed_symbol_resolution.csv')
    return acquisition['tasks'],manifest,original,old


def mapping():
    tasks,manifest,original,old=inputs()
    if (HERE/'mapping_protocol.json').exists():raise ValueError('Refuse to overwrite a completed/started mapping run')
    verify_manifest(original,manifest)
    patches=patch_inputs()
    protocol=dict(population=83,graph_source='frozen type-propagation edges plus unchanged Amendment 2 nodes',
        mapper='innermost direct edit owner; qualified path/kind/location; own AST excludes nested definitions and pass placeholders',
        duplicates='repeated fully qualified definitions remain ambiguous',
        new_definitions='candidate-only, no graph target or selector seed',
        module_edits='explicit file diagnostics, no module fallback',
        ambiguity='identity mapping only, not a claim about runtime dispatch',
        context_headers='not used to infer a changed name',
        original_worktree=original_state(original),
        code_sha256={p.name:digest(p) for p in [HERE/'mapper.py',Path(__file__),HERE/'test_mapper.py']},
        old_inventory_sha256=digest(CG/'amendment2_72ad21b/changed_symbol_resolution.csv'),
        graph_manifest_sha256=digest(CG/'amendment2_72ad21b/graph_manifest.json'),
        selector_source_sha256=digest(CG/'phase2/callgraph_selector.py'),eligibility_source_sha256=digest(CG/'phase2/inputs.py'),
        graph_rebuild=False,benchmark_execution=False,oracle_inputs=False)
    dump(HERE/'mapping_protocol.json',protocol)
    cache=HERE/'task_artifacts';cache.mkdir(exist_ok=True)
    results=[];file_diagnostics=[];ledger=[];old_audit=[];task_rows=[]
    diagnosis={ (r['task_id'],r['file'],r['changed_symbol']):r for r in read_csv(EXP/'changed_symbol_diagnosis/cases.csv') }
    for task in tasks:
        iid=task['instance_id'];directory=original/'reports/callgraph_selection'/manifest[iid]['directory']
        nodes=list(records(directory/'nodes.jsonl.gz'));node_index={n['id']:n for n in nodes}
        if digest(task['archive_path'])!=task['archive_sha256']:raise ValueError('archive hash mismatch')
        patch=patches[iid];changes=parse_patch(patch);blocks=sections(patch)
        file_outputs={};task_records=[]
        with tarfile.open(task['archive_path'],'r:') as archive:
            if archive.pax_headers.get('comment')!=task['base_commit']:raise ValueError('base commit mismatch')
            for change in changes:
                if not change.path.endswith('.py') or is_test_file(change.path) or change.is_binary:continue
                base_path=change.old_path or change.path
                if change.kind==ChangeKind.ADDED:base=None
                else:
                    try:
                        member=archive.getmember('testbed/'+base_path)
                        base=archive.extractfile(member).read() if member.isfile() else None
                    except KeyError:base=None
                output=map_file(base_path,change.path,base,blocks[change.path],nodes,
                    added_file=change.kind==ChangeKind.ADDED,deleted_file=change.kind==ChangeKind.DELETED)
                file_outputs[base_path]=output
                for ordinal,row in enumerate(output['records'],1):
                    record=dict(instance_id=iid,repo=task['repo'],record_id=f'{iid}:{base_path}:{ordinal}',
                        graph_status=manifest[iid]['graph_status'],**row)
                    task_records.append(record);results.append(record)
                for diagnostic in output['diagnostics']:
                    file_diagnostics.append(dict(instance_id=iid,repo=task['repo'],path=change.path,base_path=base_path,**diagnostic))
        for legacy in [r for r in old if r['instance_id']==iid]:
            path=legacy['base_path'];name=legacy['name'];output=file_outputs[path]
            matches=[r for r in task_records if r['base_path']==path and r.get('name')==name]
            errors=[r for r in task_records if r['base_path']==path and r['record_kind']=='file_analysis_error']
            previous_targets=json.loads(legacy['targets']);retained=set(previous_targets)&{t for r in matches if r['status']=='resolved' for t in r['targets']}
            diag=diagnosis.get((iid,path,name))
            if errors:disposition='file_analysis_uncertain'
            elif not matches:
                disposition='excluded_docstring_false_declaration' if diag and diag['root_cause_category']=='docstring_text_misidentified_as_definition' else 'excluded_context_container_or_nonsemantic_name'
            elif all(r['status']=='new_definition' for r in matches):disposition='new_definition_separated'
            elif all(r['status']=='resolved' for r in matches):disposition='resolved_qualified_definition_set'
            elif all(r['status'] in {'resolved','new_definition'} for r in matches):disposition='split_existing_and_new_qualified_definitions'
            else:disposition='mapping_uncertainty_preserved'
            ledger.append(dict(instance_id=iid,repo=task['repo'],path=path,legacy_name=name,legacy_status=legacy['status'],
                legacy_targets=previous_targets,disposition=disposition,corrected_record_ids=[r['record_id'] for r in matches],
                corrected_qualified_names=[r['qualname'] for r in matches],corrected_statuses=[r['status'] for r in matches],
                retained_old_target_ids=sorted(retained),diagnosis_case_id=diag['case_id'] if diag else None))
            if legacy['status']=='resolved':
                for target in previous_targets:
                    node=node_index[target]
                    definitions=[d for d in output['definitions'] if d['side']=='base' and d['qualname']==node['qualname'] and d['line']==node['line'] and d['column']==node['column']]
                    edited_base=any(d['directly_edited'] for d in definitions)
                    edited_candidate=any(d['side']=='candidate' and d['qualname']==node['qualname'] and d['directly_edited'] for d in output['definitions'])
                    directly_edited=edited_base or edited_candidate
                    nonsemantic=any(d.get('qualname')==node['qualname'] and d['reason']=='owned_ast_structure_unchanged' for d in output['diagnostics'])
                    kept=any(r['status']=='resolved' and target in r['targets'] for r in task_records)
                    expected_existing=directly_edited and not nonsemantic and not errors
                    old_audit.append(dict(instance_id=iid,path=path,legacy_name=name,old_target=target,old_qualname=node['qualname'],
                        directly_edited=directly_edited,directly_edited_base=edited_base,directly_edited_candidate=edited_candidate,owned_ast_unchanged=nonsemantic,retained=kept,
                        expected_genuine_existing=expected_existing,regression=expected_existing and not kept,
                        file_error=bool(errors),explanation='retained exact base identity' if kept else disposition))
        counts=Counter(r['status'] for r in task_records)
        task_rows.append(dict(instance_id=iid,repo=task['repo'],graph_status=manifest[iid]['graph_status'],
            records=len(task_records),**{k:counts[k] for k in ['resolved','ambiguous','unresolved','new_definition']},
            file_errors=sum(r['record_kind']=='file_analysis_error' for r in task_records),
            source_patch_sha256=hashlib.sha256(patch).hexdigest()))
        dump(cache/(iid+'.json'),dict(records=task_records,files=file_outputs))
        print(iid,dict(counts),flush=True)
        del nodes,node_index;gc.collect()
    csv_write(HERE/'mapping_results.csv',results)
    csv_write(HERE/'new_definitions.csv',[r for r in results if r['status']=='new_definition'])
    csv_write(HERE/'uncertain_mappings.csv',[r for r in results if r['status'] in {'ambiguous','unresolved'}],list(results[0]))
    csv_write(HERE/'file_diagnostics.csv',file_diagnostics)
    csv_write(HERE/'legacy_record_comparison.csv',ledger)
    csv_write(HERE/'old_resolved_target_audit.csv',old_audit)
    csv_write(HERE/'task_mapping_summary.csv',task_rows)
    counts=Counter(r['status'] for r in results)
    old_failures=[r for r in ledger if r['legacy_status']!='resolved']
    summary=dict(tasks=len(tasks),legacy_counts=dict(Counter(r['status'] for r in old)),corrected_counts=dict(counts),
        records=len(results),named_definition_records=sum(r['record_kind']=='definition' for r in results),
        file_error_records=sum(r['record_kind']=='file_analysis_error' for r in results),
        false_failure_records_removed=sum(r['disposition'].startswith('excluded_') for r in old_failures),
        legacy_failure_dispositions=dict(Counter(r['disposition'] for r in old_failures)),
        legacy_resolved_target_audit=dict(Counter('retained' if r['retained'] else 'excluded_or_reclassified' for r in old_audit)),
        genuine_existing_resolved_targets_regressed=sum(r['regression'] for r in old_audit),
        old_resolved_targets_in_failed_files=sum(r['file_error'] for r in old_audit),
        genuine_ambiguous_records=counts['ambiguous'],graph_rebuild=False)
    dump(HERE/'mapping_summary.json',summary)
    print(json.dumps(summary,sort_keys=True),flush=True)


def selection_comparison():
    tasks,manifest,original,old=inputs()
    patch_records={t['instance_id']:t for t in read_csv(CG/'amendment2_72ad21b/task_resolution.csv')}
    frozen_elig={r['instance_id']:r for r in json.loads((CG/'phase2/eligibility.json').read_text())['tasks']}
    historical=set(json.loads((CG/'phase2/eligibility.json').read_text())['historical_19'])
    stored=stored_selections((ROOT/'reports/failure_analysis/extracted.json').read_text())
    frozen_counts={(r['instance_id'],r['edge_variant'],int(r['depth']),r['strategy'],r['budget']):int(r['after_count'])
                   for r in read_csv(EXP/'selection_summary.csv')}
    corrected=read_csv(HERE/'mapping_results.csv');all_rows=[];changes=[];paths=[];eligibility_rows=[]
    for task in tasks:
        iid,repo=task['instance_id'],task['repo'];directory=original/'reports/callgraph_selection'/manifest[iid]['directory']
        nodes={n['id']:n for n in records(directory/'nodes.jsonl.gz')}
        edge_file=EXP/'task_artifacts'/iid/'edges.jsonl.gz'
        expected=json.loads((EXP/'task_artifacts'/iid/'summary.json').read_text())['artifact_sha256']['edges.jsonl.gz']
        assert digest(edge_file)==expected
        edges=list(records(edge_file));diagnostic=json.loads((directory/'diagnostics.json').read_text())
        original_seeds={json.loads(r['targets'])[0] for r in old if r['instance_id']==iid and r['status']=='resolved'}
        rows=[r for r in corrected if r['instance_id']==iid]
        corrected_seeds={json.loads(r['targets'])[0] for r in rows if r['status']=='resolved'}
        counts=Counter(r['status'] for r in rows)
        new_task=dict(patch_confirmed='True',names_resolved=str(counts['resolved']),names_ambiguous=str(counts['ambiguous']),
            names_total=str(len(rows)),newly_added_names=str(counts['new_definition']))
        new_stratum,new_reason=eligibility({},new_task,diagnostic,True)
        eligibility_rows.append(dict(instance_id=iid,repo=repo,before_stratum=frozen_elig[iid]['stratum'],after_stratum=new_stratum,
            before_reason=frozen_elig[iid]['eligibility_reason'],after_reason=new_reason,
            before_seed_count=len(original_seeds),after_seed_count=len(corrected_seeds),
            added_seeds=sorted(corrected_seeds-original_seeds),removed_seeds=sorted(original_seeds-corrected_seeds)))
        base_ids,_=base_test_ids(task,Registry());identities=Identities(nodes,base_ids,repo)
        selected=stored[iid]['selected_tests'] if iid in historical else None
        before,_,b_traversals=selections(nodes,edges,identities,original_seeds,selected)
        after,_,a_traversals=selections(nodes,edges,identities,corrected_seeds,selected)
        for variant in VARIANTS:
            for depth in DEPTHS:
                for strategy in (('B','C') if selected is not None else ('B',)):
                    br=before.get((variant,depth,strategy));ar=after.get((variant,depth,strategy))
                    for budget in (*BUDGETS,'ALL'):
                        bp=None if br is None else br if budget=='ALL' else br[:budget]
                        ap=None if ar is None else ar if budget=='ALL' else ar[:budget]
                        bi=None if bp is None else [r['test_id'] for r in bp]
                        ai=None if ap is None else [r['test_id'] for r in ap]
                        frozen=frozen_counts.get((iid,variant,depth,strategy,str(budget)))
                        assert frozen==(None if bi is None else len(bi)),(iid,variant,depth,strategy,budget)
                        paired=bi is not None and ai is not None
                        added=sorted(set(ai)-set(bi)) if paired else None
                        removed=sorted(set(bi)-set(ai)) if paired else None
                        row=dict(instance_id=iid,repo=repo,strategy=strategy,edge_variant=variant,depth=depth,budget=budget,
                            before_stratum=frozen_elig[iid]['stratum'],after_stratum=new_stratum,
                            before_available=bi is not None,after_available=ai is not None,
                            before_count=None if bi is None else len(bi),after_count=None if ai is None else len(ai),
                            availability_changed=(bi is None)!=(ai is None),
                            membership_changed=paired and set(bi)!=set(ai),order_changed=paired and bi!=ai,
                            added_count=None if added is None else len(added),removed_count=None if removed is None else len(removed))
                        all_rows.append(row)
                        if row['availability_changed'] or row['order_changed']:
                            changes.append(dict(**row,added=added,removed=removed))
                        if paired and strategy=='B' and budget=='ALL':
                            for raw in (added or [])[:25]:
                                node=identities.lookup(raw)['node_id']
                                witnesses=[(s,route) for s in sorted(corrected_seeds-original_seeds)
                                           if (route:=a_traversals[variant].from_seed(s).get(node)) is not None and 1<=len(route.edges)<=depth]
                                assert witnesses,(iid,raw)
                                seed,route=witnesses[0]
                                paths.append(dict(instance_id=iid,repo=repo,edge_variant=variant,depth=depth,test_id=raw,
                                                  newly_identified_existing_seed=seed,**a_traversals[variant].provenance(route)))
        print(iid,'selection inputs compared',len(original_seeds),len(corrected_seeds),flush=True)
        del nodes,edges,b_traversals,a_traversals;gc.collect()
    csv_write(HERE/'selection_summary.csv',all_rows)
    csv_write(HERE/'selection_changes.csv',changes,list(all_rows[0])+['added','removed'])
    csv_write(HERE/'new_test_paths.csv',paths,['instance_id','repo','edge_variant','depth','test_id','newly_identified_existing_seed',
        'path_nodes','path_calls','distance','uses_ambiguous_edge','ambiguous_hop_count','ambiguous_hop_positions'])
    csv_write(HERE/'eligibility_comparison.csv',eligibility_rows)
    summary=dict(tasks=83,configurations=len(all_rows),baseline_frozen_counts_reproduced=True,
        membership_changed_tasks=len({r['instance_id'] for r in all_rows if r['membership_changed']}),
        order_changed_tasks=len({r['instance_id'] for r in all_rows if r['order_changed']}),
        availability_changed_tasks=len({r['instance_id'] for r in all_rows if r['availability_changed']}),
        changed_configurations=len(changes),eligibility_changed_tasks=sum(r['before_stratum']!=r['after_stratum'] or r['before_reason']!=r['after_reason'] for r in eligibility_rows),
        new_test_paths=len(paths),graph_changed=False,selector_functions_changed=False)
    dump(HERE/'selection_comparison.json',summary);print(json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['map','select'],required=True)
    args=parser.parse_args()
    mapping() if args.stage=='map' else selection_comparison()
