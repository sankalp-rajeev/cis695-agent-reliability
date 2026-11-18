"""Reusable raw-plus-interpretive rerun audit; no launch, Docker or model calls."""
from __future__ import annotations

import json
from pathlib import Path

from reliability.benchmark.leakage import audit_task
from reliability.benchmark.leakage_interpretation import (
    complete_records,
    file_hash,
    interpret_record,
    load_inputs,
    write_tiers,
)
from reliability.benchmark.leakage_rules import AuditContext, definition_events, symbols_at_base
from reliability.benchmark.leakage_study import safe_finding


def discover_arm(run):
    """Explicit agent/generator layouts; never recursively scan other outputs."""
    tasks = run / 'tasks'
    found = {}
    for path in sorted(tasks.glob('*/trajectory.jsonl')):
        found[(path.parent.name, 'repair')] = path.parent

    generator_layouts = (
        (run / '_reproduction_cache', '*/generation_trajectory.jsonl'),
        (tasks, '*/generation_trajectory.jsonl'),
        (tasks, '*/verification/v4/cache/*/generation_trajectory.jsonl'),
    )
    for root, pattern in generator_layouts:
        for path in sorted(root.glob(pattern)):
            iid = path.parent.name
            if iid != path.relative_to(root).parts[0]:
                raise ValueError('generator-cache-id-mismatch')
            key = (iid, 'generator')
            if key in found:
                raise ValueError('duplicate-generator-layout')
            found[key] = path.parent
    return [(iid, role, path) for (iid, role), path in sorted(found.items())]


def audit_arm(run, output, image_root, *, input_provider=None):
    """input_provider exists for wholly synthetic tests; CLI always uses real proof."""
    run,output,image_root=Path(run),Path(output),Path(image_root)
    task_dirs=discover_arm(run)
    if not task_dirs:
        raise ValueError('empty-rerun-trajectory-scope')
    if output == run or output in run.parents:
        raise ValueError('audit-output-overlaps-run-root')
    records=[]; inputs_by_id={}
    for iid,role,directory in task_dirs:
        if iid not in inputs_by_id:
            inputs_by_id[iid]=(input_provider(iid) if input_provider else load_inputs(iid,None,image_root))
        inputs=inputs_by_id[iid]
        from reliability.benchmark.leakage import _test_symbol
        symbols={_test_symbol(n) for n in inputs.probes.fail_to_pass+inputs.probes.pass_to_pass}-{''}
        context=AuditContext(inputs.pin['base_commit'],iid.split('__')[-1].rsplit('-',1)[0],
            inputs.image.get('base_version'),base_symbols=symbols_at_base(inputs.archive,symbols),
            archive=inputs.pin,definitions=definition_events(directory,symbols))
        context.base_paths=frozenset(inputs.archive.members)|frozenset(str(p) for name in inputs.archive.members for p in Path(name).parents)
        git=inputs.image.get('checks',{}).get('git',{}).get('result',{})
        context.base_timestamp=git.get('base_timestamp')
        context.commit_timestamps=git.get('commit_timestamps',{})
        # A directory can carry both roles; audit only the chosen trajectory.
        # Non-trajectory final artifacts remain in scope under the raw allowlist.
        target='trajectory.jsonl' if role=='repair' else 'generation_trajectory.jsonl'
        findings,scanned=audit_task(directory,inputs.probes,context=context,trajectory_names=(target,))
        raw=dict(instance_id=iid,run=run.name,role=role,source=str(directory.resolve()),
                 archive=inputs.pin,scanned_files=scanned,findings=[safe_finding(f) for f in findings],
                 legacy_findings=[],golden={'downgrades':[],'violations':[]})
        raw_path=Path('tasks')/run.name/role/(iid+'.json')
        destination=output/raw_path; destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
        record=interpret_record(raw,inputs)
        record.update(raw_path=raw_path.as_posix(),raw_file_sha256=file_hash(destination))
        records.append(record)
    comparable={iid for iid,i in inputs_by_id.items() if i.comparable}
    records=complete_records(records,comparable)
    summary=write_tiers(output/'tiers',records,sorted(inputs_by_id),comparable)
    (output/'tiers/history_gold_checks.json').write_text(json.dumps([
        dict(instance_id=r['instance_id'],run=r['run'],role=r['role'],**h)
        for r in records for h in r['history_gold']],indent=2,sort_keys=True)+'\n')
    (output/'audit_scope.json').write_text(json.dumps(dict(run=str(run.resolve()),
        source_trajectories=len(task_dirs),source_modified=False,model_calls=0,docker_calls=0),indent=2)+'\n')
    return summary
