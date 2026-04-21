# FR-263: Add Azure OpenAI Provider

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-21

## Summary

Add an `azure` provider to the LLM factory using `AzureAIOpenAIApiChatModel` from `langchain-azure-ai`, enabling corporate environments to use Azure-hosted models (GPT-4o, o1, Llama, Mistral, Cohere) through YAMLGraph.

## Value Statement

Enterprise teams constrained to Azure infrastructure gain first-class YAMLGraph support, eliminating the need for custom provider shims or proxy workarounds.

## Problem

YAMLGraph supports 10 LLM providers but has no Azure support. Corporate environments often require Azure-hosted models due to compliance, data residency, and procurement constraints. Vertex AI, while fully implemented, has performance issues that make it unreliable as the sole enterprise provider.

Azure AI Foundry (formerly Azure ML) provides access to both Azure OpenAI models (GPT-4o, o1) and third-party models (Llama, Mistral, Cohere) hosted on Azure infrastructure, with enterprise SLAs and compliance certifications.

## Proposed Solution

Add `"azure"` to `ProviderType` and implement `_create_azure_llm()` in `llm_factory.py` using `AzureAIOpenAIApiChatModel` from the `langchain-azure-ai` package. This single class covers both Azure OpenAI deployments and the Azure AI Foundry model catalog.

### Usage

```yaml
# graphs/example.yaml
metadata:
  provider: azure
  model: gpt-4o  # maps to Azure deployment name
```

```bash
# Environment
export AZURE_AI_ENDPOINT="https://my-resource.services.ai.azure.com/openai/v1"
export AZURE_AI_API_KEY="sk-..."
export AZURE_MODEL="gpt-4o"

yamlgraph graph run graphs/example.yaml --var topic="AI"
```

### Factory function

The class `AzureAIOpenAIApiChatModel` was verified against PyPI (`langchain-azure-ai` v1.2.2, 2026-04-21). The inbox draft referenced `AzureChatModel`; that name was deprecated in v1.2.0 in favour of `AzureAIOpenAIApiChatModel`.

```python
def _create_azure_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

    endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
    api_key = os.getenv("AZURE_AI_API_KEY", "")

    if not endpoint:
        raise ValueError(
            "AZURE_AI_ENDPOINT environment variable is required. "
            "Set it to your Azure AI Foundry endpoint URL "
            "(e.g. https://my-resource.services.ai.azure.com/openai/v1)"
        )
    if not api_key:
        raise ValueError(
            "AZURE_AI_API_KEY environment variable is required. "
            "Get your key from the Azure Portal under your resource's Keys section."
        )

    return AzureAIOpenAIApiChatModel(
        endpoint=endpoint,
        credential=api_key,
        model=model,
        temperature=temperature,
        **kwargs,
    )
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `AZURE_AI_ENDPOINT` | Azure AI Foundry endpoint URL (full URL as shown in Azure Portal) |
| `AZURE_AI_API_KEY` | Azure AI API key (key-based auth only in v1) |
| `AZURE_MODEL` | Default model/deployment name (follows `{PROVIDER}_MODEL` pattern) |

**Naming rationale:** `AZURE_AI_ENDPOINT` and `AZURE_AI_API_KEY` follow the Azure SDK convention (`azure-ai-inference` uses these names). `AZURE_MODEL` follows the YAMLGraph `{PROVIDER}_MODEL` pattern (e.g. `OPENAI_MODEL`, `VERTEX_MODEL`).

**Model/deployment precedence:** `model` function parameter > `AZURE_MODEL` env var > hardcoded default (`gpt-4o`). Azure deployment names are treated as model names — the factory passes `model` directly to the Azure client.

### Files changed

| File | Change |
|------|--------|
| `yamlgraph/utils/llm_factory.py` | Add `"azure"` to `ProviderType`, add `_create_azure_llm()`, add dispatch case |
| `yamlgraph/config.py` | Add `"azure"` to `DEFAULT_MODELS` |
| `pyproject.toml` | Add `azure` optional dependency group (`langchain-azure-ai>=1.2.0`) |
| `tests/unit/test_azure_provider.py` | Unit tests (mock-based, same pattern as `test_lmstudio_provider.py`) |
| `tests/integration/test_providers.py` | Integration test with `skipif` for missing `AZURE_AI_API_KEY` and `AZURE_AI_ENDPOINT` |
| `tests/unit/test_architecture_provider_count.py` | Add `"azure"` to expected provider set |
| `CLAUDE.md` | Add Azure env vars to environment variables table |
| `ARCHITECTURE.md` | Update provider count from 10 to 11 in module table |

## Acceptance Criteria

- [ ] `"azure"` is a valid value in `ProviderType` literal
- [ ] `_create_azure_llm()` factory function creates an Azure LLM instance via `langchain-azure-ai`
- [ ] `_dispatch_provider()` routes `"azure"` to the factory function
- [ ] `DEFAULT_MODELS["azure"]` reads `AZURE_MODEL` env var with default `gpt-4o`
- [ ] `langchain-azure-ai>=1.2.0` is an optional dependency under `[azure]` extra in `pyproject.toml`
- [ ] `pip install -e ".[azure]"` resolves cleanly alongside existing LangChain stack
- [ ] Import is lazy (inside factory function) so missing package doesn't break other providers
- [ ] `create_llm(provider="azure")` raises `ValueError` with actionable message when `AZURE_AI_ENDPOINT` is missing
- [ ] `create_llm(provider="azure")` raises `ValueError` with actionable message when `AZURE_AI_API_KEY` is missing
- [ ] Unit tests cover: provider registration, factory creation, env var reading, temperature passthrough, model override, missing env var errors
- [ ] Integration test skips gracefully when `AZURE_AI_API_KEY` or `AZURE_AI_ENDPOINT` is not set
- [ ] Architecture provider count guard test (`REQ-YG-121`) passes after updating `ARCHITECTURE.md` and provider-set expectations
- [ ] `CLAUDE.md` environment variables table includes Azure variables
- [ ] All tests tagged with `@pytest.mark.req("REQ-YG-010")`
- [ ] Tests added
- [ ] Documentation updated

## Alternatives Considered

1. **`AzureChatOpenAI` from `langchain-openai`** — Only supports Azure OpenAI Service, not the broader Azure AI Foundry catalog (Llama, Mistral, Cohere). `langchain-azure-ai` provides unified coverage of both Azure OpenAI and Azure AI Foundry models through one class.

2. **Reusing OpenAI provider with Azure base URL** — Fragile; Azure uses deployment names instead of model names, requires API version headers, and auth differs (API key vs Azure AD). A dedicated factory function is cleaner.

3. **LiteLLM proxy** — Already used for Replicate. Adding another LiteLLM-routed provider creates confusion about which path to use. A direct `langchain-azure-ai` integration is more transparent.

## Constraints

- **Auth scope: key-based only.** `AZURE_AI_API_KEY` is the only supported auth method. Azure AD (`DefaultAzureCredential`) is supported by the underlying library but not tested or documented in this FR. A follow-up FR can add managed identity support.
- **Thinking budget deferred.** Azure's reasoning token API (o1/o3) may differ from Anthropic/Google patterns. Add to `THINKING_PROVIDERS` in a follow-up FR if/when Azure exposes reasoning tokens via the same interface.
- **Endpoint pass-through.** The endpoint is passed directly to the Azure client without normalization. Users must provide the full URL as shown in their Azure Portal (e.g. `https://my-resource.services.ai.azure.com/openai/v1`).
- **Single endpoint per process.** The LLM cache key does not include endpoint, consistent with other providers (e.g. DeepSeek base_url). Two graphs targeting different Azure resources in one process is not supported. Document as known limitation if needed.
- **Dependency compatibility.** `langchain-azure-ai>=1.2.0` requires `langchain>=1.2`. Since this is an optional dependency, it should not affect the core package. If resolver conflicts arise with existing `langchain-core`/`langchain-openai` versions, this FR is blocked pending a stack upgrade.

## Judgement

**Verdict:** APPROVE — Framework primitive
**Classification:** Integration — follows established provider-addition pattern
**Judge date:** 2026-04-21

**Evaluation:**

1. **Scope:** Clear and minimal. Single provider addition via proven 5-file pattern. No architectural changes.
2. **Contradictions:** None. Class name verified against PyPI v1.2.2. Thinking budget and Azure AD correctly deferred.
3. **Acceptance criteria:** 16 measurable, testable criteria. Each maps to a concrete code change or assertion.
4. **Feasibility:** High. Template exists (LM Studio provider). Optional dependency pattern established.
5. **Architecture alignment:** Perfect. Factory pattern, lazy imports, env vars, optional deps all follow conventions.
6. **Single responsibility:** Yes. One concern: Azure provider support. Orthogonal concerns (thinking budget, Azure AD) explicitly deferred.

**Note:** `llm_factory.py` is at 443 lines; this change pushes to ~461, past the 450-line max. This is pre-existing tech debt — the registry-over-elif refactor (FR-220 diary pattern) will address it holistically. Not a blocker for this FR.

**Authority granted.** Scope frozen. Implement per acceptance criteria.

## Related

- `yamlgraph/utils/llm_factory.py` — Provider factory (REQ-YG-010)
- `yamlgraph/config.py` — DEFAULT_MODELS configuration
- `tests/unit/test_lmstudio_provider.py` — Reference test pattern for new providers
- `tests/unit/test_architecture_provider_count.py` — Provider count guard (REQ-YG-121)
- FR-213 — Vertex AI Provider (closest precedent for enterprise provider addition)
- FR-230 — Google/Vertex Thinking Budget Support (thinking_budget pattern reference)

## Research Brief

*Compiled 2026-04-21. Sources: web docs, codebase analysis, diary entries.*

### Competitive Landscape

Every major LLM framework treats Azure as a first-class provider — not a "use OpenAI with a different base URL" workaround. A dedicated provider is the industry norm.

| Framework | Azure Support | Package / Mechanism | Azure AI Foundry? |
|-----------|--------------|---------------------|-------------------|
| **LangChain** | `AzureChatOpenAI` (Azure OpenAI Service only) + `AzureAIOpenAIApiChatModel` (Azure AI Foundry — unified) | `langchain-openai` for AzureChatOpenAI; `langchain-azure-ai>=1.2.0` for Foundry-unified class | ✅ via `langchain-azure-ai` |
| **AutoGen** | Two dedicated clients: `AzureOpenAIChatCompletionClient` (Azure OpenAI) + `AzureAIChatCompletionClient` (Azure AI Foundry / GitHub Models) | `autogen-ext[azure]` | ✅ |
| **Semantic Kernel** | `AddAzureOpenAIChatCompletion()` + `AddAzureAIInferenceChatCompletion()` — separate connectors for Azure OpenAI and Azure AI Inference | `Microsoft.SemanticKernel.Connectors.AzureOpenAI` / `.AzureAIInference` | ✅ |
| **LiteLLM** | `azure/` prefix routing. Supports Azure OpenAI + Azure Foundry Claude (`azure/claude-*`). Requires `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`. | Built-in — no extra package | ✅ |
| **CrewAI** | Delegates to LiteLLM — `azure/deployment-name` model strings. No dedicated Azure abstraction. | Via LiteLLM routing | ✅ (via LiteLLM) |
| **OpenAI Agents SDK** | No dedicated Azure support. Users can set `OPENAI_BASE_URL` to an Azure-compatible endpoint, but auth differences (deployment names, api-version headers, Azure AD) are not handled. | N/A — OpenAI-only by design | ❌ |
| **Google ADK** | No Azure support — Google/Vertex only by design. | N/A | ❌ |

**Could we just document "use OpenAI provider with Azure base URL"?** No. Azure uses deployment names instead of model names, requires `api-version` query parameters, and supports Azure AD auth — all incompatible with a plain `ChatOpenAI(base_url=...)` call. The FR's choice of `langchain-azure-ai` with `AzureAIOpenAIApiChatModel` is the correct LangChain-native approach, covering both Azure OpenAI and Azure AI Foundry models through one class. This matches what AutoGen and Semantic Kernel do with separate Azure clients.

### Existing Abstractions

**Factory pattern** (`yamlgraph/utils/llm_factory.py`, 443 lines): 10-provider `ProviderType` Literal → `_dispatch_provider()` → dedicated `_create_{provider}_llm()` functions. Azure would follow this exact pattern — add one Literal entry, one factory function, one dispatch case.

**Closest precedent**: Vertex AI (`_create_vertex_llm()`, lines 390–433) — the most complex provider with dual auth modes (Express API key vs ADC), env-var masking via `_masked_env()` context manager, and a thread-safety lock. Azure's key-only auth (FR-263 scope) is simpler than Vertex.

**Config** (`yamlgraph/config.py`): `DEFAULT_MODELS` dict — one entry per provider following `{PROVIDER}_MODEL` env var pattern. Azure fits exactly.

**Optional deps** (`pyproject.toml`): Pattern established by `replicate`, `redis`, `websearch` extras. `langchain-azure-ai>=1.2.0` as `[azure]` extra follows the same pattern.

**Test patterns**: `test_lmstudio_provider.py` (125 lines) is the canonical template — mock-based, covers provider validity, factory creation, env vars, temperature, model override. `test_architecture_provider_count.py` guards the provider count (must update expected set + ARCHITECTURE.md).

**No existing Azure code** in the codebase — zero overlap, zero conflicts. The `langchain-openai` package (already a base dependency) contains `AzureChatOpenAI` but the FR correctly chose `langchain-azure-ai` for broader Foundry coverage.

**Linter** (`yamlgraph/linter/checks_providers.py`): `THINKING_SUPPORTED_PROVIDERS` set — Azure should NOT be added in this FR (thinking budget deferred per constraints). No linter changes needed.

### Diary Precedents

| Diary Entry | Trap/Pattern | Relevance to FR-263 |
|-------------|-------------|---------------------|
| `2026-03-31-reflection-fr-213-vertex-ai-provider.md` | **lazy-import vs patchable name** — `try/except ImportError` at module level enables test patching but differs from in-function lazy imports. | FR-263 uses in-function import (line 53 of proposed code). Must ensure test patches target correct import path. Vertex precedent suggests module-level `try/except` may be needed if mocking `from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel`. |
| `2026-03-31-vertex-deprecation-migration.md` | **downstream_fix & working_system_inertia** — FR-213 shipped with deprecated `ChatVertexAI`; post-merge migration to `ChatGoogleGenerativeAI(vertexai=True)` was needed. | FR-263 already addresses this by verifying class name against PyPI v1.2.2 (`AzureAIOpenAIApiChatModel`, not deprecated `AzureChatModel`). Good — lesson learned from Vertex. |
| `2026-04-17-reflection-fr-230-google-vertex-thinking-budget.md` | **boundary normalization** — Enumerate full provider allowlist at boundary, never add "not-A" guard. | FR-263 correctly defers thinking budget to follow-up FR. No `THINKING_PROVIDERS` change needed. |
| `2026-04-17-reflection-fr-226-vertex-express-api-key-auth.md` | **downstream_fix** — Guard at env-var branch point (entry boundary), not at the SDK call. Mutually exclusive branches cleaner than conditional kwargs. | FR-263's factory function has clean boundary: check `AZURE_AI_ENDPOINT` and `AZURE_AI_API_KEY` at entry, raise `ValueError` if missing. No downstream patching. |
| `2026-04-12-reflection-fr-220-refactor-god-factory.md` | **registry over elif** — 15-branch elif chain refactored to registry dict in node factory. | `_dispatch_provider()` in `llm_factory.py` is currently a linear if/elif chain (10 branches). Adding Azure makes 11. Not yet at the "registry" threshold cited in FR-220 (which triggered at 15), but worth noting for future refactor. |

### Usage Evidence

- **Existing graphs using `provider:` metadata**: 69 references across `graphs/` and `examples/`
- **Provider distribution**: anthropic (24), mistral (33), openai (4), replicate (2), inception (1), xai (1), google (1) — no azure, deepseek, lmstudio, or vertex usage
- **Real-world use cases beyond the proposal**: Enterprise teams on Azure are the primary audience. Azure AI Foundry's model catalog (GPT-4o, Llama, Mistral, Cohere on Azure infra) is a differentiator vs. the existing OpenAI provider. No current users can be surveyed, but the FR's value statement (compliance, data residency, procurement) is a standard enterprise driver.
- **Current provider count**: 10 → would become 11

### Classification Signal

- **Abstraction level**: **integration** — follows an established, well-tested provider-addition pattern with no new abstractions or architectural changes
- **Recommended approach**: **build** — Azure is a first-class provider in every competing framework; "document a workaround" is insufficient due to Azure's incompatible auth/deployment model; the 5-file provider-addition pattern is proven and low-risk
- **Key risk**: `langchain-azure-ai>=1.2.0` dependency compatibility with the existing LangChain stack — resolver conflicts could block the FR (noted in constraints section)
