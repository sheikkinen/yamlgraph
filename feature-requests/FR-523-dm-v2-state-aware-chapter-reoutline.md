# Feature Request: FR-523 — DM v2: State-Aware Chapter Re-Outline (Kill the Seam Teleport in the Spec)

**Priority:** HIGH
**Type:** Bug (continuity defect, authored at planning time)
**Status:** Proposed
**Effort:** ~1 day
**Requested:** 2026-06-18

## Summary

The chapter outliner writes every chapter's beats from the **synopsis alone**,
blind to the physical end-state the prior chapter actually carried forward. When a
beat removes an actor by an environmental hazard (swept away / drowned / lost) but
the carried `world_state` places that actor at a non-hazard position and **no beat
moves them into reach first**, the generator must silently teleport the actor to
satisfy the beat. The director is then blamed at play time for a contradiction the
**planner** authored. This FR makes the next chapter's outline **state-aware**:
re-outline an unplayed chapter against the prior chapter's committed
`world_state` + `seam_packet`, so the planner can author the bridging beat the death
requires — killing the bug in the spec rather than patching the symptom in prose.

## Value Statement

A reader stops hitting "Arnulf was safe on the higher bank last chapter, why is he
suddenly swept away with no transition?" — every lethal/exit beat becomes physically
continuous with the position the story actually left the actor in.

## Problem

Forensic root cause (proven, not hypothesized — see FR-522 witness + the RED proof
in `tests/test_seam_precondition_gap.py`):

- `chapter_ops.outline_chapters(doc)` invokes the outline graph with **only**
  `{"synopsis": synopsis, "outline": {}}`. It is **state-blind**.
- `doc_ops.expand_chapters()` outlines **all** chapters up-front at derivation time,
  before any chapter is played. Beats are **never** revised once a chapter has run,
  so the outline cannot see what the previous chapter committed.
- The contradiction is therefore **authored at planning time** and only **manifests
  at generation time**. In `10023-BC`:
  - Ch2 close carried Arnulf `status=alive, location="on the higher bank with the
    retreating Aschenwulf line"` (a SAFE/HIGH position, plus a must-carry fact).
  - Ch3 `beats[0] = "Arnulf is swept away by the flood"` — a death that requires him
    **at the water**. No bridging beat moved him there.
  - The generator silently teleported him from the safe high bank into the flood;
    the reviewer scored Continuity 1/5 and blamed the play layer.

**This is distinct from the FR-519/520/521 family.** Those cured *unplanned
re-animation* (a dead/exited actor acting again) by **option removal** — roster-drop,
forward-fed continuity. This bug is the opposite failure wearing the same costume: a
*planned* transition (the synopsis genuinely intends Arnulf to be lost to the flood
and return changed near the end) that is **physically discontinuous** because the
death needs a position the carried state forbids and nothing bridges the two. Option
removal cannot fix it — the exit is supposed to happen; what is missing is the
**bridge beat**. The cure must therefore **add** an authoring input (carried state),
not remove an option.

**The One Law (Scripture `the_one_law`).** Normalize at the boundary where data
enters — the **outliner** — not downstream where it manifests (the director, the
prose). The cheapest bug is the one killed in the spec (`spec_kill`). Today the spec
(the beats) is authored against a stale world model; this FR feeds the real world
model into the spec author.

### Condemning evidence (RED, already committed-ready)

`examples/dungeon_master/api/witness_metrics.py::seam_precondition_gap(doc, cid)` is
a pure, deterministic witness: for each actor the prior chapter carried forward alive
and located, it flags the first hazard-exit beat that names them when no beat
repositions them toward the hazard first (or within the exit beat itself). On the
real `10023-BC` doc it fires exactly on the forensic finding:

```
CH3: GAP actor='Arnulf'
     carried='on the higher bank with the retreating Aschenwulf line'
     beat='Arnulf is swept away by the flood'
```

The fixture `tests/test_seam_precondition_gap.py` proves the bug deterministically
(`gap_count == 1`) and proves that **a single bridging reposition beat clears it**
(`gap_count == 0`). That zero-gap state is this FR's GREEN target.

## Proposed Solution

Make the **next unplayed chapter** re-outline itself against the **committed end-state
of the chapter just finished**, so the outline LLM authors beats that are physically
continuous with where the story actually is.

### Boundary of the change

- **Layer:** logic/planning (`chapter_ops` + the `chapter_outline` graph/prompt).
  No change to the director, `running_scene`, or the turn loop — those are
  downstream and must stay innocent of this fix.
- **Trigger:** after `close_chapter(doc, cid)` commits `world_state` + `seam_packet`,
  re-outline chapter `cid+1` (if it exists and is unplayed) from the synopsis **plus**
  that committed state. The up-front `expand_chapters()` outline becomes a *draft*;
  the just-in-time re-outline is the *authoritative* beats for the chapter about to
  play. (Idempotent: re-outlining an already-played chapter is forbidden.)

### Prompt / graph change

Extend `prompts/chapter_outline.yaml` + `chapter_outline.yaml` to accept and
interpolate the inherited physical state:

```yaml
# chapter_outline graph state (new inputs)
inputs:
  synopsis: { ... }          # unchanged
  prior_world_state: {}      # NEW: committed characters/objects/facts of chapter cid
  prior_seam_packet: {}      # NEW: character_lifecycle of chapter cid
  chapter_index: 0           # NEW: which chapter is being (re)outlined
```

The prompt gains a hard instruction (paraphrased):

> Each beat must be physically continuous with the carried positions below. If a beat
> removes a character by an environmental hazard, an **earlier beat (or the same
> beat) must first move that character from their carried position into reach of the
> hazard.** Never place a character somewhere the carried state contradicts without a
> beat that moves them there.

### `chapter_ops` change

```python
def reoutline_next_chapter(doc: dict, played_cid: str) -> dict:
    """After played_cid closes, re-author the next chapter's beats from synopsis +
    the committed world_state/seam_packet of played_cid. No-op if there is no next
    chapter or the next chapter has already played."""
    ...
```

Invoked from the play/close path (where `close_chapter` is already called), not from
`expand_chapters` (which stays the up-front draft).

## Acceptance Criteria

- [ ] **AC-1 (witness, primary).** `seam_precondition_gap(doc, cid)` reports
  `gap_count == 0` for every chapter of a freshly generated Floodmark book where the
  prior version (e.g. `10023-BC`) reported a gap — the Ch3 Arnulf gap in particular
  must be **absent**, with a visible bridging beat naming Arnulf moving toward the
  water before the swept-away beat.
- [ ] **AC-2 (unit, planning-layer).** `reoutline_next_chapter` re-authors the next
  chapter's beats from synopsis + prior committed state; given a fixture where the
  prior chapter carried an actor safe + high and the synopsis demands their drowning,
  the re-outlined beats contain a reposition beat for that actor **before** any
  hazard-exit beat (asserted via `seam_precondition_gap == 0` on the re-outlined doc,
  mocked outline LLM).
- [ ] **AC-3 (idempotence / isolation).** Re-outlining is a no-op when there is no
  next chapter or the next chapter has already played; played chapters' beats are
  never mutated. Prior chapters byte-identical.
- [ ] **AC-4 (no downstream change).** Director, `running_scene`, turn loop, and
  FR-521 roster-drop are untouched; their tests stay green.
- [ ] **AC-5 (regime).** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, **no** `req:`.
- [ ] **AC-6 (live corroboration).** A regenerated Floodmark book reviewed by
  `book_reviewer`; the Ch2→Ch3 Arnulf seam no longer scores a continuity break for an
  unbridged position teleport (corroboration, not a gate — FR-522 instrument posture).
- [ ] Tests added (RED `test_seam_precondition_gap.py` already present; GREEN adds the
  `reoutline_next_chapter` planning tests).
- [ ] `architecture.md` updated: outline becomes a draft + just-in-time state-aware
  re-outline; the seam-gap witness documented.

## Alternatives Considered

- **Fix B — planned-events lane.** Parse the synopsis into discrete planned events
  with physical preconditions and gate beats against them. Stronger and more general
  than Fix A, but materially larger (a new synopsis-derived artifact + a gate). Can
  *seed* Fix A later; not required to kill this seam. Deferred.
- **Fix C — soften carried positions.** Make the prior chapter commit looser
  positions so the next chapter has freedom. **Rejected:** it breaks the very
  positional-memory guarantee FR-520 established (weapon/staff/who-holds-the-ledge
  continuity); it would trade one continuity class for another.
- **Fix D — director reposition / bridge-beat-at-play-time.** Let the director insert
  a bridging move when it detects a precondition gap. Smaller, but it normalizes
  **downstream** (the director patching the planner's contradiction at run time) —
  exactly the boundary violation the One Law forbids. Acceptable only as a stopgap;
  Fix A removes the need for it.
- **Option removal (the FR-519/521 reflex).** Cannot apply: the exit is *planned*.
  Removing the option deletes an intended arc beat rather than making it continuous.

## Related

- `examples/dungeon_master/api/witness_metrics.py` — `seam_precondition_gap` (RED witness)
- `examples/dungeon_master/tests/test_seam_precondition_gap.py` — condemning fixture (RED proof)
- `examples/dungeon_master/api/chapter_ops.py` — `outline_chapters` (state-blind, the bug site)
- `examples/dungeon_master/api/doc_ops.py` — `expand_chapters` (up-front outline)
- `examples/dungeon_master/chapter_outline.yaml`, `prompts/chapter_outline.yaml` — outline graph/prompt
- FR-520 (positional working memory), FR-521 (forward-fed continuity), FR-522 (replay witness) — the continuity arc this completes
- `outputs/dungeon-master/10023-BC/story.json` — the offending artifact; `review.md` Continuity 1/5
- Scripture: `the_one_law`, `spec_kill`, `downstream_fix`, `boundary: schema/state`
