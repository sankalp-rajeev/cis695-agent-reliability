"""Network isolation for the container the agent actually runs in.

mini-SWE-agent's Docker environment does not read a `network:` key. It splices
`environment.run_args` into `docker run`, after `--name` and `-w` and before the
image. `--network none` has to be in that list or the container comes up with
the default bridge, which is how `pilot_10` fetched upstream patches.

The configured flag is not evidence. `observed_network_mode` reads
`HostConfig.NetworkMode` off the container Docker started, and a run records
that value — never the value it asked for. The same inspect is the evidence
for the package-cache mask: `HostConfig.Tmpfs` must include
`/opt/miniconda3/pkgs`, or the run stops.
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


#: Empty tmpfs the agent and V4 generator mount over conda's package cache.
PKG_CACHE_TMPFS = "/opt/miniconda3/pkgs"
#: pip's download cache. Its files are named by hash, and some images hold a
#: newer release of the repo under test there (matplotlib 3.7.5 wheel).
PIP_CACHE_TMPFS = "/root/.cache/pip"
MASKED_TMPFS_PATHS = (PKG_CACHE_TMPFS, PIP_CACHE_TMPFS)


def observed_tmpfs(container_id: str) -> dict[str, str]:
    """``HostConfig.Tmpfs`` on the container Docker started, not the args we passed."""
    proc = subprocess.run(
        [docker_bin(), "inspect", "-f", "{{json .HostConfig.Tmpfs}}", container_id],
        capture_output=True, text=True, env=clean_env(), check=False,
    )
    if proc.returncode != 0:
        raise IsolationError(
            f"could not inspect {container_id}: {proc.stderr.strip()[:200]}"
        )
    try:
        parsed = json.loads(proc.stdout.strip() or "null")
    except json.JSONDecodeError as exc:
        raise IsolationError(
            f"unreadable Tmpfs for {container_id}: {proc.stdout!r}"
        ) from exc
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise IsolationError(f"unreadable Tmpfs for {container_id}: {proc.stdout!r}")
    return {str(key): str(value) for key, value in parsed.items()}


def assert_pkg_cache_tmpfs(container_id: str) -> None:
    """Refuse to continue unless the package cache is an empty tmpfs.

    A ``--tmpfs`` flag that never reached ``docker run`` leaves the image's
    conda package cache readable. That is the same failure as a network flag
    that never reached the container: the run would measure the image, not
    the mask.
    """
    mounted = {path.rstrip("/") for path in observed_tmpfs(container_id)}
    missing = [path for path in MASKED_TMPFS_PATHS if path not in mounted]
    if missing:
        raise IsolationError(
            f"container {container_id} HostConfig.Tmpfs does not include "
            f"{missing!r}. The cache mask did not reach the container "
            "Docker started."
        )


def assert_network_none(container_id: str) -> str:
    mode = observed_network_mode(container_id)
    if mode != "none":
        raise IsolationError(
            f"container {container_id} NetworkMode is {mode!r}, not 'none'. "
            "The run args did not reach the container Docker started."
        )
    # Agent and V4 generator both enter through here. The package-cache mask
    # is part of that isolation, checked on the container that actually started.
    assert_pkg_cache_tmpfs(container_id)
    return mode


def label_experiment(run_args: list[str], experiment_id: str) -> list[str]:
    """Add a Docker label naming the experiment, without dropping other args."""
    if not experiment_id:
        return list(run_args)
    marker = f"experiment_id={experiment_id}"
    if marker in run_args:
        return list(run_args)
    return [*run_args, "--label", marker]


def prepare_environment(config: dict, *, experiment_id: str = "") -> dict:
    """Force the agent container onto ``--network none`` before it is started.

    mini-SWE-agent copies ``config["environment"]`` into the container it
    launches. Setting the flag here is what makes it part of that ``docker run``,
    including when the yaml forgot ``run_args``. `experiment_id` becomes a
    Docker label on that same `run_args` list, which is how agent containers
    are told apart when several experiments could be running.
    """
    env = config.setdefault("environment", {})
    env["executable"] = docker_bin()
    env["run_args"] = label_experiment(
        isolate_run_args(list(env.get("run_args") or [])), experiment_id)
    return config


def probe_agent_network(
    agent_config_path: Path, instance_id: str, *, experiment_id: str = "",
) -> str:
    """Start the agent's real environment, read NetworkMode, then stop it.

    The returned string is what Docker attached, so provenance can record it
    without taking the configured value's word for it.
    """
    import yaml
    from minisweagent.run.benchmarks.swebench import get_sb_environment

    config = yaml.safe_load(Path(agent_config_path).read_text(encoding="utf-8"))
    prepare_environment(config, experiment_id=experiment_id)
    env = get_sb_environment(config, {"instance_id": instance_id})
    try:
        if not env.container_id:
            raise IsolationError("agent container did not start")
        return assert_network_none(env.container_id)
    finally:
        env.cleanup()
