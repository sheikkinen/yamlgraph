#!/usr/bin/env bash
# worktree_setup.sh — Create worktree + branch from main
#
# Expects: TOPIC_FILE set by orchestrator
# Sets: WT_BRANCH, WT_DIR, MAIN_DIR

worktree_setup() {
    local topic_basename
    topic_basename=$(basename "$TOPIC_FILE" .md)

    # Derive branch name from topic file
    WT_BRANCH="feat/watcher2-${topic_basename}"
    WT_DIR="tmp/worktrees/${WT_BRANCH}"
    MAIN_DIR="$(pwd)"

    # Remove stale local branch if it exists
    if git show-ref --verify --quiet "refs/heads/$WT_BRANCH" 2>/dev/null; then
        log_warn "Stale branch $WT_BRANCH exists — deleting"
        git branch -D "$WT_BRANCH" 2>/dev/null || true
    fi

    # Create worktree
    log_info "Creating worktree: $WT_DIR (branch: $WT_BRANCH)"
    mkdir -p "$(dirname "$WT_DIR")"
    git worktree add "$WT_DIR" -b "$WT_BRANCH" main || {
        log_error "Failed to create worktree"
        return 1
    }

    # Symlink shared .venv
    local main_venv="$MAIN_DIR/.venv"
    if [[ -d "$main_venv" ]]; then
        ln -sf "$main_venv" "$WT_DIR/.venv"
        log_info "Symlinked .venv"
    fi

    # Ensure .venv is gitignored
    if ! grep -q "^\.venv$" "$WT_DIR/.gitignore" 2>/dev/null; then
        echo ".venv" >> "$WT_DIR/.gitignore"
    fi

    log_info "Worktree ready: $WT_DIR"
}
