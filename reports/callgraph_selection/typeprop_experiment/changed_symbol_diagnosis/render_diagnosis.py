"""Assemble the forty source-backed diagnoses; no analysis implementation changes."""
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXP=HERE.parent;CG=EXP.parent;ROOT=CG.parents[1]
sys.path[:0]=[str(EXP),str(CG),str(CG/'phase2'),str(ROOT/'src')]
from evaluate import csv_write,dump,original_state
from callgraph_selector import VARIANTS

NOTES={
'C01':'The hunk header says _format_value, but every changed executable line is inside the separate module-level _format_float. Neither Card._format_value nor module _format_value is edited.',
'C02':'The patch adds ModelAdmin.get_inlines and changes get_inline_instances to call it. The class exists at base; this method does not.',
'C03':'Six __call__ bodies are edited: RegexValidator, URLValidator, EmailValidator, DecimalValidator, FileExtensionValidator and ProhibitNullCharactersValidator. The mapper collapses their qualified identities to __call__, also including unedited BaseValidator.__call__. The correct result is a set of six edited definitions, not one guessed method or all seven candidates.',
'C04':'__eq__ appears only as following context after edited validator __call__ bodies. No equality method body or definition is edited.',
'C05':'stackplot.get_next_color is a newly added nested function in the colors-supplied branch. The other branch binds get_next_color to axes._get_lines.get_next_color; a candidate overlay must retain this conditional/mixed binding.',
'C06':'Only AnchoredLocatorBase.__call__ receives the renderer-is-None handling. InsetPosition.__call__ is another method in the file and is not edited.',
'C07':'The changed call is _LocIndexer.__getitem__: sel(**key) becomes sel(key). The following __setitem__ definition is unchanged context.',
'C08':'The edit changes DataArrayRolling.__iter__ window bounds/yield behavior. The next construct declaration is unchanged context; none of the three construct implementations is edited.',
'C09':'_is_ignored_file is a new module-level helper called twice from the existing expand_modules body. No base AST definition with that name exists.',
'C10':'MultiOutputClassifier.__init__ is unchanged context before the newly inserted fit override. No constructor in the file is edited.',
'C11':'The candidate adds MultiOutputClassifier.fit, an override absent from the base class. The four base fit nodes belong to MultiOutputEstimator, _BaseChain, ClassifierChain and RegressorChain. Mapping to any of them as the changed definition would be incorrect, even though an explicit super().fit call invokes inherited behavior.',
'C12':'The added docstring line "class labels for each estimator in the chain." matches the extractor regex as if it were a class declaration. There is no AST function/class named labels in either version.',
'C13':'MultiOutputClassifier.predict_proba is unchanged following context after the newly inserted fit method. Neither base predict_proba body is edited.',
'C14':'All executable edits belong to BaseLibSVM._sparse_fit. The next predict declaration is unchanged context; neither BaseLibSVM.predict nor BaseSVC.predict is edited.',
'C15':'Only UnrecognizedUnit.__eq__ gains self-identity/exception handling. UnitBase.__eq__ is a separate, unedited method in the same file.',
'C16':'UnrecognizedUnit.__ne__ is unchanged following context after the edited __eq__. No inequality method is edited.',
'C17':'The edited get body is TemplateView.get, which now wraps URL kwargs. RedirectView.get is an unedited same-name method.',
'C18':'The patch adds Random.get_group_by_cols to the existing Random class. A missing local override at base is not evidence of an incomplete file or a failed import.',
'C19':'BoundField._did_change is a new method containing logic moved/refactored from form changed-data handling. Its class exists, but the method has no base node.',
'C20':'BaseForm._bound_items is newly added; _clean_fields and changed_data are rewritten to call it. BaseForm itself already has a graph node.',
'C21':'The edit changes View.http_method_not_allowed and introduces its nested async func. View.options is the next unchanged declaration, not an edited method.',
'C22':'AbstractBaseUser._get_session_auth_hash is a new helper extracted from get_session_auth_hash; the old body location does not create a base node under the new name.',
'C23':'AbstractBaseUser.get_session_auth_fallback_hash is a new generator method over configured fallback secrets. The primary mapping failure is absence at base, independent of whether fallback values are runtime data.',
'C24':'Only LogNorm.autoscale changes copy=False to copy=True. Normalize.autoscale and CenteredNorm.autoscale are unedited same-name methods.',
'C25':'Only LogNorm.autoscale_None gains the vmin/vmax guard and copy=True. Normalize, TwoSlopeNorm and CenteredNorm same-name methods are unedited.',
'C26':'LogCaptureHandler.handleError is unchanged context immediately following the new clear method. The actual edits add LogCaptureHandler.clear and change LogCaptureFixture.clear.',
'C27':'deserialize_repr_crash is newly nested inside BaseReport._from_json. It returns a ReprFileLocation or None and has no base lexical definition.',
'C28':'deserialize_repr_entry is newly nested inside BaseReport._from_json, refactoring entry reconstruction. Its candidate lexical binding does not exist in the base graph.',
'C29':'deserialize_repr_traceback is newly nested inside BaseReport._from_json and calls the new entry helper. The function is not omitted by a graph resource stop.',
'C30':'serialize_repr_crash is newly nested inside BaseReport._to_json. It handles optional crash representations and has no base definition.',
'C31':'serialize_repr_entry is newly nested inside BaseReport._to_json, extracting existing serialization logic into a new lexical function.',
'C32':'serialize_repr_traceback is newly nested inside BaseReport._to_json and calls serialize_repr_entry. Both are introduced only by the patch.',
'C33':'postpone_tearDown is newly nested inside TestCaseFunction.runtest and passed to setattr(self._testcase, "tearDown", ...). Indexing the new function is static; proving its runtime callback dispatch would require additional analysis and must not be guessed.',
'C34':'_get_option_indent is a new module-level helper called from LiteralInclude.run. It parses directive option indentation and is absent from the complete base AST.',
'C35':'Only Message.__init__ changes location deduplication. Catalog, MsgOrigin, GettextRenderer and LocalTimeZone constructors are separate, unedited definitions.',
'C36':'The edited eval is coth.eval: a cotm typo becomes cothm in its body. Ten other classes define eval in the same file; the existing node retains its classmethod decorator.',
'C37':'Dagger.__mul__ is newly added to an existing Dagger class. The base graph has constructor paths to Dagger, but has no node for this new multiplication method.',
'C38':'Dagger.__rmul__ is a newly added reflected-multiplication method. Existing class reachability is not a call edge to this new method and must not be substituted as proof of test coverage.',
'C39':'Only IdentityOperator.__mul__ gains the Dagger case. Operator.__mul__ is a separate, unedited same-name method.',
'C40':'Only Rational.__new__ gains string conversion logic. Eleven other constructors in numbers.py are unedited candidates. Rational.__new__ is decorated; identifying its source node does not prove a unique runtime constructor edge.'}

SECONDARY={
'C03':'Implicit callable-instance invocation is not expanded into __call__ edges; the current wrapper refines explicit receiver attributes only. Target nodes have zero recorded incoming edges.',
'C06':'Callable locator callback dispatch/inheritance remains separate from identity mapping. The method node has zero recorded incoming edges.',
'C15':'Comparison/operator syntax is not emitted as an __eq__ call edge by the AST-call-only indexer. The target has zero incoming edges.',
'C17':'Django View.dispatch obtains handler via getattr(self, request.method.lower(), ...); TemplateView inherits the dispatch chain. No recorded edge reaches TemplateView.get.',
'C24':'LogNorm inherits Normalize; existing constructor/receiver uncertainty and the conservative inheritance checks do not supply a call edge to this autoscale method.',
'C25':'The same inherited LogNorm receiver problem remains; there is no recorded incoming edge to LogNorm.autoscale_None.',
'C35':'Message(...) calls target the class node. The original graph explicitly does not synthesize a class-to-__init__ invocation edge.',
'C36':'SymPy Function construction/framework dispatch to classmethod eval is not connected to coth.eval; the method is decorated and has zero incoming edges.',
'C39':'Binary operator dispatch to IdentityOperator.__mul__ is not an AST Call edge in this graph. The method has zero incoming edges.',
'C40':'Rational(...) constructor calls reach the class, not its decorated __new__ body. The graph deliberately does not invent this invocation edge.'}


def main():
    raw=json.loads((HERE/'inspection.json').read_text());source={r['case_id']:r for r in json.loads((HERE/'source_evidence.json').read_text())}
    downstream={r['case_id']:r for r in json.loads((HERE/'downstream_evidence.json').read_text())}
    assert len(raw)==40 and set(NOTES)=={r['case_id'] for r in raw}
    rows=[]
    for r in raw:
        case=r['case_id'];e=source[case];d=downstream[case];category=r['root_cause_category']
        assert not any(f.get('path')==r['file'] for f in e['graph_failures']),case
        if category=='qualified_scope_lost_by_simple_name_mapper':
            exact=f"File/simple-name lookup finds {len(e['base_definitions'])} definitions, because changed_symbols discards qualified scope. Source edits identify: {', '.join(r['actual_changed_base_definitions'])}."
            fix='Proposed only: map actual diff edit coordinates to qualified base AST definitions. Keep every genuinely edited definition (including multiple validator methods); exclude unedited same-name candidates. This repairs seed identity, not missing call edges.'
            sub='existing_changed_definition_scope_collision'
        elif category=='unchanged_context_or_stale_hunk_header_name':
            exact='The name is extracted solely from unchanged diff context or a stale enclosing hunk heading. No corresponding definition is edited.'
            fix='Proposed only: AST-check executable edits and enclosing definitions; do not promote adjacent context declarations or stale headers into changed seeds. Remove this false failure rather than claim a new resolution.'
            sub='stale_header' if all(x['side']=='hunk_header' for x in e['extractor_occurrences']) else 'unchanged_neighbor_definition'
        elif category=='docstring_text_misidentified_as_definition':
            exact='The textual def/class regex matches class labels inside a class docstring; base and candidate ASTs contain no definition named labels.'
            fix='Proposed only: require an actual AST declaration; discard this docstring artifact. It is not an unresolved callable.'
            sub='docstring_false_class_declaration'
        else:
            quals=r['added_candidate_definitions']
            exact=f"Candidate-only definition(s) {', '.join(quals)} do not exist in the verified parsed base file. The frozen graph consumes base source only."
            if r['current_status']=='ambiguous':exact+=' Its simple name collides with unrelated base definitions, yielding a misleading ambiguous status rather than candidate-only absence.'
            fix='Possible, not implemented: an explicitly versioned candidate-source overlay for the new definition and source-proven local calls. This changes the base-only input contract and needs reviewed call/dispatch, decorator, conditional and alias safeguards; do not substitute an enclosing class or an ancestor method.'
            qual=quals[0];parts=qual.split('.')
            definition=e['new_matching_definitions'][0]
            enclosing=[x for x in e['relevant_candidate_contexts'] if x['qualname']==qual]
            if len(parts)==1:sub='new_module_helper'
            elif case in {'C05','C27','C28','C29','C30','C31','C32','C33'}:sub='new_nested_helper'
            else:sub='new_class_method'
        row=dict(case_id=case,task_id=r['task_id'],repository=r['repository'],file=r['file'],changed_symbol=r['changed_symbol'],
            current_status=r['current_status'],exact_failure_reason=exact,resolver_diagnostic=r['resolver_reason'],
            source_code_explanation=NOTES[case],root_cause_category=category,subcategory=sub,
            fixability_classification=r['fixability'],
            fixability_rationale=('Bounded AST-aware mapping/extraction can remove the textual ambiguity or false record without runtime inference.' if r['fixability']=='A' else 'The name/owner is statically identifiable, but resolving it in a usable call graph requires a candidate-source input change plus new call connections; classification concerns end-to-end graph use, not difficulty parsing a def.'),
            potential_static_fix=fix,confidence_in_diagnosis='HIGH: exact verified base file, exact candidate diff reconstruction, AST definition ownership and frozen mapper diagnostic agree',
            graph_status=r['graph_status'],source_file_status='parsed_and_indexed',infrastructure_resource_cause=False,
            actual_changed_base_definitions=r['actual_changed_base_definitions'],candidate_only_definitions=r['added_candidate_definitions'],
            existing_graph_candidate_definitions=r['matched_base_definitions'],
            downstream_barrier=SECONDARY.get(case,'No new/base-call-path claim inferred from the name-level diagnostic. Existing enclosing-anchor reachability, where available, is retained as separate evidence.'),
            actual_target_incoming_edge_counts=d['actual_base_target_incoming_edge_counts'],
            existing_target_and_anchor_reachability=r['reachability'],evidence_reference=f'source_evidence.json#{case}; downstream_evidence.json#{case}')
        rows.append(row)
    root_counts=Counter(r['root_cause_category'] for r in rows);class_counts=Counter(r['fixability_classification'] for r in rows)
    genuine=[r for r in raw if r['root_cause_category']=='qualified_scope_lost_by_simple_name_mapper']
    genuine_nodes=[x for r in genuine for x in r['reachability'] if x['role']=='changed_base_definition']
    assert len(genuine)==10 and len(genuine_nodes)==15
    assert all(not downstream[r['case_id']]['actual_base_target_incoming_edge_counts'] for r in genuine)
    assert all(x[v]['emittable_tests']==0 for x in genuine_nodes for v in VARIANTS)
    summary=dict(experiment_commit='df3bd9bf21c4633e1353ef7af294503aaf29dfd8',cases=40,tasks=len({r['task_id'] for r in rows}),
        status_counts=dict(Counter(r['current_status'] for r in rows)),root_cause_counts=dict(root_counts),
        candidate_only_subcategories=dict(Counter(r['subcategory'] for r in rows if r['root_cause_category']=='candidate_only_definition_absent_from_base')),
        fixability_counts={k:class_counts[k] for k in 'ABCD'},
        biggest_single_category='candidate_only_definition_absent_from_base',biggest_single_category_cases=19,
        false_changed_symbol_records=11,genuine_existing_changed_name_collisions=10,genuine_existing_changed_definitions=15,
        best_next_bounded_static_work='AST- and edit-aware qualified changed-symbol identification, as a diagnostic prerequisite; no further receiver feature is justified by this cohort alone.',
        plausibly_resolvable_failed_name_records=10,additional_false_records_removable=11,
        candidate_only_records_not_recoverable_by_more_base_graph_inference=19,
        existing_reachable_tests_to_the_15_actual_base_targets=0,
        mapper_only_newly_reachable_tests_demonstrated=0,
        mapping_only_selection_gain='No recovered tests are supported by the existing graph: all 15 actual target nodes have zero incoming edges. Future invocation/dispatch work would be a separate, reviewed experiment.',
        partial_graph_case_count=sum(r['graph_status']=='partial' for r in rows),direct_infrastructure_resource_causes=0,
        candidate_only_absence_not_runtime_dynamic=True,
        fixability_scope='A concerns exact identity/accounting fixes. B means candidate graph input/call linkage changes are needed for end-to-end use; candidate AST identity itself is known. C/D are zero for the primary causes, not claims that all downstream Python behavior is static.',
        no_next_feature_implemented=True,no_selector_or_policy_change=True,graph_rebuild=False,
        frozen_inputs_unchanged=True,outputs=['cases.csv','summary.json','report.md','source_evidence.json','downstream_evidence.json','inspection_validation.json','existing_paths.csv'])
    csv_write(HERE/'cases.csv',rows);dump(HERE/'summary.json',summary)
    lines=['# Diagnosis of the forty failed changed-symbol records','',
'## Finding','',
'The 40 rows are not forty failures of receiver-type inference. Every recorded status is assigned by `build_graphs.changed_symbols()` using `(base_path, simple_name)`, without consulting `Graph.resolve()` or its call-site classifications. Graph construction has already completed; changed-name status is a separate lookup. The mapping index explicitly strips qualified scope with `qualname.rsplit(".", 1)[-1]`. The production `touched_symbols()` extractor scans added, removed, context and hunk-header text using a def/class regex. These two operations explain every label in this inventory.','',
'No graph, selector, ranker, budget, classifier or policy was changed. Existing graphs were queried for paths only; no revised seed list or selected test set was emitted. All previous experiment artifacts remain unchanged.','',
'## Counts and meaning','',
'| Primary cause | Cases | A/B/C/D | Meaning |','|---|---:|---|---|',
'| Candidate-only definition absent from base | 19 | B | 18 unresolved plus one misleading ambiguous new override; 9 new methods, 8 nested helpers, 2 module helpers. |',
'| Qualified scope lost by file/simple-name matching | 10 | A | Real edits correspond to 15 existing graph definitions; six validator methods share one coarse __call__ row. |',
'| Unchanged context or stale hunk heading | 10 | A | Unedited neighboring declarations or an earlier enclosing header are incorrectly counted as changed symbols. |',
'| Docstring text treated as a declaration | 1 | A | The line `class labels for each estimator in the chain.` is documentation, not a class. |','',
'**A = 21, B = 19, C = 0, D = 0.** A does not mean 21 missing call edges can be recovered: 11 of those rows should be removed from the failed-changed-code inventory, while 10 coarse names can be mapped to their actual edited definitions. B does not mean new functions require runtime discovery: their candidate AST identities are exact, but using them requires changing the base-only graph input boundary and establishing call connections. That is a larger, potentially risky experiment. C/D are counts of these rows’ primary causes, not assertions that downstream Python dispatch is fully static.','',
'## Why type propagation could not change these totals','',
'The pass refines edges while preserving definition nodes and the old file/simple-name mapper. It cannot distinguish two methods sharing a simple name for that mapper; cannot make a candidate-introduced function appear in a base-only graph; and cannot remove textual extractor false positives. Consequently, general call-site improvements do not imply improvements in these name-status totals. In particular, sklearn MultiOutputClassifier.fit is newly introduced by the patch yet collides with four unrelated base fit definitions. Resolving it to an ancestor or an arbitrary fit implementation would create false certainty.','',
'## Best next bounded static work','',
'The best-supported bounded next step is **AST- and edit-aware qualified changed-symbol identification**, with an explicit distinction among modified existing definitions, genuinely new definitions and context-only names. This is recommended as a prerequisite, not as another receiver-propagation feature. It could accurately map **10 of the 40 coarse records to 15 existing edited definitions** and remove **11 spurious records**. Do not describe that as 21 newly resolved changed symbols. The 19 genuinely new definitions remain outside the current base-source universe; indexing them requires a separately reviewed candidate-aware design.','',
'For the multi-validator __call__ row, six definitions are actually edited and BaseValidator.__call__ is not. The mapper must represent all six qualified edited definitions without choosing a single method or indiscriminately promoting all same-name methods. No proposed mapping was fed back into the graph or selector in this diagnosis.','',
'## Would this change test selection?','',
'**Not by itself on the stored graph. All 15 existing edited target nodes identified for the ten genuine ambiguity rows have zero incoming call edges, and zero emittable tests within depth 3 in both frozen traversal variants.** Correct seed identity is necessary, but it cannot manufacture missing invocation paths. There is no demonstrated mapper-only addition to the selected test set. No ranking or counterfactual selector was executed.','',
'The separate downstream barriers visible in the source/model include implicit __call__/comparison/operator invocation, constructors that target classes without __init__/__new__ edges, inherited receiver dispatch, Django request-method getattr dispatch and SymPy classmethod-eval construction hooks. Their presence does not change the primary mapper diagnostic. `downstream_evidence.json` records actual zero incoming-edge counts, class metadata and constructor references; these observations justify further case-level design review, not a claim that a generic dispatch feature would safely recover tests.','',
'Potential class anchors illustrate the danger of overstating benefit: Rational’s class has 1,215 resolved-only reachable test IDs and 1,244 in the secondary variant, coth’s class has 9 and IdentityOperator’s class has 3, yet their changed method bodies have zero incoming edges. Rational.__new__ is decorated and symbolic construction has custom semantics. Using those broad class paths as method coverage would be unjustified. Message.__init__ has no reachable class-anchor tests either, so the seemingly simpler constructor case also offers no observed selection gain here.','',
'For the two new Dagger operator methods, the existing Dagger class has 105 resolved-only reachable test IDs outside that task’s existing changed-seed union. This is an exploratory class-level ceiling, **not** 105 tests proven to reach __mul__/__rmul__, and not permission to substitute a whole-class seed. Several new nested helpers likewise have lexical enclosing anchors but no demonstrated graph path to the new body. `existing_paths.csv` separates such anchor paths from paths to actual changed base definitions.','',
'No single new call-graph feature is justified for adoption by this diagnosis alone. If a later edge experiment is proposed, it should name one actual qualified target and one source-backed invocation chain and retain dynamic/decorator/inheritance uncertainty. Improving generic resolved-call counts is not an adequate success criterion.','',
'## Incompleteness and resource limits','',
f'{summary["partial_graph_case_count"]} of the 40 rows occur in partial graphs. **Zero primary failures are caused by parse omissions, AST quotas or resource stops.** Every changed file was indexed/parsed, every claimed base target is present, and none of the recorded file-level failures concerns the changed file. New-definition absence was verified in the full base file, not inferred from an incomplete graph. Partial graphs may still hide downstream paths elsewhere; zero paths describes the stored graph and is not proof about runtime coverage or a hypothetical fully complete graph. Partial status does not imply dynamic analysis is needed.','',
'## Evidence and validation','',
'All 40 cases across 25 tasks were checked against exact archive hashes/PAX base commits and hash-verified frozen candidate patches. Unified diff context/removal text and hunk counts were validated before reconstructing candidate file text in memory; both versions were parsed as AST data without executing benchmark code. Reconstruction is only an inspection view, not graph construction or a patch application to the benchmark checkout. The 419 frozen graph artifacts were hash-checked. Prior experiment files and the original dirty worktree fingerprint were verified unchanged.','',
'`cases.csv` contains the requested task/repository, symbol/status, exact reason, original diagnostic, source explanation, category, A/B/C/D, proposed fix and confidence. `source_evidence.json` retains exact relevant patch blocks, AST scope spans, extractor occurrences and source snippets for every case. `downstream_evidence.json` separates method-node facts from class-anchor and candidate-call syntax. `inspection_validation.json` records the read-only checks. Confidence is high for the primary source/mapping diagnosis; proposed downstream benefit is intentionally not assigned that confidence.','',
'This diagnosis is restricted to the requested forty failed name records. It does not validate the other 147 resolved identities, candidate correctness, runtime coverage or the completeness of the changed-symbol inventory. Previous type-propagation outputs remain authoritative and were not rewritten.','',
'## Per-case findings','',
'| Case | Task | Symbol | Status | Category / class | Source finding |','|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['case_id']} | {r['task_id']} | `{r['changed_symbol']}` | {r['current_status']} | {r['root_cause_category']} / {r['fixability_classification']} | {r['source_code_explanation']} |")
    lines+=['','## Reproduce the diagnostic only','',
'From the experimental worktree, using the existing dependency interpreter and local frozen inputs:',
'```bash',
'env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/inspect_cases.py',
'env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/inspect_downstream.py',
'env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/render_diagnosis.py',
'```','',
'These scripts only write this diagnostic subdirectory. They do not change the mapping implementation, graph construction, seed policy, V2, ranking, budgets, classifier or decision policy. No commit or push is part of this diagnosis.','']
    (HERE/'report.md').write_text('\n'.join(lines))
    # Every prior tracked experiment file remains identical to its committed bytes.
    tracked=subprocess.check_output(['git','ls-files','-z','reports/callgraph_selection/typeprop_experiment'],cwd=ROOT).decode().split('\0')
    for path in filter(None,tracked):
        assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT),path
    assert not subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode()
    protocol=json.loads((EXP/'protocol.json').read_text())
    assert original_state(Path(protocol['original_worktree']))==json.loads((EXP/'original_worktree_snapshot.json').read_text())
    dump(HERE/'output_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir())
                                  if p.is_file() and p.name!='output_hashes.json' and p.suffix!='.log'})
    print(json.dumps(summary,indent=2,sort_keys=True))


if __name__=='__main__':main()
