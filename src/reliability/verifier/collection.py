"""Container collection receipts. Neither layer invokes a test or a test suite."""

from __future__ import annotations

import json
import shlex
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

from reliability.verifier.id_validation import (
    IDValidation,
    SourceTree,
    StaticIndex,
    merge_native,
)
from reliability.verifier.run_health import allowed_failure, exception_rules
from reliability.verifier.selection import TestRunner
from reliability.verifier.sympy_adapter import _SYMPY_PROGRAM

# These programs run in historical task images, including Python 3.6.
_SOURCE_SNAPSHOT = r"""
import json, pathlib, subprocess
files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).decode().split("\0")
sources = {}
for name in files:
    path = pathlib.Path(name)
    if (name.endswith(".py") or path.name in ("setup.cfg", "tox.ini", "pytest.ini", ".pytest.ini", "pyproject.toml") or name == "bin/test") and path.is_file():
        sources[name] = path.read_text(encoding="utf-8", errors="replace")
print(json.dumps(sources))
"""

_UNAVAILABLE_PATTERN = r"No module named [\"']?(?:pytest|_pytest|django|sympy)(?:[\"'\s]|$)|python[^\n]*(?:command not found|not found)|(?:can't open file|No such file)[^\n]*(?:bin/test|tests/runtests\.py)"


def classify_collector_failure(message):
    import re

    return "RUNNER_UNAVAILABLE" if re.search(_UNAVAILABLE_PATTERN, message) else "COLLECTION_ERROR"


_FAILURE_HELPER = (
    "import re\ndef failure_status(message):\n    return 'RUNNER_UNAVAILABLE' if re.search("
    + repr(_UNAVAILABLE_PATTERN)
    + ", message) else 'COLLECTION_ERROR'\n"
)

DJANGO_SETUP_NAMES = ('setup', 'setup_run_tests')


def django_setup_entry_point(names):
    """Choose from the checked-out runner API, not a dataset version guess."""
    for name in DJANGO_SETUP_NAMES:
        if name in names:
            return name
    raise ValueError('Unsupported Django runtests setup API: expected setup or setup_run_tests')


_DJANGO_COLLECT = (
    _FAILURE_HELPER
    + 'DJANGO_SETUP_NAMES = ' + repr(DJANGO_SETUP_NAMES) + '\n'
    + r"""
import contextlib, importlib, importlib.util, inspect, io, json, os, sys, traceback, unittest
request = json.load(sys.stdin)
labels, module_name = request["labels"], request["module"]
results = {}
capture = io.StringIO()
setup_entry_point = None
try:
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        sys.path.insert(0, os.path.abspath("tests"))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_sqlite")
        spec = importlib.util.spec_from_file_location("runtests", "tests/runtests.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        values = dict(verbosity=0, test_labels=labels, parallel=1, start_at=None, start_after=None)
        setup_entry_point = next((name for name in DJANGO_SETUP_NAMES
                                  if callable(getattr(runner, name, None))), None)
        if setup_entry_point is None:
            raise RuntimeError('Unsupported Django runtests setup API: expected setup or setup_run_tests')
        setup = getattr(runner, setup_entry_point)
        params = inspect.signature(setup).parameters
        unsupported = [name for name, p in params.items()
            if p.kind == inspect.Parameter.POSITIONAL_ONLY or
            (p.default == inspect.Parameter.empty and
             p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
             and name not in values)]
        if unsupported:
            raise RuntimeError('Unsupported Django setup parameters for ' + setup_entry_point + ': ' + ', '.join(unsupported))
        setup(**dict((k, v) for k, v in values.items() if k in params))
        # Import failure is never evidence that a selected attribute is absent.
        module = importlib.import_module(module_name)
except unittest.SkipTest as exc:
    reason = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', str(exc)).strip()
    for label in labels:
        results[label] = dict(ids=[], reason='' if reason else 'collection_error', message=capture.getvalue(),
            module_skip_reason=reason, collection_status='MODULE_SKIPPED' if reason else 'COLLECTION_ERROR',
            completed=bool(reason), returncode=0)
except BaseException:
    message = capture.getvalue() + traceback.format_exc()
    status = failure_status(message)
    for label in labels:
        results[label] = dict(ids=[], reason=status.lower(), message=message,
                              collection_status=status, completed=False, returncode=0)
else:
    class Absent(Exception):
        pass
    for label in labels:
        stream = io.StringIO()
        try:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                if not label.startswith(module_name + "."):
                    raise Absent("Label is outside its containing module")
                rest = label[len(module_name)+1:].split(".")
                owner = module
                for bit in rest[:-1]:
                    owner = getattr(owner, bit)
                if not inspect.isclass(owner) or not issubclass(owner, unittest.TestCase):
                    raise Absent("Selected owner is not unittest.TestCase: " + label)
                method = getattr(owner, rest[-1])
                if not callable(method):
                    raise Absent("Selected member is not callable: " + label)
                loader = unittest.TestLoader()
                if not rest[-1].startswith(loader.testMethodPrefix):
                    raise Absent("Selected member is a helper: " + label)
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
                    raise Absent("No cases loaded for " + label)
                if any(not isinstance(case, unittest.TestCase) for case in found):
                    raise RuntimeError("Loader returned non-TestCase object")
            results[label] = dict(ids=[label], reason="", message=stream.getvalue(),
                                  collection_status="COMPLETE", completed=True, returncode=0)
        except (Absent, AttributeError):
            results[label] = dict(ids=[], reason="native_not_found",
                message=stream.getvalue() + traceback.format_exc(),
                collection_status="COMPLETE", completed=True, returncode=0)
        except BaseException:
            message = stream.getvalue() + traceback.format_exc()
            status = failure_status(message)
            results[label] = dict(ids=[], reason=status.lower(), message=message,
                collection_status=status, completed=False, returncode=0)
for value in results.values():
    value['setup_entry_point'] = setup_entry_point
print(json.dumps(results))
"""
)

_NODE_IDS = Path(__file__).with_name("node_ids.py").read_text()

_PYTEST_PLUGIN = _NODE_IDS + r"""
import json, os, pytest
_module_skips, _collection_errors, _collected_modules = [], [], []

def pytest_collectstart(collector):
    if isinstance(collector, pytest.Module):
        _collected_modules.append(os.path.relpath(str(collector.fspath), os.getcwd()))

def pytest_collectreport(report):
    if report.skipped:
        location = report.longrepr
        if isinstance(location, tuple) and len(location) == 3:
            _module_skips.append(dict(nodeid=report.nodeid, path=str(location[0]),
                line=location[1], reason=str(location[2]), when='collect'))
    elif report.failed:
        _collection_errors.append(dict(nodeid=report.nodeid, message=str(report.longrepr)))

def pytest_collection_finish(session):
    with open(os.environ["VERIFIER_COLLECTION_RECEIPT"], "w") as stream:
        identities = []
        for item in session.items:
            parts = item.nodeid.split("::", 1)
            path = os.path.relpath(str(item.fspath), os.getcwd())
            identities.append(normalize_pytest_id(path + ("::" + parts[1] if len(parts) == 2 else "")))
        json.dump(dict(ids=identities, module_skips=_module_skips, collection_errors=_collection_errors, collected_modules=_collected_modules), stream)
"""


_NATIVE_DRIVER = (
    _FAILURE_HELPER
    + _NODE_IDS
    + Path(__file__).with_name('module_skips.py').read_text()
    + r"""
import json, os, pathlib, subprocess, sys, time, traceback
request = json.loads(pathlib.Path("/tmp/verifier_collect_request.json").read_text())
kind = request["runner"]
try:
    os.setsid()
except OSError:
    pass
pathlib.Path("/tmp/verifier_collect_pgid").write_text(str(os.getpgrp()))
groups = {}
for identity in request["ids"]:
    groups.setdefault(identity.split("::", 1)[0], []).append(identity)
result, groups_log, directory_cache = {}, [], {}
started = time.monotonic()
deadline = started + request.get("budget_s", 1800)
prior_elapsed = request.get("prior_elapsed_s", 0.0)
def save():
    # A timeout must not discard previously completed module collections.
    target = pathlib.Path("/tmp/verifier_collect_partial.json")
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(dict(ids=result, groups=groups_log, tests_executed=0)))
    temporary.replace(str(target))
for module, identities in sorted(groups.items()):
    start = time.monotonic()
    directory_evidence = {}
    if start >= deadline:
        for identity in identities:
            result[identity] = dict(ids=[], reason="not_reached", message="per-pass budget exhausted before collection",
                collection_status="NOT_REACHED", completed=False, elapsed_s=prior_elapsed+start-started)
        save()
        continue
    module_timeout = max(0.001, min(request["module_timeout_s"], deadline-start))
    try:
        if kind == "sympy":
            command = [sys.executable, "/tmp/verifier_sympy_driver.py", "collect", module]
            proc = subprocess.run(command, input=json.dumps(dict(ids=identities)).encode(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=module_timeout)
            if proc.returncode:
                raise RuntimeError((proc.stdout + proc.stderr).decode("utf-8", "replace"))
            receipt = json.loads(proc.stdout.decode("utf-8", "replace"))
            result.update(receipt["ids"])
        elif kind == "django":
            labels = {}
            for identity in identities:
                parts = identity.split("::")
                name = parts[0][:-3].replace("/", ".")
                if name.startswith("tests."):
                    name = name[6:]
                labels[identity] = ".".join([name] + parts[1:])
            proc = subprocess.run([sys.executable, "/tmp/verifier_django_collect.py"],
                                  input=json.dumps(dict(labels=list(labels.values()), module=name)).encode(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=module_timeout)
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
            command = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-rs", "-p", "no:cacheprovider", "-p", "verifier_collect_plugin", "--", module]
            receipt = os.path.join(os.path.dirname(__file__), "verifier_collection_nodes.json")
            if os.path.exists(receipt):
                os.unlink(receipt)
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.path.dirname(__file__) + os.pathsep + environment.get("PYTHONPATH", "")
            environment["VERIFIER_COLLECTION_RECEIPT"] = receipt
            directory_probe = module in request.get('directory_check_modules', ())
            reuse_directory = False
            if directory_probe:
                directory = os.path.dirname(module) or '.'
                command[-1] = directory
                if directory not in directory_cache:
                    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          timeout=module_timeout, env=environment)
                    message = (proc.stdout + proc.stderr).decode('utf-8', 'replace')
                    payload = json.loads(pathlib.Path(receipt).read_text()) if os.path.exists(receipt) else {}
                    directory_cache[directory] = (proc.returncode, message, payload)
                returncode, message, payload = directory_cache[directory]
                collected = payload.get('ids', [])
                skip = pytest_module_skip(module, [n for n in collected if n.split('::',1)[0] == module], payload.get('module_skips', []), message,
                                          returncode, payload.get('collection_errors', ()))
                recognized = module in payload.get('collected_modules', []) or any(n.split('::',1)[0] == module for n in collected)
                directory_evidence = dict(directory=directory, command=list(command), file_collected=recognized,
                    returncode=returncode, collection_errors=payload.get('collection_errors', []))
                if skip or not recognized:
                    successful = bool(payload) and returncode in (0,5) and not payload.get('collection_errors')
                    for identity in identities:
                        result[identity] = dict(ids=[], completed=successful, returncode=returncode,
                            reason='' if skip else 'not_a_test_module' if successful else 'collection_error',
                            collection_status='MODULE_SKIPPED' if skip else 'COMPLETE' if successful else failure_status(message),
                            module_skip_reason=skip['reason'] if skip else '',
                            message='module_skip: '+skip['reason'] if skip else message,
                            directory_collection=directory_evidence)
                    groups_log.append(dict(module=module,duration_s=time.monotonic()-start,returncode=returncode,command=command,
                                           directory_collection=directory_evidence))
                    save()
                    continue
                selected_items = [node for node in collected if any(node == identity or
                    ('[' not in identity and node.startswith(identity + '[')) for identity in identities)]
                successful = returncode in (0,5) and not payload.get('collection_errors')
                # Preserve the effective directory context on successful discovery.
                # Retry a selected file only after actual selected items prove its
                # eligibility, when an unrelated directory error needs isolation.
                reuse_directory = successful or not selected_items
                if reuse_directory:
                    collected = [n for n in collected if n.split('::',1)[0] == module]
                    proc_returncode = returncode
                    receipt_exists = bool(payload)
                else:
                    command[-1] = module
                    if os.path.exists(receipt):
                        os.unlink(receipt)
            if not reuse_directory:
                proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      timeout=max(0.001, min(module_timeout-(time.monotonic()-start), deadline-time.monotonic())), env=environment)
                message = (proc.stdout + proc.stderr).decode('utf-8', 'replace')
                payload = json.loads(pathlib.Path(receipt).read_text()) if os.path.exists(receipt) else {}
                collected = payload if isinstance(payload,list) else payload.get('ids', [])
                proc_returncode = proc.returncode
                receipt_exists = os.path.exists(receipt)
                skip = pytest_module_skip(module, collected,
                    [] if isinstance(payload,list) else payload.get('module_skips',[]), message, proc_returncode,
                    () if isinstance(payload,list) else payload.get('collection_errors',())) if receipt_exists else None
            for identity in identities:
                ids = [node for node in collected if node == identity or
                       ("[" not in identity and node.startswith(identity + "["))]
                if skip:
                    result[identity] = dict(ids=[], reason='', message='module_skip: '+skip['reason'],
                        module_skip_reason=skip['reason'], module_skip_receipt=skip,
                        collection_status='MODULE_SKIPPED', completed=True, returncode=proc_returncode)
                    continue
                error = proc_returncode not in (0, 5) or not receipt_exists or bool(payload.get("collection_errors", ()) if isinstance(payload, dict) else False)
                status = failure_status(message) if error else "COMPLETE"
                result[identity] = dict(ids=[] if error else ids,
                    reason=status.lower() if error else "" if ids else "native_not_found",
                    message=message if error or not ids else "",
                    collection_status=status, completed=not error, returncode=proc_returncode)
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start,
                               returncode=proc_returncode if kind == "pytest" else proc.returncode, command=command,
                               directory_collection=directory_evidence))
    except subprocess.TimeoutExpired:
        message = traceback.format_exc()
        for identity in identities:
            result[identity] = dict(ids=[], reason="collection_timeout", message=message, collection_status="COLLECTION_ERROR", completed=False)
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start, error=message))
    except BaseException:
        message = traceback.format_exc()
        for identity in identities:
            status = failure_status(message)
            result[identity] = dict(ids=[], reason=status.lower(), message=message, collection_status=status, completed=False)
        groups_log.append(dict(module=module, duration_s=time.monotonic()-start, error=message))
    save()
print(json.dumps(dict(ids=result, groups=groups_log, tests_executed=0)))
"""
)


@dataclass(frozen=True)
class ValidationPass:
    records: tuple[IDValidation, ...] = ()
    errors: tuple[str, ...] = ()
    duration_s: float = 0.0
    groups: tuple[dict, ...] = ()
    context: dict = field(default_factory=dict)
    evidence_files: dict = field(default_factory=dict)
    evidence_sha256: dict = field(default_factory=dict)
    stage_health: tuple[dict, ...] = ()

    @property
    def runnable_ids(self):
        # An original slot is executed only when all its expansion members validate.
        skips = {tid for item in self.records for tid,_ in item.module_skip_instances}
        return tuple(dict.fromkeys(t for item in self.records if item.valid for t in item.runnable_ids if t not in skips))

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
            'module_skipped_slots': sum(bool(r.module_skip_reason) for r in self.records),
            'module_skip_reasons': list(dict.fromkeys(r.module_skip_reason for r in self.records if r.module_skip_reason)),
            "collector_status": 'COLLECTION_ERROR' if any(s['status'] in ('COLLECTION_ERROR','RUNNER_UNAVAILABLE','NOT_REACHED') and not s.get('allowed_exception') for s in self.stage_health)
                else 'ALLOWED_FAILURE' if any(s.get('allowed_exception') for s in self.stage_health)
                else 'EMPTY_INPUT' if not self.records else 'COMPLETE',
            "stage_health": list(self.stage_health),
        }


def contain_collection(static, merged, task, exceptions, *, tree=None):
    by_id = {r.selected_id:r for r in static}
    result = []
    for record in merged:
        original = by_id[record.selected_id]
        module = record.selected_id.split('::',1)[0]
        if (original.valid and record.unavailable and record.failure_status == 'COLLECTION_ERROR'
            and not any(reason in ('collection_timeout','not_reached','native_not_found','not_a_test_module') for _,reason in record.invalid_instances)
            and 'TimeoutExpired' not in record.message
            and not allowed_failure(exceptions,task,module,'native_collection',record.message,tree=tree)):
            record = replace(original, stage='collector_fallback', collector_fallback=True,
                collector_failure_status=record.failure_status, collector_message=record.message)
        result.append(record)
    return tuple(result)


def collection_stages(task, ids, receipt, exceptions, merged=(), *, tree=None):
    proven = {tid for r in merged if r.native_proven_absent
              for tid in (r.selected_id, *(t for t, _ in r.invalid_instances))}
    proven |= {tid for r in merged for tid in r.native_absent_instances}
    modules = {}
    for identity in ids:
        modules.setdefault(identity.split('::',1)[0],[]).append(identity)
    result = []
    for module, selected in modules.items():
        records = [receipt['ids'].get(i, {'completed':False,'message':'Missing collector receipt', 'collection_status':'COLLECTION_ERROR'}) for i in selected]
        skipped = [r for r in records if r.get('collection_status') == 'MODULE_SKIPPED' and r.get('completed')
                   and r.get('module_skip_reason','').strip() and r.get('returncode',0) in (0,5)]
        bad = [r for r in records if r not in skipped and (not r.get('completed') or r.get('returncode',0) not in (0,5))]
        bad += [dict(collection_status=r.failure_status, message=r.message) for r in merged
                if r.unavailable and r.selected_id.split('::',1)[0] == module]
        messages = list(dict.fromkeys(r.get('message','') for r in bad))
        causes = [allowed_failure(exceptions,task,module,'native_collection',m,tree=tree) for m in messages]
        allowed = bool(causes) and all(causes)
        collected = {i for r in records if r.get('completed') and r.get('returncode',0) in (0,5) for i in r.get('ids',[])}
        eligible = [i for i in selected if i not in proven]
        result.append({'stage':'native_collection','module':module,'input_count':len(eligible),
            'original_input_count':len(selected),'proven_absent_count':len(selected)-len(eligible),
            'output_count':len(collected),'status':bad[0].get('collection_status','COLLECTION_ERROR') if bad else 'MODULE_SKIPPED' if skipped else 'ALL_PROVEN_INVALID' if not eligible else 'COMPLETE',
            'module_skip_reason':'; '.join(dict.fromkeys(r['module_skip_reason'] for r in skipped)),
            'module_skipped_instances':len(skipped),'native_skip_recorded':bool(skipped),
            'allowed_exception':sorted(set(causes)) if allowed else [], 'messages':messages,
            'collector_exit_codes':[g.get('returncode') for g in receipt.get('groups',[]) if g['module']==module],
            'tests_executed':0})
    return tuple(result)


def validate_in_container(container, tests, runner, *, timeout_s=1800, tree=None):
    """Snapshot the current (already base/patched) tree, then collect valid identities."""
    started = time.monotonic()
    deadline = started + timeout_s
    static, context = (), {}
    exceptions = exception_rules()
    tree = tree or ('patched' if getattr(container,'_patch_applied',False) else 'base')
    task = getattr(container,'instance_id','')
    def remaining(limit=None):
        value = max(0.001, deadline-time.monotonic())
        return min(value, limit) if limit is not None else value
    if runner.name not in ("pytest", "django", "sympy"):
        return ValidationPass(records=tuple(IDValidation(t, 'unknown', reason='runner_unavailable',
            unavailable=True, failure_status='RUNNER_UNAVAILABLE') for t in tests),
            errors=("No collection-only adapter for runner: " + runner.name,),
            stage_health=({'stage':'native_collection','status':'RUNNER_UNAVAILABLE','input_count':len(tests),'output_count':0,'tests_executed':0},))
    try:
        command = "python -c " + shlex.quote(_SOURCE_SNAPSHOT)
        rc, raw = container.exec(command, timeout_s=remaining(120))
        if rc:
            raise RuntimeError("source snapshot failed: " + raw[-2000:])
        sources = SourceTree(json.loads(raw))
        frozen_runner = runner.name
        if runner.name == 'pytest' and 'bin/test' in sources.sources and 'sympy/__init__.py' in sources.sources:
            runner = TestRunner('sympy', 'native SymPy bin/test present; repairs frozen pytest runner')
        context = {'runner': runner.name, 'frozen_runner': frozen_runner, 'runner_evidence': runner.evidence}
        index = StaticIndex(sources, runner.name)
        static = index.validate(tests)
        directory_check_modules = {t.split('::',1)[0] for t in tests if runner.name == 'pytest'
            and not index.matches(Path(t.split('::',1)[0]).name,
                                  index.pytest_patterns(t.split('::',1)[0], 'python_files'))}
        static = tuple(replace(r, static_reason=r.reason, reason='not_a_test_module', runnable_ids=())
                       if r.selected_id.split('::',1)[0] in directory_check_modules and not r.expanded else r
                       for r in static)
        ids = tuple(
            dict.fromkeys(
                t for r in static for t in (r.selected_id, *(r.runnable_ids if r.valid else ()))
            )
        )
        if not ids:
            return ValidationPass(static, duration_s=time.monotonic() - started, context=context,
                stage_health=({'stage':'native_collection','status':'EMPTY_INPUT','input_count':0,'output_count':0,'tests_executed':0},))
        payload = json.dumps(
            {"runner": runner.name, "ids": ids, "directory_check_modules": sorted(directory_check_modules), "module_timeout_s": min(timeout_s, 120),
             "budget_s": remaining(), "prior_elapsed_s": time.monotonic()-started}
        )
        for path, data in (
            ("/tmp/verifier_collect_request.json", payload),
            ("/tmp/verifier_collect_driver.py", _NATIVE_DRIVER),
            ("/tmp/verifier_django_collect.py", _DJANGO_COLLECT),
            ("/tmp/verifier_collect_plugin.py", _PYTEST_PLUGIN),
            ("/tmp/verifier_sympy_driver.py", _SYMPY_PROGRAM),
        ):
            rc, message = container.exec_input("cat > " + path, data, timeout_s=remaining(60))
            if rc:
                raise RuntimeError("collector upload failed: " + message[-2000:])
        container.exec("rm -f /tmp/verifier_collect_pgid /tmp/verifier_collect_partial.json", timeout_s=remaining(30))
        # Refresh the remaining budget after uploads, before starting any collector.
        payload = json.loads(payload)
        payload.update(budget_s=remaining(), prior_elapsed_s=time.monotonic()-started)
        container.exec_input("cat > /tmp/verifier_collect_request.json", json.dumps(payload), timeout_s=remaining(60))
        rc, raw = container.exec("python /tmp/verifier_collect_driver.py", timeout_s=remaining()+2)
        if rc:
            raise RuntimeError("collector driver failed: " + raw[-2000:])
        receipt = json.loads(raw)
        if receipt.get("tests_executed") != 0:
            raise RuntimeError("collection receipt missing zero-execution assertion")
        primary = merge_native(static, receipt["ids"])
        merged = contain_collection(static, primary, task, exceptions,tree=tree)
        return ValidationPass(
            merged, duration_s=time.monotonic() - started, groups=tuple(receipt["groups"]), context=context,
            stage_health=collection_stages(task,ids,receipt,exceptions,primary,tree=tree)
        )
    except (TimeoutError, RuntimeError, ValueError, OSError) as exc:
        if isinstance(exc, TimeoutError):
            container.exec(
                "python -c 'import os,signal; os.killpg(int(open(\"/tmp/verifier_collect_pgid\").read()),signal.SIGKILL)'",
                timeout_s=30,
            )
            rc, partial = container.exec("cat /tmp/verifier_collect_partial.json", timeout_s=30)
            receipt = json.loads(partial) if rc == 0 else {"ids": {}, "groups": []}
            # Static proofs survive missing collection evidence; unstarted IDs
            # stay missing and never become INVALID_ID through a cap hit.
            for identity in ids if static else tests:
                receipt["ids"].setdefault(identity, {"ids": [], "reason": "not_reached",
                    "collection_status": "NOT_REACHED", "completed": False,
                    "elapsed_s": time.monotonic()-started, "message": "per-pass collection budget exhausted"})
            if static:
                merged = merge_native(static, receipt["ids"])
                return ValidationPass(merged,
                    duration_s=time.monotonic()-started, groups=tuple(receipt["groups"]), context=context,
                    stage_health=collection_stages(task,ids,receipt,exceptions,merged,tree=tree))
        status = "NOT_REACHED" if isinstance(exc, TimeoutError) else classify_collector_failure(str(exc))
        records = tuple(
            IDValidation(
                t,
                "unknown",
                reason=status.lower(),
                unavailable=True,
                failure_status=status,
                message=str(exc),
                elapsed_s=time.monotonic()-started,
            )
            for t in tests
        )
        if static and status == 'COLLECTION_ERROR':
            records = contain_collection(static, records, task, exceptions,tree=tree)
        return ValidationPass(records=records, errors=() if any(r.collector_fallback for r in records) else (str(exc),),
            duration_s=time.monotonic() - started, context=context,
            stage_health=({'stage':'native_collection','status':status,'input_count':len(tests),
                'output_count':0,'messages':[str(exc)],'tests_executed':0},))
