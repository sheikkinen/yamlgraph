---
type: feat
scope: cli
req: REQ-YG-064
---
- **FR-1152 `--token-usage` counts thinking tokens**: the token tracker also sums LangChain's normalised `output_token_details.reasoning` (Anthropic's thinking tokens), and `summary()` returns it as `total_reasoning_tokens`. The `--token-usage` line adds `, N thinking` when N > 0; the count is a part of `out`, never added to the total. A run with no thinking prints exactly what it printed before. (REQ-YG-064)
