#!/usr/bin/env bash
# Ramp Tier-2 changelog gate (pre-commit local hook).
# Blocks commits that change code without a changelog fragment.
# Wire into .pre-commit-config.yaml:
#   - repo: local
#     hooks:
#       - id: changelog-gate
#         name: changelog fragment required
#         entry: scripts/gates/changelog_gate.sh
#         language: system
#         pass_filenames: false
#         stages: [pre-commit]
# Configure watched code paths via GATE_CODE_PATHS (space-separated
# prefixes, default: "src lib").
set -euo pipefail

CODE_PATHS="${GATE_CODE_PATHS:-src lib}"
STAGED=$(git diff --cached --name-only)

touches_code=false
for prefix in $CODE_PATHS; do
  if echo "$STAGED" | grep -q "^${prefix}/"; then
    touches_code=true
    break
  fi
done

if [ "$touches_code" = "true" ] && \
   ! echo "$STAGED" | grep -q '^changelog/unreleased/.*\.md$'; then
  echo "❌ code change without a changelog fragment" >&2
  echo "   add a file under changelog/unreleased/ describing the change" >&2
  exit 1
fi
exit 0
