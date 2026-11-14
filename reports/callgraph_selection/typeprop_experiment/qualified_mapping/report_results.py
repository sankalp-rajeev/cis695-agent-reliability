"""Summarize corrected mapping and its input-only effect on frozen selectors."""
import csv
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(name):
    with (HERE/name).open(newline='') as stream:return list(csv.DictReader(stream))


def load(name):return json.loads((HERE/name).read_text())


def integer(row,key):return int(row[key]) if row[key] else None


def main():
    mapping=load('mapping_summary.json');selection=load('selection_comparison.json')
    results=read('mapping_results.csv');old_audit=read('old_resolved_target_audit.csv');ledger=read('legacy_record_comparison.csv')
    rows=read('selection_summary.csv');elig=read('eligibility_comparison.csv');paths=read('new_test_paths.csv')
    counts=Counter(r['status'] for r in results)
    old_resolved={t for r in ledger if r['legacy_status']=='resolved' for t in json.loads(r['legacy_targets'])}
    old_ambiguous={t for r in ledger if r['legacy_status']=='ambiguous' for t in json.loads(r['legacy_targets'])}
    new_resolved={t for r in results if r['status']=='resolved' for t in json.loads(r['targets'])}
    retained=new_resolved&old_resolved;recovered=new_resolved&old_ambiguous;discovered=new_resolved-old_resolved-old_ambiguous
    changes=read('selection_changes.csv')
    groups=[]
    for strategy in ('B','C'):
        for variant in ('PRIMARY_RESOLVED_ONLY','SECONDARY_RESOLVED_PLUS_AMBIGUOUS'):
            group=[r for r in rows if r['strategy']==strategy and r['edge_variant']==variant]
            canonical=[r for r in group if r['depth']=='3' and r['budget']=='ALL']
            paired=[r for r in canonical if r['before_available']==r['after_available']=='True']
            groups.append(dict(strategy=strategy,edge_variant=variant,
                membership_changed_tasks=len({r['instance_id'] for r in group if r['membership_changed']=='True'}),
                order_changed_tasks=len({r['instance_id'] for r in group if r['order_changed']=='True'}),
                availability_changed_tasks=len({r['instance_id'] for r in group if r['availability_changed']=='True'}),
                depth3_all_paired_tasks=len(paired),depth3_all_before_count=sum(int(r['before_count']) for r in paired),
                depth3_all_after_count=sum(int(r['after_count']) for r in paired),
                depth3_all_added=sum(int(r['added_count']) for r in paired),depth3_all_removed=sum(int(r['removed_count']) for r in paired)))
    availability=[r for r in elig if r['before_stratum']!=r['after_stratum'] or r['before_reason']!=r['after_reason']]
    summary=dict(tasks=83,corrected_existing_definition_counts={k:counts[k] for k in ('resolved','ambiguous','unresolved')},
        new_definitions_separate=counts['new_definition'],qualified_definition_records=len(results),
        legacy_failed_records_removed=mapping['false_failure_records_removed'],legacy_actual_ambiguous_name_records_recovered=10,
        recovered_existing_definitions_from_old_ambiguous_names=len(recovered),previous_genuine_existing_definitions_retained=len(retained),
        newly_discovered_existing_edited_definitions=len(discovered),
        legacy_resolved_records_excluded_as_context_or_container=103,legacy_resolved_wrong_scope_reclassified_new=1,
        genuine_ambiguous_mappings_remaining=counts['ambiguous'],source_identity_regressions=mapping['genuine_existing_resolved_targets_regressed'],
        file_analysis_errors=mapping['file_error_records'],outside_definition_file_diagnostics=len(read('file_diagnostics.csv')),
        selection_comparison=selection,by_strategy_and_variant=groups,eligibility_changes=availability,
        graph_resolution_changed=False,selector_logic_changed=False,ranking_or_budgets_changed=False,
        uncertainty='Source identity only; runtime dispatch and coverage remain unproved. New definitions and module edits are not silently converted into base seeds.',
        tests_passed=139)
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    lines=['# Qualified changed-symbol mapping: corrected evaluation','',
'## Result','',
'All **83 tasks** were remapped against the same verified source archives and candidate patches. Corrected existing-definition mapping is **106 resolved / 0 ambiguous / 0 unresolved**. **21 new definitions** are reported separately and never turned into base-graph seeds. There are no file-analysis errors. These are source-identity results, not improved call-target resolution.','',
'The old 147/21/19 totals describe 187 coarse textual name records; the new population is 127 qualified definition records. The denominator changes because unchanged/context names are excluded, one coarse name can represent several actual edited definitions, and missing actual edited definitions are discovered. A numerical increase in resolution rate across these different populations would be misleading.','',
'## Mapping contract','',
'- Validate both hunk coordinate streams, line counts, old-side context and removed text. Reconstruct candidate text only in memory; parse base and candidate source as AST data. Headings and unchanged context cannot nominate a definition.',
'- Attribute actual nonblank edit lines to their innermost named function/class owner, including decorator/header spans. Use qualified lexical names, definition kind, exact base path and original line/column to identify graph nodes.',
'- Compare the owner’s own AST without nested definition bodies or inert pass placeholders. Do not mark an enclosing class/function solely because a child changed. Header, base, decorator, attribute and docstring edits directly owned by a definition remain changes; documentation words never become declarations. Comment/format-only changes do not create seeds.',
'- Separate candidate-only definitions, even when their simple names match existing methods in other scopes. Removed definitions retain their exact base identity. Renames are represented as an old removal plus a new definition; there is no guessed semantic rename correspondence.',
'- Keep repeated fully qualified definitions ambiguous. Missing graph nodes, inconsistent source coordinates, invalid/unsupported source, malformed or mismatched hunks and resource caps fail closed. Synthetic tests exercise these branches even though the corpus has no remaining identity ambiguity.',
'- Do not invent enclosing-class or module fallback seeds. Imports/module-level edits are explicit file diagnostics. Unique source identity does not remove decorator/inheritance/dynamic uncertainty from call edges.','',
'The mapper is isolated in `mapper.py`. It does not edit `build_graphs.py`, the production patch extractor, graph construction/resolution, V2 selection, classifier, ranking, execution budgets or policy. Call-site artifacts are reused byte-for-byte.','',
'## Reconcile the forty diagnosed failures','',
'| Old failed records | Correct treatment |','|---|---|',
'| 10 real simple-name ambiguities | Map 15 actually edited existing qualified definitions; the validator __call__ record expands to six methods. |',
'| 10 unchanged context/stale-header names | Remove from the actual-edit inventory. |',
'| 1 docstring false declaration | Remove labels; it is documentation text, not a class. |',
'| 19 genuine candidate-only definitions | Separate as new, including MultiOutputClassifier.fit, which previously collided with unrelated base fit methods. |','',
'**False failure records removed: 11. Genuine ambiguous mappings remaining: 0.** New definitions are not failures to discover a base node. They remain unseeded because the graph is base-only. The prior 40-case diagnosis is preserved unchanged.','',
'## Audit all previously resolved names','',
f'Of the previous 147 resolved records, **{len(retained)} directly edited source identities are retained**, **103 context/container-only names are excluded**, and **one wrong-scope resolution is reclassified as a new definition**: old View.options.func is not the newly added View.http_method_not_allowed.func. The mapper also distinguishes the new LogCaptureHandler.clear from the actually edited existing LogCaptureFixture.clear; one bare clear name had hidden two different situations.','',
f'The 106 corrected existing identities comprise **{len(retained)} retained prior genuine identities + {len(recovered)} recovered identities behind the ten ambiguous names + {len(discovered)} previously unreported edited existing definitions**. The last group contains body edits whose actual function was not named by the old hunk/header/context extractor. `legacy_record_comparison.csv` traces every old record, and `old_resolved_target_audit.csv` checks ownership on both diff sides so insertion-only changes are included.','',
'**Source-identity regressions: 0.** Every previously resolved definition with a direct owned AST edit remains resolved to the same frozen graph node. This is not a claim of zero test-recall regression: removing broad container/context seeds can remove useful tests if the graph lacks the real method-dispatch paths.','',
'## Changes to selected tests from corrected inputs only','',
'The comparison reuses the frozen enhanced edges and unchanged node inventory, the existing identity normalizer, `Traversal`, `features`, `rank_candidates`, eligibility function, all depths {1,2,3}, all budgets {25,50,100,250,500,ALL}, both edge variants and the same historical 19 V2 unions. Only the mapped seed inputs and derived feature values differ. Old-prefix counts reproduce every one of the 3,528 previously available configurations exactly; the new comparison additionally retains all missing configurations, for 3,672 rows.','',
'Across all configurations, **28 tasks change a paired selected set or prefix**, and **4 tasks change availability** under the unchanged eligibility rules. There are 1,170 changed configuration rows; configurations/depths/budgets are not independent samples. The 28 paired tasks and 4 availability tasks are distinct.','',
'| Strategy / variant | Tasks with changed set/prefix | Tasks with changed order | Tasks with changed availability |','|---|---:|---:|---:|']
    for r in groups:
        lines.append(f"| {r['strategy']} / {r['edge_variant']} | {r['membership_changed_tasks']} | {r['order_changed_tasks']} | {r['availability_changed_tasks']} |")
    lines+=['','The C counts concern budgeted prefixes: its full stored V2 union remains unchanged on all 19 tasks. Different scores/order result from corrected seeds; the ranking rule and budgets are unchanged.','',
'At fixed depth 3 and ALL budget, paired B tasks give the following descriptive counts. Each cell sums task-specific selected IDs, not unique tests across tasks:','',
'| B variant | Paired tasks | Before | After | Added | Removed |','|---|---:|---:|---:|---:|---:|']
    for r in groups:
        if r['strategy']=='B':lines.append(f"| {r['edge_variant']} | {r['depth3_all_paired_tasks']} | {r['depth3_all_before_count']} | {r['depth3_all_after_count']} | {r['depth3_all_added']} | {r['depth3_all_removed']} |")
    lines+=['','The reduction is mainly the consequence of excluding broad class/context seeds, not newly demonstrated execution efficiency. **No paired unbudgeted depth-3 B tests are added in either variant.** This sharp reduction may expose missing real call paths and cannot be presented as a runtime saving or a recall improvement.','',
'Six new path witnesses occur at smaller depths in `django__django-10973`, exclusively in the secondary ambiguous-edge variant: test_sigint_handler at depth 1, and test_accent/test_basic/test_column/test_escape_characters/test_nopass at depth 2. They connect to the newly identified existing DatabaseClient.runshell_db method. The ambiguous edge remains ambiguous; mapping has not promoted it to a resolved call. At depth 3 these tests were already reachable from other old seeds, so they do not increase that unbudgeted union. `new_test_paths.csv` retains every witness.','',
'### Availability is not an empty selection','',
'| Task | Before | After | Reason |','|---|---|---|---|']
    for r in availability:
        lines.append(f"| {r['instance_id']} | {r['before_stratum']} / {r['before_reason']} | {r['after_stratum']} / {r['after_reason']} | Seeds {r['before_seed_count']} → {r['after_seed_count']} |")
    lines+=['',
'Django-13569 changes from a measured empty B selection to unavailable because its sole real change is a newly added method. Matplotlib-24637, SymPy-13480 and SymPy-24562 become evaluable from newly identified existing definitions but yield measured empty B sets at depth 3. None of these transitions is relabeled as adding/removing tests from a known empty set. The prior eligibility freeze and registered C1/C2/C3 results are not rewritten or reinterpreted.','',
'## Tests, validation and limitations','',
'**139 focused mapper and existing graph/selector checks passed** (`tests.txt`). Coverage includes same names in separate scopes, multiple edited owners, stale headings, unchanged neighbors, docstring text, added overrides, nested/async definitions, decorator/base/attribute edits, duplicate qualified names, deletion/rename, insertion-only body edits, nonsemantic changes, missing/inconsistent graph nodes, parse errors, exact hunk validation, multiline offsets, newline/encoding handling and resource caps. Benchmark fixture source is parsed, not executed.','',
'All 83 mappings succeeded, with no ambiguous/unresolved definition or file-error records. Twelve file diagnostics retain edits outside named definitions, such as imports and module statements. They are not converted to module seeds and must not be mistaken for proof that every changed patch line is covered. The zero unresolved count refers to named-definition identity, not module-level semantics, runtime dispatch or dynamic coverage.','',
'Graph files, call-resolver source, selector source, ranking/budget constants, the previous experiment results and the original dirty worktree remain unchanged. The independent validator checks exact source node coordinates, new-definition absence from the base AST, old-record reconciliation, both-sided old-target retention, graph hashes and all prior file hashes.','',
'One early AST comparison bug was caught by a focused keyword-only-default test: an explicit AST None placeholder must not be confused with an intentionally omitted nested-definition marker. A distinct sentinel fixes it; the full mapping was repeated. An audit refinement also added candidate-side insertion-only ownership and a mixed existing/new coarse-name label; the final full comparison uses the recorded final code hashes. Superseded run metadata is retained under `attempts/`, separately from final results.','',
'This is a bounded direct-edit identity model. It does not prove complete semantic impact across enclosing scopes, implicit callbacks, decorators, factories or module imports. Accurate identity plus a sparse graph can select fewer tests, including potentially useful ones previously reached through broad class seeds. Runtime coverage/recall must be measured separately before using these changes in a production selection policy.','',
'## Artifacts and reproduction','',
'- `mapping_results.csv`: every corrected qualified definition and source-to-graph identity.',
'- `new_definitions.csv` / `uncertain_mappings.csv`: separate candidate-only and uncertain populations.',
'- `legacy_record_comparison.csv` / `old_resolved_target_audit.csv`: complete old-record and regression reconciliation.',
'- `selection_summary.csv` / `selection_changes.csv` / `eligibility_comparison.csv`: all configurations, exact changed memberships and availability reasons.',
'- `new_test_paths.csv`: unchanged-graph witnesses for newly reached tests.',
'- `summary.json` / `validation.json`: machine-readable results and preservation checks.','',
'To reproduce, use a disposable source copy with the same directory hierarchy and frozen local archives/graphs/patch export, preserving the prior experiment/diagnosis inputs. Keep only this subdirectory’s source, README and preservation_before.json (whose prior-input hashes must still match) before starting a fresh run (published outputs must be archived first). The map stage refuses to overwrite an existing protocol. Source under test must resolve to that copy, and output paths must remain inside this subdirectory.','',
'```bash',
'export PYTHONDONTWRITEBYTECODE=1',
'mapping_python=/home/rajee/projects/cis695-agent-reliability/.venv/bin/python',
'env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$mapping_python" -B -m pytest reports/callgraph_selection/typeprop_experiment/qualified_mapping/test_mapper.py reports/callgraph_selection/typeprop_experiment/test_typeprop.py reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py reports/callgraph_selection/phase2/test_phase2.py -q -p no:cacheprovider -o addopts=',
'env -u PYTHONPATH "$mapping_python" -B reports/callgraph_selection/typeprop_experiment/qualified_mapping/run_mapping.py --stage map',
'env -u PYTHONPATH "$mapping_python" -B reports/callgraph_selection/typeprop_experiment/qualified_mapping/run_mapping.py --stage select',
'env -u PYTHONPATH "$mapping_python" -B reports/callgraph_selection/typeprop_experiment/qualified_mapping/report_results.py',
'env -u PYTHONPATH "$mapping_python" -B reports/callgraph_selection/typeprop_experiment/qualified_mapping/validate_mapping.py',
'```','',
'No graph feature, V2 policy, classifier, ranking or budget was changed. No benchmark tests/model APIs/Docker/oracle evaluation or Git push were run.','']
    (HERE/'report.md').write_text('\n'.join(lines))
    print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':main()
