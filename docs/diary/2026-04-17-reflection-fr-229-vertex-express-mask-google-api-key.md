# Diary: FR-229 — Vertex Express Mask GOOGLE_API_KEY

**Date:** 2026-04-17
**Branch:** feat/fr-229-vertex-express-mask-google-api-key

## Cognitive Process

The task was immediately clear: production fix already present (commit 557b108); only unit tests were missing. The discipline demanded here was **test-after-fix** — the most cognitively easy but trap-prone form of TDD, because the absence of a RED phase makes verification feel trivially performative.

I confirmed the production code had `"GOOGLE_API_KEY"` in `_masked_env(...)` before writing a single test. This is correct: the FR explicitly stated the fix was present. The tests' role is to condemn the root cause so it cannot regress.

## Traps Encountered

**`patch` target mismatch risk:** The FR-229 specification proposed patching `yamlgraph.utils.llm_factory.ChatGoogleGenerativeAI`, but the actual import is a *local* import inside the function body. The correct patch target is `langchain_google_genai.ChatGoogleGenerativeAI`, matching the FR-227 pattern. Blindly copying the FR spec would have produced tests that pass vacuously (the mock is never invoked, `captured` remains empty, assertion on missing key silently passes as True).

The cure: **read the existing tests before writing new ones** (Commandment 4 — honor existing patterns).

## Insight

A test spec in a Feature Request is a design artifact, not executable code. It describes intent, not implementation. Every test in a spec must be verified against the actual module structure before it is committed. The `patch` target is an implementation detail that the spec author may not know correctly.

## Heuristic

> When a FR provides test code, treat it as pseudocode. Verify every `patch` target against the actual import path before trusting it.

**Seed:** Could the `_masked_env` context manager be generalized to accept a dict of `{key: replacement_value}` instead of only removing keys? This would allow temporarily substituting env vars with test values rather than blanking them — useful for multi-provider isolation scenarios.
