"""An observed verbose start is TIMEOUT; queued IDs remain NOT_REACHED."""

import pytest

from reliability.verifier.container import _active_test, run_from_capture
from reliability.verifier.regression import TestStatus
from reliability.verifier.selection import TestRunner, django_label


@pytest.mark.parametrize('runner', ['pytest', 'django', 'sympy'])
def test_budget_capture_distinguishes_active_and_pending_ids(runner):
    module = 'tests/test_a.py'
    prefix = '::Case' if runner == 'django' else ''
    ids = tuple(module + prefix + '::test_' + name for name in ('active', 'pending'))
    later = 'tests/test_b.py' + prefix + '::test_later'
    tests = ids + (later,)
    native = tuple(django_label(t) for t in tests) if runner == 'django' else tests
    if runner == 'django':
        raw = b'test_active (test_a.Case) ... '
    elif runner == 'sympy':
        raw = b'tests/test_a.py[2]\ntest_active '
    else:
        raw = (native[0] + ' ').encode()
    events = (
        {'event': 'start', 'batch': 1, 'ids': list(native[:2]), 'module': module, 'offset': 0},
        {'event': 'end', 'batch': 1, 'module': module, 'offset': len(raw), 'timed_out': True,
         'returncode': -9, 'missing_ids': list(native[:2]), 'load_failure': False},
        {'event': 'not_reached', 'module': module, 'ids': list(native[:2]), 'elapsed_s': 1800.0},
        {'event': 'not_reached', 'module': 'tests/test_b.py', 'ids': [native[2]], 'elapsed_s': 1800.1},
        {'event': 'complete', 'timed_out': True},
    )
    result = run_from_capture(TestRunner(runner, ''), tests, runner_log=raw,
                              events=events, budget_s=1800)
    assert result.by_id()[ids[0]].status is TestStatus.TIMEOUT
    assert result.by_id()[ids[0]].elapsed_s == 1800
    for tid in (ids[1], later):
        assert result.by_id()[tid].status is TestStatus.NOT_REACHED
        assert result.by_id()[tid].elapsed_s >= 1800
    assert result.timed_out and result.raw_results == ()


def test_active_start_matching_does_not_accept_a_sibling_substring():
    missing = ('t.py::test_a', 't.py::test_b')
    assert _active_test('pytest', missing, 't.py::test_a_extra ') is None
    assert _active_test('sympy', missing, 'test_a_extra ') is None
    assert _active_test('pytest', missing, '\x1b[1mt.py::test_b\x1b[0m ') == missing[1]
