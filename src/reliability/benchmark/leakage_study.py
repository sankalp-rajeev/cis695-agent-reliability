"""Extended historical audit with a multiset golden comparison; oracle access.

Only the explicitly named main-study roots and agent-visible allowlist are read.
Never reads grader records, correctness labels, or verdict files.
"""
from __future__ import annotations

import collections
import json
import subprocess
import sys
import types
from pathlib import Path

from reliability.benchmark.image_leakage import archive_for, base_version
from reliability.benchmark.leakage import (
    _test_symbol,
    audit_task,
    find_task_dirs,
    probes_from_oracle,
    without_base_lines,
)
from reliability.benchmark.leakage_rules import (
    AuditContext,
    definition_events,
    digest,
    symbols_at_base,
)

STUDY_ROOT = Path('/home/sankalp/projects/cis695-agent-reliability/runs')
STUDY_RUNS = ('main_50_a', 'main_50_b', 'main_2_rerun_mpl', 'main_3_rerun_infra')


def legacy_module():
    """Load immutable pre-change implementation, only inside the audit boundary."""
    text = subprocess.check_output(['git', 'show', '7fefe1d:src/reliability/benchmark/leakage.py'], text=True)
    name = '_leakage_gaps_legacy'
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(text, '7fefe1d:leakage.py', 'exec'), module.__dict__)
    return module


def safe_finding(finding):
    return dict(severity=finding.severity.value, kind=finding.kind, path=finding.path,
                line_no=finding.line_no, rule=getattr(finding, 'rule', 'legacy'),
                evidence=getattr(finding, 'evidence', {}))


def key(finding):
    return finding['path'], finding['kind'], finding['line_no']


def compare_golden(old, new):
    """Every legacy occurrence survives, except supported rule-3 downgrades.

    Matching is a multiset by artifact/kind/line. Detail strings may contain gold
    in the legacy implementation and are deliberately never serialized.
    """
    available = collections.defaultdict(list)
    for f in new:
        available[key(f)].append(f)
    downgrades, changes, preserved = [], [], 0
    for f in old:
        candidates = available[key(f)]
        same = next((n for n in candidates if n['severity'] == f['severity']), None)
        if same is not None:
            candidates.remove(same); preserved += 1
            continue
        lower = next((n for n in candidates if n['severity'] == 'review' and
                      n['rule'] in {'test-name-present-at-base', 'test-name-agent-defined-before-output'}), None)
        if lower and f['severity'] == 'confirmed':
            candidates.remove(lower)
            downgrades.append(dict(before=f, after=lower))
        elif f['kind'] == 'fail-to-pass-name' and candidates:
            # Rule 3 resolves an old REVIEW into CONFIRMED. Keep the old REVIEW
            # occurrence and add the stronger ordered-source evidence separately.
            changes.append(dict(before=f, reason='legacy-review-not-preserved'))
        else:
            changes.append(dict(before=f, reason='legacy-finding-missing-or-changed'))
    return dict(legacy_count=len(old), preserved=preserved, downgrades=downgrades,
                violations=changes, additions=sum(len(v) for v in available.values()))


def build_context(task, oracle, archive, pin, image, task_dir=None):
    probes = probes_from_oracle(oracle, task.problem_statement)
    symbols = {_test_symbol(n) for n in probes.fail_to_pass + probes.pass_to_pass} - {''}
    context = AuditContext(task.base_commit, task.repo.split('/')[-1],
                           image.get('base_version') or base_version(archive, task.repo.split('/')[-1].replace('-', '_')),
                           archive=pin, base_symbols=symbols_at_base(archive, symbols))
    context.base_paths = frozenset(archive.members) | frozenset(
        str(parent) for name in archive.members for parent in Path(name).parents)
    git = image.get('checks', {}).get('git', {})
    if git.get('status') == 'complete':
        result = git['result']
        context.base_timestamp = result['base_timestamp']
        context.commit_timestamps = result['commit_timestamps']
    return probes, context, symbols


def run_study(output, *, run_roots=None, image_root=None):
    from reliability.benchmark.leakage import import_name_for_instance
    from reliability.benchmark.loader import load_instance, load_verified
    dataset = load_verified()
    legacy = legacy_module()
    run_roots = run_roots or [STUDY_ROOT/r for r in STUDY_RUNS]
    task_dirs = sorted({p for root in run_roots for p in find_task_dirs(root)})
    if not task_dirs:
        raise ValueError('empty study scope')
    image_root = image_root or output/'images'
    cache, per_task, all_old, all_new, downgrades = {}, [], [], [], []
    for directory in task_dirs:
        iid = directory.name
        if iid not in cache:
            task, oracle = load_instance(iid, dataset)
            archive, pin = archive_for(task)
            image_path = image_root/(iid+'.json')
            image = json.loads(image_path.read_text()) if image_path.is_file() else {}
            probes, context, symbols = build_context(task, oracle, archive, pin, image)
            context.base_version = image.get('base_version') or base_version(archive, import_name_for_instance(iid))
            reduction = image.get('checks', {}).get('base_probes', {})
            if reduction.get('status') != 'complete':
                raise ValueError('legacy base subtraction missing: ' + iid)
            present = {p for p in probes.patch_lines + probes.test_patch_lines
                       if digest(p) in reduction['result']}
            probes = without_base_lines(probes, present)
            # Legacy did not scan PASS_TO_PASS. Its raw test-symbol parser is
            # retained independently by the golden module.
            old_probes = legacy.OracleProbes(instance_id=iid, patch_lines=probes.patch_lines,
                test_patch_lines=probes.test_patch_lines, fail_to_pass=probes.fail_to_pass,
                hints_lines=probes.hints_lines)
            cache[iid] = probes, old_probes, context, symbols
        probes, old_probes, context, symbols = cache[iid]
        context.definitions = definition_events(directory, symbols)
        old, _ = legacy.audit_task(directory, old_probes)
        new, scanned = audit_task(directory, probes, context=context)
        # An old REVIEW is preserved even when rule 3 adds stronger evidence.
        # Give it its own explicit rule so no golden finding silently vanishes.
        old_safe = [safe_finding(f) for f in old]
        new_safe = [safe_finding(f) for f in new]
        available_reviews = collections.Counter((key(n), n['severity']) for n in new_safe)
        for finding in old_safe:
            identity = key(finding), finding['severity']
            if finding['kind'] == 'fail-to-pass-name':
                if available_reviews[identity]:
                    available_reviews[identity] -= 1
                else:
                    new_safe.append(dict(finding, rule='legacy-review-retained'))
        golden = compare_golden(old_safe, new_safe)
        # Store only safe finding metadata and hashed symbols. The verifier
        # derives all symbol hashes itself by tokenizing the base archive.
        result = dict(instance_id=iid, run=directory.parent.parent.name,
            role='generator' if directory.parent.name == '_reproduction_cache' else 'repair',
            source=str(directory), archive=context.archive, scanned_files=scanned,
            findings=new_safe, legacy_findings=old_safe, golden=golden)
        per_task.append(result); all_old.extend(old_safe); all_new.extend(new_safe)
        downgrades.extend(golden['downgrades'])
        path = output/'tasks'/result['run']/result['role']/(iid+'.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    totals = dict(task_directories=len(per_task), unique_tasks=len(cache),
        repair_directories=sum(r['role'] == 'repair' for r in per_task),
        generator_directories=sum(r['role'] == 'generator' for r in per_task),
        scanned_files=sum(r['scanned_files'] for r in per_task),
        findings=len(all_new), severity=dict(collections.Counter(f['severity'] for f in all_new)),
        rules=dict(collections.Counter(f['rule'] for f in all_new)),
        legacy_findings=len(all_old), downgrades=len(downgrades),
        golden_violations=sum(len(r['golden']['violations']) for r in per_task),
        awareness_tasks=len({r['instance_id'] for r in per_task if any(
            f['severity'] == 'benchmark-awareness' for f in r['findings'])}),
        confirmed_tasks=sorted({r['instance_id'] for r in per_task if any(
            f['severity'] == 'confirmed' for f in r['findings'])}))
    (output/'trajectory_summary.json').write_text(json.dumps(totals, indent=2, sort_keys=True)+'\n')
    (output/'downgrades.json').write_text(json.dumps(downgrades, indent=2, sort_keys=True)+'\n')
    return totals


def extended_inputs(task_dirs, image_root):
    """Shared default audit inputs for future runs, requiring complete image proof."""
    from reliability.benchmark.loader import load_instance, load_verified
    dataset = load_verified()
    probes_by_id, contexts = {}, {}
    for iid in sorted({d.name for d in task_dirs}):
        task, oracle = load_instance(iid, dataset)
        archive, pin = archive_for(task)
        image = json.loads((image_root/(iid+'.json')).read_text())
        if any(image.get('checks', {}).get(c, {}).get('status') != 'complete'
               for c in ['git', 'base_probes', 'packages']):
            raise ValueError('image proof incomplete: ' + iid)
        if image['base_commit'] != task.base_commit:
            raise ValueError('image proof base mismatch')
        probes, context, symbols = build_context(task, oracle, archive, pin, image)
        present_hashes = set(image['checks']['base_probes']['result'])
        present = {p for p in probes.patch_lines + probes.test_patch_lines if digest(p) in present_hashes}
        probes_by_id[iid] = without_base_lines(probes, present)
        for directory in task_dirs:
            if directory.name == iid:
                context.definitions.update(definition_events(directory, symbols))
        contexts[iid] = context
    return probes_by_id, contexts


def check_fetch_versions(output):
    """Verify image-version fallback does not change stored install findings."""
    from reliability.benchmark.leakage import TRAJECTORY_FILES
    from reliability.benchmark.leakage_rules import scan_commands
    checked, changed = 0, []
    for path in sorted((output/'tasks').glob('*/*/*.json')):
        row = json.loads(path.read_text())
        if not any(f['rule'] in {'fetch-pip-install', 'fetch-conda', 'fetch-easy-install'} for f in row['findings']):
            continue
        image = json.loads((output/'images'/(row['instance_id']+'.json')).read_text())
        package = row['instance_id'].split('__')[1].rsplit('-', 1)[0]
        context = AuditContext(image['base_commit'], package, image.get('base_version'))
        for name in TRAJECTORY_FILES:
            trajectory = Path(row['source'])/name
            if not trajectory.is_file():
                continue
            current = [safe_finding(f) for f in scan_commands(trajectory,
                trajectory.read_text(errors='replace'), None, context) if f.kind == 'fetch-fixed-version']
            previous = [f for f in row['findings'] if f['kind']=='fetch-fixed-version' and f['path']==str(trajectory)]
            if current != previous:
                changed.append(dict(instance_id=row['instance_id'], run=row['run'], role=row['role']))
            checked += 1
    return dict(install_trajectories_rechecked=checked, changes=changed)
