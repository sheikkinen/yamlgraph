# Feature Request: Main-Write Guard — Worktree as the Only Enforcement Write Path

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-25
**First consumer / first event:** the next enforcement-class FR arc — the
first edit-tool write it attempts against code/test paths on the main
checkout, which the guard converts into a worktree.

**Prior art:** **Supersedes FR-750** (Judged 2026-07-18, pilot never ran):
its one-arc pilot required voluntary adoption — an unrouted worktree that no
session remembered to enter for 5 weeks while every enforcement arc
(including FR-884) ran on main; its purge list deferred this exact deny-hook
to "a separate FR, drafted only on adopt" — a gate the operator lifted
2026-08-25 (circular sequencing: the pilot needed the router it deferred).
The frozen Q1/Q4 decisions of
`docs-planning/plan-interactive-finalize-coordinator.md` (worktree parity;
"hook DENIES writes to main — worktree becomes the only write path") are
preserved, now with the FR-884 census as pricing evidence. FR-767 is the
mechanism precedent (PreToolUse path-guard, fail-closed, sole-route denial);
FR-885 (deploy watcher) and FR-886 (adoption nudge) are census siblings —
FR-886 stays advisory because a judgement has a governed alternative route;
this guard blocks because a shared index has no safe "advisory" mode.
`scripts/worktree.sh` (chaplain lineage, FR-241 teardown self-heal) is the
reused substrate. No graveyard hit proposes the interactive-lane guard
itself.

## Summary

A PreToolUse guard that **denies enforcement-class writes on the main
checkout** with a denial message that carries the complete cure inline (the
worktree command), plus the worktree-setup completion that makes the cure
actually work: `.env` provisioning alongside the existing `.venv` symlink.
Integration tail: branch → PR → `gh pr merge --auto --squash` → FR-885
watcher; no premium session ever waits on CI.

## Value Statement

The shared-index hazard (`one_session_one_repo`: 3 recorded strikes + 2
near-misses in one July week, 2 more FR-748-class catches since) becomes
structurally impossible for enforcement work, and the routing problem
("agents never read guidelines") is solved at the only address agents
reliably read — the denial message.

## Problem

1. **Voluntary routing does not happen.** FR-884 priced it: the judge sole
   route existed all window and 18.5% of tokens judged interactively anyway;
   FR-750's unrouted pilot got zero subjects in 5 weeks. Instruction text
   and wrapper scripts that agents must remember are guidelines nobody reads
   at the moment of temptation.
2. **The denial IS the guideline delivery mechanism** — witnessed 4× in one
   session (2026-08-25): pytest-pipe guard, FR-767 authoring guard,
   prior-art gate, fr-board drift — each denial carried an inline cure and
   produced one-step compliance from an agent that had read none of the
   underlying docs.
3. **The worktree dance is incomplete** (operator note, verified):
   `scripts/worktree.sh` symlinks `.venv` and cleans stale `.pth` entries
   but never provisions `.env` — any `set -a; source .env` or dotenv load in
   a fresh worktree silently yields no credentials; graph runs and
   integration tests fail late and confusingly instead of early and clearly.

## Ideal Result

An agent that starts editing code for FR-NNN on the main checkout is denied
once, with a message it can execute verbatim; thirty seconds later it is
working in `../wt-fr-NNN` with working credentials and venv; when GREEN, it
runs `gh pr merge --auto --squash` and moves on; the FR-885 watcher follows
the merge and CD. Main's index is never shared by enforcement work again,
and the interleave ritual (staged-check, explicit file lists) becomes a
historical document.

## Proposed Solution

### 1. The guard (deny-mode, fail-closed, narrow grammar)

PreToolUse check in the `pre-command-guard.sh` family:

- **Fires when:** an edit-tool write (`create_file`,
  `replace_string_in_file`, `multi_replace_string_in_file`) or a recognized
  terminal write-redirect targets **enforcement-class paths** —
  `yamlgraph/**`, `tests/**`, `scripts/**`, `capabilities/**`,
  `.github/hooks/**` — AND the target resolves inside the **main checkout**
  (not a `git worktree` — detected mechanically via `git rev-parse
  --git-common-dir` vs `--git-dir` divergence, not path heuristics).
- **Never fires on:** docs lane (`docs/**`, `feature-requests/**`,
  `changelog/**`, `research/`, `tmp/**`, `logs/**`) — the current healthy
  direct-to-main flow for FRs, judgements, diaries, boards stays untouched;
  writes inside any worktree; the chaplain lane (already worktree-native).
- **Denial format (the contract):** first line = verdict; body = the
  complete copy-paste cure; last line = doctrine pointer. No bare RTFM.

```
Enforcement write to the main checkout denied (FR-888).
Work in an FR worktree:
  scripts/worktree.sh create fr-<nnn> && cd <printed-path>
(one_session_one_repo — details: feature-requests/FR-888-*.md)
```

- **Grammar-poverty guard:** unlike FR-767's fail-closed-on-unparseable,
  unrecognized command shapes are ALLOWED here with an audit row —
  a false deny on `time`-prefixed commands (witnessed 2026-08-25) is worse
  for this guard than a rare miss, because the CI/PR ring catches escapes.
- **Escape hatch:** `FR888_ALLOW_MAIN=1` env prefix, audited to
  `audit.jsonl` — for genuine main-lane maintenance; every use is a logged
  datum for the re-census.

### 2. The worktree dance completed (`scripts/worktree.sh`)

- Symlink `.env` from the main checkout (same policy as `.venv`: single
  source of truth, key rotations propagate; `ln -snf`). Verify after
  creation: `[ -r "$wt/.env" ]` or warn explicitly.
- Print the `cd` target as the last stdout line (the guard's denial quotes
  it).
- Known limitation pinned, not hidden: the shared `.venv` means `pip
  install` from any tree mutates all trees (recorded environment hazard) —
  the setup banner says so; dependency changes belong on main-lane commits.
- Teardown remains `scripts/worktree.sh` + FR-241 self-heal; prune on
  FR rejection.

### 3. The integration tail (no premium waiting)

Documented in the same denial-adjacent runbook section: push branch →
`gh pr create` → `gh pr merge --auto --squash` (in-repo precedent:
weekly-recap workflow) → optional `scripts/vscode/rollout_watch.py`
(FR-885) for the CD leg. Merge-queue adoption is explicitly deferred until
parallel-branch update collisions are observed (strict up-to-date is on;
auto-merge alone likely suffices at current concurrency).

## Acceptance Criteria

- [ ] AC-01: Guard denies an edit-tool write to `yamlgraph/**` on the main
      checkout and ALLOWS the byte-identical write inside a worktree —
      both witnessed by hook tests in `.github/hooks/tests/` (fixture
      repos, never live)
- [ ] AC-02: Docs-lane writes (`docs/`, `feature-requests/`, `changelog/`)
      on main are never denied — witnessed by tests
- [ ] AC-03: Worktree detection uses git plumbing (`--git-common-dir`),
      not path string matching — witnessed by a test with a nested-repo
      fixture
- [ ] AC-04: Denial message contains the executable cure (create command +
      cd target); a fresh worktree created via the cure has readable
      `.env` and importable `.venv` — witnessed by an integration test
- [ ] AC-05: Unrecognized command shapes are allowed-with-audit, not
      denied (anti-`time`-prefix regression test)
- [ ] AC-06: `FR888_ALLOW_MAIN=1` escape works and writes an audit row
- [ ] AC-07: One real FR arc executed end-to-end through the guard:
      denial → worktree → enforce → PR → auto-merge — recorded in this FR
      with the wall-clock and bounce counts FR-750 wanted (its measurement
      table inherited here)
- [ ] AC-08: Re-census criterion recorded: zero shared-index incidents and
      the FR-884 classifier's repo-ops/deploy-watch interactive share over
      the next 30-day window; escape-hatch use frequency reported
- [ ] AC-09: FR-750 marked Superseded with pointer; changelog fragment;
      diary reflection

## Alternatives Considered

- **Advisory-first (FR-886 ladder)** — rejected by operator decision
  2026-08-25: a shared index has no safe advisory mode; the census already
  supplied the evidence an advisory phase would collect.
- **plan.sh as a sole route** — routes the wrong thing: ideation is the
  human-paired phase; the write boundary is where the hazard lives.
- **FR-750's voluntary pilot** — superseded: 5 weeks, zero subjects.
- **Full chaplain revival** — the FSM runtime died of disuse; this takes
  its worktree contract (salvage) without its daemon lifecycle.

## Related

- FR-750 (superseded), `docs-planning/plan-interactive-finalize-coordinator.md`
  (Q1–Q9 frozen decisions), FR-767 (guard mechanism), FR-885/FR-886
  (census siblings), FR-884 (pricing evidence + re-census instrument),
  FR-241/CAP-102 (teardown self-heal), FR-311 (bounded commit retry)
- Scripture: `one_session_one_repo`, `two_strike_split`,
  `enforcement_at_merge_boundary`, `boring_enforcement`
