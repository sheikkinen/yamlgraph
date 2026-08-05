---
type: feat
scope: examples
req: REQ-YG-578
---
- **FR-776 Vision Fallback for Scanned PDFs**: book-summary demo gains an opt-in `vision_fallback` branch — OCR-less pages are rendered via shared `render_page` (pdftoppm) and transcribed with typed `PageTranscription` page-echo validation through vision-capable providers (google, anthropic); provider preflight fires before any rendering; the FR-774 default guard moves to the graph level (raises only when the whole document yields no text and the flag is off, keeping blank windows nonfatal). (REQ-YG-578)
