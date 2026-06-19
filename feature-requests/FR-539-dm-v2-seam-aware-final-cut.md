# Feature Request: DM v2 Seam-Aware Final Cut (Entrance Manifest + Prior-Prose Bridge)

**Priority:** HIGH (closes the seam-entrance gap FR-537 exposed, FR-538 measures)
**Type:** Feature
**Status:** Proposed (depends on FR-538 landing first)
**Effort:** ~1.5 days
**Requested:** 2026-06-19

## Summary

The chapter narrator already exists — the **Final Cut** (`final_cut.invoke_final_cut`,
FR-492) re-narrates each played chapter into one continuous passage. But it composes each
chapter **blind to its neighbours**: it sees its own recaps + the inherited `world_state`
ledger + the typed `seam_packet`, never the *prose* of the adjacent chapter. That blindness is
the seam-entrance gap — a character correctly off-page in chapter N (FR-537 scoping) enters N+1
with no narrated arrival. This FR gives the existing narrator the two things it provably lacks,
**at the close boundary it already owns**:

1. **S0 — a typed `cast_entrances` manifest** (`new` / `returning` / `continuing`, derived
   from the FR-537 scoped-cast delta) telling the Final Cut who must be *established* this
   chapter.
2. **S1 — the tail of the prior chapter's final text** fed into this chapter's Final Cut, so
   the bridge is written from the prose the reader actually last saw, not reconstructed from a
   packet.

No new node, no new prose authority, no turn-level change.

## Value Statement

A character who was deliberately off-page now arrives *on the page* — the narrator opens the
chapter by establishing how each entrant comes to be present, grounded in where the previous
chapter left them — turning FR-537's clean two-handers from a source of unbridged entrances
into properly staged scenes.

## Problem

`close_chapter` → `final_cut.invoke_final_cut` composes a chapter from:
- this chapter's recaps (`turn_state.chapter_recaps_text`),
- the inherited `world_state` ledger (`format_world_state`),
- the typed `seam_packet` (`resolved_events` / `open_threads` / `must_carry_facts` /
  `opening_constraints` / `character_lifecycle`).

None of these is the **neighbouring chapter's prose**. So when FR-537 scoping makes chapter N a
two-hander, the ledger still lists the off-page actor as present-and-located; chapter N+1's
Final Cut opens treating them as continuously on-stage and never stages an entrance. 10028-BC
Ch3 (Arnulf) is exactly this: locally each Final Cut is correct, but the seam between them is
authored by neither.

We model **exits** (within-chapter `cast_exits` benches an actor; `close_chapter` records it;
`seam_precondition_gap` checks lethal exits) but not **entrances**. Restore the symmetry.

## Judgement (2026-06-19)

Conditionally approved; revised to the scope below. Resolutions applied:

- **Manifest is a candidate set, never a gate (paired B1 with FR-538).** The `cast_entrances`
  manifest is the **scope-delta candidate** set — who the narrator *should* stage. FR-538's
  witness measures the **prose outcome** — who actually arrived on the page. These are
  deliberately different lenses and will differ (a scoped entrant may never surface in prose;
  a prose name may be out of scope). The manifest **feeds the narrator**; it must **never**
  subtract from FR-538's gap set. Success = the gap drops because the Final Cut *prose* now
  stages the entrant, observable without reading the manifest. Listing a name is not bridging
  a seam (`gate_checks_shape_not_substance`).
- **R2 — bound the ledger slice.** `last_status`/`last_location` is the *motivated* slice of
  FR-537's deferred ledger-render step: surface only the **entrant's own** inherited-ledger
  row (already available in `close_chapter` as `inherited_world_state`), char-bounded like the
  seam packet — not a general ledger-scoping change.
- **R3 — prior prose must be committed, not read uncommitted.** Both `on_page(prev)` and the
  S1 tail read `prev_card["text"]`, set by `doc_ops.apply_chapter_close` *after*
  `close_chapter` returns. Chapters close in order, so the prior chapter's `text` is committed
  before `cid`'s Final Cut runs — assert this invariant explicitly (echoing the FR-519 B1
  "passed not read back" hazard); never read an uncommitted neighbour.

## Proposed Solution

Both changes land in `close_chapter` / `final_cut` — the boundary that already owns chapter
prose. Gated by the FR-538 `seam_entrance_gap` detector as the red test.

### S0 — derive a typed `cast_entrances` manifest at close

```python
# chapter_open or a new seam leaf — pure, derived, NOT authored
def derive_cast_entrances(doc: dict, cid: str) -> list[dict]:
    """Characters entering chapter ``cid`` vs the prior chapter's scoped cast.

    entering = resolve_chapter_cast(cid) − on_page(prev)
    kind: never on-page in 1..prev → 'new'; has lifecycle absence → 'returning';
          else → 'continuing'.
    Returns [{name, kind, last_seen_chapter, last_status, last_location}].
    """
```

- Source of "entering": the FR-537 `resolve_chapter_cast(doc, cid)` delta against prior on-page
  presence — **same single resolver**, no parallel cast notion (`false_duplicate` avoided).
  This is the **candidate** set (planning view); FR-538's prose witness is the **outcome** set
  (reality view). They are intentionally different lenses (see Judgement).
- `last_status` / `last_location` come from the **entrant's own row** in the inherited ledger
  (`inherited_world_state` in `close_chapter`), char-bounded — giving the narrator material to
  write the arrival *from* ("Arnulf, last seen holding the rear at the ford…") rather than
  inventing it. Bounded to that one row, not a general ledger-render change (R2).
- Stored on the card as `cast_entrances` and passed to the Final Cut as narrator **input**. It
  is **not** wired into FR-538's gap formula — the gap drops only when the resulting *prose*
  stages the entrant (B1). A manifest entry never suppresses a gap.

### S1 — feed the prior chapter's closing prose into the Final Cut

Pass a bounded **tail** of chapter N's final `text` (last ~1–2 paragraphs, char-capped like the
seam packet fields) into chapter N+1's `final_cut.invoke_final_cut` as an explicit
`PREVIOUS CHAPTER — HOW IT ENDED` context block, alongside the new `ENTERING THIS CHAPTER`
manifest. The Final Cut prompt is instructed to **open by establishing each entrant**, bridging
from where the prior prose left off.

```text
PREVIOUS CHAPTER — HOW IT ENDED (the prose the reader just finished):
{prior_tail}

ENTERING THIS CHAPTER — establish how each arrives before they act:
- Arnulf (continuing) — last seen: Ch2, holding the rear at the ford
- Reinmar (new) — not seen before; introduce him
```

### Boundaries / invariants

- **Additive:** empty entrances + absent prior tail (chapter 1) reproduce today's Final Cut.
- **Derived, not authored:** `kind` and the manifest are computed at the close boundary; no new
  LLM-authored field, no reoutline dependency.
- **Single resolver:** entrances reuse `resolve_chapter_cast`; the manifest is the *delta*, not
  a second cast computation.
- **No turn-level change:** the per-turn engine (map → director → recap) is untouched;
  establishment is composition work, owned by the Final Cut, not the director.

## Acceptance Criteria

- [ ] `derive_cast_entrances(doc, cid)` returns the documented shape; entering set is the
      `resolve_chapter_cast` delta vs prior on-page presence (single resolver, no duplicate).
- [ ] `kind` ∈ {`new`, `returning`, `continuing`} derived from on-page history + inherited
      `character_lifecycle`; `last_status`/`last_location` read from the **entrant's own**
      inherited-ledger row only, char-bounded (R2).
- [ ] `cast_entrances` is narrator **input** only; it is **not** subtracted from FR-538's
      `seam_entrance_gap` — the gap drops only when the Final Cut *prose* stages the entrant
      (B1). The manifest (candidate set) and the witness (prose outcome) stay separate lenses.
- [ ] `final_cut.invoke_final_cut` receives the bounded prior-chapter prose tail and the
      entrance manifest; the prompt opens by establishing each entrant.
- [ ] Prior tail is char-bounded (seam-packet bounding convention); chapter 1 (no prior)
      composes unchanged. The prior chapter's `text` is asserted committed before `cid`'s
      Final Cut reads it (chapters close in order; never read an uncommitted neighbour — R3).
- [ ] **Red test (FR-538 harness):** a two-chapter fixture whose Ch2 entrant is absent from Ch1
      prose reports a `seam_entrance_gap` before the change. After the change the gap drops to
      **zero because the composed Ch2 prose stages the arrival** (an arrival/reposition signal
      the FR-538 detector finds), **not** because the entrant is listed in `cast_entrances`.
      Since the Final Cut is generative, the establishment assertion runs against a real compose
      (integration-marked); the *deterministic* half asserts `derive_cast_entrances` produces
      the correct candidate manifest + that the manifest reaches the prompt context.
- [ ] **Regression:** a `cast_entrances`-less / prior-tail-less compose reproduces the prior
      Final Cut output shape (additive).
- [ ] **Witness (non-gating):** a fresh `floodmark` book post-change shows `seam_entrance`
      `gap_count` lower than 10028-BC's; reviewer no longer flags the Arnulf-class
      "appears with no prior establishment" break. Visibility, never a CI gate.
- [ ] Requirement tag + capability registry entry, changelog fragment (`type: feat`), diary
      reflection.

## Alternatives Considered

- **A dedicated seam-bridge pass joining two completed Final Cuts (S2).** Rejected as the v1 —
  it introduces a third prose authority and an ordering problem (N+1 isn't composed when N
  closes, so the join needs a second pass over finished chapters). S0+S1 give the existing
  narrator peripheral vision without fragmenting ownership. S2 stays a fallback if S0+S1
  underdeliver.
- **Add a narrator at the first/last *turn* of the engine.** Rejected — the turn engine is the
  interior simulation and its recaps feed the next turn's scene; injecting narration there
  writes the story into its own input. The narrator already lives at the right layer (Final
  Cut); it just needs neighbour context. (This was the initial instinct; reading `close_chapter`
  showed the narrator already exists — a `false_duplicate` averted.)
- **Author entrances at outline time (extend FR-537 `cast`).** Rejected for v1 — bound to the
  deferred reoutline-parity step and LLM-authored; the delta is deterministically derivable at
  close, so no authored field is needed.
- **Scope the ledger render (the deferred FR-537 step) instead.** Subsumed — S0's
  `last_status`/`last_location` is the *motivated* slice of that deferred work: surface the
  entrant's prior row to the narrator, without hiding off-cast context everywhere.

## Related

- [chapter_ops.py](../examples/dungeon_master/api/chapter_ops.py) — `close_chapter`
  (the boundary), `final_cut.invoke_final_cut` call site
- `examples/dungeon_master/api/final_cut.py` — the existing chapter narrator to extend
- [chapter_open.py](../examples/dungeon_master/api/chapter_open.py) — `resolve_chapter_cast`
  (the single cast resolver the entrance delta reuses)
- [seam_packet.py](../examples/dungeon_master/api/seam_packet.py) — `character_lifecycle`
  (the `returning` source) + the char/item bounding convention for the prior-prose tail
- `examples/dungeon_master/prompts/chapter_close.yaml` / the final-cut prompt — open-by-
  establishing-entrants instruction
- **FR-538** (the witness/harness this is gated by) — `seam_entrance_gap`
- **FR-537** (the scoping that exposed the gap; its deferred ledger-render step is partly
  subsumed by S0)
- Distinct from the status/resurrection rail (FR-507/509/510) and the unmodeled
  identity/allegiance rail (10027 Gunnar flip) — both still fire after this lands.
