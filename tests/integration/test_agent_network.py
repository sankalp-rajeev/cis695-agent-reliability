"""The container mini-SWE-agent starts must actually be on network none.

A flag that exists only in our config is how the previous pilot fetched
upstream patches. This starts DockerEnvironment through the same
``get_sb_environment`` path the agent uses, then reads HostConfig off the
container Docker created.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from reliability.agent.isolation import (
    assert_network_none,
    docker_bin,
    prepare_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ID = "psf__requests-1921"


def _docker_ready() -> bool:
    docker = docker_bin()
    if not Path(docker).exists() and shutil.which(docker) is None:
        return False
    proc = subprocess.run(
        [docker, "image", "inspect",
         "swebench/sweb.eval.x86_64.psf_1776_requests-1921:latest"],
        capture_output=True, check=False,
    )
    return proc.returncode == 0


@pytest.mark.skipif(not _docker_ready(), reason="requests eval image is not local")
def test_network_none_is_on_the_launched_container():
    from minisweagent.run.benchmarks.swebench import get_sb_environment

    config = yaml.safe_load(
        (REPO_ROOT / "configs/agent/swebench_claim.yaml").read_text(encoding="utf-8")
    )
    # Drop whatever the file says and let the runner's injection supply the
    # flag, so this does not pass merely because the yaml was edited.
    config["environment"].pop("run_args", None)
    prepare_environment(config)

    env = get_sb_environment(config, {"instance_id": INSTANCE_ID})
    try:
        assert env.container_id
        assert "--network" in env.config.run_args
        assert env.config.run_args[env.config.run_args.index("--network") + 1] == "none"
        assert assert_network_none(env.container_id) == "none"
    finally:
        env.cleanup()
