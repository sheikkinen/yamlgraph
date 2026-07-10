---
type: fix
scope: providers
---
- **FR-680 Provider dispatch registry**: Replace the 11-branch if/elif in `llm_providers.dispatch_provider` with a data-driven `_PROVIDER_FACTORIES` registry. Unknown providers now raise `ValueError` listing valid names (no silent Anthropic fallback at the dispatch boundary; `create_llm` still owns unset-provider defaulting). Adds keyless parametrized dispatch tests covering all 11 providers — including the previously untested inception/replicate/xai/lmstudio branches — with no API keys.
