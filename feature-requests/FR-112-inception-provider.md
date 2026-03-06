# FR-112: Add Inception Labs Mercury-2 Provider

**Status**: Draft
**Priority**: Low
**Effort**: 30 min
**Risk**: Low

## Context

Mercury-2 is a fast reasoning LLM from Inception Labs. Uses OpenAI-compatible API, so implementation follows existing `xai`/`lmstudio` pattern.

**API Details**:
- Base URL: `https://api.inceptionlabs.ai/v1`
- Model: `mercury-2`
- Auth: `Bearer $INCEPTION_API_KEY`
- Endpoint: `/v1/chat/completions`
- Features: Tool calling, structured outputs, 128K context
- Pricing: $0.25/1M input, $0.75/1M output
- Free tier: 10M tokens with new accounts

Docs: https://docs.inceptionlabs.ai/get-started/models

## Objective

Enable `provider: inception` in YAMLGraph for Mercury-2 model access.

## Implementation

### Step 1: Add default model to config.py

```python
# yamlgraph/config.py - add to DEFAULT_MODELS dict
"inception": os.getenv("INCEPTION_MODEL", "mercury-2"),
```

### Step 2: Add provider type and factory function

```python
# yamlgraph/utils/llm_factory.py

# Update ProviderType literal (alphabetical)
ProviderType = Literal[
    "anthropic", "google", "inception", "lmstudio", "mistral", "openai", "replicate", "xai"
]

# Add helper function (after _create_google_llm, alphabetically)
def _create_inception_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Inception Labs Mercury LLM."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url="https://api.inceptionlabs.ai/v1",
        api_key=os.getenv("INCEPTION_API_KEY"),
        **kwargs,
    )

# Add dispatch case in _dispatch_provider (alphabetically after google)
if provider == "inception":
    return _create_inception_llm(model, temperature, **kwargs)
```

### Step 3: Update documentation

**CLAUDE.md** - add to env vars table:
```markdown
| `INCEPTION_API_KEY` | Inception Labs authentication |
```

**.env.sample** - add:
```
INCEPTION_API_KEY=
```

### Step 4: Add unit test

```python
# tests/unit/test_llm_factory.py
def test_create_llm_inception(monkeypatch):
    """Test Inception provider creates ChatOpenAI with correct base_url."""
    monkeypatch.setenv("INCEPTION_API_KEY", "test-key")

    with patch("yamlgraph.utils.llm_factory.ChatOpenAI") as mock:
        create_llm(provider="inception", model="mercury-2")
        mock.assert_called_once()
        call_kwargs = mock.call_args[1]
        assert call_kwargs["base_url"] == "https://api.inceptionlabs.ai/v1"
        assert call_kwargs["model"] == "mercury-2"
```

## Files Changed

| File | Change |
|------|--------|
| `yamlgraph/config.py` | Add `inception` to DEFAULT_MODELS |
| `yamlgraph/utils/llm_factory.py` | Add type, helper, dispatch |
| `CLAUDE.md` | Add env var documentation |
| `.env.sample` | Add INCEPTION_API_KEY |
| `tests/unit/test_llm_factory.py` | Add test case |

## Usage

```bash
# Set API key
export INCEPTION_API_KEY="your-key"

# CLI
yamlgraph graph run my_graph.yaml --provider inception

# YAML metadata
metadata:
  provider: inception
  model: mercury-2
```

## Acceptance Criteria

- [ ] `create_llm(provider="inception")` returns working ChatOpenAI instance
- [ ] `INCEPTION_API_KEY` env var used for authentication
- [ ] `INCEPTION_MODEL` env var overrides default model
- [ ] Unit test passes
- [ ] Graph with `metadata.provider: inception` works

## Judgement

Low risk — follows proven pattern (xai, lmstudio). No new dependencies.
