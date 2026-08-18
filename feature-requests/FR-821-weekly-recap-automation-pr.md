# Feature Request: Weekly Recap Published to main via Automation PR + Auto-Merge

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved with revisions (judged 2026-08-18; R-1–R-5 folded)
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

- CLI contract (R-3): `--repo-path`, `--since`, `--output-dir`, `--dry-run`.
- Runs the recap graph (`repo_path`, `since="1 week ago"`) via the
  Python API.
- Renders `workstreams`, `orphans`, `hotspots` state into
  `docs/recaps/<ISO-week>.md` (ISO week `%G-W%V`) with a frozen section
  contract: `# Weekly Recap <ISO-week>`, `## Workstreams`, `## Orphans`,
  `## Hotspots` — tested against fixtured graph state, asserting
  non-empty sections, not mere file presence (R-3).
- **Substantive-window no-op guard (R-2):** before invoking the LLM,
  compute the candidate commit window and exclude prior recap automation
  commits (subject `docs(recap): weekly recap <ISO-week>`, changed paths
  only under `docs/recaps/`). Empty substantive set → exit 0, distinct
  message, no file, no branch, no PR. Literal zero-commit is
  insufficient: last week's recap merge is itself a commit in the next
  window. Guard on deterministic input, never on model output (FR-819
  lesson).

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
  (recap needs history); the persisted credential authenticates git push.
- Every `gh pr create` / `gh pr merge --auto --squash` step runs with
  `GH_TOKEN: ${{ secrets.RECAP_PAT }}` (R-1) — the PAT binds *all*
  GitHub operations, not just checkout.
- **Repo prerequisite (R-1, human-set):** auto-merge must be enabled in
  repository settings; if not, enforcement stops before relying on
  `gh pr merge --auto`.
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

## Acceptance Criteria (revised by judgement)

- [ ] AC-01: `scripts/weekly_recap.py --repo-path . --since "1 week ago"
      --output-dir docs/recaps` invokes the existing recap graph
      unmodified and writes `docs/recaps/<ISO-week>.md` only when the
      substantive commit window is non-empty.
- [ ] AC-02: The generated markdown contains a non-empty
      `# Weekly Recap <ISO-week>` heading and `## Workstreams`,
      `## Orphans`, `## Hotspots` sections derived from graph state.
- [ ] AC-03: A window with zero substantive commits exits 0, logs a
      distinct no-op message, writes no file; workflow creates no branch
      and no PR.
- [ ] AC-04: A recap-only prior automation commit does not make a quiet
      week non-quiet; covered by an LLM-free test or fixture.
- [ ] AC-05: `.github/workflows/weekly-recap.yml` has Monday 06:00 UTC
      cron, `workflow_dispatch`, `concurrency: group: weekly-recap`,
      `cancel-in-progress: false`.
- [ ] AC-06: The workflow uses `RECAP_PAT` for checkout, push,
      `gh pr create`, and `gh pr merge --auto --squash`;
      `ANTHROPIC_API_KEY` available only to the graph run; secret values
      never logged or committed.
- [ ] AC-07: A `workflow_dispatch` run creates a
      `docs(recap): weekly recap <ISO-week>` PR whose required checks
      `commitlint`, `test (3.11)`, `test (3.12)` actually trigger.
- [ ] AC-08: That PR auto-merges by squash with no human click after
      checks green; recap file on `main`; run URL + merge commit cited in
      Implementation Notes.
- [ ] AC-09: First real scheduled cron run observed green and recorded;
      until then FR status carries "cron observation pending" — a
      dispatched run is not cron evidence (R-4).
- [ ] AC-10: Secrets documented by name and purpose; PAT scope recorded
      (`contents: write`, `pull-requests: write`) plus human-confirmed
      auto-merge prerequisite; never secret values.
- [ ] AC-11: `examples/demos/recap/README.md` points to the scheduled
      consumer; `examples/demos/recap/demo-output.log` refreshed if the
      enforcement PR is `feat`/`fix` touching the demo dir (R-5,
      demo-gate).
- [ ] AC-12: Changelog fragment and diary entry exist; weekly output PRs
      remain `docs(recap): ...` with no feature/changelog/diary
      obligations.
- [ ] AC-13: No `graph.yaml` or `prompts/*.yaml` modified. If a
      graph/prompt change becomes necessary, enforcement stops and a
      separate graph-authoring FR enters the governed route.

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

## Judgement (2026-08-18)

**Verdict:** APPROVED WITH REVISIONS — authority active now that R-1–R-5
are folded (this revision). Judge: gpt-5.5 via `scripts/judge.sh`; draft
at `tmp/draft-judgement.md`.

| # | Revision | Folded as |
|---|----------|-----------|
| R-1 | Bind `GH_TOKEN: RECAP_PAT` to every `gh` step; auto-merge repo setting is a human-set prerequisite | Workflow §2, AC-06/AC-10 |
| R-2 | Quiet week = zero *substantive* commits (exclude prior recap-only automation commits), not literal zero | Render script §1, AC-03/AC-04 |
| R-3 | Freeze render CLI + markdown section contract; test substance, not presence | Render script §1, AC-01/AC-02 |
| R-4 | Dispatch proof merges; cron evidence recorded later — dispatched run ≠ cron evidence | AC-09 |
| R-5 | README pointer trips demo-gate on `feat` PRs → refresh `demo-output.log` in scope | AC-11 |

**Scope frozen (D-1…D-6):** render script + tests + workflow + first recap
artifact on `main` + demo README pointer (with demo-output refresh) +
changelog/diary/FR notes.

**Not authorized:** modifying recap graph/prompts; doctrine or
required-check changes; direct pushes to `main`; admin/bypass PATs;
notification layers; issues/email/RSS output; generalizing to other repos
or the chaplain plan; a `yamlgraph recap` CLI command.

**Conditions (all GATE):** C-1 revisions folded before authority (done);
C-2 graph/prompts unmodified; C-3 only the fine-grained repo-scoped PAT;
C-4 human review of workflow/secret/auto-merge changes before reliance;
C-5 not fully complete until real cron evidence; C-6 branch-protection
settings unchanged.

### Questions for the human

None — the two human-set prerequisites (RECAP_PAT secret, auto-merge repo
setting) are execution steps, not open decisions.

## Implementation Notes (2026-08-18)

**Status:** D-1/D-2/D-3/D-5 delivered; dispatch proof (AC-07/AC-08)
blocked on human-set `RECAP_PAT`; cron observation pending.

- RED 9af06b82 (11 tests, `tests/unit/test_weekly_recap.py`,
  REQ-YG-604/CAP-241) → GREEN 3117c178 (`scripts/weekly_recap.py`) →
  ci c8d21d24 (workflow) → docs 4a726a18 (README pointer + demo proof).
- **Defect caught by `read_raw_output_first`:** first real dry-run
  rendered `## Workstreams\n(none)` on a 109-commit week. Raw log showed
  the `synthesize` node had FAILED (local `PROVIDER=deepseek` timeout),
  the graph error handler swallowed it, and orphans still rendered
  (they bypass the model, FR-704) — a shapely, plausible, wrong recap.
  Condemned with `test_node_failure_raises_never_renders`; cure:
  `run_recap_graph` raises on any `errors` in final state. Workflow pins
  `PROVIDER: anthropic`.
- **Git quirk:** `--since=2999-01-01` overflows approxidate and silently
  includes *everything* (git 2.50.1); test uses 2099. Noted in-test.
- Demo-proof hook fired locally on the README pointer (R-5 anticipated
  the CI gate; the local hook is stricter) — `demo-output.log`
  regenerated from a real anthropic run.
- Second real dry-run (anthropic): full sectioned recap with joined
  `[Status: …]` tags — `logs/fr821-dryrun2.log`.
- Prerequisites: `allow_auto_merge=true` verified via API;
  `ANTHROPIC_API_KEY` secret set from operator vault via stdin (value
  never displayed, FR-819 pattern). `RECAP_PAT` awaits human creation:
  fine-grained, resource = sheikkinen/yamlgraph only, permissions
  Contents RW + Pull requests RW.
