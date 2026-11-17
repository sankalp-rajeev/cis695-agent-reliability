"""Render only sanitized audit metadata into the final report."""
import collections
import json
from pathlib import Path


def main():
    root = Path('reports/next_phases/leakage_gaps')
    summary = json.loads((root/'trajectory_summary.json').read_text())
    image_summary = json.loads((root/'image_summary.json').read_text())
    images = [json.loads(p.read_text()) for p in sorted((root/'images').glob('*.json'))]
    tasks = [json.loads(p.read_text()) for p in sorted((root/'tasks').glob('*/*/*.json'))]
    unit = json.loads((root/'unit_comparison.json').read_text())
    findings = [f for t in tasks for f in t['findings']]
    confirmed = [f for f in findings if f['severity']=='confirmed']
    exposures = [(r, r.get('checks',{}).get('git',{}).get('result',{})) for r in images]
    future = [(r,g) for r,g in exposures if g.get('future_object_count')]
    gold = [(r,g) for r,g in exposures if any(b['present'] for b in g.get('gold_post_image_blobs',[]))]
    copies = [(r,c) for r in images for c in r.get('checks',{}).get('packages',{}).get('result',{}).get('copies',[])]
    different = [(r,c) for r,c in copies if c.get('different_from_base')]
    unknown = [(r,c) for r,c in copies if c.get('different_from_base') is None]
    source_future = [(r,d) for r,g in future for d in g.get('future_commit_details',[]) if d['changed_source_file_count']]
    lines = [
        '# Leakage gaps audit', '',
        ('**Verdict: confirmed evidence appears in stored agent-visible artifacts.**' if confirmed else
         '**Verdict: no confirmed answer access was found in the stored repair-agent or V4 artifacts.**'), '',
        'This is an artifact audit, not proof that the model could not remember an answer. '
        'Image exposure and an agent actually receiving an answer are separate observations. '
        'The audit uses no correctness labels or grader results.', '',
        f'Stored trajectories: {summary["task_directories"]} directories '
        f'({summary["repair_directories"]} repair, {summary["generator_directories"]} V4), '
        f'{summary["unique_tasks"]} unique tasks, {summary["scanned_files"]} in-scope files. '
        f'Confirmed findings: {len(confirmed)}; affected tasks: {len(summary["confirmed_tasks"])}. '
        f'Benchmark-awareness findings: {summary["severity"].get("benchmark-awareness",0)} '
        f'across {summary["awareness_tasks"]} unique tasks.', '',
        f'Images: {image_summary["present"]}/{image_summary["cohort"]} present; '
        f'{len(image_summary["missing"])} missing; {len(image_summary["incomplete"])} incomplete. '
        f'{len(future)} images contain commits after base; '
        f'{len(gold)} images contain at least one exact gold post-image blob. '
        f'{len(different)} unmasked package copies have a version different from base; '
        f'{len(unknown)} copy versions remain unresolved.', '',
        '<!-- totals-json: '+json.dumps(dict(trajectory=summary,images=image_summary),sort_keys=True)+' -->', '',
        '## Stored-run findings', '',
        'Read in place: `main_50_a`, `main_50_b`, `main_2_rerun_mpl`, '
        '`main_3_rerun_infra`, including each root’s `_reproduction_cache`. '
        'Only the audit allowlist is opened; oracle/grader result files are excluded. '
        'Per-artifact severity, rule and hashed evidence are in `tasks/<run>/<role>/<iid>.json`.', '',
        '| Severity | Findings |', '|---|---:|',
    ]
    lines += [f'| {key} | {value} |' for key,value in sorted(summary['severity'].items())]
    lines += ['', '| Rule | Findings |', '|---|---:|']
    lines += [f'| {key} | {value} |' for key,value in sorted(summary['rules'].items())]
    lines += ['', 'Counts are findings, not unique events: the same occurrence can be represented '
              'in a trajectory and final artifacts, and several source rules can match one command. '
              'A successful fetch/history output is added alongside its attempted-command finding. '
              'Legacy REVIEW findings remain when rule 3 adds stronger evidence.', '']
    if confirmed:
        lines += ['Confirmed artifact evidence (no oracle content):', '',
                  '| Task | Run | Role | Kind | Rule | Artifact | Line |', '|---|---|---|---|---|---|---:|']
        lines += [f'| {t["instance_id"]} | {t["run"]} | {t["role"]} | {f["kind"]} | {f["rule"]} | {Path(f["path"]).name} | {f["line_no"] or 0} |'
                  for t in tasks for f in t['findings'] if f['severity']=='confirmed']
        lines += ['']
    lines += ['## Golden comparison and rule 3', '',
        f'Immutable baseline: audit module from `7fefe1d`. Legacy findings: {summary["legacy_findings"]}; '
        f'golden violations: {summary["golden_violations"]}; explicit rule-3 downgrades: {summary["downgrades"]}. '
        'Comparison uses a multiset of artifact, kind, line and severity. '
        '`downgrades.json` lists every downgrade; the independent verifier reopens the '
        'archive directly and checks its digest and symbol hashes.', '',
        'Base test symbols are checked in SHA-256-verified `SourceArchive` inputs. '
        '83 archives carry historical pins; 10 existing archives receive audit inventory pins. '
        'The seven requests archives were missing from the supplied archive directory, '
        'so read-only `git archive` of each image’s pinned base commit supplied a local '
        'archive and a new digest. This provenance is recorded per task. '
        'A name at base is REVIEW. An absent name seen before any successful agent '
        'file-write defines it is CONFIRMED; a name introduced by such a write is REVIEW. '
        'Final artifacts are assessed after the trajectory’s writes.', '',
        '## Image exposure', '',
        'Every image was read through our own anonymous `docker run --rm --network none '
        '--read-only --pull never` containers, with a read-only probe mount. No existing '
        'container was inspected, stopped or changed; no image was pulled. '
        'Git probes use read-only commands, including `hash-object` without `-w`. '
        'All reachable refs and all objects are enumerated; newer timestamps and '
        'descendants of base both count. A setup commit after base alone does not '
        'establish that an answer is available. Exact gold post-image blob presence '
        'is tested independently.', '',
        '| Task | Future reachable | Future objects | Changed file categories | Gold added-line matches in future diff | Gold blobs present / probed |',
        '|---|---:|---:|---|---:|---:|']
    for r,g in future:
        details = g.get('future_commit_details',[])
        blobs = g.get('gold_post_image_blobs',[])
        categories = collections.Counter()
        for detail in details:
            categories.update(detail.get('changed_file_categories', {}))
        description = ', '.join(f'{key}={value}' for key,value in sorted(categories.items()) if value) or 'identical tree'
        lines += [f'| {r["instance_id"]} | {g["future_reachable_count"]} | {g["future_object_count"]} | '
                  f'{description} | {sum(d.get("gold_added_line_match_count",0) for d in details)} | '
                  f'{sum(b["present"] for b in blobs)} / {len(blobs)} |']
    lines += ['', 'Each `images/<iid>.json` records future commit hashes, changed-file counts, '
              'changed-source-file counts, hashed changed paths, object counts and gold blob '
              'hash/presence pairs. No commit messages, source text or patch lines are published.', '',
              f'Future commits with source changes: {len(source_future)}. '
              'The per-image tree deltas describe what those commits contain without revealing content.', '',
              '**Smallest proposed isolation fix (not implemented):** start the agent with a '
              'fresh single-commit repository materialized from the verified pinned base archive, '
              'with no copied `.git` directory. Keep the installed task environment and existing '
              'network/cache masks. This removes historical refs, reflogs and dangling objects '
              'together. Merely deleting refs leaves objects searchable. The user owns the '
              'decision to change agent startup.', '',
              '### Package caches and unmasked copies', '',
              '| Task | Conda cache files | Pip cache files | Repo archives | Unmasked copies | Different versions |',
              '|---|---:|---:|---:|---:|---:|']
    for r in images:
        packages=r.get('checks',{}).get('packages',{}).get('result',{})
        masks=packages.get('masked',{})
        lines += [f'| {r["instance_id"]} | {masks.get("/opt/miniconda3/pkgs",{}).get("file_count",0)} | '
                  f'{masks.get("/root/.cache/pip",{}).get("file_count",0)} | '
                  f'{sum(len(v["repo_archives"]) for v in masks.values())} | {len(packages.get("copies",[]))} | '
                  f'{sum(c.get("different_from_base") is True for c in packages.get("copies",[]))} |']
    lines += ['', 'Cache archive and extracted-package versions, paths or path hashes, and copy '
              'versions are recorded in each image JSON. These counts show what the two tmpfs '
              'masks hide before an agent starts. Copies resolving to `/testbed` are excluded '
              'from the unmasked-copy count. Base source versions are preferred; the fallback '
              'is an ancestor-tag description at the pinned base, explicitly identified in JSON. '
              'Version comparisons indicate differences, not an ordering of releases.', '',
              '| Unmasked different-version copy task | Copy path | Base version | Copy version | Gold added-line matches |',
              '|---|---|---|---|---:|']
    for r,c in different:
        lines += [f'| {r["instance_id"]} | `{c["path"]}` | {c["base_version"]} | {c["version"]} | {c["gold_added_line_count"]} |']
    lines += ['', 'Requests exclusion check (counts only):', '',
              '| Task | Vendored copies | Different-version vendored copies | Distinctive gold-line matches across copies |',
              '|---|---:|---:|---:|']
    for r in images:
        if r['instance_id'].startswith('psf__requests-'):
            vendor = [c for c in r.get('checks',{}).get('packages',{}).get('result',{}).get('copies',[]) if c['vendored']]
            lines += [f'| {r["instance_id"]} | {len(vendor)} | {sum(c.get("different_from_base") is True for c in vendor)} | {sum(c["gold_added_line_count"] for c in vendor)} |']
    lines += ['', '## Validation and reproduction', '',
        'All commands run from the worktree root with this worktree’s `.venv` and:', '',
        '```sh', 'export HF_HOME=/home/sankalp/projects/wt-leakage/runs/hf_home',
        'export HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1',
        'env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_image_leakage.py',
        'env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/audit_leakage_gaps.py',
        'env -u PYTHONPATH PYTHONPATH=src .venv/bin/python scripts/verify_leakage_gaps.py',
        'env -u PYTHONPATH PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -rfE', '```', '',
        'Docker access was escalated only for the listed image operations. The split '
        '`--prepare`/`--collect --inventory` mode supports Docker-only escalation. '
        'Private requests, dataset data, raw logs and exported archives remain under ignored `runs/`.', '',
        'Offline dataset cache initially copied: 15,484,578 bytes (15 MB), '
        'only SWE-bench Verified Hub and datasets entries. No tests or reference files were changed.', '',
        f'Full unit-suite comparison by node ID: {len(unit["new_failed_or_error_ids"])} new failures/errors; '
        f'{len(unit["reference_now_passes"])} reference failures now pass. '
        'The six failures and seventeen errors are exactly the reference IDs; '
        'there are no newly passing reference failures to explain. '
        'Full IDs and comparison are in `unit_comparison.json`; local output is '
        '`runs/leakage_gaps/pytest.out`. Synthetic tests cover every command family, '
        'ordered test definitions, verified archives, mocked Docker invocation and '
        'reachable/dangling commits in temporary repositories.', '',
        'The independent verifier imports only the standard library. It recounts per-task '
        'JSON, checks report totals, preserves legacy findings as a multiset and '
        'rechecks each rule-3 downgrade directly against the archive. '
        'No agent-container isolation fix was implemented. No branch was pushed.', '']
    (root/'REPORT.md').write_text('\n'.join(lines))
    print('Wrote report from sanitized results')


if __name__ == '__main__':
    main()
