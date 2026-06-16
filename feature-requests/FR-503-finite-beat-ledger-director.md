# Feature Request: FR-503 — Finite beat ledger for the director (the unanchored-phase stall)

**Priority:** HIGH
**Type:** Bug fix (generation quality)
**Status:** Enforcing — code GREEN (120 DM tests), live witness pending (2026-06-16)
**Effort:** ~1 day
**Requested:** 2026-06-16

## Implementation status (2026-06-16)

RED → GREEN landed (commit `849e1e75` = RED). Changes, all in
`examples/dungeon_master/`:

- **`api/turn_ops.py`** — new pure helpers: `chapter_beat_list` (the finite
  contract), `_phase_for_count` (J3 truth table), `_satisfied_indices` (1-based
  numbers → 0-based, out-of-range ignored, text-echo fallback), `_apply_beat_ledger`
  (resolve indices → canonical text, accumulate cumulatively, compute
  `phase`/`scene_complete`; `N == 0` → FR-491 free-text fallback). `_beats_block`
  surfaces the numbered beats + "BEATS STILL TO PORTRAY" into `running_scene`.
  `invoke_turn` now calls `_apply_beat_ledger` instead of `_clamp_phase` +
  `_canonicalize_beats` (both kept for the `N == 0` fallback only).
- **`prompts/chapter_outline.yaml`** — emits an ordered `beats` list (3–6) per chapter.
- **`prompts/turn_direct.yaml`** — `beats_satisfied` is now satisfied beat
  **numbers** (`array of integers`); the prose drops "free text".
- **`prompts/character_intent.yaml`** — anti-skip guard narrowed: drive toward the
  FIRST beat still to portray, don't skip past it, don't stall.
- **`api/chapter_ops.py`** (`outline_chapters` + `_beat_list`) and
  **`api/doc_ops.py`** (`expand_chapters`) — carry/persist `beats` onto the card.
- **`tests/test_turn_prototype.py`** — 6 new tests (truth table, index parsing,
  ledger resolution + cumulative, `N == 0` fallback, `running_scene` pending beats).

J1 verified: persisted `beats_satisfied` stays `list[str]` and `beats_total =
len(beats)`, so `chapter_beats`/`final_cut_context`/`director_card.html` are
untouched. The `N == 0` fallback keeps every pre-FR-503 test green (mock outlines
carry no beats), including the FR-481 `_clamp_phase` and FR-491 `beats_total == 0`
tests. `_clamp_phase` removal is deferred to FR-504.

## Summary

The DM v2 director judges chapter progress from a **prose** chapter summary with
no enumerated, finite list of key events. As a result `beats_satisfied` is a
free-text accumulator that inflates without bound, `phase` has no rails to climb,
and `scene_complete` has no denominator. The director stalls in `"rising"`
indefinitely, and the FR-501 turn cap — designed as a rare safety valve — becomes
the *primary* way most chapters close. This is the shared root cause behind the
mediocre prose scores on **both** providers tested (inception/mercury 2/5,
azure/gpt-5.4-mini 2/5): the looping, prop-thrashing, non-escalating chapters the
`book_reviewer` repeatedly flags.

## Problem

### The evidence (two providers, same pathology)

A live Floodmark regeneration was run on two very different providers and scored
with `examples/book_reviewer`:

| | Inception (mercury) 10003-BC | Azure (gpt-5.4-mini) 10004-BC |
|---|---|---|
| Chapters | 9 | 6 |
| Overall | 2/5 | 2/5 |
| Continuity | 1/5 | 1/5 |
| Force-closed by FR-501 cap | 2 of 9 | **4 of 6** |

The reviewer's located findings on both books name the same failure: *"nearly
every paragraph follows the pattern 'Hilde [action], Gunnar [action], …', which
deadens engagement"*; chapters are *"a single, unresolved physical struggle that
repeats the same actions across multiple paragraphs without clear progression or
outcome."*

### The mechanism (the smoking gun)

Per-turn director output for two azure chapters:

```
ch1 (capped):   opening → rising → rising → … → rising   (16 turns, never escalates)
   beats_satisfied count: 0,3,6,6,10,12,16,18,22,22,26,29,32,33,33,35
ch6 (resolved): opening → rising → climax → resolved     (11 turns)
   beats_satisfied count: 0,2,2,2,2,5,5,5,7,7,10
```

Chapter 1 reports **35 "satisfied beats" for a 2–4 sentence summary** and never
leaves `"rising"`. Two compounding defects produce this:

1. **No finite beat anchor.** The chapter summary is unstructured prose
   (`chapter_outline.yaml` returns only `title` + `summary`). The director must,
   every turn and from scratch, infer the finite set of key events, judge which
   are satisfied, and decide completion — all from free text. With no stable
   enumerated target there is no denominator: `beats_satisfied` is merged
   cumulatively (FR-491) as free-text phrases that never dedupe, so the count
   climbs forever, and `scene_complete` ("every event the summary describes has
   occurred") can never be concluded because the director can always find "one
   more beat" in the newest recap.

2. **No forward pressure to the characters.** `running_scene` (turn_ops.py)
   shows each character only the chapter's prose summary, the inherited world
   state, and the **last 3 recaps** — never *which beats remain*. The
   `character_intent` prompt adds an anti-skip-ahead guard ("attempt only the
   single next thing… never assume the chapter's events have already occurred"),
   which correctly prevents replaying the climax but supplies **no pull toward
   the next unsatisfied beat**. Every character therefore transacts on the
   nearest object, every turn, and the scene never advances.

This is a **composition bug** (Scripture: every component passes its unit test —
the director extracts beats, the characters stay in role and don't skip ahead,
the FR-501 cap terminates — but the *policy connecting them* has no forward
pressure). It is **not** a provider defect: two models with opposite
architectures (diffusion mercury, GPT-class azure) both stall in `"rising"`. The
FR-501 cap is vindicated (without it azure would have run four chapters to 96
turns each) but a cap that fires on the majority of chapters is masking a
generation defect, not handling a rare edge.

## Proposed Solution

Replace the unanchored free-text beat judgement with a **finite, ordered, computed
beat ledger** — applying the same "scores are computed, not asked" doctrine the
`book_reviewer` already proves (FR-497).

1. **Enumerate beats at outline time.** `chapter_outline.yaml` returns, per
   chapter, an ordered `beats: [str, …]` (≈3–6 key events) alongside the prose
   `summary`. The finite list is the chapter's contract.

2. **Director selects from the list, does not invent.** `turn_direct` changes
   from "extract free-text satisfied beats" to "return the indices of the
   enumerated beats now satisfied" — a bounded set over a known list. Near-dupe
   inflation becomes impossible.

3. **Compute phase and completion, do not ask.** Derive deterministically in
   Python from `|satisfied| / |beats|`:
   - `scene_complete = (satisfied == all beats)` — no longer an LLM guess that
     can stall;
   - `phase`: `opening` at 0 satisfied → `rising` while partial → `climax` on the
     final beat → `resolved` when complete.
   The LLM judges only *which enumerated beats are now true* (its genuine job);
   the rails are arithmetic.

4. **Close the loop into the scene.** `running_scene` surfaces
   **"BEATS STILL TO PORTRAY (drive toward the FIRST of these next): …"** so both
   the characters and the director have an explicit forward target. The
   anti-skip-ahead guard is narrowed: forbid jumping *past* the next unsatisfied
   beat, but *require advancing to it*.

The FR-501 turn cap remains as the deterministic backstop; the goal is that it
fires rarely again (the natural ≈6-turn close), not on the majority of chapters.

## Acceptance Criteria

- [ ] `chapter_outline.yaml` returns an ordered `beats` list per chapter; the
      schema and a pure parse test pin it.
- [ ] The chapter card persists the enumerated `beats` for the chapter.
- [ ] `turn_direct` returns satisfied-beat **indices over the enumerated list**,
      not free-text phrases; a near-duplicate recap can no longer inflate the
      satisfied count beyond `|beats|`.
- [ ] **J1:** `_direction_dict` resolves the returned indices back to canonical
      beat **text**, so the persisted `beats_satisfied` stays `list[str]` and
      `beats_total = len(beats)`; `chapter_beats`, `final_cut_context`, and
      `director_card.html` need no change. A unit test pins index→text resolution
      (including out-of-range indices ignored).
- [ ] **J3:** `scene_complete` and `phase` are **computed** from the satisfied set
      in Python per the frozen truth table (pure function, unit-tested), not read
      from the LLM. `N == 0` falls back to the FR-491 free-text path (no
      divide-by-zero); a unit test covers the `N == 0` chapter.
- [ ] `running_scene` includes the remaining (unsatisfied) beats with an explicit
      "drive toward the first of these" instruction; a unit test asserts the
      remaining-beats section is present and excludes satisfied beats.
- [ ] **J4 (live witness):** a regenerated Floodmark book on **azure** (same
      premise) shows the FR-501 cap firing on a **minority** of chapters (down from
      4/6), and the `book_reviewer` engagement mean improves vs the 1.83 azure
      baseline — recorded in this FR on enforce.
- [ ] DM unit suite green; FR-501 cap behaviour unchanged (still the backstop).
- [ ] `_clamp_phase` (FR-481) is removed or proven subsumed by the computed
      monotonic phase; no orphaned helper remains.

## Notes / Scope

- Single example (`examples/dungeon_master/`), FR-474 J3 regime: no CAP file, no
  `@pytest.mark.req` markers, honest `feat(dungeon-master): FR-503 …` commits with
  an `FR-474 J3` trailer, a changelog fragment, and a diary reflection.
- Out of scope: arbitrary-chapter regeneration (FR-502), book-level revision
  passes, and the `closed_by: budget|scene_complete` degradation flag (FR-501
  Seed) — though this FR makes that flag cheaper since `phase`/completion become
  computed.

## Judgement (2026-06-16)

**Verdict: APPROVED with refinements. Scope frozen.** The diagnosis is sound and
evidenced (two-provider trace, monotonic free-text inflation to 35 beats on a
3-sentence summary). The root cause — an unanchored, unbounded beat judgement with
no forward pressure — is correctly identified as a composition bug, not a provider
defect. The "compute the rails, ask only the genuine judgement" direction is the
right shape (it is exactly the FR-497 `book_reviewer` doctrine turned inward).

Four refinements are folded into scope before authority is granted:

### J1 — Do not orphan the four existing free-text-beat consumers

The current `beats_satisfied` is a free-text list read by **four** sites the
original proposal did not enumerate (Scripture: `refactor_orphans_secondary`).
Changing the director to emit *indices* without addressing these would silently
break Final Cut fidelity and the UI:

- `_canonicalize_beats` (turn_ops.py, FR-491) — unions free-text phrases, sets
  `beats_total = 0`. **Replaced** by the ledger.
- `_clamp_phase` (turn_ops.py, FR-481) — monotonic phase clamp. **Subsumed** —
  a phase computed from a monotonic satisfied-count is monotonic by construction.
- `chapter_beats` / `final_cut_context` (turn_ops.py, FR-492) — union the
  free-text phrases and hand them to the Final Cut as the chapter's fidelity
  signal. Must keep reading **text**.
- `director_card.html` — renders `beats_satisfied` as text and `beats_total`.

**Resolution (minimal blast radius):** the director returns satisfied **indices
over the enumerated list**, but `_direction_dict` **resolves them back to the
canonical beat text** before persisting. The stored `beats_satisfied` stays a
list of strings and `beats_total` becomes `len(beats)`. Therefore Final Cut, the
UI, and `chapter_beats` need **no change** — only their input becomes finite and
deduped. Only the director schema, the scene assembly, and the new
phase/completion computation change.

### J2 — Soften the completion claim; the cap remains the backstop

"`scene_complete` can never stall" is too strong. If the director refuses to mark
the final beat, the chapter still will not complete. The honest claim: completion
stops being an **unbounded free-text guess** and becomes a **bounded `k / N`
signal** — a stall is now *observable* (the card shows `4 / 5`) and the FR-501 cap
remains the deterministic backstop. The win is observability + a denominator, not
the elimination of all stalls.

### J3 — Pin the phase truth table; forbid the climax/resolved collapse

With discrete beats, `climax` and `resolved` can collapse (both = "last beat
satisfied"). The derivation must be explicit and is frozen as:

| satisfied (s) of total (N) | phase |
|---|---|
| `s == 0` | `opening` |
| `0 < s < N - 1` | `rising` |
| `s == N - 1` | `climax` |
| `s == N` (and `N >= 1`) | `resolved` |
| `N == 0` (no enumerated beats) | fall back to FR-491 free-text behaviour |

`scene_complete = (N >= 1 and s == N)`. The `N == 0` fallback is mandatory: a
chapter whose outline produced no beats must still play and close via the existing
path, never divide-by-zero.

### J4 — The witness must be the same-provider, same-premise regen

The acceptance witness is a Floodmark regen on **azure** (the 4/6-capped
baseline), scored by `book_reviewer`. Success = cap fires on a **minority** of
chapters AND engagement mean rises above the 1.83 azure baseline. This is the live
witness; record it in the FR on enforce, not a unit assertion.

### Out of scope (held firm)

FR-502 resume, book-level revision, and the `closed_by` degradation flag (FR-501
Seed) remain out. The `N == 0` fallback keeps FR-491's free-text path alive rather
than deleting it — that deletion, if desired, is a separate follow-up once all
outlines reliably emit beats.

**Enforce regime:** FR-474 J3 — no CAP file, no `req` markers; honest
`feat(dungeon-master): FR-503 …` commits with an `FR-474 J3` trailer, a changelog
fragment, and a diary reflection. TDD: the phase/completion truth table (J3) and
the index→text resolution (J1) are pure functions — write their failing unit
tests first.

## References

- FR-501 — per-chapter turn budget (the backstop this FR aims to make rare again)
- FR-499 — structured world_state ledger (the boundary-normalization precedent)
- FR-497 — `book_reviewer` (the regression oracle and the "compute, don't ask" precedent)
- FR-491 — cumulative `beats_satisfied` (the free-text accumulator this FR replaces)
- Diary: `docs/diary/diary-2026-06-16-the-score-that-changed-its-meaning.md`
