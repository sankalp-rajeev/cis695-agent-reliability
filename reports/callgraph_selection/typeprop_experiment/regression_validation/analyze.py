"""Post-hoc identity retention audit. Never executes tests or changes a selector.

Replays frozen prefix memberships using recorded deltas, not graph traversal.
Evidence has separate observed-regression and official-witness denominators.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
CG = EXP.parent
ROOT = CG.parents[1]
ORIGINAL = Path('/home/rajee/projects/cis695-agent-reliability')
QM = EXP / 'qualified_mapping'
sys.path.insert(0, str(ROOT / 'reports/v2_diagnostic'))
from oracle_posthoc import canonical, match_test


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def read_csv(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f))


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def write_csv(name, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with (HERE / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fields, lineterminator='\n'); w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def original_state():
    args = ['git', '-C', str(ORIGINAL)]
    paths = subprocess.check_output(args + ['ls-files', '-m', '-d', '-o', '--exclude-standard', '-z']).decode().split('\0')
    return dict(head=subprocess.check_output(args + ['rev-parse', 'HEAD']).decode().strip(),
        status=subprocess.check_output(args + ['status', '--porcelain=v1', '-uall']).decode(),
        files={p: sha(ORIGINAL / p) if (ORIGINAL / p).is_file() else None for p in sorted(set(paths) - {''})})


def cfg(r): return tuple(str(r[k]) for k in ('instance_id', 'strategy', 'edge_variant', 'depth', 'budget'))
def flag(value): return value == 'True'


def delta(before, row):
    """Apply an already recorded set delta; None is unavailable, never empty."""
    if row is None: return None if before is None else set(before)
    if 'after_available' in row and not flag(row['after_available']): return None
    added, removed = json.loads(row['added'] or 'null'), json.loads(row['removed'] or 'null')
    if before is None:
        assert row['after_count'] == '0' and added is None and removed is None
        return set()
    assert added is not None and removed is not None
    assert set(removed) <= before
    assert not set(added) & before
    return (before - set(removed)) | set(added)


def matches(test, selected, repo):
    if selected is None: return None
    if canonical(test, repo)[0] is None: return None
    return bool(match_test(test, sorted(selected), repo, {})['selected_ids'])


def reconstruct(rows):
    ranked = ORIGINAL / 'reports/callgraph_selection/phase2/ranked_outputs.jsonl.gz'
    pin = json.loads((CG / 'phase2/selector_freeze.json').read_text())['output_sha256']['ranked_outputs.jsonl.gz']
    assert sha(ranked) == pin
    with gzip.open(ranked, 'rt') as f:
        ranks = {(d['instance_id'], d['strategy'], d['edge_variant'], str(d['depth'])): d
                 for d in map(json.loads, f) if d['strategy'] in ('B', 'C')}
    type_deltas = {cfg(r): r for r in read_csv(EXP / 'selection_changes.csv')}
    map_deltas = {cfg(r): r for r in read_csv(QM / 'selection_changes.csv')}
    type_counts = {cfg(r): r for r in read_csv(EXP / 'selection_summary.csv')}
    selections = {}
    for r in rows:
        key = cfg(r)
        if flag(r['before_available']):
            ids = [x['test_id'] for x in ranks[key[:4]].get('candidates', [])]
            assert len(ids) == len(set(ids))
            prefix = set(ids if r['budget'] == 'ALL' else ids[:int(r['budget'])])
            before = delta(prefix, type_deltas.get(key))
            assert len(before) == int(type_counts[key]['after_count']) == int(r['before_count']), key
        else: before = None
        after = delta(before, map_deltas.get(key))
        assert (after is not None) == flag(r['after_available']), key
        if after is not None: assert len(after) == int(r['after_count']), key
        selections[key] = (before, after)
    return selections, ranked


def evidence(tasks, patches):
    source_paths = [ROOT / 'reports/failure_analysis/extracted.json',
        ROOT / 'reports/failure_analysis/group4_failing_tests.json',
        ROOT / 'reports/failure_analysis/group4_regression_rerun.json',
        ROOT / 'reports/v2_diagnostic/patches.csv',
        ROOT / 'reports/v2_scoring_audit/resume_20261026/raw_test_outcomes.csv',
        ROOT / 'reports/v2_scoring_audit/resume_20261026/raw_collection.sha256.json',
        ROOT / 'reports/v2_scoring_audit/resume_20261026/environment_sanity.csv',
        ROOT / 'reports/v2_scoring_audit/resume_20261026/regression_reruns.csv']
    ceiling = ROOT / 'reports/ceiling_check/failing_tests.csv'
    if not ceiling.exists(): ceiling = ORIGINAL / 'reports/ceiling_check/failing_tests.csv'
    source_paths.append(ceiling)
    snapshots = json.loads(source_paths[0].read_text())['tasks']
    snapshot = {t['instance_id']: t for t in snapshots}
    projected, witnesses = [], []
    ceiling_rows = read_csv(ceiling)
    ceiling_index = {(r['instance_id'], r['official_id']): r for r in ceiling_rows}
    for iid, t in snapshot.items():
        assert sha_bytes(t['agent_patch'].encode()) == patches[iid]['patch_sha256'].removeprefix('sha256:')
        assert t['source_run'] == patches[iid]['source_run']
        projected.append(dict(instance_id=iid, source_run=t['source_run'],
            patch_sha256=sha_bytes(t['agent_patch'].encode()), oracle=t['oracle_record']['outcome'],
            regression=t['signals']['regression'],
            f2p_failure=t['oracle_record']['f2p_failure'], p2p_failure=t['oracle_record']['p2p_failure']))
        for group in ('f2p_failure', 'p2p_failure'):
            for tid in t['oracle_record'][group]:
                c = ceiling_index.get((iid, tid))
                assert c, (iid, tid)
                assert c['source_run'] == t['source_run']
                node = c['archive_member'].removeprefix('testbed/') + '::' + c['ast_identity'] if c['ast_identity'] else None
                if node and '[' in tid: node += tid[tid.index('['):]
                usable = c['existing_suite_witness'] == 'True'
                witnesses.append(dict(instance_id=iid, test_id=tid, matching_id=node or tid,
                    evidence_tier='official_existing_base_witness' if usable else 'official_non_base_or_uncertain',
                    usable_for_existing_test_recall=usable, base_relation=c['base_relation'],
                    source='reports/ceiling_check/failing_tests.csv; reports/failure_analysis/extracted.json#oracle_record.' + group,
                    limitation='Official harness failure; base identity unchanged does not establish a paired base-pass/candidate-fail in the historical V2 environment.'))
    reported = json.loads(source_paths[1].read_text())
    rerun = {r['instance_id']: r for r in json.loads(source_paths[2].read_text())['tasks']}
    for iid, ids in reported.items():
        if iid.startswith('_'): continue
        assert ids == rerun[iid]['failing'] and rerun[iid]['signal'] == 'FAIL'
        assert rerun[iid]['source_run'] == tasks[iid]['source_run']
        for tid in ids:
            witnesses.append(dict(instance_id=iid, test_id=tid, matching_id=tid,
                evidence_tier='reported_existing_regression', usable_for_existing_test_recall=True,
                base_relation='existing regression-suite test',
                source='reports/failure_analysis/group4_failing_tests.json; group4_regression_rerun.json',
                limitation='Frozen per-test regression summary, cached baseline; original raw test logs not required or asserted available.'))
    raw_root = ROOT / 'reports/v2_scoring_audit/resume_20261026'
    local_raw_root = ORIGINAL / 'reports/v2_scoring_audit/resume_20261026'
    raw_hashes = json.loads((raw_root / 'raw_collection.sha256.json').read_text())
    env = {r['instance_id']: r for r in read_csv(raw_root / 'environment_sanity.csv')}
    paired = read_csv(raw_root / 'raw_test_outcomes.csv')
    checked = {}
    for r in paired:
        iid = r['instance_id']; e = env[iid]
        assert e['patch_sha256'] == patches[iid]['patch_sha256'].removeprefix('sha256:')
        assert e['patch_applied'] == 'True'
        r['observed_base_commit'] = e['observed_base_commit']
        r['graph_base_commit'] = tasks[iid]['base_commit']
        r['base_commit_identity_matches'] = e['observed_base_commit'] == tasks[iid]['base_commit']
        for k in ('base_raw_ref', 'patched_raw_ref'):
            ref = r[k]
            if ref not in checked:
                path = local_raw_root / ref
                assert path.is_file() and sha(path) == raw_hashes[ref], ref
                checked[ref] = raw_hashes[ref]
        r['outcome_class'] = ('observed_regression' if r['base_outcome'] == 'passed' and r['patched_outcome'] == 'failed'
            else 'observed_non_detecting_pass' if r['base_outcome'] == r['patched_outcome'] == 'passed'
            else 'observed_preexisting_failure' if r['base_outcome'] == r['patched_outcome'] == 'failed'
            else 'observed_skip_or_other')
        r['limitation'] = 'Supplemental later local pair: image HEAD differs from graph base; source-tree/historical image equivalence unverified. Concrete cases only, never all possible parameters.'
    # Keep one detecting identity per tier; pytest's raw result corroborates its historical report.
    raw_detecting = {(r['instance_id'], r['raw_test_id']) for r in paired if r['outcome_class'] == 'observed_regression'}
    for iid, tid in raw_detecting:
        assert any(w['instance_id'] == iid and w['test_id'] == tid and w['evidence_tier'] == 'reported_existing_regression' for w in witnesses)
    additional = []
    # Discover only the exact frozen task/run. Other experiments or candidate hashes
    # are not interchangeable, even if they share a SWE-bench instance ID.
    for iid, task in tasks.items():
        path = ORIGINAL / 'runs' / task['source_run'] / 'tasks' / iid / 'verification_record.full.json'
        if not path.exists(): continue
        source_paths.append(path)
        record = json.loads(path.read_text())
        accepted = record['patch_sha256'] == patches[iid]['patch_sha256']
        additional.append(dict(instance_id=iid, source=str(path), source_sha256=sha(path),
            patch_sha256=record['patch_sha256'], expected_patch_sha256=patches[iid]['patch_sha256'],
            accepted=accepted, regression=record['regression'],
            disposition='aggregate only; no per-test outcomes serialized' if accepted else 'EXCLUDED: different candidate patch'))
        if accepted and iid not in snapshot:
            snapshot[iid] = dict(signals=dict(regression=record['regression']))
    write_csv('additional_local_record_evidence.csv', additional)
    corroboration = []
    for iid in sorted({r['instance_id'] for r in paired}):
        path = ROOT / 'reports/v2_stabilization/classifier_v2/live/tasks' / iid / 'paired_outcomes.csv'
        source_paths.append(path)
        rows = read_csv(path)
        expected = {r['raw_test_id']: (r['base_outcome'], r['patched_outcome']) for r in paired if r['instance_id'] == iid}
        assert {r['raw_id']: (r['base'], r['patched']) for r in rows} == expected
        corroboration.append(dict(instance_id=iid, rows=len(rows), exact_same_pairs=True, independent_evidence=False))
    inventory = ORIGINAL / 'reports/v2_scoring_audit/raw_test_outcomes.csv'
    inv_rows = read_csv(inventory)
    assert all(not r['raw_test_id'] and not r['base_outcome'] and not r['patched_outcome'] for r in inv_rows)
    source_paths.append(inventory)
    write_csv('paired_outcomes.csv', paired)
    write_csv('witnesses.csv', witnesses)
    (HERE / 'frozen_ceiling_failing_tests.csv').write_bytes(ceiling.read_bytes())
    dump('historical_evidence_projection.json', projected)
    dump('evidence_manifest.json', dict(sources={str(p): sha(p) for p in source_paths},
        verified_raw_logs=checked, later_raw_rows=len(paired), historical_snapshots=len(snapshots),
        additional_local_records=additional, classifier_pair_corroboration=corroboration,
        older_raw_table=dict(rows=len(inv_rows), actual_observations=0, disposition='Unexecuted request inventory; Docker preflight failed. Never treated as outcomes.'),
        raw_detecting_corroborates_existing_report=sorted(raw_detecting),
        candidate_identity='All 19 historical patch bytes/source runs and all three later paired patch hashes verified against frozen mapping inputs.',
        later_base_identity=[dict(instance_id=iid, graph_base_commit=tasks[iid]['base_commit'], observed_image_head=env[iid]['observed_base_commit']) for iid in sorted({r['instance_id'] for r in paired})],
        historical_equivalence='All three later image HEADs differ from graph bases; source-tree/historical image/runner equivalence is not established. Supplemental observations only. No new execution performed.'))
    return snapshot, witnesses, paired, source_paths


def sha_bytes(payload): return hashlib.sha256(payload).hexdigest()


def main():
    assert not (HERE / 'protocol.json').exists(), 'Refuse to overwrite a completed audit'
    tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    preserved = {p: sha(ROOT / p) for p in tracked if p and not p.startswith(str(HERE.relative_to(ROOT)) + '/')}
    start_original = original_state()
    dump('protocol.json', dict(frozen_mapping_commit=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip(),
        purpose='User-authorized post-hoc validation only; no outcome-driven retuning.',
        headline='B, depth 3, ALL, PRIMARY_RESOLVED_ONLY, paired available tasks',
        configs='All frozen B/C depths 1/2/3 and budgets 25/50/100/250/500/ALL; no new policy.',
        recall='Known named witness identity retention, separate tiers; unknown task outcomes excluded, not negative. No runtime execution claimed.',
        irrelevant='Only concrete observed pass/pass outcomes called non-detecting in the recorded run. No absence-from-failure-list inference.',
        identity='Existing canonical/match_test: exact normalization, explicit unparameterized family includes parameterized case; no fuzzy matching.',
        algorithm='Frozen ranked prefix memberships -> frozen typeprop set deltas -> frozen qualified mapping set deltas. Counts asserted at each available stage.',
        selection_order='Only memberships reconstructed; frozen deltas already encode every finite-budget prefix. No ranking replay.',
        missing='Unavailable selection is null, distinct from available empty set.',
        preserved_sha256=preserved, original_worktree=start_original))
    tasks = {t['instance_id']: t for t in json.loads((CG / 'inputs.json').read_text())['tasks']}
    patches = {r['instance_id']: r for r in read_csv(CG / 'amendment2_72ad21b/verified_patch_manifest.csv')}
    rows = read_csv(QM / 'selection_summary.csv')
    selections, ranked = reconstruct(rows)
    snapshot, witnesses, paired, sources = evidence(tasks, patches)
    usable = [w for w in witnesses if w['usable_for_existing_test_recall']]
    assert all(canonical(w['matching_id'], tasks[w['instance_id']]['repo'])[0] is not None for w in usable)
    by_iid = defaultdict(list)
    raw_iid = defaultdict(list)
    for w in usable: by_iid[w['instance_id']].append(w)
    for r in paired: raw_iid[r['instance_id']].append(r)
    named_evidence_tasks = sorted(by_iid)
    paired_raw_tasks = sorted(raw_iid)
    study_table = {r['instance_id']: r for r in read_csv(ROOT / 'reports/v2_diagnostic/patches.csv')}
    patch_labels = {iid: r['oracle_outcome_posthoc'] for iid, r in study_table.items()}
    metrics, checks, removals, headline = [], [], [], []
    aggregates = defaultdict(Counter)
    serialized = []
    for r in rows:
        key = cfg(r); iid = r['instance_id']; repo = r['repo']; before, after = selections[key]
        is_headline = key[1:] == ('B', 'PRIMARY_RESOLVED_ONLY', '3', 'ALL')
        removed = before - after if before is not None and after is not None else None
        added = after - before if before is not None and after is not None else None
        m = dict(r, oracle_outcome=patch_labels[iid], recorded_table_v2_outcome=study_table[iid]['v2_outcome'],
            reduction_count=len(removed) - len(added) if removed is not None else None,
            reduction_fraction=(len(before) - len(after)) / len(before) if before and after is not None else None,
            observed_pair_rows=len(raw_iid[iid]), historical_aggregate=snapshot[iid]['signals']['regression']['outcome'] if iid in snapshot else 'UNKNOWN',
            evidence_note='No named detecting evidence' if not by_iid[iid] else 'Named evidence; tiers have separate denominators')
        for tier, prefix in [('reported_existing_regression', 'regression'), ('official_existing_base_witness', 'official_witness')]:
            ww = [w for w in by_iid[iid] if w['evidence_tier'] == tier]
            hits_b, hits_a, lost, retained, gained, missed = [], [], [], [], [], []
            for w in ww:
                b = matches(w['matching_id'], before, repo); a = matches(w['matching_id'], after, repo)
                check = dict(zip(('instance_id', 'strategy', 'edge_variant', 'depth', 'budget'), key))
                check.update(test_id=w['test_id'], matching_id=w['matching_id'], evidence_tier=tier,
                    oracle_outcome=patch_labels[iid], before_selected=b, after_selected=a,
                    transition='UNAVAILABLE' if b is None or a is None else 'RETAINED' if b and a else 'LOST' if b else 'GAINED' if a else 'MISSED_BOTH',
                    source=w['source'])
                checks.append(check)
                if b: hits_b.append(w['test_id'])
                if a: hits_a.append(w['test_id'])
                if b and a: retained.append(w['test_id'])
                if b and a is False: lost.append(w['test_id'])
                if a and b is False: gained.append(w['test_id'])
                if a is False and b is False: missed.append(w['test_id'])
            m.update({prefix + '_known': len(ww), prefix + '_before_hits': len(hits_b) if before is not None and ww else None,
                prefix + '_after_hits': len(hits_a) if after is not None and ww else None,
                prefix + '_before_recall': len(hits_b) / len(ww) if before is not None and ww else None,
                prefix + '_after_recall': len(hits_a) / len(ww) if after is not None and ww else None,
                prefix + '_retained': retained, prefix + '_lost': lost, prefix + '_gained': gained, prefix + '_missed_both': missed})
            ag = aggregates[key[1:] + (tier,)]
            if ww and before is not None and after is not None:
                ag.update(tasks=1, known=len(ww), before_hits=len(hits_b), after_hits=len(hits_a), lost=len(lost), retained=len(retained), gained=len(gained), missed_both=len(missed))
        if is_headline:
            for tid in sorted(removed or []):
                obs = [o for o in raw_iid[iid] if matches(o['raw_test_id'], {tid}, repo)]
                failing = [w['test_id'] for w in by_iid[iid] if matches(w['matching_id'], {tid}, repo)]
                label = ('known_detecting_witness' if failing else 'observed_regression' if any(o['outcome_class'] == 'observed_regression' for o in obs)
                    else 'observed_non_detecting_cases_only' if obs and all(o['outcome_class'] == 'observed_non_detecting_pass' for o in obs)
                    else 'observed_preexisting_or_skipped_cases_only' if obs else 'UNKNOWN_NO_PER_TEST_OUTCOME')
                removals.append(dict(instance_id=iid, selected_test_id=tid, classification=label,
                    known_witness_ids=failing, paired_raw_cases=len(obs), concrete_outcome_classes=dict(Counter(o['outcome_class'] for o in obs)),
                    limitation='Partial concrete cases do not establish irrelevance of an entire function family.'))
            headline.append(m)
        metrics.append(m)
        serialized.append(dict(zip(('instance_id', 'strategy', 'edge_variant', 'depth', 'budget'), key)) | dict(
            before_selected=sorted(before) if before is not None else None, after_selected=sorted(after) if after is not None else None))
    with (HERE / 'selection_memberships.jsonl.gz').open('wb') as binary:
        with gzip.GzipFile(filename='', mode='wb', fileobj=binary, mtime=0) as zipped:
            for r in serialized: zipped.write((json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n').encode())
    write_csv('configuration_metrics.csv', metrics)
    write_csv('task_summary.csv', headline)
    write_csv('witness_selection.csv', checks)
    write_csv('removed_tests.csv', removals)
    write_csv('availability_changes.csv', [m for m in headline if flag(m['availability_changed'])])
    aggregate_rows = []
    for k, c in sorted(aggregates.items()):
        d = dict(zip(('strategy', 'edge_variant', 'depth', 'budget', 'evidence_tier'), k)) | dict(c)
        d.update(before_recall=c['before_hits'] / c['known'] if c['known'] else None,
            after_recall=c['after_hits'] / c['known'] if c['known'] else None)
        aggregate_rows.append(d)
    write_csv('recall_by_configuration.csv', aggregate_rows)
    common = [m for m in headline if flag(m['before_available']) and flag(m['after_available'])]
    totals = {stage: sum(int(m[stage + '_count']) for m in common) for stage in ('before', 'after')}
    assert totals == dict(before=715, after=131), totals
    assert len(common) == 78 and len(headline) == 83 and len(rows) == 3672
    primary_checks = [c for c in checks if (c['strategy'], c['edge_variant'], c['depth'], c['budget']) == ('B', 'PRIMARY_RESOLVED_ONLY', '3', 'ALL')]
    summary = dict(population=83, configurations=len(rows), paired_headline_tasks=len(common),
        headline_counts=totals, selected_tests_removed=len(removals), selection_size_reduction=(715-131)/715,
        removed_test_evidence=dict(Counter(r['classification'] for r in removals)),
        headline_recall=[r for r in aggregate_rows if (r['strategy'], r['edge_variant'], r['depth'], r['budget']) == ('B', 'PRIMARY_RESOLVED_ONLY', '3', 'ALL')],
        named_historical_regressions=sum(w['evidence_tier']=='reported_existing_regression' for w in usable),
        official_existing_base_witnesses=sum(w['evidence_tier']=='official_existing_base_witness' for w in usable),
        usable_named_evidence_tasks=named_evidence_tasks, paired_raw_tasks=paired_raw_tasks,
        wrong_patch_after_misses=[c for c in primary_checks if c['oracle_outcome'] != 'resolved' and c['after_selected'] is False],
        headline_lost=[c for c in primary_checks if c['transition']=='LOST'],
        unnamed_historical_regression_tasks=[iid for iid,t in snapshot.items() if t['signals']['regression']['outcome']=='FAIL' and not any(w['evidence_tier']=='reported_existing_regression' for w in by_iid[iid])],
        global_recall='UNKNOWN: most tasks have no named per-test detecting evidence; aggregate PASS/FAIL does not identify omitted test outcomes.',
        irrelevant_removed='UNKNOWN globally; only observed concrete non-detecting cases identified. Official witness and empirical regression recall are distinct.')
    dump('summary.json', summary)
    assert original_state() == start_original
    assert all(sha(ROOT / p) == h for p,h in preserved.items())
    dump('validation.json', dict(status='passed', existing_tracked_files_preserved=len(preserved), original_worktree_unchanged=True,
        reconstructed_configurations=len(rows), all_available_counts_match_frozen_summaries=True,
        frozen_ranked_sha256=sha(ranked), evidence_sources_hash_verified_at_read=True,
        source_or_selector_changes=False, benchmark_execution=False, unknown_is_not_negative=True))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('wrong_patch_after_misses', 'headline_lost')}, indent=2))


if __name__ == '__main__': main()
