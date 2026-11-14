"""Independent frozen-evidence checks; no graph/selector mutations or benchmark execution."""
import ast,csv,gzip,hashlib,json,subprocess,sys,tarfile
from collections import defaultdict,deque
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];EXP=HERE.parent
sys.path.insert(0,str(EXP))
from evaluate import digest,original_state

def j(name):return json.loads((HERE/name).read_text())
def readrows(path):
 with gzip.open(path,'rt') as f:return list(map(json.loads,f))
def main():
 checks=[]
 def check(name,condition):
  assert condition,name
  checks.append(name)
 manifest=j('input_manifest.json')
 for p,h in manifest['sha256'].items():check('input_hash:'+str(Path(p).name)+':'+p,digest(p)==h)
 baseline=j('preservation_before.json')
 check('original_worktree_unchanged',original_state(Path('/home/rajee/projects/cis695-agent-reliability'))==baseline['original'])
 check('all_619_prior_tracked_files_unchanged',len(baseline['tracked'])==619 and all(digest(ROOT/p)==h for p,h in baseline['tracked'].items()))
 facts=j('graph_evidence.json');source=j('source_evidence.json');cases=list(csv.DictReader((HERE/'cases.csv').open()))
 check('six_separate_case_rows',len(facts)==len(cases)==6 and {f['case_id'] for f in facts}=={r['case_id'] for r in cases})
 known=json.loads((ROOT/'reports/failure_analysis/group4_failing_tests.json').read_text());known.pop('_notice')
 check('exact_historical_identity_set',{(i,t) for i,ts in known.items() for t in ts}=={(r['instance_id'],r['test_id']) for r in facts})
 tasks={t['instance_id']:t for t in json.loads((ROOT/'reports/callgraph_selection/inputs.json').read_text())['tasks']}
 archives={};texts={};trees={}
 for iid in known:
  with tarfile.open(tasks[iid]['archive_path']) as a:
   check('archive_commit:'+iid,a.pax_headers.get('comment')==tasks[iid]['base_commit'])
   archives[iid]={m.name:m for m in a}
   for s in source:
    if s['instance_id']!=iid or not s['available']:continue
    payload=a.extractfile('testbed/'+s['path']).read();text=payload.decode();texts[(iid,s['path'])]=text
    check('source_blob:'+iid+':'+s['path'],hashlib.sha256(payload).hexdigest()==s['base_file_sha256'])
    lines=text.splitlines()
    for snip in s['snippets']:
     check('source_excerpt:'+iid+':'+s['path']+':'+str(snip['start']),snip['text']=='\n'.join(f'{i+1}: {lines[i]}' for i in range(snip['start']-1,snip['end'])))
 for f in facts:
  check('unique_test_mapping:'+f['case_id'],f['test_mapping']['node_id']==f['test_node']['id'] and f['test_mapping']['mapping_reason']=='unique_exact_base_definition')
  check('all_frozen_B_ALL_depths_miss:'+f['case_id'],len(f['frozen_B_ALL_memberships'])==6 and all(r['after_selected']=='False' for r in f['frozen_B_ALL_memberships']))
  graph_manifest=json.loads((ROOT/'reports/callgraph_selection/amendment2_72ad21b/graph_manifest.json').read_text())
  olddir=Path('/home/rajee/projects/cis695-agent-reliability/reports/callgraph_selection')/graph_manifest[f['instance_id']]['directory']
  ns={n['id']:n for n in readrows(olddir/'nodes.jsonl.gz')};es=readrows(EXP/'task_artifacts'/f['instance_id']/'edges.jsonl.gz')
  check('edge_records_are_exact_frozen_records:'+f['case_id'],all({k:v for k,v in e.items() if k!='ordinal'}==es[e['ordinal']] for e in f['edge_records']))
  for allow in (False,True):
   forward=defaultdict(set)
   for e in es:
    if e['status']=='resolved' or (allow and e['status']=='ambiguous'):forward[e['caller']].update(e['targets'])
   visited={f['test_node']['id']};q=deque(visited)
   while q:
    for nxt in forward[q.popleft()]:
     if nxt in ns and nxt not in visited:visited.add(nxt);q.append(nxt)
   check('uncapped_stored_graph_unreachable:'+f['case_id']+':'+str(allow),not set(f['seed_incoming'])&visited)
 def edge(case,path,line,expr):return [e for e in facts[case-1]['edge_records'] if e['path']==path and e['line']==line and e['expression']==expr]
 check('R01_constructor_receiver_unresolved',edge(1,'tests/basic/tests.py',140,'<Call>.save')[0]['targets']==[])
 check('R01_internal_calls_ambiguous',edge(1,'django/db/models/base.py',746,'self.save_base')[0]['status']=='ambiguous' and edge(1,'django/db/models/base.py',783,'self._save_table')[0]['status']=='ambiguous')
 check('R02_local_receiver_unresolved',edge(2,'tests/queries/test_q.py',40,'q.deconstruct')[0]['targets']==[])
 check('Q_mutation_sites_are_indexed',all(x['indexed'] for x in facts[1]['global_method_mutation_guard']['source_sites']))
 check('R02_constructor_import_is_ambiguous',edge(2,'tests/queries/test_q.py',39,'Q')[0]['status']=='ambiguous')
 for path,line in [('django/db/models/deletion.py',54),('django/utils/deconstruct.py',49)]:
  tree=ast.parse(texts[('django__django-14140',path)])
  check('Q_global_attribute_mutation_guard_site:'+path,any(isinstance(n,ast.Attribute) and isinstance(n.ctx,ast.Store) and n.attr=='deconstruct' and n.lineno==line for n in ast.walk(tree)))
 qtree=ast.parse(texts[('django__django-14140','django/db/models/query_utils.py')]);qcls=next(n for n in qtree.body if isinstance(n,ast.ClassDef) and n.name=='Q')
 check('Q_declared_hierarchy_and_plain_class',len(qcls.bases)==1 and ast.unparse(qcls.bases[0])=='tree.Node' and not qcls.decorator_list)
 check('R03_unary_receiver_is_distinct',isinstance(next(n for n in ast.walk(ast.parse(texts[('django__django-14140','tests/queries/test_q.py')])) if isinstance(n,ast.Assign) and n.lineno==46).value,ast.UnaryOp))
 check('R03_local_receiver_unresolved',edge(3,'tests/queries/test_q.py',47,'q.deconstruct')[0]['targets']==[])
 inv=next(n for n in qcls.body if isinstance(n,ast.FunctionDef) and n.name=='__invert__')
 check('R03_source_returns_constructor_result',ast.unparse(inv.body[0])=='obj = type(self)()' and ast.unparse(inv.body[-1])=='return obj')
 check('R04_property_access_has_no_invocation_record',not any(e['caller']==facts[3]['test_node']['id'] and 'errors' in e['expression'] for e in facts[3]['edge_records']))
 ft=ast.parse(texts[('django__django-14631','tests/forms_tests/tests/test_forms.py')])
 check('R04_property_load_exists',any(isinstance(n,ast.Attribute) and n.lineno==2122 and n.attr=='errors' and isinstance(n.ctx,ast.Load) for n in ast.walk(ft)))
 check('R04_internal_calls_ambiguous',edge(4,'django/forms/forms.py',174,'self.full_clean')[0]['status']=='ambiguous' and edge(4,'django/forms/forms.py',385,'self._clean_fields')[0]['status']=='ambiguous')
 check('R04_existing_changed_target_present',any(r['qualname']=='BaseForm._clean_fields' and r['status']=='resolved' for r in facts[3]['changed_definitions']))
 check('R05_fixture_module_call_unresolved',edge(5,'testing/test_pastebin.py',124,'pastebin.create_new_paste')[0]['targets']==[])
 pt=ast.parse(texts[('pytest-dev__pytest-5809','testing/test_pastebin.py')]);pc=next(n for n in pt.body if isinstance(n,ast.ClassDef) and n.name=='TestPaste');fixture=next(n for n in pc.body if isinstance(n,ast.FunctionDef) and n.name=='pastebin')
 check('R05_literal_plugin_return',ast.unparse(fixture.body[0])=="return request.config.pluginmanager.getplugin('pastebin')")
 check('R06_app_build_unresolved',edge(6,'tests/test_build_latex.py',1607,'app.build')[0]['targets']==[])
 wrong=edge(6,'sphinx/builders/__init__.py',351,'self.write')[0]
 check('R06_wrong_resolved_base_write',wrong['status']=='resolved' and wrong['targets']==['sphinx/builders/__init__.py::Builder.write::method@511:4'])
 check('R06_target_has_zero_incoming_edges',all(not v for v in facts[5]['seed_incoming'].values()))
 check('R06_external_docutils_not_in_archive',not facts[5]['external_source_inventory']['docutils_source_members'])
 check('partial_parse_failures_are_unrelated',facts[3]['graph_failures'][0]['path']=='tests/test_runner_apps/tagged/tests_syntax_error.py' and facts[4]['graph_failures'][0]['path']=='doc/en/example/py2py3/test_py2.py' and all(not f['graph_failures'] for f in [facts[0],facts[1],facts[2],facts[5]]))
 result=dict(passed=True,checks=len(checks),case_specific_checks=checks[-20:],original_worktree_unchanged=True,prior_tracked_files_unchanged=619,benchmark_tests_executed=False,fixes_implemented=False)
 (HERE/'independent_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 if '--seal' in sys.argv:
  assert not (HERE/'output_hashes.json').exists(),'Refuse to overwrite a seal'
  hashes={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='output_hashes.json'}
  (HERE/'output_hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
 else:
  hashes=j('output_hashes.json')
  assert set(hashes)=={p.name for p in HERE.iterdir() if p.is_file() and p.name!='output_hashes.json'}
  assert all(digest(HERE/name)==h for name,h in hashes.items()),'Diagnosis output seal mismatch'
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
