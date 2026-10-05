---
type: fix
scope: llm
req: REQ-YG-010
---
- **FR-1146 Omit temperature for Anthropic models that reject it**: `create_llm` now sends `temperature` to Anthropic only for the probed accepting lines (`claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-sonnet-4-6`, `claude-opus-4-5`, `claude-opus-4-6`); every other Claude id, including `claude-opus-4-7`, `claude-opus-4-8` and all 5.x models, omits it and logs the omission at info. Previously every LLM node on those models failed with `400 temperature is deprecated for this model`. The extended-thinking `temperature=1` override is unchanged. (REQ-YG-010)
