---
type: fix
scope: fsm
---
- **FR-420 extract_event dict support**: `extract_event()` now handles plain dicts (LangGraph serialized `CopilotResult` state) in addition to strings and Pydantic models. Unified dict/model_dump branches eliminate code duplication. Fixes judge step always routing to `event=error` instead of APPROVE/AMEND/REJECT/SPLIT verdicts.
