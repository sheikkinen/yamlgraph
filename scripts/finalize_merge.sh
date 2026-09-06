#!/usr/bin/env bash
# finalize_merge.sh - Post-Merge Finalization for Enforce Pipeline (FR-125)
#
# Automates three post-merge obligations after a PR from the enforce pipeline
# is merged: changelog fragment, FR status update, and diary reflection stub.
#
# Usage:
#   scripts/finalize_merge.sh <feature-request-path>
#
# Prerequisites:
#   - Must be on main branch with clean working tree
#   - FR file must exist at the given path
#   - changelog/unreleased/ and docs/diary/ must exist in repo root
#
# Example:
#   git checkout main && git pull
#   scripts/finalize_merge.sh feature-requests/FR-125-enforce-pipeline-finalize.md

set -euo pipefail

# ── Source shared library (FR-258) ──────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$REPO_ROOT/scripts/lib/finalize_lib.sh"

# ── Validate preconditions ──────────────────────────────────────────────────

FR_PATH="${1:-}"

if [[ -z "$FR_PATH" ]]; then
    echo "❌ Usage: $0 <feature-request-path>" >&2
    exit 1
fi

[[ -f "$FR_PATH" ]] || { echo "❌ FR file not found: $FR_PATH" >&2; exit 1; }
git diff --quiet || { echo "❌ Working tree dirty" >&2; exit 1; }
[[ "$(git branch --show-current)" == "main" ]] || { echo "❌ Not on main branch" >&2; exit 1; }

# ── Extract FR metadata ─────────────────────────────────────────────────────

extract_fr_metadata "$FR_PATH"

# ── Step 1: Changelog fragment (FR-179) ─────────────────────────────────────

SLUG=$(echo "$FR_TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
FRAGMENT_PATH="changelog/unreleased/${FR_NUM}-${SLUG}.md"

if [[ -f "$FRAGMENT_PATH" ]]; then
    echo "⚠️  ${FR_NUM} fragment already exists, skipping"
else
    create_changelog_fragment "$FR_NUM" "$FR_TITLE" "$FR_SUMMARY" "$REQ_ID"
    echo "📝 Created changelog fragment: ${FRAGMENT_PATH}"
fi

# ── Step 2: FR status update ────────────────────────────────────────────────

update_fr_status "$FR_PATH"

# ── Step 3: Diary reflection stub ───────────────────────────────────────────

DATE=$(date +%Y-%m-%d)
DIARY_ENTRY="docs/diary/${DATE}-reflection-${FR_NUM}.md"
if [ ! -f "$DIARY_ENTRY" ]; then
    create_diary_stub "$FR_NUM" "$FR_TITLE"
else
    echo "📝 Diary reflection already exists (pipeline-generated), skipping stub"
fi

# ── Step 4: Commit finalization ──────────────────────────────────────────────

git add "changelog/unreleased/" "$FR_PATH"
mkdir -p ./tmp
cat > ./tmp/msg.txt << EOF
chore: ${FR_NUM} post-merge finalization

- Changelog fragment created in changelog/unreleased/
- FR status updated to Implemented
- Diary reflection stub created (untracked)
EOF
git commit -F ./tmp/msg.txt

echo "✅ Finalization complete for ${FR_NUM}"
echo "📝 Fill diary reflection before committing (hook enforced):"
echo "   ${DIARY_ENTRY}"
echo "   Replace [What cognitive trap/lesson/question] placeholders with real content."
