"""Three exact local task images; V2 only, no selector, V1/V3/V4 or oracle runs."""
import csv
import hashlib
import json
import shlex
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa

from reliability.verifier.container import ContainerRepoTree, ContainerTestExecutor, TaskContainer
from reliability.verifier.decision import Evidence, FullPolicy
from reliability.verifier.record import (
    DecisionEntry,
    SignalAbsence,
    SignalKind,
    SignalRecord,
    VerificationRecord,
    evidence_from_record,
)
from reliability.verifier.regression import RegressionConfig, run_regression
from reliability.verifier.run import signal_from_regression
from reliability.verifier.selection import Selection, TestRunner
from reliability.verifier.superseded_shadow_v2 import shadow_from_report

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2_stabilization/classifier_v2'
INPUTS=ROOT/'reports/v2_scoring_audit/frozen_inputs'
CASES=('pylint-dev__pylint-7277','pylint-dev__pylint-6528','pytest-dev__pytest-5809')
REAL_RUN=subprocess.run


def sha(raw):return hashlib.sha256(raw).hexdigest()


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')


def logged_run(argv,*args,**kwargs):
    entry={'utc_before_execution':datetime.now(UTC).isoformat(),'argv':list(argv),
           'timeout_s':kwargs.get('timeout'),'stdin_sha256':None}
    data=kwargs.get('input')
    if data is not None:entry['stdin_sha256']=sha(data.encode() if isinstance(data,str) else data)
    with (OUT/'commands.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n');f.flush()
    print('EXACT COMMAND BEFORE EXECUTION:',shlex.join(argv),flush=True)
    return REAL_RUN(argv,*args,**kwargs)


class LocalOnlyContainer(TaskContainer):
    def run_args(self):
        argv=super().run_args();argv.insert(2,'--pull=never');return argv


class MeasuredExecutor:
    def __init__(self,executor):
        self.executor=executor;self.container=executor.container;self.calls=[]
    def run(self,tests,*,patched,timeout_s):
        start=time.monotonic()
        result=self.executor.run(tests,patched=patched,timeout_s=timeout_s)
        self.calls.append({'patched':patched,'requested_tests':list(tests),
            'wall_s':time.monotonic()-start,
            'runner_s':sum(e.get('duration_s',0.0) for e in result.events if e.get('event')=='end'),
            'runner_batches':sum(e.get('event')=='start' for e in result.events),
            'raw_cases':len(result.raw_results),'evidence_complete':result.evidence_complete,
            'timed_out':result.timed_out,'evidence_files':result.evidence_files})
        return result


def issue_projection():
    path=next((Path.home()/'.cache/huggingface/datasets/SWE-bench___swe-bench_verified').rglob('*-test.arrow'))
    result={}
    with pa.memory_map(str(path),'r') as stream:
        for batch in pa.ipc.open_stream(stream):
            for row in batch.select(['instance_id','problem_statement']).to_pylist():
                if row['instance_id'] in CASES:result[row['instance_id']]=row['problem_statement']
    return result


def one(iid,inputs,issue):
    folder=OUT/'live/tasks'/iid;folder.mkdir(parents=True,exist_ok=False)
    metadata=json.loads((OUT/'preflight'/f'{iid}.stdout').read_text())
    prior=json.loads((ROOT/'reports/v2_scoring_audit/resume_20261026/preflight'/f'{iid}.image.stdout').read_text())
    assert metadata['Id']==prior['Id'],'Image drift since previous raw audit'
    patch=(INPUTS/f'{iid}.patch').read_bytes();assert sha(patch)==inputs['patch_sha256']
    selected=tuple(inputs['selected_tests'])
    container=LocalOnlyContainer(iid,patch.decode(),image=metadata['Id'],
        experiment_id='v2_stabilization_live_v2')
    started=time.monotonic()
    try:
        container.start()
        paths=sorted({t.split('::',1)[0] for t in selected}|{
            line[6:] for line in patch.decode().splitlines() if line.startswith('+++ b/')})
        import tarfile
        with tarfile.open(Path.home()/'cg_repos/task_archives'/f'{iid}.tar') as archive:
            expected={path:sha(archive.extractfile('testbed/'+path).read()) for path in paths}
        code=("import json,hashlib,pathlib,sys,subprocess,pytest; "
              "paths="+repr(paths)+"; "
              "print(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),"
              "'python':sys.version,'pytest':pytest.__version__,"
              "'hashes':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths}}))")
        rc,raw=container.exec(shlex.join(['python','-c',code]),timeout_s=30)
        assert rc==0,raw
        observed=json.loads(raw);assert observed['hashes']==expected,'Base source drift'
        save(folder/'environment.json',{'image_id':metadata['Id'],'tag':inputs['study_image_tag'],
            'repo_digests':metadata.get('RepoDigests'),**observed,
            'base_source_matches_archives':True,'same_image_as_previous_audit':True,
            'historical_study_image_identity':'UNKNOWN: no historical digest; no substitution',
            'candidate_patch_sha256':sha(patch),'selection_sha256':sha(json.dumps(selected).encode()),
            'full_pass_timeout_s':300,'network':'none'})
        executor=MeasuredExecutor(ContainerTestExecutor(container,
            runner=TestRunner(inputs['runner'],'frozen original selection'),evidence_dir=folder/'raw'))
        report=run_regression(iid,Selection(tests=selected),executor,
                              RegressionConfig(baseline_cache_dir=None))
        initial_calls=len(executor.calls)
        native=report.signal
        shadow=shadow_from_report(report,issue,patch.decode(),ContainerRepoTree(container),executor)
        assert report.signal is native
        regression=signal_from_regression(report);regression.findings['superseded_shadow']=shadow
        # Other stages are explicitly disabled; this is not a full V1-V4 run.
        absent=lambda kind:SignalRecord.absent(kind,SignalAbsence.DISABLED,'V2-only live validation; stage not run')
        policy_input=Evidence(regression=regression.outcome)
        record=VerificationRecord(instance_id=iid,experiment_id='v2_stabilization_live_v2',
            verifier_config='full',patch_sha256='sha256:'+sha(patch),
            integrity=absent(SignalKind.INTEGRITY),regression=regression,
            static=absent(SignalKind.STATIC),reproduction=absent(SignalKind.REPRODUCTION),
            reproduction_generator={'generator':{'model_id':'NOT_INVOKED_V2_ONLY_VALIDATION'}},
            selected_tests=selected,selection_runner=inputs['runner'],
            decision=DecisionEntry.from_record(FullPolicy().decide(policy_input)),
            verified_at=datetime.now(UTC).isoformat())
        record.write(folder/'verification_record.full.json')
        restored=VerificationRecord.read(folder/'verification_record.full.json')
        assert restored.regression.findings['signal']==report.signal.value
        assert restored.regression.findings['original_signal']==report.original_signal.value
        assert evidence_from_record(restored).regression==regression.outcome
        for call in executor.calls:
            for name,path in call['evidence_files'].items():assert Path(path).is_file(),name
        for run in (report.baseline,report.patched,*report.confirmations):
            for name,path in run.evidence_files.items():assert sha(Path(path).read_bytes())==run.evidence_sha256[name]
        base={r.test_id:r.status.value for r in report.baseline.raw_results}
        patched={r.test_id:r.status.value for r in report.patched.raw_results}
        with (folder/'paired_outcomes.csv').open('x',newline='') as f:
            writer=csv.DictWriter(f,['raw_id','selected_ids','base','patched'],lineterminator='\n');writer.writeheader()
            for tid in sorted(base.keys()|patched.keys()):
                writer.writerow({'raw_id':tid,'selected_ids':json.dumps(report.baseline.raw_id_map.get(tid,())),
                                 'base':base.get(tid),'patched':patched.get(tid)})
        result={'instance_id':iid,'old':report.original_signal.value,'new':report.signal.value,
            'completeness':report.completeness,'incompleteness':list(report.incompleteness),
            'selected':len(selected),'base_raw_cases':len(base),'patched_raw_cases':len(patched),
            'base_accounted_selected':len({t for ids in report.baseline.raw_id_map.values() for t in ids}),
            'patched_accounted_selected':len({t for ids in report.patched.raw_id_map.values() for t in ids}),
            'raw_id_sets_equal':base.keys()==patched.keys(),
            'unmatched_ids':list(report.baseline.unmatched_ids+report.patched.unmatched_ids),
            'base_timeout':report.baseline.timed_out,'patched_timeout':report.patched.timed_out,
            'initial_and_legacy_calls':initial_calls,'all_calls':executor.calls,
            'initial_and_legacy_wall_s':sum(c['wall_s'] for c in executor.calls[:initial_calls]),
            'initial_and_legacy_runner_s':sum(c['runner_s'] for c in executor.calls[:initial_calls]),
            'shadow_extra_calls':len(executor.calls)-initial_calls,'shadow_costs':shadow.get('costs'),
            'shadow_predictions':shadow.get('predictions',[shadow]),
            'container_elapsed_s':time.monotonic()-started,
            'serialized_neutral_outcome':restored.regression.outcome.value,
            'downstream_roundtrip_passed':True,'raw_hash_checks_passed':True}
        save(folder/'result.json',result)
        print('LIVE RESULT',json.dumps({k:result[k] for k in
            ('instance_id','old','new','completeness','selected','base_raw_cases','shadow_extra_calls','shadow_costs')}),flush=True)
        return result
    finally:container.stop()


def main():
    subprocess.run=logged_run
    inputs=json.loads((INPUTS/'selections.json').read_text());issues=issue_projection()
    results=[one(iid,inputs[iid],issues[iid]) for iid in CASES]
    save(OUT/'live_summary.json',{'cases':results,
        'complete_PASS_achieved':any(r['new']=='PASS' and r['completeness']=='COMPLETE' for r in results),
        'total_initial_and_legacy_wall_s':sum(r['initial_and_legacy_wall_s'] for r in results),
        'total_shadow_extra_wall_s':sum(r['shadow_costs']['additional_wall_s'] for r in results),
        'total_shadow_extra_runner_s':sum(r['shadow_costs']['additional_runner_s'] for r in results),
        'Django':'Skipped: original audited Django task images are absent; no substitutes/pulls/builds',
        'v1_v3_v4':'Not run; disabled in transport records; final policy unchanged'})


if __name__=='__main__':main()
