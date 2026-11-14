"""Environment-only, lazy startup activation; compatible with Python 3.6.

No command-line inspection or eager tracer/framework imports. Never raise.
"""
# ruff: noqa: BLE001, S110 -- startup must never raise, even if error reporting fails
import os


def _error(exc):
    try:
        path = os.path.join(os.environ['PHASE6B_TRACE_OUT'], str(os.getpid()) + '.error')
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(descriptor, repr(exc).encode('utf-8', 'replace') + b'\n')
        finally:
            os.close(descriptor)
    except BaseException:
        try:
            os.write(2, b'phase6b startup failure; error marker unavailable\n')
        except BaseException:
            pass


try:
    if os.environ.get('PHASE6B_TRACE') == '1':
        if os.environ.get('PHASE6B_OWNER'):
            import phase6b_trace
            phase6b_trace.install()
        import builtins
        _original_import = builtins.__import__

        def _lazy_import(name, *args, **kwargs):
            if name.partition('.')[0] in ('django', 'pytest', '_pytest', 'unittest'):
                builtins.__import__ = _original_import
                try:
                    import phase6b_trace
                    phase6b_trace.install()
                except BaseException as exc:
                    _error(exc)
            return _original_import(name, *args, **kwargs)

        builtins.__import__ = _lazy_import
except BaseException as exc:
    _error(exc)
