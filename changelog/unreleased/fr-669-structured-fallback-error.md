---
type: fix
scope: executor
---
- **FR-669 Structured fallback raises extraction error**: When FR-464 JSON extraction fallback fails, raises `ValueError("could not extract JSON")` with response snippet instead of re-raising the original opaque provider `response_format` error. Also accepts `list` JSON responses.
