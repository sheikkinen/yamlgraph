---
type: feat
scope: examples
req: REQ-YG-471
---
- **FR-473 Iterable Text Card**: The shared editable-prose card (synopsis and
  woven beat) gained a 3-line prompt textarea plus **Iterate** and **Accept**.
  *Iterate* runs a shared `refine` prompt ("apply `<prompt>` to `<text>`"),
  replaces the text in place, and re-renders; an empty prompt is a pure save.
  Text autosaves on change. Iterating a beat returns it to a draft and never
  writes the chapter file (only Accept commits). Synopsis *Regenerate* and beat
  *Re-roll* are removed in favor of Iterate. (REQ-YG-471)
