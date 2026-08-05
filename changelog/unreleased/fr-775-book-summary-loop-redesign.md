---
type: feat
scope: examples
req: REQ-YG-577
---
- **FR-775 Book-Summary Loop Redesign**: split_document gains `mode: info` (pdfinfo-only page-count probe), `allow_empty_selection` (windowed loop fetches opt out of all-empty/all-filtered raises; default stays loud), and absolute page identity per chunk (`page`, or `page_start`/`page_end` when batched). The book-summary demo becomes a cursor-loop showcase: tool manifest probe/fetch, python-node gates and batch planning, per-page LLM map with `{page, summary}` schema, page-identity accumulation through an `add` reducer, and `loop_limits`/`loop_exits` termination — small-model-friendly one-page LLM calls with a documented 1000-page budget. (REQ-YG-577)
