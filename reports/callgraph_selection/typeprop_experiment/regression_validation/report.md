The 715 → 131 reduction does **not** demonstrate that regression detection was preserved. Most removals have no per-test outcome evidence. Resolved-only SCG already missed every named historical regression; corrected SCG also loses official failure witnesses. Including ambiguous edges exposes an additional loss of two recorded regressions.

This is post-hoc validation of the mapping frozen in commit `fed5973`. No benchmark tests were newly executed and no graph, selector, V2 policy, classifier, ranking, or budget was changed. All 3,672 existing B/C configurations were checked using frozen ranked prefix memberships and the two recorded delta layers; every available before/after count reconciles. Selection identities, not hypothetical execution outcomes, are compared.

The headline configuration is B (SCG-only), resolved edges, depth 3, ALL. Across the same 78 tasks with available selections, **715 → 131**, removing **584 selected identities (81.7%)**, with no additions. Counts describe selected functions/families, not expanded parameterized test invocations.

| Frozen stratum, paired tasks | Tasks | Before → after |
|---|---:|---:|
| PRIMARY_COMPLETE | 53 | 591 → 106 |
| EXTENDED_PARTIAL | 22 | 92 → 22 |
| EXCLUDED, diagnostic selections only | 3 | 32 → 3 |

Thus 715 → 131 pools complete, partial, and excluded diagnostic selections. It is not the strict primary-eligible cohort. The pylint witness loss below occurs in the EXCLUDED stratum; the Django regression loss with ambiguous edges occurs in PRIMARY_COMPLETE.

Two evidence tiers have separate denominators:

* **Reported regressions:** six named existing-suite regressions across five tasks, identified by frozen per-test regression summaries with cached baselines. These five candidate patches were oracle-resolved; “regression” and “wrong patch” are distinct labels.
* **Official existing-base witnesses:** seven official harness failures across four wrong patches, whose test definitions existed unchanged at base. This establishes a failing identity in that official evaluation, not a paired regression in the historical V2 environment. Added/rewritten/uncertain gold tests are excluded from existing-suite recall.

| Depth 3, ALL configuration | Reported regressions retained before → after | Official existing-base witnesses before → after |
|---|---:|---:|
| B, resolved only | 0/6 → 0/6 (0% → 0%) | 2/7 → 0/7 (28.6% → 0%) |
| B, resolved + ambiguous | 2/6 → 0/6 (33.3% → 0%) | 2/7 → 0/7 |
| C, stored V2 pool reranked, either edge variant | 6/6 → 6/6 | 7/7 → 7/7 |

For resolved-only B, zero reported regressions are retained, lost, or gained: all six were missed both before and after. For B with ambiguous edges, **two are lost**, none retained or gained, four missed both. Its selection size falls **1,215 → 179**. Full C membership stays unchanged; finite prefixes can lose witnesses: at depth 3, primary C official-witness recall changes 3/7 → 1/7 at K=25, 4/7 → 2/7 at K=50, and 5/7 → 6/7 at K=100. Secondary C loses the two Django regressions at K=250 and K=500 (reported-regression recall 5/6 → 3/6). These are frozen prefix effects, not policy changes.

All tasks with named usable detecting evidence are below. “Hits” use the relevant tier, never combine their denominators.

| Task | Resolved-only B selected before → after | Evidence and hits before → after |
|---|---:|---|
| django-12209 | 0 → 0 | Reported regression: 0/1 → 0/1 |
| django-14140 | 0 → 0 | Reported regressions: 0/2 → 0/2; ambiguous-edge B: **2/2 → 0/2**, 262 → 0 selected |
| django-14631 | 0 → 0 | Reported regression: 0/1 → 0/1 |
| pytest-5809 | 0 → 0 | Reported regression: 0/1 → 0/1 |
| sphinx-10435 | 0 → 0 | Reported regression: 0/1 → 0/1 |
| pylint-6528, wrong | 31 → 2 | Official witnesses: **2/4 → 0/4** |
| pylint-7277, wrong | 1 → 1 | Official witness: 0/1 → 0/1 |
| django-13297, wrong | 1 → 0 | Official witness: 0/1 → 0/1 |
| matplotlib-25479, wrong | 0 → 0 | Official witness: 0/1 → 0/1; historical regression is unnamed |

The new wrong-patch miss is pylint-6528's `tests/lint/unittest_lint.py::test_multiprocessing`: selecting this family previously retained official failures `[1]` and `[2]`; corrected B omits both, at all frozen depths. The other five official witnesses were already missed: pylint-6528 `test_custom_should_analyze_file` and `TestRunTC::test_jobs_score`, pylint-7277 `TestRunTC::test_jobs_score`, django-13297 `DeprecationTests::test_template_params_warning`, and matplotlib-25479 `test_register_cmap`.

The actual reported regressions lost by ambiguous-edge B are django-14140's `tests/queries/test_q.py::QTests::test_deconstruct` and `test_deconstruct_negated`, at all frozen depths. Correcting seed identity does not guarantee preservation of useful reachability previously supplied by broader seeds.

Of the **584 removed identities**, **555 (95.0%) have no usable per-test outcome observations**. Another **28** have 53 concrete pass/pass observations in later frozen local pairs. The remaining identity is the multiprocessing family: its two official failure witnesses also pass/pass in those later pairs. This disagreement is retained explicitly. All three later image HEADs differ from the graph base commits, and source-tree/historical image equivalence is unverified; these supplemental passes cannot establish historical irrelevance or a newly observed runtime false negative. No global “irrelevant tests removed” count is defensible.

Availability changes are separate from size reduction: django-13569 changes available-empty → unavailable (new definitions only); matplotlib-24637, sympy-13480, and sympy-24562 change unavailable → available-empty. Django-16082 stays unavailable. None has named detecting-test evidence, so no recall gain/loss is assigned to availability changes.

Evidence coverage: 19 frozen historical snapshots plus four additional matching-candidate local aggregate records cover 23 tasks; aggregate-only outcomes do not identify omitted tests. One local xarray-6744 record is excluded for a different candidate hash. The three later raw pairs contain 689 concrete outcomes; their six raw logs were hash-verified, and later classifier tables corroborate the same pairs without double-counting. The older 18,662-row “raw outcomes” table contains only unexecuted requests after Docker preflight failure and supplies zero outcomes. matplotlib-25479's aggregate “one regression” has no recorded regression ID here; its official witness is not assumed to be that unnamed regression. Remaining missing evidence stays unknown, so overall 83-task regression recall is unknown.

Artifacts: [headline_selected_tests.csv](headline_selected_tests.csv) gives before/after IDs and removals for all 83 tasks. [task_summary.csv](task_summary.csv) covers all 83 tasks, with availability, before/after sizes, evidence counts, tier-specific recall and retained/lost IDs. [selection_memberships.jsonl.gz](selection_memberships.jsonl.gz) records every before/after selected identity; [configuration_metrics.csv](configuration_metrics.csv) and [recall_by_configuration.csv](recall_by_configuration.csv) cover all configurations. [witness_selection.csv](witness_selection.csv) names every retained, lost, gained or missed witness; [removed_tests.csv](removed_tests.csv) distinguishes observations from gaps. [evidence_manifest.json](evidence_manifest.json), [protocol.json](protocol.json), and [validation.json](validation.json) record provenance and preservation checks. Fifteen audit checks passed. All 590 previously tracked files and the original dirty worktree remain unchanged.
