# Diary: FR-227 Vertex Express Env Var Masking

**Date:** 2026-04-17
**FR:** FR-227
**Type:** Bugfix

## Context

FR-226 added Vertex AI Express mode (API key auth without ADC), but it failed
when `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` were also set in `.env`.

## Cognitive Process

1. **Symptom**: `DefaultCredentialsError` despite `VERTEX_API_KEY` being set and
   the Express branch taken in `_create_vertex_llm`.
2. **Initial hypothesis**: LangChain wrapper ignores `google_api_key` when
   `GOOGLE_API_KEY` env var exists — partially true.
3. **Deeper root cause**: The `google-genai` SDK's `BaseApiClient.__init__` reads
   `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` from `os.environ` directly.
   Its internal precedence rule: *implicit project/location from env > implicit
   API key from env* causes it to set `api_key=None` and attempt ADC auth.
4. **Fix**: Temporarily mask the conflicting env vars during
   `ChatGoogleGenerativeAI` construction under a threading lock.

## Trap

**downstream_fix** — The symptom (ADC error) manifested inside the SDK, but the
fix belongs at the yamlgraph boundary where we construct the LLM client. The SDK
treats environment variables as an implicit input boundary; we must normalize at
our boundary by controlling what the SDK sees.

## Insight

When a library reads `os.environ` internally with its own precedence logic,
passing explicit constructor args is insufficient — the env vars themselves must
be masked. This is a variant of the `normalize at the boundary` principle applied
to environment-as-input.

## Seed

Could a `provider_env` context manager become a general pattern for all providers
that read env vars with conflicting precedence (e.g., OpenAI's `OPENAI_API_KEY`
vs `AZURE_OPENAI_API_KEY`)?
