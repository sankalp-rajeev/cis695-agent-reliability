"""Read frozen sources/artifacts and report facts; never build or change a graph.

Run: python3 reports/callgraph_selection/typeprop_experiment/regression_path_diagnosis/inspect_paths.py
Requires the pinned local archives and ignored graph artifacts used by earlier audits.
"""
from __future__ import annotations
import ast,csv,gzip,hashlib,json,subprocess,sys,tarfile
from collections import defaultdict,deque
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3];EXP=HERE.parent;CG=EXP.parent
ORIGINAL=Path('/home/rajee/projects/cis695-agent-reliability')
sys.path[:0]=[str(EXP),str(EXP/'changed_symbol_diagnosis')]
from evaluate import patch_inputs,original_state,digest
from inspect_cases import reconstruct,patch_section
from inputs import Registry,base_test_ids
from callgraph_selector import Identities,VARIANTS

def dump(name,value): (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def rows(p):
 with gzip.open(p,'rt') as f:return list(map(json.loads,f))
def table(p):return list(csv.DictReader(p.open()))
def shortest(nodes,edges,start,targets,ambiguous=False):
 """Read-only forward BFS without a depth cap, to distinguish missing edges from budget limits."""
 forward=defaultdict(set)
 for e in edges:
  if e['status']=='resolved' or (ambiguous and e['status']=='ambiguous'):
   forward[e['caller']].update(t for t in e['targets'] if t in nodes)
 paths={start:[start]};q=deque([start])
 while q:
  n=q.popleft()
  for nxt in sorted(forward[n]):
   if nxt not in paths:paths[nxt]=paths[n]+[nxt];q.append(nxt)
 return {t:paths.get(t) for t in sorted(targets)}

# Each range is a source-inspection request, not a proposed edge or a selector input.
RANGES={
'django__django-12209':{
 'tests/basic/tests.py':[(1,35),(137,140)],'tests/basic/models.py':[(1,8),(47,48)],
 'django/db/models/base.py':[(404,408),(663,677),(746,748),(750,751),(764,786),(829,870)],
 'django/db/models/__init__.py':[(1,40)]},
'django__django-14140':{
 'tests/queries/test_q.py':[(1,5),(38,52)],'django/db/models/__init__.py':[(1,52)],
 'django/db/models/query_utils.py':[(12,14),(28,40),(67,71),(83,97)],
 'django/utils/tree.py':[(11,41)],'django/db/models/deletion.py':[(47,55)],'django/utils/deconstruct.py':[(6,18),(48,55)]},
'django__django-14631':{
 'tests/forms_tests/tests/test_forms.py':[(1,38),(2115,2123)],
 'django/forms/__init__.py':[(1,25)],'django/forms/forms.py':[(1,90),(151,175),(372,406),(437,459),(490,507)],
 'django/forms/boundfield.py':[(1,30),(212,220)]},
'pytest-dev__pytest-5809':{
 'testing/test_pastebin.py':[(90,133)],'src/_pytest/pastebin.py':[(65,91)],
 'src/_pytest/config/__init__.py':[(127,168),(331,333),(540,588)],
 'src/_pytest/fixtures.py':[(460,479)],'testing/conftest.py':[(1,55)]},
'sphinx-doc__sphinx-10435':{
 'tests/test_build_latex.py':[(1605,1629)],'tests/conftest.py':[(1,20)],
 'sphinx/testing/fixtures.py':[(55,99),(104,141),(161,185)],
 'sphinx/testing/util.py':[(89,100),(123,129),(149,166)],
 'sphinx/application.py':[(248,255),(304,329)],
 'sphinx/builders/__init__.py':[(115,121),(280,299),(348,354),(511,518)],
 'sphinx/builders/latex/__init__.py':[(105,115),(252,261),(290,302),(505,510)],
 'sphinx/writers/latex.py':[(66,87),(1695,1718)],
 'sphinx/registry.py':[(156,160),(327,353)],'sphinx/util/docutils.py':[(496,529)],
 'tests/roots/test-reST-code-role/index.rst':[(1,9)],
 'tests/roots/test-reST-code-role/conf.py':[(1,80)]}}
SCOPE_QUERIES={
'django__django-12209':{'django/db/models/base.py':['Model','Model.save','Model.save_base','Model._save_table'], 'tests/basic/models.py':['PrimaryKeyWithDefault']},
'django__django-14140':{'django/db/models/query_utils.py':['Q','Q.__invert__','Q.deconstruct'], 'django/utils/tree.py':['Node']},
'django__django-14631':{'django/forms/forms.py':['BaseForm','Form','BaseForm.errors','BaseForm.full_clean','BaseForm._clean_fields','BaseForm.changed_data']},
'pytest-dev__pytest-5809':{'testing/test_pastebin.py':['TestPaste.pastebin'], 'src/_pytest/pastebin.py':['create_new_paste']},
'sphinx-doc__sphinx-10435':{'sphinx/application.py':['Sphinx.build'], 'sphinx/builders/__init__.py':['Builder.build_update','Builder.build','Builder.write'], 'sphinx/builders/latex/__init__.py':['LaTeXBuilder.write'], 'sphinx/writers/latex.py':['LaTeXWriter.translate','LaTeXTranslator.visit_literal'], 'sphinx/util/docutils.py':['SphinxTranslator.dispatch_visit']}}

def main():
 baseline=json.loads((HERE/'preservation_before.json').read_text())
 subprocess.run(['git','merge-base','--is-ancestor',baseline['head'],'HEAD'],cwd=ROOT,check=True)
 assert original_state(ORIGINAL)==baseline['original']
 known=json.loads((ROOT/'reports/failure_analysis/group4_failing_tests.json').read_text());known.pop('_notice')
 tasks={t['instance_id']:t for t in json.loads((CG/'inputs.json').read_text())['tasks']}
 manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text());patches=patch_inputs()
 mapping=table(EXP/'qualified_mapping/mapping_results.csv');witness=table(EXP/'regression_validation/witness_selection.csv')
 histories={t['instance_id']:t for t in json.loads((ROOT/'reports/failure_analysis/group4_regression_rerun.json').read_text())['tasks']}
 extracted={t['instance_id']:t for t in json.loads((ROOT/'reports/failure_analysis/extracted.json').read_text())['tasks']}
 input_hashes={};source_evidence=[];facts=[];case_number=0
 for iid,tests in known.items():
  task=tasks[iid];assert histories[iid]['failing']==tests and histories[iid]['baseline_from_cache']
  assert histories[iid]['source_run']==task['source_run']==extracted[iid]['source_run']
  assert hashlib.sha256(extracted[iid]['agent_patch'].encode()).hexdigest()==hashlib.sha256(patches[iid]).hexdigest()
  assert digest(task['archive_path'])==task['archive_sha256'];input_hashes[task['archive_path']]=task['archive_sha256']
  directory=ORIGINAL/'reports/callgraph_selection'/manifest[iid]['directory']
  for name,h in manifest[iid]['artifact_sha256'].items():
   assert digest(directory/name)==h;input_hashes[str(directory/name)]=h
  enhanced=EXP/'task_artifacts'/iid;summary=json.loads((enhanced/'summary.json').read_text())
  assert digest(enhanced/'edges.jsonl.gz')==summary['artifact_sha256']['edges.jsonl.gz']
  for p in [enhanced/'edges.jsonl.gz',enhanced/'summary.json']:input_hashes[str(p)]=digest(p)
  nodes={n['id']:n for n in rows(directory/'nodes.jsonl.gz')};edges=rows(enhanced/'edges.jsonl.gz')
  maps=[r for r in mapping if r['instance_id']==iid];seeds={t for r in maps if r['status']=='resolved' for t in json.loads(r['targets'])}
  base_ids,_=base_test_ids(task,Registry());ident=Identities(nodes,base_ids,task['repo'])
  scopes=rows(directory/'scopes.jsonl.gz')
  with tarfile.open(task['archive_path']) as archive:
   assert archive.pax_headers.get('comment')==task['base_commit']
   names=set(archive.getnames())
   for path,ranges in RANGES[iid].items():
    member='testbed/'+path
    if member not in names:
     source_evidence.append(dict(instance_id=iid,path=path,available=False));continue
    payload=archive.extractfile(member).read();text=payload.decode();lines=text.splitlines()
    snippets=[dict(start=a,end=min(b,len(lines)),text='\n'.join(f'{i+1}: {lines[i]}' for i in range(a-1,min(b,len(lines))))) for a,b in ranges]
    item=dict(instance_id=iid,path=path,available=True,base_file_sha256=hashlib.sha256(payload).hexdigest(),base_commit=task['base_commit'],snippets=snippets)
    if any(r['path']==path for r in maps):
     section=patch_section(patches[iid],path);candidate,hunks=reconstruct(text,section)
     item.update(patch_section=section,candidate_file_sha256=hashlib.sha256(candidate.encode()).hexdigest(),candidate_view='validated hunk reconstruction for inspection only; never indexed into a graph')
     tree=ast.parse(candidate);item['candidate_changed_definitions']=[]
     for r in maps:
      if r['path']!=path:continue
      defs=json.loads(r['candidate_definitions'])
      for d in defs:
       start=d['start'];end=d['end'];item['candidate_changed_definitions'].append(dict(qualname=r['qualname'],start=start,end=end,text='\n'.join(f'{i+1}: {candidate.splitlines()[i]}' for i in range(start-1,end))))
    source_evidence.append(item)
   external=dict(docutils_source_members=[n for n in names if n.startswith('testbed/docutils/') or '/site-packages/docutils/' in n],pluggy_source_members=[n for n in names if n.startswith('testbed/pluggy/') or '/site-packages/pluggy/' in n])
  relevant={n['id'] for n in nodes.values() if n['qualname'] in SCOPE_QUERIES[iid].get(n['path'],[])}
  for tid in tests:
   case_number+=1;path,*qual=tid.split('::');qual='.'.join(qual)
   test_nodes=[n for n in nodes.values() if n['path']==path and n['qualname']==qual];assert len(test_nodes)==1
   test=test_nodes[0];assert ident.lookup(tid)['node_id']==test['id']
   ids=relevant|{test['id']};site_edges=[dict(ordinal=i,**e) for i,e in enumerate(edges) if e['caller'] in ids]
   selections=[r for r in witness if r['instance_id']==iid and r['test_id']==tid and r['evidence_tier']=='reported_existing_regression' and r['strategy']=='B' and r['budget']=='ALL']
   assert len(selections)==6 and all(r['after_selected']=='False' for r in selections)
   fact=dict(case_id=f'R{case_number:02}',instance_id=iid,test_id=tid,base_commit=task['base_commit'],archive_sha256=task['archive_sha256'],patch_sha256=hashlib.sha256(patches[iid]).hexdigest(),source_run=task['source_run'],test_mapping=ident.lookup(tid),test_node=test,changed_definitions=maps,graph_status=manifest[iid]['graph_status'],graph_failures=json.loads((directory/'diagnostics.json').read_text())['parse_and_resource_failures'],relevant_nodes=[nodes[n] for n in sorted(ids)],edge_records=site_edges,seed_incoming={s:[dict(ordinal=i,**e) for i,e in enumerate(edges) if s in e['targets']] for s in sorted(seeds)},paths_without_depth_limit={v:shortest(nodes,edges,test['id'],seeds,v==VARIANTS[1]) for v in VARIANTS},frozen_B_ALL_memberships=selections,external_source_inventory=external,historical_regression_evidence=histories[iid])
   if iid=='django__django-14140':
    fact['global_method_mutation_guard']=dict(attribute='deconstruct',source_sites=[dict(path='django/db/models/deletion.py',line=54,receiver='set_on_delete',indexed=any(n['path']=='django/db/models/deletion.py' for n in nodes.values())),dict(path='django/utils/deconstruct.py',line=49,receiver='klass',indexed=any(n['path']=='django/utils/deconstruct.py' for n in nodes.values()))],effect='TypeIndexer records attribute stores globally; resolve_calls requires method name absent from mutated_attributes. These sites block deconstruct on Q as well. No receiver-sensitive disambiguation exists.')
    fact['reexport_scope_evidence']=[s for s in scopes if s['kind']=='module' and s['path'] in ['django/db/models/__init__.py','tests/queries/test_q.py']]
   facts.append(fact)
 for p in [ROOT/'reports/failure_analysis/group4_failing_tests.json',ROOT/'reports/failure_analysis/group4_regression_rerun.json',ROOT/'reports/failure_analysis/extracted.json',CG/'inputs.json',CG/'amendment2_72ad21b/graph_manifest.json',CG/'amendment2_72ad21b/patch_verification.json',EXP/'qualified_mapping/mapping_results.csv',EXP/'qualified_mapping/old_resolved_target_audit.csv',EXP/'regression_validation/witness_selection.csv',CG/'static_graph.py',EXP/'typeprop_graph.py',CG/'phase2/callgraph_selector.py',EXP/'evaluate.py',EXP/'changed_symbol_diagnosis/inspect_cases.py']:
  input_hashes[str(p)]=digest(p)
 dump('source_evidence.json',source_evidence);dump('graph_evidence.json',facts)
 dump('input_manifest.json',dict(frozen_commit=baseline['head'],sha256=input_hashes,scope='Six historical named regression identities across five tasks; no benchmark execution, graph rebuild, edge injection, ranking or selector run. BFS only queries stored edges, including a separate unbounded diagnostic query.'))
 preserved={p:h for p,h in baseline['tracked'].items() if digest(ROOT/p)==h}
 assert len(preserved)==len(baseline['tracked'])
 assert original_state(ORIGINAL)==baseline['original']
 dump('validation.json',dict(cases=len(facts),tasks=len(known),all_test_identities_uniquely_mapped=True,all_corrected_B_ALL_depths_miss=True,all_input_hashes_verified=True,prior_tracked_files_unchanged=len(preserved),original_worktree_unchanged=True,source_archives_commit_verified=True,candidate_hunks_validated=True,benchmark_code_executed=False,graphs_modified=False,policies_modified=False))
 print(json.dumps(dict(cases=len(facts),tasks=len(known),prior_tracked_files_unchanged=len(preserved))))
if __name__=='__main__':main()
