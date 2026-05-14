# Break Glass: Emergency Bypass Procedure

> **When the fire alarm rings, you break the glass. Then you file the incident report.**

This document describes the emergency bypass procedure for GitHub branch protection on `main`. Branch protection exists to enforce squash-merge, conventional commits, and required status checks. Bypassing it is a last resort.

## When to Use

Emergency bypass is justified **only** for:

- **Backup recovery**: Restoring `main` after data loss or corruption.
- **Critical hotfix**: A production outage that cannot wait for CI to pass (e.g., broken dependency, security vulnerability).
- **Infrastructure repair**: Fixing CI itself when a broken workflow blocks all merges.

Emergency bypass is **never** justified for:

- Skipping a failing test you don't want to fix.
- Merging a feature faster.
- Avoiding a commitlint failure.

## Local Boundary Guard: `.gitignore` Edits (FR-372)

Staged changes to any `.gitignore` file are blocked by the local pre-commit
hook `gitignore-boundary-guard` by default. This boundary exists because
ignore rules define what is tracked vs. local-only and can silently widen
exposure if changed casually.

For intentional human edits, use the documented explicit bypass:

```bash
YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1 \
YAMLGRAPH_GITIGNORE_REASON="FR-372 adjust ignore boundary for <reason>" \
git commit
```

Bypass is accepted only when:

- `YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1`
- `YAMLGRAPH_GITIGNORE_REASON` is non-empty and includes trace token `FR-<num>` or `gh-<num>`

`--no-verify` is not the normal path for this guard and must not be used as
routine bypass.

## Procedure

### 1. Assess

Confirm that the standard PR path is genuinely blocked or too slow for the emergency. If CI is simply slow, wait.

### 2. Override

Repository admins can bypass branch protection via the GitHub UI:

1. Create a PR (even for emergency changes, prefer PR for traceability).
2. On the merge button, admin override allows merging despite failed checks.
3. If direct push is absolutely necessary: admin can temporarily disable the branch protection rule in Settings → Branches, push, then **immediately re-enable**.

### 3. Restore Protection

After the emergency push:

- **Verify branch protection is re-enabled** in Settings → Branches → `main`.
- Confirm all three enforcement layers are active:
  - ✅ Require pull request before merging
  - ✅ Require status checks (`commitlint`, `test`)
  - ✅ Squash merge only (Settings → General → Pull Requests)

### 4. Audit Trail

Every emergency bypass **must** be followed by a diary entry. Create a file in `docs/diary/` within 24 hours documenting:

```markdown
# Emergency Bypass: [DATE]

## What was pushed
[Describe the commit(s) pushed via override]

## Why bypass was necessary
[Explain why the standard PR + CI path was insufficient]

## Corrective action
[What was done to prevent recurrence — e.g., fix the broken CI, add a missing test]

## Protection restored
- [ ] Branch protection re-enabled
- [ ] Squash merge only confirmed
- [ ] Required checks confirmed
```

If the bypass was triggered by a CI infrastructure failure, also file a feature request in `feature-requests/` to prevent recurrence.

## Who Can Override

Only repository admins (`sheikkinen` and collaborators with admin role) can bypass branch protection. This is enforced by GitHub — non-admin contributors cannot override.

## Related

- **FR-150**: Branch protection configuration (this procedure's parent FR)
- **FR-127**: CI commitlint enforcement (required status check)
- **FR-149**: CI CHANGELOG gate (future required status check)
- `CLAUDE.md` → Branch Protection section
