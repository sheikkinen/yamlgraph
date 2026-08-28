---
type: feat
scope: examples
req: REQ-YG-624
---
- **FR-896 Pattern/Model Census Demo**: ships
  `examples/demos/pattern_model_census/` — a read-only, invocation-time
  discover/extract slot pipeline (reusing the FR-892 tool-slot mechanism)
  that classifies architectural/design patterns and LLM model/provider
  mentions from commit metadata via two `inception`/`mercury-2`-pinned
  map lenses. Extraction is metadata-only (`repo`, `sha`, `date`,
  `subject`, `shortstat` — no diff/file content, enforced by a
  `extra="forbid"` schema). The LLM-free reducer fails closed on any
  output path inside `yamlgraph` outside `tmp/`, and its public-safe
  markdown summary carries only `repo_alias`, `quarter`, `lens`, `label`,
  `count` — raw repo names, commit subjects, and SHAs stay in the private
  JSONL working ledger only. (REQ-YG-624)
