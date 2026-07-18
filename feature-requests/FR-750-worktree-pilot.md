# Feature Request: FR-750 Worktree Pilot — one FR arc lived in a tree, measured

**Priority:** MEDIUM
**Type:** Enhancement (workflow pilot; measurement before mandate)
**Status:** Proposed
**Effort:** 1 day (the pilot arc's overhead + instrumentation)
**Requested:** 2026-07-18
**First consumer / first event:** the next enforcement-class FR after
judgement of this one — it becomes the pilot subject; first event =
its worktree's creation at plan time.

## Summary

Run exactly ONE interactive FR arc — plan, judge, enforce, finalize —
entirely inside an FR-scoped git worktree, with named measurements,
to decide whether worktree isolation becomes the interactive lane's
enforcement container. No hooks armed, no mandate; the pilot's
evidence is the deliverable.

## Value Statement

The shared-index hazard (`one_session_one_repo`, 3 recorded strikes +
2 near-misses this week) either gets dissolved by construction or the
worktree idea gets a data-backed grave next to the watcher — one
arc's cost buys the decision either way.

## Problem

4+ parallel agent sessions share one checkout of main. Doctrine
manages the hazard by ritual (staged-check, explicit file lists,
immediate commits); this week the ritual caught a foreign staged FR
twice and a `commit -a` sweep once — recoveries took seconds, but the
top-tier (fable-class) agent itself committed the sweep, proving the
choreography is error-prone at every tier.

The chaplain lane solved this by construction: worktree per FR,
judge+enforce in the tree, teardown at merge. But the watcher is dead
— died of disuse, no retirement FR, no post-mortem — so its worktree
contract is salvage material, not a living precedent. Whether the
interactive lane (whose value is tight human pairing in ONE visible
checkout) can live in trees is an open empirical question with known
unpriced costs.

**Prior art:** watcher-pipeline-v2 worktree lifecycle
(scripts/worktree.sh, .chaplain/lib/watcher/worktree_setup.sh /
worktree_teardown.sh, clean-worktree.sh — the salvage inventory);
`one_session_one_repo` (Scripture, 3 strikes); FR-698 (executor-
neutral worktree tooling, the last watcher-era commit); the session
phase census + its re-judgement (docs/research-session-phase-census-
2026-07-18.md). Disposition: the pilot reuses the salvaged scripts
verbatim where possible; it deliberately does NOT resurrect the FSM
runtime.

## Ideal Result

The decision "do interactive arcs live in worktrees?" is made by one
arc's measured evidence instead of by architecture taste. If yes: the
lane adopts an enforcement container that makes cross-session
collisions structurally impossible. If no: the ritual stays, the idea
gets a documented grave, and no hook was ever armed against the 63%
of traffic that never had the disease.

## Proposed Solution

1. **Pilot subject:** the next enforcement-class FR (feat/fix
   touching yamlgraph/, tests/, capabilities/) after this FR is
   judged. Docs-class work is explicitly NOT piloted.
2. **Lifecycle under test (R2 contract):** tree born at PLAN (FR
   drafted in the tree), judgement lands in the tree, RED/GREEN +
   diary in the tree, finalize = squash back via the concurrency
   mechanism judged appropriate (PR or local merge — recorded, not
   prescribed), teardown after. Pruning path exercised deliberately
   if the pilot FR dies.
3. **Named measurements, recorded in THIS FR:**
   - environment-setup minutes (venv strategy: shared interpreter vs
     per-tree install — the recorded incident class);
   - tree-confusion incidents (wrong-cwd commands, editor showing
     stale tree);
   - FR-visibility friction (board/triage/parallel-judge reads of an
     FR that lives off-main);
   - pruning/teardown burden;
   - human-pairing ergonomics (subjective, human's verdict recorded
     verbatim);
   - hook-cycle count vs a recent on-main arc of similar size
     (FR-747 = baseline: 2 commits, 1 bounce).
4. **Decision table, pre-committed:** adopt (all measurements
   tolerable + human verdict positive) / adapt (change birth point to
   enforce-time, re-pilot once) / abandon (documented grave with the
   numbers). The main-write-denial hook is a SEPARATE future FR,
   drafted only on "adopt".

## Acceptance Criteria

- [ ] AC-01: one complete arc (plan→judge→enforce→finalize→teardown)
      executed in a worktree; every phase's artifacts land correctly.
- [ ] AC-02: all six measurements recorded in this FR with numbers,
      not adjectives.
- [ ] AC-03: decision table row selected and justified; follow-up FR
      drafted only if "adopt".
- [ ] AC-04: salvage inventory annotated — which watcher scripts were
      reused as-is, which needed changes, which are dead.

## Out of scope (purge list)

- The main-write-denial hook (both rings) — separate FR, gated on
  "adopt".
- The finalize graph / commit agent — separate concern, evidence-
  gated on counts this pilot does not produce.
- Any FSM/statemachine-engine resurrection.
- Migrating docs-class commits off main.

## Alternatives Considered

- Mandate worktrees now (original plan §5 Q4): rejected by
  re-judgement — the disease's measured damage this week was one
  cosmetic reformat; construction-grade cures need more than paper
  cuts as justification.
- Do nothing (ritual is enough): the pilot IS the test of this
  alternative — if measurements say the ritual outperforms the tree,
  that is the documented outcome.

## Questions for the human (as options, or 'none')

None at proposal time — the pilot exists to replace questions with
measurements. The venv strategy (shared vs per-tree) is measured, not
asked.

## Triage (generated — claims requiring disposition)

- [pending] canon: would_you_use_this: yes, the next enforcement-class FR after this one is judged becomes the pilot subject
- [pending] canon: who_reads_this_when: the interactive lane's team at finalize time, when the decision table row is selected and justification written
- [pending] canon: does_the_platform_already_do_this: yes, salvaged from watcher-pipeline-v2 (scripts/worktree.sh, chaplain/lib/watcher/{worktree_setup,worktree_teardown}.sh, clean-worktree.sh) — pilot reuses verbatim where possible
- [pending] pre-mortem: Pilot FR selected but is docs-class (explicitly out of scope per Proposed Solution §1) — triage never runs, AC-01 never exercised, FR ships with no measurements
- [pending] pre-mortem: Measurements recorded as adjectives ('environment setup was smooth', 'pairing felt good') instead of numbers — AC-02 fails mechanically on audit
- [pending] pre-mortem: Decision table row selected but no follow-up FR drafted despite 'adopt' verdict — the enforcement hook never gets gated properly, violating the commitment in Proposed Solution §4
- [pending] pre-mortem: Salvage inventory annotated incompletely (e.g. 'worktree.sh reused' with no record of which lines changed or why) — AC-04 fails, next pilot has no inheritance chain
- [pending] pre-mortem: Hook-cycle count vs FR-747 baseline never recorded because pilot arc's commits are not compared to the same-size baseline's 2 commits / 1 bounce — AC-02 incomplete, decision lacks the mechanical evidence needed
- [pending] value-prop: For the interactive lane team, kills the shared-index collision hazard (3 strikes + 2 near-misses this week) by deciding whether worktree isolation is viable, vs the current error-prone ritual (staged-check, explicit file lists, immediate commits) — completable and derivable from FR text
