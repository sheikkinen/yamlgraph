# Feature Request: FR-528 — DM v2: Outliner Playable-Beat Classification (kill the plateau at its source)

**Priority:** HIGH
**Type:** Bug (pacing/continuity defect, authored at outline time)
**Status:** **ENFORCED via re-scoped design (2026-06-18).** The `playable: false`-on-a-beat
mechanism was REJECTED at Judge (J1-J6): `beats` is a hardened `list[str]` contract
(`_beat_list` coerces, `_require_beats` validates, FR-504) that the director selects *by
number*; promoting beats to objects ripples through ~8 call sites plus the recorded
corpus. The SHIPPED cure keeps the epilogue OUT of the beat ledger entirely: a
deterministic `unplayable_beat_gap` witness fires when a chapter's FINAL beat LEADS with a
future-time-skip marker, and `outline_chapters` re-rolls (instructing an in-scene
resolution or a summary fold), then RAISES after the bounded retry. `n = len(beats)` and
`scene_complete = k == n` are untouched. See Implementation (2026-06-18) and Judgement
(J1-J6).
**Effort:** ~1 day (re-scoped design)
**Requested:** 2026-06-18

## Implementation (2026-06-18)

Shipped the re-scoped design (the `playable`-flag schema change in Proposed Solution §A/§B
below is SUPERSEDED and was not built):

- **`witness_metrics.unplayable_beat_gap(card)`** — pure outline-time witness. Fires when
  the chapter's FINAL beat (after stripping leading quotes/dashes, case-insensitively)
  STARTS with a future-time-skip marker (`_TIME_SKIP_LEAD_TOKENS`: "by autumn", "years
  later", …). Returns `{gap_count, gaps:[{beat_index, beat, marker, reason}]}`. The
  **leading-anchor** is the precise discriminator — an epilogue *opens* with the jump,
  whereas a present-tense in-scene resolution does not — so a beat that merely NAMES a
  settlement/feud-end (a thing the scene CAN play) is not flagged, avoiding the
  `plausible_wrong_answer` over-fire a "settlement"/"feud" co-occurrence detector hits.
  Only the FINAL beat is checked (a mid-list time-skip does not pin the chapter open).
- **`chapter_ops` gate** — `_unplayable_chapters` + `_unplayable_feedback` mirror the
  FR-525 `_packed_chapters`/`_reversal_feedback` pair; both gates now compose inside the
  single `outline_chapters` `_OUTLINE_MAX_ATTEMPTS` loop. On a hit the outline re-rolls
  with feedback instructing either an in-scene present-tense final beat OR folding the
  time-skip aftermath into the chapter `summary` as closing narration; on persistence it
  RAISES (Commandment 6, no silent fallback). The epilogue thus survives as `summary`
  narration (which `final_cut_context` already feeds), never as an unreachable beat.
- **Tests (FR-474 J3, REQ-exempt):** `test_unplayable_beat_gap.py` (5: real 10025-BC CH8
  epilogue fires; present-tense in-scene clean; present-tense settlement clean = the
  plausible-wrong-answer guard; mid-list time-skip clean; empty card safe) and two
  `test_chapters.py` gate tests (re-rolls until clear; raises on persistence). Full DM
  suite 252 passed; lint/format clean.
- **NOT built (gated/out of scope):** the `compose_book_deterministic` change to render a
  separate `denouement` field — the chosen channel is the EXISTING `summary`, so no new
  field and no composer change was needed. Reflection C (Gap 2 + Gap 3 are one
  non-partitioning Arnulf arc) is addressed indirectly: a chapter that no longer rides
  the cap stops replaying the thread; the cross-chapter reappearance coherence remains
  FR-526's lane.


## Summary

A DM v2 chapter resolves naturally only when its director computes
`scene_complete = (k == n)`, where `n = len(beats)` and `k = len(beats_satisfied)`
([`turn_ops.py`](../examples/dungeon_master/api/turn_ops.py) `_apply_beat_ledger`,
~L888-L897). The outliner sometimes authors a **final time-skip / epilogue beat** the
capped in-scene action can never reach (e.g. `10025-BC` Ch8 beat 5: "By autumn... a
settlement that ends the blood-feud" — narrated, not playable on the ridge). Because
every authored beat counts toward `n`, `k` is pinned at `n-1` forever, `scene_complete`
never fires, and the chapter rides the 16-turn cap replaying its resolved confrontation
(the no-progress tail FR-527 measured at 208 turns over 127 chapters). This FR lets the
outliner mark a beat **`playable: false`** (narrated denouement, not played); such beats
are excluded from `n`, so `scene_complete` fires when every *playable* beat lands, and
the epilogue is rendered by `compose_book` as the closing paragraph instead of pinning
the chapter open.

## Value Statement

A reader stops hitting "the same confrontation, fifteen times": the chapter ends when
its playable story ends, while a legitimate epilogue beat survives as narration instead
of being amputated or replayed to the cap.

## Problem

This is the root cause FR-527 only treated as a symptom. FR-527 tried to cut the tail at
the **play boundary** with a beat-stall guard and was falsified: a count plateau is
indistinguishable from a routine mid-scene pause (up to 9 turns in the corpus). The
plateau is not a play-loop defect — it is an **outline defect**: a beat was authored that
the bounded scene cannot physically satisfy, so `k` can structurally never reach `n`.
Normalize at the boundary where the bad beat is authored (`the_one_law`), not downstream
where it manifests as repetition.

**One defect, not two (Reflection C).** The `10025-BC` reviewer's Gap 2 (Ch8 replays
Ch7's resolved Arnulf conflict ~15x) and Gap 3 (Arnulf "on the ridge" Ch6 → "emerging
from water" Ch7 → "convinced again" Ch8) are the *same* outliner failure: an Arnulf arc
that does not partition cleanly across chapters. A correctly-scoped playable-beat
classification — every chapter's playable beats are reachable inside its own cap — closes
both: the chapter that no longer replays also stops re-introducing a thread the prior
chapter already closed.

**Why not forbid the beat (rejected framing).** The doc's first sketch (§5.2) was a
detector that *forbids* a final time-skip beat. That amputates a legitimate denouement —
books have epilogues. The honest cure classifies the beat (`playable: false`) so the
narration survives, rather than rejecting a whole class of valid story structure. This is
a smaller, truer change and avoids the FR-525-style "reject the outline" blast radius for
beats that are perfectly fine *as narration*.

## Proposed Solution

Two coordinated changes, both at the outline boundary; the schema field is load-bearing,
the prompt guidance is best-effort.

### A. `playable` flag on the beat schema (load-bearing)

Extend the chapter outline so a beat may be authored as narrated-not-played:

```yaml
# chapter card (authored by outline_chapters / reoutline_chapter_beats)
beats:
  - text: "Hilde and Gunnar reach the high ledge together"      # playable (default)
  - text: "Arnulf is hauled from the flood, alive"               # playable
  - text: "By autumn, a settlement ends the blood-feud"
    playable: false                                              # narrated denouement
```

`_apply_beat_ledger` computes `n = len([b for b in beats if playable])` (default
`playable: true` when the key is absent — existing books unchanged). `scene_complete`
fires when every *playable* beat is satisfied. The non-playable beats are carried on the
card for `compose_book` to render as the chapter's closing narration.

### B. Outliner prompt: classify, do not omit (best-effort)

`chapter_outline.yaml` / the reoutline prompt instruct the outliner to mark a beat
`playable: false` when it is a time-skip / off-scene epilogue the chapter's scene cannot
physically enact — and to keep every *playable* beat reachable within the chapter (the
clean-partition rule that also closes Gap 3).

### C. Deterministic detector (gate, mirrors FR-525)

A pure `unplayable_beat_gap(card)` witness flags a chapter whose **final** beat is a
time-skip/epilogue (token-matched: future-time / settlement / "by autumn" style) yet
still marked `playable`. Wired into `outline_chapters` like `reversal_pack_gap`: on a hit
the outline is re-invoked with the violation named (bounded retry), then RAISES
(Commandment 6, no silent fallback).

## Judgement (2026-06-18 — SENT BACK, design re-scoped)

The FR's diagnosis is correct and confirmed against the code: the plateau is an OUTLINE
defect (a final beat the bounded scene cannot physically reach), not a play-loop defect,
and the boundary is right. But reading the actual beat contract overturns the proposed
mechanism, and a smaller design achieves the same goal without touching a hardened
contract or migrating the corpus.

- **J1 — `playable: false` on a beat is a category error (REJECTED).** `beats` is a
  validated `list[str]` (`_beat_list` coerces every entry to `str`, `_require_beats`
  rejects empty, FR-504), and the director satisfies beats by SELECTING THEIR NUMBER
  from the enumerated list (`_satisfied_indices`). A beat the scene can never reach is
  one the director can never select — so it does not belong in the *selection list* at
  all. Tagging it `playable: false` smuggles a non-selectable item into a list whose
  whole purpose is selection.

- **J2 — the blast radius is far larger than "~1 day".** Promoting a beat from `str` to
  `{text, playable}` ripples through `_beat_list`, `_satisfied_indices` (text match),
  `_apply_beat_ledger`, `chapter_beat_list`, `reversal_pack_gap`, `scan_turn_waste.py`,
  `scan_beat_gaps.py`, every fixture, the outline prompts, AND the recorded `*-BC`
  corpus (which stores `beats: list[str]`). That is a contract migration, not a flag.

- **J3 — the correct boundary is to keep the epilogue OUT of the beat ledger.** Re-scope:
  the outliner emits a chapter-level **`denouement` (narrated closing) field**, OR
  relocates the time-skip into the existing `summary`, NEVER into `beats`. Then
  `n = len(beats)` counts only in-scene beats, `scene_complete = k == n` fires when the
  scene resolves (UNCHANGED — no ripple into `climax_turn` / Final Cut), and the epilogue
  is preserved as narration. `beats` stays `list[str]` (zero migration). This satisfies
  Reflection A's goal (preserve, do not amputate) at a fraction of the cost.

- **J4 — enforcement is the proven FR-525 pattern.** A pure `unplayable_beat_gap(card)`
  detector (final beat is a time-skip/epilogue token yet authored as an in-scene beat)
  wired into `outline_chapters`: on a hit, re-invoke the outline with the violation named
  (bounded `_OUTLINE_MAX_ATTEMPTS`), instructing the outliner to make the final beat
  in-scene OR move the resolution to `denouement`/`summary`; RAISE on exhaustion
  (Commandment 6). Mirrors `reversal_pack_gap` exactly — a known-good shape.

- **J5 — confirm one composition fact at enforce (do not assume).** Verify that
  `compose_book_deterministic` (or `final_cut`) renders the chosen narration channel
  (`denouement` field, or the relocated `summary`) into the manuscript, so the epilogue
  actually reaches the reader. If neither renders it today, the smallest wiring to do so
  is in scope; nothing larger.

- **J6 — test/commit regime (FR-474 J3).** Example-scoped: NO `@pytest.mark.req`. RED
  condemns the `unplayable_beat_gap` on the `10025-BC` Ch8 shape (final epilogue beat
  flagged) and a `scene_complete` test proving an in-scene-only beat list resolves; GREEN
  separately. `fix(dungeon_master): FR-528 …`, changelog `type:fix scope:examples` no
  `req:`, diary entry (FR-XXX gate).

**Action:** return to Plan. Rewrite Proposed Solution around the `denouement`/`summary`
relocation + `unplayable_beat_gap` detector (drop the `playable`-on-beat schema change),
then re-judge. The acceptance criteria below are superseded by this judgement and must be
rewritten to the re-scoped design.

## Acceptance Criteria

- [ ] `playable: bool = True` accepted on a beat; absent key defaults to playable
      (existing recorded books parse unchanged).
- [ ] `_apply_beat_ledger` computes `n` over playable beats only; `scene_complete` fires
      when all playable beats are satisfied. RED condemns the `10025-BC` Ch8 shape (5
      beats, beat 5 non-playable → `n=4`, `scene_complete` at the turn `k` reaches 4).
- [ ] `compose_book` renders non-playable beats as closing narration (not dropped).
- [ ] `unplayable_beat_gap(card)` pure detector: fires on a final time-skip beat marked
      playable, clean on a chapter whose final beat is in-scene. Negative control: a
      legitimately playable final beat is NOT flagged.
- [ ] `outline_chapters` re-invokes on a hit (bounded, `_OUTLINE_MAX_ATTEMPTS`) then
      RAISES on exhaustion (mirror FR-525).
- [ ] Example-scoped (FR-474 J3): NO `@pytest.mark.req`, no CAP/REQ minting; changelog
      fragment `type:fix scope:examples`, no `req:`.
- [ ] **Corroboration (FR-522 posture, NOT a gate):** regenerate the floodmark premise;
      `scan_turn_waste.py` reports materially fewer wasted turns than the 208/127
      baseline, and the reviewer's per-chapter engagement floor rises above 1/5.

## Alternatives Considered

- **FR-527 play-boundary stall guard** — falsified at enforce; a count plateau cannot be
  distinguished from a natural mid-scene pause. The plateau must be prevented at outline
  time, not detected at play time.
- **Forbid the time-skip beat entirely** — amputates a legitimate denouement; classify
  (`playable: false`) preserves the narration.
- **Change `scene_complete` to close at `k >= n-1`** (treat the last beat as optional) —
  ripples into `climax_turn` / Final Cut and silently drops a beat that is sometimes
  genuinely playable; the `playable` flag is explicit about *which* beat is narrated.

## Related

- `examples/dungeon_master/api/turn_ops.py` — `_apply_beat_ledger`, `scene_complete`,
  `chapter_should_close`.
- `examples/dungeon_master/api/chapter_ops.py` — `outline_chapters`,
  `reoutline_chapter_beats`, `reversal_pack_gap` wiring to mirror.
- `examples/dungeon_master/prompts/chapter_outline.yaml` — the outline prompt.
- FR-527 (falsified play-boundary cure, this FR is its re-scope), FR-525 (outliner
  split-gate, same gate pattern), FR-523 (state-aware reoutline).
- `examples/dungeon_master/docs/continuity-issues.md` §5.2, Gap 2, Gap 3.
- `/memories/repo/dm-play-loop-chapter-turn-budget.md`.
