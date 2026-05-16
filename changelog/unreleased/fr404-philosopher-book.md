---
type: feat
scope: demos
req: REQ-YG-404
---
- **FR-404 Philosopher's Book**: YAMLGraph pipeline generating a 21-chapter philosophical work, one chapter per cognitive trap, using copilot nodes with diary search tools and sequential map execution. Chapters saved incrementally to `output_dir/chapters/` for crash-safe runs; single-chapter generation via `--var chapter_num=N`; `assemble_book` prefers saved files over state. (REQ-YG-404)
