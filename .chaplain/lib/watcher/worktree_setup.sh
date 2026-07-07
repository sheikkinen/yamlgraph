#!/usr/bin/env bash
# worktree_setup.sh — Watcher wrapper over canonical scripts/worktree.sh new
#
# Usage: bash worktree_setup.sh --topic <topic_file> [--branch-prefix <prefix>] [--work-dir <selector>]

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

BRANCH_PREFIX="feat/watcher2-"
WORK_DIR="."
TOPIC_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --topic) TOPIC_FILE="$2"; shift 2 ;;
        --branch-prefix) BRANCH_PREFIX="$2"; shift 2 ;;
        --work-dir) WORK_DIR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$TOPIC_FILE" ]]; then
    log_error "Usage: worktree_setup.sh --topic <topic_file>"
    exit 1
fi

TOPIC_BASENAME=$(basename "$TOPIC_FILE" .md)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"
git worktree prune

exec bash "$REPO_ROOT/scripts/worktree.sh" new "$TOPIC_BASENAME" \
    --prefix "$BRANCH_PREFIX" \
    --work-dir "$WORK_DIR" \
    --json
