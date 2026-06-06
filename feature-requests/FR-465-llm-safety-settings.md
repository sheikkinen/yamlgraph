# Feature Request: FR-465 Configurable LLM Safety Settings

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-05

## Summary

Expose a provider-agnostic `safety_settings` configuration so graph authors can
relax (or tighten) provider content-moderation thresholds from YAML. Today the
threshold is hard-wired to each provider's default — for Google/Vertex Gemini
that is `BLOCK_MEDIUM_AND_ABOVE`, which silently blocks legitimate output in
sensitive-but-valid domains (healthcare intake, crisis lines, moderation
tooling, security research). There is currently **no code path** through which a
caller can set it.

## Value Statement

Graph authors running legitimate sensitive-domain workloads can stop the
provider's moderation layer from suppressing valid model output, without forking
the framework or dropping to raw SDK calls.

## Problem

### The setting is unreachable, not merely defaulted

The lever is closed at all three layers:

1. **Constructors never pass it.** `_create_google_llm`
   ([yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py)) and
   `_create_vertex_llm` build `ChatGoogleGenerativeAI(...)` with `model`,
   `temperature`, credentials, and an optional `thinking_budget` — no
   `safety_settings`. Every Gemini call runs at Google's defaults.
2. **The factory signature is closed.** `create_llm(provider, model, temperature,
   max_tokens, thinking_budget)`
   ([yamlgraph/utils/llm_factory.py](../yamlgraph/utils/llm_factory.py)) has no
   `**kwargs` passthrough; the internal `_create_*` functions accept `**kwargs`
   but nothing upstream populates it.
3. **No YAML surface.** `NodeConfig`
   ([yamlgraph/models/graph_schema.py](../yamlgraph/models/graph_schema.py)) and
   the `defaults` block expose `provider`, `model`, `temperature`, `max_tokens`,
   `thinking_budget` — there is no `safety_settings` key, and the LLM cache key
   `(provider, model, temperature, max_tokens, thinking_budget)` does not even
   model it as a dimension.

### Symptom for the author

A Gemini moderation block returns `finish_reason=SAFETY` with empty content. The
node then emits an empty/odd `response` with no recourse — the author cannot
raise the threshold to `BLOCK_NONE` for a domain where that is the correct and
intended configuration.

## Provider Survey (all 11 supported providers)

The supported providers are `anthropic, azure, deepseek, google, inception,
lmstudio, mistral, openai, replicate, vertex, xai`
([ProviderType](../yamlgraph/utils/llm_factory.py)). Their moderation surfaces
differ substantially:

| Provider | SDK class | Construction-time safety knob | In scope? |
|----------|-----------|-------------------------------|-----------|
| **google** | `ChatGoogleGenerativeAI` | `safety_settings: {HarmCategory: HarmBlockThreshold}` | **Yes (v1)** |
| **vertex** | `ChatGoogleGenerativeAI(vertexai=True)` | `safety_settings` (same dict) | **Yes (v1)** |
| **mistral** | `ChatMistralAI` | `safe_prompt: bool` (guardrail "safe mode") | Deferred (different shape — boolean, not category/threshold) |
| anthropic | `ChatAnthropic` | None — safety is built in, not per-request configurable | No (no knob exists) |
| azure | `AzureAIOpenAIApiChatModel` | Content filter set at **deployment/resource** level (Azure AI Content Safety), not a constructor param | No (deployment config, not framework) |
| openai | `ChatOpenAI` | Moderation is a **separate `/moderations` endpoint**; chat completions have no per-request threshold | No (out-of-band API) |
| deepseek | `ChatOpenAI` (compat) | None | No |
| inception | `ChatOpenAI` (compat) | None | No |
| lmstudio | `ChatOpenAI` (compat, local) | None — local model, no provider moderation | No |
| replicate | `ChatLiteLLM` | Model-dependent passthrough; no uniform knob | No |
| xai | `ChatOpenAI` (compat) | None | No |

**Conclusion:** Only **google** and **vertex** share a true category→threshold
safety model. Mistral has a *boolean* `safe_prompt` of a fundamentally different
shape; mapping a category/threshold config onto a boolean is lossy, so it is
deferred (see Alternatives). The remaining eight providers have no construction-
time safety knob — for them `safety_settings` is meaningless and must be a
**lint warning**, not a silent no-op.

## Proposed Solution

### 1. Provider-agnostic, typed YAML schema (Commandment 5 — no raw SDK strings)

Authors specify normalized category/threshold enums; the factory translates them
to the provider SDK enums.

```yaml
# Node-level (or under defaults:)
nodes:
  generate_probe:
    type: race
    safety_settings:
      dangerous_content: none      # BLOCK_NONE
      harassment: only_high        # BLOCK_ONLY_HIGH
      hate_speech: medium_and_above
      sexually_explicit: medium_and_above
    candidates:
      - { provider: vertex, model: gemini-2.5-flash }
```

Normalized enums (validated by Pydantic):

- **Categories:** `harassment`, `hate_speech`, `sexually_explicit`,
  `dangerous_content`, `civic_integrity`.
- **Thresholds:** `none` → `BLOCK_NONE`, `only_high` → `BLOCK_ONLY_HIGH`,
  `medium_and_above` → `BLOCK_MEDIUM_AND_ABOVE`, `low_and_above` →
  `BLOCK_LOW_AND_ABOVE`.

Any other key/value is a Pydantic validation error at load time (fail at the
boundary, not at the provider call).

### 2. Plumbing (mirror the `thinking_budget` precedent, FR-071/FR-230)

The exact path `thinking_budget` already travels:

1. `NodeConfig.safety_settings` + `GraphConfigSchema.defaults` validator
   ([graph_schema.py](../yamlgraph/models/graph_schema.py)).
2. `node_factory/llm_nodes.py` — node value > defaults value, into
   `LLMNodeConfig`.
3. `executor.py::execute_prompt(..., safety_settings=...)` →
   `PromptExecutor.execute` → `create_llm(...)`.
4. `llm_factory.create_llm` — new parameter; add to the cache key; validate
   provider support; pass to `dispatch_provider`.
5. `llm_providers.dispatch_provider` → `_create_google_llm` /
   `_create_vertex_llm`, which translate the normalized dict to
   `{HarmCategory.*: HarmBlockThreshold.*}` and pass `safety_settings=` to the
   constructor.

### 3. Cache key

Extend the key to
`(provider, model, temperature, max_tokens, thinking_budget, safety_settings_frozen)`
where `safety_settings_frozen` is a `frozenset` of `(category, threshold)` pairs
(dicts are unhashable). Without this, two nodes differing only in safety config
would collide on the cached instance.

### 4. Unsupported-provider handling

- `create_llm` raises `ValueError` if `safety_settings` is set for a provider not
  in `SAFETY_PROVIDERS = {"google", "vertex"}` — same guard shape as the
  `thinking_budget`/`THINKING_PROVIDERS` check.
- A new linter check (W-series, e.g. **W072**) in
  [checks_providers.py](../yamlgraph/linter/checks_providers.py) warns when
  `safety_settings` appears on a node/candidate whose provider does not support
  it, mirroring `check_thinking_budget` (W071-*).

## Acceptance Criteria

- [ ] AC-01 `NodeConfig.safety_settings` accepts a validated
      `dict[Category, Threshold]`; invalid category or threshold raises a Pydantic
      `ValidationError` at config load.
- [ ] AC-02 `defaults.safety_settings` is validated identically and is overridden
      by a node-level value.
- [ ] AC-03 `_create_google_llm` and `_create_vertex_llm` pass a translated
      `safety_settings={HarmCategory.*: HarmBlockThreshold.*}` to
      `ChatGoogleGenerativeAI` (assert via mocked constructor kwargs, per FR-226
      pattern).
- [ ] AC-04 `create_llm(safety_settings=..., provider="openai")` (or any provider
      ∉ `SAFETY_PROVIDERS`) raises `ValueError`.
- [ ] AC-05 LLM cache distinguishes two otherwise-identical configs that differ
      only in `safety_settings` (no cross-contamination).
- [ ] AC-06 Linter emits W072 when `safety_settings` is set on an unsupported
      provider's node/candidate.
- [ ] AC-07 Omitting `safety_settings` leaves Gemini construction byte-for-byte
      unchanged (no `safety_settings` kwarg passed) — happy path unchanged.
- [ ] Tests added (req tagged); `lint-imports`, `ruff`, `req_coverage` green.
- [ ] Documentation updated: `reference/graph-yaml.md` (node fields) and a
      changelog fragment in `changelog/unreleased/`.

## Alternatives Considered

1. **Raw `**kwargs` passthrough from YAML to the constructor.** Rejected —
   violates Commandment 5 (untyped dicts wandering the codebase) and exposes raw
   SDK enum strings; no validation boundary; brittle across SDK versions.
2. **Include Mistral `safe_prompt` in v1.** Deferred — it is a boolean, not a
   category/threshold map. Folding a bool into the same schema is lossy and
   risks a `framework_costume` abstraction. If demand appears, add a separate,
   honestly-shaped `mistral`-scoped option in a follow-up FR rather than
   pretending one schema fits both.
3. **Per-provider `safety_settings` raw dict (no normalization).** Rejected —
   couples graph YAML to `langchain-google-genai` enum names and makes graphs
   non-portable across providers.
4. **Do nothing / document deployment-level config.** Insufficient for
   Google/Vertex: unlike Azure/OpenAI, the Gemini threshold is a *request-time*
   construction parameter, so there is no deployment knob to point authors at.

## Non-Goals

- Azure / OpenAI moderation configuration (deployment-level / separate endpoint —
  not a construction parameter; out of framework scope).
- Anthropic safety tuning (no configurable per-request knob exists).
- Application-level handling of a `finish_reason=SAFETY` empty response (that is a
  node-author / downstream concern, distinct from configuring the threshold).

## Related

- FR-071 / FR-230 — `thinking_budget` plumbing; the exact precedent this FR
  mirrors (YAML → schema → node_factory → executor → factory → provider).
- FR-226 — Vertex Express auth; source of the "mocked constructor, assert kwargs"
  test pattern.
- FR-213 — Vertex AI provider introduction.
- `yamlgraph/utils/llm_providers.py`, `yamlgraph/utils/llm_factory.py`,
  `yamlgraph/models/graph_schema.py`, `yamlgraph/node_factory/llm_nodes.py`,
  `yamlgraph/linter/checks_providers.py` — the files this FR touches.
