#!/bin/bash
# scripts/check_demo_proof.sh — Pre-commit hook for FR-206 demo proof gate.
# Checks staged files: if any examples/demos/<name>/ files are staged
# (excluding demo-output.log itself), require demo-output.log to also be staged.
set -euo pipefail

STAGED=$(git diff --cached --name-only)

# Extract demo directory names that have changes (excluding the log itself)
CHANGED_DEMOS=$(echo "$STAGED" \
  | grep -E '^examples/demos/[^/]+/' \
  | grep -vE 'demo-output\.log$' \
  | sed 's|examples/demos/\([^/]*\)/.*|\1|' \
  | sort -u) || true

if [ -z "$CHANGED_DEMOS" ]; then
  exit 0
fi

MISSING=0
for DEMO in $CHANGED_DEMOS; do
  LOG="examples/demos/${DEMO}/demo-output.log"
  if echo "$STAGED" | grep -qF "$LOG"; then
    echo "✅ Demo proof found: $LOG"
  else
    echo "❌ Demo '$DEMO' changed but no demo-output.log staged"
    MISSING=$((MISSING + 1))
  fi
done

if [ "$MISSING" -gt 0 ]; then
  echo ""
  echo "Run each changed demo and stage the output log:"
  echo "  yamlgraph graph run examples/demos/<name>/graph.yaml --full 2>&1 | tee examples/demos/<name>/demo-output.log"
  exit 1
fi
