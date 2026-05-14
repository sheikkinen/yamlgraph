#!/bin/bash
# Shared semantic contract for CI artifact validation (FR-373).
# shellcheck shell=bash

validate_changelog_fragment_file() {
  local fragment_file="$1"
  local fragment_label="${2:-$fragment_file}"

  if [ ! -f "$fragment_file" ]; then
    echo "::error::changelog fragment missing from workspace: $fragment_label"
    return 1
  fi

  if ! grep -q '[^[:space:]]' "$fragment_file"; then
    echo "::error::changelog fragment is empty: $fragment_label"
    return 1
  fi

  if ! awk '
    NR == 1 && $0 == "---" { in_front_matter = 1; next }
    in_front_matter && $0 == "---" { found_end = 1; exit }
    END { exit(found_end ? 0 : 1) }
  ' "$fragment_file"; then
    echo "::error::changelog fragment must start with YAML front matter: $fragment_label"
    return 1
  fi

  if ! awk '
    NR == 1 && $0 == "---" { in_front_matter = 1; next }
    in_front_matter && $0 == "---" { found_end = 1; exit }
    in_front_matter && $0 ~ /^type:[[:space:]]*[^[:space:]]+/ { found_type = 1 }
    END { exit(found_end && found_type ? 0 : 1) }
  ' "$fragment_file"; then
    echo "::error::changelog fragment front matter missing type: field: $fragment_label"
    return 1
  fi

  if ! awk '
    NR == 1 && $0 == "---" { in_front_matter = 1; next }
    in_front_matter && $0 == "---" { in_front_matter = 0; in_body = 1; next }
    in_body && $0 ~ /^[[:space:]]*-[[:space:]]+/ { found_list = 1; exit }
    END { exit(in_body && found_list ? 0 : 1) }
  ' "$fragment_file"; then
    echo "::error::changelog fragment body missing markdown list item (- ): $fragment_label"
    return 1
  fi

  echo "✅ Changelog fragment validated: $fragment_label"
  return 0
}

validate_diary_reflection_file() {
  local diary_file="$1"
  local diary_label="${2:-$diary_file}"

  if [ ! -f "$diary_file" ]; then
    echo "::error::diary reflection missing from workspace: $diary_label"
    return 1
  fi

  if ! grep -q '[^[:space:]]' "$diary_file"; then
    echo "::error::diary reflection is empty: $diary_label"
    return 1
  fi

  local byte_count
  byte_count="$(wc -c < "$diary_file" | tr -d ' ')"
  if [ "$byte_count" -le 100 ]; then
    echo "::error::diary reflection must be >100 bytes: $diary_label"
    return 1
  fi

  if ! grep -qE '^##[[:space:]]+' "$diary_file"; then
    echo "::error::diary reflection missing markdown ## header: $diary_label"
    return 1
  fi

  if ! grep -q 'Seed:' "$diary_file"; then
    echo "::error::diary reflection missing Seed: marker: $diary_label"
    return 1
  fi

  echo "✅ Diary reflection validated: $diary_label"
  return 0
}
