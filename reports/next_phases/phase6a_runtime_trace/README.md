# Phase 6a: runtime versus static graph

Post-hoc diagnostic only. These 7 grader witnesses and 6 regression witnesses come from known outcomes in the Phase 4 report. They must never feed test selection. No selector, executor, image, frozen result or tag is changed.

All 13 tests ran alone on each tree, once traced and once untraced (52 invocations). The trees use pristine archived source and that source plus the candidate whose SHA-256 matches audited_labels.csv. Local frozen image IDs, network none and CPU shares 2048 match Phase 4; no test skipped. Django uses tests/runtests.py. Read-only sitecustomize.py is loaded through PYTHONPATH and uses only sys.settrace.

## Counts

| Measurement | Count |
|---|---:|
| Tests | 13 |
| Tasks | 9 |
| Changed functions | 15 |
| Patch-only functions | 3 |
| Test/tree/function rows | 50 |
| Entered at runtime | 25 |
| Not entered in traced thread | 13 |
| Absent on tree | 6 |
| Unknown (thread blind spot) | 6 |
| Runtime entries statically reachable | 0 |
| Matched traced/untraced pairs | 26 |
| TRACE_PERTURBS | 0 |

First missing test-rooted edges: decorator = 2, fixture = 8, inheritance = 5, other = 3, property = 3, re-export = 4 (counts are test/tree/function rows).

The comparison uses the SCG source snapshot at e1a3ed1c74fd304493c3fe3811de755af77e306c, verified against reports/v2_scg_paired/scg_source_manifest.json. It regenerates the same base TypeGraph/TypeAmendedGraph with the same archive inputs. Only resolved edges count. reached_statically is unbounded forward reachability; static_hops and within_scg_depth_3 separately expose the actual SCG depth-3 limit. The graph is never rebuilt from patched source.

## Per-test summary

| # | Task | Test | Base / patched | Changed entered base / patched | Unknown rows | Outcome matches |
|---|---|---|---|---:|---:|---|
| 1 | pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_custom_should_analyze_file` | PASSED / PASSED | 1 / 2 | 0 | 2/2 |
| 2 | pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[1]` | PASSED / PASSED | 1 / 2 | 0 | 2/2 |
| 3 | pylint-dev__pylint-6528 | `tests/lint/unittest_lint.py::test_multiprocessing[2]` | PASSED / PASSED | 0 / 0 | 3 | 2/2 |
| 4 | pylint-dev__pylint-6528 | `tests/test_self.py::TestRunTC::test_jobs_score` | PASSED / PASSED | 0 / 0 | 3 | 2/2 |
| 5 | django__django-13297 | `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning` | PASSED / PASSED | 2 / 2 | 0 | 2/2 |
| 6 | matplotlib__matplotlib-25479 | `lib/matplotlib/tests/test_colors.py::test_register_cmap` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |
| 7 | pylint-dev__pylint-7277 | `tests/test_self.py::TestRunTC::test_jobs_score` | PASSED / PASSED | 0 / 0 | 0 | 2/2 |
| 8 | django__django-14140 | `tests/queries/test_q.py::QTests::test_deconstruct` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |
| 9 | django__django-14140 | `tests/queries/test_q.py::QTests::test_deconstruct_negated` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |
| 10 | pytest-dev__pytest-5809 | `testing/test_pastebin.py::TestPaste::test_create_new_paste` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |
| 11 | django__django-12209 | `tests/basic/tests.py::ModelInstanceCreationTests::test_save_primary_with_default` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |
| 12 | django__django-14631 | `tests/forms_tests/tests/test_forms.py::FormsTestCase::test_datetime_clean_initial_callable_disabled` | PASSED / FAILED | 1 / 2 | 0 | 2/2 |
| 13 | sphinx-doc__sphinx-10435 | `tests/test_build_latex.py::test_latex_code_role` | PASSED / FAILED | 1 / 1 | 0 | 2/2 |

## Interpretation and limitations

- runtime_chains.json preserves the complete first-entry stack plus first entry under the test. hops is null if the first entry precedes the test (Model._save_table runs during database setup); hops_under_test records its later test-rooted chain. A hop counts each Python frame, including decorators, generators and installed dependencies. These are live stacks, not asynchronous causal chains.
- sys.settrace is local to the installing thread. Pylint-6528 test_multiprocessing[2] and test_jobs_score start a multiprocessing pool whose feeder thread consumes _iterate_file_descrs and calls expand_modules / patched _is_ignored_file. Their absent entries are UNKNOWN. The report records partial tracing for both trees of those tests, rather than inventing non-reachability. No threading.settrace, profiler, monkeypatch or coverage API is used. Other NO values mean no entry observed in the traced thread, not a claim about all threads or native code.
- Fixture receiver types block the first edges in Django client, pytest plugin and Sphinx app chains. The Sphinx chain also includes installed docutils traversal and later visitor dispatch; those are later gaps, not its first missing edge. Inheritance blocks Model.save and the custom PyLinter; re-exports block Q.deconstruct; a decorator closure blocks colormap registration; property access invokes BaseForm.errors without an explicit call edge. Pylint multiprocessing[1] has a loop-local receiver left uncertain by bounded propagation (other). Source lines, graph statuses/reasons and runtime receiver MROs support these source-reviewed explanations in runtime_chains.json.
- A patch-only function has no base graph node. Its first missing edge can still occur earlier in the chain. Functions absent on a tree use ABSENT, not NO. Changed definitions are the union of innermost AST functions owning added/deleted hunk lines, with matched qualified definitions and line ranges on both trees; module edits without a function are retained as unmapped hunk entries.
- Tracer syntax is checked against Python 3.5 grammar and synthetic tests run on the host. The benchmark receipts record actual image interpreters. This is compatibility by standard-library APIs and grammar, not a claim that every Python minor version was executed.
- Interrupted work is retained under local interrupted_attempt and before_trace_receipts, with hashes in raw_artifact_manifest.json. Four early Django source receipts failed on an ASCII filesystem encoding; reading UTF-8 filename bytes corrected the verification without changing the container locale. All final source receipts pass. The earlier incomplete invocation and weaker trace receipts were superseded by complete final pairs.

## Artifacts and reproduction

phase6a_runtime_vs_static.csv is the requested comparison. test_outcomes.csv gives all 26 pairs and trace limitations; changed_functions.json maps every candidate hunk; runtime_chains.json gives frame/edge evidence. execution_manifest.json, static_graph_manifest.json and raw_artifact_manifest.json bind execution, source and local raw captures by SHA-256. summary_table.csv and summary.json supply the counts above.

See tools/runtime_trace/README.md for preparation/run commands. With the local captures present, run `.venv/bin/python tools/runtime_trace/driver.py summarize` twice and compare all output hashes; determinism.json records the verified identical artifact set. Summary generation reads captures only and runs no benchmarks.
