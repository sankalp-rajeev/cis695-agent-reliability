"""Python 3.6-compatible call-only, fork-aware, per-process trace journals."""
# ruff: noqa: BLE001, S110 -- tracing must not perturb test outcomes; errors become markers
import _thread
import atexit
import contextlib
import gzip
import json
import os
import inspect
import shutil
import sys
import threading
import unittest


class Recorder:
    def __init__(self, root, output=None):
        self.root = os.path.abspath(root).rstrip('/') + '/'
        self.output = output
        self.pid, self.parent_pid = os.getpid(), os.getppid()
        self.index, self.codes = {}, []
        self.tests, self.flags = {}, {}
        self.common, self.common_flags = set(), set()
        self.active, self.scopes = None, []
        self.children, self.dirty = [], set()
        self.context, self.lock = threading.local(), threading.RLock()
        self.enabled, self.failed, self.finished = False, False, False
        self.originals = {}
        self.written_codes, self.written_common, self.written_children = 0, set(), 0

    def marker(self, suffix, value):
        if not self.output:
            return
        os.makedirs(self.output, exist_ok=True)
        path = os.path.join(self.output, str(self.pid) + '.' + suffix)
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

    def targets(self):
        inherited = getattr(self.context, 'targets', None)
        if inherited is None:
            inherited = getattr(threading.current_thread(), '_phase6b_targets', None)
        if inherited is not None:
            return inherited
        if self.scopes:
            return self.scopes[-1]
        return [self.active] if self.active else []

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
                        targets = self.targets()
                        if targets:
                            for tid in targets:
                                self.tests.setdefault(tid, set()).add(index)
                                self.dirty.add(tid)
                        else:
                            self.common.add(index)
        except BaseException as exc:
            self.error(exc)
        return None  # noqa: RET501, PLR1711 -- no local trace function is installed

    def begin(self, tid):
        try:
            self.active = tid
            self.tests.setdefault(tid, set())
            self.dirty.add(tid)
        except BaseException as exc:
            self.error(exc)

    def end(self, tid):
        self.active = None
        self.checkpoint()

    @contextlib.contextmanager
    def scope(self, targets):
        self.scopes.append(list(targets))
        try:
            yield
        finally:
            self.scopes.pop()

    def after_fork(self):
        owner = self.active
        self.parent_pid, self.pid = self.pid, os.getpid()
        self.tests, self.flags, self.children, self.dirty = {}, {}, [], set()
        self.scopes = []
        self.context, self.lock = threading.local(), threading.RLock()
        self.written_codes, self.written_common, self.written_children = 0, set(), 0
        self.finished, self.active = False, owner
        self.marker('ready', {'pid': self.pid, 'parent_pid': self.parent_pid, 'forked': True})
        threading.settrace(self.trace)
        sys.settrace(self.trace)

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
            thread._phase6b_targets = list(recorder.targets())
            return recorder.originals['thread_start'](thread, *args, **kwargs)

        def low_start(function, args, kwargs=None):
            targets = list(recorder.targets())

            def followed():
                recorder.context.targets = targets
                sys.settrace(recorder.trace)
                return function(*args, **(kwargs or {}))
            return recorder.originals['low_start'](followed, ())

        def fork():
            targets = list(recorder.targets())
            pid = recorder.originals['fork']()
            try:
                if pid == 0:
                    recorder.after_fork()
                else:
                    recorder.children.append({'pid': pid, 'tests': targets, 'kind': 'fork'})
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
            try:
                return recorder.originals['suite_run'](suite, *args, **kwargs)
            finally:
                recorder.checkpoint()

        import multiprocessing.process
        self.originals['process_start'] = multiprocessing.process.BaseProcess.start

        def process_start(process, *args, **kwargs):
            import multiprocessing
            method = getattr(process, '_start_method', None) or multiprocessing.get_start_method()
            if method != 'fork':
                recorder.incomplete('unfollowed_' + method + '_worker')
            return recorder.originals['process_start'](process, *args, **kwargs)

        import subprocess
        self.originals['popen_init'] = subprocess.Popen.__init__

        def popen_init(process, *args, **kwargs):
            targets = list(recorder.targets())
            result = recorder.originals['popen_init'](process, *args, **kwargs)
            bound = inspect.signature(recorder.originals['popen_init']).bind(process, *args, **kwargs)
            arguments = bound.arguments
            argv = arguments.get('args', [])
            argv = list(argv) if isinstance(argv, (list, tuple)) else [argv]
            executable = arguments.get('executable') or (argv[0] if argv else '')
            environment = arguments.get('env')
            resolved = shutil.which(str(executable), path=(environment or os.environ).get('PATH'))
            python = bool(resolved and os.path.basename(os.path.realpath(resolved)).startswith('python'))
            shebang = None
            if resolved and not python:
                try:
                    with open(resolved, 'rb') as stream:
                        header = stream.read(256)
                    if header.startswith(b'#!'):
                        shebang = header.split(b'\n')[0].decode('utf-8', 'replace')
                        python = 'python' in shebang
                except OSError:
                    pass
            recorder.children.append({'pid': process.pid, 'tests': targets, 'kind': 'exec',
                'executable': str(executable), 'resolved_executable': resolved,
                'argv': [str(a) for a in argv[:3]], 'python': python, 'shebang': shebang,
                'scope': 'test' if targets else 'session',
                'inherited_environment': environment is None or environment.get('PHASE6B_TRACE') == '1'})
            environment = kwargs.get('env')
            if environment is not None and environment.get('PHASE6B_TRACE') != '1':
                recorder.incomplete('child_did_not_inherit_environment', targets)
            return result

        threading.Thread.start = start_thread
        _thread.start_new_thread = low_start
        unittest.TestCase.run, unittest.TestSuite.run = case_run, suite_run
        multiprocessing.process.BaseProcess.start = process_start
        subprocess.Popen.__init__ = popen_init
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
        self.enabled = False

    def payload(self):
        return {'version': 2, 'pid': self.pid, 'parent_pid': self.parent_pid, 'codes': self.codes,
                'tests': {tid: sorted(indices | self.common) for tid, indices in self.tests.items()},
                'flags': {tid: sorted(self.flags.get(tid, set()) | self.common_flags) for tid in self.tests},
                'children': self.children}

    def checkpoint(self, final=False):
        if not self.output or self.finished or self.failed:
            return
        try:
            with self.lock:
                delta = {'version': 2, 'pid': self.pid, 'parent_pid': self.parent_pid,
                         'codes_start': self.written_codes, 'codes': self.codes[self.written_codes:],
                         'tests': {tid: sorted(self.tests.get(tid, set())) for tid in self.dirty},
                         'flags': {tid: sorted(self.flags.get(tid, set())) for tid in self.dirty},
                         'common': sorted(self.common - self.written_common),
                         'common_flags': sorted(self.common_flags),
                         'children': self.children[self.written_children:]}
                path = os.path.join(self.output, str(self.pid) + '.jsonl.gz')
                with open(path, 'ab') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as stream:
                    stream.write((json.dumps(delta, sort_keys=True) + '\n').encode())
                self.written_codes = len(self.codes)
                self.written_common.update(self.common)
                self.written_children = len(self.children)
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
