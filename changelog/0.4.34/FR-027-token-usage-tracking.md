---
type: feat
scope: token
req: REQ-YG-064
---
- **Token usage tracking** (REQ-YG-064): `TokenUsageCallbackHandler` callback accumulates `input_tokens`, `output_tokens`, and `total_calls` across all LLM invocations in a graph run. CLI `--token-usage` flag prints summary. Follows the same `config["callbacks"]` pattern as LangSmith tracer. Completes FR-027 P2-8.
