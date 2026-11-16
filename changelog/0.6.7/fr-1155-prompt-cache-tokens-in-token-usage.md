---
type: feat
scope: cli
req: REQ-YG-064
---
- **FR-1155 `--token-usage` counts prompt-cache reads and writes**: the token tracker also sums LangChain's normalised `input_token_details` cache counts, and `summary()` returns them as `total_cache_read_tokens` and `total_cache_write_tokens`. The write count is `max(cache_creation, ephemeral_5m + ephemeral_1h)`, because langchain-anthropic 1.7.0 zeroes `cache_creation` when the per-TTL breakdown is present. The `--token-usage` line adds `, R cache read` and `, W cache write` after any thinking count, each when greater than 0; both are parts of `in`, never added to the total. A run with no cache activity prints exactly what it printed before. A live Haiku 5.5 witness proves a `system_segments` cache write followed by a read. (REQ-YG-064)
