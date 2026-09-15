#!/usr/bin/env bash
# Run the test suite in a clean interpreter environment.
#
# This host has ROS 2 Jazzy installed, and its setup script exports
# PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages into every shell. That
# directory is injected ahead of the project venv, so a bare `pytest` autoloads
# ROS's pytest plugins and dies on an unrelated missing dependency:
#
#   ModuleNotFoundError: No module named 'lark'
#
# It is also a correctness hazard well beyond pytest - these are Python 3.12
# packages leaking into a 3.11 venv, so any project process could import a
# module the lockfile never pinned. Clearing PYTHONPATH is the fix; do not
# replace this with a list of `-p no:<plugin>` flags, which only masks pytest.
set -euo pipefail

unset PYTHONPATH

cd "$(dirname "$0")/.."
exec env -u PYTHONPATH .venv/bin/python -m pytest "$@"
