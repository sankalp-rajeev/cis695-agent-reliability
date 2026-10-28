"""Render the phase-1b amendment rebuild and frozen-patch resolution inventory."""
import csv
import json


def percentage(value):
    return f"{value:.1%}" if value != "" else "n/a"


def render(work, summary, manifest, tasks):
    lines = [
        "# Amendment 2 rebuild and changed-symbol resolution",
        "",
        "2026-10-22. Steps 1–3 only. No selectors or success-criterion evaluation ran.",
        "No oracle or gold inputs were used. Benchmark source was parsed with `ast` only; "
        "it was never imported, installed or executed. No Docker or network was used.",
        "",
        "## Committed design and input verification",
        "",
        f"Commit `{summary['design_commit']}` touched `design.md` only. Its working bytes "
        "match the commit. Amendment 2, C1/C2/C3 and the decision map are present; the design was not edited.",
        "",
        "All 83 frozen candidate patches were verified against both export `manifest.csv` "
        "and the earlier 83-patch hash inventory. The export directory is absent on this machine; "
        "the explicitly supplied `frozen_patches_export.tgz` was read directly without persisting raw patches. "
        "`csv_source_run`, checked against the committed study cohort, is the final-study provenance. "
        "Raw source aliases and four `ambiguous` manifest notes are preserved in `verified_patch_manifest.csv`; "
        "no alternate run was substituted.",
        "",
        "Base inputs are the previously acquired, SHA-256-verified local `~/cg_repos/task_archives/<instance_id>.tar` "
        "archives. Each archive's PAX commit matches the pinned base commit in the original `inputs.json`. "
        "Each of the four rebuilds used a temporary `/tmp` extraction of `testbed/`, deleted after construction.",
        "",
        "## Four amended graphs",
        "",
        "Preflight parses each eligible Python file once and counts `ast.walk`-equivalent entries "
        "once toward 10,000,000. Files are omitted by descending preflight AST count, ties by "
        "lexical path, until retained input is at most 5,000,000. Cached retained ASTs are indexed "
        "without reparsing. Indexing visits are recorded separately as `NodeVisitor.visit` calls "
        "over retained trees, under the same 600-second task wall limit. This visit metric differs "
        "from a full `ast.walk`: the shared indexer intentionally skips some syntax contexts. "
        "The shared indexer and resolver are reused; selection and production verifier code were not changed.",
        "",
        "| Task | Status | Python files | Retained files | Preflight entries | Retained entries | Indexing visits | Omitted (tests) | Graph nodes | Edge records | Runtime, s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    diagnostics = []
    for iid, entry in sorted(manifest.items()):
        if not entry["directory"].startswith(work.name + "/"):
            continue
        directory = work.parent / entry["directory"]
        diagnostic = json.loads((directory / "diagnostics.json").read_text())
        row = diagnostic["row"]
        with (directory / "omitted_files.csv").open(newline="") as stream:
            omitted = list(csv.DictReader(stream))
        diagnostics.append((iid, row, omitted))
        test_count = sum(r["is_test_file"] == "True" for r in omitted)
        lines.append(f"| {iid} | {row['graph_status']} | {row['python_files']:,} | {row['parsed_files']:,} | "
                     f"{row['preflight_ast_nodes']:,} | {row['retained_ast_nodes']:,} | {row['indexing_visits']:,} | "
                     f"{len(omitted)} ({test_count}) | {row['nodes']:,} | {row['edge_records']:,} | {row['graph_runtime_seconds']:.2f} |")
    lines += ["", "Every omitted file is listed below in removal order. Test flags use the existing "
              "verifier path classifier after omission ranking; they do not affect the rule."]
    for iid, row, omitted in diagnostics:
        lines += ["", f"### {iid}", ""]
        for item in sorted(omitted, key=lambda r: int(r["removal_rank"])):
            flag = " — test file" if item["is_test_file"] == "True" else ""
            lines.append(f"- `{item['path']}` ({int(item['ast_nodes']):,} entries){flag}")
    verification = summary["original_graph_hash_verification"]
    lines += ["", "Post-ranking package annotations are in `omission_annotations.csv`. None of the 43 "
              "omitted task/file pairs shares an exact immediate package with an extracted changed name, "
              "and every changed source file is retained. For SymPy-19783, omitted "
              "`sympy/physics/quantum/tests/test_spin.py` is in a descendant of the changed quantum package; "
              "that is recorded separately from exact package overlap. Package proximity does not establish test coverage.",
              "", f"SHA-256 verification passed for every file of the other **{verification['unchanged_other_tasks']}** "
              f"original graphs. All **{verification['unchanged_original_tasks_including_old_sympy']}** original graph directories "
              f"remain unchanged ({verification['compared_files']} files checked). `graph_manifest.json` overlays only the "
              "four new graphs on the original 79; the original four stopped graphs are retained as historical artifacts.",
              "", "## Changed-symbol resolution, all 83 final-study patches", "",
              "Matching reuses `build_graphs.changed_symbols`, the existing unified-diff parser and symbol extractor. "
              "It requires an exact simple name in the changed base file. A unique definition resolves; multiple "
              "definitions are ambiguous. No fuzzy or cross-file fallback is used. These are extracted names, "
              "not validated semantic change locations. Newly added names are inferred only when a name is absent "
              "at base, appears in added-side extracted definitions, and does not appear on the removed side; "
              "file absence is checked against the verified base archive. Names missing because a file was "
              "omitted or unparseable remain unknown, rather than being called newly added.",
              "", "Rates below are resolved / (resolved + ambiguous + unresolved), first including all extracted "
              "names, then excluding inferred newly added names. No-name production files remain listed per task "
              "but do not add invented symbols to either denominator. Repository totals pool symbol counts.", "",
              "| Repository | Tasks | Complete / partial | Resolved | Ambiguous | Unresolved | Including new | Newly added | Excluding new |",
              "|---|---:|---:|---:|---:|---:|---|---:|---|"]
    for row in [*summary["per_repository"], summary["totals"]]:
        lines.append(f"| {row['repo']} | {row['tasks']} | {row['complete_graphs']} / {row['partial_graphs']} | "
                     f"{row['names_resolved']} | {row['names_ambiguous']} | {row['names_unresolved']} | "
                     f"{row['names_resolved']}/{row['names_total']} ({percentage(row['resolution_rate'])}) | "
                     f"{row['newly_added_names']} | {row['excluding_new_resolved']}/{row['excluding_new_total']} "
                     f"({percentage(row['excluding_new_resolution_rate'])}) |")
    lines += ["", "`changed_symbol_resolution.csv` records every extracted name, candidate target IDs, exact "
              "resolution reason and origin evidence. `task_resolution.csv` records each task's status, "
              "no-name production files, graph location and final-study source run. "
              "`repository_resolution.csv` contains the complete counts and both rate denominators. "
              "The versioned `base_feasibility.csv` joins these fresh resolution values to the active graph diagnostics; "
              "the original baseline CSV is preserved. "
              "Any graph eligibility columns are input inventories only; no C1/C2/C3 outcome is evaluated.",
              "", "## Reproduction", "", "From the project root, with the pinned archives and export available:", "",
              "```bash", "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage verify",
              "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage rebuild",
              "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/rebuild_and_resolve.py --stage resolve",
              "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/validate_amendment2.py",
              "```", "", "The rebuild refuses to overwrite an existing versioned graph. To reproduce construction, "
              "use a clean copy with the recorded pre-run hash/design snapshots and without the four new versioned "
              "graph directories. The resolve stage reuses stored graphs and may be rerun independently. "
              "All generated artifacts and research code are under `reports/callgraph_selection/`; no commits were made.",
              "", "## Synthetic tests and artifact validation", "",
              "The 13 existing synthetic tests and seven new tests passed (**20 passed**). New checks cover "
              "largest-first ties and stopping, strict incomplete-preflight handling, cached single parsing, "
              "identical nodes/edges/scopes to the original graph on retained synthetic inputs, partial parse failures, "
              "new-name attribution and count-pooled aggregation. Fixture source is parsed, never executed.", "",
              "```bash", "env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py -q -p no:cacheprovider -o addopts=",
              "```", "", "`validate_amendment2.py` checks original graph hashes, all new artifact hashes, "
              "the four partial statuses and caps, every per-file cost/hash against the earlier preflight, "
              "the complete 43-file omission set, all 83 final-study source identities and every aggregation denominator. "
              "See `validation.json` for the completed validation result and `tests.txt` for pytest output.", ""]
    (work / "report.md").write_text("\n".join(lines))
