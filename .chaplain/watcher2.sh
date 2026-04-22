#!/usr/bin/env bash
# watcher2.sh — Watcher2 pipeline orchestrator (FR-273)
#
# Phase 3: Planning + judging pipeline with copilot session chaining.
# Plan → Research → Write acceptance tests → pytest RED → Judge → verdict check.
# Shell steps between copilot invocations, state chained via --import/--export-state.
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

    # ── Phase 3: Planning + Judging pipeline ────────────────────────────
    # FR-273 Phase 3: copilot session chain with shell steps between nodes
    PIPELINE_STATE="tmp/pipeline-state.json"
    DRAFTS_DIR=".chaplain/drafts"
    GRAPH_DIR=".chaplain/graphs/watcher-plan"
    mkdir -p "$DRAFTS_DIR" tmp

    # ── Step 1: Plan ────────────────────────────────────────────────────
    log_info "Step 1/4: Plan — reading topic, drafting FR..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-plan.yaml" \
        --var topic_file="$MAIN_DIR/$TOPIC_FILE" \
        --var drafts_dir="$DRAFTS_DIR" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-plan.log; then
        log_error "Plan step failed"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # Shell: commit FR draft
    git add "$DRAFTS_DIR/" feature-requests/ 2>/dev/null || true
    if git diff --cached --quiet; then
        log_error "Plan produced no files"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi
    git commit -m "chore: watcher2 — FR draft from plan step" --no-verify

    # ── Step 2: Research ────────────────────────────────────────────────
    log_info "Step 2/4: Research — gathering evidence..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-research.yaml" \
        --var drafts_dir="$DRAFTS_DIR" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-research.log; then
        log_warn "Research step failed — continuing without research"
    fi

    # Shell: commit research additions to FR
    git add "$DRAFTS_DIR/" feature-requests/ 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git commit -m "chore: watcher2 — research brief appended" --no-verify
    fi

    # ── Step 3: Write acceptance tests ──────────────────────────────────
    log_info "Step 3/4: Write acceptance tests (RED)..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-acceptance.yaml" \
        --var drafts_dir="$DRAFTS_DIR" \
        --var worktree_dir="$(pwd)" \
        --var branch="$WT_BRANCH" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-acceptance.log; then
        log_warn "Acceptance test step failed — continuing to judge"
    fi

    # Shell: verify RED (tests should fail on unmodified code)
    log_info "Verifying RED — tests should fail..."
    TEST_FILES=$(find tests/ -name "*.py" -newer "$PIPELINE_STATE" -type f 2>/dev/null)
    if [[ -n "$TEST_FILES" ]]; then
        if pytest $TEST_FILES -x --no-cov -q 2>&1 | tee tmp/watcher2-red.log; then
            log_warn "Tests pass on unmodified code — acceptance tests may be trivial"
        else
            log_info "RED confirmed — tests fail as expected"
        fi
        # Commit test files (copilot may have already committed with SKIP=pytest)
        git add tests/ 2>/dev/null || true
        if ! git diff --cached --quiet; then
            SKIP=pytest git commit -m "test: watcher2 — RED acceptance tests" --no-verify
        fi
    else
        log_warn "No new test files found"
    fi

    # ── Step 4: Judge ───────────────────────────────────────────────────
    log_info "Step 4/4: Judge — evaluating FR draft..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-judge.yaml" \
        --var drafts_dir="$DRAFTS_DIR" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-judge.log; then
        log_error "Judge step failed"
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # Shell: check verdict
    VERDICT=$(python3 -c "
import json, sys
state = json.load(open('$PIPELINE_STATE'))
output = state.get('judge_result', {}).get('output', '')
for v in ['APPROVE', 'REJECT', 'AMEND', 'SPLIT']:
    if v in output.upper():
        print(v)
        sys.exit(0)
print('UNKNOWN')
" 2>/dev/null || echo "UNKNOWN")

    log_info "Judge verdict: $VERDICT"

    if [[ "$VERDICT" == "REJECT" ]]; then
        log_warn "FR rejected by judge — aborting cycle"
        # Commit judge result for traceability
        git add "$DRAFTS_DIR/" feature-requests/ 2>/dev/null || true
        git diff --cached --quiet || git commit -m "chore: watcher2 — FR rejected by judge" --no-verify
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    if [[ "$VERDICT" == "AMEND" || "$VERDICT" == "SPLIT" ]]; then
        log_warn "FR needs amendment ($VERDICT) — aborting cycle"
        git add "$DRAFTS_DIR/" feature-requests/ .chaplain/inbox/ 2>/dev/null || true
        git diff --cached --quiet || git commit -m "chore: watcher2 — FR $VERDICT by judge" --no-verify
        cd "$MAIN_DIR"
        worktree_teardown
        write_cycle_metrics
        rm -f "$TOPIC_FILE"
        continue
    fi

    # APPROVE or UNKNOWN — commit and proceed to PR
    git add "$DRAFTS_DIR/" feature-requests/ 2>/dev/null || true
    git diff --cached --quiet || git commit -m "chore: watcher2 — FR approved by judge" --no-verify

    # Derive PR title from topic
    PR_TITLE="chore: watcher2 plan — ${TOPIC_BASENAME%.md}"

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
