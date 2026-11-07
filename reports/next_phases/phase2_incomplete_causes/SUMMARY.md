# Phase 2: stored V2 evidence-gap audit

**POST-HOC ANALYSIS ONLY. Native results remain unchanged.**

Status: **done**. All 83 V2 tasks and both initial trees are inventoried, with confirmation calls marked separately; all 780 capture hashes in both arms verify. The three earlier CPU probes are documented separately in Phase 1 and are not benchmark runs or Phase 2 inputs to scoring.

## Cause counts and parser-only replay

`phase2_incomplete_causes.csv` reports all 83 tasks, including 39 INCOMPLETE and 13 NOT_AVAILABLE. Selected tree-ID slot counts, native gap-record counts and typed observation counts have separate columns; they must not be summed as one unit. Cause groups overlap.

Parser-only replay makes 9/39 INCOMPLETE tasks complete with the frozen skip-compatible policy; 2/13 NOT_AVAILABLE tasks gain paired binary evidence. These are offline evidence reconstructions, not new native verdicts or confirmed new FAILs. All six original native FAIL tasks retain observed base-pass/patched-fail evidence.

Replay changes only result reading: ANSI removal, Django two-line status handling and summary rejection, unique ID mapping, and concrete parameter accounting. It admits no new selected family, executes no tests, and reports the skip-strict alternative separately. Missing tests, ERROR observations, actual runner failures and ID-set changes continue to block completeness.

## Batch aborts

942 load/collection-abort batch occurrences across 32 tasks, including 92 GIS environment-guard aborts; 216 additional runner-start failures are separate (including SymPy missing pytest). `task_tree_batch_aborts.csv` has all 166 task/tree rows, including zeros.

`batch_aborts.csv` names the offending label when the capture names it, or lists static base-source candidates with an explicit identification confidence. It classifies properties, attributes and nested helpers using AST only. An inferred unique property is not an experimental isolated rerun. Unknown labels are retained: 0 load-abort occurrences. Collateral counts exclude named suspects and only count selected NOT_RUN identities with no observed concrete outcome; they do not guarantee those tests would pass after repair.

## Accepted and environment-conditioned skips

13 current PASS tasks accept selected SKIPPED evidence for completeness. `accepted_skips.csv` distinguishes exact selected skips, mapped parameter skips and original pre-integrity PASS scoring. `all_task_skips.csv` covers the same five reason groups across every task, with unknown/truncated/source-only quality visible and XFAIL preserved separately.

Reason groups: cores/CPU, missing dependency, platform, Python version, other. Source-derived explanations are labelled as static candidates or matches to captured prefixes; ambiguous and missing reasons stay explicit. Other includes unknown reasons and non-environment expected failures, so it is not an asserted environmental-cause count. `module_collection_skips.csv` reports selected requests whose own batch skipped collection; `class_setup_skips.csv` matches unnamed captured setup skips to literal setUpClass guards, without manufacturing test-body outcomes. Both are separate from concrete SKIPPED outcomes; chart columns also separate GIS-guard NOT_RUN requests.

`historical_PASS_inventory.csv` lists 97 historical PASS records; `historical_skip_observations.csv` lists 1530 available skip observations. Full historical verification envelopes usually preserve only a baseline cache and aggregate patched verdict: their patched statuses/completeness are unknown, not silently reconstructed. Different candidates are excluded from skip counts; unbound later pairs remain separately labelled, and heterogeneous selections/images are not pooled with the 83-task run.

## Remaining evidence limits

0 native gap records remain unclassified; 0 original selected-ID gap records have no resolved mechanism beyond an unreported outcome; 0 load-abort batches have no identified offending label. These unresolved details prevent claiming complete causal attribution when nonzero. All records have an input path/hash; capture examples have 1-based lines, and native gap records also have JSON pointers.

The audit does not install missing runners, change selection, repair the executor, alter CPU resources, or start Phase 3. The new skip-strict PASS rule is reported as a diagnostic policy contrast, not silently substituted for parser-only recovery.

## Files for review

- `native_gap_ledger.csv`: every recorded native gap and its assigned group.
- `selected_gap_attribution.csv`: every selected NOT_RUN/TIMEOUT/ERROR slot and observed admission or execution mechanism.
- `batch_aborts.csv`, `task_tree_batch_aborts.csv`: aborts, candidates, object kinds and collateral accounting.
- `accepted_skips.csv`, `all_task_skips.csv`, historical inventories: case-level skip evidence.
- `parser_replay.csv`, `call_replay_summary.csv`, `pass_to_error_observations.csv`: offline replay and classification diagnostics.
- `charts/*.csv`: each at most 15 rows including its header; plotting units are explicit.
- `input_manifest.json`: source/capture/archive hashes and historical coverage scope.

The analysis is published separately from the frozen native results.


## Counting and identification details

The per-cause `charts/cause_*.csv` files split every cause into INCOMPLETE,
NOT_AVAILABLE and other native strata; each has three data rows. Every chart
CSV has at most 15 rows including its header. Selected tree-ID slots and native
gap-record counts and typed observations are distinct units and are never added together.
Raw ERROR cases, concrete ID-set differences, PASS-to-ERROR transitions and
empty-selection task indicators have typed observation columns; they are never
labelled selected tree-ID slots. Already admitted ERROR outcomes are attributed
to collection/test errors even when they also have a concrete parsed identity.

Skip charts include both raw-case/tree slots and deduplicated selected-family/tree
slots. Families with different parameter-case reasons can appear in more than one
reason group. Named environment groups contain source-attributed candidates as
well as captured reasons; quality columns expose the distinction. Other includes
unknown reasons, database conditions and expected failures, with XFAIL counted
separately. Module-collection skip requests, class-setup skip requests and GIS
guard abort requests have separate columns and are not manufactured test outcomes.

`charts/batch_abort_label_confidence.csv` distinguishes explicit not-found or
collection-module diagnostics, inferred unique properties, named loader-signature
errors and ambiguous method-name candidates. Zero unidentified abort groups does
not mean every candidate is experimentally isolated: no such rerun was made.
Collateral totals are counts relative to the identified candidate set, not proof
that those requests would pass after removing that set.

`PASS_task_skip_inventory.csv` explicitly lists every task with a current or
original PASS, including zero observed-skip rows. Historical native envelopes,
paired records and stabilization tables are separate evidence tiers. The primary
historical chart excludes 13 PASS records for other candidates; their available
baseline skip observations are supplied in `historical_other_candidate_skips.csv`
instead. No available historical PASS record is silently interpreted as having
paired SKIPPED outcomes when only its baseline cache survived.


## Validation

Nine synthetic parser fixtures pass without importing benchmark code. The task
matrix reconciles exactly to 39,876 initial selected tree-ID gap slots and 22,586
native gap records. All 39 INCOMPLETE and 13 NOT_AVAILABLE tasks have at least
one attributed cause or typed observation. All 23 chart CSVs have at most 13
rows including their headers.

Prepublication scans found no credential or environment dump. Benign matches
are ordinary test identifiers and audit documentation. Oracle-pattern matches
are ordinary test names or module paths, with no gold-patch or test-patch payload.
No raw harness log, patch/archive file or file over 20 MB is included.

Historical counts are record-observations, not unique test executions; repeated
PASS envelopes can share a baseline cache. Other-candidate observations remain
separate from the full-83 cohort and its historical chart counts.


## Requested batch, skip and projection breakdowns

[BATCH_AND_POLICY_PROJECTIONS.md](BATCH_AND_POLICY_PROJECTIONS.md) gives the
full denominator, the six offending-label classes, top five tasks, grouped
skip counts and both projections. The 942 abort batches strand **3,138 collateral
NOT_RUN tree-ID slots**, **10.06% of all 31,179 native initial NOT_RUN slots**.
The largest losses are Django-13297 (824), Django-14631 (518), Django-15930
(416), Django-16136 (398) and Django-11820 (240), counting both trees.

The offending-label classes are 8 property, 98 non-test function, 0 class
attribute, 4 module-level helper, 130 missing module (explicit xmlschema import
errors), and 702 other batch occurrences. Multiple candidate labels are
preserved rather than counted as additional batches.

Among 13 skip-dependent native PASS tasks, the grouped concrete-test/task counts
are CPU 38/2, missing dependency 1/1, platform 0/0, Python version 0/0 and other
244/12. Tests are deduplicated across trees; task groups overlap. Other includes
8 XFAIL tests. **0/13 stay PASS under strict SKIPPED-as-missing handling**.
**2/13 have only CPU-conditioned ordinary skips**, but both also have XFAIL
outcomes normalized to SKIPPED, so **0/13 are CPU-only across all normalized
SKIPPED outcomes**.

The **projections, not results**, are **42/83 yes/no** with current policy plus
parser replay (36 projected PASS + 6 retained FAIL), versus **20/83** with parser
replay plus strict skips (14 projected PASS + 6 retained FAIL). This preserves
confirmed native FAIL regardless of other missing evidence and assumes no
runner repair, new test execution, new regression or new confirmation.

Only after those outputs were written, the separate
[POST-HOC label join](ACCEPTED_SKIP_LABELS_POST_HOC_ONLY.md) found **4/13
incorrect-labelled**: Django-16667, Matplotlib-23299, Pylint-6528 and Pylint-7277.
All 13 label-sidecar candidate-patch hashes match the frozen tasks. This does
not show that executing skipped tests would detect those incorrect patches;
labels did not change the fixed cohort, reason groups, parsing or projections.

Reproduce the additions with `scripts/phase2_policy_projection.py --report
<phase2-report> --results <stored-results> --output <fresh-directory>`. Its
`--posthoc-labels` mode requires the previously written label-blind report and
records the document/cohort hashes before reading labels. The main capture
analysis and this aggregation have 12 synthetic checks in total.
