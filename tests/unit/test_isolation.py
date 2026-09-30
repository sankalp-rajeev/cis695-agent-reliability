"""--network none has to be in the args mini-SWE-agent passes to docker run."""

from __future__ import annotations

import pytest

from reliability.agent.isolation import IsolationError, isolate_run_args, prepare_environment


def test_missing_run_args_gain_network_none_and_keep_rm():
    assert isolate_run_args(None) == ["--rm", "--network", "none"]
    assert isolate_run_args([]) == ["--rm", "--network", "none"]


def test_existing_rm_is_preserved():
    assert isolate_run_args(["--rm"]) == ["--rm", "--network", "none"]


def test_already_isolated_args_are_left_alone():
    args = ["--rm", "--network", "none"]
    assert isolate_run_args(args) == args


def test_any_other_network_is_refused():
    with pytest.raises(IsolationError, match="bridge"):
        isolate_run_args(["--rm", "--network", "bridge"])


def test_prepare_environment_puts_the_flag_where_docker_run_reads_it():
    """mini-SWE-agent splices environment.run_args into the docker run command."""
    config = {"environment": {"environment_class": "docker", "cwd": "/testbed"}}
    prepare_environment(config)
    assert config["environment"]["run_args"][-2:] == ["--network", "none"]
    assert "--rm" in config["environment"]["run_args"]
