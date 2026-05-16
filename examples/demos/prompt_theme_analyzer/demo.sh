#!/usr/bin/env bash
# Demo: Prompt Theme Analyzer — classify, aggregate, and group themes from image prompts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"

cd "$PROJECT_ROOT"

echo "yamlgraph graph run examples/demos/prompt_theme_analyzer/graph.yaml \\" | tee "$LOG"
echo "  --var source_dir=\"examples/demos/prompt_theme_analyzer/fixtures\" \\" | tee -a "$LOG"
echo "  --var output_path=\"outputs/prompt-theme-report.md\"" | tee -a "$LOG"

yamlgraph graph run examples/demos/prompt_theme_analyzer/graph.yaml \
  --var source_dir="examples/demos/prompt_theme_analyzer/fixtures" \
  --var output_path="outputs/prompt-theme-report.md" 2>&1 | tee -a "$LOG"

echo -e "\n✓ Graph execution completed successfully" | tee -a "$LOG"
