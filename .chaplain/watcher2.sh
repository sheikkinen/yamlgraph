#!/usr/bin/env bash
# watcher2.sh — Watcher2 pipeline orchestrator (FR-273)
#
# Phase 1: Git skeleton — worktree lifecycle with no LLM.
# Polls inbox, creates worktree, simulates work, creates PR, waits for CI,
# merges, tears down.
#
# Usage:
#   .chaplain/watcher2.sh
#
# Environment:
#   POLL (default: 10) — seconds between inbox checks

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib/watcher"
INBOX=".chaplain/inbox"
PROCESSING=".chaplain/processing"
ALLOWED_AUTHORS="$SCRIPT_DIR/allowed-authors.txt"
BODY_SIZE_CAP=10000
METRIC_DIR="tmp/pipeline-metrics"
POLL="${POLL:-10}"

# ── Logging ─────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info() { echo -e "${GREEN}[watcher2]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[watcher2]${NC} $1"; }
log_error() { echo -e "${RED}[watcher2]${NC} $1" >&2; }

# ── Source libs ─────────────────────────────────────────────────────────
source "$LIB_DIR/inbox_sync.sh"
source "$LIB_DIR/preflight.sh"
source "$LIB_DIR/worktree_setup.sh"
source "$LIB_DIR/worktree_teardown.sh"
source "$LIB_DIR/create_pr.sh"
source "$LIB_DIR/wait_ci.sh"
source "$LIB_DIR/merge_pr.sh"
source "$LIB_DIR/post_merge.sh"
source "$LIB_DIR/metrics.sh"

# ── Ensure dirs ─────────────────────────────────────────────────────────
mkdir -p "$INBOX" "$PROCESSING" "$METRIC_DIR"

echo "👀 watcher2: Watching $INBOX/ (poll=${POLL}s)"

# ── Main loop ───────────────────────────────────────────────────────────
while true; do
    # ── Poll: sync remote inbox ─────────────────────────────────────────
    inbox_sync

    # ── Pick next item ──────────────────────────────────────────────────
    TOPIC_FILE=$(find "$INBOX" -name "*.md" -type f 2>/dev/null | head -1)
    if [[ -z "$TOPIC_FILE" ]]; then
        sleep "$POLL"
        continue
    fi

    # Move to processing dir to prevent re-pick
    TOPIC_BASENAME=$(basename "$TOPIC_FILE")
    mv "$TOPIC_FILE" "$PROCESSING/$TOPIC_BASENAME"
    TOPIC_FILE="$PROCESSING/$TOPIC_BASENAME"
    log_info "📋 Processing: $TOPIC_FILE"

    # ── Cycle start ─────────────────────────────────────────────────────
    T_CYCLE_START=$(date +%s)
    CYCLE_OUTCOME="failure"
    CI_RESULT=""
    PR_NUMBER=""
    PR_URL=""
    WT_DIR=""
    WT_BRANCH=""
    MAIN_DIR="$(pwd)"

    # ── Preflight ───────────────────────────────────────────────────────
    if ! preflight; then
        log_error "Preflight failed — skipping cycle"
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # ── Worktree setup ──────────────────────────────────────────────────
    if ! worktree_setup; then
        log_error "Worktree setup failed — skipping cycle"
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # ── Enter worktree ──────────────────────────────────────────────────
    cd "$WT_DIR"
    unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
    log_info "Working in: $(pwd)"

    # ── Phase 1: Simulate work (placeholder) ────────────────────────────
    # TODO: Phase 2+ will replace this with yamlgraph copilot invocations
    log_info "Simulating work (phase 1 placeholder)..."

    # Copy topic file into the branch as a changelog fragment
    mkdir -p changelog/unreleased
    cp "$MAIN_DIR/$TOPIC_FILE" "changelog/unreleased/watcher2-${TOPIC_BASENAME}"

    # Run pre-commit on the staged file
    git add changelog/unreleased/
    log_info "Running pre-commit..."
    if ! pre-commit run --files changelog/unreleased/"watcher2-${TOPIC_BASENAME}" 2>&1; then
        # Re-add after auto-fixes
        git add changelog/unreleased/
    fi

    # Commit and push
    PR_TITLE="chore: watcher2 test — ${TOPIC_BASENAME%.md}"
    mkdir -p ./tmp
    cat > ./tmp/msg.txt << CMSG
chore: watcher2 phase-1 test

Automated by watcher2 pipeline (FR-273).
Topic: ${TOPIC_BASENAME}
CMSG
    git commit -F ./tmp/msg.txt --no-verify || {
        log_error "Nothing to commit"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    }

    git push origin "$WT_BRANCH" || {
        log_error "Push failed"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    }

    # ── Create PR ───────────────────────────────────────────────────────
    cd "$MAIN_DIR"
    if ! create_pr; then
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # ── Wait for CI ─────────────────────────────────────────────────────
    if ! wait_ci; then
        log_warn "CI did not pass — keeping worktree for inspection"
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # ── Merge ───────────────────────────────────────────────────────────
    if ! merge_pr; then
        log_warn "Merge failed — keeping worktree for inspection"
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # ── Cleanup ─────────────────────────────────────────────────────────
    CYCLE_OUTCOME="success"
    worktree_teardown
    post_merge
    write_cycle_metrics
    rm -f "$TOPIC_FILE"

    log_info "✅ Cycle complete for: $TOPIC_BASENAME"
    sleep "$POLL"
done
