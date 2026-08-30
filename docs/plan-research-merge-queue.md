# Research: GitHub Merge Queue for yamlgraph main

**Date:** 2026-08-30
**Trigger:** Diary 2026-08-30 "the parallel writers and the serial door" — with
N parallel worktree PRs and `Require up to date (strict)`, every merge
invalidates the other N−1 PRs: O(N) rebases + CI re-runs per landing. Operator
names merge acrobatics the #1 handicap (time, tokens, money).
**Question fired:** `does_the_platform_already_do_this` — yes. The answer is
the merge queue.

## Findings (docs.github.com, verified 2026-08-30)

### Availability — YES, free

- `sheikkinen/yamlgraph` is **PUBLIC** → merge queue is available on the free
  plan (private repos would need Enterprise Cloud).
- Configured as the **"Require merge queue"** branch protection setting on
  `main` (classic protection is fine; no rulesets required — repo currently
  has classic protection only, rulesets endpoint returns `[]`).
- No wildcard (`*`) branch patterns allowed with a queue — ours is literal
  `main`, fine.

### What it does — replaces strict-up-to-date mechanically

> "The merge queue provides the same benefits as the **Require branches to be
> up to date before merging** branch protection, but does not require a pull
> request author to update their pull request branch and wait for status
> checks to finish before trying to merge."

Mechanics: `gh pr merge` on a queue-required branch auto-enqueues. The queue
builds temporary `gh-readonly-queue/main/pr-N` branches stacking each PR on
main + everything ahead of it, dispatches a `merge_group` webhook, waits for
required checks on the *group*, merges FIFO. A failing PR is ejected and the
groups behind it are rebuilt without it. **Squash** is a supported queue merge
method — PR title stays the commit message. Rebase toll: zero manual rebases;
CI runs once per group position instead of once per PR per landing ahead of it.

### Retrofit surface in this repo (the actual work)

1. **`workflow.yml`** (required `test (3.11)` / `test (3.13)`): add
   `merge_group:` to `on:`. The FR-919 `changes` gate already short-circuits
   non-PR events to `code == 'true'`
   (`github.event_name != 'pull_request' || …`), so merge groups run the full
   suite automatically — correct and conservative. No job edits needed.
2. **`commitlint.yml`** (required `commitlint`): add `merge_group:` trigger
   **plus a no-op success job for merge_group events**. The current job is
   `if: github.event_name == 'pull_request'` (action-semantic-pull-request
   cannot run outside PR context) — on a merge_group event it would skip, the
   required context never reports, and the queue times the PR out. Title
   validity was already proven at PR time; a merge_group no-op reporter is
   sound, not theatre.
3. **Skipped-jobs deadlock is a prerequisite, not solved by the queue.**
   Entry to the queue still requires all required checks green *on the PR*.
   Docs-only PRs deadlock today (FR-889 §4d, witnessed PR #501): the path
   filter skips the test matrix and skipped jobs never report. The §4d default
   cure — an always-reporting no-op success job when `code != 'true'` — must
   land first, or docs PRs can never enter the queue and the `--admin` habit
   survives.
4. **The `--admin` habit is the real enemy.** Every merge in the current flow
   is `gh pr merge --squash --admin` (bypass), largely *because* of the §4d
   deadlock. A queue that everyone bypasses serializes nothing. Once checks
   always report: agents use plain `gh pr merge` (auto-enqueues), and the
   pre-command guard should deny `--admin` outside break-glass
   (`reference/break-glass.md` documents the exception path).
5. **Queue tuning for this repo's shape** (single operator, bursts of parallel
   agent PRs): merge method **squash**; min group 1; small wait time; "only
   merge non-failing pull requests" **enabled** (our test flakes are rare and
   a false-negative hold is cheaper than a broken main); status-check timeout
   ≥ the slow path of the test matrix.

### What the queue does NOT fix

- Semantic conflicts between parallel FRs (two PRs touching the same doctrine
  file still conflict — the queue ejects, a human/agent still resolves).
- CI minutes: group builds still run the full matrix; savings come from
  eliminating *repeated* PR-branch re-runs after each rebase, not from
  skipping work.
- The diary/FR-doc write contention on `feature-requests/` — that is a
  content-collision problem, not an integration-order problem.

## Proposed next steps (ordered; each is one FR)

1. **FR-A — always-reporting required contexts** (FR-889 §4d cure, blocking
   prerequisite): no-op success reporter for `test (3.11)`/`test (3.13)` when
   the FR-919 path filter says `code != 'true'`, and for `commitlint` on
   non-PR events it currently skips. Acceptance: a docs-only PR reaches green
   required checks with zero admin intervention.
2. **FR-B — enable the merge queue**: add `merge_group:` triggers to
   `workflow.yml` + `commitlint.yml`; enable "Require merge queue" on `main`
   (squash, min group 1, non-failing-only); **disable strict up-to-date**
   (the queue subsumes it); update `CLAUDE.md` branch-protection table and the
   agent merge ritual from `--squash --admin` to plain `gh pr merge`.
   Acceptance: two PRs opened from parallel worktrees land via the queue with
   zero manual rebases and zero `--admin` flags in the audit log.
3. **FR-C — guard the bypass**: pre-command guard denies `gh pr merge
   --admin` outside the documented break-glass path. Without this, FR-B decays
   back into the bypass culture within a week.
4. **Measure**: before/after — count of rebase events and PR-branch CI re-runs
   per landed PR over a comparable 3-day window (the 08-27..30 window is the
   baseline: 78 commits, constant rebasing).

## Sources

- docs.github.com: "Managing a merge queue" (availability, merge_group event,
  temp branch mechanics, queue settings, wildcard restriction)
- docs.github.com: "Merging a pull request with a merge queue" (`gh pr merge`
  auto-enqueue, admin bypass option, ejection reasons)
- Live repo state: `gh api repos/sheikkinen/yamlgraph/branches/main/protection`
  (contexts: commitlint, test (3.11), test (3.13); strict=true;
  enforce_admins=false), workflow trigger blocks, FR-919 `changes` gate.
