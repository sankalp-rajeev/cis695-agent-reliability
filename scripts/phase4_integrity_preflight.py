#!/usr/bin/env python3
"""Audit 83 pristine pinned images: source identity and generated inventory only.

Never applies a candidate, collects tests, executes tests, or reads run outcomes.
"""

from __future__ import annotations

import argparse
import base64
import csv
import difflib
import gzip
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

from reliability.env import clean_env
from reliability.verifier.container import TaskContainer, _docker_bin
from reliability.verifier.source_integrity import (
    BaseSourceSpec,
    GeneratedInputAudit,
    verify_base_source,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FROZEN = Path('/home/sankalp/projects/cis695-agent-reliability/reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z/paired_frozen')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def table(path, rows, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def cause(row):
    if row['accepted_export_subst_difference']:
        return 'PROVEN_EXPORT_SUBST: base Git blob equals image; exact Git archive expansion equals frozen entry'
    if row['reason'] == 'image_differs_from_base_blob':
        return 'Image content differs from declared base Git blob; rejected'
    before = base64.b64decode(row['archive_b64']).decode(errors='replace') if row.get('archive_b64') else ''
    after = base64.b64decode(row['observed_b64']).decode(errors='replace') if row.get('observed_b64') else ''
    if row['path'].endswith(('pyproject.toml', 'setup.cfg')) and 'setuptools==68.0.0' in after and 'setuptools==68.0.0' not in before:
        return 'Image build-time setuptools==68.0.0 configuration pin; not export-subst; rejected without restoration'
    if row.get('base_blob_sha256') == row['observed_sha256']:
        return 'Frozen archive differs from image/base blob without an allowed exact export proof; rejected'
    return row['reason'] or 'unexplained byte difference; rejected'


def main(args):
    assert not args.output.exists(), 'Use a fresh preflight directory'
    args.output.mkdir(parents=True)
    metadata_path = args.frozen/'tasks.json'
    known = json.loads((ROOT/'reports/next_phases/phase3_fix678/base_probes/django/manifest.json').read_text())
    assert sha(metadata_path.read_bytes()) == known['input_sha256'][str(metadata_path)]
    tasks = json.loads(metadata_path.read_text())
    assert len(tasks) == len({t['instance_id'] for t in tasks}) == 83
    started = time.monotonic()
    rows, differences, exports, generated = [], [], [], []

    class PristineContainer(TaskContainer):
        def run_args(self):
            argv = super().run_args()
            argv.insert(2, '--pull=never')
            return argv

    for index, task in enumerate(sorted(tasks, key=lambda t:t['instance_id']), 1):
        iid = task['instance_id']
        print(json.dumps({'event':'pristine_preflight_start','index':index,'total':83,'task':iid}), flush=True)
        folder = args.output/'tasks'/iid
        folder.mkdir(parents=True)
        row = {'task':iid,'repo':task['repo'],'status':'PROBE_ERROR','checked_source_files':0,
               'raw_differences':0,'accepted_export_differences':0,'unresolved_mismatches':0,
               'generated_version_modules':0,'generated_flags':'','error':''}
        try:
            image_id = task['image_binding']['host_image_id']
            assert image_id.startswith('sha256:')
            spec = BaseSourceSpec(task['base_commit'], args.archives/(iid+'.tar'), task['base_archive_sha256'])
            # No source_spec here: gather all mismatches instead of halting
            # the audit. Production start(source_spec=...) uses halt=True.
            with PristineContainer(iid, '', image=image_id, experiment_id='phase4_fix9_pristine_audit') as container:
                proc = subprocess.run([_docker_bin(),'inspect','--format','{{json .}}',container.name],
                                      env=clean_env(),capture_output=True,text=True,check=True)
                info = json.loads(proc.stdout)
                assert info['Image'] == image_id
                assert info['HostConfig']['NetworkMode'] == 'none'
                assert info['HostConfig']['CpuShares'] == 2048
                assert not container._patch_applied
                audit = GeneratedInputAudit(container.generated_snapshot)
                source = audit.stage('pristine_source_guard', lambda container=container, spec=spec:verify_base_source(container,spec,halt=False))
                assert not container._patch_applied
                write(folder/'generated_inputs.json', audit.to_dict())
                payload = (json.dumps(source, indent=2)+'\n').encode()
                (folder/'source_receipt.json.gz').write_bytes(gzip.compress(payload,mtime=0))
                write(folder/'identity.json',{'image_id':image_id,'image_tag_metadata':task['image_tag'],
                      'base_commit':task['base_commit'],'archive_sha256':task['base_archive_sha256'],
                      'container_argv':container.run_args(),'patch_applied':False,
                      'tests_executed':0,'collection_performed':False})
                raw = [r for r in source['files'] if r['archive_sha256'] != r['observed_sha256']]
                for item in raw:
                    differences.append({'task':iid,'repo':task['repo'],'path':item['path'],
                        'archive_sha256':item['archive_sha256'],'image_sha256':item['observed_sha256'],
                        'base_blob_sha256':item.get('base_blob_sha256',''),
                        'accepted_export_subst':item['accepted_export_subst_difference'],
                        'reason':item['reason'],'cause':cause(item)})
                    if item.get('archive_b64') and item.get('observed_b64'):
                        before = base64.b64decode(item['archive_b64']).decode(errors='replace')
                        after = base64.b64decode(item['observed_b64']).decode(errors='replace')
                        diff = ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='archive/'+item['path'],tofile='image/'+item['path']))
                        write(folder/('diff_'+sha(item['path'].encode())[:12]+'.json'),{'path':item['path'],'diff':diff})
                for path in source['export_subst_files']:
                    exports.append({'task':iid,'repo':task['repo'],'path':path})
                inventory = audit.snapshots[0]['files'] if audit.snapshots else {}
                for path, digest in inventory.items():
                    generated.append({'task':iid,'repo':task['repo'],'path':path,'sha256':digest})
                row.update(status=source['status'],checked_source_files=source['checked_files'],
                           raw_differences=len(raw),accepted_export_differences=len(source['accepted_export_subst_differences']),
                           unresolved_mismatches=len(source['mismatches']),generated_version_modules=len(inventory),
                           generated_flags=';'.join(audit.flags))
        except Exception as exc:  # noqa: BLE001
            row['error'] = repr(exc)
            write(folder/'probe_error.json',{'error':repr(exc),'tests_executed':0,'collection_performed':False})
        rows.append(row)
        write(folder/'summary.json',row)
        print(json.dumps({'event':'pristine_preflight_end',**row}),flush=True)
    table(args.output/'tasks.csv',rows,list(rows[0]))
    table(args.output/'differences.csv',differences,['task','repo','path','archive_sha256','image_sha256','base_blob_sha256','accepted_export_subst','reason','cause'])
    table(args.output/'export_subst_files.csv',exports,['task','repo','path'])
    table(args.output/'generated_inventory.csv',generated,['task','repo','path','sha256'])
    write(args.output/'summary.json',{'tasks':83,'statuses':dict(Counter(r['status'] for r in rows)),
          'tasks_with_any_raw_difference':[r['task'] for r in rows if r['raw_differences']],
          'tasks_with_unresolved_mismatches':[r['task'] for r in rows if r['unresolved_mismatches']],
          'export_subst_repositories':sorted({r['repo'] for r in exports}),
          'generated_version_modules':len(generated),'wall_s':time.monotonic()-started,
          'tests_executed':0,'collection_performed':False,'patches_applied':0,
          'attempt1_outcomes_read':False,'correctness_labels_read':False})
    write(args.output/'manifest.json',{'executor_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'source_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__).resolve(),*sorted((ROOT/'src/reliability/verifier').glob('*.py'))]},
          'frozen_tasks_sha256':sha(metadata_path.read_bytes()),
          'receipt_sha256':{str(p.relative_to(args.output)):sha(p.read_bytes()) for p in sorted(args.output.rglob('*')) if p.is_file() and p.name!='manifest.json'}})
    print(json.dumps(json.loads((args.output/'summary.json').read_text()),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',type=Path,default=DEFAULT_FROZEN)
    parser.add_argument('--archives',type=Path,default=Path('/home/sankalp/cg_repos/task_archives'))
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
