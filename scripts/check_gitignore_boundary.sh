#!/bin/bash
# scripts/check_gitignore_boundary.sh — Pre-commit hook for FR-372.
# Blocks staged .gitignore changes by default. Allows explicit human-intent
# bypass only with:
#   YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1
#   YAMLGRAPH_GITIGNORE_REASON containing FR-<num> or gh-<num>
set -euo pipefail

DIARY_REF="docs/diary/2026-05-12-private-repo-dataloss-recovery.md"

STAGED=$(git diff --cached --name-only --diff-filter=ACMR)
GITIGNORE_CHANGES=$(printf "%s\n" "$STAGED" | grep -E '(^|/)\.gitignore$' || true)

if [ -z "$GITIGNORE_CHANGES" ]; then
  exit 0
fi

print_gitignore_changes() {
  while IFS= read -r path; do
    [ -n "$path" ] && printf "  - %s\n" "$path"
  done <<< "$GITIGNORE_CHANGES"
}

ALLOW="${YAMLGRAPH_ALLOW_GITIGNORE_EDIT:-}"
REASON="${YAMLGRAPH_GITIGNORE_REASON:-}"

if [ "$ALLOW" = "1" ]; then
  if [ -z "$REASON" ]; then
    echo "❌ .gitignore boundary guard: bypass requested without YAMLGRAPH_GITIGNORE_REASON."
    echo "Boundary guard fails closed when explicit reason is missing."
    echo "Reason must be non-empty and contain FR-<num> or gh-<num>."
    exit 1
  fi

  if ! printf "%s\n" "$REASON" | grep -Eq '(FR-[0-9]+|gh-[0-9]+)'; then
    echo "❌ .gitignore boundary guard: invalid YAMLGRAPH_GITIGNORE_REASON."
    echo "Reason must include FR-<num> or gh-<num> trace token."
    echo "Given: $REASON"
    exit 1
  fi

  echo "⚠️  .gitignore boundary bypass accepted (explicit intent)."
  echo "Reason: $REASON"
  echo "Staged .gitignore path(s):"
  print_gitignore_changes
  exit 0
fi

echo "❌ .gitignore boundary guard: staged .gitignore changes are blocked by default."
echo "Boundary risk: ignore rules define tracking/privacy boundaries for local artifacts."
echo "Incident reference: $DIARY_REF"
echo ""
echo "Staged .gitignore path(s):"
print_gitignore_changes
echo ""
echo "If this edit is intentional, use explicit bypass with traceable reason:"
echo '  YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1 \'
echo '  YAMLGRAPH_GITIGNORE_REASON="FR-372 adjust ignore boundary for <reason>" \'
echo "  git commit"
echo ""
echo "Do not use --no-verify as the normal path."
exit 1
