#!/usr/bin/env bash
# preflight.sh — Pre-flight checks before worktree operations
#
# Expects: called from repo root on main branch
# Side effects: prunes stale worktrees, switches to main if needed

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log_hook_remediation() {
    log_error "Remediation:"
    log_error "  git config --local --unset core.hooksPath"
    log_error "  pre-commit install"
    log_error "  pre-commit install --hook-type commit-msg"
}

validate_hook_integrity() {
    local hooks_path hooks_dir hook_name hook_path

    if hooks_path=$(git config --local --get core.hooksPath 2>/dev/null); then
        if [[ -z "$hooks_path" ]]; then
            log_error "Invalid hook configuration: core.hooksPath is explicitly empty"
            log_hook_remediation
            return 1
        fi

        if [[ "$hooks_path" != ".git/hooks" && "$hooks_path" != ".git/hooks/" ]]; then
            log_error "Invalid hook configuration: core.hooksPath must be unset or .git/hooks (got: $hooks_path)"
            log_hook_remediation
            return 1
        fi
    fi

    if ! hooks_dir=$(git rev-parse --git-path hooks 2>/dev/null); then
        log_error "Unable to resolve git hooks directory via 'git rev-parse --git-path hooks'"
        return 1
    fi

    for hook_name in pre-commit commit-msg; do
        hook_path="$hooks_dir/$hook_name"
        if [[ ! -f "$hook_path" ]]; then
            log_error "Missing required hook: $hook_path"
            log_hook_remediation
            return 1
        fi
        if [[ ! -x "$hook_path" ]]; then
            log_error "Hook is not executable: $hook_path"
            log_hook_remediation
            return 1
        fi
    done
}

preflight() {
    # Ensure we're on main
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        log_error "watcher2 must run from main branch (currently on $current_branch)"
        return 1
    fi

    # Validate git hook integrity before watcher processing.
    if ! validate_hook_integrity; then
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

    # JSON stdout for bash_context_action
    echo '{"status": "ok"}'
}

preflight
