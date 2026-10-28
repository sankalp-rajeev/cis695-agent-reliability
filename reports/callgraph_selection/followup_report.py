"""Render phase-1b follow-up measurements; no source/oracle/selector access."""
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent


def render(summary, partials, symbols):
    baseline = json.loads((OUT / "feasibility.json").read_text())
    totals = summary["total_calls"]
    test_result = (OUT / "synthetic_tests.txt").read_text().strip().splitlines()[-1]
    lines = ["# Phase 1b: accepted AST baseline and follow-ups", "",
             "Original code and artifacts were committed by the user as `f8c610d`. These follow-ups are uncommitted. "
             "No graph, selector, verifier, repair, oracle or benchmark test was rerun. Base archive code is only parsed with `ast`; "
             "there is no benchmark import/install/execution, Docker, network, gold-patch use or oracle analysis.", "",
             "**83 graph attempts: 56 complete, 23 partial, four resource-limited.** Original graph outputs and "
             "`base_feasibility.csv`, `feasibility.json`, `graph_inputs.json`, `inputs.json`, and `validation.json` are preserved. "
             "The original registered design is unchanged before the appended, pending amendment; its recorded SHA-256 still "
             "pins that prefix. The amendment below it is a proposal, not an active rule.", "",
             "## Synthetic tests", "",
             "The seven original checks passed. Additional follow-up checks cover namespace classification and new-name "
             "denominators; the exact selected-file pytest result and command are in `synthetic_tests.txt`. "
             "The initial plain invocation failed during third-party ROS plugin startup (`ModuleNotFoundError: lark`), "
             "before collection. Clearing `PYTHONPATH` and disabling plugin autoload avoids that environment dependency. "
             "Only `reports/callgraph_selection/test_static_graph.py` was collected. Synthetic fixture source is parsed, never executed.", "",
             f"Final selected-file result: **{test_result}**.", "",
             "```bash", "env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py -q -p no:cacheprovider -o addopts=", "```", "",
             "## Why the four SymPy builds stopped", "",
             "The frozen **5,000,000 AST-node limit is cumulative per task**, not per file. The files below crossed the "
             "remaining task allowance; they do not individually contain five million nodes. `Graph.check()` raises "
             "`ResourceLimit`, which is caught outside the whole file/build loop. Consequently, a limit in any file exits "
             "the build, skips import expansion and call resolution, and yields `resource_limited`. Syntax exceptions are "
             "instead caught inside the file loop and processing continues. This is the implemented frozen rule, not evidence "
             "of a malformed SymPy file. Checks occur every 4,096 nodes within a file and at file boundaries, explaining the "
             "small counter overshoot. The four stopped artifacts contain zero emitted edges; edge resolution was unavailable, "
             "not an observed absence of calls.", "",
             "The original resource diagnostics did **not** store the stopping path. Paths and per-file counts below are "
             "**inferred by deterministic AST-counter replay** over the hash-verified base tar, with the same lexical order "
             "and Python 3.11 checkpoint schedule. Every replay exactly matches the stored stop counter and parsed-file count. "
             "This recount neither constructs/retries a graph nor changes the stored artifacts.", "",
             "| Task | Crossing file | Nodes before file | Nodes in whole file | Recorded stop |",
             "|---|---|---:|---:|---:|"]
    for stop in summary["sympy_stops"]:
        lines.append(f"| {stop['instance_id']} | `{stop['path']}` | {stop['nodes_before_file']:,} "
                     f"| {stop['file_ast_nodes']:,} | {stop['observed_stop_counter']:,} |")
    lines += ["", "Full counters, inspected portion, file sizes, hashes and evidence status are in `sympy_limit_stops.csv`. "
              "A dated **DRAFT / NOT APPROVED / NOT APPLIED** amendment is appended to `design.md`. It proposes whole-file "
              "omission with a partial flag and explicit file list. Because today's limit counts cumulative inspected work, "
              "continuing requires an explicit budget-semantics change, not merely catching the same exception inside the loop. "
              "The draft separates a 5,000,000 retained-AST quota from a proposed 10,000,000 inspected-node work ceiling; "
              "the latter remains a task-wide hard stop. No counterfactual success or benefit is claimed, and no oracle "
              "information was used to diagnose or propose this change.", "",
              "## Call-resolution boundary", "",
              "Counts below partition the **79 completed full/partial graph artifacts**. All four resource-limit tasks have "
              "unavailable call classification and are omitted from this denominator. The historical resolved/ambiguous/unresolved "
              "labels are preserved; this is a separate diagnostic annotation, not resolver or verifier behavior.", "",
              "1. **Internal resolved:** recorded unique first-party definition target.",
              "2. **Internal ambiguous/unresolved:** a recorded first-party candidate, definition/receiver binding, or explicit "
              "first-party module/import namespace, with no unique resolved target.",
              "3. **External/builtin:** unshadowed builtin name, or an explicit import/module namespace whose root is outside "
              "the base first-party module inventory.",
              "4. **Unknown boundary:** parameters, assignments/rebinding, mixed origins, star-import/global/nonlocal uncertainty, "
              "dynamic receivers, and unsupported scopes without sufficient namespace evidence. These cannot honestly be "
              "forced into the other three buckets.", "",
              "Lexical binding lookup reuses stored scopes. Explicit import origins lost by the original import expansion are "
              "recovered from AST-only base imports using the existing `Indexer` import representation. Module inventory includes "
              "unparsed Python paths and namespace parents, so a missing internal parse is not automatically called external. "
              "Internal/external refers to nominal static namespace evidence, not proven runtime provenance; internal reexports, "
              "inherited third-party methods and monkey-patching remain limitations. No fuzzy matching or second test-ID normalizer "
              "is introduced.", "",
              "| Repository | Tasks | Internal resolved | Internal ambiguous/unresolved | External/builtin | Unknown boundary |",
              "|---|---:|---:|---:|---:|---:|"]
    for repo in summary["per_repository"]:
        lines.append(f"| {repo['repo']} | {repo['tasks_with_call_classification']} | {repo['internal_resolved']:,} "
                     f"| {repo['internal_ambiguous_unresolved']:,} | {repo['external_builtin']:,} | {repo['unknown_boundary']:,} |")
    lines.append(f"| **Total** | **79** | **{totals['internal_resolved']:,}** | **{totals['internal_ambiguous_unresolved']:,}** "
                 f"| **{totals['external_builtin']:,}** | **{totals['unknown_boundary']:,}** |")
    lines += ["", f"Partition total: **{sum(totals.values()):,} recorded call sites**. Per-task and repository tables are in "
              "`call_resolution_by_task.csv` and `call_resolution_by_repository.csv`; evidence/reason counts are in "
              "`followup_summary.json`. Unknown calls are not counted as internal failures or external calls.", "",
              "## Changed names: including and excluding new definitions", "",
              "Frozen candidates are available for **25 tasks: 19 confirmed historical snapshots and six local candidates "
              "with unverified final-run identity**. There are 58 missing patches. Changed-name resolution is measured on "
              "24 tasks (18 confirmed, six local); `sympy__sympy-17318` has an available candidate but no usable graph and "
              "retains blank measurements. Missing candidates are never substituted from another run.", "",
              "The existing `parse_patch` and `touched_symbols` are reused on the candidate's added and removed diff sides. "
              "A name is classified newly added only when the base diagnostic establishes its absence in a parsed changed "
              "file, a definition with that name occurs on added lines, and none occurs on removed definition lines. This "
              "identifies five names below. These are unavailable base seeds, **not graph-resolution failures**. This remains "
              "the existing file/simple-name inventory, including hunk context; a same-name addition alongside a base definition "
              "cannot be split into separate lexical seeds by that representation and is not guessed to be new.", "",
              "| Provenance | Denominator | Resolved | Ambiguous | Unresolved | Resolution rate |",
              "|---|---|---:|---:|---:|---:|"]
    for row in summary["changed_symbol_rates"]:
        label = "excluding new names" if row["exclude_newly_added"] else "including new names"
        lines.append(f"| {row['provenance']} | {row['total']} ({label}) | {row['resolved']} | {row['ambiguous']} "
                     f"| {row['unresolved']} | {row['resolution_rate']:.1%} |")
    lines += ["", "| Task | File | Newly added name |", "|---|---|---|"]
    for symbol in symbols:
        if symbol["origin"] == "newly_added_name_absent_at_base":
            lines.append(f"| {symbol['instance_id']} | `{symbol['path']}` | `{symbol['name']}` |")
    lines += ["", "All four remaining ambiguities are multiple same-name definitions in the changed file. Name origins and "
              "original classifications are preserved in `changed_symbol_origins.csv`; paired rates are in "
              "`changed_symbol_rates.csv`. Existing graph/seed artifacts remain unchanged.", "",
              "## Every partial graph, by file", "",
              f"**23 partial graphs, {len(partials)} file-level reasons:** 71 syntax/encoding failures and six Python symlink "
              "omissions across task snapshots. The complete task → file → reason → line/message listing is in "
              "[partial_graphs.md](partial_graphs.md) and `partial_graph_files.csv`. It includes all 15 partial Django, "
              "five partial pylint, and three partial pytest graphs. Each omitted file remains visible; none was excluded "
              "to turn a partial graph into a complete one.", "",
              "## Original feasibility by repository", "",
              "Counts below sum task snapshots, not unique files across repositories. Times are original graph-build "
              "measurements, not test runtimes. Resource-limit prefix file/node counts are lower bounds. Only the 56 complete "
              "graphs are eligible under the current design; 11 of the confirmed historical 19 are complete. Partial handling "
              "in the proposed amendment does not make partial graphs eligible for the primary comparison.", "",
              "| Repository | Complete / partial / limited | Python files / indexed parsed files | Parse failures / omitted | Nodes | Graph / total seconds |",
              "|---|---|---|---|---:|---|"]
    for row in baseline["per_repository"]:
        status = row["graph_status_counts"]
        lines.append(f"| {row['repo']} | {status.get('complete',0)} / {status.get('partial',0)} / {status.get('resource_limited',0)} "
                     f"| {row['python_files']:,} / {row['parsed_files']:,} | {row['parse_failures']} / {row['omitted_files']} "
                     f"| {row['nodes']:,} | {row['graph_runtime_seconds']:.2f} / {row['task_runtime_seconds']:.2f} |")
    lines += ["", "## Provenance, validation and reproduction", "",
              "Base sources are the user's read-only acquired archives under `~/cg_repos/task_archives/<instance_id>.tar`, "
              "with a `testbed/` prefix. The acquisition manifest pins all 83 base SHAs and archive hashes, and 12 clone "
              "HEADs; 11 repositories have headline tasks and requests has none. No clone worktree is read or modified. "
              "Follow-up AST metadata/counting reads verified tar members directly without retaining or executing source.", "",
              "The 19 confirmed candidate strings come from the hash-pinned snapshot's whitelist projection "
              "(`instance_id`, `source_run`, `agent_patch` only); all other values are skipped without decoding. Local "
              "candidates come only from the matching source-run path and pass the existing frozen-patch hash/size checks. "
              "The sixth local candidate, pytest-6202, was found during phase 1b; it remains exploratory.", "",
              "Original artifact validation passed all 83 tasks. It checked hashes, graph/CSV accounting, edge IDs, missing "
              "fields, cleanup and static post-hoc import boundaries. The earlier five root-annotation call omissions were "
              "corrected before the accepted commit; initial code hashes and reused/rebuilt provenance remain in "
              "`graph_inputs.json`. No new graph correction is applied in these follow-ups. Current `followup_inputs.json` "
              "pins the follow-up code, accepted graph manifest, pending design and derived outputs; original validation "
              "hashes describe the original report, not this updated report.", "",
              "Reproduce the read-only follow-up tables/report from the accepted stored baseline and local archives:", "",
              "```bash", "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/followup_analysis.py", "```", "",
              "Do not rerun `build_graphs.py` or treat the draft as active. The old validator checks an immutable design "
              "hash; this follow-up verifies the original prefix and separately hashes the pending amendment. "
              "The follow-up performs no selection, reachability ranking or oracle comparisons.", "",
              "**Nothing in the primary evaluation confirms that a selected test exercises the changed code.** Static "
              "resolution, including the new namespace categories, is a proxy and not dynamic coverage or correctness evidence.", "",
              "**Stopped before selectors. The amendment is pending approval and has not been implemented.**", ""]
    (OUT / "report.md").write_text("\n".join(lines))
    listing = ["# All 23 partial graphs: complete file-level reasons", "",
               "Stored phase-1b diagnostics only. Resource-limit stops are listed separately in `sympy_limit_stops.csv`.", "",
               "| Task | File | Reason | Line | Stored message |", "|---|---|---|---:|---|"]
    for row in sorted(partials, key=lambda r: (r["instance_id"], r["path"])):
        message = row.get("message", "Link/special member omitted without following it.").replace("|", "\\|")
        listing.append(f"| {row['instance_id']} | `{row['path']}` | {row['reason']} | {row.get('line') or ''} | {message} |")
    (OUT / "partial_graphs.md").write_text("\n".join(listing) + "\n")
