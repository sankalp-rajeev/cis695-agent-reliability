"""Exact selected-family guard around SymPy's native bin/test runner."""

# Runs in task images, including Python 3.6. The native test_file implementation
# performs collection; matches(False) prevents test calls during collection.
_SYMPY_PROGRAM = r'''
import contextlib, importlib, inspect, io, json, os, re, runpy, sys, traceback
mode, module = sys.argv[1:3]
request = json.load(sys.stdin) if mode == "collect" else {"ids": sys.argv[3:]}
identities = request["ids"]
wanted = set(t.split("::", 1)[1] for t in identities if t.startswith(module + "::") and len(t.split("::")) == 2)
os.environ["SYMPY_USE_CACHE"] = "no"
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.abspath("bin"))
stream = io.StringIO()

def failure(message):
    return "RUNNER_UNAVAILABLE" if re.search(r"No module named [\"']?sympy(?:[\"'\s]|$)|(?:can't open file|No such file)[^\n]*bin/test", message) else "COLLECTION_ERROR"

def prepare():
    name = "sympy.testing.runtests" if os.path.isfile("sympy/testing/runtests.py") else "sympy.utilities.runtests"
    native = importlib.import_module(name)
    original_generator = inspect.isgeneratorfunction
    original_files = native.SymPyTests.get_test_files
    target = os.path.abspath(module)
    errors, found = [], []
    def guard_generator(function):
        # Do not execute an unselected generator while the native collector
        # expands generator factories, before its matches() filter runs.
        if original_generator(function) and function.__name__ in wanted:
            raise RuntimeError("Selected generator has no verified concrete identities: " + function.__name__)
        return False
    def matches(instance, function):
        # Native expansion has finished before matches() is called. Restore
        # inspect semantics before any test body can run.
        inspect.isgeneratorfunction = original_generator
        if original_generator(function):
            if function.__name__ in wanted:
                errors.append("Selected generator has no verified concrete identities: " + function.__name__)
            return False
        if mode == "collect":
            found.append(module + "::" + function.__name__)
            return False
        return function.__name__ in wanted
    def files(instance, directory, *args, **kwargs):
        available = original_files(instance, directory, *args, **kwargs)
        return [path for path in available if os.path.abspath(path) == target]
    native.SymPyTests.matches = matches
    native.SymPyTests.get_test_files = files
    inspect.isgeneratorfunction = guard_generator
    return native, found, errors, original_generator

if mode == "collect":
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            native, found, errors, original_generator = prepare()
            class Reporter:
                def root_dir(self, root):
                    pass
                def entering_test(self, function):
                    raise RuntimeError("Collection attempted test execution")
                def test_exception(self, exc_info):
                    errors.append("".join(traceback.format_exception(*exc_info)))
                def import_error(self, filename, exc_info):
                    errors.append("".join(traceback.format_exception(*exc_info)))
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            collector = native.SymPyTests(Reporter(), kw=())
            if any(os.path.abspath(p) == os.path.abspath(module) for p in collector.get_test_files('sympy')):
                collector.test_file(os.path.abspath(module))
            inspect.isgeneratorfunction = original_generator
            if errors:
                raise RuntimeError("\n".join(errors))
        result = {t: dict(ids=[t] if t in found else [], reason="" if t in found else "native_not_found",
                         completed=True, collection_status="COMPLETE", returncode=0,
                         message=stream.getvalue() if t not in found else "") for t in identities}
    except BaseException:
        message = stream.getvalue() + traceback.format_exc()
        status = failure(message)
        result = {t: dict(ids=[], reason=status.lower(), message=message,
                         completed=False, collection_status=status, returncode=0) for t in identities}
    print(json.dumps(dict(ids=result, tests_executed=0)))
else:
    native, found, errors, original_generator = prepare()
    # -C must apply before the initial sympy import; it is set above as well.
    # Keep the exact-selection guard in this one module process rather than
    # losing it to the native hash-randomization re-exec subprocess.
    sys.argv = ["bin/test", "-C", "--verbose", "--no-subprocess", module]
    runpy.run_path("bin/test", run_name="__main__")
'''
