---
type: feat
scope: ebook
req: REQ-YG-092
---
- **FR-103 eBook Judge-Amend Subgraph** (REQ-YG-092): Validation pattern for per-chapter content verification
  - `examples/ebook/subgraphs/validate_chapter.yaml`: Judge→amend cycle subgraph
  - `examples/ebook/prompts/judge/chapter.yaml`: Validates inline citations against source files
  - `examples/ebook/prompts/amend/chapter.yaml`: Fixes chapters when validation fails
  - `examples/ebook/prompts/chapter/*.yaml`: 6 merged chapter prompts with inline citations
  - `persist_chapter` tool node for single chapter persistence
  - Rewired graph to 18 nodes (write→validate→persist per chapter)
  - 4 new doctrine validation tests in `tests/unit/test_ebook_doctrine_validation.py`
