#!/usr/bin/env bash
# worktree_teardown.sh — Watcher wrapper over canonical scripts/worktree.sh rm
#
# Usage: bash worktree_teardown.sh --dir <wt_dir>

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

WT_DIR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir) WT_DIR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$WT_DIR" ]]; then
    log_error "Usage: worktree_teardown.sh --dir <wt_dir>"
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"
exec bash "$REPO_ROOT/scripts/worktree.sh" rm --dir "$WT_DIR"
