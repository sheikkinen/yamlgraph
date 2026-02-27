#!/usr/bin/env bash
# enforce_worktree.sh - Parallel Development Pipeline via Git Worktrees (FR-106)
#
# Creates an isolated git worktree, runs the enforce pipeline graph,
# and cleans up - enabling parallel feature development.
#
# Usage:
#   scripts/enforce_worktree.sh <feature-request-path> [base-branch]
#
# Example:
#   scripts/enforce_worktree.sh feature-requests/FR-106-parallel-worktree-pipeline.md
#   scripts/enforce_worktree.sh feature-requests/FR-107-test.md develop
#
# The script:
# 1. Validates clean working tree (no uncommitted changes)
# 2. Creates a git worktree with a branch derived from FR filename
# 3. Symlinks the shared .venv to avoid redundant installs
# 4. Runs the enforce pipeline graph inside the worktree
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

# Validate clean working tree using Python helper (excludes diary - inquisitor writes there)
log_info "Validating clean working tree..."
if ! python3 -c "from yamlgraph.utils.worktree_helpers import validate_clean_working_tree; validate_clean_working_tree(exclude_paths=['docs/diary.md'])" 2>&1; then
    log_error "Working tree has uncommitted changes. Commit or stash before running."
    exit 1
fi

# Trap-based cleanup: remove worktree on exit (success or failure)
cleanup() {
    local exit_code=$?
    log_info "Cleaning up worktree: $WORKTREE_DIR"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
    # Also delete the branch if it was newly created and has no remote
    if ! git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
        git branch -D "$BRANCH" 2>/dev/null || true
    fi
    exit $exit_code
}
trap cleanup EXIT

# Create worktree with new branch
log_info "Creating git worktree..."
mkdir -p "$(dirname "$WORKTREE_DIR")"
git worktree add "$WORKTREE_DIR" -b "$BRANCH" "$BASE_BRANCH"

# Symlink shared .venv to avoid redundant installs
MAIN_VENV="$(pwd)/.venv"
if [[ -d "$MAIN_VENV" ]]; then
    log_info "Symlinking shared .venv..."
    ln -sf "$MAIN_VENV" "$WORKTREE_DIR/.venv"
fi

# Run the enforce pipeline graph inside the worktree
log_info "Running enforce pipeline in worktree..."
cd "$WORKTREE_DIR"

# Check if the graph exists (it might not if it's being implemented)
GRAPH_PATH="examples/enforce/graph.yaml"
if [[ ! -f "$GRAPH_PATH" ]]; then
    log_error "Enforce graph not found: $GRAPH_PATH"
    log_error "The enforce pipeline graph must exist before running this script."
    exit 1
fi

yamlgraph graph run "$GRAPH_PATH" \
    --var fr_path="$FR_PATH" \
    --var branch="$BRANCH" \
    --full

log_info "Enforce pipeline completed successfully!"
