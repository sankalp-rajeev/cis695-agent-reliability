#!/usr/bin/env bash
# Phase 1.3b: build a non-empty, semantically wrong patch that still applies.
#
# Usage: make_wrong_patch.sh <target_instance>
#
# Why this control exists: 1.3 proved only that the harness refuses a no-op. It
# short-circuits empty predictions (`empty_patch_ids`, `completed_instances: 0`)
# and never runs the test suite, so it says nothing about whether FAIL_TO_PASS
# discriminates a wrong patch from a correct one. This control forces the harness
# to actually run the tests on a patch that applies but does not fix the bug.
#
# Construction: borrow the gold patch's target file, but write a change that is
# syntactically valid and behaviourally inert (a trailing comment). Borrowing a
# different instance's gold patch was tried first and rejected - those patches do
# not apply at this instance's base commit, and a patch that fails to apply would
# leave the tests unrun, reproducing the exact blind spot 1.3 already has.
#
# The diff is produced by git inside the target's own evaluation image, so hunk
# headers and context are correct by construction and the patch is guaranteed to
# apply at the base commit.
set -uo pipefail

REPO="$HOME/projects/cis695-agent-reliability"
cd "$REPO"

TARGET="$1"
OUTDIR="runs/1.3b_wrong_patch"
mkdir -p "$OUTDIR/patches"

IMG="$(.venv/bin/python scripts/image_for.py "$TARGET")"
PATCH_FILE="$OUTDIR/patches/${TARGET}.wrong.diff"

# The first file the gold patch touches: the change lands where a real fix would,
# so the control is not trivially distinguishable by file location.
TARGET_FILE="$(.venv/bin/python scripts/oracle_field.py "$TARGET" patch 2>/dev/null \
  | awk '/^--- a\// { sub(/^--- a\//, ""); print; exit }')"

if [ -z "$TARGET_FILE" ]; then
  echo "could not determine target file for $TARGET" >&2
  exit 1
fi

docker run --rm "$IMG" bash -c "
  cd /testbed
  printf '\n# Attempted fix for ${TARGET}: no functional change.\n' >> '${TARGET_FILE}'
  git diff
" > "$PATCH_FILE" 2>/dev/null

if [ ! -s "$PATCH_FILE" ]; then
  echo "empty diff generated for $TARGET" >&2
  exit 1
fi

# Verify in a clean container that the harness will be able to apply it.
if docker run --rm -v "$PWD/$PATCH_FILE:/tmp/p.diff:ro" "$IMG" \
     bash -c 'cd /testbed && git apply --check /tmp/p.diff' 2>/dev/null; then
  lines=$(grep -c '' "$PATCH_FILE")
  echo "$TARGET file=$TARGET_FILE applies=yes patch_lines=$lines"
else
  echo "$TARGET generated patch does not apply" >&2
  exit 1
fi
