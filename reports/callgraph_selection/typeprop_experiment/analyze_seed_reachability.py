"""Explain changed-seed fan-in gains even when the selected test union is unchanged."""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
CG=HERE.parent
ROOT=CG.parents[1]
sys.path[:0]=[str(HERE),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from evaluate import csv_write, records, Registry, base_test_ids, Identities, Traversal


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    original=Path(protocol['original_worktree'])/'reports/callgraph_selection'
    manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    tasks={t['instance_id']:t for t in json.loads((CG/'inputs.json').read_text())['tasks']}
    eligibility={r['instance_id']:r for r in json.loads((CG/'phase2/eligibility.json').read_text())['tasks']}
    grouped=defaultdict(list)
    with (HERE/'specificity_changes.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            grouped[row['instance_id']].append((json.loads(row['before']),json.loads(row['after'])))
    with (CG/'amendment2_72ad21b/changed_symbol_resolution.csv').open(newline='') as stream:
        seeds_by_task=defaultdict(set)
        for row in csv.DictReader(stream):
            if row['status']=='resolved':
                seeds_by_task[row['instance_id']].add(json.loads(row['targets'])[0])
    summaries,paths=[] ,[]
    for iid,changes in grouped.items():
        directory=original/manifest[iid]['directory']
        nodes={n['id']:n for n in records(directory/'nodes.jsonl.gz')}
        before_edges=list(records(directory/'edges.jsonl.gz'))
        after_edges=list(records(HERE/'task_artifacts'/iid/'edges.jsonl.gz'))
        base_ids,_=base_test_ids(tasks[iid],Registry())
        identities=Identities(nodes,base_ids,tasks[iid]['repo'])
        cache={}
        for before,after in changes:
            variant=before['edge_variant'];seed=before['seed']
            if variant not in cache:
                b=Traversal(nodes,before_edges,variant);a=Traversal(nodes,after_edges,variant)
                old_union,_=b.test_paths(seeds_by_task[iid],identities.test_definitions)
                cache[variant]=(b,a,old_union)
            b,a,old_union=cache[variant]
            b_hits={n:r for n,r in b.from_seed(seed).items() if n in identities.test_definitions and 1<=len(r.edges)<=3}
            a_hits={n:r for n,r in a.from_seed(seed).items() if n in identities.test_definitions and 1<=len(r.edges)<=3}
            assert len(b_hits)==before['fan_in'] and len(a_hits)==after['fan_in']
            added=sorted(set(a_hits)-set(b_hits));removed=sorted(set(b_hits)-set(a_hits))
            summaries.append(dict(instance_id=iid,repo=tasks[iid]['repo'],stratum=eligibility[iid]['stratum'],
                edge_variant=variant,seed=seed,before_test_fan_in=len(b_hits),after_test_fan_in=len(a_hits),
                tests_gained=len(added),tests_lost=len(removed),
                gained_tests_already_in_old_union=sum(n in old_union for n in added),
                gained_tests_new_to_union=sum(n not in old_union for n in added)))
            for n in added:
                route=a_hits[n]
                paths.append(dict(instance_id=iid,repo=tasks[iid]['repo'],stratum=eligibility[iid]['stratum'],
                    edge_variant=variant,seed=seed,test_node=n,test_id=identities.emittable.get(n),
                    already_in_old_union=n in old_union,**a.provenance(route),
                    new_typeprop_ordinals=[i for i in route.edges if after_edges[i]['provenance']!='existing_static_resolution']))
    csv_write(HERE/'changed_seed_reachability.csv',summaries)
    csv_write(HERE/'changed_seed_reachability_paths.csv',paths)
    print(json.dumps(dict(changed_seed_variant_rows=len(summaries),new_test_seed_path_rows=len(paths)),sort_keys=True))


if __name__=='__main__':
    main()
