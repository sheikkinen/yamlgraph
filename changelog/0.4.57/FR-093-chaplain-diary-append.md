---
type: feat
scope: chaplain
req: REQ-YG-090
---
- **FR-093 Chaplain Diary Append** (CAP-31, REQ-YG-090): Extend `.chaplain/graph.yaml` with automatic diary entry creation
  - `summarize` (LLM) node produces DiaryEntry schema (theme, body, seed) from Plan→Judge output
  - `write_diary` (Python) node appends formatted entry to `docs/diary.md`
  - `format_diary_entry()` now accepts configurable `prefix` parameter (default "World Digest")
  - `watch.sh` passes `--var date` and `--var diary_prefix=Chaplain` to graph
  - `.chaplain/prompts/summarize.yaml` with inline Pydantic schema
