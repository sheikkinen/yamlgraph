---
type: fix
scope: probe_recap
req: REQ-YG-083
---
- **FR-181 Probe Recap Python→YAML**: Eliminate `execute_prompt()` from probe_recap tool node. `extract_answers` converted to `type: llm` node; `merge_extraction` pure Python node reads `extraction_result` from state. Applied to both outcaller and incaller. SECTION_ORDER fixed (Added→Removed→Fixed); aggregate_changelog sorts entries ascending by FR number. (REQ-YG-083)
