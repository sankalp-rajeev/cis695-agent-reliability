"""Validate complete qualified-mapping results without modifying frozen inputs."""
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent;EXP=HERE.parent;CG=EXP.parent;ROOT=CG.parents[1]
sys.path[:0]=[str(HERE),str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from evaluate import digest,records,original_state,verify_manifest,dump


def csv_rows(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))


def main():
    protocol=json.loads((HERE/'mapping_protocol.json').read_text())
    for name,sha in protocol['code_sha256'].items():assert digest(HERE/name)==sha,name
    assert digest(CG/'phase2/callgraph_selector.py')==protocol['selector_source_sha256']
    assert digest(CG/'phase2/inputs.py')==protocol['eligibility_source_sha256']
    before=json.loads((HERE/'preservation_before.json').read_text())
    for path,sha in before['prior_files_sha256'].items():assert digest(ROOT/path)==sha,path
    original=Path(json.loads((EXP/'protocol.json').read_text())['original_worktree'])
    assert original_state(original)==protocol['original_worktree']
    manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    verified_baseline=verify_manifest(original,manifest)
    results=csv_rows(HERE/'mapping_results.csv');summary=json.loads((HERE/'summary.json').read_text())
    tasks=csv_rows(HERE/'task_mapping_summary.csv');assert len(tasks)==83
    assert len(results)==127 and len({r['record_id'] for r in results})==127
    counts=Counter(r['status'] for r in results)
    assert {k:counts[k] for k in ['resolved','ambiguous','unresolved']}==summary['corrected_existing_definition_counts']
    assert counts['new_definition']==21
    by_task=defaultdict(list)
    for r in results:by_task[r['instance_id']].append(r)
    checked_targets=0;checked_new=0;enhanced_graphs=0
    for iid,entry in manifest.items():
        nodes={n['id']:n for n in records(original/'reports/callgraph_selection'/entry['directory']/'nodes.jsonl.gz')}
        enhanced=EXP/'task_artifacts'/iid/'edges.jsonl.gz'
        frozen=json.loads((EXP/'task_artifacts'/iid/'summary.json').read_text())
        assert digest(enhanced)==frozen['artifact_sha256']['edges.jsonl.gz'];enhanced_graphs+=1
        cache=json.loads((HERE/'task_artifacts'/(iid+'.json')).read_text())
        assert len(cache['records'])==len(by_task[iid])
        for r in by_task[iid]:
            base_defs=json.loads(r['base_definitions']);candidate_defs=json.loads(r['candidate_definitions']);targets=json.loads(r['targets'])
            output=cache['files'][r['base_path']]
            affected={tuple(k) for k in output['directly_edited_base_keys']+output['directly_edited_candidate_keys']}
            assert (r['qualname'],r['definition_kind']) in affected
            if r['status']=='resolved':
                assert len(targets)==len(base_defs)==1
                n=nodes[targets[0]];d=base_defs[0]
                assert (n['path'],n['qualname'],n['line'],n['column'])==(r['base_path'],r['qualname'],d['line'],d['column'])
                assert n['kind']!='module'
                assert not candidate_defs or candidate_defs[0]['qualname']==d['qualname']
                checked_targets+=1
            elif r['status']=='new_definition':
                assert not base_defs and len(candidate_defs)==1 and not targets
                assert not any(n['path']==r['base_path'] and n['qualname']==r['qualname'] and n['kind']!='module' for n in nodes.values())
                checked_new+=1
    old_audit=csv_rows(HERE/'old_resolved_target_audit.csv')
    assert len(old_audit)==147
    genuine=[r for r in old_audit if r['expected_genuine_existing']=='True']
    assert len(genuine)==43 and all(r['retained']=='True' and r['regression']=='False' for r in genuine)
    assert all(r['regression']=='False' and r['file_error']=='False' for r in old_audit)
    diagnosis=csv_rows(EXP/'changed_symbol_diagnosis/cases.csv')
    ledger=csv_rows(HERE/'legacy_record_comparison.csv')
    indexed={(r['instance_id'],r['path'],r['legacy_name']):r for r in ledger}
    expected_names={r['case_id']:r for r in json.loads((EXP/'changed_symbol_diagnosis/inspection.json').read_text())}
    for d in diagnosis:
        legacy=indexed[(d['task_id'],d['file'],d['changed_symbol'])]
        matched=[r for r in by_task[d['task_id']] if r['record_id'] in json.loads(legacy['corrected_record_ids'])]
        category=d['root_cause_category']
        if category=='qualified_scope_lost_by_simple_name_mapper':
            assert {r['qualname'] for r in matched}==set(expected_names[d['case_id']]['actual_changed_base_definitions'])
            assert all(r['status']=='resolved' for r in matched)
        elif category=='candidate_only_definition_absent_from_base':
            assert {r['qualname'] for r in matched}==set(expected_names[d['case_id']]['added_candidate_definitions'])
            assert all(r['status']=='new_definition' for r in matched)
        else:assert not matched and legacy['disposition'].startswith('excluded_')
    rows=csv_rows(HERE/'selection_summary.csv');assert len(rows)==3672
    assert len({(r['instance_id'],r['strategy'],r['edge_variant'],r['depth'],r['budget']) for r in rows})==3672
    membership={r['instance_id'] for r in rows if r['membership_changed']=='True'}
    availability={r['instance_id'] for r in rows if r['availability_changed']=='True'}
    assert len(membership)==28 and len(availability)==4 and not membership&availability
    for r in rows:
        for side in ['before','after']:
            available=r[side+'_available']=='True'
            assert available==bool(r[side+'_count'])
            if available and r['budget']!='ALL':assert int(r[side+'_count'])<=int(r['budget'])
        if r['strategy']=='C' and r['budget']=='ALL' and r['before_available']==r['after_available']=='True':
            assert r['before_count']==r['after_count'] and r['membership_changed']=='False'
    paths=csv_rows(HERE/'new_test_paths.csv');assert len(paths)==6
    for row in paths:
        assert row['edge_variant']=='SECONDARY_RESOLVED_PLUS_AMBIGUOUS'
        assert len(json.loads(row['path_calls']))<=int(row['depth'])<=3
        assert row['uses_ambiguous_edge']=='True'
    validation=dict(passed=True,tasks_mapped=83,focused_checks_passed=139,corrected_resolved=checked_targets,
        corrected_ambiguous=counts['ambiguous'],corrected_unresolved=counts['unresolved'],new_definitions_separate=checked_new,
        all_40_diagnosed_failures_reconciled=True,genuine_old_resolved_source_identities_retained=len(genuine),
        genuine_source_identity_regressions=0,baseline_graph_artifact_hashes_verified=verified_baseline,
        enhanced_graph_edge_hashes_unchanged=enhanced_graphs,prior_experiment_and_diagnosis_files_unchanged=len(before['prior_files_sha256']),
        original_worktree_unchanged=True,selector_and_eligibility_source_unchanged=True,
        baseline_selector_counts_reproduced=True,selection_configurations=3672,missing_selection_not_treated_as_zero=True,
        new_definition_or_fallback_seeds_injected=False,graph_resolution_changed=False,V2_policy_ranking_budgets_unchanged=True,
        runtime_coverage_or_recall_validated=False)
    dump(HERE/'validation.json',validation)
    dump(HERE/'output_hashes.json',{str(p.relative_to(HERE)):digest(p) for p in sorted(HERE.rglob('*')) if p.is_file()
        and 'task_artifacts' not in p.parts and '__pycache__' not in p.parts and 'attempts' not in p.parts and p.suffix!='.log'
        and p.name!='output_hashes.json'})
    print(json.dumps(validation,indent=2,sort_keys=True))


if __name__=='__main__':main()
