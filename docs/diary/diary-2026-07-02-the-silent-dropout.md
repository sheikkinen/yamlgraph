# Diary: The Silent Dropout — When Validation Eats Work Product

**Date**: 2026-07-02
**FR**: FR-649 (persist boundary normalization)
**Trap**: downstream_fix → symptom_patch → plausible_wrong_answer

## The Cognitive Process

The worldgen pipeline ran successfully — nodes executed, LLM returned rich content, the loop iterated. Everything looked fine. But deepened pages vanished. The pipeline reported "0 pages written" for content that had been generated, processed, and handed to persist_pages.

The root cause: Pydantic validation at the persist boundary was silently returning `None` for pages whose *shapes* were correct but whose *field names* differed from the schema. The LLM returned `{target_id, type, description}` for relationships where the schema expected `{to, kind, valence}`. Structurally equivalent data, semantically identical, but rejected by exact-match validation.

## The Trap

**Silent dropout is the most dangerous failure mode in LLM pipelines.** It produces no error, no warning, no crash. The pipeline completes successfully. The output *looks* plausible — there are some pages, just fewer than expected. The absence of content is indistinguishable from the LLM choosing not to generate it.

This is `plausible_wrong_answer` applied to pipeline mechanics: the pipeline's return value passes shape check (it's a dict with the right keys) but is semantically wrong (it dropped 26 of 30 pages).

## The Cure

**Normalize at the boundary where external data enters** (The One Law). The LLM output is the external boundary. `normalize_page()` coerces the seven known variation patterns before Pydantic ever sees the data. And the fallback — persist-with-warning instead of silent drop — ensures that even unknown variations preserve work product.

## Heuristic

**Validation-as-gatekeeper vs validation-as-normalizer.** When the data source is an LLM, validation should normalize first and reject only as a last resort. The LLM's contract is semantic ("give me a relationship"), not syntactic ("give me a dict with key 'to'"). Normalize the syntax; preserve the semantics; log the delta.

## Seed

Can `normalize_page` be generated from the Pydantic schema itself? If the schema declares `to: str` and the LLM sends `target_id: str`, the mapping `target_id → to` could be inferred from field descriptions or from a canonical alias registry. This would make normalization declarative rather than hand-coded — and it would extend to any schema, not just WorldPage.
