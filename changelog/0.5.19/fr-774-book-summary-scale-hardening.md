---
type: feat
scope: examples
req: REQ-YG-577
---
- **FR-774 Book-Summary Scale Hardening**: `split_document` gains `pages_per_chunk` (batch consecutive pages into one chunk, one pdftotext call each) and `min_chars` (drop sub-threshold chunks) with new explicit failures: all-empty extraction raises naming scanned/image-only (vision fallback stays a signposted non-goal) and all-filtered-by-threshold raises naming `min_chars` — never a success-shaped empty chunk list. The book-summary demo batches 10 pages/chunk with `min_chars: 200` under a documented 1000-page budget; prompts speak excerpt semantics with summary-only output. Fixes the reported 418-page truncation-to-100 and blank-page commentary. (REQ-YG-577)
