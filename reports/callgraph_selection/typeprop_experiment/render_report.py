"""Render the research report from validated outputs and explicit source-audit notes."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE/name).read_text())


def csv_rows(name):
    with (HERE/name).open(newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    result=load('enhanced_summary.json');baseline=load('baseline_summary.json');validation=load('validation.json')
    reviews=load('audit_review.json');samples=load('audit_candidates.json')
    assert {r['sample_key'] for r in reviews}=={r['sample_key'] for r in samples}
    audit=Counter(r['classification'] for r in reviews)
    assert not audit['INCORRECT'], 'Fix incorrect new edges before publication'
    timings=load('runtime_sample.json')
    pair={}
    for r in timings:
        pair.setdefault(r['instance_id'],{})[r['variant']]=r
    assert len(pair)==11 and all(set(v)=={'baseline','enhanced'} for v in pair.values())
    fresh_baseline=sum(v['baseline']['graph_seconds'] for v in pair.values())
    fresh_enhanced=sum(v['enhanced']['graph_seconds'] for v in pair.values())
    baseline_rss=max(v['baseline']['process_peak_rss_kib'] for v in pair.values())
    enhanced_rss=max(v['enhanced']['process_peak_rss_kib'] for v in pair.values())
    runtime=dict(tasks=11,baseline_graph_seconds=fresh_baseline,enhanced_graph_seconds=fresh_enhanced,
        ratio=fresh_enhanced/fresh_baseline,relative_increase=fresh_enhanced/fresh_baseline-1,
        baseline_max_process_rss_kib=baseline_rss,enhanced_max_process_rss_kib=enhanced_rss,
        repetitions=1,isolated_processes=True)
    (HERE/'runtime_summary.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n')
    task_metrics=[json.loads(r['type_metrics']) for r in csv_rows('task_summary.csv')]
    selections=csv_rows('selection_summary.csv');changes=csv_rows('selection_changes.csv')
    seed_reachability=csv_rows('changed_seed_reachability.csv')
    seed_paths=csv_rows('changed_seed_reachability_paths.csv')
    assert all(json.loads(r['new_typeprop_ordinals']) for r in seed_paths)
    primary_seed_gains=[r for r in seed_reachability if r['edge_variant']=='PRIMARY_RESOLVED_ONLY']
    only_resolved=[r for r in changes if r['edge_variant']=='PRIMARY_RESOLVED_ONLY']
    assert not only_resolved
    validation.update(tests_passed=False,focused_graph_tests_all_passed=True,focused_tests_passed=104,focused_tests_failed=0,
        project_unit_tests_passed=891,project_unit_tests_failed=3,project_unit_tests_skipped=6,
        project_unit_suite_all_passed=False,
        project_unit_failure_explanations={
            'test_env.py::test_assert_clean_interpreter_passes_under_the_test_runner':'Reused editable venv still lists the original source tree on sys.path; modules under test were explicitly loaded from the isolated source tree.',
            'test_launch_tmux.py::test_resume_contamination_prints_an_instruction_without_a_traceback':'Worktree-local .venv/bin/python is absent; dependency venv is reused by absolute path.',
            'test_selection_ground_truth.py::test_django_16899_selects_admin_checks':'Baseline checkout lacks ignored tests/fixtures/base_trees/django__django-16899.patch.'},
        audit_status='complete: static source inspection by agent, not runtime or independent human adjudication',
        audit_sample_size=len(reviews),audit_supported=audit['SUPPORTED'],audit_questionable=audit['QUESTIONABLE'],
        audit_incorrect=audit['INCORRECT'],resolved_only_selection_changes=0,
        runtime_sample_complete=True,propagation_converged_tasks=sum(m['converged'] for m in task_metrics),
        propagation_max_rounds_observed=max(m['rounds'] for m in task_metrics),
        resolved_only_changed_seed_fanin_gains=len(primary_seed_gains),
        resolved_only_new_test_seed_pairs=sum(int(r['tests_gained']) for r in primary_seed_gains),
        changed_seed_path_rows=len(seed_paths),all_changed_seed_paths_use_typeprop=True,
        final_recommendation='DO NOT ADOPT')
    (HERE/'validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
    repos=csv_rows('repository_summary.csv')
    new=result['new_resolved_by_provenance'];before=result['baseline_calls'];after=result['enhanced_calls']
    transitions=result['transitions'];changed=result['baseline_changed_symbols']
    paragraphs=[
'# Lightweight receiver type propagation: static call-graph experiment','',
'2026-11-02. Local branch `experiment/callgraph-typeprop`; starting commit '
'`0c0c87fda86cf0a2f7c33866020325856e7303de`. This is a new offline experiment, not a revision of the frozen capstone results.','',
'## 1. Question','',
'Can lightweight local and caller-to-parameter type propagation improve static call resolution and reachability from pre-existing tests to changed production symbols? The primary evidence is changed-symbol and test-selection impact; additional graph edges alone are insufficient.','',
'## 2. Baseline','',
'The frozen Amendment 2 overlay uses 79 original `Graph` outputs and four largest-first `AmendedGraph` SymPy outputs, pinned by `amendment2_72ad21b/graph_manifest.json`. Its 83 task snapshots span 11 represented repositories. All 419 manifest-listed graph artifacts were hash-verified before and after evaluation. Each enhanced build reproduced every baseline node and call edge exactly before adding type evidence. Baseline implementations, the original design, Phase 2 outputs and production code are unchanged.','',
'The overlay has 56 complete, 27 partial and zero resource-limited graphs. The older pre-Amendment inventory (56 complete, 23 partial, four limited) is historical context and is not mixed into the comparison denominator. The original all-task named-symbol baseline is 147 resolved / 21 ambiguous / 19 unresolved, totaling 187. Source archives, base commits and frozen candidate patches retain their existing SHA-256 checks.','',
'## 3. Method','',
'`typeprop_graph.py` wraps the existing AST indexer and Graph/AmendedGraph builders. Nodes, lexical bindings and existing import resolution are reused. Single, unconditional assignments within a function or method may supply an exact constructor class; arbitrary factory returns, assignment aliases and module-level instance assignments are excluded. A local assignment must finish before the call on an earlier source line. Direct constructor arguments are supported.','',
'Only calls resolved by the frozen baseline supply positive argument-to-parameter constraints. Required positional, positional-only and keyword-only parameters use explicit argument mapping. Defaults, variadics, expansions and invalid mappings remain unknown. Newly inferred receiver calls are deliberately not additional propagation sources. Parameter-to-parameter transfer uses a synchronous fixed point, bounded at 64 rounds and 16 possible classes per fact. Unknown evidence taints the result; overflow and non-convergence fail closed. Recursion and mutual recursion terminate. All 83 observed fixed points converged within six rounds. No benchmark module is imported or executed, and no external type engine or annotation inference is used.','',
'Facts retain constructor locations or incoming call ordinals/actual arguments. Edge provenance distinguishes the existing resolver, local constructors, caller parameters and transitive caller parameters; enhanced edges also retain baseline status, reason and targets. A transitive attribution means transitive evidence participates, even when another direct witness also exists. Raw facts and enhanced edges are regenerable local artifacts under `task_artifacts/`.','',
'## 4. Safety / conservative rules','',
'- Preserve every previously resolved edge and target list; retain the baseline classification separately for newly refined edges. Several possible receiver classes remain ambiguous. Known and unknown callers together do not become uniquely resolved.',
'- Reject decorated/conditional/inherited classes, custom `__new__`, `__getattr__`, `__getattribute__`, detected reflective class members, uncertain class imports, star-import boundaries and redirected/mutated bindings.',
'- Preserve pre-expansion binding multiplicity: deduplicated unknown bindings must not hide reassignment or deletion. Global/nonlocal mutation and unsupported-scope stores taint their owners. Callable value escapes, including references inside unsupported scopes, block confident parameter facts.',
'- Preserve baseline self/cls behavior, but do not propagate their defining-class metadata as an exact instance type: subclasses may override methods.',
'- Detected attribute writes block new edges with that name. New private method names beginning with `__` and not ending in `__` remain unresolved because Python name mangling is not modeled.',
'- Preserve parse failures, omissions, all graph resource caps, unsupported lambda/comprehension/annotation call classifications, selector eligibility, depths, ranking, identities and budgets.','',
'This is an observed-static-caller model, not an open-world soundness proof. Unseen external calls, reflection through dictionaries, mutation in unmodeled callees and arbitrary monkey-patching remain limitations. A unique static target does not establish successful runtime invocation, dynamic coverage or correctness.','',
'## 5. Synthetic validation','',
'**104 focused and existing graph checks passed.** Coverage includes constructor/import aliases, direct constructor arguments, keyword mapping, set-valued callers, unknown contamination, repeated stores/deletion, recursion, transitive transfer, defaults/expansions, dynamic/inherited classes, resource stops, self handling, private-name mangling, escaped lambda callables and nonlocal/comprehension mutation. Fixture source is parsed only. Exact output: `focused_tests.txt`.','',
'The broader clean-baseline unit suite produced **891 passed, 6 skipped, 3 failed**. Those failures concern the reused editable-venv path, absent worktree-local `.venv/bin/python`, and a missing ignored baseline `.patch` fixture. `project_unit_tests.txt` retains exact failures and `validation.json` gives their test IDs. No unrelated verifier/V2 fix was attempted.','',
'## 6. Corpus-wide results','',
f'All **{result["tasks_compared"]}/83** tasks were compared: 56 complete / 27 partial / 0 resource-limited. There are **{result["parse_failures"]}** parse failures across task snapshots, unchanged; partial graphs remain partial. The builds account for **{result["ast_nodes"]:,}** inspected/preflight AST entries and **{result["call_sites"]:,}** call sites. These counts sum task snapshots, including repeated repository versions; they are not unique-source counts.','',
'| Call-site status | Baseline | Enhanced | Change |','|---|---:|---:|---:|']
    for status in ('resolved','ambiguous','unresolved'):
        paragraphs.append(f'| {status} | {before[status]:,} | {after[status]:,} | {after[status]-before[status]:+,} |')
    paragraphs+=['','| Transition | Call sites |','|---|---:|']
    for transition in ('unresolved -> resolved','unresolved -> ambiguous','ambiguous -> resolved',
                       'resolved -> ambiguous','resolved -> unresolved','ambiguous -> unresolved'):
        paragraphs.append(f'| {transition} | {transitions.get(transition,0):,} |')
    paragraphs+=['',f'New resolved call sites: **{validation["new_resolved_edges"]:,}**; local constructor **{new.get("local_constructor",0):,}**, caller parameter **{new.get("caller_parameter",0):,}**, transitive caller parameter **{new.get("caller_parameter_transitive",0):,}**. '
        f'The caller propagation contribution is **{new.get("caller_parameter",0)+new.get("caller_parameter_transitive",0)}** sites. '
        f'Total resolution rises by **{100*validation["new_resolved_edges"]/result["call_sites"]:.3f} percentage points**; this is not a precision or coverage measurement.','',
        '| Repository | Tasks | Baseline R / A / U | Enhanced R / A / U | New resolved | Selection tasks changed |',
        '|---|---:|---|---|---:|---:|']
    for r in repos:
        b=' / '.join(f'{int(r["baseline_"+k]):,}' for k in ('resolved','ambiguous','unresolved'))
        a=' / '.join(f'{int(r["enhanced_"+k]):,}' for k in ('resolved','ambiguous','unresolved'))
        paragraphs.append(f'| {r["repo"]} | {r["tasks"]} | {b} | {a} | {int(r["new_resolved"]):,} | {r["selection_tasks_changed"]} |')
    paragraphs+=['','`provenance_counts.csv`, `callsite_changes.csv`, `unresolved_reasons_before_after.csv` and `task_summary.csv` retain the detailed inventory. Zero resolved edges became ambiguous or unresolved; independently streamed target-list checks also confirm that every one of the 1,634,110 previously resolved target lists is identical.','',
'## 7. Changed-symbol impact','',
'Frozen candidate patches and the existing `changed_symbols` pipeline were reused for the exact same 187 extracted names. Both graphs yield **147 resolved / 21 ambiguous / 19 unresolved**. There are **zero status changes, zero gains and zero losses**; `changed_symbol_changes.csv` therefore contains its header only. Definition nodes are unchanged, and this extractor matches file/simple-name identity rather than using call reachability, so extra call edges cannot fix that particular lookup.','',
'The separate reachability analysis finds **three affected tasks**. In the qualified partial graph for `pylint-dev__pylint-4970`, **16 existing test definitions** gain resolved-only paths to **two changed methods**, `Similar.run` and `Similar._compute_sims`: 32 new test/seed pairs. Their fan-in rises from 0 to 16 in each variant. All 16 tests were already reachable through the changed `Similar` class constructor; the overall test union remains 17 and its order is unchanged. This is an improvement in per-seed static evidence despite unchanged emitted selections. It occurs in EXTENDED_PARTIAL, not the complete-graph primary stratum. The changed `CreateModel` seed also gains six tests in each of two Django snapshots, under the ambiguous-edge variant only. `changed_seed_reachability.csv` separates all six task/seed/variant rows, and `changed_seed_reachability_paths.csv` retains all 76 new paths without pooling variants. `specificity_changes.csv` records the weight changes.','',
'## 8. Test-selection impact','',
f'The existing Phase 2 `Identities`, `Traversal`, `features` and `rank_candidates` functions were reused for both graphs. Baseline selected counts match the frozen Phase 2 table for all **{len(selections):,}** computed B/C configurations. The 19 stored V2 unions, eligibility strata, depths 1/2/3, budgets 25/50/100/250/500/ALL, specificity formula, identity mapping and ranking are unchanged. Missing/zero-seed configurations retain their frozen eligibility rather than becoming zero selections.','',
'**Resolved-only B/C selections change on zero tasks. C changes on zero tasks at every budget and depth**, so all historical V2 prefix overlaps remain unchanged. Under `SECONDARY_RESOLVED_PLUS_AMBIGUOUS`, B at depth 3 changes on exactly two tasks:','',
'| Task | Frozen stratum | Before / after | Added / removed |','|---|---|---|---|',
'| django__django-13786 | PRIMARY_COMPLETE | 0 / 6 | 6 / 0 |',
'| django__django-15499 | EXTENDED_PARTIAL | 0 / 6 | 6 / 0 |','',
'These are the same six migration test IDs in two snapshots (12 task/test additions, six distinct ID strings). Each of the six budget configurations changes on each task: 12 changed configurations overall. No tests are removed. The path is test → newly resolved `MigrationAutodetector._detect_changes` → existing `generate_created_models` → ambiguous `CreateModel`. The retained ambiguity explains why resolved-only selection stays empty. `selection_changes.csv` lists every changed set, `selection_paths.csv` lists the source callsites and paths, and `specificity_changes.csv` gives fan-in/weight differences. Added tests have a plausible static connection; no execution, cost or defect-detection advantage is established.','',
'Nothing in the primary evaluation confirms that a selected test exercises the changed code.','',
'## 9. Manual edge audit','',
f'The deterministic sample selects one minimum-SHA256 newly resolved callsite per repository/provenance stratum, across all task snapshots. Final sample: **{len(reviews)}**, classified **{audit["SUPPORTED"]} SUPPORTED / {audit["QUESTIONABLE"]} QUESTIONABLE / {audit["INCORRECT"]} INCORRECT** by source-context inspection. This is the agent’s static review, not independent human adjudication or a corpus precision estimate. `audit_candidates.json` retains site/target/constructor/caller-chain snippets, and `audit_review.json` records each decision.','',
'| Repository / provenance | Expression | Classification | Evidence |','|---|---|---|---|']
    by_key={a['sample_key']:a for a in samples}
    for review in reviews:
        a=by_key[review['sample_key']]
        paragraphs.append(f'| {a["repo"]} / {a["edge"]["provenance"]} | `{a["edge"]["expression"]}` | {review["classification"]} | {review["reason"]} |')
    paragraphs+=['',
'Audit-driven corrections are preserved in `incidents.json`. Early self-derived exact types and later lambda/nonlocal boundary cases were rejected before final evaluation. A superseded full-run audit found **one incorrect private-name edge in 15 samples**; all five affected new private-name callsites across the corpus are now rejected, a regression test was added, and all 83 tasks were rerun. The final sample was selected again from the corrected output. Superseded results are not pooled with final results.','',
'Concrete positive propagation examples include `DomainMap` passed into matplotlib’s integrator and `Scanner` passed through pytest’s expression/expr/and_expr/not_expr recursion before `Scanner.accept`. Type annotations are not used to infer these facts.','',
'## 10. Runtime/resource cost','',
f'The final corpus’s graph-build times sum to **{result["enhanced_runtime_seconds"]:.2f} s**; the frozen historical builds sum to **{result["baseline_runtime_seconds"]:.2f} s**. These historical timings are not a controlled overhead estimate. The inference phase itself sums to **{result["inference_seconds"]:.2f} s**; indexing, provenance and retaining the baseline for comparison add other costs. Peak observed process RSS is **{result["peak_process_rss_kib"]/1024**2:.2f} GiB**.','',
f'A matched timing sample uses the lexically first task per represented repository (11 tasks), one build per variant in a fresh process, alternating variant order by repository. Baseline graph time: **{fresh_baseline:.2f} s**; enhanced: **{fresh_enhanced:.2f} s**, **{fresh_enhanced/fresh_baseline:.2f}×** (**{100*(fresh_enhanced/fresh_baseline-1):.1f}%** increase). Largest sampled process RSS: **{baseline_rss/1024**2:.2f} GiB** baseline and **{enhanced_rss/1024**2:.2f} GiB** enhanced. RSS includes interpreter/extraction high-water usage and is not incremental graph allocation. One repetition supports a descriptive comparison, not a stable performance distribution. Raw measurements and sampling rules are in `runtime_sample.json` / `runtime_protocol.json`.','',
'One superseded long-process run exited 139 with a segmentation fault after 81 saved task records. The cause is unestablished; it is not relabeled an AST-quota failure or OOM. A fresh process finished its two pending tasks. The final corrected experiment uses batches of ten tasks per Python process under the same per-task limits. All final tasks completed and all persisted callsites were independently validated. The incident remains a robustness limitation.','',
'## 11. Failure cases','',
'Python remains difficult: factory-return types, aliases between local instances, container-held instances, inherited dispatch, subclassed self/cls, descriptor/decorator behavior, dynamic mutation, unobserved callers, defaults/variadics and unsupported scopes limit useful evidence. Private-name mangling is excluded rather than approximated. Escaped-callable and unknown-input rejection deliberately sacrifices recall. The graph still has millions of external, dynamic or unsupported callsites; its unresolved count is not an internal-call failure rate.','',
'The small source audit caught a real semantic mistake, and cannot guarantee the remaining new edges are all correct. Graph resolution is unique only under the explicit static model; arbitrary dictionary/reflection effects and runtime monkey-patching are not proved absent. Most gains arise from local constructors in repeated snapshots; the advisor’s interprocedural pass adds only 69 resolved sites and does not improve resolved-only changed-seed test selection in this cohort.','',
'## 12. Recommendation','',
'**DO NOT ADOPT** this pass into the production test selector on this evidence. Preserve it as a reproducible research prototype: the proposed propagation works on real code and bounded synthetic cases, but it gives no resolved-only selection benefit for the study’s changed seeds, leaves changed-symbol lookup unchanged, adds measurable cost and has limited audited precision evidence plus a recorded process failure. The resolved-only per-method reachability gain in a partial pylint graph and the secondary-only six-test gain in two Django snapshots are positive static evidence, but neither establishes better regression detection. Broader independent source review, stronger mutation/boundary reasoning, and practical resolved-only gains would be needed before reconsidering adoption. No production policy, ranking, budgets or frozen study classifications change.','',
'### Artifacts and reproduction','',
'All new committed files live in this experiment directory. Bulk per-task graphs/facts, interrupted-run bulk data, caches and logs are ignored. The original dirty worktree’s branch, HEAD, Git status and content hashes of modified/untracked files match its starting fingerprint. Existing frozen graph hashes and tracked baseline files are unchanged. `validation.json` records exact independent checks.','',
'Use the existing dependency interpreter by absolute path (or an equivalent locked environment), clear PYTHONPATH, disable pytest plugin autoload, and pass `-B`. Run the focused command listed below. For a new full evaluation, use a disposable clean worktree based on the starting commit `0c0c87f`, with only this experiment’s source files copied from `experiment/callgraph-typeprop` and no published generated outputs. Keep the local frozen baseline graph directories, archives and patch export accessible; capture a fresh `original_worktree_snapshot.json` with `evaluate.original_state`. The evaluator refuses to silently overwrite a protocol. Start with `evaluate.py --batch-size 10`, then repeat `--resume --batch-size 10` until its `COMPLETE` record. Resume requires the exact same source-file set and hashes as the first batch. Generate reports only after evaluation is complete.','',
'```bash',
'export PYTHONDONTWRITEBYTECODE=1',
"typeprop_python=/home/rajee/projects/cis695-agent-reliability/.venv/bin/python",
'env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$typeprop_python" -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py reports/callgraph_selection/phase2/test_phase2.py reports/callgraph_selection/typeprop_experiment/test_typeprop.py -q -p no:cacheprovider -o addopts=',
'# After the complete evaluation, run:',
'env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/validate_experiment.py',
'env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/benchmark_runtime.py',
'env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/analyze_seed_reachability.py',
'# Review audit_candidates.json and record classifications in audit_review.json, then:',
'env -u PYTHONPATH "$typeprop_python" -B reports/callgraph_selection/typeprop_experiment/render_report.py',
'```','',
'No benchmark code, model API, Docker, oracle evaluation, network acquisition, V2 discovery rerun or Git push was performed.','']
    (HERE/'report.md').write_text('\n'.join(paragraphs))
    outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir())
             if p.is_file() and p.name!='output_manifest.json' and p.suffix in {'.json','.csv','.md','.txt','.py'}}
    (HERE/'output_manifest.json').write_text(json.dumps(outputs,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
