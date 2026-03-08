# Feature Request: Add DeepSeek LLM Provider

**Priority:** LOW
**Type:** Feature
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08
**Judged:** 2026-03-08

## Judgement

**Verdict: APPROVE** — Scope is frozen. Authority granted to implement.

**Evaluation:**

1. **Scope: Clear and minimal.** Adds one provider following the proven xAI/Inception `ChatOpenAI` + `base_url` pattern. No new dependencies, no new abstractions.

2. **No contradictions.** All claims verified against codebase:
   - `.env.sample` lines 22-23 already document `DEEPSEEK_API_KEY` (dead config) ✓
   - xAI pattern at `llm_factory.py:85-95` uses exact `ChatOpenAI` + `base_url` pattern proposed ✓
   - `ProviderType` currently has 8 providers ✓
   - `_dispatch_provider()` uses if-chain routing ✓

3. **Acceptance criteria: Measurable and complete.** Each item is a verifiable checklist. One clarification: AC item 9 ("REQ-YG-121 provider count expectation updated") — the test at `tests/unit/test_architecture_provider_count.py:44-61` has a **hardcoded `expected` set** that must have `"deepseek"` added. The count auto-detects from `ProviderType`, but the smoke-test set does not.

4. **Feasible.** Copy-paste of existing pattern. 1-day estimate is realistic.

5. **Architecture-aligned.** Extends the factory without modifying its interface. Follows the Three-Layer Pattern — config is truth, code is logic.

## Summary

Add DeepSeek as a ninth LLM provider to the `create_llm()` factory, using the OpenAI-compatible API pattern already established by xAI and Inception providers.

## Value Statement

Graph authors gain access to DeepSeek's reasoning models (deepseek-reasoner, deepseek-chat) through the same `provider="deepseek"` interface used by all other providers, with zero new dependencies.

## Problem

DeepSeek offers competitive reasoning models (deepseek-reasoner, deepseek-chat) via an OpenAI-compatible API. The `.env.sample` already documents `DEEPSEEK_API_KEY` and `DEEPSEEK_MODEL`, but the factory has no dispatch path for `"deepseek"` — the env vars are dead config.

## Proposed Solution

Follow the xAI/Inception pattern: `ChatOpenAI` with custom `base_url`. No new pip dependencies required since `langchain-openai` is already a core dependency.

### Factory addition (`yamlgraph/utils/llm_factory.py`)

```python
def _create_deepseek_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create DeepSeek LLM (OpenAI-compatible API)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )
```

### YAML usage

```yaml
metadata:
  provider: deepseek
  model: deepseek-reasoner
```

### CLI usage

```bash
PROVIDER=deepseek yamlgraph graph run examples/demos/hello/graph.yaml --var name="World"
```

## Acceptance Criteria

- [ ] `ProviderType` Literal includes `"deepseek"`
- [ ] `DEFAULT_MODELS` includes `"deepseek": os.getenv("DEEPSEEK_MODEL", "deepseek-chat")`
- [ ] `_create_deepseek_llm()` function exists using `ChatOpenAI` with `base_url="https://api.deepseek.com/v1"`
- [ ] `_dispatch_provider()` routes `"deepseek"` to the new function
- [ ] Integration test in `tests/integration/test_providers.py` with `@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"))` guard
- [ ] `ARCHITECTURE.md` updated: provider count "8 providers" → "9 providers", DeepSeek added to provider list
- [ ] `reference/getting-started.md` updated: provider count and env var table
- [ ] `CLAUDE.md` updated: `DEEPSEEK_API_KEY` added to env var table, provider list updated
- [ ] REQ-YG-121 provider count expectation updated (or test auto-detects from `ProviderType`)
- [ ] `PROVIDER` env var docs list `deepseek` as an option
- [ ] No new pip dependencies added (uses existing `langchain-openai`)
- [ ] Unit tests pass, lint passes
- [ ] Documentation updated

## Alternatives Considered

1. **langchain-deepseek package**: A dedicated LangChain integration exists but would add a new dependency. Since DeepSeek's API is OpenAI-compatible, reusing `langchain-openai` with `base_url` is simpler and consistent with xAI/Inception patterns.

2. **Generic OpenAI-compatible provider**: A single "openai-compatible" provider with configurable base_url would reduce per-provider boilerplate. However, named providers give better UX (`provider: deepseek` vs `provider: openai-compatible, base_url: ...`) and match the established pattern. Could be revisited if provider count exceeds ~12.

## Related

- `.env.sample` lines 22-23: `DEEPSEEK_API_KEY` and `DEEPSEEK_MODEL` already documented
- `yamlgraph/utils/llm_factory.py`: Provider factory (xAI pattern at lines 85-95)
- `yamlgraph/config.py`: `DEFAULT_MODELS` dict
- `tests/integration/test_providers.py`: Provider integration test patterns
- REQ-YG-121: Architecture provider count guard
- FR-119: Lint provider/model top-level (related provider validation)
