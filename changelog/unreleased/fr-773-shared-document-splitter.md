---
type: feat
scope: examples
req: REQ-YG-577
---
- **FR-773 Shared Document Splitter Manifest**: `examples/shared/split_document.py` splits a PDF into per-page text chunks (`{"chunks": [{"index", "text"}], "total"}`) via poppler, with an explicit ValueError failure contract (unknown mode, missing file, missing binaries, subprocess failure, unparseable page count — no fallback). Declared once in `examples/shared/split_document.tool.yaml` (FR-768 manifest) and consumed by the new `examples/demos/book-summary` demo: tool_call with inline kwargs (FR-772) → map over chunks → reduce to book summary. (REQ-YG-577)
