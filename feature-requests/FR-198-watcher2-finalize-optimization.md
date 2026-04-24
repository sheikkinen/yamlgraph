# Feature Request: Watcher2 Finalize Pre-commit Optimization

**Priority:** MEDIUM  
**Type:** Enhancement  
**Status:** Proposed  
**Effort:** 0.5 days  
**Requested:** 2026-04-24  

## Summary

Optimize watcher2 finalize step to reduce copilot session invocations by pre-formatting code before pre-commit loops and increasing retry attempts from 3 to 5.

## Value Statement

Watcher2 pipeline completes 25 minutes faster by eliminating unnecessary copilot finalize sessions for auto-fixable pre-commit failures.

## Problem

Watcher2 finalize wastes 25 minutes spawning a copilot session because the pre-commit loop exhausts 3 attempts on cascading auto-fixers (ruff → trailing-whitespace → end-of-file-fixer), each fixing one layer per pass.

**Evidence from watcher2-run-3.log (FR-275 cycle):**
- Attempt 1: ruff auto-fixes 3 errors
- Attempt 2: trailing-whitespace fixes diary + FR files  
- Attempt 3: end-of-file-fixer fixes same files
- Result: falls through to 1500s copilot finalize session

A 4th attempt would have passed. Instead, copilot spends 25 minutes doing `git add && pre-commit run`.

**Root Cause Analysis:**
The current pre-commit configuration includes multiple auto-fixing hooks that create cascading changes:
1. `ruff` (with `--fix, --exit-non-zero-on-fix`)
2. `ruff-format`
3. `trailing-whitespace`
4. `end-of-file-fixer`

Each hook modifies files and triggers the next hook in sequence, but the current 3-attempt limit is insufficient for the cascade to complete.

## Proposed Solution

### 1. Pre-format before commit loop

Run ruff fix and format on staged files before entering the pre-commit loop to eliminate the most common auto-fix cascade at the source:

```bash
# Before pre-commit loop in watcher2.sh around line 306
git add -A 2>/dev/null || true
ruff check --fix yamlgraph/ tests/ 2>/dev/null || true
ruff format yamlgraph/ tests/ 2>/dev/null || true
git add -A 2>/dev/null || true
```

### 2. Increase pre-commit loop to 5 attempts

Change the loop from `for attempt in 1 2 3` to `for attempt in 1 2 3 4 5` in `.chaplain/watcher2.sh` line 308:

```bash
# Current
for attempt in 1 2 3; do
    log_info "Pre-commit attempt $attempt/3..."

# Proposed
for attempt in 1 2 3 4 5; do
    log_info "Pre-commit attempt $attempt/5..."
```

And update the failure message on line 320:
```bash
# Current
log_warn "Pre-commit still failing after 3 attempts — invoking copilot fix..."

# Proposed  
log_warn "Pre-commit still failing after 5 attempts — invoking copilot fix..."
```

**Rationale:**
- Three auto-fixers (ruff, trailing-whitespace, end-of-file-fixer) need at minimum 3 passes
- Two additional passes provide safety margin for edge cases
- Pre-formatting eliminates the most common ruff issues upfront

## Acceptance Criteria

- [ ] `ruff check --fix` runs before pre-commit loop
- [ ] `ruff format` runs before pre-commit loop  
- [ ] Pre-commit loop allows 5 attempts (was 3)
- [ ] Failure message updated to reflect "5 attempts"
- [ ] No copilot fallback triggered for auto-fixable cascading issues
- [ ] Tests added for the optimization logic
- [ ] Documentation updated if needed

## Implementation Details

**File to modify:** `.chaplain/watcher2.sh` (finalize section, lines ~306-320)

**Before:**
```bash
# Run pre-commit (may take multiple passes)
PRECOMMIT_PASS=false
for attempt in 1 2 3; do
    log_info "Pre-commit attempt $attempt/3..."
    git add -A 2>/dev/null || true
    if pre-commit run --all-files 2>&1 | tee tmp/watcher2-precommit.log; then
        PRECOMMIT_PASS=true
        break
    fi
    # Re-add after auto-fixes
    git add -A 2>/dev/null || true
done

if [[ "$PRECOMMIT_PASS" != "true" ]]; then
    log_warn "Pre-commit still failing after 3 attempts — invoking copilot fix..."
```

**After:**
```bash
# Pre-format to reduce auto-fix cascades
git add -A 2>/dev/null || true
ruff check --fix yamlgraph/ tests/ 2>/dev/null || true
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
```

## Alternatives Considered

1. **Skip ruff in pre-commit entirely**: Would break the fail_fast behavior and lose other ruff checks beyond formatting
2. **Reorder pre-commit hooks**: Would require extensive testing and might not solve the cascade issue
3. **Disable auto-fix in ruff pre-commit**: Would push all formatting issues to manual copilot sessions

## Risk Assessment

**Low Risk:**
- Changes are isolated to watcher2 pipeline
- Ruff commands already run in development workflow
- Increasing retry attempts is conservative
- Fallback to copilot session remains unchanged

**Potential Issues:**
- Ruff might conflict with git staging in rare edge cases
- Slightly longer pipeline execution due to extra ruff runs

## Related

- Original issue: `.chaplain/processing/gh-198.md`
- Related pre-commit config: `.pre-commit-config.yaml` (lines 5-12, ruff hooks)
- Watcher2 implementation: `.chaplain/watcher2.sh` (finalize section)
- FR-275: Test speed optimization (related context from logs)