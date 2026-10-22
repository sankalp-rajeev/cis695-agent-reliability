"""POST-HOC ANALYSIS ONLY: read frozen selections, then compare oracle IDs.

Never imports/calls select_tests, any executor, a model, or dataset downloader.
Nothing here may feed a run, policy, manifest, config, or verifier decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shlex
import sys
from collections import Counter, defaultdict
from pathlib import Path

import diagnostic
from diagnostic import collect, distribution, encoded, put
from reliability.agent.freeze import digest_bytes
from reliability.benchmark.loader import oracle_record_from_row
from reliability.verifier.selection import django_label

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NOTICE = "POST-HOC ANALYSIS ONLY. Never feed these comparisons into selection or decisions."
SAMPLE = ("django__django-13212", "django__django-13297", "pytest-dev__pytest-7432")
POSTHOC_FIELDS = (
    "oracle_outcome_posthoc", "local_oracle_outcome_posthoc", "pytest_7432_note_posthoc",
    "official_f2p_count_posthoc", "official_p2p_count_posthoc",
    "f2p_selected_count_posthoc", "p2p_selected_count_posthoc",
    "f2p_selection_hit_posthoc", "p2p_selection_hit_posthoc",
    "unmatched_f2p_ids_posthoc", "unmatched_p2p_ids_posthoc",
    "failed_f2p_ids_posthoc", "relevant_test_categories_posthoc",
)
ADDED = "relevant test did not exist at base (added or rewritten by gold test patch)"
NO_F2P = "not applicable: oracle records no failed FAIL_TO_PASS tests"
UNKNOWN = "selected test execution/classification missing"


class Inputs:
    def __init__(self):
        self.files: dict[str, str] = {}

    def read(self, path: Path) -> bytes:
        data = path.read_bytes()
        self.files[str(path.resolve())] = hashlib.sha256(data).hexdigest()
        return data

    def json(self, path: Path):
        return json.loads(self.read(path))


def population(text: str) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if len({r["instance_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate study IDs")
    headline = [r for r in rows if r["stratum"] == "headline"]
    nonempty = [r for r in headline if r["oracle"] != "empty_patch"]
    if len(headline) != 93 or len(nonempty) != 83:
        raise ValueError("expected committed 93-task headline / 83 non-empty population")
    return nonempty


def identity(row: dict) -> dict:
    return {"instance_id": row["instance_id"], "repo": row["repo"],
            "source_run": row["source_run"], "verifier_decision": row["verifier_decision"],
            "v2_outcome": row["regression"]}


def load_gold_arrow(path: Path | None, inputs: Inputs) -> dict:
    """Read an existing Arrow cache directly: no datasets locks or network."""
    if path is None:
        return {}
    import pyarrow.ipc as ipc

    table = ipc.open_stream(io.BytesIO(inputs.read(path))).read_all()
    if table.num_rows != 500:
        raise ValueError("cached benchmark must contain exactly 500 instances")
    result = {}
    for raw in table.to_pylist():
        record = oracle_record_from_row(raw)  # existing schema/normalization
        result[record.instance_id] = {
            "f2p": list(record.fail_to_pass), "p2p": list(record.pass_to_pass),
            "test_patch": record.test_patch, "source": str(path),
        }
    return result


def canonical(test_id: str, repo: str) -> tuple[str | None, str]:
    """Exact identities only; no similarity, substring, or bare-tail fallback."""
    value = test_id.removeprefix("./")
    if "::" in value:
        if repo == "django/django":
            return django_label(value), "django_node_to_dotted_label"
        return value, "exact_node_id"
    match = re.fullmatch(r"(test_\w+) \(([\w.]+)\)", value)
    if match:
        name, location = match.groups()
        return (location if location.rsplit(".", 1)[-1] == name
                else location + "." + name), "django_unittest_label"
    if re.fullmatch(r"[\w.]+\.test_\w+", value):
        return value, "exact_dotted_label"
    if re.fullmatch(r"test_\w+(?:\[.*\])?", value):
        return None, "unqualified_name_needs_gold_identity"
    return None, "unresolved_docstring_or_non_test_id"


def family(value: str) -> str:
    return value.split("[", 1)[0]


def gold_changes(test_patch: str, repo: str) -> dict[str, str]:
    """Index exactly located test functions touched by the stored gold diff.

    Existing unified-diff representation is reused. Hunk lines are walked in
    order using unidiff; class/function scope is tracked. A function hunk header
    may identify a test, but git's class header is not reliable enclosing scope
    (it can name an earlier nested class). Unknown class scope stays unresolved.
    'Added or rewritten' describes the official test *version*, not necessarily
    absence of a pre-existing function with that name.
    """
    from unidiff import PatchSet
    from reliability.verifier.patch import parse_patch

    if not test_patch.strip():
        return {}
    parsed = parse_patch(test_patch)
    sections = {f.path: [h.section for h in f.hunks] for f in parsed}
    result: dict[str, str] = {}
    for file in PatchSet(test_patch):
        path = file.path
        for index, hunk in enumerate(file):
            section = sections.get(path, [""] * (index + 1))[index]
            classes: list[tuple[int, str]] = []
            current: tuple[int, str, bool] | None = None
            function_seed = re.match(r"(?:async\s+)?def\s+(test_\w+)", section)
            if function_seed:
                current = (-1, function_seed[1], bool(re.search(r"\(\s*(self|cls)\b", section)))
            for line in hunk:
                text = line.value.rstrip("\n")
                stripped = text.lstrip()
                indent = len(text) - len(stripped)
                declaration = re.match(r"(class|def)\s+(\w+)", stripped)
                if declaration:
                    while classes and classes[-1][0] >= indent:
                        classes.pop()
                    if declaration[1] == "class":
                        classes.append((indent, declaration[2]))
                        current = None
                    else:
                        current = ((indent, declaration[2], indent > 0 and not classes)
                                   if declaration[2].startswith("test_") else None)
                elif stripped and not stripped.startswith(("#", "@")) and current:
                    if current[0] >= 0 and indent <= current[0]:
                        current = None
                if (current and (line.is_added or line.is_removed)
                        and stripped and not stripped.startswith("#")):
                    name = current[1]
                    members = [c[1] for c in classes] + [name]
                    node = path + "::" + "::".join(members)
                    key, _ = canonical(node, repo)
                    result[key] = "scope_unresolved" if current[2] else "added_or_rewritten"
    return result


def gold_relation(key: str | None, changed: dict[str, str], repo: str) -> str | None:
    """Do not turn an incomplete gold-diff class scope into a selection failure."""
    if key is None:
        return None
    key = family(key)
    if changed.get(key) == "added_or_rewritten":
        return "added_or_rewritten"
    for partial, status in changed.items():
        if status != "scope_unresolved":
            continue
        if repo == "django/django":
            module, _, method = partial.rpartition(".")
            if key.startswith(module + ".") and key.rsplit(".", 1)[-1] == method:
                return "gold class scope unresolved"
        elif "::" in key and "::" in partial:
            if key.split("::")[0] == partial.split("::")[0] and key.rsplit("::", 1)[-1] == partial.rsplit("::", 1)[-1]:
                return "gold class scope unresolved"
    return None


def match_test(test_id: str, selected: list[str], repo: str,
               changed: dict[str, str]) -> dict:
    key, normalization = canonical(test_id, repo)
    if key is None and normalization == "unqualified_name_needs_gold_identity":
        # An exact function name may be resolved only with one concrete identity
        # in the stored gold diff; never use uniqueness in a partial selection.
        candidates = [k for k in changed if changed[k] == "added_or_rewritten"
                      and k.rsplit("::", 1)[-1] == family(test_id)]
        if len(candidates) == 1:
            key = candidates[0] + test_id[len(family(test_id)):]
            normalization = "unique_exact_name_in_gold_diff"
    result = {"official_id": test_id, "canonical_id": key,
              "normalization": normalization, "selected_ids": [],
              "match_method": "unmatched", "reason": ""}
    if key is None:
        result["reason"] = normalization
        return result
    selected_keys = [(s, canonical(s, repo)[0]) for s in selected]
    exact = [s for s, k in selected_keys if k == key]
    if exact:
        result.update(selected_ids=exact, match_method="exact_normalized_identity")
    elif "[" in key:
        # select_tests.node_ids emits function families, not parametrized cases.
        hits = [s for s, k in selected_keys if k == family(key)]
        if hits:
            result.update(selected_ids=hits, match_method="explicit_parameterized_family")
    if not result["selected_ids"]:
        result["reason"] = "no selected exact identity or unparameterized family"
    return result


def relevant_category(match: dict, changed: dict[str, str], *,
                      per_test: dict | None, aggregate: dict | None,
                      selected_known: bool, repo: str = "") -> tuple[str, str]:
    key = match["canonical_id"]
    relation = gold_relation(key, changed, repo)
    if relation == "added_or_rewritten":
        return ADDED, "inferred"
    if relation == "gold class scope unresolved":
        return "gold class scope unresolved: not attributed to selection failure", "missing"
    if not selected_known:
        return "missing stored selection", "missing"
    if key is None:
        return "unmatched official ID: cannot classify", "missing"
    if not match["selected_ids"]:
        return "never selected the relevant test", "inferred"
    outcomes = [per_test.get(s) for s in match["selected_ids"]] if per_test else []
    known = set(outcomes) - {None}
    categories = {
        "TIMEOUT": "selected but timed out before execution",
        "PRE_EXISTING_FAIL": "executed and classified as pre-existing failure",
        "REGRESSION": "correctly detected a regression",
        "PASS": "executed and missed behavior for another reason",
        "NEWLY_PASSING": "executed and missed behavior for another reason",
        "FLAKY": "executed and missed behavior for another reason",
    }
    if len(known) == 1 and len(outcomes) == len([o for o in outcomes if o is not None]):
        outcome = next(iter(known))
        if outcome in categories:
            return categories[outcome], "recorded"
    # The only safe attribution from aggregate counts is universal timeout.
    if aggregate and aggregate.get("n_selected", 0) > 0:
        if aggregate.get("TIMEOUT") == aggregate["n_selected"]:
            return "selected but timed out before execution", "inferred"
    return UNKNOWN, "missing"


def build(study: list[dict], snapshots: dict, gold_cache: dict, inputs: Inputs):
    rows, match_rows, wrong_rows = [], [], []
    for committed in study:
        iid, run = committed["instance_id"], committed["source_run"]
        task_dir = REPO / "runs" / run / "tasks" / iid
        snapshot = snapshots.get((iid, run))
        evidence, patch_text = None, None
        source = "docs/results_100.csv"
        patch_source = "missing frozen candidate diff"
        kind, note = "committed_table_only", "detailed study verification record unavailable"
        if snapshot:
            if snapshot["csv_row"] != committed:
                raise ValueError(f"snapshot belongs to a different committed study row: {iid}")
            original = snapshot["signals"]
            evidence = {key: original[key] for key in (
                "decision", "regression", "selected_tests", "selection_convention")}
            patch_text = snapshot.get("agent_patch")
            source = "reports/failure_analysis/extracted.json#" + iid
            patch_source = source + ":agent_patch"
            kind, note = "study_snapshot", "stored study extraction; no analysis rerun"
        elif (task_dir / "verification_record.full.json").is_file():
            path = task_dir / "verification_record.full.json"
            inputs.read(path)
            evidence = diagnostic.project_local(path)
            source = str(path.relative_to(REPO))
            patch_path = task_dir / "patch.diff"
            if patch_path.is_file():
                raw = inputs.read(patch_path)
                if digest_bytes(raw) != evidence["patch_sha256"]:
                    raise ValueError(f"local patch hash mismatch: {iid}")
                patch_text = raw.decode("utf-8")
                patch_source = str(patch_path.relative_to(REPO))
            kind = "local_record_final_identity_unverified"
            note = ("local record agrees on recorded decision/V2; final-run identity cannot "
                    "be established from committed aggregate CSV")
        row = collect(identity(committed), evidence, patch_text, source=source,
                      patch_source=patch_source, artifact_kind=kind, note=note)
        for field in POSTHOC_FIELDS:
            put(row, field, None, source="POST-HOC: not stored/available")
        put(row, "oracle_outcome_posthoc", committed["oracle"], source="docs/results_100.csv")

        local_oracle = None
        if (task_dir / "oracle_record.json").is_file():
            local_oracle = inputs.json(task_dir / "oracle_record.json")
            put(row, "local_oracle_outcome_posthoc", local_oracle["outcome"],
                source=str((task_dir / "oracle_record.json").relative_to(REPO)))
        if iid == "pytest-dev__pytest-7432":
            local_value = local_oracle["outcome"] if local_oracle else "missing"
            put(row, "pytest_7432_note_posthoc",
                f"committed={committed['oracle']}; local={local_value}; committed classification "
                "retained. Local harness says applied cleanly; test output records segfault/139.",
                "inferred", "docs/results_100.csv; local oracle_record.json and harness logs")

        gold = gold_cache.get(iid)
        if snapshot:
            gold = {"f2p": snapshot["official_fail_to_pass"],
                    "p2p": snapshot["official_pass_to_pass"],
                    "test_patch": snapshot["gold_test_patch"], "source": source}
            cached = gold_cache.get(iid)
            if cached and any(gold[k] != cached[k] for k in ("f2p", "p2p", "test_patch")):
                raise ValueError(f"cached gold differs from study snapshot: {iid}")
        changed = gold_changes(gold["test_patch"], committed["repo"]) if gold else {}
        selected = row["selected_test_ids"]
        matches = {}
        if gold:
            for group in ("f2p", "p2p"):
                put(row, f"official_{group}_count_posthoc", len(gold[group]), "inferred", gold["source"])
                if selected is None:
                    continue
                matches[group] = [match_test(t, selected, committed["repo"], changed)
                                  for t in gold[group]]
                hits = sum(bool(m["selected_ids"]) for m in matches[group])
                put(row, f"{group}_selected_count_posthoc", hits, "inferred", gold["source"])
                # A failed match is not evidence of non-selection when an ID is
                # unresolvable (notably Django's docstring-style test names).
                resolvable = all(m["canonical_id"] is not None for m in matches[group])
                hit = True if hits else (False if resolvable else None)
                put(row, f"{group}_selection_hit_posthoc", hit, "inferred", gold["source"])
                put(row, f"unmatched_{group}_ids_posthoc",
                    [m["official_id"] for m in matches[group] if not m["selected_ids"]],
                    "inferred", gold["source"])
                for match in matches[group]:
                    match_rows.append({"notice": NOTICE, "instance_id": iid,
                                       "source_run": run, "group": group.upper(),
                                       "gold_source": gold["source"], **match})
        if committed["oracle"] == "unresolved":
            # Relevant means FAILED F2P only, not all oracle failures.
            oracle = snapshot.get("oracle_record") if snapshot else None
            if oracle is not None:
                failed = oracle.get("f2p_failure")
                failure_source = source + ":oracle_record.f2p_failure"
            elif local_oracle and local_oracle["outcome"] == committed["oracle"]:
                failed = local_oracle.get("fail_to_pass", {}).get("failure")
                failure_source = str(task_dir.relative_to(REPO)) + "/oracle_record.json"
            else:
                failed, failure_source = None, "missing matching study oracle record"
            put(row, "failed_f2p_ids_posthoc", failed, source=failure_source)
            details = []
            if failed == []:
                details = [{"official_id": "", "category": NO_F2P, "status": "recorded",
                            "note": "Wrong under oracle because of PASS_TO_PASS failures; "
                                    "outside the requested relevant-test definition."}]
            elif failed is not None:
                for test in failed:
                    match = match_test(test, selected or [], committed["repo"], changed)
                    aggregate = {"n_selected": row["total_selected_tests"],
                                 "TIMEOUT": row["number_timed_out"]}
                    category, status = relevant_category(
                        match, changed, per_test=None, aggregate=aggregate,
                        selected_known=selected is not None, repo=committed["repo"])
                    details.append({**match, "category": category, "status": status,
                                    "gold_version_relation": gold_relation(match["canonical_id"], changed, committed["repo"]),
                                    "note": "Per-test V2 outcomes are not stored."})
            else:
                details = [{"official_id": "", "category": "missing failed F2P list",
                            "status": "missing", "note": failure_source}]
            put(row, "relevant_test_categories_posthoc", details, "inferred", failure_source)
            for detail in details:
                wrong_rows.append({"notice": NOTICE, "instance_id": iid, "source_run": run,
                                   "verifier_decision": committed["verifier_decision"],
                                   "v2_outcome": committed["regression"], **detail})
        rows.append(row)
    return rows, match_rows, wrong_rows


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    # All outputs are restricted to this diagnostic directory.
    if path.resolve().parent != OUT:
        raise ValueError("outputs must remain under reports/v2_diagnostic/")
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: encoded(row.get(key)) for key in fields} for row in rows)


def number(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def overlap_summary(rows: list[dict], group: str) -> dict:
    applicable = [r for r in rows if r[f"official_{group}_count_posthoc"]
                  and r["selected_test_ids"] is not None]
    positive = sum(r[f"{group}_selection_hit_posthoc"] is True for r in applicable)
    negative = sum(r[f"{group}_selection_hit_posthoc"] is False for r in applicable)
    return {"applicable": len(applicable), "positive": positive, "no_exact_hit": negative,
            "unresolved": len(applicable) - positive - negative,
            "missing": sum(r["selected_test_ids"] is None
                           or r[f"official_{group}_count_posthoc"] is None for r in rows)}


def report(rows: list[dict], wrong: list[dict], command: str, prefix: str) -> str:
    lines = ["# Current V2 stored-artifact diagnostic", "", NOTICE, "",
             "No selection, verification, repair, oracle evaluation, Docker, or network was run.",
             "", f"Reproduce from repository root:\n\n```bash\n{command}\n```", "",
             "## Population and evidence", "",
             f"{len(rows)} non-empty headline patches. Committed oracle classifications: "
             + str(dict(Counter(r['oracle_outcome_posthoc'] for r in rows))) + ".",
             "Committed decisions and V2 outcomes always come from docs/results_100.csv.",
             "Artifact origins: " + str(dict(Counter(r['artifact_kind'] for r in rows))) + ".",
             "Study snapshots take precedence over local records. Local-only records are "
             "reported separately as final identity unverified; matching aggregate labels do "
             "not prove they are the final study run. Only the study-snapshot cohort supplies "
             "confirmed detailed main-study evidence. Other local evidence is exploratory. "
             "No pilot or alternate-run substitution.",
             "", "## V2 baseline (all included committed rows)", "",
             "| V2 | Tasks |", "|---|---:|"]
    lines += [f"| {key} | {value} |" for key, value in sorted(Counter(
        r["v2_outcome"] for r in rows).items())]
    lines += ["", "## Available-artifact distributions", "",
              "These are availability-limited, failure-enriched subsets, not unbiased "
              "83-task estimates. Quantiles use linear interpolation. Averages of task ratios "
              "are distinct from pooled execution coverage. Zero selections give undefined ratios.",
              "Counts follow existing Outcome.executed: ERROR and PRE_EXISTING_FAIL count as "
              "executed, TIMEOUT and NOT_RUN do not. Runtime is stored V2 duration, which may "
              "include baseline/cache work and flake reruns.", "",
              "| Cohort | Metric | Available / tasks | Missing | Min | P25 | Median | P75 | P90 | Max | Mean |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for cohort, group in (("study snapshots only", [
            r for r in rows if r["artifact_kind"] == "study_snapshot"]),
            ("all available (exploratory)", rows)):
        for field in ("total_selected_tests", "number_executed", "timeout_fraction",
                      "execution_coverage", "v2_runtime_s"):
            stats = distribution([r[field] for r in group])
            values = [number(stats.get(k)) for k in ("min", "p25", "median", "p75", "p90", "max", "mean")]
            lines.append(f"| {cohort} | {field} | {stats['n']}/{len(group)} | "
                         f"{stats['missing']} | " + " | ".join(values) + " |")
    for cohort, group in (("Confirmed study snapshots", [
            r for r in rows if r["artifact_kind"] == "study_snapshot"]),
            ("All available (exploratory)", rows)):
        pairs = [r for r in group if r["total_selected_tests"] and r["number_executed"] is not None]
        selected_sum = sum(r["total_selected_tests"] for r in pairs)
        executed_sum = sum(r["number_executed"] for r in pairs)
        lines += ["", f"{cohort} paired totals: {selected_sum} selected, {executed_sum} executed; "
                  f"pooled coverage {number(executed_sum / selected_sum if selected_sum else None)}."]
    lines += ["", "## Pathological cases", "",
              "Descriptive thresholds: selected ≥1,000 or TIMEOUT/selected >0.5. "
              "These labels do not alter selection or policy.", "",
              "| Instance | Origin | Selected | Executed | TIMEOUT | Timeout fraction | Coverage |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        if ((row["total_selected_tests"] or 0) >= 1000 or (row["timeout_fraction"] or 0) > .5):
            lines.append("| " + " | ".join(number(row[k]) for k in (
                "instance_id", "artifact_kind", "total_selected_tests", "number_executed",
                "number_timed_out", "timeout_fraction", "execution_coverage")) + " |")
    lines += ["", "## By repository", "",
              "Counts cover the committed population; exploratory averages cover available "
              "artifacts (including unverified local-only records) only. "
              "Missing evidence is never counted as zero.", "",
              "| Repository | Tasks | PASS / FAIL / NA | Detailed records | Mean selected | Mean executed | Mean timeout fraction | Mean coverage | Mean V2 seconds |",
              "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    repos = defaultdict(list)
    for row in rows:
        repos[row["repo"]].append(row)
    for repo, group in sorted(repos.items()):
        outcomes = Counter(r["v2_outcome"] for r in group)
        means = [number(distribution([r[k] for r in group]).get("mean")) for k in (
            "total_selected_tests", "number_executed", "timeout_fraction", "execution_coverage", "v2_runtime_s")]
        available = sum(r["total_selected_tests"] is not None for r in group)
        lines.append(f"| {repo} | {len(group)} | {outcomes['PASS']} / {outcomes['FAIL']} / "
                     f"{outcomes['NOT_AVAILABLE']} | {available}/{len(group)} | " + " | ".join(means) + " |")
    lines += ["", "## POST-HOC ORACLE-ONLY: selection overlap", "", NOTICE, "",
              "Matching: exact node identity; deterministic Django node-to-dotted and unittest "
              "label normalization (including redundant method suffix); explicit parameterized "
              "case → selected function-family matching. Bare names resolve only to a unique "
              "exact function identity in the stored gold diff. No fuzzy, substring, or generic "
              "tail matching. Django docstring-style names remain unresolved, not guessed. "
              "A hit can identify the old function even when the official body was rewritten.",
              "", "| Cohort | Official group | Applicable nonempty lists + stored selection | Positive tasks | No exact-ID hit | Unresolved tasks | Missing selection/list |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for cohort, cohort_rows in (("confirmed study snapshots", [
            r for r in rows if r["artifact_kind"] == "study_snapshot"]),
            ("all available (exploratory)", rows)):
        for group in ("f2p", "p2p"):
            stats = overlap_summary(cohort_rows, group)
            lines.append(f"| {cohort} | {group.upper()} | {stats['applicable']} | "
                         f"{stats['positive']} | {stats['no_exact_hit']} | "
                         f"{stats['unresolved']} | {stats['missing']} |")
    lines += ["", "Unmatched official IDs and their matching methods/reasons are fully listed in "
              f"`{prefix}oracle_test_matches.csv` (including matched rows) and per-task JSON arrays "
              f"in `{prefix}patches.csv`. Missing selection is unknown, not a failed match. "
              "An empty official list is not applicable. Positive counts are demonstrable "
              "lower bounds; a no-exact-ID hit is not proof that a renamed pre-existing "
              "counterpart was absent. Such mappings cannot be invented from name similarity. "
              "These are post-hoc coverage observations, "
              "not a selector or a proposed test set.", "",
              "## POST-HOC ORACLE-ONLY: known wrong patches", "",
              "Relevant test means an official FAIL_TO_PASS test the patch fails, from the stored "
              "oracle record. P2P-only failures are explicitly not applicable here. Added/rewritten "
              "means the official test version did not exist at base; an older function may still "
              "have been selected. Categories are per test and need not be mutually exclusive per task.",
              "Per-test execution outcomes are absent in current records. Partial timeout totals "
              "cannot identify which test timed out. Pre-existing-failure totals likewise cannot "
              "identify a particular test. Such cases remain missing, never guessed.", "",
              "| Wrong patch | Decision / V2 | Failed F2P count | Matched failed F2P IDs | Observed regressions | Categories |",
              "|---|---|---:|---:|---:|---|"]
    for row in rows:
        if row["oracle_outcome_posthoc"] == "unresolved":
            cats = Counter(d["category"] for d in row["relevant_test_categories_posthoc"])
            failed = row["failed_f2p_ids_posthoc"]
            matched = sum(bool(d.get("selected_ids")) for d in row["relevant_test_categories_posthoc"])
            lines.append(f"| {row['instance_id']} | {row['verifier_decision']} / {row['v2_outcome']} | "
                         f"{number(len(failed) if failed is not None else None)} | {matched} | "
                         f"{number(row['number_observed_regressions'])} | "
                         + "; ".join(f"{k}: {v}" for k, v in cats.items()) + " |")
    category_tasks = defaultdict(set)
    for detail in wrong:
        category_tasks[detail["category"]].add(detail["instance_id"])
    lines += ["", "Category task counts: " + str({k: len(v) for k, v in sorted(category_tasks.items())}) + ".",
              "Detailed identities, normalization methods and provenance are in "
              f"`{prefix}wrong_patch_tests.csv`. matplotlib-25479 is the one wrong patch with "
              "V2 FAIL and one observed regression: detection at patch level is recorded, "
              "but the missing per-test outcomes prevent attributing that regression to a "
              "particular failed F2P test.", "",
              "## Missing evidence, assumptions, and discrepancies", "",
              "- Tier 1/Tier 2 membership exists in Selection.by_tier at runtime but is not "
              "serialized by VerificationRecord. Both requested tier counts remain blank. "
              "The recorded union/order cannot reconstruct overlapping tier memberships.",
              "- Candidate Python source files and symbols are derived using the existing "
              "parse_patch/touched_symbols and selector source-file definition. These are "
              "diff-derived names, not a call graph or a complete semantic change inventory.",
              "- Every main CSV value has `_status` (recorded/inferred/missing) and `_source`. "
              "Sparse histogram keys become inferred zero only if the histogram covers the "
              "entire selected union; missing records remain blank.",
              "- Full selected-ID unions remain in the hashed input records rather than "
              "being duplicated as enormous CSV cells. Matched IDs are in the oracle-only "
              "detail CSV; every unmatched official ID is listed there as well.",
              "- No base-tree discovery or test execution is repeated. Existing Group 4 rerun "
              "outputs were inspected but are not substituted for main-study evidence.",
              "- The extracted snapshot covers 19 deliberately chosen failure-analysis cases. "
              "The cached Arrow benchmark supplies only post-hoc official lists and gold diffs; "
              "it supplies no missing selection or execution evidence. The input manifest "
              "records code and input paths and SHA-256 hashes; no dataset loader/download is invoked."]
    lines += ["", "| Field | Recorded | Inferred | Missing |", "|---|---:|---:|---:|"]
    for field in ("changed_source_files", "changed_symbols", "test_layout_convention",
                  "tier1_selected_count", "tier2_selected_count", "total_selected_tests",
                  "number_executed", "number_timed_out", "number_pre_existing_failures",
                  "number_observed_regressions", "v2_runtime_s", "per_test_outcomes"):
        counts = Counter(r[field + "_status"] for r in rows)
        lines.append(f"| {field} | {counts['recorded']} | {counts['inferred']} | {counts['missing']} |")
    lines.append("")
    for row in rows:
        if row["pytest_7432_note_posthoc"]:
            lines.append("- pytest-7432: " + row["pytest_7432_note_posthoc"])
    lines += ["- django-13297: the failed-F2P set is empty (its oracle failure is P2P). "
              "Its 6,890/8,155 timeouts establish partial V2 evidence, not the individual warning "
              "test's execution status. PASS requires some execution and zero observed regressions "
              "(VERIFIER_POLICY.md §4), not full selection completion.",
              "- pylint-7277: aggregate PRE_EXISTING_FAIL does not prove the outcome of "
              "test_jobs_score. The earlier narrative's likely explanation is not promoted to data.",
              "- django-12209: the official F2P string is a functools.partial docstring, "
              "not a resolvable test identity. It stays unmatched.",
              "- A gold diff may omit the enclosing test class. Exact file/function evidence "
              "with missing class scope is reported unresolved rather than guessed or called "
              "a selection failure. Renamed tests and docstring-only IDs without an exact "
              "stored identity mapping are likewise unresolved; no fuzzy correspondence is used.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-arrow", type=Path,
                        help="existing benchmark Arrow file, read directly without network/locks")
    parser.add_argument("--sample", action="store_true", help="only the three named preview tasks")
    args = parser.parse_args(argv)
    inputs = Inputs()
    for path in (OUT / "diagnostic.py", OUT / "oracle_posthoc.py", OUT / "test_diagnostic.py",
                 REPO / "docs/VERIFIER_POLICY.md", REPO / "src/reliability/verifier/selection.py",
                 REPO / "src/reliability/verifier/regression.py", REPO / "src/reliability/verifier/record.py",
                 REPO / "src/reliability/verifier/patch.py", REPO / "uv.lock"):
        inputs.read(path)
    study = population(inputs.read(REPO / "docs/results_100.csv").decode())
    if args.sample:
        study = [next(r for r in study if r["instance_id"] == iid) for iid in SAMPLE]
    extracted = inputs.json(REPO / "reports/failure_analysis/extracted.json")
    snapshots = {(t["instance_id"], t["source_run"]): t for t in extracted["tasks"]}
    gold = load_gold_arrow(args.dataset_arrow, inputs)
    rows, matches, wrong = build(study, snapshots, gold, inputs)
    prefix = "sample_" if args.sample else ""
    command = "env -u PYTHONPATH .venv/bin/python -B reports/v2_diagnostic/oracle_posthoc.py"
    if args.dataset_arrow:
        command += " --dataset-arrow " + shlex.quote(str(args.dataset_arrow.resolve()))
    if args.sample:
        command += " --sample"
    fields = [k for k in rows[0] if not k.startswith("selected_test_ids")]
    write_csv(OUT / f"{prefix}patches.csv", rows, fields)
    write_csv(OUT / f"{prefix}oracle_test_matches.csv", matches)
    write_csv(OUT / f"{prefix}wrong_patch_tests.csv", wrong)
    (OUT / f"{prefix}report.md").write_text(report(rows, wrong, command, prefix), encoding="utf-8")
    (OUT / f"{prefix}inputs.json").write_text(json.dumps({
        "notice": NOTICE, "command": command, "sha256": inputs.files,
        "python_version": sys.version,
        "n_rows": len(rows), "sample_ids": list(SAMPLE) if args.sample else None,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rows to reports/v2_diagnostic/{prefix}patches.csv")
    if args.sample:
        preview_fields = ["instance_id", "source_run", "oracle_outcome_posthoc", "verifier_decision",
                          "v2_outcome", "changed_source_files", "changed_symbols",
                          "test_layout_convention", "tier1_selected_count", "tier2_selected_count",
                          "total_selected_tests", "number_executed", "number_timed_out",
                          "number_pre_existing_failures", "number_observed_regressions", "v2_runtime_s",
                          "execution_coverage", "pytest_7432_note_posthoc"]
        writer = csv.DictWriter(sys.stdout, fieldnames=preview_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: encoded(r[k]) for k in preview_fields} for r in rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
