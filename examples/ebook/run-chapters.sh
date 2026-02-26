#!/bin/bash
# Run all eBook chapters with controlled parallelism.
# Usage: ./run-chapters.sh [workers] [output_dir]
#   workers:    number of parallel chapter runs (default: 2)
#   output_dir: output directory (default: docs/ebook/v1)
#
# FR-104: Parallel Chapter Generation with Worker Pools
set -euo pipefail

WORKERS=${1:-2}
OUTPUT_DIR=${2:-docs/ebook/v1}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Chapter definitions: graph-file:output-filename
CHAPTERS=(
  "graph-ch00.yaml:00-introduction.md"
  "graph-ch01.yaml:01-doctrine.md"
  "graph-ch02.yaml:02-precommit-gates.md"
  "graph-ch03.yaml:03-chaplain-pipeline.md"
  "graph-ch04.yaml:04-inquisitor.md"
  "graph-ch05.yaml:05-diary-system.md"
  "graph-ch06.yaml:06-traceability.md"
  "graph-ch07.yaml:07-yamlgraph-core.md"
  "graph-ch08.yaml:08-wizard.md"
)

TOTAL=${#CHAPTERS[@]}
FAILED=0
SUCCEEDED=0

echo "═══════════════════════════════════════════════════════"
echo "  eBook Pipeline — ${TOTAL} chapters, ${WORKERS} workers"
echo "  Output: ${OUTPUT_DIR}"
echo "═══════════════════════════════════════════════════════"
echo ""

mkdir -p "${OUTPUT_DIR}"

run_chapter() {
  local spec=$1
  local graph="${spec%%:*}"
  local filename="${spec##*:}"
  local graph_path="${SCRIPT_DIR}/${graph}"

  echo "[START] ${graph} → ${filename}"

  if yamlgraph graph run "${graph_path}" \
    --var output_dir="${OUTPUT_DIR}" \
    --var filename="${filename}" \
    --full 2>&1; then
    echo "[DONE]  ${filename} ✓"
    return 0
  else
    echo "[FAIL]  ${filename} ✗"
    return 1
  fi
}

export -f run_chapter
export SCRIPT_DIR OUTPUT_DIR

printf '%s\n' "${CHAPTERS[@]}" | xargs -P "${WORKERS}" -I {} bash -c 'run_chapter "$@"' _ {}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Pipeline complete. Check ${OUTPUT_DIR}/ for output."
echo "═══════════════════════════════════════════════════════"
