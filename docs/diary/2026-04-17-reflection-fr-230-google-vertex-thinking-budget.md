# Diary: FR-230 Google/Vertex Thinking Budget

**Date:** 2026-04-17
**FR:** FR-230
**REQ:** REQ-YG-230

## Cognitive Process

FR-230 was a targeted extension of an existing feature (FR-071). The existing
`thinking_budget` guard in `create_llm` hard-coded `provider == "anthropic"`,
which blocked Google/Vertex users from a legitimate feature. The fix was
surgical: introduce `THINKING_PROVIDERS`, scope the temperature override and
three linter checks to Anthropic only, and pass `thinking_budget` through the
dispatch chain.

## Traps Encountered

**`downstream_fix` avoided**: The temptation here was to add a
`provider in ("google", "vertex")` branch _after_ the guard failed. Instead,
the guard itself was rewritten at the correct boundary — the `create_llm`
allowlist. This matches the doctrine: normalize at the boundary where external
data enters, not downstream where it manifests.

**Patch target subtlety**: `_create_google_llm` uses an inline import
(`from langchain_google_genai import ChatGoogleGenerativeAI`). Patching
`yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI` would not intercept the
inline import; the correct patch target is
`langchain_google_genai.ChatGoogleGenerativeAI`. Discovered by writing the test
first (RED) and watching it pass for the wrong reason — a moment that exposed
the patch target was wrong before implementation.

**Schema validator scope**: The original validator enforced the Anthropic
minimum (1024) at schema level. FR-230 moves this to runtime (`create_llm`),
letting the schema accept any integer ≥ -1 and delegating provider-specific
constraints to the factory. This is the correct boundary: schema can't know
provider context at field-validator level.

## Heuristic

> When extending provider-specific behavior, enumerate the full provider
> allowlist at the boundary — never add a "not-A" guard when "A, B, C are
> valid" is the accurate intent.

## Seed

Could `THINKING_PROVIDERS` be sourced from the capability registry (CAP files)
rather than a hardcoded set, making new provider additions self-documenting?
