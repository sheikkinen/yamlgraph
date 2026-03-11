---
type: fix
scope: diary
---
- **FR-093 Diary Entry Parsing** Fix `write_diary()` failing to append when `diary_entry` arrives as Pydantic model string representation (e.g., `theme='...' body='...' seed='...'`). Added regex parsing branch to handle this serialization format from LLM structured output.
