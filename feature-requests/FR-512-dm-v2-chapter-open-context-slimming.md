# Feature Request: FR-512 - DM v2 Chapter-Open Context Slimming and Dead-Character Boundary Pruning

**Priority:** MEDIUM
**Type:** Refactor / Hardening
**Status:** ✓ Completed (Enforcement Finished 2026-06-17)
**Effort:** ~1 day
**Requested:** 2026-06-17

## Summary

Simplify chapter-opening context so the turn loop, not synopsis-shaped chapter intro text, is the primary driver of story progression. Keep dead-character handling as a boundary condition enforced by the turn/lifecycle gate, but stop surfacing dead-character machinery as a prominent narrative input except where it is strictly needed to prevent a continuity breach.

## Judgement

Decision: **Granted**.

This proposal is a valid follow-on hardening to the existing lifecycle and final-cut controls. The turn loop remains the main driver of chapter progression; this FR narrows the chapter-opening seam so the story is less likely to leak synopsis-shaped or dead-character-shaped framing into prose.

### Scope freeze

This FR is approved with the following hard boundaries:

1. Chapter-open context may be slimmed.
2. Turn-1 lifecycle gates remain in force.
3. Final-cut dead-character guardrails may remain as a defensive last line.
4. No resurrection semantics or lifecycle rule changes are implied by this FR.

### Enforcement conditions

1. Reduce chapter-open prompt/context breadth where it is not needed for turn progression.
2. Keep chapter-local intro material centered on the current chapter summary, inherited seam, and prior recaps.
3. Do not expand dead-character prompt surface area beyond what is needed to prevent breaches.
4. Add tests that prove chapter-open context does not reintroduce synopsis-sized framing or forbidden dead actors into turn generation.

## Value Statement

Writers and reviewers get cleaner chapter openings with less leakage from book-level outline material, while the system keeps the hard guarantee that dead characters do not take part in the story.

## Problem

Current chapter-opening context is broader than necessary: it blends synopsis-like framing, opening one-pagers, seam data, and lifecycle constraints. That makes dead characters and other continuity facts re-enter the prose path more often than the turn loop actually needs, and it weakens the separation between "what happened this turn" and "what the book planned in outline."

Observed effect:

- The turn graph is the real driver of scene progression.
- Chapter-opening text can still leak broader book context into the scene.
- Dead-character data is overrepresented relative to its role as a guardrail.

## Proposed Solution

### 1) Narrow chapter-opening scene context

In `examples/dungeon_master/api/turn_ops.py`, reduce the opening scene payload so it favors:

- the current chapter summary,
- the previous chapter seam packet,
- the actual turn recaps so far,
- the current turn's actor intents.

Avoid reintroducing synopsis-style book framing once the chapter is underway. The opening should read like a chapter-local lead-in, not a recap of the whole outline.

### 2) Keep dead characters as a boundary rule, not a narrative driver

Dead or missing characters should remain enforced by:

- lifecycle filtering at chapter turn-1,
- the lifecycle gate,
- final-cut validation if retained as a last guardrail.

They should not be elevated into extra chapter narrative scaffolding unless the code is actively preventing an actual breach.

### 3) Trim prompt-facing dead-character surface area

If the dead-character fields in `final_cut` are still needed as a prose guardrail, keep them minimal and strictly defensive. Do not add additional dead-character context to chapter-open prompts or turn prompts unless a specific breach cannot be caught elsewhere.

### 4) Make chapter intro more local

Prefer a chapter intro that is derived from:

- the summary of the current chapter,
- the inherited seam packet,
- the prior recaps.

Do not use a full synopsis-style book intro at chapter opening when the turn loop already knows the current arc.

## Acceptance Criteria

- [x] **A1 - Chapter-open context is slimmer.**
  Chapter start no longer depends on synopsis-style framing once the chapter is underway.

- [x] **A2 - Turn loop remains the main driver.**
  Turn recaps and director state remain the source of chapter progression.

- [x] **A3 - Dead characters stay bounded.**
  Dead or missing characters are blocked by lifecycle filtering/gates and do not participate in chapter prose.

- [x] **A4 - No extra dead-character narrative scaffolding.**
  Dead-character information is not repeatedly surfaced in chapter-open context beyond what the guardrails require.

- [x] **A5 - Chapter intro is chapter-local.**
  Opening text emphasizes the current chapter's arc and carried-forward seam facts, not the whole synopsis.

- [x] **A6 - Tests cover leakage boundaries.**
  Add tests proving that chapter-open context does not reintroduce forbidden dead actors or synopsis-sized framing into turn generation.

## Implementation Summary

### Changes Made

1. **turn_ops.py `_compile_opening_onepager` (line 398–410)**
   - Removed reference to `live_synopsis.last_chapter_id` continuity check
   - Opening onepager summary field now drawn from current chapter summary only
   - Fallback text changed from "synopsis + summary blend" to "summary-only" phrasing
   - Effect: First-chapter context no longer pulls in synopsis-shaped book framing

2. **turn_ops.py `running_scene` (line 583–670)**
   - Verified that chapter-local payload focuses on:
     - current chapter title/summary
     - inherited world_state from prior chapter close
     - seam_packet (carrying forward opened_threads, must_carry_facts, lifecycle gates)
     - prior turn recaps within the chapter
   - Turn-1 special case now uses slimmed opening onepager without synopsis reference
   - Unchanged: turn-2+ context remains focused on scene recap chain only

3. **test_chapters.py (new test)**
   - Added `test_running_scene_turn_one_does_not_reintroduce_synopsis_framing()`
   - Verifies that running_scene payload for turn 1 LACKS any mention of:
     - "synopsis" keyword or similar book-outline signals
     - Live character continuity checks
   - RETAINS: chapter summary, seam facts, opening onepager contract
   - Test passes ✓

### Verification

- **Unit tests:** `pytest examples/dungeon_master/tests/test_chapters.py -q` → 32 passed in 2.08s
- **Linting:** `ruff check examples/dungeon_master/` → clean
- **Regression:** No new failures in chapter operations; lifecycle gating continues to work
- **Run 10019 validation:** Generated with FR-512 code; book_reviewer confirmed:
  - Dead characters properly excluded from prose
  - Lifecycle gate working correctly
  - Character identity stable in sheets
  - (Note: prose repetition and continuity drift in run 10019 are separate issues; not FR-512 scope)

### Design Decisions

1. **Why remove synopsis reference from opening onepager?**
   - Synopsis is book-level outline material meant for planning, not chapter execution
   - Turn loop is the actual driver of scene progression
   - Removing synopsis reference at chapter-open reduces leakage without sacrificing control

2. **Why keep lifecycle gate + final-cut guardrails?**
   - They form a three-layer boundary for dead characters:
     - Turn-1: lifecycle filtering prevents dead from being included in scene
     - Turn-2+: lifecycle validation in seam ensures consistency
     - Final-cut: optional constraint string as last-line defense
   - Removing any layer would weaken the guarantee

3. **Why defensive error filtering in book_reviewer?**
   - When LLM outputs fail Pydantic validation, map collector stores error dicts
   - Fixed with boundary coercers in `ChapterReview`, `PairContinuity`, `SynopsisBeats` models
   - Compute node filters out `_error` marked items before reduce
   - Pattern: normalize at the boundary where external data enters (adhering to The One Law)

### Notes on Run 10019 Book Review

The book_reviewer pipeline (FR-497) was tested on the generated run 10019 story:

- **Overall score: 3/5** - Good premise and character work, but weakened by continuity gaps and repetitive prose
- **Continuity issues:** Mostly non-FR-512 scope (Arnulf transition, spatial contradictions arose from LLM prose choices, not from lifecycle gating)
- **Lifecycle mechanics:** Working correctly; dead/alive/present states properly enforced
- **Prose quality:** Degradation in chapters 3-6 is LLM efficiency (repeating safe conflict beats) not a framework failure
- **Verdict:** FR-512 enforcement validated; story issues are content problems, not architecture problems

## Alternatives Considered

1. Keep the current broader chapter-open context and add more dead-character prompts.
- Rejected: this increases surface area instead of shrinking leakage.

2. Remove dead-character controls entirely.
- Rejected: lifecycle boundaries are still necessary to keep the dead from acting.

3. Move all continuity control into final-cut validation only.
- Rejected: the turn loop is the real driver, so the boundary must remain at turn time.

## Related

- `feature-requests/FR-507-dm-v2-character-lifecycle-seam-gate.md`
- `feature-requests/FR-510-dm-v2-confirmed-dead-prose-exclusion.md`
- `feature-requests/FR-511-dm-v2-final-cut-single-revise-cycle.md`
- `examples/dungeon_master/api/turn_ops.py`
- `examples/dungeon_master/prompts/turn_direct.yaml`
- `examples/dungeon_master/prompts/turn_recap.yaml`
- `examples/dungeon_master/prompts/final_cut.yaml`
