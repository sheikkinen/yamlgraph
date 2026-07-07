#!/usr/bin/env bash
# worktree.sh — Canonical worktree lifecycle command (FR-698)
#
# Verbs:
#   new <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]
#   spike <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]
#   rm <name|--dir <wt_dir>> [--note "<text>"]
#   list

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/worktree.sh new <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]
  scripts/worktree.sh spike <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]
  scripts/worktree.sh rm <name|--dir <wt_dir>> [--note "<text>"]
  scripts/worktree.sh list
EOF
}

log_info() {
    echo "ℹ️  $*" >&2
}

log_warn() {
    echo "⚠️  $*" >&2
}

log_error() {
    echo "❌ $*" >&2
}

fail() {
    log_error "$*"
    exit 1
}

repo_root() {
    git rev-parse --show-toplevel
}

work_dir_slug() {
    echo "$1" | tr '/' '-'
}

json_escape() {
    python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$1"
}

append_spike_note() {
    local repo_dir="$1"
    local spike_name="$2"
    local note="$3"
    local note_file="$repo_dir/docs/diary/spike-notes.log"
    local day
    day=$(date +%Y-%m-%d)
    mkdir -p "$(dirname "$note_file")"
    touch "$note_file"
    printf '%s %s: %s\n' "$day" "$spike_name" "$note" >>"$note_file"
}

validate_spike_note() {
    local note="$1"
    local compact
    if [[ -z "$note" ]]; then
        fail "Spike worktree removal requires --note \"<text>\""
    fi
    if [[ "$note" == *$'\n'* ]]; then
        fail "Spike note must be a single line"
    fi
    compact=$(echo "$note" | tr -d '[:space:]')
    if [[ ${#compact} -lt 10 ]]; then
        fail "Spike note must contain at least 10 non-whitespace characters"
    fi
}

new_or_spike() {
    local mode="$1"
    local name="$2"
    local branch_prefix="feat/"
    local work_dir="."
    local emit_json=false
    local main_dir
    local wt_branch
    local wt_dir
    local gh_pr_list_exit=0
    local existing_merged_pr=""

    shift 2
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --prefix)
                branch_prefix="$2"
                shift 2
                ;;
            --work-dir)
                work_dir="$2"
                shift 2
                ;;
            --json)
                emit_json=true
                shift
                ;;
            *)
                fail "Unknown option for $mode: $1"
                ;;
        esac
    done

    [[ -n "$name" ]] || fail "Missing <name> for $mode"

    main_dir=$(repo_root)
    cd "$main_dir"

    wt_branch="${branch_prefix}${name}"
    if [[ "$work_dir" == "." ]]; then
        wt_dir="tmp/worktrees/${wt_branch}"
    else
        wt_dir="tmp/worktrees/$(work_dir_slug "$work_dir")/${wt_branch}"
    fi

    git worktree prune

    if git show-ref --verify --quiet "refs/heads/$wt_branch" 2>/dev/null; then
        log_warn "Stale branch $wt_branch exists — deleting"
        git branch -D "$wt_branch" 2>/dev/null || true
    fi

    if command -v gh >/dev/null 2>&1; then
        existing_merged_pr=$(gh pr list \
            --state merged \
            --head "$wt_branch" \
            --json number,url,mergedAt \
            --jq '.[0] | select(.number != null)' 2>/dev/null) || gh_pr_list_exit=$? || true
        if [[ "$gh_pr_list_exit" -ne 0 ]]; then
            log_warn "Merged PR history query failed for $wt_branch — continuing without collision guard"
        elif [[ -n "$existing_merged_pr" ]]; then
            log_info "Skipping worktree setup: previously merged PR found for $wt_branch ($existing_merged_pr)"
            return 2
        fi
    else
        log_warn "gh CLI unavailable — skipping merged PR collision guard for $wt_branch"
    fi

    log_info "Creating worktree: $wt_dir (branch: $wt_branch)"
    mkdir -p "$(dirname "$wt_dir")"
    git worktree add "$wt_dir" -b "$wt_branch" main

    if [[ -d "$main_dir/.venv" ]]; then
        ln -snf "$main_dir/.venv" "$wt_dir/.venv"
        log_info "Symlinked .venv"
    fi

    if ! grep -q "^\.venv$" "$wt_dir/.gitignore" 2>/dev/null; then
        echo ".venv" >>"$wt_dir/.gitignore"
    fi

    if [[ "$mode" == "spike" ]]; then
        cat >"$wt_dir/.wt-spike-meta.json" <<EOF
{"name": $(json_escape "$name"), "branch": $(json_escape "$wt_branch")}
EOF
    fi

    if [[ "$emit_json" == "true" ]]; then
        echo "{\"wt_dir\": \"$wt_dir\", \"wt_branch\": \"$wt_branch\", \"main_dir\": \"$main_dir\", \"work_dir\": \"$work_dir\"}"
    else
        log_info "Worktree ready: $wt_dir"
    fi
}

list_worktrees() {
    local main_dir
    main_dir=$(repo_root)
    cd "$main_dir"

    printf 'WORKTREE\tBRANCH\tAGE\n'
    git worktree list --porcelain | awk '
      /^worktree / { wt=$2 }
      /^branch / {
        br=$2
        gsub("^refs/heads/", "", br)
        cmd="git -C \"" wt "\" log -1 --format=%cr HEAD 2>/dev/null"
        cmd | getline age
        close(cmd)
        if (age == "") age="unknown"
        printf "%s\t%s\t%s\n", wt, br, age
      }
    '
}

remove_worktree() {
    local target_name=""
    local target_dir=""
    local note=""
    local main_dir
    local wt_branch
    local wt_dir
    local wt_abs
    local spike_meta
    local spike_name

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dir)
                target_dir="$2"
                shift 2
                ;;
            --note)
                note="$2"
                shift 2
                ;;
            -*)
                fail "Unknown option for rm: $1"
                ;;
            *)
                if [[ -n "$target_name" ]]; then
                    fail "rm accepts one name argument or --dir"
                fi
                target_name="$1"
                shift
                ;;
        esac
    done

    main_dir=$(repo_root)
    cd "$main_dir"

    if [[ -z "$target_dir" ]]; then
        [[ -n "$target_name" ]] || fail "rm requires <name> or --dir <wt_dir>"
        if [[ -d "$target_name" ]]; then
            target_dir="$target_name"
        else
            target_dir="tmp/worktrees/feat/$target_name"
        fi
    fi

    [[ -d "$target_dir" ]] || fail "Worktree directory does not exist: $target_dir"
    wt_dir="$target_dir"
    wt_abs=$(cd "$wt_dir" && pwd)
    spike_meta="$wt_dir/.wt-spike-meta.json"
    if [[ -f "$spike_meta" ]]; then
        validate_spike_note "$note"
        spike_name=$(python3 -c "import json,sys; data=json.load(open(sys.argv[1])); print(data.get('name','unknown'))" "$spike_meta" 2>/dev/null || basename "$wt_dir")
        append_spike_note "$main_dir" "$spike_name" "$note"
    fi

    wt_branch=$(git -C "$wt_dir" branch --show-current 2>/dev/null || basename "$wt_dir")
    main_dir=$(git -C "$wt_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null | sed 's|/\.git$||' || repo_root)
    cd "$main_dir" 2>/dev/null || true

    log_info "Tearing down worktree: $wt_dir"
    git worktree remove "$wt_dir" --force 2>/dev/null || log_warn "Failed to remove worktree $wt_dir"
    git branch -D "$wt_branch" 2>/dev/null || true
    git push origin --delete "$wt_branch" 2>/dev/null || true

    if [[ "$(git config --get core.bare 2>/dev/null || echo false)" == "true" ]]; then
        log_warn "Detected bare=true corruption — restoring"
        git config core.bare false
    fi

    if [[ -d "$main_dir/.venv" ]]; then
        python3 - <<EOF 2>/dev/null || true
from pathlib import Path
from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries
clean_stale_pth_entries(Path("$main_dir/.venv"), "$wt_abs")
EOF
    fi

    if ! python3 - <<'EOF' 2>/dev/null
from yamlgraph.utils.worktree_helpers import validate_editable_install
raise SystemExit(0 if validate_editable_install() else 1)
EOF
    then
        log_warn "Editable install broken after cleanup — reinstalling"
        pip install -e "$main_dir" --quiet 2>/dev/null || true
    fi

    git checkout main --quiet 2>/dev/null || true
    git pull --ff-only --quiet 2>/dev/null || log_warn "Failed to pull main after teardown"
    log_info "Teardown complete"
}

main() {
    local verb
    verb="${1:-}"
    if [[ -z "$verb" ]]; then
        usage
        exit 1
    fi
    shift || true

    case "$verb" in
        new)
            new_or_spike "new" "${1:-}" "${@:2}"
            ;;
        spike)
            new_or_spike "spike" "${1:-}" "${@:2}"
            ;;
        list)
            list_worktrees
            ;;
        rm)
            remove_worktree "$@"
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            fail "Unknown verb: $verb"
            ;;
    esac
}

main "$@"
