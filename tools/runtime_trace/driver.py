#!/usr/bin/env python3
"""Phase 6a only: fixed outcome-informed witnesses, never a selector.

prepare builds AST hunk mappings; graphs recreates the pinned SCG graph;
run executes exactly one requested test per fresh container; summarize reads
stored data only. No image builds, pulls, installs, tags or executor changes.
"""
import argparse
import ast
import collections
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'runs/phase6a_runtime_trace'
OUT = ROOT/'reports/next_phases/phase6a_runtime_trace'
CG = 'reports/callgraph_selection/'
STATIC_FILES = [CG+'static_graph.py',CG+'amended_graph.py',CG+'build_graphs.py',
 CG+'phase2/inputs.py',CG+'phase2/callgraph_selector.py',
 CG+'typeprop_experiment/typeprop_graph.py',CG+'typeprop_experiment/qualified_mapping/mapper.py',
 'reports/v2_diagnostic/oracle_posthoc.py','reports/v2_diagnostic/diagnostic.py',
 CG+'amendment2_72ad21b/graph_manifest.json']


def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p): return json.loads(Path(p).read_text())
def dump(p,x):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def git_bytes(rev,path):return subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT)


def functions(source,path):
 tree=ast.parse(source);result=[]
 def visit(body,prefix=''):
  for n in body:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    q=prefix+n.name
    if not isinstance(n,ast.ClassDef):
     result.append({'path':path,'qualname':q,'name':n.name,'start':n.lineno,
      'decorator_start':min([n.lineno]+[d.lineno for d in n.decorator_list]),
      'end':n.end_lineno,'decorators':[ast.unparse(d) for d in n.decorator_list]})
    visit(n.body,q+'.')
   else:
    for field in ['body','orelse','finalbody']:
     sub=getattr(n,field,None)
     if isinstance(sub,list):visit(sub,prefix)
    for handler in getattr(n,'handlers',[]):visit(handler.body,prefix)
 visit(tree.body)
 return result


def hunks(patch):
 records=[];path=None;hunk=None;old=new=0
 for line in patch.splitlines():
  if line.startswith('+++ '):
   path=line[4:];path=path[2:] if path.startswith('b/') else path
  elif line.startswith('@@ '):
   m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',line)
   assert m,line
   old,new=int(m[1]),int(m[3]);hunk={'path':path,'header':line,'old_start':old,'new_start':new,'old_changed':[],'new_changed':[]};records.append(hunk)
  elif hunk is not None:
   if line.startswith('+') and not line.startswith('+++'):hunk['new_changed'].append(new);new+=1
   elif line.startswith('-') and not line.startswith('---'):hunk['old_changed'].append(old);old+=1
   elif line.startswith(' '):old+=1;new+=1
   elif line.startswith('diff --git '):hunk=None
 return records


def prepare():
 inputs=load(RAW/'inputs.json');specs=inputs['specs'];prepared={}
 for iid,spec in specs.items():
  assert file_sha(spec['archive_path'])==spec['archive_sha256']
  # Candidate source path comes from the immutable audit, not the label value.
  audit=load_bytes(git_bytes(inputs['execution_revision'],'reports/next_phases/phase4_posthoc/label_audit/analysis.json'))
  patchpath=Path(next(r['frozen_patch_path'] for r in audit['all_tasks'] if r['task']==iid))
  patch=patchpath.read_bytes();assert sha(patch)==spec['patch_sha256']
  folder=RAW/'sources'/iid;base=folder/'base';patched=folder/'patched'
  assert not folder.exists(),'Refuse to overwrite source preparation'
  base.mkdir(parents=True)
  with tarfile.open(spec['archive_path']) as t:
   assert t.pax_headers.get('comment')==spec['base_commit']
   for m in t.getmembers():
    name=Path(m.name)
    assert name.parts[0]=='testbed' and '..' not in name.parts
    relative=Path(*name.parts[1:])
    if m.isfile():
     target=base/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(t.extractfile(m).read());target.chmod(m.mode)
  shutil.copytree(base,patched)
  p=subprocess.run(['git','apply','--unsafe-paths','--directory='+str(patched),'-'],input=patch,capture_output=True,cwd='/tmp')
  assert p.returncode==0,p.stderr.decode()
  hs=hunks(patch.decode());all_defs={};errors=[]
  for tree,root in [('base',base),('patched',patched)]:
   defs={}
   for path in sorted({h['path'] for h in hs if h['path'].endswith('.py')}):
    source=root/path
    if source.exists():
     try:defs[path]=functions(source.read_text(),path)
     except (SyntaxError,UnicodeError) as exc:errors.append({'tree':tree,'path':path,'reason':repr(exc)})
   all_defs[tree]=defs
  changed_keys=set()
  for h in hs:
   h['mapped_functions']={}
   for tree,side in [('base','old_changed'),('patched','new_changed')]:
    defs=all_defs[tree].get(h['path'],[]);hit=set()
    for line in h[side]:
     candidates=[d for d in defs if d['decorator_start']<=line<=d['end']]
     if candidates:
      innermost=min(candidates,key=lambda d:d['end']-d['decorator_start'])
      key=(h['path'],innermost['qualname']);hit.add(key);changed_keys.add(key)
    h['mapped_functions'][tree]=[list(k) for k in sorted(hit)]
  changed=[]
  for path,qual in sorted(changed_keys):
   item={'id':path+'::'+qual,'path':path,'qualname':qual}
   for tree in ['base','patched']:
    matches=[d for d in all_defs[tree].get(path,[]) if d['qualname']==qual]
    assert len(matches)<=1,('ambiguous changed definition',iid,path,qual)
    item[tree]=matches[0] if matches else None
   item['patch_only']=item['base'] is None;item['removed']=item['patched'] is None
   changed.append(item)
  tests=[]
  for original in inputs['tests']:
   if original['task']!=iid:continue
   identity=original['test_id'];path,*parts=identity.split('::');qual='.'.join(re.sub(r'\[.*','',s) for s in parts)
   row=dict(original,functions={})
   for tree,root in [('base',base),('patched',patched)]:
    found=[d for d in functions((root/path).read_text(),path) if d['qualname']==qual]
    assert len(found)==1,(iid,identity,found)
    row['functions'][tree]=found[0]
   tests.append(row)
  prepared[iid]={'spec':spec,'patch_path':str(patchpath),'changed_functions':changed,'hunks':hs,'AST_errors':errors,'tests':tests}
  print('PREPARED',iid,len(changed),'functions',len(tests),'tests',flush=True)
 snapshot=RAW/'static_snapshot'
 hashes={}
 for p in STATIC_FILES:
  b=git_bytes(inputs['static_revision'],p);target=snapshot/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);hashes[p]=sha(b)
 dump(RAW/'prepared.json',{'tasks':prepared,'static_code_sha256':hashes,'inputs_sha256':file_sha(RAW/'inputs.json')})

def load_bytes(b):return json.loads(b)


def graphs():
 prepared=load(RAW/'prepared.json');snapshot=RAW/'static_snapshot';cg=snapshot/CG
 sys.path[:0]=[str(cg/'typeprop_experiment/qualified_mapping'),str(cg/'typeprop_experiment'),str(cg/'phase2'),str(cg),str(snapshot/'reports/v2_diagnostic')]
 import typeprop_graph
 import build_graphs as builders
 manifest=load(cg/'amendment2_72ad21b/graph_manifest.json')
 for iid,row in prepared['tasks'].items():
  target=RAW/'graphs'/(iid+'.json.gz');assert not target.exists()
  cls=typeprop_graph.TypeAmendedGraph if manifest[iid]['directory'].startswith('amendment2_') else typeprop_graph.TypeGraph
  start=time.monotonic();spec=row['spec'];static_root=RAW/'static_sources'/iid
  static_root.mkdir(parents=True,exist_ok=True)
  _,skipped=builders.extract({'archive_path':spec['archive_path'],'archive_sha256':spec['archive_sha256'],'base_commit':spec['base_commit']},static_root)
  g=cls().build(static_root/'testbed')
  for item in skipped:
   if item['path'].endswith('.py'):
    g.files[item['path']]='omitted_archive_link';g.failures.append(item);g.counts['omitted_files']+=1
  if g.status=='complete' and g.failures:g.status='partial'
  data={'task':iid,'status':g.status,'nodes':g.nodes,'edges':g.edges,'files':g.files,'failures':g.failures,'counts':dict(g.counts),'static_revision':load(RAW/'inputs.json')['static_revision'],'build_seconds':time.monotonic()-start}
  target.parent.mkdir(parents=True,exist_ok=True)
  with gzip.open(target,'wt') as f:json.dump(data,f,sort_keys=True)
  print('GRAPH',iid,g.status,len(g.nodes),len(g.edges),flush=True)
  del g
  import gc;gc.collect()

SOURCE_RECEIPT = r'''
import os,json,hashlib,sys
with open('/tmp/phase6a_expected.json') as f: expected=json.load(f)
wrong=[];total=0
for p,h in expected.items():
 try:
  with open(b'/testbed/'+p.encode('utf-8'),'rb') as f:b=f.read()
  total+=len(b)
  if hashlib.sha256(b).hexdigest()!=h:wrong.append(p)
 except (IOError,OSError):wrong.append(p)
result={'checked_files':len(expected),'total_bytes':total,'mismatches':wrong,'python':sys.version,'os_cpu_count':os.cpu_count(),'PYTHONHASHSEED':os.environ.get('PYTHONHASHSEED'),'PYTHONWARNINGS':os.environ.get('PYTHONWARNINGS')}
print(json.dumps(result,sort_keys=True))
sys.exit(1 if wrong else 0)
'''


def put_file(container,path,data):
 payload=io.BytesIO()
 with tarfile.open(fileobj=payload,mode='w') as t:
  info=tarfile.TarInfo(Path(path).name);info.size=len(data);info.mode=0o644;t.addfile(info,io.BytesIO(data))
 container.put_archive(str(Path(path).parent),payload.getvalue())


def parse_outcome(text,identity,django=False):
 if django:
  # A single native label is passed. Never infer PASS from exit status.
  ran=re.search(r'Ran (\d+) tests? in ',text)
  if ran and int(ran[1])==1:
   if re.search(r'^OK \(skipped=1\)',text,re.M):return 'SKIPPED'
   if re.search(r'^OK\s*$',text,re.M):return 'PASSED'
   failed=re.search(r'^FAILED \(([^\n]+)\)',text,re.M)
   if failed:return 'ERROR' if 'errors=' in failed[1] else 'FAILED'
  return 'NO_RECORDED_RESULT'
 normalized=text.replace('::()::','::')
 status=[]
 for line in normalized.splitlines():
  if identity not in line:continue
  for value in ['FAILED','ERROR','PASSED','SKIPPED','XFAIL','XPASS']:
   if re.search(r'\b'+value+r'\b',line):status.append(value);break
 if status:return status[-1]
 return 'NO_RECORDED_RESULT'


def execute_with_timeout(container,command,timeout):
 import threading
 api=container.client.api;exec_id=api.exec_create(container.id,command,workdir='/testbed')['Id'];data=[];errors=[]
 def consume():
  try:
   for b in api.exec_start(exec_id,stream=True):data.append(b)
  except BaseException as exc:errors.append(repr(exc))
 thread=threading.Thread(target=consume,daemon=True);start=time.monotonic();thread.start();thread.join(timeout)
 timed_out=thread.is_alive()
 if timed_out:
  container.kill();thread.join(10)
 return {'output':b''.join(data),'timed_out':timed_out,'duration_s':time.monotonic()-start,
  'returncode':None if timed_out else api.exec_inspect(exec_id).get('ExitCode'),'stream_errors':errors}


def run_tests():
 import docker
 import shlex
 prepared=load(RAW/'prepared.json');inputs=load(RAW/'inputs.json');client=docker.from_env(timeout=1800)
 records=load(RAW/'runtime_runs.json') if (RAW/'runtime_runs.json').exists() else []
 for index,test in enumerate(inputs['tests'],1):
  iid=test['task'];task=prepared['tasks'][iid];spec=task['spec']
  for tree in ['base','patched']:
   for traced in [True,False]:
    key='%02d-%s-%s'%(index,tree,'traced' if traced else 'untraced')
    existing=next((r for r in records if r['key']==key),None)
    if existing:
     for name,h in existing['artifact_sha256'].items():assert file_sha(RAW/name)==h
     assert existing.get('tracer_sha256')==file_sha(ROOT/'tools/runtime_trace/sitecustomize.py'),'Tracer changed; preserve old attempt before rerunning'
     print('CACHED',key,flush=True);continue
    folder=RAW/'executions'/key;assert not folder.exists(),('Refuse to overwrite incomplete invocation',folder)
    folder.mkdir(parents=True);(folder/'traces').mkdir();(folder/'traces').chmod(0o777)
    test_meta=next(t for t in task['tests'] if t['test_id']==test['test_id'])['functions'][tree]
    changed=[dict(c[tree],id=c['id']) for c in task['changed_functions'] if c[tree] is not None]
    config={'source_root':'/testbed','test_id':test['test_id'],'tree':tree,'test_function':test_meta,'changed_functions':changed}
    dump(folder/'trace_config.json',config)
    expected={p.relative_to(RAW/'sources'/iid/tree).as_posix():file_sha(p) for p in (RAW/'sources'/iid/tree).rglob('*') if p.is_file()}
    image=spec['image_id'];client.images.get(image) # Never pulls or changes images.
    c=None;start=time.monotonic();record={'key':key,'task':iid,'test_id':test['test_id'],'tree':tree,'traced':traced,'image_id':image,'candidate_sha256':spec['patch_sha256'],'outcome':'NOT_RUN','reason':None}
    print('START',key,iid,test['test_id'],flush=True)
    try:
     c=client.containers.create(image=image,command='sleep infinity',detach=True,working_dir='/testbed',network_mode='none',cpu_shares=2048,
      volumes={str(ROOT/'tools/runtime_trace'):{'bind':'/runtime_trace','mode':'ro'},str(folder/'trace_config.json'):{'bind':'/runtime_trace_config.json','mode':'ro'},str(folder/'traces'):{'bind':'/runtime_trace_output','mode':'rw'},task['patch_path']:{'bind':'/runtime_candidate.diff','mode':'ro'}},labels={'experiment':'phase6a-runtime-trace','posthoc_only':'true'})
     c.start();c.reload();record['host_config']={k:c.attrs['HostConfig'].get(k) for k in ['NetworkMode','CpuShares','CpuQuota','CpuPeriod']}
     assert record['host_config']['NetworkMode']=='none' and record['host_config']['CpuShares']==2048
     reset=c.exec_run(['git','reset','--hard',spec['base_commit']],workdir='/testbed')
     assert reset.exit_code==0,reset.output.decode(errors='replace')
     # Overlay every frozen source entry while retaining compiled extensions
     # and installed dependencies from the immutable image. No installs.
     c.put_archive('/',Path(spec['archive_path']).read_bytes())
     if tree=='patched':
      applied=c.exec_run(['git','apply','/runtime_candidate.diff'],workdir='/testbed')
      (folder/'patch_application.txt').write_bytes(applied.output)
      assert applied.exit_code==0,applied.output.decode(errors='replace')
     put_file(c,'/tmp/phase6a_expected.json',json.dumps(expected,sort_keys=True).encode())
     receipt=c.exec_run(['/bin/bash','-lc','source /opt/miniconda3/bin/activate && conda activate testbed && python -c '+shlex.quote(SOURCE_RECEIPT)],workdir='/testbed')
     (folder/'source_receipt.json').write_bytes(receipt.output)
     assert receipt.exit_code==0,receipt.output.decode(errors='replace')[-2000:]
     record['source_receipt']=json.loads(receipt.output)
     if iid.startswith('django'):
      p,*parts=test['test_id'].split('::');label=p.removeprefix('tests/').removesuffix('.py').replace('/','.')+'.'+'.'.join(parts)
      argv=['python','tests/runtests.py','--verbosity=2']
      if spec.get('django_parallel_one'):argv+=['--parallel','1']
      argv+=[label]
     else:argv=['python','-m','pytest','-p','no:cacheprovider','-v','-rA','--',test['test_id']]
     env=['env','PYTHONPATH=/runtime_trace','PYTHONDONTWRITEBYTECODE=1','RUNTIME_TRACE_ENABLE='+('1' if traced else '0'),'RUNTIME_TRACE_CONFIG=/runtime_trace_config.json','RUNTIME_TRACE_OUTPUT=/runtime_trace_output']
     command=['/bin/bash','-lc','source /opt/miniconda3/bin/activate && conda activate testbed && cd /testbed && exec '+shlex.join(env+argv)]
     record['argv']=argv;record['tracer_sha256']=file_sha(ROOT/'tools/runtime_trace/sitecustomize.py')
     result=execute_with_timeout(c,command,600);(folder/'stdout.txt').write_bytes(result.pop('output'))
     record.update(result);text=(folder/'stdout.txt').read_text(errors='replace')
     record['outcome']='TIMEOUT' if record['timed_out'] else parse_outcome(text,test['test_id'],iid.startswith('django'))
     if record['outcome']=='NO_RECORDED_RESULT':record['reason']='native runner did not record the requested single-test result; see stdout'
     events=[]
     for p in sorted((folder/'traces').glob('*.jsonl')):
      events.extend(json.loads(l) for l in p.read_text().splitlines() if l)
     record['trace_installed_processes']=sum(e['event']=='installed' for e in events)
     record['trace_entry_records']=sum(e['event']=='entry' for e in events)
     record['trace_errors']=[e for e in events if e['event']=='trace_error']
     if traced and (not record['trace_installed_processes'] or record['trace_errors']):record['reason']='tracer not installed or reported recording errors'
    except Exception as exc:
     record['outcome']='INFRASTRUCTURE_ERROR';record['reason']=repr(exc)
     (folder/'failure.txt').write_text(repr(exc)+'\n')
    finally:
     if c is not None:c.remove(force=True)
    record['wall_s']=time.monotonic()-start
    record['artifact_sha256']={p.relative_to(RAW).as_posix():file_sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
    records.append(record);dump(RAW/'runtime_runs.json',records)
    print('DONE',key,record['outcome'],'trace_entries',record.get('trace_entry_records'),record.get('reason'),flush=True)
 print('COMPLETE',len(records),'single-test invocations',flush=True)


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('action',choices=['prepare','graphs','run','summarize'])
 args=parser.parse_args()
 if args.action=='prepare':prepare()
 elif args.action=='graphs':graphs()
 elif args.action=='run':run_tests()
 else:
  from summarize import main as summarize
  summarize()

if __name__=='__main__':main()
