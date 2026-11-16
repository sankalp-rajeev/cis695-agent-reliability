"""Run the full unit suite with explicit network and repository label guards."""

import os
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def guard(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise RuntimeError("network forbidden during policy offline tests")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).absolute()
        if ROOT in path.parents and (
            path.name == "oracle_record.json"
            or any(p in path.parts for p in ("phase4_posthoc", "grader_gap", "posthoc_labels"))
            or (path.parent == ROOT / "docs" and path.name.startswith("results_100."))
        ):
            raise RuntimeError("label source forbidden during policy offline tests")


def pytest_sessionstart(session):
    sys.addaudithook(guard)


if __name__ == "__main__":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    # Match python -m pytest: repository test helpers import via tests.unit.
    sys.path.insert(0, str(ROOT))
    import pytest

    raise SystemExit(pytest.main(["tests/unit", *sys.argv[1:]], plugins=[sys.modules[__name__]]))
