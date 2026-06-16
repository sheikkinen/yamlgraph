# Feature Request: FR-504 — Retire the FR-491 free-text beat fallback (post-ledger purge)

**Priority:** MEDIUM
**Type:** Refactor (dead-code removal)
**Status:** Enforced — code GREEN (116 DM tests), single beat regime (2026-06-16)
**Effort:** < 0.5 day → revised **~1 day** (test blast radius)
**Requested:** 2026-06-16

## Blocker status (2026-06-16) — both CLEARED

- **B1 (sequencing) — CLEARED.** FR-503's J4 live witness landed: azure Floodmark
  regen `outputs/dungeon-master/10005-BC/story.json`. Every one of its 8 chapters
  carries a non-empty `beats` list (4–6 each), and the FR-501 cap dropped to a 2/8
  minority. The go/no-go signal (R1) is GREEN — real outlines reliably emit beats,
  so making `beats` a mandatory boundary contract rejects only malformed outlines,
  not observed ones.
- **B2 (blast radius) — ACKNOWLEDGED, scope honoured.** The mock `chapter_outline`
  is updated to emit beats in the SAME commit as the contract (R2); the full
  six-test free-text cluster + the two dead mock helpers are retired (R3); monotonic
  coverage is re-homed onto the computed ledger.

## Judgement (2026-06-16)

**Verdict: the direction is right; authority is WITHHELD pending two blockers.**
The entropy argument is sound — two beat regimes for one judgement is exactly the
duplication Scripture forbids, and the inventory of production artifacts
(`_canonicalize_beats`, `_PHASE_ORDER`/`_clamp_phase`, the `N == 0` branch) is
accurate against the post-FR-503 code now on disk. But the FR may **not** proceed
yet, for two reasons:

### Blocker 1 — the blocking precondition is unmet (sequencing)

FR-504's own premise is "once FR-503 has shipped **and outlines reliably emit a
non-empty `beats` list**." FR-503 shipped (commit `76f2607d`), but its **J4 live
witness has not been produced** — the azure Floodmark regen was interrupted
(exit 130) before a single book proved that real outlines carry beats and that the
cap-firing rate dropped. Making `beats` a mandatory boundary contract (step 1)
**before** that proof would mean rejecting outlines we have never observed. The
J4 witness is the literal go/no-go signal; until it exists, FR-504 is blocked.

### Blocker 2 — the test blast radius is materially understated (`partial_remediation`)

FR-504 names **two** test impacts (the `_clamp_phase` unit test and one
`beats_total == 0` assertion). The real radius is the **whole suite**, via two
mechanisms the FR misses:

1. **The mock outline emits no beats.** `_mock_execute_prompt`'s `chapter_outline`
   branch returns `{title, summary}` with **no `beats`** (test_turn_prototype.py
   ~93). Every test that drives `_reach_play` flows through `expand_chapters`; once
   step 1 requires `len(beats) >= 1` at that boundary, **all ~115 play-path tests
   raise** at setup, not just the two named. The mock outline **must** be updated
   to emit beats as part of this FR — a precondition, not an afterthought.

2. **A six-test free-text cluster is retired, not two.** These exercise the path
   being deleted and will not survive the mock change (they assert free-text-only
   behaviour the ledger replaces):
   - `test_phase_is_clamped_monotonic` (501) — drives `_clamp_phase` via a mock
     that returns free-text phases; once beats exist, phase is computed, not clamped.
   - `test_clamp_phase_floors_at_prior_but_allows_advance` (522) — unit test of the
     deleted helper.
   - `test_beats_satisfied_is_cumulative_and_canonical` (572) — asserts
     `beats_total == 0`; false once beats exist.
   - `test_paraphrases_of_one_beat_dedupe_to_one` (602) — free-text dedup semantics.
   - `test_director_card_shows_beat_count` (626) — asserts `"/ 0" not in text`;
     the card will now show `k / N`.
   - `test_apply_beat_ledger_n_zero_falls_back_to_freetext` (946) — **FR-503's own
     fallback test**, which tests the very branch FR-504 removes; it must be
     deleted, not merely "converted".

   The helpers `_phase_execute_prompt` and `_beats_execute_prompt` become dead once
   their tests are removed — `vulture` will flag them; delete them too.

### Refinements folded into scope (binding before authority is granted)

- **R1:** Add a go/no-go gate: FR-504 starts only after FR-503's J4 witness shows
  a real azure book where every chapter carries a non-empty `beats` list. Cite the
  witness `story.json` path in FR-504 before the first commit.
- **R2:** The mock `chapter_outline` (and any fixture outline) must emit `beats`;
  this is step 0 of the enforce, landed in the **same** commit as the contract so
  the suite never goes red mid-change.
- **R3:** Retire the full six-test free-text cluster + the two now-dead mock
  helpers, not the two items originally listed. Replace coverage where the
  *behaviour* still matters (monotonic phase is now a property of the computed
  ledger — assert it on the ledger, e.g. extend `test_phase_for_count_truth_table`
  or add a cumulative-monotonic ledger test — rather than on the deleted clamp).
- **R4:** Keep the boundary-rejection test (an empty/missing `beats` outline is
  rejected with a clear error) — this is the one genuinely new test and the proof
  the contract holds.

### What stays correct

The core move (single ledger path, `beats` as a validated boundary contract,
`the_one_law` normalization at the outline seam) and the scope guards (the v1
`purgatory/` tree out of scope; FR-502/revision/`closed_by` out of scope) are all
endorsed. Enforce regime is FR-474 J3 (`refactor(dungeon-master): FR-504 …`,
`FR-474 J3` trailer, changelog `type: removal`, diary).

**Next action:** complete FR-503's J4 azure witness first. If it confirms reliable
beats + a reduced cap rate, FR-504's blockers clear and it proceeds with the R1–R4
scope. If the witness shows outlines sometimes omit beats, FR-504 is **rejected**
in its current form (the fallback is load-bearing, not dead) and returns to Plan.

## Summary

FR-503 replaces the director's unbounded free-text beat judgement with a finite,
enumerated, computed beat ledger — but, to bound its blast radius, it **keeps** the
old FR-491 free-text accumulator alive as the `N == 0` (no enumerated beats)
fallback. Once FR-503 has shipped and outlines reliably emit a non-empty `beats`
list, that fallback is dead weight: a second, divergent code path that can only be
reached by a malformed outline. This FR removes it and makes a non-empty `beats`
list a **validated boundary contract**, so there is exactly one beat-judgement path.

## Problem

FR-503 leaves two coexisting beat regimes:

1. **Ledger path** (FR-503): director returns satisfied indices over an enumerated
   `beats` list; `phase`/`scene_complete` computed from `k / N`.
2. **Free-text fallback** (FR-491): when a chapter has `N == 0` beats,
   `_canonicalize_beats` unions free-text phrases (`beats_total = 0`) and
   `_clamp_phase` floors the LLM-reported phase.

Two paths for one judgement is exactly the entropy Scripture forbids ("kill all
entropy and false idols… no shims, no adapters, no 'compat' flags"). The fallback
exists only because FR-503 could not, in one change, *prove* every outline emits
beats. Carrying it indefinitely means: a divergent phase derivation, a misleading
`beats_total = 0` on the card for the fallback case, and `chapter_beats` having to
reason about both shapes forever.

## Obsolete artifacts to remove (grounded inventory)

All in `examples/dungeon_master/api/turn_ops.py` unless noted:

| Artifact | Lines (pre-503) | Disposition |
|---|---|---|
| `_canonicalize_beats` (free-text union, `beats_total = 0`) | ~307–322 | **Delete** — superseded by the ledger resolution (FR-503 J1) |
| `_PHASE_ORDER` + `_clamp_phase` | ~285–304 | **Delete IF** not already removed by FR-503 J1 (FR-503 marks it "removed or proven subsumed"); this FR is the safety net that confirms no caller remains |
| `N == 0` fallback branch in the phase/completion computation | added by FR-503 | **Delete** — unreachable once `beats` is non-empty by contract |
| `test_clamp_phase_floors_at_prior_but_allows_advance` (test_turn_prototype.py:522) | — | **Delete** with `_clamp_phase` |
| `beats_total == 0` assertion (test_turn_prototype.py:596) | — | **Replace** with a `beats_total == len(beats)` assertion |
| FR-491 free-text rationale in `chapter_beats` docstring (turn_ops.py:377) | — | **Update** — it no longer reads free-text phrases |

> Note: the v1 DM graveyard in `examples/dungeon_master/purgatory/` (FR-466/467,
> `turn-loop.yaml`, `weave-beat.yaml`, `plot.yaml`, `preplan.yaml`) is a separate,
> already-retired tree and is **out of scope** for this FR.

## Proposed Solution

1. **Make `beats` a required, non-empty boundary contract.** Add validation in the
   chapter-outline parse step (and/or the card persistence) that every chapter has
   `len(beats) >= 1`. Normalize at the boundary where the outline enters
   (Scripture: `the_one_law`), not downstream where `N == 0` would manifest.
2. **Delete the fallback.** Remove `_canonicalize_beats`, the `N == 0` branch, and
   (if still present) `_clamp_phase` / `_PHASE_ORDER`. The computed-ledger path
   becomes the sole beat regime.
3. **Update the card.** `beats_total` is always `len(beats)`; remove the
   `k / 0`-suppression special case in `director_card.html` if one remains.
4. **Update tests.** Delete the `_clamp_phase` test; convert the `beats_total == 0`
   assertion to the ledger invariant. Add a test that an outline missing/empty
   `beats` is **rejected at the boundary** (the contract), not silently fallen back.

## Acceptance Criteria

- [x] **R1 (go/no-go):** FR-503's J4 witness exists — a real azure book where every
      chapter card carries a non-empty `beats` list — and its `story.json` path is
      cited here before the first FR-504 commit. **→
      `outputs/dungeon-master/10005-BC/story.json` (8/8 chapters carry 4–6 beats).**
- [x] **R2:** the mock `chapter_outline` (and any fixture outline) emits `beats`,
      landed in the **same commit** as the contract so the suite never goes red
      mid-change. **→ `test_turn_prototype._mock_execute_prompt` and
      `test_chapters.OUTLINE` both emit beats; `_mock_direction` reports satisfied
      beats as 1-based numbers.**
- [x] Chapter outlines with an empty/missing `beats` list are rejected at the
      parse/persist boundary with a clear error; a unit test pins the rejection.
      **→ `chapter_ops._require_beats`, called by `outline_chapters`;
      `test_outline_requires_nonempty_beats`.**
- [x] `_canonicalize_beats`, the `N == 0` fallback branch, and `_clamp_phase` /
      `_PHASE_ORDER` are deleted; `vulture` reports no dead reference and `grep`
      finds no remaining caller. **→ all deleted; only historical FR docs reference
      them.**
- [x] `beats_total` is always `len(beats)`; no `k / 0` rendering path remains.
- [x] **R3:** the full free-text test cluster is retired —
      `test_phase_is_clamped_monotonic`, `test_clamp_phase_floors_at_prior_but_allows_advance`,
      `test_beats_satisfied_is_cumulative_and_canonical`,
      `test_paraphrases_of_one_beat_dedupe_to_one`, `test_director_card_shows_beat_count`,
      and FR-503's own `test_apply_beat_ledger_n_zero_falls_back_to_freetext` — plus
      the now-dead `_phase_execute_prompt` / `_beats_execute_prompt` mock helpers.
- [x] Monotonic-phase coverage is preserved as a **property of the computed ledger**
      (`test_apply_beat_ledger_phase_is_monotonic_under_accumulation`), not via the
      deleted clamp.
- [x] DM unit suite green (116 passed); a Floodmark regen still produces a valid
      book (10005-BC: every chapter hits the ledger path, none the removed
      fallback).

## Notes / Scope

- FR-474 J3 regime: no CAP file, no `req` markers; `refactor(dungeon-master):
  FR-504 …` commits with an `FR-474 J3` trailer, a changelog fragment (`type:
  removal`), and a diary reflection.
- **Sequencing:** this FR must not start until FR-503 is enforced and a regen has
  demonstrated every chapter carries a non-empty `beats` list (otherwise the
  contract in step 1 would reject real outlines). FR-503's J4 witness is the
  go/no-go signal for FR-504.

## References

- FR-503 — finite beat ledger (the change this FR cleans up after)
- FR-491 — cumulative free-text `beats_satisfied` (the path this FR retires)
- FR-481 — monotonic phase clamp (`_clamp_phase`, subsumed by the computed phase)
- FR-492 — `chapter_beats` / Final Cut fidelity (consumer whose docstring updates)
- Scripture: `kill all entropy and false idols`; `the_one_law` (normalize at the
  boundary); `refactor_orphans_secondary`
