## 2026-03-08: Inquisitor Audit LI — Housekeeping Bypass Pattern

**Context:** Audited the 5 most recent commits on `main` (e9171dd → 6f5e737). All five are housekeeping: `docs(FR)`, `chore`, `docs(diary)`. No `feat` or `fix` commits in scope. Checked Conventional Commits, CHANGELOG, ARCHITECTURE.md requirements, `@pytest.mark.req` tags, diary reflections, and noqa confessions.

**Findings:**

- ✗ VIOLATION: **Four direct pushes to `main` without PR** — Commits 6f5e737, 47de643, 9edfdde, 6836029 all pushed directly by "Test <test@test.com>", bypassing branch protection (FR-150). Only e9171dd came via PR #33. Third consecutive audit flagging this pattern (XLVII, XLVIII, LI). The branch protection rule requiring PRs is either not enforced for this author or admin-overridden without documented break-glass procedure.

- ✗ VIOLATION: **FR-157 diary reflection still missing** — No `reflection-fr-157.md` exists. Third audit flagging this (XLVI, XLVIII, LI). The diary-gate CI job (FR-158) prevents future occurrences, but the historical debt from FR-157's merge remains unaddressed. `audit_as_ritual` trap fully applies.

- ✓ COMPLIANT: **Conventional Commits on all 5 commits** — All follow `type(scope): description`. No `feat` or `fix` in scope, so CHANGELOG/ARCHITECTURE/test requirements do not apply.

- ✓ COMPLIANT: **noqa confessions clean** — `noqa_coverage.py` reports 0 undocumented suppressions (53 noqa, 57 confessions).

- ✓ COMPLIANT: **No new capabilities without traceability** — The `docs(FR)` commit (FR-162) adds a feature request document only, no code or tests expected at this stage.

**Heuristic:** When a violation persists across three consecutive audits, the audit itself has become the `audit_as_ritual` trap it warns against. The structural remedy already exists in the codebase (CI gates for PRs, diary gates for reflections) but is circumvented by admin pushes. The gap is not in detection or in gating — it is in the identity that bypasses both. The cheapest fix is not another CI job but restricting admin push privileges or requiring post-push remediation tickets.

**Seed:** Should the project adopt a post-push webhook that auto-creates a remediation issue whenever a commit lands on `main` without a PR reference, converting bypass incidents from audit findings into tracked work items?
