"""Validate diagnostic accounting, source-file indexing and frozen-file preservation."""
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent;EXP=HERE.parent;CG=EXP.parent;ROOT=CG.parents[1]
sys.path[:0]=[str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from evaluate import records,original_state,dump


def main():
    rows=list(csv.DictReader((HERE/'cases.csv').open(newline='')))
    summary=json.loads((HERE/'summary.json').read_text())
    assert len(rows)==40 and len({r['case_id'] for r in rows})==40
    assert Counter(r['current_status'] for r in rows)=={'ambiguous':21,'unresolved':19}
    assert {k:Counter(r['fixability_classification'] for r in rows)[k] for k in 'ABCD'}==summary['fixability_counts']
    required=['task_id','repository','changed_symbol','current_status','exact_failure_reason','resolver_diagnostic',
              'source_code_explanation','root_cause_category','fixability_classification','potential_static_fix','confidence_in_diagnosis']
    assert all(all(r[k] for k in required) for r in rows)
    original=Path(json.loads((EXP/'protocol.json').read_text())['original_worktree'])
    graph_manifest=json.loads((CG/'amendment2_72ad21b/graph_manifest.json').read_text())
    files=defaultdict(set)
    for row in rows:files[row['task_id']].add(row['file'])
    checked=0
    for iid,paths in files.items():
        directory=original/'reports/callgraph_selection'/graph_manifest[iid]['directory']
        modules={n['path'] for n in records(directory/'nodes.jsonl.gz') if n['kind']=='module'}
        failures=json.loads((directory/'diagnostics.json').read_text())['parse_and_resource_failures']
        assert paths<=modules,(iid,paths-modules)
        assert not any(f.get('path') in paths for f in failures),iid
        checked+=len(paths)
    current_ids={(r['task_id'],r['file'],r['changed_symbol'],r['current_status']) for r in rows}
    frozen=list(csv.DictReader((CG/'amendment2_72ad21b/changed_symbol_resolution.csv').open()))
    frozen_ids={(r['instance_id'],r['base_path'],r['name'],r['status']) for r in frozen if r['status']!='resolved'}
    assert current_ids==frozen_ids
    for name,sha in json.loads((HERE/'output_hashes.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha,name
    tracked=subprocess.check_output(['git','ls-files','-z','reports/callgraph_selection/typeprop_experiment'],cwd=ROOT).decode().split('\0')
    for path in filter(None,tracked):
        assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show','df3bd9b:'+path],cwd=ROOT),path
    assert original_state(original)==json.loads((EXP/'original_worktree_snapshot.json').read_text())
    assert not subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode()
    validation=dict(passed=True,case_count=40,all_requested_columns_populated=True,exact_frozen_failed_case_identity=True,
        parsed_indexed_changed_file_task_pairs=checked,changed_file_omissions=0,direct_resource_causes=0,
        prior_experiment_tracked_files_unchanged=len(list(filter(None,tracked))),original_worktree_unchanged=True,
        diagnostic_hashes_verified=True,graph_rebuilt=False,selector_rerun=False,implementation_or_policy_changed=False)
    dump(HERE/'validation.json',validation)
    dump(HERE/'output_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir())
        if p.is_file() and p.name!='output_hashes.json' and p.suffix!='.log'})
    print(json.dumps(validation,indent=2,sort_keys=True))


if __name__=='__main__':main()
