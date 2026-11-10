#!/usr/bin/env python3
"""Post-hoc analysis after the immutable Phase 4 seal; no test execution.

Data reads are restricted to the manifested attempt, its sealed results,
the hash-pinned original V2 run, and the candidate-bound correctness labels.
The named witness/cohort definitions below are fixed constants, not groups
chosen using the new outcomes. Helpers imported from the sealed computation
are code only; its Fix5 reconstruction/compute functions are never called.
"""
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SEAL = ROOT / 'reports/next_phases/phase4_rerun/attempt4_seal'
sys.path.insert(0, str(SEAL))
import compute_seal as sealed
import scipy
from scipy.stats import beta

RUN = sealed.RUN
SEALED_HEAD = 'e40d60afac6534bba03a20168ea681fca24228af'
SEAL_TAG_OBJECT = 'ba55b83560fa6c4cc1f2fe220c09387a648473b0'
SEALED_RESULTS_SHA = '94786d24848b9707eaeb73dd353affd108d95d50ddc773d0f23ed539341d7530'
LABELS = ROOT / 'reports/v2_scg_analysis/full83_postcollection_20261106T012810_258795Z/correctness_sidecar.json'
LABELS_SHA = 'cd61a6e726a32e159db87a5040be5ea49c5c67e147faac424bf9a756d4e0c990'
ORIGINAL = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/full_83_20261105T231219_643682Z/results')
POLICIES = sealed.POLICIES
VERDICTS = ('PASS','FAIL','REGRESSION_ERROR','INCOMPLETE','NOT_AVAILABLE')
GRADER_TESTS = [{'task': 'django__django-13297', 'test_id': 'tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning', 'family': 'tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning'}, {'task': 'matplotlib__matplotlib-25479', 'test_id': 'lib/matplotlib/tests/test_colors.py::test_register_cmap', 'family': 'lib/matplotlib/tests/test_colors.py::test_register_cmap'}, {'task': 'pylint-dev__pylint-6528', 'test_id': 'tests/lint/unittest_lint.py::test_custom_should_analyze_file', 'family': 'tests/lint/unittest_lint.py::test_custom_should_analyze_file'}, {'task': 'pylint-dev__pylint-6528', 'test_id': 'tests/lint/unittest_lint.py::test_multiprocessing[1]', 'family': 'tests/lint/unittest_lint.py::test_multiprocessing'}, {'task': 'pylint-dev__pylint-6528', 'test_id': 'tests/lint/unittest_lint.py::test_multiprocessing[2]', 'family': 'tests/lint/unittest_lint.py::test_multiprocessing'}, {'task': 'pylint-dev__pylint-6528', 'test_id': 'tests/test_self.py::TestRunTC::test_jobs_score', 'family': 'tests/test_self.py::TestRunTC::test_jobs_score'}, {'task': 'pylint-dev__pylint-7277', 'test_id': 'tests/test_self.py::TestRunTC::test_jobs_score', 'family': 'tests/test_self.py::TestRunTC::test_jobs_score'}]
KNOWN_WITNESSES = [{'task': 'django__django-12209', 'test_id': 'tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default', 'family': 'tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default'}, {'task': 'django__django-14140', 'test_id': 'tests/queries/test_q.py::QTests::test_deconstruct', 'family': 'tests/queries/test_q.py::QTests::test_deconstruct'}, {'task': 'django__django-14140', 'test_id': 'tests/queries/test_q.py::QTests::test_deconstruct_negated', 'family': 'tests/queries/test_q.py::QTests::test_deconstruct_negated'}, {'task': 'django__django-14631', 'test_id': 'tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled', 'family': 'tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled'}, {'task': 'pytest-dev__pytest-5809', 'test_id': 'testing/test_pastebin.py::TestPaste::test_create_new_paste', 'family': 'testing/test_pastebin.py::TestPaste::test_create_new_paste'}, {'task': 'sphinx-doc__sphinx-10435', 'test_id': 'tests/test_build_latex.py::test_latex_code_role', 'family': 'tests/test_build_latex.py::test_latex_code_role'}]
SKIP_DEPENDENT_TASKS = ['django__django-12965', 'django__django-16315', 'django__django-16667', 'matplotlib__matplotlib-23299', 'matplotlib__matplotlib-24026', 'matplotlib__matplotlib-24637', 'matplotlib__matplotlib-24970', 'pallets__flask-5014', 'pydata__xarray-4695', 'pydata__xarray-6599', 'pylint-dev__pylint-6528', 'pylint-dev__pylint-7277', 'sphinx-doc__sphinx-10466']
DEFINITION_PROVENANCE = {'reports/next_phases/phase1_known_failures/phase1_known_failures.csv': 'b1488d5838ede34b3a1570000d53b6af64389e1c48171121b4a2807ab228320a', 'reports/v2_discovery_cleanup/audit/known_witnesses_retained.json': 'df9f91ac987e3240a6a65985a0844eef189bf23ed07017971d0bef49bcaa3ff1', 'reports/next_phases/phase2_incomplete_causes/accepted_PASS_skip_policy.csv': 'c731574b32df56b09bd76b0bf18dfa1564f05dbf4c3b593a8c158c823498f231'}

ROW = {k:True for k in ('test_id','status','message','elapsed_s')}
EVENT = {k:True for k in ('event','batch','module','ids','observed_ids','missing_ids','offset',
    'split','load_failure','timed_out','returncode','retry','parent','active_id','test_started','per_test_output','argv')}
PASS_SCHEMA = {'results':{'*':ROW},'raw_results':{'*':ROW},'raw_id_map':True,
    'execution_results':{'*':ROW},'execution_id_map':True,'validation':True,
    'events':{'*':EVENT},'stage_health':True,'evidence_files':True,'evidence_sha256':True,
    'validation_summary':{'context':{'runner':True}},'confirmation':True,'timed_out':True,'budget_s':True}
REPORT_SCHEMA = {'signal':True,'outcomes':True,'confirmation_summary':True,
    'confirmations':{'*':PASS_SCHEMA}}
ORIGINAL_SCHEMA = {'signal':True,'outcomes':True,'selected_tests':True,
    'calls':{'@limit':2,'*':{'patched':True,'run':{'results':{'*':ROW},'raw_results':{'*':ROW},
        'evidence_files':True,'evidence_sha256':True,'events':{'*':EVENT},'timed_out':True}}}}
SEVERITY = {'skipped':0,'xfail':1,'passed':2,'xpass':3,'failed':4,'error':5,'crash':6,
            'not_run':7,'not_reached':8,'timeout':9,'collection_error':10,'invalid_id':11}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def preconditions():
    assert git('rev-parse','phase4-run-sealed^{}')==SEALED_HEAD
    assert git('rev-parse','refs/tags/phase4-run-sealed')==SEAL_TAG_OBJECT
    remote={ref:digest for digest,ref in (line.split() for line in git('ls-remote','origin',
        'refs/tags/phase4-run-sealed','refs/tags/phase4-run-sealed^{}').splitlines())}
    assert remote.get('refs/tags/phase4-run-sealed^{}')==SEALED_HEAD
    assert remote.get('refs/tags/phase4-run-sealed')==SEAL_TAG_OBJECT
    entries,info=sealed.verify_run()
    data=(SEAL/'results.json').read_bytes()
    assert sealed.sha(data)==SEALED_RESULTS_SHA
    # Importing the helper must not substitute changed code for sealed code.
    expected=subprocess.check_output(['git','show',SEALED_HEAD+':'+str(Path(sealed.__file__).relative_to(ROOT))],cwd=ROOT)
    assert expected==Path(sealed.__file__).read_bytes()
    return entries,info,json.loads(data)


def proportion(k,n):
    assert 0<=k<=n
    if not n:
        return {'count':k,'denominator':n,'fraction':None,'ci95':None,'defined':False}
    lower=0.0 if k==0 else float(beta.ppf(0.025,k,n-k+1))
    upper=1.0 if k==n else float(beta.ppf(0.975,k+1,n-k))
    return {'count':k,'denominator':n,'fraction':k/n,'ci95':[lower,upper],'defined':True}


def evaluate(verdicts,labels):
    matrix={verdict:{'correct':0,'incorrect':0} for verdict in VERDICTS}
    for iid,verdict in verdicts.items():
        assert verdict in matrix, (iid,verdict)
        matrix[verdict][labels[iid]]+=1
    assert sum(row['correct'] for row in matrix.values())==69
    assert sum(row['incorrect'] for row in matrix.values())==14
    metrics={}
    for name,positive in (('primary_FAIL_only',{'FAIL'}),('secondary_FAIL_plus_REGRESSION_ERROR',{'FAIL','REGRESSION_ERROR'})):
        decisions={'PASS'}|positive
        detected=[iid for iid,v in verdicts.items() if labels[iid]=='incorrect' and v in positive]
        false=[iid for iid,v in verdicts.items() if labels[iid]=='correct' and v in positive]
        missed=[iid for iid,v in verdicts.items() if labels[iid]=='incorrect' and v=='PASS']
        nwrong=sum(labels[iid]=='incorrect' and v in decisions for iid,v in verdicts.items())
        nright=sum(labels[iid]=='correct' and v in decisions for iid,v in verdicts.items())
        metrics[name]={'positive_verdicts':sorted(positive),'verdicted_denominator_states':sorted(decisions),
            'detection_all_incorrect':proportion(len(detected),14),
            'detection_verdicted_incorrect':proportion(len(detected),nwrong),
            'false_alarm_all_correct':proportion(len(false),69),
            'false_alarm_verdicted_correct':proportion(len(false),nright),
            'missed_all_incorrect':proportion(len(missed),14),
            'missed_verdicted_incorrect':proportion(len(missed),nwrong),
            'detected_incorrect_tasks':sorted(detected),'false_alarm_correct_tasks':sorted(false),
            'missed_incorrect_PASS_tasks':sorted(missed)}
    return {'verdict_by_label':matrix,'metrics':metrics}


def normalize(identity):
    return identity.replace('::()::','::').removesuffix('::()')


def module_key(module):
    return str(module or '').split('::')[0].removeprefix('tests/').removesuffix('.py').replace('/','.')


def signatures(text):
    found=[]
    for line in text.splitlines():
        line=line.strip()
        if re.search(r'\b(?:[A-Za-z_]\w*(?:Error|Exception|Warning)|KeyboardInterrupt|SystemExit):',line):
            clean=re.sub(r'0x[0-9a-fA-F]+','<address>',line)
            if clean not in found:found.append(clean[:600])
    if 'Aborting: A GIS database backend is required to run gis_tests.' in text:
        found.append('GIS database backend required')
    return found[-8:]


class Data:
    def __init__(self,entries,seal_result):
        self.entries=entries
        self.hashes={}
        self.original_hashes={p:d for p,d in seal_result['input_sha256'].items()
                              if Path(p).is_relative_to(ORIGINAL)}
        self.parser={'django_label':sealed.django_label}
        assert sealed.sha(sealed.FIX5_PARSER_SOURCE.encode())==sealed.FIX5_PARSER_SHA
        exec(compile(sealed.FIX5_PARSER_SOURCE.replace('from reliability.verifier.selection import django_label\n',''),
            '<sealed-native-terminal-parser>','exec'),self.parser)

    def run_bytes(self,path,expected=None):
        path=Path(path)
        if not path.is_absolute():path=ROOT/path
        relative=path.resolve().relative_to(RUN.resolve()).as_posix()
        assert relative in self.entries,relative
        raw=path.read_bytes();actual=sealed.sha(raw)
        assert actual==self.entries[relative] and (expected is None or actual==expected),relative
        self.hashes[str(path)]=actual
        return raw

    def run_json(self,relative,schema):
        return sealed.project(self.run_bytes(RUN/relative),schema)

    def original_bytes(self,path,expected=None):
        path=Path(path);assert path.is_relative_to(ORIGINAL) and str(path) in self.original_hashes
        raw=path.read_bytes();actual=sealed.sha(raw)
        assert actual==self.original_hashes[str(path)] and (expected is None or actual==expected),str(path)
        self.hashes[str(path)]=actual
        return raw

    def captured(self,run,runner,original=False):
        read=self.original_bytes if original else self.run_bytes
        files=run.get('evidence_files',{});hashes=run.get('evidence_sha256',{})
        log=read(files['runner.raw'],hashes['runner.raw']) if 'runner.raw' in files else b''
        stderr=read(files['stderr.raw'],hashes['stderr.raw']) if 'stderr.raw' in files else b''
        observed=self.parser['parse_capture']((log+stderr).decode('utf-8','replace'),runner)
        events=run.get('events',[])
        if not original and 'events.jsonl' in files:
            raw_events=read(files['events.jsonl'],hashes['events.jsonl'])
            projected=[sealed.project(line,EVENT) for line in raw_events.splitlines() if line.strip()]
            assert projected==events,'Recorded event receipts differ from capture'
            events=projected
        return {'run':run,'runner':runner,'log':log,'stderr':stderr,'observed':observed,
                'events':events,'files':files}


def test_status(capture,tid,family=None):
    run,runner=capture['run'],capture['runner']
    expected=sealed.django_label(tid) if runner=='django' else normalize(tid)
    exact=[(rid,v) for rid,v in capture['observed'].items() if v['kind']=='case' and normalize(rid)==expected]
    if not exact and '[' not in tid:
        exact=[(rid,v) for rid,v in capture['observed'].items() if v['kind']=='case' and normalize(rid).split('[',1)[0]==expected]
    if exact:
        values=[v['status'] for _,v in exact]
        return {'status':values[0] if len(set(values))==1 else 'MIXED',
                'source':'native terminal capture','raw_cases':[{'test_id':rid,'status':v['status'],'line':v['line']} for rid,v in exact]}
    for row in run.get('execution_results',[]):
        if normalize(row['test_id']) in (normalize(tid),expected):
            return {'status':row['status'],'source':'recorded execution attribution','message':row.get('message','')}
    selected=next((r for r in run.get('results',[]) if r['test_id']==tid),None)
    if selected:
        return {'status':selected['status'],'source':'recorded selected slot','message':selected.get('message','')}
    return {'status':'NOT_OBSERVED','source':'no exact terminal or execution identity',
            'family_status':next((r['status'] for r in run.get('results',[]) if r['test_id']==family),None)}


def native_identity(identity,runner):
    return sealed.django_label(identity) if runner=='django' and '::' in identity else normalize(identity)


def batch_audit(capture,event):
    start=next((e for e in capture['events'] if e.get('event')=='start' and e.get('batch')==event.get('batch')),{})
    begin,end=start.get('offset',0),event.get('offset',len(capture['log']))
    assert 0<=begin<=end<=len(capture['log'])
    text=capture['log'][begin:end].decode('utf-8','replace')
    actual=capture['run']
    missing=set(event.get('missing_ids',[]))
    native_missing={native_identity(t,capture['runner']) for t in missing}
    crashes=[r['test_id'] for r in actual.get('execution_results',[]) if r['status']=='crash' and native_identity(r['test_id'],capture['runner']) in native_missing]
    progress=bool(event.get('observed_ids') or event.get('per_test_output') or event.get('active_id') or event.get('test_started'))
    death=isinstance(event.get('returncode'),int) and event['returncode']!=0 and not event.get('timed_out')
    first_line=capture['log'][:begin].count(b'\n')+1
    last_line=capture['log'][:end].count(b'\n')
    terminal=[{'test_id':rid,'status':v['status'],'line':v['line']}
              for rid,v in capture['observed'].items() if v['kind']=='case' and first_line<=v['line']<=last_line]
    terminal.sort(key=lambda x:x['line'])
    summaries=re.findall(r'Ran (\d+) tests? in ([0-9.]+)s',text)
    normal=event.get('returncode')==0 and bool(re.search(r'^OK(?: \(.*\))?\s*$',text,re.M))
    return {'batch':event.get('batch'),'module':event.get('module',start.get('module')),
        'argv':start.get('argv',[]),'returncode':event.get('returncode'),'timed_out':bool(event.get('timed_out')),
        'observed_selected_ids':event.get('observed_ids',[]),'active_id':event.get('active_id'),
        'observed_progress':progress,'process_death_after_progress':death and progress,
        'recorded_CRASH_execution_ids':crashes,'missing_execution_ids':sorted(missing),
        'pre_registered_CRASH_rule_supported':bool(crashes) and death and progress,
        'normal_runner_completion':normal,'runner_summary':summaries[-1] if summaries else None,
        'last_terminal_cases':terminal[-5:],
        'attribution_note':('Recorded CRASH lacks process-death evidence; normal-exit unreported requests, not established crash collateral. Sealed values unchanged.' if crashes and not death else ''),
        'traceback_signatures':signatures(text),'capture_file':capture['files'].get('runner.raw'),
        'capture_byte_offsets':[begin,end],
        'tail_excerpt':text[-1600:]}


def confirmation_proof(capture,candidate,base_capture):
    run=capture['run'];row=next((r for r in run['results'] if r['test_id']==candidate),None)
    assert row is not None
    matched_cases=[{'test_id':rid,'status':v['status'],'line':v['line']} for rid,v in capture['observed'].items() if v['kind']=='case'
             and candidate in run.get('raw_id_map',{}).get(rid,[])]
    matches=[v for rid,v in capture['observed'].items() if v['kind']=='case'
             and candidate in run.get('raw_id_map',{}).get(rid,[])]
    if matches:
        derived=max((v['status'] for v in matches),key=lambda x:SEVERITY[x])
        return {'recorded_status':row['status'],'raw_derived_status':derived,
            'verified':derived==row['status'],'proof_kind':'native terminal cases',
            'native_case_count':len(matches),'native_terminal_cases':matched_cases,
            'traceback_signatures':signatures((capture['log']+capture['stderr']).decode('utf-8','replace')) if row['status'] in ('failed','error') else []}
    if row['status']=='crash':
        evidence=[batch_audit(capture,e) for e in capture['events'] if e.get('event')=='end'
                  and batch_audit(capture,e)['recorded_CRASH_execution_ids']]
        ok=any(e['process_death_after_progress'] for e in evidence)
        return {'recorded_status':'crash','raw_derived_status':'crash' if ok else None,
                'verified':ok,'proof_kind':'process death after progress','evidence':evidence}
    if row['status']=='error':
        receipt=next((r for r in run.get('validation',[]) if r['selected_id']==candidate),{})
        pending={native_identity(t,capture['runner']) for t in receipt.get('runnable_ids',[])}
        ends=[e for e in capture['events'] if e.get('event')=='end' and pending.intersection(native_identity(t,capture['runner']) for t in e.get('missing_ids',[]))]
        silent=[e for e in ends if e.get('load_failure') and not e.get('observed_ids') and not e.get('per_test_output') and not e.get('test_started') and not e.get('active_id') and not e.get('timed_out')]
        proven=[]
        for e in silent:
            parent=next((p for p in silent if p.get('batch')==e.get('parent')),None)
            base_progress=any(b.get('event')=='end' and module_key(b.get('module',''))==module_key(e.get('module',''))
                and (b.get('observed_ids') or b.get('per_test_output')) for b in base_capture['events'])
            if e.get('retry') and parent and base_progress:
                proven.append(batch_audit(capture,e))
        fixtures=[{'test_id':rid,'status':v['status'],'kind':v['kind']} for rid,v in capture['observed'].items()
                  if v['status']=='error' and v['kind']!='case']
        ok=bool(proven or fixtures)
        return {'recorded_status':'error','raw_derived_status':'error' if ok else None,'verified':ok,
                'proof_kind':'Fix17 silent patched module after base progress' if proven else 'native fixture/loader error' if fixtures else 'NO_POSITIVE_RAW_PROOF',
                'silent_retry_evidence':proven,'fixture_evidence':fixtures}
    return {'recorded_status':row['status'],'raw_derived_status':None,'verified':False,'proof_kind':'NO_POSITIVE_RAW_PROOF'}


def collection_signature(run,receipt,result,module):
    texts=[receipt.get('message',''),result.get('message','')]
    direct=[]
    for stage in run.get('stage_health',[]):
        if module_key(stage.get('module',''))==module_key(module):
            if stage.get('import_signature'):direct.append(stage['import_signature'])
            texts.extend(stage.get('messages',[]));texts.append(stage.get('message',''))
    for row in run.get('execution_results',[]):
        if row['status']=='collection_error' and row['test_id'] in receipt.get('runnable_ids',[]):
            texts.append(row.get('message',''))
    if direct:return ' | '.join(sorted(set(direct)))
    text='\n'.join(str(x) for x in texts if x)
    values=signatures(text)
    if values:return ' | '.join(values[-2:])
    return receipt.get('reason') or text[:400] or 'COLLECTION_ERROR: no signature recorded'


def analyze():
    entries,manifest,seal_result=preconditions()
    raw=LABELS.read_bytes();assert sealed.sha(raw)==LABELS_SHA
    sidecar=json.loads(raw)
    labels={iid:{'right':'correct','wrong':'incorrect'}[row['correctness']] for iid,row in sidecar.items()}
    counts=collections.Counter(labels.values())
    assert counts=={'correct':69,'incorrect':14},dict(counts)
    sealed_rows={r['task']:r for r in seal_result['per_task']}
    assert set(labels)==set(sealed_rows)
    data=Data(entries,seal_result)
    plan=data.run_json('plan.json',{'task_order':True,'task_specs':{'*':{'instance_id':True,'patch_sha256':True}}})
    for task in plan['task_specs']:
        assert sidecar[task['instance_id']]['patch_sha256']==task['patch_sha256'],'Correctness label candidate mismatch'
    order=plan['task_order']
    verdicts={p:{iid:sealed_rows[iid]['policies'][p] for iid in order} for p in POLICIES}
    policies={p:evaluate(verdicts[p],labels) for p in POLICIES}
    old_verdicts={};old_captures={};old_selected={}
    special_tasks={r['task'] for r in GRADER_TESTS+KNOWN_WITNESSES}|{'pylint-dev__pylint-6528','pylint-dev__pylint-7277'}
    for iid in order:
        path=ORIGINAL/'tasks'/iid/'v2/result.json'
        old=sealed.project(data.original_bytes(path),ORIGINAL_SCHEMA)
        old_verdicts[iid]=old['signal'] or 'NOT_AVAILABLE'
        old_selected[iid]=old.get('selected_tests') or []
        if iid in special_tasks:
            runner='django' if iid.startswith('django__') else 'pytest'
            old_captures[iid]={('patched' if c['patched'] else 'base'):data.captured(c['run'],runner,original=True) for c in old.get('calls',[])}
    original=evaluate(old_verdicts,labels)
    assert len(SKIP_DEPENDENT_TASKS)==13 and all(old_verdicts[iid]=='PASS' for iid in SKIP_DEPENDENT_TASKS)
    skip_wrong=[iid for iid in SKIP_DEPENDENT_TASKS if labels[iid]=='incorrect']
    assert len(skip_wrong)==4
    witness_groups={'grader_failing_pre_existing':[],'known_regression_witnesses':[]}
    cpu_families={(r['task'],r['test_id']) for r in seal_result['H3']['CPU_conditioned']['fixed_ids']}
    cpu_cases=collections.defaultdict(dict)
    crash_rows=[];noncap_rows=[];confirmations=[];candidate_rows=[]
    coll=collections.Counter();coll_tree=collections.Counter()
    for number,iid in enumerate(order,1):
        captures={}
        for tree in ('base','patched'):
            run=data.run_json('tasks/'+iid+'/'+tree+'.json',PASS_SCHEMA)
            runner=run.get('validation_summary',{}).get('context',{}).get('runner')
            runner=runner or ('sympy' if iid.startswith('sympy__') else 'django' if iid.startswith('django__') else 'pytest')
            capture=data.captured(run,runner);captures[tree]=capture
            for event in capture['events']:
                if event.get('event')!='end':continue
                audit=batch_audit(capture,event)
                if audit['recorded_CRASH_execution_ids']:
                    crash_rows.append({'task':iid,'tree':tree,'scope':'initial',**audit})
            results={r['test_id']:r for r in run['results']}
            receipts={r['selected_id']:r for r in run['validation']}
            for tid,result in results.items():
                receipt=receipts[tid]
                if result['status']=='not_reached' and not run.get('timed_out'):
                    native={native_identity(t,runner) for t in receipt.get('runnable_ids',[])}
                    relevant=[batch_audit(capture,e) for e in capture['events'] if e.get('event')=='end' and native.intersection(native_identity(t,runner) for t in e.get('missing_ids',[]))]
                    collateral=any(e['process_death_after_progress'] and e['recorded_CRASH_execution_ids']
                        and native.isdisjoint(native_identity(t,runner) for t in e['recorded_CRASH_execution_ids']) for e in relevant)
                    noncap_rows.append({'task':iid,'tree':tree,'test_id':tid,'sealed_status':'not_reached',
                                        'crash_collateral':collateral,'reclassified':False,'preceding_batches':relevant,
                                        'explanation':('Process-death collateral supported by the capture' if collateral else
                                            'Normal-exit unreported requests; no emitted start/result or explicit class-skip record establishes their underlying cause. Not crash collateral; sealed statuses unchanged.' if any(e['normal_runner_completion'] for e in relevant) else
                                            'Cause not established by captured evidence; sealed statuses unchanged')})
                if result['status']=='collection_error':
                    module=tid.split('::')[0];signature=collection_signature(run,receipt,result,module)
                    coll[iid,module,signature]+=1;coll_tree[iid,module,signature,tree]+=1
            for raw_id,observed in capture['observed'].items():
                if observed['kind']=='case' and any((iid,tid) in cpu_families for tid in run.get('raw_id_map',{}).get(raw_id,[])):
                    cpu_cases[iid,raw_id][tree]={'status':observed['status'],'line':observed['line'],'capture':capture['files'].get('runner.raw')}
        for group,definitions in (('grader_failing_pre_existing',GRADER_TESTS),('known_regression_witnesses',KNOWN_WITNESSES)):
            for definition in definitions:
                if definition['task']!=iid:continue
                row={**definition,'label':labels[iid],
                    'Policy_C':verdicts['C_invalid_excluded'][iid],'Policy_S':verdicts['S_invalid_excluded'][iid],
                    'trees':{tree:test_status(captures[tree],definition['test_id'],definition['family']) for tree in ('base','patched')},
                    'original_trees':{tree:test_status(old_captures[iid][tree],definition['test_id'],definition['family']) for tree in ('base','patched')}}
                witness_groups[group].append(row)
        item=data.run_json('tasks/'+iid+'/result.json',{'native_passes':True,'policies':{p:REPORT_SCHEMA for p in POLICIES}})
        assert all(item['policies'][p]['signal']==verdicts[p][iid] for p in POLICIES)
        primary=item['policies']['C_invalid_excluded'];calls=primary.get('confirmations',[])
        assert len(calls)==item['native_passes']-2
        candidate_calls=collections.defaultdict(lambda:{'base':[],'patched':[]})
        for call in calls:
            meta=call['confirmation'];candidate=meta['candidate_id'];tree=meta['tree']
            capture=data.captured(call,captures[tree]['runner'])
            proof=confirmation_proof(capture,candidate,captures['base'])
            record={'task':iid,'label':labels[iid],'candidate_id':candidate,'tree':tree,'attempt':meta['attempt'],
                'isolated':meta['isolated'],'capture':capture['files'].get('runner.raw'),**proof}
            confirmations.append(record);candidate_calls[candidate][tree].append(record)
            for event in capture['events']:
                if event.get('event')=='end':
                    audit=batch_audit(capture,event)
                    if audit['recorded_CRASH_execution_ids']:
                        crash_rows.append({'task':iid,'tree':tree,'scope':'confirmation','candidate_id':candidate,**audit})
        for summary in primary.get('confirmation_summary',[]):
            candidate=summary['candidate_id'];groups=candidate_calls[candidate]
            groups={tree:sorted(rows,key=lambda x:x['attempt']) for tree,rows in groups.items()}
            status={tree:[r['recorded_status'] for r in rows] for tree,rows in groups.items()}
            stable=(len(groups['base'])==len(groups['patched'])==3 and all(s=='passed' for s in status['base'])
                    and all(s in ('failed','error','crash') for s in status['patched']))
            assert status['base']==summary['base_statuses'] and status['patched']==summary['patched_statuses']
            assert stable==summary['stable']
            candidate_rows.append({'task':iid,'label':labels[iid],'candidate_id':candidate,
                'initial_outcome':summary['initial_outcome'],'final_outcome':primary['outcomes'].get(candidate),
                'base_statuses':status['base'],'patched_statuses':status['patched'],'stable_under_registered_rule':stable,
                'all_six_raw_proofs_verified':all(r['verified'] for rows in groups.values() for r in rows),
                'patched_raw_failure_signatures':sorted({sig for r in groups['patched'] for sig in r.get('traceback_signatures',[])})})
        print(json.dumps({'event':'posthoc_task','completed':number,'total':83,'task':iid}),flush=True)
    assert len(confirmations)==seal_result['confirmation_run_count']==72
    assert len(noncap_rows)==6 and {r['task'] for r in noncap_rows}=={'django__django-13297','django__django-14631','django__django-15930'}
    assert sum(coll.values())==seal_result['category_counts_total']['COLLECTION_ERROR']==1934
    cpu=[]
    for (iid,tid),trees in sorted(cpu_cases.items()):
        assert set(trees)=={'base','patched'}
        cpu.append({'task':iid,'test_id':tid,'label':labels[iid],'trees':trees,
                    'original_trees':{tree:test_status(old_captures[iid][tree],tid) for tree in ('base','patched')}})
    assert len(cpu)==38 and sum(len(r['trees']) for r in cpu)==76
    assert all(tree['status']=='passed' for r in cpu for tree in r['trees'].values())
    modules=collections.defaultdict(lambda:{'slots':0,'by_tree':collections.Counter(),'signatures':[]})
    for (iid,module,signature),count in sorted(coll.items()):
        row=modules[iid,module];row['slots']+=count
        trees={tree:coll_tree[iid,module,signature,tree] for tree in ('base','patched')}
        row['by_tree'].update(trees);row['signatures'].append({'signature':signature,'slots':count,'by_tree':trees})
    breakdown=[{'task':iid,'module':module,'slots':row['slots'],'by_tree':dict(row['by_tree']),
                'signatures':row['signatures']} for (iid,module),row in modules.items()]
    breakdown.sort(key=lambda x:(-x['slots'],x['task'],x['module']))
    global_modules={}
    for row in breakdown:
        key=(row['task'].split('__',1)[0],row['module'])
        item=global_modules.setdefault(key,{'repository':key[0],'module':key[1],'slots':0,'by_tree':collections.Counter(),'tasks':set(),'signatures':collections.Counter()})
        item['slots']+=row['slots'];item['by_tree'].update(row['by_tree']);item['tasks'].add(row['task'])
        for signature in row['signatures']:item['signatures'][signature['signature']]+=signature['slots']
    ranked_modules=[{**row,'by_tree':dict(row['by_tree']),'tasks':sorted(row['tasks']),
        'signatures':[{'signature':sig,'slots':n} for sig,n in sorted(row['signatures'].items())]} for row in global_modules.values()]
    ranked_modules.sort(key=lambda x:(-x['slots'],x['repository'],x['module']))
    witness_summary={group:{'tests':len(rows),'current_status_pairs':dict(sorted(collections.Counter(
        row['trees']['base']['status']+' / '+row['trees']['patched']['status'] for row in rows).items())),
        'tasks':sorted({r['task'] for r in rows})} for group,rows in witness_groups.items()}
    result={'scope':'Phase 4 plan section 5 post-hoc; immutable executor and seal',
        'preconditions':{'remote_seal_target':SEALED_HEAD,'annotated_tag_object':SEAL_TAG_OBJECT,'manifest':manifest},
        'labels':{'path':str(LABELS),'sha256':LABELS_SHA,'counts':dict(counts),'candidate_patch_hash_binding_verified':True},
        'interval_method':'Two-sided exact 95% Clopper-Pearson, beta quantiles 0.025 and 0.975',
        'denominator_rules':{'primary':'FAIL alone / all labelled patches, or / PASS+FAIL within each label',
                            'secondary':'FAIL+REGRESSION_ERROR / all labelled patches, or / PASS+FAIL+REGRESSION_ERROR within each label',
                            'missed':'Incorrect PASS; both all-incorrect and corresponding verdicted denominators'},
        'policies':policies,'original_V2':{'scope':'Frozen original native V2 verdicts; no invented original Policy S or INVALID_ID replay',**original},
        'witness_groups':witness_groups,'witness_summary':witness_summary,
        'skip_dependent':{'fixed_13_tasks':SKIP_DEPENDENT_TASKS,'incorrect_count':4,
            'incorrect_tasks':[{'task':iid,'label':labels[iid],'original_verdict':old_verdicts[iid],
                'policies':{p:verdicts[p][iid] for p in POLICIES}} for iid in skip_wrong]},
        'CPU_conditioned_tests':cpu,'confirmation_runs':confirmations,'stable_confirmation_set':candidate_rows,
        'confirmation_audit':{'actual_runs':len(confirmations),'candidates':len(candidate_rows),
            'raw_proofs_verified':sum(r['verified'] for r in confirmations),
            'all_candidates_match_registered_stability_rule':all(r['stable_under_registered_rule'] for r in candidate_rows),
            'django_10973':[r for r in candidate_rows if r['task']=='django__django-10973']},
        'crash_attribution':crash_rows,'noncap_NOT_REACHED':noncap_rows,
        'crash_attribution_summary':{'recorded_CRASH_execution_slots':sum(len(x['recorded_CRASH_execution_ids']) for x in crash_rows),
            'recorded_CRASH_slots_with_process_death_proof':sum(len(x['recorded_CRASH_execution_ids']) for x in crash_rows if x['pre_registered_CRASH_rule_supported']),
            'normal_exit_CRASH_attributions':sum(len(x['recorded_CRASH_execution_ids']) for x in crash_rows if x['normal_runner_completion']),
            'noncap_NOT_REACHED_supported_as_crash_collateral':sum(x['crash_collateral'] for x in noncap_rows),
            'reclassification_performed':False},
        'collection_errors':{'unit':'initial selected tree slots','total_slots':sum(coll.values()),
            'by_task':dict(sorted(collections.Counter({iid:sum(r['slots'] for r in breakdown if r['task']==iid) for iid in {r['task'] for r in breakdown}}).items())),
            'by_task_module_signature':breakdown,'top_15_task_modules':breakdown[:15],
            'top_15_modules':ranked_modules[:15]},
        'sealed_quantities':{k:seal_result[k] for k in ('H1','H1b','H2','H3','cap_hits','category_counts_total')},
        'per_task_labels_and_verdicts':[{'task':iid,'label':labels[iid],'original_V2':old_verdicts[iid],
            'policies':{p:verdicts[p][iid] for p in POLICIES}} for iid in order],
        'fixed_named_group_definition_provenance':DEFINITION_PROVENANCE,
        'data_input_sha256':dict(sorted(data.hashes.items())),
        'script_sha256':sealed.hash_file(Path(__file__)),'scipy_version':scipy.__version__,
        'reclassification_performed':False,'executor_changed':False,'sealed_results_changed':False,'tags_changed':False}
    sealed.verify_run()
    return result


def fmt(p):
    if not p['defined']:return '%d/0 (undefined)'%p['count']
    return '%d/%d = %.2f%% [%.2f%%, %.2f%%]'%(p['count'],p['denominator'],100*p['fraction'],100*p['ci95'][0],100*p['ci95'][1])


def matrix_lines(result):
    lines=['| Policy | Verdict | Correct | Incorrect |','|---|---|---:|---:|']
    for policy,row in result['policies'].items():
        for verdict in VERDICTS:
            counts=row['verdict_by_label'][verdict]
            lines.append('| %s | %s | %s | %s |'%(policy,verdict,counts['correct'],counts['incorrect']))
    return lines


def rates_lines(result,include_original=True):
    lines=['All intervals below are exact two-sided 95% Clopper-Pearson. Primary positive = FAIL; secondary positive = FAIL or REGRESSION_ERROR. The conditional denominator is PASS+FAIL for primary, and PASS+FAIL+REGRESSION_ERROR for secondary. No verdict is reclassified.','',
        '| Policy | Rule | Detection /14 | Detection among verdicted incorrect | False alarms /69 | False alarms among verdicted correct | Missed PASS /14 | Missed among verdicted incorrect |',
        '|---|---|---|---|---|---|---|---|']
    sources=list(result['policies'].items())+([('original_V2_native',result['original_V2'])] if include_original else [])
    for policy,row in sources:
        for rule,metrics in row['metrics'].items():
            lines.append('| %s | %s | %s |'%(policy,rule,' | '.join(fmt(metrics[key]) for key in (
                'detection_all_incorrect','detection_verdicted_incorrect','false_alarm_all_correct','false_alarm_verdicted_correct','missed_all_incorrect','missed_verdicted_incorrect'))))
    return lines


def markdown(r):
    lines=['# Phase 4 post-hoc analysis','',
        'Analysis follows the immutable `phase4-run-sealed` tag at `%s`. Labels: `%s`, SHA-256 `%s`; 69 correct and 14 incorrect, each bound to the manifested candidate patch hash.'%(SEALED_HEAD,r['labels']['path'],r['labels']['sha256']),
        '', '## Verdict by correctness label','']+matrix_lines(r)
    lines+=['','## Detection, false alarms and missed incorrect PASS','']+rates_lines(r)
    lines+=['','## Frozen original V2 comparison','','Original native verdicts only; no counterfactual original S or INVALID_ID policy has been fabricated.','','| Verdict | Correct | Incorrect |','|---|---:|---:|']
    for verdict in VERDICTS:
        x=r['original_V2']['verdict_by_label'][verdict];lines.append('| %s | %s | %s |'%(verdict,x['correct'],x['incorrect']))
    for group,title in (('grader_failing_pre_existing','Seven grader-failing existing tests'),('known_regression_witnesses','Six known regression witnesses')):
        lines+=['','## '+title,'','| Task | Test | Label | Original base / patched | Current base / patched | Policy C | Policy S |','|---|---|---|---|---|---|---|']
        for x in r['witness_groups'][group]:
            old=' / '.join(x['original_trees'][tree]['status'] for tree in ('base','patched'))
            new=' / '.join(x['trees'][tree]['status'] for tree in ('base','patched'))
            lines.append('| `%s` | `%s` | %s | %s | %s | %s | %s |'%(x['task'],x['test_id'],x['label'],old,new,x['Policy_C'],x['Policy_S']))
    lines+=['','## Four incorrect patches among the 13 skip-dependent original PASS tasks','','| Task | Original | C excluded | S excluded | C missing | S missing |','|---|---|---|---|---|---|']
    for x in r['skip_dependent']['incorrect_tasks']:
        p=x['policies'];lines.append('| `%s` | %s | %s | %s | %s | %s |'%(x['task'],x['original_verdict'],p['C_invalid_excluded'],p['S_invalid_excluded'],p['C_invalid_missing'],p['S_invalid_missing']))
    lines+=['','## CPU-conditioned outcomes reported at seal','','These 38 concrete tests (76 tree instances) were already reported at seal. No new tests were run. Membership uses the 12 fixed selected families saved in the sealed results.','','| Task | Native test | Original base / patched | Current base / patched |','|---|---|---|---|']
    for x in r['CPU_conditioned_tests']:
        lines.append('| `%s` | `%s` | %s | %s |'%(x['task'],x['test_id'], ' / '.join(x['original_trees'][t]['status'] for t in ('base','patched')),' / '.join(x['trees'][t]['status'] for t in ('base','patched'))))
    audit=r['confirmation_audit']
    lines+=['','## Stable confirmations and raw attribution','',
        '%s isolated tree calls cover %s candidates. Positive raw-capture proofs verified: %s. Stability is base PASS 3/3 and patched FAILED/ERROR/CRASH 3/3; no broader non-PASS set is used. ERROR/CRASH is scored as ERROR, and the recorded outcomes remain unchanged.'%(audit['actual_runs'],audit['candidates'],audit['raw_proofs_verified']),
        '', '| Task | Candidate | Label | Initial | Final | Base statuses | Patched statuses | Stable | Raw proofs |','|---|---|---|---|---|---|---|---|---|']
    for x in r['stable_confirmation_set']:
        lines.append('| `%s` | `%s` | %s | %s | %s | %s | %s | %s | %s |'%(x['task'],x['candidate_id'],x['label'],x['initial_outcome'],x['final_outcome'],','.join(x['base_statuses']),','.join(x['patched_statuses']),x['stable_under_registered_rule'],x['all_six_raw_proofs_verified']))
    lines+=['','### Django-10973 REGRESSION_ERROR','', 'This task is correct-labelled. Five candidates have base PASS 3/3 and patched ERROR 3/3; the task contributes only to secondary positive/false-alarm counts. Native patched signatures:']
    for candidate in audit['django_10973']:
        lines.append('- `%s`: %s' % (candidate['candidate_id'], '; '.join(candidate['patched_raw_failure_signatures'])))
    lines+=['','### All 72 confirmation calls','','| Task | Candidate | Tree | Attempt | Recorded | Raw-derived | Proof |','|---|---|---|---:|---|---|---|']
    for x in r['confirmation_runs']:
        lines.append('| `%s` | `%s` | %s | %s | %s | %s | %s |'%(x['task'],x['candidate_id'],x['tree'],x['attempt'],x['recorded_status'],x['raw_derived_status'],x['proof_kind']))
    lines+=['','## Recorded CRASH attribution audit','','All six sealed CRASH attributions have progress but no process-death evidence: their batches exit 0 with an OK summary. They do not satisfy the pre-registered death requirement. The explanation below does not reclassify them; raw offsets, final terminal cases and excerpts are in analysis.json.','','| Task | Tree | Module | Exit | Progress | Recorded active CRASH |','|---|---|---|---:|---|---|']
    for x in r['crash_attribution']:
        lines.append('| `%s` | %s | `%s` | %s | %s | `%s` |'%(x['task'],x['tree'],x['module'],x['returncode'],x['observed_progress'],', '.join(x['recorded_CRASH_execution_ids'])))
    lines+=['','## Six NOT_REACHED slots without a cap','','Explanation only: these are normal-exit unreported requests, not supported crash collateral. The runner completes other tests successfully; neither omitted ForcedTimeZoneDatabaseTests method emits a result/start, and no explicit class-skip record establishes the underlying cause. No status or policy was reclassified.','','| Task | Tree | NOT_REACHED test | Preceding CRASH | Exit | Crash collateral | Signature |','|---|---|---|---|---:|---|---|']
    for x in r['noncap_NOT_REACHED']:
        b=x['preceding_batches'][0] if x['preceding_batches'] else {}
        lines.append('| `%s` | %s | `%s` | `%s` | %s | %s | %s |'%(x['task'],x['tree'],x['test_id'],', '.join(b.get('recorded_CRASH_execution_ids',[])),b.get('returncode'),x['crash_collateral'],'; '.join(b.get('traceback_signatures',[])).replace('|','\\|')))
    lines+=['','## COLLECTION_ERROR: largest remaining missing-evidence category','',
        '%s initial selected tree slots. Complete task/module/signature breakdown is in analysis.json; the 15 largest modules follow.'%r['collection_errors']['total_slots'],
        '', '| Repository | Module | Slots | Base | Patched | Affected tasks | Signatures |','|---|---|---:|---:|---:|---:|---|']
    for x in r['collection_errors']['top_15_modules']:
        sig='; '.join('%s (%s)'%(s['signature'],s['slots']) for s in x['signatures']).replace('|','\\|').replace('\n',' ')
        lines.append('| `%s` | `%s` | %s | %s | %s | %s | %s |'%(x['repository'],x['module'],x['slots'],x['by_tree']['base'],x['by_tree']['patched'],len(x['tasks']),sig))
    lines+=['','## Disclosures','',
        '- INVALID_ID sensitivity: Policy C primary yes/no is 58 with invalid IDs excluded versus 48 treated as missing; Policy S is 26 versus 25.',
        '- The six non-cap NOT_REACHED slots are normal-exit unreported requests, not supported crash collateral. Their companion sealed CRASH attributions lack process-death evidence. Neither status is reclassified.',
        '- COLLECTION_ERROR is the largest remaining unadmitted status category across all initial selected tree slots; this is not a claim about its share within the fixed B1 residual.',
        '- CPU-conditioned outcomes were reported at seal, before labels were read.',
        '- The frozen original comparison uses its recorded native policy, not a fabricated repaired-policy replay.',
        '', 'The executor, all sealed results, run files, and all tags remain unchanged. This script performs analysis only; no Docker or benchmark execution.', '']
    return '\n'.join(lines).encode()


def main():
    result=analyze()
    (OUT/'analysis.json').write_bytes(sealed.json_bytes(result))
    (OUT/'analysis.md').write_bytes(markdown(result))
    print(json.dumps({'analysis_json_sha256':sealed.hash_file(OUT/'analysis.json'),
        'analysis_md_sha256':sealed.hash_file(OUT/'analysis.md'),
        'confirmation_raw_proofs':result['confirmation_audit']['raw_proofs_verified'],
        'noncap_slots':len(result['noncap_NOT_REACHED'])},sort_keys=True))


if __name__=='__main__':main()
