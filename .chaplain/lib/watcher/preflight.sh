#!/usr/bin/env bash
# preflight.sh — Pre-flight checks before worktree operations
#
# Expects: called from repo root on main branch
# Side effects: prunes stale worktrees, switches to main if needed

preflight() {
    # Ensure we're on main
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        log_error "watcher2 must run from main branch (currently on $current_branch)"
        return 1
    fi

    # Pull latest
    git pull --ff-only --quiet 2>/dev/null || log_warn "git pull failed — continuing with local main"

    # Prune stale worktrees
    git worktree prune 2>/dev/null || true

    # Prune worktrees older than 12 hours
    local wt_base="tmp/worktrees"
    if [[ -d "$wt_base" ]]; then
        find "$wt_base" -mindepth 1 -maxdepth 3 -type d -name ".git" -mmin +720 2>/dev/null \
        | while read -r gitdir; do
            local wt_dir
            wt_dir=$(dirname "$gitdir")
            log_warn "Pruning stale worktree: $wt_dir"
            git worktree remove "$wt_dir" --force 2>/dev/null || true
        done
    fi

    # Validate editable install
    if ! python3 -c "import yamlgraph" 2>/dev/null; then
        log_warn "yamlgraph import broken — reinstalling editable"
        pip install -e . --quiet 2>/dev/null || log_error "Failed to reinstall yamlgraph"
    fi

    log_info "Preflight complete"
}
