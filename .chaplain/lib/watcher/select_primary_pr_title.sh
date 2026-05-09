#!/usr/bin/env bash
# Select primary PR title from branch history (oldest first):
# 1) first feat/fix
# 2) else first non-docs/non-chore
# 3) else first subject

set -euo pipefail

extract_type() {
    local subject="$1"
    local type_regex='^(feat|fix|chore|docs|refactor|test|ci|perf|style|build|revert)(\([^)]+\))?:[[:space:]]+'
    if [[ "$subject" =~ $type_regex ]]; then
        echo "${BASH_REMATCH[1]}"
        return
    fi
    echo ""
}

subjects=()
while IFS= read -r subject; do
    subjects+=("$subject")
done < <(git log --reverse --format=%s origin/main..HEAD)

if [[ ${#subjects[@]} -eq 0 ]]; then
    git log -1 --format=%s
    exit 0
fi

for subject in "${subjects[@]}"; do
    subject_type=$(extract_type "$subject")
    if [[ "$subject_type" == "feat" || "$subject_type" == "fix" ]]; then
        echo "$subject"
        exit 0
    fi
done

for subject in "${subjects[@]}"; do
    subject_type=$(extract_type "$subject")
    if [[ "$subject_type" != "docs" && "$subject_type" != "chore" ]]; then
        echo "$subject"
        exit 0
    fi
done

echo "${subjects[0]}"
