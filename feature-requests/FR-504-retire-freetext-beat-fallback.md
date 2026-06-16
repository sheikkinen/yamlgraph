# Feature Request: FR-504 — Retire the FR-491 free-text beat fallback (post-ledger purge)

**Priority:** MEDIUM
**Type:** Refactor (dead-code removal)
**Status:** Proposed — **blocked on FR-503 enforce**
**Effort:** < 0.5 day
**Requested:** 2026-06-16

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

- [ ] Chapter outlines with an empty/missing `beats` list are rejected at the
      parse/persist boundary with a clear error; a unit test pins the rejection.
- [ ] `_canonicalize_beats` and the `N == 0` fallback branch are deleted; `vulture`
      reports no dead reference to them.
- [ ] `_clamp_phase` / `_PHASE_ORDER` are gone (confirming FR-503 J1's subsumption);
      `grep` finds no remaining caller.
- [ ] `beats_total` is always `len(beats)`; no `k / 0` rendering path remains.
- [ ] The `_clamp_phase` test is removed; the `beats_total == 0` assertion is
      converted to the ledger invariant.
- [ ] DM unit suite green; a Floodmark regen still produces a valid book (no
      chapter hits the removed fallback).

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
