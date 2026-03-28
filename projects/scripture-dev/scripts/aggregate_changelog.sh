#!/usr/bin/env bash
# aggregate_changelog.sh — Generate CHANGELOG.md from fragment files.
#
# Reads changelog/unreleased/ and changelog/{version}/ directories,
# groups entries by type (Added/Fixed/Removed), and outputs Keep a Changelog format.
#
# Shell-only — no interpreter dependencies beyond bash.
#
# Usage: ./scripts/aggregate_changelog.sh > CHANGELOG.md
set -euo pipefail

CHANGELOG_DIR="${1:-changelog}"

# Section mapping: type → heading
section_heading() {
    case "$1" in
        feat)    echo "Added" ;;
        fix)     echo "Fixed" ;;
        removal) echo "Removed" ;;
        *)       echo "Changed" ;;
    esac
}

# Parse YAML front matter from a fragment file
# Extracts type field value
parse_type() {
    sed -n '/^---$/,/^---$/p' "$1" | grep '^type:' | sed 's/^type: *//' | tr -d "'" | tr -d '"'
}

# Extract body (everything after the second ---)
parse_body() {
    awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$1"
}

# Collect entries from a directory, grouped by type
render_section() {
    local dir="$1"
    local added="" fixed="" removed="" changed=""

    if [ ! -d "$dir" ]; then
        return
    fi

    for fragment in "$dir"/*.md; do
        [ -f "$fragment" ] || continue
        local ftype
        ftype=$(parse_type "$fragment")
        local body
        body=$(parse_body "$fragment")
        [ -z "$body" ] && continue

        case "$ftype" in
            feat)    added="${added}${body}"$'\n' ;;
            fix)     fixed="${fixed}${body}"$'\n' ;;
            removal) removed="${removed}${body}"$'\n' ;;
            *)       changed="${changed}${body}"$'\n' ;;
        esac
    done

    if [ -n "$added" ]; then
        echo "### Added"
        echo ""
        echo "$added"
    fi
    if [ -n "$removed" ]; then
        echo "### Removed"
        echo ""
        echo "$removed"
    fi
    if [ -n "$fixed" ]; then
        echo "### Fixed"
        echo ""
        echo "$fixed"
    fi
    if [ -n "$changed" ]; then
        echo "### Changed"
        echo ""
        echo "$changed"
    fi
}

# --- Main ---

echo "# Changelog"
echo ""

# Unreleased
echo "## [Unreleased]"
echo ""
render_section "$CHANGELOG_DIR/unreleased"

# Versioned releases (sorted descending)
if [ -d "$CHANGELOG_DIR" ]; then
    versions=$(find "$CHANGELOG_DIR" -maxdepth 1 -mindepth 1 -type d \
        -not -name unreleased \
        -exec basename {} \; 2>/dev/null | sort -t. -k1,1nr -k2,2nr -k3,3nr)

    for version in $versions; do
        echo "## [$version]"
        echo ""
        render_section "$CHANGELOG_DIR/$version"
    done
fi
