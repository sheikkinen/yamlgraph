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
# 4. Delegates to: yamlgraph graph run examples/enforce/graph.yaml
# 5. Cleans up the worktree on exit (success or failure)

set -euo pipefail

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
    exit $exit_code
}
trap cleanup EXIT

# Create worktree with new branch
log_info "Creating git worktree..."
mkdir -p "$(dirname "$WORKTREE_DIR")"
git worktree add "$WORKTREE_DIR" -b "$BRANCH" "$BASE_BRANCH"

# Symlink shared .venv to avoid redundant installs
MAIN_VENV="$MAIN_DIR/.venv"
if [[ -d "$MAIN_VENV" ]]; then
    log_info "Symlinking shared .venv..."
    ln -sf "$MAIN_VENV" "$WORKTREE_DIR/.venv"
    # Ensure .venv is gitignored in worktree (prevents symlink from being committed)
    if ! grep -q "^\.venv$" "$WORKTREE_DIR/.gitignore" 2>/dev/null; then
        echo ".venv" >> "$WORKTREE_DIR/.gitignore"
    fi
fi

cd "$WORKTREE_DIR"
# FR-139: Sanitize git env vars to prevent bare=true corruption
unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
log_info "Working in: $(pwd)"

# Delegate all LLM phases to the enforce pipeline graph (FR-128)
# The graph handles: implement → test/demo → pre-commit → submit PR
log_info "Running enforce pipeline graph..."
yamlgraph graph run examples/enforce/graph.yaml \
    --var fr_path="$FR_PATH" \
    --var branch="$BRANCH" \
    --full

# FR-139: Post-run assertion — catch mid-run corruption
cd "$MAIN_DIR"
if [[ "$(git config --get core.bare 2>/dev/null)" == "true" ]]; then
    log_error "bare=true detected after pipeline run — restoring"
    git config core.bare false
fi

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
