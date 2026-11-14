# Diagnosis of the forty failed changed-symbol records

## Finding

The 40 rows are not forty failures of receiver-type inference. Every recorded status is assigned by `build_graphs.changed_symbols()` using `(base_path, simple_name)`, without consulting `Graph.resolve()` or its call-site classifications. Graph construction has already completed; changed-name status is a separate lookup. The mapping index explicitly strips qualified scope with `qualname.rsplit(".", 1)[-1]`. The production `touched_symbols()` extractor scans added, removed, context and hunk-header text using a def/class regex. These two operations explain every label in this inventory.

No graph, selector, ranker, budget, classifier or policy was changed. Existing graphs were queried for paths only; no revised seed list or selected test set was emitted. All previous experiment artifacts remain unchanged.

## Counts and meaning

| Primary cause | Cases | A/B/C/D | Meaning |
|---|---:|---|---|
| Candidate-only definition absent from base | 19 | B | 18 unresolved plus one misleading ambiguous new override; 9 new methods, 8 nested helpers, 2 module helpers. |
| Qualified scope lost by file/simple-name matching | 10 | A | Real edits correspond to 15 existing graph definitions; six validator methods share one coarse __call__ row. |
| Unchanged context or stale hunk heading | 10 | A | Unedited neighboring declarations or an earlier enclosing header are incorrectly counted as changed symbols. |
| Docstring text treated as a declaration | 1 | A | The line `class labels for each estimator in the chain.` is documentation, not a class. |

**A = 21, B = 19, C = 0, D = 0.** A does not mean 21 missing call edges can be recovered: 11 of those rows should be removed from the failed-changed-code inventory, while 10 coarse names can be mapped to their actual edited definitions. B does not mean new functions require runtime discovery: their candidate AST identities are exact, but using them requires changing the base-only graph input boundary and establishing call connections. That is a larger, potentially risky experiment. C/D are counts of these rows’ primary causes, not assertions that downstream Python dispatch is fully static.

## Why type propagation could not change these totals

The pass refines edges while preserving definition nodes and the old file/simple-name mapper. It cannot distinguish two methods sharing a simple name for that mapper; cannot make a candidate-introduced function appear in a base-only graph; and cannot remove textual extractor false positives. Consequently, general call-site improvements do not imply improvements in these name-status totals. In particular, sklearn MultiOutputClassifier.fit is newly introduced by the patch yet collides with four unrelated base fit definitions. Resolving it to an ancestor or an arbitrary fit implementation would create false certainty.

## Best next bounded static work

The best-supported bounded next step is **AST- and edit-aware qualified changed-symbol identification**, with an explicit distinction among modified existing definitions, genuinely new definitions and context-only names. This is recommended as a prerequisite, not as another receiver-propagation feature. It could accurately map **10 of the 40 coarse records to 15 existing edited definitions** and remove **11 spurious records**. Do not describe that as 21 newly resolved changed symbols. The 19 genuinely new definitions remain outside the current base-source universe; indexing them requires a separately reviewed candidate-aware design.

For the multi-validator __call__ row, six definitions are actually edited and BaseValidator.__call__ is not. The mapper must represent all six qualified edited definitions without choosing a single method or indiscriminately promoting all same-name methods. No proposed mapping was fed back into the graph or selector in this diagnosis.

## Would this change test selection?

**Not by itself on the stored graph. All 15 existing edited target nodes identified for the ten genuine ambiguity rows have zero incoming call edges, and zero emittable tests within depth 3 in both frozen traversal variants.** Correct seed identity is necessary, but it cannot manufacture missing invocation paths. There is no demonstrated mapper-only addition to the selected test set. No ranking or counterfactual selector was executed.

The separate downstream barriers visible in the source/model include implicit __call__/comparison/operator invocation, constructors that target classes without __init__/__new__ edges, inherited receiver dispatch, Django request-method getattr dispatch and SymPy classmethod-eval construction hooks. Their presence does not change the primary mapper diagnostic. `downstream_evidence.json` records actual zero incoming-edge counts, class metadata and constructor references; these observations justify further case-level design review, not a claim that a generic dispatch feature would safely recover tests.

Potential class anchors illustrate the danger of overstating benefit: Rational’s class has 1,215 resolved-only reachable test IDs and 1,244 in the secondary variant, coth’s class has 9 and IdentityOperator’s class has 3, yet their changed method bodies have zero incoming edges. Rational.__new__ is decorated and symbolic construction has custom semantics. Using those broad class paths as method coverage would be unjustified. Message.__init__ has no reachable class-anchor tests either, so the seemingly simpler constructor case also offers no observed selection gain here.

For the two new Dagger operator methods, the existing Dagger class has 105 resolved-only reachable test IDs outside that task’s existing changed-seed union. This is an exploratory class-level ceiling, **not** 105 tests proven to reach __mul__/__rmul__, and not permission to substitute a whole-class seed. Several new nested helpers likewise have lexical enclosing anchors but no demonstrated graph path to the new body. `existing_paths.csv` separates such anchor paths from paths to actual changed base definitions.

No single new call-graph feature is justified for adoption by this diagnosis alone. If a later edge experiment is proposed, it should name one actual qualified target and one source-backed invocation chain and retain dynamic/decorator/inheritance uncertainty. Improving generic resolved-call counts is not an adequate success criterion.

## Incompleteness and resource limits

16 of the 40 rows occur in partial graphs. **Zero primary failures are caused by parse omissions, AST quotas or resource stops.** Every changed file was indexed/parsed, every claimed base target is present, and none of the recorded file-level failures concerns the changed file. New-definition absence was verified in the full base file, not inferred from an incomplete graph. Partial graphs may still hide downstream paths elsewhere; zero paths describes the stored graph and is not proof about runtime coverage or a hypothetical fully complete graph. Partial status does not imply dynamic analysis is needed.

## Evidence and validation

All 40 cases across 25 tasks were checked against exact archive hashes/PAX base commits and hash-verified frozen candidate patches. Unified diff context/removal text and hunk counts were validated before reconstructing candidate file text in memory; both versions were parsed as AST data without executing benchmark code. Reconstruction is only an inspection view, not graph construction or a patch application to the benchmark checkout. The 419 frozen graph artifacts were hash-checked. Prior experiment files and the original dirty worktree fingerprint were verified unchanged.

`cases.csv` contains the requested task/repository, symbol/status, exact reason, original diagnostic, source explanation, category, A/B/C/D, proposed fix and confidence. `source_evidence.json` retains exact relevant patch blocks, AST scope spans, extractor occurrences and source snippets for every case. `downstream_evidence.json` separates method-node facts from class-anchor and candidate-call syntax. `inspection_validation.json` records the read-only checks. Confidence is high for the primary source/mapping diagnosis; proposed downstream benefit is intentionally not assigned that confidence.

This diagnosis is restricted to the requested forty failed name records. It does not validate the other 147 resolved identities, candidate correctness, runtime coverage or the completeness of the changed-symbol inventory. Previous type-propagation outputs remain authoritative and were not rewritten.

## Per-case findings

| Case | Task | Symbol | Status | Category / class | Source finding |
|---|---|---|---|---|
| C01 | astropy__astropy-14508 | `_format_value` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | The hunk header says _format_value, but every changed executable line is inside the separate module-level _format_float. Neither Card._format_value nor module _format_value is edited. |
| C02 | django__django-11095 | `get_inlines` | unresolved | candidate_only_definition_absent_from_base / B | The patch adds ModelAdmin.get_inlines and changes get_inline_instances to call it. The class exists at base; this method does not. |
| C03 | django__django-13212 | `__call__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Six __call__ bodies are edited: RegexValidator, URLValidator, EmailValidator, DecimalValidator, FileExtensionValidator and ProhibitNullCharactersValidator. The mapper collapses their qualified identities to __call__, also including unedited BaseValidator.__call__. The correct result is a set of six edited definitions, not one guessed method or all seven candidates. |
| C04 | django__django-13212 | `__eq__` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | __eq__ appears only as following context after edited validator __call__ bodies. No equality method body or definition is edited. |
| C05 | matplotlib__matplotlib-24026 | `get_next_color` | unresolved | candidate_only_definition_absent_from_base / B | stackplot.get_next_color is a newly added nested function in the colors-supplied branch. The other branch binds get_next_color to axes._get_lines.get_next_color; a candidate overlay must retain this conditional/mixed binding. |
| C06 | matplotlib__matplotlib-26291 | `__call__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only AnchoredLocatorBase.__call__ receives the renderer-is-None handling. InsetPosition.__call__ is another method in the file and is not edited. |
| C07 | pydata__xarray-4695 | `__setitem__` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | The changed call is _LocIndexer.__getitem__: sel(**key) becomes sel(key). The following __setitem__ definition is unchanged context. |
| C08 | pydata__xarray-6744 | `construct` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | The edit changes DataArrayRolling.__iter__ window bounds/yield behavior. The next construct declaration is unchanged context; none of the three construct implementations is edited. |
| C09 | pylint-dev__pylint-6528 | `_is_ignored_file` | unresolved | candidate_only_definition_absent_from_base / B | _is_ignored_file is a new module-level helper called twice from the existing expand_modules body. No base AST definition with that name exists. |
| C10 | scikit-learn__scikit-learn-14629 | `__init__` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | MultiOutputClassifier.__init__ is unchanged context before the newly inserted fit override. No constructor in the file is edited. |
| C11 | scikit-learn__scikit-learn-14629 | `fit` | ambiguous | candidate_only_definition_absent_from_base / B | The candidate adds MultiOutputClassifier.fit, an override absent from the base class. The four base fit nodes belong to MultiOutputEstimator, _BaseChain, ClassifierChain and RegressorChain. Mapping to any of them as the changed definition would be incorrect, even though an explicit super().fit call invokes inherited behavior. |
| C12 | scikit-learn__scikit-learn-14629 | `labels` | unresolved | docstring_text_misidentified_as_definition / A | The added docstring line "class labels for each estimator in the chain." matches the extractor regex as if it were a class declaration. There is no AST function/class named labels in either version. |
| C13 | scikit-learn__scikit-learn-14629 | `predict_proba` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | MultiOutputClassifier.predict_proba is unchanged following context after the newly inserted fit method. Neither base predict_proba body is edited. |
| C14 | scikit-learn__scikit-learn-14894 | `predict` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | All executable edits belong to BaseLibSVM._sparse_fit. The next predict declaration is unchanged context; neither BaseLibSVM.predict nor BaseSVC.predict is edited. |
| C15 | astropy__astropy-7606 | `__eq__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only UnrecognizedUnit.__eq__ gains self-identity/exception handling. UnitBase.__eq__ is a separate, unedited method in the same file. |
| C16 | astropy__astropy-7606 | `__ne__` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | UnrecognizedUnit.__ne__ is unchanged following context after the edited __eq__. No inequality method is edited. |
| C17 | django__django-13297 | `get` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | The edited get body is TemplateView.get, which now wraps URL kwargs. RedirectView.get is an unedited same-name method. |
| C18 | django__django-13569 | `get_group_by_cols` | unresolved | candidate_only_definition_absent_from_base / B | The patch adds Random.get_group_by_cols to the existing Random class. A missing local override at base is not evidence of an incomplete file or a failed import. |
| C19 | django__django-14631 | `_did_change` | unresolved | candidate_only_definition_absent_from_base / B | BoundField._did_change is a new method containing logic moved/refactored from form changed-data handling. Its class exists, but the method has no base node. |
| C20 | django__django-14631 | `_bound_items` | unresolved | candidate_only_definition_absent_from_base / B | BaseForm._bound_items is newly added; _clean_fields and changed_data are rewritten to call it. BaseForm itself already has a graph node. |
| C21 | django__django-16136 | `options` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | The edit changes View.http_method_not_allowed and introduces its nested async func. View.options is the next unchanged declaration, not an edited method. |
| C22 | django__django-16631 | `_get_session_auth_hash` | unresolved | candidate_only_definition_absent_from_base / B | AbstractBaseUser._get_session_auth_hash is a new helper extracted from get_session_auth_hash; the old body location does not create a base node under the new name. |
| C23 | django__django-16631 | `get_session_auth_fallback_hash` | unresolved | candidate_only_definition_absent_from_base / B | AbstractBaseUser.get_session_auth_fallback_hash is a new generator method over configured fallback secrets. The primary mapping failure is absence at base, independent of whether fallback values are runtime data. |
| C24 | matplotlib__matplotlib-20488 | `autoscale` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only LogNorm.autoscale changes copy=False to copy=True. Normalize.autoscale and CenteredNorm.autoscale are unedited same-name methods. |
| C25 | matplotlib__matplotlib-20488 | `autoscale_None` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only LogNorm.autoscale_None gains the vmin/vmax guard and copy=True. Normalize, TwoSlopeNorm and CenteredNorm same-name methods are unedited. |
| C26 | pytest-dev__pytest-10051 | `handleError` | ambiguous | unchanged_context_or_stale_hunk_header_name / A | LogCaptureHandler.handleError is unchanged context immediately following the new clear method. The actual edits add LogCaptureHandler.clear and change LogCaptureFixture.clear. |
| C27 | pytest-dev__pytest-5787 | `deserialize_repr_crash` | unresolved | candidate_only_definition_absent_from_base / B | deserialize_repr_crash is newly nested inside BaseReport._from_json. It returns a ReprFileLocation or None and has no base lexical definition. |
| C28 | pytest-dev__pytest-5787 | `deserialize_repr_entry` | unresolved | candidate_only_definition_absent_from_base / B | deserialize_repr_entry is newly nested inside BaseReport._from_json, refactoring entry reconstruction. Its candidate lexical binding does not exist in the base graph. |
| C29 | pytest-dev__pytest-5787 | `deserialize_repr_traceback` | unresolved | candidate_only_definition_absent_from_base / B | deserialize_repr_traceback is newly nested inside BaseReport._from_json and calls the new entry helper. The function is not omitted by a graph resource stop. |
| C30 | pytest-dev__pytest-5787 | `serialize_repr_crash` | unresolved | candidate_only_definition_absent_from_base / B | serialize_repr_crash is newly nested inside BaseReport._to_json. It handles optional crash representations and has no base definition. |
| C31 | pytest-dev__pytest-5787 | `serialize_repr_entry` | unresolved | candidate_only_definition_absent_from_base / B | serialize_repr_entry is newly nested inside BaseReport._to_json, extracting existing serialization logic into a new lexical function. |
| C32 | pytest-dev__pytest-5787 | `serialize_repr_traceback` | unresolved | candidate_only_definition_absent_from_base / B | serialize_repr_traceback is newly nested inside BaseReport._to_json and calls serialize_repr_entry. Both are introduced only by the patch. |
| C33 | pytest-dev__pytest-7236 | `postpone_tearDown` | unresolved | candidate_only_definition_absent_from_base / B | postpone_tearDown is newly nested inside TestCaseFunction.runtest and passed to setattr(self._testcase, "tearDown", ...). Indexing the new function is static; proving its runtime callback dispatch would require additional analysis and must not be guessed. |
| C34 | sphinx-doc__sphinx-10323 | `_get_option_indent` | unresolved | candidate_only_definition_absent_from_base / B | _get_option_indent is a new module-level helper called from LiteralInclude.run. It parses directive option indentation and is absent from the complete base AST. |
| C35 | sphinx-doc__sphinx-10466 | `__init__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only Message.__init__ changes location deduplication. Catalog, MsgOrigin, GettextRenderer and LocalTimeZone constructors are separate, unedited definitions. |
| C36 | sympy__sympy-13480 | `eval` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | The edited eval is coth.eval: a cotm typo becomes cothm in its body. Ten other classes define eval in the same file; the existing node retains its classmethod decorator. |
| C37 | sympy__sympy-19783 | `__mul__` | unresolved | candidate_only_definition_absent_from_base / B | Dagger.__mul__ is newly added to an existing Dagger class. The base graph has constructor paths to Dagger, but has no node for this new multiplication method. |
| C38 | sympy__sympy-19783 | `__rmul__` | unresolved | candidate_only_definition_absent_from_base / B | Dagger.__rmul__ is a newly added reflected-multiplication method. Existing class reachability is not a call edge to this new method and must not be substituted as proof of test coverage. |
| C39 | sympy__sympy-19783 | `__mul__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only IdentityOperator.__mul__ gains the Dagger case. Operator.__mul__ is a separate, unedited same-name method. |
| C40 | sympy__sympy-24562 | `__new__` | ambiguous | qualified_scope_lost_by_simple_name_mapper / A | Only Rational.__new__ gains string conversion logic. Eleven other constructors in numbers.py are unedited candidates. Rational.__new__ is decorated; identifying its source node does not prove a unique runtime constructor edge. |

## Reproduce the diagnostic only

From the experimental worktree, using the existing dependency interpreter and local frozen inputs:
```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/inspect_cases.py
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/inspect_downstream.py
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /home/rajee/projects/cis695-agent-reliability/.venv/bin/python -B reports/callgraph_selection/typeprop_experiment/changed_symbol_diagnosis/render_diagnosis.py
```

These scripts only write this diagnostic subdirectory. They do not change the mapping implementation, graph construction, seed policy, V2, ranking, budgets, classifier or decision policy. No commit or push is part of this diagnosis.
