"""Read-only Docker image bindings for the frozen paired experiment.

Only the exact frozen tags are inspected. Availability is not source fidelity.
No code in this module starts containers, pulls images or builds images.
"""
from __future__ import annotations

import json
import re
import subprocess

from reliability.env import clean_env
from reliability.verifier.container import _docker_bin


class ImageBindingError(ValueError):
    pass


def docker_read(args):
    return subprocess.run([_docker_bin(), *args], capture_output=True, text=True,
                          timeout=30, env=clean_env(), check=False)


def daemon_id():
    try:
        proc = docker_read(["info", "--format", "{{json .ID}}"])
        value = json.loads(proc.stdout) if proc.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise ImageBindingError(f"Docker daemon inspection failed: {exc}") from exc
    if not isinstance(value, str) or not value.strip():
        raise ImageBindingError("Docker daemon inspection failed: " + proc.stderr[-1000:])
    return value


def inspect_image(tag):
    try:
        proc = docker_read(["image", "inspect", "--format", "{{json .}}", tag])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"availability": "INSPECTION_ERROR", "host_image_id": None,
                "repo_digests": [], "reason": str(exc)}
    if proc.returncode:
        # A daemon/permission/CLI failure must not masquerade as an absent image.
        missing = any(f"No such {kind}: {tag}" in proc.stderr for kind in ("image", "object"))
        return {"availability": "MISSING" if missing else "INSPECTION_ERROR",
                "host_image_id": None, "repo_digests": [], "reason": proc.stderr[-1000:]}
    try:
        record = json.loads(proc.stdout)
        ident, tags, digests = record["Id"], record["RepoTags"], record.get("RepoDigests") or []
        if (not isinstance(ident, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
                or not isinstance(tags, list) or tag not in tags
                or not isinstance(digests, list) or any(not isinstance(d, str) for d in digests)):
            raise ValueError("invalid ID, exact tag absent, or malformed image metadata")
    except (ValueError, KeyError, TypeError) as exc:
        return {"availability": "INSPECTION_ERROR", "host_image_id": None,
                "repo_digests": [], "reason": f"Invalid Docker inspection: {exc}"}
    return {"availability": "AVAILABLE", "host_image_id": ident,
            "repo_digests": sorted(digests), "reason": None}


def binding_record(task, observed):
    historical = task["image_id"]
    actual = observed["host_image_id"]
    comparison = ("IMAGE_UNAVAILABLE" if actual is None else "HISTORICAL_ID_UNAVAILABLE"
                  if historical is None else "MATCH" if actual == historical else "DIFFERENT")
    return {"instance_id": task["instance_id"], "image_tag": task["image_tag"],
            "historical_image_id": historical, "historical_image_digest": task["image_digest"],
            "historical_environment_status": task["environment_status"], **observed,
            "historical_id_comparison": comparison,
            "historical_id_mismatch": actual != historical if actual and historical else None,
            "source_fidelity": "NOT_VERIFIED"}


def validate_record(task, binding):
    status, ident = binding["availability"], binding["host_image_id"]
    if status == "AVAILABLE":
        valid = isinstance(ident, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
    else:
        valid = status == "MISSING" and ident is None
    if not valid:
        raise ImageBindingError(f"Unverified host image binding: {task['instance_id']}")
    observed = {key: binding[key] for key in ("availability", "host_image_id", "repo_digests", "reason")}
    if binding != binding_record(task, observed):
        raise ImageBindingError(f"Image binding historical metadata/identity mismatch: {task['instance_id']}")


def verify_current(task, binding):
    validate_record(task, binding)
    current = inspect_image(binding["image_tag"])
    if (current["availability"] != binding["availability"]
            or current["host_image_id"] != binding["host_image_id"]):
        raise ImageBindingError(f"Host image drift for {task['instance_id']} ({binding['image_tag']}): "
                                f"frozen={binding['availability']}/{binding['host_image_id']}, "
                                f"current={current['availability']}/{current['host_image_id']}; "
                                f"{current['reason']}")


def capture(tasks):
    try:
        daemon, error = daemon_id(), None
    except ImageBindingError as exc:
        daemon, error = None, str(exc)
    rows = []
    for task in tasks:
        observed = inspect_image(task["image_tag"]) if daemon else {
            "availability": "INSPECTION_ERROR", "host_image_id": None, "repo_digests": [], "reason": error}
        rows.append(binding_record(task, observed))
    return {"docker_daemon_id": daemon, "rows": rows,
            "ready": daemon is not None and all(r["availability"] != "INSPECTION_ERROR" for r in rows)}
