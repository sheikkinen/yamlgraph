---
type: fix
scope: providers
req: REQ-YG-684
---
- **FR-1056 DeepSeek thinking can be turned off**: `thinking_budget: 0` on a `deepseek` node now sends `reasoning_effort: "none"`, disabling DeepSeek's default reasoning instead of being silently discarded. DeepSeek exposes no token budget, so only `0` is expressible: omitting the field preserves the API default (thinking on, effort `high`), an accepted sub-1024 budget stays a logged no-op for provider portability, and `≥1024` still raises. (REQ-YG-684)
