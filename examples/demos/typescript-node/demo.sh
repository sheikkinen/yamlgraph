#!/usr/bin/env bash
# Demo: TypeScript calls YAMLGraph CLI via child_process.execFile and parses JSON stdout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"

PYTHON_BIN="${YAMLGRAPH_PYTHON:-$PROJECT_ROOT/.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

YAMLGRAPH_BIN="${YAMLGRAPH_BIN:-$PROJECT_ROOT/.venv/bin/yamlgraph}"
if [ ! -x "$YAMLGRAPH_BIN" ]; then
  YAMLGRAPH_BIN="yamlgraph"
fi

echo "=== TypeScript Node Subprocess Demo ===" | tee "$LOG"
echo "Project root: $PROJECT_ROOT" | tee -a "$LOG"

echo -e "\n--- Step 1: Lint graph ---" | tee -a "$LOG"
cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m yamlgraph.cli graph lint "$SCRIPT_DIR/graph.yaml" 2>&1 | tee -a "$LOG"

echo -e "\n--- Step 2: Install TypeScript dependencies ---" | tee -a "$LOG"
cd "$SCRIPT_DIR"
npm install --no-audit --no-fund 2>&1 | tail -5 | tee -a "$LOG"

echo -e "\n--- Step 3: Run TypeScript execFile integration ---" | tee -a "$LOG"
YAMLGRAPH_BIN="$YAMLGRAPH_BIN" npx tsx src/index.ts 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
