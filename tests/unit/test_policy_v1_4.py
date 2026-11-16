"""Offline behavioral gates for the four pre-decided v1.4 changes."""

import difflib
import itertools
import json
from pathlib import Path

import pytest
import yaml

from reliability.reporting.accounting import accounting_sensitivities, report_accounting
from reliability.verifier.decision import Decision, Evidence, FullPolicy, SignalOutcome
from reliability.verifier.integrity_v1_4 import check_integrity, compare_tests
from reliability.verifier.patch import parse_patch
from reliability.verifier.policy_v1_4 import EvidenceV14, FullPolicyV14, get_policy
from reliability.verifier.reproduction_freeze import GenerationOutcome, ReproductionSetup
from reliability.verifier.reproduction_v1_4 import RecordingGenerator, run_reproduction, telemetry
from reliability.verifier.static_v1_4 import run_static_checks

ROOT = Path(__file__).resolve().parents[2]
BASE = "def test_existing():\n    x = 2\n    assert x == 2\n    assert x > 0\n"


def patch(path, before, after):
    return f"diff --git a/{path} b/{path}\n" + "".join(
        difflib.unified_diff(
            before.splitlines(True),
            after.splitlines(True),
            fromfile="a/" + path,
            tofile="b/" + path,
        )
    )


@pytest.mark.parametrize("expression", ["True", "1", "not False", "x == x"])
def test_assertion_replaced_by_tautology(expression):
    assert compare_tests(BASE, BASE.replace("x == 2", expression))


def test_removed_assertion_not_hidden_by_assertion_in_new_test():
    after = BASE.replace("    assert x > 0\n", "") + "\ndef test_added():\n    assert True\n"
    assert compare_tests(BASE, after)


def test_pass_replaces_non_assertion_test_body():
    assert compare_tests("def test_x():\n    check()\n", "def test_x():\n    pass\n")


@pytest.mark.parametrize(
    "marker",
    [
        "pytest.mark.skip",
        "pytest.mark.skipif(True)",
        "pytest.mark.xfail",
        'unittest.skip("reason")',
        "unittest.expectedFailure",
    ],
)
def test_existing_test_decorators(marker):
    assert compare_tests(BASE, "@" + marker + "\n" + BASE)


@pytest.mark.parametrize("call", ['pytest.skip("reason")', 'pytest.xfail("reason")'])
def test_existing_test_skip_calls(call):
    assert compare_tests(BASE, BASE.replace("    x = 2", "    " + call + "\n    x = 2"))


@pytest.mark.parametrize(
    "after",
    [
        BASE + "    assert x < 3\n",
        BASE + "\ndef test_new():\n    assert True\n",
        BASE + "\n@pytest.mark.skip\ndef test_new():\n    pass\n",
        BASE.replace("x == 2", "x == 3"),
    ],
)
def test_additions_and_nontrivial_replacement_do_not_reject(after):
    assert not compare_tests(BASE, after)


def test_removal_in_method_not_hidden_by_new_method():
    before = "class TestX:\n    def test_a(self):\n        assert check()\n"
    after = "class TestX:\n    def test_a(self):\n        pass\n    def test_b(self):\n        assert check()\n"
    assert compare_tests(before, after)


@pytest.mark.parametrize(
    "path,before,after,reason",
    [
        ("tests/test_x.py", "def test_x():\n    pass\n", "def test_x(:\n", "SyntaxError"),
        ("tests/test_x.txt", "test\n", "changed\n", "non-Python"),
    ],
)
def test_unanalyzable_files_are_recorded(tmp_path, path, before, after, reason):
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(before)
    report = check_integrity(patch(path, before, after), tmp_path)
    assert report.analysis[0]["status"] == "unavailable"
    assert reason in report.analysis[0]["reason"]


def test_no_base_tree_is_explicit():
    report = check_integrity(patch("tests/test_x.py", BASE, BASE + "    assert True\n"))
    assert "base tree unavailable" in report.analysis[0]["reason"]


def test_real_patch_uses_complete_files(tmp_path):
    target = tmp_path / "tests/test_x.py"
    target.parent.mkdir()
    target.write_text(BASE)
    report = check_integrity(
        patch("tests/test_x.py", BASE, BASE.replace("x == 2", "True")), tmp_path
    )
    assert report.has(
        __import__("reliability.verifier.integrity", fromlist=["Violation"]).Violation.TEST_WEAKENED
    )
    assert report.analysis[0]["status"] == "checked"


class Tree:
    def list_files(self):
        return ("ruff.toml", "mypy.ini", "setup.py")

    def read_text(self, path):
        return ""


class Executor:
    def __init__(self, failing=()):
        self.failing = failing
        self.calls = []

    def run_capture(self, command, *, patched, timeout_s):
        self.calls.append((command, patched))
        tool = (
            "syntax"
            if "py_compile" in command
            else "import"
            if "-c" in command
            else "lint"
            if command[0] == "ruff"
            else "typecheck"
            if command[0] == "mypy"
            else "build"
        )
        version = "--version" in command
        stdout = "tool 1.0" if version else "old finding\n" + ("new finding\n" if patched else "")
        return {
            "exit_code": int(not version and tool in self.failing),
            "stdout": stdout,
            "stderr": "e" * 5000,
            "timed_out": False,
        }


SOURCE_PATCH = patch("mod.py", "x=1\n", "x=2\n")


def test_v3_all_command_evidence_and_relative_base_even_on_pass():
    report = run_static_checks(parse_patch(SOURCE_PATCH), Tree(), Executor())
    assert report.outcome is SignalOutcome.PASS
    for check in report.findings["checks"]:
        assert check["command"] and check["exit_code"] == 0
        assert check["tool_version"] != "unavailable"
        assert len(check["stderr"].encode()) == 4096
        if check["kind"] in ("lint", "typecheck"):
            assert check["base_result"]["exit_code"] == 0
            assert check["new_findings"] == ["new finding"]
        else:
            assert check["base_result"] is None


@pytest.mark.parametrize("kind", ["syntax", "import"])
def test_absolute_failure_gates_accept_and_import_has_baseline(kind):
    report = run_static_checks(parse_patch(SOURCE_PATCH), Tree(), Executor([kind]))
    assert report.outcome is SignalOutcome.FAIL
    check = next(c for c in report.findings["checks"] if c["kind"] == kind)
    if kind == "import":
        assert check["base_result"]["exit_code"] == 1
    evidence = EvidenceV14(
        integrity=SignalOutcome.PASS,
        regression=SignalOutcome.PASS,
        reproduction=SignalOutcome.PASS,
        v3_absolute_failure=True,
    )
    result = FullPolicyV14().decide(evidence)
    assert result.decision is Decision.FLAG
    assert result.reasons == ("v3_absolute_failure",)


def test_lint_typecheck_build_do_not_gate():
    report = run_static_checks(
        parse_patch(SOURCE_PATCH), Tree(), Executor(["lint", "typecheck", "build"])
    )
    assert report.outcome is SignalOutcome.PASS
    assert (
        FullPolicyV14()
        .decide(
            EvidenceV14(
                integrity=SignalOutcome.PASS,
                regression=SignalOutcome.PASS,
                reproduction=SignalOutcome.PASS,
            )
        )
        .decision
        is Decision.ACCEPT
    )


def test_v3_timeout_preserves_record():
    class TimeoutExecutor:
        def run_capture(self, *args, **kwargs):
            raise TimeoutError

    report = run_static_checks(parse_patch(SOURCE_PATCH), Tree(), TimeoutExecutor())
    assert all(
        c["status"] == "TIMEOUT" and c["exit_code"] is None for c in report.findings["checks"]
    )


def test_policy_truth_table_only_authorized_gate_changes():
    for values in itertools.product(SignalOutcome, repeat=4):
        fields = dict(zip(("integrity", "regression", "static", "reproduction"), values))
        old = FullPolicy().decide(Evidence(**fields))
        assert FullPolicyV14().decide(EvidenceV14(**fields)).decision == old.decision
        gated = FullPolicyV14().decide(EvidenceV14(**fields, v3_absolute_failure=True))
        assert gated.decision == (
            Decision.FLAG if old.decision is Decision.ACCEPT else old.decision
        )


def test_unavailable_ast_analysis_blocks_accept():
    result = FullPolicyV14().decide(
        EvidenceV14(
            integrity=SignalOutcome.PASS,
            regression=SignalOutcome.PASS,
            reproduction=SignalOutcome.PASS,
            v1_analysis_incomplete=True,
        )
    )
    assert result.decision is Decision.FLAG
    assert "v1_analysis_incomplete" in result.reasons


def setup():
    return ReproductionSetup.load(
        verifier_config=ROOT / "configs/verifier/full_v1_4.yaml", repo_root=ROOT
    )


def test_only_generator_step_cap_changes():
    old = yaml.safe_load((ROOT / "configs/verifier/full.yaml").read_text())
    new = yaml.safe_load((ROOT / "configs/verifier/full_v1_4.yaml").read_text())
    before, after = old["reproduction"]["budget"], new["reproduction"]["budget"]
    assert before["generator_max_steps"] == 40 and after["generator_max_steps"] == 80
    assert {**before, "generator_max_steps": 80} == after
    assert after["retries"] == 0
    assert get_policy().version == "v1.4.0-full"


@pytest.mark.parametrize(
    "termination,steps,cost,expected",
    [
        ("LimitsExceeded", 80, 0.1, "steps"),
        ("LimitsExceeded", 20, 1.0, "cost"),
        ("TimeExceeded", 2, 0.1, "time"),
        ("TokenLimit", 2, 0.1, "tokens"),
        ("LimitsExceeded", 2, 0.1, "other"),
        ("Submitted", 2, 0.1, None),
    ],
)
def test_v4_limit_subtypes_and_usage(termination, steps, cost, expected):
    messages = (
        {
            "role": "assistant",
            "content": "secret=sample-value\n" + "z" * 6000,
            "extra": {"response": {"usage": {"prompt_tokens": 12, "completion_tokens": 7}}},
        },
    )
    result = telemetry(
        GenerationOutcome({}, termination, steps, cost, trajectory=messages), setup(), 2.5
    )
    assert result["fired_limit_subtype"] == expected
    assert result["total_input_tokens"] == 12 and result["total_output_tokens"] == 7
    assert result["elapsed_seconds"] == 2.5
    assert result["configured_caps"]["generator_max_steps"] == 80
    assert len(result["sanitized_output_tail"].encode()) <= 4096


def test_v4_sanitizes_and_does_not_invent_missing_usage():
    result = telemetry(
        GenerationOutcome(
            {}, "Submitted", trajectory=({"role": "assistant", "content": "password=secret-value"},)
        ),
        setup(),
        1.0,
    )
    assert "secret-value" not in result["sanitized_output_tail"]
    assert result["total_input_tokens"] is None


def test_recording_generator_calls_once_and_persists(tmp_path):
    class Fake:
        calls = 0

        def generate(self, issue_text, instance_id):
            self.calls += 1
            return GenerationOutcome({}, "LimitsExceeded", 80, 0.1)

    fake = Fake()
    path = tmp_path / "evidence.json"
    RecordingGenerator(fake, setup(), path).generate("issue", "instance")
    assert fake.calls == 1
    assert json.loads(path.read_text())["fired_limit_subtype"] == "steps"


def test_disabled_v4_also_has_evidence_schema(tmp_path):
    record = run_reproduction(
        "x", "", setup(), cache_dir=tmp_path, use_container=False, patch_applies=True
    )
    assert record.findings["generation_evidence"]["steps_used"] is None
    assert record.findings["generation_evidence"]["configured_caps"]["retries"] == 0


def test_reporting_primary_and_all_labeled_sensitivities():
    outcomes = ["PASSED", "INVALID_ID"]
    primary = report_accounting(outcomes)
    assert primary["accounting"] == "S_invalid_excluded"
    assert primary["status"] == "PASS" and primary["denominator"] == 1
    assert primary["INVALID_ID"] == 1
    variants = accounting_sensitivities(["PASSED", "SKIPPED", "INVALID_ID"])
    assert len(variants) == 4 and sum(v["primary"] for v in variants) == 1
    assert variants[0]["status"] == "INCOMPLETE" and variants[2]["status"] == "PASS"
    assert all(v["label"].startswith("sensitivity:") for v in variants[1:])


def test_reporting_fail_never_demoted_and_empty_not_pass():
    assert all(v["status"] == "FAIL" for v in accounting_sensitivities(["FAILED", "INVALID_ID"]))
    assert report_accounting(["INVALID_ID"])["status"] == "INCOMPLETE"


def test_golden_and_audit_probe_proof():
    import csv

    directory = ROOT / "reports/policy_v1_4"
    golden = list(csv.DictReader((directory / "golden.csv").open()))
    delta = list(csv.DictReader((directory / "delta.csv").open()))
    probes = list(csv.DictReader((directory / "v1_probes.csv").open()))
    assert len(golden) == len(delta) == 100
    assert all(r["exact_record_match"] == "yes" for r in golden)
    assert all(r["caught"] == "yes" for r in probes)
    assert sum(r["expected"] == "REJECT" and r["suite"] == "sealed_audit" for r in probes) == 11


def test_v14_entrypoint_writes_separate_record_without_model_or_container(tmp_path):
    import hashlib
    from types import SimpleNamespace
    from unittest.mock import patch as mock_patch

    from reliability.verifier.run_v1_4 import verify_task

    data = SOURCE_PATCH.encode()
    (tmp_path / "patch.diff").write_bytes(data)
    (tmp_path / "patch.diff").chmod(0o444)
    repair = SimpleNamespace(
        instance_id="example__example-1",
        experiment_id="offline-test",
        patch=SimpleNamespace(
            sha256="sha256:" + hashlib.sha256(data).hexdigest(), size_bytes=len(data)
        ),
    )
    with mock_patch("reliability.verifier.run_v1_4.RepairRecord.read", return_value=repair):
        records = verify_task(tmp_path, use_container=False)
    assert records[0].decision.policy_version == "v1.4.0-full"
    assert records[0].decision.decision is Decision.FLAG
    assert (tmp_path / "verification_record.full-v1.4.json").is_file()
    assert not (tmp_path / "verification_record.full.json").exists()
    assert (
        records[0].reproduction.findings["generation_evidence"]["configured_caps"][
            "generator_max_steps"
        ]
        == 80
    )


def test_v1_skip_added_to_new_test_does_not_trigger_legacy_false_positive(tmp_path):
    target = tmp_path / "tests/test_existing.py"
    target.parent.mkdir()
    target.write_text(BASE)
    after = BASE + "\n@pytest.mark.skip\ndef test_new():\n    pass\n"
    report = check_integrity(patch("tests/test_existing.py", BASE, after), tmp_path)
    assert report.passed
    assert report.analysis[0]["status"] == "checked"


def test_recording_generator_error_preserves_elapsed_without_inventing_usage(tmp_path):
    class Broken:
        def generate(self, issue_text, instance_id):
            raise RuntimeError("password=sample-secret")

    path = tmp_path / "failed.json"
    with pytest.raises(RuntimeError):
        RecordingGenerator(Broken(), setup(), path).generate("issue", "instance")
    data = json.loads(path.read_text())
    assert data["elapsed_seconds"] >= 0
    assert data["steps_used"] is None
    assert data["token_usage_status"] == "generation failed before outcome"
    assert "sample-secret" not in data["sanitized_output_tail"]
