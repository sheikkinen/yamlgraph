# Feature Request: Provider dispatch registry with keyless branch coverage

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-07-04

## Summary

`utils/llm_providers.py::dispatch_provider` is an 11-branch if/elif chain
(radon C) selecting the provider factory. Four branches (inception,
replicate, xai, lmstudio) have **zero test coverage** — they are dispatch
code that has never been executed by the suite. Convert the chain to a
data-driven registry dict and add keyless (mocked-constructor) dispatch
tests covering every provider branch.

## Value Statement

Adding a provider becomes a one-line registry entry with a mechanical test,
and provider-selection regressions (wrong factory, wrong default model,
dropped kwargs) are caught without any API key.

## Problem

1. **Open-closed violation.** Every new provider (three added in 2026 H1:
   vertex express, azure foundry, inception) edits `dispatch_provider`,
   growing its complexity. Radon already grades it C.
2. **Untestable-in-practice branches.** Tests for provider creation skip
   without API keys, so the inception/replicate/xai/lmstudio branches have
   never run under pytest. A typo in a branch (wrong env var name, wrong
   default model constant) ships silently — the `plausible_wrong_answer`
   shape at the provider boundary, which Scripture names explicitly:
   "normalize at the boundary, trusting no provider's type."
3. **Dispatch logic and construction logic are entangled**, so the cheap
   part (which factory?) can't be tested apart from the expensive part
   (construct real client).
4. **Defense-in-depth gap.** `create_llm()` already rejects invalid provider
  names before calling `dispatch_provider`, so normal callers do not fall
  through today. But `dispatch_provider()` itself still has a default
  Anthropic branch, which makes the lower boundary dishonest if it is called
  directly or if validation drifts.

## Proposed Solution

### Registry

```python
# utils/llm_providers.py
_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "anthropic": _create_anthropic_llm,
    "azure": _create_azure_llm,
    "deepseek": _create_deepseek_llm,
    "google": _create_google_llm,
    "inception": _create_inception_llm,
    "lmstudio": _create_lmstudio_llm,
    "mistral": _create_mistral_llm,
    "openai": _create_openai_llm,
    "replicate": _create_replicate_llm,
    "vertex": _create_vertex_llm,
    "xai": _create_xai_llm,
}

def dispatch_provider(provider: str, ...) -> BaseChatModel:
    factory = _PROVIDER_FACTORIES.get(provider)
    if factory is None:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Valid: {', '.join(sorted(_PROVIDER_FACTORIES))}"
        )
    return factory(...)
```

- **Unknown provider raises inside `dispatch_provider`** — normal callers are
  already protected by `create_llm()` validation, but the dispatch boundary
  itself should still be loud. The unset-provider default remains solely in
  `create_llm()`; `dispatch_provider()` should not have a hidden Anthropic
  fallback.

### Keyless branch tests

Parametrized over the registry, monkeypatching each provider's client
constructor so no key or network is needed:

```python
@pytest.mark.parametrize("provider", sorted(_PROVIDER_FACTORIES))
def test_dispatch_selects_correct_factory(provider, monkeypatch):
    ...  # assert the right constructor was called with expected model/kwargs
```

Asserts per branch: correct constructor called, default model constant
passed, temperature/thinking_budget plumbed. These are dispatch tests, not
integration tests — existing key-gated integration tests remain unchanged.

## Constraints

- Registry stays module-private in this FR — no plugin/entry-point
  registration API. That is speculative surface (Purge rule) until a real
  external provider needs it.
- No changes to individual `_create_*_llm` factories beyond what dispatch
  extraction requires.
- Provider selection priority (param > YAML > `PROVIDER` env > anthropic
  default) is `create_llm`'s concern and must be untouched — dedicated test
  pins it.

## Acceptance Criteria

- [x] `dispatch_provider` contains no if/elif provider chain; radon grade B
  or better
- [x] Unknown provider name passed directly to `dispatch_provider` raises
  `ValueError` listing valid providers
- [x] Existing `create_llm(provider="mistal")` invalid-provider test remains
  the caller-level misspelling guard; do not add a false RED claiming normal
  callers currently fall through to Anthropic
- [x] Parametrized keyless dispatch test covers **all 11** registry entries;
  runs in the fast suite (`-m "not slow"`, no API keys)
- [x] Default-resolution priority test (param > YAML > env > default) passes
  unchanged
- [x] All tests tagged `@pytest.mark.req(...)` (existing provider CAP/REQ)
- [x] Changelog fragment in `changelog/unreleased/`
- [x] `reference/` provider docs updated if they describe the fallthrough

## Implementation Status

**Enforced.** Replaced the 11-branch chain with `_PROVIDER_FACTORIES` registry
plus a `_THINKING_PROVIDERS` frozenset that routes `thinking_budget` only to
anthropic/google/vertex. `dispatch_provider` now `.get()`s the factory and
raises `ValueError` listing valid names on miss — no Anthropic default at this
boundary. `dispatch_provider` is no longer radon C. New keyless suite
`tests/unit/test_fr680_provider_registry.py` parametrizes over all 11
providers (monkeypatching the registry), exercising the previously untested
inception/replicate/xai/lmstudio branches without keys. Existing
`create_llm` selection-priority and invalid-provider tests unchanged and
passing. No `reference/` doc described the fallthrough, so none required edit.

**Deviation:** four FR-230 tests patched the factory by module attribute
(`patch("...._create_google_llm")`). The registry captures factory references
at import, so name-patching no longer reached dispatch — those tests were
re-pointed to patch the new seam (`patch.dict(_PROVIDER_FACTORIES, ...)`).
Behavior asserted (thinking_budget plumbed, temperature not overridden) is
identical; only the patch target moved to follow the dispatch seam.

## Alternatives Considered

1. **Entry-point plugin system** — rejected for now: no external consumer
   exists; registry dict gives 90% of the extensibility at 5% of the
   surface.
2. **Keep chain, add tests only** — rejected: tests would pin an 11-branch
   chain including its silent fallthrough; the refactor is what makes the
   loud failure and one-line extension possible.
3. **Registry on `create_llm` level instead of `dispatch_provider`** —
   rejected: `create_llm` owns cross-provider normalization (temperature,
   thinking budget); mixing selection into it re-entangles what this FR
   separates.

## Related

- FR-659 — coverage-gap push (same doctrine: untested boundary = unverified
  claim)
- Scripture: Agents' prayer ("normalize at the boundary, trusting no
  provider's type"), Commandment 6 (no silent fallbacks),
  `detection_without_enforcement`
- `utils/llm_factory.py::create_llm` — consumer; unchanged selection
  priority

## Judgement

**APPROVED WITH REQUIRED AMENDMENTS FOLDED IN.** The registry refactor is worth
doing: `dispatch_provider()` is an 11-branch selection function and several
provider branches can be tested cheaply without API keys by patching the local
factory functions. A module-private registry improves coverage and extension
mechanics without adding a plugin surface.

One premise needed correction. Normal misspelled providers do **not** currently
fall through to Anthropic, because `create_llm()` validates `selected_provider`
against `DEFAULT_MODELS` before dispatch. The real issue is lower-boundary
defense in depth: direct `dispatch_provider("mistal", ...)` falls through to
Anthropic today. The RED/GREEN criteria now target that direct dispatch
contract and preserve the existing caller-level invalid-provider test.

**Verdict:** Approved after correction. Keep this as a dispatch refactor plus
keyless branch coverage; do not change provider-selection priority or individual
provider factory behavior.
