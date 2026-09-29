"""Phase 8.3: the leakage audit must actually catch a leak.

An audit nobody has tested against a real leak is a comfort, not a gate, so most
of this file plants oracle data in an agent-visible artifact and asserts it is
found. The remainder pins the two scoping decisions the result depends on: the
oracle's own outputs are out of scope, and an audit that scanned nothing fails.
"""

from __future__ import annotations

import pytest

from reliability.benchmark.leakage import (
    ORACLE_FIELD_NAMES,
    OracleProbes,
    Severity,
    audit,
    audit_task,
    distinctive_lines,
    find_task_dirs,
    in_scope,
    probes_from_oracle,
)

GOLD_PATCH = """diff --git a/requests/sessions.py b/requests/sessions.py
index aaaaaaa..bbbbbbb 100644
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -70,7 +70,9 @@ def merge_setting(request_setting, session_setting):
-    for (k, v) in request_setting.items():
+    none_keys = [k for (k, v) in merged_setting.items() if v is None]
+    for key in none_keys:
+        del merged_setting[key]
"""

TEST_PATCH = """diff --git a/tests/test_requests.py b/tests/test_requests.py
--- a/tests/test_requests.py
+++ b/tests/test_requests.py
@@ -100,3 +100,6 @@ class TestRequests:
+    def test_header_remove_is_case_insensitive(self):
+        session = requests.Session()
+        assert session.headers.get('Accept-Encoding') is None
"""


class FakeOracle:
    instance_id = "psf__requests-1921"
    patch = GOLD_PATCH
    test_patch = TEST_PATCH
    fail_to_pass = ("tests/test_requests.py::TestRequests::test_header_remove",)
    hints_text = "The fix is to delete keys whose value is None after merging."


@pytest.fixture
def probes():
    return probes_from_oracle(FakeOracle())


def make_task(tmp_path, files: dict[str, str], instance="psf__requests-1921"):
    task_dir = tmp_path / "exp" / "tasks" / instance
    task_dir.mkdir(parents=True)
    for name, content in files.items():
        (task_dir / name).write_text(content)
    return task_dir


CLEAN = {
    "trajectory.jsonl": '{"role":"user","content":"Fix the header merge bug."}\n',
    "patch.diff": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n",
    "repair_record.json": '{"instance_id": "psf__requests-1921"}',
}


# --- a clean run passes ----------------------------------------------------


def test_a_clean_task_produces_no_findings(tmp_path, probes):
    findings, n_files = audit_task(make_task(tmp_path, CLEAN), probes)
    assert findings == []
    assert n_files == 3


def test_a_clean_run_passes(tmp_path, probes):
    make_task(tmp_path, CLEAN)
    result = audit(find_task_dirs(tmp_path), {"psf__requests-1921": probes})
    assert result.passed
    assert result.content_checked_tasks == 1


# --- planted leaks are caught ----------------------------------------------


def test_a_gold_patch_in_the_trajectory_is_caught(tmp_path, probes):
    """The case the gate exists for."""
    files = dict(CLEAN)
    files["trajectory.jsonl"] = (
        '{"role":"user","content":"Here is the fix: '
        "none_keys = [k for (k, v) in merged_setting.items() if v is None]\"}\n"
    )
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    confirmed = [f for f in findings if f.severity is Severity.CONFIRMED]
    assert any(f.kind == "gold-patch-content" for f in confirmed)


def test_a_leak_without_its_label_is_still_caught(tmp_path, probes):
    """A leak does not have to arrive carrying the word FAIL_TO_PASS."""
    files = dict(CLEAN)
    files["trajectory.jsonl"] = (
        "The expected test is:\n"
        "    def test_header_remove_is_case_insensitive(self):\n"
    )
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    assert not any("oracle-field-name" == f.kind for f in findings)
    assert any(f.kind == "test-patch-content" for f in findings)


def test_hints_text_in_a_prompt_is_surfaced_for_review(tmp_path, probes):
    """hints_text is the most easily overlooked leak — it is not ground truth,
    but it frequently describes the fix.

    It is REVIEW rather than CONFIRMED because hints and the problem statement
    are drawn from the same pull-request thread, so an agent reproducing the bug
    writes similar lines independently. See
    `test_an_agents_own_phrasing_of_the_issue_is_not_a_confirmed_leak`.
    """
    files = dict(CLEAN)
    files["trajectory.jsonl"] = (
        "Hint: The fix is to delete keys whose value is None after merging.\n")
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    matches = [f for f in findings if f.kind == "hints-text-content"]
    assert matches
    assert all(f.severity is Severity.REVIEW for f in matches)


# --- false positives the first real run exposed ----------------------------


def test_a_probe_also_in_the_problem_statement_is_not_used(tmp_path):
    """A string the agent was legitimately given cannot evidence a leak.

    hints_text routinely quotes the problem statement verbatim, so without this
    subtraction the audit reports a leak every time an agent restates the issue
    it was asked to fix.
    """
    class Overlapping:
        instance_id = "psf__requests-1921"
        patch = test_patch = ""
        fail_to_pass = ()
        hints_text = "session.headers.pop('Accept-Encoding', None)"

    statement = "Reported repro:\n    session.headers.pop('Accept-Encoding', None)\n"
    assert probes_from_oracle(Overlapping()).hints_lines
    assert probes_from_oracle(Overlapping(), statement).hints_lines == ()


def test_subtraction_applies_to_the_gold_patch_too(tmp_path):
    """Some issues quote the eventual fix in the report itself."""
    class Quoted:
        instance_id = "a__a-1"
        patch = "+    merged_setting = dict_class(to_key_val_list(session_setting))"
        test_patch = hints_text = ""
        fail_to_pass = ()

    statement = ("The bug is here:\n"
                 "    merged_setting = dict_class(to_key_val_list(session_setting))")
    assert probes_from_oracle(Quoted()).patch_lines
    assert probes_from_oracle(Quoted(), statement).patch_lines == ()


def test_an_agents_own_phrasing_of_the_issue_is_not_a_confirmed_leak(tmp_path):
    """The real case from the first run of this audit.

    The problem statement carried `session.headers['Accept-Encoding'] = None`;
    hints carried the same line abbreviated to `s.headers[...]`. Subtraction
    cannot catch that, so the severity has to.
    """
    class Abbreviated:
        instance_id = "psf__requests-1921"
        patch = test_patch = ""
        fail_to_pass = ()
        hints_text = "s.headers['Accept-Encoding'] = None"

    statement = "Repro:\n    session.headers['Accept-Encoding'] = None\n"
    probes = probes_from_oracle(Abbreviated(), statement)

    files = dict(CLEAN)
    files["trajectory.jsonl"] = "$ python -c \"s.headers['Accept-Encoding'] = None\"\n"
    task = make_task(tmp_path, files)

    findings, _ = audit_task(task, probes)
    assert findings                                   # still surfaced
    assert not [f for f in findings if f.severity is Severity.CONFIRMED]
    assert audit([task], {"psf__requests-1921": probes}).passed


@pytest.mark.parametrize("name", ORACLE_FIELD_NAMES)
def test_every_oracle_field_name_is_caught(tmp_path, name, probes):
    files = dict(CLEAN)
    files["trajectory.jsonl"] = f'{{"content":"debug dump: {name} = [...]"}}\n'
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    assert any(f.kind == "oracle-field-name" and name in f.detail for f in findings)


def test_a_leak_into_a_verifier_input_is_caught(tmp_path, probes):
    """Verifier inputs are in scope too — Phase 5.1 forbids selection from
    consulting PASS_TO_PASS."""
    files = dict(CLEAN)
    files["verification_record.full.json"] = (
        '{"selected_tests": [], "PASS_TO_PASS": ["test_a"]}')
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    assert any(f.kind == "oracle-field-name" for f in findings)


def test_a_leak_fails_the_audit(tmp_path, probes):
    files = dict(CLEAN)
    files["trajectory.jsonl"] = "PASS_TO_PASS leaked here\n"
    make_task(tmp_path, files)

    result = audit(find_task_dirs(tmp_path), {"psf__requests-1921": probes})
    assert not result.passed
    assert result.confirmed


def test_an_unreadable_file_cannot_be_cleared(tmp_path, probes):
    """A file that could not be scanned has not been shown to be clean."""
    task_dir = make_task(tmp_path, CLEAN)
    (task_dir / "patch.diff").chmod(0o000)
    try:
        findings, _ = audit_task(task_dir, probes)
        assert any(f.kind == "unreadable" for f in findings)
    finally:
        (task_dir / "patch.diff").chmod(0o644)


# --- FAIL_TO_PASS names are reviewable, not automatic failures -------------


def test_a_fail_to_pass_name_is_flagged_for_review(tmp_path, probes):
    """Most are added by the test patch and cannot legitimately appear, but some
    exist at the base commit and an agent reading the test file would reproduce
    them innocently."""
    files = dict(CLEAN)
    files["trajectory.jsonl"] = "$ pytest -k test_header_remove\n"
    findings, _ = audit_task(make_task(tmp_path, files), probes)

    matches = [f for f in findings if f.kind == "fail-to-pass-name"]
    assert matches
    assert all(f.severity is Severity.REVIEW for f in matches)


def test_a_review_finding_alone_does_not_fail_the_gate(tmp_path, probes):
    """Failing on a coincidence would train the reader to ignore the gate."""
    files = dict(CLEAN)
    files["trajectory.jsonl"] = "$ pytest -k test_header_remove\n"
    make_task(tmp_path, files)

    result = audit(find_task_dirs(tmp_path), {"psf__requests-1921": probes})
    assert result.passed
    assert result.review


# --- scoping ---------------------------------------------------------------


def test_the_oracles_own_output_is_out_of_scope(tmp_path, probes):
    """oracle_record.json is supposed to contain FAIL_TO_PASS names. Scanning it
    would guarantee a hit and make the audit meaningless."""
    files = dict(CLEAN)
    files["oracle_record.json"] = '{"fail_to_pass": {"success": ["test_a"]}}'
    files["harness.log"] = "FAIL_TO_PASS: test_header_remove_is_case_insensitive\n"
    findings, n_files = audit_task(make_task(tmp_path, files), probes)

    assert findings == []
    assert n_files == 3     # the two oracle outputs were not read


@pytest.mark.parametrize("name", [
    "oracle_record.json", "oracle_verdict.json", "harness.log", "predictions.jsonl"])
def test_oracle_outputs_are_excluded_by_name(tmp_path, name):
    assert not in_scope(tmp_path / name)


@pytest.mark.parametrize("name", [
    "trajectory.jsonl", "agent_output.txt", "patch.diff",
    "verification_record.full.json", "verification_record.baseline.json"])
def test_agent_and_verifier_artifacts_are_in_scope(tmp_path, name):
    assert in_scope(tmp_path / name)


def test_unknown_artifacts_are_out_of_scope_until_added(tmp_path):
    """An allowlist, so a new file is out of scope until someone adds it on
    purpose rather than being scanned by accident and producing noise."""
    assert not in_scope(tmp_path / "scratch_notes.txt")


def test_harness_controls_are_not_scanned(tmp_path):
    """runs/1.2_gold_sanity legitimately contains gold patches."""
    control = tmp_path / "1.2_gold_sanity"
    control.mkdir()
    (control / "predictions_gold.jsonl").write_text(GOLD_PATCH)
    make_task(tmp_path, CLEAN)

    found = find_task_dirs(tmp_path)
    assert len(found) == 1
    assert found[0].name == "psf__requests-1921"


# --- an audit that scanned nothing is not a pass ---------------------------


def test_scanning_no_tasks_is_a_failure(tmp_path):
    result = audit([], {})
    assert not result.passed
    assert result.scanned_files == 0


def test_scanning_a_task_with_no_artifacts_is_a_failure(tmp_path):
    empty = tmp_path / "exp" / "tasks" / "a__a-1"
    empty.mkdir(parents=True)

    result = audit([empty], {})
    assert not result.passed
    assert result.scanned_tasks == 1
    assert result.scanned_files == 0


def test_a_structural_only_audit_reports_no_content_coverage(tmp_path):
    """The gate script turns this into a failure; the result object must make
    the shortfall visible for it to do so."""
    make_task(tmp_path, CLEAN)
    result = audit(find_task_dirs(tmp_path))

    assert result.scanned_tasks == 1
    assert result.content_checked_tasks == 0


def test_empty_probes_do_not_count_as_content_coverage(tmp_path):
    make_task(tmp_path, CLEAN)
    result = audit(find_task_dirs(tmp_path),
                   {"psf__requests-1921": OracleProbes(instance_id="x")})
    assert result.content_checked_tasks == 0


# --- probe construction ----------------------------------------------------


def test_diff_markers_are_stripped_from_probes():
    """A leak would be reproduced as source, not as a diff."""
    lines = distinctive_lines(GOLD_PATCH)
    assert any(line.startswith("none_keys = [k for") for line in lines)
    assert not any(line.startswith("+") for line in lines)


def test_short_lines_are_not_used_as_probes():
    """`)` and `return None` appear in every repository."""
    text = "diff --git a/a.py b/a.py\n+)\n+    return None\n+    pass\n"
    assert distinctive_lines(text) == ()


def test_diff_noise_is_not_used_as_a_probe():
    for noise in ("@@ -1,2 +1,2 @@ def f(self, x):", "index abcdef1..1234567 100644"):
        assert noise.strip() not in distinctive_lines(f"diff --git a/a b/b\n{noise}\n")


def test_probes_are_capped():
    big = "\n".join(f"+    some_distinctive_line_number_{i} = compute()" for i in range(200))
    assert len(distinctive_lines(big)) <= 40


def test_probes_from_an_empty_oracle_are_empty():
    class Empty:
        instance_id = "a__a-1"
        patch = test_patch = hints_text = ""
        fail_to_pass = ()

    assert probes_from_oracle(Empty()).is_empty
