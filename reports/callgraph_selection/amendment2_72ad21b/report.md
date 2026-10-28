# Amendment 2 rebuild and changed-symbol resolution

2026-10-22. Steps 1–3 only. No selectors or success-criterion evaluation ran.
No oracle or gold inputs were used. Benchmark source was parsed with `ast` only; it was never imported, installed or executed. No Docker or network was used.

## Committed design and input verification

Commit `72ad21bce666aa766cc329c9bef8057f790c0ef5` touched `design.md` only. Its working bytes match the commit. Amendment 2, C1/C2/C3 and the decision map are present; the design was not edited.

All 83 frozen candidate patches were verified against both export `manifest.csv` and the earlier 83-patch hash inventory. The export directory is absent on this machine; the explicitly supplied `frozen_patches_export.tgz` was read directly without persisting raw patches. `csv_source_run`, checked against the committed study cohort, is the final-study provenance. Raw source aliases and four `ambiguous` manifest notes are preserved in `verified_patch_manifest.csv`; no alternate run was substituted.

Base inputs are the previously acquired, SHA-256-verified local `~/cg_repos/task_archives/<instance_id>.tar` archives. Each archive's PAX commit matches the pinned base commit in the original `inputs.json`. Each of the four rebuilds used a temporary `/tmp` extraction of `testbed/`, deleted after construction.

## Four amended graphs

Preflight parses each eligible Python file once and counts `ast.walk`-equivalent entries once toward 10,000,000. Files are omitted by descending preflight AST count, ties by lexical path, until retained input is at most 5,000,000. Cached retained ASTs are indexed without reparsing. Indexing visits are recorded separately as `NodeVisitor.visit` calls over retained trees, under the same 600-second task wall limit. This visit metric differs from a full `ast.walk`: the shared indexer intentionally skips some syntax contexts. The shared indexer and resolver are reused; selection and production verifier code were not changed.

| Task | Status | Python files | Retained files | Preflight entries | Retained entries | Indexing visits | Omitted (tests) | Graph nodes | Edge records | Runtime, s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sympy__sympy-13480 | partial | 1,181 | 1,175 | 6,958,393 | 4,762,362 | 3,627,132 | 6 (0) | 26,475 | 370,101 | 21.47 |
| sympy__sympy-14711 | partial | 1,220 | 1,214 | 7,106,521 | 4,910,490 | 3,740,098 | 6 (0) | 27,799 | 381,328 | 21.52 |
| sympy__sympy-17318 | partial | 1,324 | 1,310 | 9,260,685 | 4,961,401 | 3,718,163 | 14 (5) | 34,737 | 379,546 | 25.60 |
| sympy__sympy-19783 | partial | 1,420 | 1,403 | 9,551,134 | 4,976,923 | 3,739,428 | 17 (6) | 36,389 | 376,017 | 28.73 |

Every omitted file is listed below in removal order. Test flags use the existing verifier path classifier after omission ranking; they do not affect the rule.

### sympy__sympy-13480

- `sympy/integrals/rubi/rules/sine.py` (582,289 entries)
- `sympy/integrals/rubi/rules/trinomial_products.py` (477,810 entries)
- `sympy/integrals/rubi/rules/secant.py` (347,416 entries)
- `sympy/integrals/rubi/rules/quadratic_products.py` (284,672 entries)
- `sympy/integrals/rubi/rules/inverse_hyperbolic.py` (255,827 entries)
- `sympy/integrals/rubi/rules/tangent.py` (248,017 entries)

### sympy__sympy-14711

- `sympy/integrals/rubi/rules/sine.py` (582,289 entries)
- `sympy/integrals/rubi/rules/trinomial_products.py` (477,810 entries)
- `sympy/integrals/rubi/rules/secant.py` (347,416 entries)
- `sympy/integrals/rubi/rules/quadratic_products.py` (284,672 entries)
- `sympy/integrals/rubi/rules/inverse_hyperbolic.py` (255,827 entries)
- `sympy/integrals/rubi/rules/tangent.py` (248,017 entries)

### sympy__sympy-17318

- `sympy/integrals/rubi/rubi_tests/tests/test_trinomials.py` (1,287,229 entries) — test file
- `sympy/integrals/rubi/rules/sine.py` (426,302 entries)
- `sympy/integrals/rubi/rubi_tests/tests/test_miscellaneous_algebra.py` (394,153 entries) — test file
- `sympy/integrals/rubi/rubi_tests/tests/test_logarithms.py` (372,086 entries) — test file
- `sympy/integrals/rubi/rules/secant.py` (260,698 entries)
- `sympy/polys/benchmarks/bench_solvers.py` (199,492 entries)
- `sympy/integrals/rubi/rules/quadratic_products.py` (199,005 entries)
- `sympy/integrals/rubi/rubi_tests/tests/test_exponential.py` (195,434 entries) — test file
- `sympy/integrals/rubi/rules/inverse_hyperbolic.py` (189,510 entries)
- `sympy/integrals/rubi/rules/tangent.py` (180,167 entries)
- `sympy/integrals/rubi/rules/inverse_trig.py` (170,660 entries)
- `sympy/physics/quantum/tests/test_spin.py` (161,796 entries) — test file
- `sympy/integrals/rubi/rules/trinomial_products.py` (137,744 entries)
- `sympy/integrals/rubi/rules/miscellaneous_algebraic.py` (125,008 entries)

### sympy__sympy-19783

- `sympy/integrals/rubi/rubi_tests/tests/test_trinomials.py` (1,287,229 entries) — test file
- `sympy/integrals/rubi/rules/sine.py` (417,405 entries)
- `sympy/integrals/rubi/rubi_tests/tests/test_miscellaneous_algebra.py` (394,153 entries) — test file
- `sympy/integrals/rubi/rubi_tests/tests/test_logarithms.py` (372,086 entries) — test file
- `sympy/integrals/rubi/rules/secant.py` (255,289 entries)
- `sympy/polys/benchmarks/bench_solvers.py` (199,492 entries)
- `sympy/integrals/rubi/rules/quadratic_products.py` (195,470 entries)
- `sympy/integrals/rubi/rubi_tests/tests/test_exponential.py` (195,434 entries) — test file
- `sympy/integrals/rubi/rules/inverse_hyperbolic.py` (184,840 entries)
- `sympy/integrals/rubi/rules/tangent.py` (176,505 entries)
- `sympy/integrals/rubi/rules/inverse_trig.py` (166,307 entries)
- `sympy/physics/quantum/tests/test_spin.py` (138,191 entries) — test file
- `sympy/integrals/rubi/rules/trinomial_products.py` (134,952 entries)
- `sympy/integrals/rubi/rules/miscellaneous_algebraic.py` (122,058 entries)
- `sympy/integrals/rubi/rubi_tests/tests/test_sine.py` (117,680 entries) — test file
- `sympy/integrals/rubi/rules/hyperbolic.py` (110,429 entries)
- `sympy/integrals/rubi/rules/binomial_products.py` (106,691 entries)

Post-ranking package annotations are in `omission_annotations.csv`. None of the 43 omitted task/file pairs shares an exact immediate package with an extracted changed name, and every changed source file is retained. For SymPy-19783, omitted `sympy/physics/quantum/tests/test_spin.py` is in a descendant of the changed quantum package; that is recorded separately from exact package overlap. Package proximity does not establish test coverage.

SHA-256 verification passed for every file of the other **79** original graphs. All **83** original graph directories remain unchanged (415 files checked). `graph_manifest.json` overlays only the four new graphs on the original 79; the original four stopped graphs are retained as historical artifacts.

## Changed-symbol resolution, all 83 final-study patches

Matching reuses `build_graphs.changed_symbols`, the existing unified-diff parser and symbol extractor. It requires an exact simple name in the changed base file. A unique definition resolves; multiple definitions are ambiguous. No fuzzy or cross-file fallback is used. These are extracted names, not validated semantic change locations. Newly added names are inferred only when a name is absent at base, appears in added-side extracted definitions, and does not appear on the removed side; file absence is checked against the verified base archive. Names missing because a file was omitted or unparseable remain unknown, rather than being called newly added.

Rates below are resolved / (resolved + ambiguous + unresolved), first including all extracted names, then excluding inferred newly added names. No-name production files remain listed per task but do not add invented symbols to either denominator. Repository totals pool symbol counts.

| Repository | Tasks | Complete / partial | Resolved | Ambiguous | Unresolved | Including new | Newly added | Excluding new |
|---|---:|---:|---:|---:|---:|---|---:|---|
| astropy/astropy | 4 | 4 / 0 | 5 | 3 | 0 | 5/8 (62.5%) | 0 | 5/8 (62.5%) |
| django/django | 31 | 16 / 15 | 67 | 4 | 6 | 67/77 (87.0%) | 6 | 67/71 (94.4%) |
| matplotlib/matplotlib | 15 | 15 / 0 | 18 | 3 | 1 | 18/22 (81.8%) | 1 | 18/21 (85.7%) |
| mwaskom/seaborn | 1 | 1 / 0 | 1 | 0 | 0 | 1/1 (100.0%) | 0 | 1/1 (100.0%) |
| pallets/flask | 1 | 1 / 0 | 1 | 0 | 0 | 1/1 (100.0%) | 0 | 1/1 (100.0%) |
| psf/requests | 0 | 0 / 0 | 0 | 0 | 0 | 0/0 (n/a) | 0 | 0/0 (n/a) |
| pydata/xarray | 5 | 5 / 0 | 6 | 2 | 0 | 6/8 (75.0%) | 0 | 6/8 (75.0%) |
| pylint-dev/pylint | 5 | 0 / 5 | 15 | 0 | 1 | 15/16 (93.8%) | 1 | 15/15 (100.0%) |
| pytest-dev/pytest | 7 | 4 / 3 | 13 | 1 | 7 | 13/21 (61.9%) | 7 | 13/14 (92.9%) |
| scikit-learn/scikit-learn | 5 | 5 / 0 | 7 | 4 | 1 | 7/12 (58.3%) | 1 | 7/11 (63.6%) |
| sphinx-doc/sphinx | 4 | 4 / 0 | 7 | 1 | 1 | 7/9 (77.8%) | 1 | 7/8 (87.5%) |
| sympy/sympy | 5 | 1 / 4 | 7 | 3 | 2 | 7/12 (58.3%) | 2 | 7/10 (70.0%) |
| ALL | 83 | 56 / 27 | 147 | 21 | 19 | 147/187 (78.6%) | 19 | 147/168 (87.5%) |

`changed_symbol_resolution.csv` records every extracted name, candidate target IDs, exact resolution reason and origin evidence. `task_resolution.csv` records each task's status, no-name production files, graph location and final-study source run. `repository_resolution.csv` contains the complete counts and both rate denominators. The versioned `base_feasibility.csv` joins these fresh resolution values to the active graph diagnostics; the original baseline CSV is preserved. Any graph eligibility columns are input inventories only; no C1/C2/C3 outcome is evaluated.

## Reproduction

From the project root, with the pinned archives and export available:

```bash
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage verify
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage rebuild
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage resolve
env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_amendment2.py
```

The rebuild refuses to overwrite an existing versioned graph. To reproduce construction, use a clean copy with the recorded pre-run hash/design snapshots and without the four new versioned graph directories. The resolve stage reuses stored graphs and may be rerun independently. All generated artifacts and research code are under `reports/callgraph_selection/`; no commits were made.

## Synthetic tests and artifact validation

The 13 existing synthetic tests and seven new tests passed (**20 passed**). New checks cover largest-first ties and stopping, strict incomplete-preflight handling, cached single parsing, identical nodes/edges/scopes to the original graph on retained synthetic inputs, partial parse failures, new-name attribution and count-pooled aggregation. Fixture source is parsed, never executed.

```bash
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py -q -p no:cacheprovider -o addopts=
```

`validate_amendment2.py` checks original graph hashes, all new artifact hashes, the four partial statuses and caps, every per-file cost/hash against the earlier preflight, the complete 43-file omission set, all 83 final-study source identities and every aggregation denominator. See `validation.json` for the completed validation result and `tests.txt` for pytest output.
