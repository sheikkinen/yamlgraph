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

# Validate clean working tree using Python helper (excludes diary and feature-requests/)
log_info "Validating clean working tree..."
if ! python3 -c "from yamlgraph.utils.worktree_helpers import validate_clean_working_tree; validate_clean_working_tree(exclude_paths=['docs/diary.md', 'feature-requests/'])" 2>&1; then
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
log_info "Working in: $(pwd)"

# Phase 1: Implementation (copilot)
log_info "Phase 1: Implementation..."
IMPLEMENT_PROMPT="Read the feature request at $FR_PATH. Follow TDD: write failing tests first, then implement the minimal change to make tests pass. Do not run pre-commit or git commands - just implement the code."

copilot -p "$IMPLEMENT_PROMPT" --allow-all
IMPL_EXIT=$?
if [[ $IMPL_EXIT -ne 0 ]]; then
    log_error "Implementation phase failed with exit code $IMPL_EXIT"
    exit 1
fi

# Phase 2: Test and Demo (copilot)
log_info "Phase 2: Test and Demo..."
TEST_PROMPT="Run pytest for this feature. If tests fail, fix the code. Create a simple demo or example if applicable. Do not run pre-commit or git commands."

copilot -p "$TEST_PROMPT" --allow-all --continue
TEST_EXIT=$?
if [[ $TEST_EXIT -ne 0 ]]; then
    log_error "Test phase failed with exit code $TEST_EXIT"
    exit 1
fi

# Phase 3: Pre-commit loop (shell runs pre-commit, copilot fixes)
log_info "Phase 3: Pre-commit checks..."
MAX_PRECOMMIT_ATTEMPTS=5
for i in $(seq 1 $MAX_PRECOMMIT_ATTEMPTS); do
    log_info "Pre-commit attempt $i/$MAX_PRECOMMIT_ATTEMPTS..."

    if pre-commit run --all-files 2>&1 | tee /tmp/precommit-output.txt; then
        log_info "Pre-commit passed!"
        break
    fi

    if [[ $i -eq $MAX_PRECOMMIT_ATTEMPTS ]]; then
        log_error "Pre-commit failed after $MAX_PRECOMMIT_ATTEMPTS attempts"
        cat /tmp/precommit-output.txt
        exit 1
    fi

    log_warn "Pre-commit failed, asking copilot to fix..."
    FIX_PROMPT="Pre-commit hooks failed. Here's the output:

$(cat /tmp/precommit-output.txt)

Fix the issues. Do not run pre-commit yourself - I will run it after you fix the code."

    copilot -p "$FIX_PROMPT" --allow-all --continue
done

# Phase 4: Commit and Push (shell)
log_info "Phase 4: Commit and push..."
FR_NUM=$(echo "$FR_PATH" | grep -oE 'FR-[0-9]+')
COMMIT_MSG="feat: $FR_NUM implementation

Auto-generated via enforce_worktree.sh pipeline"

git add -A
git commit -m "$COMMIT_MSG" --no-verify  # Skip hooks, we already ran them
git push -u origin "$BRANCH"

# Phase 5: Create PR (shell)
log_info "Phase 5: Creating PR..."
PR_TITLE="$FR_NUM: $(head -1 "$FR_PATH" | sed 's/^#* *//')"
PR_BODY="Automated PR from enforce_worktree.sh

Feature Request: $FR_PATH
Branch: $BRANCH"

gh pr create --title "$PR_TITLE" --body "$PR_BODY" --base "$BASE_BRANCH" || log_warn "PR creation failed or PR already exists"

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
