---
type: fix
scope: dungeon-master
---
- **FR-499A Reasoning Budget**: Cap the `chapter_close` node's hidden reasoning via `thinking_budget: 512` and raise `max_tokens` to 8000. gemini-3.5-flash spends reasoning tokens from the completion budget before emitting JSON; a 2000-token cap was consumed entirely by reasoning (~1921 tok), leaving an empty `world_state` ledger. The threshold is kept below 1024 so it bounds Gemini reasoning on vertex yet is ignored on non-thinking providers (inception/mercury) rather than raising. A config-boundary test pins both guards.
