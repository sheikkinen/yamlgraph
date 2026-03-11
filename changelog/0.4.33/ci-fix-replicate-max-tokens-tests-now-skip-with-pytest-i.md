---
type: fix
scope: ci
---
- **CI fix**: Replicate `max_tokens` tests now skip with `pytest.importorskip("langchain_litellm")` when the optional dependency is missing. Fixes v0.4.32 CI failure.
