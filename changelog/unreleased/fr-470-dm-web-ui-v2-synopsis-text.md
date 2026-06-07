---
type: feat
scope: examples
req: REQ-YG-468
---
- **DM Web UI v2 — Synopsis as one editable text**: The synopsis is now generated
  and stored as a single prose paragraph instead of five structured fields. The
  synopsis card and the woven-beat view share one full-height editable component
  (`text_block.html`), so both fill the stage the same way. Downstream preplan
  prompts (plot, chapters, cast) now consume `{{ synopsis }}` as clean text rather
  than a Python-repr dict. (REQ-YG-468)
