# Diary: FR-166 Pydantic count_range Extraction

**Date:** 2026-03-08
**FR:** FR-166 (verification-count-range-pydantic)
**Type:** Bug Fix

## What Happened

Verification gate demo (`examples/demos/verification-gate/`) was reporting false violations because `count_range` verification always reported 0 items for Pydantic model outputs. The bug: `len(BaseModel)` raises `TypeError` (Pydantic doesn't implement `__len__`), and the except clause silently defaulted to 0.

## Cognitive Trap Encountered: **plausible_wrong_answer**

The silent fallback to `length = 0` produced a plausible-but-wrong count that passed silently through the system. The symptom — "expected 3-5 items, got 0" warnings on correct LLM outputs — could easily be dismissed as user error or flaky LLM behavior.

This is Commandment 6 territory: *"Thou shalt not hedge with silent fallbacks; a plausible wrong answer is harder to catch than a crash."*

## The Fix

Added `_extract_countable()` helper that unwraps Pydantic models with a single list field before counting. Design follows the **single-list heuristic**: common patterns like `KeyPoints(points=[...])` extract cleanly, while ambiguous cases (multi-list or no-list models) fall through unchanged — no silent wrong answer.

## TDD Discipline Applied

The fix followed strict RED-GREEN:
1. **RED commit**: 7 new tests in `TestCountRangePydanticExtraction`, 3 failing (exposing the bug)
2. **GREEN commit**: `_extract_countable()` + single line change to use it

The RED phase revealed that multi-list and no-list fallback tests *already passed* — proving the existing behavior was correct for those edge cases. Only the single-list extraction was broken.

## Heuristic

**Normalize at the boundary, not downstream.** The Pydantic model is the boundary where LLM output enters; extraction should happen there, not in every downstream consumer that needs a count.

## Seed

When should extraction be explicit (config field) vs. implicit (heuristic)?

The single-list heuristic works for common patterns but is invisible. Would `count_field: points` in verification config make the contract clearer, even if the heuristic usually guesses right? Or is that API complexity without value?
