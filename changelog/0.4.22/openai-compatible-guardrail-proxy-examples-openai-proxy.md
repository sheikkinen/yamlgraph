---
type: feat
scope: openai-compatible
---
- **OpenAI-compatible guardrail proxy** (`examples/openai_proxy/`) — Fly.io-deployable FastAPI proxy with OpenAI `/v1/chat/completions` API. Graph pipeline: `echo_input` → `validate_input` (stamps `*validation missing*`) → LLM respond. Bearer token auth via `WEB_API_KEY`. 45 tests. Deployed at `yamlgraph-proxy.fly.dev`.
