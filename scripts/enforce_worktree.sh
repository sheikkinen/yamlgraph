#!/usr/bin/env bash
# enforce_worktree.sh - Parallel Development Pipeline via Git Worktrees (FR-106, FR-128)
#
# Creates an isolated git worktree, delegates all LLM phases to the
# enforce pipeline graph, and cleans up on exit.
#
# Usage:
#   scripts/enforce_worktree.sh <feature-request-path> [base-branch]
#
# Example:
#   scripts/enforce_worktree.sh feature-requests/FR-106-parallel-worktree-pipeline.md
#   scripts/enforce_worktree.sh feature-requests/FR-107-test.md develop
#
# The script (Presentation layer):
# 1. Validates clean working tree (no uncommitted changes)
# 2. Creates a git worktree with a branch derived from FR filename
# 3. Symlinks the shared .venv to avoid redundant installs
# 4. Delegates to: yamlgraph graph run .chaplain/graphs/enforce/graph.yaml (FR-196)
# 5. Cleans up the worktree on exit (success or failure)

set -euo pipefail

# FR-256: Pipeline timing metrics
METRIC_DIR="tmp/pipeline-metrics"
mkdir -p "$METRIC_DIR"
T_START=$(date +%s)
STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PHASE_WORKTREE_SETUP=0
PHASE_LLM_ENFORCE=0
PHASE_POST_ASSERTIONS=0
PHASE_SUCCESS_OUTPUT=0
PIPELINE_OUTCOME="failure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Validate arguments
if [[ $# -lt 1 ]]; then
    log_error "Usage: $0 <feature-request-path> [base-branch]"
    exit 1
fi

FR_PATH="$1"
BASE_BRANCH="${2:-main}"

# Validate FR file exists
if [[ ! -f "$FR_PATH" ]]; then
    log_error "Feature request file not found: $FR_PATH"
    exit 1
fi

# Use Python helpers to derive branch name and worktree path
BRANCH=$(python3 -c "from yamlgraph.utils.worktree_helpers import derive_branch_name; print(derive_branch_name('$FR_PATH'))")
WORKTREE_DIR=$(python3 -c "from yamlgraph.utils.worktree_helpers import construct_worktree_path; print(construct_worktree_path('$BRANCH'))")

log_info "Feature Request: $FR_PATH"
log_info "Branch: $BRANCH"
log_info "Worktree: $WORKTREE_DIR"
log_info "Base Branch: $BASE_BRANCH"

# Validate clean working tree using Python helper (excludes diary and feature-requests/)
log_info "Validating clean working tree..."
if ! python3 -c "from yamlgraph.utils.worktree_helpers import validate_clean_working_tree; validate_clean_working_tree(exclude_paths=['docs/diary/', '.chaplain/', 'feature-requests/'])" 2>&1; then
    log_error "Working tree has uncommitted changes. Commit or stash before running."
    exit 1
fi

# Commit FR to main before creating worktree (ensures FR exists in worktree)
# Uses --no-verify to avoid pre-commit circular dependency
if ! git diff --quiet -- "$FR_PATH" 2>/dev/null || ! git ls-files --error-unmatch "$FR_PATH" >/dev/null 2>&1; then
    log_info "Committing FR to main before worktree creation..."
    git add "$FR_PATH"
    git commit --no-verify -m "docs(FR): add $(basename "$FR_PATH" .md) for enforce pipeline"
    git push
    log_info "FR committed and pushed to main"
fi

# Save main directory for later use
MAIN_DIR="$(pwd)"

# Trap-based cleanup: remove worktree on exit (success or failure)
cleanup() {
    local exit_code=$?
    # FR-256: Write timing metrics JSON (best-effort)
    local t_end
    t_end=$(date +%s)
    local duration=$((t_end - T_START))
    local finished_at
    finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local ts_safe
    ts_safe=$(echo "$STARTED_AT" | tr -d ':' | tr -d '-' | sed 's/Z//')
    local fr_id
    fr_id=$(basename "$FR_PATH" .md | grep -oE 'FR-[0-9]+' || echo "unknown")
    if [[ $exit_code -eq 0 ]]; then PIPELINE_OUTCOME="success"; fi
    printf '{\n  "pipeline": "enforce",\n  "fr": "%s",\n  "branch": "%s",\n  "outcome": "%s",\n  "started_at": "%s",\n  "finished_at": "%s",\n  "duration_seconds": %d,\n  "phases": {\n    "worktree_setup": %d,\n    "llm_enforce": %d,\n    "post_assertions": %d,\n    "success_output": %d\n  },\n  "retries": 0\n}\n' \
        "$fr_id" "$BRANCH" "$PIPELINE_OUTCOME" "$STARTED_AT" "$finished_at" \
        "$duration" "$PHASE_WORKTREE_SETUP" "$PHASE_LLM_ENFORCE" \
        "$PHASE_POST_ASSERTIONS" "$PHASE_SUCCESS_OUTPUT" \
        > "$METRIC_DIR/enforce-${fr_id}-${ts_safe}.json" 2>/dev/null || true
    cd "$MAIN_DIR" 2>/dev/null || true
    log_info "Cleaning up worktree: $WORKTREE_DIR"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
    # Also delete the branch if it was newly created and has no remote
    if ! git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
        git branch -D "$BRANCH" 2>/dev/null || true
    fi
    # FR-139: Guard against bare=true corruption
    local bare_after
    bare_after=$(git config --get core.bare 2>/dev/null || echo "false")
    if [[ "$bare_after" == "true" ]]; then
        log_warn "Detected bare=true corruption in .git/config — restoring to bare=false"
        git config core.bare false
    fi
    # FR-174: Clean stale .pth/.egg-link entries referencing the removed worktree
    local abs_worktree
    abs_worktree=$(cd "$MAIN_DIR" && python3 -c "from pathlib import Path; print(Path('$WORKTREE_DIR').resolve())" 2>/dev/null || echo "")
    if [[ -n "$abs_worktree" && -d "$MAIN_DIR/.venv" ]]; then
        python3 -c "
from pathlib import Path
from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries
clean_stale_pth_entries(Path('$MAIN_DIR/.venv'), '$abs_worktree')
" 2>/dev/null || true
    fi
    # FR-241: Validate editable install after .pth cleaning; self-heal if broken
    if ! python3 -c "import yamlgraph" 2>/dev/null; then
        log_warn "Editable install broken after cleanup — reinstalling"
        pip install -e "$MAIN_DIR" --quiet 2>/dev/null || true
    fi
    exit $exit_code
}
trap cleanup EXIT

# Create worktree with new branch
t_phase_start=$(date +%s)
log_info "Creating git worktree..."
mkdir -p "$(dirname "$WORKTREE_DIR")"
git worktree add "$WORKTREE_DIR" -b "$BRANCH" "$BASE_BRANCH"

# Symlink shared .venv to avoid redundant installs
# FR-174: Validate .venv health before symlinking (fail loudly, not silently skip)
MAIN_VENV="$MAIN_DIR/.venv"
python3 -c "from pathlib import Path; from yamlgraph.utils.worktree_helpers import validate_venv_health; validate_venv_health(Path('$MAIN_VENV'))"
log_info "Symlinking shared .venv..."
ln -sf "$MAIN_VENV" "$WORKTREE_DIR/.venv"
# FR-174: Validate symlink resolves correctly
python3 -c "from pathlib import Path; from yamlgraph.utils.worktree_helpers import validate_venv_symlink; validate_venv_symlink(Path('$WORKTREE_DIR/.venv'), Path('$MAIN_VENV'))"
# Ensure .venv is gitignored in worktree (prevents symlink from being committed)
if ! grep -q "^\.venv$" "$WORKTREE_DIR/.gitignore" 2>/dev/null; then
    echo ".venv" >> "$WORKTREE_DIR/.gitignore"
fi

cd "$WORKTREE_DIR"
# FR-139: Sanitize git env vars to prevent bare=true corruption
unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
log_info "Working in: $(pwd)"
PHASE_WORKTREE_SETUP=$(($(date +%s) - t_phase_start))

# Delegate all LLM phases to the enforce pipeline graph (FR-128, FR-196)
# The graph handles: implement → test/demo → pre-commit → submit PR
t_phase_start=$(date +%s)
log_info "Running enforce pipeline graph..."
yamlgraph graph run .chaplain/graphs/enforce/graph.yaml \
    --var fr_path="$FR_PATH" \
    --var branch="$BRANCH" \
    --full
PHASE_LLM_ENFORCE=$(($(date +%s) - t_phase_start))

# FR-139: Post-run assertion — catch mid-run corruption
t_phase_start=$(date +%s)
cd "$MAIN_DIR"
if [[ "$(git config --get core.bare 2>/dev/null)" == "true" ]]; then
    log_error "bare=true detected after pipeline run — restoring"
    git config core.bare false
fi
PHASE_POST_ASSERTIONS=$(($(date +%s) - t_phase_start))

t_phase_start=$(date +%s)
log_info "Enforce pipeline completed successfully!"

# Print next steps
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  NEXT STEPS${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}To merge via command line:${NC}"
echo "    gh pr merge $BRANCH --squash --delete-branch"
echo ""
echo -e "  ${YELLOW}To merge via GitHub web:${NC}"
echo "    gh pr view $BRANCH --web"
echo ""
echo -e "  ${YELLOW}To discard (close PR and delete branch):${NC}"
echo "    gh pr close $BRANCH --delete-branch"
echo ""
echo -e "  ${YELLOW}To delete branch only (if PR already closed):${NC}"
echo "    git push origin --delete $BRANCH"
echo "    git branch -D $BRANCH 2>/dev/null || true"
echo ""
echo -e "  ${YELLOW}After merging, finalize:${NC}"
echo "    git checkout main && git pull"
echo "    scripts/finalize_merge.sh $FR_PATH"
echo ""
PHASE_SUCCESS_OUTPUT=$(($(date +%s) - t_phase_start))
