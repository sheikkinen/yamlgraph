#!/usr/bin/env bash
# watcher2.sh — Watcher2 pipeline orchestrator (FR-273)
#
# Phase 2: Copilot diary — yamlgraph copilot node reads inbox topic,
# writes diary reflection, commits and merges via PR.
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

    # ── Phase 2: Copilot diary reflection ──────────────────────────────
    # FR-273 Phase 2: yamlgraph copilot node reads topic, writes diary
    log_info "Running copilot diary reflection..."

    PIPELINE_DATE=$(date +%Y-%m-%d)
    PIPELINE_STATE="tmp/pipeline-state.json"
    DIARY_GRAPH=".chaplain/graphs/watcher-diary/graph.yaml"

    # Invoke yamlgraph copilot graph
    if ! yamlgraph graph run "$DIARY_GRAPH" \
        --var topic_file="$MAIN_DIR/$TOPIC_FILE" \
        --var date="$PIPELINE_DATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-copilot.log; then
        log_error "Copilot diary graph failed"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # Verify diary file was created
    DIARY_FILE=$(find docs/diary/ -name "${PIPELINE_DATE}-watcher2-*" -type f 2>/dev/null | head -1)
    if [[ -z "$DIARY_FILE" ]]; then
        log_warn "Copilot did not create diary file — falling back to topic copy"
        mkdir -p docs/diary
        cp "$MAIN_DIR/$TOPIC_FILE" "docs/diary/${PIPELINE_DATE}-watcher2-reflection.md"
        DIARY_FILE="docs/diary/${PIPELINE_DATE}-watcher2-reflection.md"
    fi

    # Stage, run pre-commit, commit
    git add docs/diary/
    log_info "Running pre-commit..."
    if ! pre-commit run --files "$DIARY_FILE" 2>&1; then
        git add docs/diary/
    fi

    PR_TITLE="docs: watcher2 diary — ${TOPIC_BASENAME%.md}"
    mkdir -p ./tmp
    cat > ./tmp/msg.txt << CMSG
docs: watcher2 diary reflection

Automated by watcher2 pipeline (FR-273 Phase 2).
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
