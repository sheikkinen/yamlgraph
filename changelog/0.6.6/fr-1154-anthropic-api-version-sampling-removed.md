---
type: fix
scope: llm
req: REQ-YG-010
---
- **FR-1154 Omit sampling parameters under Anthropic API 2026-10-21**: with `anthropic>=2` installed (API version `2026-10-21`, which rejects `temperature`/`top_p`/`top_k` on every model with a 400), `create_llm()` now sends no temperature on any Anthropic model, including the `temperature=1` previously forced by `thinking_budget >= 1024`. The decision follows the `anthropic-version` header the installed SDK sends; on SDK 1.x the FR-1146 per-model rule is unchanged. (REQ-YG-010)
