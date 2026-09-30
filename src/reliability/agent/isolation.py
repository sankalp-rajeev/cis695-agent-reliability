"""Network isolation for the container the agent actually runs in.

mini-SWE-agent's Docker environment does not read a `network:` key. It splices
`environment.run_args` into `docker run`, after `--name` and `-w` and before the
image. `--network none` has to be in that list or the container comes up with
the default bridge, which is how `pilot_10` fetched upstream patches.

The configured flag is not evidence. `observed_network_mode` reads
`HostConfig.NetworkMode` off the container Docker started, and a run records
that value — never the value it asked for.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from reliability.env import clean_env

_DOCKER_CLI = Path("/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker")


class IsolationError(RuntimeError):
    """The container that launched is not the isolation that was requested."""


def docker_bin() -> str:
    found = shutil.which("docker")
    if found and Path(found).exists():
        return found
    if _DOCKER_CLI.exists():
        return str(_DOCKER_CLI)
    return "docker"


def isolate_run_args(run_args: list[str] | None) -> list[str]:
    """Return docker run args that include ``--network none``.

    A config that asks for any other network is refused rather than overridden
    quietly: overriding would let a run claim one posture while a reader of the
    config sees another.
    """
    args = list(run_args) if run_args else ["--rm"]
    if "--network" in args:
        index = args.index("--network")
        value = args[index + 1] if index + 1 < len(args) else ""
        if value != "none":
            raise IsolationError(
                f"refusing to launch with --network {value!r}; agent containers "
                "must be --network none"
            )
        return args
    return [*args, "--network", "none"]


def observed_network_mode(container_id: str) -> str:
    """What Docker actually attached this container to.

    ``docker inspect`` of ``HostConfig.NetworkMode``, not the args we passed.
    """
    proc = subprocess.run(
        [docker_bin(), "inspect", "-f", "{{json .HostConfig.NetworkMode}}", container_id],
        capture_output=True, text=True, env=clean_env(), check=False,
    )
    if proc.returncode != 0:
        raise IsolationError(
            f"could not inspect {container_id}: {proc.stderr.strip()[:200]}"
        )
    mode = json.loads(proc.stdout.strip() or '""')
    if not isinstance(mode, str) or not mode:
        raise IsolationError(f"unreadable NetworkMode for {container_id}: {proc.stdout!r}")
    return mode


def assert_network_none(container_id: str) -> str:
    mode = observed_network_mode(container_id)
    if mode != "none":
        raise IsolationError(
            f"container {container_id} NetworkMode is {mode!r}, not 'none'. "
            "The run args did not reach the container Docker started."
        )
    return mode


def prepare_environment(config: dict) -> dict:
    """Force the agent container onto ``--network none`` before it is started.

    mini-SWE-agent copies ``config["environment"]`` into the container it
    launches. Setting the flag here is what makes it part of that ``docker run``,
    including when the yaml forgot ``run_args``.
    """
    env = config.setdefault("environment", {})
    env["executable"] = docker_bin()
    env["run_args"] = isolate_run_args(list(env.get("run_args") or []))
    return config


def probe_agent_network(agent_config_path: Path, instance_id: str) -> str:
    """Start the agent's real environment, read NetworkMode, then stop it.

    The returned string is what Docker attached, so provenance can record it
    without taking the configured value's word for it.
    """
    import yaml
    from minisweagent.run.benchmarks.swebench import get_sb_environment

    config = yaml.safe_load(Path(agent_config_path).read_text(encoding="utf-8"))
    prepare_environment(config)
    env = get_sb_environment(config, {"instance_id": instance_id})
    try:
        if not env.container_id:
            raise IsolationError("agent container did not start")
        return assert_network_none(env.container_id)
    finally:
        env.cleanup()
