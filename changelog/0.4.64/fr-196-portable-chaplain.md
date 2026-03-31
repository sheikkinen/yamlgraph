---
type: feat
scope: chaplain
req: REQ-YG-196
---
- **FR-196 Portable Chaplain**: Add `path` field to `PythonToolConfig` for file-path-based Python tool loading via `spec_from_file_location`. Relocate Chaplain graphs, prompts, and tools from `examples/` to `.chaplain/graphs/` for self-contained portability. Inline `DiaryEntry`/`extract_json` into `examples/shared/diary.py` for dependency isolation. (REQ-YG-196)
