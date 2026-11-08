#!/usr/bin/env python3
"""Build G2 identity sets from the frozen ORIGINAL V2 run, admission only."""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

from reliability.verifier.admission_reference import original_admitted

ROOT = Path(__file__).resolve().parents[1]
DATA = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z')


def main(output):
    if output.exists():
        raise ValueError('Use a fresh reference directory')
    expected = json.loads((ROOT/'reports/next_phases/phase2_incomplete_causes/input_manifest.json').read_text())['input_sha256']
    frozen = DATA/'paired_frozen'
    tasks = json.loads((frozen/'tasks.json').read_text())
    sets, counts, hashes = {}, [], {}
    for task in tasks:
        iid = task['instance_id']
        path = DATA/'full_83_20261105T231219_643682Z/results/tasks'/iid/'v2/result.json'
        ids = original_admitted(path, expected[str(path)])
        selected = set(json.loads((frozen/task['selections']['v2']).read_text())['tests'])
        if any(set(values)-selected for values in ids.values()):
            raise ValueError('Original admission contains a non-frozen identity: '+iid)
        sets[iid] = ids
        counts.append({'instance_id':iid,'base_reference_admitted_IDs':len(ids['base']),
                       'patched_reference_admitted_IDs':len(ids['patched'])})
        hashes[str(path)] = expected[str(path)]
        print('reference_projected',iid,flush=True)
    if len(sets) != 83:
        raise ValueError('Wrong G2 reference cohort')
    output.mkdir(parents=True)
    payload = (json.dumps(sets, sort_keys=True)+'\n').encode()
    (output/'reference_ids.json.gz').write_bytes(gzip.compress(payload, mtime=0))
    with (output/'counts.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(counts[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(counts)
    manifest = {'source':'frozen original V2 run; not attempt 1, attempt 2, or offline projection',
        'tasks':83,'input_sha256':hashes,'projected_fields':['calls[0:2].patched','calls[0:2].run.results[*].test_id','calls[0:2].run.results[*].status -> admission Boolean only'],
        'verdict_fields_decoded':False,'outcome_classes_retained':False,'correctness_labels_read':False,
        'reference_sha256':hashlib.sha256((output/'reference_ids.json.gz').read_bytes()).hexdigest(),
        'reference_uncompressed_sha256':hashlib.sha256(payload).hexdigest(),
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__).resolve(),ROOT/'src/reliability/verifier/admission_reference.py']}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
