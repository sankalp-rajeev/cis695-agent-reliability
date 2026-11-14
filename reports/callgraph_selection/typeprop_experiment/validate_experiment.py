"""Independent streaming checks over persisted before/after graph artifacts."""
from __future__ import annotations
import json
import sys
from collections import Counter
from itertools import zip_longest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent),str(HERE.parents[2]/'src')]
from evaluate import original_state, verify_manifest
from build_graphs import digest
from followup_analysis import records


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for filename,sha in protocol['code_sha256'].items():
        assert digest(HERE/filename)==sha, ('Execution code changed',filename)
    original=Path(protocol['original_worktree'])
    cg=original/'reports/callgraph_selection'
    manifest=json.loads((HERE.parent/'amendment2_72ad21b/graph_manifest.json').read_text())
    summary=json.loads((HERE/'enhanced_summary.json').read_text())
    validation=json.loads((HERE/'validation.json').read_text())
    transitions=Counter();sites=0;new_unique=0;unchanged_resolved_targets=0;task_files=0
    for iid,entry in sorted(manifest.items()):
        directory=HERE/'task_artifacts'/iid
        task=json.loads((directory/'summary.json').read_text())
        assert task['comparable'],('Missing comparable graph',iid)
        for filename,sha in task['artifact_sha256'].items():
            assert digest(directory/filename)==sha,('Experiment artifact changed',iid,filename)
            task_files+=1
        facts={(r['scope'],r['name']):r for r in records(directory/'type_facts.jsonl.gz')}
        baseline=records(cg/entry['directory']/'edges.jsonl.gz')
        enhanced=records(directory/'edges.jsonl.gz')
        for before,after in zip_longest(baseline,enhanced):
            assert before is not None and after is not None,('Callsite count changed',iid)
            for key in ('caller','scope','path','line','column','expression'):
                assert before[key]==after[key],('Callsite identity changed',iid,key)
            transitions[before['status']+' -> '+after['status']]+=1
            sites+=1
            if before['status']=='resolved':
                assert after['status']=='resolved' and before['targets']==after['targets'],('Resolved edge regressed',iid)
                unchanged_resolved_targets+=1
            if after['status']=='resolved' and before['status']!='resolved':
                assert len(after['targets'])==len(after['receiver_types'])==1
                fact=facts[(after['receiver_fact']['scope'],after['receiver_fact']['name'])]
                assert not fact['unknown'] and fact['types']==after['receiver_types']
                assert after['baseline_status']==before['status']
                assert after['baseline_targets']==before['targets']
                new_unique+=1
        print(iid,'validated',flush=True)
    assert dict(transitions)==summary['transitions']
    assert sites==summary['call_sites']
    assert new_unique==validation['new_resolved_edges']
    assert original_state(original)==json.loads((HERE/'original_worktree_snapshot.json').read_text())
    baseline_files=verify_manifest(original,manifest)
    validation.update(independent_streaming_validation_passed=True, independently_checked_call_sites=sites,
        unchanged_resolved_target_lists=unchanged_resolved_targets, validated_new_unique_receiver_edges=new_unique,
        experimental_artifact_hashes_verified=task_files, verified_baseline_files=baseline_files,
        original_worktree_untouched=True, code_hashes_match_execution=True)
    (HERE/'validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
    print(json.dumps(validation,sort_keys=True),flush=True)


if __name__=='__main__':
    main()
