#!/usr/bin/env bash
# worktree_teardown.sh — Remove worktree, prune branch, pull main
#
# Expects: WT_DIR, WT_BRANCH, MAIN_DIR set by orchestrator

worktree_teardown() {
    cd "$MAIN_DIR" 2>/dev/null || true

    log_info "Tearing down worktree: $WT_DIR"

    # Remove worktree
    git worktree remove "$WT_DIR" --force 2>/dev/null || log_warn "Failed to remove worktree $WT_DIR"

    # Delete local branch (remote was deleted by squash merge)
    git branch -D "$WT_BRANCH" 2>/dev/null || true

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
