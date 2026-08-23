#!/usr/bin/env bash
# Ramp Tier-2 diary gate (pre-commit local hook).
# Blocks commits that close out a feature request without a diary
# reflection in the same change set.
# Wire into .pre-commit-config.yaml:
#   - repo: local
#     hooks:
#       - id: diary-gate
#         name: diary reflection required
#         entry: scripts/gates/diary_gate.sh
#         language: system
#         pass_filenames: false
#         stages: [pre-commit]
set -euo pipefail

STAGED=$(git diff --cached --name-only)

if echo "$STAGED" | grep -q '^feature-requests/FR-.*\.md$' && \
   ! echo "$STAGED" | grep -q '^docs/diary/.*\.md$'; then
  echo "❌ feature-request change without a diary reflection" >&2
  echo "   add a docs/diary/ entry (see docs/diary/TEMPLATE.md)" >&2
  exit 1
fi
exit 0
