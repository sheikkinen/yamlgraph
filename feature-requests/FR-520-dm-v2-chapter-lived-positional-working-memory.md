# Feature Request: FR-520 - DM v2 Chapter-Lived Positional Working Memory (Phase 2)

**Priority:** MEDIUM
**Type:** Feature
**Status:** **REJECTED (2026-06-18)** — superseded by **FR-521**. The gate-open review found the FR's premise false: the signal it proposed to build (a new `positional_memory.py` producing a turn-grained continuity record) **already exists** as the director's per-turn `continuity`/`steer` judgement. The witnessed defect is a missing feed-forward wiring (`detection_without_enforcement`), not a missing module — and the witnesses are all lifecycle/death-point, none positional. Replanned as FR-521 (feed the director's existing signal forward; no new module). This FR is retained as the rejection record; do **not** implement it.
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

> **Gate evidence (2026-06-18, 10022-BC generate+review with FR-519 shipped).**
> A second witness book (Arnulf arc) exposes two distinct escape paths the
> LangSmith `final_cut` traces confirm at the input boundary, sharpening Phase 2's
> scope:
>
> 1. **`missing_presumed_dead` is excluded from the death-token filter.** Ch3
>    `world_state` holds `Arnulf status=missing_presumed_dead`, but
>    `_DEAD_STATUS_TOKENS = {dead, slain, killed, deceased, fallen}` does not
>    contain it, so the Ch3 final_cut trace (05:57:19) shows
>    `dead_within_chapter = ''` — the gate never fired. The prose then declares
>    Arnulf dead and has him "dragging his chest higher and reaching for the edge"
>    in the same chapter. This is the headline class FR-519 targets, and it escapes
>    on exactly the lifecycle state the **presumed-dead → returns** synopsis arc
>    depends on. **Phase 2's death-point signal must treat `missing_presumed_dead`
>    as a death event, not only `dead`/`confirmed_dead`.**
> 2. **Enforcement is scoped to the final cut, not the running turns.** The Ch8
>    traces (06:03:16/06:03:21) show the before-open gate *did* fire
>    (`dead_before_open = 'Arnulf'`) and the closing scene is clean, yet "Arnulf
>    lunged" survives at 23% through the chapter (char 994/4329) — inside an
>    unguarded `running_scene` turn. **The turn-grained signal must be consulted by
>    `running_scene`, not only injected into the final cut.**
>
> Both findings reconcile to a correct chapter-end ledger (`story.json` tracks
> Arnulf alive→missing_presumed_dead→alive→confirmed_dead exactly), confirming this
> is the turn-path-vs-snapshot gap the gate names. Evidence:
> `logs/10022-ls2.log` (per-chapter final_cut inputs), `logs/10022-analysis.log`
> (ledger), `logs/10022-prose2.log` (offending sentences),
> `outputs/dungeon-master/10022-BC/review.md` (continuity 1/5).

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

## Judgement — Gate-Open Review (2026-06-18)

Decision: **Blocked — Granted on redraft.** The gate is open (two witnesses), but
the witnessed residual and the FR's proposed mechanism have **diverged**. Both
witnesses — 10021-BC ch6 (Hagan acts after within-chapter death) and 10022-BC ch3
(`missing_presumed_dead` escapes the death-token filter) + ch8 (post-death action
in a running turn) — are **lifecycle / death-point** contradictions. None is a
possession or position contradiction; the gate evidence states plainly that
possession "was sufficiently fixed by FR-519." The FR may build only what a witness
demands. The following blockers must be resolved in a redraft before code.

**B0 — The premise is false: the signal already exists. This is the director's
job, not a new module's (supersedes B1–B5's "build a pure module" framing).** The
FR's Problem section claims "there is no turn-grained record of who held what at
turn N for the next turn to consult." The 10022-BC director trace disproves this.
The director (`turn_direct.yaml`) runs **every turn** (`invoke_turn`: map → direct
→ recap) and is already instructed to flag, in its `continuity` field, "a character
… already lost/seized reappearing" and lifecycle breaches. On 10022-BC Ch3 it
**detected the Arnulf contradiction on 8 of 16 turns**, verbatim: *"Arnulf acts
after being swept away and disappeared; he cannot physically grab the bank edge or
haul himself onto firmer ground"* (t3), repeated t2,4,6,7,8,10,16. The detection is
not missing — it is **precise and per-turn**. The defect is that
`turn_ops.running_scene` (the turn-N+1 context builder) threads the prior **recaps**
but **not** the prior turn's director `continuity`/`steer` flags, so the cast's
intent map and the recap are regenerated with no knowledge of the warning, propose
Arnulf acting again, and the director re-flags it — an advisory with no feedback and
no gate. This is the Scripture's `detection_without_enforcement` trap: *"lint
without gate = advisory."* The redraft must therefore choose the **wiring** fix, not
a new pure-memory module:

- **B0-a (feed-forward, cheapest):** thread the prior turn's `continuity` (and the
  death-relevant `steer`) into `running_scene` so turn N+1's intent map + recap are
  generated **knowing** the flag. No new extraction boundary — the director already
  extracts — which **dissolves B2 entirely**. This is the minimal change and the
  first thing to try.
- **B0-b (escalate, if feed-forward is insufficient):** when a `continuity` flag
  for the same actor **repeats ≥K turns**, deterministically drop that actor from
  the turn's roster, reusing the existing `_filter_roster_for_lifecycle` /
  `build_allowed_scene_cast` machinery that already does exactly this for the
  chapter-open lifecycle gate. No new module; an existing gate extended one rung.

A new `positional_memory.py` is only justified if B0-a **and** B0-b are tried and a
witnessed contradiction still survives. Default: there is no new module. The death-
token widening (10022-BC evidence #1) still applies — but as input to the director's
existing lifecycle awareness and the warn-only detector, not to a new memory layer.

The blockers below stand as the contract **if** a residual after B0 proves a module
is needed; otherwise they are moot once B0-a/B0-b clear the witnesses.

**B1 — Re-scope to the lifecycle lane; drop the unwitnessed possession/position
lanes.** The title ("Positional Working Memory"), Summary, Value Statement, Scope,
and gate condition #2 all describe an `inventory`/`objects`/`location` working
memory whose drop-then-use object continuity and named-position moves have **no
witness** — and whose gate condition (#2, "a turn-to-turn possession/position
contradiction") is **contradicted by its own evidence**. Per the FR's no-speculative-
build discipline, those lanes must be removed (closed as not-needed, decision
recorded). What remains is a chapter-lived, turn-grained **lifecycle** memory: it
records the **death-turn index** so `running_scene` at turn N+1 knows a character
died at turn N. Retitle the FR away from "Positional."

**B2 — Pin the death-turn extraction boundary (supersedes prior C2).** The death-turn
index is recorded nowhere today: `world_state` is a chapter snapshot, and the seam
gives only chapter-grain status. `update(memory, recap)` must extract "X died at
turn N" from recap prose — a fallible FR-513-class prose→structured boundary. The
redraft must pin the mechanism (deterministic token match reusing the widened
death-token set, vs. a small structured LLM step), require it to be **grounded** (no
death asserted without recap evidence), and test it against the concrete 10022-BC
Ch3 recap as the first fixture.

**B3 — The `missing_presumed_dead` widening must not bar a legitimate return.**
Widening the death-token set changes `dead_character_names` everywhere it is used
(final_cut before/within partition + the warn-only detector). The redraft must keep
the death-point **chapter-scoped** so a presumed-dead character who returns (Arnulf
ch6, the synopsis resurrection) is not permanently barred. Test: Arnulf may act in
ch6 even though ch3 marked him `missing_presumed_dead`. This is the hazard that
makes a blunt status-filter widening dangerous — the same state names both "dead for
now" and "about to return."

**B4 — Running-turn enforcement is preventive, not raising.** FR-519 made
within-chapter enforcement warn-only precisely because raising breaks beat-fidelity
when the played arc itself has post-death action (Hagan turns 11–16). Extending the
signal to `running_scene` must **inject the death-point constraint into the turn
prompt** (so turn N+1 is generated knowing X is dead), not raise on an
already-generated turn — which would dead-end play. The redraft must state the
enforcement mode and keep play non-blocking.

**B5 — Drop the fold/lane-floor interaction unless a persistent write survives
(subsumes prior C3).** If the lifecycle lane only gates turn prompts and writes
nothing to `world_state` (the chapter-end status is already authoritative), say so
explicitly and delete the `fold(memory) -> ledger_overlay` step and its FR-514
lane-floor precedence question. Only if the redraft proves a persistent write is
needed does the C3 precedence rule re-apply. Default: no fold, no floor conflict.

Granted on redraft satisfying B1–B5. The redraft must carry the 10022-BC Ch3
(presumed-dead-fires) and Ch8 (post-death running turn) cases plus the 10021-BC ch6
(within-chapter death) case as its first three fixtures, and must not introduce the
possession/position lanes that no witness justifies.

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
    (object handovers, position moves, **lifecycle transitions incl.
    `missing_presumed_dead`**) at the boundary where the recap is committed.
  - `fold(memory) -> ledger_overlay` — collapse the chapter's working memory into
    the persistent `world_state` lanes at `close_chapter`.
- **Widen the death-token set to include `missing_presumed_dead`** (10022-BC
  evidence #1): the turn-grained death-point signal must fire on the presumed-dead
  state the synopsis resurrection arc rides on, not only `dead`/`confirmed_dead`.
  This is the single status-vocabulary fix that unblocks the headline Ch3 class.
- Wiring: `turn_ops.running_scene` **consults** the working memory for turn N+1's
  context **and applies the within-chapter death-point constraint to running turns**
  (10022-BC evidence #2 — Ch8 proves a clean final cut is insufficient when the
  contradiction lives in the chapter body); `chapter_ops.close_chapter` **folds**
  it; nothing persists it beyond the chapter (mirroring FR-492's no-stored-book
  rule).

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
- [ ] Unit test: a `missing_presumed_dead` transition fires the death-point signal
      (10022-BC Ch3 fixture) — the presumed-dead state is not excluded the way
      `_DEAD_STATUS_TOKENS` excluded it.
- [ ] Unit test: a post-death action in a **running turn** (not the final cut) is
      caught (10022-BC Ch8 fixture — "Arnulf lunged" mid-chapter after
      `confirmed_dead`).
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
  `chapter_ops.close_chapter` (fold); `_DEAD_STATUS_TOKENS` (the set to widen for
  `missing_presumed_dead`), `dead_character_names` (the death-point source).
- Evidence: `outputs/dungeon-master/10021-BC/{story.json,review.md}` (Hagan ch6
  within-chapter residual); `outputs/dungeon-master/10022-BC/{story.json,review.md}`
  (Arnulf arc — presumed-dead filter gap + running-turn escape, LangSmith-confirmed
  in `logs/10022-ls2.log`).
