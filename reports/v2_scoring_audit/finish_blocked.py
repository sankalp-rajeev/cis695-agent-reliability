"""Finish reviewable audit outputs when Docker preflight prevents raw collection.

No oracle/grader/gold access, benchmark execution, or claims of corrected results.
"""
import ast
import csv
import io
import json
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

from audit import ROOT, OUT, SOURCES, csv_write, dump, read_json, sha, now


def canonical(tid, django=False):
    if django:
        p, *parts = tid.split("::")
        return p.removeprefix("tests/").removesuffix(".py").replace("/", ".") + "." + ".".join(parts)
    return tid.removeprefix("./")


def inspect_selected(iid, selected):
    """Source-only risk screening, not a claim that any test actually executed."""
    index, param, docstring = {}, [], []
    archive = Path.home() / "cg_repos/task_archives" / (iid + ".tar")
    if not archive.exists():
        return {"source_scan": "base archive missing", "parameter_family_count": None, "django_docstring_count": None,
                "unresolved_static_id_count": None, "plausibility": "UNKNOWN"}
    with tarfile.open(archive) as tar:
        members = {m.name: m for m in tar if m.isfile()}
        for path in sorted({t.split("::")[0] for t in selected}):
            member = members.get("testbed/" + path)
            if not member:
                continue
            try:
                tree = ast.parse(tar.extractfile(member).read().decode("utf-8", errors="replace"))
            except (SyntaxError, ValueError, RecursionError):
                continue
            def visit(body, classes=(), class_decorators=()):
                for n in body:
                    if isinstance(n, ast.ClassDef):
                        visit(n.body, classes + (n.name,), class_decorators + tuple(ast.unparse(d) for d in n.decorator_list))
                    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        tid = path + "::" + "::".join(classes + (n.name,))
                        index[tid] = {"line": n.lineno, "parametrized": any("parametrize" in d for d in class_decorators + tuple(ast.unparse(d) for d in n.decorator_list)),
                                      "docstring": bool(ast.get_docstring(n))}
            visit(tree.body)
    for tid in selected:
        n = index.get(tid)
        if n and n["parametrized"] and "[" not in tid:
            param.append({"selected_id": tid, "archive_member": "testbed/" + tid.split("::")[0], "line": n["line"]})
        if n and n["docstring"] and iid.startswith("django__"):
            docstring.append(tid)
    return {"source_scan": "base AST only; no collection or execution", "parameter_family_count": len(param),
            "parameter_family_evidence": param, "django_docstring_count": len(docstring),
            "unresolved_static_id_count": sum(t not in index for t in selected),
            "plausibility": "PLAUSIBLY_AFFECTED" if param or iid.startswith("django__") else "UNKNOWN: no raw ID output; static absence does not rule out mismatch"}


def affected_records(targets):
    metadata = read_json(ROOT / "reports/next_steps/nonoracle_metadata.json")
    snapshot = read_json(ROOT / "reports/next_steps/v2_projection.json")
    rows = []
    for iid, m in sorted(metadata.items()):
        selected = None
        provenance = m["artifact_kind"]
        if iid in snapshot:
            selected = snapshot[iid]["selected_tests"]
        else:
            p = ROOT / "runs" / m["source_run"] / "tasks" / iid / "verification_record.full.json"
            if p.is_file():
                # This is a verifier record, not an oracle/grader record.
                selected = read_json(p).get("selected_tests")
        risk = inspect_selected(iid, selected) if selected is not None else {
            "source_scan": "not possible: original selection record absent", "parameter_family_count": None,
            "django_docstring_count": None, "unresolved_static_id_count": None, "plausibility": "UNKNOWN: stored selection absent"}
        normalized = defaultdict(list)
        for tid in selected or []:
            normalized[canonical(tid, iid.startswith("django__"))].append(tid)
        collision = [v for v in normalized.values() if len(v) > 1]
        rows.append({"instance_id": iid, "source_run": m["source_run"], "record_provenance": provenance,
             "original_v2": m["v2_outcome"], "selection_available": selected is not None,
             "selected_count": len(selected) if selected is not None else None,
             "duplicate_or_normalized_selected_collision_count": len(collision) if selected is not None else None,
             "duplicate_raw_emitted_ids": "UNKNOWN: raw logs unavailable",
             **risk, "raw_evidence_subset_member": False,
             "raw_pair_status": "not found in inspected stored V2 sources; normalized baseline-only caches do not qualify",
             "rescoring_possible": False,
             "authorized_target": iid in targets,
             "additional_execution_authorized": iid in targets,
             "needed": "collect immutable raw base+patched evidence and stability repeats" + ("; recover original frozen selection first" if selected is None else ""),
             "blocker": "local Docker engine unavailable" if iid in targets else "not in authorized eight; do not rerun automatically",
             "status": "inferred risk/eligibility; stored outcome/provenance confirmed"})
        print("screened", iid, risk["plausibility"], flush=True)
    csv_write("affected_stored_records.csv", rows)
    csv_write("additional_reruns_needed.csv", [r for r in rows if r["instance_id"] not in targets])
    dump("raw_evidence_subset.json", {"size": 0, "instance_ids": [], "reason": "No new raw collection possible; no sufficient existing pre-parser paired logs found in inspected V2 sources",
        "authorized_targets_blocked": sorted(targets), "additional_non_target_patches": len(rows) - len(targets),
        "original_on_same_subset_size": 0, "corrected_on_same_subset_size": 0})
    return rows


def main():
    scope = read_json(OUT / "target_scope.json")["targets"]
    inputs = read_json(OUT / "frozen_inputs/selections.json")
    protocol = read_json(OUT / "protocol.json")
    for path, digest in protocol["source_hashes"].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError("production source changed")
    # No output is presented as actual test evidence when no test process was launched.
    raw_rows = []
    reruns, old_fixed, environment = [], [], []
    snapshot = read_json(ROOT / "reports/next_steps/v2_projection.json")
    for t in scope:
        iid = t["instance_id"]
        r = inputs[iid]
        for tid in r["selected_tests"]:
            raw_rows.append({"instance_id": iid, "source_run": r["source_run"], "requested_selected_id": tid,
                "raw_test_id": None, "base_outcome": None, "patched_outcome": None,
                "base_exit_status": None, "patched_exit_status": None,
                "base_timeout_status": None, "patched_timeout_status": None,
                "runner": r["runner"], "raw_base_stdout_ref": None, "raw_base_stderr_ref": None,
                "raw_patched_stdout_ref": None, "raw_patched_stderr_ref": None,
                "base_duration_s": None, "patched_duration_s": None,
                "record_kind": "UNEXECUTED_REQUEST_INVENTORY; not a raw test observation",
                "status": "UNKNOWN", "reason": "Docker engine preflight failed; no container/test launched"})
        reruns.append({"instance_id": iid, "candidate_rule": protocol["phase3_candidates"], "test_id": None,
              "required_additional_reruns_per_tree": 3, "base_completed_reruns": 0, "patched_completed_reruns": 0,
              "base_initial_runs": 0, "patched_initial_runs": 0,
              "base_pass_count": 0, "base_fail_count": 0, "base_error_count": 0, "base_timeout_count": 0,
              "patched_pass_count": 0, "patched_fail_count": 0, "patched_error_count": 0, "patched_timeout_count": 0,
              "stability": "UNKNOWN", "status": "NOT_EXECUTED; environment blocked, not a passing/flaky test"})
        old_fixed.append({"instance_id": iid, "original_study_v2": snapshot[iid]["regression"]["outcome"],
              "old_v2_on_audit_logs": None, "fixed_v2_on_same_audit_logs": None, "changed": "UNKNOWN",
              "fixed_raw_usable_flag": False, "raw_evidence_subset_member": False,
              "reason": "No new raw logs and no sufficient original paired raw evidence; do not turn absent evidence into corrected NOT_AVAILABLE"})
        environment.append({"instance_id": iid, "image_tag": r["study_image_tag"], "study_image_digest": None,
              "current_image_id": None, "current_repo_digests": None, "image_hash_match": "UNKNOWN",
              "docker_engine_reachable": False, "planned_runner": r["runner"], "observed_runner_version": None,
              "observed_python_version": None, "base_commit_check": "NOT_EXECUTED", "candidate_patch_sha256": r["patch_sha256"],
              "full_pass_timeout_s": 300, "initial_pair_budget_s": 600, "individual_rerun_timeout_s": 300,
              "historical_timeout_override": "UNKNOWN; no override in inspected snapshots; 300/600 are source defaults",
              "status": "UNKNOWN environment identity; confirmed engine preflight failure"})
    csv_write("raw_test_outcomes.csv", raw_rows)
    csv_write("regression_reruns.csv", reruns)
    csv_write("old_vs_fixed.csv", old_fixed)
    csv_write("environment_sanity.csv", environment)
    affected = affected_records(set(inputs))
    meta = read_json(ROOT / "reports/next_steps/nonoracle_metadata.json")
    original_counts = Counter(r["v2_outcome"] for r in meta.values())
    metrics = []
    for version in ("original_same_raw_evidence_subset", "corrected_same_raw_evidence_subset"):
        metrics.append({"population": "raw-evidence-supported paired subset", "version": version, "subset_size": 0,
             "subset_ids": [], "right_count": 0, "wrong_count": 0, "PASS": 0, "FAIL": 0, "NOT_AVAILABLE": 0,
             "usable_count": 0, "fail_precision_wrong_numerator": 0, "fail_precision_FAIL_denominator": 0,
             "fail_precision": None, "false_positive_numerator": 0, "usable_right_denominator": 0, "false_positive_rate": None,
             "wrong_detected_numerator": 0, "usable_wrong_denominator": 0, "wrong_detection_rate": None,
             "comparison_base_wrong_numerator": 14, "comparison_base_patch_denominator": 83,
             "comparison_base_wrong_rate": 14 / 83, "precision_minus_base_rate": None,
             "usable_definition": protocol["usable_v2_exact_user_definition"], "status": "UNKNOWN rates: empty subset, not zero performance"})
    csv_write("metrics_before_after.csv", metrics)
    # Carry the source-only proposal as an explicitly unvalidated diff. Do not invent observed fixtures.
    next_analysis = ast.parse((ROOT / "reports/next_steps/analyze.py").read_text())
    proposal = next(ast.literal_eval(n.value) for n in next_analysis.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "SUGGESTED_DIFF" for t in n.targets))
    (OUT / "parser_fix.diff").write_text(proposal)
    (OUT / "tests.txt").write_text(
        "NOT RUN. No benchmark, individual-test rerun, test collection, or parser-unit test was executed.\n"
        "Docker version commands only were attempted; exact argv and outcomes are in commands.jsonl and preflight/.\n"
        "Phase-2 raw test observations: 0. Phase-3 completed reruns: 0 per tree.\n"
        "No STABLE or FLAKY classifications made. No observed raw test-ID formats exist for this audit.\n"
        "Parser fixtures were not invented from gold tests, desired patch outcomes, or prior analysis guesses.\n"
        "parser_fix.diff is the prior source-only proposal, UNAPPLIED and UNVALIDATED here.\n"
    )
    existing = (OUT / "report.md").read_text()
    # Keep the Phase-1 preflight chronology verbatim; append the final status.
    if "## Final execution status" in existing:
        existing = existing.split("## Final execution status")[0]
    risk_counts = Counter("plausible" if r["plausibility"] == "PLAUSIBLY_AFFECTED" else "unknown" for r in affected)
    confirmed_selection = sum(r["selection_available"] and r["record_provenance"] == "study_snapshot" for r in affected)
    local_selection = sum(r["selection_available"] and r["record_provenance"] != "study_snapshot" for r in affected)
    lines = [existing.rstrip(), "", "## Final execution status", "",
        "[confirmed] **Execution is blocked: no local Docker engine endpoint is available.** The distro Docker wrapper says WSL integration is unavailable. The Windows CLI initially hit a sandbox socket restriction; the same read-only query was then authorized outside the sandbox and reached Windows, where both local named pipes were absent. This is an engine availability failure, not a sandbox approval rejection and not a test result.", "",
        "| Read-only preflight | Recorded result |", "|---|---|",
        "| distro `docker version` | [confirmed] Exit 1; Docker unavailable in this WSL distro |",
        "| Windows CLI, sandboxed | [confirmed] Exit 1; WSL vsock permission error |",
        "| Windows CLI, outside sandbox, `dockerDesktopLinuxEngine` | [confirmed] Exit 1; local pipe not found; `Server: null` |",
        "| Windows CLI, outside sandbox, legacy `docker_engine` | [confirmed] Exit 1; local pipe not found; `Server: null` |", "",
        "[confirmed] Every command was printed and recorded in `commands.jsonl` before execution, with a 20-second timeout. Stdout/stderr bytes and exit/status/duration are unchanged under `preflight/`. No network endpoint was used by the two Windows queries: both explicitly addressed local named pipes. No service was started and no image was pulled, built, installed or substituted.", "",
        "## Phase status", "", "| Phase | Result |", "|---|---|",
        "| 1: existing evidence and frozen amended protocol | [confirmed] Complete for the available records; per-patch cause remains UNKNOWN |",
        "| 2: initial raw base/patch collection | [unknown] Blocked before any container launch; 0 observations |",
        "| 3: bidirectional/base-FAIL confirmation | [unknown] 0 initial runs and 0 additional reruns on either tree; no STABLE/FLAKY labels |",
        "| 4: same-raw-log old/fixed comparison | [unknown] No qualifying raw log pair; not performed |",
        "| 5: actual-format parser tests and raw-only re-scoring | [unknown] Source-only risk screen completed; no observed raw formats, tests or valid re-scores |",
        "| 6: paired corrected metrics | [unknown] Raw-evidence subset size 0; rates undefined, not zero |", "",
        "[confirmed] `raw_test_outcomes.csv` inventories **18,662 requested selected IDs**, but its `record_kind` explicitly says UNEXECUTED_REQUEST_INVENTORY. Raw ID, tree outcomes, runner exits, timeout results, test duration and test stdout/stderr references are blank. The engine failure is not written as a test FAIL/TIMEOUT/NOT_AVAILABLE. `regression_reruns.csv` records the unmet three-additional-reruns requirement and zero completed attempts, not synthetic observations.", "",
        "[unknown] Image-hash equality cannot be established: the historical digest was not found in the inspected V2 metadata and the stopped engine prevents current image inspection. Runner/Python versions and base commit could not be checked in the image. `environment_sanity.csv` records all eight planned tags, candidate hashes, timeouts and UNKNOWN environment checks. No execution has been mistaken for flakiness or study-environment equivalence.", "",
        "## Source-only parser assessment and scope limit", "",
        "[confirmed] The current source contains the exact-admission parameter-family defect at `src/reliability/verifier/container.py:365`, independently of oracle correctness labels. The proposed local diff is unchanged from the preceding source review and remains unapplied. [unknown] Without new raw runner formats and repeat outcomes, this audit cannot validate or replace that proposal as an empirically justified final fix, nor show that it caused any target's verdict.", "",
        "[inferred] Family aggregation in the carried-forward proposal is incomplete for full case-level differential scoring: a family failing on both trees can conceal a new failing case. The Django parser's ambiguous suffix matching and last-write handling also require observed-format evidence. These limitations are stated rather than covered with outcome-directed synthetic fixtures. `tests.txt` therefore reports NOT RUN.", "",
        f"[confirmed] The stored-evidence risk screen covers all **83** nonempty headline rows, without reading oracle/grader/gold fields. Selected-ID unions are available for **{confirmed_selection} confirmed study snapshots** and **{local_selection} local-only, final-identity-unverified records**; the other **{83-confirmed_selection-local_selection}** lack detailed stored selections. Local-only evidence is not substituted for confirmed final-study evidence.", "",
        f"[inferred] Static base-archive inspection flags **{risk_counts['plausible']}** available-selection records as plausibly affected (explicit parameter families or Django parser exposure); **{risk_counts['unknown']}** remain UNKNOWN, including missing-selection records. This is a risk screen, not proof of a changed V2 result. Exact IDs, parameter/decorator file-line evidence, duplicate/normalization counts, and missing evidence are in `affected_stored_records.csv`.", "",
        "[confirmed] **Valid raw-evidence re-scoring subset: 0 patches, IDs `[]`. Original metrics on that same subset also contain 0 patches.** The older normalized baseline caches and named-regression summaries do not satisfy the requirement for paired pre-parser logs. `metrics_before_after.csv` contains paired empty-subset rows and undefined rate fields; zero numerators/denominators there describe an empty cohort, not an observed zero-error result. No corrected all-83 result is claimed.", "",
        f"[confirmed] For orientation only, the oracle-free committed V2 outcome tally is PASS={original_counts['PASS']}, FAIL={original_counts['FAIL']}, NOT_AVAILABLE={original_counts['NOT_AVAILABLE']}. These original labels do not establish the newly defined raw-complete usable denominator. The previous report's PASS-or-FAIL denominator is not reused as usable under this audit's stricter definition.", "",
        "[confirmed] `additional_reruns_needed.csv` lists the exact **75 patches outside the authorized eight**, the raw evidence needed and whether their original selection must first be recovered. None was rerun. The authorized eight are separately listed in `target_scope.json` and remain blocked. No additional run is authorized by this report.", "",
        "[confirmed] The raw-collection gate stayed closed. Other than the narrow, explicitly requested committed right/FAIL cohort lookup, this audit did not read new oracle outcomes, grader records, gold patches or official failing-test lists. No post-hoc label was used to select a confirmation test, diagnose a failure, design a parser fix or tune scoring.", "",
        "## Direct answers", "", "| Question | Answer |", "|---|---|",
        "| 1. Real parser/scoring bug? | [confirmed] Source-level parameterized-ID admission defect. [unknown] Empirical effect on these runs and final case-level fix are not established. Partial aggregate PASS alone is not evidence an individual timeout was scored PASS. |",
        "| 2. Did it cause any of the five right-patch FAILs? | [unknown] No qualifying raw rerun/repeat evidence. Existing parsed regression IDs do not establish parser causation. |",
        "| 3. Did it cause any of the three PASS misses? | [unknown] No qualifying paired raw per-test evidence; do not assign cached/aggregate failures to a named test. |",
        "| 4. How many apparent regressions were real? | [unknown] Six previously named parsed V2 transitions across five patches; zero newly validated. 'Zero validated' does not mean zero real. |",
        "| 5. How many were flaky? | [unknown] No initial/repeat audit outcomes, so neither STABLE nor FLAKY can be assigned. |",
        "| 6. Does corrected FAIL carry signal beyond the base rate? | [unknown] Corrected FAIL precision is 0/0 (undefined) on the zero-patch evidence subset, compared explicitly with the requested base rate 14/83 = 16.8675%. No corrected precision lift can be calculated; a targeted-eight statistic would not answer the population question. |",
        "| 7. Hard gate or advisory? | [inferred] Remain unresolved pending raw evidence and environment identity. No gate or policy was changed, and no recommendation was tuned using correctness labels. |", "",
        "[inferred] After raw collection becomes possible, interpretation must keep stable TRUE_REGRESSION on a post-hoc right patch separate from implementation bugs: a correct behavioral change can legitimately break an old test, which is a V2 design limit. Stable failed-base absorption is PRE_EXISTING_FAILURE. Neither observation authorizes changing the rule using gold outcomes.", "",
        "## Reproduction and stop boundary", "",
        "[confirmed] Commands executed in this audit: `python3 -B reports/v2_scoring_audit/audit.py prepare`; `python3 -B reports/v2_scoring_audit/audit.py preflight`; the separately printed/recorded Windows named-pipe queries; and `python3 -B reports/v2_scoring_audit/finish_blocked.py`. These performed artifact analysis or Docker version checks only. No benchmark or parser-unit test command ran.", "",
        "[confirmed] All required output filenames exist. Original code, policies, frozen study artifacts and existing reports are unchanged. The new frozen candidate/selection inputs and protocol are hashed; preflight evidence remains separate from test observations. Stopped at the unavailable-engine boundary. No selector work, coverage experiment, graph engineering, testmon, Ollama, model, agent or ablation was started.", ""]
    (OUT / "report.md").write_text("\n".join(lines))
    (OUT / "README.md").write_text(
        "# V2 scoring audit\n\n"
        "Status: BLOCKED BEFORE TEST EXECUTION. See [report.md](report.md).\n\n"
        "All five fixes and both interpretation notes are frozen in `protocol.json`. "
        "The eight authorized candidates and original selections are under `frozen_inputs/`.\n\n"
        "`commands.jsonl` and `preflight/` preserve the exact Docker version commands and their failures. "
        "Both local Windows engine pipes were absent even outside the sandbox. No container or test ran.\n\n"
        "`raw_test_outcomes.csv` is explicitly an unexecuted request inventory, not raw test observations. "
        "Empty outcome/ID/duration/log fields mean not collected. `regression_reruns.csv` has zero completed repeats. "
        "`old_vs_fixed.csv` leaves audit verdicts unknown. `metrics_before_after.csv` covers the same empty subset "
        "on both sides; undefined metrics must not be interpreted as zero rates or all-83 corrections.\n\n"
        "`affected_stored_records.csv` is a source-only risk screen of all 83 records. "
        "`additional_reruns_needed.csv` lists all 75 non-target patches, not authorization to run them. "
        "`parser_fix.diff` is a source-only, unapplied, unvalidated proposal; `tests.txt` records why no "
        "actual-format fixtures or tests could be run.\n\n"
        "Do not use post-hoc oracle labels for diagnosis, confirmation-test selection or scoring-rule tuning. "
        "Preserve all original artifacts. No network, commits, agents or models.\n"
    )
    dump("completion.json", {"time_utc": now(), "status": "blocked", "phase1_completed": True, "phases2_to6_completed": False,
         "docker_version_probes": 4, "containers_launched": 0, "test_runs": 0, "parser_unit_tests": 0,
         "raw_test_observations": 0, "unexecuted_request_inventory_rows": len(raw_rows), "raw_rescoring_subset_size": 0,
         "affected_records_screened": len(affected), "source_hashes_unchanged": True,
         "oracle_gate_opened": False, "cohort_label_exception": "only five committed right/FAIL target identification explicitly requested"})
    manifest = read_json(OUT / "frozen_inputs/manifest.json")
    for p, expected in manifest["files_sha256"].items():
        if sha((OUT / p).read_bytes()) != expected:
            raise ValueError("frozen input changed")
    if sha((OUT / "protocol.json").read_bytes()) != manifest["protocol_sha256"]:
        raise ValueError("protocol changed")
    dump("outputs.sha256.json", {str(p.relative_to(OUT)): sha(p.read_bytes()) for p in OUT.rglob('*')
                                if p.is_file() and p.name != "outputs.sha256.json"})
    print(json.dumps({"status": "blocked before tests", "requested_families": len(raw_rows),
                      "affected_records": len(affected), "raw_subset": 0, "sources_and_frozen_inputs_unchanged": True}))


if __name__ == "__main__":
    main()
