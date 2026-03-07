# Feature Request: Co-authored-by Trailer Enforcement via Pre-commit Hook

**FR-132**
**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-03-07

## Summary

Add a `commit-msg` pre-commit hook that rejects commits missing the `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer, and fix `enforce_worktree.sh` to inject the trailer in all commits it creates.

## Value Statement

All contributors get mechanical enforcement of the Copilot co-authorship trailer, eliminating a five-audit calcification streak (CALCIFIED-4 through CALCIFIED-6) that memory-based compliance could not resolve.

## Problem

The Copilot `Co-authored-by` trailer has been flagged as a violation in Inquisitor Audits XXII, XXIII, XXIV, XXV, and XXVI — five consecutive audits spanning 2026-03-07. The audits escalated the finding from CALCIFIED-4 to CALCIFIED-6 before a brief manual fix in Audit XXV (commit `27bc679`), which immediately regressed in Audit XXVI (commit `a6feb1c`).

**Root cause:** No mechanical gate exists. Compliance depends on human memory, which regresses to mean under workload. The Knowledge Graph's `audit_as_ritual` trap has been triggered: "3+ audits without fix → ritual, not process."

**Architectural gap:**
- `scripts/enforce_worktree.sh` creates two commits (lines 69 and 162–168) using `git commit -m` without any trailer.
- `scripts/finalize_merge.sh` already includes the trailer (line 107) — proving the pattern works but is inconsistently applied.
- FR-127 (CI Conventional Commit enforcement) explicitly covers only commit type prefix validation, not trailers.

## Proposed Solution

### 1. Pre-commit hook (commit-msg stage)

Add a local `commit-msg` hook to `.pre-commit-config.yaml` that validates the Copilot trailer is present:

```yaml
  - id: copilot-trailer
    name: Co-authored-by Copilot trailer
    entry: >-
      bash -c 'grep -q "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>" "$1"
      || { echo "✗ Missing Co-authored-by: Copilot trailer"; exit 1; }'
    language: system
    stages: [commit-msg]
    always_run: true
```

Place this hook **before** the `absolution` hook so failures block absolution.

### 2. Fix `enforce_worktree.sh`

Update the two commit points to include the trailer:

**Line 69** (FR commit):
```bash
# Before
git commit --no-verify -m "docs(FR): add $(basename "$FR_PATH" .md) for enforce pipeline"

# After — write to tmp file to include trailer
mkdir -p ./tmp
cat > ./tmp/msg.txt << EOF
docs(FR): add $(basename "$FR_PATH" .md) for enforce pipeline

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
EOF
git commit --no-verify -F ./tmp/msg.txt
```

**Lines 162–168** (feature commit):
```bash
# Before
COMMIT_MSG="feat: $FR_NUM implementation

Auto-generated via enforce_worktree.sh pipeline"
git add -A
git commit -m "$COMMIT_MSG" --no-verify

# After — write to tmp file to include trailer
mkdir -p ./tmp
cat > ./tmp/msg.txt << EOF
feat: $FR_NUM implementation

Auto-generated via enforce_worktree.sh pipeline

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
EOF
git add -A
git commit --no-verify -F ./tmp/msg.txt
```

Note: `--no-verify` is required for pipeline commits (they run outside the normal hook context). The trailer is injected directly, not validated by the hook.

### 3. No changes to `finalize_merge.sh`

`finalize_merge.sh` already includes the trailer on line 107. No action needed.

## Acceptance Criteria

- [ ] `git commit` without Copilot `Co-authored-by` trailer → rejected by `commit-msg` hook
- [ ] `git commit` with Copilot `Co-authored-by` trailer → passes hook
- [ ] `enforce_worktree.sh` FR commit (line ~69) includes Copilot trailer
- [ ] `enforce_worktree.sh` feature commit (lines ~162–168) includes Copilot trailer
- [ ] `finalize_merge.sh` trailer (line 107) remains unchanged
- [ ] `pre-commit install --hook-type commit-msg` activates the new hook
- [ ] `req_coverage.py --strict` still passes (no requirement regression)
- [ ] Hook appears before `absolution` in `.pre-commit-config.yaml`
- [ ] Tests added for hook validation logic
- [ ] CHANGELOG.md updated

## Alternatives Considered

1. **Extend FR-127 scope**: FR-127 targets CI-level PR title enforcement via GitHub Actions. Adding trailer validation to it would mix concerns (CI vs local hooks) and delay both deliverables.

2. **Git `commit.template`**: A template pre-fills the trailer in the editor, but doesn't enforce it — users can delete it. Insufficient for mechanical compliance.

3. **`prepare-commit-msg` hook (auto-inject)**: Auto-append the trailer to every commit message. This avoids rejection UX but raises honesty concerns flagged in Audit XXIV Seed: "Is that honest — does the pipeline always use Copilot?" Rejected: enforcement (reject bad) is preferable to mutation (silently fix).

4. **CI-only enforcement**: A GitHub Actions workflow could validate trailers on push. This catches violations later in the cycle; pre-commit catches them at authoring time. The Scripture favors earliest-possible enforcement ("normalize at the boundary").

## Related

- **FR-127**: CI Conventional Commit enforcement (Approved, does not cover trailers)
- **FR-106**: `enforce_worktree.sh` parallel development pipeline
- **FR-125**: `finalize_merge.sh` post-merge finalization
- **Inquisitor Audits XXII–XXVI**: Six consecutive trailer violations (CALCIFIED-4 through CALCIFIED-6)
- **Knowledge Graph**: `audit_as_ritual` trap, `audit_gate` process pattern
- **`.pre-commit-config.yaml`**: Existing `commit-msg` hooks (conventional-pre-commit, feat-requires-fr, changelog-required)
