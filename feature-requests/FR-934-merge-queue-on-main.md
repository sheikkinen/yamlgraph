# Feature Request: Enable the GitHub merge queue on main — retire the rebase toll

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the next two PRs opened from parallel
worktree lanes — instead of the second PR rebasing after the first
lands, both are enqueued with `gh pr merge` and the queue validates and
lands them in order. The event occurs within hours of merge: the
08-27..30 window landed ~78 commits from parallel lanes under the
rebase regime.
**Research:** [docs/plan-research-merge-queue.md](../docs/plan-research-merge-queue.md)
(committed 2026-08-30, PR #520 — platform-capability survey against
docs.github.com plus live repo-state evidence; equivalent committed
record per FR-890 R-6). Sole-route provenance note: `scripts/research.sh
feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`
was run twice on 2026-08-30 and failed both times at the artifact
contract — the librarian_structure node exceeded the 400-char rationale
cap on all retries (graph rc=1, exit 65). The failure is recorded here
rather than routed around; the cap defect sits in FR-932's in-flight
territory (`examples/demos/research-route/nodes/research_tools.py`) and
is not patched by this FR. The brief is committed alongside this FR for
re-run when the route heals.
**Prior art:** FR-889 built the worktree → PR → squash substrate and its
§4d recorded the docs-PR deadlock (cured: the always-reporting no-op
step is live in `workflow.yml` `test` job; witnessed green on docs-only
PR #520, all three required contexts SUCCESS). FR-919 owns the doc-only
CI skip this FR must preserve. FR-902/FR-927 are the cautionary
precedent: they automated worktree provisioning — the cheap step — and
were retired in 72h with zero consumers; this FR targets the integration
boundary where the measured cost actually sits. No prior or REJECTED FR
proposes governing the merge boundary; `git log --grep` and a
feature-requests filename sweep found no merge-queue proposal.

## Summary

Enable GitHub's native merge queue on `main` (squash method), add the
`merge_group` trigger to the two workflows that carry required status
contexts, and disable `Require up to date (strict)` — the queue subsumes
it. Landing K parallel PRs stops costing O(K²) rebase+CI cycles and
zero manual rebases.

## Value Statement

Agents working in parallel worktrees stop paying a rebase and a full CI
re-run per previously-landed PR; the operator stops paying the
corresponding wall-clock time, LLM tokens, and money — named the single
largest process handicap.

## Problem

With `Require up to date (strict)` and N open PRs, every squash merge
invalidates the base of the other N−1 PRs; each must rebase and re-run
the matrix before it can land. The 08-27..30 window (78 commits, 20
worktrees, 13 stale merged lanes) paid this toll continuously. The
platform ships the cure: a merge queue provides "the same benefits as
the Require branches to be up to date before merging branch protection,
but does not require a pull request author to update their pull request
branch and wait for status checks to finish before trying to merge"
(docs.github.com, "Managing a merge queue"). The repo is public, so the
feature is on the free plan.

## Proposed Solution

Three surfaces, smallest sufficient change on each:

### 1. `merge_group` triggers (2 workflow files)

`workflow.yml`:

```yaml
"on":
  pull_request:
    types: [opened, synchronize, reopened]
  merge_group:
  push:
    tags:
      - 'v*.*.*'
```

The FR-919 `changes` gate already short-circuits non-PR events to
`code == 'true'` (`github.event_name != 'pull_request' || …`), so merge
groups run the full matrix with zero job edits — correct, since a queue
group is the last validation before main.

`commitlint.yml`: add `merge_group:` to `on:` and an always-success
no-op job step for merge_group events. The existing `commitlint` job is
`if: github.event_name == 'pull_request'` (action-semantic-pull-request
cannot run outside PR context); on a merge_group event the required
`commitlint` context must still report or the queue times the PR out —
the same never-reporting deadlock class as FR-889 §4d. Title validity
was already proven at PR time; a no-op reporter for the group event is
sound.

### 2. Branch protection (settings change, recorded not scripted)

- Enable **Require merge queue** on `main`: merge method **squash**,
  min group size 1, small wait time, **only merge non-failing pull
  requests** enabled, status-check timeout ≥ the slow path of the test
  matrix.
- Disable **Require branches to be up to date before merging** — the
  queue subsumes it; keeping both reintroduces the pre-queue rebase
  requirement at PR level for no additional safety.
- Applied via `gh api` and verified by reading the protection back;
  the resulting JSON is pasted into this FR's implementation notes.

### 3. Ritual update (documentation)

`CLAUDE.md` branch-protection table and merge ritual: the merge verb
becomes plain `gh pr merge --squash` (auto-enqueues on a queue-required
branch per GitHub CLI docs). `--admin` is no longer the routine verb —
its prohibition is FR-935's scope, not this FR's.

## Acceptance Criteria

- [ ] AC-01: `workflow.yml` and `commitlint.yml` both list `merge_group`
      in their `on:` block (unit-testable by YAML parse, pattern of
      `tests/unit/test_fr919_*` CI-shape witnesses).
- [ ] AC-02: on a merge_group event, all three required contexts
      (`commitlint`, `test (3.11)`, `test (3.13)`) reach a reported
      conclusion — witnessed by the first queued PR's merge_group check
      run, cited in this FR by run URL.
- [ ] AC-03: branch protection on `main` shows merge queue required,
      squash method, and `strict: false` — verified by
      `gh api repos/:owner/:repo/branches/main/protection` output
      pasted into implementation notes.
- [ ] AC-04: two PRs from parallel worktree lanes land through the
      queue with zero manual rebase commands and zero `--admin` flags —
      witnessed by the PRs' timelines and the session audit log.
- [ ] AC-05: a docs-only PR enters and clears the queue without human
      override (the FR-919 skip keeps its cost saving: the `changes`
      filter still short-circuits only on `pull_request` events;
      merge_group runs full matrix by design and this is recorded as a
      deliberate cost).
- [ ] AC-06: changelog fragment (`type: feat`) in
      `changelog/unreleased/`.
- [ ] AC-07: `CLAUDE.md` branch-protection table updated to the
      post-queue truth.

## Alternatives Considered

| alternative | disposition |
|---|---|
| Auto-rebase bot / local watcher re-basing open PRs after each merge | REJECTED — rebuilds what the platform ships; still costs one full CI re-run per PR per landing; adds owned infrastructure (growth_as_default) |
| Serialize agents (one PR open at a time) | REJECTED — surrenders the concurrency FR-889 bought; the operator names parallel implementation as working today |
| Keep strict up-to-date, keep `--admin` bypass as the release valve | REJECTED — the toll stays for compliant merges and the bypass forfeits every required check; measured today: bypass is already the default verb |
| Batch merges manually (collect PRs, rebase once, merge in sequence) | REJECTED — same O(K²) CI in the worst case, adds human scheduling; the queue does exactly this mechanically with FIFO ejection |
| Merge queue (this FR) | PURSUED — free on public repos, subsumes strict up-to-date, squash-compatible, `gh pr merge` auto-enqueues non-interactively |

## Related

- [docs/plan-research-merge-queue.md](../docs/plan-research-merge-queue.md) — research record
- FR-889 (worktree → PR substrate; §4d deadlock cure, live and witnessed on PR #520)
- FR-919 (doc-only skip; its `changes` gate composes with merge_group unchanged)
- FR-935 (companion: deny `--admin` outside break-glass — the queue is only real if the bypass is exceptional)
- FR-902/FR-927 (cautionary precedent: automation aimed at the wrong end of the pipeline)
- docs/diary/diary-2026-08-30-the-parallel-writers-and-the-serial-door.md (the trap that fired this FR)
