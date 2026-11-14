"""Read-only diagnosis of the frozen 40 failed changed-name records.

Locates edits in ASTs for evidence only. Never builds/modifies a graph, produces
selector seeds, ranks tests, or executes benchmark code. Candidate file text is
reconstructed in memory solely to distinguish new definitions from diff context.
"""
from __future__ import annotations
import ast
import csv
import gc
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
CG=EXP.parent
ROOT=CG.parents[1]
sys.path[:0]=[str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from evaluate import patch_inputs, records, digest, csv_write, original_state, verify_manifest
from callgraph_selector import Identities, Traversal, VARIANTS
from inputs import Registry, base_test_ids
from reliability.verifier.patch import parse_patch

HUNK=re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: ?(.*))?$')
NAME=re.compile(r'^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)')


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def patch_section(payload,path):
    for block in payload.decode().split('diff --git ')[1:]:
        if block.splitlines()[0].endswith(' b/'+path):
            return 'diff --git '+block
    raise ValueError(('Patch section missing',path))


def reconstruct(base,section):
    """Validate unified diff old-side bytes and reconstruct an AST inspection view."""
    old=base.splitlines(keepends=True);plain=[s.rstrip('\r\n') for s in old]
    output=[];position=0;hunks=[];current=None
    for line in section.splitlines():
        match=HUNK.match(line)
        if match:
            if current:
                assert current['old_seen']==current['old_count'] and current['new_seen']==current['new_count'],current
            start,old_count,new_start,new_count,heading=match.groups()
            start=int(start);old_count=int(old_count or 1);new_start=int(new_start);new_count=int(new_count or 1)
            index=start-1 if old_count else start
            assert index>=position
            output.extend(plain[position:index]);position=index
            current=dict(old_start=start,old_count=old_count,new_start=new_start,new_count=new_count,
                         heading=heading or '',old_seen=0,new_seen=0,removed=[],added=[],context=[])
            hunks.append(current)
        elif current and line.startswith((' ','-','+')):
            sign,text=line[0],line[1:]
            if sign in (' ','-'):
                assert position<len(plain) and plain[position]==text,('Source/hunk mismatch',position+1,text)
                old_line=position+1;position+=1;current['old_seen']+=1
            else:
                old_line=None
            if sign in (' ','+'):
                new_line=len(output)+1;output.append(text);current['new_seen']+=1
            else:
                new_line=None
            item=dict(text=text,old_line=old_line,new_line=new_line)
            current[{' ':'context','-':'removed','+':'added'}[sign]].append(item)
        elif current and line.startswith('\\ No newline'):
            pass
        elif current and line:
            raise ValueError(('Unexpected diff content',line))
    if current:
        assert current['old_seen']==current['old_count'] and current['new_seen']==current['new_count'],current
    output.extend(plain[position:])
    return '\n'.join(output)+'\n',hunks


class Definitions(ast.NodeVisitor):
    def __init__(self):
        self.stack=[];self.rows=[];self.docs=[]
    def definition(self,node):
        qual='.'.join([*self.stack,node.name])
        row=dict(name=node.name,qualname=qual,line=node.lineno,end_line=node.end_lineno,
                 kind=type(node).__name__,column=node.col_offset,
                 decorators=[ast.unparse(d) for d in node.decorator_list],
                 bases=[ast.unparse(b) for b in node.bases] if isinstance(node,ast.ClassDef) else [])
        self.rows.append(row)
        if (node.body and isinstance(node.body[0],ast.Expr)
                and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str)):
            self.docs.append(dict(owner=qual,line=node.body[0].lineno,end_line=node.body[0].end_lineno))
        self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
    visit_ClassDef=definition
    visit_FunctionDef=definition
    visit_AsyncFunctionDef=definition


def owner(definitions,line):
    hits=[d for d in definitions if d['line']<=line<=d['end_line']]
    return max(hits,key=lambda d:(d['qualname'].count('.'),d['line'])) if hits else None


def context(text,line,radius=3):
    lines=text.splitlines()
    return '\n'.join(f'{i+1}: {lines[i]}' for i in range(max(0,line-radius-1),min(len(lines),line+radius)))


def inspect():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip().startswith('df3bd9b')
    existing={str(p.relative_to(ROOT)):digest(p) for p in EXP.rglob('*')
              if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts
              and 'task_artifacts' not in p.parts and p.suffix!='.log'}
    # Frozen graph artifacts, code, summaries and original worktree are verified,
    # not overwritten or rebuilt.
    protocol=json.loads((EXP/'protocol.json').read_text());original=Path(protocol['original_worktree'])
    original_before=original_state(original)
    manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    verified=verify_manifest(original,manifest)
    acquisition={t['instance_id']:t for t in json.loads((CG/'inputs.json').read_text())['tasks']}
    all_symbols=list(csv.DictReader((CG/'amendment2_72ad21b/changed_symbol_resolution.csv').open()))
    failures=[r for r in all_symbols if r['status'] in {'ambiguous','unresolved'}]
    assert len(failures)==40 and Counter(r['status'] for r in failures)=={'ambiguous':21,'unresolved':19}
    patches=patch_inputs()
    frozen_status={r['instance_id']:r for r in json.loads((CG/'phase2/eligibility.json').read_text())['tasks']}
    grouped=defaultdict(list)
    for index,row in enumerate(failures,1):grouped[row['instance_id']].append((index,row))
    cases=[];all_evidence=[];all_paths=[]
    for iid,items in grouped.items():
        task=acquisition[iid];record=manifest[iid]
        directory=original/'reports/callgraph_selection'/record['directory']
        assert digest(task['archive_path'])==task['archive_sha256']
        graph_nodes={n['id']:n for n in records(directory/'nodes.jsonl.gz')}
        graph_edges=list(records(EXP/'task_artifacts'/iid/'edges.jsonl.gz'))
        expected_edges=json.loads((EXP/'task_artifacts'/iid/'summary.json').read_text())['artifact_sha256']['edges.jsonl.gz']
        assert digest(EXP/'task_artifacts'/iid/'edges.jsonl.gz')==expected_edges
        base_ids,_=base_test_ids(task,Registry());identities=Identities(graph_nodes,base_ids,task['repo'])
        traversals={v:Traversal(graph_nodes,graph_edges,v) for v in VARIANTS}
        current_seeds={json.loads(r['targets'])[0] for r in all_symbols if r['instance_id']==iid and r['status']=='resolved'}
        current_unions={v:traversals[v].test_paths(current_seeds,identities.test_definitions)[0] for v in VARIANTS}
        with tarfile.open(task['archive_path'],'r:') as archive:
            assert archive.pax_headers.get('comment')==task['base_commit']
            for index,row in items:
                path=row.get('base_path') or row['path'];name=row['name']
                member=archive.getmember('testbed/'+path);assert member.isfile()
                payload=archive.extractfile(member).read();base=payload.decode('utf-8')
                section=patch_section(patches[iid],row['path']);candidate,hunks=reconstruct(base,section)
                bd=Definitions();bd.visit(ast.parse(payload,filename=path))
                cd=Definitions();cd.visit(ast.parse(candidate,filename=path+' [inspection-only candidate view]'))
                old_edits=[x for h in hunks for x in h['removed'] if x['text'].strip()]
                new_edits=[x for h in hunks for x in h['added'] if x['text'].strip()]
                old_owners=[owner(bd.rows,x['old_line']) for x in old_edits]
                new_owners=[owner(cd.rows,x['new_line']) for x in new_edits]
                old_touched=sorted({d['qualname'] for d in old_owners if d})
                new_touched=sorted({d['qualname'] for d in new_owners if d})
                base_defs=[d for d in bd.rows if d['name']==name]
                candidate_defs=[d for d in cd.rows if d['name']==name]
                matching_old=[d for d in base_defs if d['qualname'] in old_touched]
                matching_new=[d for d in candidate_defs if d['qualname'] in new_touched]
                before_quals={d['qualname'] for d in bd.rows}
                new_matching_defs=[d for d in matching_new if d['qualname'] not in before_quals]
                regex_hits=[]
                for h in hunks:
                    match=NAME.match(h['heading'])
                    if match and match.group(1)==name:regex_hits.append(dict(side='hunk_header',text=h['heading'],old_line=None,new_line=None))
                    for side in ('removed','added','context'):
                        for x in h[side]:
                            match=NAME.match(x['text'])
                            if match and match.group(1)==name:
                                doc=next((d for d in (cd.docs if x['new_line'] else bd.docs)
                                          if d['line']<=(x['new_line'] or x['old_line'])<=d['end_line']),None)
                                regex_hits.append(dict(side=side,**x,inside_docstring=doc))
                assert regex_hits,(iid,name)
                changed_quals=sorted({d['qualname'] for d in matching_old}|{d['qualname'] for d in matching_new if d['qualname'] in before_quals})
                target_nodes=[n for n in graph_nodes.values() if n['path']==path and n['qualname'] in changed_quals and n['kind']!='module']
                if not candidate_defs and not base_defs and any(x.get('inside_docstring') for x in regex_hits):
                    category='docstring_text_misidentified_as_definition';fixability='A'
                elif not matching_old and not matching_new:
                    category='unchanged_context_or_stale_hunk_header_name';fixability='A'
                elif new_matching_defs:
                    category='candidate_only_definition_absent_from_base';fixability='B'
                else:
                    category='qualified_scope_lost_by_simple_name_mapper';fixability='A'
                relevant_quals=changed_quals or new_touched or old_touched
                anchor_quals=set()
                for d in new_matching_defs:
                    parts=d['qualname'].split('.')
                    for length in range(len(parts)-1,0,-1):
                        q='.'.join(parts[:length])
                        if q in before_quals:anchor_quals.add(q);break
                anchors=[n for n in graph_nodes.values() if n['path']==path and n['qualname'] in anchor_quals]
                target_reach=[]
                for node in target_nodes+anchors:
                    results=dict(node_id=node['id'],qualname=node['qualname'],role='changed_base_definition' if node in target_nodes else 'existing_enclosing_anchor',already_seed=node['id'] in current_seeds,
                                 decorated=node['decorated'],bases=node.get('bases',[]))
                    for v,t in traversals.items():
                        hits={n:p for n,p in t.from_seed(node['id']).items() if n in identities.test_definitions and 1<=len(p.edges)<=3}
                        emitted={n:p for n,p in hits.items() if n in identities.emittable}
                        results[v]=dict(test_definitions=len(hits),emittable_tests=len(emitted),
                            tests_outside_current_seed_union=sum(n not in current_unions[v] for n in emitted))
                        for test,route in sorted(emitted.items())[:25]:
                            all_paths.append(dict(case_id=f'C{index:02}',instance_id=iid,node_id=node['id'],role=results['role'],variant=v,
                                test_id=identities.emittable[test],outside_current_seed_union=test not in current_unions[v],**t.provenance(route)))
                    target_reach.append(results)
                # All graph candidates really exist and match the unqualified key.
                recorded=json.loads(row['targets'])
                assert {n['id'] for n in graph_nodes.values() if n['path']==path and n['qualname'].rsplit('.',1)[-1]==name and n['kind']!='module'}==set(recorded)
                evidence=dict(case_id=f'C{index:02}',instance_id=iid,path=path,name=name,base_commit=task['base_commit'],
                    archive_sha256=task['archive_sha256'],base_file_sha256=hashlib.sha256(payload).hexdigest(),
                    patch_sha256=hashlib.sha256(patches[iid]).hexdigest(),patch_section=section,
                    base_definitions=base_defs,candidate_definitions=candidate_defs,
                    old_changed_owners=old_touched,new_changed_owners=new_touched,
                    matching_changed_base_qualnames=changed_quals,new_matching_definitions=new_matching_defs,
                    extractor_occurrences=regex_hits,graph_candidates=[graph_nodes[t] for t in recorded],
                    relevant_base_contexts=[dict(qualname=d['qualname'],context=context(base,d['line'])) for d in base_defs],
                    relevant_candidate_contexts=[dict(qualname=d['qualname'],context=context(candidate,d['line'])) for d in candidate_defs],
                    reachability=target_reach,graph_status=record['graph_status'],stratum=frozen_status[iid]['stratum'],
                    graph_failures=json.loads((directory/'diagnostics.json').read_text())['parse_and_resource_failures'])
                all_evidence.append(evidence)
                cases.append(dict(case_id=f'C{index:02}',task_id=iid,repository=row['repo'],file=path,
                    changed_symbol=name,current_status=row['status'],resolver_reason=row['reason'],
                    root_cause_category=category,fixability=fixability,confidence='high',
                    matched_base_definitions=[d['qualname'] for d in base_defs],
                    actual_changed_base_definitions=changed_quals,
                    added_candidate_definitions=[d['qualname'] for d in new_matching_defs],
                    actual_edited_definition_owners=sorted(set(old_touched+new_touched)),
                    graph_status=record['graph_status'],source_file_status='parsed',
                    directly_caused_by_graph_incompleteness=False,reachability=target_reach))
        print(iid,'diagnosed',len(items),flush=True)
        del graph_nodes,graph_edges,traversals
        gc.collect()
    cases.sort(key=lambda r:r['case_id']);all_evidence.sort(key=lambda r:r['case_id'])
    dump(HERE/'inspection.json',cases);dump(HERE/'source_evidence.json',all_evidence)
    csv_write(HERE/'existing_paths.csv',all_paths)
    assert existing=={str(p.relative_to(ROOT)):digest(p) for p in EXP.rglob('*')
              if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts
              and 'task_artifacts' not in p.parts and p.suffix!='.log'}
    assert original_before==original_state(original)
    dump(HERE/'inspection_validation.json',dict(cases=len(cases),status_counts=dict(Counter(r['current_status'] for r in cases)),
        provisional_root_causes=dict(Counter(r['root_cause_category'] for r in cases)),
        fixability_counts=dict(Counter(r['fixability'] for r in cases)),
        existing_experiment_files_unchanged=True,original_worktree_unchanged=True,
        verified_frozen_graph_files=verified,source_files_verified_parsed=True,
        candidate_files_reconstructed_with_exact_context_checks=True,benchmark_execution=False,
        graph_rebuild=False,selector_execution=False,ranking_change=False,policy_change=False,
        inspector_sha256=digest(Path(__file__))))


if __name__=='__main__':
    inspect()
