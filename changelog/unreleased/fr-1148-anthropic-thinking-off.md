---
type: fix
scope: llm
req: REQ-YG-083
---
- **FR-1148 `thinking_budget: 0` turns Anthropic thinking off**: `0` on an Anthropic node now sends the off switch each model accepts: `{"type": "between_tools"}` on `claude-sonnet-5-5`, `{"type": "disabled"}` on the other listed Claude models, and a `ValueError` at client construction on `claude-opus-5-5` and `claude-fable-5*`, which cannot turn thinking off. Previously `0` sent nothing, so Sonnet 5.5 could spend its whole `max_tokens` on thinking and return an empty or cut-off answer. Omitting `thinking_budget` and `>= 1024` are unchanged. (REQ-YG-083)
