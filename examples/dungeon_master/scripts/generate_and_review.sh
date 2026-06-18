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

echo "📖 Generating book → $OUT (turn-cap $TURN_CAP)"
python examples/dungeon_master/scripts/generate.py \
  --premise "$PREMISE" \
  --out "$OUT" \
  --turn-cap "$TURN_CAP"

echo "🔍 Reviewing $OUT/story.md"
python -m yamlgraph.cli graph run examples/book_reviewer/graph.yaml \
  --var manuscript_path="$OUT" \
  --full

echo "✓ Done: $OUT/story.md  ·  $OUT/review.md"
