#!/usr/bin/env bash
# finalize_lib.sh — Shared finalization functions (FR-258)
#
# Extracted from scripts/finalize_merge.sh to eliminate duplication
# between the manual script and the watch.sh automation loop.
#
# Functions:
#   extract_fr_metadata  — sets FR_HEADING, FR_NUM, FR_TITLE, REQ_ID, FR_SUMMARY
#   create_changelog_fragment — creates changelog/unreleased/ fragment (idempotent)
#   update_fr_status     — updates FR **Status:** to ✅ Implemented
#   create_diary_stub    — creates docs/diary/ reflection stub (idempotent)
#
# Usage:
#   source scripts/lib/finalize_lib.sh

# Extract FR metadata from an FR file path.
# Sets global variables: FR_HEADING, FR_NUM, FR_TITLE, REQ_ID, FR_SUMMARY
extract_fr_metadata() {
    local fr_path="$1"
    FR_HEADING=$(grep -m1 '^# ' "$fr_path" | sed 's/^#[# ]*//')
    FR_NUM=$(basename "$fr_path" .md | grep -oE 'FR-[0-9]+')
    FR_TITLE=$(echo "$FR_HEADING" | sed 's/^Feature Request: //' | sed "s/^${FR_NUM} //")
    REQ_ID=$(grep -oE 'REQ-YG-[0-9]+' "$fr_path" | head -1 || true)
    FR_SUMMARY=$(awk '/^## Summary/{found=1; next} found && /^[^ #]/{print; exit}' "$fr_path")
}

# Create changelog fragment in changelog/unreleased/ — idempotent (skips if exists).
# Args: fr_num fr_title fr_summary req_id
create_changelog_fragment() {
    local fr_num="$1" fr_title="$2" fr_summary="$3" req_id="$4"
    local slug entry frag_path

    slug=$(echo "$fr_title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
    frag_path="changelog/unreleased/${fr_num}-${slug}.md"

    mkdir -p changelog/unreleased
    [[ -f "$frag_path" ]] && return 0

    entry="- **${fr_num} ${fr_title}**: ${fr_summary}"
    [[ -n "$req_id" ]] && entry="${entry} (${req_id})"

    {
        echo "---"
        echo "type: feat"
        echo "scope: ${slug%%-*}"
        [[ -n "$req_id" ]] && echo "req: ${req_id}"
        echo "---"
        echo "${entry}"
    } > "$frag_path"
}

# Update FR status to ✅ Implemented.
# Args: fr_path
update_fr_status() {
    local fr_path="$1"
    sed 's/^\*\*Status:\*\*.*/\*\*Status:\*\* ✅ Implemented/' "$fr_path" > "${fr_path}.tmp" \
        && mv "${fr_path}.tmp" "$fr_path"
}

# Create diary reflection stub in docs/diary/ — idempotent (skips if exists).
# Args: fr_num fr_title
create_diary_stub() {
    local fr_num="$1" fr_title="$2"
    local diary_date diary_entry

    diary_date=$(date +%Y-%m-%d)
    mkdir -p docs/diary
    diary_entry="docs/diary/${diary_date}-reflection-${fr_num}.md"

    [[ -f "$diary_entry" ]] && return 0

    cat > "$diary_entry" << DIARY
## ${diary_date}: ${fr_num} — Implementation Reflection

**Context:** Implemented ${fr_title}.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
DIARY
}
