"""Finish the read-only three-phase report, after the selector freeze exists.

Diagnosis uses V2-only projections, source, and base ASTs. Oracle fields are
opened only for phase-2 accounting and phase-3 post-hoc labels/retention.
"""
import ast
import csv
import hashlib
import io
import json
import tarfile
from collections import Counter
from pathlib import Path

from freeze import OUT, ROOT, read, dump, write_csv, stamp, sha, INPUTS, object_items, whitespace, skip_json

SNAPSHOT = ROOT / "reports/failure_analysis/extracted.json"
TARGETS = {"pylint-dev__pylint-6528": "main_50_a", "pylint-dev__pylint-7277": "main_50_a", "django__django-13297": "main_50_b"}
SUGGESTED_DIFF = '''--- a/src/reliability/verifier/container.py
+++ b/src/reliability/verifier/container.py
@@ -362,9 +362,16 @@ def _parse_pytest(output: str, tests: tuple[str, ...]) -> dict[str, TestStatus]:
     statuses: dict[str, TestStatus] = {}
     for line in output.splitlines():
         match = _PYTEST_LINE.match(line.strip())
-        if match is None or match.group("id") not in wanted:
+        if match is None:
             continue
-        test, status = match.group("id"), _PYTEST_OUTCOME[match.group("outcome")]
+        test = match.group("id")
+        if test not in wanted and "[" in test:
+            family = test.split("[", 1)[0]
+            if family in wanted:
+                test = family
+        if test not in wanted:
+            continue
+        status = _PYTEST_OUTCOME[match.group("outcome")]
         earlier = statuses.get(test)
         if earlier is None or _PYTEST_SEVERITY[status] >= _PYTEST_SEVERITY[earlier]:
             statuses[test] = status
'''


def phase1():
    """Runs before any post-hoc input is opened by this process."""
    snapshots = json.loads(read(OUT / "v2_projection.json"))
    diagnoses, availability, param = [], [], []
    for iid, run in TARGETS.items():
        r = snapshots[iid]
        if r["source_run"] != run:
            raise ValueError("V2 source run conflict")
        reg = r["regression"]
        checked = [ROOT / "runs" / run / "tasks" / iid / name for name in ("verification_record.full.json", "verification_record.baseline.json")]
        checked += [ROOT / "runs" / run / "_baseline_cache" / (iid + ".baseline.json"),
                    ROOT / "reports/failure_analysis/_baseline_cache_copy" / (iid + ".baseline.json")]
        for p in checked:
            availability.append({"instance_id": iid, "path": str(p.relative_to(ROOT)), "exists": p.exists(), "status": "confirmed"})
        missing = ["same-run per-test base statuses and IDs", "same-run per-test patched statuses and IDs",
                   "per-test final classifications", "raw base/patched runner stdout or result logs",
                   "per-test completion/timeout identity and timestamps", "exact historical executor source revision"]
        diagnoses.append({"instance_id": iid, "source_run": run, "primary_cause": "(f) UNKNOWN",
                          "cause_status": "inferred", "v2_outcome": reg["outcome"], "recorded_summary": reg["findings"]["summary"],
                          "n_selected": len(r["selected_tests"]), "n_executed": reg["findings"]["n_executed"],
                          "evidence": f"reports/failure_analysis/extracted.json:{r['source_lines']['regression']}",
                          "selected_evidence": f"reports/failure_analysis/extracted.json:{r['source_lines']['selected_tests']}",
                          "missing": missing, "recorded_values_status": "confirmed",
                          "why_unknown": "Aggregate counts do not identify which tests were NOT_RUN/PRE_EXISTING_FAIL/TIMEOUT; no raw per-pass records establish a cause."})
        # Scan every selected family, not an oracle-picked test. This checks parser compatibility only.
        wanted = set(r["selected_tests"])
        archive = Path.home() / "cg_repos/task_archives" / (iid + ".tar")
        with tarfile.open(archive) as tar:
            members = {m.name: m for m in tar if m.isfile()}
            for path in sorted({x.split("::")[0] for x in wanted}):
                member = members.get("testbed/" + path)
                if not member:
                    continue
                try:
                    tree = ast.parse(tar.extractfile(member).read().decode())
                except (SyntaxError, UnicodeError, ValueError):
                    continue
                def visit(body, classes=()):
                    for n in body:
                        if isinstance(n, ast.ClassDef):
                            visit(n.body, classes + (n.name,))
                        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            tid = path + "::" + "::".join(classes + (n.name,))
                            if tid in wanted:
                                decorators = [ast.unparse(d) for d in n.decorator_list]
                                if any("parametrize" in d for d in decorators):
                                    param.append({"instance_id": iid, "selected_family": tid,
                                                  "archive": str(archive), "member": "testbed/" + path,
                                                  "definition_line": n.lineno, "decorators": decorators,
                                                  "parser_evidence": "src/reliability/verifier/container.py:365",
                                                  "source_fact_status": "confirmed", "actual_cause": "UNKNOWN; raw per-pass output absent", "cause_status": "inferred"})
                visit(tree.body)
    write_csv(OUT / "phase1_diagnoses.csv", diagnoses)
    write_csv(OUT / "phase1_record_availability.csv", availability)
    write_csv(OUT / "phase1_parametrized_families.csv", param)
    dump(OUT / "phase1_completed_before_posthoc.json", {"completed_utc": stamp(), "oracle_diagnosis_inputs": False,
         "files_sha256": {name: sha((OUT / name).read_bytes()) for name in ("phase1_diagnoses.csv", "phase1_record_availability.csv", "phase1_parametrized_families.csv")}})
    for name in ("regression.py", "container.py", "selection.py", "run.py", "record.py"):
        read(ROOT / "src/reliability/verifier" / name)
    return diagnoses, param


def phase2():
    """Oracle outcome is a post-hoc label here; never an input to diagnosis/selectors."""
    all_rows = list(csv.DictReader(io.StringIO(read(ROOT / "docs/results_100.csv").decode())))
    rows = [r for r in all_rows if r["stratum"] == "headline" and r["oracle"] != "empty_patch"]
    missing = [r["instance_id"] for r in rows if r["regression"] not in {"PASS", "FAIL", "NOT_AVAILABLE"}]
    write_csv(OUT / "phase2_outcomes.csv", [{"instance_id": r["instance_id"], "repo": r["repo"], "source_run": r["source_run"],
         "posthoc_right_wrong": "right" if r["oracle"] == "resolved" else "wrong", "v2_outcome": r["regression"],
         "label_status": "confirmed", "v2_status": "confirmed"} for r in rows])
    if missing:
        dump(OUT / "missing_v2_outcomes.json", missing)
        raise SystemExit("V2 labels missing; stopped after listing them")
    counts = []
    for repo in ["ALL"] + sorted({r["repo"] for r in rows}):
        for label in ("right", "wrong"):
            cohort = [r for r in rows if (repo == "ALL" or r["repo"] == repo) and (r["oracle"] == "resolved") == (label == "right")]
            c = Counter(r["regression"] for r in cohort)
            usable = c["PASS"] + c["FAIL"]
            counts.append({"repo": repo, "posthoc_label": label, "total": len(cohort), "PASS": c["PASS"], "FAIL": c["FAIL"],
                           "NOT_AVAILABLE": c["NOT_AVAILABLE"], "missing_outcome": 0, "usable": usable,
                           "false_positive_rate_all_right": c["FAIL"] / len(cohort) if label == "right" and cohort else None,
                           "false_positive_rate_usable_right": c["FAIL"] / usable if label == "right" and usable else None,
                           "status": "inferred"})
    write_csv(OUT / "phase2_counts_by_repo.csv", counts)
    fps = [r for r in rows if r["oracle"] == "resolved" and r["regression"] == "FAIL"]
    write_csv(OUT / "phase2_false_positives.csv", [{"instance_id": r["instance_id"], "repo": r["repo"], "source_run": r["source_run"],
               "v2_outcome": "FAIL", "posthoc_outcome": "resolved", "classification_status": "inferred"} for r in fps])
    return rows, counts, fps


def posthoc_projection():
    """Decode official lists/outcomes only, never gold test/source patches."""
    text = read(SNAPSHOT).decode()
    decoder = json.JSONDecoder()
    records = {}
    for key, pos in object_items(text, 0):
        if key != "tasks":
            continue
        pos += 1
        while True:
            pos = whitespace(text, pos)
            if text[pos] == "]":
                break
            if text[pos] == ",":
                pos = whitespace(text, pos + 1)
            record = {k: decoder.raw_decode(text, v)[0] for k, v in object_items(text, pos)
                      if k in {"instance_id", "source_run", "official_fail_to_pass", "oracle_record"}}
            records[record["instance_id"]] = record
            pos = skip_json(text, pos)
    return records


def canonical(value, repo):
    import re
    if "::" in value:
        if repo == "django/django":
            p, *parts = value.split("::")
            return p.removeprefix("tests/").removesuffix(".py").replace("/", ".") + "." + ".".join(parts)
        return value
    m = re.fullmatch(r"(test_\w+) \(([\w.]+)\)", value)
    if m:
        name, loc = m.groups()
        return loc if loc.endswith("." + name) else loc + "." + name
    return None


def match(tid, selected, repo, bare_mapping):
    key = canonical(tid, repo)
    method = "exact normalized identity"
    if key is None and tid in bare_mapping:
        key = canonical(bare_mapping[tid], repo)
        method = "stored exact post-hoc identity from ceiling evidence"
    if key is None:
        return None, [], "unresolved official identity; no fuzzy/docstring/renamed-test matching"
    hits = [s for s in selected if canonical(s, repo) == key]
    if not hits and "[" in key:
        hits = [s for s in selected if canonical(s, repo) == key.split("[", 1)[0]]
        if hits:
            method = "explicit parameterized family"
    return bool(hits), hits, method


def phase3(meta, study):
    posthoc = posthoc_projection()
    inventory = json.loads(read(OUT / "base_inventory.json"))
    sizes = list(csv.DictReader(io.StringIO(read(OUT / "selector_sizes.csv").decode())))
    ceiling = list(csv.DictReader(io.StringIO(read(ROOT / "reports/ceiling_check/failing_tests.csv").decode())))
    ceiling_labels = {r["instance_id"]: r for r in csv.DictReader(io.StringIO(read(ROOT / "reports/ceiling_check/patches.csv").decode()))}
    study_by_id = {r["instance_id"]: r for r in study}
    matches, metrics, opportunities = [], [], []
    for size in sizes:
        iid, selector = size["instance_id"], size["selector"]
        r = study_by_id[iid]
        payload = json.loads(read(OUT / "frozen_selections" / iid / (selector + ".json")))
        selected = payload["test_ids"]
        ph = posthoc[iid]
        if ph["source_run"] != r["source_run"] or payload["source_run"] != r["source_run"]:
            raise ValueError("post-hoc run mismatch")
        failed = ph["oracle_record"]["f2p_failure"] + ph["oracle_record"]["p2p_failure"]
        # Official F2P is a changed-behavior probe, not an oracle-free proof of code coverage.
        groups = {"official_failures": failed, "official_changed_behavior_F2P": ph["official_fail_to_pass"]}
        cr = [c for c in ceiling if c["instance_id"] == iid]
        bare = {c["official_id"]: c["archive_member"].removeprefix("testbed/") + "::" + c["ast_identity"] for c in cr}
        if iid in ceiling_labels and ceiling_labels[iid]["label"] == "existing-suite could expose":
            groups["existing_suite_opportunity_witnesses"] = [c["official_id"] for c in cr if c["existing_suite_witness"] == "True"]
        row = dict(size)
        row["posthoc_right_wrong"] = "right" if r["oracle"] == "resolved" else "wrong"
        for name, tests in groups.items():
            hits, unknown = 0, 0
            for tid in tests:
                retained, selected_ids, method = match(tid, selected, r["repo"], bare)
                hits += retained is True
                unknown += retained is None
                cc = next((c for c in cr if c["official_id"] == tid), {})
                matches.append({"instance_id": iid, "selector": selector, "posthoc_group": name, "official_id": tid,
                                "retained": retained, "matched_selected_ids": selected_ids, "method": method,
                                "base_relation_posthoc": cc.get("base_relation", "not classified in the prior 14-wrong-patch analysis"),
                                "meaning": "identity/family retention only; rewritten versions and added tests are not supplied to any selector",
                                "status": "inferred", "unknown": retained is None})
            row[name + "_total"] = len(tests)
            row[name + "_retained"] = hits
            row[name + "_unresolved"] = unknown
        metrics.append(row)
        if "existing_suite_opportunity_witnesses" in groups:
            opportunities.append({"instance_id": iid, "selector": selector, "witness_count": row["existing_suite_opportunity_witnesses_total"],
                 "retained_witness_count": row["existing_suite_opportunity_witnesses_retained"],
                 "unresolved_id_count": row["existing_suite_opportunity_witnesses_unresolved"],
                 "posthoc_label": "existing-suite could expose", "baseline_v2_outcome": r["regression"],
                 "status": "inferred", "execution_evidence": "incomplete; identity retention is not a pass/fail floor"})
    write_csv(OUT / "phase3_metrics.csv", metrics)
    write_csv(OUT / "phase3_posthoc_test_matches.csv", matches)
    write_csv(OUT / "phase3_opportunities.csv", opportunities)
    # Existing per-test durations are placeholders; report their availability rather than summing false zeros.
    durations = []
    for iid in inventory:
        run = study_by_id[iid]["source_run"]
        candidates = [ROOT / "runs" / run / "_baseline_cache" / (iid + ".baseline.json"),
                      ROOT / "reports/failure_analysis/_baseline_cache_copy" / (iid + ".baseline.json")]
        path = next((p for p in candidates if p.exists()), None)
        if path:
            base = json.loads(read(path))
            results = base.get("results", [])
            nonzero = sum(float(x.get("duration_s", 0)) > 0 for x in results)
            durations.append({"instance_id": iid, "source": str(path.relative_to(ROOT)), "stored_test_records": len(results),
                              "positive_per_test_durations": nonzero, "usable_for_estimation": nonzero > 0, "status": "confirmed"})
        else:
            durations.append({"instance_id": iid, "source": "missing same-run baseline cache", "stored_test_records": None,
                              "positive_per_test_durations": None, "usable_for_estimation": False, "status": "confirmed"})
    write_csv(OUT / "duration_availability.csv", durations)
    return metrics, matches, opportunities, durations


def report(diagnoses, params, study, counts, fps, metrics, matches, opportunities, manifest, manifest_hash, durations):
    na = list(csv.DictReader((OUT / "no_result_groups.csv").open()))
    cases = list(csv.DictReader((OUT / "case_cohort.csv").open()))
    meta = json.loads((OUT / "nonoracle_metadata.json").read_text())
    lines = ["# Next steps: stored V2 diagnosis, false positives, and frozen static selectors", "",
        "[confirmed] Analysis only. Outputs are confined to `reports/next_steps/`. No commits, "
        "network, agents, models, Docker, benchmark tests, test collection, or unit tests were run. "
        "The only executed programs were standard-library artifact analysis scripts; no repository "
        "runtime modules were imported and no graph was rebuilt or modified.", "",
        "[inferred] Conservative readings: a selected identity does not establish execution; "
        "aggregate counts cannot name the affected test. A gold class change cannot diagnose "
        "a V2 run that never used gold. NOT_AVAILABLE is a recorded V2 label, not a missing "
        "outcome. 'Usable' in Phase 2 means PASS or FAIL, irrespective of incomplete execution. "
        "An import closure here follows reverse *syntactic* module imports, and graph distance "
        "means at most three reverse call edges. Static retention never establishes a V2 result.", "",
        "[confirmed] Claim tags: confirmed facts come directly from stored evidence or source; "
        "inferred claims are arithmetic, static projections, or interpretations. Unknowns are "
        "stated as UNKNOWN and are not promoted into a cause or zero measurement.", "",
        "## Phase 1 — three V2 PASS misses", "",
        "[inferred] **All three primary causes are (f) UNKNOWN.** The exact-run V2 snapshots "
        "exist, but only selection unions and aggregate histograms survived. No stored "
        "per-test base/patched result pair establishes any proposed primary cause. Diagnosis "
        "uses only the V2 projection, base archives, code, and file-availability checks. It was "
        "written before this analysis program opened any post-hoc inputs; see "
        "`phase1_completed_before_posthoc.json`.", "",
        "| Case | Primary cause | Recorded selected / executed and histogram | Evidence |",
        "|---|---|---|---|"]
    for d in diagnoses:
        lines.append(f"| {d['instance_id']} | [inferred] (f) UNKNOWN | [confirmed] {d['n_selected']} / {d['n_executed']}; `{json.dumps(d['recorded_summary'])}` | `{d['evidence']}`; selection `{d['selected_evidence']}` |")
    lines += ["", "[confirmed] `phase1_record_availability.csv` records the absent exact-run "
        "`verification_record.full.json`, `verification_record.baseline.json`, run baseline "
        "cache, and failure-analysis copied baseline cache for each of these three. Their "
        "aggregate records are preserved in `reports/failure_analysis/extracted.json`, "
        "not lost entirely.", "",
        "[inferred] Exactly what is missing for each case: the raw base result IDs/statuses; "
        "raw patched result IDs/statuses; final per-test classifications; stdout/result logs "
        "for each pass; test-specific timeout/completion evidence; and a pin identifying "
        "the executor source revision used in that historical run. The current source can "
        "explain mechanisms, but cannot identify which mechanism affected a named test.", "",
        "| Proposed cause | Evidence and conclusion |", "|---|---|",
        "| (a) timed out / never ran, scored as pass | [confirmed] django-13297 has 6,890 TIMEOUTs and 1,265 PASS outcomes; the Pylint cases have 27/13 NOT_RUN. `regression.py:213` preserves NOT_RUN/TIMEOUT and `regression.py:314` emits patch PASS when some outcomes executed and none regressed. [inferred] Partial aggregate PASS is evidenced; no individual timeout was scored PASS. Which test was incomplete is UNKNOWN. |",
        "| (b) already failed at base | [confirmed] Each Pylint histogram has two PRE_EXISTING_FAIL outcomes; django-13297 has none. `regression.py:228` through `:237` implements base/patch comparison. [inferred] Cannot assign either Pylint count to a particular test; (b) is not established. |",
        "| (c) ID mismatch | [confirmed] The current pytest parser requires exact selected IDs (`container.py:359`, especially `:365`); Django maps labels (`container.py:386`). [inferred] A parameter-family accounting defect is evidenced below, but per-run output is absent, so it is not proven as any whole-patch primary cause. |",
        "| (d) gold-changed Django class | [confirmed] The V2 executor toggles candidate base/patched trees (`container.py:286`); the reducer looks up selected IDs (`regression.py:295`). [inferred] A post-hoc gold comparison cannot establish a runtime ID mismatch. No gold data was consulted for diagnosis. |",
        "| (e) OTHER | [inferred] No alternative cause is established by the stored per-case evidence. |",
        "| (f) UNKNOWN | [inferred] Primary for all three; the missing per-pass records above prevent a causal assignment. |", "",
        "[confirmed] **A source-level ID-accounting defect, separate from the unknown causes:** "
        "the snapshot selects unparameterized families. In the base archive for pylint-6528, "
        "`testbed/tests/lint/unittest_lint.py:804` decorates `test_multiprocessing` with "
        "`@pytest.mark.parametrize(\"jobs\", [1, 2])`; its definition is at line 805. The "
        "current `_parse_pytest` (`container.py:365`) discards an emitted `family[case]` ID "
        "when only `family` was selected. `container.py:315` then represents an unreported "
        "family as NOT_RUN. This conclusion requires no grader or gold data. The full "
        "oracle-free scan is in `phase1_parametrized_families.csv`.", "",
        "[inferred] Minimal **proposed, unapplied, untested** parser fix: map concrete cases "
        "back to an explicitly requested family and reuse the existing worst-status fold. "
        "This fixes discarded family output, not the policy for partial execution, and "
        "does not establish a causal explanation for these misses. It is not a full "
        "case-level differential design: a red base family can still absorb a new red "
        "case under family aggregation. Exact historical parser identity is UNKNOWN.", "",
        "```diff", SUGGESTED_DIFF.rstrip(), "```", "",
        "## Phase 2 — V2 false-positive rate", "",
        "[confirmed] All 83 nonempty headline patches have a V2 outcome in "
        "`docs/results_100.csv` (69 right, 14 wrong by post-hoc oracle label); none is "
        "missing. The 13 NOT_AVAILABLE outcomes remain in the table. Detailed records "
        "are unavailable for many tasks, but their headline outcomes are present, so "
        "the missing-outcome stop condition does not apply.", "",
        "| Post-hoc patch label | PASS | FAIL | NOT_AVAILABLE | Total |", "|---|---:|---:|---:|---:|"]
    for c in counts:
        if c["repo"] == "ALL":
            lines.append(f"| [inferred] {c['posthoc_label']} | {c['PASS']} | {c['FAIL']} | {c['NOT_AVAILABLE']} | {c['total']} |")
    lines += ["", "[inferred] **False-positive rate over all right patches: 5/69 = 7.25%.** "
        "**Over right patches with usable V2: 5/(53+5) = 5/58 = 8.62%.** "
        "Usable excludes 11 NOT_AVAILABLE right patches, not partially executed PASS "
        "patches. False positives are exactly right patches with V2 FAIL, not all final "
        "FLAG/REJECT decisions.", "",
        "| Repository | Right PASS / FAIL / NA | Wrong PASS / FAIL / NA |", "|---|---:|---:|"]
    for repo in sorted({r["repo"] for r in study}):
        cc = {c["posthoc_label"]: c for c in counts if c["repo"] == repo}
        def triplet(label):
            return " / ".join(str(cc[label][k]) for k in ("PASS", "FAIL", "NOT_AVAILABLE"))
        lines.append(f"| [inferred] {repo} | {triplet('right')} | {triplet('wrong')} |")
    lines += ["", "[inferred] False-positive IDs: " + "; ".join("`" + r["instance_id"] + "`" for r in fps) + ".",
        "[confirmed] Raw outcomes, repository denominators/rates, and individual false "
        "positives are in `phase2_outcomes.csv`, `phase2_counts_by_repo.csv`, and "
        "`phase2_false_positives.csv`. Oracle outcome is used only as a post-hoc label.", "",
        "## Phase 3 — static side experiment; no execution", "",
        f"[confirmed] **Step A preceded Step B.** All 36 outputs for nine cases were "
        f"written to `frozen_selections/` and hashed in its manifest at "
        f"`{manifest['frozen_utc']}`. Manifest SHA-256: `{manifest_hash}`. "
        "The freeze program lexically skips all unapproved mixed-snapshot values, "
        "including labels, gold patches, official lists and grader fields; the CSV "
        "projection accesses whitelisted non-oracle columns. It uses hash-verified "
        "candidate patch exports, base archives and existing graphs. Frozen files "
        "are verified before and after the post-hoc stage and are never regenerated "
        "in response to retention results.", "",
        "[confirmed] The conversation already contained historical oracle observations; "
        "no claim of human/model blinding is made. Step A's program is isolated from "
        "those data: its selectors have no oracle field input. The fixed supplemental "
        "four-opportunity cohort comes from the user's requested preceding analysis; "
        "its labels are not queried to construct or tune any selector.", "",
        "[inferred] Cohort: six stored selections of at least 1,000 tests; zero "
        "no-result cases established as selection-related; and the requested four "
        "opportunities reported separately (one overlaps the six, giving nine unique "
        "cases). Unexplained NOT_AVAILABLE outcomes are not reclassified as selection "
        "failures just because a static selector can return tests.", "",
        "| Stored no-result group | Cases | Included as selection-related |", "|---|---:|---| "]
    ng = Counter(r["group"] for r in na)
    for group in ("selection-related", "timeout", "runner", "collection", "unknown"):
        lines.append(f"| [inferred] {group} | {ng[group]} | {'yes' if group == 'selection-related' else 'no'} |")
    lines += ["", "[confirmed] Timeout: `astropy__astropy-13977` (already in the large "
        "cohort, not promoted to selection-related). Runner: `sympy__sympy-17318` "
        "(pytest absent). [inferred] UNKNOWN: " + ", ".join("`" + r["instance_id"] + "`" for r in na if r["group"] == "unknown") + ". "
        "See `no_result_groups.csv` for each record and evidence.", "",
        "[inferred] **Frozen selector definitions:**", "",
        "- **I1:** base test modules directly importing a candidate-changed production module.",
        "- **I2:** the reverse syntactic import closure through one or two module hops. All statically declared imports, including conditional/local imports, count. `from pkg import name` links exact `pkg` and an exact `pkg.name` submodule when present; `from pkg import *` links only `pkg`. Relative imports use the actual package. Source roots `src/` and `lib/` are stripped; Django has its known `tests/` import-root alias. No dynamic imports, fuzzy tails, automatic parent-package expansion or re-export inference.",
        "- **G3-R / G3-A:** existing amended graph, reverse call distance 1–3, using the same uniquely resolved candidate-changed symbol seeds. G3-R permits resolved edges; G3-A also permits existing ambiguous edges. Ambiguous seeds stay excluded in both, so the comparison changes edge status only. No class expansion, lexical fallback, ranking, budgets, or graph repair. Tests must exist in the base AST inventory.", "",
        "[confirmed] Graph paths/hashes and candidate/archive hashes are in "
        "`step_a_inputs.json`; cohort and graph status in `case_cohort.csv`. "
        "[inferred] Both Pylint supplemental graphs are partial with missing portions "
        "(original graph reports resource-limited edge resolution); django-14631 is "
        "also partial. No graph output is treated as complete where its artifact says "
        "partial. Import AST parse failures are recorded separately in "
        "`base_inventory.json`. These static inventories are not proof of runtime "
        "collectability, inherited/dynamically generated test completeness, or coverage.", "",
        "[inferred] Cells below are **test-family count / module count**; **THOUSANDS** "
        "marks at least 1,000 static tests. `L` = six large cases; `S` = supplemental "
        "opportunity-only cases. Counts are derived from the frozen sets.", "",
        "| Case | Cohort | I1 | I2 | G3-R | G3-A |", "|---|---|---:|---:|---:|---:|"]
    selectors = manifest["selectors"]
    by_key = {(r["instance_id"], r["selector"]): r for r in metrics}
    for c in cases:
        cells = []
        for selector in selectors:
            m = by_key[c["instance_id"], selector]
            cells.append(f"{m['test_count']} / {m['module_count']}" + (" **THOUSANDS**" if int(m["test_count"]) >= 1000 else ""))
        lines.append(f"| {c['instance_id']} | {'L' if c['large_selection']=='True' else 'S'} | " + " | ".join(cells) + " |")
    lines += ["", "[inferred] Runtime: exact subset runtimes are UNKNOWN. The available "
        "per-test caches for three large cases contain only zero duration placeholders "
        "(`duration_availability.csv`); no measured per-test timing can support a "
        "subset estimate. `selector_sizes.csv` and `phase3_metrics.csv` include an "
        "explicitly low-confidence proportional estimate `stored V2 duration × new "
        "set size / stored selected size` for seven uncensored cases. It includes "
        "setup/cache and assumes equal costs; it is a size-scaled proxy, not measured "
        "runtime or a promised speedup. Astropy-13977 and django-13297 are timeout "
        "censored and receive no estimate. An empty set's arithmetic zero is not "
        "a measured startup time.", "",
        "| Case | I1 proportional seconds | I2 proportional seconds | G3-R proportional seconds | G3-A proportional seconds |",
        "|---|---:|---:|---:|---:|"]
    for c in cases:
        vals = []
        for selector in selectors:
            x = by_key[c["instance_id"], selector]["proportional_runtime_proxy_s"]
            vals.append(f"{float(x):.1f}" if x not in (None, "") else "UNKNOWN (censored)")
        lines.append(f"| [inferred] {c['instance_id']} | " + " | ".join(vals) + " |")
    lines += ["", "[confirmed] **Step B only:** official failures and official F2P "
        "lists were opened after the manifest existed. No gold patch or gold test "
        "source is read by either new script. The earlier ceiling CSV supplies "
        "post-hoc base-relation labels, never selector inputs. [inferred] Exact "
        "Django unittest/node normalization and explicit parameter-family matching "
        "are used; docstring-only and renamed identities without a stored mapping "
        "stay UNKNOWN. The official F2P list is reported as a changed-behavior "
        "probe, not as a runtime changed-code coverage oracle.", "",
        "| Six large cases | Compared probes | I1 retained | I2 retained | G3-R retained | G3-A retained |",
        "|---|---|---:|---:|---:|---:|"]
    for c in cases:
        if c["large_selection"] != "True":
            continue
        iid = c["instance_id"]
        kind = "official_changed_behavior_F2P" if by_key[iid, selectors[0]]["posthoc_right_wrong"] == "right" else "official_failures"
        vals = []
        for selector in selectors:
            m = by_key[iid, selector]
            vals.append(f"{m[kind+'_retained']}/{m[kind+'_total']}" + (f"; {m[kind+'_unresolved']} UNKNOWN" if m[kind+'_unresolved'] else ""))
        lines.append(f"| {iid} | {'official F2P' if kind.endswith('F2P') else 'official failures'} | " + " | ".join(vals) + " |")
    lines += ["", "[inferred] **Four previously labeled existing-suite opportunities, "
        "separate from the six-case experiment:** cells count retained failing P2P "
        "identities/families. These are descriptive post-hoc opportunities with "
        "incomplete execution evidence, **not a pass/fail floor or selector acceptance "
        "criterion**. Pylint-6528's four official cases include two parameter cases "
        "served by one selected family.", "",
        "| Opportunity | Baseline V2 | I1 | I2 | G3-R | G3-A |", "|---|---|---:|---:|---:|---:|"]
    for iid in sorted({o["instance_id"] for o in opportunities}):
        oo = {o["selector"]: o for o in opportunities if o["instance_id"] == iid}
        cells = [f"{oo[s]['retained_witness_count']}/{oo[s]['witness_count']}" for s in selectors]
        lines.append(f"| [inferred] {iid} | [confirmed] {oo[selectors[0]]['baseline_v2_outcome']} | " + " | ".join(cells) + " |")
    lines += ["", "[inferred] Retaining a rewritten F2P name does not supply its gold "
        "body; new tests cannot be present in a base-only selection. Django-13297's "
        "unchanged P2P method has the previously recorded gold-changed class context; "
        "that is a post-hoc interpretation caveat, not Phase-1 causal evidence. For "
        "all four opportunities the stored per-test V2 execution status remains "
        "UNKNOWN. Raw identities, methods, unresolved IDs and base-relation labels "
        "are in `phase3_posthoc_test_matches.csv`; aggregate retention is in "
        "`phase3_metrics.csv` and `phase3_opportunities.csv`.", "",
        "[confirmed] Stopped after Phase 3. No coverage pilot, graph engineering, "
        "testmon work, production edits, selector deployment, or test execution was started.", "",
        "## Reproduction and audit files", "",
        "[confirmed] Executed artifact-analysis commands (neither is a test command):", "", "```bash",
        "python3 -B reports/next_steps/freeze.py", "python3 -B reports/next_steps/analyze.py", "```", "",
        "[confirmed] `freeze.py` refuses to overwrite an existing manifest. "
        "`step_b_gate.json` records the manifest hash and verification; "
        "`completion.json` records frozen-file verification after analysis. "
        "`analysis_inputs.json` records the later input hashes. Do not feed any "
        "post-hoc labels, comparisons, or proposed diff back into a run, selector "
        "or policy.", ""]
    return "\n".join(lines)


def verify_frozen(manifest):
    for relative, expected in manifest["files_sha256"].items():
        if sha((OUT / relative).read_bytes()) != expected:
            raise ValueError("frozen file changed: " + relative)


def main():
    path = OUT / "frozen_selections/manifest.json"
    raw = read(path)
    manifest = json.loads(raw)
    verify_frozen(manifest)
    digest = sha(raw)
    dump(OUT / "step_b_gate.json", {"step_b_program_started_utc": stamp(), "manifest_sha256": digest,
         "step_a_frozen_utc": manifest["frozen_utc"], "frozen_files_verified_before_program_posthoc_access": True,
         "historical_chat_knowledge": "Prior task already contained labels; new Step A process never accessed them. No claim of cognitive blinding."})
    diagnoses, params = phase1()
    study, counts, fps = phase2()
    meta = json.loads(read(OUT / "nonoracle_metadata.json"))
    metrics, matches, opportunities, durations = phase3(meta, study)
    (OUT / "report.md").write_text(report(diagnoses, params, study, counts, fps, metrics, matches, opportunities, manifest, digest, durations))
    verify_frozen(manifest)
    if sha(path.read_bytes()) != digest:
        raise ValueError("manifest changed")
    read(Path(__file__).resolve())
    dump(OUT / "analysis_inputs.json", INPUTS)
    dump(OUT / "completion.json", {"completed_utc": stamp(), "frozen_files_unchanged": True,
         "manifest_sha256": digest, "phase1_primary_causes": {d["instance_id"]: d["primary_cause"] for d in diagnoses},
         "phase2_missing_outcomes": 0, "phase3_cases": len(manifest["cases"]), "phase3_selector_outputs": len(metrics),
         "thousands_outputs": [{"instance_id": m["instance_id"], "selector": m["selector"], "test_count": m["test_count"]} for m in metrics if int(m["test_count"]) >= 1000],
         "benchmarks_executed": False, "tests_executed": False, "models_or_agents": False})
    print(json.dumps({"diagnoses": [d["primary_cause"] for d in diagnoses], "all_counts": [c for c in counts if c["repo"] == "ALL"],
                      "selector_outputs": len(metrics), "retention_rows": len(matches), "frozen_manifest_sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
