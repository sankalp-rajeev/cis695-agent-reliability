"""Read-only, Python 3.5-compatible first-entry tracer for Phase 6a diagnostics.

Only sys.settrace is used. Nothing selects tests or changes test functions.
Enable with RUNTIME_TRACE_ENABLE=1, a JSON RUNTIME_TRACE_CONFIG, and an
RUNTIME_TRACE_OUTPUT directory. Disabled mode installs no tracing hook.
"""
import os
import sys


def _install():
    if os.environ.get('RUNTIME_TRACE_ENABLE') != '1':
        return
    import atexit
    import json
    import time
    config_path = os.environ['RUNTIME_TRACE_CONFIG']
    with open(config_path) as stream:
        config = json.load(stream)
    output = os.environ['RUNTIME_TRACE_OUTPUT']
    root = config.get('source_root', '/testbed').rstrip('/') + '/'
    functions = {}
    for row in config['changed_functions']:
        for start in set([row['decorator_start'], row['start']]):
            functions.setdefault((row['path'], row['name'], start), []).append(row)
    test = config['test_function']
    test_starts = set([test['decorator_start'], test['start']])
    state = {'pid': None, 'seen': set(), 'events': 0, 'failed': False,
             'test_entries': 0, 'thread_starts': 0}
    installed_pid = os.getpid()

    def write(value):
        pid = os.getpid()
        path = os.path.join(output, 'trace-%s.jsonl' % pid)
        payload = (json.dumps(value, sort_keys=True) + '\n').encode('utf-8')
        descriptor = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o666)
        try:
            os.write(descriptor, payload)
        finally:
            os.close(descriptor)

    def process():
        pid = os.getpid()
        if state['pid'] != pid:
            state['pid'] = pid
            state['seen'] = set()
            write({'event': 'installed', 'pid': pid, 'ppid': os.getppid(),
                   'fork_after_install': pid != installed_pid,
                   'python': sys.version, 'sys_trace_only': True,
                   'test_id': config['test_id'], 'tree': config['tree']})

    def frame_record(frame):
        code = frame.f_code
        filename = code.co_filename
        path = filename[len(root):] if filename.startswith(root) else filename
        receiver = frame.f_locals.get('self')
        receiver_type = type(receiver) if receiver is not None else None
        mro = []
        if receiver_type is not None:
            for cls in type.__getattribute__(receiver_type, '__mro__')[:12]:
                mro.append(cls.__module__ + '.' + cls.__name__)
        return {'path': path, 'name': code.co_name,
                'code_firstline': code.co_firstlineno, 'line': frame.f_lineno,
                'code_qualname': getattr(code, 'co_qualname', None),
                'receiver_mro': mro}

    def trace(frame, event, arg):
        if event != 'call' or state['failed']:
            return None
        code = frame.f_code
        filename = code.co_filename
        # Observe thread starts from the traced thread, without patching Thread
        # or using threading.settrace. Their execution remains a disclosed limit.
        if filename.endswith('/threading.py') and code.co_name == 'start':
            process()
            state['thread_starts'] += 1
            write({'event': 'thread_start', 'pid': os.getpid(),
                   'thread_name': getattr(frame.f_locals.get('self'), 'name', None)})
            return None
        if not filename.startswith(root):
            return None
        if (filename[len(root):] == test['path'] and code.co_name == test['name']
                and code.co_firstlineno in test_starts):
            process()
            state['test_entries'] += 1
            write({'event': 'test_enter', 'pid': os.getpid(),
                   'path': test['path'], 'name': test['name']})
        candidates = functions.get((filename[len(root):], code.co_name, code.co_firstlineno))
        if not candidates:
            return None
        try:
            process()
            frames = []
            current = frame
            while current is not None and len(frames) < 256:
                frames.append(frame_record(current))
                current = current.f_back
            frames.reverse()
            indexes = [n for n, item in enumerate(frames)
                       if item['path'] == test['path'] and item['name'] == test['name']
                       and item['code_firstline'] in test_starts]
            index = indexes[-1] if indexes else None
            for row in candidates:
                phases = ['first_any']
                if index is not None:
                    phases.append('first_under_test')
                for phase in phases:
                    key = (row['id'], phase)
                    if key in state['seen']:
                        continue
                    state['seen'].add(key)
                    write({'event': 'entry', 'pid': os.getpid(), 'ppid': os.getppid(),
                           'fork_after_install': os.getpid() != installed_pid,
                           'function_id': row['id'], 'phase': phase,
                           'stack': frames, 'stack_truncated': current is not None,
                           'test_frame_index': index,
                           'hops': len(frames) - 1 - index if index is not None else None,
                           'monotonic': time.monotonic()})
                    state['events'] += 1
        except BaseException as exc:
            state['failed'] = True
            try:
                write({'event': 'trace_error', 'pid': os.getpid(),
                       'error_type': type(exc).__name__, 'message': str(exc)[:500]})
            except BaseException:
                os.write(2, b'RUNTIME_TRACE_RECORDING_ERROR\n')
            sys.settrace(None)
        return None

    def finish():
        active = sys.gettrace() is trace
        sys.settrace(None)
        try:
            process()
            write({'event': 'finished', 'pid': os.getpid(),
                   'entries': state['events'], 'failed': state['failed'],
                   'test_entries': state['test_entries'],
                   'thread_starts': state['thread_starts'],
                   'hook_active_at_finish': active})
        except BaseException:
            os.write(2, b'RUNTIME_TRACE_FINISH_ERROR\n')

    process()
    atexit.register(finish)
    sys.settrace(trace)


_install()
