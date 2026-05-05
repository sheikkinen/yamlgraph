#!/usr/bin/env bash
# pipeline-status.sh — Quick status of chaplain pipeline(s)
# Usage: pipeline-status.sh [issue-number]
#   No args: show all active pipelines + queue overview
#   With arg: show detailed status for specific issue

set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

header() { echo -e "\n${BLUE}── $1 ──${NC}"; }

if [[ $# -eq 0 ]]; then
    # ── Overview mode ──
    header "Queue"
    for dir in inbox processing failed done; do
        count=$(find ".chaplain/$dir" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        case "$dir" in
            inbox)      color=$BLUE ;;
            processing) color=$YELLOW ;;
            failed)     color=$RED ;;
            done)       color=$GREEN ;;
        esac
        files=$(find ".chaplain/$dir" -name '*.md' -exec basename {} .md \; 2>/dev/null | tr '\n' ' ')
        echo -e "  ${color}${dir}${NC} (${count}): ${files}"
    done

    header "Worktrees"
    git worktree list | grep -v "^\S.*\[main\]" || echo "  (none besides main)"

    header "Active Logs"
    for log in logs/fsm-pipeline-*.log; do
        [[ -e "$log" ]] || { echo "  (none)"; break; }
        issue=$(basename "$log" | sed 's/fsm-pipeline-\(gh-[0-9]*\)-.*/\1/')
        last_state=$(grep -o '[a-z_]* --[a-z_]*--> [a-z_]*' "$log" 2>/dev/null | tail -1 || echo "unknown")
        last_ts=$(tail -1 "$log" 2>/dev/null | grep -o '^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' || echo "?")
        warnings=$(grep -c "WARNING" "$log" 2>/dev/null | tr -d '[:space:]' || echo 0)
        errors=$(grep -c "ERROR" "$log" 2>/dev/null | tr -d '[:space:]' || echo 0)
        echo -e "  ${issue}: ${last_state} (${last_ts}) warn=${warnings} err=${errors}"
    done

    header "Open PRs"
    gh pr list --state open --json number,title,statusCheckRollup --template '{{range .}}  #{{.number}} {{.title}} {{range .statusCheckRollup}}{{if eq .status "FAILURE"}}❌{{.context}} {{end}}{{end}}
{{end}}' 2>/dev/null || echo "  (gh cli unavailable)"

else
    # ── Detail mode for specific issue ──
    ISSUE="$1"
    # Normalize: accept "318" or "gh-318"
    [[ "$ISSUE" =~ ^[0-9]+$ ]] && ISSUE="gh-${ISSUE}"

    header "Pipeline: ${ISSUE}"

    # Queue position
    for dir in inbox processing failed done; do
        if [[ -f ".chaplain/$dir/${ISSUE}.md" ]]; then
            echo -e "  Queue: ${dir}"
            break
        fi
    done

    # Log file
    LOG=$(ls -t logs/fsm-pipeline-${ISSUE}-*.log 2>/dev/null | head -1)
    if [[ -z "$LOG" ]]; then
        echo "  No log file found"
        exit 0
    fi
    echo "  Log: ${LOG}"

    header "State Transitions"
    grep '\-\-.*\-\->' "$LOG" 2>/dev/null | grep -o '\[watcher-pipeline-v2\].*' | sed 's/\[watcher-pipeline-v2\] /  /' || echo "  (none)"

    header "Errors & Warnings"
    grep -E "ERROR|WARNING" "$LOG" 2>/dev/null | grep -v "action_loader\|DEBUG" | tail -10 | sed 's/^/  /' || echo "  (none)"

    header "Last 10 Lines"
    tail -10 "$LOG" | sed 's/^/  /'

    # Worktree
    WT=$(git worktree list | grep "${ISSUE}" || true)
    if [[ -n "$WT" ]]; then
        header "Worktree"
        echo "  ${WT}"
    fi

    # PR
    PR_NUM=$(echo "$ISSUE" | grep -o '[0-9]\+')
    PR_INFO=$(gh pr list --state all --search "head:feat/watcher2-${ISSUE}" --json number,state,title --template '{{range .}}#{{.number}} [{{.state}}] {{.title}}{{end}}' 2>/dev/null || true)
    if [[ -n "$PR_INFO" ]]; then
        header "PR"
        echo "  ${PR_INFO}"
    fi
fi
