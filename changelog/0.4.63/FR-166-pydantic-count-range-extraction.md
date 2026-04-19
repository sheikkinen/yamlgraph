---
type: fix
scope: pydantic
req: REQ-YG-155
---
- **FR-166 Pydantic count_range Extraction**: Add `_extract_countable()` helper that unwraps Pydantic models with a single list field before count_range verification. Fixes bug where `len(BaseModel)` raised `TypeError`, defaulting to 0 and causing false violations on correct LLM outputs. (REQ-YG-154)
