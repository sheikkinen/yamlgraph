# Feature Request: FR-519 - DM v2 Intra-Chapter Prose-vs-State Enforcement (Phase 1)

**Priority:** HIGH
**Type:** Bug / Enforcement Hardening
**Status:** Enforced — Phase 1 landed; witness triggered the FR-520 Phase-2 gate
**Effort:** ~1-2 days
**Requested:** 2026-06-18

## Summary

Stop a chapter's final prose from contradicting the chapter's **own committed
`world_state`** — a character who dies in paragraph 2 still acting in paragraph 8,
or a character using an object the prose just showed them lose. The ledger already
holds the correct facts (lifecycle status, `inventory`, `objects.holder`) and they
are *internally consistent at chapter grain*; nothing threads them into the
final-cut prompt as a constraint. This FR is **Phase 1: enforcement-first** — it
reads only the existing per-chapter ledger and injects it into `final_cut_context`
→ `final_cut.yaml` as a hard constraint, with warn-only post-generation validation.
The turn-grained **working memory** that catches contradictions which reconcile
back to the chapter-end snapshot is the separate **Phase 2 (FR-520)**, gated on
this FR's witness.

## Value Statement

A reader never sees a character killed mid-chapter keep fighting, nor use a weapon
the prose just had them drop — the two most jarring continuity breaks a critic
flags, fixed at the one seam (the final cut) that sees the whole chapter at once.

## Judgement

Decision: **Granted on redraft.** The bug is real, the seam (final cut) is the
right one, and the two contradiction classes share one mechanism. One blocker (B1)
is a genuine internal inconsistency that must be fixed before enforce; the rest of
scope is frozen as written.

**B1 (must-fix) — the proposed data source does not exist at final-cut time.**
Proposed Solution #1 and #2 both read `_chapter_card(doc, cid).get("world_state")`.
Verified against `chapter_ops.close_chapter`: the chapter's own `world_state` is
**not committed to the doc** when `invoke_final_cut` runs — the adapter writes it
*after* `close_chapter` returns. So that read yields the stale/empty prior card,
and within-chapter deaths/possession would be invisible — the exact "boundary too
late" failure this FR names, reproduced in the fix.
*Resolution (frozen):* the data **does** exist one local variable away. In
`close_chapter`, the close-graph output `closed` (computed before `invoke_final_cut`)
already carries `closed["world_state"].characters` (with `status=dead`) and
`closed["seam_packet"].character_lifecycle` (within-chapter deaths, `source_chapter
== cid`). The redraft must **thread `closed` into `final_cut_context` /
`invoke_final_cut`** as the within-chapter-death source — not read the doc card.
Possession facts must source from the **inherited ledger**
(`turn_ops.inherited_world_state(doc, cid)`, already available and persistent),
optionally overlaid with `closed`'s emitted lanes.

**B2 (resolved) — reuse the existing revise pipeline, do not duplicate.**
`close_chapter` already runs FR-510's `_collect_dead_character_prose_violations` +
`_revise_final_cut_once` against a `dead_names` list built from the prior seam.
The death half is therefore a **small extension**: widen that `dead_names` to the
union (prior seam ∪ `closed` within-chapter deaths) so both the prompt injection
and the existing validation/revise see within-chapter deaths. No new revise loop.

**B3 (resolved) — within-chapter dead stay in `allowed_cast`.** A character who
dies mid-chapter acts legitimately *before* death, so they must remain in
`build_allowed_scene_cast` (which gates who may appear at all). The new constraint
forbids only post-death action, never presence. The redraft must not remove them
from the allowed cast.

**B4 (resolved, mandatory posture) — possession enforcement is warn-only because
the lane floor can manufacture false positives.** FR-514's `apply_lane_floor`
carries an emptied `inventory`/`objects` lane forward unchanged. A chapter that
legitimately disarms a character but emits an empty lane will floor the old
possession forward, and a possession constraint would then wrongly forbid the
legitimate change in the *next* chapter. This FR's warn-only commitment is therefore
**not optional** for the possession half — block is forbidden until the
false-positive rate (driven by floored lanes) is measured. The death half inherits
FR-510's existing revise-and-raise behavior unchanged (it predates this FR).

Grant scope notes:
- The `final_cut.yaml` rename (`dead_characters` → `dead_before_open` +
  `dead_within_chapter`) is permitted (single consumer); the existing passive-legacy
  allowance ("the fallen staff") is preserved for both blocks.
- Helper name in the sketch is illustrative; the existing normalizer is
  `_norm_name` (`turn_ops.py`), reuse it rather than introducing `_norm`.
- Acceptance criteria stand; add one: a within-chapter-dead character remains in
  `allowed_cast` and is only forbidden post-death action (B3 regression guard).

## Problem

Two contradiction classes share a single root cause and a single cheap fix:

### A. Intra-chapter death (lifecycle)

FR-510 excludes `confirmed_dead` characters from a chapter's final cut, but derives
the list from the **inherited (prior-chapter)** seam packet only:

```python
prior_seam = parse_seam_packet(inherited_seam_packet(doc, cid))
dead = [... if existence_state == "confirmed_dead" ...]
```

This blocks a character already dead at chapter open (the cross-chapter case). It
does **nothing** for a character who dies *during* the chapter, because the death
is recorded in chapter `cid`'s **own closing** seam (`source_chapter == cid`),
produced by `close_chapter` *after* the prose is written — a boundary too late to
guard the prose that contradicts it. For the **last** chapter there is no next
chapter, so the signal is never consumed at all.

### B. Possession contradictions the ledger already disproves

The persistent ledger holds the correct possession truth across the whole book,
and the prose contradicts it within a chapter:

- Hilde's `weapon`: held in **every** chapter 1→6, never dropped. Ch2 prose "drove
  her own weapon into the mud … freeing both hands" — a transient beat the ledger
  correctly ignored, then never reconciled.
- Hagan's `ritual staff`: `holder='Hagan'` in **every** chapter 1→6. Ch6 prose has
  Reinmar "kick it farther off the track," then Hagan keeps thrusting it.

Both are the same **enforcement** gap: the chapter's committed `world_state`
(lifecycle status + `inventory` + `objects.holder`) is never handed to the
final-cut model as a constraint. This is a composition bug — every component is
individually correct (the death is detected, the ledger stores `status=dead` and
`inv=['weapon']`), but the committed state never reaches the prose seam.

> Not in scope (recorded so it is not mistaken for a memory failure): the review's
> **spatial-geography vagueness** (Ch1/Ch3/Ch5 — "where is everyone relative to the
> bank?", "same chokepoint or different points?") is prose being *vague*, not
> *contradicting state*. No constraint injection can author clarity; that is
> prompt-craft, addressed separately.

## Evidence

**Run 10021-BC** (`outputs/dungeon-master/10021-BC`). Book reviewer Continuity **1/5**.

Death (chapter 6): the reviewer's headline finding —
> Hagan is killed mid-chapter … yet continues to appear and act after his death
> multiple times … and finally 'Hagan, already dead, dragged a bloodied hand
> across the settlement edge'.

`story.json` proves the system *knew*: `chapters.cards["6"].world_state.characters`
has `Hagan … status=dead`; the closing seam records
`Hagan: existence=confirmed_dead, source_chapter=6`.

Possession: `chapters.cards[*].world_state` shows `Hilde inv=['weapon']` and
`ritual staff holder='Hagan'` in **every** chapter 1→6 — the correct persistent
facts the Ch2/Ch6 prose flips and the reviewer cites.

## Scope

In scope:
- **Death (union the sources):** derive the final-cut exclusion from the
  inherited seam **union** the chapter's own committed death signals
  (`world_state.characters` dead status and/or `character_lifecycle`
  `source_chapter == cid`). Distinguish "already dead at open" (never appears)
  from "dies within this chapter" (acts up to death, never after).
- **Possession:** derive a constraint from the chapter's committed
  `inventory` + `objects.holder` and inject it so the model is told who holds what
  through the chapter; an object changes hands only if the narration shows the
  handover and the new holder keeps it.
- Both injected into `final_cut_context` → `final_cut.yaml`, Jinja-guarded
  (empty string suppresses the block, per FR-510 B3).
- Warn-only post-generation validation: typed logs
  (`DEAD_CHARACTER_ACTS_POST_DEATH`, `OBJECT_USED_AFTER_LOSS`); no raise.
- Witness rerun of 10021-BC: Hagan acts up to his death, never after; the
  weapon-in-mud / staff-kicked findings clear **or** are shown to require FR-520.

Out of scope:
- Any **new persisted state** or turn-grained working memory — that is FR-520
  (Phase 2). Phase 1 reads only the existing ledger.
- Blocking (raise) on violation — keep FR-510's measure-first posture; promote to
  a gate only once false-positive rate is measured.
- Spatial-geography vagueness (prose craft, not state).
- Resurrection / ghost semantics (Arnulf returns *alive*; unaffected).
- Rewriting the director/recap graph or the final-cut graph schema.

## Proposed Solution

### 1) Union the death sources in `final_cut_context`

```python
def _dead_in_chapter(doc: dict, cid: str) -> tuple[list[str], list[str]]:
    """(before_open, within_chapter) confirmed-dead names for chapter cid."""
    prior = parse_seam_packet(inherited_seam_packet(doc, cid))
    before = {
        _norm(i.get("name"))
        for i in (prior.get("character_lifecycle") or [])
        if str(i.get("existence_state")).strip() == "confirmed_dead"
    }
    ws = parse_world_state(_chapter_card(doc, cid).get("world_state"))
    within = {
        _norm(c.get("name"))
        for c in ws.get("characters", [])
        if str(c.get("status", "")).strip().lower() in {"dead", "slain", "killed"}
    } - before
    return sorted(n for n in before if n), sorted(n for n in within if n)
```

### 2) Possession constraint from the committed ledger

```python
def _possession_facts(doc: dict, cid: str) -> str:
    ws = parse_world_state(_chapter_card(doc, cid).get("world_state"))
    lines = [
        f"{c['name']} holds: {', '.join(i for i in c.get('inventory', []) if str(i).strip())}"
        for c in ws.get("characters", [])
        if [i for i in c.get("inventory", []) if str(i).strip()]
    ]
    lines += [
        f"the {o['name']} is held by {o['holder']}"
        for o in ws.get("objects", []) if o.get("holder")
    ]
    return "\n".join(lines)
```

### 3) `final_cut.yaml` — three Jinja-guarded blocks

```jinja
{% if dead_before_open %}
These characters are already dead and must not appear, speak, or act:
{{ dead_before_open }}
{% endif %}
{% if dead_within_chapter %}
These characters die during this chapter. They may act up to the moment of their
death, but must not speak, move, or act in any way after they are killed:
{{ dead_within_chapter }}
{% endif %}
{% if possession_facts %}
These possession facts hold through this chapter. An object changes hands only if
the narration shows the handover AND the new holder keeps it; never let a character
use an object the prose has just shown them lose:
{{ possession_facts }}
{% endif %}
```

### 4) Warn-only validation

Reuse FR-510's active-role heuristic (8-word window, enumerated passive patterns):
a dead name in an active role after its death point → `DEAD_CHARACTER_ACTS_POST_DEATH`;
a tracked object used after the prose shows its loss → `OBJECT_USED_AFTER_LOSS`.
Typed logs only, no raise.

## Acceptance Criteria

- [ ] `final_cut_context` emits `dead_before_open`, `dead_within_chapter`, and
      `possession_facts` from the chapter's own committed `world_state` (+ inherited
      seam for before-open); all empty strings when nothing applies.
- [ ] `final_cut.yaml` consumes all three behind Jinja guards; empty suppresses
      each block (no prompt change for chapters with no deaths/objects).
- [ ] Unit test: a character marked dead at this chapter's close routes to
      `dead_within_chapter`; a prior-seam confirmed-dead routes to
      `dead_before_open` (FR-510 regression preserved).
- [ ] Unit test: `Hilde inv=['weapon']` yields a "Hilde holds: weapon" line;
      `objects.holder='Hagan'` yields a staff-held-by-Hagan line.
- [ ] Unit test: empty ledger → all three empty, no prompt blocks.
- [ ] Warn-only validation emits the typed logs on post-death action and
      use-after-loss; no raise (FR-510 posture).
- [ ] Witness: regenerate 10021-BC — Hagan never acts after death; the weapon /
      staff findings clear, OR the FR-520 Phase-2 gate is triggered and recorded.
- [ ] Tests added; `docs/architecture.md` §5a / lifecycle note updated.

## Alternatives Considered

- **Gate the turn recaps instead of the final cut.** The director judges turn by
  turn and cannot know a death/loss is coming; the final cut is the first seam with
  whole-chapter view. Recap-level gating is a larger change (future work).
- **Jump straight to a working-memory layer.** Rejected as speculative — the
  evidence shows the persistent facts are *correct and present* but *unenforced*.
  Prove enforcement insufficient (the FR-520 gate) before building turn-grained
  state (Scripture: kill the cheapest bug; do not over-engineer).
- **Promote to a blocking gate now.** Rejected to preserve FR-510's measure-first
  discipline.

## Implementation

Landed per the frozen judgement; the redraft followed B1 exactly.

**B1 resolution (as built).** `final_cut_context(doc, cid, closed=None)` and
`invoke_final_cut(..., closed=None)` now take the close-graph output `closed`.
`close_chapter` threads it (`invoke_final_cut(doc, cid, closed=closed)` and through
`_revise_final_cut_once`). Within-chapter deaths come from `closed` (its
`world_state` dead-status characters ∪ its closing seam `character_lifecycle`);
possession comes from `inherited_world_state(doc, cid)` overlaid with `closed`'s
emitted lanes. The chapter's own committed `world_state` is never read back (it
does not exist at final-cut time) — exactly the boundary the judge flagged.

**New `turn_ops` surface.** `dead_character_names(doc, cid, closed) ->
(before_open, within_chapter)` (public, reused by the warn path) and
`_possession_facts(doc, cid, closed)`. `final_cut_context` now emits
`dead_before_open`, `dead_within_chapter`, `possession_facts` (each `""` when
empty), plus the unchanged `allowed_cast`.

**Prompt + graph contract.** `prompts/final_cut.yaml` splits the old
`dead_characters` block into `dead_before_open` (never appears) +
`dead_within_chapter` (acts up to death only) and adds a `possession_facts` block;
the passive-legacy allowance ("the fallen staff") is preserved. **The graph
`final_cut.yaml` had to declare the three new keys in both `state:` and the node
`variables:`** — the unit tests (which mock `invoke_final_cut`) could not catch
this; the witness run did (the prompt raised `Missing required variable(s)` until
the graph state schema was widened). A graph state key is a contract, not an
implicit pass-through (boundary: `module_structure`).

**Deviation from B2 (recorded).** B2 asked to widen FR-510's raising `dead_names`
to include within-chapter deaths. Implementing that literally breaks B3: FR-510's
blanket active-role detector flags *every* appearance of a dead name, so a
within-chapter-dead character's **legitimate pre-death action** would be flagged
and would trigger revise-and-raise on valid prose — the death point cannot be
located in prose mechanically. Resolved toward safety: the **before-open** class
keeps FR-510's revise-and-raise unchanged; the **within-chapter** class is
**warn-only** (`DEAD_CHARACTER_ACTS_POST_DEATH`, a coarse upper bound that also
counts legitimate pre-death action). This honours B3 + B4's measure-first posture.
Possession is warn-only (`OBJECT_USED_AFTER_LOSS`) per B4. Diagnostics live in
`_log_intra_chapter_continuity`; neither raises.

**Tests.** `tests/test_dead_character_prose.py` extended: dead-source routing
(within vs before-open), context threading from `closed`, possession lines from
the inherited ledger, first-chapter empties, and `detect_object_use_after_loss`
hit/no-hit. The two renamed-key tests updated. `tests/test_final_cut_revise_cycle.py`
stubs updated for the new `closed` kwarg. Full DM suite: **196 passed**.

**Witness — FR-520 gate TRIGGERED.** Re-closed chapter 6 of `10021-BC` under the
new constraints (`logs/fr519-witness.log`, `tmp/fr519_ch6_new.txt`). Result:
- The constraint **reaches the model** and the warn diagnostics fire as designed.
- **Possession improved:** the ritual staff is now handled passively after
  Reinmar kicks it away ("the staff lay out of his reach"); Hagan's attempts to
  *reclaim* it fail rather than succeed — the original "kicked away then thrust"
  contradiction is gone. (The single `OBJECT_USED_AFTER_LOSS` weapon hit is a
  false positive on "the planted weapon" — Hilde's ground-marker — exactly the
  lane/heuristic noise B4 anticipated; warn-only was the right call.)
- **Within-chapter death NOT resolved:** Hagan still acts after he is struck down
  ("made one last claim … stepping in", "drove the staff down again", "bloodied
  hand dragged across the settlement edge"). The **played arc itself** has Hagan
  acting across turns 11–16 after his death turn; the final-cut prompt cannot
  reconcile it without violating beat-fidelity. This is a genuine turn-to-turn
  contradiction that reconciles to the chapter-end ledger (Hagan `status=dead`).

That residual is the exact entry condition FR-520 was gated on. Phase 1 is
complete and verified; **the FR-520 Phase-2 working-memory gate is now witnessed
open** (turn-grained death-point tracking is required, not more prompt text).

## Related

- **`feature-requests/FR-520-dm-v2-chapter-lived-positional-working-memory.md`** —
  **Phase 2**: the turn-grained working memory, gated on this FR's witness.
- `feature-requests/FR-510-dm-v2-confirmed-dead-prose-exclusion.md` (cross-chapter
  exclusion; this FR closes the same-chapter gap it left open).
- `feature-requests/FR-507`/`FR-509` (the lifecycle gate + cast filter).
- `feature-requests/FR-513..518` (the relationship ledger-as-memory arc; this FR is
  the *physical-state* enforcement analogue).
- `examples/dungeon_master/api/turn_ops.py` — `final_cut_context`, `invoke_final_cut`.
- `examples/dungeon_master/api/world_state.py` — `Character.status/inventory`,
  `WorldObject.holder`.
- `examples/dungeon_master/prompts/final_cut.yaml`.
- Evidence: `outputs/dungeon-master/10021-BC/{review.md,story.json}` (Continuity 1/5;
  Hagan `status=dead`, `Hilde inv=['weapon']`, staff `holder='Hagan'` all chapters).
