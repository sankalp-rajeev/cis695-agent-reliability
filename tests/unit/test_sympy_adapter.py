"""Native SymPy collection/execution selection and verbose terminal identities."""

import ast
import json
import subprocess
import sys

import pytest

from reliability.env import clean_env
from reliability.verifier.container import _BATCH_DRIVER, run_from_capture
from reliability.verifier.id_validation import SourceTree
from reliability.verifier.regression import TestStatus
from reliability.verifier.result_parser import parse_capture
from reliability.verifier.selection import TestRunner, discover_runner
from reliability.verifier.sympy_adapter import _SYMPY_PROGRAM


@pytest.mark.parametrize(
    "tail,status",
    [
        ("ok", "passed"),
        ("f", "xfail"),
        ("X", "xpass"),
        ("F", "failed"),
        ("E", "error"),
        (" - s", "skipped"),
        ("Slow w", "skipped"),
        ("KeyboardInterrupt K", "skipped"),
        ("Timeout T", "timeout"),
    ],
)
def test_every_sympy_verbose_status_is_distinct(tail, status):
    parsed = parse_capture(
        "sympy/core/tests/test_basic.py[1]\ntest_case " + tail + " [OK]\n", "sympy"
    )
    assert parsed["sympy/core/tests/test_basic.py::test_case"]["status"] == status


def test_sympy_parser_handles_ansi_multiline_and_does_not_parse_summary():
    raw = """sympy/core/tests/test_a.py[2]
test_one
warning from module
\x1b[32mok\x1b[0m
test_two f [OK]
================ tests finished: 1 passed, 1 expected to fail ================
test_fake ok
"""
    parsed = parse_capture(raw, "sympy")
    assert set(parsed) == {
        "sympy/core/tests/test_a.py::test_one",
        "sympy/core/tests/test_a.py::test_two",
    }
    assert parsed["sympy/core/tests/test_a.py::test_one"]["status"] == "passed"
    assert parsed["sympy/core/tests/test_a.py::test_two"]["flavor"] == "XFAIL"


def test_sympy_import_failure_never_invents_case_outcomes():
    assert parse_capture("sympy/tests/test_bad.py[?] Failed to import [FAIL]\n", "sympy") == {}


def test_sympy_error_after_pass_is_not_silently_downgraded():
    parsed = parse_capture("sympy/tests/test_a.py[1]\ntest_a ok\nE\n", "sympy")
    assert parsed["sympy/tests/test_a.py::test_a"]["status"] == "error"


def test_native_sympy_runner_precedes_pytest_configuration():
    tree = SourceTree({"bin/test": "", "sympy/__init__.py": "", "pytest.ini": "[pytest]"})
    assert discover_runner(tree).name == "sympy"


FRAMEWORK = """
import glob,inspect,os
class SymPyTests:
 def __init__(self, reporter, kw=()):
  self._reporter=reporter
  reporter.root_dir(os.getcwd())
 def get_test_files(self, directory):
  return glob.glob(os.path.join(os.getcwd(),directory,'tests','test_*.py'))
 def matches(self,function): return 'test_one' in function.__name__
 def test_file(self,filename):
  gl={'__file__':filename}
  try: exec(compile(open(filename).read(),filename,'exec'),gl)
  except ImportError:
   import sys
   self._reporter.import_error(filename,sys.exc_info());return
  functions=[fn for name,fn in gl.items() if name.startswith('test_') and inspect.isfunction(fn)]
  expanded=[]
  for fn in functions:
   if inspect.isgeneratorfunction(fn):
    expanded.extend(fn())
   else: expanded.append(fn)
  functions=[fn for fn in expanded if self.matches(fn)]
  if not functions:return
  self._reporter.entering_filename(filename,len(functions))
  for fn in functions:
   self._reporter.entering_test(fn)
   fn()
   self._reporter.test_pass()
"""


def fake_repo(tmp_path):
    package = tmp_path / "sympy"
    package.mkdir()
    (package / "__init__.py").write_text("")
    testing = package / "testing"
    testing.mkdir()
    (testing / "__init__.py").write_text("")
    (testing / "runtests.py").write_text(FRAMEWORK)
    tests = package / "tests"
    tests.mkdir()
    bin = tmp_path / "bin"
    bin.mkdir()
    (bin / "test").write_text("""import os,sys
from sympy.testing.runtests import SymPyTests
assert '-C' in sys.argv and '--verbose' in sys.argv and '--no-subprocess' in sys.argv
assert os.environ['SYMPY_USE_CACHE']=='no'
assert os.environ['PYTHONWARNINGS']=='ignore::UserWarning,ignore::SyntaxWarning'
import warnings
with warnings.catch_warnings(record=True) as emitted:
 warnings.warn('ignored user',UserWarning)
 warnings.warn('ignored syntax',SyntaxWarning)
 assert not emitted
class Reporter:
 def root_dir(self,root):self.root=root
 def entering_filename(self,path,n):print(os.path.relpath(path,self.root)+'['+str(n)+']')
 def entering_test(self,fn):print(fn.__name__+' ',end='')
 def test_pass(self):print('ok')
r=Reporter();t=SymPyTests(r)
for file in t.get_test_files('sympy'):t.test_file(file)
""")
    selected = tests / "test_sample.py"
    canary = tmp_path / "executed.txt"
    selected.write_text(f"""import inspect

def test_one():
 def helper_generator():
  yield 1
 assert inspect.isgeneratorfunction(helper_generator)
 open({str(canary)!r},'a').write('one\\n')

def test_one_extra():
 raise AssertionError('unselected substring family executed')

def test_unselected_generator():
 raise AssertionError('unselected generator body executed')
 yield 1
""")
    # The native CLI's file substring matching must not broaden module scope.
    (tests / "test_sample.py_extra.py").write_text(
        'raise AssertionError("unselected module loaded")\n'
    )
    program = tmp_path / "adapter.py"
    program.write_text(_SYMPY_PROGRAM)
    return program, canary


def test_native_sympy_collection_never_calls_test_or_generator_bodies(tmp_path):
    program, canary = fake_repo(tmp_path)
    module = "sympy/tests/test_sample.py"
    ids = [module + "::test_one", module + "::missing"]
    proc = subprocess.run(
        [sys.executable, str(program), "collect", module],
        input=json.dumps({"ids": ids}),
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    receipt = json.loads(proc.stdout)
    assert receipt["ids"][ids[0]]["ids"] == [ids[0]]
    assert receipt["ids"][ids[1]]["ids"] == []
    assert receipt["ids"][ids[1]]["completed"] is True
    assert not canary.exists()


def test_native_sympy_execution_uses_exact_names_not_substrings(tmp_path):
    program, canary = fake_repo(tmp_path)
    module = "sympy/tests/test_sample.py"
    tid = module + "::test_one"
    proc = subprocess.run(
        [sys.executable, str(program), "execute", module, tid],
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert canary.read_text() == "one\n"
    parsed = parse_capture(proc.stdout, "sympy")
    assert set(parsed) == {tid} and parsed[tid]["status"] == "passed"
    run = run_from_capture(TestRunner("sympy", ""), (tid,), runner_log=proc.stdout.encode())
    assert run.results[0].status is TestStatus.PASSED


def test_selected_sympy_generator_is_missing_not_executed_or_invalid(tmp_path):
    program, canary = fake_repo(tmp_path)
    module = "sympy/tests/test_sample.py"
    tid = module + "::test_unselected_generator"
    proc = subprocess.run(
        [sys.executable, str(program), "collect", module],
        input=json.dumps({"ids": [tid]}),
        cwd=tmp_path,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    receipt = json.loads(proc.stdout)["ids"][tid]
    assert receipt["collection_status"] == "COLLECTION_ERROR" and receipt["completed"] is False
    assert not canary.exists()


def test_sympy_program_and_shared_parser_work_in_python36():
    ast.parse(_SYMPY_PROGRAM, feature_version=(3, 6))
    ast.parse(_BATCH_DRIVER, feature_version=(3, 6))


def test_pre_sympy_baseline_cache_cannot_mix_with_native_adapter(tmp_path):
    from reliability.verifier.regression import RegressionConfig, load_cached_baseline

    config = RegressionConfig(baseline_cache_dir=tmp_path)
    (tmp_path / "task.baseline.json").write_text(
        json.dumps(
            {
                "parser_revision": "native-capture-v4-collection-guard",
                "results": [{"test_id": "sympy/tests/test_a.py::test_a", "status": "passed"}],
            }
        )
    )
    assert load_cached_baseline(config, "task") is None
