# Diary: Vertex AI Deprecation Migration

**Date**: 2026-03-31
**Branch**: fix/vertex-deprecation-migration

## What I Did

Migrated the `vertex` provider from the deprecated `ChatVertexAI` class
(`langchain-google-vertexai`) to `ChatGoogleGenerativeAI(vertexai=True)`
(`langchain-google-genai`).

## Cognitive Process

FR-213 was merged hours ago using `ChatVertexAI`. The first smoke test revealed
a `LangChainDeprecationWarning` stating `ChatVertexAI` was deprecated in
LangChain 3.2.0 and would be removed in 4.0.0. The recommended replacement
is `ChatGoogleGenerativeAI` from `langchain-google-genai` — which is already
a core dependency of YAMLGraph (used by `provider: google`).

Inspecting `ChatGoogleGenerativeAI`'s constructor confirmed it now has
`vertexai`, `project`, and `location` parameters — the same auth surface
as `ChatVertexAI`. The migration was a single-function change: set
`vertexai=True` and use `model=` instead of `model_name=`.

## Traps Encountered

**Trap: downstream_fix**. The initial FR-213 implementation chose
`langchain-google-vertexai` because that was the "Vertex AI package". But
the upstream deprecation shows the genai package absorbed that functionality.
The fix: normalize at the boundary (the import) rather than patching downstream.

**Trap: working_system_inertia**. FR-213 passed all tests and merged cleanly.
The deprecation warning was easy to ignore since the code functioned. But
"it works" blocks seeing it clearly — the optional `[vertex]` extra was
unnecessary complexity since `langchain-google-genai` already handles Vertex AI.

## What Worked

- Checking `ChatGoogleGenerativeAI`'s constructor signature via `inspect`
  confirmed the migration path before writing any code.
- Removing the `[vertex]` optional extra simplified the dependency tree.
- All 4 existing vertex tests adapted cleanly with minimal changes.

## Seed

The `google` and `vertex` providers now share the same underlying class
(`ChatGoogleGenerativeAI`) — differing only in `vertexai=True` and auth
mechanism. Could they be consolidated into a single provider with an
`auth: api_key | adc` parameter, reducing the dispatch surface?
