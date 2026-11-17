"""Audit locally present cohort images; no pulls, persistent containers or writes.

--prepare writes PRIVATE stdin requests under runs/. --collect imports sanitized
probe outputs produced by Docker-only escalated commands. The default runs both.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from reliability.benchmark.image_leakage import (
    ROOT, prepare_requests, public_image_result, run_image,
)
from reliability.env import assert_clean_interpreter
from reliability.verifier.container import image_for


def main():
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'manifests/main_100.csv')
    parser.add_argument('--private', type=Path, default=ROOT/'runs/leakage_gaps')
    parser.add_argument('--output', type=Path, default=ROOT/'reports/next_phases/leakage_gaps')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--inventory', type=Path, help='docker image ls JSON-lines output')
    args = parser.parse_args()
    requests_dir = args.private/'image_requests'
    responses = args.private/'image_responses'
    for path in (requests_dir, responses, args.output/'images'):
        path.mkdir(parents=True, exist_ok=True)
    if args.prepare or not args.collect:
        summary = prepare_requests(args.manifest, requests_dir)
        (args.private/'prepared.json').write_text(json.dumps(summary, indent=2)+'\n')
        print('Prepared private requests:', len(summary))
        print('Base versions known:', sum(row['base_version'] is not None for row in summary))
    if args.prepare:
        return 0
    if args.inventory:
        text = args.inventory.read_text()
    else:
        text = subprocess.check_output(['docker', 'image', 'ls', '--no-trunc', '--format', '{{json .}}'], text=True)
    inventory = [json.loads(line) for line in text.splitlines() if line.strip()]
    images = {r['Repository']+':'+r['Tag']: r['ID'] for r in inventory}
    results = []
    for path in sorted(requests_dir.glob('*.json')):
        request = json.loads(path.read_text())
        iid = request['instance_id']
        tag = image_for(iid)
        if tag not in images:
            result = dict(instance_id=iid, image=tag, status='missing', rule='image-not-local')
        elif args.collect:
            output = responses/(iid+'.json')
            if not output.is_file() or not output.stat().st_size:
                result = dict(instance_id=iid, image=images[tag], status='incomplete', rule='probe-output-missing')
            else:
                result = public_image_result(json.loads(output.read_text()), request, images[tag])
        else:
            result = run_image(images[tag], request)
        (args.output/'images'/(iid+'.json')).write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
        results.append(result)
    summary = dict(cohort=len(results), present=sum(r.get('status') != 'missing' for r in results),
        missing=[r['instance_id'] for r in results if r.get('status') == 'missing'],
        incomplete=[r['instance_id'] for r in results if r.get('status') == 'incomplete' or
                    any(c['status'] != 'complete' for c in r.get('checks', {}).values())])
    (args.output/'image_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))
    return int(bool(summary['incomplete']))


if __name__ == '__main__':
    raise SystemExit(main())
