#!/usr/bin/env bash
# copilot_instrument.sh — Local Copilot process-mining instrumentation (FR-362)
#
# Usage:
#   scripts/copilot_instrument.sh [--run-id ID] [--base-ref REF] [--copilot-bin BIN] [--keep-worktree]
#
# Two-phase contract:
#   1) plan       (fresh session)
#   2) implement  (resumed with --resume <session-id>)
#
# Output contract:
#   outputs/copilot-instrumentation/<run-id>/<phase>/
#     - prompt.txt
#     - command.txt
#     - stdout.jsonl
#     - stderr.log
#     - share.md
#     - otel.jsonl
#     - copilot-debug.log
#     - git-status.txt
#     - git-diff.patch
#
# Safety boundary:
#   - Copilot execution runs only inside a disposable git worktree.
#   - The disposable worktree is removed at exit unless --keep-worktree is set.

set -euo pipefail

RUN_ID=""
BASE_REF="HEAD"
COPILOT_BIN="${COPILOT_BIN:-copilot}"
KEEP_WORKTREE=false

usage() {
    cat <<'EOF'
Run local two-phase Copilot instrumentation for process-mining (FR-362).

Usage:
  scripts/copilot_instrument.sh [options]

Options:
  --run-id ID          Explicit run ID (default: UTC timestamp)
  --base-ref REF       Git ref used to create disposable worktree (default: HEAD)
  --copilot-bin BIN    Copilot binary name/path (default: copilot)
  --keep-worktree      Keep disposable worktree for manual inspection
  -h, --help           Show this help

Phases:
  plan:
    copilot --silent --share <.../plan/share.md> -p "<plan prompt>"

  implement (resumed):
    copilot --silent --share <.../implement/share.md> --resume <session-id> -p "<implement prompt>"

Artifacts are written under:
  outputs/copilot-instrumentation/<run-id>/
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-id)
            RUN_ID="$2"
            shift 2
            ;;
        --base-ref)
            BASE_REF="$2"
            shift 2
            ;;
        --copilot-bin)
            COPILOT_BIN="$2"
            shift 2
            ;;
        --keep-worktree)
            KEEP_WORKTREE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

REPO_ROOT=$(git rev-parse --show-toplevel)
if [[ -z "$RUN_ID" ]]; then
    RUN_ID=$(date -u +"%Y%m%dT%H%M%SZ")
fi

OUTPUT_DIR="$REPO_ROOT/outputs/copilot-instrumentation/$RUN_ID"
WORKTREE_DIR="$REPO_ROOT/tmp/copilot-instrumentation/worktree-$RUN_ID"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$WORKTREE_DIR")"

cleanup() {
    if [[ "$KEEP_WORKTREE" == false && -d "$WORKTREE_DIR" ]]; then
        git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_DIR" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

git -C "$REPO_ROOT" worktree add --detach "$WORKTREE_DIR" "$BASE_REF" >/dev/null
WORKTREE_ROOT=$(git -C "$WORKTREE_DIR" rev-parse --show-toplevel)
if [[ "$WORKTREE_ROOT" == "$REPO_ROOT" ]]; then
    echo "Refusing to run outside disposable worktree boundary." >&2
    exit 1
fi

capture_debug_log() {
    local phase_dir="$1"
    local copilot_log_dir="$HOME/.copilot/logs"
    if [[ -d "$copilot_log_dir" ]]; then
        local latest_log
        latest_log=$(ls -1t "$copilot_log_dir"/* 2>/dev/null | head -n 1 || true)
        if [[ -n "${latest_log:-}" && -f "$latest_log" ]]; then
            cp "$latest_log" "$phase_dir/copilot-debug.log"
            return
        fi
    fi
    printf 'No Copilot debug log found at %s\n' "$copilot_log_dir" >"$phase_dir/copilot-debug.log"
}

capture_git_state() {
    local phase_dir="$1"
    git -C "$WORKTREE_DIR" --no-pager status --short --branch >"$phase_dir/git-status.txt"
    git -C "$WORKTREE_DIR" --no-pager diff >"$phase_dir/git-diff.patch"
}

ensure_otel_artifact() {
    local phase="$1"
    local phase_dir="$2"
    local otel_file="$phase_dir/otel.jsonl"
    if [[ ! -s "$otel_file" ]]; then
        local ts
        ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        printf '{"phase":"%s","event_type":"otel_placeholder","timestamp":"%s","summary":"No exporter configured; set COPILOT_OTEL_JSONL to capture spans."}\n' \
            "$phase" "$ts" >"$otel_file"
    fi
}

run_phase() {
    local phase="$1"
    local prompt="$2"
    local resume_id="${3:-}"
    local phase_dir="$OUTPUT_DIR/$phase"
    local otel_file="$phase_dir/otel.jsonl"

    mkdir -p "$phase_dir"
    printf '%s\n' "$prompt" >"$phase_dir/prompt.txt"

    local cmd=("$COPILOT_BIN" "--silent" "--share" "$phase_dir/share.md")
    if [[ -n "$resume_id" ]]; then
        cmd+=("--resume" "$resume_id")
    fi
    cmd+=("-p" "$prompt")

    printf '%q ' "${cmd[@]}" >"$phase_dir/command.txt"
    printf '\n' >>"$phase_dir/command.txt"

    export COPILOT_OTEL_JSONL="$otel_file"
    (
        cd "$WORKTREE_DIR"
        "${cmd[@]}" >"$phase_dir/stdout.jsonl" 2>"$phase_dir/stderr.log"
    )

    capture_debug_log "$phase_dir"
    capture_git_state "$phase_dir"
    ensure_otel_artifact "$phase" "$phase_dir"
}

extract_session_id() {
    local share_file="$1"
    sed -nE 's/.*\*\*Session ID:\*\*[[:space:]]*`([a-f0-9-]+)`.*/\1/p' "$share_file" | head -n 1
}

PLAN_PROMPT=${PLAN_PROMPT:-"Plan an implementation against the Minesweeper target. Return concrete ordered steps."}
IMPLEMENT_PROMPT=${IMPLEMENT_PROMPT:-"Implement the approved plan for the Minesweeper target in this disposable worktree."}

echo "▶ Running phase: plan"
run_phase "plan" "$PLAN_PROMPT"

PLAN_SHARE="$OUTPUT_DIR/plan/share.md"
if [[ ! -f "$PLAN_SHARE" ]]; then
    echo "Missing plan share markdown: $PLAN_SHARE" >&2
    exit 1
fi

SESSION_ID=$(extract_session_id "$PLAN_SHARE")
if [[ -z "$SESSION_ID" ]]; then
    echo "Failed to extract session ID from plan phase share file." >&2
    exit 1
fi

echo "▶ Running phase: implement (resumed)"
run_phase "implement" "$IMPLEMENT_PROMPT" "$SESSION_ID"

cat >"$OUTPUT_DIR/run-metadata.json" <<EOF
{
  "run_id": "$RUN_ID",
  "base_ref": "$BASE_REF",
  "worktree": "$WORKTREE_DIR",
  "plan_session_id": "$SESSION_ID",
  "phases": ["plan", "implement"]
}
EOF

echo "✓ Instrumentation complete: $OUTPUT_DIR"
