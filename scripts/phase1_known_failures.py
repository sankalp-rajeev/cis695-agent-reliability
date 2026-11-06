#!/usr/bin/env python3
"""POST-HOC ANALYSIS ONLY: inspect seven witnesses in stored full-83 captures.

Uses only the standard library. Never imports the harness or benchmark code,
starts processes, changes frozen evidence, or recomputes native verdicts.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re


WITNESS_SHA256 = "099bb6f13654a0ec10901f21c02eb3169d33214332f0dabe49fd6a7d6a6cdc76"
MANIFEST_SHA256 = "11ad4bb7ea40b987d20bcbbb6afdd030314ad1379c2956dada570e7c1ff87642"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def write_csv(path, rows):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def django_label(test_id):
    parts = test_id.split("::")
    module = parts[0]
    if module.startswith("tests/"):
        module = module[len("tests/"):]
    if module.endswith(".py"):
        module = module[:-3]
    module = module.replace("/", ".")
    return ".".join([module] + parts[1:])


def observe(test_id, family, call, call_index, verified):
    run = call["run"]
    requested = call.get("requested", run["requested_tests"])
    assert test_id in requested or family in requested, test_id
    selected = [r for r in run["results"] if r["test_id"] in (test_id, family)]
    assert len(selected) == 1, (test_id, selected)
    raw = [r for r in run["raw_results"] if r["test_id"] == test_id]
    if not raw and test_id.startswith("tests/"):
        raw = [r for r in run["raw_results"] if r["test_id"] == django_label(test_id)]
    assert len(raw) <= 1, (test_id, raw)
    runner = Path(run["evidence_files"]["runner.raw"])
    events = Path(run["evidence_files"]["events.jsonl"])
    capture_bytes = runner.read_bytes()
    capture_lines = capture_bytes.decode().split("\n")
    event_lines = events.read_text().splitlines()
    status = raw[0]["status"] if raw else "NOT_OBSERVED"
    status_word = {"passed": "PASSED", "failed": "FAILED", "skipped": "SKIPPED", "error": "ERROR"}.get(status)
    literal_lines = [(i, line) for i, line in enumerate(capture_lines, 1)
                     if test_id in line and status_word and
                     re.search(r"\s" + status_word + r"(?:\s|$)", line)]
    evidence = {"capture_path": str(runner), "capture_sha256": verified[str(runner)],
                "status_lines": [{"line": i, "text": line} for i, line in literal_lines],
                "events_path": str(events), "events_sha256": verified[str(events)]}
    if raw:
        assert literal_lines, (test_id, status, runner)
    else:
        label = django_label(test_id)
        starts = [(i, event) for i, event in enumerate(run["events"])
                  if event.get("event") == "start" and label in event.get("ids", [])]
        assert len(starts) == 1, (test_id, starts)
        index, start = starts[0]
        end = run["events"][index + 1]
        assert end["event"] == "end" and end["batch"] == start["batch"]
        assert end["returncode"] != 0 and not run["timed_out"]
        segment = capture_bytes[start["offset"]:end["offset"]]
        assert b"TypeError: don't know how to make test from: <property object" in segment
        first_line = capture_bytes[:start["offset"]].count(b"\n") + 1
        last_line = capture_bytes[:end["offset"]].count(b"\n")
        event_numbers = [i for i, line in enumerate(event_lines, 1)
                         if json.loads(line).get("batch") == start["batch"]]
        assert len(event_numbers) == 2
        evidence.update({"batch": start["batch"], "batch_returncode": end["returncode"],
                         "batch_capture_lines": [first_line, last_line],
                         "batch_byte_offsets": [start["offset"], end["offset"]],
                         "batch_event_lines": event_numbers,
                         "diagnostic": "TypeError: don't know how to make test from: <property object ...>",
                         "target_label_in_start_event": label,
                         "other_label_in_same_batch": "django.test.runner.RemoteTestResult.test_index",
                         "limitation": "Loader property-object failure is observed; exact offending label is not identified by the traceback."})
        trace_start = next(i for i in range(first_line, last_line + 1)
                           if capture_lines[i - 1] == "Traceback (most recent call last):")
        evidence["exact_traceback"] = [{"line": i, "text": capture_lines[i - 1]}
                                       for i in range(trace_start, last_line + 1)]
    if status == "skipped":
        assert raw[0].get("message", "") == "", "A stored full skip message requires review"
        match = re.search(r"\bSKIPPED(?:\s+\(([^)]*)\))?", literal_lines[0][1])
        assert match
        evidence["captured_skip_reason"] = match.group(1)
        evidence["skip_reason_complete"] = bool(match.group(1) and "..." not in match.group(1))
        evidence["skip_mechanism"] = "UNKNOWN_FROM_CAPTURE: marker/importorskip/version/platform condition not recorded"
    gap = bool(raw and test_id != family and selected[0]["status"] == "not_run")
    if gap:
        assert family in run["raw_id_map"][test_id]
    return {"call_index": call_index, "phase": "patched" if call["patched"] else "base",
            "scope": "initial" if call_index < 2 else "confirmation_or_base_recheck",
            "raw_status": status, "selected_status": selected[0]["status"],
            "parameter_admission_gap": gap, "timed_out": run["timed_out"],
            "evidence_complete": run["evidence_complete"], "evidence": evidence}


def inspect_recorded_policy(args, tasks, expected, inputs):
    """Read stored provenance, candidate file names and pinned scoring source."""
    def recorded_json(path):
        digest = sha(path)
        assert digest == expected[str(path)], path
        inputs[str(path)] = digest
        return json.loads(path.read_text())

    provenance = recorded_json(args.results / "run_provenance.json")
    policy = args.execution_source / "src/reliability/verifier/regression.py"
    digest = sha(policy)
    assert digest == provenance["source_sha256"]["src/reliability/verifier/regression.py"]
    inputs[str(policy)] = digest
    policy_lines = policy.read_text().split("\n")
    required = ["TestStatus.PASSED, TestStatus.SKIPPED", "if (result is None or result.status is TestStatus.NOT_RUN) and recovered:",
                'return "INCOMPLETE" if original == "PASS" and completeness != "COMPLETE" else original',
                "if base_ok and patched_ok:"]
    assert all(any(needle in line for line in policy_lines) for needle in required)
    policy_refs = [{"line": i, "text": line} for i, line in enumerate(policy_lines, 1)
                   if any(needle in line for needle in required) or "return Outcome.PASS" in line]
    frozen_tasks = recorded_json(args.frozen / "tasks.json")
    task = next(row for row in frozen_tasks if row["instance_id"] == "django__django-13297")
    patch = args.frozen / task["patch_path"]
    assert sha(patch) == task["patch_sha256"] == expected[str(patch)]
    inputs[str(patch)] = sha(patch)
    # Publish only changed file names and the digest, never candidate patch text.
    changed = re.findall(r"^\+\+\+ b/(.+)$", patch.read_text(), re.MULTILINE)
    assert changed == ["django/views/generic/base.py"]
    facts = {task_id: {"verdict": row["signal"], "original_verdict": row["original_signal"],
             "completeness": row["completeness"], "incompleteness_count": len(row["incompleteness"]),
             "initial_capture_complete": [call["run"]["evidence_complete"] for call in row["calls"][:2]]}
             for task_id, row in tasks.items()}
    for task_id in ["pylint-dev__pylint-6528", "pylint-dev__pylint-7277"]:
        assert facts[task_id]["verdict"] == "PASS" and facts[task_id]["completeness"] == "COMPLETE"
        assert facts[task_id]["incompleteness_count"] == 0
    return {"tasks": facts, "scoring_source": str(policy), "scoring_source_sha256": digest,
            "scoring_source_revision": provenance["actual_git_revision"], "scoring_lines": policy_refs,
            "django_candidate_changed_files": changed, "django_candidate_patch_sha256": task["patch_sha256"],
            "django_target_module": "generic_views.test_base", "django_other_requested_module": "django.test.runner",
            "skip_mechanism_limit": "Full reason strings and marker/importorskip/version/platform mechanisms are not recoverable from these captures. No source archive or runtime probe was used."}


def render_summary(records, facts):
    django = next(r for r in records if r["summary"]["instance_id"] == "django__django-13297")
    lines = ["# Phase 1: seven existing-test grader failures", "", "**POST-HOC ANALYSIS ONLY.**",
        "Seven witnesses across four incorrect-labelled patches were inspected using stored full-83 captures and hash-pinned execution provenance/scoring source. All seven were selected; 40 capture hashes verify.", "",
        "| Bucket | Tests | Finding |", "|---|---:|---|",
        "| A — not reached | 1 | Django batch loader failure on both trees |",
        "| E — skipped on both trees | 5 | Four Pylint-6528 witnesses and one Pylint-7277 witness |",
        "| F — already detected | 1 | Matplotlib-25479 confirmed regression |", "",
        "**Buckets E (skipped) and F (already detected) were added after Phase 1 inspection of the data.** They were not preregistered. Frozen selectors, outcomes and verdicts remain unchanged. The roadmap amendment records the retrospective addition.", "",
        "## Django-13297: exact error and effect on the verdict", "",
        "Target: `tests/generic_views/test_base.py::DeprecationTests::test_template_params_warning`; module `generic_views.test_base` (the capture prints `Importing application generic_views`). Batch 3 also requests `django.test.runner.RemoteTestResult.test_index`. The traceback does not name the exact offending test label, so that label is not asserted to be the culprit.", ""]
    for observation in django["observations"]:
        e = observation["evidence"]
        lines += ["**" + observation["phase"] + " tree:** `" + e["capture_path"] + ":88` (traceback lines 88–99).", "", "```text"]
        lines += [str(line["line"]) + ": " + line["text"] for line in e["exact_traceback"]]
        lines += ["```", ""]
    lines += ["The exception occurs on **both** trees; each batch exits 1 without a timeout. The failing frame is Python 3.6 `unittest.loader.loadTestsFromName`, line 213. Calling frames are `tests/runtests.py` and `django/test/runner.py`. The candidate changes only `django/views/generic/base.py`: neither the failing frame nor any listed calling frame is candidate-modified. The candidate file names/digest and stored scoring source hash are recorded in `phase1_evidence.json`.", "",
        "V2 records selected status **NOT_RUN on base and NOT_RUN on patched**, with no concrete raw observation. Its paired per-test outcome is NOT_RUN. Both missing statuses appear in the recorded incompleteness list. The task's original PASS is converted to **INCOMPLETE** (`INCOMPLETE_CONFIRMED`); this gap contributes alongside other gaps, without being scored as a candidate regression. Since the error is not patched-only, this case does not trigger the proposed additional patched-only REGRESSION_ERROR roadmap item.", "",
        "## Five Pylint skips: exact saved text and limits", "",
        "| Task | Test | Captured reason string, on each tree | Skip mechanism | Base / patched selected status |", "|---|---|---|---|---|"]
    for record in records:
        row = record["summary"]
        if row["bucket"] != "E_SKIPPED":
            continue
        base, patched = record["observations"][:2]
        reason = base["evidence"]["captured_skip_reason"]
        assert reason == patched["evidence"]["captured_skip_reason"]
        text = "not printed" if reason is None else "`" + reason + "` (truncated)"
        lines.append("| " + row["instance_id"] + " | `" + row["test_id"] + "` | " + text +
                     " | unknown from captures | " + base["selected_status"].upper() + " / " + patched["selected_status"].upper() + " |")
    lines += ["", "The saved lines prove SKIPPED for all five concrete tests on both trees. They do **not** preserve the full reason strings or identify a marker, importorskip, version guard or platform guard. The recorded raw-result `message` fields are empty. `Need 2...` and `Need 2 or mo...` are reported verbatim; their expansions and mechanisms are not inferred. No source archives were inspected, no benchmark code was imported, and no Docker/rerun/environment probe was performed.", "",
        "**Final task verdicts: pylint-6528 PASS / COMPLETE; pylint-7277 PASS / COMPLETE, both with zero recorded incompleteness reasons.** These skips were accepted for completeness. The frozen scorer treats SKIPPED as `base_ok`/`patched_ok`, producing per-test PASS for the three exact selected IDs. For the two multiprocessing parameter cases, the bare selected family stays NOT_RUN, but mapped raw SKIPPED cases satisfy the completeness recovery rule. Thus these PASS verdicts relied on accepting skipped selected evidence. Under the requested stricter missing-evidence rule, the existing PASS→INCOMPLETE gate would block those PASS decisions; no native record is rescored here.", "",
        "Stored policy evidence: `" + facts["scoring_source"] + "` — completeness recovery at lines 232–237, skip-to-PASS classification at lines 311–315, and PASS→INCOMPLETE at line 266. Its hash matches the completed run provenance. Phase 3 therefore adds **treat SKIPPED selected tests as missing evidence for PASS**, including mapped parameter cases.", "",
        "## Artifacts and accounting", "",
        "`phase1_known_failures.csv` has seven rows and the requested `base_outcome`, `patched_outcome`, `skip_or_error_reason`, `v2_task_verdict`, `evidence_path:line` fields. The outcome columns are the runner's selected-ID statuses; concrete parameter SKIPPED states remain in `base_raw_status`/`patched_raw_status`, and skip mechanisms are explicitly unknown. Every evidence reference names each tree separately.", "",
        "`phase1_observations.csv` has all 16 observations; `phase1_evidence.json` retains status/traceback excerpts, source/capture hashes, task completeness, and event/byte ranges. Matplotlib retains PASS→FAIL, patched confirmation FAIL, additional base PASS, native REGRESSION and task FAIL. No C or D case was observed. No Phase 2 work was performed.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--witnesses", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--local-evidence-manifest", required=True, type=Path)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--execution-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert sha(args.witnesses) == WITNESS_SHA256, "Pinned e1a3ed1 witness inventory drift"
    assert sha(args.local_evidence_manifest) == MANIFEST_SHA256, "Local evidence manifest drift"
    expected = {}
    for line in args.local_evidence_manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert name not in expected
        expected[name] = digest
    assert len(expected) == 2988
    with args.witnesses.open(newline="") as stream:
        witnesses = [row for row in csv.DictReader(stream)
                     if row["evidence_tier"] == "official_existing_base_witness"]
    assert len(witnesses) == 7 and len({w["instance_id"] for w in witnesses}) == 4
    tasks, input_hashes, capture_hashes = {}, {str(args.witnesses): WITNESS_SHA256}, {}
    for task in sorted({row["instance_id"] for row in witnesses}):
        path = args.results / "tasks" / task / "v2/result.json"
        digest = sha(path)
        assert digest == expected[str(path)], path
        input_hashes[str(path)] = digest
        data = json.loads(path.read_text())
        assert data["instance_id"] == task
        tasks[task] = data
        for call in data["calls"]:
            for name, capture in call["run"]["evidence_files"].items():
                capture = Path(capture)
                digest = sha(capture)
                assert digest == call["run"]["evidence_sha256"][name] == expected[str(capture)], capture
                capture_hashes[str(capture)] = digest
    policy_facts = inspect_recorded_policy(args, tasks, expected, input_hashes)
    records, rows, observation_rows = [], [], []
    for witness in sorted(witnesses, key=lambda w: (w["instance_id"], w["matching_id"])):
        task, test_id = witness["instance_id"], witness["matching_id"]
        data = tasks[task]
        family = test_id.split("[", 1)[0]
        assert test_id in data["selected_tests"] or family in data["selected_tests"]
        observations = [observe(test_id, family, call, i, capture_hashes)
                        for i, call in enumerate(data["calls"])]
        base, patched = observations[:2]
        assert (base["phase"], patched["phase"]) == ("base", "patched")
        gap = any(o["parameter_admission_gap"] for o in observations)
        if all(o["raw_status"] == "skipped" for o in observations):
            bucket, reason = "E_SKIPPED", "Explicit SKIPPED on both trees; assertions were not exercised."
            if test_id.endswith("test_custom_should_analyze_file"):
                reason += " Capture does not print a skip reason."
            else:
                reason += " Capture prints a truncated 'Need 2...' reason; the complete condition is unproven."
            if gap:
                reason += " Concrete skipped parameter outcomes were also dropped from bare-family admission (secondary B-type gap)."
            assert data["signal"] == "PASS" and data["completeness"] == "COMPLETE"
            assert data["outcomes"][family] == ("NOT_RUN" if gap else "PASS")
        elif all(o["raw_status"] == "NOT_OBSERVED" for o in observations):
            bucket, reason = "A_NOT_REACHED", "Requested in batch 3 on both trees; loader property-object TypeError aborted the batch. Not a timeout."
            assert data["original_signal"] == "PASS" and data["signal"] == "INCOMPLETE"
            assert data["outcomes"][family] == "NOT_RUN"
            for phase in ["base", "patched"]:
                assert phase + ": " + test_id + ": not_run" in data["incompleteness"]
            for observation in observations:
                for line in observation["evidence"]["exact_traceback"]:
                    frame = re.search(r'File "([^"]+)"', line["text"])
                    if frame:
                        relative = frame.group(1).replace("/testbed/", "", 1)
                        assert relative not in policy_facts["django_candidate_changed_files"]
        elif base["raw_status"] == "passed" and patched["raw_status"] == "failed":
            bucket, reason = "F_ALREADY_DETECTED", "Native REGRESSION and task FAIL; patched confirmation failed and additional base observation passed."
            assert data["signal"] == "FAIL" and data["outcomes"][family] == "REGRESSION"
            assert [o["raw_status"] for o in observations] == ["passed", "failed", "failed", "passed"]
        else:
            raise AssertionError((task, test_id, observations))
        row = {"analysis_scope": "POST-HOC ANALYSIS ONLY", "instance_id": task,
               "test_id": test_id, "selected_family": family, "selected_by_v2": True,
               "bucket": bucket, "base_raw_status": base["raw_status"],
               "patched_raw_status": patched["raw_status"],
               "base_selected_status": base["selected_status"],
               "patched_selected_status": patched["selected_status"],
               "secondary_parameter_admission_gap": gap,
               "native_test_outcome": data["outcomes"].get(test_id, data["outcomes"].get(family)),
               "native_task_verdict": data["signal"], "reason": reason,
               "base_capture": base["evidence"]["capture_path"],
               "base_capture_sha256": base["evidence"]["capture_sha256"],
               "base_capture_lines": json.dumps([r["line"] for r in base["evidence"]["status_lines"]]
                   or base["evidence"].get("batch_capture_lines", [])),
               "patched_capture": patched["evidence"]["capture_path"],
               "patched_capture_sha256": patched["evidence"]["capture_sha256"],
               "patched_capture_lines": json.dumps([r["line"] for r in patched["evidence"]["status_lines"]]
                   or patched["evidence"].get("batch_capture_lines", []))}
        row["base_outcome"] = base["selected_status"].upper()
        row["patched_outcome"] = patched["selected_status"].upper()
        row["v2_task_verdict"] = data["signal"]
        row["v2_task_completeness"] = data["completeness"]
        if bucket == "E_SKIPPED":
            printed = base["evidence"]["captured_skip_reason"]
            assert printed == patched["evidence"]["captured_skip_reason"]
            row["skip_or_error_reason"] = "reason not printed" if printed is None else printed
            row["skip_mechanism"] = base["evidence"]["skip_mechanism"]
        elif bucket == "A_NOT_REACHED":
            row["skip_or_error_reason"] = "Both trees: TypeError: don't know how to make test from: <property object ...>; batch 3 loader abort"
            row["skip_mechanism"] = "not applicable"
        else:
            row["skip_or_error_reason"] = "already detected: base PASSED, patched FAILED, confirmation FAILED, base recheck PASSED"
            row["skip_mechanism"] = "not applicable"
        row["evidence_path:line"] = "; ".join(o["phase"] + "=" + o["evidence"]["capture_path"] + ":" +
             str(o["evidence"]["status_lines"][0]["line"] if o["evidence"]["status_lines"] else 88)
             for o in observations[:2])
        rows.append(row)
        records.append({"summary": row, "witness_inventory_record": witness, "observations": observations})
        for o in observations:
            observation_rows.append({"instance_id": task, "test_id": test_id,
                **{k: v for k, v in o.items() if k != "evidence"},
                "capture_path": o["evidence"]["capture_path"],
                "capture_sha256": o["evidence"]["capture_sha256"],
                "capture_lines": json.dumps([r["line"] for r in o["evidence"]["status_lines"]]
                    or o["evidence"].get("batch_capture_lines", []))})
    counts = dict(Counter(row["bucket"] for row in rows))
    assert counts == {"A_NOT_REACHED": 1, "F_ALREADY_DETECTED": 1, "E_SKIPPED": 5}
    assert len(observation_rows) == 16 and len(capture_hashes) == 40
    assert sum(r["secondary_parameter_admission_gap"] for r in rows) == 2
    # Recheck every consumed input after analysis, before creating new outputs.
    for name, digest in {**input_hashes, **capture_hashes}.items():
        assert sha(Path(name)) == digest, name
    args.output.mkdir(parents=True, exist_ok=False)
    write_csv(args.output / "phase1_known_failures.csv", rows)
    write_csv(args.output / "phase1_observations.csv", observation_rows)
    write_json(args.output / "phase1_evidence.json", {"analysis_scope": "POST-HOC ANALYSIS ONLY",
        "witness_source_revision": "e1a3ed1c74fd304493c3fe3811de755af77e306c",
        "witness_source_sha256": WITNESS_SHA256, "local_evidence_manifest": str(args.local_evidence_manifest),
        "local_evidence_manifest_sha256": MANIFEST_SHA256, "input_sha256": input_hashes,
        "capture_sha256": capture_hashes, "verified_captures": len(capture_hashes),
        "bucket_counts": counts, "records": records, "followup_answers": policy_facts,
        "categories_added_after_phase1_inspection": ["E_SKIPPED", "F_ALREADY_DETECTED"], "native_verdicts_changed": False,
        "benchmark_tests_executed": 0, "containers_started": 0})
    summary = render_summary(records, policy_facts)
    with (args.output / "SUMMARY.md").open("x") as stream:
        stream.write(summary)
    print(json.dumps({"output": str(args.output), "tests": len(rows), "bucket_counts": counts,
                      "observations": len(observation_rows), "verified_captures": len(capture_hashes)}, indent=2))


if __name__ == "__main__":
    main()
