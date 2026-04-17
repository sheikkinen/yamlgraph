# Feature Request: FR-230 Google/Vertex Thinking Budget Support

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-17

## Summary

Extend `thinking_budget` support to `google` and `vertex` providers.
`langchain-google-genai 4.2.0` accepts `thinking_budget` as a first-class
constructor parameter on `ChatGoogleGenerativeAI` — no wrapping required.
Currently `create_llm` raises `ValueError` whenever `thinking_budget ≥ 1024`
and the provider is not `anthropic`, silently blocking legitimate Gemini usage.

## Value Statement

Graph authors using Gemini 2.5+ models can enable extended thinking via the
same `thinking_budget` field already available for Anthropic, with no Python
required.

## Problem

FR-071 shipped `thinking_budget` as an Anthropic-only feature.  The guard in
`create_llm` (line 249–256, `llm_factory.py`) raises `ValueError` for any
non-Anthropic provider — including `google` and `vertex` — even though
`langchain-google-genai` 4.2.0 has supported the field natively since that
release.

Compounding issues:

1. **Linter W071-2** tells users `thinking_budget` only works with
   `provider='anthropic'` — now incorrect for google/vertex.
2. **Linter W071-1** warns about `temperature != 1` for all thinking providers;
   Google does not impose this constraint, so the warning is misleading.
3. **Linter W071-4** warns when `0 < thinking_budget < 1024`, citing the
   Anthropic minimum — this floor does not apply to Google.
4. **Linter W071-3** lists only Claude model substrings as thinking-capable;
   Gemini 2.5+ thinking-capable models are unrecognised.
5. **Schema validator** on `NodeConfig.thinking_budget` forbids `-1`, which is
   Google's sentinel value for automatic budget selection.

## Proposed Solution

### YAML interface (unchanged from FR-071; new providers now accepted)

```yaml
defaults:
  provider: google                         # or vertex
  model: gemini-2.5-flash
  thinking_budget: 8000                    # forwarded to ChatGoogleGenerativeAI

nodes:
  reason:
    prompt: reason
    state_key: reasoning
    # inherits defaults.thinking_budget

  summarize:
    prompt: summarize
    state_key: summary
    thinking_budget: 0                     # opt out per node

  deep_think:
    prompt: deep_think
    state_key: deep_analysis
    thinking_budget: -1                    # Google automatic mode
```

### Implementation

**1. Schema validator** (`yamlgraph/models/graph_schema.py`):

Relax `validate_thinking_budget` to allow `-1` (Google automatic mode).
Allowed values: `None`, `-1` (auto), `0` (disabled), or `≥ 1024` (Anthropic
budget) or any positive integer (Google budget, no minimum enforced here).
Concretely: reject only values in `1–1023` when provider context is anthropic.
Since provider is not available at field-level validation, relax to accept any
integer `≥ -1` and let provider-specific runtime validation in `create_llm`
enforce the Anthropic minimum.

New rule: `thinking_budget must be None, -1, 0, or a positive integer`.
Values < -1 raise `ValueError`.

**2. `create_llm` guard** (`yamlgraph/utils/llm_factory.py`):

Replace the "only anthropic" guard with a "supported providers" allowlist:

```python
THINKING_PROVIDERS = {"anthropic", "google", "vertex"}

if thinking_budget is not None and thinking_budget >= 1024 and selected_provider not in THINKING_PROVIDERS:
    raise ValueError(...)
```

For Anthropic: keep the temperature=1 override and warning.
For google/vertex: **do not** override temperature.

**3. `_dispatch_provider`** (`yamlgraph/utils/llm_factory.py`):

Forward `thinking_budget` to `_create_google_llm` and `_create_vertex_llm`.

**4. `_create_google_llm` and `_create_vertex_llm`**:

Accept `thinking_budget: int | None = None` and pass it as a constructor kwarg
when non-None. The SDK builds `ThinkingConfig` internally.

```python
def _create_google_llm(
    model: str, temperature: float, thinking_budget: int | None = None, **kwargs: object
) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI
    google_kwargs = dict(kwargs)
    if thinking_budget is not None:
        google_kwargs["thinking_budget"] = thinking_budget
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        **google_kwargs,
    )
```

Same pattern for `_create_vertex_llm`.

**5. Linter updates** (`yamlgraph/linter/checks_providers.py`):

- **W071-1** (temp override warning): scope to `provider == 'anthropic'` only.
- **W071-2** (unsupported provider): narrow the provider check to exclude
  `google` and `vertex` from the warning. Update message and fix text.
- **W071-3** (model not thinking-capable): extend `THINKING_CAPABLE_MODELS`
  with Google substrings: `"gemini-2.5"`, `"gemini-3"`.  Adjust fix text to
  mention both Anthropic and Google capable models.
- **W071-4** (below-minimum): scope to `provider == 'anthropic'` only (Google
  has no enforced minimum; -1 is valid auto-mode).

**6. `docstring / create_llm` updates**:

Update `thinking_budget` parameter doc: mention google/vertex support, -1
auto-mode, and that temperature is not forced for non-Anthropic providers.

## Acceptance Criteria

- [x] `create_llm(provider="google", thinking_budget=8000)` does **not** raise.
- [x] `create_llm(provider="vertex", thinking_budget=8000)` does **not** raise.
- [x] `create_llm(provider="mistral", thinking_budget=8000)` still raises `ValueError`.
- [x] `ChatGoogleGenerativeAI` is instantiated with `thinking_budget=8000` when
  `provider='google'` and `thinking_budget=8000`.
- [x] Temperature is **not** overridden for google/vertex providers even when
  `thinking_budget ≥ 1024`.
- [x] `thinking_budget=-1` is accepted by `NodeConfig` schema validator (Google
  automatic mode).
- [x] `thinking_budget=-2` is rejected by schema validator with `ValueError`.
- [x] Linter W071-2 does **not** fire for `provider='google'` or `provider='vertex'`.
- [x] Linter W071-1 does **not** fire for `provider='google'` or `provider='vertex'`.
- [x] Linter W071-4 does **not** fire for `provider='google'` or `provider='vertex'`.
- [x] Linter W071-3 does **not** fire for `gemini-2.5-flash` model with
  `thinking_budget > 0`.
- [x] Unit tests (mocked) cover: google thinking enabled, vertex thinking enabled,
  google/vertex with thinking skips temp override, unsupported provider raises,
  -1 schema acceptance, -2 schema rejection.
- [ ] Integration test (guarded by `VERTEX_API_KEY`) calls graph with
  `thinking_budget: 1024` and `provider: vertex` on `gemini-2.5-flash` and
  asserts node completes successfully.
- [x] Tests tagged `@pytest.mark.req("REQ-YG-230")`.
- [x] `REQ-YG-230` added to `ARCHITECTURE.md` capability and requirement tables.
- [x] `ALL_REQS` range in `scripts/req_coverage.py` extended to include 230.
- [x] `reference/graph-yaml.md` updated: note google/vertex as valid providers
  for `thinking_budget`; document `-1` auto-mode.
- [x] Changelog fragment added to `changelog/unreleased/`.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Add a new `thinking_level` field for Google ("low"/"medium"/"high") | Out of scope for this FR; Gemini 3+ feature; separate concern |
| Expose `thinking_budget` as a separate `google_thinking_budget` field | Unnecessary divergence from existing API; same field, different provider semantics |
| Validate Google-specific semantics in Pydantic | Provider not available at field-validator level; factory-level guard is the normalisation boundary |

## Related

- `yamlgraph/utils/llm_factory.py` — `create_llm`, `_create_google_llm`, `_create_vertex_llm`, `_dispatch_provider`
- `yamlgraph/linter/checks_providers.py` — W071-* warnings
- `yamlgraph/models/graph_schema.py` — `NodeConfig.thinking_budget` validator
- `feature-requests/FR-071-thinking-budget-graph-level.md` — original implementation
- `feature-requests/FR-213-vertex-ai-provider.md` — Vertex AI provider
- [langchain-google-genai 4.2.0 release](https://github.com/langchain-ai/langchain-google/releases) — `thinking_budget` first-class support
- [Google Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking)
