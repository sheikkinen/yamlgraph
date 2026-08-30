# Problem brief: the integration toll on parallel worktree PRs

**Prior art:** filename-noun hits in `feature-requests/research-briefs/`
share only generic tokens ("gate", "route", "session"):
`session-accountability-record.md` concerns session receipts, and
`fr-891-web-research-fail-open.md` concerns web-search failure policy.
The genuine prior art is FR-889 (OS-enforced main lock that created the
worktree → PR flow; its §4d records the docs-PR deadlock), FR-919
(doc-only CI skip whose skipped jobs never report), FR-902/FR-927 (the
auto-lane arc, built then retired — provisioning was never the
bottleneck), and the committed record
`docs/plan-research-merge-queue.md` (platform-capability survey,
2026-08-30). A REJECTED-FR sweep for merge/integration tooling found no
prior proposal governing the merge boundary itself.

## Problem statement

FR-889 routes all change through worktree → PR → squash merge onto a
protected `main`. Branch protection requires three status contexts
(`commitlint`, `test (3.11)`, `test (3.13)`) and `Require up to date
(strict)`. With N pull requests open in parallel — the normal mode:
agents implement concurrently in separate worktrees — every squash
merge invalidates the base of the other N−1 PRs. Each of those must
rebase and re-run the full CI matrix before it can merge, so landing K
parallel PRs costs O(K²) rebase-plus-CI cycles. Over 2026-08-27..30 the
repo landed ~78 commits under this regime; the operator names the merge
acrobatics — time, LLM tokens, money — as the single largest process
handicap.

Two aggravating defects make the toll worse than the quadratic
baseline. First, docs-only PRs cannot merge at all without human
override: the FR-919 path filter skips the test matrix on docs-only
diffs, skipped required contexts never report, and the PR deadlocks
awaiting `test (3.11)`/`test (3.13)` forever (FR-889 §4d, witnessed on
PR #501). Second, because of that deadlock the operational culture has
normalized `gh pr merge --squash --admin` — an unconditional bypass of
every required check (`enforce_admins` is disabled). The audit trail of
recent sessions shows admin bypass as the default merge verb, which
means the required contexts currently gate almost nothing in practice:
the protection exists, the toll is paid, and the safety it was buying
is silently forfeited by the bypass.

The problem: the integration boundary serializes parallel agent work at
quadratic cost while simultaneously failing to enforce its own checks,
and no committed record governs how PRs should be ordered, validated
against each other, and landed without per-PR manual rebasing or
routine admin bypass.

## Classification

enforcement/latency-critical

## Constraints

- Squash merge remains the only merge method; the PR title remains the
  commit message on `main` (Conventional Commits, enforced by
  `commitlint`).
- The required status contexts (`commitlint`, `test (3.11)`,
  `test (3.13)`) must remain required and must actually report on every
  PR class, including docs-only diffs; a cure that removes protection
  rather than making it enforceable is out of bounds.
- The FR-919 doc-only CI cost saving must be preserved at PR-event
  scope: docs-only PR validation must not start paying for the full
  test matrix. (Amended per FR-934 judgement R-2, option 1: the final
  integration candidate before `main` may run the full matrix — that
  boundary is where assurance is bought; the original end-to-end form
  of this constraint is preserved as recorded disagreement in FR-934.)
- `main` stays OS-locked (FR-889); the worktree → PR flow is the fixed
  substrate, not a variable.
- Single-operator repo on the GitHub Free plan, public visibility;
  solutions must not require paid plan features or org-level settings.
- Agent-driven: whatever the landing procedure is, an agent must be
  able to execute it non-interactively with `gh`; a procedure that
  requires the web UI per-merge recreates the human bottleneck.
- Emergency override must survive somewhere (break-glass,
  `reference/break-glass.md`) but must be auditable and exceptional,
  not the default verb.

## Witnessed incidents

- PR #501 (2026-08-29): docs-only FR-889 scope PR deadlocked on
  never-reporting skipped test contexts; admin merge required; recorded
  as FR-889 §4d with AC-16.
- 2026-08-30 session terminals: `gh pr merge --squash --admin` used as
  the routine merge verb across at least four distinct sessions in the
  visible terminal history, including for PRs #519 and #520.
- 2026-08-27..30: 78 commits landed on `main`; the 08-30 worktree
  census found 20 worktrees, of which 13 were stale residue of merged
  lanes — each had paid at least one rebase cycle against a moving
  `main` before landing.
- FR-902 → FR-927 (2026-08-28..30): three FRs spent automating worktree
  provisioning while the integration boundary — where the actual cost
  sits — remained ungoverned; the machinery was retired within 72 hours
  with zero consumers.
