---
type: feat
scope: census
req: REQ-YG-674
---
- **FR-1033 Bounded local-Markdown corpus adapters**: `md_discover` and
  `md_extract` bind the corpus-census pipeline to a directory of Markdown
  files. Both fail closed — an over-ceiling directory or an oversize file
  raises naming the observed value and the limit, rather than returning a
  prefix or a truncation. Each item carries byte identity frozen at discovery
  and re-verified before decoding. (REQ-YG-674)
