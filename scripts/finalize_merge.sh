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

FR_HEADING=$(grep -m1 '^# ' "$FR_PATH" | sed 's/^#[# ]*//')
FR_NUM=$(basename "$FR_PATH" .md | grep -oE 'FR-[0-9]+')
# Strip "Feature Request: " prefix and FR number to get clean title
FR_TITLE=$(echo "$FR_HEADING" | sed 's/^Feature Request: //' | sed "s/^${FR_NUM} //")
REQ_ID=$(grep -oE 'REQ-YG-[0-9]+' "$FR_PATH" | head -1 || true)

# Extract first content line from ## Summary for the CHANGELOG description
FR_SUMMARY=$(awk '/^## Summary/{found=1; next} found && /^[^ #]/{print; exit}' "$FR_PATH")

# ── Step 1: Changelog fragment (FR-179) ─────────────────────────────────────

ENTRY="- **${FR_NUM} ${FR_TITLE}**: ${FR_SUMMARY}"
[[ -n "$REQ_ID" ]] && ENTRY="${ENTRY} (${REQ_ID})"

SLUG=$(echo "$FR_TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
FRAGMENT_PATH="changelog/unreleased/${FR_NUM}-${SLUG}.md"

mkdir -p changelog/unreleased

# Duplicate guard — skip if fragment already exists
if [[ -f "$FRAGMENT_PATH" ]]; then
    echo "⚠️  ${FR_NUM} fragment already exists, skipping"
else
    REQ_LINE=""
    [[ -n "$REQ_ID" ]] && REQ_LINE="req: ${REQ_ID}"

    cat > "$FRAGMENT_PATH" << FRAGMENT
---
type: feat
scope: ${SLUG%%-*}
${REQ_LINE}
---
${ENTRY}
FRAGMENT
    echo "📝 Created changelog fragment: ${FRAGMENT_PATH}"
fi

# ── Step 2: FR status update ────────────────────────────────────────────────

sed 's/^\*\*Status:\*\*.*/\*\*Status:\*\* ✅ Implemented/' "$FR_PATH" > "${FR_PATH}.tmp" && mv "${FR_PATH}.tmp" "$FR_PATH"

# ── Step 3: Diary reflection stub ───────────────────────────────────────────

DATE=$(date +%Y-%m-%d)
mkdir -p docs/diary
DIARY_ENTRY="docs/diary/${DATE}-reflection-${FR_NUM}.md"
if [ ! -f "$DIARY_ENTRY" ]; then
    cat > "$DIARY_ENTRY" << EOF
## ${DATE}: ${FR_NUM} — Implementation Reflection

**Context:** Implemented ${FR_TITLE}.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
EOF
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
