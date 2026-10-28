"""Evaluate frozen shadow rule using allowlisted projections only.

Write predictions BEFORE opening retrospective labels. Missing historical raw
logs remain absent. Full initial-run context is retained, including runner errors.
"""
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

import pyarrow as pa

from reliability.verifier.superseded_shadow import run_shadow

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2_stabilization'
AUDIT=ROOT/'reports/v2_scoring_audit'
COHORT=('django__django-12209','django__django-14140','django__django-14631',
        'pytest-dev__pytest-5809','sphinx-doc__sphinx-10435')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    frozen=json.loads((OUT/'frozen_rule.json').read_text())
    implementation=ROOT/'src/reliability/verifier'
    for name,digest in frozen['implementation_sha256'].items():
        assert sha((implementation/name).read_bytes())==digest
    # Read only issue IDs/statements from the local Arrow cache. No dataset loader.
    cache=next((Path.home()/'.cache/huggingface/datasets/SWE-bench___swe-bench_verified').rglob('*-test.arrow'))
    issues={}
    with pa.memory_map(str(cache),'r') as stream:
        for batch in pa.ipc.open_stream(stream):
            for row in batch.select(['instance_id','problem_statement']).to_pylist():
                if row['instance_id'] in COHORT:issues[row['instance_id']]=row['problem_statement']
    # This contains V2 regression IDs, not superseded/genuine/gold classifications.
    v2=json.loads((ROOT/'reports/failure_analysis/group4_regression_rerun.json').read_text())
    failing={r['instance_id']:r['failing'] for r in v2['tasks']}
    packets=[];manifests=[]
    resumed=AUDIT/'resume_20261026'
    for iid in COHORT:
        patch_path=AUDIT/'frozen_inputs'/f'{iid}.patch'
        paths=sorted({tid.split('::',1)[0] for tid in failing[iid]})
        archive=Path.home()/'cg_repos/task_archives'/f'{iid}.tar'
        with tarfile.open(archive) as tar:
            sources=[tar.extractfile('testbed/'+p).read().decode() for p in paths]
        packet={'issue':issues[iid],'candidate_patch':patch_path.read_text(),
                'test_source':'\n'.join(sources),'base_output':[],'patched_output':[]}
        refs={'issue':str(cache)+':'+iid+':problem_statement',
              'candidate_patch':str(patch_path.relative_to(ROOT)),
              'test_source':[str(archive)+'!testbed/'+p for p in paths],
              'base_output':[],'patched_output':[]}
        if (resumed/'phase2'/iid/'base/initial/runner.raw').exists():
            tid=failing[iid][0]
            candidates=json.loads((resumed/'phase3'/iid/'candidates.json').read_text())['candidates']
            index=candidates.index(tid)
            for tree,key in (('base','base_output'),('patched','patched_output')):
                folders=[resumed/'phase2'/iid/tree/'initial']+[
                    resumed/'phase3'/iid/tree/f'candidate_{index:04d}_repeat_{repeat}'
                    for repeat in (1,2,3)]
                for folder in folders:
                    attempt=json.loads((folder/'attempt.json').read_text())
                    events=[json.loads(s) for s in (folder/'batch_events.jsonl').read_text().splitlines()]
                    starts={e['batch']:e for e in events if e['event']=='start'}
                    matching=[e for e in events if e['event']=='end' and e['returncode'] in (0,1)
                              and tid in starts[e['batch']]['ids']]
                    packet[key].append({'stdout':(folder/'runner.raw').read_text(errors='replace'),
                        'stderr':(folder/'driver.stderr').read_text(errors='replace'),
                        'returncode':matching[-1]['returncode'] if matching else None,
                        'timed_out':attempt['driver_state']=='timeout'})
                    refs[key].append({'stdout':str((folder/'runner.raw').relative_to(ROOT)),
                        'stderr':str((folder/'driver.stderr').relative_to(ROOT)),
                        'receipt':str((folder/'batch_events.jsonl').relative_to(ROOT)),
                        'receipt_note':'Target test batch exit; complete initial raw context is not trimmed'})
        packets.append(packet)
        manifests.append({'instance_id':iid,'held_out_diagnostic':iid=='django__django-12209',
            'allowlisted_inputs_sha256':sha(json.dumps(packet,sort_keys=True).encode()),
            'field_sha256':{key:sha(json.dumps(value,sort_keys=True).encode()) for key,value in packet.items()},
            'source_refs':refs,'observations':{'base':len(packet['base_output']),'patched':len(packet['patched_output'])}})
    # Canary + real prohibited files: deny at OS boundary, not a prompt instruction.
    probes=[ROOT/'reports/failure_analysis/group4_gold_check.json',
            ROOT/'reports/failure_analysis/quotes/pytest-dev__pytest-5809.md',
            ROOT/'docs/results_100.csv',
            ROOT/'runs/main_50_a/tasks/pytest-dev__pytest-5809/oracle_record.json']
    assert all(p.is_file() for p in probes)
    with tempfile.TemporaryDirectory(prefix='v2_classifier_isolation_',dir='/tmp') as tmp:
        canary=Path(tmp)/'retrospective_labels';canary.write_text('PROHIBITED_CANARY')
        result=run_shadow(packets,probes=[str(p) for p in probes]+[str(canary)])
    assert result.get('isolation',{}).get('all_filesystem_reads_denied'),result
    assert all(v=='DENIED' for v in result['isolation']['probe_results'].values())
    assert len(result['predictions'])==5
    output={'frozen_rule_sha256':frozen['frozen_rule_sha256'],
        'predictions_saved_before_retrospective_label_access':True,
        'prior_researcher_familiarity_acknowledged':True,
        'isolation':result['isolation'],
        'cases':[{**manifest,**prediction} for manifest,prediction in zip(manifests,result['predictions'],strict=True)]}
    with (OUT/'shadow_predictions.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
    for name,digest in frozen['implementation_sha256'].items():assert sha((implementation/name).read_bytes())==digest
    print('Frozen hash:',frozen['frozen_rule_sha256'])
    for case in output['cases']:print(case['instance_id'],case['prediction'],case['reason'])
    print('All prohibited-file read probes: DENIED. No task environments executed.')


if __name__=='__main__':main()
