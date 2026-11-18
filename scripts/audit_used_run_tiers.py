"""Read frozen study provenance and publish split tiers for the patches used."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from verify_leakage_gaps import (
    FOLLOWUP_TIERS,
    SUPERSEDED_COLUMNS,
    USED_COLUMNS,
    read,
    resolve_repair_run,
    used_run_tables,
)

REPO = Path(__file__).resolve().parents[1]
STUDY = Path('/home/sankalp/projects/cis695-agent-reliability')
RUNS = ('main_50_a', 'main_2_rerun_mpl', 'main_50_b', 'main_3_rerun_infra')
FROZEN = (STUDY / 'reports/v2_scg_integration/ubuntu_static_b030e50_20261105T172604_853449Z'
          / 'paired_frozen/tasks.json')
MASK_COMMITS = {
    'conda': '8d0f57aa71a8f7b3431a8defa5b535da9d3f6504',
    'pip': 'b7f0a0e51b24a272a88692ef997ee091feea8eb9',
}
MASK_PATHS = {'conda': '/opt/miniconda3/pkgs', 'pip': '/root/.cache/pip'}
BRANCH_SNAPSHOT = '9654fc7c4168da0ff0c1bdf786f99a8a38d0c006'
AUDIT_BASELINE = 'b759bdb'


def file_sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sha256_field(value):
    value = (value or '').removeprefix('sha256:')
    if not re.fullmatch(r'[a-f0-9]{64}', value):
        raise ValueError('invalid provenance digest')
    return value


def collect_provenance(frozen_manifest, records):
    """Project run, patch and suite provenance. Never read decision or outcome fields."""
    if frozen_manifest != FROZEN:
        raise ValueError('unexpected historical frozen manifest path')
    tasks = {}
    for row in read(frozen_manifest):
        iid = row['instance_id']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+', iid) or iid in tasks:
            raise ValueError('invalid frozen task identity')
        source_run = row.get('source_run')
        patch = sha256_field(row['patch_sha256'])
        candidates = {}
        for run in RUNS:
            path = STUDY / 'runs' / run / 'tasks' / iid / 'patch.diff'
            if path.is_file():
                candidates[run] = file_sha256(path)
        repair, _ = resolve_repair_run(source_run, patch, candidates)
        directory = STUDY / 'runs' / repair / 'tasks' / iid
        signal_proofs = {}
        for name in ('verification_record.baseline.json', 'verification_record.full.json'):
            path = directory / name
            if path.is_file():
                record = read(path)
                suite = record.get('reproduction', {}).get('findings', {}).get('suite_sha256')
                signal_proofs[name] = {
                    'patch_sha256': sha256_field(record['patch_sha256']),
                    'suite_sha256': sha256_field(suite) if suite else None,
                }
        suites = {}
        for run in RUNS:
            path = STUDY / 'runs' / run / '_reproduction_cache' / iid / 'frozen.json'
            if path.is_file():
                suites[run] = sha256_field(read(path)['suite_sha256'])
        tasks[iid] = {
            'source_run': source_run, 'patch_sha256': patch, 'repair_patch_sha256s': candidates,
            'reproduction_record_provenance': signal_proofs, 'v4_suite_sha256s': suites,
        }

    inputs = {record['instance_id'] for record in records if record['comparable']}
    if tasks.keys() != inputs:
        raise ValueError('frozen provenance and audit cohort differ')
    return {'frozen_manifest': str(frozen_manifest), 'frozen_manifest_sha256': file_sha256(frozen_manifest),
            'tasks': tasks}


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()


def collect_timeline(observations):
    """Bind each run's config masks to its recorded revision and UTC start time."""
    main_history = set(git('rev-list', '--first-parent', AUDIT_BASELINE).splitlines())
    branch_history = set(git('rev-list', '--first-parent', BRANCH_SNAPSHOT).splitlines())
    changes = {}
    for cache, commit in MASK_COMMITS.items():
        parents, committed = git('show', '-s', '--format=%P%n%cI', commit).splitlines()
        changes[cache] = dict(commit=commit, parent_commits=parents.split(),
                              committed_utc=datetime.fromisoformat(committed).astimezone(UTC).isoformat(),
                              on_audit_first_parent=commit in main_history,
                              on_fix_branch_first_parent=commit in branch_history)
    runs = {}
    for run in RUNS:
        path = STUDY / 'runs' / run / 'meta.yaml'
        meta = path.read_text()

        def field(name):
            match = re.search(r'^' + name + r':\s*([^\n]+)$', meta, re.M)
            if not match:
                raise ValueError('missing run metadata field: ' + name)
            return match.group(1).strip("'\" ")

        revision = field('git_commit')
        if not re.fullmatch(r'[a-f0-9]{40}', revision) or field('git_dirty') != 'false':
            raise ValueError('run configuration revision is unpinned')
        started = datetime.fromisoformat(field('timestamp_utc')).astimezone(UTC)
        ancestors = set(git('rev-list', revision).splitlines())
        configs = {}
        for role, name in (('repair', 'swebench_claim'), ('generator', 'v4_generator')):
            content = git('show', f'{revision}:configs/agent/{name}.yaml')
            masks = re.findall(r'^\s*- --tmpfs\s*\n\s*- (/[^\s:]+)', content, re.M)
            configs[role] = {cache: mask in masks for cache, mask in MASK_PATHS.items()}
            for cache, enabled in configs[role].items():
                if enabled != (MASK_COMMITS[cache] in ancestors):
                    raise ValueError('recorded run mask disagrees with revision ancestry')
                committed = datetime.fromisoformat(changes[cache]['committed_utc'])
                if enabled != (started >= committed):
                    raise ValueError('recorded run start disagrees with mask chronology')
        runs[run] = dict(started_utc=started.isoformat(), git_commit=revision,
                         masks_by_role=configs, observed_cache=observations[run])
    return dict(fix_branch='fix/pkg-cache-mask', fix_branch_snapshot=BRANCH_SNAPSHOT,
                mask_commits=changes, runs=runs)


def report_section(summary, timeline):
    used = summary['used_comparable']
    t4 = used['any_role']['T4']
    names = used['highest_tier']['T3-name']
    both = names + used['highest_tier']['T3-content'] + used['highest_tier']['T4']
    first = timeline['runs']['main_50_a']['observed_cache']
    lines = [
        '## Interpreted verdict for the frozen Phase 4 runs', '',
        '**(a) Environment.** The image Git audit found 0 distinctive gold added lines in '
        'post-base history and 0 of 120 exact gold blobs. Different-version package copies '
        'occurred only in the 7 excluded requests images. Stored cache exposure was confined '
        'to `main_50_a`, before the pip mask. '
        f'{len(first["nonempty_return_tasks"])} tasks had {first["nonempty_return_observations"]} '
        f'nonempty source or filename observations, including {len(first["returned_source_tasks"])} tasks '
        'that returned source content.', '',
        f'**(b) Used runs.** {len(t4)} of {summary["comparable_count"]} comparable tasks reached T4 '
        'in the repair or V4 run linked to the frozen patch. '
        'The historical T4 for `matplotlib__matplotlib-20676` came from `main_50_a`. '
        'Its frozen repair patch and V4 signal resolve to `main_2_rerun_mpl`. '
        '`matplotlib__matplotlib-21568` is outside the frozen comparable cohort.', '',
        f'**(c) Memory indicators.** {names} of {summary["comparable_count"]} comparable tasks '
        'were T3-name as their highest tier in the used runs. '
        f'{used["highest_tier"]["T3-content"]} were T3-content, consistent with solving or memory. '
        f'{both} reached T3 or T4 in total.', '',
        'T3-name takes precedence over T3-content when both occur. The counts below '
        'use the used run or the highest tier across runs for each task and role. '
        'Observed counts give the number of tasks with a trajectory for that row. '
        'Nine V4 tasks in the 93-task scope have no stored trajectory and are omitted '
        'from its tier counts. Both 83-task role tables have full coverage.', '',
        '| Scope | Role | T0 | T1 | T2 | T3-content | T3-name | T4 | Observed |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for scope, label in (('used_comparable', 'Used runs (83)'),
                         ('all_runs_comparable', 'All runs (83)'),
                         ('all_runs_non_requests', 'All runs (93)')):
        for role, name in (('repair', 'Repair'), ('generator', 'V4')):
            row = summary[scope][role]
            counts = ' | '.join(str(row['counts'][tier]) for tier in FOLLOWUP_TIERS)
            lines.append(f'| {label} | {name} | {counts} | {row["observed_tasks"]} |')
    lines += [
        '', 'Phase 4 provenance names the source run directly for 79 patches and uses '
        '`rerun` for 4. All 83 frozen patch hashes match stored patch bytes. '
        'All 83 V4 signals in the patch-matched verification records have a unique '
        'frozen-suite hash match with an observed generator trajectory. '
        '[Used-run tiers](tiers/used_run_tiers.csv) and '
        '[superseded-run tiers](tiers/superseded_run_tiers.csv) list the role-specific results.', '',
        '### Cache-mask timeline', '',
        'The two mask changes entered the first-parent history of the reviewed '
        '`fix/pkg-cache-mask` snapshot and the audit baseline as single-parent commits. '
        'Each run’s recorded revision and its repair and V4 configuration establish mask coverage.', '',
    ]
    for cache, change in timeline['mask_commits'].items():
        lines.append(f'- {cache.capitalize()} mask landed at `{change["commit"]}` on '
                     f'{change["committed_utc"]} (UTC).')
    lines += ['', '| Run | Recorded start (UTC) | Revision | Conda mask | Pip mask | Cache observations |',
              '|---|---|---|---|---|---|']
    for run, row in timeline['runs'].items():
        masks = row['masks_by_role']['repair']
        evidence = {
            'main_50_a': f'{first["nonempty_return_observations"]} nonempty pip observations',
            'main_50_b': 'Empty listings for both masks from one command',
            'main_2_rerun_mpl': 'No cache-read receipts',
            'main_3_rerun_infra': 'No cache-read receipts',
        }[run]
        conda, pip = ['yes' if masks[x] else 'no' for x in ('conda', 'pip')]
        lines.append(f'| `{run}` | {row["started_utc"]} | `{row["git_commit"][:12]}` | '
                     f'{conda} | {pip} | {evidence} |')
    lines += [
        '', '| Cache evidence | Tasks |', '|---|---|',
        '| Source content returned | ' + ', '.join(first['returned_source_tasks']) + ' |',
        '| Any nonempty source or filename observation | ' +
        ', '.join(first['nonempty_return_tasks']) + ' |', '',
        'Counts use the accepted cache receipts. The mask states come from the recorded '
        'code revisions. Post-fix observations contain no nonempty cache source or filenames.', '',
        '<!-- used-run-totals-json: ' + json.dumps(summary, sort_keys=True) + ' -->', '',
    ]
    return '\n'.join(lines)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, default=REPO / 'reports/next_phases/leakage_gaps')
    root = parser.parse_args().report_dir
    tiers = root / 'tiers'
    records = [read(p) for p in sorted((tiers / 'artifacts').glob('*/*/*.json'))]
    provenance = collect_provenance(FROZEN, records)
    used, superseded, summary = used_run_tables(records, provenance['tasks'])
    timeline = collect_timeline(summary['cache_observations'])
    for name, rows, columns in (
        ('used_run_tiers.csv', used, USED_COLUMNS),
        ('superseded_run_tiers.csv', superseded, SUPERSEDED_COLUMNS),
    ):
        with (tiers / name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    write_json(tiers / 'used_run_provenance.json', provenance)
    write_json(tiers / 'used_run_summary.json', summary)
    write_json(tiers / 'cache_mask_timeline.json', timeline)
    report = root / 'REPORT.md'
    prior = report.read_text()
    old_headline = '## Interpreted verdict\n'
    max_headline = '## Max-over-runs view\n'
    if max_headline in prior:
        _, body = prior.split(max_headline, 1)
    else:
        _, body = prior.split(old_headline, 1)
    report.write_text('# Leakage gaps audit\n\n' + report_section(summary, timeline) + '\n' + max_headline + body)
    print(json.dumps({'used_tasks': len(used), 'superseded_rows': len(superseded),
                      'used_highest_tiers': summary['used_comparable']['highest_tier']}, sort_keys=True))


if __name__ == '__main__':
    main()
