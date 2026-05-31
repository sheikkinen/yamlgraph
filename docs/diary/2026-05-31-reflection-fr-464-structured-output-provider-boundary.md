# Diary: Structured Output Provider Boundary

**Date**: 2026-05-31
**FR**: FR-464 Structured Output JSON Fallback

## Observation

DeepSeek rejects `response_format` in `with_structured_output()` — a provider boundary violation. The fix applies the same fallback pattern (extract_json + model_validate) already proven in agent.py (FR-456) to executor.py and race_node.py.

## Trap: downstream_fix

The initial instinct was to fix at the call site where the error manifests. But the real boundary is the provider interface — different providers support different subsets of the structured output API. The one-law applies: normalize at the boundary where external data enters.

## Heuristic

**Provider capability variance is a boundary, not a bug**: When a provider rejects a feature that others accept, the fix belongs at the provider boundary layer, not in retry logic or error handling. The fallback pattern (try structured, fall back to extraction) should be the default for all provider-facing structured output calls.

## Seed:

Could provider capability probing be automated — a startup-time check that records which providers support `response_format`, `tool_choice`, `thinking`, etc., so fallback paths are selected proactively rather than reactively on first failure?
