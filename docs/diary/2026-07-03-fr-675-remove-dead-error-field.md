# Diary: FR-675 — Remove dead top-level error field

**Date:** 2026-07-03
**FR:** FR-675
**Duration:** ~15 min enforcement

## What happened

Pure entropy removal — `error` field existed in `BASE_FIELDS`, was initialized to `None`, exported as `None`, and never written by any production code. Removed from three locations in `state_builder.py` (declaration, init, codegen) and fixed `export.py` to derive error from the `errors` list instead.

## Cognitive trap avoided

**growth_as_default**: The original FR-668 wanted to *add* writers to the dead field — converge the two patterns. FR-675 correctly identified that subtraction is the honest fix: if nothing writes it, the field is a phantom claim.

**plausible_wrong_answer surface**: Every export shipped `"error": None` — correct type, correct shape, zero information. Consumers parsing this key received a plausible signal (null = no error) when in reality the field was simply unpopulated regardless of actual error state.

## Insight

Removing a field is cheaper than adding a compatibility layer. The export derivation (`errors[-1].model_dump(mode="json")`) makes the `error` key truthful for the first time — it now carries real information when errors exist.

Bonus: `state_builder.py` went from 471 → 439 lines, bringing it back under the 450-line ceiling.

## Seed

Could the remaining `errors` list pattern itself be made richer — e.g., export all errors as a list rather than just the last one? Is there downstream value in seeing the full error chain?
