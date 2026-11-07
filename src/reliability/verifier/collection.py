"""Container collection receipts. Neither layer invokes a test or a test suite."""

from __future__ import annotations

import json
import shlex
import time
from dataclasses import dataclass, field

from reliability.verifier.id_validation import IDValidation, SourceTree, StaticIndex, merge_native

# These programs run in historical task images, including Python 3.6.
_SOURCE_SNAPSHOT = r"""
import json, pathlib, subprocess
files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).decode().split("\0")
sources = {}
for name in files:
    path = pathlib.Path(name)
    if (name.endswith(".py") or path.name in ("setup.cfg", "tox.ini", "pytest.ini", ".pytest.ini", "pyproject.toml")) and path.is_file():
        sources[name] = path.read_text(encoding="utf-8", errors="replace")
print(json.dumps(sources))
"""

_DJANGO_COLLECT = r"""
import contextlib, importlib.util, inspect, io, json, os, sys, traceback, unittest
request = json.load(sys.stdin)
labels = request["labels"]
results = {}
capture = io.StringIO()
try:
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        sys.path.insert(0, os.path.abspath("tests"))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_sqlite")
        spec = importlib.util.spec_from_file_location("runtests", "tests/runtests.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        values = dict(verbosity=0, test_labels=labels, parallel=1, start_at=None, start_after=None)
        params = inspect.signature(module.setup).parameters
        module.setup(**dict((k, v) for k, v in values.items() if k in params))
except BaseException:
    message = capture.getvalue() + traceback.format_exc()
    for label in labels:
        results[label] = dict(ids=[], reason="native_load_error", message=message)
else:
    for label in labels:
        stream = io.StringIO()
        try:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                # Check the owner before calling unittest's loader, which otherwise
                # invokes a plain function in an attempt to create a test suite.
                bits = label.split(".")
                loaded = None
                for stop in range(len(bits) - 1, 0, -1):
                    try:
                        loaded = __import__(".".join(bits[:stop]), fromlist=["*"])
                        rest = bits[stop:]
                        break
                    except ImportError:
                        continue
                if loaded is None:
                    raise ImportError("No module for selected label: " + label)
                owner = loaded
                for bit in rest[:-1]:
                    owner = getattr(owner, bit)
                if not inspect.isclass(owner) or not issubclass(owner, unittest.TestCase):
                    raise TypeError("Selected owner is not unittest.TestCase: " + label)
                method = getattr(owner, rest[-1])
                if not callable(method):
                    raise TypeError("Selected member is not callable: " + label)
                loader = unittest.TestLoader()
                if not rest[-1].startswith(loader.testMethodPrefix):
                    raise LookupError("Selected member is a helper, not a test method: " + label)
                suite = loader.loadTestsFromName(label)
                def cases(value):
                    if isinstance(value, unittest.TestSuite):
                        for child in value:
                            for item in cases(child):
                                yield item
                    else:
                        yield value
                found = list(cases(suite))
                failures = [getattr(case, "_exception", None) for case in found
                            if case.__class__.__name__ == "_FailedTest"]
                if loader.errors or failures:
                    raise RuntimeError("\n".join(loader.errors + [str(e) for e in failures]))
                if not found:
                    raise LookupError("No test cases loaded for " + label)
                if any(not isinstance(case, unittest.TestCase) for case in found):
                    raise TypeError("Loader returned non-TestCase object")
            results[label] = dict(ids=[label], reason="", message=stream.getvalue())
        except BaseException as exc:
            results[label] = dict(ids=[], reason="native_not_found" if isinstance(exc, (AttributeError, LookupError)) else "native_load_error",
                                  message=stream.getvalue() + traceback.format_exc())
print(json.dumps(results))
"""

_PYTEST_PLUGIN = r"""
import json, os

def pytest_collection_finish(session):
    with open(os.environ["VERIFIER_COLLECTION_RECEIPT"], "w") as stream:
        identities = []
        for item in session.items:
            parts = item.nodeid.split("::", 1)
            path = os.path.relpath(str(item.fspath), os.getcwd())
            identities.append(path + ("::" + parts[1] if len(parts) == 2 else ""))
        json.dump(identities, stream)
"""


_NATIVE_DRIVER = r"""
import json, os, pathlib, subprocess, sys, time, traceback
request = json.loads(pathlib.Path("/tmp/verifier_collect_request.json").read_text())
kind = request["runner"]
groups = {}
for identity in request["ids"]:
    groups.setdefault(identity.split("::", 1)[0], []).append(identity)
result, groups_log = {}, []
for module, identities in sorted(groups.items()):
    start = time.monotonic()
    try:
        if kind == "django":
            labels = {}
            for identity in identities:
                parts = identity.split("::")
                name = parts[0][:-3].replace("/", ".")
                if name.startswith("tests."):
                    name = name[6:]
                labels[identity] = ".".join([name] + parts[1:])
            proc = subprocess.run([sys.executable, "/tmp/verifier_django_collect.py"],
                                  input=json.dumps(dict(labels=list(labels.values()))).encode(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=request["module_timeout_s"])
            if proc.returncode:
                raise RuntimeError((proc.stdout + proc.stderr).decode("utf-8", "replace"))
            native = json.loads(proc.stdout.decode("utf-8", "replace"))
            for identity, label in labels.items():
                observed = native.get(label, dict(ids=[], reason="native_not_found", message="Missing loader receipt"))
                # Keep canonical node IDs for comparison and original-family mapping.
                if observed["ids"]:
                    observed["ids"] = [identity]
                result[identity] = observed
            command = [sys.executable, "/tmp/verifier_django_collect.py"]
        else:
            command = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-p", "verifier_collect_plugin", module]
            receipt = os.path.join(os.path.dirname(__file__), "verifier_collection_nodes.json")
            if os.path.exists(receipt):
                os.unlink(receipt)
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.path.dirname(__file__) + os.pathsep + environment.get("PYTHONPATH", "")
            environment["VERIFIER_COLLECTION_RECEIPT"] = receipt
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=request["module_timeout_s"], env=environment)
            stdout = proc.stdout.decode("utf-8", "replace")
            message = stdout + proc.stderr.decode("utf-8", "replace")
            collected = json.loads(pathlib.Path(receipt).read_text()) if os.path.exists(receipt) else []
            for identity in identities:
                ids = [node for node in collected if node == identity or
                       ("[" not in identity and node.startswith(identity + "["))]
                error = proc.returncode not in (0, 5)
                result[identity] = dict(ids=[] if error else ids,
                    reason="native_load_error" if error else "" if ids else "native_not_found",
                    message=message if error or not ids else "")
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start,
                               returncode=proc.returncode, command=command))
    except subprocess.TimeoutExpired:
        message = traceback.format_exc()
        for identity in identities:
            result[identity] = dict(ids=[], reason="collection_timeout", message=message)
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start, error=message))
    except BaseException:
        message = traceback.format_exc()
        for identity in identities:
            result[identity] = dict(ids=[], reason="native_load_error", message=message)
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start, error=message))
print(json.dumps(dict(ids=result, groups=groups_log, tests_executed=0)))
"""


@dataclass(frozen=True)
class ValidationPass:
    records: tuple[IDValidation, ...] = ()
    errors: tuple[str, ...] = ()
    duration_s: float = 0.0
    groups: tuple[dict, ...] = ()
    context: dict = field(default_factory=dict)
    evidence_files: dict = field(default_factory=dict)
    evidence_sha256: dict = field(default_factory=dict)

    @property
    def runnable_ids(self):
        # An original slot is executed only when all its expansion members validate.
        return tuple(
            dict.fromkeys(t for item in self.records if item.valid for t in item.runnable_ids)
        )

    def to_dict(self):
        return {
            "context": self.context,
            "records": [r.to_dict() for r in self.records],
            "errors": list(self.errors),
            "duration_s": self.duration_s,
            "groups": list(self.groups),
            "selected_slots": len(self.records),
            "invalid_slots": sum(bool(r.reason) and not r.unavailable for r in self.records),
            "unavailable_slots": sum(r.unavailable for r in self.records),
            "expanded_slots": sum(r.expanded for r in self.records),
            "expanded_instances": sum(
                len(r.owner_instances or r.runnable_ids) for r in self.records if r.expanded
            ),
            "runnable_instances": len(self.runnable_ids),
        }


def validate_in_container(container, tests, runner, *, timeout_s=300):
    """Snapshot the current (already base/patched) tree, then collect valid identities."""
    started = time.monotonic()
    if runner.name not in ("pytest", "django"):
        return ValidationPass(errors=("No collection-only adapter for runner: " + runner.name,))
    try:
        command = "python -c " + shlex.quote(_SOURCE_SNAPSHOT)
        rc, raw = container.exec(command, timeout_s=120)
        if rc:
            raise RuntimeError("source snapshot failed: " + raw[-2000:])
        static = StaticIndex(SourceTree(json.loads(raw)), runner.name).validate(tests)
        ids = tuple(
            dict.fromkeys(
                t for r in static for t in (r.runnable_ids if r.valid else (r.selected_id,))
            )
        )
        if not ids:
            return ValidationPass(static, duration_s=time.monotonic() - started)
        payload = json.dumps(
            {"runner": runner.name, "ids": ids, "module_timeout_s": min(timeout_s, 120)}
        )
        for path, data in (
            ("/tmp/verifier_collect_request.json", payload),
            ("/tmp/verifier_collect_driver.py", _NATIVE_DRIVER),
            ("/tmp/verifier_django_collect.py", _DJANGO_COLLECT),
            ("/tmp/verifier_collect_plugin.py", _PYTEST_PLUGIN),
        ):
            rc, message = container.exec_input("cat > " + path, data, timeout_s=60)
            if rc:
                raise RuntimeError("collector upload failed: " + message[-2000:])
        rc, raw = container.exec("python /tmp/verifier_collect_driver.py", timeout_s=timeout_s)
        if rc:
            raise RuntimeError("collector driver failed: " + raw[-2000:])
        receipt = json.loads(raw)
        if receipt.get("tests_executed") != 0:
            raise RuntimeError("collection receipt missing zero-execution assertion")
        merged = merge_native(static, receipt["ids"])
        return ValidationPass(
            merged, duration_s=time.monotonic() - started, groups=tuple(receipt["groups"])
        )
    except (TimeoutError, RuntimeError, ValueError, OSError) as exc:
        return ValidationPass(errors=(str(exc),), duration_s=time.monotonic() - started)
