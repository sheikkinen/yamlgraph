---
type: fix
scope: reliability
---
- **FR-933 Retry Carries Validation Feedback**: A node retrying after a Pydantic `ValidationError` now receives bounded, diagnostic-only feedback (failing field path, sanitized message, limit/actual metadata) as an appended correction instruction. Previously the retry re-sent a byte-identical request to a deterministic model, so a schema rejection could only be re-earned — `max_retries` bought attempts that could not differ. The rejected value is never carried back.
