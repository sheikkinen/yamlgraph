# Feature Request: Main-Write Guard — Worktree as the Only Enforcement Write Path

**Priority:** HIGH
**Type:** Feature
**Status:** Completed 2026-08-25 — PR #476 squash-merged fc349777 by operator decision (AC-13 satisfied); guard live on main; worktree torn down via rm-safe --merged-confirmed (dogfood)
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
  `.github/hooks/**` — AND the target resolves inside the **main checkout**.
- **Worktree detection predicate (frozen, R-2):** main checkout ⇔
  `git rev-parse --path-format=absolute --git-common-dir` resolves (after
  symlink normalization, `pwd -P`) to the same directory as
  `git rev-parse --path-format=absolute --git-dir`; linked worktree ⇔ the
  resolved paths differ. Non-git or parse-error contexts fail closed ONLY
  when an enforcement-class write target is present, with an audit row
  naming the parse failure. Nested git repositories under the checkout are
  fixture-tested so a foreign repo is never misclassified as the main
  checkout.
- **Never fires on:** docs lane (`docs/**`, `feature-requests/**`,
  `changelog/**`, `research/`, `tmp/**`, `logs/**`) — the current healthy
  direct-to-main flow for FRs, judgements, diaries, boards stays untouched;
  writes inside any worktree; the chaplain lane (already worktree-native).
- **Denial format (the contract):** first line = verdict; body = the
  complete copy-paste cure; last line = doctrine pointer. No bare RTFM.

```
Enforcement write to the main checkout denied (FR-888).
Work in an FR worktree:
  scripts/worktree.sh new fr-<nnn> && cd <printed-path>
(one_session_one_repo — details: feature-requests/FR-888-*.md)
```

(R-1: the cure uses the EXISTING `new` verb — `scripts/worktree.sh`
supports `new|spike|rm|list`, not `create`; the script must print an
unambiguous final `cd <path>` line the denial quotes. No alias is added.)

- **Write-shape grammar (R-3 — CI is NOT the safety net; the hazard is
  local and pre-CI):** unrecognized **read-only/non-write** shapes are
  allowed with an audit row (anti-`time`-prefix). But a terminal command
  that both mentions an enforcement-class path AND contains an
  unclassified write signal (`>`, `>>`, `tee`, `cp`, `mv`, `rsync`,
  `install`, `sed -i`, `python/perl/ruby -c|-e` with `open`/`write`,
  `dd`, `truncate`) is DENIED with the worktree cure unless the escape
  hatch is present.
- **Escape hatch (R-4):** `FR888_ALLOW_MAIN=1` env prefix — allows ONLY
  the FR-888 main-write denial class. Audit row carries `session_id`,
  `tool_use_id` (when available), cwd, normalized target path(s),
  command/tool name, reason `fr888-main-write-override`. It must not
  bypass unrelated guards (Co-authored-by, `--no-verify`, branch
  creation, FR-767 authoring route) — witnessed by tests.

### 2. The worktree dance completed (`scripts/worktree.sh`)

- Symlink `.env` from the main checkout (same policy as `.venv`: single
  source of truth, key rotations propagate; `ln -snf`). Verify after
  creation: `[ -r "$wt/.env" ]` or warn explicitly.
- Print the `cd` target as the last stdout line (the guard's denial quotes
  it).
- Known limitation pinned, not hidden: the shared `.venv` means `pip
  install` from any tree mutates all trees (recorded environment hazard) —
  the setup banner says so; dependency changes belong on main-lane commits.
- Teardown ownership — every creation path has a named pruner (gap found
  2026-08-25: the auto-merge tail removes the blocking pipeline that used
  to be alive at merge time, so the happy path would otherwise leave an
  unowned tree per merged FR):

  | Path | When | How | By whom |
  |---|---|---|---|
  | Merged FR | watcher observes merge confirmed | verify branch merged + zero untracked files → safe removal; else flag on board | **FR-885 watcher** — ONLY under FR-885's own authority (R-5); under FR-888, this path is proven by fixture/stub contract |
  | Rejected FR | at rejection fold | same verify-then-remove | the session folding the rejection (witnessed, AC-11) |
  | Pipeline died mid-flight | board refresh | flag with age + untracked count; human dispositions | `now.py` board → human (AC-10) |

  Safety invariant on all paths: **a tree with untracked files is never
  auto-removed** — flagged instead (untracked = no recovery; the FR-697
  orphans are the witness). **R-6:** the current `worktree.sh rm` uses
  `git worktree remove --force` + branch delete — unsafe for automatic
  pruning; this FR adds a narrow **safe-removal mode** (verify merged +
  zero untracked, else flag) used by the automatic paths; manual `rm`
  behavior is unchanged. FR-241 self-heal remains the repair layer.

### 3. The integration tail (no premium waiting)

Documented in the same denial-adjacent runbook section: push branch →
`gh pr create` → `gh pr merge --auto --squash` (in-repo precedent:
weekly-recap workflow) → optional `scripts/vscode/rollout_watch.py`
(FR-885) for the CD leg. Merge-queue adoption is explicitly deferred until
parallel-branch update collisions are observed (strict up-to-date is on;
auto-merge alone likely suffices at current concurrency).

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: PreToolUse hook denies an unsentineled edit-tool write to an
      enforcement-class path when cwd is the main checkout and allows the
      byte-identical write in a linked worktree — fixture tests, never
      live repo mutation
- [ ] AC-02: Docs-lane writes (`docs/**`, `feature-requests/**`,
      `changelog/**`, `research/**`, `tmp/**`, `logs/**`) on main allowed
      and tested
- [ ] AC-03: Worktree detection via normalized git plumbing
      (`--path-format=absolute --git-common-dir` vs `--git-dir`); tested
      for main checkout, linked worktree, nested repo, parse-error cases
- [ ] AC-04: Denial message: first line verdict, body contains one
      executable cure using the canonical `scripts/worktree.sh new` verb
      plus a concrete `cd` target, last line doctrine pointer
- [ ] AC-05: `worktree.sh` produces a tree with readable `.env` (when main
      has one) and importable `.venv`; final stdout line is the `cd`
      command/path the denial cure quotes
- [ ] AC-06: Terminal write grammar tested: redirect, quoted redirect,
      `tee`, `cp`/`mv`, directory copy materializing an enforcement path,
      `sed -i`, env-prefixed command, `time`-prefixed read-only ALLOWED,
      `time`-prefixed write DENIED or explicitly classified
- [ ] AC-07: `FR888_ALLOW_MAIN=1` allows only the FR-888 denial class,
      emits the full audit row (session/tool/cwd/targets, reason
      `fr888-main-write-override`), and bypasses no other guard
- [ ] AC-08: Unrecognized non-write shapes allowed-with-audit; unrecognized
      write-shaped commands targeting enforcement paths denied without the
      escape hatch
- [ ] AC-09: FR-750 marked Superseded with pointer; changelog fragment;
      diary reflection
- [ ] AC-10: Orphan-tree detection on the `now.py` board (no open PR + no
      live pipeline → age + untracked count), fixtures; auto-deletion
      explicitly absent
- [ ] AC-11: Teardown ownership witnessed WITHOUT depending on unapproved
      FR-885: rejected-path teardown and a merged-path stub/fixture both
      verify branch state + zero untracked before removal, both flag
      instead of remove on untracked; live watcher teardown stays FR-885's
      acceptance
- [ ] AC-12: Existing hook suites (FR-767 authoring guard, pre-command
      guard) still pass; no guard weakened
- [ ] AC-13: Human review of the hook/worktree enforcement diff recorded
      before it is treated as merged policy (R-7 gate)

**Decisions (operator, 2026-08-25):** enforcement starts immediately and
this FR's own arc is the first worktree-resident arc (dogfood); the R-7
human-review gate is satisfied via **PR + the sole review route**
(`scripts/review.sh`) followed by the operator's merge decision.

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

## Implementation Status (2026-08-25, enforced in tmp/worktrees/feat/fr-888)

- Dogfood: this arc is the first worktree-resident arc. The tree's birth
  witnessed three cure-path defects live: no `.env`, no final `cd` line,
  and the FR's original `create` verb never existed (judge R-1 confirmed).
- RED: `.github/hooks/tests/test_main_write_guard.py` (19 witnesses,
  11 red at commit). GREEN: Check 7 in `pre-command-guard.sh` (plumbing
  detection per R-2, write-TARGET grammar per R-3 — mention-grammar
  false-deny caught and fixed pre-commit, audited escape per R-4, bash
  pre-filter preserving the FR-442 python budget); `worktree.sh` `.env`
  symlink + final `cd` line + `rm-safe` (setup artifacts excluded from
  the untracked check); AC-10 orphan flags on the `now.py` board.
- 162 hook tests green including FR-767/FR-442 suites (AC-12).
- Deviations: none from judged scope; AC-13 (human review) pending on
  the PR; live arc measurement (inherited FR-750 table) recorded after
  merge+first routed arc.

**Merge record (2026-08-25):** 5 review rounds via the sole review route
(advisory), 14 defect classes fixed from reviewer probes (rm-safe
merge-state + squash path, dir-copy materialization, executable cure,
guard-root scoping, Delete/Move-to hunks, time/whitespace wrappers,
direct writers, sed variants, interpreter inner paths). Operator issued
the merge decision explicitly ("force merge") — the human gate is the
merge click, not the review loop's convergence. 181 hook tests green at
merge. Lifecycle dogfood complete: born by `worktree.sh new`, died by
`rm-safe --merged-confirmed`.
