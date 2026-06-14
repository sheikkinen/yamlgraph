# FR-482: DM v2 — Cumulative `beats_satisfied` via Canonical BEATS Matching

**Priority:** LOW
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). Scope frozen to **M1 (deterministic fuzzy match
in code) + cumulative canonical persist**. M2/M3 (director returns indices)
rejected. Card `k / N` count IN. See *Judgement*. **Implemented (2026-06-14)**,
after FR-481 — see *Implementation Status*.
**Effort:** ~0.5 day (prototype)
**Requested:** 2026-06-14
**Judged:** 2026-06-14
**Continues:** FR-481 (director card & arc integrity). This is the **J3 split-out**
— the `beats_satisfied` contract concern Judgement deferred out of FR-481 because
a correct cumulative union is a fuzzy-matching problem, not a free-string union.
Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**; the walkthrough
tests under `examples/dungeon_master/tests/` are a visibility harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

The director's `beats_satisfied` field has an **undefined contract** — it
oscillates between cumulative (all beats so far) and incremental (this turn's new
beat) across turns. Define it as **cumulative** and make it deterministically
correct by matching each turn's reported phrases against the **canonical `BEATS`
parsed from the frozen `key_scene.text`**, rather than accumulating the model's
free-text phrases (which paraphrase turn to turn and would accumulate
near-duplicates).

## Value Statement

`beats_satisfied` becomes a trustworthy progress signal: a stable set of *which
canonical beats* have been satisfied, with a count that does not lie. The
Director card (FR-481 A) gains a "3 / 8 beats" progress readout that monotonically
fills toward the scene's end, instead of a wobbling list whose size depends on
whether the model felt cumulative this turn.

## Problem

Evidence — run `outputs/dungeon-master/6eae1ce5/`, `beats_satisfied` per turn:

```
T1: [1 beat]   incremental (opening)
T4: [4 beats]  cumulative
T5: [1 beat]   incremental
T6: [1 beat]   incremental
T7: [7 beats]  cumulative
T8: [1 beat]   incremental
T9: [1 beat]   incremental
```

The field's meaning changes turn to turn, so no consumer can rely on it. The
prompt (`turn_direct.yaml`) says "the BEATS that have now actually occurred"
(implying cumulative) but `gemini-3.5-flash` does not honor it consistently.

### Why a naive union is wrong

The director copies beats "as short phrases" that **drift in wording** turn to
turn. Across run `6eae1ce5` the same underlying beat appears as both
`"Taka pulls Jarek out of the quicksand."` and near-variants. A naive
`set().union(...)` of the model's free strings would accumulate paraphrases as
distinct entries — the count would over-report and the set would never stabilize.
The honest cumulative set must be expressed in the scene's **own** canonical beat
vocabulary, not the model's per-turn phrasing.

## Proposed Solution

Parse the scene's authoritative beats once, then match each turn's reported
phrases onto that fixed vocabulary and persist the cumulative satisfied subset.

### Deliverable — Canonical-beats cumulative union

- **Parse canonical BEATS** from the frozen `key_scene.text`'s `BEATS:` block
  (the scene is already frozen before turn 1; `turn_ops` can read it once). This
  yields an ordered list of N canonical beat strings.
- **Match each turn's `beats_satisfied`** phrases against the canonical list.
  Design alternatives (for the Judge):
  - **M1 — Deterministic fuzzy match in code** (`turn_ops.py`): normalized
    token-overlap / `difflib.SequenceMatcher` ratio against each canonical beat,
    threshold to accept. Model-independent, testable, no extra LLM call.
  - **M2 — Director returns canonical indices.** Change `turn_direct.yaml` to
    have the director report satisfied beats by their **index** into the
    key-scene BEATS list (the scene is in its context). Eliminates fuzzy matching
    entirely — the model maps its judgement to the canonical vocabulary at source.
    Risk: relies on the model counting/indexing correctly.
  - **M3 — Hybrid:** director returns phrases (unchanged), code matches to
    canonical indices (M1), and the *persisted* field is the cumulative set of
    canonical beats by index.
  - Lean: **M2** (normalize at the judgement boundary — the director already has
    the scene, so let it speak the scene's vocabulary) with an **M1 fallback**
    for phrases that don't resolve to an index. The Judge should weigh M2's
    model-trust against M1's determinism.
- **Persist cumulatively** in `invoke_turn`: the recorded `beats_satisfied` for
  turn _n_ is the union of turn _n_'s matched canonical beats with turn _n−1_'s
  recorded set — always the full satisfied subset, expressed in canonical terms.
- **Surface a count** (`k / N`) on the Director card (FR-481 A) once the field is
  reliable.

## Acceptance Criteria

- `beats_satisfied` on turn _n_ ⊇ `beats_satisfied` on turn _n−1_ (cumulative,
  monotonic) for a multi-turn scene — a test asserts the superset relation.
- Every entry in a turn's `beats_satisfied` is one of the canonical BEATS parsed
  from `key_scene.text` (no paraphrase leakage) — a test asserts subset of the
  canonical set.
- A turn that reports the same beat under drifted wording does not add a
  duplicate — a test feeds two paraphrases of one canonical beat and asserts the
  satisfied count increments by exactly one.
- Full walkthrough suite GREEN; `ruff check` clean; `yamlgraph graph lint` clean
  on any changed graph YAML.

## Open Questions (for the Judge)

1. **Matching strategy:** M1 (deterministic fuzzy), M2 (director returns
   indices), or M3 (hybrid)? Lean M2 + M1 fallback.
2. **Threshold / tie-breaking** for M1/fallback fuzzy matching — accept the
   best-ranked canonical beat above a ratio, or require a margin over the
   runner-up?
3. **Card count display** — ship the `k / N` readout in this FR, or leave the
   card showing the (now-canonical) list and defer the count?

## Implementation Notes

- Depends on FR-481 A (the Director card) for the surfacing half; the
  data-correctness half (parse + match + cumulative persist) stands alone in
  `turn_ops.py` and can land independently.
- Persistence belongs in `turn_ops.invoke_turn` where the turn record is written,
  alongside the FR-481 B2 phase clamp — both normalize the director dict at the
  same boundary before it is recorded.
- TDD: RED test first (SKIP=pytest split), then GREEN.
- Changelog fragment required (`type: feat, scope: examples`, no `req:`).
- Diary reflection with a Seed on completion.

## Judgement (2026-06-14)

Scope frozen to **M1 (deterministic fuzzy match) + cumulative canonical
persist**, with the **`k / N` count** on the card. **Depends on FR-481** landing
first (the card and the `invoke_turn` clamp boundary). Authority granted.

**J1 — Matching strategy: M1 (deterministic fuzzy), not M2/M3.** Resolves *Open
Question 1*. M2 (director returns canonical indices) and the M2 half of M3 are
**rejected**: the motivating defect is that `gemini-3.5-flash` *cannot reliably
speak the field's contract* — it oscillates cumulative/incremental despite an
explicit prompt instruction. Asking the same model to also count and index
correctly into the BEATS list trusts the very faculty that already failed, and
moves a deterministic problem (string → canonical-beat) into the model. The beats
are frozen in `key_scene.text` before turn 1; matching the director's free
phrases onto that fixed vocabulary is a **closed, testable, code-side** problem.
Normalize at the boundary where the data is *certain* (the frozen scene), not
where it is *unreliable* (the model's per-turn phrasing). M1 it is; the director
prompt is left unchanged (it keeps returning phrases).

**J2 — Threshold: best-match-above-floor with a required margin.** Resolves *Open
Question 2*. Use `difflib.SequenceMatcher` ratio on normalized strings (lowercase,
strip punctuation, collapse whitespace) against each canonical beat. Accept the
best-ranked canonical beat **only if** its ratio clears an absolute floor (lean
`0.6`) **and** beats the runner-up by a margin (lean `0.1`) — the margin prevents
a phrase that is equally close to two beats from being mis-assigned. A phrase
that clears no canonical beat is **dropped, not invented** (Commandment 6: a
filter that yields nothing raises/omits rather than substituting a wrong beat).
Thresholds are constants at the top of the matching function, tunable without
structural change; the paraphrase-dedup acceptance test pins the behaviour.

**J3 — Persist cumulative canonical set, order-stable.** The recorded
`beats_satisfied` for turn _n_ is the union of turn _n_'s matched canonical beats
with turn _n−1_'s recorded set, **emitted in canonical BEATS order** (not match
order, not insertion order) so the displayed list reads as scene progression.
This lands in `turn_ops.invoke_turn` at the same boundary as the FR-481 B2 phase
clamp — one normalization pass over the director dict before it is recorded.

**J4 — Card count: `k / N` IN.** Resolves *Open Question 3*. Once the field is a
reliable subset of N canonical beats, the count is trivially correct and is the
whole point of the cleanup — ship it on the FR-481 Director card. `N` = parsed
canonical beat count; `k` = `len(beats_satisfied)`. If the `key_scene.text` has no
parseable `BEATS:` block (older/edited scenes), `N` is unknown — the card shows
the list without a count rather than a misleading `k / 0`.

**J5 — Sequencing.** This FR **must land after FR-481**. The persist step shares
`invoke_turn` with the B2 clamp, and the count consumes the Director card. Do not
enforce FR-482 until FR-481 is committed.

**J6 — Regime + TDD.** Inherits FR-474 J3 (no CAP/REQ/gate/demo-log; walkthrough
tests are a visibility harness, not a CI gate). `changelog-required` hook still
applies — one fragment (`type: feat, scope: examples`, no `req:`). RED test first
(SKIP=pytest split), then GREEN. The three acceptance tests — superset/monotonic,
subset-of-canonical, paraphrase-dedup-counts-one — are mandatory. `ruff check` and
`yamlgraph graph lint` clean.

**Authority granted** for M1 + cumulative canonical persist + `k / N` count,
**after FR-481 lands**.

## Implementation Status (2026-06-14)

Shipped **M1 + cumulative canonical persist + `k / N` count**, on top of FR-481
(committed first). All in `examples/dungeon_master/api/turn_ops.py`.

| Piece | Status | Where |
|---|---|---|
| `parse_beats(key_scene_text)` — BEATS bullets between labels | ✅ | `turn_ops.py` |
| `_match_beat` — difflib floor `0.6` + margin `0.1`, drop-if-none | ✅ | `turn_ops.py` |
| `_canonicalize_beats` — cumulative canonical union, scene order | ✅ | `turn_ops.py` |
| `beats_total` on the direction dict | ✅ | `turn_ops.py` |
| `k / N` count on the Director card | ✅ | `director_card.html` (FR-481) |

**Decisions / notes:**

- **M1 with the judged thresholds.** `_match_beat` ranks canonical beats by
  `SequenceMatcher` ratio on normalised text (lowercase, strip punctuation,
  collapse whitespace), accepts the best only if it clears `_BEAT_FLOOR = 0.6`
  **and** beats the runner-up by `_BEAT_MARGIN = 0.1`. A phrase clearing nothing
  is dropped, never invented (Commandment 6). Thresholds are module constants.
- **Cumulative in scene order.** `_canonicalize_beats` maps the prior turn's
  (already-canonical) beats back to indices, adds this turn's matched indices,
  and emits `[canonical[i] for i in sorted(indices)]` — a running union read as
  scene progression. Lands in `invoke_turn` right after the FR-481 B2 phase clamp
  (one normalisation pass over the director dict before it is recorded).
- **No-BEATS fallback (J4).** When `parse_beats` finds no block, there is no
  vocabulary to bind to: the raw phrases are kept (still cumulative,
  de-duplicated) and `beats_total = 0`, so the card shows the list without a
  misleading `k / 0`. (This is what keeps the FR-480 phantom test — which
  overwrites the scene with a BEATS-less line — green.)
- **Director prompt unchanged.** M2 (asking the model to return canonical indices)
  was rejected at judgement; `turn_direct.yaml` still returns free phrases, which
  the code binds.
- **Tests (FR-474 J3 visibility harness, no `req` tag):** cumulative-and-canonical
  (turn 2 ⊇ turn 1, subset of parsed BEATS, `beats_total` = N), paraphrase-dedupe
  (two wordings of one beat → count 1), card `1 / 2` count rendered, `parse_beats`
  unit, and `_match_beat` accept/drop unit. The test mock `key_scene` gained a
  BEATS block so the canonical vocabulary exists. Full suite **31 passed**;
  `ruff check` + `ruff format` clean; `yamlgraph graph lint turn.yaml` clean.

**Seed carried forward (from FR-481 J3):** the threshold pair `0.6 / 0.1` is
tuned to the prototype's terse beats; a production scene with longer, clause-rich
beats may need different constants or a token-set ratio. Revisit if a real run
shows a legitimate beat dropped.
