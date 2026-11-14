"""Matched, isolated-process timing sample; no patches or outcome labels."""
from __future__ import annotations
import argparse
import json
import os
import resource
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CG = HERE.parent
ROOT = CG.parents[1]
sys.path[:0] = [str(HERE), str(CG), str(ROOT / 'src')]
from build_graphs import extract, digest
from static_graph import Graph
from amended_graph import AmendedGraph
from typeprop_graph import TypeGraph, TypeAmendedGraph


def worker(iid, variant):
    task = next(t for t in json.loads((CG / 'inputs.json').read_text())['tasks'] if t['instance_id'] == iid)
    manifest = json.loads((CG / 'amendment2_72ad21b/graph_manifest.json').read_text())
    amended = manifest[iid]['directory'].startswith('amendment2_')
    cls = ((TypeAmendedGraph if amended else TypeGraph) if variant == 'enhanced'
           else (AmendedGraph if amended else Graph))
    with tempfile.TemporaryDirectory(prefix='cis695-typeprop-timing-', dir='/tmp') as tmp:
        extract(task, Path(tmp))
        graph = cls().build(Path(tmp) / 'testbed')
    return dict(instance_id=iid, repo=task['repo'], variant=variant, graph_seconds=graph.runtime,
        process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        calls=len(graph.edges), resolved=sum(e['status']=='resolved' for e in graph.edges),
        inference_seconds=getattr(graph, 'type_metrics', {}).get('inference_seconds',0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', nargs=2, metavar=('INSTANCE','VARIANT'))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(*args.worker)))
        return
    groups = defaultdict(list)
    for task in json.loads((CG / 'inputs.json').read_text())['tasks']:
        groups[task['repo']].append(task['instance_id'])
    sample = [min(ids) for repo,ids in sorted(groups.items())]
    protocol = dict(sample_rule='lexicographically first instance per represented repository',
        tasks=sample, repetitions=1, order='baseline/enhanced alternates by repository index',
        isolated_processes=True, extraction_in_graph_seconds=False,
        rss='process high-water mark including extraction, interpreter and graph; not incremental bytes',
        code_sha256=digest(Path(__file__)), python=sys.version)
    (HERE / 'runtime_protocol.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n')
    rows=[]
    for index,iid in enumerate(sample):
        variants=('baseline','enhanced') if index%2==0 else ('enhanced','baseline')
        for variant in variants:
            env=dict(os.environ);env.pop('PYTHONPATH',None)
            result=subprocess.run([sys.executable,'-B',str(Path(__file__)), '--worker',iid,variant],
                env=env,cwd=ROOT,capture_output=True,text=True,check=True,timeout=720)
            row=json.loads(result.stdout);rows.append(row)
            print(json.dumps(row),flush=True)
            (HERE / 'runtime_sample.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
