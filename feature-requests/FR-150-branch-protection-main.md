# Feature Request: GitHub branch protection for main

**Priority:** HIGH
**Type:** Enhancement
**Status:** ✅ Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add GitHub branch protection rules to `main` that require pull requests, squash-merge only, and passing status checks — closing the structural gap that lets direct pushes and non-squash merges bypass every enforcement gate.

## Value Statement

All contributors get a single infrastructure gate that enforces squash-merge, conventional commits, CHANGELOG entries, and co-authorship trailers — replacing five audit findings with one configuration change.

## Problem

Inquisitor audits XXXV and XXXVI found non-squash merge commits reaching `main`:
- `86a15c2`: invalid `merge:` commit type, missing Co-authored-by trailer.
- `2e34fa9`: non-squash merge commit violating both squash-merge convention and Conventional Commits format.

The root cause: **no branch protection exists on `main`**. All enforcement gates (FR-077 CHANGELOG hook, FR-127 CI commitlint, FR-132 Co-authored-by trailer, FR-125 post-merge finalization) operate on the PR path only. Direct pushes and non-squash merges bypass every one of them. The Inquisitor's heuristic names it: *"The PR path is the compliant path."*

This is an infrastructure gap, not a code gap. No amount of pre-commit hooks or CI workflows can prevent a `git push origin main` when GitHub allows it.

## Proposed Solution

Configure GitHub branch protection on `main` via repository settings (Settings → Branches → Branch protection rules):

### 1. Require pull request before merging
- No direct pushes to `main`.
- Required approvals: 0 (solo project; increase when team grows).

### 2. Restrict merge strategy to squash merge only
- Settings → General → Pull Requests → Allow squash merging only.
- Disable "Allow merge commits" and "Allow rebase merging".

### 3. Require status checks to pass before merging
- Mark these CI checks as required:
  - `commitlint` (FR-127: Conventional Commits + FR-038 feat-requires-fr)
  - Unit tests (existing CI workflow)
  - `changelog-check` (FR-149: add as required check when FR-149 is implemented)

### 4. Emergency bypass procedure
- Admin override available for legitimate operations (backup recovery, hotfix).
- Every admin override MUST be followed by a post-facto audit entry in `docs/diary/` documenting: what was pushed, why bypass was necessary, and corrective action taken.

### 5. Documentation
- Add branch protection rules to `CLAUDE.md` under a new "Branch Protection" section.
- Document the emergency bypass procedure in `reference/break-glass.md`.

## Acceptance Criteria

- [x] Direct push to `main` is rejected by GitHub for non-admin users
- [x] Only squash merge is available as merge strategy in PR UI
- [x] `commitlint` workflow is marked as a required status check
- [x] PR merge is blocked when `commitlint` check fails
- [x] Emergency bypass procedure is documented in `reference/break-glass.md`
- [x] `CLAUDE.md` updated with branch protection section
- [x] Verify: a PR with non-conventional title cannot be merged
- [x] Verify: a `feat` PR without `FR-XXX` reference cannot be merged

## Alternatives Considered

1. **Server-side Git hooks (pre-receive)**: GitHub does not support custom pre-receive hooks on non-Enterprise plans. Branch protection rules are the native equivalent.

2. **Additional CI-only enforcement**: Adding more CI workflows cannot prevent direct pushes. CI runs *after* code reaches the branch; branch protection prevents it *before*.

3. **Local-only enforcement (pre-commit)**: Already in place (FR-077, FR-127 local hooks). Bypassed trivially with `--no-verify` or by pushing from a machine without hooks installed. Local hooks are defense-in-depth, not primary enforcement.

## Related

- **FR-127**: CI Conventional Commit enforcement (Implemented) — becomes a required check
- **FR-132**: Copilot trailer enforcement (Approved) — protected by PR-only path
- **FR-077**: CHANGELOG commit enforcement (Implemented) — local hook, needs CI counterpart
- **FR-125**: Enforce pipeline finalize (Implemented) — post-merge script, assumes PR path
- **FR-149**: CI CHANGELOG gate (Approved) — becomes a required check when implemented
- **Audit XXXV**: `86a15c2` non-squash merge with invalid type
- **Audit XXXVI**: `2e34fa9` non-squash merge on main

## Implementation Notes

This FR is primarily a **configuration change**, not a code change:
1. GitHub Settings → Branches → Add rule for `main`
2. GitHub Settings → General → Pull Requests → Squash merge only
3. Minor documentation additions

No Python code changes required. Effort is documentation + verification.

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Reviewed:** 2026-03-08

**Assessment:**
- Scope is clear and minimal: one GitHub configuration change + documentation.
- Root cause is well-documented with specific audit citations (XXXV, XXXVI).
- Acceptance criteria are measurable and verifiable.
- Implementation is feasible — standard GitHub feature, no code changes.
- Aligns with existing enforcement landscape (FR-127, FR-132, FR-077, FR-149).
- Single responsibility: branch protection is one cohesive infrastructure concern.

**Editorial fixes applied:**
1. Resolved `FR-XXX` placeholder → `FR-038` (feat-requires-fr hook).
2. Resolved ambiguous approval requirement → 0 approvals (solo project).
3. Clarified `changelog-check` timing → deferred until FR-149 is implemented.
