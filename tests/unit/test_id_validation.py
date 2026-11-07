"""Runner-aware static classification and collection-only native receipts."""

import ast
import json
import subprocess
import sys

import pytest

from reliability.env import clean_env
from reliability.verifier.collection import (
    _DJANGO_COLLECT,
    _NATIVE_DRIVER,
    _PYTEST_PLUGIN,
    ValidationPass,
    validate_in_container,
)
from reliability.verifier.id_validation import IDValidation, SourceTree, StaticIndex, merge_native
from reliability.verifier.regression import (
    Outcome,
    RunResult,
    Signal,
    TestResult,
    TestStatus,
    classify,
    completeness_of,
    run_from_dict,
    run_regression,
    run_to_dict,
)
from reliability.verifier.selection import Selection, TestRunner
from reliability.verifier.validated_run import apply_validation

SOURCE = """
from unittest import TestCase as Case
from unittest.mock import patch
class Base:
    def test_shared(self): raise AssertionError('must not execute')
class Concrete(Base, Case): pass
class Child(Concrete): pass
class Overrides(Base, Case):
    def test_shared(self): pass
class Other:
    def test_orphan(self): pass
class Tests(Case):
    @property
    def test_property(self): return 1
    @patch('os.getcwd')
    def test_decorated(self, mocked): pass
    def helper(self): pass
    constant = 1
    def test_host(self):
        def test_nested(): pass
class TestNative:
    def test_method(self): pass
class TestWithInit:
    def __init__(self): pass
    def test_method(self): pass
class TestHidden:
    __test__ = False
    def test_method(self): pass
class TestHiddenChild(TestHidden): pass
class TestVisibleChild(TestHidden):
    __test__ = True

def test_function(): pass
@patch('os.getcwd')
def test_wrapped(mocked): pass
"""


def index(runner="django", source=SOURCE, extra=None):
    return StaticIndex(SourceTree({"tests/test_sample.py": source, **(extra or {})}), runner)


def label(name):
    return "tests/test_sample.py::" + name


@pytest.mark.parametrize(
    "name,category,valid,reason",
    [
        ("Tests::test_decorated", "decorated_callable", True, ""),
        ("Tests::test_property", "property", False, "property"),
        ("test_function", "plain_function", False, "plain_function"),
        ("test_wrapped", "decorated_callable", False, "plain_function"),
        ("Tests::helper", "helper", False, "helper"),
        ("Tests::constant", "helper", False, "non_callable_attribute"),
        ("Tests::test_nested", "helper", False, "nested_helper"),
        ("Tests::test_missing", "not_found", False, "not_found"),
        ("MissingClass::test_decorated", "not_found", False, "not_found"),
        ("Other::test_orphan", "non_runnable_owner_method", False, "no_runnable_owner"),
        ("Concrete::test_shared", "runnable_test", True, ""),
    ],
)
def test_every_django_classification(name, category, valid, reason):
    record = index().classify(label(name))
    assert (record.category, record.valid, record.reason) == (category, valid, reason)


def test_mixin_expansion_is_transitive_and_excludes_overrides():
    record = index().classify(label("Base::test_shared"))
    assert record.expanded and record.valid
    assert record.runnable_ids == (label("Child::test_shared"), label("Concrete::test_shared"))
    assert label("Overrides::test_shared") not in record.runnable_ids
    assert record.to_dict()["expansion_count"] == 2


def test_inherited_selected_owner_does_not_expand_to_sibling_branches():
    source = """
import unittest
class Root:
 def test_one(self): pass
class Middle(Root): pass
class Left(Middle, unittest.TestCase): pass
class Right(Root, unittest.TestCase): pass
"""
    record = index(source=source).classify(label("Middle::test_one"))
    assert record.runnable_ids == (label("Left::test_one"),)


def test_multiple_inheritance_uses_effective_method_not_just_ancestry():
    source = """
from unittest import TestCase
class A:
 def test_a(self): pass
class B:
 def test_a(self): pass
class One(B, A, TestCase): pass
class Two(A, B, TestCase): pass
"""
    assert index(source=source).classify(label("A::test_a")).runnable_ids == (label("Two::test_a"),)


def test_import_aliases_relative_reexports_and_testcase_ancestry():
    sources = {
        "pkg/__init__.py": "from .base import Unit",
        "pkg/base.py": "from unittest.case import TestCase as Unit",
        "tests/test_sample.py": "from pkg import Unit as Imported\nclass Whatever(Imported):\n def test_a(self): pass",
    }
    record = StaticIndex(SourceTree(sources), "django").classify(label("Whatever::test_a"))
    assert record.valid and record.owner_is_testcase


@pytest.mark.parametrize(
    "name,valid",
    [
        ("TestNative::test_method", True),
        ("Tests::test_decorated", True),
        ("TestWithInit::test_method", False),
        ("TestHidden::test_method", True),
        ("test_function", True),
        ("test_wrapped", True),
    ],
)
def test_pytest_owner_and_function_semantics(name, valid):
    record = index("pytest").classify(label(name))
    # The hidden base has an explicit runnable subclass, so it expands to that.
    assert record.valid is valid
    if name == "TestHidden::test_method":
        assert record.expanded and record.runnable_ids == (label("TestVisibleChild::test_method"),)


@pytest.mark.parametrize(
    "config,text",
    [
        ("pytest.ini", "[pytest]\npython_classes = *Checks\n"),
        ("setup.cfg", "[tool:pytest]\npython_classes = *Checks\n"),
        ("tox.ini", "[pytest]\npython_classes = *Checks\n"),
        ("pyproject.toml", '[tool.pytest.ini_options]\npython_classes = ["*Checks"]\n'),
    ],
)
def test_effective_pytest_class_config(config, text):
    src = "class MathChecks:\n def test_a(self): pass\n"
    record = index("pytest", src, {config: text}).classify(label("MathChecks::test_a"))
    assert record.valid and not record.expanded


def test_pytest_config_precedence_and_inherited_init():
    src = (
        "class Base:\n def __init__(self): pass\nclass TestChild(Base):\n def test_a(self): pass\n"
    )
    assert not index("pytest", src).classify(label("TestChild::test_a")).valid
    src = "class MathChecks:\n def test_a(self): pass\n"
    record = index(
        "pytest", src, {"pytest.ini": "", "setup.cfg": "[tool:pytest]\npython_classes=*Checks"}
    ).classify(label("MathChecks::test_a"))
    assert not record.valid


def test_static_source_is_never_imported_or_executed(tmp_path):
    canary = tmp_path / "executed"
    src = f'open({str(canary)!r}, "w").write("bad")\nraise RuntimeError("import")\ndef test_a(): pass\n'
    assert index("pytest", src).classify(label("test_a")).valid
    assert not canary.exists()


def test_unparseable_and_missing_files_are_explicit():
    assert index(source="def test_a(:").classify(label("test_a")).reason == "source_parse_error"
    assert index().classify("gone.py::test_a").reason == "not_found"
    assert index().classify("../outside.py::test_a").reason == "not_found"


def test_native_failure_invalidates_original_expansion_and_preserves_members():
    original = index().classify(label("Base::test_shared"))
    a, b = original.runnable_ids
    merged = merge_native(
        (original,),
        {
            a: {"ids": [a], "completed": True},
            b: {"ids": [], "reason": "native_load_error", "message": "missing dependency"},
        },
    )[0]
    assert not merged.valid and merged.reason == "collection_error"
    assert merged.unavailable and merged.failure_status == "COLLECTION_ERROR"
    assert merged.runnable_ids == (a,)
    assert merged.invalid_instances == ((b, "native_load_error"),)
    assert "missing dependency" in merged.message
    assert merged.to_dict()["expansion_count"] == 2
    assert not ValidationPass((merged,)).runnable_ids


def test_native_cannot_add_a_different_family():
    selected = IDValidation("t.py::test_a", "runnable_test", ("t.py::test_a",))
    merged = merge_native((selected,), {"t.py::test_a": {"ids": ["t.py::test_b"]}})[0]
    assert merged.reason == "collection_error"
    assert merged.invalid_instances[0][1] == "native_identity_mismatch"


def test_native_is_authoritative_and_disagreement_is_recorded():
    selected = IDValidation("t.py::test_generated", "helper", reason="non_callable_attribute")
    merged = merge_native(
        (selected,), {"t.py::test_generated": {"ids": ["t.py::test_generated"], "completed": True}}
    )[0]
    assert merged.valid and merged.native_disagrees
    assert merged.static_reason == "non_callable_attribute"


def test_one_missing_expanded_instance_cannot_admit_original_slot():
    original = index().classify(label("Base::test_shared"))
    a, b = original.runnable_ids
    raw = RunResult(
        results=(TestResult(a, TestStatus.PASSED), TestResult(b, TestStatus.NOT_RUN)),
        raw_results=(TestResult(a, TestStatus.PASSED),),
        raw_id_map={a: (a,)},
        evidence_complete=True,
    )
    run = apply_validation(raw, ValidationPass((original,)))
    assert run.by_id()[original.selected_id].status is TestStatus.NOT_RUN
    assert run.validation[0]["admitted"] is False
    assert run.validation[0]["admitted_instances"] == 1
    assert completeness_of((original.selected_id,), run, run)[0] == "INCOMPLETE_CONFIRMED"


def test_overlapping_selected_families_share_only_authorized_concrete_instances():
    original = index().classify(label("Base::test_shared"))
    direct = index().classify(label("Concrete::test_shared"))
    ids = original.runnable_ids
    raw = RunResult(
        results=tuple(TestResult(t, TestStatus.PASSED) for t in ids),
        raw_results=tuple(TestResult(t, TestStatus.PASSED) for t in ids),
        raw_id_map={t: (t,) for t in ids},
        evidence_complete=True,
    )
    run = apply_validation(raw, ValidationPass((original, direct)))
    assert completeness_of((original.selected_id, direct.selected_id), run, run) == ("COMPLETE", ())
    assert run_from_dict(json.loads(json.dumps(run_to_dict(run)))) == run


def test_invalid_id_is_not_not_run_and_not_execution():
    tid = "t.py::test_missing"
    invalid = apply_validation(
        RunResult(evidence_complete=True),
        ValidationPass((IDValidation(tid, "not_found", reason="not_found"),)),
    )
    assert invalid.by_id()[tid].status is TestStatus.INVALID_ID
    assert classify(tid, invalid.by_id()[tid], invalid.by_id()[tid]) is Outcome.INVALID_ID
    assert not Outcome.INVALID_ID.executed

    class Executor:
        def run(self, *args, **kwargs):
            return invalid

    report = run_regression("task", Selection(tests=(tid,)), Executor())
    assert report.signal is Signal.NOT_AVAILABLE
    assert report.n_executed == 0


def native_project(tmp_path, runner, ids):
    request = tmp_path / "request.json"
    driver = tmp_path / "collect.py"
    django = tmp_path / "django.py"
    request.write_text(json.dumps({"runner": runner, "ids": ids, "module_timeout_s": 30}))
    django.write_text(_DJANGO_COLLECT)
    (tmp_path / "verifier_collect_plugin.py").write_text(_PYTEST_PLUGIN)
    code = _NATIVE_DRIVER.replace("/tmp/verifier_collect_request.json", str(request)).replace(
        "/tmp/verifier_django_collect.py", str(django)
    )
    driver.write_text(code)
    proc = subprocess.run(
        [sys.executable, str(driver)],
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(proc.stdout)


def test_real_pytest_collection_expands_parameters_without_executing(tmp_path):
    sentinel = tmp_path / "executed"
    (tmp_path / "test_sample.py").write_text(f"""
import pytest
@pytest.mark.parametrize('value', [1, 2])
def test_one(value):
 open({str(sentinel)!r}, 'w').write('bad')
 raise AssertionError('must not run')
""")
    data = native_project(
        tmp_path, "pytest", ["test_sample.py::test_one", "test_sample.py::missing"]
    )
    assert data["ids"]["test_sample.py::test_one"]["ids"] == [
        "test_sample.py::test_one[1]",
        "test_sample.py::test_one[2]",
    ]
    assert data["ids"]["test_sample.py::missing"]["reason"] == "native_not_found"
    assert data["tests_executed"] == 0 and not sentinel.exists()


def test_native_module_load_error_does_not_abort_other_module(tmp_path):
    (tmp_path / "test_bad.py").write_text('raise RuntimeError("load problem")\n')
    (tmp_path / "test_good.py").write_text('def test_one(): raise AssertionError("must not run")\n')
    data = native_project(tmp_path, "pytest", ["test_bad.py::test_a", "test_good.py::test_one"])
    assert data["ids"]["test_bad.py::test_a"]["reason"] == "collection_error"
    assert "load problem" in data["ids"]["test_bad.py::test_a"]["message"]
    assert data["ids"]["test_good.py::test_one"]["ids"] == ["test_good.py::test_one"]


def test_real_dry_unittest_load_never_calls_plain_function_or_test_body(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "runtests.py").write_text(
        "def setup(verbosity, test_labels, parallel, start_at, start_after): pass\n"
    )
    sentinel = tmp_path / "executed"
    (tests / "sample.py").write_text(f"""
import unittest
class Case(unittest.TestCase):
 def test_one(self):
  open({str(sentinel)!r}, 'w').write('bad')
 def helper(self): pass
def test_factory():
 open({str(sentinel)!r}, 'w').write('bad')
 return unittest.TestSuite()
""")
    data = native_project(
        tmp_path,
        "django",
        [
            "tests/sample.py::Case::test_one",
            "tests/sample.py::Case::missing",
            "tests/sample.py::test_factory",
        ],
    )
    assert data["ids"]["tests/sample.py::Case::test_one"]["ids"]
    assert data["ids"]["tests/sample.py::Case::missing"]["reason"] == "native_not_found"
    assert data["ids"]["tests/sample.py::test_factory"]["reason"] == "native_not_found"
    assert not sentinel.exists()


def test_unavailable_collection_adapter_never_falls_through_to_execution():
    class Container:
        def exec(self, *args, **kwargs):
            pytest.fail("must not start an unsupported runner")

    result = validate_in_container(Container(), ("x.py::test_a",), TestRunner("unsupported", ""))
    assert result.errors


def test_collection_programs_parse_on_python36():
    for program in (_NATIVE_DRIVER, _DJANGO_COLLECT):
        ast.parse(program, feature_version=(3, 6))


class ValidationContainer:
    def __init__(self, sources=None, native=None, raw=b"t.py::test_a PASSED\n"):
        self.sources = sources or {"t.py": "def test_a(): pass\n"}
        self.native = native or {
            "t.py::test_a": {"ids": ["t.py::test_a"]},
            "t.py::test_missing": {
                "ids": [],
                "reason": "native_not_found",
                "message": "not collected",
            },
        }
        for entry in self.native.values():
            entry.setdefault("completed", True)
        self.raw, self.calls, self.inputs = raw, [], {}

    def set_patched(self, patched):
        self.calls.append(("tree", patched))

    def exec(self, command, timeout_s=120):
        self.calls.append(command)
        if command.startswith("python -c "):
            return 0, json.dumps(self.sources)
        if command == "python /tmp/verifier_collect_driver.py":
            return 0, json.dumps({"ids": self.native, "groups": [], "tests_executed": 0})
        return 0, ""

    def exec_input(self, command, data, timeout_s=60):
        self.inputs[command] = data
        return 0, ""

    def exec_raw(self, command, timeout_s):
        self.calls.append(command)
        if command.startswith(("python /tmp/verifier_driver", "cat /tmp/verifier_out")):
            return 0, self.raw, b"", False
        if command.startswith("cat /tmp/verifier_events"):
            events = [
                {"event": "start", "batch": 1, "offset": 0},
                {"event": "end", "batch": 1, "offset": len(self.raw), "returncode": 0},
                {"event": "complete"},
            ]
            return 0, "\n".join(json.dumps(e) for e in events).encode(), b"", False
        return 0, b"", b"", False


def test_executor_validates_current_tree_before_execution_and_excludes_invalid(tmp_path):
    from reliability.verifier.container import ContainerTestExecutor

    container = ValidationContainer()
    result = ContainerTestExecutor(container, evidence_dir=tmp_path).run(
        ("t.py::test_a", "t.py::test_missing"), patched=True, timeout_s=30
    )
    assert container.calls[0] == ("tree", True)
    assert container.calls.index("python /tmp/verifier_collect_driver.py") < container.calls.index(
        "python /tmp/verifier_driver.py pytest"
    )
    assert result.by_id()["t.py::test_a"].status is TestStatus.PASSED
    assert result.by_id()["t.py::test_missing"].status is TestStatus.INVALID_ID
    assert container.inputs["cat > /tmp/verifier_ids"].strip() == "t.py::test_a"
    assert result.validation[1]["reason"] == "not_found"
    assert result.validation[1]["invalid_instances"] == [["t.py::test_missing", "native_not_found"]]
    assert list(tmp_path.rglob("validation.json"))


def test_all_invalid_labels_never_start_execution_driver():
    from reliability.verifier.container import ContainerTestExecutor

    container = ValidationContainer()
    result = ContainerTestExecutor(container).run(
        ("t.py::test_missing",), patched=False, timeout_s=30
    )
    assert result.results[0].status is TestStatus.INVALID_ID
    assert not any(
        isinstance(c, str) and c.startswith("python /tmp/verifier_driver.py")
        for c in container.calls
    )


def test_validation_infrastructure_error_cannot_turn_into_invalid_id():
    from reliability.verifier.container import ContainerTestExecutor

    class Broken(ValidationContainer):
        def exec(self, command, timeout_s=120):
            return 1, "snapshot unavailable"

    result = ContainerTestExecutor(Broken()).run(("t.py::test_a",), patched=False, timeout_s=30)
    assert result.results[0].status is TestStatus.COLLECTION_ERROR
    assert result.infrastructure_errors


def test_invalid_on_one_tree_is_excluded_without_admitting_a_new_family():
    valid_id, invalid_id = "t.py::test_a", "t.py::test_b"
    a = IDValidation(valid_id, "runnable_test", (valid_id,))
    invalid = IDValidation(invalid_id, "not_found", reason="not_found")
    good = IDValidation(invalid_id, "runnable_test", (invalid_id,))

    def paired(records):
        ids = ValidationPass(records).runnable_ids
        run = RunResult(
            results=tuple(TestResult(t, TestStatus.PASSED) for t in ids),
            raw_results=tuple(TestResult(t, TestStatus.PASSED) for t in ids),
            raw_id_map={t: (t,) for t in ids},
            evidence_complete=True,
        )
        return apply_validation(run, ValidationPass(records))

    base, patch = paired((a, invalid)), paired((a, good))
    assert completeness_of((valid_id, invalid_id), base, patch) == ("COMPLETE", ())

    class Executor:
        def run(self, tests, *, patched, timeout_s):
            return patch if patched else base

    report = run_regression("task", Selection(tests=(valid_id, invalid_id)), Executor())
    assert report.outcomes[invalid_id] is Outcome.INVALID_ID
    assert report.signal is Signal.PASS


def test_collection_receipt_ignores_pytest_output_verbosity(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -vv\n")
    (tmp_path / "test_one.py").write_text(
        'def test_a(): raise AssertionError("must not execute")\n'
    )
    data = native_project(tmp_path, "pytest", ["test_one.py::test_a"])
    assert data["ids"]["test_one.py::test_a"]["ids"] == ["test_one.py::test_a"]


def test_collection_timeout_remains_missing_evidence_instead_of_invalid_id():
    tid = "t.py::test_a"
    record = IDValidation(tid, "runnable_test", (tid,))
    merged = merge_native(
        (record,), {tid: {"ids": [], "reason": "collection_timeout", "message": "timed out"}}
    )[0]
    assert merged.unavailable and not merged.valid
    run = apply_validation(RunResult(evidence_complete=True), ValidationPass((merged,)))
    assert run.results[0].status is TestStatus.COLLECTION_ERROR
    assert ValidationPass((merged,)).to_dict()["invalid_slots"] == 0
    assert completeness_of((tid,), run, run)[0] == "INCOMPLETE_CONFIRMED"


def test_no_runnable_owner_reason_survives_native_rejection():
    tid = label("Other::test_orphan")
    record = index().classify(tid)
    merged = merge_native(
        (record,), {tid: {"ids": [], "reason": "native_load_error", "message": "not TestCase"}}
    )[0]
    assert merged.reason == "no_runnable_owner"
    assert merged.invalid_instances == ((tid, "native_load_error"),)


def test_patched_source_is_classified_independently():
    before = index().classify(label("Concrete::test_shared"))
    after = index(
        source=SOURCE.replace("class Concrete(Base, Case): pass", "class Concrete(Base): pass")
    ).classify(label("Concrete::test_shared"))
    assert before.valid
    assert not after.valid and after.reason == "no_runnable_owner"


def test_expanded_django_regression_keys_are_runnable_canonical_identities():
    selected = IDValidation(
        "tests/sample.py::Base::test_a",
        "non_runnable_owner_method",
        ("tests/sample.py::One::test_a", "tests/sample.py::Two::test_a"),
        expanded=True,
    )
    ids = selected.runnable_ids

    def make(status):
        raw_ids = ["sample.One.test_a", "sample.Two.test_a"]
        raw = RunResult(
            results=tuple(TestResult(t, status) for t in ids),
            raw_results=tuple(TestResult(t, status) for t in raw_ids),
            raw_id_map=dict(zip(raw_ids, [(t,) for t in ids])),
            evidence_complete=True,
        )
        return apply_validation(raw, ValidationPass((selected,)))

    base = make(TestStatus.PASSED)

    class Executor:
        def run(self, tests, *, patched: bool, timeout_s):
            if patched:
                assert all("::" in t for t in tests)
            return make(TestStatus.FAILED) if patched else base

    report = run_regression("task", Selection(tests=(selected.selected_id,)), Executor())
    assert report.signal is Signal.FAIL
    assert report.regressions == tuple(sorted(ids))


def test_pytest_hidden_testcase_owner_does_not_ignore_test_false():
    src = "import unittest\nclass Hidden(unittest.TestCase):\n __test__=False\n def test_a(self): pass\n"
    record = index("pytest", src).classify(label("Hidden::test_a"))
    assert not record.valid and record.reason == "no_runnable_owner"


def test_ast_cache_cannot_reuse_an_old_tree_after_source_changes():
    cache = {}
    first = SourceTree({"tests/test_sample.py": "def test_a(): pass\n"})
    second = SourceTree({"tests/test_sample.py": "value = 1\n"})
    assert StaticIndex(first, "pytest", parse_cache=cache).classify(label("test_a")).valid
    assert not StaticIndex(second, "pytest", parse_cache=cache).classify(label("test_a")).valid


def test_native_collection_normalizes_nested_config_root_nodeids(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "pytest.ini").write_text("[pytest]\n")
    (package / "test_one.py").write_text('def test_a(): raise AssertionError("must not execute")\n')
    data = native_project(tmp_path, "pytest", ["package/test_one.py::test_a"])
    assert data["ids"]["package/test_one.py::test_a"]["ids"] == ["package/test_one.py::test_a"]
