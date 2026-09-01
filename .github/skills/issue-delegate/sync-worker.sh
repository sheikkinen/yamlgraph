#!/usr/bin/env bash
# sync-worker.sh — deploy the canonical FR-949 worker bundle to a comms-repo
# checkout at frozen paths, then verify byte equality (AC-03, REQ-YG-637).
# Never copies credentials or control-side files (submit.sh, SKILL.md).
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ $# -ne 1 ]; then
  echo "usage: sync-worker.sh <comms-checkout-dir>" >&2
  exit 2
fi
DEST=$1
if [ ! -d "$DEST" ]; then
  echo "sync-worker: destination does not exist: $DEST" >&2
  exit 2
fi

# Frozen deployment map — the only files that ever reach the comms repo.
PAIRS=(
  "delegate.yml:.github/workflows/delegate.yml"
  "models.py:.github/delegate/models.py"
  "worker.py:.github/delegate/worker.py"
  "windows_job.ps1:.github/delegate/windows_job.ps1"
)

for pair in "${PAIRS[@]}"; do
  src="${pair%%:*}"
  rel="${pair#*:}"
  mkdir -p "$DEST/$(dirname "$rel")"
  cp "$SCRIPT_DIR/$src" "$DEST/$rel"
done

# Verify byte equality after deployment.
for pair in "${PAIRS[@]}"; do
  src="${pair%%:*}"
  rel="${pair#*:}"
  if ! cmp -s "$SCRIPT_DIR/$src" "$DEST/$rel"; then
    echo "sync-worker: deployed copy differs: $rel" >&2
    exit 1
  fi
done

echo "sync-worker: bundle deployed byte-identical to $DEST"
