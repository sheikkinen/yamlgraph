# Feature Request: FR-527 — DM v2: Beat-Progress Early Close (Stop the No-Progress Tail)

**Priority:** HIGH
**Type:** Bug (engagement defect, authored at play time)
**Status:** **FALSIFIED AT ENFORCE — Fix A abandoned, re-scoped to FR-528 (2026-06-18).**
The judged Fix A (deterministic beat-progress stall guard) was implemented under TDD,
and its own load-bearing J6 corpus safety check **falsified it**: natural directors
routinely pause beat-marking mid-scene for up to **9 turns** and resume, so the
count-plateau signal cannot separate a *finished* director from a *pausing* one. Any
stall window small enough to cut the waste tail also preempts natural pauses; any
window large enough to spare them (> 9) shrinks to the cap (saving ~0 turns). The
production guard was reverted; the real cure is the OUTLINER refusing to author an
un-satisfiable-in-scene final beat (J4 seed → **FR-528**). See *Enforcement Outcome*
below. (Prior status: JUDGED — scope frozen, authorized for enforce, 2026-06-18.)
**Effort:** Fix A dead-ended; cure deferred to FR-528
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

**REJECTED at judgement (J2) — retained for the record.** `scene_complete` is not a
field the director writes; `_apply_beat_ledger` COMPUTES `direction["scene_complete"]
= (k == n)` from the satisfied-beat count. The director only selects WHICH enumerated
beats are now true. There is no prompt lever that "flips" a computed field. The honest
lever would be to get the director to mark the *terminal* beat satisfied — futile for
a genuine time-skip/epilogue beat (CH8 beat 5 "By autumn…") that the scene never
reaches, and risky (premature beat-marking) otherwise. The deterministic stall guard
(A) subsumes this case without touching the prompt.

### Bound choice

`scan_turn_waste.py` uses `STALL_THRESHOLD = 3` and surfaces 208 wasted turns;
`BEAT_STALL_LIMIT = 3` mirrors it, giving a chapter three turns of denouement after
its last beat before the loop closes it. Tunable; the instrument re-sizes the effect
of any change.

## Judgement (2026-06-18 — scope frozen, authorized for enforce)

The FR's diagnosis (a no-progress tail rides the cap, measured at 208 turns over 127
chapters) is real and well-witnessed. But reading the actual mechanism
(`turn_ops._apply_beat_ledger`) overturns the proposed *cure's* framing in two
load-bearing places. The judgement keeps the deterministic guard, rejects the prompt
lever, and replaces the fuzzy corroboration AC with a deterministic counterfactual.

- **J1 — Boundary confirmed.** The cure belongs in `turn_ops.chapter_should_close`,
  the single close predicate that `session.py`, `navigation.py`, and the FR-522
  `chapter_replay.py` witness all inherit. One edit, three call sites covered, no
  duplication. Correct boundary (`the_one_law`).

- **J2 — Fix B REJECTED (factually impossible as written).** `scene_complete` is
  COMPUTED, not authored: `_apply_beat_ledger` sets
  `direction["scene_complete"] = (k == n)` where `k = len(beats_satisfied)` and
  `n = len(beats)`. The director chooses only WHICH enumerated beats are now true
  (`_satisfied_indices`); the rails are code (FR-503 J3). No prompt can "flip" a
  derived field. Fix B is struck from scope.

- **J3 — The "all beats satisfied" alternative is not an alternative — it is the
  status quo.** `scene_complete = (k == n)` already closes a chapter the instant
  every beat is satisfied. CH8 never closed because its count plateaued at **k=4,
  n=5** — beat 5 never marked. So the disease is precisely *the plateau at k<n*, and
  the cure is a guard on the plateau, NOT a change to how `scene_complete` is
  computed. Changing the `k == n` rule would ripple into `climax_turn` and the Final
  Cut (`climax_turn` falls back to the `scene_complete` turn) — OUT OF SCOPE. The
  `k == n` natural-close path is left exactly as-is.

- **J4 — The plateau's root cause is an OUTLINER concern, recorded as a seed.** CH8
  beat 5 ("By autumn… a settlement that ends the blood-feud") is a time-skip/epilogue
  beat the ridge scene can never reach, so `k` can never equal `n`. This is a cousin
  of FR-525 (the outliner authoring a beat the capped scene cannot play). Fixing the
  outliner to not author un-satisfiable-in-scene resolution beats is a **separate FR
  (seed: FR-528?)**, OUT OF SCOPE here. FR-527 cures the *symptom* deterministically
  regardless of why the plateau formed — which is the right division: the play loop
  must be robust to any stall, whatever its cause.

- **J5 — Stall semantics frozen (exact, to kill ambiguity).** Add a pure helper
  `_beats_stalled(doc, cid, n, limit)` over `chapter_turns(doc, cid)`. Let
  `count(t) = len(turn_direction(doc, cid, t)["beats_satisfied"])`. The chapter is
  stalled at turn `n` iff:
  `n > limit` **and** `count(n) == count(n - limit)` **and** `count(n) >= 1`.
  `chapter_should_close` becomes `scene_complete OR _beats_stalled(…, BEAT_STALL_LIMIT)
  OR n >= CHAPTER_TURN_CAP`, with `BEAT_STALL_LIMIT = 3`. The hard cap stays the
  ultimate backstop; the `count >= 1` clause forbids closing an opening that has
  established nothing. On the recorded CH8 trace (counts …t5=3, t6=4, t7=4, t8=4,
  t9=4) this first fires at **n=9** (`count(9)=count(6)=4`), closing the chapter
  seven turns before the cap.

- **J6 — Deterministic counterfactual replaces the fuzzy engagement AC as the
  load-bearing safety check.** The risk of an early-close guard is cutting a
  chapter that would still have made progress. This is checkable WITHOUT a live LLM:
  a pure scan over every recorded chapter in `outputs/dungeon-master/100*-BC` must
  assert that `_beats_stalled` never fires *strictly before* an existing
  `scene_complete` turn — proving the guard cannot shorten a chapter that closes
  naturally today. (Spot-checked in judgement: CH1's counts 0,1,2,2,3,3,5 never
  satisfy `count(n)==count(n-3)` before its t7 natural close.) The "engagement floor
  rises above 1/5" regen stays, but as **corroboration only (FR-522 posture, never a
  CI gate)** — an LLM property, not a deterministic guarantee.

- **J7 — Test/commit regime.** Example-scoped: NO `@pytest.mark.req`, no CAP/REQ
  minting (match FR-525/FR-526 under FR-474 J3). Tests are pure dict-in/bool-out over
  synthetic traces + the recorded CH8 plateau, in `tests/test_navigation.py` beside
  the existing `chapter_should_close` tests. Commit RED (the CH8 plateau condemned:
  `chapter_should_close(...,9)` expected True, fails pre-fix) then GREEN separately.
  Enforce commit is `fix(dungeon_master): FR-527 …` with a changelog fragment
  (`type:fix scope:examples`, no `req:`) and a diary entry (FR-XXX gate).

- **J8 — `scan_turn_waste.py` is already committed (`bbb8ea12`) as the witness; do
  not re-commit it.** Effort revised to ~0.5 day with Fix B dropped.

**Scope frozen:** Fix A (the `_beats_stalled` guard in `chapter_should_close`,
`BEAT_STALL_LIMIT = 3`) plus the J6 deterministic corpus safety check. Fix B and any
change to the `scene_complete = (k == n)` computation are OUT. **Build order:** RED
(condemn the CH8 plateau + the corpus counterfactual) → GREEN (add `_beats_stalled`,
wire the predicate) → corroborate (regen floodmark, re-run `scan_turn_waste.py`).

## Enforcement Outcome (2026-06-18 — Fix A falsified by its own J6 gate)

Fix A was implemented exactly as judged (RED committed `a2a92f4f`: the CH8 plateau
condemned + the J6 corpus counterfactual; GREEN added `_beats_stalled` /
`BEAT_STALL_LIMIT = 3` / wired `chapter_should_close`). The GREEN run then **failed
the J6 corpus safety check** — the one the judgement made load-bearing precisely to
catch this:

```
10003-BC CH5: stall guard preempted natural close at t9 (scene_complete @t14)
```

A full corpus scan (`outputs/dungeon-master/100*-BC`, 18 books) proved the failure is
structural, not a tuning miss:

- **Natural directors pause and resume.** A count-plateau (no `beats_satisfied`
  growth) is NOT a "scene over" signal — it is routine mid-scene. The longest plateau
  *preceding a natural `scene_complete`* is **9 turns**: `10013-BC CH1`,
  `counts=[0,2,2,2,2,2,2,2,2,2,3,3,5]` — frozen at 2 for t2..t10, then resumes and
  closes at t13. ~24 naturally-closing chapters contain a >=3-turn pre-close plateau.
- **No useful separation exists.** To never preempt a natural close, `BEAT_STALL_LIMIT`
  must exceed 9. But of the 27 force-capped waste chapters, **18 have a frozen tail
  shorter than 9 turns** — at any safe limit they get zero benefit. The few long-tail
  cases fire essentially at the cap: the motivating `10025-BC CH8` froze at k=4 for 11
  turns (t6..t16); at limit 9 the guard fires at t15, saving **one** turn before the
  16-turn cap. The benefit the FR promised (close ~t9, save 7) evaporates entirely.
- **The discriminators the judgement assumed do not discriminate.** `k == total-1`
  (only the final beat missing) does not separate either: `10005-BC CH3` plateaus at
  exactly 4/5 for 4 turns, then resumes to 5/5 and closes naturally. And `beats_total`
  is `0` in older books (pre-FR-503 recording), so it is not even a readable signal.

**Why the judgement missed it.** J6 spot-checked a single easy trace (CH1's
`0,1,2,2,3,3,5`, which happens to never plateau for 3) and generalized. The
worst-case corpus member (`10013-BC CH1`'s 9-turn plateau) was never enumerated. The
gate's *design* was correct — running it over the **whole** corpus, not one trace, is
what exposed the flaw. The witness won (`Respect the RED — the witness wins`).

**Resolution.** The production guard was reverted to the FR-501 form
(`scene_complete OR n >= CHAPTER_TURN_CAP`). The RED-era unit tests asserting "close
on stall" encoded a now-falsified requirement and were replaced by a single corpus
test, `test_beat_plateau_signal_is_non_separable`, which pins the overlap (longest
natural plateau >= 9 turns AND waste tails shorter than it) so the dead end is never
retried. The cure moves to the boundary J4 already named: the **outliner** must not
author a final beat the capped scene can never reach (**FR-528**). FR-527 stands as
the recorded falsification — the cheapest bug is the one killed at the gate before it
ships.

## Acceptance Criteria

- [ ] `_beats_stalled(doc, cid, n, limit)` pure helper added to `turn_ops.py` with
      the J5 semantics (`n > limit AND count(n) == count(n - limit) AND count(n) >= 1`).
      Example-scoped: NO `@pytest.mark.req`, no CAP/REQ minting (J7).
- [ ] `chapter_should_close` = `scene_complete OR _beats_stalled(…, BEAT_STALL_LIMIT)
      OR n >= CHAPTER_TURN_CAP`, with `BEAT_STALL_LIMIT = 3`. The `k == n`
      `scene_complete` computation is UNCHANGED (J3).
- [ ] RED test condemns the recorded 10025-BC CH8 plateau (counts …t6=4,t7=4,t8=4,
      t9=4): `chapter_should_close(doc, "8", 9)` expected True, fails pre-fix; GREEN
      after (J5, J7).
- [ ] Negative control: a chapter whose `beats_satisfied` count still grows within the
      last 3 turns is NOT early-closed.
- [ ] Negative control: an opening with `count == 0` is NOT early-closed (the
      `count >= 1` clause).
- [ ] Negative control: `scene_complete` still closes at its turn; `CHAPTER_TURN_CAP`
      still backstops.
- [ ] **Deterministic corpus safety check (J6, load-bearing):** a pure scan over
      every recorded chapter in `outputs/dungeon-master/100*-BC` asserts `_beats_stalled`
      never fires strictly before that chapter's existing `scene_complete` turn — the
      guard cannot shorten a naturally-closing chapter.
- [ ] **Corroboration (FR-522 posture, NOT a gate):** regenerate a book from the
      floodmark premise; `scan_turn_waste.py` reports materially fewer wasted turns
      than the 208/127 baseline, and the reviewer's per-chapter engagement floor rises
      above 1/5. Never wired into CI.
- [ ] `scan_turn_waste.py` already committed (`bbb8ea12`) as the witness — no
      re-commit (J8).

## Alternatives Considered

- **Fix B — prompt the director to set `scene_complete`** — impossible; the field is
  computed `k == n`, not authored (J2).
- **Change `scene_complete` to close at `k >= n-1` (treat the last beat as optional)**
  — ripples into `climax_turn` / Final Cut and silently drops a beat that is sometimes
  genuinely playable; the stall guard achieves the close without changing the
  natural-close contract (J3).
- **Raise `CHAPTER_TURN_CAP`** — wrong direction; lengthens the no-progress tail and
  re-opens the FR-501 runaway.
- **Per-chapter prose review/revise** — treats the symptom after the turns are spent;
  cannot see the over-long-scene cause; wrong boundary.
- **Hard "close when all beats satisfied"** — that is already `scene_complete`; it
  cannot fire on a `k < n` plateau, which is exactly the failure (J3).

## Related

- `examples/dungeon_master/api/turn_ops.py` — `chapter_should_close`, `CHAPTER_TURN_CAP`,
  `turn_direction`, `chapter_scene_complete` (FR-501).
- `examples/dungeon_master/scripts/scan_turn_waste.py` — FR-527 witness instrument.
- FR-501 (per-chapter turn cap), FR-525 (outliner split-gate), FR-524 (beat-coverage
  witness) — the bound/over-commit/under-use trilogy.
- `outputs/dungeon-master/10025-BC/review.md` — the review that surfaced Ch8.
- `/memories/repo/dm-play-loop-chapter-turn-budget.md`.
