---
type: feat
scope: lm
---
- **LM Studio Provider Support**
  - New `lmstudio` provider for local LLM inference via LM Studio
  - Uses OpenAI-compatible API with custom `base_url`
  - No API key required (local server)
  - Config: `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL`
  - Default model: `qwen2.5-coder-7b-instruct`
  - 8 unit tests for provider integration
