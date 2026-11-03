"""Additional read-only edge/constructor evidence; no seed or graph changes."""
import ast
import json
import sys
import tarfile
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXP=HERE.parent;CG=EXP.parent;ROOT=CG.parents[1]
sys.path[:0]=[str(HERE),str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from inspect_cases import Definitions,context,owner,reconstruct,patch_section
from evaluate import records,patch_inputs,dump
from inputs import Registry,base_test_ids
from callgraph_selector import Traversal,Identities,VARIANTS


def main():
    cases=json.loads((HERE/'inspection.json').read_text())
    source={r['case_id']:r for r in json.loads((HERE/'source_evidence.json').read_text())}
    original=Path(json.loads((EXP/'protocol.json').read_text())['original_worktree'])/'reports/callgraph_selection'
    manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    tasks={t['instance_id']:t for t in json.loads((CG/'inputs.json').read_text())['tasks']}
    patches=patch_inputs();by_task=defaultdict(list)
    for r in cases:by_task[r['task_id']].append(r)
    output=[]
    for iid,rows in by_task.items():
        nodes={n['id']:n for n in records(original/manifest[iid]['directory']/'nodes.jsonl.gz')}
        edges=list(records(EXP/'task_artifacts'/iid/'edges.jsonl.gz'))
        traversals={v:Traversal(nodes,edges,v) for v in VARIANTS}
        ids,_=base_test_ids(tasks[iid],Registry());ident=Identities(nodes,ids,tasks[iid]['repo'])
        with tarfile.open(tasks[iid]['archive_path'],'r:') as archive:
            for row in rows:
                ev=source[row['case_id']];path=row['file'];base=archive.extractfile('testbed/'+path).read().decode()
                candidate,_=reconstruct(base,ev['patch_section']);tree=ast.parse(candidate);defs=Definitions();defs.visit(tree)
                named=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==row['changed_symbol']]
                syntax_calls=[];value_references=[]
                for n in ast.walk(tree):
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==row['changed_symbol']:
                        scope=owner(defs.rows,n.lineno)
                        syntax_calls.append(dict(line=n.lineno,owner=scope['qualname'] if scope else '<module>',context=context(candidate,n.lineno)))
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='setattr':
                        if any(isinstance(a,ast.Name) and a.id==row['changed_symbol'] for a in n.args):
                            value_references.append(dict(kind='setattr_callable_injection',line=n.lineno,context=context(candidate,n.lineno)))
                parent_nodes=[]
                for qual in row['actual_changed_base_definitions']:
                    parent=qual.rpartition('.')[0]
                    cls=next((n for n in nodes.values() if n['path']==path and n['qualname']==parent and n['kind']=='class'),None)
                    if cls:parent_nodes.append(cls)
                targets={n['id'] for n in nodes.values() if n['path']==path and n['qualname'] in row['actual_changed_base_definitions']}
                incoming=[e for e in edges if set(e['targets'])&targets]
                parents=[]
                for node in parent_nodes:
                    reach={}
                    for v,t in traversals.items():
                        hits={n:r for n,r in t.from_seed(node['id']).items() if n in ident.emittable and 1<=len(r.edges)<=3}
                        reach[v]=dict(emittable_test_count=len(hits),test_ids=[ident.emittable[n] for n in sorted(hits)[:5]])
                    calls=[e for e in edges if node['id'] in e['targets']]
                    parents.append(dict(class_node=node,incoming_class_calls=len(calls),
                        class_call_status_counts=dict(Counter(e['status'] for e in calls)),
                        representative_constructor_calls=sorted(calls,key=lambda e:(not e['path'].startswith('tests'),e['path'],e['line']))[:3],
                        class_reachability=reach))
                output.append(dict(case_id=row['case_id'],actual_base_target_incoming_edge_counts=dict(Counter(e['status'] for e in incoming)),
                    actual_base_target_incoming_reason_counts=dict(Counter(e['reason'] for e in incoming)),
                    representative_target_incoming_edges=incoming[:5],parent_class_evidence=parents,
                    candidate_same_name_call_syntax=syntax_calls,callable_injection_evidence=value_references))
    dump(HERE/'downstream_evidence.json',sorted(output,key=lambda r:r['case_id']))
    for r in output:
        if r['parent_class_evidence']:
            print(r['case_id'],r['actual_base_target_incoming_edge_counts'],[(p['class_node']['qualname'],p['class_node']['bases'],p['class_reachability']) for p in r['parent_class_evidence']])


if __name__=='__main__':main()
