#!/usr/bin/env python3
"""Compute draft-v1 §3 B1/B2 from frozen stored captures, without execution."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_write(path, rows):
    with path.open('x', newline='') as stream:
        writer=csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def outcome(value):
    # Keep expected/unexpected outcomes distinct even though the historical
    # native status and Phase 2 compatibility replay normalized them.
    if value['flavor'] in ('XFAIL', 'expected failure'):
        return 'XFAIL'
    if value['flavor'] in ('XPASS', 'unexpected success'):
        return 'XPASS'
    return value['status'].upper()


def run(args):
    assert not args.output.exists()
    hashes={}
    def read(path):
        data=path.read_bytes();hashes[str(path)]=sha(data);return data
    def rows(path):
        read(path)
        with path.open(newline='')as stream:return list(csv.DictReader(stream))
    native_expected=json.loads(read(args.report/'input_manifest.json'))['input_sha256']
    frozen=json.loads(read(args.frozen/'tasks.json'))
    spec=importlib.util.spec_from_file_location('phase2_parser',args.parser)
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    read(args.parser)
    gaps=[r for r in rows(args.report/'selected_gap_attribution.csv')if r['scope']=='initial']
    keys={(r['instance_id'],r['tree'],r['test_id'])for r in gaps}
    assert len(gaps)==len(keys)==39876
    exclusions=Counter(r['cause']for r in gaps if r['cause']in ('environment_guard_abort','empty_selection','base_patched_id_set_difference'))
    b1=len(gaps)-sum(exclusions.values())
    reference={r['instance_id']:r for r in rows(args.report/'parser_replay.csv')}
    guards={(r['instance_id'],r['tree']):r['replay_runner_gap_reasons'] for r in rows(args.report/'call_replay_summary.csv')if r['scope']=='initial'}
    task_rows, tree_rows, special_rows=[],[],[]
    raw_initial_calls=0
    for meta in frozen:
        task=meta['instance_id'];runner=meta['runner']['name']
        path=args.results/'tasks'/task/'v2/result.json'
        data=read(path);assert sha(data)==native_expected[str(path)]
        native=json.loads(data);selected=native.get('selected_tests')or[]
        frozen_selected=json.loads(read(args.frozen/meta['selections']['v2']))['tests']
        assert selected==frozen_selected
        trees={}
        for call in native.get('calls',[])[:2]:
            raw_initial_calls+=1
            tree='patched'if call['patched']else'base'
            capture=Path(call['run']['evidence_files']['runner.raw'])
            raw=read(capture);assert sha(raw)==call['run']['evidence_sha256']['runner.raw']
            parsed=parser.parse_capture(raw.decode('utf-8','replace'),runner)
            mapper=parser.mapping_for(selected,runner)
            mapped=defaultdict(dict);counts=Counter()
            for rid,value in parsed.items():
                state=outcome(value)
                ids=mapper(rid)
                if len(ids)==1 and value['kind']=='case':
                    mapped[ids[0]][rid]=state;counts[state]+=1
                    if state in ('XFAIL','XPASS'):
                        special_rows.append({'instance_id':task,'tree':tree,'selected_test_id':ids[0],
                            'concrete_id':rid,'outcome':state,'evidence_path':str(capture),'line':value['line']})
            tree_rows.append({'instance_id':task,'tree':tree,**{s:counts[s]for s in ('PASSED','FAILED','ERROR','SKIPPED','XFAIL','XPASS')},
                'runner_gap_reasons':guards[task,tree],'evidence_path':str(capture)})
            trees[tree]={'mapped':mapped,'raw_ids':set(parsed)}
        compatible=str(reference[task]['parser_only_complete_skip_compatible'])=='True'
        strict=bool(selected and set(trees)=={'base','patched'})
        if strict:
            base,patched=trees['base'],trees['patched']
            strict &= base['raw_ids']==patched['raw_ids']
            strict &= not guards[task,'base'] and not guards[task,'patched']
            for test in selected:
                b,p=base['mapped'].get(test,{}),patched['mapped'].get(test,{})
                strict &= bool(b) and b.keys()==p.keys()
                strict &= all(v not in ('SKIPPED','ERROR','NOT_RUN','TIMEOUT')for v in list(b.values())+list(p.values()))
            assert not strict or compatible,task
        verdict='RETAINED_NATIVE_FAIL'if native['signal']=='FAIL'else'PROJECTED_PASS'if strict else'NO_PROJECTED_BINARY_VERDICT'
        task_rows.append({'instance_id':task,'native_verdict':native['signal'],
            'parser_replay_skip_compatible_complete':compatible,'strict_XFAIL_separate_complete':bool(strict),
            'old_strict_normalized_complete':reference[task]['parser_only_complete_skip_strict'],
            'B2_projection':verdict})
    counts=Counter(r['B2_projection']for r in task_rows)
    b2=counts['PROJECTED_PASS']+counts['RETAINED_NATIVE_FAIL']
    assert len(task_rows)==83 and counts['RETAINED_NATIVE_FAIL']==6
    assert b1==37614 and b2==21
    args.output.mkdir(parents=True)
    summary={'scope':'STORED-DATA BASELINES AND PROJECTIONS ONLY','B1_addressable_gap_slots':b1,
        'initial_selected_tree_ID_gap_slots':len(gaps),'excluded_GIS_guard_slots':exclusions['environment_guard_abort'],
        'excluded_empty_selection_slots':exclusions['empty_selection'],
        'excluded_ID_set_difference_only_slots':exclusions['base_patched_id_set_difference'],
        'B2_strict_XFAIL_separate_projected_yes_no':b2,'B2_projected_PASS':counts['PROJECTED_PASS'],
        'B2_retained_native_FAIL':counts['RETAINED_NATIVE_FAIL'],'cohort_tasks':83,
        'raw_initial_calls':raw_initial_calls,'XFAIL_tree_cases':sum(r['outcome']=='XFAIL'for r in special_rows),
        'XPASS_tree_cases':sum(r['outcome']=='XPASS'for r in special_rows),
        'additional_strict_complete_vs_normalized':[r['instance_id']for r in task_rows if r['strict_XFAIL_separate_complete']and r['old_strict_normalized_complete']=='False'],
        'native_verdicts_changed':False,'Docker_calls':0}
    csv_write(args.output/'B1_B2.csv',[
        {'baseline':'B1','value':b1,'denominator':39876,'unit':'addressable_initial_selected_tree_ID_gap_slots'},
        {'baseline':'B2','value':b2,'denominator':83,'unit':'projected_yes_no_tasks_XFAIL_XPASS_separate'}])
    csv_write(args.output/'B2_tasks.csv',task_rows)
    csv_write(args.output/'B2_tree_outcomes.csv',tree_rows)
    csv_write(args.output/'B2_XFAIL_XPASS_evidence.csv',special_rows)
    (args.output/'baseline_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    (args.output/'baseline_manifest.json').write_text(json.dumps({'script_sha256':sha(Path(__file__).read_bytes()),
        'input_sha256':hashes,'labels_read':False,'source_execution':'none; Phase 2 parser only',
        'B1_unit_rule':'empty-selection and raw-ID-set-difference task/event counts contribute zero selected slots',
        'B2_policy':'SKIPPED blocks PASS; XFAIL and XPASS are distinct evidence; native FAIL retained; no new confirmation inferred'},indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--frozen',type=Path,required=True)
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--parser',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    run(ap.parse_args())
