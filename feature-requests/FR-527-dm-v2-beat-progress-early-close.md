# Feature Request: FR-527 — DM v2: Beat-Progress Early Close (Stop the No-Progress Tail)

**Priority:** HIGH
**Type:** Bug (engagement defect, authored at play time)
**Status:** Proposed
**Effort:** ~1 day
**Requested:** 2026-06-18

## Summary

A DM v2 chapter's only natural exit is its director emitting `scene_complete`;
absent that, the FR-501 `CHAPTER_TURN_CAP = 16` force-closes it. But the director
frequently **stops making beat progress long before turn 16 and never flips
`scene_complete`** — so the chapter rides the hard cap, replaying material that adds
no new beat. The `beats_satisfied` set freezes, the phase sticks in `climax`, and the
remaining turns are padding that collapses engagement. This FR makes the play loop
close a chapter when **beat progress has stalled for K consecutive turns** (a
deterministic no-progress guard), and tightens the director to flip `scene_complete`
once the satisfiable beats are covered — closing the chapter at the story's end
instead of the budget's end (`the_one_law`: act on the signal already in state).

## Value Statement

A reader stops hitting "the same confrontation, fifteen times" — once a chapter has
played out the beats it can play, it ends, instead of burning its turn budget on
repetition that the book reviewer scores 1/5 on engagement.

## Problem

Forensic root cause (proven by the FR-527 witness `scan_turn_waste.py`, not
hypothesized):

- `turn_ops.chapter_should_close(doc, cid, n)` closes a chapter at
  `scene_complete OR n >= CHAPTER_TURN_CAP` (FR-501). It consults **only**
  `scene_complete` and the hard cap. It does **not** consult `beats_satisfied`.
- The director's per-turn `direction` side-channel already reports a growing
  `beats_satisfied` list and a `phase`. When the director satisfies the beats it can
  satisfy but never declares `scene_complete`, `beats_satisfied` **stops growing**
  while turns keep playing to the cap.
- Those no-progress turns are where the model replays the resolved confrontation.
  The closing/epilogue beat (the chapter's resolution) is frequently never reported
  satisfied — it *is* the scene end — so the director, lacking a "you're done" signal,
  loops in `climax` until the cap fires.

### Condemning evidence (RED instrument, committed with this FR)

`examples/dungeon_master/scripts/scan_turn_waste.py` is a pure deterministic witness
(FR-522 instrument posture): for each force-capped chapter that never emitted
`scene_complete`, it measures the **no-progress tail** — turns played after the last
turn whose `beats_satisfied` count grew. Run over the DM corpus
(`outputs/dungeon-master/100*-BC`):

```
GRAND TOTAL WASTED TURNS: 208 over 127 chapters
```

This is **systemic, not a one-off**. 14 of 18 books contain at least one stalled
chapter. The worst single instance is the chapter that motivated this FR:

- `10025-BC` Ch8 "The New Camp": all 4 satisfiable beats reached at **turn 6**, the
  `beats_satisfied` set then **frozen through turn 16**, replaying Arnulf's
  abandon-Gunnar demand ~10 times. Book reviewer: **engagement 1/5, coherence 2/5,
  prose 2/5** for Ch8 alone, and the headline "severely undermined by persistent
  continuity problems." Every *other* chapter of that book scored 4–5/5 on
  engagement. Ch8 is the no-progress tail made visible.
- `10024-BC`: 26 wasted turns over 3 chapters. `10023-BC`: 23. `10012-BC`: 25.

**This is the dual of FR-501 and FR-525.** FR-501 bounded a chapter whose director
*never* says "done" (unbounded above). FR-525 forbade a chapter that promises *more
than the bound can play* (over-committed within the bound). This is a chapter that
has *already played everything it will play* yet stays open to the bound (under-using
the bound, over-playing the content). FR-501's cap stopped the runaway; it did not
make the chapter end *when the scene ends*.

**The One Law (`the_one_law`).** The signal that the scene is over — beat progress has
stopped — already exists in the committed `direction` side-channel. The close
decision ignores it and waits for the budget to expire. Normalize at the boundary
where the signal lives (the play loop's close decision), not downstream in a prose
revise pass that would only compress text the model already spent turns generating.

**Why not chapter-level review/revise.** A per-chapter reviewer treats the *symptom*
(verbose, repetitive prose) after the model has already spent the LLM turns producing
it, and cannot see that the cause is an over-long scene. The cheapest fix ends the
scene earlier, so the repetition is never generated. Revise is the wrong boundary.

## Proposed Solution

Two coordinated changes, both at the play boundary; the deterministic guard is
load-bearing, the prompt nudge is best-effort.

### A. Deterministic no-progress guard in `chapter_should_close` (load-bearing)

Extend the close decision to also close when beat progress has stalled for
`BEAT_STALL_LIMIT` consecutive turns:

```python
# turn_ops.py
BEAT_STALL_LIMIT = 3  # denouement grace after the last beat lands

def chapter_should_close(doc: dict, cid: str, n: int) -> bool:
    if turn_direction(doc, cid, n).get("scene_complete"):
        return True
    if _beats_stalled(doc, cid, n, BEAT_STALL_LIMIT):
        return True
    return n >= CHAPTER_TURN_CAP
```

`_beats_stalled` is pure over the played turns: True when the `beats_satisfied` count
has not increased across the last `BEAT_STALL_LIMIT` turns AND at least one beat is
satisfied (never close an opening that has not established anything). This keeps the
hard cap as the ultimate backstop and never fires before a real denouement window.

### B. Director prompt: flip `scene_complete` when satisfiable beats are covered

Tighten the director prompt so that once `beats_satisfied` covers the playable beats
(all but a never-satisfiable closing beat), it reports `scene_complete = true` rather
than looping in `climax`. Best-effort — the guard in (A) is the deterministic floor.

### Bound choice

`scan_turn_waste.py` uses `STALL_THRESHOLD = 3` and surfaces 208 wasted turns;
`BEAT_STALL_LIMIT = 3` mirrors it, giving a chapter three turns of denouement after
its last beat before the loop closes it. Tunable; the instrument re-sizes the effect
of any change.

## Acceptance Criteria

- [ ] `_beats_stalled` pure helper added to `turn_ops.py` with `@pytest.mark.req`
      (exempt under FR-474 J3 if example-scoped — match siblings).
- [ ] `chapter_should_close` closes on a 3-turn beat-progress stall, still closes on
      `scene_complete`, still backstops at `CHAPTER_TURN_CAP`.
- [ ] Negative control: a chapter still adding beats at turn 15 is NOT early-closed
      (only stalled chapters close early).
- [ ] Negative control: an opening chapter with zero satisfied beats is NOT
      early-closed (no premature close before anything is established).
- [ ] RED test condemns the 10025-BC Ch8 trace (stall @t6 → would close ~t9, not t16)
      before the fix; GREEN after.
- [ ] Director prompt updated to flip `scene_complete` on satisfiable-beat coverage.
- [ ] Corroboration: regenerate a book from the floodmark premise; `scan_turn_waste.py`
      reports materially fewer wasted turns than the pre-fix corpus baseline (208/127),
      and the book reviewer's per-chapter engagement floor rises above 1/5.
- [ ] `scan_turn_waste.py` committed as the FR-527 witness instrument.

## Alternatives Considered

- **Raise `CHAPTER_TURN_CAP`** — wrong direction; lengthens the no-progress tail and
  re-opens the FR-501 runaway.
- **Per-chapter prose review/revise** — treats the symptom after the turns are spent;
  cannot see the over-long-scene cause; wrong boundary (rejected above).
- **Prompt-only (B without A)** — leaves a non-deterministic floor; a director that
  ignores the nudge keeps riding the cap. The guard must be deterministic (Commandment
  6: no silent reliance on the model behaving).
- **Hard "close when all beats satisfied"** — under-counts: the closing beat is often
  never reported satisfied, so 100% coverage never triggers (empirically validated:
  the first cut of `scan_turn_waste.py` using this rule reported 0 waste while Ch8
  visibly wasted 10 turns). The stall signal is the honest one.

## Related

- `examples/dungeon_master/api/turn_ops.py` — `chapter_should_close`, `CHAPTER_TURN_CAP`,
  `turn_direction`, `chapter_scene_complete` (FR-501).
- `examples/dungeon_master/scripts/scan_turn_waste.py` — FR-527 witness instrument.
- FR-501 (per-chapter turn cap), FR-525 (outliner split-gate), FR-524 (beat-coverage
  witness) — the bound/over-commit/under-use trilogy.
- `outputs/dungeon-master/10025-BC/review.md` — the review that surfaced Ch8.
- `/memories/repo/dm-play-loop-chapter-turn-budget.md`.
