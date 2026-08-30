---
type: fix
scope: research
req: REQ-YG-623
---
- **FR-926 Research Failure Cites the Recorded Cause**: `gather_findings` now surfaces the errors the retry handler already recorded in `state["errors"]` — node, error category, exception type, and message — alongside the missing persona key, instead of raising the symptom alone. `PipelineError` objects and dict-form entries are both rendered; unstructured entries are ignored and an empty error channel keeps the terse message. (REQ-YG-623)
