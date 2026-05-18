# Fix: Non-canonical author identity in daemon commits

## Violation

Audit 231 (2026-04-21, ⚠ DRIFT) and Audit 234 (2026-05-18, ✗ VIOLATION) both found commits authored by `Test <test@test.com>` reaching `main`. In audit 231 this was commit `a7a609c8`; in audit 234 it was commit `aa3c5e26`. Different commits, same pattern — the Chaplain watcher daemon is committing with a placeholder git identity rather than the project owner's canonical identity.

The Scripture trap `automation_inherits_doctrine` extends to authorship: "Automation that creates commits must inherit the operator's git identity, not a placeholder." `git blame` and forensic audit of daemon-authored commits are unreliable when the author is `Test <test@test.com>`.

No current CI gate enforces author identity canonicity. The `copilot-trailer-gate` only inspects trailer content, not commit author fields.

## Suggested Fix

Micro-fix (two parts):

### Part 1 — Watcher identity configuration

In `.chaplain/scripts/` (or `watch.sh`), ensure `GIT_AUTHOR_NAME` and `GIT_AUTHOR_EMAIL` (and `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL`) are sourced from the local git config before any `git commit` call:

```bash
# At the top of the commit block in watch.sh:
GIT_AUTHOR_NAME=$(git config user.name)
GIT_AUTHOR_EMAIL=$(git config user.email)
GIT_COMMITTER_NAME=$GIT_AUTHOR_NAME
GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
```

If `user.name` is not configured, abort with an error message rather than falling back to a generic identity.

### Part 2 — CI author identity gate (structural gap)

Add a CI job `author-identity-gate` to `.github/workflows/commitlint.yml` that rejects PRs containing commits where the author email matches a blocklist (e.g., `test@test.com`, `noreply@github.com` when not a bot account). This widens the existing `copilot-trailer-gate` into the broader "identity policy class" that the audit 234 heuristic describes.

**Acceptance criteria:**
1. Watcher commits on dev machine show the project owner's git identity.
2. A PR containing a commit authored by `Test <test@test.com>` fails the new CI gate.
3. No regression to existing `copilot-trailer-gate` behaviour.
