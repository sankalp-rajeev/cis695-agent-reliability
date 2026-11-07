"""All repository/tree launches request CPU shares, never a CPU-time cap."""

import pytest

from reliability.agent.isolation import IsolationError, prepare_environment
from reliability.verifier.container import TaskContainer


@pytest.mark.parametrize('task', ['django__django-13297', 'astropy__astropy-13977', 'sympy__sympy-13480'])
@pytest.mark.parametrize('patched', [False, True])
def test_every_task_tree_uses_cpu_shares(task, patched):
    container = TaskContainer(task, '')
    container._patch_applied = patched
    args = container.run_args()
    assert args[args.index('--cpu-shares') + 1] == '2048'
    assert args.count('--cpu-shares') == 1
    assert '--cpus' not in args
    assert args[args.index('--network') + 1] == 'none'


@pytest.mark.parametrize('args', [[], ['--cpu-shares', '1024'], ['--cpu-shares=512']])
def test_agent_and_generator_environment_also_uses_2048(args):
    config = {'environment': {'run_args': args}}
    prepare_environment(config)
    prepare_environment(config)
    result = config['environment']['run_args']
    assert result.count('--cpu-shares') == 1
    assert result[result.index('--cpu-shares') + 1] == '2048'
    assert result[result.index('--network') + 1] == 'none'


def test_agent_cpu_time_cap_is_refused():
    with pytest.raises(IsolationError, match='time cap'):
        prepare_environment({'environment': {'run_args': ['--cpus=2']}})
