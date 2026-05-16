#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"

cd "$PROJECT_ROOT"

mkdir -p outputs/philosopher-book
echo "yamlgraph graph run examples/demos/philosopher_book/graph.yaml \\" | tee "$LOG"
echo '  --var output_dir="outputs/philosopher-book"' | tee -a "$LOG"
yamlgraph graph run examples/demos/philosopher_book/graph.yaml \
  --var output_dir="outputs/philosopher-book" 2>&1 | tee -a "$LOG"
echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
