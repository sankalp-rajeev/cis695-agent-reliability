"""Summaries of frozen oracle-blind selector outputs; never changes selection."""
from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter, defaultdict

from inputs import HERE, CG, DESIGN_COMMIT, csv_write, dump, sha
from callgraph_selector import VARIANTS, DEPTHS, BUDGETS
from diagnostic import distribution

LARGE = ("django__django-13212", "astropy__astropy-13977", "django__django-12209",
         "django__django-13297", "django__django-14140", "django__django-14631")
STRATA = ("PRIMARY_COMPLETE", "EXTENDED_PARTIAL")


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def number(row, field):
    value = row.get(field, "")
    return float(value) if value not in ("", None) else None


def selected(row):
    value = number(row, "selected_count") if row else None
    return int(value) if value is not None else None


def table_index(rows):
    return {(r["instance_id"], r["strategy"], r["edge_variant"], int(r["depth"]), str(r["budget"])): r for r in rows}


def summarize(rows):
    """Pool only identical scope/stratum/variant/d/K/repo; preserve missing values."""
    lookup = table_index(rows)
    groups = defaultdict(list)
    for row in rows:
        scopes = (["HISTORICAL_19"] if row["historical_19"] == "True" else [])
        if row["strategy"] == "B":
            scopes.append("B_ALL_CONFIRMED_83")
        for scope in scopes:
            for repo in ("ALL", row["repo"]):
                groups[(scope, row["stratum"], row["edge_variant"], row["depth"], row["budget"], row["strategy"], repo)].append(row)
    summaries = []
    for key, group in sorted(groups.items()):
        scope, stratum, variant, depth, budget, strategy, repo = key
        common = [r for r in group if all(selected(lookup.get((r["instance_id"], s, variant, int(depth), budget))) is not None
                                        for s in ("A", "B", "C"))] if scope == "HISTORICAL_19" else group
        values = [selected(r) for r in common]
        stats = distribution(values)
        row = dict(scope=scope, stratum=stratum, edge_variant=variant, depth=int(depth), budget=budget,
                   strategy=strategy, repo=repo, cohort_tasks=len(group), common_evaluable_tasks=len(common),
                   available_tasks=stats["n"], missing_tasks=len(group) - stats["n"],
                   evaluation_eligible=stratum in STRATA,
                   **{k: stats.get(k) for k in ("mean", "median", "p75", "p90", "max", "total")},
                   tasks_ge_1000=sum(v is not None and v >= 1000 for v in values))
        if scope == "HISTORICAL_19":
            paired = [r for r in common if selected(r) is not None and number(r, "v2_same_budget_count") is not None]
            a_total = sum(number(r, "v2_same_budget_count") for r in paired)
            row.update(paired_A_tasks=len(paired), A_total=a_total,
                tasks_reduced_vs_A=sum(number(r, "delta_vs_same_budget_A") < 0 for r in paired),
                tasks_expanded_vs_A=sum(number(r, "delta_vs_same_budget_A") > 0 for r in paired),
                tasks_equal_vs_A=sum(number(r, "delta_vs_same_budget_A") == 0 for r in paired),
                total_reduction_vs_A=1 - sum(selected(r) for r in paired) / a_total if a_total else None,
                mean_delta_vs_A=distribution([number(r, "delta_vs_same_budget_A") for r in paired]).get("mean"))
        available = [r for r in common if selected(r) is not None]
        for name in ("reachable_selected_count", "mapped_unreachable_selected_count", "unmappable_selected_count",
                     "resolved_only_reachable_selected_count", "distance_1_selected_count", "distance_2_selected_count", "distance_3_selected_count"):
            row[name] = sum(number(r, name) or 0 for r in available)
        reachable = row["reachable_selected_count"]
        row["direct_proportion_of_reachable"] = row["distance_1_selected_count"] / reachable if reachable else None
        row["transitive_proportion_of_reachable"] = ((row["distance_2_selected_count"] + row["distance_3_selected_count"]) / reachable) if reachable else None
        row["mean_v2_retention_fraction"] = distribution([number(r, "v2_retention_fraction") for r in available]).get("mean")
        summaries.append(row)
    return summaries


def verdict(successes, denominator, threshold):
    if denominator == 0:
        return dict(label="failed", underlying="NOT_EVALUABLE", passed=False)
    passed = successes >= threshold
    return dict(label="met" if passed else "partly met" if successes else "failed", underlying="PASS" if passed else "FAIL", passed=passed)


def criteria(rows, eligibility):
    lookup = table_index(rows)
    eligible = {r["instance_id"]: r for r in eligibility["tasks"]}
    results = []
    for variant in VARIANTS:
        for stratum in STRATA:
            large = [iid for iid in LARGE if eligible[iid]["stratum"] == stratum]
            primary = stratum == STRATA[0]
            c1_hits, c2_hits = [], []
            for iid in large:
                b = selected(lookup.get((iid, "B", variant, 2, "ALL")))
                c = lookup.get((iid, "C", variant, 2, "100"))
                if b is not None and 1 <= b <= 250:
                    c1_hits.append(iid)
                if c and (number(c, "reachable_selected_count") or 0) > 0:
                    c2_hits.append(iid)
            for name, hits in (("C1", c1_hits), ("C2", c2_hits)):
                result = dict(criterion=name, stratum=stratum, edge_variant=variant, successes=len(hits),
                    eligible_tasks=len(large), denominator=6 if primary else len(large), threshold=5 if primary else None,
                    success_tasks=hits, excluded_fixed_tasks=[iid for iid in LARGE if iid not in large],
                    decides=primary and variant == VARIANTS[0], descriptive_only=not (primary and variant == VARIANTS[0]))
                result.update(verdict(len(hits), result["denominator"], 5) if primary else dict(label="descriptive only", underlying="NOT_A_PRIMARY_CRITERION", passed=False))
                results.append(result)
            ids = eligibility["c3_primary_eligible" if primary else "c3_extended_eligible"]
            hits = [iid for iid in ids if (selected(lookup.get((iid, "B", variant, 3, "ALL"))) or 0) >= 1]
            threshold = math.ceil(len(ids) / 2)
            result = dict(criterion="C3", stratum=stratum, edge_variant=variant, successes=len(hits),
                eligible_tasks=len(ids), denominator=len(ids), threshold=threshold if primary else None,
                success_tasks=hits, eligible_task_ids=ids,
                excluded_fixed_tasks=[iid for iid, e in eligible.items() if e["v2_outcome"] == "NOT_AVAILABLE" and iid not in ids],
                decides=primary and variant == VARIANTS[0], descriptive_only=not (primary and variant == VARIANTS[0]))
            result.update(verdict(len(hits), len(ids), threshold) if primary else dict(label="descriptive only", underlying="NOT_A_PRIMARY_CRITERION", passed=False))
            results.append(result)
    primary = {r["criterion"]: r for r in results if r["decides"]}
    rank_filter = primary["C1"]["passed"] and primary["C2"]["passed"]
    fallback = primary["C3"]["passed"]
    decision = ("Both rank/filter layer over Tier 2 and fallback" if rank_filter and fallback else
                "Rank/filter layer over Tier 2" if rank_filter else "Fallback only" if fallback else
                "Do not use on this experiment's evidence")
    return dict(results=results, rank_filter_supported=rank_filter, fallback_supported=fallback, decision_map_outcome=decision)


def fmt(value):
    if value is None or value == "":
        return "NA"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def eff_table(rows):
    lines = ["| Scope / selector | d | K | n / cohort | Median | Mean | p75 | p90 | Max | Tasks ≥1000 | Reduced / expanded vs A | Total reduction vs A |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for r in sorted(rows, key=lambda x: (x["scope"], x["strategy"], x["depth"], 1000000 if x["budget"] == "ALL" else int(x["budget"]))):
        delta = f"{r['tasks_reduced_vs_A']} / {r['tasks_expanded_vs_A']}" if "paired_A_tasks" in r else "NA"
        fraction = r.get("total_reduction_vs_A")
        reduction = f"{fraction:.1%}" if fraction is not None else "NA"
        scope = "19" if r["scope"] == "HISTORICAL_19" else "B broader"
        lines.append(f"| {scope} / {r['strategy']} | {r['depth']} | {r['budget']} | {r['available_tasks']} / {r['cohort_tasks']} | "
                     f"{fmt(r['median'])} | {fmt(r['mean'])} | {fmt(r['p75'])} | {fmt(r['p90'])} | {fmt(r['max'])} | "
                     f"{r['tasks_ge_1000']} | {delta} | {reduction} |")
    return lines


def report():
    from run import verify_freeze
    freeze = verify_freeze()  # required before any summarization
    rows = read_csv(HERE / "per_task.csv")
    lookup = table_index(rows)
    eligibility = json.loads((HERE / "eligibility.json").read_text())
    by_id = {r["instance_id"]: r for r in eligibility["tasks"]}
    summaries = summarize(rows)
    csv_write(HERE / "selector_summary.csv", summaries)
    measured = criteria(rows, eligibility)
    dump(HERE / "criteria.json", measured)
    specificity = read_csv(HERE / "seed_specificity.csv")
    diagnostics = read_csv(HERE / "graph_diagnostics.csv")
    incidents = json.loads((HERE / "incidents.json").read_text())
    unmatched = []
    with gzip.open(HERE / "ranked_outputs.jsonl.gz", "rt") as stream:
        for line in stream:
            record = json.loads(line)
            if record['strategy'] == 'C' and record['edge_variant'] == VARIANTS[0] and record['depth'] == 1:
                unmatched.extend(dict(instance_id=record['instance_id'], test_id=c['test_id'],
                    normalization_method=c.get('normalization_method'), mapping_reason=c.get('mapping_reason'),
                    graph_status=c['graph_status']) for c in record['candidates'] if c['graph_status'] == 'unmappable')
    csv_write(HERE / "unmatched_v2_ids.csv", unmatched,
              ("instance_id", "test_id", "normalization_method", "mapping_reason", "graph_status"))
    repository_rows = []
    repos = sorted({r['repo'] for r in diagnostics} | {'psf/requests'})
    for repo in repos:
        group = [r for r in diagnostics if r['repo'] == repo]
        builds = [json.loads(r['graph_build_counts']) for r in group]
        repository_rows.append(dict(repo=repo, tasks=len(group), complete_graphs=sum(r['graph_build_status'] == 'complete' for r in group),
            partial_graphs=sum(r['graph_build_status'] == 'partial' for r in group),
            primary_eligible=sum(r['stratum'] == STRATA[0] for r in group), extended_eligible=sum(r['stratum'] == STRATA[1] for r in group),
            excluded=sum(r['stratum'] == 'EXCLUDED' for r in group),
            python_files=sum(b.get('python_files', 0) for b in builds), nodes=sum(int(r['nodes']) for r in group),
            parse_failures=sum(b.get('parse_failures', 0) for b in builds), omitted_files=sum(b.get('omitted_files', 0) for b in builds),
            resolved_calls=sum(json.loads(r['edge_status_counts']).get('resolved', 0) for r in group),
            ambiguous_calls=sum(json.loads(r['edge_status_counts']).get('ambiguous', 0) for r in group),
            unresolved_calls=sum(json.loads(r['edge_status_counts']).get('unresolved', 0) for r in group),
            base_test_ids=sum(int(r['distinct_base_ids']) for r in group),
            represented_definitions=sum(int(r['represented_base_test_definitions'] or 0) for r in group)))
    csv_write(HERE / 'repository_graph_summary.csv', repository_rows)
    primary = {r['criterion']: r for r in measured['results'] if r['decides']}
    lines = ['# Phase 2-lite: offline static test selection', '',
        '2026-10-22. Selectors and eligibility were frozen before this analysis. No oracle comparison, gold patch, '
        'benchmark import/collection/execution, Docker or network was used. No commits or phase 3.', '',
        '## Plain-language answer (seven lines)', '',
        f"Call graphs receive the following support from the registered decision map: **{measured['decision_map_outcome']}**.",
        f"C1 is {primary['C1']['label']} ({primary['C1']['successes']}/6 fixed large cases; threshold 5).",
        f"C2 is {primary['C2']['label']} ({primary['C2']['successes']}/6 fixed large cases; threshold 5).",
        f"C3 is {primary['C3']['label']} ({primary['C3']['successes']}/{primary['C3']['denominator']} eligible NOT_AVAILABLE cases; threshold {primary['C3']['threshold']}).",
        'The graph-only selector can return fewer candidates; C keeps the full V2 union and changes its order before budget prefixes.',
        'Qualified partial graphs and ambiguous-edge results are reported separately and cannot change that decision.',
        'These are static candidate counts, not evidence of runtime savings or defect detection.', '',
        'Nothing in the primary evaluation confirms that a selected test actually exercises the changed code.', '',
        '## Deviations and incidents', '',
        '- A usage-limit pause interrupted phase-2 implementation; the agent resumed after auditing the full worktree, '
        'README, existing tests and absence of selector outputs. The complete pre-resume file inventory is in '
        '`resume_state.md` / `resume_state.json`.',
        '- The first execution failed before constructing any candidate because the tar root directory was stored as '
        '`testbed`, while the reader required `testbed/`. The reader now accepts either root-directory spelling; '
        'a synthetic archive regression test was added. The failed attempt\'s files, hashes and pre-fix code hashes '
        'are preserved under `failed_attempts/archive_root_check/`.',
        '- The next foreground execution ended abruptly during the interrupted chat/tool session. '
        + incidents['interrupted_run'] + ' The stored log has 23 completed-task records ending at '
        '`django__django-15103`; the user reported 24 tasks. No completed 24th-task record survived, so both '
        'counts are recorded without inventing an exit status. Partial files were moved to '
        '`failed_attempts/interrupted_foreground_run/` and hashed only as failed-attempt evidence, '
        'never treated as a successful selector freeze or analyzed for results.',
        '- Long execution was restarted from scratch under `nohup`, retaining stdout/stderr and an exit-status file. '
        'The original eligibility files were reused unchanged. Execution and output freezing are now separate stages; '
        'all 83 task IDs and an explicit completion line were verified before any successful-output hash or analysis.',
        '**No ranking rule, eligibility rule or frozen parameter changed. No selector output was seen before the fixes:** '
        'candidate IDs, scores, selected-set counts, summaries and criterion outcomes were not inspected; '
        'only progress logs, file metadata and gzip integrity were checked. The selector/ranking module matches its '
        'pre-fix hash. The frozen design remains unchanged.', '',
        f"Eligibility-freeze file SHA-256 (`eligibility_freeze.json`): `{incidents['eligibility_freeze_file_sha256']}`.", '',
        f"Frozen eligibility payload SHA-256 (`eligibility.json`): `{incidents['eligibility_json_sha256']}`. "
        'It was written and frozen **before any selector output**: the runner persists both files before entering '
        'the selector writer, and the same eligibility digest is already recorded in the archive-reader failure manifest. '
        'The freeze files were not rewritten on either restart.', '',
        'Every autonomous rerun is listed below; the failure manifests retain the earlier attempts:', '',
        '| Rerun | Launch | Outcome | Task records | Exit |', '|---|---|---|---:|---:|',
        *[f"| {r['attempt']} | {r['launch']} | {r.get('status', 'unknown')}: {r.get('cause', 'completed without a selector exception')} | {r.get('completed_task_records', 'NA')} | {r.get('exit_status', 'NA')} |"
          for r in incidents['autonomous_reruns']], '',
        'Conservative readings: an unrecorded termination cause is reported as unknown, rather than assigned to a '
        'timeout or crash. Finished partials with other omission reasons have diagnostic-only results and never '
        'enter either evaluation stratum. Unmappable IDs retain missing graph features and cannot manufacture '
        'reachability; base identities use the existing production extractor and diagnostic normalizer only. '
        'The shared-tail interpretation was explicitly approved by the user and recorded before execution.', '',
        '## Frozen inputs, populations and outcomes', '',
        f"Design commit: `{DESIGN_COMMIT}`; code revision: `{freeze['code_revision']}`, with uncommitted code pinned by SHA-256 in `inputs.json`. "
        'The design is unchanged. `selector_freeze.json` binds the selector outputs before analysis; `outputs.sha256.json` '
        'and its SHA-256 sidecar bind the final report bundle. Every consumed graph, archive, snapshot, patch-export and '
        'manifest input is hashed. The original phase-1 graphs, run artifacts, policies and manifests are unchanged.', '',
        'All 83 candidate patches match the verified export manifest; CSV source_run is final-study provenance. '
        'The export is read directly from the previously supplied local frozen_patches_export.tgz. '
        'Base test identities use stored local exact-commit task archives, without importing or executing source. '
        'A and C use only the exact stored selection IDs/order for the 19 study_snapshot tasks; no V2 rerun occurs.', '',
        '| Stratum | All 83 tasks | Stored-selection tasks | Evaluation status |',
        '|---|---:|---:|---|']
    for stratum in (*STRATA, 'EXCLUDED'):
        group = [e for e in by_id.values() if e['stratum'] == stratum]
        lines.append(f"| {stratum} | {len(group)} | {sum(e['artifact_kind'] == 'study_snapshot' for e in group)} | "
                     f"{'Separate evaluation' if stratum in STRATA else 'Diagnostic only / unavailable'} |")
    lines += ['', 'B runs on every finished graph with a verified patch and resolved seeds, including diagnostic-only '
              'partials with other omission reasons. Those EXCLUDED results never enter primary or extended evaluation. '
              'Zero resolved seeds, ambiguous-only seeds, missing graphs and empty reachability are distinct. '
              '`eligibility.json` and its hash were written before traversal; the C3 primary denominator is fixed at '
              f"{len(eligibility['c3_primary_eligible'])} tasks.", '',
              '| Excluded task | Reason | Graph | Resolved / ambiguous / unresolved names |', '|---|---|---|---|']
    for e in by_id.values():
        if e['stratum'] == 'EXCLUDED':
            lines.append(f"| {e['instance_id']} | {e['eligibility_reason']} | {e['graph_build_status']} | "
                         f"{e['resolved_seeds']} / {e['ambiguous_seeds']} / {e['unresolved_seeds']} |")
    lines += ['', '## Registered criteria and decision map', '',
              'Only PRIMARY_RESOLVED_ONLY on PRIMARY_COMPLETE decides. “Partly met” means some successes below the '
              'registered threshold; its formal result is FAIL. C1/C2 keep all six fixed rows in their denominators, '
              'including the partial Django-14631. C3 uses only its pre-frozen eligible denominator.', '',
              '| Criterion | Result | Successes / denominator | Eligible | Required | Formal result |', '|---|---|---:|---:|---:|---|']
    for name in ('C1', 'C2', 'C3'):
        r = primary[name]
        lines.append(f"| {name} | **{r['label']}** | {r['successes']} / {r['denominator']} | {r['eligible_tasks']} | {r['threshold']} | {r['underlying']} |")
    lines += ['', 'C1: B at d=2 has 1–250 unbudgeted tests. C2: C at d=2, K=100 contains a stored V2 candidate '
              'with a resolved path of length ≤2 to a resolved changed seed. C3: B at d=3 selects a pre-existing test '
              'for at least half the eligible NOT_AVAILABLE tasks.', '',
              f"**Decision-map outcome: {measured['decision_map_outcome']}.** Rank/filter support requires C1 AND C2; "
              'fallback support requires C3. This experiment alone cannot support replacing Tier 2.', '',
              '| Separate descriptive counterpart | Variant | Criterion | Hits / denominator | Note |', '|---|---|---|---:|---|']
    for r in measured['results']:
        if not r['decides']:
            lines.append(f"| {r['stratum']} | {r['edge_variant']} | {r['criterion']} | {r['successes']} / {r['denominator']} | "
                         f"{'Fixed six; secondary does not decide' if r['stratum'] == STRATA[0] else 'Eligible extended subset only; never pooled'} |")
    lines += ['', '## Six large cases', '',
              'B columns are unbudgeted; “V2 reachable” counts candidates in the full C union with graph paths at each depth. '
              'C prefix sizes are reported in K order 25/50/100/250/500 and are identical across depths; '
              'unbudgeted C always retains all V2 candidates. Counts do not establish execution coverage.']
    case_rows = []
    for variant in VARIANTS:
        lines += ['', f'### {variant}', '',
                  '| Task | Stratum | V2 | B d1 / d2 / d3 | V2 reachable d1 / d2 | C sizes by K, all d | C K100 d2 reachable |', '|---|---|---:|---|---|---|---:|']
        for iid in LARGE:
            def row(s, d, k='ALL'):
                return lookup.get((iid, s, variant, d, str(k)))
            a = selected(row('A', 1))
            counts = [selected(row('B', d)) for d in DEPTHS]
            reachable = [int(number(row('C', d), 'reachable_candidate_count') or 0) for d in (1, 2)]
            c_sizes = [selected(row('C', 2, k)) for k in BUDGETS]
            c_hits = int(number(row('C', 2, 100), 'reachable_selected_count') or 0)
            case_rows.append(dict(instance_id=iid, edge_variant=variant, stratum=by_id[iid]['stratum'], v2_count=a,
                B_depth1=counts[0], B_depth2=counts[1], B_depth3=counts[2], V2_reachable_depth1=reachable[0],
                V2_reachable_depth2=reachable[1], C_sizes_by_budget=c_sizes, C_top100_depth2_reachable=c_hits))
            lines.append(f"| {iid} | {by_id[iid]['stratum']} | {a} | {' / '.join(map(fmt, counts))} | "
                         f"{' / '.join(map(fmt, reachable))} | {' / '.join(map(fmt, c_sizes))} | {c_hits} |")
        lines += ['', '| Task | Changed seeds: depth-3 fan-in, weight | Model.save fan-in, weight | Does specificity favor changed seeds over this hub? |', '|---|---|---|---|']
        for iid in LARGE:
            seeds = [r for r in specificity if r['instance_id'] == iid and r['edge_variant'] == variant and r['role'] == 'CHANGED_SEED']
            hubs = [r for r in specificity if r['instance_id'] == iid and r['edge_variant'] == variant and r['role'] == 'HUB_DIAGNOSTIC_ONLY']
            text = '; '.join(f"{r['qualname']}: {r['fan_in_depth3']}, 1/{r['weight_denominator']}" for r in seeds) or 'Unavailable'
            if not hubs:
                hub_text, answer = 'Absent', 'Could not assess this comparison: no Model.save in this base graph.'
            else:
                h = int(hubs[0]['fan_in_depth3'])
                hub_text = f"{h}, 1/{1+h}"
                lower = sum(int(r['fan_in_depth3']) < h for r in seeds)
                answer = (f"Yes for {lower}/{len(seeds)} seeds (lower observed fan-in)." if lower else
                          'No: it could not prefer a changed seed over Model.save by observed fan-in.')
                if h == 0:
                    answer += ' Model.save has zero represented test reachability, so the static model gives it maximum weight.'
            lines.append(f"| {iid} | {text} | {hub_text} | {answer} |")
    csv_write(HERE / 'large_cases.csv', case_rows)
    lines += ['', '## Every NOT_AVAILABLE task', '',
              'Values are pre-existing candidate counts at d=1/2/3. Zero is measured empty reachability; NA is unavailable, '
              'never an empty set. The primary C3 numerator uses only the complete, eligible d=3 rows. '
              'Diagnostic excluded rows and qualified extended rows are kept separate.', '',
              '| Task | Stratum / reason | PRIMARY B d1 / d2 / d3 | SECONDARY B d1 / d2 / d3 | Primary d3 any? |', '|---|---|---|---|---|']
    na_rows = []
    for iid, e in by_id.items():
        if e['v2_outcome'] != 'NOT_AVAILABLE':
            continue
        values = [[selected(lookup.get((iid, 'B', variant, d, 'ALL'))) for d in DEPTHS] for variant in VARIANTS]
        any_value = 'NA' if values[0][2] is None else 'yes' if values[0][2] else 'no'
        lines.append(f"| {iid} | {e['stratum']} / {e['eligibility_reason']} | {' / '.join(map(fmt, values[0]))} | "
                     f"{' / '.join(map(fmt, values[1]))} | {any_value} |")
        for variant, counts in zip(VARIANTS, values):
            na_rows.append(dict(instance_id=iid, edge_variant=variant, stratum=e['stratum'], eligibility_reason=e['eligibility_reason'],
                B_depth1=counts[0], B_depth2=counts[1], B_depth3=counts[2], any_depth3=counts[2] > 0 if counts[2] is not None else None,
                primary_C3_denominator_member=iid in eligibility['c3_primary_eligible']))
    csv_write(HERE / 'not_available.csv', na_rows)
    lines += ['', '## Candidate efficiency: all frozen depths and budgets', '',
              '“19” is the historical stored-selection cohort, separately limited to common-evaluable tasks in each stratum. '
              '“B broader” is the new graph-only analysis of confirmed patches, not an 83-task A/B/C comparison. '
              'Each table is separate: do not pool strata or variants. All five budgets and ALL are shown. '
              'Quantiles use the existing diagnostic linear interpolation. Reductions/expansions compare the same task and '
              'same budget with A; total reduction uses summed counts, not a runtime estimate. '
              'A is repeated across depth/variant only to align configurations, not as independent evidence. '
              '`selector_summary.csv` also gives per-repository results, direct/transitive proportions, distance bins and V2 retention.', '']
    for stratum in STRATA:
        for variant in VARIANTS:
            lines += [f'<details><summary>{stratum} — {variant}: every depth and budget</summary>', '']
            lines += eff_table([r for r in summaries if r['stratum'] == stratum and r['edge_variant'] == variant and r['repo'] == 'ALL'])
            lines += ['', '</details>', '']
    paired_variant = []
    for r in rows:
        if r['edge_variant'] != VARIANTS[0] or r['stratum'] not in STRATA:
            continue
        other = lookup.get((r['instance_id'], r['strategy'], VARIANTS[1], int(r['depth']), r['budget']))
        if selected(r) is not None and selected(other) is not None:
            paired_variant.append(dict(instance_id=r['instance_id'], stratum=r['stratum'], strategy=r['strategy'],
                depth=r['depth'], budget=r['budget'], primary_count=selected(r), secondary_count=selected(other),
                secondary_minus_primary=selected(other) - selected(r),
                primary_reachable=int(number(r, 'reachable_selected_count') or 0),
                secondary_reachable=int(number(other, 'reachable_selected_count') or 0),
                secondary_resolved_only_reachable=int(number(other, 'resolved_only_reachable_selected_count') or 0)))
    csv_write(HERE / 'paired_variants.csv', paired_variant)
    status_fields = ('instance_id', 'stratum', 'strategy', 'edge_variant', 'depth', 'outcome',
                     'reachable_candidate_count', 'mapped_unreachable_candidate_count', 'unmappable_candidate_count')
    csv_write(HERE / 'graph_status_by_task.csv', [{k: r[k] for k in status_fields} for r in rows if r['budget'] == 'ALL'], status_fields)
    lines += ['## Candidate graph_status counts per task', '',
              '`graph_status_by_task.csv` gives every task/strategy/variant/depth; `per_task.csv` additionally gives '
              'selected-prefix counts at each K. The full A and C unions have identical status counts; only their order '
              'differs. B candidates are reachable pre-existing tests only; its other two status counts are zero when '
              'available, and missing when unavailable. The table gives depth-1/2/3 triplets; NA is unavailable.', '',
              '<details><summary>All 83 tasks, both variants: B and full stored-union status counts</summary>', '',
              '| Task | Stratum | Variant | B reachable d1/d2/d3 | A/C reachable d1/d2/d3 | A/C mapped-unreachable d1/d2/d3 | A/C unmappable d1/d2/d3 |',
              '|---|---|---|---|---|---|---|']
    for iid, entry in by_id.items():
        for variant in VARIANTS:
            b = [selected(lookup.get((iid, 'B', variant, d, 'ALL'))) for d in DEPTHS]
            groups = []
            for status in ('reachable', 'mapped_unreachable', 'unmappable'):
                values = []
                for d in DEPTHS:
                    record = lookup.get((iid, 'A', variant, d, 'ALL'))
                    value = number(record, status + '_candidate_count') if record else None
                    values.append(int(value) if value is not None else None)
                groups.append(' / '.join(map(fmt, values)))
            lines.append(f"| {iid} | {entry['stratum']} | {variant} | {' / '.join(map(fmt, b))} | {' | '.join(groups)} |")
    lines += ['', '</details>', '']
    lines += ['## Graphs, identities and bounded provenance', '',
              '| Repository | Tasks | Complete / partial | Eligible primary / extended | Files | Nodes | Resolved / ambiguous / unresolved calls | Parse failures / omissions |',
              '|---|---:|---|---|---:|---:|---|---|']
    for r in repository_rows:
        lines.append(f"| {r['repo']} | {r['tasks']} | {r['complete_graphs']} / {r['partial_graphs']} | {r['primary_eligible']} / {r['extended_eligible']} | "
                     f"{r['python_files']} | {r['nodes']} | {r['resolved_calls']} / {r['ambiguous_calls']} / {r['unresolved_calls']} | {r['parse_failures']} / {r['omitted_files']} |")
    counts = json.loads((HERE / 'provenance_counts.json').read_text())
    lines += ['', 'Counts sum task-specific base snapshots, not unique files across a repository. Unresolved calls include '
              'external/dynamic/unsupported calls; the table is not an internal-call resolution rate. '
              '`graph_diagnostics.csv` lists every omitted/unparseable path, seed status, call reason, graph location and base-identity mapping count. '
              'All qualified partials retain their full reasons in `eligibility.json`; no missing file becomes resolved.', '',
              'Test-ID matching calls the existing diagnostic `canonical`, `family`, and `match_test` functions, with an empty '
              'gold-identity map and only base/selected IDs. Exact identities and documented explicit parameter families only; '
              'no fuzzy, bare-name or Django docstring guessing. The production `node_ids` supplies base candidates. '
              'Legacy nested-class IDs, duplicate definitions and parse/omission gaps stay unmappable. '
              f"`unmatched_v2_ids.csv` lists all {len(unmatched)} unmappable stored candidates (one inventory per task, not duplicated by d/K/variant).", '',
              'Every frozen candidate has graph_status reachable / mapped_unreachable / unmappable; per-task rows contain candidate '
              'and selected counts for each. Mapped-unreachable scores are 0; unmappable scores/direct counts/distances remain null. '
              'Their common C tail uses computable module/package features and original V2 position, without priority for mapping status.', '',
              f"Full paths retained by variant: {counts['full_paths_by_variant']}; the maximum is 22,950 per variant / 45,900 overall. "
              'Only top 25 B/C candidates per task/variant/depth carry up to three lexical-seed paths of at most three hops. '
              'Budgets share those rows; all later ranks and omitted seed paths are aggregated by distance and budget membership. '
              'Secondary provenance flags each ambiguous hop, original call site, candidate targets and reasons, and records whether '
              'resolved-only reachability exists at the same depth. Ambiguity on a selected shortest path does not prove it is required.', '',
              '`paired_variants.csv` provides common-task primary/secondary counts and resolved-only retention; '
              'it never pools variants or changes the primary decision.', '',
              '## Validation and reproduction', '',
              'Synthetic fixtures only; benchmark tests are not run. The exact test output is in `tests.txt`. '
              '`validation.json` checks frozen inputs/outputs, budgets, identities, shared-tail ranking, strata, criteria and provenance caps.', '',
              '```bash',
              'env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest reports/callgraph_selection/test_static_graph.py reports/callgraph_selection/test_amended_graph.py reports/callgraph_selection/phase2/test_phase2.py -q -p no:cacheprovider -o addopts=',
              '# Detached execution used for this run; wait for BACKGROUND_RUN_COMPLETE exit=0, then freeze:',
              'nohup bash reports/callgraph_selection/phase2/run_background.sh > reports/callgraph_selection/phase2/background_attempt_2.log 2>&1 < /dev/null &',
              'cg_selector_pid=$!',
              'printf "%s\\n" "$cg_selector_pid" > reports/callgraph_selection/phase2/selector_pid.txt',
              'wait "$cg_selector_pid"  # Keep the sandbox parent alive; poll the background log from another call.',
              'env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage freeze',
              'env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage report',
              'env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/validate.py',
              '```', '',
              'The select stage refuses to overwrite an existing selector freeze. Reproduce selection in a clean copy containing '
              'the pinned code/README and local inputs but none of the generated phase-2 outputs; report-only reproduction verifies '
              'the existing freeze and does not rerun selection. All changes remain inside reports/callgraph_selection/ and uncommitted. '
              'Work stops at this report, before phase 3.', '']
    plain_index = lines.index('## Plain-language answer (seven lines)') + 2
    plain_summary = lines[plain_index:plain_index + 7]
    completion = json.loads((HERE / 'selector_completion.json').read_text())
    (HERE / 'MORNING_SUMMARY.md').write_text(
        f"COMPLETED — {completion['tasks']} headline tasks accounted for (B: {completion['applicable_B_tasks']} applicable; "
        f"A/C: {completion['stored_A_C_tasks']} stored-selection tasks). Report: report.md.\n\n" +
        '\n'.join(plain_summary) + '\n')
    (HERE / 'report.md').write_text('\n'.join(lines))
