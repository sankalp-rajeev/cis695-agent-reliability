"""Synthetic tracer, fixture-attribution, selector and harness safety gates."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / 'tools/phase6b_trace'
sys.path.insert(0, str(CODE))
from phase6b_selection import build_selection, changed_targets, load_traces, read_trace
from phase6b_trace import Recorder


def sample(tmp_path, text):
    namespace = {}
    exec(compile(text, str(tmp_path / 'sample.py'), 'exec'), namespace)  # noqa: S102 -- literal synthetic source only
    return namespace


def names(recorder, tid):
    payload = recorder.payload()
    return {payload['codes'][i][1] for i in payload['tests'][tid]}


def test_call_events_and_no_local_trace(tmp_path):
    functions = sample(tmp_path, 'def inner(): return 1\ndef outer(): return inner()\n')
    recorder = Recorder(tmp_path)
    recorder.start()
    try:
        recorder.begin('a')
        functions['outer']()
        recorder.end('a')
    finally:
        recorder.stop()
    assert {'outer', 'inner'} <= names(recorder, 'a')
    assert recorder.trace(sys._getframe(), 'line', None) is None


def test_thread_calls_recorded_and_attributed(tmp_path):
    functions = sample(tmp_path, 'def worker(): return 2\n')
    recorder = Recorder(tmp_path)
    recorder.start()
    try:
        recorder.begin('a')
        thread = threading.Thread(target=functions['worker'])
        thread.start()
        thread.join()
        recorder.end('a')
    finally:
        recorder.stop()
    assert 'worker' in names(recorder, 'a')


def test_unittest_class_setup_and_setup_test_data_attributed_to_both(tmp_path, monkeypatch):
    monkeypatch.setenv('PHASE6B_RUNNER', 'django')
    functions = sample(tmp_path, '''
import unittest
class Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.setUpTestData()
    @classmethod
    def setUpTestData(cls): cls.value = 1
    @classmethod
    def tearDownClass(cls): pass
    def setUp(self): pass
    def tearDown(self): pass
    def test_a(self): self.assertEqual(self.value, 1)
    def test_b(self): self.assertEqual(self.value, 1)
''')
    recorder = Recorder(tmp_path)
    recorder.start()
    try:
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(functions['Case']))
    finally:
        recorder.stop()
    assert result.wasSuccessful()
    assert len(recorder.tests) == 2
    for tid in recorder.tests:
        assert {'setUpClass', 'setUpTestData', 'tearDownClass', 'setUp', 'tearDown'} <= names(recorder, tid)


def test_shared_scope_finalizer_and_interned_gzip_round_trip(tmp_path):
    functions = sample(tmp_path, 'def setup(): pass\ndef teardown(): pass\ndef test_body(): pass\n')
    recorder = Recorder(tmp_path, str(tmp_path / 'output'))
    recorder.start()
    try:
        with recorder.scope(['a', 'b']):
            functions['setup']()
        for tid in ('a', 'b'):
            recorder.begin(tid)
            functions['test_body']()
            recorder.end(tid)
        with recorder.scope(['a', 'b']):
            functions['teardown']()
    finally:
        recorder.flush()
    paths = list((tmp_path / 'output').glob('*.jsonl.gz'))
    data = read_trace(paths[0])
    assert len(data['codes']) == len(set(map(tuple, data['codes'])))
    for tid in ('a', 'b'):
        assert all(isinstance(i, int) for i in data['tests'][tid])
        assert {'setup', 'teardown', 'test_body'} <= names(recorder, tid)


def test_real_pytest_fixture_and_xunit_attribution(tmp_path):
    (tmp_path / 'test_example.py').write_text('''
import pytest
def setup_module(): pass
def teardown_module(): pass
def session_teardown_marker(): pass
def module_teardown_marker(): pass
@pytest.fixture(scope="session", autouse=True)
def session_fixture():
    yield
    session_teardown_marker()
@pytest.fixture(scope="module", autouse=True)
def module_fixture():
    yield
    module_teardown_marker()
class TestGroup:
    @classmethod
    def setup_class(cls): pass
    @classmethod
    def teardown_class(cls): pass
    def test_one(self): pass
    def test_two(self): pass
''')
    traces = tmp_path / 'traces'
    environment = {**os.environ, 'PYTHONPATH': str(CODE), 'PYTEST_PLUGINS': 'phase6b_pytest',
                   'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PHASE6B_TRACE': '1',
                   'PHASE6B_RUNNER': 'pytest', 'PHASE6B_ROOT': str(tmp_path), 'PHASE6B_TRACE_OUT': str(traces)}
    completed = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-c', '/dev/null', 'test_example.py'],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payloads = [read_trace(p) for p in traces.glob('*.jsonl.gz')]
    data = next(p for p in payloads if len(p['tests']) == 2)
    for indices in data['tests'].values():
        recorded = {data['codes'][i][1] for i in set(indices) | data['common']}
        assert {'setup_module', 'teardown_module', 'setup_class', 'teardown_class',
                'session_fixture', 'module_fixture', 'session_teardown_marker', 'module_teardown_marker'} <= recorded


def test_no_trace_retained_and_function_subset():
    targets = {'files': ['api.py'], 'functions': [{'path': 'api.py', 'name': 'changed',
        'start': 4, 'decorator_start': 4}], 'absent_from_base': [], 'mapping_errors': []}
    result = build_selection(['a', 'b', 'c'], dict.fromkeys(['a', 'b', 'c'], 'passed'),
        {'a': {('/testbed/api.py', 'changed', 4)}, 'b': {('/testbed/api.py', 'other', 8)}}, {}, targets)
    assert result['file'] == ['a', 'b', 'c']
    assert result['function'] == ['a', 'c']
    assert result['retained_reasons']['c'] == ['NO_USABLE_TRACE', 'TRACE_INCOMPLETE']


def test_ast_qualified_mapping_and_new_function_retention():
    source = 'class C:\n    def changed(self):\n        return 1\n'
    patch = '--- a/api.py\n+++ b/api.py\n@@ -1,3 +1,3 @@\n class C:\n     def changed(self):\n-        return 1\n+        return 2\n'
    targets = changed_targets(patch, {'api.py': source})
    assert targets['functions'][0]['qualname'] == 'C.changed'
    added = '--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+def new(): pass\n'
    assert changed_targets(added, {})['absent_from_base'] == ['new.py']


def harness():
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('phase6b_harness_test', ROOT / 'scripts/phase6b_run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parallel_command_preserved_and_run_requires_frozen_tag(tmp_path):
    module = harness()
    command = ['python', 'tests/runtests.py', '--verbosity=2', '--parallel', '4', 'test']
    assert module.command_prefix(command, 'django') == command[:5]
    with pytest.raises(ValueError, match='harness freeze'):
        module.main(['run', '--output', str(ROOT / 'runs/phase6b_never_started')])


def test_repaired_container_mounts_and_instrumentation_only_on_execution(tmp_path, monkeypatch):
    module = harness()
    container = module.TraceContainer('synthetic', '', image='sha256:' + 'a' * 64)
    container.trace_output = tmp_path
    args = container.run_args()
    assert args[args.index('--network') + 1] == 'none'
    assert args[args.index('--cpu-shares') + 1] == '2048'
    assert '--pull=never' in args
    assert any('/phase6b_tracer,readonly' in arg for arg in args)
    commands = []
    monkeypatch.setattr(module.p4.FrozenContainer, 'exec_raw', lambda self, command, timeout: commands.append(command))
    container.trace_token, container.trace_runner = 'base_traced', 'pytest'
    container.exec_raw('python /tmp/verifier_driver.py pytest 100 0', 100)
    container.exec_raw('python -c "collection probe"', 100)
    assert 'PYTEST_PLUGINS=phase6b_pytest' in commands[0]
    assert commands[0].endswith('python /tmp/verifier_driver.py pytest 100 0')
    assert commands[1] == 'python -c "collection probe"'


def test_aggregate_reading_uses_costs_and_retained_ids():
    module = harness()
    row = {'v2_size': 10, 'base_traced_s': 4., 'base_untraced_s': 2., 'sealed_full_patched_s': 10.,
           'stable_disagreements': [], 'selection': {'trace_incomplete': [], 'without_usable_trace': []},
           'targets': {'absent_from_base': []}, 'modes': {mode: {'reference_kept': list(range(12)),
           'r': .5, 'total_cost_s': 7., 'baseline_cost_s': 12., 'patched_s': 3., 'selected_count': 5,
           'selected_executed': 5} for mode in ('file', 'function')}}
    result = module.aggregate([row])
    assert result['pooled']['file']['success']
    assert result['pooled']['file']['adopt']
    assert result['pooled']['file']['tracing_overhead_T'] == 2.


def trace_environment(tmp_path):
    (tmp_path / 'traces').mkdir(exist_ok=True)
    return {**os.environ, 'PYTHONPATH': str(CODE), 'PHASE6B_TRACE': '1',
            'PHASE6B_RUNNER': 'django', 'PHASE6B_ROOT': str(tmp_path),
            'PHASE6B_TRACE_OUT': str(tmp_path / 'traces')}


def fake_run(raw_ids, executed=None, pid=None):
    executed = raw_ids if executed is None else executed
    mapping = {raw: 'synthetic.py::' + str(i) for i, raw in enumerate(raw_ids)}
    return SimpleNamespace(
        events=[{'event': 'start', 'pid': pid}] if pid else [],
        raw_execution_map=mapping,
        execution_id_map={native: [native] for native in mapping.values()},
        execution_results=[SimpleNamespace(test_id=mapping[raw], status=SimpleNamespace(value='passed'))
                           for raw in executed])


def test_fork_pool_django_parallel_shape_and_executor_id_merge(tmp_path):
    program = tmp_path / 'parallel_shape.py'
    program.write_text('''
import multiprocessing, unittest, time, json
class A(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.setUpTestData()
    @classmethod
    def setUpTestData(cls): cls.value = 1
    def test_a(self): marker_a()
class B(unittest.TestCase):
    def test_b(self): marker_b()
def marker_a(): pass
def marker_b(): pass
def run_suite(name):
    time.sleep(.03)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(A if name == 'a' else B)
    ids = [test.id() for test in suite]
    result = unittest.TestResult()
    suite.run(result)
    assert result.wasSuccessful()
    return ids
if __name__ == '__main__':
    pool = multiprocessing.get_context('fork').Pool(2)
    result = pool.map(run_suite, ['a', 'b'])
    pool.close()
    pool.join()
    print(json.dumps(result))
''')
    proc = subprocess.run([sys.executable, str(program)], env=trace_environment(tmp_path),
        capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    raw_ids = [tid for group in json.loads(proc.stdout) for tid in group]
    paths = list((tmp_path / 'traces').glob('*.jsonl.gz'))
    records = [read_trace(path) for path in paths]
    root = next(r for r in records if r['parent_pid'] not in {item['pid'] for item in records})
    run = fake_run(raw_ids, pid=root['pid'])
    codes, flags, info = load_traces(tmp_path / 'traces', run, 'django')
    assert info['workers_with_tests'] == 2
    assert info['incomplete_count'] == 0
    assert not any(flags.values())
    assert 'marker_a' in {c[1] for c in codes['synthetic.py::0']}
    assert 'marker_b' not in {c[1] for c in codes['synthetic.py::0']}
    assert 'marker_b' in {c[1] for c in codes['synthetic.py::1']}
    assert 'setUpTestData' in {c[1] for c in codes['synthetic.py::0']}
    assert len({r['pid'] for r in records}) == len(records)


def test_missing_executed_record_flagged_and_marker_failures_rejected(tmp_path):
    rec = Recorder(tmp_path, str(tmp_path))
    rec.marker('ready', {'pid': rec.pid})
    rec.codes = [(str(tmp_path / 'synthetic.py'), 'test_a', 1)]
    rec.tests = {'raw_a': {0}}
    rec.dirty = {'raw_a'}
    rec.checkpoint(final=True)
    run = fake_run(['raw_a', 'raw_b', 'skipped'], executed=['raw_a', 'raw_b'], pid=rec.pid)
    _codes, flags, info = load_traces(tmp_path, run, 'django')
    assert info['incomplete_count'] == 1
    assert info['incomplete_fraction'] == .5
    assert 'executed_without_trace_record' in flags['synthetic.py::1']
    assert not flags.get('synthetic.py::2')
    (tmp_path / (str(rec.pid) + '.done')).unlink()
    with pytest.raises(ValueError, match='Missing trace/readiness/completion'):
        load_traces(tmp_path, run, 'django')
    rec.marker('done', {'pid': rec.pid})
    rec.error(RuntimeError('synthetic internal tracer error'))
    with pytest.raises(ValueError, match='error marker'):
        load_traces(tmp_path, run, 'django')


def test_sitecustomize_without_argv_is_lazy_and_never_raises(tmp_path):
    env = trace_environment(tmp_path)
    env.pop('PHASE6B_TRACE', None)  # probe explicitly executes startup before framework import
    program = '''
import os, sys, builtins
os.environ['PHASE6B_TRACE'] = '1'
del sys.argv
with open(os.environ['STARTUP_SOURCE']) as source:
    exec(compile(source.read(), os.environ['STARTUP_SOURCE'], 'exec'), {'__name__': 'startup_probe'})
assert not os.listdir(os.environ['PHASE6B_TRACE_OUT'])
sys.argv = ['synthetic']
import unittest
import phase6b_trace
assert phase6b_trace.RECORDER is not None
'''
    proc = subprocess.run([sys.executable, '-c', program], env={**env, 'STARTUP_SOURCE': str(CODE / 'sitecustomize.py')},
        capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert list((tmp_path / 'traces').glob('*.ready'))
    assert not list((tmp_path / 'traces').glob('*.error'))


def test_startup_internal_error_is_marked_without_failing_interpreter(tmp_path):
    bad = tmp_path / 'bad'
    bad.mkdir()
    (bad / 'phase6b_trace.py').write_text("raise RuntimeError('synthetic tracer import failure')\n")
    env = trace_environment(tmp_path)
    env['PYTHONPATH'] = str(bad) + os.pathsep + str(CODE)
    proc = subprocess.run([sys.executable, '-c', "import unittest; print('survived')"],
        env=env, capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0
    assert 'survived' in proc.stdout
    errors = list((tmp_path / 'traces').glob('*.error'))
    # The output directory is a harness-created writable mount.
    if not errors:
        pytest.fail('startup did not record its failure')


def test_environment_stripping_python_child_followed_and_owned(tmp_path):
    child = tmp_path / 'child.py'
    child.write_text('def child_marker(): pass\nchild_marker()\n')
    rec = Recorder(tmp_path, str(tmp_path))
    rec.start()
    try:
        rec.begin('raw_a')
        proc = subprocess.run([sys.executable, str(child)], env={'PATH': os.environ['PATH']},
                              check=False, capture_output=True, timeout=10)
        rec.end('raw_a')
    finally:
        rec.flush()
    assert proc.returncode == 0, proc.stderr
    codes, flags, info = load_traces(tmp_path, fake_run(['raw_a'], pid=rec.pid), 'django')
    assert 'child_marker' in {c[1] for c in codes['synthetic.py::0']}
    assert not flags['synthetic.py::0']
    assert info['incomplete_fraction'] == 0.


def test_pid_marker_cannot_collide(tmp_path):
    recorder = Recorder(tmp_path, str(tmp_path))
    recorder.marker('ready', {'pid': recorder.pid})
    with pytest.raises(FileExistsError):
        recorder.marker('ready', {'pid': recorder.pid})


def test_five_percent_cutoff_applies_to_every_smoke():
    module = harness()
    for parallel in (False, True):
        with pytest.raises(ValueError, match='more than 5%'):
            module.check_parallel_smoke({'workers_with_tests': 2, 'incomplete_fraction': .25}, parallel)
        module.check_parallel_smoke({'workers_with_tests': 2, 'incomplete_fraction': .05}, parallel)


def test_nonpython_observation_never_flags(tmp_path):
    rec = Recorder(tmp_path, str(tmp_path / 'traces'))
    body = sample(tmp_path, 'def body(): pass\n')['body']
    rec.start()
    try:
        with rec.scope(['raw_a', 'raw_b'], 'module'):
            subprocess.run(['/bin/true'], env={}, check=True, timeout=10)
        rec.begin('raw_a')
        body()
        rec.end('raw_a')
        rec.begin('raw_b')
        body()
        rec.end('raw_b')
    finally:
        rec.flush()
    _, flags, info = load_traces(tmp_path / 'traces', fake_run(['raw_a', 'raw_b'], pid=rec.pid), 'django')
    assert info['incomplete_count'] == 0 and not any(flags.values())
    assert rec.children[0]['python'] is False
    assert rec.children[0]['scope'] == 'module'


def test_shared_python_child_and_test_window_secondary(tmp_path):
    child = tmp_path / 'shared.py'
    child.write_text('def shared_marker(): pass\nshared_marker()\n')
    body = sample(tmp_path, 'def body(): pass\n')['body']
    rec = Recorder(tmp_path, str(tmp_path / 'traces'))
    rec.start()
    try:
        with rec.scope(['raw_a', 'raw_b'], 'class'):
            subprocess.run([sys.executable, str(child)], env={}, check=True, timeout=10)
        for tid in ('raw_a', 'raw_b', 'raw_c'):
            rec.begin(tid)
            body()
            rec.end(tid)
    finally:
        rec.flush()
    run = fake_run(['raw_a', 'raw_b', 'raw_c'], pid=rec.pid)
    codes, flags, info = load_traces(tmp_path / 'traces', run, 'django')
    windows, _, _ = load_traces(tmp_path / 'traces', run, 'django', test_window_only=True)
    assert info['incomplete_count'] == 0 and not any(flags.values())
    for tid in ('synthetic.py::0', 'synthetic.py::1'):
        assert 'shared_marker' in {c[1] for c in codes[tid]}
        assert 'shared_marker' not in {c[1] for c in windows[tid]}
    assert 'shared_marker' not in {c[1] for c in codes['synthetic.py::2']}
    assert {'class', 'test'} <= set(info['scopes_seen'])


def test_unfollowable_python_child_flags_only_spawn_scope(tmp_path):
    body = sample(tmp_path, 'def body(): pass\n')['body']
    rec = Recorder(tmp_path, str(tmp_path / 'traces'))
    rec.start()
    try:
        with rec.scope(['raw_a', 'raw_b'], 'module'):
            subprocess.run([sys.executable, '-S', '-c', 'pass'], env={}, check=True, timeout=10)
        for tid in ('raw_a', 'raw_b', 'raw_c'):
            rec.begin(tid)
            body()
            rec.end(tid)
    finally:
        rec.flush()
    _, flags, info = load_traces(tmp_path / 'traces', fake_run(['raw_a', 'raw_b', 'raw_c'], pid=rec.pid), 'django')
    assert info['incomplete_count'] == 2
    assert 'unfollowed_child_process' in flags['synthetic.py::0']
    assert 'unfollowed_child_process' in flags['synthetic.py::1']
    assert not flags['synthetic.py::2']


@pytest.mark.parametrize('spawn', ['posix_spawn', 'posix_spawnp'])
def test_posix_spawn_python_child_is_followed(tmp_path, spawn):
    if not hasattr(os, spawn):
        pytest.skip('platform has no posix_spawn')
    child = tmp_path / 'child.py'
    child.write_text('def spawned_marker(): pass\nspawned_marker()\n')
    rec = Recorder(tmp_path, str(tmp_path / 'traces'))
    rec.start()
    try:
        rec.begin('raw_a')
        pid = getattr(os, spawn)(sys.executable, [sys.executable, str(child)], {})
        assert os.waitpid(pid, 0)[1] == 0
        rec.end('raw_a')
    finally:
        rec.flush()
    codes, flags, info = load_traces(tmp_path / 'traces', fake_run(['raw_a'], pid=rec.pid), 'django')
    assert 'spawned_marker' in {c[1] for c in codes['synthetic.py::0']}
    assert info['incomplete_count'] == 0 and not any(flags.values())


def test_exec_replacement_keeps_pid_segments_and_owner(tmp_path):
    child = tmp_path / 'child.py'
    child.write_text('def exec_marker(): pass\nexec_marker()\n')
    program = tmp_path / 'parent.py'
    program.write_text("import os, sys, unittest, phase6b_trace\n"
                       "phase6b_trace.RECORDER.begin('raw_a')\n"
                       "os.execvpe(sys.executable, [sys.executable, os.environ['CHILD']], {})\n")
    environment = trace_environment(tmp_path)
    environment['CHILD'] = str(child)
    proc = subprocess.run([sys.executable, str(program)], env=environment,
                          capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0, proc.stderr
    records = [read_trace(p) for p in (tmp_path / 'traces').glob('*.jsonl.gz')]
    assert len(records) == 2 and len({r['pid'] for r in records}) == 1
    pid = records[0]['pid']
    codes, flags, info = load_traces(tmp_path / 'traces', fake_run(['raw_a'], pid=pid), 'django')
    assert 'exec_marker' in {c[1] for c in codes['synthetic.py::0']}
    assert info['incomplete_count'] == 0 and not any(flags.values())


def test_unittest_class_scope_does_not_leak_to_other_class(tmp_path, monkeypatch):
    monkeypatch.setenv('PHASE6B_RUNNER', 'django')
    functions = sample(tmp_path, 'import unittest\n'
        'class A(unittest.TestCase):\n'
        '    @classmethod\n'
        '    def setUpClass(cls): marker_shared()\n'
        '    def test_a(self): pass\n'
        '    def test_b(self): pass\n'
        'class B(unittest.TestCase):\n'
        '    def test_c(self): pass\n'
        'def marker_shared(): pass\n')
    rec = Recorder(tmp_path)
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(functions[c]) for c in ('A', 'B')])
    rec.start()
    try:
        suite.run(unittest.TestResult())
    finally:
        rec.stop()
    for tid in rec.tests:
        if '.A.' in tid:
            assert 'marker_shared' in names(rec, tid)
        else:
            assert 'marker_shared' not in names(rec, tid)


def test_checkpoint_resume_rejects_capture_tampering(tmp_path):
    module = harness()
    (tmp_path / 'base_traced.json').write_text('{"capture": "original"}')
    module.task_checkpoint(tmp_path, {'task': 'synthetic', 'count': 1})
    assert module.completed_task(tmp_path) == {'task': 'synthetic', 'count': 1}
    (tmp_path / 'base_traced.json').write_text('{"capture": "changed"}')
    with pytest.raises(ValueError, match='capture hash mismatch'):
        module.completed_task(tmp_path)


def test_python_shebang_child_is_traced(tmp_path):
    child = tmp_path / 'helper'
    child.write_text('#!' + sys.executable + '\ndef shebang_marker(): pass\nshebang_marker()\n')
    child.chmod(0o755)
    rec = Recorder(tmp_path, str(tmp_path / 'traces'))
    rec.start()
    try:
        rec.begin('raw_a')
        subprocess.run([str(child)], env={}, check=True, timeout=10)
        rec.end('raw_a')
    finally:
        rec.flush()
    codes, flags, info = load_traces(tmp_path / 'traces', fake_run(['raw_a'], pid=rec.pid), 'django')
    assert 'shebang_marker' in {c[1] for c in codes['synthetic.py::0']}
    assert info['incomplete_count'] == 0 and not any(flags.values())
    assert rec.children[-1]['python'] is True
