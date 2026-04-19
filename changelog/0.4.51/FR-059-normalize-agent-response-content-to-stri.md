---
type: fix
scope: normalize
---
- **FR-059 Normalize agent response.content to string** (REQ-YG-018): Anthropic Claude returns `response.content` as `list[dict]` content blocks instead of `str`. Added `_normalize_content()` helper that extracts text from list blocks, passes strings through, and converts None to empty string. Applied at both agent return paths (normal completion and max-iterations). Four new tests.
