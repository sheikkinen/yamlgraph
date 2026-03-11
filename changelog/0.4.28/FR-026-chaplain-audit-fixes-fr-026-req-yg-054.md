---
type: fix
scope: chaplain
req: REQ-YG-054
---
- **Chaplain audit fixes (FR-026, REQ-YG-054)** — 4 findings from code audit:
  - **HIGH**: `wrap_for_reducer` crash on non-dict python sub-node return — `AttributeError` on `.get()` when function returns string/int/list. Fixed with early `isinstance` guard.
  - **MEDIUM**: LLM `on_error: skip` silently dropped errors — no `PipelineError` recorded in `errors` list, unlike tool/python nodes. Now records error consistently.
  - **MEDIUM**: `on_error: retry/fallback` on tool/python nodes silently became `fail` — added linter check E011 to catch unsupported error strategies at lint time.
  - **LOW**: `prompts_relative=True` with `graph_path=None` + `prompts_dir` set — no warning about degraded resolution. Now logs warning.
