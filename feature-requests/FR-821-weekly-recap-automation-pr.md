# Feature Request: Weekly Recap Published to main via Automation PR + Auto-Merge

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-18
**First consumer / first event:** The operator, Monday morning, opening
`docs/recaps/<ISO-week>.md` on `main` to see what shipped last week —
without running anything. Second consumer: any agent session using the
recap as `changelog_first_diagnostic` input.

**Prior art:** FR-700/FR-702/FR-703/FR-704 (the `recap` graph — reused
verbatim, not modified); FR-819 (GitHub-native scheduled publication PoC —
proved cron + commit-back on an *unprotected* repo; this FR is the
protected-repo adaptation); FR-046 (rejected "GitHub Action only" digest
option — rejected because CI was the wrong runtime for a *dev tool*; here
scheduled publication *is* the product, same disposition as FR-819 R-1);
`docs/plan-github-chaplain-arbitrary-repo.md` (downstream consumer of the
automation-PR pattern, not a deliverable).

## Summary

A weekly GitHub Actions workflow runs the existing
`examples/demos/recap` graph against this repository, renders the result
to `docs/recaps/<YYYY-Www>.md`, and lands it on the protected `main`
branch through the documented automation route: a `docs(recap):` PR with
auto-merge enabled, gated by the three required checks.

## Value Statement

The repo narrates its own week on `main` with zero human effort, and the
scheduled run doubles as a weekly CI/dependency health check.

## Problem

The recap graph exists and works (FR-700 arc) but has no consumer moment
— it runs only when someone remembers to run it. Meanwhile `main` is
protected: the Actions `GITHUB_TOKEN` cannot push to it directly, so the
digest-PoC pattern (FR-819: commit + push) does not transfer. The
documented automation route (CLAUDE.md Branch Protection: "PR flow is for
automation") has never actually been exercised by automation.

## Ideal Result

Every Monday a recap of the past week appears on `main` as
`docs/recaps/2026-W34.md`, merged by a green automation PR nobody
touched. A quiet week produces nothing — no PR, no noise. The whole
mechanism is one workflow file, one small render script, and two repo
secrets.

## Proposed Solution

**No graph work.** `examples/demos/recap/graph.yaml` is reused unmodified
(any future modification re-enters the graph-authoring doctrine).

### 1. Render script — `scripts/weekly_recap.py`

- Runs the recap graph (`repo_path=.`, `since="1 week ago"`) via the
  Python API.
- Renders `workstreams`, `orphans`, `hotspots` state into
  `docs/recaps/<ISO-week>.md` (ISO week from `date +%G-W%V` semantics).
- **No-op guard:** if the window contains zero commits, exit 0 with a
  distinct message and write nothing (empty-window LLM output is not
  trusted — FR-819 lesson: guard on deterministic input, not on model
  output).

### 2. Workflow — `.github/workflows/weekly-recap.yml`

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"   # Monday 06:00 UTC
  workflow_dispatch:
concurrency:
  group: weekly-recap
  cancel-in-progress: false
```

- Checkout with `token: ${{ secrets.RECAP_PAT }}` and `fetch-depth: 0`
  (recap needs history).
- `pip install -e .` + graph deps; run `scripts/weekly_recap.py`.
- If a recap file was written: branch `recap/<ISO-week>`, commit, push,
  `gh pr create --title "docs(recap): weekly recap <ISO-week>"`,
  then `gh pr merge --auto --squash`.
- If no-op: log and exit green, no branch, no PR.

### 3. The PAT is load-bearing, not optional

PRs created with the default `GITHUB_TOKEN` **do not trigger
`pull_request` workflows** (GitHub anti-recursion rule) — the required
checks (`commitlint`, `test (3.11)`, `test (3.12)`) would never run and
auto-merge would never fire. `RECAP_PAT` is a fine-grained PAT scoped to
this single repository with `contents: write` + `pull-requests: write`,
set by the human (C-7 discipline from FR-819).

### 4. Gate compatibility (why `docs(recap):` sails through)

| Gate | Effect on this PR |
|------|-------------------|
| `commitlint` | `docs(recap): …` is valid Conventional Commits |
| `test (3.11/3.12)` | Run and gate; doubles as weekly health check |
| changelog/diary/demo gates | Only block `feat`/`fix` — inert for `docs` |
| Strict up-to-date | See Known Limitation below |

### Secrets required (human-set)

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | The recap graph's single LLM node |
| `RECAP_PAT` | Fine-grained, this repo only: contents + pull-requests write |

### Known limitation

Strict up-to-date: if `main` advances between PR creation and checks
going green, auto-merge stalls until the branch updates. At Monday 06:00
UTC on a single-dev repo this is rare; mitigation is a manual
`workflow_dispatch` re-run or updating the branch — no machinery is added
for it.

## Acceptance Criteria

- [ ] AC-01: `scripts/weekly_recap.py` runs the recap graph and writes
      `docs/recaps/<ISO-week>.md`; zero-commit window → exit 0, no file.
- [ ] AC-02: `.github/workflows/weekly-recap.yml` exists with weekly cron,
      `workflow_dispatch`, and `concurrency: cancel-in-progress: false`.
- [ ] AC-03: A `workflow_dispatch` run creates a `docs(recap):` PR whose
      required checks **actually trigger** (proof the PAT route works).
- [ ] AC-04: That PR auto-merges with no human click; the recap file is on
      `main` (run URL + merge commit cited in Implementation Notes).
- [ ] AC-05: No-op path evidenced: a run with an empty window (or dry-run
      flag) produces no branch and no PR.
- [ ] AC-06: Secrets documented; PAT scope recorded in the FR — never the
      value.
- [ ] AC-07: First scheduled (cron) run observed green.
- [ ] AC-08: Pointer added to `examples/demos/recap/README.md` (the graph
      now has a scheduled consumer).
- [ ] AC-09: Changelog fragment + diary entry (this FR lands as `feat` in
      its own enforcement PR or direct push; the *weekly output* PRs are
      `docs`).

## Alternatives Considered

1. **Direct push to `main` with admin PAT** — rejected: stores a
   protection-bypassing credential in Actions to skip a PR; worst
   privilege-to-benefit ratio.
2. **Unprotected `recaps` branch** — rejected: artifact off `main`,
   weaker visibility; the whole point is the recap on the default branch.
3. **Labeled GitHub Issue as output** — demoted to non-goal: fine as a
   notification layer later, but an issue is not a committed artifact and
   dies unmergeable.
4. **Separate repo (digest pattern)** — rejected earlier in the arc: the
   recap reads this repo's history/FRs/diaries; a separate repo just
   re-clones it.
5. **Copilot-PAT (`COPILOT_GITHUB_TOKEN`) as LLM route** — deferred: the
   recap graph uses a standard LLM node; Anthropic key is already the
   proven CI pattern (FR-819). Copilot-PAT gets its own proof elsewhere.

## Non-Goals

- Modifying the recap graph or prompts (C: any change re-enters
  graph-authoring doctrine and this FR's scope freeze).
- Notification layers (issues, email, RSS).
- Generalizing to other repos or the chaplain plan.

## Related

- `examples/demos/recap/` — the reused graph (FR-700/702/703/704)
- FR-819 — GitHub-native digest PoC (scheduled-publication precedent)
- CLAUDE.md § Branch Protection — the automation-PR route this exercises
- `docs/plan-github-chaplain-arbitrary-repo.md` — downstream consumer

## Judgement (pending)

**Verdict:** —
