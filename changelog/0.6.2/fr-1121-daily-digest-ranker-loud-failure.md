---
type: fix
scope: examples
req: REQ-YG-664
---
- **FR-1121 daily_digest ranker survives constrained decoding and fails loudly**: `examples/daily_digest/prompts/rank_stories.yaml` types `stories` as `list[dict]` instead of `list[Any]`, whose untyped items the Anthropic SDK's constrained-decoding transform rejects since FR-998; `rank_stories` declares `on_error: fail`, so a ranker failure propagates instead of continuing into formatting with an absent result. Three offline witnesses: SDK transform on the committed prompt model, the declaration, and a compiled-graph run proving the original exception propagates and `format_email` never runs. (REQ-YG-664)
