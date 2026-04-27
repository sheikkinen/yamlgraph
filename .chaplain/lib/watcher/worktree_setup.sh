#!/usr/bin/env bash
# worktree_setup.sh — Create worktree + branch from main
#
# Expects: TOPIC_FILE set by orchestrator
# Sets: WT_BRANCH, WT_DIR, MAIN_DIR

worktree_setup() {
    local topic_basename
    local existing_merged_pr
    local gh_pr_list_exit=0
    topic_basename=$(basename "$TOPIC_FILE" .md)

    # Derive branch name from topic file
    WT_BRANCH="feat/watcher2-${topic_basename}"
    WT_DIR="tmp/worktrees/${WT_BRANCH}"
    MAIN_DIR="$(pwd)"

    # Prune orphaned worktree metadata before branch creation
    git worktree prune

    # Remove stale local branch if it exists
    if git show-ref --verify --quiet "refs/heads/$WT_BRANCH" 2>/dev/null; then
        log_warn "Stale branch $WT_BRANCH exists — deleting"
        git branch -D "$WT_BRANCH" 2>/dev/null || true
    fi

    # Guard against recycled branch names that already have merged PR history
    if command -v gh >/dev/null 2>&1; then
        existing_merged_pr=$(gh pr list \
            --state merged \
            --head "$WT_BRANCH" \
            --json number,url,mergedAt \
            --jq '.[0] | select(.number != null)' 2>/dev/null) || gh_pr_list_exit=$? || true
        if [[ "$gh_pr_list_exit" -ne 0 ]]; then
            log_warn "Merged PR history query failed for $WT_BRANCH — continuing without collision guard"
        elif [[ -n "$existing_merged_pr" ]]; then
            WT_MERGED_PR_REF="$existing_merged_pr"
            log_info "Skipping worktree setup: previously merged PR found for $WT_BRANCH ($existing_merged_pr)"
            return 2
        fi
    else
        log_warn "gh CLI unavailable — skipping merged PR collision guard for $WT_BRANCH"
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

    # JSON stdout for bash_context_action
    echo "{\"wt_dir\": \"$WT_DIR\", \"wt_branch\": \"$WT_BRANCH\", \"main_dir\": \"$MAIN_DIR\"}"
}
