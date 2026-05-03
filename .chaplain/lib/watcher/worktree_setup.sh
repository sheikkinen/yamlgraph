#!/usr/bin/env bash
# worktree_setup.sh — Create worktree + branch from main
#
# Usage: bash worktree_setup.sh --topic <topic_file>
# Sets: WT_BRANCH, WT_DIR, MAIN_DIR

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --topic) TOPIC_FILE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$TOPIC_FILE" ]]; then
    log_error "Usage: worktree_setup.sh --topic <topic_file>"
    exit 1
fi

worktree_setup() {
    local topic_basename
    local existing_merged_pr
    local gh_pr_list_exit=0
    local cleanup_worktree_path=""
    local worktree_bindings=""
    topic_basename=$(basename "$TOPIC_FILE" .md)

    # Derive branch name from topic file
    WT_BRANCH="feat/watcher2-${topic_basename}"
    WT_DIR="tmp/worktrees/${WT_BRANCH}"
    MAIN_DIR="$(pwd)"

    # Prune orphaned worktree metadata before branch creation
    git worktree prune

    # Remove stale worktree attachments bound to this branch before branch cleanup
    worktree_bindings="$(git worktree list --porcelain)"
    while IFS= read -r line; do
        if [[ "$line" == worktree\ * ]]; then
            cleanup_worktree_path="${line#worktree }"
        elif [[ "$line" == "branch refs/heads/$WT_BRANCH" ]]; then
            if [[ -n "$cleanup_worktree_path" ]]; then
                log_warn "Stale worktree attachment for $WT_BRANCH at $cleanup_worktree_path — removing"
                if ! git worktree remove "$cleanup_worktree_path" --force 2>/dev/null; then
                    log_error "Failed to remove stale worktree attachment: $cleanup_worktree_path"
                    return 1
                fi
            fi
        elif [[ -z "$line" ]]; then
            cleanup_worktree_path=""
        fi
    done <<< "$worktree_bindings"

    # Remove stale local branch if it exists
    if git show-ref --verify --quiet "refs/heads/$WT_BRANCH" 2>/dev/null; then
        log_warn "Stale branch $WT_BRANCH exists — deleting"
        if ! git branch -D "$WT_BRANCH" 2>/dev/null; then
            log_error "Failed to delete stale local branch $WT_BRANCH"
            return 1
        fi
    fi

    # Best-effort remote stale branch cleanup
    git push origin --delete "$WT_BRANCH" 2>/dev/null || log_warn "Remote stale branch cleanup skipped for $WT_BRANCH"

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
    if [[ -d "$WT_DIR" ]]; then
        log_warn "Stale worktree directory $WT_DIR exists — removing"
        if ! rm -rf "$WT_DIR"; then
            log_error "Failed to remove stale worktree directory $WT_DIR"
            return 1
        fi
    fi
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

worktree_setup
