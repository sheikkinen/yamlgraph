# Diary: FR-213 — Google Vertex AI Provider

**Date**: 2026-03-31
**Branch**: feat/fr-213-vertex-ai-provider

## What I Did

Added `provider: vertex` to the YAMLGraph LLM factory, backed by `ChatVertexAI`
from `langchain-google-vertexai`. The implementation follows the established
provider pattern precisely: one helper function, one dispatch case, one entry in
`DEFAULT_MODELS`, one optional extra in `pyproject.toml`.

## Cognitive Process

The task was well-scoped by the FR with a complete implementation sketch. The
primary decision point was **how to make `ChatVertexAI` patchable for the unit
test**. The FR's test patches `yamlgraph.utils.llm_factory.ChatVertexAI` — which
requires the name to exist in the module's namespace.

Other providers use lazy imports inside their helper functions (e.g.,
`from langchain_anthropic import ChatAnthropic`). Patching those works only when
you patch the import path (`langchain_anthropic.ChatAnthropic`), not the local
name. The FR test uses the local-name pattern, which requires a module-level import.

I resolved this with a `try/except ImportError` at module level, which:
1. Makes `ChatVertexAI` a module-level name (patchable at `yamlgraph.utils.llm_factory.ChatVertexAI`)
2. Falls back gracefully to `None` if the optional package isn't installed
3. Raises a clear `ImportError` with install instructions at call time

## Traps Encountered

**Trap: lazy-import vs patchable name**. The lazy import pattern used by other
providers is correct for optional dependencies that may not be installed. But the
test contract required the name to be in the module namespace. The `try/except`
at module level bridges both requirements cleanly without changing the lazy-import
philosophy of other providers.

**Heuristic**: When a test patches `module.ClassName`, ensure `ClassName` is
assigned at module level — even if via a `try/except` guard. Lazy imports inside
functions are not patchable at the module path.

## What Worked

- TDD discipline: 5 failing tests → all green in one implementation pass
- Following the existing pattern exactly (dispatch function, helper function,
  DEFAULT_MODELS entry) meant zero guesswork
- The `try/except ImportError` pattern correctly handles the optional dependency
  without requiring `langchain-google-vertexai` to be installed in CI

## Seed

Could we generate the list of providers in `ProviderType`, `DEFAULT_MODELS`, and
the ARCHITECTURE.md module table from a single source of truth (e.g., a YAML
registry of providers)? The current setup requires touching 5+ files for each new
provider — a single provider registry would reduce drift between them.
