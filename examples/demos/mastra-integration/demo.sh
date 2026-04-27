#!/usr/bin/env bash
# Demo: Mastra TypeScript client discovers YAMLGraph typed MCP tools
#
# Requires: Node.js >= 18, Python 3.11+, yamlgraph installed
# No LLM API key needed — proves tool discovery only.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"

echo "=== Mastra Integration Demo ===" | tee "$LOG"
echo "Project root: $PROJECT_ROOT" | tee -a "$LOG"

# --- Step 1: Validate the graph ---
echo -e "\n--- Step 1: Validate graph ---" | tee -a "$LOG"
"$PROJECT_ROOT/.venv/bin/python" -m yamlgraph.cli graph lint "$SCRIPT_DIR/graph.yaml" 2>&1 | tee -a "$LOG"

# --- Step 2: Install TypeScript dependencies ---
echo -e "\n--- Step 2: Install TS dependencies ---" | tee -a "$LOG"
cd "$SCRIPT_DIR/mastra-app"
npm install --no-audit --no-fund 2>&1 | tail -5 | tee -a "$LOG"

# --- Step 3: Run Mastra MCP client ---
echo -e "\n--- Step 3: Discover typed MCP tools ---" | tee -a "$LOG"
npx tsx src/index.ts 2>&1 | tee -a "$LOG"

echo -e "\n--- Demo complete ---" | tee -a "$LOG"
