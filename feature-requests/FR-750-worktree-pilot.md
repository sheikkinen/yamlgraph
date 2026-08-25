# Feature Request: FR-750 Worktree Pilot — one FR arc lived in a tree, measured

**Priority:** MEDIUM
**Type:** Enhancement (workflow pilot; measurement before mandate)
**Status:** Superseded by FR-888 (2026-08-25, operator decision) — the
voluntary pilot got zero subjects in 5 weeks while every enforcement arc ran
on main; FR-888 replaces measurement-before-mandate with a deny-mode
main-write guard whose denial routes arcs into worktrees, inheriting this
FR's measurement table as its AC-07/AC-08.
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

- [accepted] canon: would_you_use_this: yes, the next enforcement-class FR after this one is judged becomes the pilot subject — tightened by F1: subject must touch yamlgraph/ proper and is named in this FR before measurement.
- [accepted] canon: who_reads_this_when: the interactive lane's team at finalize time, when the decision table row is selected and justification written — rung/reader/moment named; the table is the deliverable.
- [accepted] canon: does_the_platform_already_do_this: yes, salvaged from watcher-pipeline-v2 (scripts/worktree.sh, chaplain/lib/watcher/{worktree_setup,worktree_teardown}.sh, clean-worktree.sh) — pilot reuses verbatim where possible — all four scripts verified present.
- [accepted] pre-mortem: Pilot FR selected but is docs-class (explicitly out of scope per Proposed Solution §1) — triage never runs, AC-01 never exercised, FR ships with no measurements — F1 pins eligibility (yamlgraph/ diff) and a 14-day wait-and-record rule instead of scope-stretching.
- [accepted] pre-mortem: Measurements recorded as adjectives ('environment setup was smooth', 'pairing felt good') instead of numbers — AC-02 fails mechanically on audit — F3 fixes a unit per row up front; unitless row = failed AC-02.
- [accepted] pre-mortem: Decision table row selected but no follow-up FR drafted despite 'adopt' verdict — the enforcement hook never gets gated properly, violating the commitment in Proposed Solution §4 — AC-03 already binds follow-up drafting to 'adopt'; F2 additionally defaults mixed reads away from adopt.
- [accepted] pre-mortem: Salvage inventory annotated incompletely (e.g. 'worktree.sh reused' with no record of which lines changed or why) — AC-04 fails, next pilot has no inheritance chain — F5 fixes the per-script vocabulary: reused-verbatim / patched (+diff line count) / dead.
- [accepted] pre-mortem: Hook-cycle count vs FR-747 baseline never recorded because pilot arc's commits are not compared to the same-size baseline's 2 commits / 1 bounce — AC-02 incomplete, decision lacks the mechanical evidence needed — F4 additionally names the FR-749 confound and the substitute-baseline rule.
- [accepted] value-prop: For the interactive lane team, kills the shared-index collision hazard (3 strikes + 2 near-misses this week) by deciding whether worktree isolation is viable, vs the current error-prone ritual (staged-check, explicit file lists, immediate commits) — completable and derivable from FR text — honest framing: the deliverable is the decision, and 'abandon' is a success outcome.

## Judgement (2026-07-18)

**Verdict: AUTHORITY GRANTED** — scope frozen with the pins below.
This FR is measurement-before-mandate in its cleanest form: the
deliverable is a filled decision table, and "abandon" is a fully
successful outcome. That framing is the FR's chief virtue; the pins
protect it.

Salvage inventory verified: all four cited scripts exist
(`scripts/worktree.sh`, `.chaplain/lib/watcher/worktree_setup.sh`,
`worktree_teardown.sh`, `.chaplain/scripts/clean-worktree.sh`). Prior
art dispositioned; no FSM resurrection in scope.

**F1 — Pilot subject eligibility is the FR's soft spot.** "Next
enforcement-class FR (feat/fix touching yamlgraph/, tests/,
capabilities/)" — note FR-749, judged the same day, does NOT qualify
(scripts/ and hooks only, zero framework code). Pin: the pilot
subject is the next FR whose enforcement diff touches `yamlgraph/`
proper; the subject's id is written into this FR at pilot start,
before any measurement. If no eligible FR appears within 14 days,
that fact is itself recorded and the pilot waits — no scope-stretching
a docs-class FR into eligibility (the first pre-mortem).

**F2 — n=1 with a non-matched baseline.** FR-747 (2 commits, 1
bounce) is a baseline of convenience, not a matched control; one arc
cannot distinguish tree-costs from subject-costs. Pin: the decision
table may only claim what n=1 supports — "adopt" requires that NO
measurement was intolerable AND the human verdict is positive;
anything mixed lands on "adapt + re-pilot once" by default. Ambiguity
is information; do not launder a tied read into adoption
(threshold_encodes_forecast).

**F3 — Numbers, not adjectives, mechanically enforced.** AC-02's six
measurements each get a unit at pilot start: minutes, count, count,
minutes, verbatim quote (the one legitimately non-numeric row), count.
A row without its unit filled is a failed AC-02, full stop.

**F4 — Worktree interacts with FR-749's subject matter.** If FR-749
lands first, the pilot arc inherits edit-time hygiene, contaminating
the hook-cycle comparison against the pre-749 FR-747 baseline. Pin:
record FR-749's activation state (on/off) in the measurements row for
hook-cycles; if active, compare against a post-749 on-main arc
instead, or annotate the confound explicitly. A confounded number
with its confound named is evidence; the same number without it is
noise.

**F5 — Teardown is part of the arc, not an epilogue.** AC-01's
"teardown after" includes verifying `git worktree list` is clean and
the venv strategy's artifacts are gone; the watcher died leaving
trees behind (CAP-102 exists because of this). The salvage annotation
(AC-04) must state per script: reused-verbatim / patched (with diff
line count) / dead.

Triage claims: all dispositioned by F1–F5 (pre-mortems 1→F1, 2→F3,
3→decision-table contract as written, 4→F5, 5→F4; canon claims
verified above).
