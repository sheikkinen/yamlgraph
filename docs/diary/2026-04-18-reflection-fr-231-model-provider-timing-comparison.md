# Diary: FR-231 Model & Provider Timing Comparison

**Date:** 2026-04-18
**FR:** FR-231
**Caps:** CAP-89, CAP-90

## Cognitive Process

The FR was cleanly scoped into two independent phases — a timing callback (Phase 1) and a bench command (Phase 2). The key insight was recognizing that both phases follow existing patterns exactly: the timing callback mirrors `TokenUsageCallbackHandler`, and the bench CLI follows the `graph run` subcommand pattern.

## Trap Encountered: Tuple Expansion Fragility

Expanding `_build_run_config`'s return tuple from 6 to 7 elements broke existing tests that mock this function. This is a classic downstream-fix trap: the tuple positional API is brittle. A `dataclass` or `NamedTuple` would be more resilient — adding a field wouldn't break unpacking at existing callsites if they used named access.

## Insight

**Pattern-following eliminates design decisions.** By following the `TokenUsageCallbackHandler` pattern exactly (same callback injection, same factory function, same CLI flag pattern), the timing tracker required zero architectural decisions — it was pure implementation.

## Heuristic

When extending a positional tuple API, expect all mock sites to break. Consider graduating tuple returns to `NamedTuple` when a function's return type grows beyond 4 elements.

## Seed

Could `_build_run_config` return a `RunConfig` dataclass instead of a tuple, so future additions don't break every callsite?
