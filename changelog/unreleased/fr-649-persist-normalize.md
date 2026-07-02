---
type: fix
scope: novel_fandom
req: REQ-YG-499
---
- **FR-649 Persist boundary normalization**: normalize_page coerces LLM-varied shapes (relationship key variants, participant dicts, consequence dicts, reference dicts, scalar-to-list, Rule.domain default) to schema-expected shapes before Pydantic validation. Pages that still fail are persisted with warning instead of silently dropped. (REQ-YG-499)
