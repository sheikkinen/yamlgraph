#!/usr/bin/env bash
# vscode_storage_cleanup.sh — Reclaim VS Code / Copilot chat storage in tiers.
#
# Tiers (safest first):
#   1  Workspace throwaway logs        tmp/*.log            (regenerable)
#   2  Copilot chat debug-logs         debug-logs/<uuid>/   (raw transcripts)
#   3  Chat history + edit sessions    chatSessions/,
#                                       chatEditingSessions/ (UI-restorable)
#
# Usage:
#   scripts/vscode_storage_cleanup.sh [--apply] [--tiers 1,2,3]
#                                     [--age-tmp DAYS] [--age-logs DAYS]
#                                     [--age-chat DAYS] [--verbose]
#
# Defaults: dry-run, all tiers, age-tmp 14, age-logs 14, age-chat 30.
# Nothing is deleted unless --apply is passed.
#
# Environment:
#   VSCODE_USER_DIR   Override VS Code User dir
#                     (default: ~/Library/Application Support/Code/User)
#   WORKSPACE_DIR     Override workspace root (default: current git toplevel/PWD)

set -euo pipefail

APPLY=false
TIERS="1,2,3"
AGE_TMP=14
AGE_LOGS=14
AGE_CHAT=30
VERBOSE=false

VSCODE_USER_DIR="${VSCODE_USER_DIR:-$HOME/Library/Application Support/Code/User}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)     APPLY=true; shift ;;
        --tiers)     TIERS="$2"; shift 2 ;;
        --age-tmp)   AGE_TMP="$2"; shift 2 ;;
        --age-logs)  AGE_LOGS="$2"; shift 2 ;;
        --age-chat)  AGE_CHAT="$2"; shift 2 ;;
        --verbose)   VERBOSE=true; shift ;;
        -h|--help)
            sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

tier_enabled() { [[ ",${TIERS}," == *",$1,"* ]]; }

now=$(date +%s)

mtime_of() {
    if [[ "$(uname)" == "Darwin" ]]; then
        stat -f %m "$1"
    else
        stat -c %Y "$1"
    fi
}

age_days_of() {
    local m
    m=$(mtime_of "$1")
    echo $(( (now - m) / 86400 ))
}

# Human-readable size of a path (0 if missing).
size_of() {
    [[ -e "$1" ]] || { echo 0; return; }
    du -sk "$1" 2>/dev/null | awk '{print $1}'
}

freed_kb=0

# remove_if_old PATH AGE_LIMIT LABEL
remove_if_old() {
    local path="$1" limit="$2" label="$3"
    [[ -e "$path" ]] || return 0
    local age
    age=$(age_days_of "$path")
    if [[ $age -ge $limit ]]; then
        local kb
        kb=$(size_of "$path")
        freed_kb=$((freed_kb + kb))
        if [[ "$APPLY" == true ]]; then
            rm -rf "$path"
            echo "🗑  removed $label: $(basename "$path") (${age}d, ${kb}K)"
        else
            echo "🔍 would remove $label: $(basename "$path") (${age}d, ${kb}K)"
        fi
    else
        [[ "$VERBOSE" == true ]] && echo "✓  keep $label: $(basename "$path") (${age}d)"
        return 0
    fi
}

# Resolve the workspaceStorage dir for the current workspace by matching
# workspace.json -> folder URI == WORKSPACE_DIR.
find_ws_storage() {
    local base="$VSCODE_USER_DIR/workspaceStorage"
    [[ -d "$base" ]] || return 0
    local target="file://$WORKSPACE_DIR"
    local d
    for d in "$base"/*/; do
        local wj="${d}workspace.json"
        [[ -f "$wj" ]] || continue
        if grep -q "\"$target\"" "$wj" 2>/dev/null; then
            echo "${d%/}"
            return 0
        fi
    done
}

echo "═══════════════════════════════════════════════════════════"
echo "VS Code storage cleanup — mode: $([[ "$APPLY" == true ]] && echo APPLY || echo DRY-RUN)"
echo "  workspace : $WORKSPACE_DIR"
echo "  tiers     : $TIERS"
echo "═══════════════════════════════════════════════════════════"

# ── Tier 1 : workspace throwaway logs ──────────────────────────────────────
if tier_enabled 1; then
    echo; echo "── Tier 1: workspace tmp/*.log (>= ${AGE_TMP}d) ──"
    if [[ -d "$WORKSPACE_DIR/tmp" ]]; then
        shopt -s nullglob
        for f in "$WORKSPACE_DIR"/tmp/*.log; do
            remove_if_old "$f" "$AGE_TMP" "tmp-log"
        done
        shopt -u nullglob
    else
        echo "  (no tmp/ directory)"
    fi
fi

WS_STORAGE=""
if tier_enabled 2 || tier_enabled 3; then
    WS_STORAGE=$(find_ws_storage)
    if [[ -z "$WS_STORAGE" ]]; then
        echo; echo "⚠  Could not resolve workspaceStorage for $WORKSPACE_DIR — skipping tiers 2/3."
    fi
fi

# ── Tier 2 : Copilot chat debug-logs ───────────────────────────────────────
if tier_enabled 2 && [[ -n "$WS_STORAGE" ]]; then
    echo; echo "── Tier 2: Copilot debug-logs sessions (>= ${AGE_LOGS}d) ──"
    dl="$WS_STORAGE/GitHub.copilot-chat/debug-logs"
    if [[ -d "$dl" ]]; then
        for d in "$dl"/*/; do
            [[ -d "$d" ]] || continue
            remove_if_old "${d%/}" "$AGE_LOGS" "debug-log"
        done
    else
        echo "  (no debug-logs directory)"
    fi
fi

# ── Tier 3 : chat history + edit sessions ──────────────────────────────────
if tier_enabled 3 && [[ -n "$WS_STORAGE" ]]; then
    echo; echo "── Tier 3: chatSessions + chatEditingSessions (>= ${AGE_CHAT}d) ──"
    for sub in chatSessions chatEditingSessions; do
        dir="$WS_STORAGE/$sub"
        [[ -d "$dir" ]] || { echo "  (no $sub directory)"; continue; }
        for e in "$dir"/*; do
            [[ -e "$e" ]] || continue
            remove_if_old "$e" "$AGE_CHAT" "$sub"
        done
    done
fi

echo
echo "═══════════════════════════════════════════════════════════"
freed_mb=$(( freed_kb / 1024 ))
if [[ "$APPLY" == true ]]; then
    echo "🧹 Reclaimed ~${freed_mb} MB"
else
    echo "🔍 Would reclaim ~${freed_mb} MB (re-run with --apply to delete)"
fi
echo "═══════════════════════════════════════════════════════════"
