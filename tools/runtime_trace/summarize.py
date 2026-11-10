"""Deterministic, offline Phase 6a report. Never emits a test selection."""
import collections
import csv
import gzip
import io
import json
import re
from pathlib import Path

import driver as d

FUNCTION_KINDS = {'function', 'method', 'test_function', 'test_method'}


class Comparison:
    def __init__(self, iid, task, graph):
        self.iid, self.task, self.graph = iid, task, graph
        self.definitions = {}
        self.index = collections.defaultdict(list)
        self.adj = collections.defaultdict(set)
        for node in graph['nodes'].values():
            self.index[(node['path'], node['qualname'])].append(node['id'])
        for edge in graph['edges']:
            if edge['status'] == 'resolved':
                self.adj[edge['caller']].update(edge['targets'])
        self.distances = {}

    def source(self, tree, path):
        return d.RAW / 'sources' / self.iid / tree / path

    def frame(self, frame, tree):
        key = (tree, frame['path'])
        if key not in self.definitions:
            path = self.source(*key)
            try:
                self.definitions[key] = d.functions(path.read_text(), frame['path']) if path.is_file() else []
            except (SyntaxError, UnicodeError):
                self.definitions[key] = []
        matches = [f for f in self.definitions[key] if f['name'] == frame['name']
                   and frame['code_firstline'] in (f['start'], f['decorator_start'])]
        qualname = matches[0]['qualname'] if len(matches) == 1 else frame.get('code_qualname')
        qualname = qualname or frame['name'] + '@' + str(frame['code_firstline'])
        candidates = self.index.get((frame['path'], qualname), [])
        return dict(frame, ast_qualname=qualname,
                    function_id=frame['path'] + '::' + qualname,
                    static_node=candidates[0] if len(candidates) == 1 else None)

    def distance(self, test, function):
        path, *parts = test.split('::')
        qualname = '.'.join(re.sub(r'\[.*', '', p) for p in parts)
        starts = self.index.get((path, qualname), [])
        if test not in self.distances:
            distances = {n: 0 for n in starts}
            queue = collections.deque(starts)
            while queue:
                node = queue.popleft()
                for target in sorted(self.adj[node]):
                    if target not in distances:
                        distances[target] = distances[node] + 1
                        queue.append(target)
            self.distances[test] = distances
        targets = self.index.get((function['path'], function['qualname']), [])
        values = [self.distances[test][n] for n in targets if n in self.distances[test]]
        return min(values) if values else None

    def missing_edges(self, event, tree):
        frames = [self.frame(f, tree) for f in event['stack']]
        start = event['test_frame_index']
        # The under-test chain is compared separately when first entry was setup.
        if start is None:
            return frames, []
        missing = []
        for ordinal in range(start, len(frames) - 1):
            caller, callee = frames[ordinal:ordinal + 2]
            if callee['static_node'] in self.adj.get(caller['static_node'], set()):
                continue
            sites = [e for e in self.graph['edges'] if e['caller'] == caller['static_node']]
            # Endpoints define an edge; preserve callsite evidence at the observed
            # suspended line. Patched callsites can have shifted coordinates.
            at_line = [e for e in sites if e['line'] == caller['line']] if tree == 'base' else []
            source = self.source(tree, caller['path'])
            line = source.read_text().splitlines()[caller['line'] - 1] if source.is_file() else ''
            cause, reason = classify(caller, callee, line)
            missing.append(dict(stack_edge_index=ordinal - start, caller=caller['function_id'],
                                callee=callee['function_id'], runtime_callsite=caller['path'] + ':' + str(caller['line']),
                                source_line=line.strip(), cause=cause, explanation=reason,
                                caller_static_node=caller['static_node'], callee_static_node=callee['static_node'],
                                static_callsite_evidence=at_line))
        return frames, missing


def classify(caller, callee, source_line):
    """Source-reviewed explanations, separate from the mechanical edge check."""
    if 'self.client.get' in source_line:
        return 'fixture', 'Django installs self.client during test setup; its receiver type is unavailable to this static callsite.'
    if callee['ast_qualname'] == 'BaseForm.errors':
        return 'property', 'Access to form.errors invokes the property getter; the graph indexes explicit calls, not descriptor invocation.'
    if callee['ast_qualname'] == 'Q.deconstruct':
        return 're-export', 'Q is imported through django.db.models; the graph marks its re-exported constructor ambiguous and q.deconstruct unresolved.'
    if 'deprecat' in callee['path'] and callee['name'] in {'wrapper', 'inner'}:
        return 'decorator', 'The runtime callable is the decorator closure; the graph treats the decorated definition as ambiguous.'
    if 'PrimaryKeyWithDefault().save' in source_line:
        return 'inheritance', 'PrimaryKeyWithDefault inherits Model.save; the constructor-result receiver is unresolved (<Call>.save).'
    if caller['name'] == 'test_custom_should_analyze_file' and callee['name'] == 'check':
        return 'inheritance', '_CustomPyLinter inherits PyLinter.check; loop-local receiver evidence remains unresolved.'
    if caller['name'] == 'test_multiprocessing' and callee['name'] == 'check':
        return 'other', 'The loop-local PyLinter receiver is uncertain_or_rebound_name; bounded type propagation does not establish it.'
    if 'pastebin.create_new_paste' in source_line:
        return 'fixture', 'The pastebin fixture returns a plugin module via getplugin; the test parameter has no static module binding.'
    if caller['name'] == 'test_latex_code_role' and callee['name'] == 'build':
        return 'fixture', 'The app fixture supplies a SphinxTestApp instance; the test parameter type is not statically established.'
    if caller['name'] in {'dispatch_visit', 'dispatch_departure'}:
        return 'visitor dispatch', 'The visitor method is obtained dynamically by node type and method name.'
    if callee['path'].startswith('/'):
        return 'other', 'The runtime edge enters an installed dependency outside the repository graph.'
    if callee['static_node'] is None:
        return 'other', 'The runtime callable has no node in the frozen base graph (including patch-only definitions and synthetic code objects).'
    return 'other', 'The observed caller/callee pair has no resolved edge; source and static callsite evidence are retained for inspection.'


def write_csv(path, rows, columns=None):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns or list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def pair_status(traced, untraced):
    valid = {'PASSED', 'FAILED', 'ERROR', 'SKIPPED', 'XFAIL', 'XPASS'}
    if traced['outcome'] not in valid or untraced['outcome'] not in valid:
        return 'UNVERIFIED'
    return 'MATCH' if (traced['outcome'], traced['returncode']) == (untraced['outcome'], untraced['returncode']) else 'TRACE_PERTURBS'


def main():
    inputs = d.load(d.RAW / 'inputs.json')
    prepared = d.load(d.RAW / 'prepared.json')
    records = d.load(d.RAW / 'runtime_runs.json')
    assert inputs['never_use_for_selection'] and inputs['test_list_is_posthoc_only']
    assert prepared['inputs_sha256'] == d.file_sha(d.RAW / 'inputs.json')
    assert len(records) == 52 and len({r['key'] for r in records}) == 52
    for path, expected in inputs['input_sha256'].items():
        assert d.sha(d.git_bytes(inputs['execution_revision'], path)) == expected
    labels = {r['task']: r['frozen_candidate_sha256'] for r in csv.DictReader(io.StringIO(
        d.git_bytes(inputs['execution_revision'], 'reports/next_phases/phase4_posthoc/label_audit/audited_labels.csv').decode()))}
    audit = json.loads(d.git_bytes(inputs['execution_revision'], 'reports/next_phases/phase4_posthoc/analysis.json'))
    groups = { (r['task'], r['test_id']): group for group, rows in audit['witness_groups'].items() for r in rows }
    assert {(r['task'], r['test_id']) for r in inputs['tests']} == set(groups) and len(groups) == 13
    manifest = d.load(d.ROOT / 'reports/v2_scg_paired/scg_source_manifest.json')
    assert manifest['revision'] == inputs['static_revision']
    assert prepared['static_code_sha256'] == manifest['files']
    for path, expected in prepared['static_code_sha256'].items():
        assert d.file_sha(d.RAW / 'static_snapshot' / path) == expected
    by_key = {r['key']: r for r in records}
    for record in records:
        assert record['candidate_sha256'] == labels[record['task']]
        assert record['image_id'] == inputs['specs'][record['task']]['image_id']
        assert record['host_config']['NetworkMode'] == 'none' and record['host_config']['CpuShares'] == 2048
        assert not record['source_receipt']['mismatches']
        assert record['tracer_sha256'] == d.file_sha(d.ROOT / 'tools/runtime_trace/sitecustomize.py')
        for path, expected in record['artifact_sha256'].items():
            assert d.file_sha(d.RAW / path) == expected, path
    rows, chains, pairs, graphs = [], [], [], []
    for iid, task in sorted(prepared['tasks'].items()):
        assert task['spec']['patch_sha256'] == labels[iid]
        assert d.file_sha(task['patch_path']) == labels[iid]
        graph_path = d.RAW / 'graphs' / (iid + '.json.gz')
        with gzip.open(graph_path, 'rt') as stream:
            graph = json.load(stream)
        assert graph['static_revision'] == inputs['static_revision'] and graph['status'] != 'resource_limited'
        comparison = Comparison(iid, task, graph)
        graphs.append(dict(task=iid, status=graph['status'], nodes=len(graph['nodes']), edges=len(graph['edges']),
                           graph_sha256=d.file_sha(graph_path), failures=graph['failures'], counts=graph['counts']))
        for n, test in enumerate(inputs['tests'], 1):
            if test['task'] != iid:
                continue
            for tree in ['base', 'patched']:
                prefix = '%02d-%s-' % (n, tree)
                traced, untraced = by_key[prefix + 'traced'], by_key[prefix + 'untraced']
                events = []
                for path in sorted((d.RAW / 'executions' / (prefix + 'traced') / 'traces').glob('*.jsonl')):
                    events.extend(json.loads(line) for line in path.read_text().splitlines())
                entries = [e for e in events if e['event'] == 'entry']
                entered = any(e['event'] == 'test_enter' for e in events)
                finished = [e for e in events if e['event'] == 'finished']
                errors = [e for e in events if e['event'] == 'trace_error']
                healthy = entered and bool(finished) and all(e['hook_active_at_finish'] and not e['failed'] for e in finished) and not errors
                threads = sorted({e.get('thread_name', '') for e in events if e['event'] == 'thread_start'})
                partial = iid == 'pylint-dev__pylint-6528' and (test['test_id'].endswith('test_multiprocessing[2]') or test['test_id'].endswith('test_jobs_score'))
                reason = ('sys.settrace is local to the installing thread. multiprocessing.Pool task feeder consumes _iterate_file_descrs, which calls expand_modules (and patched _is_ignored_file), in an untraced thread. Absence there is UNKNOWN, not NO.' if partial else '')
                if not healthy:
                    reason = 'No healthy trace completion/test-entry receipt: ' + str(traced.get('reason'))
                match = pair_status(traced, untraced)
                pairs.append(dict(task=iid, test=test['test_id'], group=groups[(iid, test['test_id'])], tree=tree,
                                  traced_outcome=traced['outcome'], untraced_outcome=untraced['outcome'],
                                  traced_exit=traced['returncode'], untraced_exit=untraced['returncode'],
                                  outcome_match=match, trace_status='PARTIAL_THREAD_LIMIT' if partial and healthy else 'TRACED' if healthy else 'UNTRACEABLE',
                                  reason=reason, thread_names=';'.join(threads), test_enter_receipt=entered))
                for changed in task['changed_functions']:
                    distance = comparison.distance(test['test_id'], changed)
                    observed = [e for e in entries if e['function_id'] == changed['id'] and e['phase'] == 'first_any']
                    under = [e for e in entries if e['function_id'] == changed['id'] and e['phase'] == 'first_under_test']
                    first = min(observed, key=lambda e:(e['monotonic'],e['pid'])) if observed else None
                    first_under = min(under, key=lambda e:(e['monotonic'],e['pid'])) if under else None
                    missing, stack, under_stack, under_missing = [], [], [], []
                    if first:
                        stack, missing = comparison.missing_edges(first, tree)
                    if first_under:
                        under_stack, under_missing = comparison.missing_edges(first_under, tree)
                    # Use a real test-rooted stack for the graph comparison. First
                    # invocation during setup has no fabricated test frame or hops.
                    diagnostic = under_missing if first_under else missing
                    gap = diagnostic[0] if diagnostic else None
                    absent = changed[tree] is None
                    unknown = not first and not absent and (not healthy or (partial and changed['path'].endswith('expand_modules.py')))
                    reached = 'YES' if first else 'ABSENT' if absent else 'UNKNOWN' if unknown else 'NO'
                    explanation = 'Definition absent on this tree.' if absent else reason if unknown else ''
                    if not first and not unknown and not absent:
                        explanation = 'No entry recorded in the traced thread.'
                        if changed['qualname'] == 'modify_sys_path':
                            explanation += ' This witness calls pylint.lint.Run in-process; modify_sys_path is the CLI entrypoint path.'
                        if changed['qualname'] == 'PyLinter._discover_files':
                            explanation += ' The recursive-discovery branch is disabled in this witness.'
                    row = dict(task=iid, test=test['test_id'], tree=tree, changed_function=changed['id'],
                               reached_at_runtime=reached, hops=first['hops'] if first else None,
                               reached_statically='YES' if distance is not None else 'NO',
                               first_missing_edge=(gap['caller'] + ' -> ' + gap['callee'] + ' @ ' + gap['runtime_callsite']) if gap else '',
                               cause=gap['cause'] if gap else '', traced_untraced_outcome_match=match,
                               traced_outcome=traced['outcome'], untraced_outcome=untraced['outcome'],
                               entered_under_test=bool(first_under), hops_under_test=first_under['hops'] if first_under else None,
                               static_hops=distance, within_scg_depth_3=distance is not None and 1 <= distance <= 3,
                               patch_only=changed['patch_only'], definition_present=not absent,
                               definition_start=changed[tree]['start'] if not absent else None,
                               definition_end=changed[tree]['end'] if not absent else None,
                               reason=explanation, gap_explanation=gap['explanation'] if gap else '',
                               trace_status=pairs[-1]['trace_status'])
                    rows.append(row)
                    chains.append(dict(task=iid, test=test['test_id'], tree=tree, changed_function=changed['id'],
                                       first_entry_stack=stack, first_under_test_stack=under_stack,
                                       first_entry_pid=first['pid'] if first else None,
                                       first_entry_phase='under_test' if first and first['test_frame_index'] is not None else 'setup_or_runner' if first else None,
                                       missing_edges_under_test=diagnostic))
    rows.sort(key=lambda r:(r['test'],r['task'],r['tree'],r['changed_function']))
    pairs.sort(key=lambda r:(r['test'],r['task'],r['tree']))
    chains.sort(key=lambda r:(r['test'],r['task'],r['tree'],r['changed_function']))
    d.OUT.mkdir(parents=True, exist_ok=True)
    write_csv(d.OUT / 'phase6a_runtime_vs_static.csv', rows)
    write_csv(d.OUT / 'test_outcomes.csv', pairs)
    d.dump(d.OUT / 'runtime_chains.json', chains)
    d.dump(d.OUT / 'changed_functions.json', {iid: {k:task[k] for k in ['changed_functions', 'hunks', 'AST_errors']} for iid, task in sorted(prepared['tasks'].items())})
    d.dump(d.OUT / 'inputs.json', inputs)
    d.dump(d.OUT / 'execution_manifest.json', records)
    d.dump(d.OUT / 'static_graph_manifest.json', dict(revision=inputs['static_revision'], source_sha256=prepared['static_code_sha256'],
          comparison='Regenerated frozen TypeGraph/TypeAmendedGraph, PRIMARY_RESOLVED_ONLY. Baseline amendment manifest chooses the builder; its old pre-typeprop edge hashes are not hashes of this enhanced graph.', graphs=graphs))
    statuses = collections.Counter(r['reached_at_runtime'] for r in rows)
    causes = collections.Counter(r['cause'] for r in rows if r['cause'])
    counts = dict(tests=13, tasks=len(prepared['tasks']), single_test_invocations=len(records), paired_tree_outcomes=len(pairs),
                  outcome_matches=sum(p['outcome_match']=='MATCH' for p in pairs),
                  TRACE_PERTURBS=sum(p['outcome_match']=='TRACE_PERTURBS' for p in pairs),
                  unverified_pairs=sum(p['outcome_match']=='UNVERIFIED' for p in pairs),
                  trace_status=dict(collections.Counter(p['trace_status'] for p in pairs)),
                  changed_functions=sum(len(t['changed_functions']) for t in prepared['tasks'].values()),
                  patch_only_functions=sum(c['patch_only'] for t in prepared['tasks'].values() for c in t['changed_functions']),
                  comparison_rows=len(rows), runtime_status=dict(statuses), first_missing_edge_causes=dict(causes),
                  runtime_entered_but_static_unreachable=sum(r['reached_at_runtime']=='YES' and r['reached_statically']=='NO' for r in rows),
                  runtime_entered_under_test=sum(r['entered_under_test'] for r in rows),
                  static_reachable=sum(r['reached_statically']=='YES' for r in rows),
                  tests_with_changed_entry=len({(r['task'],r['test']) for r in rows if r['reached_at_runtime']=='YES'}),
                  skip_invocations=sum(r['outcome']=='SKIPPED' for r in records))
    d.dump(d.OUT / 'summary.json', counts)
    # Raw captures and superseded attempts are not copied into git. Hash them.
    raw_paths = [d.RAW / name for name in ['inputs.json', 'prepared.json', 'runtime_runs.json']]
    for name in ['executions', 'graphs', 'interrupted_attempt', 'before_trace_receipts']:
        raw_paths.extend(p for p in (d.RAW / name).rglob('*') if p.is_file())
    d.dump(d.OUT / 'raw_artifact_manifest.json', {p.relative_to(d.ROOT).as_posix():d.file_sha(p) for p in sorted(set(raw_paths))})
    table = []
    for n, test in enumerate(inputs['tests'], 1):
        selected = [r for r in rows if r['task']==test['task'] and r['test']==test['test_id']]
        base, patched = [next(p for p in pairs if p['task']==test['task'] and p['test']==test['test_id'] and p['tree']==tree) for tree in ['base','patched']]
        yes = [sum(r['reached_at_runtime']=='YES' and r['tree']==tree for r in selected) for tree in ['base','patched']]
        unknown = sum(r['reached_at_runtime']=='UNKNOWN' for r in selected)
        table.append(dict(number=n, task=test['task'], test=test['test_id'], base_outcome=base['traced_outcome'],
                          patched_outcome=patched['traced_outcome'], base_changed_entered=yes[0], patched_changed_entered=yes[1],
                          static_reachable=sum(r['reached_statically']=='YES' for r in selected), unknown_rows=unknown, outcome_matches='2/2' if base['outcome_match']==patched['outcome_match']=='MATCH' else base['outcome_match']+'/'+patched['outcome_match']))
    write_csv(d.OUT / 'summary_table.csv', table)
    text = ['# Phase 6a: runtime versus static graph', '',
            'Post-hoc diagnostic only. These 7 grader witnesses and 6 regression witnesses come from known outcomes in the Phase 4 report. They must never feed test selection. No selector, executor, image, frozen result or tag is changed.', '',
            'All 13 tests ran alone on each tree, once traced and once untraced (52 invocations). The trees use pristine archived source and that source plus the candidate whose SHA-256 matches audited_labels.csv. Local frozen image IDs, network none and CPU shares 2048 match Phase 4; no test skipped. Django uses tests/runtests.py. Read-only sitecustomize.py is loaded through PYTHONPATH and uses only sys.settrace.', '',
            '## Counts', '', '| Measurement | Count |', '|---|---:|']
    for label, value in [('Tests',13), ('Tasks',counts['tasks']), ('Changed functions',counts['changed_functions']), ('Patch-only functions',counts['patch_only_functions']), ('Test/tree/function rows',len(rows)), ('Entered at runtime',statuses['YES']), ('Not entered in traced thread',statuses['NO']), ('Absent on tree',statuses['ABSENT']), ('Unknown (thread blind spot)',statuses['UNKNOWN']), ('Runtime entries statically reachable',sum(r['reached_at_runtime']=='YES' and r['reached_statically']=='YES' for r in rows)), ('Matched traced/untraced pairs',counts['outcome_matches']), ('TRACE_PERTURBS',counts['TRACE_PERTURBS'])]:
        text.append('| %s | %s |' % (label,value))
    text += ['', 'First missing test-rooted edges: ' + ', '.join('%s = %s' % x for x in sorted(causes.items())) + ' (counts are test/tree/function rows).', '',
             'The comparison uses the SCG source snapshot at ' + inputs['static_revision'] + ', verified against reports/v2_scg_paired/scg_source_manifest.json. It regenerates the same base TypeGraph/TypeAmendedGraph with the same archive inputs. Only resolved edges count. reached_statically is unbounded forward reachability; static_hops and within_scg_depth_3 separately expose the actual SCG depth-3 limit. The graph is never rebuilt from patched source.', '',
             '## Per-test summary', '', '| # | Task | Test | Base / patched | Changed entered base / patched | Unknown rows | Outcome matches |', '|---|---|---|---|---:|---:|---|']
    for row in table:
        text.append('| {number} | {task} | `{test}` | {base_outcome} / {patched_outcome} | {base_changed_entered} / {patched_changed_entered} | {unknown_rows} | {outcome_matches} |'.format(**row))
    text += ['', '## Interpretation and limitations', '',
             '- runtime_chains.json preserves the complete first-entry stack plus first entry under the test. hops is null if the first entry precedes the test (Model._save_table runs during database setup); hops_under_test records its later test-rooted chain. A hop counts each Python frame, including decorators, generators and installed dependencies. These are live stacks, not asynchronous causal chains.',
             '- sys.settrace is local to the installing thread. Pylint-6528 test_multiprocessing[2] and test_jobs_score start a multiprocessing pool whose feeder thread consumes _iterate_file_descrs and calls expand_modules / patched _is_ignored_file. Their absent entries are UNKNOWN. The report records partial tracing for both trees of those tests, rather than inventing non-reachability. No threading.settrace, profiler, monkeypatch or coverage API is used. Other NO values mean no entry observed in the traced thread, not a claim about all threads or native code.',
             '- Fixture receiver types block the first edges in Django client, pytest plugin and Sphinx app chains. The Sphinx chain also includes installed docutils traversal and later visitor dispatch; those are later gaps, not its first missing edge. Inheritance blocks Model.save and the custom PyLinter; re-exports block Q.deconstruct; a decorator closure blocks colormap registration; property access invokes BaseForm.errors without an explicit call edge. Pylint multiprocessing[1] has a loop-local receiver left uncertain by bounded propagation (other). Source lines, graph statuses/reasons and runtime receiver MROs support these source-reviewed explanations in runtime_chains.json.',
             '- A patch-only function has no base graph node. Its first missing edge can still occur earlier in the chain. Functions absent on a tree use ABSENT, not NO. Changed definitions are the union of innermost AST functions owning added/deleted hunk lines, with matched qualified definitions and line ranges on both trees; module edits without a function are retained as unmapped hunk entries.',
             '- Tracer syntax is checked against Python 3.5 grammar and synthetic tests run on the host. The benchmark receipts record actual image interpreters. This is compatibility by standard-library APIs and grammar, not a claim that every Python minor version was executed.',
             '- Interrupted work is retained under local interrupted_attempt and before_trace_receipts, with hashes in raw_artifact_manifest.json. Four early Django source receipts failed on an ASCII filesystem encoding; reading UTF-8 filename bytes corrected the verification without changing the container locale. All final source receipts pass. The earlier incomplete invocation and weaker trace receipts were superseded by complete final pairs.', '',
             '## Artifacts and reproduction', '',
             'phase6a_runtime_vs_static.csv is the requested comparison. test_outcomes.csv gives all 26 pairs and trace limitations; changed_functions.json maps every candidate hunk; runtime_chains.json gives frame/edge evidence. execution_manifest.json, static_graph_manifest.json and raw_artifact_manifest.json bind execution, source and local raw captures by SHA-256. summary_table.csv and summary.json supply the counts above.', '',
             'See tools/runtime_trace/README.md for preparation/run commands. With the local captures present, run `.venv/bin/python tools/runtime_trace/driver.py summarize` twice and compare all output hashes; determinism.json records the verified identical artifact set. Summary generation reads captures only and runs no benchmarks.', '']
    (d.OUT / 'README.md').write_text('\n'.join(text))
    print(json.dumps(counts,sort_keys=True))


if __name__ == '__main__':
    main()
