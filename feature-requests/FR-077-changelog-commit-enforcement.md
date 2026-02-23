# Feature Request: Enforce CHANGELOG.md in feat/fix Commits

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-23

## Summary

Add a `commit-msg` pre-commit hook that rejects `feat:` and `fix:` commits unless `CHANGELOG.md` is staged.

## Problem

Commandment 10 declares: *"let the CHANGELOG.md bear witness to the evolution of the Word."* Today this is cultural, not enforced. Contributors can ship features and fixes without documenting them, leading to:

- Changelog drift — releases with undocumented changes
- "I'll update it later" syndrome — deferred entries that never arrive
- Incomplete release notes — users cannot discover what changed

FR-038 established the pattern: if a commit type carries design intent, enforce its companion artifact. `feat:` requires `FR-XXX`; by the same logic, `feat:` and `fix:` should require `CHANGELOG.md`.

## Proposed Solution

A `commit-msg` hook that checks:
1. Is the commit message prefixed with `feat:` or `fix:` (with optional scope)?
2. Is `CHANGELOG.md` in the staged files (`git diff --cached --name-only`)?

If (1) is true and (2) is false, block the commit.

### Hook implementation

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: changelog-required
      name: feat/fix commits require CHANGELOG.md
      entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE \"^(feat|fix)(\\(.*\\))?:\" && ! git diff --cached --name-only | grep -qE \"^CHANGELOG\\.md$\"; then echo \"ERROR: feat:/fix: commits must include CHANGELOG.md changes\"; echo \"Add your entry under the current [Unreleased] or version heading.\"; exit 1; fi'"
      language: system
      stages: [commit-msg]
      always_run: true
```

### Enforcement matrix

| Prefix | Requires CHANGELOG.md | Rationale |
|--------|----------------------|-----------|
| `feat:` | ✅ Yes | New capability — users need to know |
| `fix:` | ✅ Yes | Bug fix — users need to know |
| `chore:` | ❌ No | Internal maintenance |
| `docs:` | ❌ No | Documentation is self-documenting |
| `refactor:` | ❌ No | Internal restructuring |
| `test:` | ❌ No | Test-only changes |
| `ci:` | ❌ No | Pipeline changes |
| `perf:` | ❌ No | Could argue either way; keep friction low |
| `style:` | ❌ No | Formatting |
| `build:` | ❌ No | Build system |

### Valid examples

```
feat: FR-077 add changelog enforcement    # CHANGELOG.md staged ✓
fix: handle null token in streaming       # CHANGELOG.md staged ✓
chore: update dependencies                # No CHANGELOG.md required
refactor: extract edge compiler           # No CHANGELOG.md required
```

### Invalid (blocked)

```
feat: FR-077 add changelog enforcement    # CHANGELOG.md NOT staged ✗
fix: handle null token in streaming       # CHANGELOG.md NOT staged ✗
```

## Acceptance Criteria

- [x] `commit-msg` hook added to `.pre-commit-config.yaml`
- [x] `feat:` commits without staged `CHANGELOG.md` are blocked
- [x] `fix:` commits without staged `CHANGELOG.md` are blocked
- [x] `feat(scope):` and `fix(scope):` variants handled correctly
- [x] Other prefixes (`chore:`, `docs:`, `refactor:`, etc.) not blocked
- [x] Hook tested with valid and invalid scenarios
- [x] Hook ordering: runs after `conventional-pre-commit` and `feat-requires-fr`

## Constraints

- **No `--no-verify` escape** — already forbidden by project policy; CI enforces
- **Merge commits exempt** — merge messages start with `Merge ...`, not `feat:`/`fix:`, so the prefix regex doesn't match
- **Amend-friendly** — `git commit --amend` re-runs hooks; if CHANGELOG.md is already committed, it appears in the cached diff

## Alternatives Considered

1. **No enforcement** — Current state. Relies on discipline. Changelog drifts.
2. **Enforce all commit types** — Too noisy. `chore: bump deps` doesn't warrant a changelog entry.
3. **Automated changelog generation from commits** — Tools like `git-cliff` or `auto-changelog` exist, but they produce mechanical output. Hand-written entries are more useful to users. Not mutually exclusive — could layer generation on top later.
4. **Enforce only `feat:`** — Misses bug fixes, which users equally care about.
5. **CI-only check (not pre-commit)** — Delayed feedback. Pre-commit catches it before push, preserving the fast-feedback loop established by FR-038.

## Related

- FR-038 `feat-requires-fr` — Prior art for selective commit enforcement
- `.pre-commit-config.yaml` — Hook configuration
- `CHANGELOG.md` — The artifact being protected
- Commandment 10 — *"let the CHANGELOG.md bear witness"*
