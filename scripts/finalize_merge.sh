#!/usr/bin/env bash
# finalize_merge.sh - Post-Merge Finalization for Enforce Pipeline (FR-125)
#
# Automates three post-merge obligations after a PR from the enforce pipeline
# is merged: CHANGELOG entry, FR status update, and diary reflection stub.
#
# Usage:
#   scripts/finalize_merge.sh <feature-request-path>
#
# Prerequisites:
#   - Must be on main branch with clean working tree
#   - FR file must exist at the given path
#   - CHANGELOG.md and docs/diary/ must exist in repo root
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

# ── Step 1: CHANGELOG entry ─────────────────────────────────────────────────

ENTRY="- **${FR_NUM} ${FR_TITLE}**: ${FR_SUMMARY}"
[[ -n "$REQ_ID" ]] && ENTRY="${ENTRY} (${REQ_ID})"

# Duplicate guard — skip if FR already in CHANGELOG
if grep -q "$FR_NUM" CHANGELOG.md; then
    echo "⚠️  ${FR_NUM} already in CHANGELOG, skipping"
else
    # Find "### Added" under "## [Unreleased]" and insert after it
    ADDED_LINE=$(awk '/^## \[Unreleased\]/,/^## \[[0-9]/' CHANGELOG.md | grep -n '### Added' | head -1 | cut -d: -f1 || true)
    if [[ -n "$ADDED_LINE" ]]; then
        UNRELEASED_LINE=$(grep -n '^## \[Unreleased\]' CHANGELOG.md | head -1 | cut -d: -f1)
        INSERT_AT=$((UNRELEASED_LINE + ADDED_LINE - 1))
        # Portable in-place edit using temp file (platform-incompatible otherwise)
        sed "${INSERT_AT}a\\
${ENTRY}
" CHANGELOG.md > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md
    else
        # No ### Added section yet — create one
        UNRELEASED_LINE=$(grep -n '^## \[Unreleased\]' CHANGELOG.md | head -1 | cut -d: -f1)
        sed "${UNRELEASED_LINE}a\\
\\
### Added\\
${ENTRY}
" CHANGELOG.md > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md
    fi
fi

# ── Step 2: FR status update ────────────────────────────────────────────────

sed 's/^\*\*Status:\*\*.*/\*\*Status:\*\* ✅ Implemented/' "$FR_PATH" > "${FR_PATH}.tmp" && mv "${FR_PATH}.tmp" "$FR_PATH"

# ── Step 3: Diary reflection stub ───────────────────────────────────────────

DATE=$(date +%Y-%m-%d)
mkdir -p docs/diary
DIARY_ENTRY="docs/diary/${DATE}-reflection-${FR_NUM}.md"
cat > "$DIARY_ENTRY" << EOF
## ${DATE}: ${FR_NUM} — Implementation Reflection

**Context:** Implemented ${FR_TITLE}.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
EOF

# ── Step 4: Commit finalization ──────────────────────────────────────────────

git add CHANGELOG.md "$FR_PATH" docs/diary/
mkdir -p ./tmp
cat > ./tmp/msg.txt << EOF
chore: ${FR_NUM} post-merge finalization

- CHANGELOG [Unreleased] entry added
- FR status updated to Implemented
- Diary reflection stub appended

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
EOF
git commit -F ./tmp/msg.txt

echo "✅ Finalization complete for ${FR_NUM}"
echo "📝 Edit docs/diary/${DATE}-reflection-${FR_NUM}.md to fill in Trap/Heuristic/Seed"
