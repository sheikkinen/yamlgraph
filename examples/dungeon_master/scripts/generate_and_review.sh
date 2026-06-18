#!/usr/bin/env bash
# Generate a DM v2 book, then auto-review it with examples/book_reviewer.
#
# Usage:
#   examples/dungeon_master/scripts/generate_and_review.sh <out-dir> "<premise>" [turn-cap]
#
# Example:
#   examples/dungeon_master/scripts/generate_and_review.sh \
#     outputs/dungeon-master/10021-BC "10,000 BC, the great thaw — ..." 256
#
# Writes <out-dir>/story.json + story.md (generation) and <out-dir>/review.md (review).
set -euo pipefail

OUT="${1:?usage: generate_and_review.sh <out-dir> \"<premise>\" [turn-cap]}"
PREMISE="${2:?usage: generate_and_review.sh <out-dir> \"<premise>\" [turn-cap]}"
TURN_CAP="${3:-256}"

# Run from the repo root so PYTHONPATH and example paths resolve.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

# Resolve a Python interpreter without requiring the venv to be pre-activated.
# Priority: $PYTHON override > repo-local .venv > python3 > python.
if [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  echo "error: no Python interpreter found (set \$PYTHON or create .venv)" >&2
  exit 1
fi
echo "🐍 Using interpreter: $PY"

echo "📖 Generating book → $OUT (turn-cap $TURN_CAP)"
"$PY" examples/dungeon_master/scripts/generate.py \
  --premise "$PREMISE" \
  --out "$OUT" \
  --turn-cap "$TURN_CAP"

echo "🔍 Reviewing $OUT/story.md"
"$PY" -m yamlgraph.cli graph run examples/book_reviewer/graph.yaml \
  --var manuscript_path="$OUT" \
  --full

# FR-530 Stage 1: emit the reviewer's continuity axis as a per-run, machine-readable
# witness (visibility, NOT a gate -- FR-522 posture). Non-blocking: a missing review or
# a low score never fails the run.
echo "📊 Emitting continuity witness (visibility, not a gate)"
"$PY" -m examples.dungeon_master.scripts.emit_continuity_witness --out "$OUT" \
  || echo "⚠️  continuity witness skipped (non-blocking)"

echo "✓ Done: $OUT/story.md  ·  $OUT/review.md"
