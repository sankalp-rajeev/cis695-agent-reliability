#!/usr/bin/env bash
# Phase 0.2 gate: no API key has ever been committed.
#
# The checklist states this gate as `git log -p | grep -iE "sk-ant|sk-proj"`, but
# that always matches: docs/checklist.md contains those literals in the line that
# documents the gate, so the gate reports a hit on its own definition. Matching
# bare prefixes is wrong anyway - the thing that is dangerous is a prefix followed
# by actual key material, so the patterns below require the trailing secret.
#
# Scope is full history, not the working tree: a key that was committed and later
# removed is still published in the object store and must be rotated, so it has to
# be caught here rather than by inspecting HEAD.
set -uo pipefail
unset PYTHONPATH

cd "$(dirname "$0")/.."

PATTERNS=(
  'sk-ant-[A-Za-z0-9_-]{16,}'
  'sk-proj-[A-Za-z0-9_-]{16,}'
  'sk-[A-Za-z0-9]{32,}'
  'ghp_[A-Za-z0-9]{20,}'
  'hf_[A-Za-z0-9]{20,}'
  'AKIA[0-9A-Z]{16}'
)

joined="$(IFS='|'; echo "${PATTERNS[*]}")"
found=0

# Matches are reported by location only, never by value. A script that prints
# the secret it found leaves the secret in terminal scrollback, in any log that
# captured the run, and in whatever pastes into a chat or an issue — so the
# audit would itself become a disclosure channel.
echo "scanning full git history for committed credentials..."
if git log -p --all 2>/dev/null | grep -cEi "$joined" | grep -qv '^0$'; then
  echo "FAIL: credential-shaped string found in git history" >&2
  echo "      run: git log -p --all | grep -nEi '<pattern>' to locate it" >&2
  found=1
fi

# Ignored files are excluded because a real .env holding a live key is the
# expected local state - this script's own contract, asserted below, is that it
# must never be *tracked*, not that it must not exist. Scanning it would fail
# every developer machine that is correctly configured, which is the fastest way
# to get a security gate disabled.
echo "scanning tracked and untracked-but-not-ignored files..."
while IFS= read -r file; do
  [ -f "$file" ] || continue
  case "$file" in .venv/*|runs/*|logs/*|*/__pycache__/*) continue ;; esac
  if grep -qEi "$joined" "$file" 2>/dev/null; then
    echo "FAIL: credential-shaped string in $file (line $(
      grep -nEi "$joined" "$file" | head -1 | cut -d: -f1))" >&2
    found=1
  fi
done < <(git ls-files --cached --others --exclude-standard 2>/dev/null)

# A real .env is expected to exist locally; it must never be tracked.
if git ls-files --error-unmatch .env > /dev/null 2>&1; then
  echo "FAIL: .env is tracked by git" >&2
  found=1
fi

if [ "$found" -eq 0 ]; then
  echo "PASS: no credentials in history, working tree, or index"
fi
exit "$found"
