#!/bin/bash
# scripts/check_demo_proof.sh — Pre-commit hook for FR-206/FR-325 demo proof gate.
# Checks staged files: if any examples/demos/<name>/ files are staged
# (excluding demo-output.log itself), require demo-output.log to also be staged
# and validate that staged log content shows successful execution.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/demo_log_semantics.sh"

STAGED=$(git diff --cached --name-only --diff-filter=d)

# Extract demo directory names that have changes (excluding the log itself
# and the shared tests/ directory which is test infrastructure, not a demo)
CHANGED_DEMOS=$(echo "$STAGED" \
  | grep -E '^examples/demos/[^/]+/' \
  | grep -vE 'demo-output\.log$' \
  | grep -vE '^examples/demos/tests/' \
  | sed 's|examples/demos/\([^/]*\)/.*|\1|' \
  | sort -u) || true

if [ -z "$CHANGED_DEMOS" ]; then
  exit 0
fi

MISSING=0
INVALID=0
for DEMO in $CHANGED_DEMOS; do
  LOG="examples/demos/${DEMO}/demo-output.log"
  if echo "$STAGED" | grep -qF "$LOG"; then
    TMP_LOG="$(mktemp)"
    if git show ":$LOG" > "$TMP_LOG" 2>/dev/null; then
      if ! validate_demo_output_log_file "$TMP_LOG" "$LOG"; then
        INVALID=$((INVALID + 1))
      fi
    else
      echo "❌ Unable to read staged log content: $LOG"
      INVALID=$((INVALID + 1))
    fi
    rm -f "$TMP_LOG"
  else
    echo "❌ Demo '$DEMO' changed but no demo-output.log staged"
    MISSING=$((MISSING + 1))
  fi
done

if [ "$MISSING" -gt 0 ] || [ "$INVALID" -gt 0 ]; then
  echo ""
  echo "Run each changed demo and stage a successful output log:"
  echo "  yamlgraph graph run examples/demos/<name>/graph.yaml --full 2>&1 | tee examples/demos/<name>/demo-output.log"
  exit 1
fi
