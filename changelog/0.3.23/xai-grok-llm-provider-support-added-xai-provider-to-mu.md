---
type: feat
scope: xaigrok
---
- **xAI/Grok LLM Provider Support**
  - Added `xai` provider to multi-provider LLM factory
  - Uses OpenAI-compatible API with `base_url="https://api.x.ai/v1"`
  - Default model: `grok-beta` (configurable via `XAI_MODEL` env var)
  - Updated router demo to use xAI instead of Mistral
  - Added comprehensive tests for xAI provider
