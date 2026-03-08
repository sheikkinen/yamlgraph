# Feature Request: FR-141 Squash Merge Orphan Detection

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a pre-finalization orphan check to `scripts/finalize_merge.sh` that detects files deleted by a squash merge which `main` modified after the feature branch diverged, warning the operator before content is silently lost.

## Value Statement

Pipeline operators are warned before orphaned content silently vanishes during squash merges, preventing data loss like the FR-134 diary entries lost in Audit XXVIII.

## Problem

When FR-134 (diary folder refactor) was squash-merged, entries added to `docs/diary.md` on `main` after the branch diverged were silently replaced. The migration itself became the last victim of the concurrent-write problem it was designed to solve (Audit XXVIII heuristic: *The last migration victim is the migration itself*).

`finalize_merge.sh` currently performs four post-merge steps (CHANGELOG entry, FR status update, diary stub, commit) but has no awareness of content that may have been orphaned by the merge. This gap means:

1. Content added to `main` between branch point and merge is silently lost when the squash deletes a file.
2. The loss is only discoverable through manual `git log` archaeology.
3. Two consecutive audits (XXVII, XXVIII) flagged the symptom (unfilled reflection stub) without detecting the root cause (orphaned diary entries from the pre-migration format).

## Proposed Solution

Add a **Step 0: Orphan Detection** to `finalize_merge.sh` that runs before the existing CHANGELOG/status/diary steps.

### Scope: Deletions Only

This FR addresses **deleted files only** (`--diff-filter=D`). Files that are fully overwritten (same path, completely different content) are out of scope. The motivating case (FR-134) was a deletion (`diary.md` replaced by `diary/` folder), and deletions have an unambiguous algorithmic definition. Overwrite detection requires a similarity threshold (e.g., 100% changed lines) which introduces false positives and belongs in a separate FR if needed.

### Interface Contract

The current interface:

```
finalize_merge.sh <feature-request-path>
```

Becomes:

```
finalize_merge.sh <feature-request-path> [branch-name] [--strict]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<feature-request-path>` | Yes | Path to FR markdown (existing) |
| `[branch-name]` | No | Name of the merged feature branch (e.g., `feature/FR-134`). Used to compute divergence point via `git merge-base main <branch-name>`. |
| `--strict` | No | Exit non-zero when orphans are detected (for CI use). |

**Branch name resolution order:**

1. Explicit `[branch-name]` parameter (most reliable).
2. Parse from squash commit message — GitHub default format includes `* branch-name:` in the body. Used as fallback when branch parameter is omitted.
3. If neither resolves, skip orphan detection with a warning: `⚠️  Cannot determine branch point; orphan detection skipped. Pass branch name to enable.`

### Algorithm (Amended)

```bash
# Step 0: Orphan Detection
# Requires: branch name or parseable squash commit message

resolve_branch_name() {
    local explicit_branch="$1"
    if [[ -n "$explicit_branch" ]]; then
        echo "$explicit_branch"
        return
    fi
    # Fallback: parse from squash commit message (GitHub format)
    local parsed
    parsed=$(git log -1 --format="%b" HEAD | grep -oP '^\* \K\S+(?=:)' | head -1)
    if [[ -n "$parsed" ]]; then
        echo "$parsed"
        return
    fi
    return 1
}

BRANCH_NAME=$(resolve_branch_name "$2")
if [[ $? -ne 0 ]]; then
    echo "⚠️  Cannot determine branch point; orphan detection skipped."
    echo "   Pass branch name to enable: finalize_merge.sh <fr-path> <branch>"
else
    # 1. Find the actual divergence point
    MERGE_BASE=$(git merge-base main "$BRANCH_NAME")

    # 2. List files the squash commit deleted relative to the merge base
    DELETED_FILES=$(git diff --name-only --diff-filter=D "$MERGE_BASE" HEAD)

    # 3. For each deleted file, check if main modified it after divergence
    ORPHANS_FOUND=false
    for file in $DELETED_FILES; do
        MAIN_COMMITS=$(git log --oneline "$MERGE_BASE"..HEAD~1 -- "$file")
        if [[ -n "$MAIN_COMMITS" ]]; then
            echo "⚠️  ORPHAN: $file was modified on main after branch diverged"
            echo "   Commits on main:"
            echo "$MAIN_COMMITS" | sed 's/^/     /'
            echo "   Recover with: git show HEAD~1:$file"
            ORPHANS_FOUND=true
        fi
    done

    # 4. Handle results
    if [[ "$ORPHANS_FOUND" == true ]]; then
        echo ""
        echo "⚠️  Orphaned content detected. Review before proceeding."
        echo "   Use 'git log -p <commit> -- <file>' to inspect lost content."
        if [[ "$STRICT_MODE" == true ]]; then
            echo "❌  --strict mode: aborting finalization."
            exit 1
        fi
    else
        echo "✓ No orphaned content detected."
    fi
fi

# Existing Steps 1-4 continue unchanged...
```

**Key fix from Judgement Issue #1:** The algorithm uses `git merge-base main <branch-name>` with the *actual feature branch name* instead of the flawed `git merge-base HEAD~1 HEAD` which trivially returns `HEAD~1` in linear post-squash history.

### False Positive Prevention

A file is flagged as orphaned **only** when both conditions hold:

1. The file was **deleted** by the squash commit relative to the merge base (`--diff-filter=D`).
2. `main` has commits **modifying that file** between the merge base and the pre-squash HEAD (`git log MERGE_BASE..HEAD~1 -- $file`).

Files that exist only in the feature branch (never on `main` post-divergence) produce no `MAIN_COMMITS` and are correctly excluded. Files deleted by the feature branch that `main` never touched post-divergence are also excluded.

## Acceptance Criteria

- [ ] `finalize_merge.sh` accepts optional `[branch-name]` positional parameter and `--strict` flag
- [ ] When branch name is provided, orphan detection finds files deleted by squash that `main` modified post-divergence
- [ ] When branch name is omitted, fallback parses squash commit message; if unparseable, detection is skipped with warning
- [ ] Warning output includes: file path, commit SHAs on main, and recovery command (`git show HEAD~1:<file>`)
- [ ] `--strict` flag exits non-zero when orphans are detected
- [ ] No false positives: files only in the feature branch (never modified on main post-divergence) are not flagged
- [ ] Existing finalize behavior (Steps 1-4: CHANGELOG, FR status, diary stub, commit) is unchanged when no orphans exist
- [ ] Tests: shell test with mock git history exercising: orphan detected, clean merge, strict-mode exit, branch-name fallback parsing, skip-when-unparseable
- [ ] Documentation: `finalize_merge.sh` header comment updated with new interface; `CLAUDE.md` gains merge safety subsection under Pull Request Conventions

## Prerequisites

- **FR-140** (Clean GIT_* env test fixture) — Approved. Orphan detection tests use subprocess git calls that require clean GIT_* environment. Must be implemented first.
- **FR-134 reflection stub** (`docs/diary/2026-03-08-reflection-fr-134.md`) — Must be filled with genuine content. Trap: `working_system_inertia`. Heuristic: *The last migration victim is the migration itself.*

## Alternatives Considered

1. **`git merge-base HEAD~1 HEAD` (original algorithm)** — Rejected. After squash merge, history is linear; `merge-base` trivially returns `HEAD~1`, making the detection range empty. See Judgement Issue #1.
2. **Tag-before-merge anchor** (`pre-merge/$FR_NUM` tag) — Reliable but requires upstream workflow change (tagging before every merge). Higher friction than accepting branch name.
3. **Rebase merge instead of squash** — Preserves full history but contradicts squash-merge-only convention (`CLAUDE.md` Pull Request Conventions).
4. **Automated content recovery** — Too risky; orphaned content may conflict with the new file structure. Warning + manual recovery is safer.
5. **Include "fully rewritten" files** — Requires defining a similarity threshold for `--diff-filter=M` files. Introduces false positive risk. Deferred to future FR if needed.

## Related

- `scripts/finalize_merge.sh` — target script for enhancement
- `feature-requests/FR-134-diary-folder-refactor.md` — the migration that exposed the orphan problem
- `feature-requests/FR-140-clean-git-env-test-fixture.md` — prerequisite for test infrastructure
- `docs/diary/2026-03-08-inquisitor-audit-xxvii.md` — first audit flagging the drift
- `docs/diary/2026-03-08-inquisitor-audit-xxviii.md` — root cause heuristic

## Judgement Log

### Judgement 1: AMEND (2026-03-08)

Returned to inbox. Three issues identified:

1. **CRITICAL — Algorithm flaw:** `git merge-base HEAD~1 HEAD` is a no-op in linear history. **Resolved:** Accept branch name as parameter with commit-message-parse fallback.
2. **MAJOR — "Fully rewritten" undefined:** No algorithmic definition for overwrite detection. **Resolved:** Scoped to deletions only (`--diff-filter=D`). Overwrite detection deferred.
3. **MAJOR — Interface contract unspecified:** New parameter not defined. **Resolved:** `finalize_merge.sh <fr-path> [branch-name] [--strict]` with resolution order documented.

### Judgement 2: APPROVE (2026-03-08)

All three Judgement 1 issues resolved. Scope is clear, minimal, and internally consistent. Acceptance criteria are measurable. Algorithm is sound for the deletions-only case.

**Implementation note:** Guard `git merge-base main "$BRANCH_NAME"` against deleted branch refs — if the ref no longer exists locally, fall back to the warning path instead of letting `set -euo pipefail` abort the script. This is a defensive coding detail, not a design gap.

Scope frozen. Authority granted.
