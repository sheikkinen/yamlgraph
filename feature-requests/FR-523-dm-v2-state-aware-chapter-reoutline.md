# Feature Request: FR-523 — DM v2: State-Aware Chapter Re-Outline (Kill the Seam Teleport in the Spec)

**Priority:** HIGH
**Type:** Bug (continuity defect, authored at planning time)
**Status:** **Enforced (2026-06-18)** — built per the frozen Judgement: new `chapter_reoutline.yaml` graph + prompt (J1), pure `chapter_ops.reoutline_chapter_beats` (J2), the guarded write `doc_ops.reoutline_next_chapter` hooked at the end of `apply_chapter_close` (J3/J7), beats-only (J4). 8 new GREEN tests incl. the non-vacuity negative control (J5) plus the committed RED witness/fixture (f368a770); full DM suite green (226); graph lint clean; `architecture.md` updated. REQ-exempt (J3 regime); not a CI gate (J6 live-regen is corroboration).
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

### Prompt / graph change (J1 — NEW single-chapter graph, not an extension)

The existing `chapter_outline.yaml` is a **whole-book partitioner** ("the chapters in
order must partition the whole synopsis: no gap, no overlap"). A single-chapter
re-outline is a *different contract* and MUST NOT reuse that prompt. Add a new
`graphs`/`prompts` pair `chapter_reoutline.yaml` that re-authors **only the BEATS of
one chapter** given the synopsis, that chapter's frozen title+summary, and the prior
chapter's committed physical state:

```yaml
# chapter_reoutline inputs
synopsis: { ... }          # whole-book context (unchanged source)
chapter_title: ""          # FROZEN — echoed back, never rewritten
chapter_summary: ""        # FROZEN — echoed back, never rewritten
prior_world_state: ""      # committed characters/objects/facts of the prior chapter
prior_seam_packet: {}      # character_lifecycle + must_carry of the prior chapter
```

Output is the SAME shape `outline_chapters` already parses (`_beat_list` /
`_require_beats` reused verbatim): `{ "beats": [ ... ] }`. The prompt gains a hard
instruction (paraphrased):

> Each beat must be physically continuous with the carried positions below. If a beat
> removes a character by an environmental hazard, an **earlier beat (or the same
> beat) must first move that character from their carried position into reach of the
> hazard.** Never place a character somewhere the carried state contradicts without a
> beat that moves them there.

### `chapter_ops` change (J2 — pure, returns beats; the adapter writes)

`chapter_ops` is a declared PURE layer (invoke a graph, return normalized output,
**never** mutate `doc`). The re-outline therefore returns the re-authored beats; the
`doc_ops` adapter writes them — mirroring `outline_chapters` (pure) vs
`expand_chapters` (writes).

```python
async def reoutline_chapter_beats(doc: dict, cid: str) -> list[str]:
    """Re-author chapter ``cid``'s beats from synopsis + frozen title/summary +
    the PRIOR chapter's committed world_state/seam_packet. Pure: invokes
    CHAPTER_REOUTLINE_GRAPH and returns the parsed, _require_beats-validated list;
    never mutates ``doc``. Title and summary are NOT re-authored."""
    ...
```

### Hook point (J3 — after the close write, in the adapter)

Invoked at the **end of `doc_ops.apply_chapter_close(doc, story_dir, cid)`**, after
the just-played chapter's `world_state`/`seam_packet` are committed and written.
It re-authors the beats of the **next** chapter id in `order` and writes them onto
that card. NOT invoked from `expand_chapters` (which stays the up-front draft).

## Acceptance Criteria

> **The deterministic gate is AC-1 (mocked-LLM unit). The live regen (AC-6) is
> corroboration, not a gate** — a fresh book is a fresh LLM roll; gap-count on it is
> non-deterministic (FR-522 instrument posture). Tests prove the constraint; the
> witness corroborates the abstraction.

- [ ] **AC-1 (deterministic gate, mocked LLM).** With `CHAPTER_REOUTLINE_GRAPH`
  stubbed: given a fixture where the prior chapter committed an actor **safe + high**
  and the chapter's frozen summary demands their drowning, the adapter writes the
  stub's bridge-containing beats and `seam_precondition_gap(doc, next_cid) == 0`.
  **Negative control (non-vacuous):** a stub returning beats WITHOUT a bridge leaves
  `gap_count == 1` — proving the assertion measures the bridge, not the plumbing.
- [ ] **AC-2 (purity + write split).** `reoutline_chapter_beats` never mutates `doc`
  (asserted via deep-copy equality); the write happens only in `apply_chapter_close`.
  Returns a `_require_beats`-validated list; raises (no silent fallback) on empty.
- [ ] **AC-3 (frozen title/summary).** Re-outline rewrites **only** `beats`; the
  card's `title` and `summary` are byte-identical before/after (so the whole-book
  partition and `_planned_reappearance_chapter`'s title/summary scan are unaffected).
- [ ] **AC-4 (guards / isolation).** No-op when there is no next chapter, or the next
  chapter already has any played turns or is `reviewed` (not merely "not reviewed").
  Played chapters and all prior chapters are byte-identical after a re-outline.
- [ ] **AC-5 (no downstream change).** Director, `running_scene`, turn loop, FR-521
  roster-drop, and `_clamp_lifecycle_reappearance_to_plan` are untouched; their tests
  stay green; `lint-imports` clean (no new cross-layer edge).
- [ ] **AC-6 (live corroboration, not a gate).** A regenerated Floodmark book: the
  Ch3 Arnulf seam that fired in `10023-BC` shows a bridge beat and `seam_precondition
  _gap` no longer flags **that** actor; `book_reviewer` no longer scores the Ch2→Ch3
  position teleport as a continuity break. The known witness over-fire on *hypothetical*
  framings (Ch2 "realize they will drown if they keep fighting") is **out of scope** —
  it is not an exit and needs no bridge (witness precision is deferred, see Related).
- [ ] **AC-7 (regime).** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, **no** `req:`. `feat`/`fix` + no
  `FR-XXX`-in-subject path avoided — commit subject carries `FR-523` and a diary entry
  accompanies the GREEN commit (diary-gate).
- [ ] `architecture.md` updated: outline becomes a draft + just-in-time state-aware
  beats re-outline; the `seam_precondition_gap` witness documented.

## Judgement (2026-06-18)

Examined against the live code (`chapter_ops.outline_chapters`/`close_chapter`,
`doc_ops.expand_chapters`/`apply_chapter_close`, `prompts/chapter_outline.yaml`,
`_clamp_lifecycle_reappearance_to_plan`). Contradictions resolved; scope frozen:

- **J1 — New single-chapter graph, not an extension.** `chapter_outline.yaml` is a
  whole-book partitioner whose contract ("partition the whole synopsis: no gap, no
  overlap") is incompatible with re-authoring one chapter. The re-outline is a
  distinct `chapter_reoutline.yaml` graph/prompt emitting `{beats:[...]}`, parsed by
  the existing `_beat_list`/`_require_beats`. Extending the partitioner is forbidden.
- **J2 — Purity preserved.** The drafted `reoutline_next_chapter(doc) -> dict` that
  mutates violates `chapter_ops`'s pure contract. Frozen as
  `async reoutline_chapter_beats(doc, cid) -> list[str]` (pure read); the write lives
  in `doc_ops.apply_chapter_close` (the adapter), mirroring `outline_chapters` vs
  `expand_chapters`.
- **J3 — Single hook point.** Re-outline runs once, at the end of
  `apply_chapter_close`, on the *next* chapter id, after the closing chapter's state
  is committed and written. Not in `expand_chapters`; not in the pure layer.
- **J4 — Beats-only.** Title and summary are frozen at derivation. Re-authoring them
  would shift the whole-book partition and break `_planned_reappearance_chapter`
  (which scans titles+summaries for the return signal that clamps lifecycle
  reappearance). Only `beats` may change.
- **J5 — Deterministic gate is the mocked unit (AC-1), not the live regen.** A
  freshly generated book is a fresh roll; holding the fix to universal `gap_count==0`
  on a heuristic instrument is not a deterministic acceptance. AC-1 (stubbed graph +
  fixture + negative control) is the gate; AC-6 is corroboration.
- **J6 — Witness over-fire is out of scope.** `seam_precondition_gap` fires on the
  *hypothetical* Ch2 "realize they will drown if they keep fighting" (no actual exit,
  no bridge needed). The fix is not held to clearing that; tightening the witness to
  exclude conditional/hypothetical framings is a separate follow-up (Related), not
  this FR.
- **J7 — Guards.** No-op unless a next chapter exists AND it has zero played turns
  AND is not `reviewed` — a mid-crash partially-played chapter must not have its beats
  yanked.
- **J8 — Fix B stays deferred.** No synopsis-derived planned-events artifact, no
  beat-gating lane in this FR. The carried physical state is the only new input.
- **J9 — No new layer edge.** `chapter_reoutline` is invoked exactly like
  `chapter_outline` (via `get_app`/`tree.py`); `lint-imports` must stay clean.
- **J10 — RED already landed.** `seam_precondition_gap` + `test_seam_precondition_
  gap.py` are committed (f368a770); GREEN adds the graph, the pure function, the
  adapter write, AC-1/2/3/4 tests, the changelog fragment, and a diary entry.

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
- `examples/dungeon_master/api/chapter_ops.py` — `outline_chapters` (state-blind, the bug site); `close_chapter`, `_clamp_lifecycle_reappearance_to_plan` (J4 dependency)
- `examples/dungeon_master/api/doc_ops.py` — `expand_chapters` (up-front draft), `apply_chapter_close` (J3 hook point)
- `examples/dungeon_master/chapter_outline.yaml`, `prompts/chapter_outline.yaml` — the whole-book partitioner (J1: NOT extended)
- FR-520 (positional working memory), FR-521 (forward-fed continuity), FR-522 (replay witness) — the continuity arc this completes
- `outputs/dungeon-master/10023-BC/story.json` — the offending artifact; `review.md` Continuity 1/5
- **Follow-up (deferred, not this FR):** `seam_precondition_gap` precision pass — exclude conditional/hypothetical framings ("if they keep fighting", "would drown") so the witness fires only on realized exits (J6).
- Scripture: `the_one_law`, `spec_kill`, `downstream_fix`, `boundary: schema/state`
