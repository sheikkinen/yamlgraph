---
type: fix
scope: agent
---
- **FR-678 Narrowed structured-output catch**: `agent._try_structured_output` now catches only `ValidationError` around the cheap `model_validate` parse; programming defects (`TypeError`, `AttributeError`) and a broken `extract_json` (`ValueError`) propagate instead of being masked as an expensive LLM re-invoke. Fallback triggers log at `warning` with the exception class name.
