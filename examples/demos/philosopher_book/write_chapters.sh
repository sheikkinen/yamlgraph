#!/usr/bin/env bash
# Write multiple chapters in parallel, max 5 concurrent.
# Usage: ./write_chapters.sh [chapters...] [--output-dir DIR]
#   ./write_chapters.sh             # chapters 1-21
#   ./write_chapters.sh 1 2 3       # specific chapters
#   ./write_chapters.sh 1-5         # range shorthand
# Environment: run from project root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OUTPUT_DIR="outputs/philosopher-book"
MAX_CONCURRENT=5

# Parse args
chapters=()
i=1
while [[ $i -le $# ]]; do
  arg="${!i}"
  if [[ "$arg" == "--output-dir" ]]; then
    i=$((i+1)); OUTPUT_DIR="${!i}"
  elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
    for n in $(seq "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"); do chapters+=("$n"); done
  elif [[ "$arg" =~ ^[0-9]+$ ]]; then
    chapters+=("$arg")
  fi
  i=$((i+1))
done

# Default: all 21 chapters
if [[ ${#chapters[@]} -eq 0 ]]; then
  chapters=($(seq 1 21))
fi

cd "$PROJECT_ROOT"
mkdir -p "$OUTPUT_DIR/chapters" "$OUTPUT_DIR/logs"

echo "📚 Writing ${#chapters[@]} chapter(s) in parallel (max $MAX_CONCURRENT concurrent)"
echo "   Output: $OUTPUT_DIR"
echo ""

pids=()
failed=()

run_chapter() {
  local num="$1"
  local log="$OUTPUT_DIR/logs/ch-$(printf '%02d' "$num").log"
  echo "  ▶ Chapter $num starting..."
  if yamlgraph graph run examples/demos/philosopher_book/graph.yaml \
      --var output_dir="$OUTPUT_DIR" \
      --var chapter_num="$num" 2>&1 > "$log"; then
    echo "  ✓ Chapter $num done"
  else
    echo "  ✗ Chapter $num failed (see $log)"
    return 1
  fi
}

# Fan-out with max concurrency gate
active=0
for num in "${chapters[@]}"; do
  run_chapter "$num" &
  pids+=("$! $num")
  active=$((active+1))
  if [[ $active -ge $MAX_CONCURRENT ]]; then
    # Wait for one slot to free up
    wait -n 2>/dev/null || true
    active=$((active-1))
  fi
done

# Wait for all remaining
for entry in "${pids[@]}"; do
  pid="${entry%% *}"
  num="${entry##* }"
  if ! wait "$pid" 2>/dev/null; then
    failed+=("$num")
  fi
done

echo ""
if [[ ${#failed[@]} -eq 0 ]]; then
  echo "✓ All ${#chapters[@]} chapter(s) completed successfully"
  ls -1 "$OUTPUT_DIR/chapters/" | sort
else
  echo "✗ ${#failed[@]} chapter(s) failed: ${failed[*]}"
  exit 1
fi
