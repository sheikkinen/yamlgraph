# Feature Request: DM v2 Chapter Entry/Exit State Contracts + Outline Composition Gate

**Priority:** MEDIUM (root-cause fix for the cross-chapter discontinuity class; structural)
**Type:** Feature
**Status:** Judged — Approved with conditions (scope frozen 2026-06-19)
**Effort:** ~1.5 days
**Requested:** 2026-06-19

## Summary

A chapter card today carries a one-paragraph `summary` (the arc), `beats` (the finite
event ledger), and — since FR-537 — a focal `cast`. What it does **not** carry is a typed
statement of **what is true at the chapter's open** (`entry_state`) and **what must be true
at its close** (`exit_state`). Without those, the only cross-chapter contract is the
inherited `world_state` ledger — a *derived* artifact the partitioner never sees and cannot
validate. So two adjacent chapters can be each locally coherent yet **fail to compose**:
chapter N ends in isolated grief, chapter N+1 opens mid-crowd with no transition (10029-BC
Ch2→Ch3). This FR adds entry/exit contracts as **authored, structured** chapter fields and
makes the outline partitioner **validate that consecutive chapters compose** — a re-rollable
authoring gate, in the same family as the FR-525 reversal-pack and FR-528 epilogue gates.

This is a **scope/plot** contract, distinct from FR-537 (who is in the chapter) and from
FR-538/539 (staging a character's *entrance* in prose). It governs the *state seam*, not the
roster and not the entrance prose.

## Value Statement

A book architect (and the partitioner that re-rolls a bad outline) catches a
chapter-to-chapter discontinuity **at outline time** — "Ch3 opens with an assembled group,
but Ch2 closes with two people alone on a ledge" — turning a silent mid-book prose surprise
into a detectable, re-rollable authoring error before a single turn is played.

## Problem

The turn loop is a *local sampler*: it guarantees turn N follows from turn N−1, nothing
more. Cross-chapter coherence rests entirely on the inherited `world_state` ledger, which:

1. the **partitioner never sees** (it authors `summary`/`beats`/`cast`, then chapters are
   played and the ledger is derived at close), so it cannot author a chapter to *open from*
   the prior chapter's close; and
2. is **prose-rendered into `running_scene`** where a 0.7-temperature sampler may ignore or
   contradict it.

The result is the 10029-BC cross-chapter break class:
- Ch2→Ch3: isolated-grief close → assembled-crowd open, no transition (review: "completely
  different social and emotional context with no transition").

The cheapest plot bug is the one killed in the outline. Today there is no outline-time
representation of a chapter's opening/closing state to validate against its neighbours.

## Proposed Solution

### 1. Two new authored chapter fields (outline boundary)

Extend `chapter_outline.yaml` to emit, per chapter:
- **`entry_state`**: 1–2 sentences naming the social/physical configuration true at the
  chapter's *open* — who is present, where, in what relation.
- **`exit_state`**: 1–2 sentences naming the configuration that must be true at *close* — the
  hand-off the next chapter inherits.

Parse in `outline_ops.outline_chapters` (a `_state_field` helper beside `_beat_list`/
`_cast_list`); store on each card in `doc_ops.expand_chapters` (beside `cast`), normalized at
the boundary (`the_one_law`).

### 2. Deterministic composition gate (outline re-roll)

A pure `gap_detectors.composition_gap(chapters)` that checks each adjacent pair: does
chapter N+1's `entry_state` *compose* with chapter N's `exit_state`? v1 is **deterministic and
narrow** — flag only the mechanical incompatibilities we can check without an LLM:
- a character named present in N+1 `entry_state` whom N `exit_state` placed absent/lost (and
  no lifecycle reappearance authorizes it),
- a location/configuration in N+1 `entry_state` that N `exit_state` contradicts by an
  enumerated antonym set (present↔absent, together↔scattered) — **bounded, not free-text NLP**
  (sidesteps `regex_fourth_exclusion`: only match known roster names / a closed antonym set).

**Scope boundary (judged Condition 1) — carve against `seam_precondition_gap`.**
`gap_detectors.seam_precondition_gap` already owns the **physical lethal-seam** (a carried-alive
actor killed by a hazard with no reposition beat bridging the move). `composition_gap` is its
**social/relational-configuration** twin (isolated↔assembled, who-is-together) and MUST NOT
re-detect the lethal-position case — that belongs to its sibling. The docstring states this
boundary explicitly.

**Frozen antonym set (judged Condition 2).** v1 matches exactly: roster names + the closed
antonym set `{present↔absent, together↔scattered}`. A fourth special-case branch is the
`regex_fourth_exclusion` trap → escalate to the deferred LLM tier, never widen the regex.

On a hit, re-invoke the partitioner with the violation fed back (bounded retry like FR-525/
FR-528), then raise — never emit a non-composing outline (Commandment 6: no silent fallback).

### 3. Feed `entry_state` into `running_scene` turn-1 context

Surface the authored `entry_state` as an explicit turn-1 framing block (beside the existing
seam contract), so the opening turn plays *from* the contracted open rather than reconstructing
it from the ledger alone.

## Acceptance Criteria

- [ ] `chapter_outline.yaml` emits `entry_state`/`exit_state`; `outline_ops` parses them;
      `expand_chapters` stores them per card.
- [ ] `gap_detectors.composition_gap` flags an adjacent pair where N+1 `entry_state` asserts a
      character present whom N `exit_state` placed absent (no lifecycle reappearance), and a
      closed-antonym configuration contradiction — deterministic, roster-bounded.
- [ ] **(Condition 1)** A pure physical lethal-seam case is NOT flagged by `composition_gap`
      (it belongs to `seam_precondition_gap`); a test asserts the two detectors do not overlap.
- [ ] **(Condition 2)** The antonym set is frozen to `{present↔absent, together↔scattered}`; the
      detector matches only roster names + that closed set (no free-text NLP).
- [ ] `outline_chapters` re-rolls the partitioner on a composition gap (bounded retry) and
      raises if unresolved; never emits a non-composing outline.
- [ ] `running_scene` turn-1 surfaces `entry_state` as an explicit framing block.
- [ ] **(Condition 3)** A story authored before this FR (no `entry_state`/`exit_state`) replays
      **byte-identical** — the empty/absent contract degrades to today's behavior (additive),
      proven by a regression test, not prose.
- [ ] Unit tests: a non-composing fixture pair is flagged; a composing pair passes; the re-roll
      path is exercised with a feedback-corrected mock.
- [ ] `ARCHITECTURE.md` Module Organization / DM seam doctrine notes entry/exit contracts as
      the outline-time state seam, distinct from FR-537 cast scope and FR-539 entrance prose.

## Alternatives Considered

- **LLM-judge the composition** (ask a model "do these compose?"): rejected for v1 — a
  probabilistic gate is too soft for a hard invariant (FR-534's lesson). The deterministic,
  roster-bounded checks catch the measured 10029-BC class without a model; an LLM tier can be
  a later escalation if the deterministic set proves insufficient.
- **Derive entry/exit from the ledger instead of authoring them**: rejected — the ledger is a
  *play-time* artifact; the partitioner authors *before* play and needs an authored contract to
  validate against. Deriving it post-hoc cannot prevent a non-composing outline.
- **Fold into FR-539**: rejected — FR-539 bridges *entrance prose* at the close boundary; this
  governs *outline-time state composition*. Different boundary (outline vs close), different
  artifact (authored contract vs narrated prose). Keeping them separate avoids
  `false_duplicate`.

## Related

- [FR-537](FR-537-dm-v2-chapter-scoped-cast.md) — cast scope (who is in the chapter); this FR
  is the *state* seam alongside it
- [FR-538](FR-538-dm-v2-seam-entrance-witness.md) / [FR-539](FR-539-dm-v2-seam-aware-final-cut.md)
  — entrance *measurement* and entrance *prose staging*; orthogonal to outline-time state composition
- FR-525 / FR-528 — existing deterministic outline re-roll gates (the pattern this extends)
- [outline_ops.py](../examples/dungeon_master/api/outline_ops.py) — `_beat_list`/`_cast_list`
  parsers, `outline_chapters` re-roll loop
- [doc_ops.py](../examples/dungeon_master/api/doc_ops.py) — `expand_chapters` card boundary
- [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) — `running_scene` turn-1 framing
- [gap_detectors.py](../examples/dungeon_master/api/gap_detectors.py) — `seam_precondition_gap`
  (the **physical lethal-seam** sibling; `composition_gap` is its **social-configuration** twin)
- `examples/dungeon_master/prompts/chapter_outline.yaml` — outline schema
- `outputs/dungeon-master/10029-BC/review.md` — the Ch2→Ch3 non-composition evidence

## Judgement (2026-06-19) — APPROVED with conditions

**Verified against the codebase (claims hold):** `outline_ops.outline_chapters` carries the
FR-525/FR-528 bounded re-roll loop this extends; `_beat_list`/`_cast_list` parsers exist beside
the proposed `_state_field`; `gap_detectors.py` is the correct home; `doc_ops.expand_chapters`
is the card boundary. The pattern is real and the FR conforms to it (Commandment 4).

**Condition 1 — carve against `seam_precondition_gap` (avoid `false_duplicate`).**
`gap_detectors.seam_precondition_gap` already detects an *unbridged lethal seam* (carried-alive
actor killed by a hazard with no reposition beat) — the *physical-position* seam. `composition_gap`
must be explicitly scoped to the **social/relational configuration** seam (who-is-together,
isolated↔assembled) and must NOT re-detect the lethal-position case. State this boundary in the
docstring and add a test asserting a pure lethal-seam case is *not* flagged by `composition_gap`
(it belongs to its sibling).

**Condition 2 — the v1 closed-antonym set is the whole scope.** The deterministic check is
bounded to roster names + one enumerated antonym set (present↔absent, together↔scattered). Any
temptation to grow a fourth/fifth special-case branch is the `regex_fourth_exclusion` trap →
escalate to the deferred LLM tier instead of widening the regex. Freeze the antonym set in the FR.

**Condition 3 — additive-degradation AC is load-bearing.** The "empty/absent contract degrades
to today's behavior" AC must be a byte-level regression test, not prose; a story authored before
this FR (no `entry_state`/`exit_state`) must replay identically.

**Scope frozen.** Effort estimate (~1.5d) accepted. Distinct boundary confirmed: outline-time
authored *state* contract — neither FR-537 (roster) nor FR-539 (entrance prose). Authority granted
to enforce once Conditions 1–3 are folded into the ACs.

## Implementation (2026-06-19) — ENFORCED

- **Authored fields:** `chapter_outline.yaml` now emits `entry_state`/`exit_state`;
  `outline_ops._state_field` parses them (trim, non-string → `""`); `outline_chapters` carries
  them in each chapter dict; `doc_ops.expand_chapters` stores them per card.
- **Composition gate:** landed in a new leaf `api/composition_gap.py` (NOT `gap_detectors`, which
  is at the 449/450 size ceiling — a clean FR-536 split). `composition_gap(chapters)` checks each
  adjacent pair against the **frozen** two-concept antonym set (`together<->scattered` scene-level;
  `present<->absent` subject-bound to a roster name from the union of chapter `cast`).
- **Condition 1 (carve):** `composition_gap` reads ONLY `entry_state`/`exit_state` strings;
  `seam_precondition_gap` reads `beats` + committed `world_state`. They consume disjoint inputs and
  cannot overlap. `test_pure_lethal_seam_not_flagged_by_composition_gap` proves a lethal case fires
  the sibling and not the newcomer.
- **Condition 2 (frozen set):** exactly `{present<->absent, together<->scattered}`; documented as
  the whole scope, fourth branch → deferred LLM tier (`regex_fourth_exclusion`).
- **Condition 3 (additive):** absent contracts are skipped (`continue`) — no gap, no re-roll — so a
  pre-FR-540 outline degrades to today's behavior (`test_missing_contract_degrades_additively`).
- **Re-roll:** `outline_chapters` re-invokes the partitioner with `_composition_feedback` on a
  composition gap (bounded retry beside FR-525/FR-528), raises if unresolved.
- **Turn-1 framing:** `running_scene` surfaces `entry_state` as a `CHAPTER ENTRY STATE` block on
  `n == 1` only (`test_running_scene_surfaces_entry_state_turn_one_only`).
- 9 tests (`test_composition_gap.py`); 364 DM tests green; all gates clean.
