#!/usr/bin/env bash
# scripts/chaplain.sh — Plan → Judge loop for research subjects
# Usage: scripts/chaplain.sh <subjects-file> [--dry-run] [--model MODEL]
set -euo pipefail
cd "$(dirname "$0")/.."

# --- Config ---
PLAN_MODEL="claude-sonnet-4.6"
JUDGE_MODEL="claude-sonnet-4.6"
MAX_JUDGE_CYCLES=3
TIMEOUT=120
DRY_RUN=false
PROMPTS_DIR="scripts/chaplain-prompts"
FR_DIR="feature-requests"
LOG_DIR=".chaplain/logs"

# --- Parse args ---
SUBJECTS_FILE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --model) PLAN_MODEL="$2"; JUDGE_MODEL="$2"; shift 2 ;;
        --plan-model) PLAN_MODEL="$2"; shift 2 ;;
        --judge-model) JUDGE_MODEL="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) SUBJECTS_FILE="$1"; shift ;;
    esac
done

if [[ -z "$SUBJECTS_FILE" ]]; then
    echo "Usage: scripts/chaplain.sh <subjects-file> [--dry-run] [--model MODEL]"
    echo ""
    echo "Options:"
    echo "  --dry-run         Print prompts without invoking copilot"
    echo "  --model MODEL     Set model for both plan and judge"
    echo "  --plan-model M    Set model for planning (default: claude-sonnet-4.6)"
    echo "  --judge-model M   Set model for judging (default: claude-sonnet-4.6)"
    echo "  --timeout SECS    Timeout per copilot invocation (default: 120)"
    exit 1
fi

if [[ ! -f "$SUBJECTS_FILE" ]]; then
    echo "ERROR: Subjects file not found: $SUBJECTS_FILE" >&2
    exit 1
fi

mkdir -p "$LOG_DIR"

# --- Read subjects ---
SUBJECTS=()
while IFS= read -r line; do
    # Strip leading "- ", whitespace, empty lines, comments
    line="${line#"${line%%[![:space:]]*}"}"  # ltrim
    line="${line%"${line##*[![:space:]]}"}"  # rtrim
    line="${line#- }"                        # strip bullet
    [[ -z "$line" || "$line" == \#* ]] && continue
    SUBJECTS+=("$line")
done < "$SUBJECTS_FILE"

if [[ ${#SUBJECTS[@]} -eq 0 ]]; then
    echo "ERROR: No subjects found in $SUBJECTS_FILE" >&2
    exit 1
fi

echo "📋 ${#SUBJECTS[@]} subjects loaded from $SUBJECTS_FILE"
for s in "${SUBJECTS[@]}"; do echo "   • $s"; done
echo ""

# --- Helpers ---
slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-60 | sed 's/-$//'
}

next_fr_number() {
    local max=0
    for f in "$FR_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local num
        num=$(basename "$f" | grep -oE '^[0-9]+' | head -1)
        [[ -n "$num" ]] && (( 10#$num > max )) && max=$((10#$num))
    done
    # Also check draft- files
    for f in "$FR_DIR"/draft-*.md; do
        [[ -f "$f" ]] || continue
        local num
        num=$(basename "$f" | sed 's/^draft-//' | grep -oE '^[0-9]+' | head -1)
        [[ -n "$num" ]] && (( 10#$num > max )) && max=$((10#$num))
    done
    echo $((max + 1))
}

run_copilot() {
    local prompt="$1"
    local model="$2"
    local logfile="$3"

    if $DRY_RUN; then
        echo "--- DRY RUN ---"
        echo "Model: $model"
        echo "Prompt (first 500 chars):"
        echo "${prompt:0:500}"
        echo "--- END DRY RUN ---"
        return 0
    fi

    timeout "$TIMEOUT" copilot -p "$prompt" \
        -s --model "$model" \
        --allow-all-tools --no-ask-user \
        2>&1 | tee "$logfile"
}

# --- Load prompt templates ---
PLAN_TEMPLATE=$(cat "$PROMPTS_DIR/plan.md")
JUDGE_TEMPLATE=$(cat "$PROMPTS_DIR/judge.md")
AMEND_TEMPLATE=$(cat "$PROMPTS_DIR/amend.md")

# --- Process each subject ---
RESULTS=()
FR_COUNTER=$(next_fr_number)
for subject in "${SUBJECTS[@]}"; do
    slug=$(slugify "$subject")
    fr_num=$FR_COUNTER
    FR_COUNTER=$((FR_COUNTER + 1))
    draft_file="$FR_DIR/draft-${fr_num}-${slug}.md"

    echo "═══════════════════════════════════════════════════════════"
    echo "📝 Subject: $subject"
    echo "   FR: $fr_num | File: $draft_file"
    echo "═══════════════════════════════════════════════════════════"

    # --- Phase 1: Plan ---
    echo ""
    echo "  ✏️  Planning..."
    plan_prompt="${PLAN_TEMPLATE//\{\{SUBJECT\}\}/$subject}"
    plan_prompt="${plan_prompt//\{\{FR_NUMBER\}\}/$fr_num}"
    plan_prompt="${plan_prompt//\{\{DRAFT_FILE\}\}/$draft_file}"

    run_copilot "$plan_prompt" "$PLAN_MODEL" "$LOG_DIR/plan-${slug}.log"

    if $DRY_RUN; then
        RESULTS+=("$subject: DRY RUN")
        echo ""
        continue
    fi

    # Check if plan created the file
    if [[ ! -f "$draft_file" ]]; then
        echo "  ⚠️  Plan did not create $draft_file — skipping judge"
        RESULTS+=("$subject: PLAN FAILED (no file created)")
        echo ""
        continue
    fi

    echo "  ✓ Draft created: $draft_file"

    # --- Phase 2: Judge (with amend loop) ---
    verdict="AMEND"
    cycle=0
    while [[ "$verdict" == "AMEND" && $cycle -lt $MAX_JUDGE_CYCLES ]]; do
        cycle=$((cycle + 1))
        echo ""
        echo "  ⚖️  Judging (cycle $cycle/$MAX_JUDGE_CYCLES)..."

        judge_prompt="${JUDGE_TEMPLATE//\{\{DRAFT_FILE\}\}/$draft_file}"
        judge_prompt="${judge_prompt//\{\{SUBJECT\}\}/$subject}"

        judge_output=$(run_copilot "$judge_prompt" "$JUDGE_MODEL" "$LOG_DIR/judge-${slug}-${cycle}.log")

        # Extract verdict from judge output
        if echo "$judge_output" | grep -qi "APPROVE"; then
            verdict="APPROVE"
        elif echo "$judge_output" | grep -qi "REJECT"; then
            verdict="REJECT"
        elif echo "$judge_output" | grep -qi "AMEND"; then
            verdict="AMEND"
        else
            # Default: if judge didn't say explicitly, treat as approve
            verdict="APPROVE"
        fi

        echo "  → Verdict: $verdict"

        if [[ "$verdict" == "AMEND" && $cycle -lt $MAX_JUDGE_CYCLES ]]; then
            echo ""
            echo "  🔧 Amending..."
            amend_prompt="${AMEND_TEMPLATE//\{\{DRAFT_FILE\}\}/$draft_file}"
            amend_prompt="${amend_prompt//\{\{SUBJECT\}\}/$subject}"

            run_copilot "$amend_prompt" "$PLAN_MODEL" "$LOG_DIR/amend-${slug}-${cycle}.log"
            echo "  ✓ Amendment applied"
        fi
    done

    if [[ "$verdict" == "AMEND" ]]; then
        verdict="AMEND (max cycles reached)"
    fi

    RESULTS+=("$subject: $verdict → $draft_file")
    echo ""
done

# --- Summary ---
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 Chaplain Summary"
echo "═══════════════════════════════════════════════════════════"
for r in "${RESULTS[@]}"; do
    echo "  $r"
done
echo ""
echo "Review: ls $FR_DIR/draft-*.md"
echo "Logs:   ls $LOG_DIR/"
