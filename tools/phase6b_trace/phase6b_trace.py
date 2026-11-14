"""Python 3.6-compatible call-only, scoped, child-aware trace journals."""
# ruff: noqa: BLE001, S110 -- tracing errors become explicit markers
import _thread
import atexit
import contextlib
import functools
import gzip
import inspect
import json
import os
import shlex
import shutil
import sys
import threading
import unittest


class Recorder:
    def __init__(self, root, output=None):
        self.root = os.path.abspath(root).rstrip('/') + '/'
        self.output = output
        self.pid, self.parent_pid = os.getpid(), os.getppid()
        self.segment = int(os.environ.get('PHASE6B_EXEC_SEQ', '0'))
        self.inherited_owner = json.loads(os.environ.get('PHASE6B_OWNER', 'null'))
        self.index, self.codes = {}, []
        self.tests, self.flags = {}, {}
        self.common, self.common_flags = set(), set()
        self.active = None
        self.children, self.dirty = [], set()
        self.scoped, self.written_scoped = {}, {}
        self.scope_tests = {'module': {}, 'class': {}}
        self.context, self.lock = threading.local(), threading.RLock()
        self.enabled, self.failed, self.finished = False, False, False
        self.originals = {}
        self.written_codes, self.written_common, self.written_children = 0, set(), 0

    def ownership(self):
        if self.inherited_owner is not None:
            return self.inherited_owner['scope'], list(self.inherited_owner['tests'])
        scopes = getattr(self.context, 'scopes', ())
        if scopes:
            return scopes[-1]
        inherited = getattr(self.context, 'owner', None)
        if inherited is None:
            inherited = getattr(threading.current_thread(), '_phase6b_owner', None)
        if inherited is not None:
            return inherited
        return ('test', [self.active]) if self.active else ('session', [])

    def targets(self):
        return self.ownership()[1]

    def stem(self):
        return str(self.pid) + ('_' + str(self.segment) if self.segment else '')

    def marker(self, suffix, value):
        if not self.output:
            return
        value = dict(value, scope=self.ownership()[0], segment=self.segment)
        os.makedirs(self.output, exist_ok=True)
        path = os.path.join(self.output, self.stem() + '.' + suffix)
        if suffix == 'ready':
            with open(path, 'x') as stream:
                json.dump(value, stream, sort_keys=True)
            return
        with open(path + '.tmp', 'w') as stream:
            json.dump(value, stream, sort_keys=True)
        os.replace(path + '.tmp', path)

    def error(self, exc):
        self.failed = True
        try:
            self.marker('error', {'pid': self.pid, 'error': repr(exc)})
        except BaseException:
            try:
                os.write(2, b'phase6b internal failure; error marker unavailable\n')
            except BaseException:
                pass

    def incomplete(self, reason, targets=None):
        targets = self.targets() if targets is None else targets
        if not targets:
            self.common_flags.add(reason)
        for tid in targets:
            self.flags.setdefault(tid, set()).add(reason)
            self.dirty.add(tid)

    def trace(self, frame, event, arg):
        try:
            if event == 'call' and os.getpid() == self.pid and not self.failed:
                filename = frame.f_code.co_filename
                if filename.startswith(self.root) and not frame.f_globals.get('__name__', '').startswith('phase6b_'):
                    with self.lock:
                        key = (filename, frame.f_code.co_name, frame.f_code.co_firstlineno)
                        index = self.index.get(key)
                        if index is None:
                            index = len(self.codes)
                            self.index[key] = index
                            self.codes.append(key)
                        scope, targets = self.ownership()
                        self.scoped.setdefault((scope, tuple(targets)), set()).add(index)
                        if targets:
                            for tid in targets:
                                self.tests.setdefault(tid, set()).add(index)
                                self.dirty.add(tid)
                        else:
                            self.common.add(index)
        except BaseException as exc:
            self.error(exc)
        return None  # no local or line tracing

    def begin(self, tid):
        self.active = tid
        self.tests.setdefault(tid, set())
        self.dirty.add(tid)

    def end(self, tid):
        self.active = None
        self.checkpoint()

    @contextlib.contextmanager
    def scope(self, targets, scope='session'):
        if scope not in ('session', 'module', 'class', 'test'):
            raise ValueError('Invalid trace scope')
        if not hasattr(self.context, 'scopes'):
            self.context.scopes = []
        self.context.scopes.append((scope, list(targets)))
        try:
            yield
        finally:
            self.context.scopes.pop()

    def after_fork(self):
        owner = self.ownership()
        self.parent_pid, self.pid = self.pid, os.getpid()
        self.segment = 0
        self.tests, self.flags, self.children, self.dirty = {}, {}, [], set()
        self.scoped, self.written_scoped = {}, {}
        self.context, self.lock = threading.local(), threading.RLock()
        # A worker pool created in shared setup later assigns individual tests;
        # only forks inside a test/shared explicit scope retain fixed ownership.
        if owner[1]:
            self.inherited_owner = {'scope': owner[0], 'tests': owner[1]}
        self.written_codes, self.written_common, self.written_children = 0, set(), 0
        self.finished = False
        self.marker('ready', {'pid': self.pid, 'parent_pid': self.parent_pid, 'forked': True})
        threading.settrace(self.trace)
        sys.settrace(self.trace)

    def child_description(self, executable, argv, environment, cwd=None, shell=False):
        scope, targets = self.ownership()
        argv = list(argv) if isinstance(argv, (list, tuple)) else [argv]
        executable = os.fsdecode(executable or (argv[0] if argv else ''))
        environment = os.environ if environment is None else environment
        search = environment.get('PATH', os.defpath)
        candidate = executable
        if cwd and os.path.dirname(candidate) and not os.path.isabs(candidate):
            candidate = os.path.join(os.fsdecode(cwd), candidate)
        resolved = shutil.which('/bin/sh' if shell else candidate, path=search)
        python = None if not resolved else os.path.basename(os.path.realpath(resolved)).startswith('python')
        shebang = None
        if resolved and not python:
            try:
                with open(resolved, 'rb') as stream:
                    header = stream.read(256)
                if header.startswith(b'#!'):
                    shebang = header.split(b'\n')[0].decode('utf-8', 'replace')
                    words = shlex.split(shebang[2:])
                    interpreter = words[0] if words else ''
                    if os.path.basename(interpreter) == 'env':
                        interpreter = next((w for w in words[1:] if not w.startswith('-') and '=' not in w), '')
                    python = os.path.basename(interpreter).startswith('python')
            except OSError:
                python = None
        return {'tests': list(targets), 'scope': scope, 'executable': executable,
                'resolved_executable': resolved, 'argv': [os.fsdecode(a) for a in argv[:3]],
                'python': python, 'shebang': shebang,
                'inherited_environment': environment.get('PHASE6B_TRACE') == '1'}

    def child_environment(self, environment, description, replacement=False):
        if description['python'] is False:
            return environment
        merged = dict(os.environ if environment is None else environment)
        code = os.path.dirname(os.path.abspath(__file__))
        paths = merged.get('PYTHONPATH', '').split(os.pathsep)
        merged['PYTHONPATH'] = os.pathsep.join([code] + [p for p in paths if p and p != code])
        merged.update(PHASE6B_TRACE='1', PHASE6B_ROOT=self.root.rstrip('/'),
                      PHASE6B_TRACE_OUT=str(self.output or ''),
                      PHASE6B_RUNNER=os.environ.get('PHASE6B_RUNNER', ''),
                      PHASE6B_OWNER=json.dumps({'scope': description['scope'], 'tests': description['tests']}),
                      PHASE6B_EXEC_SEQ=str(self.segment + 1 if replacement else 0))
        return merged

    def register_suite(self, suite):
        for item in suite:
            if item is None:
                continue
            if isinstance(item, unittest.TestSuite):
                self.register_suite(item)
            elif hasattr(item, 'id'):
                tid, cls = item.id(), item.__class__
                self.scope_tests['class'].setdefault(cls, set()).add(tid)
                self.scope_tests['module'].setdefault(cls.__module__, set()).add(tid)

    def start(self):
        if self.enabled:
            return
        self.enabled = True
        self.originals = {'sys_trace': sys.gettrace(), 'thread_trace': getattr(threading, '_trace_hook', None),
                          'thread_start': threading.Thread.start, 'low_start': _thread.start_new_thread,
                          'case_run': unittest.TestCase.run, 'suite_run': unittest.TestSuite.run,
                          'exit': os._exit}
        if hasattr(os, 'fork'):
            self.originals['fork'] = os.fork
        recorder = self

        def start_thread(thread, *args, **kwargs):
            thread._phase6b_owner = recorder.ownership()
            return recorder.originals['thread_start'](thread, *args, **kwargs)

        def low_start(function, args, kwargs=None):
            owner = recorder.ownership()

            def followed():
                recorder.context.owner = owner
                sys.settrace(recorder.trace)
                return function(*args, **(kwargs or {}))
            return recorder.originals['low_start'](followed, ())

        def fork():
            scope, targets = recorder.ownership()
            pid = recorder.originals['fork']()
            try:
                if pid == 0:
                    recorder.after_fork()
                else:
                    recorder.children.append({'pid': pid, 'tests': targets, 'scope': scope,
                                              'kind': 'fork', 'python': True})
            except BaseException as exc:
                recorder.error(exc)
            return pid

        def exit_process(code):
            recorder.checkpoint(final=True)
            recorder.originals['exit'](code)

        def case_run(case, *args, **kwargs):
            if os.environ.get('PHASE6B_RUNNER') == 'pytest':
                return recorder.originals['case_run'](case, *args, **kwargs)
            recorder.begin(case.id())
            try:
                return recorder.originals['case_run'](case, *args, **kwargs)
            finally:
                recorder.end(case.id())

        def suite_run(suite, *args, **kwargs):
            recorder.register_suite(suite)
            try:
                return recorder.originals['suite_run'](suite, *args, **kwargs)
            finally:
                recorder.checkpoint()

        for method in ('_handleClassSetUp', '_tearDownPreviousClass', '_handleModuleFixture', '_handleModuleTearDown'):
            if not hasattr(unittest.TestSuite, method):
                continue
            original = getattr(unittest.TestSuite, method)
            self.originals[method] = original

            def wrap_shared(original, method):
                @functools.wraps(original)
                def shared(suite, *args, **kwargs):
                    previous = method in ('_tearDownPreviousClass', '_handleModuleTearDown')
                    result = args[-1]
                    cls = getattr(result, '_previousTestClass', None) if previous else args[0].__class__
                    scope = 'class' if 'Class' in method else 'module'
                    key = cls if scope == 'class' else getattr(cls, '__module__', None)
                    targets = sorted(recorder.scope_tests[scope].get(key, ()))
                    with recorder.scope(targets, scope):
                        return original(suite, *args, **kwargs)
                return shared
            setattr(unittest.TestSuite, method, wrap_shared(original, method))

        import multiprocessing.process
        self.originals['process_start'] = multiprocessing.process.BaseProcess.start

        def process_start(process, *args, **kwargs):
            import multiprocessing
            method = getattr(process, '_start_method', None) or multiprocessing.get_start_method()
            scope, targets = recorder.ownership()
            # spawn/forkserver use private fork_exec rather than Popen. Preserve
            # ownership in their inherited environment; absence of a journal is
            # evaluated by the host for this scope, never silently accepted.
            saved = {key: os.environ.get(key) for key in ('PHASE6B_OWNER', 'PHASE6B_EXEC_SEQ')}
            if method != 'fork':
                os.environ['PHASE6B_OWNER'] = json.dumps({'scope': scope, 'tests': targets})
                os.environ['PHASE6B_EXEC_SEQ'] = '0'
            try:
                value = recorder.originals['process_start'](process, *args, **kwargs)
                if method != 'fork':
                    recorder.children.append({'pid': process.pid, 'tests': targets, 'scope': scope,
                                              'kind': method, 'python': True})
                return value
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

        import subprocess
        self.originals['popen_init'] = subprocess.Popen.__init__
        popen_signature = inspect.signature(self.originals['popen_init'])

        def popen_init(process, *args, **kwargs):
            bound = popen_signature.bind(process, *args, **kwargs)
            arguments = bound.arguments
            argv = arguments.get('args', [])
            description = recorder.child_description(arguments.get('executable'), argv,
                arguments.get('env'), arguments.get('cwd'), arguments.get('shell', False))
            if description['python'] is not False:
                arguments['env'] = recorder.child_environment(arguments.get('env'), description)
            value = recorder.originals['popen_init'](*bound.args, **bound.kwargs)
            recorder.children.append(dict(description, pid=process.pid, kind='exec'))
            return value

        for name in ('execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe'):
            if hasattr(os, name):
                self.originals[name] = getattr(os, name)
        original_execve = os.execve
        original_execvpe = os.execvpe

        def wrap_exec(name):
            def execute(path, *args):
                has_env = name.endswith('e')
                environment = args[-1] if has_env else None
                argv = list(args[0]) if name.startswith('execv') else list(args[:-1] if has_env else args)
                description = recorder.child_description(path, argv, environment)
                environment = recorder.child_environment(environment, description, replacement=True)
                recorder.children.append(dict(description, pid=recorder.pid,
                    segment=recorder.segment + 1, kind='exec_replace'))
                recorder.checkpoint(final=True)
                try:
                    call = original_execvpe if 'p' in name else original_execve
                    return call(path, argv, dict(os.environ) if environment is None else environment)
                except BaseException:
                    recorder.finished = False
                    recorder.children.pop()
                    raise
            return execute

        for name in ('posix_spawn', 'posix_spawnp'):
            if not hasattr(os, name):
                continue
            original = getattr(os, name)
            self.originals[name] = original

            def wrap_spawn(original):
                def spawn(path, argv, env, **kwargs):
                    description = recorder.child_description(path, argv, env)
                    pid = original(path, argv, recorder.child_environment(env, description), **kwargs)
                    recorder.children.append(dict(description, pid=pid, kind='posix_spawn'))
                    return pid
                return spawn
            setattr(os, name, wrap_spawn(original))

        threading.Thread.start = start_thread
        _thread.start_new_thread = low_start
        unittest.TestCase.run, unittest.TestSuite.run = case_run, suite_run
        multiprocessing.process.BaseProcess.start = process_start
        subprocess.Popen.__init__ = popen_init
        for name in ('execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe'):
            if name in self.originals:
                setattr(os, name, wrap_exec(name))
        os._exit = exit_process
        if 'fork' in self.originals:
            os.fork = fork
        self.marker('ready', {'pid': self.pid, 'parent_pid': self.parent_pid, 'forked': False})
        threading.settrace(self.trace)
        sys.settrace(self.trace)

    def stop(self):
        if not self.enabled:
            return
        sys.settrace(self.originals['sys_trace'])
        threading.settrace(self.originals['thread_trace'])
        threading.Thread.start = self.originals['thread_start']
        _thread.start_new_thread = self.originals['low_start']
        unittest.TestCase.run, unittest.TestSuite.run = self.originals['case_run'], self.originals['suite_run']
        import multiprocessing.process
        import subprocess
        multiprocessing.process.BaseProcess.start = self.originals['process_start']
        subprocess.Popen.__init__ = self.originals['popen_init']
        os._exit = self.originals['exit']
        if 'fork' in self.originals:
            os.fork = self.originals['fork']
        for name in ('execl', 'execle', 'execlp', 'execlpe', 'execv', 'execve', 'execvp', 'execvpe', 'posix_spawn', 'posix_spawnp'):
            if name in self.originals:
                setattr(os, name, self.originals[name])
        for name in ('_handleClassSetUp', '_tearDownPreviousClass', '_handleModuleFixture', '_handleModuleTearDown'):
            if name in self.originals:
                setattr(unittest.TestSuite, name, self.originals[name])
        self.enabled = False

    def payload(self):
        return {'version': 3, 'pid': self.pid, 'parent_pid': self.parent_pid, 'codes': self.codes,
                'tests': {tid: sorted(indices | self.common) for tid, indices in self.tests.items()},
                'flags': {tid: sorted(self.flags.get(tid, set()) | self.common_flags) for tid in self.tests},
                'children': self.children,
                'scopes': [{'scope': s, 'tests': list(t), 'codes': sorted(c)} for (s, t), c in self.scoped.items()]}

    def checkpoint(self, final=False):
        if not self.output or self.finished or self.failed:
            return
        try:
            with self.lock:
                scoped = []
                for key, values in self.scoped.items():
                    delta = values - self.written_scoped.get(key, set())
                    if delta:
                        scoped.append({'scope': key[0], 'tests': list(key[1]), 'codes': sorted(delta)})
                delta = {'version': 3, 'scope': self.ownership()[0], 'pid': self.pid,
                         'segment': self.segment, 'parent_pid': self.parent_pid,
                         'codes_start': self.written_codes, 'codes': self.codes[self.written_codes:],
                         'tests': {tid: sorted(self.tests.get(tid, set())) for tid in self.dirty},
                         'flags': {tid: sorted(self.flags.get(tid, set())) for tid in self.dirty},
                         'common': sorted(self.common - self.written_common),
                         'common_flags': sorted(self.common_flags), 'scopes': scoped,
                         'children': self.children[self.written_children:]}
                path = os.path.join(self.output, self.stem() + '.jsonl.gz')
                with open(path, 'ab') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as stream:
                    stream.write((json.dumps(delta, sort_keys=True) + '\n').encode())
                self.written_codes = len(self.codes)
                self.written_common.update(self.common)
                self.written_children = len(self.children)
                for key, values in self.scoped.items():
                    self.written_scoped.setdefault(key, set()).update(values)
                self.dirty.clear()
                self.marker('done', {'pid': self.pid, 'state': 'final' if final else 'checkpoint'})
                self.finished = final
        except BaseException as exc:
            self.error(exc)

    def flush(self):
        self.checkpoint(final=True)
        self.stop()


RECORDER = None


def install():
    global RECORDER
    if RECORDER is None:
        RECORDER = Recorder(os.environ.get('PHASE6B_ROOT', '/testbed'), os.environ['PHASE6B_TRACE_OUT'])
        RECORDER.start()
        atexit.register(RECORDER.flush)
    return RECORDER
