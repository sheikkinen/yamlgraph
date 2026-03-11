---
type: fix
scope: ebook
req: REQ-YG-091
---
- **FR-100 eBook Authoring Pipeline** (CAP-32, REQ-YG-091): YAMLGraph-driven pipeline to write development pipeline documentation as an eBook
  - `examples/ebook/graph.yaml`: 14-node pipeline with copilot research nodes, LLM writing nodes, judge, and write tool
  - `examples/ebook/nodes/writing.py`: `write_chapters_tool` writes formatted chapter content to disk
  - `examples/ebook/prompts/research/*.yaml`: 6 research prompts for gathering source material
  - `examples/ebook/prompts/write/*.yaml`: 6 writing prompts for drafting chapters
  - `examples/ebook/prompts/judge_draft.yaml`: Review prompt for accuracy and completeness
  - `docs/ebook/README.md`: Build instructions and contribution guide
  - `docs/ebook/_build.sh`: pandoc-based HTML/PDF renderer
  - Unit tests for `write_chapters_tool` in `tests/unit/test_ebook_writing.py`
