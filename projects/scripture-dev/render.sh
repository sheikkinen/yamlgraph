#!/usr/bin/env bash
# render.sh — Parameterize template files from scripture.yaml configuration.
#
# Reads _templates/ source files and renders them to their target locations,
# substituting __PLACEHOLDER__ markers with values from scripture.yaml.
#
# Usage: ./render.sh
# Re-runnable: always renders from _templates/ (source of truth).
set -euo pipefail

CONFIG="scripture.yaml"

if [ ! -f "$CONFIG" ]; then
    echo "ERROR: $CONFIG not found. Run from scripture-dev root." >&2
    exit 1
fi

# Parse scripture.yaml (POSIX, no PyYAML dependency)
get_value() {
    grep "^${1}:" "$CONFIG" | sed "s/^${1}: *//; s/ *#.*//" | tr -d "'" | tr -d '"'
}

REQ_PREFIX=$(get_value req_prefix)
FR_PREFIX=$(get_value fr_prefix)
PROJECT_NAME=$(get_value project_name)
MAX_FILE_LINES=$(get_value max_file_lines)
MAX_COMPLEXITY=$(get_value max_complexity)
COVERAGE=$(get_value coverage_threshold)

# Validate required values
for var_name in REQ_PREFIX FR_PREFIX PROJECT_NAME MAX_FILE_LINES MAX_COMPLEXITY COVERAGE; do
    eval val=\$$var_name
    if [ -z "$val" ]; then
        echo "ERROR: Missing required config key for $var_name in $CONFIG" >&2
        exit 1
    fi
done

echo "Rendering templates with:"
echo "  project_name:       $PROJECT_NAME"
echo "  req_prefix:         $REQ_PREFIX"
echo "  fr_prefix:          $FR_PREFIX"
echo "  max_file_lines:     $MAX_FILE_LINES"
echo "  max_complexity:      $MAX_COMPLEXITY"
echo "  coverage_threshold: $COVERAGE"

# Render from _templates/ to target locations
TEMPLATES_DIR="_templates"

if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "ERROR: $TEMPLATES_DIR directory not found." >&2
    exit 1
fi

# Find all files in _templates/ and render to root
find "$TEMPLATES_DIR" -type f | while read -r template; do
    # Strip _templates/ prefix to get target path
    target="${template#${TEMPLATES_DIR}/}"

    # Ensure target directory exists
    target_dir=$(dirname "$target")
    mkdir -p "$target_dir"

    # Apply sed substitutions
    sed \
        -e "s/__REQ_PREFIX__/${REQ_PREFIX}/g" \
        -e "s/__FR_PREFIX__/${FR_PREFIX}/g" \
        -e "s/__PROJECT_NAME__/${PROJECT_NAME}/g" \
        -e "s/__MAX_FILE_LINES__/${MAX_FILE_LINES}/g" \
        -e "s/__MAX_COMPLEXITY__/${MAX_COMPLEXITY}/g" \
        -e "s/__COVERAGE_THRESHOLD__/${COVERAGE}/g" \
        "$template" > "$target"

    # Preserve executable permission
    if [ -x "$template" ]; then
        chmod +x "$target"
    fi
done

echo "✓ Rendered templates with config from ${CONFIG}"
