# Reflection: FR-226 Vertex Express API Key Auth

**Date:** 2026-04-17

## Cognitive Process

This was a textbook boundary normalization case from the Scripture knowledge graph: *normalize at the boundary where external data enters*. The fix belongs at the entry point of `_create_vertex_llm` — where the env-var is first read — not at a downstream call site.

## Trap Encountered

**`downstream_fix`**: My first mental model wanted to guard at the `ChatGoogleGenerativeAI` call by conditionally filtering kwargs. The cure was recognizing the correct boundary: the env-var branch point *is* the boundary, and the two code paths must be mutually exclusive from there.

## Insight

A mutually exclusive branch at the boundary is cleaner than any kwargs-filtering approach: it makes the contract explicit, removes the need for `if api_key: del kwargs["project"]` defensive code, and aligns exactly with the SDK constraint (cannot pass both `api_key` and `project`).

## TDD Discipline

RED first confirmed the current behavior explicitly — the `test_vertex_adc_no_api_key` test passed immediately (existing ADC path already correct), while the two Express tests failed as expected. This validated that the problem was purely the missing Express branch, not a regression in ADC behavior.

**Seed:** Should `VERTEX_API_KEY` be validated for format at startup (e.g., warn if it looks like a service account JSON path instead of an API key string), or is silent acceptance the right ergonomic here?
