"""Label-isolated, standard-library bookkeeping for this audit only."""
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUNS = ('main_2_rerun_mpl', 'main_3_rerun_infra', 'main_50_a', 'main_50_b')
FORBIDDEN = ('oracle', 'resolved', 'label', 'grader')


def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()
                if not any(s in k.lower() for s in FORBIDDEN)}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


def tasks():
    return json.loads((ROOT / 'reports/v2_discovery_cleanup/frozen_83/tasks.json').read_text())


def manifest(run):
    with (ROOT / 'manifests' / (run + '.csv')).open(newline='') as f:
        rows = csv.DictReader(f)
        key = next(k for k in ('instance_id', 'task_id', 'id') if k in rows.fieldnames)
        return {r[key] for r in rows}


def selected_records():
    members = {r: manifest(r) for r in RUNS}
    ids = set().union(*members.values())
    result = {}
    for task in sorted(ids):
        directories = [ROOT / 'runs' / r / 'tasks' / task for r in RUNS]
        present = [d for d in directories if d.is_dir()]
        reruns = [d for d in present if d.parts[-3] in RUNS[:2]]
        originals = [d for d in present if d.parts[-3] in RUNS[2:]]
        assert len(reruns) <= 1 and len(originals) <= 1
        directory = (reruns or originals or [None])[0]
        if directory is None:
            continue
        assert task in members[directory.parts[-3]]
        path = directory / 'verification_record.full.json'
        if path.is_file():
            result[task] = (str(path.relative_to(ROOT)), sanitize(json.loads(path.read_text())))
    assert sum(t['instance_id'] not in result for t in tasks()) <= 17
    return result


def groups(records):
    frozen = {t['instance_id'] for t in tasks()}
    return {'frozen83': {k: v for k, v in records.items() if k in frozen},
            'all_tasks': records}


def write_csv(name, rows, fields):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_json(name, value):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def policy_module():
    path = ROOT / 'src/reliability/verifier/decision.py'
    spec = importlib.util.spec_from_file_location('audit_unchanged_decision', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evidence(module, record, regression=None, static=None):
    flags = record['integrity'].get('findings', {})
    return module.Evidence(
        integrity=module.SignalOutcome(record['integrity']['outcome']),
        regression=module.SignalOutcome(regression or record['regression']['outcome']),
        static=module.SignalOutcome(static or record['static']['outcome']),
        reproduction=module.SignalOutcome(record['reproduction']['outcome']),
        high_severity_risk=flags.get('high_severity_risk', False),
        prohibited_manipulation=flags.get('prohibited_manipulation', False),
        patch_applies=flags.get('patch_applies', True),
    )
