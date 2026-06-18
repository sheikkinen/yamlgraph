# Feature Request: FR-520 - DM v2 Chapter-Lived Positional Working Memory (Phase 2)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Gate OPEN — FR-519 witness (10021-BC ch6) confirmed the residual; ready to plan
**Effort:** ~1-2 days
**Requested:** 2026-06-18

> **Gate evidence (2026-06-18, FR-519 enforce witness).** Re-closing chapter 6 of
> `10021-BC` with FR-519's final-cut enforcement in place leaves Hagan acting after
> his within-chapter death ("made one last claim … stepping in", "drove the staff
> down again", "bloodied hand dragged across the settlement edge") while the
> chapter-end ledger holds `Hagan status=dead`. The played arc itself has him
> acting across turns 11–16 after his death turn, so the final-cut prompt cannot
> reconcile it without breaking beat-fidelity. This is exactly the turn-to-turn
> contradiction that reconciles to the chapter-end snapshot — the entry condition
> below is satisfied. Possession (the staff) was sufficiently fixed by FR-519's
> prompt injection, so Phase 2's scope narrows to the **death-point / lifecycle**
> turn-grained signal. See `feature-requests/FR-519-*` Implementation + Witness.

## Summary

Add a chapter-lived, turn-grained **working memory** of physical state — who holds
what, who stands where — to catch contradictions that the chapter-snapshot
`world_state` ledger structurally cannot see: a character who drops a weapon in
turn 3 and wields it in turn 5 while still *holding it at chapter close*. The
persistent ledger is correct at the chapter boundary; the **path through the turns**
is unconstrained. This is the working-memory layer to the relationship ledger's
long-term memory — seeded from the inherited ledger at turn 1, updated each recap,
consulted by the next turn, folded into the persistent ledger at close, then
discarded.

**This FR is Phase 2.** Phase 1 enforcement of the *existing* persistent facts ships
first as **FR-519**. This FR is **gated**: it is built only if FR-519's witness
shows turn-to-turn contradictions remain after the chapter-end facts are enforced.

## Value Statement

A reader never sees a character lose an object and use it again within the same
chapter, nor jump between named positions without a narrated move — the
turn-grained physical continuity a chapter-snapshot ledger cannot enforce on its own.

## Judgement

Decision: **Gate ratified; build deferred.** The phasing is correct and the entry
gate is the right discipline — this FR must **not** be built until FR-519's witness
proves enforcement insufficient. The judge ratifies the gate and freezes three
conditions that the gate-open redraft must satisfy before any code.

**C1 — the gap is intra-chapter turn-to-turn propagation, not chapter-start
visibility.** Sharpen the problem statement: `running_scene` *already* renders the
inherited ledger's `location`/`inventory`/`objects` into turn context via
`format_world_state`, so turn 1 already sees chapter-start positions. The missing
signal is strictly **turn N's committed changes reaching turn N+1 within the same
chapter**. The redraft must scope to exactly that and not re-solve chapter-start
visibility (already solved).

**C2 — `update(memory, recap)` is a NEW prose→structured boundary and inherits the
FR-513 grounding discipline.** Extracting "X dropped the weapon" from free-form
director recap prose is itself a fallible extraction (deterministic parse or a small
structured LLM step). This is precisely why the gate exists: if FR-519 (which adds
*no* extraction boundary) suffices, we avoid introducing a fragile new one. On
gate-open, the extraction mechanism must be pinned against the concrete residual
fixture, and any LLM extraction must be grounded (no physical change asserted
without recap evidence), mirroring `parse_world_state`'s boundary gate.

**C3 — fold must reconcile with FR-514's lane floor.** `fold(memory) -> overlay`
writes into the same `characters.inventory`/`objects` lanes that `apply_lane_floor`
floors at close. The redraft must specify precedence (does a working-memory fold
override a floored lane, or vice versa?) so the two mechanisms do not silently
fight — the same floor interaction flagged in FR-519 B4.

Gate-open entry condition (unchanged, ratified): FR-519 enforced **and** witnessed,
**and** a turn-to-turn contradiction that reconciles to the chapter-end ledger still
remains. If FR-519 clears it, close this FR as not-needed and record the decision.
The redraft carries the concrete residual case as its first test fixture.

## Problem

The `world_state` ledger tracks `characters.location`, `characters.inventory`, and
the `objects` lane, but it is a **per-chapter snapshot** — one committed value at
chapter close. A contradiction that *resolves back* to that snapshot is invisible
by construction:

- "dropped weapon turn 3, used it turn 5, holding it at close" — the close ledger
  correctly reads `holds: weapon`; the turn-3→turn-5 contradiction left no trace.

FR-519 (Phase 1) threads the chapter-end facts into the final-cut prompt, which
catches prose that contradicts the **boundary** truth. It cannot catch a
mid-chapter flip that reconciles by close, because there is no turn-grained record
of "who held what at turn N" for the next turn to consult. That record is the
missing **working memory**.

This mirrors the established split: the FR-513–518 relationship ledger is
*long-term* memory (carried across chapters); this is *working* memory (lives
inside one chapter, discarded after the close fold) — the same two-tier shape every
surveyed agent-memory system uses.

## Phase 2 gate (entry condition)

This FR is **not** to be built until **both** hold:

1. FR-519 is enforced and witnessed on 10021-BC (or a kill/drop fixture).
2. The witness still shows a turn-to-turn possession/position contradiction that
   **reconciles to the chapter-end ledger** (i.e. Phase 1 could not see it).

If FR-519's witness clears the contradictions, this FR closes as **not-needed** and
the gate decision is recorded. The redraft that opens Phase 2 must carry the
concrete remaining failing case as its first test fixture (no speculative build).

## Scope

In scope (once gated open):
- A pure `positional_memory.py` (mirroring `world_state.py`'s purity — no LLM, no
  I/O) with:
  - `seed(inherited_ledger) -> memory` — initial who-holds-what / who-is-where from
    the chapter's inherited `world_state` at turn 1.
  - `update(memory, recap) -> memory` — fold one turn's recap into the working set
    (object handovers, position moves) at the boundary where the recap is committed.
  - `fold(memory) -> ledger_overlay` — collapse the chapter's working memory into
    the persistent `world_state` lanes at `close_chapter`.
- Wiring: `turn_ops.running_scene` **consults** the working memory for turn N+1's
  context; `chapter_ops.close_chapter` **folds** it; nothing persists it beyond the
  chapter (mirroring FR-492's no-stored-book rule).

Out of scope:
- Spatial-geography vagueness / establishing-shot prose craft (not a state bug).
- A general physics / collision / continuous-space model — this tracks discrete
  named possession and named position, not geometry.
- The persistent ledger's chapter-grain shape or the relationship lane (unchanged).
- Anything FR-519 already covers (chapter-end-fact enforcement at the final cut).

## Proposed Solution (sketch — detailed on gate-open)

```python
# positional_memory.py — pure, chapter-lived
def seed(inherited: dict) -> dict: ...          # from world_state at turn 1
def update(memory: dict, recap: str) -> dict: ...  # fold one recap's moves/handovers
def fold(memory: dict) -> dict: ...             # overlay onto world_state at close
```

- `running_scene(doc, cid, n)` reads the working memory (not just the inherited
  ledger) so turn N+1 sees turn N's committed handovers/moves.
- `close_chapter` calls `fold` and overlays the result onto the emitted lanes
  before the persistent commit, then discards the working memory.

The concrete `update` extraction strategy (deterministic parse vs. a small
structured LLM step over the recap) is deferred to the gate-open redraft, chosen
against the actual remaining failing case so it is not over-built.

## Acceptance Criteria

- [ ] **Gate recorded first:** FR-519 witnessed; a concrete turn-to-turn
      contradiction that reconciles to the chapter-end ledger is captured as the
      Phase 2 fixture. (If none, close this FR as not-needed.)
- [ ] `positional_memory.py` is pure (no LLM, no I/O) with `seed`/`update`/`fold`.
- [ ] Unit test: seed from an inherited ledger reproduces its possession/position.
- [ ] Unit test: drop-then-use across turns is caught (the captured fixture) —
      turn N+1 context reflects the turn-N drop.
- [ ] Unit test: `fold` produces a `world_state` overlay consistent with the final
      turn's working memory.
- [ ] Working memory is not persisted beyond the chapter; only the close fold
      survives.
- [ ] Witness: the FR-519-residual contradiction clears.
- [ ] Tests added; `docs/architecture.md` §5a updated with the working-vs-long-term
      memory split.

## Alternatives Considered

- **Fold Phase 1 and Phase 2 into one FR.** Rejected — Phase 1 reads existing state
  (cheap, no new persistence) and may suffice alone; bundling forces the heavier
  working-memory build before its need is proven. Splitting keeps the escalation
  evidence-driven (the gate).
- **Persist the working memory across chapters.** Rejected — that is what the
  long-term ledger (FR-513–518) is for; the working memory's value is precisely
  that it is chapter-scoped and discarded, keeping turn context bounded.
- **Gate each turn recap against the ledger directly.** Equivalent in effect but
  couples the director to physical bookkeeping; a dedicated pure module keeps the
  seam testable and the director focused on arc judgement.

## Related

- **`feature-requests/FR-519-dm-v2-intra-chapter-prose-state-enforcement.md`** —
  **Phase 1** (ships first; this FR is gated on its witness).
- `feature-requests/FR-513..518` — the relationship ledger-as-memory arc; this FR is
  its *physical-state working-memory* analogue.
- `examples/dungeon_master/api/world_state.py` — `Character.location/inventory`,
  `WorldObject.holder/location` (the persistent lanes the working memory seeds from
  and folds into).
- `examples/dungeon_master/api/turn_ops.py` — `running_scene` (consult),
  `chapter_ops.close_chapter` (fold).
- Evidence: `outputs/dungeon-master/10021-BC/{story.json,review.md}`.
