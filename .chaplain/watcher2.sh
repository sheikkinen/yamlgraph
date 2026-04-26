#!/usr/bin/env bash
# watcher2.sh — Watcher2 pipeline orchestrator (FR-273)
#
# Phase 4: Planning + judging + enforcement pipeline with copilot session chaining.
# Plan → Research → Write acceptance tests → pytest RED → Judge → verdict check.
# Implement → Test/Demo → Critique/Distill → Finalize.
# Shell steps between copilot invocations, state chained via --import/--export-state.
#
# Usage:
#   .chaplain/watcher2.sh
#
# Environment:
#   POLL (default: 10) — seconds between inbox checks

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Global logging — capture all output to timestamped log file ─────────
mkdir -p logs
LOG_FILE="logs/watcher2-run-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# ── Log rotation — keep last 10 log files ───────────────────────────────
find logs/ -name 'watcher2-run-*.log' -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true

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
mkdir -p "$INBOX" "$PROCESSING" "$METRIC_DIR" ".chaplain/failed"

# ── ERR trap — catch unguarded crashes with line number ─────────────────
trap 'log_error "Unexpected crash at line $LINENO (exit $?)"; handle_failure "unexpected crash at line $LINENO"' ERR

# ── Failure handler (preserves forensic evidence) ───────────────────
handle_failure() {
    local reason="${1:-unknown}"
    log_error "Cycle failed: $reason"

    # ── Forensic analysis phase (FR-285) ────────────────────────────────
    # Gracefully fail if yamlgraph unavailable
    if command -v yamlgraph >/dev/null 2>&1; then
        log_info "🔍 Running forensic analysis..."

        # Extract failure context
        FAILURE_REASON="$reason"
        TOPIC_CONTENT=""
        LOG_FILES=""
        WORKTREE_STATE=""

        if [[ -n "${TOPIC_FILE:-}" && -f "$TOPIC_FILE" ]]; then
            TOPIC_CONTENT=$(cat "$TOPIC_FILE" 2>/dev/null || echo "Unable to read topic file")
        fi

        # Collect relevant log files
        LOG_FILES=$(find tmp/ -name "watcher2-*.log" 2>/dev/null || true)

        # Inspect worktree state if available
        if [[ -n "${WT_DIR:-}" && -d "$WT_DIR" ]]; then
            cd "$WT_DIR" 2>/dev/null || true
            WORKTREE_STATE=$(git status --porcelain 2>/dev/null || echo "Git status unavailable")
        fi

        # Run forensic analysis to generate diary entry
        yamlgraph graph run .chaplain/graphs/watcher-forensic/graph.yaml \
            --var failure_reason="$FAILURE_REASON" \
            --var topic_content="$TOPIC_CONTENT" \
            --var log_files="$LOG_FILES" \
            --var worktree_state="$WORKTREE_STATE" \
            --full 2>/dev/null || log_warn "Forensic analysis failed"
    else
        log_warn "Copilot session unavailable, skipping forensic analysis"
    fi

    if [[ -n "${WT_DIR:-}" && -d "$WT_DIR" ]]; then
        log_warn "Worktree preserved for inspection: $WT_DIR"
    fi
    if [[ -n "${TOPIC_FILE:-}" && -f "$TOPIC_FILE" ]]; then
        local failed_name
        failed_name=$(basename "$TOPIC_FILE")
        # Enhanced failure record with diary reference
        echo "forensic_entry_path: docs/diary/$(date +%Y-%m-%d)-forensic.md" >> "$TOPIC_FILE" 2>/dev/null || true
        mv "$TOPIC_FILE" ".chaplain/failed/$failed_name" 2>/dev/null || true
        log_warn "Topic moved to: .chaplain/failed/$failed_name"
    fi
    cd "$MAIN_DIR" 2>/dev/null || cd "$(dirname "$0")/.."
    write_cycle_metrics
}

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
        handle_failure "preflight"
        continue
    fi

    # ── Worktree setup ──────────────────────────────────────────────────
    if worktree_setup; then
        :
    else
        worktree_setup_status=$?
        if [[ "$worktree_setup_status" == 2 ]]; then
            CYCLE_OUTCOME="skipped"
            log_info "Skipping topic due to merged branch collision guard for $WT_BRANCH"
            rm "$TOPIC_FILE"
            write_cycle_metrics
            sleep "$POLL"
            continue
        fi
        handle_failure "worktree setup"
        continue
    fi

    # ── Enter worktree ──────────────────────────────────────────────────
    cd "$WT_DIR"
    unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
    log_info "Working in: $(pwd)"

    # ── Phase 3: Planning + Judging pipeline ────────────────────────────
    # FR-273 Phase 3: copilot session chain with shell steps between nodes
    PIPELINE_STATE="tmp/pipeline-state.json"
    ACCEPTANCE_MARKER="tmp/pre-acceptance-marker"
    GRAPH_DIR=".chaplain/graphs/watcher-plan"
    mkdir -p tmp

    # ── Step 1: Plan ────────────────────────────────────────────────────
    log_info "Step 1/4: Plan — reading topic, drafting FR..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-plan.yaml" \
        --var topic_file="$MAIN_DIR/$TOPIC_FILE" \
        --var worktree_dir="$(pwd)" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-plan.log; then
        handle_failure "plan step"
        continue
    fi

    # Shell: commit FR draft and capture created FR path
    git add feature-requests/ 2>/dev/null || true
    if git diff --cached --quiet; then
        handle_failure "plan produced no files"
        continue
    fi
    git commit -m "chore: watcher2 — FR draft from plan step" --no-verify
    # Capture the FR file created in this commit (not a stale one)
    CREATED_FR_PATH=$(git diff-tree --no-commit-id --name-only -r HEAD -- feature-requests/ \
        | grep -E 'FR-[0-9]+.*\.md$' | head -1 || true)
    if [[ -n "$CREATED_FR_PATH" ]]; then
        log_info "Plan created: $CREATED_FR_PATH"
    else
        log_warn "Could not detect FR path from plan commit"
    fi

    # ── Step 2: Research ────────────────────────────────────────────────
    log_info "Step 2/4: Research — gathering evidence..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-research.yaml" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-research.log; then
        log_warn "Research step failed — continuing without research"
    fi

    # Shell: commit research additions to FR
    git add feature-requests/ 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git commit -m "chore: watcher2 — research brief appended" --no-verify
    fi

    # ── Step 3: Write acceptance tests ──────────────────────────────────
    log_info "Step 3/4: Write acceptance tests (RED)..."
    # FR-280: Create marker file before acceptance step to fix RED verification timestamp bug
    touch "$ACCEPTANCE_MARKER"
    if ! yamlgraph graph run "$GRAPH_DIR/step-acceptance.yaml" \
        --var worktree_dir="$(pwd)" \
        --var branch="$WT_BRANCH" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-acceptance.log; then
        log_warn "Acceptance test step failed — continuing to judge"
    fi

    # Shell: verify RED (tests should fail on unmodified code)
    log_info "Verifying RED — tests should fail..."
    # FR-280: Use marker file instead of pipeline state for timestamp comparison
    TEST_FILES=$(find tests/ -name "*.py" -newer "$ACCEPTANCE_MARKER" -type f 2>/dev/null)
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
    # FR-280: Clean up marker file after RED verification
    [[ -f "$ACCEPTANCE_MARKER" ]] && rm "$ACCEPTANCE_MARKER"

    # ── Step 4: Judge ───────────────────────────────────────────────────
    log_info "Step 4/4: Judge — evaluating FR draft..."
    if ! yamlgraph graph run "$GRAPH_DIR/step-judge.yaml" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE" \
        --full 2>&1 | tee tmp/watcher2-judge.log; then
        handle_failure "judge step"
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
        git add feature-requests/ 2>/dev/null || true
        git diff --cached --quiet || git commit -m "chore: watcher2 — FR rejected by judge" --no-verify
        handle_failure "judge rejected"
        continue
    fi

    if [[ "$VERDICT" == "AMEND" || "$VERDICT" == "SPLIT" ]]; then
        log_warn "FR needs amendment ($VERDICT) — aborting cycle"
        git add feature-requests/ .chaplain/inbox/ 2>/dev/null || true
        git diff --cached --quiet || git commit -m "chore: watcher2 — FR $VERDICT by judge" --no-verify
        handle_failure "judge $VERDICT"
        continue
    fi

    # APPROVE or UNKNOWN — commit and proceed to enforcement
    git add feature-requests/ 2>/dev/null || true
    git diff --cached --quiet || git commit -m "chore: watcher2 — FR approved by judge" --no-verify

    # ── Phase 4: Enforcement pipeline ───────────────────────────────────
    # FR-273 Phase 4: implement → test/demo → critique/distill → finalize
    ENFORCE_DIR=".chaplain/graphs/watcher-enforce"
    ENFORCE_STATE="tmp/enforce-state.json"

    # Find the FR path — prefer the one created by the plan step
    if [[ -n "${CREATED_FR_PATH:-}" && -f "$CREATED_FR_PATH" ]]; then
        FR_PATH="$CREATED_FR_PATH"
    else
        # Fallback: newest FR file by git commit time
        FR_PATH=$(git log --diff-filter=A --name-only --pretty=format: -- 'feature-requests/FR-*.md' \
            | grep -E 'FR-[0-9]+.*\.md$' | head -1 || true)
    fi
    if [[ -z "$FR_PATH" ]]; then
        handle_failure "no FR file for enforcement"
        continue
    fi
    log_info "Enforcing: $FR_PATH"

    # ── Enforce Step 1: Implement ───────────────────────────────────────
    log_info "Enforce 1/4: Implement — TDD red→green..."
    if ! yamlgraph graph run "$ENFORCE_DIR/step-implement.yaml" \
        --var fr_path="$FR_PATH" \
        --var branch="$WT_BRANCH" \
        --export-state "$ENFORCE_STATE" \
        --full 2>&1 | tee tmp/watcher2-implement.log; then
        handle_failure "implement step"
        continue
    fi

    # Commit implementation
    git add -A 2>/dev/null || true
    git diff --cached --quiet || git commit -m "feat: watcher2 — implementation" --no-verify

    # ── Enforce Step 2: Test and demo ───────────────────────────────────
    log_info "Enforce 2/4: Test and demo..."
    if ! yamlgraph graph run "$ENFORCE_DIR/step-test-demo.yaml" \
        --import-state "$ENFORCE_STATE" \
        --export-state "$ENFORCE_STATE" \
        --full 2>&1 | tee tmp/watcher2-test-demo.log; then
        log_warn "Test/demo step failed — continuing to critique"
    fi

    # Commit test/demo additions
    git add -A 2>/dev/null || true
    git diff --cached --quiet || git commit -m "test: watcher2 — tests and demos" --no-verify

    # ── Enforce Step 3: Critique and distill ────────────────────────────
    log_info "Enforce 3/4: Critique and distill..."

    # Extract FR number from feature request path
    FR_NUM=$(basename "$FR_PATH" | grep -oE 'FR-[0-9]+' | sed 's/FR-//' || true)

    if ! yamlgraph graph run "$ENFORCE_DIR/step-critique.yaml" \
        --var fr_path="$FR_PATH" \
        --var fr_num="$FR_NUM" \
        --import-state "$ENFORCE_STATE" \
        --export-state "$ENFORCE_STATE" \
        --full 2>&1 | tee tmp/watcher2-critique.log; then
        handle_failure "critique step failed"
        continue
    fi

    # Commit diary/critique output
    git add -A 2>/dev/null || true
    git diff --cached --quiet || git commit -m "docs: watcher2 — critique and diary" --no-verify

    # ── Auto-Generate Changelog Fragment (FR-283) ─────────────────────────
    # Extract FR number from feature request path
    FR_NUM=$(basename "$FR_PATH" | grep -oE 'FR-[0-9]+' | sed 's/FR-//' || true)
    FR_ID="FR-${FR_NUM}"

    # Generate changelog fragment filename
    CHANGELOG_FRAG="changelog/unreleased/fr-${FR_NUM}-$(basename "$FR_PATH" .md | sed "s/FR-${FR_NUM}-//" | head -c 40).md"

    if [[ ! -f "$CHANGELOG_FRAG" ]] && ! ls changelog/unreleased/fr-"${FR_NUM}"-*.md 1>/dev/null 2>&1; then
        # Derive change type and scope from FR path
        CHANGE_TYPE="feat"
        SCOPE=$(basename "$FR_PATH" .md | sed "s/FR-${FR_NUM}-//" | cut -d- -f1)

        # Find requirement ID from capability registry
        REQ_ID=$(grep -l "fr: $FR_ID" capabilities/CAP-*.yaml 2>/dev/null | head -1 | \
            xargs -I{} grep -oE 'REQ-YG-[0-9]+' {} 2>/dev/null | head -1 || true)

        # Validate FR_NUM matches expected FR to prevent cross-wiring
        if [[ "$FR_NUM" != "$(basename "$FR_PATH" | grep -oE '[0-9]+' | head -1)" ]]; then
            log_warn "FR number mismatch detected - potential cross-wiring"
        fi

        # Generate fragment content
        mkdir -p "$(dirname "$CHANGELOG_FRAG")"
        {
            echo "---"
            echo "type: $CHANGE_TYPE"
            echo "scope: $SCOPE"
            [[ -n "$REQ_ID" ]] && echo "req: $REQ_ID"
            echo "---"
            echo "- **$FR_ID**: Generated changelog fragment. ($REQ_ID)"
        } > "$CHANGELOG_FRAG"

        log_info "Generated changelog fragment: $CHANGELOG_FRAG"
    fi

    # ── Enforce Step 4: Finalize (shell) ────────────────────────────────
    log_info "Enforce 4/4: Finalize — pre-commit + push..."

    # Progressive ruff fixing: safe first, unsafe for remaining issues
    git add -A 2>/dev/null || true
    ruff check --fix yamlgraph/ tests/ 2>/dev/null || true
    ruff check --fix --unsafe-fixes yamlgraph/ tests/ 2>/dev/null || true
    ruff format yamlgraph/ tests/ 2>/dev/null || true
    git add -A 2>/dev/null || true

    # Run pre-commit (may take multiple passes)
    PRECOMMIT_PASS=false
    for attempt in 1 2 3 4 5; do
        log_info "Pre-commit attempt $attempt/5..."
        git add -A 2>/dev/null || true
        if pre-commit run --all-files 2>&1 | tee tmp/watcher2-precommit.log; then
            PRECOMMIT_PASS=true
            break
        fi
        # Re-add after auto-fixes
        git add -A 2>/dev/null || true
    done

    if [[ "$PRECOMMIT_PASS" != "true" ]]; then
        log_warn "Pre-commit still failing after 5 attempts — invoking copilot fix..."
        if yamlgraph graph run "$ENFORCE_DIR/step-finalize.yaml" \
            --var fr_path="$FR_PATH" \
            --var branch="$WT_BRANCH" \
            --import-state "$ENFORCE_STATE" \
            --export-state "$ENFORCE_STATE" \
            --full 2>&1 | tee tmp/watcher2-finalize.log; then
            git add -A 2>/dev/null || true
        else
            log_error "Copilot finalize also failed"
        fi
    fi

    # Final commit + push
    git add -A 2>/dev/null || true
    git diff --cached --quiet || git commit -m "chore: watcher2 — finalize" --no-verify

    # Validate changelog fragment FR number matches branch name
    if ls changelog/unreleased/*.md 1>/dev/null 2>&1; then
        FRAGMENT_FR=$(grep -oE 'FR-[0-9]+' changelog/unreleased/*.md | head -1 || true)
        BRANCH_FR=$(echo "$WT_BRANCH" | grep -oE 'FR-[0-9]+' | head -1 || true)
        if [[ "$FRAGMENT_FR" != "$BRANCH_FR" ]]; then
            log_warn "Fragment FR mismatch: $FRAGMENT_FR vs $BRANCH_FR"
        fi
    fi

    # Derive PR title from FR
    FR_NUM=$(echo "$FR_PATH" | grep -oE 'FR-[0-9]+' | head -1 || true)
    PR_TITLE="feat: watcher2 enforce — ${FR_NUM:-${TOPIC_BASENAME%.md}}"

    git push origin "$WT_BRANCH" || {
        handle_failure "push"
        continue
    }

    # ── Create PR ───────────────────────────────────────────────────────
    cd "$MAIN_DIR"
    if ! create_pr; then
        handle_failure "create PR"
        continue
    fi

    # ── Wait for CI ─────────────────────────────────────────────────────
    if ! wait_ci; then
        # Attempt CI remediation (max 2 attempts)
        CI_REMEDIATED=false
        for ci_attempt in 1 2; do
            log_warn "CI failed — remediation attempt $ci_attempt/2..."

            # Capture failure logs — get run ID first (FR-284)
            CI_LOG="$MAIN_DIR/tmp/ci-failure.log"
            RUN_ID=$(gh run list --branch "$WT_BRANCH" --status failure --limit 1 --json databaseId -q '.[0].databaseId' --repo "sheikkinen/yamlgraph" 2>/dev/null || true)
            if [[ -n "$RUN_ID" ]]; then
                gh run view "$RUN_ID" --log-failed --repo "sheikkinen/yamlgraph" > "$CI_LOG" 2>&1 || true
            else
                echo "No failed run found for branch $WT_BRANCH" > "$CI_LOG"
            fi

            # Invoke copilot to diagnose and fix
            cd "$WT_DIR"
            if yamlgraph graph run "$ENFORCE_DIR/step-ci-remediate.yaml" \
                --var ci_log_path="$CI_LOG" \
                --var pr_number="$PR_NUMBER" \
                --import-state "$ENFORCE_STATE" \
                --full; then

                # Re-run finalize (pre-commit + push)
                git add -A && ruff check --fix . && ruff check --fix --unsafe-fixes . && ruff format .
                pre-commit run --all-files || true
                git add -A
                if ! git diff --cached --quiet; then
                    git commit -m "fix: watcher2 — CI remediation" --no-verify
                    git push origin "$WT_BRANCH"
                else
                    log_warn "CI remediation produced no changes — skipping commit"
                fi

                cd "$MAIN_DIR"
                if wait_ci; then
                    CI_REMEDIATED=true
                    break
                fi
            fi
        done

        if [[ "$CI_REMEDIATED" != "true" ]]; then
            handle_failure "CI (after remediation)"
            continue
        fi
    fi

    # ── Merge ───────────────────────────────────────────────────────────
    if ! merge_pr; then
        handle_failure "merge"
        continue
    fi

    # ── Cleanup ─────────────────────────────────────────────────────────
    CYCLE_OUTCOME="success"
    worktree_teardown
    post_merge
    write_cycle_metrics
    rm "$TOPIC_FILE"

    log_info "✅ Cycle complete for: $TOPIC_BASENAME"
    sleep "$POLL"
done
