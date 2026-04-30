#!/usr/bin/env bash
# worktree_teardown.sh — Remove worktree, prune branch, pull main
#
# Usage: bash worktree_teardown.sh --dir <wt_dir>

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Parse args
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

# Derive branch and main dir from worktree dir
WT_BRANCH=$(git -C "$WT_DIR" branch --show-current 2>/dev/null || basename "$WT_DIR")
MAIN_DIR=$(git -C "$WT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null | sed 's|/\.git$||' || pwd)

worktree_teardown() {
    cd "$MAIN_DIR" 2>/dev/null || true

    log_info "Tearing down worktree: $WT_DIR"

    # Remove worktree
    git worktree remove "$WT_DIR" --force 2>/dev/null || log_warn "Failed to remove worktree $WT_DIR"

    # Delete local and remote branch
    git branch -D "$WT_BRANCH" 2>/dev/null || true
    git push origin --delete "$WT_BRANCH" 2>/dev/null || true

    # Guard against bare=true corruption (FR-139)
    local bare_val
    bare_val=$(git config --get core.bare 2>/dev/null || echo "false")
    if [[ "$bare_val" == "true" ]]; then
        log_warn "Detected bare=true corruption — restoring"
        git config core.bare false
    fi

    # Clean stale .pth entries (FR-174)
    if [[ -d "$MAIN_DIR/.venv" ]]; then
        python3 -c "
from pathlib import Path
from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries
clean_stale_pth_entries(Path('$MAIN_DIR/.venv'), str(Path('$WT_DIR').resolve()))
" 2>/dev/null || true
    fi

    # Validate editable install (FR-241)
    if ! python3 -c "import yamlgraph" 2>/dev/null; then
        log_warn "Editable install broken after cleanup — reinstalling"
        pip install -e "$MAIN_DIR" --quiet 2>/dev/null || true
    fi

    # Pull latest main after merge
    git checkout main --quiet 2>/dev/null || true
    git pull --ff-only --quiet 2>/dev/null || log_warn "Failed to pull main after teardown"

    log_info "Teardown complete"
}

worktree_teardown
