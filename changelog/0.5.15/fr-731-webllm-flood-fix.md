---
type: fix
scope: examples
---
- **FR-731 WebLLM flood fix**: grammar-constrained decoding without prompt-side JSON steering floods whitespace deterministically (run 1: 3919 bytes, one `{` + 3914 spaces, 86.8 s). `build.py` now appends a schema-agnostic JSON directive to every compiled system prompt — mechanical compile output, not hand-tuning (test guards no field names leak); the page bounds `max_tokens: 512`. The spike's first banked finding: prompt template + schema alone is insufficient for grammar-enforced runtimes.
