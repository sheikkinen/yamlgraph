---
type: feat
scope: async
---
- **FR-676 Async invoke retry+fallback parity**: `invoke_async` now retries on transient errors with exponential backoff (`asyncio.sleep`) and falls back to JSON extraction when provider rejects `response_format` (FR-464 parity). `build_schema_hint` moved to `executor_base.py` for shared use. (REQ-YG-010)
