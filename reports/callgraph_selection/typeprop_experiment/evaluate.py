"""Reproduce the frozen baseline, compare enhanced graphs and unchanged selectors."""
from __future__ import annotations
import argparse
import csv
import gc
import gzip
import hashlib
import io
import json
import resource
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
CG = HERE.parent
ROOT = CG.parents[1]
sys.path[:0] = [str(HERE), str(CG), str(CG / 'phase2'), str(ROOT / 'src')]
from typeprop_graph import TypeGraph, TypeAmendedGraph, MAX_ROUNDS, MAX_TYPES
from static_graph import Graph, LIMITS
from build_graphs import extract, digest, changed_symbols, jsonlines
from followup_analysis import records
from inputs import Registry, base_test_ids, stored_selections
from callgraph_selector import Identities, Traversal, VARIANTS, DEPTHS, BUDGETS, features, rank_candidates

START = '0c0c87fda86cf0a2f7c33866020325856e7303de'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def csv_write(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict, tuple)) else v
                             for k, v in row.items()})


def original_state(original):
    args = ['git', '-C', str(original)]
    paths = subprocess.check_output(args + ['ls-files', '-m', '-d', '-o', '--exclude-standard', '-z']).decode().split('\0')
    return dict(status=subprocess.check_output(args + ['status', '--porcelain=v1', '-uall']).decode(),
        head=subprocess.check_output(args + ['rev-parse', 'HEAD']).decode().strip(),
        branch=subprocess.check_output(args + ['branch', '--show-current']).decode().strip(),
        sha256={p: digest(original / p) if (original / p).is_file() else None for p in sorted(set(paths) - {''})})


def verify_manifest(original, manifest):
    count = 0
    for iid, record in manifest.items():
        for name, sha in record['artifact_sha256'].items():
            if digest(original / 'reports/callgraph_selection' / record['directory'] / name) != sha:
                raise ValueError('Frozen graph hash mismatch: ' + iid + '/' + name)
            count += 1
    return count


def patch_inputs():
    pinned = json.loads((CG / 'amendment2_72ad21b/patch_verification.json').read_text())
    export = Path(pinned['export_path'])
    if digest(export) != pinned['export_sha256']:
        raise ValueError('Patch export hash mismatch')
    expected = {r['instance_id']: r for r in read_csv(CG / 'amendment2_72ad21b/verified_patch_manifest.csv')}
    patches = {}
    with tarfile.open(export, 'r:gz') as archive:
        manifest = archive.extractfile('frozen_patches_export/manifest.csv').read()
        if hashlib.sha256(manifest).hexdigest() != pinned['manifest_sha256']:
            raise ValueError('Patch manifest hash mismatch')
        for iid, record in expected.items():
            payload = archive.extractfile('frozen_patches_export/' + iid + '.patch').read()
            if hashlib.sha256(payload).hexdigest() != record['patch_sha256'].removeprefix('sha256:'):
                raise ValueError('Patch hash mismatch: ' + iid)
            patches[iid] = payload
    return patches


def selections(nodes, edges, identities, seeds, stored):
    if not seeds:
        return {}, [], {}
    traversals = {v: Traversal(nodes, edges, v) for v in VARIANTS}
    paths, fans = {}, {}
    for v in VARIANTS:
        paths[v], fans[v] = traversals[v].test_paths(seeds, identities.test_definitions)
    modules = {nodes[s]['module'] for s in seeds}
    rankings, specificity = {}, []
    for v in VARIANTS:
        for seed in sorted(seeds):
            specificity.append(dict(edge_variant=v, seed=seed, fan_in=fans[v][seed],
                                    weight=1 / (1 + fans[v][seed])))
        for depth in DEPTHS:
            for strategy in (('B', 'C') if stored is not None else ('B',)):
                pool = ([(raw, identities.lookup(raw)['node_id'], i) for i, raw in enumerate(stored, 1)]
                        if strategy == 'C' else [(raw, node, None) for node, raw in identities.emittable.items()])
                candidates = []
                for raw, node, position in pool:
                    row, reachable, _ = features(raw, node, nodes, modules, paths[v], fans[v], depth,
                                                  paths[VARIANTS[0]], position, identities.lookup(raw))
                    if strategy == 'B' and not reachable:
                        continue
                    candidates.append(row)
                rankings[(v, depth, strategy)] = rank_candidates(strategy, candidates)
    return rankings, specificity, traversals


def context(root, path, line, radius=3):
    lines = (root / path).read_text(errors='replace').splitlines()
    return '\n'.join(f'{i + 1}: {lines[i]}' for i in range(max(0, line - radius - 1), min(len(lines), line + radius)))


def audit_record(g, root, ordinal, iid, repo):
    edge = g.edges[ordinal]
    evidence, seen = [], set()
    def trace(key, depth=0):
        if key in seen or depth > 8:
            return
        seen.add(key)
        fact = g.fact_evidence.get(key, {})
        scope, name = key
        if 'assignment' in fact:
            evidence.append(dict(kind='local_constructor', name=name, scope=scope,
                context=context(root, g.scopes[scope]['path'], fact['assignment']['line'])))
        for incoming in fact.get('incoming', []):
            call = g.call_details[incoming['callsite']]
            evidence.append(dict(kind='caller_argument', name=name, scope=scope,
                context=context(root, g.scopes[call['scope']]['path'], call['line'])))
            if incoming['actual'] and incoming['actual'][0] == 'name':
                trace((call['scope'], incoming['actual'][1]), depth + 1)
    trace((edge['receiver_fact']['scope'], edge['receiver_fact']['name']))
    return dict(instance_id=iid, repo=repo, ordinal=ordinal, edge=edge,
        site_context=context(root, edge['path'], edge['line']),
        target_context=[context(root, g.nodes[t]['path'], g.nodes[t]['line']) for t in edge['targets']],
        receiver_classes=[g.nodes[t] for t in edge['receiver_types']], evidence=evidence)


def run(args):
    original = args.original.resolve()
    manifest = json.loads((CG / 'amendment2_72ad21b/graph_manifest.json').read_text())
    tasks = json.loads((CG / 'inputs.json').read_text())['tasks']
    frozen_rows = {r['instance_id']: r for r in read_csv(CG / 'amendment2_72ad21b/base_feasibility.csv')}
    frozen_symbols = read_csv(CG / 'amendment2_72ad21b/changed_symbol_resolution.csv')
    frozen_counts = {(r['instance_id'], r['edge_variant'], int(r['depth']), r['strategy'], r['budget']): r
                     for r in read_csv(CG / 'phase2/per_task.csv')}
    eligibility = {r['instance_id']: r for r in json.loads((CG / 'phase2/eligibility.json').read_text())['tasks']}
    if not args.tasks:
        verified_files = verify_manifest(original, manifest)
    else:
        verified_files = verify_manifest(original, {i: manifest[i] for i in args.tasks})
    patches = patch_inputs()
    stored = stored_selections((ROOT / 'reports/failure_analysis/extracted.json').read_text())
    historical = set(json.loads((CG / 'phase2/eligibility.json').read_text())['historical_19'])
    chosen = [t for t in tasks if not args.tasks or t['instance_id'] in args.tasks]
    protocol = dict(starting_commit=START, date='2026-11-02', tasks=len(chosen), population=83,
        original_worktree=str(original), baseline='Amendment 2 overlay: 79 original + 4 amended SymPy',
        baseline_implementation=['static_graph.py', 'amended_graph.py'],
        baseline_manifest_sha256=digest(CG / 'amendment2_72ad21b/graph_manifest.json'),
        verified_baseline_files=verified_files, max_rounds=MAX_ROUNDS, max_types=MAX_TYPES,
        limits=LIMITS, process_batch_size=args.batch_size, propagation_calls='frozen baseline resolved only; uncertain calls taint parameters',
        parameter_boundary='observed static callers, with escaped callable references rejected; not an open-world proof',
        defaults_and_variadics='unsupported: unknown', keywords='required positional/keyword-only supported',
        fixed_point='synchronous set union + unknown; cycles without evidence stay bottom; round exhaustion fails closed',
        selector=dict(depths=DEPTHS, budgets=(*BUDGETS, 'ALL'), variants=VARIANTS,
                      ranking='existing phase2 features/rank_candidates unchanged', eligibility='frozen phase2 strata unchanged'),
        audit='one minimum-SHA256 new resolved callsite per repository/provenance stratum, after full run',
        benchmark_execution=False, oracle_inputs=False, code_sha256={p.name: digest(p) for p in HERE.glob('*.py')})
    if (HERE / 'protocol.json').exists() and not args.resume:
        raise ValueError('Outputs already exist; use a fresh experiment directory or --resume')
    if args.resume:
        previous = json.loads((HERE / 'protocol.json').read_text())
        if previous['code_sha256'] != protocol['code_sha256'] or previous['tasks'] != protocol['tasks']:
            raise ValueError('Resume requires identical code/population')
    else:
        dump(HERE / 'protocol.json', protocol)
        rows = list(frozen_rows.values())
        dump(HERE / 'baseline_summary.json', dict(tasks=83,
            graph_status_counts=dict(Counter(r['graph_status'] for r in rows)),
            calls={s: sum(int(r.get(s + '_edges', 0) or 0) for r in rows) for s in ('resolved','ambiguous','unresolved')},
            ast_nodes=sum(int(r['ast_nodes']) for r in rows),
            call_sites=sum(int(r['call_sites']) for r in rows),
            changed_symbols=dict(Counter(r['status'] for r in frozen_symbols)),
            graph_runtime_seconds=sum(float(r['graph_runtime_seconds']) for r in rows),
            parse_failures=sum(int(r['parse_failures']) for r in rows),
            manifest_sha256=protocol['baseline_manifest_sha256']))
    cache = HERE / 'task_artifacts'
    cache.mkdir(exist_ok=True)
    processed = 0
    for task in chosen:
        iid, repo = task['instance_id'], task['repo']
        destination = cache / iid
        if args.resume and (destination / 'summary.json').is_file():
            continue
        destination.mkdir(exist_ok=True)
        started = time.monotonic()
        directory = original / 'reports/callgraph_selection' / manifest[iid]['directory']
        frozen_nodes = {n['id']: n for n in records(directory / 'nodes.jsonl.gz')}
        frozen_edges = list(records(directory / 'edges.jsonl.gz'))
        with tempfile.TemporaryDirectory(prefix='cis695-typeprop-', dir='/tmp') as temporary:
            archive_sha, skipped = extract(task, Path(temporary))
            root = Path(temporary) / 'testbed'
            graph_class = TypeAmendedGraph if manifest[iid]['directory'].startswith('amendment2_') else TypeGraph
            g = graph_class().build(root)
            for item in skipped:
                if item['path'].endswith('.py'):
                    g.files[item['path']] = 'omitted_archive_link'
                    g.failures.append(item)
                    g.counts['omitted_files'] += 1
            if g.status == 'complete' and g.failures:
                g.status = 'partial'
            if g.status == 'resource_limited':
                dump(destination / 'summary.json', dict(instance_id=iid, repo=repo, graph_status=g.status,
                    failures=g.failures, elapsed_seconds=time.monotonic()-started, comparable=False))
                print(iid, 'RESOURCE_LIMITED', flush=True)
                continue
            # Baseline identity is checked against every stored node and edge, not just totals.
            if g.nodes != frozen_nodes or g.baseline_edges != frozen_edges:
                raise ValueError('Reproduced baseline differs from frozen graph: ' + iid)
            if g.status != manifest[iid]['graph_status']:
                raise ValueError('Build completeness changed: ' + iid)
            transitions, changes, audits = Counter(), [], {}
            before_reasons, after_reasons = Counter(), Counter()
            for ordinal, (before, after) in enumerate(zip(frozen_edges, g.edges)):
                transitions[before['status'] + ' -> ' + after['status']] += 1
                if before['status'] != 'resolved':
                    before_reasons[before['reason']] += 1
                if after['status'] != 'resolved':
                    after_reasons[after['reason']] += 1
                if before['status'] != after['status'] or before['targets'] != after['targets']:
                    changes.append(dict(instance_id=iid, repo=repo, ordinal=ordinal, path=after['path'],
                        line=after['line'], column=after['column'], scope=after['scope'], expression=after['expression'],
                        before_status=before['status'], after_status=after['status'], before_targets=before['targets'],
                        after_targets=after['targets'], before_reason=before['reason'], after_reason=after['reason'],
                        provenance=after['provenance'], receiver_types=after.get('receiver_types', [])))
                    if after['status'] == 'resolved':
                        key = hashlib.sha256((iid + ':' + str(ordinal)).encode()).hexdigest()
                        provenance = after['provenance']
                        if provenance not in audits or key < audits[provenance][0]:
                            audits[provenance] = (key, ordinal)
            audit_candidates = [dict(sample_key=key, **audit_record(g, root, ordinal, iid, repo))
                                for key, ordinal in audits.values()]
        baseline_graph = SimpleNamespace(nodes=frozen_nodes, files=g.files)
        before_symbols = [s for s in changed_symbols(patches[iid], baseline_graph) if s['name'] is not None]
        after_symbols = [s for s in changed_symbols(patches[iid], g) if s['name'] is not None]
        expected = [r for r in frozen_symbols if r['instance_id'] == iid]
        normalize = lambda rows: sorted((r['path'], r['name'], r['status'],
            tuple(json.loads(r['targets']) if isinstance(r['targets'], str) else r['targets'])) for r in rows)
        if normalize(before_symbols) != normalize(expected):
            raise ValueError('Fresh changed-symbol extraction differs from frozen: ' + iid)
        symbol_changes = [dict(instance_id=iid, before=b, after=a) for b, a in zip(before_symbols, after_symbols) if b != a]
        seeds = {s['targets'][0] for s in before_symbols if s['status'] == 'resolved'}
        registry = Registry()
        base_ids, _ = base_test_ids(task, registry)
        identities = Identities(g.nodes, base_ids, repo)
        stored_ids = stored[iid]['selected_tests'] if iid in historical else None
        b_rank, b_specificity, b_traversals = selections(g.nodes, frozen_edges, identities, seeds, stored_ids)
        a_rank, a_specificity, a_traversals = selections(g.nodes, g.edges, identities, seeds, stored_ids)
        selection_rows, selection_changes, path_evidence = [], [], []
        for (variant, depth, strategy), before in b_rank.items():
            after = a_rank[(variant, depth, strategy)]
            for budget in (*BUDGETS, 'ALL'):
                b_prefix = before if budget == 'ALL' else before[:budget]
                a_prefix = after if budget == 'ALL' else after[:budget]
                b_ids, a_ids = [r['test_id'] for r in b_prefix], [r['test_id'] for r in a_prefix]
                added, removed = sorted(set(a_ids) - set(b_ids)), sorted(set(b_ids) - set(a_ids))
                expected_count = frozen_counts[(iid, variant, depth, strategy, str(budget))]['selected_count']
                if expected_count == '' or int(expected_count) != len(b_ids):
                    raise ValueError('Unchanged selector disagrees with frozen count: ' + iid)
                row = dict(instance_id=iid, repo=repo, stratum=eligibility[iid]['stratum'], strategy=strategy,
                    edge_variant=variant, depth=depth, budget=budget, before_count=len(b_ids), after_count=len(a_ids),
                    added_count=len(added), removed_count=len(removed), membership_changed=set(b_ids) != set(a_ids),
                    order_changed=b_ids != a_ids, v2_before_overlap=len(set(b_ids) & set(stored_ids or [])),
                    v2_after_overlap=len(set(a_ids) & set(stored_ids or [])),
                    before_reachable=sum(r['graph_status'] == 'reachable' for r in b_prefix),
                    after_reachable=sum(r['graph_status'] == 'reachable' for r in a_prefix))
                selection_rows.append(row)
                if row['order_changed']:
                    selection_changes.append(dict(**row, added=added, removed=removed))
                # At most 25 newly reached tests per config, one shortest seed path each.
                if budget == 'ALL' and strategy == 'B':
                    for raw in added[:25]:
                        node = identities.lookup(raw)['node_id']
                        candidates = [(seed, route) for seed in sorted(seeds)
                                      if (route := a_traversals[variant].from_seed(seed).get(node)) is not None
                                      and 1 <= len(route.edges) <= depth]
                        if candidates:
                            seed, route = candidates[0]
                            path_evidence.append(dict(instance_id=iid, repo=repo, edge_variant=variant, depth=depth,
                                test_id=raw, seed=seed, **a_traversals[variant].provenance(route),
                                new_typeprop_ordinals=[o for o in route.edges if g.edges[o]['provenance'] != 'existing_static_resolution']))
        jsonlines(destination / 'edges.jsonl.gz', g.edges)
        jsonlines(destination / 'type_facts.jsonl.gz', g.fact_records())
        dump(destination / 'callsite_changes.json', changes)
        dump(destination / 'symbol_changes.json', symbol_changes)
        dump(destination / 'audit_candidates.json', audit_candidates)
        dump(destination / 'selection_rows.json', selection_rows)
        dump(destination / 'selection_changes.json', selection_changes)
        dump(destination / 'selection_paths.json', path_evidence)
        dump(destination / 'specificity.json', dict(before=b_specificity, after=a_specificity))
        row = dict(instance_id=iid, repo=repo, graph_status=g.status, comparable=True,
            baseline_nodes_and_edges_identical=True, baseline_selector_counts_identical=True,
            baseline_calls=dict(Counter(e['status'] for e in frozen_edges)),
            enhanced_calls=dict(Counter(e['status'] for e in g.edges)), transitions=dict(transitions),
            baseline_changed_symbols=dict(Counter(s['status'] for s in before_symbols)),
            enhanced_changed_symbols=dict(Counter(s['status'] for s in after_symbols)),
            baseline_runtime_seconds=float(frozen_rows[iid]['graph_runtime_seconds']),
            enhanced_runtime_seconds=g.runtime, task_seconds=time.monotonic() - started,
            parse_failures=g.counts['parse_failures'], ast_nodes=g.counts['ast_nodes'],
            retained_ast_nodes=g.counts.get('retained_ast_nodes', g.counts['ast_nodes']),
            call_sites=g.counts['call_sites'], counts=dict(g.counts), type_metrics=g.type_metrics,
            before_reasons=dict(before_reasons), after_reasons=dict(after_reasons),
            new_resolved_by_provenance=dict(Counter(c['provenance'] for c in changes if c['after_status'] == 'resolved')),
            selection_membership_changed=any(r['membership_changed'] for r in selection_rows),
            selection_order_changed=any(r['order_changed'] for r in selection_rows),
            peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            artifact_sha256={p.name: digest(p) for p in destination.iterdir() if p.name != 'summary.json'})
        dump(destination / 'summary.json', row)
        print(json.dumps({k: row[k] for k in ('instance_id','graph_status','enhanced_runtime_seconds',
            'new_resolved_by_provenance','selection_membership_changed','peak_process_rss_kib')}), flush=True)
        del g, frozen_nodes, frozen_edges, b_traversals, a_traversals
        gc.collect()
        processed += 1
        if args.batch_size and processed >= args.batch_size:
            break
    missing = [t['instance_id'] for t in chosen if not (cache / t['instance_id'] / 'summary.json').is_file()]
    if missing:
        print('BATCH_COMPLETE ' + json.dumps(dict(completed_this_process=processed, pending_tasks=len(missing))), flush=True)
        return
    aggregate(chosen, original, manifest)


def aggregate(tasks, original, manifest):
    summaries, changes, symbols, selection_rows, selection_changes, paths, audits, specificity = [], [], [], [], [], [], {}, []
    for task in tasks:
        directory = HERE / 'task_artifacts' / task['instance_id']
        row = json.loads((directory / 'summary.json').read_text())
        summaries.append(row)
        if not row['comparable']:
            continue
        for filename, target in [('callsite_changes', changes), ('symbol_changes', symbols),
                                 ('selection_rows', selection_rows), ('selection_changes', selection_changes),
                                 ('selection_paths', paths)]:
            target.extend(json.loads((directory / (filename + '.json')).read_text()))
        for sample in json.loads((directory / 'audit_candidates.json').read_text()):
            key = sample['repo'], sample['edge']['provenance']
            if key not in audits or sample['sample_key'] < audits[key]['sample_key']:
                audits[key] = sample
        specific = json.loads((directory / 'specificity.json').read_text())
        for before, after in zip(specific['before'], specific['after']):
            if before != after:
                specificity.append(dict(instance_id=task['instance_id'], repo=task['repo'], before=before, after=after))
    measured = [r for r in summaries if r['comparable']]
    total = dict(tasks_attempted=len(tasks), tasks_compared=len(measured),
        graph_status_counts=dict(Counter(r['graph_status'] for r in summaries)),
        baseline_calls=dict(sum((Counter(r['baseline_calls']) for r in measured), Counter())),
        enhanced_calls=dict(sum((Counter(r['enhanced_calls']) for r in measured), Counter())),
        transitions=dict(sum((Counter(r['transitions']) for r in measured), Counter())),
        baseline_changed_symbols=dict(sum((Counter(r['baseline_changed_symbols']) for r in measured), Counter())),
        enhanced_changed_symbols=dict(sum((Counter(r['enhanced_changed_symbols']) for r in measured), Counter())),
        baseline_runtime_seconds=sum(r['baseline_runtime_seconds'] for r in measured),
        enhanced_runtime_seconds=sum(r['enhanced_runtime_seconds'] for r in measured),
        inference_seconds=sum(r['type_metrics']['inference_seconds'] for r in measured),
        ast_nodes=sum(r['ast_nodes'] for r in measured), call_sites=sum(r['call_sites'] for r in measured),
        parse_failures=sum(r['parse_failures'] for r in measured),
        peak_process_rss_kib=max(r.get('peak_process_rss_kib',0) for r in summaries),
        new_resolved_by_provenance=dict(sum((Counter(r['new_resolved_by_provenance']) for r in measured), Counter())),
        tasks_selection_membership_changed=sum(r['selection_membership_changed'] for r in measured),
        tasks_selection_order_changed=sum(r['selection_order_changed'] for r in measured),
        selection_configurations=len(selection_rows), changed_selection_configurations=len(selection_changes))
    dump(HERE / 'enhanced_summary.json', total)
    dump(HERE / 'audit_candidates.json', sorted(audits.values(), key=lambda a: (a['repo'], a['edge']['provenance'])))
    csv_write(HERE / 'callsite_changes.csv', changes, ['instance_id','repo','ordinal','path','line','column','scope','expression',
        'before_status','after_status','before_targets','after_targets','before_reason','after_reason','provenance','receiver_types'])
    csv_write(HERE / 'changed_symbol_changes.csv', symbols, ['instance_id','before','after'])
    csv_write(HERE / 'task_summary.csv', summaries)
    csv_write(HERE / 'selection_summary.csv', selection_rows)
    csv_write(HERE / 'selection_changes.csv', selection_changes, list(selection_rows[0]) + ['added','removed'])
    csv_write(HERE / 'selection_paths.csv', paths, ['instance_id','repo','edge_variant','depth','test_id','seed','path_nodes',
        'path_calls','distance','uses_ambiguous_edge','ambiguous_hop_count','ambiguous_hop_positions','new_typeprop_ordinals'])
    csv_write(HERE / 'specificity_changes.csv', specificity, ['instance_id','repo','before','after'])
    csv_write(HERE / 'provenance_counts.csv', [dict(provenance=k, new_resolved_call_sites=v) for k,v in total['new_resolved_by_provenance'].items()])
    reasons = []
    for phase in ('before', 'after'):
        counts = sum((Counter(r[phase + '_reasons']) for r in measured), Counter())
        reasons.extend(dict(phase=phase, reason=k, count=v) for k,v in sorted(counts.items()))
    csv_write(HERE / 'unresolved_reasons_before_after.csv', reasons)
    repositories = []
    for repo in sorted(set(t['repo'] for t in tasks)):
        rows = [r for r in measured if r['repo'] == repo]
        value = dict(repo=repo, tasks=len(rows), complete=sum(r['graph_status']=='complete' for r in rows),
                     partial=sum(r['graph_status']=='partial' for r in rows))
        for phase in ('baseline', 'enhanced'):
            counts = sum((Counter(r[phase + '_calls']) for r in rows), Counter())
            value.update({phase + '_' + k: counts[k] for k in ('resolved','ambiguous','unresolved')})
        value['new_resolved'] = value['enhanced_resolved'] - value['baseline_resolved']
        value['selection_tasks_changed'] = sum(r['selection_membership_changed'] for r in rows)
        repositories.append(value)
    csv_write(HERE / 'repository_summary.csv', repositories)
    before_state = json.loads((HERE / 'original_worktree_snapshot.json').read_text())
    unchanged = before_state == original_state(original)
    baseline_files = verify_manifest(original, {t['instance_id']:manifest[t['instance_id']] for t in tasks})
    tracked_diff = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines()
    validation = dict(tests_passed='See focused_tests.txt', tasks_compared=len(measured),
        baseline_files_unchanged=baseline_files > 0 and not tracked_diff, verified_baseline_files=baseline_files,
        original_worktree_untouched=unchanged,
        previous_resolved_edges_lost=total['transitions'].get('resolved -> unresolved',0),
        previous_resolved_edges_changed_to_ambiguous=total['transitions'].get('resolved -> ambiguous',0),
        new_resolved_edges=sum(v for k,v in total['new_resolved_by_provenance'].items()),
        new_ambiguous_edges=sum(v for k,v in total['transitions'].items() if k.endswith(' -> ambiguous') and not k.startswith('ambiguous')),
        changed_symbol_resolutions_gained=sum(s['after']['status']=='resolved' and s['before']['status']!='resolved' for s in symbols),
        changed_symbol_resolutions_lost=sum(s['before']['status']=='resolved' and s['after']['status']!='resolved' for s in symbols),
        baseline_reproduced_exactly=all(r['baseline_nodes_and_edges_identical'] for r in measured),
        baseline_selector_counts_reproduced=all(r['baseline_selector_counts_identical'] for r in measured),
        all_added_test_paths_use_typeprop=all(p['new_typeprop_ordinals'] for p in paths),
        audit_supported=None, audit_questionable=None, audit_incorrect=None,
        audit_status='pending human-readable source review by agent',
        oracle_inputs=False, benchmark_code_executed=False)
    dump(HERE / 'validation.json', validation)
    if not unchanged or not validation['baseline_files_unchanged']:
        raise ValueError('Isolation/baseline preservation check failed')
    print('COMPLETE ' + json.dumps(total), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=Path('/home/rajee/projects/cis695-agent-reliability'))
    parser.add_argument('--tasks', nargs='+')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--batch-size', type=int, default=0, help='fresh-process boundary; zero runs all pending tasks')
    run(parser.parse_args())
