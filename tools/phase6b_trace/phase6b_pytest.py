"""Pytest protocol/fixture attribution, loaded with PYTEST_PLUGINS only."""
import functools

import phase6b_trace
import pytest


def pytest_configure(config):
    phase6b_trace.install()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    recorder = phase6b_trace.RECORDER
    recorder.begin(item.nodeid)
    try:
        yield
    finally:
        recorder.end(item.nodeid)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_fixture_setup(fixturedef, request):
    recorder = phase6b_trace.RECORDER
    if fixturedef.scope == 'function':
        yield
        return
    prefix = request.node.nodeid
    targets = [item.nodeid for item in request.session.items if not prefix
               or item.nodeid == prefix or item.nodeid.startswith(prefix + '::')
               or item.nodeid.startswith(prefix + '/')]
    with recorder.scope(targets):
        yield
    # Wrap actual finalizers: shared teardown often runs inside the final test's
    # protocol, so the protocol boundary alone is insufficient attribution.
    def wrap(callback):
        @functools.wraps(callback)
        def finalizer(*args, **kwargs):
            with recorder.scope(targets):
                return callback(*args, **kwargs)
        return finalizer
    fixturedef._finalizers[:] = [wrap(callback) for callback in fixturedef._finalizers]
